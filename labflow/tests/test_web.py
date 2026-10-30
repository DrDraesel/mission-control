"""Tests for labflow.app — FastAPI TestClient over the real LabFlow core.

Uses a throwaway patient dir per test; the only stubbed collaborator is
``probe_all`` (monkeypatched) so no live lab apps are required.  The
lock/concurrency tests drive real threads through ``os.replace`` (TestClient
dispatches the sync endpoints onto a worker threadpool) and use a local
recording notifier to count notifications.
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile
import threading
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from labflow import app as app_module  # noqa: E402
from labflow.notify import Notifier, NullNotifier  # noqa: E402
from labflow.patients import PatientStore  # noqa: E402
from labflow.workflow import DEFAULT_WORKFLOW  # noqa: E402

ORDERED_IDS = [station.id for station in DEFAULT_WORKFLOW.ordered_stations()]


class RecordingNotifier(Notifier):
    """Notifier double that records every callback as (event, station_id)."""

    def __init__(self):
        self.calls = []

    def step_started(self, patient, station, next_station=None):
        self.calls.append(("step_started", getattr(station, "id", None)))
        return True

    def step_completed(self, patient, station, next_station=None):
        self.calls.append(("step_completed", getattr(station, "id", None)))
        return True

    def flow_completed(self, patient):
        self.calls.append(("flow_completed", None))
        return True

    def reminder(self, patient, current_station=None):
        self.calls.append(("reminder", getattr(current_station, "id", None)))
        return True

    def events(self, name=None):
        """All event names, or the station ids of one event name."""
        if name is None:
            return [event for event, _ in self.calls]
        return [sid for event, sid in self.calls if event == name]


class WebLayerTestCase(unittest.TestCase):
    """One app + tmp store + recording notifier per test."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        store = PatientStore(pathlib.Path(self._tmp.name))
        self.store = store
        self.notifier = RecordingNotifier()
        self.app = app_module.create_app(
            config={}, store=store, workflow=DEFAULT_WORKFLOW, notifier=self.notifier
        )
        self.client = TestClient(self.app)

    # -- helpers ---------------------------------------------------------
    def create_patient(self, name="Jane Doe", intake=None):
        response = self.client.post(
            "/api/patients", json={"name": name, "intake": intake or {}}
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["ok"])
        return body["patient"]

    def patient_view(self, patient_id):
        response = self.client.get(f"/api/patients/{patient_id}")
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def complete_all(self, patient_id):
        while True:
            view = self.patient_view(patient_id)
            if view["next"] is None:
                return view
            response = self.client.post(f"/api/patients/{patient_id}/complete", json={})
            self.assertEqual(response.status_code, 200, response.text)


