"""Tests for labflow.result_probes - mock fetchers, no live servers needed."""

from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from labflow import result_probes as probes  # noqa: E402


def fetch_ok(document):
    def fetch(url, timeout):
        return 200, json.dumps(document)

    return fetch


def fetch_status(status, text=""):
    def fetch(url, timeout):
        return status, text

    return fetch


def fetch_raises(exc):
    def fetch(url, timeout):
        raise exc

    return fetch


def tcp(open_):
    def check(host, port, timeout=None):
        return open_

    return check


class BertecProbeTests(unittest.TestCase):
    def test_healthy_sessions(self):
        doc = {
            "ok": True,
            "sessions": [
                {"id": "s2", "completed_at": "2026-10-16T10:00:00+00:00",
                 "protocol_label": "Balance Battery", "athlete": "A"},
                {"id": "s1", "completed_at": "2026-10-15T09:00:00+00:00",
                 "protocol_label": "Baseline", "athlete": "B"},
            ],
        }
        result = probes.probe_bertec(fetch=fetch_ok(doc))
        self.assertTrue(result["available"])
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["latest"]["id"], "s2")
        self.assertEqual(result["latest"]["protocol_label"], "Balance Battery")
        self.assertEqual(result["latest"]["completed_at"], "2026-10-16T10:00:00+00:00")
        self.assertNotIn("error", result)

    def test_latest_picks_newest_even_when_list_is_unordered(self):
        doc = {"ok": True, "sessions": [
            {"id": "old", "completed_at": "2026-01-01T00:00:00+00:00"},
            {"id": "new", "started_at": "2026-09-01T00:00:00+00:00"},  # no completed_at
        ]}
        result = probes.probe_bertec(fetch=fetch_ok(doc))
        self.assertEqual(result["latest"]["id"], "new")

    def test_empty_sessions_is_available_with_zero_count(self):
        result = probes.probe_bertec(fetch=fetch_ok({"ok": True, "sessions": []}))
        self.assertTrue(result["available"])
        self.assertEqual(result["count"], 0)
        self.assertIsNone(result["latest"])

    def test_connection_refused_reports_error(self):
        result = probes.probe_bertec(
            fetch=fetch_raises(ConnectionRefusedError("[WinError 10061] refused"))
        )
        self.assertFalse(result["available"])
        self.assertEqual(result["app"], "bertec")
        self.assertIn("ConnectionRefusedError", result["error"])

    def test_http_404_is_unavailable_with_detail(self):
        result = probes.probe_bertec(
            fetch=fetch_status(404, '{"detail":"Not Found"}')
        )
        self.assertFalse(result["available"])
        self.assertIn("HTTP 404", result["error"])
        self.assertIn("Not Found", result["error"])

    def test_malformed_json_is_unavailable(self):
        result = probes.probe_bertec(fetch=fetch_status(200, "not json at all"))
        self.assertFalse(result["available"])
        self.assertIn("malformed JSON", result["error"])

    def test_wrong_shape_is_unavailable(self):
        result = probes.probe_bertec(fetch=fetch_status(200, json.dumps({"ok": True})))
        self.assertFalse(result["available"])
        self.assertIn("malformed response", result["error"])

    def test_dict_style_fetcher_result_is_accepted(self):
        def fetch(url, timeout):
            return {"status": 200, "text": json.dumps({"ok": True, "sessions": []})}

        result = probes.probe_bertec(fetch=fetch)
        self.assertTrue(result["available"])


