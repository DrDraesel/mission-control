"""Tests for labflow.engine — full walkthrough, progress, notifications."""

from __future__ import annotations

import contextlib
import io
import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from labflow.engine import CLOSED_STATES, FlowEngine  # noqa: E402
from labflow.notify import Notifier, NullNotifier  # noqa: E402
from labflow.patients import PatientStore, utc_now_iso  # noqa: E402
from labflow.workflow import DEFAULT_WORKFLOW  # noqa: E402

ORDERED_IDS = [station.id for station in DEFAULT_WORKFLOW.ordered_stations()]


class RecordingNotifier(Notifier):
    """Notifier double that records every callback (no network, no output)."""

    kind = "recording"

    def __init__(self):
        self.calls = []

    def _record(self, event, patient, station=None, next_station=None):
        self.calls.append({
            "event": event,
            "patient": patient.get("id") if isinstance(patient, dict) else None,
            "station": station.id if station is not None else None,
            "next": next_station.id if next_station is not None else None,
        })
        return True

    def step_started(self, patient, station, next_station=None):
        return self._record("step_started", patient, station, next_station)

    def step_completed(self, patient, station, next_station=None):
        return self._record("step_completed", patient, station, next_station)

    def flow_completed(self, patient):
        return self._record("flow_completed", patient)

    def reminder(self, patient, current_station=None):
        return self._record("reminder", patient, current_station)

    def events(self):
        return [call["event"] for call in self.calls]


class ExplodingNotifier(Notifier):
    """Every callback raises — the engine must survive it."""

    def step_started(self, patient, station, next_station=None):
        raise RuntimeError("boom-started")

    def step_completed(self, patient, station, next_station=None):
        raise RuntimeError("boom-completed")

    def flow_completed(self, patient):
        raise RuntimeError("boom-flow")

    def reminder(self, patient, current_station=None):
        raise RuntimeError("boom-reminder")


class EngineTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.store = PatientStore(self._tmp.name)
        self.workflow = DEFAULT_WORKFLOW
        self.notifier = RecordingNotifier()
        self.engine = FlowEngine(self.store, self.workflow, self.notifier)
        self.patient = self.store.create("Jane Doe")
        self.pid = self.patient["id"]

    def tearDown(self):
        self._tmp.cleanup()

    def patient_now(self):
        return self.store.get(self.pid)

    def advance_to(self, target_id):
        """Run stations (begin+complete) until ``target_id`` is the current one."""
        while True:
            current = self.engine.current_step(self.patient_now())
            if current is None or current.id == target_id:
                return current
            self.engine.begin_step(self.pid)
            self.engine.complete_step(self.pid)

    def walk_to_end(self, limit=50):
        steps = 0
        while self.engine.current_step(self.patient_now()) is not None and steps < limit:
            self.engine.begin_step(self.pid)
            self.engine.complete_step(self.pid)
            steps += 1
        return steps


class StartPatientTests(EngineTestCase):
    def test_initialises_all_stations_pending_in_ordered_order(self):
        started = self.engine.start_patient(self.pid)
        self.assertEqual(list(started["steps"].keys()), ORDERED_IDS)
        for entry in started["steps"].values():
            self.assertEqual(entry["state"], "pending")
            self.assertIsNone(entry["started_at"])
            self.assertIsNone(entry["completed_at"])
            self.assertEqual(entry["notes"], "")
            self.assertEqual(entry["results"], [])

    def test_sets_status_active(self):
        self.assertEqual(self.patient["status"], "draft")
        started = self.engine.start_patient(self.pid)
        self.assertEqual(started["status"], "active")
        self.assertEqual(self.patient_now()["status"], "active")

    def test_is_idempotent_and_keeps_existing_progress(self):
        self.engine.start_patient(self.pid)
        self.engine.begin_step(self.pid)
        self.engine.complete_step(self.pid)
        again = self.engine.start_patient(self.pid)
        self.assertEqual(again["steps"]["intake"]["state"], "done")
        self.assertEqual(list(again["steps"].keys()), ORDERED_IDS)

    def test_unknown_patient_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.engine.start_patient("nobody-0000")