class StaticTests(WebLayerTestCase):
    def test_index_serves_the_ui(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("LabFlow", response.text)
        self.assertIn("NEXT STEP", response.text)

    def test_static_assets_are_served(self):
        js = self.client.get("/static/labflow.js")
        self.assertEqual(js.status_code, 200)
        self.assertIn("LabFlow web UI", js.text)
        css = self.client.get("/static/styles.css")
        self.assertEqual(css.status_code, 200)
        self.assertIn(".next-banner", css.text)

    def test_mirror_serves_the_portrait_station_display(self):
        response = self.client.get("/mirror")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Mirror Station", response.text)
        self.assertIn("/api/patients", response.text)
        # read-only display: it must never POST back into the flow
        self.assertNotIn("POST", response.text)
        self.assertNotIn("method:\"POST\"", response.text)


class WorkflowEndpointTests(WebLayerTestCase):
    def test_workflow_endpoint_order_matches_longest_last(self):
        response = self.client.get("/api/workflow")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        workflow = payload["workflow"]
        self.assertEqual([s["id"] for s in workflow["stations"]], ORDERED_IDS)
        # pinned intake first, the longest test (30 min) last
        self.assertEqual(workflow["stations"][0]["id"], "intake")
        self.assertEqual(workflow["stations"][-1]["id"], "treadmill_form")
        minutes = [s["typical_minutes"] for s in workflow["stations"][1:]]
        self.assertEqual(minutes, sorted(minutes))
        self.assertEqual(workflow["validation_errors"], [])

    def test_workflow_station_payload_shape(self):
        workflow = self.client.get("/api/workflow").json()["workflow"]
        station = workflow["stations"][0]
        for key in ("id", "name", "app", "description", "typical_minutes", "launch",
                    "capture", "order", "launch_hint", "capture_prompt"):
            self.assertIn(key, station)
        self.assertEqual(station["launch"]["type"], "manual")
        self.assertIn("consent_signed", station["capture"]["fields"])


class PatientLifecycleTests(WebLayerTestCase):
    def test_patients_list_starts_empty(self):
        body = self.client.get("/api/patients").json()
        self.assertEqual(body, {"ok": True, "patients": []})

    def test_create_patient_initialises_flow(self):
        patient = self.create_patient()
        self.assertEqual(patient["status"], "active")
        self.assertEqual(set(patient["steps"]), set(ORDERED_IDS))
        self.assertTrue(all(s["state"] == "pending" for s in patient["steps"].values()))

    def test_create_patient_requires_name(self):
        response = self.client.post("/api/patients", json={})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["ok"])

    def test_patient_view_shows_next_step_and_progress(self):
        patient = self.create_patient()
        view = self.patient_view(patient["id"])
        self.assertEqual(len(view["steps"]), 9)
        self.assertEqual(view["next"]["id"], "intake")
        self.assertEqual(view["next"]["name"], "Intake & Consent")
        self.assertIn("Intake & Consent", view["next_instruction"])
        self.assertEqual(view["progress"], {"done": 0, "total": 9, "pct": 0, "current": "intake"})

    def test_unknown_patient_is_404(self):
        response = self.client.get("/api/patients/does-not-exist")
        self.assertEqual(response.status_code, 404)
        self.assertFalse(response.json()["ok"])
        self.assertIn("unknown patient", response.json()["error"])

    def test_begin_then_complete_advances_to_next_station(self):
        patient = self.create_patient()
        pid = patient["id"]

        started = self.client.post(f"/api/patients/{pid}/begin", json={})
        self.assertEqual(started.status_code, 200, started.text)
        self.assertEqual(started.json()["patient"]["steps"]["intake"]["state"], "in_progress")

        done = self.client.post(f"/api/patients/{pid}/complete", json={})
        self.assertEqual(done.status_code, 200, done.text)
        body = done.json()
        self.assertEqual(body["patient"]["steps"]["intake"]["state"], "done")
        self.assertEqual(body["next"]["id"], "vitals")
        self.assertEqual(body["progress"]["done"], 1)
        self.assertIn("Vitals", body["next_instruction"])

    def test_complete_records_notes_and_results(self):
        patient = self.create_patient()
        pid = patient["id"]
        response = self.client.post(
            f"/api/patients/{pid}/complete",
            json={"notes": "consent signed", "results": {"consent_signed": True}},
        )
        self.assertEqual(response.status_code, 200, response.text)
        step = response.json()["patient"]["steps"]["intake"]
        self.assertEqual(step["state"], "done")
        self.assertEqual(step["notes"], "consent signed")
        self.assertIn({"consent_signed": True}, step["results"])

    def test_complete_auto_begins_a_pending_current_step(self):
        patient = self.create_patient()
        response = self.client.post(f"/api/patients/{patient['id']}/complete", json={})
        step = response.json()["patient"]["steps"]["intake"]
        self.assertEqual(step["state"], "done")  # no explicit Begin needed
        self.assertTrue(step["started_at"])
        self.assertTrue(step["completed_at"])

    def test_complete_non_current_station_is_409(self):
        patient = self.create_patient()
        response = self.client.post(
            f"/api/patients/{patient['id']}/complete", json={"station_id": "balance"}
        )
        self.assertEqual(response.status_code, 409)
        self.assertFalse(response.json()["ok"])
        self.assertIn("not the current step", response.json()["error"])

    def test_skip_records_reason_and_advances(self):
        patient = self.create_patient()
        pid = patient["id"]
        response = self.client.post(
            f"/api/patients/{pid}/skip", json={"reason": "patient declined"}
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        step = body["patient"]["steps"]["intake"]
        self.assertEqual(step["state"], "skipped")
        self.assertIn("Skipped: patient declined", step["notes"])
        self.assertEqual(body["next"]["id"], "vitals")
        self.assertEqual(body["progress"]["done"], 1)

    def test_full_flow_completes_and_then_conflicts(self):
        patient = self.create_patient()
        pid = patient["id"]
        view = self.complete_all(pid)
        self.assertIsNone(view["next"])
        self.assertEqual(view["progress"], {"done": 9, "total": 9, "pct": 100, "current": None})
        self.assertEqual(view["patient"]["status"], "completed")
        self.assertIn("All stations complete", view["next_instruction"])

        conflict = self.client.post(f"/api/patients/{pid}/complete", json={})
        self.assertEqual(conflict.status_code, 409)
        begin = self.client.post(f"/api/patients/{pid}/begin", json={})
        self.assertEqual(begin.status_code, 409)

    def test_redo_resets_station_and_reopens_completed_flow(self):
        patient = self.create_patient()
        pid = patient["id"]
        self.complete_all(pid)

        response = self.client.post(f"/api/patients/{pid}/redo", json={"station_id": "vitals"})
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        step = body["patient"]["steps"]["vitals"]
        self.assertEqual(step["state"], "pending")
        self.assertIsNone(step["started_at"])
        self.assertIsNone(step["completed_at"])
        self.assertEqual(body["next"]["id"], "vitals")
        self.assertEqual(body["patient"]["status"], "active")

    def test_redo_validates_station_id(self):
        patient = self.create_patient()
        pid = patient["id"]
        missing = self.client.post(f"/api/patients/{pid}/redo", json={})
        self.assertEqual(missing.status_code, 400)
        unknown = self.client.post(f"/api/patients/{pid}/redo", json={"station_id": "nope"})
        self.assertEqual(unknown.status_code, 404)

    def test_measurement_endpoint(self):
        patient = self.create_patient()
        pid = patient["id"]
        response = self.client.post(
            f"/api/patients/{pid}/measurement",
            json={"metric": "resting_hr", "value": 54, "unit": "bpm", "source": "vitals cart"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertEqual(body["measurement"]["metric"], "resting_hr")
        self.assertEqual(body["measurement"]["value"], 54)
        self.assertEqual(body["measurement"]["unit"], "bpm")
        self.assertIn("ts", body["measurement"])
        self.assertEqual(len(body["patient"]["measurements"]), 1)

        missing = self.client.post(f"/api/patients/{pid}/measurement", json={"value": 1})
        self.assertEqual(missing.status_code, 400)

    def test_link_endpoint_links_session_and_completes_step(self):
        patient = self.create_patient()
        pid = patient["id"]
        response = self.client.post(
            f"/api/patients/{pid}/link", json={"app": "bertec", "session_id": "sess-1"}
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["step_completed"])
        self.assertEqual(body["linked"], {"app": "bertec", "session_id": "sess-1"})
        self.assertEqual(body["patient"]["linked_sessions"]["bertec"]["ids"], ["sess-1"])
        self.assertEqual(body["patient"]["steps"]["intake"]["state"], "done")
        self.assertEqual(body["next"]["id"], "vitals")

        # linking the same session again must not duplicate the id
        again = self.client.post(
            f"/api/patients/{pid}/link", json={"app": "bertec", "session_id": "sess-1"}
        )
        self.assertEqual(again.json()["patient"]["linked_sessions"]["bertec"]["ids"], ["sess-1"])

    def test_link_requires_app_and_session(self):
        patient = self.create_patient()
        pid = patient["id"]
        self.assertEqual(
            self.client.post(f"/api/patients/{pid}/link", json={"session_id": "x"}).status_code, 400
        )
        self.assertEqual(
            self.client.post(f"/api/patients/{pid}/link", json={"app": "bertec"}).status_code, 400
        )

    def test_create_patient_retries_transient_windows_file_lock(self):
        """A one-off PermissionError from os.replace must not fail creation."""
        inner = app_module.FlowEngine(self.store, DEFAULT_WORKFLOW, NullNotifier())

        class FlakyEngine:
            def __init__(self):
                self.calls = 0

            def start_patient(self, patient_id):
                self.calls += 1
                if self.calls == 1:
                    raise PermissionError("[WinError 32] transient lock")
                return inner.start_patient(patient_id)

            def progress(self, patient):
                return inner.progress(patient)

        flaky = FlakyEngine()
        app = app_module.create_app(config={}, store=self.store, workflow=DEFAULT_WORKFLOW,
                                    notifier=NullNotifier(), engine=flaky)
        client = TestClient(app)
        response = client.post("/api/patients", json={"name": "Flaky File"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["ok"])
        self.assertEqual(flaky.calls, 2)  # retried once, then succeeded

    def test_patients_list_includes_progress(self):
        patient = self.create_patient(name="List Check")
        body = self.client.get("/api/patients").json()
        entry = next(p for p in body["patients"] if p["id"] == patient["id"])
        self.assertEqual(entry["progress"]["total"], 9)
        self.assertEqual(entry["progress"]["current"], "intake")

    def test_next_endpoint_and_unknown_patient(self):
        patient = self.create_patient()
        pid = patient["id"]
        body = self.client.get(f"/api/next/{pid}").json()
        self.assertTrue(body["ok"])
        self.assertIn("Intake & Consent", body["instruction"])
        self.assertEqual(body["current"]["id"], "intake")
        self.assertEqual(self.client.get("/api/next/nobody").status_code, 404)


class ProbeEndpointTests(WebLayerTestCase):
    def test_probes_endpoint_uses_probe_all(self):
        patient = self.create_patient()
        pid = patient["id"]
        fake = {"checked_at": "2026-10-16T12:00:00+00:00",
                "apps": {"bertec": {"app": "bertec", "available": True, "count": 2, "latest": {"id": "s9"}}}}
        fake_probe = mock.Mock(return_value=fake)
        with mock.patch.object(app_module, "probe_all", fake_probe):
            response = self.client.get(f"/api/patients/{pid}/probes")
            self.assertEqual(fake_probe.call_count, 1)
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["probes"], fake)
        self.assertIsNone(body["station_probe"])  # intake has no probe

    def test_probes_station_probe_reported_for_auto_station(self):
        patient = self.create_patient()
        pid = patient["id"]
        # walk to the bertec balance station (8th in order, index 7)
        for _ in range(7):
            self.client.post(f"/api/patients/{pid}/complete", json={})
        with mock.patch.object(app_module, "probe_all",
                               lambda: {"checked_at": "", "apps": {}}):
            body = self.client.get(f"/api/patients/{pid}/probes").json()
        self.assertEqual(body["station_probe"], "bertec protocol sessions")

    def test_probes_unknown_patient_is_404(self):
        response = self.client.get("/api/patients/ghost/probes")
        self.assertEqual(response.status_code, 404)


class NameLengthTests(WebLayerTestCase):
    """F3 — the API caps patient names at 120 chars (after stripping)."""

    def test_create_patient_name_at_limit_succeeds_and_flow_runs(self):
        name = "x" * 120
        response = self.client.post("/api/patients", json={"name": name})
        self.assertEqual(response.status_code, 200, response.text)
        patient = response.json()["patient"]
        self.assertEqual(patient["name"], name)
        # the file really exists on disk and the flow can be driven onward
        self.assertTrue(self.store.exists(patient["id"]))
        self.assertEqual(len(list(self.store.patients_dir.glob("*.json"))), 1)
        done = self.client.post(f"/api/patients/{patient['id']}/complete", json={})
        self.assertEqual(done.status_code, 200, done.text)
        self.assertEqual(done.json()["progress"]["done"], 1)

    def test_create_patient_name_over_limit_is_400_json(self):
        for length in (121, 300, 100000):
            with self.subTest(length=length):
                response = self.client.post("/api/patients", json={"name": "x" * length})
                self.assertEqual(response.status_code, 400, response.text)
                self.assertEqual(
                    response.headers["content-type"].split(";")[0], "application/json"
                )
                body = response.json()
                self.assertFalse(body["ok"])
                self.assertIn("name", body["error"])
        # nothing was persisted for any rejected name
        self.assertEqual(list(self.store.patients_dir.glob("*.json")), [])

    def test_name_limit_counts_stripped_length(self):
        padded = "  " + "x" * 120 + "  "
        response = self.client.post("/api/patients", json={"name": padded})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["patient"]["name"], "x" * 120)

        over = "  " + "x" * 121 + "  "
        response = self.client.post("/api/patients", json={"name": over})
        self.assertEqual(response.status_code, 400, response.text)
        self.assertFalse(response.json()["ok"])

    def test_index_form_caps_name_input(self):
        html = self.client.get("/").text
        self.assertIn('id="np-name"', html)
        self.assertIn('maxlength="120"', html)


class WindowsLockResilienceTests(WebLayerTestCase):
    """F1a — transient Windows file locks must not 500, lose writes or escape
    the ``{'ok': false, ...}`` JSON error contract."""

    @staticmethod
    def _flaky_replace(failures=1):
        """Patch ``os.replace`` to raise PermissionError ``failures`` times."""
        real_replace = os.replace
        state = {"left": failures}

        def replace(src, dst, *args, **kwargs):
            if state["left"] > 0:
                state["left"] -= 1
                raise PermissionError("[WinError 32] file is in use by another process")
            return real_replace(src, dst, *args, **kwargs)

        return mock.patch.object(os, "replace", replace), state

    def test_create_patient_retries_one_transient_lock_on_draft_save(self):
        """The create path's first (draft) save is retried too — it used to be
        the plain-text 500 from the review's deterministic repro."""
        patcher, state = self._flaky_replace(failures=1)
        with patcher:
            response = self.client.post("/api/patients", json={"name": "Flaky Draft"})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["ok"])
        self.assertEqual(state["left"], 0, "lock failure was never injected")
        self.assertTrue(self.store.exists(response.json()["patient"]["id"]))

    def test_every_mutation_retries_one_transient_lock(self):
        """begin/complete/skip/redo/measurement/link all survive a one-off lock."""
        patient = self.create_patient()
        pid = patient["id"]
        mutations = [
            ("begin", f"/api/patients/{pid}/begin", {}),
            ("complete", f"/api/patients/{pid}/complete", {}),
            ("measurement", f"/api/patients/{pid}/measurement",
             {"metric": "resting_hr", "value": 55, "unit": "bpm"}),
            ("redo", f"/api/patients/{pid}/redo", {"station_id": "vitals"}),
            ("link", f"/api/patients/{pid}/link",
             {"app": "bertec", "session_id": "sess-lock"}),
            ("skip", f"/api/patients/{pid}/skip", {"reason": "no treadmill today"}),
        ]
        for label, path, payload in mutations:
            with self.subTest(mutation=label):
                patcher, state = self._flaky_replace(failures=1)
                with patcher:
                    response = self.client.post(path, json=payload)
                self.assertEqual(response.status_code, 200, response.text)
                self.assertTrue(response.json()["ok"])
                self.assertEqual(state["left"], 0, "lock failure was never injected")
        view = self.patient_view(pid)
        self.assertEqual(view["progress"]["done"], 3)  # intake, vitals, hrv closed
        self.assertEqual(len(view["patient"]["measurements"]), 1)

    def test_persistent_lock_failure_still_returns_json_not_plain_500(self):
        """After the retries are exhausted the answer is a JSON 503, not an
        HTML/plain-text 500 — on create (draft save) and on a mutation."""

        def always_locked(src, dst, *args, **kwargs):
            raise PermissionError("[WinError 5] access denied")

        with mock.patch.object(os, "replace", always_locked):
            response = self.client.post("/api/patients", json={"name": "Locked Out"})
        self.assertEqual(response.status_code, 503, response.text)
        self.assertEqual(
            response.headers["content-type"].split(";")[0], "application/json"
        )
        body = response.json()
        self.assertFalse(body["ok"])
        self.assertIn("error", body)
        # the failed draft save left nothing behind (no partial/tmp files)
        self.assertEqual(list(self.store.patients_dir.iterdir()), [])

        patient = self.create_patient(name="Locked Later")
        with mock.patch.object(os, "replace", always_locked):
            response = self.client.post(f"/api/patients/{patient['id']}/complete", json={})
        self.assertEqual(response.status_code, 503, response.text)
        self.assertFalse(response.json()["ok"])
        view = self.patient_view(patient["id"])
        self.assertEqual(view["progress"]["done"], 0)  # nothing half-written
        self.assertEqual(view["patient"]["steps"]["intake"]["state"], "pending")


class ConcurrencyRegressionTests(WebLayerTestCase):
    """F1a — hammering one patient from N threads: every response is JSON, no
    writes are lost among ops that returned ``ok: true``, and a double-click
    on one station advances it exactly once with exactly one notification."""

    def _run_threaded(self, calls, timeout=120):
        """Fire all calls from real threads behind a barrier; return responses.

        Any worker exception (or a non-JSON/500 answer that TestClient would
        re-raise) fails the test loudly instead of being swallowed.
        """
        barrier = threading.Barrier(len(calls))
        results = [None] * len(calls)
        errors = [None] * len(calls)

        def worker(index, call):
            try:
                barrier.wait(timeout=30)
                results[index] = call()
            except BaseException as exc:  # pragma: no cover - asserted below
                errors[index] = exc

        threads = [
            threading.Thread(target=worker, args=(index, call))
            for index, call in enumerate(calls)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=timeout)
        self.assertFalse(any(thread.is_alive() for thread in threads), "worker stuck")
        raised = [error for error in errors if error is not None]
        self.assertEqual(raised, [], f"worker raised: {raised!r}")
        return results

    def test_concurrent_complete_skip_measurement_no_lost_writes(self):
        patient = self.create_patient()
        pid = patient["id"]
        metrics = [f"metric-{i}" for i in range(4)]

        def complete():
            return self.client.post(f"/api/patients/{pid}/complete", json={})

        def skip():
            return self.client.post(f"/api/patients/{pid}/skip", json={"reason": "load"})

        calls = [complete] * 8 + [skip] * 4 + [
            (lambda metric=metric: self.client.post(
                f"/api/patients/{pid}/measurement",
                json={"metric": metric, "value": 1, "unit": "u"},
            ))
            for metric in metrics
        ]
        responses = self._run_threaded(calls)

        for response in responses:
            self.assertIn(response.status_code, (200, 409), response.text)
            body = response.json()  # any non-JSON body/500 raises here
            self.assertIsInstance(body.get("ok"), bool)
            self.assertEqual(body["ok"], response.status_code == 200)

        ok_advances = sum(
            1 for r in responses[:12] if r.status_code == 200
        )  # 8 completes + 4 skips contend for the 9 stations
        self.assertEqual(sum(1 for r in responses[12:] if r.status_code == 200), 4)

        view = self.patient_view(pid)
        final = view["patient"]
        recorded = {m["metric"] for m in final["measurements"]}
        self.assertEqual(recorded, set(metrics))  # no ok:true measurement lost
        closed = sum(
            1 for entry in final["steps"].values()
            if entry["state"] in ("done", "skipped")
        )
        self.assertEqual(closed, ok_advances)  # every ok:true advance is durable
        self.assertEqual(closed, 9)  # all 9 stations closed exactly once

        completed = self.notifier.events("step_completed")
        self.assertEqual(len(completed), ok_advances)  # one notification per advance
        self.assertEqual(len(set(completed)), 9)  # no station closed twice
        self.assertEqual(self.notifier.events("flow_completed"), [None])
        self.assertEqual(final["status"], "completed")

        # the file on disk agrees with the API view
        raw = json.loads(
            (self.store.patients_dir / f"{pid}.json").read_text(encoding="utf-8")
        )
        self.assertEqual(len(raw["measurements"]), 4)
        self.assertEqual(raw["status"], "completed")

    def test_concurrent_double_complete_advances_once_notifies_once(self):
        """Idempotency guard: mutations serialise per patient under an
        in-process lock and ``_require_current`` re-validates the client-named
        station against the freshly persisted state — so a fast double "Done"
        click advances exactly one station, fires exactly one
        ``step_completed``, and the second click gets a 409 guard error."""
        patient = self.create_patient()
        pid = patient["id"]
        payload = {"station_id": "intake", "notes": "double-click"}

        def click():
            return self.client.post(f"/api/patients/{pid}/complete", json=payload)

        responses = self._run_threaded([click, click])
        codes = sorted(response.status_code for response in responses)
        self.assertEqual(codes, [200, 409])

        winner = [r for r in responses if r.status_code == 200][0]
        self.assertTrue(winner.json()["ok"])
        guard = [r for r in responses if r.status_code == 409][0].json()
        self.assertFalse(guard["ok"])
        self.assertIn("not the current step", guard["error"])

        view = self.patient_view(pid)
        self.assertEqual(view["patient"]["steps"]["intake"]["state"], "done")
        self.assertEqual(view["progress"]["done"], 1)  # exactly ONE advance
        self.assertEqual(view["next"]["id"], "vitals")

        self.assertEqual(self.notifier.events("step_completed"), ["intake"])
        self.assertEqual(self.notifier.events("flow_completed"), [])

        # a third (sequential) click on the now-stale station stays guarded
        again = self.client.post(f"/api/patients/{pid}/complete", json=payload)
        self.assertEqual(again.status_code, 409)
        self.assertEqual(self.notifier.events("step_completed"), ["intake"])


if __name__ == "__main__":
    unittest.main()