class RunTrackProbeTests(unittest.TestCase):
    def test_healthy_sessions_latest_by_ended_ts(self):
        doc = {"sessions": [
            {"id": 3, "patient_name": "Anna", "ended_ts": "2026-10-05 13:00:00",
             "discipline": "running", "status": "complete"},
            {"id": 7, "patient_name": "Bob", "ended_ts": "2026-10-06 09:30:00",
             "discipline": "cycling", "status": "complete"},
        ]}
        result = probes.probe_runtrack(fetch=fetch_ok(doc), tcp_check=tcp(True))
        self.assertTrue(result["available"])
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["latest"]["id"], 7)
        self.assertEqual(result["latest"]["patient_name"], "Bob")
        self.assertEqual(result["latest"]["ended_ts"], "2026-10-06 09:30:00")

    def test_refused_and_port_closed(self):
        result = probes.probe_runtrack(
            fetch=fetch_raises(ConnectionRefusedError("refused")), tcp_check=tcp(False)
        )
        self.assertFalse(result["available"])
        self.assertIn("ConnectionRefusedError", result["error"])

    def test_refused_but_port_open_reports_note(self):
        result = probes.probe_runtrack(
            fetch=fetch_raises(TimeoutError("timed out")), tcp_check=tcp(True)
        )
        self.assertTrue(result["available"])
        self.assertIsNone(result["count"])
        self.assertIsNone(result["latest"])
        self.assertIn("port open", result["note"])

    def test_html_body_with_open_port_is_available_with_note(self):
        result = probes.probe_runtrack(
            fetch=fetch_status(200, "<!doctype html><html>hi</html>"), tcp_check=tcp(True)
        )
        self.assertTrue(result["available"])
        self.assertIsNone(result["count"])
        self.assertIn("non-JSON", result["note"])

    def test_404_with_closed_port_is_unavailable(self):
        result = probes.probe_runtrack(
            fetch=fetch_status(404, "{}"), tcp_check=tcp(False)
        )
        self.assertFalse(result["available"])
        self.assertIn("HTTP 404", result["error"])

    def test_wrong_shape_with_open_port_falls_back(self):
        result = probes.probe_runtrack(
            fetch=fetch_status(200, json.dumps({"patients": []})), tcp_check=tcp(True)
        )
        self.assertTrue(result["available"])
        self.assertIn("sessions", result["note"])


class NeuroSyncProbeTests(unittest.TestCase):
    def _make_session(self, folder, name="raw.csv", age_s=0):
        folder.mkdir(parents=True, exist_ok=True)
        (folder / name).write_text("t,ch1\n0,1\n", encoding="utf-8")
        if age_s:
            old = (datetime.now() - timedelta(seconds=age_s)).timestamp()
            os.utime(folder / name, (old, old))
            os.utime(folder, (old, old))
        return folder

    def test_counts_both_layouts(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / "recordings"
            root.mkdir()
            legacy = self._make_session(root / "20260929_120007_263087", age_s=1000)
            subject = self._make_session(
                root / "subjects" / "anna_555" / "20261001_090000_000001"
            )
            result = probes.probe_neurosync(root=root)
            self.assertTrue(result["available"])
            self.assertEqual(result["count"], 2)
            self.assertEqual(result["latest"]["id"], subject.name)
            self.assertIn("modified_at", result["latest"])
            self.assertEqual(result["path"], str(root))
            self.assertTrue(str(legacy) in json.dumps(result) or legacy.exists())

    def test_missing_dir_is_unavailable_never_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = probes.probe_neurosync(root=pathlib.Path(tmp) / "nope")
            self.assertFalse(result["available"])
            self.assertIn("not found", result["error"])

    def test_empty_dir_counts_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            result = probes.probe_neurosync(root=root)
            self.assertTrue(result["available"])
            self.assertEqual(result["count"], 0)
            self.assertIsNone(result["latest"])


class ProbeAllTests(unittest.TestCase):
    def test_probe_all_shape_and_never_raises(self):
        def explode(url, timeout):
            raise OSError("everything is down")

        with tempfile.TemporaryDirectory() as tmp:
            result = probes.probe_all(
                fetch=explode, neurosync_root=pathlib.Path(tmp) / "missing"
            )
        self.assertIn("checked_at", result)
        self.assertEqual(set(result["apps"]), {"bertec", "runtrack", "neurosync"})
        for summary in result["apps"].values():
            self.assertIsInstance(summary["available"], bool)
            self.assertIn("count", summary)

    def test_probe_all_healthy_mix(self):
        docs = {
            probes.BERTEC_SESSIONS_URL: {"ok": True, "sessions": []},
            probes.RUNTRACK_SESSIONS_URL: {"sessions": [{"id": 1, "ended_ts": "2026-01-01 00:00:00"}]},
        }

        def fetch(url, timeout):
            return 200, json.dumps(docs[url])

        with tempfile.TemporaryDirectory() as tmp:
            apps = probes.probe_all(fetch=fetch, neurosync_root=pathlib.Path(tmp))["apps"]
        self.assertTrue(apps["bertec"]["available"])
        self.assertTrue(apps["runtrack"]["available"])
        self.assertEqual(apps["runtrack"]["count"], 1)
        self.assertTrue(apps["neurosync"]["available"])

    def test_default_fetcher_exists_and_is_callable(self):
        self.assertTrue(callable(probes.default_fetch))


if __name__ == "__main__":
    unittest.main()