class StepNavigationTests(EngineTestCase):
    def test_current_step_is_intake_even_before_start(self):
        current = self.engine.current_step(self.patient_now())
        self.assertEqual(current.id, "intake")

    def test_current_step_walks_the_ordered_list(self):
        self.engine.start_patient(self.pid)
        for expected in ORDERED_IDS:
            current = self.engine.current_step(self.patient_now())
            self.assertEqual(current.id, expected)
            self.engine.begin_step(self.pid)
            self.engine.complete_step(self.pid)
        self.assertIsNone(self.engine.current_step(self.patient_now()))

    def test_begin_step_marks_in_progress_and_notifies(self):
        self.engine.start_patient(self.pid)
        self.engine.begin_step(self.pid)
        entry = self.patient_now()["steps"]["intake"]
        self.assertEqual(entry["state"], "in_progress")
        self.assertIsNotNone(entry["started_at"])
        self.assertEqual(
            self.notifier.calls[0],
            {"event": "step_started", "patient": self.pid, "station": "intake", "next": "vitals"},
        )

    def test_begin_step_keeps_first_started_at(self):
        self.engine.start_patient(self.pid)
        self.engine.begin_step(self.pid)
        first = self.patient_now()["steps"]["intake"]["started_at"]
        self.engine.begin_step(self.pid)
        self.assertEqual(self.patient_now()["steps"]["intake"]["started_at"], first)

    def test_begin_step_after_completion_returns_none(self):
        self.engine.start_patient(self.pid)
        self.walk_to_end()
        self.assertIsNone(self.engine.begin_step(self.pid))
        self.assertIsNone(self.engine.complete_step(self.pid))
        self.assertIsNone(self.engine.skip_step(self.pid, "nothing left"))

    def test_unknown_patient_raises_everywhere(self):
        for call in (
            lambda: self.engine.begin_step("nobody-0000"),
            lambda: self.engine.complete_step("nobody-0000"),
            lambda: self.engine.skip_step("nobody-0000", "x"),
            lambda: self.engine.redo_step("nobody-0000", "intake"),
        ):
            with self.assertRaises(KeyError):
                call()
        # a never-started patient (no steps at all) is 'at' the first station
        self.assertEqual(self.engine.current_step({}).id, "intake")

    def test_current_step_none_when_all_closed(self):
        self.engine.start_patient(self.pid)
        self.walk_to_end()
        self.assertIsNone(self.engine.current_step(self.patient_now()))
        self.assertEqual(CLOSED_STATES, ("done", "skipped"))


class CompleteStepTests(EngineTestCase):
    def test_complete_marks_done_and_notifies_next(self):
        self.engine.start_patient(self.pid)
        self.engine.begin_step(self.pid)
        self.notifier.calls.clear()
        self.engine.complete_step(self.pid)
        entry = self.patient_now()["steps"]["intake"]
        self.assertEqual(entry["state"], "done")
        self.assertIsNotNone(entry["completed_at"])
        self.assertEqual(self.notifier.calls, [
            {"event": "step_completed", "patient": self.pid, "station": "intake", "next": "vitals"},
        ])

    def test_complete_stores_notes_and_results(self):
        self.engine.start_patient(self.pid)
        self.engine.complete_step(self.pid, notes="all good", results=[{"consent": True}])
        entry = self.patient_now()["steps"]["intake"]
        self.assertEqual(entry["notes"], "all good")
        self.assertEqual(entry["results"], [{"consent": True}])

    def test_complete_accepts_a_single_result_item(self):
        self.engine.start_patient(self.pid)
        self.engine.complete_step(self.pid, results={"hr": 60})
        self.assertEqual(self.patient_now()["steps"]["intake"]["results"], [{"hr": 60}])

    def test_complete_without_begin_sets_started_at(self):
        self.engine.start_patient(self.pid)
        self.engine.complete_step(self.pid)
        entry = self.patient_now()["steps"]["intake"]
        self.assertIsNotNone(entry["started_at"])
        self.assertIsNotNone(entry["completed_at"])

    def test_full_walkthrough_notifies_flow_completed_once(self):
        self.engine.start_patient(self.pid)
        done = self.walk_to_end()
        self.assertEqual(done, len(ORDERED_IDS))
        events = self.notifier.events()
        self.assertEqual(events.count("step_started"), len(ORDERED_IDS))
        self.assertEqual(events.count("step_completed"), len(ORDERED_IDS))
        self.assertEqual(events.count("flow_completed"), 1)
        self.assertEqual(events[-2:], ["step_completed", "flow_completed"])
        final_step_completed = [c for c in self.notifier.calls if c["event"] == "step_completed"][-1]
        self.assertIsNone(final_step_completed["next"])
        self.assertEqual(final_step_completed["station"], "treadmill_form")

    def test_full_walkthrough_progress_and_status(self):
        self.engine.start_patient(self.pid)
        self.walk_to_end()
        patient = self.patient_now()
        self.assertEqual(patient["status"], "completed")
        self.assertEqual(self.engine.progress(patient),
                         {"done": len(ORDERED_IDS), "total": len(ORDERED_IDS), "pct": 100, "current": None})
        self.assertTrue(all(patient["steps"][sid]["state"] == "done" for sid in ORDERED_IDS))

    def test_state_persisted_through_the_store(self):
        self.engine.start_patient(self.pid)
        self.engine.begin_step(self.pid)
        self.engine.complete_step(self.pid, notes="persisted", results=[1])
        fresh_engine = FlowEngine(PatientStore(self._tmp.name), DEFAULT_WORKFLOW, NullNotifier())
        patient = fresh_engine.store.get(self.pid)
        self.assertEqual(patient["steps"]["intake"]["notes"], "persisted")
        self.assertEqual(fresh_engine.current_step(patient).id, "vitals")


