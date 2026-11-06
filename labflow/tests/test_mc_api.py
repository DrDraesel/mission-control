"""Tests for the Mission Control API (``labflow/mc/api.py``) + chart export.

Everything is synthetic and hermetic: one temp data dir per test, and the
adapters are pointed at empty fixture roots through an injected ``Ingest`` so
no real lab app tree (or patient data) is ever read.

Covered: every documented endpoint (overview, patients, chart, sync, ingest,
inbody, link, integrations, export.html), the 404 for an unknown patient, the
400 for an ingest push without provenance, sync counts, and the export's
disclaimer / provenance rendering.
"""

from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from labflow.app import create_app  # noqa: E402
from labflow.mc.export import DISCLAIMER  # noqa: E402
from labflow.mc.ingest import Ingest  # noqa: E402
from labflow.notify import NullNotifier  # noqa: E402
from labflow.patients import PatientStore  # noqa: E402

SOURCES = ("bertec", "runtrack", "neurosync", "inbody")


class MissionControlApiTest(unittest.TestCase):
    """One app + one temp data dir per test; adapters see only fixture roots."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name)

        self.roots = {source: self.root / "roots" / source for source in SOURCES}
        self.store = PatientStore(self.root)
        # Explicit roots: a sync can never wander into the real lab trees.
        self.ingest = Ingest(store=self.store, data_dir=self.root, roots=self.roots)

        self.app = create_app(
            config={},
            store=self.store,
            notifier=NullNotifier(),
            mc_ingest=self.ingest,
        )
        self.client = TestClient(self.app)

    # -- helpers -----------------------------------------------------------
    def _patient(self, name="Ada Lovelace", dob="1990-01-01"):
        response = self.client.post("/api/patients", json={"name": name, "dob": dob})
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["patient"]

    def _ingest_payload(self, patient_id, **overrides):
        payload = {
            "source": "bertec",
            "session_id": "bertec-session-1",
            "subject_id": patient_id,
            "measured_at": "2026-11-01T09:30:00+00:00",
            "metrics": [
                {"metric": "bertec.asi", "value": 1.42, "unit": "index"},
                {"metric": "bertec.kept_trials", "value": 8, "unit": "count"},
            ],
            "quality": "verified",
            "provenance": {
                "app": "bertec-jump",
                "device": "Bertec force plate",
                "file": "data/protocols/bertec-session-1/session.json",
            },
            "analysis": "CMJ; quality: verified; segments: jump",
            "ai_text": "Consistent landing symmetry.",
            "ai_model": "local-test-model",
        }
        payload.update(overrides)
        return payload

    def _seed_bertec(self, session_id="sess-1", athlete="", quality="incomplete"):
        """Write a synthetic bertec session.json under the fixture root."""
        session_dir = self.roots["bertec"] / "data" / "protocols" / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        session = {
            "id": session_id,
            "protocol_id": "cmj",
            "protocol_label": "Countermovement jump",
            "athlete": athlete,
            "started_at": "2026-11-01T08:00:00",
            "completed_at": "2026-11-01T08:05:00",
            "quality": quality,
            "processing_version": "1.0.0",
            "kept_trials": 5,
            "summary": {
                "jump": {
                    "means": {"asi": 1.11, "peak_force_n": 1500.0},
                    "flag_counts": {},
                    "fall_risk": 0.2,
                }
            },
        }
        (session_dir / "session.json").write_text(json.dumps(session), encoding="utf-8")
        return session

    # -- overview ----------------------------------------------------------
    def test_overview_empty(self):
        response = self.client.get("/api/mc/overview")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["counts"]["patients"], 0)
        self.assertEqual(body["counts"]["observations"], 0)
        self.assertEqual(body["counts"]["unlinked_sessions"], 0)
        self.assertIsNone(body["last_ingest"])
        self.assertEqual(body["disclaimer"], DISCLAIMER)

        integrations = body["integrations"]
        self.assertEqual([item["source"] for item in integrations], list(SOURCES))
        for item in integrations:
            self.assertIn("path", item)
            self.assertIn("reachable", item)
            self.assertIn("sessions", item)
            self.assertIn("last_checked", item)
            self.assertFalse(item["reachable"])
            self.assertIn("hint", item)

    def test_overview_after_ingest(self):
        patient = self._patient()
        response = self.client.post("/api/mc/ingest", json=self._ingest_payload(patient["id"]))
        self.assertEqual(response.status_code, 200, response.text)

        body = self.client.get("/api/mc/overview").json()
        self.assertEqual(body["counts"]["patients"], 1)
        self.assertEqual(body["counts"]["observations"], 2)
        self.assertEqual(body["counts"]["sessions"], 1)
        self.assertEqual(body["counts"]["sources"], {"bertec": 2})
        self.assertIsNotNone(body["last_ingest"])

    # -- patients ----------------------------------------------------------
    def test_patients_list_with_counts(self):
        patient = self._patient()
        self.client.post("/api/mc/ingest", json=self._ingest_payload(patient["id"]))

        response = self.client.get("/api/mc/patients")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["totals"]["patients"], 1)
        entry = body["patients"][0]
        self.assertEqual(entry["id"], patient["id"])
        self.assertEqual(entry["name"], "Ada Lovelace")
        self.assertEqual(entry["dob"], "1990-01-01")
        self.assertEqual(entry["observations"], 2)
        self.assertEqual(entry["sources"], {"bertec": 2})
        self.assertEqual(entry["sessions"], {"bertec": 1})
        self.assertEqual(entry["last_activity"], "2026-11-01T09:30:00+00:00")
        self.assertEqual(body["disclaimer"], DISCLAIMER)

    # -- ingest ------------------------------------------------------------
    def test_ingest_is_idempotent_and_chart_shows_it(self):
        patient = self._patient()
        payload = self._ingest_payload(patient["id"])

        first = self.client.post("/api/mc/ingest", json=payload)
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(first.json()["added"], 2)
        self.assertEqual(first.json()["received"], 2)

        second = self.client.post("/api/mc/ingest", json=payload)
        self.assertEqual(second.status_code, 200, second.text)
        self.assertEqual(second.json()["added"], 0)
        self.assertEqual(second.json()["skipped"], 2)

        # Reads never sync: no adapter ran, the two pushed rows are all there is.
        chart = self.client.get(f"/api/mc/patients/{patient['id']}/chart")
        self.assertEqual(chart.status_code, 200, chart.text)
        body = chart.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["patient"]["name"], "Ada Lovelace")
        self.assertEqual(body["totals"], {"observations": 2, "sessions": 1, "sources": 1})
        self.assertEqual(body["disclaimer"], DISCLAIMER)
        self.assertEqual(len(body["timeline"]), 1)
        timeline = body["timeline"][0]
        self.assertEqual(timeline["source"], "bertec")
        self.assertEqual(timeline["session_id"], "bertec-session-1")
        self.assertEqual(timeline["quality"], "verified")
        self.assertEqual(timeline["ai_model"], "local-test-model")

        latest = {item["metric"]: item for item in body["latest"]}
        self.assertEqual(latest["bertec.asi"]["value"], 1.42)
        self.assertEqual(latest["bertec.asi"]["unit"], "index")

        cards = {card["source"]: card for card in body["sources"]}
        self.assertTrue(cards["bertec"]["available"])
        self.assertEqual(cards["bertec"]["sessions"], 1)
        self.assertFalse(cards["runtrack"]["available"])

    def test_chart_refresh_rebuilds_index(self):
        patient = self._patient()
        self.client.post("/api/mc/ingest", json=self._ingest_payload(patient["id"]))
        response = self.client.get(f"/api/mc/patients/{patient['id']}/chart?refresh=1")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["totals"]["observations"], 2)
        index = self.ingest.load_index()
        self.assertIsNotNone(index)
        self.assertEqual(index["counts"]["observations"], 2)

    def test_ingest_missing_provenance_is_400(self):
        patient = self._patient()
        payload = self._ingest_payload(patient["id"])
        payload.pop("provenance")

        response = self.client.post("/api/mc/ingest", json=payload)
        self.assertEqual(response.status_code, 400, response.text)
        body = response.json()
        self.assertIn("provenance", body["detail"])
        self.assertNotIn("ok", body)  # the documented error shape, not the app envelope

        empty = self._ingest_payload(patient["id"], provenance={})
        again = self.client.post("/api/mc/ingest", json=empty)
        self.assertEqual(again.status_code, 400, again.text)
        self.assertIn("provenance", again.json()["detail"])

    def test_ingest_validation_errors_are_400(self):
        patient = self._patient()
        cases = [
            ("missing source", {"source": ""}),
            ("missing session", {"session_id": ""}),
            ("missing measured_at", {"measured_at": None}),
            ("empty metrics", {"metrics": []}),
            ("bad metric namespace", {"metrics": [{"metric": "runtrack.form_index", "value": 1}]}),
            ("metric without value", {"metrics": [{"metric": "bertec.asi"}]}),
        ]
        for label, override in cases:
            with self.subTest(label):
                response = self.client.post(
                    "/api/mc/ingest", json=self._ingest_payload(patient["id"], **override)
                )
                self.assertEqual(response.status_code, 400, response.text)
                self.assertIn("detail", response.json())

    def test_ingest_rejects_malformed_json_with_400(self):
        response = self.client.post(
            "/api/mc/ingest",
            content="{not json",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 400, response.text)
        self.assertIn("JSON", response.json()["detail"])

    def test_ingest_unknown_subject_is_404(self):
        response = self.client.post("/api/mc/ingest", json=self._ingest_payload("nobody-here"))
        self.assertEqual(response.status_code, 404, response.text)
        self.assertIn("unknown patient", response.json()["detail"])

    def test_ingest_quality_is_never_upgraded(self):
        patient = self._patient()
        self.client.post("/api/mc/ingest", json=self._ingest_payload(patient["id"]))
        downgrade = self._ingest_payload(patient["id"], quality="flagged")
        response = self.client.post("/api/mc/ingest", json=downgrade)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["updated"], 2)

        chart = self.client.get(f"/api/mc/patients/{patient['id']}/chart").json()
        self.assertEqual(chart["timeline"][0]["quality"], "flagged")

    # -- sync --------------------------------------------------------------
    def test_sync_returns_counts_and_carries_quality(self):
        patient = self._patient()
        self._seed_bertec(session_id="sess-1", athlete=patient["id"], quality="incomplete")

        # A read does not run adapters.
        before = self.client.get(f"/api/mc/patients/{patient['id']}/chart").json()
        self.assertEqual(before["totals"]["observations"], 0)

        response = self.client.post(f"/api/mc/patients/{patient['id']}/sync")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["patient_id"], patient["id"])
        # 2 means + kept_trials + quality
        self.assertEqual(body["added"], 4)
        self.assertEqual(body["candidates"], 4)
        self.assertEqual(body["skipped"], 0)
        self.assertEqual(body["sources"]["bertec"]["found"], 4)
        self.assertEqual(body["observations_total"], 4)

        again = self.client.post(f"/api/mc/patients/{patient['id']}/sync").json()
        self.assertEqual(again["added"], 0)
        self.assertEqual(again["skipped"], 4)

        chart = self.client.get(f"/api/mc/patients/{patient['id']}/chart").json()
        self.assertEqual(chart["totals"]["observations"], 4)
        self.assertEqual(chart["timeline"][0]["quality"], "incomplete")
        self.assertEqual(chart["timeline"][0]["source"], "bertec")

    def test_sync_unknown_patient_is_404(self):
        response = self.client.post("/api/mc/patients/ghost/sync")
        self.assertEqual(response.status_code, 404, response.text)

    # -- link --------------------------------------------------------------
    def test_link_attaches_an_unlinked_session(self):
        patient = self._patient()
        self._seed_bertec(session_id="sess-2", athlete="")
        # Seed the unlinked bucket through the real core (the endpoint-only
        # path cannot create unlinked rows: a one-patient sync never flushes
        # the global bucket).
        self.ingest.sync()
        self.assertEqual(len(self.ingest.unlinked()), 1)

        response = self.client.post(
            f"/api/mc/patients/{patient['id']}/link",
            json={"source": "bertec", "session_id": "sess-2"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertTrue(body["removed_from_unlinked"])
        self.assertTrue(body["attached"])
        self.assertFalse(body["still_unlinked"])
        self.assertGreater(body["added"], 0)
        self.assertEqual(self.ingest.unlinked(), [])

        chart = self.client.get(f"/api/mc/patients/{patient['id']}/chart").json()
        self.assertEqual(chart["totals"]["sessions"], 1)
        self.assertEqual(chart["timeline"][0]["session_id"], "sess-2")

    def test_link_validation(self):
        patient = self._patient()
        for label, payload in (
            ("no source", {"session_id": "x"}),
            ("no session", {"source": "bertec"}),
            ("unknown source", {"source": "fax", "session_id": "x"}),
        ):
            with self.subTest(label):
                response = self.client.post(
                    f"/api/mc/patients/{patient['id']}/link", json=payload
                )
                self.assertEqual(response.status_code, 400, response.text)
                self.assertIn("detail", response.json())

        missing = self.client.post("/api/mc/patients/ghost/link", json={"source": "bertec", "session_id": "x"})
        self.assertEqual(missing.status_code, 404, missing.text)

    def test_link_accepts_link_id_alias(self):
        """InBody links by its own patient id; the API must accept that key."""
        patient = self._patient()
        self._seed_bertec(session_id="sess-3", athlete="")
        self.ingest.sync()
        response = self.client.post(
            f"/api/mc/patients/{patient['id']}/link",
            json={"source": "bertec", "link_id": "sess-3"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertTrue(response.json()["attached"])

    def test_integrations_marks_inbody_database_reachable(self):
        import os
        import tempfile
        from unittest import mock

        with tempfile.TemporaryDirectory() as tmp:
            db = os.path.join(tmp, "inbody.db")
            with open(db, "wb") as handle:
                handle.write(b"")
            with mock.patch.dict(os.environ, {"INBODY_DB": db}, clear=False):
                payload = self.client.get("/api/mc/integrations").json()
                rows = {r["source"]: r for r in payload["integrations"]}
        inbody = rows["inbody"]
        self.assertTrue(inbody["reachable"], inbody)
        self.assertEqual(inbody["mode"], "sqlite (read-only)")
        self.assertEqual(inbody["path"], db)


    # -- inbody manual entry ----------------------------------------------
    def test_inbody_manual_entry(self):
        patient = self._patient()
        response = self.client.post(
            f"/api/mc/patients/{patient['id']}/inbody",
            json={
                "measured_at": "2026-11-02T07:15:00+00:00",
                "weight_kg": 70.5,
                "body_fat_pct": 18.2,
                "entered_by": "front desk",
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["quality"], "unverified")
        self.assertEqual(body["added"], 2)
        self.assertIn("verify against the device printout", body["note"])

        chart = self.client.get(f"/api/mc/patients/{patient['id']}/chart").json()
        latest = {item["metric"]: item for item in chart["latest"]}
        self.assertEqual(latest["body.weight_kg"]["value"], 70.5)
        self.assertEqual(latest["body.body_fat_pct"]["quality"], "unverified")

        # A transcribed serial is provenance-only verification, never a claim.
        serial = self.client.post(
            f"/api/mc/patients/{patient['id']}/inbody",
            json={
                "measured_at": "2026-11-03T07:15:00+00:00",
                "values": {"weight_kg": 70.9},
                "device_serial": "INB-1234",
            },
        )
        self.assertEqual(serial.status_code, 200, serial.text)
        self.assertEqual(serial.json()["quality"], "verified")

    def test_inbody_validation(self):
        patient = self._patient()
        empty = self.client.post(f"/api/mc/patients/{patient['id']}/inbody", json={})
        self.assertEqual(empty.status_code, 400, empty.text)
        self.assertIn("detail", empty.json())

        bad_time = self.client.post(
            f"/api/mc/patients/{patient['id']}/inbody",
            json={"measured_at": "not-a-date", "weight_kg": 70},
        )
        self.assertEqual(bad_time.status_code, 400, bad_time.text)

        ghost = self.client.post("/api/mc/patients/ghost/inbody", json={"weight_kg": 70})
        self.assertEqual(ghost.status_code, 404, ghost.text)

    # -- integrations ------------------------------------------------------
    def test_integrations_reports_paths_and_reachability(self):
        self._seed_bertec(session_id="sess-3", athlete="")
        self.roots["inbody"].mkdir(parents=True, exist_ok=True)

        response = self.client.get("/api/mc/integrations")
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["disclaimer"], DISCLAIMER)
        self.assertIn("checked_at", body)

        by_source = {item["source"]: item for item in body["integrations"]}
        self.assertEqual(set(by_source), set(SOURCES))
        self.assertTrue(by_source["bertec"]["reachable"])
        self.assertTrue(by_source["bertec"]["path"].endswith("protocols"))
        self.assertTrue(by_source["inbody"]["reachable"])
        self.assertFalse(by_source["runtrack"]["reachable"])
        for item in by_source.values():
            self.assertIn("last_checked", item)

    # -- export ------------------------------------------------------------
    def test_export_html_contains_disclaimer_and_patient_name(self):
        patient = self._patient()
        self.client.post("/api/mc/ingest", json=self._ingest_payload(patient["id"]))

        response = self.client.get(f"/api/mc/patients/{patient['id']}/export.html")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("inline", response.headers["content-disposition"])
        self.assertIn(patient["id"], response.headers["content-disposition"])

        document = response.text
        self.assertIn(DISCLAIMER, document)
        self.assertIn("Ada Lovelace", document)
        self.assertIn("bertec.asi", document)
        self.assertIn("1.42", document)
        # Provenance of every number: session id + file locator.
        self.assertIn("bertec-session-1", document)
        self.assertIn("data/protocols/bertec-session-1/session.json", document)
        # Self-contained: no external scripts, styles or images.
        self.assertNotIn("<script", document.lower())
        self.assertNotIn('src="http', document)
        self.assertNotIn('href="http', document)
        self.assertIn("<style>", document)

    def test_export_unknown_patient_is_404(self):
        response = self.client.get("/api/mc/patients/ghost/export.html")
        self.assertEqual(response.status_code, 404, response.text)
        self.assertIn("detail", response.json())

    def test_export_with_no_observations_still_carries_disclaimer(self):
        patient = self._patient()
        response = self.client.get(f"/api/mc/patients/{patient['id']}/export.html")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn(DISCLAIMER, response.text)
        self.assertIn("Ada Lovelace", response.text)
        self.assertIn("No observations recorded", response.text)

    def test_export_escapes_patient_text(self):
        patient = self._patient(name="<script>alert(1)</script>")
        response = self.client.get(f"/api/mc/patients/{patient['id']}/export.html")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertNotIn("<script>alert(1)</script>", response.text)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", response.text)

    # -- 404 coverage ------------------------------------------------------
    def test_unknown_patient_is_404_on_every_patient_route(self):
        for method, path, payload in (
            ("get", "/api/mc/patients/ghost/chart", None),
            ("post", "/api/mc/patients/ghost/sync", None),
            ("post", "/api/mc/patients/ghost/inbody", {"weight_kg": 70}),
            ("post", "/api/mc/patients/ghost/link", {"source": "bertec", "session_id": "x"}),
            ("get", "/api/mc/patients/ghost/export.html", None),
        ):
            with self.subTest(path):
                if payload is None:
                    response = getattr(self.client, method)(path)
                else:
                    response = getattr(self.client, method)(path, json=payload)
                self.assertEqual(response.status_code, 404, response.text)
                self.assertIn("detail", response.json())

    def test_all_documented_routes_are_mounted(self):
        routes = set(self.app.openapi()["paths"])
        expected = {
            "/api/mc/overview",
            "/api/mc/patients",
            "/api/mc/patients/{patient_id}/chart",
            "/api/mc/patients/{patient_id}/sync",
            "/api/mc/ingest",
            "/api/mc/patients/{patient_id}/inbody",
            "/api/mc/patients/{patient_id}/link",
            "/api/mc/integrations",
            "/api/mc/patients/{patient_id}/export.html",
            "/mc",
            "/mc/patient/{patient_id}",
            "/mc/integrations",
            "/mc/inbody",
        }
        self.assertTrue(expected.issubset(routes), sorted(expected - routes))


if __name__ == "__main__":
    unittest.main()
