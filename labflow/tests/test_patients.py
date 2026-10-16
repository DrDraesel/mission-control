"""Tests for labflow.patients — CRUD, atomic writes, guards."""

from __future__ import annotations

import json
import pathlib
import re
import sys
import tempfile
import unittest
import unittest.mock as mock
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from labflow.patients import PATIENT_STATUSES, STEP_STATES, PatientStore, utc_now_iso  # noqa: E402


class PatientStoreTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.store = PatientStore(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def tmp_files(self):
        return sorted(p.name for p in self.store.patients_dir.iterdir())


class CreateTests(PatientStoreTestCase):
    def test_root_layout_and_first_patient(self):
        self.assertTrue((self.root / "patients").is_dir())
        patient = self.store.create("Jane Doe")
        self.assertEqual(patient["name"], "Jane Doe")
        self.assertEqual(patient["status"], "draft")
        self.assertEqual(patient["intake"], {})
        self.assertEqual(patient["steps"], {})
        self.assertEqual(patient["measurements"], [])
        self.assertEqual(patient["linked_sessions"], {})
        self.assertNotIn("dob", patient)
        self.assertNotIn("contact", patient)
        self.assertEqual(self.tmp_files(), [f"{patient['id']}.json"])

    def test_id_is_slug_plus_4_hex(self):
        patient = self.store.create("Jane Doe")
        self.assertRegex(patient["id"], re.compile(r"^jane-doe-[0-9a-f]{4}$"))

    def test_slug_normalises_symbols_and_unicode(self):
        patient = self.store.create("  Anna  Müller / Test #7 ")
        self.assertRegex(patient["id"], re.compile(r"^anna-m-ller-test-7-[0-9a-f]{4}$"))

    def test_create_requires_a_name(self):
        with self.assertRaises(ValueError):
            self.store.create("   ")

    def test_create_with_intake_dob_contact(self):
        patient = self.store.create("Jane Doe", intake={"consent_signed": True},
                                    dob="1990-01-01", contact="jane@example.com")
        reloaded = self.store.get(patient["id"])
        self.assertEqual(reloaded["intake"], {"consent_signed": True})
        self.assertEqual(reloaded["dob"], "1990-01-01")
        self.assertEqual(reloaded["contact"], "jane@example.com")

    def test_intake_dict_is_copied_not_aliased(self):
        intake = {"a": 1}
        patient = self.store.create("Jane Doe", intake=intake)
        intake["a"] = 2
        self.assertEqual(patient["intake"], {"a": 1})

    def test_duplicate_id_guard_retries(self):
        with mock.patch("labflow.patients.secrets.token_hex",
                        side_effect=["aaaa", "aaaa", "bbbb", "cccc"]):
            first = self.store.create("Jane Doe")
            second = self.store.create("Jane Doe")
        self.assertEqual(first["id"], "jane-doe-aaaa")
        self.assertEqual(second["id"], "jane-doe-bbbb")
        self.assertEqual(self.store.count(), 2)

    def test_created_at_is_iso_utc(self):
        patient = self.store.create("Jane Doe")
        parsed = datetime.fromisoformat(patient["created_at"])
        self.assertIsNotNone(parsed.tzinfo)
        self.assertLessEqual(abs(parsed.utcoffset().total_seconds()), 1)


class GetListTests(PatientStoreTestCase):
    def test_get_roundtrip(self):
        patient = self.store.create("Jane Doe")
        self.assertEqual(self.store.get(patient["id"]), patient)

    def test_get_unknown_returns_none(self):
        self.assertIsNone(self.store.get("nobody-0000"))
        self.assertIsNone(self.store.get(""))
        self.assertIsNone(self.store.get(None))

    def test_get_rejects_unsafe_ids(self):
        self.assertIsNone(self.store.get("../../etc/passwd"))
        self.assertIsNone(self.store.get("a/b"))
        self.assertIsNone(self.store.get("Jane Doe"))

    def test_list_is_newest_first(self):
        first = self.store.create("First Person")
        second = self.store.create("Second Person")
        ids = [p["id"] for p in self.store.list()]
        self.assertEqual(ids, [second["id"], first["id"]])

    def test_list_empty_is_empty(self):
        self.assertEqual(self.store.list(), [])

    def test_list_skips_corrupt_files(self):
        patient = self.store.create("Jane Doe")
        (self.store.patients_dir / "broken.json").write_text("{not json", encoding="utf-8")
        self.assertEqual([p["id"] for p in self.store.list()], [patient["id"]])

    def test_exists_and_count(self):
        self.assertFalse(self.store.exists("nobody-0000"))
        patient = self.store.create("Jane Doe")
        self.assertTrue(self.store.exists(patient["id"]))
        self.assertEqual(self.store.count(), 1)


class SaveTests(PatientStoreTestCase):
    def test_save_is_atomic_and_leaves_no_tmp_files(self):
        patient = self.store.create("Jane Doe")
        patient["intake"] = {"weight_recorded": True}
        self.store.save(patient)
        self.assertEqual(self.tmp_files(), [f"{patient['id']}.json"])
        on_disk = json.loads((self.store.patients_dir / f"{patient['id']}.json").read_text(encoding="utf-8"))
        self.assertEqual(on_disk["intake"], {"weight_recorded": True})

    def test_save_overwrites_existing_file(self):
        patient = self.store.create("Jane Doe")
        patient["status"] = "active"
        self.store.save(patient)
        patient["status"] = "completed"
        self.store.save(patient)
        self.assertEqual(self.store.get(patient["id"])["status"], "completed")

    def test_interrupted_save_keeps_original_content(self):
        patient = self.store.create("Jane Doe")
        patient["intake"] = {"changed": True}
        with mock.patch("labflow.patients.json.dumps", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError):
                self.store.save(patient)
        self.assertEqual(self.store.get(patient["id"])["intake"], {})
        self.assertEqual([n for n in self.tmp_files() if n.endswith(".tmp")], [])

    def test_replace_failure_cleans_up_tmp_file(self):
        patient = self.store.create("Jane Doe")
        patient["intake"] = {"changed": True}
        with mock.patch("labflow.patients.os.replace", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.store.save(patient)
        self.assertEqual([n for n in self.tmp_files() if n.endswith(".tmp")], [])
        self.assertEqual(self.store.get(patient["id"])["intake"], {})

    def test_save_rejects_invalid_id_and_non_dict(self):
        with self.assertRaises(ValueError):
            self.store.save({"id": "../evil", "name": "X"})
        with self.assertRaises(ValueError):
            self.store.save("not a dict")

    def test_save_requires_a_name(self):
        patient = self.store.create("Jane Doe")
        patient["name"] = "  "
        with self.assertRaises(ValueError):
            self.store.save(patient)


class UpdateStepTests(PatientStoreTestCase):
    def test_update_step_creates_entry_and_sets_fields(self):
        patient = self.store.create("Jane Doe")
        updated = self.store.update_step(patient["id"], "vitals", state="in_progress",
                                         started_at=utc_now_iso(), notes="go")
        entry = updated["steps"]["vitals"]
        self.assertEqual(entry["state"], "in_progress")
        self.assertEqual(entry["notes"], "go")
        self.assertEqual(entry["results"], [])
        self.assertIsNone(entry["completed_at"])
        self.assertEqual(self.store.get(patient["id"])["steps"]["vitals"]["notes"], "go")

    def test_update_step_preserves_other_fields(self):
        patient = self.store.create("Jane Doe")
        self.store.update_step(patient["id"], "vitals", state="in_progress", results=[{"hr": 61}])
        updated = self.store.update_step(patient["id"], "vitals", state="done")
        self.assertEqual(updated["steps"]["vitals"]["results"], [{"hr": 61}])

    def test_update_step_unknown_patient_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.store.update_step("nobody-0000", "vitals", state="done")

    def test_update_step_rejects_unknown_state(self):
        patient = self.store.create("Jane Doe")
        with self.assertRaises(ValueError):
            self.store.update_step(patient["id"], "vitals", state="sleeping")

    def test_step_states_constant(self):
        self.assertEqual(STEP_STATES, ("pending", "in_progress", "done", "skipped"))


class MeasurementAndSessionTests(PatientStoreTestCase):
    def test_add_measurement_appends_with_ts(self):
        patient = self.store.create("Jane Doe")
        self.store.add_measurement(patient["id"], "weight_kg", 82.4, "kg", "inbody")
        updated = self.store.add_measurement(patient["id"], "spo2_pct", 98, "%", "vitals")
        measurements = updated["measurements"]
        self.assertEqual(len(measurements), 2)
        self.assertEqual(measurements[0]["metric"], "weight_kg")
        self.assertEqual(measurements[0]["value"], 82.4)
        self.assertEqual(measurements[0]["unit"], "kg")
        self.assertEqual(measurements[0]["source"], "inbody")
        self.assertIn("ts", measurements[0])
        datetime.fromisoformat(measurements[1]["ts"])

    def test_add_measurement_unknown_patient_raises(self):
        with self.assertRaises(KeyError):
            self.store.add_measurement("nobody-0000", "weight_kg", 1, "kg", "inbody")

    def test_add_measurement_requires_metric(self):
        patient = self.store.create("Jane Doe")
        with self.assertRaises(ValueError):
            self.store.add_measurement(patient["id"], "", 1, "kg", "inbody")

    def test_link_session_groups_by_app_and_dedupes(self):
        patient = self.store.create("Jane Doe")
        self.store.link_session(patient["id"], "bertec", "s-1")
        self.store.link_session(patient["id"], "bertec", "s-1")
        updated = self.store.link_session(patient["id"], "runtrack", "42")
        self.assertEqual(updated["linked_sessions"],
                         {"bertec": {"ids": ["s-1"]}, "runtrack": {"ids": ["42"]}})

    def test_link_session_validates_inputs(self):
        patient = self.store.create("Jane Doe")
        with self.assertRaises(ValueError):
            self.store.link_session(patient["id"], "", "s-1")
        with self.assertRaises(ValueError):
            self.store.link_session(patient["id"], "bertec", "")
        with self.assertRaises(KeyError):
            self.store.link_session("nobody-0000", "bertec", "s-1")


class DeleteAndStatusTests(PatientStoreTestCase):
    def test_delete_requires_confirm_flag(self):
        patient = self.store.create("Jane Doe")
        with self.assertRaises(ValueError):
            self.store.delete(patient["id"])
        self.assertTrue(self.store.exists(patient["id"]))

    def test_delete_removes_the_file(self):
        patient = self.store.create("Jane Doe")
        self.assertTrue(self.store.delete(patient["id"], confirm=True))
        self.assertIsNone(self.store.get(patient["id"]))
        self.assertFalse(self.store.delete(patient["id"], confirm=True))

    def test_delete_unknown_id_returns_false(self):
        self.assertFalse(self.store.delete("nobody-0000", confirm=True))

    def test_set_status_validates_and_persists(self):
        patient = self.store.create("Jane Doe")
        updated = self.store.set_status(patient["id"], "active")
        self.assertEqual(updated["status"], "active")
        self.assertEqual(self.store.get(patient["id"])["status"], "active")
        with self.assertRaises(ValueError):
            self.store.set_status(patient["id"], "zombie")

    def test_status_constant(self):
        self.assertEqual(PATIENT_STATUSES, ("active", "completed", "draft"))


if __name__ == "__main__":
    unittest.main()