class SkipAndRedoTests(EngineTestCase):
    def test_skip_marks_skipped_and_advances(self):
        self.engine.start_patient(self.pid)
        self.notifier.calls.clear()
        self.engine.skip_step(self.pid, "patient declined")
        entry = self.patient_now()["steps"]["intake"]
        self.assertEqual(entry["state"], "skipped")
        self.assertIn("patient declined", entry["notes"])
        self.assertIsNotNone(entry["completed_at"])
        self.assertEqual(self.engine.current_step(self.patient_now()).id, "vitals")
        self.assertEqual(self.notifier.calls, [
            {"event": "step_completed", "patient": self.pid, "station": "intake", "next": "vitals"},
        ])

    def test_skipped_station_counts_as_done_in_progress(self):
        self.engine.start_patient(self.pid)
        self.engine.skip_step(self.pid, "no show")
        progress = self.engine.progress(self.patient_now())
        self.assertEqual(progress["done"], 1)
        self.assertEqual(progress["pct"], 11)  # floor(1 / 9 * 100)
        self.assertEqual(progress["current"], "vitals")

    def test_skip_without_reason_still_records_note(self):
        self.engine.start_patient(self.pid)
        self.engine.skip_step(self.pid)
        self.assertEqual(self.patient_now()["steps"]["intake"]["notes"], "Skipped.")

    def test_skip_last_station_completes_the_flow(self):
        self.engine.start_patient(self.pid)
        self.advance_to("treadmill_form")
        self.notifier.calls.clear()
        self.engine.skip_step(self.pid, "treadmill unavailable")
        self.assertEqual(self.notifier.events(), ["step_completed", "flow_completed"])
        self.assertEqual(self.patient_now()["status"], "completed")
        self.assertEqual(self.engine.progress(self.patient_now())["pct"], 100)

    def test_redo_resets_station_and_notifies_reminder(self):
        self.engine.start_patient(self.pid)
        self.engine.begin_step(self.pid)
        self.engine.complete_step(self.pid)
        self.notifier.calls.clear()
        self.engine.redo_step(self.pid, "intake")
        entry = self.patient_now()["steps"]["intake"]
        self.assertEqual(entry["state"], "pending")
        self.assertIsNone(entry["started_at"])
        self.assertIsNone(entry["completed_at"])
        self.assertIn("Redo requested", entry["notes"])
        self.assertEqual(self.engine.current_step(self.patient_now()).id, "intake")
        self.assertEqual(self.notifier.calls[-1]["event"], "reminder")
        self.assertEqual(self.notifier.calls[-1]["station"], "intake")

    def test_redo_keeps_captured_results(self):
        self.engine.start_patient(self.pid)
        self.engine.complete_step(self.pid, results=[{"weight_kg": 82}])
        self.engine.redo_step(self.pid, "intake")
        self.assertEqual(self.patient_now()["steps"]["intake"]["results"], [{"weight_kg": 82}])

    def test_redo_reopens_a_completed_flow(self):
        self.engine.start_patient(self.pid)
        self.walk_to_end()
        self.engine.redo_step(self.pid, "balance")
        patient = self.patient_now()
        self.assertEqual(patient["status"], "active")
        self.assertEqual(self.engine.current_step(patient).id, "balance")
        self.assertEqual(self.engine.progress(patient)["current"], "balance")

    def test_redo_unknown_station_raises(self):
        self.engine.start_patient(self.pid)
        with self.assertRaises(KeyError):
            self.engine.redo_step(self.pid, "not-a-station")


