"""Tests for the Mission Control core — schema, adapters, ingest, chart.

Everything is synthetic and built in a temp directory: no real patient data, no
real app directories.  The fixtures mirror the shapes the apps actually write
(verified against ``bertec-jump``, ``runtrack`` and ``neurosync``), with made-up
numbers.
"""

from __future__ import annotations

import json
import math
import os
import pathlib
import sqlite3
import sys
import tempfile
import unittest
import unittest.mock

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from labflow.mc import (  # noqa: E402
    DISCLAIMER,
    Ingest,
    Observation,
    build_chart,
    dedupe_key,
    normalize_quality,
    normalize_timestamp,
)
from labflow.mc.adapters import (  # noqa: E402
    ADAPTERS,
    AdapterContext,
    build_context,
    collect_all,
    default_roots,
    project_root,
)
from labflow.mc.adapters import bertec, inbody, intake, neurosync, runtrack  # noqa: E402
from labflow.patients import PatientStore  # noqa: E402


def bertec_session(**overrides) -> dict:
    """Shape of ``bertec-jump/data/protocols/<id>/session.json``."""
    data = {
        "id": "20261101T100000_abc12345",
        "protocol_id": "dl_stance",
        "processing_version": "lp10-dc100-v1",
        "protocol_label": "Double-Leg Quiet Stance (Eyes Open / Eyes Closed)",
        "athlete": "Jane Doe",
        "started_at": "2026-11-01T10:00:00.000000+00:00",
        "completed_at": "2026-11-01T10:10:00.000000+00:00",
        "quality": "complete",
        "kept_trials": ["t1", "t2"],
        "summary": {
            "eo_firm": {
                "kept_trials": ["t1", "t2"],
                "means": {"asi": 1.42, "path_mm": 830.2, "sway_rms_mm": 2.75},
                "flag_counts": {"clipped": 0},
                "fall_risk": {"level": "low"},
            }
        },
    }
    data.update(overrides)
    return data


def runtrack_summary(**overrides) -> dict:
    """Shape of ``runtrack`` ``sessions.summary_json``."""
    data = {
        "n_frames": 217,
        "labels": ["external power proxy assumes 0.25 vertical cost factor"],
        "duration_s": 9.0,
        "symmetry_mean_pct": 98.8,
        "trunk_lean_deg": {"mean": -1.0, "std": 1.5},
        "head_sway_norm": 0.1227,
        "external_power_est_watts": 485.4,
        "form_index": 50.0,
        "form": {"trunk_lean_deg": {"value": -1.0, "band": [4, 12], "in_band": False}},
        "joints": {"left_elbow": {"mean": 104.6, "min": 77.5, "max": 161.0, "rom": 83.5}},
    }
    data.update(overrides)
    return data


def neurosync_summary(**overrides) -> dict:
    """Shape of ``neurosync`` ``recordings/.../summary.json``."""
    data = {
        "started_at": "2026-11-02T09:00:00+00:00",
        "subject_name": "Jane Doe",
        "subject_phone": "5550100",
        "device_type": "brainbit_classic",
        "device_label": "BrainBit Classic / Black",
        "device": {"device_key": "brainbit_classic"},
        "simulated": False,
        "channels": ["O1", "O2", "T3", "T4"],
        "fs_hz": 250,
        "duration_s": 4.8,
        "analysis": {
            "valid": True,
            "ready": True,
            "reason": "all quality gates passed",
            "condition": "eyes closed",
            "bands": {
                "Delta": {"power_uv2": 5.0, "relative_pct": 10.0},
                "Theta": {"power_uv2": 9.0, "relative_pct": 20.0},
                "Alpha": {"power_uv2": 20.0, "relative_pct": 45.0},
                "Beta": {"power_uv2": 7.0, "relative_pct": 15.0},
            },
        },
        "stable_estimate": {
            "valid": True,
            "bands": {
                "Delta": {"power_uv2": 5.0, "relative_pct": 10.0},
                "Theta": {"power_uv2": 9.0, "relative_pct": 20.0},
                "Alpha": {"power_uv2": 20.0, "relative_pct": 45.0},
                "Beta": {"power_uv2": 7.0, "relative_pct": 15.0},
            },
        },
        "ai_doctor": {"ok": True, "text": "Alpha predominant at rest.", "model": "qwen3"},
    }
    data.update(overrides)
    return data


#: The subset of InBodyStage1 ``migrations/001_initial.sql`` we read.
INBODY_SCHEMA = """
CREATE TABLE patients (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, dob TEXT, sex TEXT, synthetic INTEGER NOT NULL
);
CREATE TABLE encounters (
 id TEXT PRIMARY KEY, patient_id TEXT NOT NULL REFERENCES patients(id), label TEXT NOT NULL
);
CREATE TABLE results (
 id TEXT PRIMARY KEY, patient_id TEXT NOT NULL REFERENCES patients(id),
 encounter_id TEXT NOT NULL REFERENCES encounters(id), test_timestamp TEXT NOT NULL,
 ingested_at TEXT NOT NULL, source_type TEXT NOT NULL, source_identifier TEXT NOT NULL,
 source_hash TEXT NOT NULL, content TEXT NOT NULL, supersedes TEXT REFERENCES results(id),
 UNIQUE(patient_id, source_type, source_identifier), UNIQUE(supersedes)
);
"""


def inbody_content(
    measurements,
    *,
    encounter_id="E1",
    patient_id="S1",
    test_timestamp="2026-11-05T08:00:00+00:00",
    source_identifier="SRC-1",
    device_model="InBody 570",
    source_type="manual",
) -> dict:
    """A normalized-v1 payload (``schemas/normalized-v1.json``)."""
    return {
        "patient_id": patient_id,
        "encounter_id": encounter_id,
        "test_timestamp": test_timestamp,
        "source_identifier": source_identifier,
        "device_model": device_model,
        "source_type": source_type,
        "measurements": measurements,
    }


def metric(name, value, unit, status=None, **extra) -> dict:
    payload = {"metric": name, "value": value, "unit": unit}
    if status is not None:
        payload["status"] = status
    payload.update(extra)
    return payload