class InstructionAndProgressTests(EngineTestCase):
    def test_next_instruction_for_intake(self):
        self.engine.start_patient(self.pid)
        text = self.engine.next_instruction(self.patient_now())
        self.assertIn("Intake & Consent", text)
        self.assertIn("15 min", text)
        self.assertIn("consent", text.lower())
        self.assertIn("Manual: tablet intake form", text)
        self.assertIn("Enter: full_name", text)

    def test_next_instruction_for_eeg(self):
        self.engine.start_patient(self.pid)
        self.advance_to("eeg_baseline")
        text = self.engine.next_instruction(self.patient_now())
        self.assertIn("EEG Baseline", text)
        self.assertIn("Run: neurosync record", text)
        self.assertIn("neurosync recordings", text)
        self.assertIn("20 min", text)

    def test_next_instruction_for_balance(self):
        self.engine.start_patient(self.pid)
        self.advance_to("balance")
        text = self.engine.next_instruction(self.patient_now())
        self.assertIn("Balance Battery", text)
        self.assertIn("http://127.0.0.1:8765", text)
        self.assertIn("bertec protocol sessions", text)
        self.assertIn("25 min", text)

    def test_next_instruction_when_complete(self):
        self.engine.start_patient(self.pid)
        self.walk_to_end()
        text = self.engine.next_instruction(self.patient_now())
        self.assertIn("complete", text.lower())

    def test_progress_values(self):
        self.engine.start_patient(self.pid)
        self.assertEqual(self.engine.progress(self.patient_now()),
                         {"done": 0, "total": 9, "pct": 0, "current": "intake"})
        for _ in range(4):
            self.engine.begin_step(self.pid)
            self.engine.complete_step(self.pid)
        progress = self.engine.progress(self.patient_now())
        self.assertEqual(progress, {"done": 4, "total": 9, "pct": 44, "current": "blood_panels"})
        self.walk_to_end()
        self.assertEqual(self.engine.progress(self.patient_now())["pct"], 100)


class NotifierRobustnessTests(EngineTestCase):
    def test_engine_without_notifier_is_silent(self):
        engine = FlowEngine(self.store, self.workflow)
        self.assertIsInstance(engine.notifier, NullNotifier)
        engine.start_patient(self.pid)
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            while engine.current_step(self.store.get(self.pid)) is not None:
                engine.begin_step(self.pid)
                engine.complete_step(self.pid)
        self.assertEqual(buffer.getvalue(), "")

    def test_exploding_notifier_never_breaks_the_flow(self):
        engine = FlowEngine(self.store, self.workflow, ExplodingNotifier())
        engine.start_patient(self.pid)
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            engine.begin_step(self.pid)
            engine.complete_step(self.pid)
            engine.redo_step(self.pid, "intake")
            engine.skip_step(self.pid, "why not")
        self.assertIn("notifier error", errors.getvalue())
        self.assertEqual(self.store.get(self.pid)["steps"]["intake"]["state"], "skipped")

    def test_notifier_without_expected_method_is_tolerated(self):
        class Minimal:
            pass

        engine = FlowEngine(self.store, self.workflow, Minimal())
        engine.start_patient(self.pid)
        engine.begin_step(self.pid)  # must not raise
        self.assertEqual(self.store.get(self.pid)["steps"]["intake"]["state"], "in_progress")


if __name__ == "__main__":
    unittest.main()