class McFixture(unittest.TestCase):
    """Temp repo-shaped tree: data dir + the three app roots."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self._tmp.name)
        self.data_dir = self.root / "data"
        self.store = PatientStore(self.data_dir)
        self.roots = {
            "bertec": self.root / "bertec-jump",
            "runtrack": self.root / "runtrack",
            "neurosync": self.root / "neurosync",
            "inbody": self.data_dir / "inbody",
        }
        self.ingest = Ingest(self.store, roots=self.roots)
        # Keep the host's InBody configuration out of the fixtures.
        env = unittest.mock.patch.dict(
            os.environ,
            {
                "INBODY_DB": str(self.root / "no-such-inbody.db"),
                "INBODY_IMPORT_DIR": str(self.roots["inbody"]),
            },
        )
        env.start()
        self.addCleanup(env.stop)

    def tearDown(self):
        self._tmp.cleanup()

    # -- fixtures ------------------------------------------------------------
    def make_patient(self, name="Jane Doe", **kwargs) -> dict:
        """Create a patient, retrying the atomic replace.

        ``os.replace`` can lose a race with Windows AV/indexing on a fresh temp
        file (WinError 32) — the same reason ``app.py`` retries saves.
        """
        import time

        last_error = None
        for _ in range(6):
            try:
                return self.store.create(name, **kwargs)
            except PermissionError as exc:  # pragma: no cover - Windows timing
                last_error = exc
                time.sleep(0.05)
        raise last_error or RuntimeError(f"could not create patient {name!r}")

    def write_bertec(self, session: dict | None = None, dirname: str | None = None) -> pathlib.Path:
        session = session or bertec_session()
        folder = self.roots["bertec"] / "data" / "protocols" / (dirname or session["id"])
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "session.json").write_text(json.dumps(session), encoding="utf-8")
        return folder

    def make_runtrack_db(self, rows: list[dict], patients: list[tuple[int, str]]) -> pathlib.Path:
        path = self.roots["runtrack"] / "data" / "runtrack.db"
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path))
        try:
            conn.executescript(
                """
                CREATE TABLE patients(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  phone TEXT NOT NULL UNIQUE,
                  created_ts TEXT NOT NULL DEFAULT (datetime('now'))
                );
                CREATE TABLE sessions(
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  patient_id INTEGER NOT NULL REFERENCES patients(id),
                  started_ts TEXT NOT NULL,
                  ended_ts TEXT,
                  duration_s REAL,
                  source_label TEXT,
                  weight_kg REAL,
                  height_cm REAL,
                  speed_kmh REAL,
                  frames INTEGER,
                  status TEXT DEFAULT 'running',
                  summary_json TEXT,
                  dir TEXT,
                  view_plane TEXT DEFAULT 'sagittal',
                  discipline TEXT DEFAULT 'running',
                  bike_type TEXT
                );
                """
            )
            conn.executemany(
                "INSERT INTO patients(id, name, phone) VALUES (?, ?, ?)",
                [(pid, name, f"555{pid:04d}") for pid, name in patients],
            )
            for row in rows:
                conn.execute(
                    "INSERT INTO sessions(id, patient_id, started_ts, ended_ts, duration_s,"
                    " status, summary_json, view_plane, discipline)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        row["id"],
                        row["patient_id"],
                        row.get("started_ts", "2026-11-03 09:00:00"),
                        row.get("ended_ts", "2026-11-03 09:10:00"),
                        row.get("duration_s", 9.0),
                        row.get("status", "complete"),
                        json.dumps(row.get("summary", runtrack_summary())),
                        row.get("view_plane", "sagittal"),
                        row.get("discipline", "running"),
                    ),
                )
            conn.commit()
        finally:
            conn.close()
        return path

    def write_neurosync(self, summary: dict | None = None, subject="jane_doe_5550100",
                        session="2026-11-02T09-00-00") -> pathlib.Path:
        summary = summary if summary is not None else neurosync_summary()
        folder = self.roots["neurosync"] / "recordings" / "subjects" / subject / session
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
        return folder

    def write_inbody_csv(self, name: str, body: str) -> pathlib.Path:
        folder = self.roots["inbody"]
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / name
        path.write_text(body, encoding="utf-8")
        return path

    def make_inbody_db(self, results, patients=(("S1", "Jane Doe"),), encounters=(("E1", "S1"),)) -> pathlib.Path:
        """A temp InBodyStage1 database with the real DDL (migrations/001)."""
        path = self.root / "inbody-app" / "runtime" / "inbody.db"
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path))
        try:
            conn.executescript(INBODY_SCHEMA)
            conn.executemany(
                "INSERT INTO patients(id, name, dob, sex, synthetic) VALUES (?, ?, NULL, NULL, 1)",
                [(patient_id, name) for patient_id, name in patients],
            )
            conn.executemany(
                "INSERT INTO encounters(id, patient_id, label) VALUES (?, ?, 'study')",
                [(encounter_id, patient_id) for encounter_id, patient_id in encounters],
            )
            for row in results:
                conn.execute(
                    "INSERT INTO results(id, patient_id, encounter_id, test_timestamp, ingested_at,"
                    " source_type, source_identifier, source_hash, content, supersedes)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        row["id"],
                        row.get("patient_id", "S1"),
                        row.get("encounter_id", "E1"),
                        row["test_timestamp"],
                        row.get("ingested_at", row["test_timestamp"]),
                        row.get("source_type", "manual"),
                        row.get("source_identifier")
                        or (row.get("content") or {}).get("source_identifier")
                        or f"src-{row['id']}",
                        row.get("source_hash", f"hash-{row['id']}"),
                        json.dumps(row["content"]),
                        row.get("supersedes"),
                    ),
                )
            conn.commit()
        finally:
            conn.close()
        return path

    def write_inbody_json(self, name: str, payload) -> pathlib.Path:
        folder = self.roots["inbody"]
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    # -- helpers -------------------------------------------------------------
    def rows(self, **kwargs) -> list[dict]:
        return self.ingest.read(**kwargs)

    def metrics(self, **kwargs) -> dict:
        return {row["metric"]: row for row in self.rows(**kwargs)}

    def context(self, patient_id=None) -> AdapterContext:
        patients = [self.store.get(patient_id)] if patient_id else self.store.list()
        return build_context(
            store=self.store, roots=self.roots, data_dir=self.data_dir, patients=patients
        )


# --------------------------------------------------------------------------
# schema
# --------------------------------------------------------------------------
class SchemaTests(unittest.TestCase):
    def good(self, **overrides):
        payload = {
            "subject_id": "jane-doe-1a2b",
            "source": "bertec",
            "session_id": "s1",
            "measured_at": "2026-11-01T10:00:00+00:00",
            "metric": "bertec.eo_firm.asi",
            "value": 1.42,
            "unit": "index",
            "quality": "incomplete",
            "provenance": {"app": "bertec-jump", "file": "data/protocols/s1/session.json"},
        }
        payload.update(overrides)
        return payload

    def test_valid_observation_normalizes(self):
        observation = Observation(**self.good())
        self.assertEqual(observation.metric, "bertec.eo_firm.asi")
        self.assertEqual(observation.value, 1.42)
        self.assertEqual(observation.quality, "incomplete")
        self.assertEqual(len(observation.dedupe_key()), 40)

    def test_missing_provenance_raises(self):
        payload = self.good()
        del payload["provenance"]
        with self.assertRaises(ValueError):
            Observation(**payload)
        with self.assertRaises(ValueError):
            Observation(**self.good(provenance={}))

    def test_provenance_without_locator_raises(self):
        with self.assertRaises(ValueError):
            Observation(**self.good(provenance={"app": "bertec-jump"}))

    def test_missing_session_id_raises(self):
        with self.assertRaises(ValueError):
            Observation(**self.good(session_id=""))

    def test_source_may_not_write_another_namespace(self):
        with self.assertRaises(ValueError):
            Observation(**self.good(metric="runtrack.form_index"))
        with self.assertRaises(ValueError):
            Observation(**self.good(metric="eeg.alpha_rel"))
        # manual entry can never claim a device namespace
        with self.assertRaises(ValueError):
            Observation(**self.good(source="manual", metric="bertec.asi"))
        self.assertEqual(
            Observation(**self.good(source="manual", metric="vitals.heart_rate")).metric,
            "vitals.heart_rate",
        )

    def test_unknown_source_raises(self):
        with self.assertRaises(ValueError):
            Observation(**self.good(source="invented-app"))

    def test_metric_must_be_namespaced(self):
        with self.assertRaises(ValueError):
            Observation(**self.good(metric="asi"))
        with self.assertRaises(ValueError):
            Observation(**self.good(metric="bertec."))

    def test_unknown_quality_word_is_never_verified(self):
        self.assertEqual(normalize_quality("complete"), "verified")
        self.assertEqual(normalize_quality("incomplete"), "incomplete")
        self.assertEqual(normalize_quality("uncalibrated"), "flagged")
        self.assertEqual(normalize_quality("something-new"), "flagged")
        self.assertEqual(normalize_quality(""), "unverified")
        # An unrecognised word is carried as ``flagged`` (a named problem is
        # never laundered into ``verified``), never silently dropped.
        coerced = Observation(
            **self.good(quality="looks-fine-to-me", provenance={"app": "x", "file": "y"})
        )
        self.assertEqual(coerced.quality, "flagged")

    def test_boolean_and_non_finite_values_rejected(self):
        for value in (True, float("nan"), float("inf")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    Observation(**self.good(value=value))

    def test_nan_never_reaches_storage(self):
        with self.assertRaises(ValueError):
            Observation(**self.good(value=math.nan))

    def test_state_strings_rejected(self):
        with self.assertRaises(ValueError):
            Observation(**self.good(session_id="a|b"))
        with self.assertRaises(ValueError):
            Observation(**self.good(subject_id="../etc/passwd"))

    def test_naive_timestamp_is_pinned_to_utc_and_reported(self):
        iso, assumed = normalize_timestamp("2026-11-03 09:00:00")
        self.assertEqual(iso, "2026-11-03T09:00:00+00:00")
        self.assertTrue(assumed)
        iso, assumed = normalize_timestamp("2026-11-03T09:00:00+00:00")
        self.assertEqual(iso, "2026-11-03T09:00:00+00:00")
        self.assertFalse(assumed)
        with self.assertRaises(ValueError):
            normalize_timestamp("not a date")

    def test_dedupe_key_is_sha1_of_the_four_fields(self):
        first = dedupe_key("bertec", "s1", "bertec.asi", "2026-11-01T10:00:00+00:00")
        self.assertEqual(len(first), 40)
        int(first, 16)  # hex
        self.assertEqual(
            first, dedupe_key("bertec", "s1", "bertec.asi", "2026-11-01T10:00:00+00:00")
        )
        self.assertNotEqual(
            first, dedupe_key("bertec", "s1", "bertec.asi", "2026-11-01T10:00:01+00:00")
        )
        self.assertNotEqual(first, dedupe_key("runtrack", "s1", "bertec.asi", "2026-11-01T10:00:00+00:00"))

    def test_round_trip_dict(self):
        observation = Observation(**self.good())
        row = observation.to_dict()
        self.assertEqual(row["dedupe_key"], observation.dedupe_key())
        restored = Observation.from_dict(row)
        self.assertEqual(restored.to_dict(), row)


# --------------------------------------------------------------------------
# adapters — empty state
# --------------------------------------------------------------------------
class EmptySourcesTests(McFixture):
    def test_no_app_directories_means_no_rows_and_no_errors(self):
        patient = self.make_patient()
        report = self.ingest.sync()
        self.assertEqual(report["added"], 0)
        self.assertEqual(report["candidates"], 0)
        self.assertEqual(report["unlinked_total"], 0)
        self.assertEqual(report["errors"], [])
        self.assertEqual(self.rows(), [])

        chart = build_chart(self.store, patient["id"])
        self.assertEqual(chart["timeline"], [])
        self.assertEqual(chart["totals"]["observations"], 0)
        self.assertTrue(all(not card["available"] for card in chart["sources"]))

    def test_each_adapter_returns_an_empty_result(self):
        context = self.context()
        for name, adapter in ADAPTERS.items():
            with self.subTest(source=name):
                result = adapter(context)
                self.assertEqual(result.observations, [])
                self.assertEqual(result.unlinked, [])
                self.assertEqual(result.errors, [])

    def test_missing_neurosync_recordings_is_not_an_error(self):
        (self.roots["neurosync"] / "recordings").mkdir(parents=True)
        patient = self.make_patient()
        self.store.link_session(patient["id"], "neurosync", "anything")
        result = neurosync.collect(self.context())
        self.assertEqual(result.observations, [])
        self.assertEqual(result.errors, [])


class PathTests(unittest.TestCase):
    """The sibling-app paths are resolved from the repo layout, not guessed."""

    def test_project_root_is_the_repo_root(self):
        import labflow.mc as mc_package

        expected = pathlib.Path(mc_package.__file__).resolve().parent
        self.assertEqual(project_root() / "labflow" / "mc", expected)
        self.assertTrue((project_root() / "labflow" / "patients.py").is_file())

    def test_default_roots_point_at_sibling_projects(self):
        roots = default_roots()
        self.assertEqual(set(roots), {"bertec", "runtrack", "neurosync", "inbody"})
        projects = project_root().parent
        self.assertEqual(roots["bertec"], projects / "bertec-jump")
        self.assertEqual(roots["runtrack"], projects / "runtrack")
        self.assertEqual(roots["neurosync"], projects / "neurosync")

    def test_env_overrides_win(self):
        with unittest.mock.patch.dict(
            os.environ, {"MC_BERTEC_ROOT": "/custom/bertec", "MC_RUNTRACK_ROOT": "/custom/rt"}
        ):
            roots = default_roots()
        self.assertEqual(roots["bertec"], pathlib.Path("/custom/bertec"))
        self.assertEqual(roots["runtrack"], pathlib.Path("/custom/rt"))

    def test_inbody_root_lives_in_the_data_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            ingest = Ingest(PatientStore(pathlib.Path(tmp)), data_dir=pathlib.Path(tmp))
            self.assertEqual(ingest.roots()["inbody"], pathlib.Path(tmp) / "inbody")


# --------------------------------------------------------------------------
# bertec
# --------------------------------------------------------------------------
class BertecAdapterTests(McFixture):
    def test_incomplete_session_stays_incomplete(self):
        patient = self.make_patient()
        self.write_bertec(bertec_session(quality="incomplete"))
        report = self.ingest.sync()
        self.assertEqual(report["added"], 5)  # 3 means + kept_trials + quality

        metric_rows = self.metrics()
        self.assertEqual(metric_rows["bertec.eo_firm.asi"]["quality"], "incomplete")
        self.assertEqual(metric_rows["bertec.eo_firm.asi"]["value"], 1.42)
        self.assertEqual(metric_rows["bertec.eo_firm.path_mm"]["unit"], "mm")
        self.assertEqual(metric_rows["bertec.kept_trials"]["value"], 2.0)
        self.assertEqual(metric_rows["bertec.quality"]["value"], "incomplete")
        for row in self.rows():
            self.assertEqual(row["subject_id"], patient["id"])
            self.assertEqual(row["source"], "bertec")

    def test_complete_session_is_verified_but_unlinked_without_a_link(self):
        self.make_patient()
        session = bertec_session(athlete="")
        self.write_bertec(session)
        report = self.ingest.sync()
        self.assertEqual(report["added"], 0)
        unlinked = self.ingest.unlinked()
        self.assertEqual(len(unlinked), 1)
        self.assertEqual(unlinked[0]["source"], "bertec")
        self.assertEqual(unlinked[0]["session_id"], session["id"])
        self.assertIn("no explicit patient link", unlinked[0]["reason"])

    def test_explicit_link_attaches_even_with_empty_athlete(self):
        patient = self.make_patient()
        session = bertec_session(athlete="")
        self.store.link_session(patient["id"], "bertec", session["id"])
        self.write_bertec(session)
        self.ingest.sync()
        self.assertEqual({row["subject_id"] for row in self.rows()}, {patient["id"]})
        self.assertEqual(self.ingest.unlinked(), [])

    def test_exact_name_links_but_ambiguous_name_does_not(self):
        first = self.make_patient("Jane Doe")
        self.write_bertec(bertec_session(), dirname="match")
        self.ingest.sync()
        self.assertTrue(self.rows())
        self.assertEqual({row["subject_id"] for row in self.rows()}, {first["id"]})

        # A second patient with the same name makes the name match ambiguous.
        self.make_patient("Jane Doe")
        self.write_bertec(bertec_session(id="second-session"), dirname="ambiguous")
        report = self.ingest.sync()
        self.assertEqual(report["added"], 0)
        labels = {(item["session_id"]) for item in self.ingest.unlinked()}
        self.assertIn("second-session", labels)

    def test_unreadable_session_is_an_error_not_a_crash(self):
        self.make_patient()
        folder = self.roots["bertec"] / "data" / "protocols" / "broken"
        folder.mkdir(parents=True)
        (folder / "session.json").write_text("{not json", encoding="utf-8")
        report = self.ingest.sync()
        self.assertEqual(report["added"], 0)
        self.assertEqual(len(report["errors"]), 1)
        self.assertEqual(report["errors"][0]["source"], "bertec")

    def test_quality_metric_and_analysis_carry_the_app_words(self):
        patient = self.make_patient()
        self.write_bertec(bertec_session(quality="incomplete"))
        self.ingest.sync()
        session = self.ingest.read()[0]
        self.assertIn("Double-Leg Quiet Stance", session["analysis"])
        self.assertIn("incomplete", session["analysis"])
        self.assertIn("eo_firm", session["analysis"])
        self.assertEqual(session["provenance"]["app"], "bertec-jump")
        self.assertEqual(session["provenance"]["processing_version"], "lp10-dc100-v1")
        self.assertEqual(session["subject_id"], patient["id"])


# --------------------------------------------------------------------------
# runtrack
# --------------------------------------------------------------------------
class RunTrackAdapterTests(McFixture):
    def test_complete_with_view_plane_is_verified(self):
        patient = self.make_patient()
        self.make_runtrack_db([{"id": 1, "patient_id": 1}], [(1, "Jane Doe")])
        report = self.ingest.sync()
        self.assertGreater(report["added"], 0)

        metric_rows = self.metrics()
        self.assertEqual(metric_rows["runtrack.form_index"]["quality"], "verified")
        self.assertEqual(metric_rows["runtrack.form_index"]["value"], 50.0)
        self.assertEqual(metric_rows["runtrack.form_index"]["unit"], "score")
        self.assertEqual(metric_rows["runtrack.symmetry_mean_pct"]["unit"], "%")
        self.assertEqual(metric_rows["runtrack.trunk_lean_deg"]["value"], -1.0)
        self.assertEqual(metric_rows["runtrack.head_sway_norm"]["unit"], "index")
        self.assertEqual(metric_rows["runtrack.external_power_est_watts"]["unit"], "W")
        self.assertEqual(metric_rows["runtrack.joint.left_elbow.mean"]["value"], 104.6)
        self.assertEqual(metric_rows["runtrack.joint.left_elbow.mean"]["unit"], "deg")
        self.assertEqual({row["subject_id"] for row in self.rows()}, {patient["id"]})

    def test_missing_view_plane_downgrades_to_unverified(self):
        self.make_patient()
        self.make_runtrack_db(
            [{"id": 1, "patient_id": 1, "status": "complete", "view_plane": ""}],
            [(1, "Jane Doe")],
        )
        self.ingest.sync()
        self.assertEqual({row["quality"] for row in self.rows()}, {"unverified"})

    def test_running_status_is_unverified(self):
        self.make_patient()
        self.make_runtrack_db([{"id": 1, "patient_id": 1, "status": "running"}], [(1, "Jane Doe")])
        self.ingest.sync()
        self.assertEqual({row["quality"] for row in self.rows()}, {"unverified"})

    def test_unknown_patient_name_goes_to_unlinked(self):
        self.make_patient("Jane Doe")
        self.make_runtrack_db([{"id": 7, "patient_id": 1}], [(1, "Somebody Else")])
        report = self.ingest.sync()
        self.assertEqual(report["added"], 0)
        self.assertEqual(self.ingest.unlinked()[0]["session_id"], "7")

    def test_database_is_opened_read_only(self):
        self.make_runtrack_db([{"id": 1, "patient_id": 1}], [(1, "Jane Doe")])
        conn = runtrack.connect_readonly(self.roots["runtrack"] / "data" / "runtrack.db")
        try:
            with self.assertRaises(sqlite3.OperationalError):
                conn.execute("INSERT INTO patients(name, phone) VALUES ('X', '1')")
        finally:
            conn.close()

    def test_missing_summary_still_records_the_session(self):
        patient = self.make_patient()
        self.make_runtrack_db(
            [{"id": 1, "patient_id": 1, "summary": {}}], [(1, "Jane Doe")]
        )
        self.store.link_session(patient["id"], "runtrack", "1")
        self.ingest.sync()
        self.assertEqual(self.rows(), [])  # no numbers, but also no crash
        self.assertEqual(self.ingest.unlinked(), [])


# --------------------------------------------------------------------------
# neurosync
# --------------------------------------------------------------------------
class NeuroSyncAdapterTests(McFixture):
    def test_band_metrics_and_verified_session(self):
        patient = self.make_patient()
        self.write_neurosync()
        report = self.ingest.sync()
        self.assertGreater(report["added"], 0)

        metric_rows = self.metrics()
        self.assertEqual(metric_rows["eeg.alpha_rel"]["value"], 45.0)
        self.assertEqual(metric_rows["eeg.alpha_rel"]["unit"], "%")
        self.assertEqual(metric_rows["eeg.alpha_abs"]["value"], 20.0)
        self.assertEqual(metric_rows["eeg.alpha_abs"]["unit"], "µV²")
        self.assertAlmostEqual(metric_rows["eeg.tbr"]["value"], 9.0 / 7.0, places=3)
        self.assertEqual(metric_rows["eeg.quality"]["value"], 1.0)
        self.assertEqual({row["quality"] for row in self.rows()}, {"verified"})
        self.assertEqual({row["subject_id"] for row in self.rows()}, {patient["id"]})
        self.assertEqual(metric_rows["eeg.alpha_rel"]["ai_text"], "Alpha predominant at rest.")
        self.assertEqual(metric_rows["eeg.alpha_rel"]["ai_model"], "qwen3")

    def test_simulated_session_is_unverified_with_provenance_flag(self):
        self.make_patient()
        self.write_neurosync(neurosync_summary(simulated=True, device_label="SIMULATED BrainBit"))
        self.ingest.sync()
        rows = self.rows()
        self.assertTrue(rows)
        self.assertEqual({row["quality"] for row in rows}, {"unverified"})
        self.assertIs(rows[0]["provenance"]["simulated"], True)

    def test_failed_gate_is_unverified(self):
        self.make_patient()
        summary = neurosync_summary()
        summary["analysis"] = dict(summary["analysis"], valid=False, ready=False, reason="high resistance")
        self.write_neurosync(summary)
        self.ingest.sync()
        self.assertEqual({row["quality"] for row in self.rows()}, {"unverified"})
        quality_metric = self.metrics()["eeg.quality"]
        self.assertEqual(quality_metric["value"], 0.0)

    def test_simulated_cannot_be_verified_even_with_a_passing_gate(self):
        self.make_patient()
        self.write_neurosync(neurosync_summary(simulated=True))
        self.ingest.sync()
        self.assertEqual({row["quality"] for row in self.rows()}, {"unverified"})

    def test_non_scalar_blocks_are_not_flattened_into_metrics(self):
        self.make_patient()
        self.write_neurosync()
        self.ingest.sync()
        metrics = set(self.metrics())
        self.assertNotIn("eeg.device", metrics)
        self.assertNotIn("eeg.channels", metrics)
        self.assertNotIn("eeg.analysis", metrics)
        self.assertTrue(all(metric.startswith("eeg.") for metric in metrics))
        provenance = self.rows()[0]["provenance"]
        self.assertIn("device", provenance)
        self.assertEqual(provenance["channels"], "O1,O2,T3,T4")
        self.assertIn("skipped_non_scalar", provenance)

    def test_unlinked_without_subject_name(self):
        self.make_patient("Jane Doe")
        self.write_neurosync(neurosync_summary(subject_name=""))
        report = self.ingest.sync()
        self.assertEqual(report["added"], 0)
        self.assertEqual(len(self.ingest.unlinked()), 1)


# --------------------------------------------------------------------------
# inbody
# --------------------------------------------------------------------------
CSV_HEADER = (
    "measured_at,weight_kg,skeletal_muscle_kg,body_fat_kg,"
    "body_fat_pct,visceral_fat,lean_mass_kg,bmi\n"
)


class InBodyAdapterTests(McFixture):
    def test_csv_import_is_unverified_manual_entry(self):
        patient = self.make_patient()
        self.write_inbody_csv(
            f"{patient['id']}.csv",
            CSV_HEADER + "2026-11-04T08:00:00+00:00,82.4,34.1,18.2,22.1,9,61.9,24.8\n",
        )
        report = self.ingest.sync()
        self.assertEqual(report["added"], 7)

        metric_rows = self.metrics()
        self.assertEqual(metric_rows["body.weight_kg"]["value"], 82.4)
        self.assertEqual(metric_rows["body.weight_kg"]["unit"], "kg")
        self.assertEqual(metric_rows["body.skeletal_muscle_kg"]["unit"], "kg")
        self.assertEqual(metric_rows["body.body_fat_pct"]["unit"], "%")
        self.assertEqual(metric_rows["body.bmi"]["unit"], "index")
        # The manual template keeps its own names; the device vocabulary it maps
        # to is recorded alongside, not silently substituted.
        self.assertEqual(
            metric_rows["body.weight_kg"]["provenance"]["canonical_metric"], "body.weight"
        )
        self.assertEqual({row["quality"] for row in self.rows()}, {"unverified"})
        self.assertIn("verify against the device printout", self.rows()[0]["analysis"])

    def test_device_serial_makes_the_row_verified_by_provenance(self):
        patient = self.make_patient()
        self.write_inbody_csv(
            f"{patient['id']}.csv",
            "measured_at,weight_kg,device_serial\n2026-11-04T08:00:00+00:00,82.4,SN-123\n",
        )
        self.ingest.sync()
        row = self.rows()[0]
        self.assertEqual(row["quality"], "verified")
        self.assertEqual(row["provenance"]["device_serial"], "SN-123")

    def test_subject_id_column_wins_over_file_name(self):
        patient = self.make_patient()
        self.write_inbody_csv(
            "export.csv",
            "measured_at,subject_id,weight_kg\n2026-11-04T08:00:00+00:00,"
            f"{patient['id']},82.4\n",
        )
        self.ingest.sync()
        self.assertEqual({row["subject_id"] for row in self.rows()}, {patient["id"]})

    def test_row_without_a_patient_goes_to_unlinked(self):
        self.make_patient()
        self.write_inbody_csv(
            "mystery.csv",
            CSV_HEADER + "2026-11-04T08:00:00+00:00,82.4,34.1,18.2,22.1,9,61.9,24.8\n",
        )
        report = self.ingest.sync()
        self.assertEqual(report["added"], 0)
        self.assertEqual(len(self.ingest.unlinked()), 1)

    # -- the real InBody app (SQLite) ---------------------------------------
    def use_inbody_db(self, results, **kwargs) -> pathlib.Path:
        """Build a temp InBody DB and point INBODY_DB at it for this test."""
        db = self.make_inbody_db(results, **kwargs)
        patcher = unittest.mock.patch.dict(os.environ, {"INBODY_DB": str(db)})
        patcher.start()
        self.addCleanup(patcher.stop)
        return db

    def db_result(self, result_id="R1", **content_kwargs) -> dict:
        return {
            "id": result_id,
            "test_timestamp": content_kwargs.get("test_timestamp", "2026-11-05T08:00:00+00:00"),
            "content": inbody_content(**content_kwargs),
        }

    def test_database_result_maps_three_metrics(self):
        patient = self.make_patient()
        self.store.link_session(patient["id"], "inbody", "S1")
        self.use_inbody_db(
            [
                self.db_result(
                    measurements=[
                        metric("weight", 82.4, "kg", "verified"),
                        metric("body_fat_mass", 18.2, "kg", "verified"),
                        metric("percent_body_fat", 22.1, "%", "verified"),
                    ]
                )
            ]
        )
        report = self.ingest.sync()
        self.assertEqual(report["added"], 3)
        self.assertEqual(report["errors"], [])

        rows = self.rows()
        self.assertEqual({row["subject_id"] for row in rows}, {patient["id"]})
        self.assertEqual({row["source"] for row in rows}, {"inbody"})
        metric_rows = self.metrics()
        self.assertEqual(
            set(metric_rows), {"body.weight", "body.body_fat_mass", "body.percent_body_fat"}
        )
        weight = metric_rows["body.weight"]
        self.assertEqual(weight["value"], 82.4)
        self.assertEqual(weight["unit"], "kg")
        self.assertEqual(weight["quality"], "verified")
        self.assertEqual(weight["session_id"], "R1")
        self.assertEqual(weight["provenance"]["result_id"], "R1")
        self.assertEqual(weight["provenance"]["encounter_id"], "E1")
        self.assertEqual(weight["provenance"]["source_identifier"], "SRC-1")
        self.assertEqual(weight["provenance"]["source_hash"], "hash-R1")
        self.assertEqual(weight["provenance"]["device_model"], "InBody 570")
        self.assertEqual(weight["provenance"]["app"], "inbody")
        self.assertEqual(weight["provenance"]["import"], "sqlite")
        self.assertTrue(weight["provenance"]["file"].endswith("inbody.db"))
        self.assertIn("InBody 570", weight["analysis"])

    def test_superseded_result_is_ignored(self):
        patient = self.make_patient()
        self.store.link_session(patient["id"], "inbody", "S1")
        self.use_inbody_db(
            [
                {
                    "id": "R1",
                    "test_timestamp": "2026-11-01T08:00:00+00:00",
                    "source_identifier": "SRC-1",
                    "content": inbody_content(
                        [metric("weight", 80.0, "kg", "verified")],
                        test_timestamp="2026-11-01T08:00:00+00:00",
                        source_identifier="SRC-1",
                    ),
                },
                {
                    "id": "R2",
                    "test_timestamp": "2026-11-05T08:00:00+00:00",
                    "source_identifier": "SRC-2",
                    "supersedes": "R1",
                    "content": inbody_content(
                        [metric("weight", 82.5, "kg", "verified")],
                        test_timestamp="2026-11-05T08:00:00+00:00",
                        source_identifier="SRC-2",
                    ),
                },
            ]
        )
        self.ingest.sync()
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["value"], 82.5)
        self.assertEqual(rows[0]["session_id"], "R2")
        self.assertNotIn("R1", {row["session_id"] for row in rows})

    def test_newest_result_per_encounter_wins(self):
        patient = self.make_patient()
        self.store.link_session(patient["id"], "inbody", "S1")
        self.use_inbody_db(
            [
                {
                    "id": "OLD",
                    "test_timestamp": "2026-11-01T08:00:00+00:00",
                    "source_type": "pdf",
                    "source_identifier": "PDF-1",
                    "content": inbody_content(
                        [metric("weight", 80.0, "kg", "verified")],
                        test_timestamp="2026-11-01T08:00:00+00:00",
                        source_type="pdf",
                    ),
                },
                {
                    "id": "NEW",
                    "test_timestamp": "2026-11-05T08:00:00+00:00",
                    "source_type": "manual",
                    "source_identifier": "MAN-1",
                    "content": inbody_content(
                        [metric("weight", 82.0, "kg", "verified")],
                        test_timestamp="2026-11-05T08:00:00+00:00",
                    ),
                },
            ]
        )
        self.ingest.sync()
        rows = self.rows()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["value"], 82.0)
        self.assertEqual(rows[0]["session_id"], "NEW")

    def test_missing_database_returns_no_rows_with_a_note(self):
        self.make_patient()
        result = inbody.collect(self.context())
        self.assertEqual(result.observations, [])
        self.assertEqual(result.errors, [])
        self.assertTrue(any("not found" in note["note"] for note in result.notes))

        report = self.ingest.sync()
        self.assertEqual(report["added"], 0)
        self.assertTrue(report["notes"])

    def test_database_is_opened_read_only(self):
        db = self.use_inbody_db([self.db_result(measurements=[metric("weight", 80.0, "kg")])])
        conn = inbody.connect_readonly(db)
        try:
            with self.assertRaises(sqlite3.OperationalError):
                conn.execute("INSERT INTO patients(id, name, synthetic) VALUES ('X', 'Y', 1)")
        finally:
            conn.close()

    def test_wal_commits_are_read(self):
        """InBody leaves commits in ``-wal``; an immutable open would miss them."""
        db = self.root / "inbody-app" / "runtime" / "inbody.db"
        db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db))
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript(INBODY_SCHEMA)
            conn.execute("INSERT INTO patients(id, name, synthetic) VALUES ('S1', 'Jane Doe', 1)")
            conn.execute("INSERT INTO encounters(id, patient_id, label) VALUES ('E1', 'S1', 'study')")
            conn.execute(
                "INSERT INTO results(id, patient_id, encounter_id, test_timestamp, ingested_at,"
                " source_type, source_identifier, source_hash, content, supersedes)"
                " VALUES ('R1', 'S1', 'E1', '2026-11-05T08:00:00+00:00', '2026-11-05T08:00:00+00:00',"
                " 'manual', 'SRC-1', 'hash-1', ?, NULL)",
                (json.dumps(inbody_content([metric("weight", 82.4, "kg", "verified")])),),
            )
            conn.commit()  # stays in the WAL: the connection is still open

            patient = self.make_patient()
            self.store.link_session(patient["id"], "inbody", "S1")
            with unittest.mock.patch.dict(os.environ, {"INBODY_DB": str(db)}):
                result = inbody.collect(self.context())
            self.assertEqual([observation.value for observation in result.observations], [82.4])
            self.assertEqual(result.errors, [])
        finally:
            conn.close()

    def test_normalized_json_import(self):
        patient = self.make_patient()
        self.store.link_session(patient["id"], "inbody", "S1")
        self.write_inbody_json(
            "drop.json",
            inbody_content(
                [
                    metric("weight", 81.0, "kg", "verified"),
                    metric("visceral_fat_level", 9, "index", "verified"),
                ],
                encounter_id="ENC-JSON",
            ),
        )
        report = self.ingest.sync()
        self.assertEqual(report["added"], 2)
        metric_rows = self.metrics()
        self.assertEqual(metric_rows["body.weight"]["value"], 81.0)
        self.assertEqual(metric_rows["body.visceral_fat_level"]["unit"], "index")
        self.assertEqual(metric_rows["body.weight"]["provenance"]["import"], "json")
        self.assertEqual(metric_rows["body.weight"]["session_id"], "drop:ENC-JSON")

    def test_invalid_json_import_is_an_error_not_a_crash(self):
        self.make_patient()
        self.write_inbody_json("bad.json", {"encounter_id": "E1", "measurements": []})
        report = self.ingest.sync()
        self.assertEqual(report["added"], 0)
        self.assertTrue(any("normalized-v1" in str(err.get("error")) for err in report["errors"]))

    def test_unverified_measurement_status_is_preserved(self):
        patient = self.make_patient()
        self.store.link_session(patient["id"], "inbody", "S1")
        self.use_inbody_db(
            [
                self.db_result(
                    measurements=[
                        metric("weight", 82.4, "kg", "verified"),
                        metric("percent_body_fat", 22.1, "%", "unverified"),
                        metric("skeletal_muscle_mass", 34.1, "kg"),  # no status at all
                    ]
                )
            ]
        )
        self.ingest.sync()
        metric_rows = self.metrics()
        self.assertEqual(metric_rows["body.weight"]["quality"], "verified")
        self.assertEqual(metric_rows["body.percent_body_fat"]["quality"], "unverified")
        self.assertEqual(metric_rows["body.skeletal_muscle_mass"]["quality"], "unverified")

    def test_names_are_never_used_to_link(self):
        self.make_patient("Jane Doe")
        self.use_inbody_db(
            [self.db_result(measurements=[metric("weight", 82.4, "kg", "verified")])],
            patients=(("S1", "Jane Doe"),),  # same name, still not a link
        )
        report = self.ingest.sync()
        self.assertEqual(report["added"], 0)
        unlinked = self.ingest.unlinked()
        self.assertEqual(len(unlinked), 1)
        self.assertEqual(unlinked[0]["source"], "inbody")
        self.assertIn("names are never matched", unlinked[0]["reason"])

    def test_body_inbody_patient_id_hint_links_the_session(self):
        patient = self.make_patient()
        self.store.add_measurement(patient["id"], "body.inbody_patient_id", "S1", "", "inbody")
        self.use_inbody_db([self.db_result(measurements=[metric("weight", 82.4, "kg", "verified")])])
        self.ingest.sync()
        self.assertEqual({row["subject_id"] for row in self.rows()}, {patient["id"]})
        self.assertEqual(self.metrics()["body.weight"]["value"], 82.4)

    def test_quality_note_rides_along_in_analysis(self):
        patient = self.make_patient()
        self.store.link_session(patient["id"], "inbody", "S1")
        self.use_inbody_db(
            [
                self.db_result(
                    measurements=[
                        metric("weight", 82.4, "kg", "unverified", quality_note="copied from printout")
                    ]
                )
            ]
        )
        self.ingest.sync()
        self.assertIn("copied from printout", self.rows()[0]["analysis"])
        self.assertEqual(self.rows()[0]["quality"], "unverified")

    def test_manual_entry_helper(self):
        patient = self.make_patient()
        observations = inbody.build_manual(
            patient["id"], "2026-11-04T08:00:00+00:00", {"weight_kg": "82.4", "body_fat_pct": 22.1}
        )
        self.assertEqual(len(observations), 2)
        self.assertEqual({observation.quality for observation in observations}, {"unverified"})
        self.assertEqual(
            {observation.metric for observation in observations},
            {"body.weight_kg", "body.body_fat_pct"},
        )
        verified = inbody.build_manual(
            patient["id"], "2026-11-04T08:00:00+00:00", {"weight_kg": 82.4}, device_serial="SN-9"
        )
        self.assertEqual(verified[0].quality, "verified")


# --------------------------------------------------------------------------
# intake
# --------------------------------------------------------------------------
class IntakeAdapterTests(McFixture):
    def test_intake_fields_and_measurements(self):
        patient = self.make_patient(
            "Jane Doe", dob="1990-01-01", intake={"height_cm": 171.5, "sex": "F", "sport": "running"}
        )
        self.store.add_measurement(patient["id"], "heart_rate", 58, "bpm", "vitals-station")
        self.store.add_measurement(patient["id"], "vitals.systolic", 118, "mmHg", "vitals-station")

        self.ingest.sync()
        metric_rows = self.metrics()

        self.assertEqual(metric_rows["intake.height_cm"]["value"], 171.5)
        self.assertEqual(metric_rows["intake.height_cm"]["unit"], "cm")
        self.assertEqual(metric_rows["intake.sex"]["value"], "F")
        self.assertEqual(metric_rows["vitals.heart_rate"]["value"], 58.0)
        self.assertEqual(metric_rows["vitals.heart_rate"]["unit"], "bpm")
        self.assertEqual(metric_rows["vitals.systolic"]["unit"], "mmHg")
        self.assertEqual({row["quality"] for row in self.rows()}, {"unverified"})
        self.assertEqual({row["source"] for row in self.rows()}, {"intake"})

    def test_two_synthetic_sessions_per_patient(self):
        patient = self.make_patient("Jane Doe", intake={"height_cm": 171.5})
        self.store.add_measurement(patient["id"], "heart_rate", 58, "bpm", "vitals")
        self.ingest.sync()
        chart = build_chart(self.store, patient["id"])
        self.assertEqual(len(chart["timeline"]), 2)
        self.assertEqual(chart["sources"][4]["label"], "Intake")

    def test_patient_without_intake_adds_nothing(self):
        self.make_patient()
        self.ingest.sync()
        self.assertEqual(self.rows(), [])


# --------------------------------------------------------------------------
# ingest
# --------------------------------------------------------------------------
class IngestTests(McFixture):
    def test_second_ingest_adds_zero(self):
        self.make_patient()
        self.write_bertec()
        first = self.ingest.sync()
        self.assertGreater(first["added"], 0)
        second = self.ingest.sync()
        self.assertEqual(second["added"], 0)
        self.assertEqual(second["updated"], 0)
        self.assertEqual(second["skipped"], first["added"])
        self.assertEqual(len(self.rows()), first["added"])

    def test_append_only_file_grows_by_lines_only(self):
        self.make_patient()
        self.write_bertec()
        self.ingest.sync()
        path = self.ingest.observations_path
        before = path.read_text(encoding="utf-8").splitlines()
        self.ingest.sync()
        after = path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(before, after)

    def test_quality_is_never_upgraded(self):
        patient = self.make_patient()
        base = {
            "subject_id": patient["id"],
            "source": "bertec",
            "session_id": "s1",
            "measured_at": "2026-11-01T10:00:00+00:00",
            "metric": "bertec.asi",
            "value": 1.0,
            "provenance": {"app": "bertec-jump", "file": "x"},
        }
        self.ingest.add([Observation(**base, quality="incomplete")])
        result = self.ingest.add([Observation(**base, quality="verified")])
        self.assertEqual(result["added"], 0)
        self.assertEqual(result["updated"], 0)
        self.assertEqual({row["quality"] for row in self.rows()}, {"incomplete"})

    def test_a_downgrade_is_appended_and_wins(self):
        patient = self.make_patient()
        base = {
            "subject_id": patient["id"],
            "source": "bertec",
            "session_id": "s1",
            "measured_at": "2026-11-01T10:00:00+00:00",
            "metric": "bertec.asi",
            "value": 1.0,
            "provenance": {"app": "bertec-jump", "file": "x"},
        }
        self.ingest.add([Observation(**base, quality="verified")])
        result = self.ingest.add([Observation(**base, quality="incomplete")])
        self.assertEqual(result["updated"], 1)
        self.assertEqual({row["quality"] for row in self.rows()}, {"incomplete"})

    def test_unknown_patient_is_rejected(self):
        with self.assertRaises(ValueError):
            self.ingest.add(
                [
                    Observation(
                        subject_id="nobody-0000",
                        source="inbody",
                        session_id="s1",
                        measured_at="2026-11-01T10:00:00+00:00",
                        metric="body.weight_kg",
                        value=80.0,
                        provenance={"app": "labflow", "file": "x"},
                    )
                ]
            )

    def test_single_patient_sync_scope(self):
        jane = self.make_patient("Jane Doe")
        self.make_patient("John Roe")
        self.write_bertec(bertec_session(athlete="Jane Doe"))
        report = self.ingest.sync(jane["id"])
        self.assertEqual(report["scope"], jane["id"])
        self.assertTrue(self.rows())
        self.assertEqual({row["subject_id"] for row in self.rows()}, {jane["id"]})
        with self.assertRaises(KeyError):
            self.ingest.sync("nobody-0000")

    def test_scoped_sync_counts_other_patients_correctly(self):
        jane = self.make_patient("Jane Doe")
        john = self.make_patient("John Roe")
        self.write_bertec(bertec_session(id="j1", athlete="Jane Doe"))
        self.write_bertec(bertec_session(id="j2", athlete="John Roe"))

        report = self.ingest.sync(jane["id"])
        self.assertEqual({row["subject_id"] for row in self.rows()}, {jane["id"]})
        # John's session is linked, not unlinked — a scoped sync must not claim
        # otherwise just because it only *wrote* Jane's rows.
        self.assertEqual(report["unlinked_in_run"], 0)
        self.assertEqual(self.ingest.unlinked(), [])

    def test_index_rebuild_shape(self):
        patient = self.make_patient()
        self.write_bertec()
        self.ingest.sync()
        index = self.ingest.rebuild_index()
        self.assertIn("built_at", index)
        self.assertEqual(index["counts"]["patients"], 1)
        self.assertEqual(index["counts"]["observations"], len(self.rows()))
        session = index["patients"][patient["id"]]["sessions"]
        self.assertEqual(len(session), 1)
        entry = next(iter(session.values()))
        self.assertEqual(entry["source"], "bertec")
        self.assertIn("bertec.eo_firm.asi", entry["metrics"])
        self.assertTrue(self.ingest.index_path.exists())

    def test_corrupt_line_does_not_break_reads(self):
        patient = self.make_patient()
        self.write_bertec()
        self.ingest.sync()
        good = len(self.rows())
        with self.ingest.observations_path.open("a", encoding="utf-8") as handle:
            handle.write("{not json\n")
            handle.write(json.dumps({"subject_id": patient["id"], "source": "???", "metric": "x"}) + "\n")
        self.assertEqual(len(self.rows()), good)
        report = self.ingest.sync()
        self.assertEqual(report["added"], 0)

    def test_unlinked_bucket_is_cleared_by_a_later_link(self):
        patient = self.make_patient()
        session = bertec_session(athlete="")
        self.write_bertec(session)
        self.ingest.sync()
        self.assertEqual(len(self.ingest.unlinked()), 1)
        self.store.link_session(patient["id"], "bertec", session["id"])
        self.ingest.sync()
        self.assertEqual(self.ingest.unlinked(), [])
        self.assertTrue(self.rows())

    def test_adapters_never_write_into_source_trees(self):
        self.make_patient()
        self.write_bertec()
        self.make_runtrack_db([{"id": 1, "patient_id": 1}], [(1, "Jane Doe")])
        self.write_neurosync()

        def snapshot():
            return {
                str(path): path.stat().st_mtime_ns
                for root_name in ("bertec", "runtrack", "neurosync")
                for path in sorted(self.roots[root_name].rglob("*"))
                if path.is_file()
            }

        before = snapshot()
        self.ingest.sync()
        self.assertEqual(before, snapshot())

    def test_resolved_read_keeps_only_effective_rows(self):
        patient = self.make_patient()
        base = {
            "subject_id": patient["id"],
            "source": "inbody",
            "session_id": "s1",
            "measured_at": "2026-11-01T10:00:00+00:00",
            "metric": "body.weight_kg",
            "value": 80.0,
            "provenance": {"app": "labflow", "file": "x"},
        }
        self.ingest.add([Observation(**base, quality="verified")])
        self.ingest.add([Observation(**base, quality="flagged")])
        self.assertEqual(len(self.rows(resolve=False)), 2)
        self.assertEqual(len(self.rows()), 1)
        self.assertEqual(self.rows()[0]["quality"], "flagged")


# --------------------------------------------------------------------------
# chart
# --------------------------------------------------------------------------
class ChartTests(McFixture):
    def seed(self) -> dict:
        patient = self.make_patient("Jane Doe")
        self.store.link_session(patient["id"], "runtrack", "1")
        self.make_runtrack_db(
            [{"id": 1, "patient_id": 1, "ended_ts": "2026-11-03 12:00:00"}], [(1, "Jane Doe")]
        )
        self.write_bertec(bertec_session(quality="incomplete"))  # 2026-11-01T10:00
        self.write_neurosync()  # 2026-11-02T09:00
        self.ingest.sync()
        return patient

    def test_timeline_is_newest_first_and_grouped_by_source(self):
        patient = self.seed()
        chart = build_chart(self.store, patient["id"])
        order = [item["source"] for item in chart["timeline"]]
        self.assertEqual(order, ["runtrack", "neurosync", "bertec"])
        self.assertEqual(chart["totals"]["sessions"], 3)
        first = chart["timeline"][0]
        self.assertEqual(first["quality"], "verified")
        self.assertEqual(first["source_label"], "RunTrack")
        self.assertTrue(first["analysis"])
        self.assertTrue(first["provenance"])

    def test_cards_are_fixed_order_with_latest_values(self):
        patient = self.seed()
        chart = build_chart(self.store, patient["id"])
        self.assertEqual(
            [card["source"] for card in chart["sources"]],
            ["bertec", "runtrack", "neurosync", "inbody", "intake", "manual"],
        )
        bertec_card = chart["sources"][0]
        self.assertTrue(bertec_card["available"])
        self.assertEqual(bertec_card["sessions"], 1)
        latest = {item["metric"]: item for item in bertec_card["latest"]}
        self.assertEqual(latest["bertec.eo_firm.asi"]["value"], 1.42)
        self.assertEqual(latest["bertec.eo_firm.asi"]["quality"], "incomplete")
        inbody_card = chart["sources"][3]
        self.assertFalse(inbody_card["available"])
        self.assertEqual(inbody_card["latest"], [])

    def test_latest_per_metric_prefers_the_newest_session(self):
        patient = self.make_patient()
        self.store.link_session(patient["id"], "bertec", "old")
        self.store.link_session(patient["id"], "bertec", "new")
        self.write_bertec(
            bertec_session(
                id="old",
                athlete="",
                completed_at="2026-11-01T10:00:00+00:00",
                summary={"eo": {"means": {"asi": 1.0}}},
            )
        )
        self.write_bertec(
            bertec_session(
                id="new",
                athlete="",
                completed_at="2026-11-05T10:00:00+00:00",
                summary={"eo": {"means": {"asi": 2.5}}},
            )
        )
        self.ingest.sync()
        chart = build_chart(self.store, patient["id"])
        latest = {item["metric"]: item for item in chart["latest"]}
        self.assertEqual(latest["bertec.eo.asi"]["value"], 2.5)
        self.assertEqual([item["session_id"] for item in chart["timeline"]], ["new", "old"])

    def test_unknown_patient_raises(self):
        with self.assertRaises(KeyError):
            build_chart(self.store, "nobody-0000")

    def test_payload_carries_the_disclaimer(self):
        patient = self.make_patient()
        chart = build_chart(self.store, patient["id"])
        self.assertEqual(chart["disclaimer"], DISCLAIMER)
        self.assertIn("Not a certified EHR", chart["disclaimer"])
        self.assertEqual(chart["patient"]["id"], patient["id"])

    def test_chart_does_not_mutate_the_store(self):
        patient = self.seed()
        before = self.ingest.observations_path.read_bytes()
        build_chart(self.store, patient["id"])
        self.assertEqual(before, self.ingest.observations_path.read_bytes())


if __name__ == "__main__":
    unittest.main(verbosity=2)
