"""Tests for labflow.mirror_display — no device, no network.

The adb/HTTP edges are patched; what is asserted here is the contract that
matters for the unit: refuse to run without LabFlow or without the mirror,
tunnel the right port, and give every launch a distinct URL (the kiosk's
BrowserActivity silently ignores an identical intent and leaves a stale page).
"""

from __future__ import annotations

import pathlib
import subprocess
import sys
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from labflow import mirror_display as md  # noqa: E402


class LaunchTests(unittest.TestCase):
    def test_launch_targets_the_kiosk_browser_activity(self):
        calls = []

        def fake_run(args, timeout=20.0):
            calls.append(args)
            return subprocess.CompletedProcess(args, 0, "", "")

        with mock.patch.object(md, "_run", fake_run):
            md.launch("adb", "192.168.1.110", "http://127.0.0.1:8790/mirror")

        self.assertEqual(len(calls), 1)
        args = calls[0]
        self.assertIn("ai.dongmi.barbell/.ui.sys.BrowserActivity", args)
        url = args[args.index("-d") + 1]
        self.assertTrue(url.startswith("http://127.0.0.1:8790/mirror#"), url)

    def test_every_launch_url_is_distinct(self):
        urls = []

        def fake_run(args, timeout=20.0):
            urls.append(args[args.index("-d") + 1])
            return subprocess.CompletedProcess(args, 0, "", "")

        with mock.patch.object(md, "_run", fake_run), mock.patch.object(md.time, "time", side_effect=[10, 20]):
            md.launch("adb", "10.0.0.5", "http://127.0.0.1:8790/mirror")
            md.launch("adb", "10.0.0.5", "http://127.0.0.1:8790/mirror")

        self.assertNotEqual(urls[0], urls[1])

    def test_reverse_tunnels_the_labflow_port(self):
        calls = []

        def fake_run(args, timeout=20.0):
            calls.append(args)
            return subprocess.CompletedProcess(args, 0, "", "")

        with mock.patch.object(md, "_run", fake_run):
            md.push_reverse("adb", "192.168.1.110", 8790)

        self.assertIn("reverse", calls[0])
        self.assertIn("tcp:8790", calls[0])


class GuardTests(unittest.TestCase):
    def test_refuses_to_run_without_labflow(self):
        with mock.patch.object(md, "_labflow_up", return_value=False), \
             mock.patch.object(md, "connect") as connect:
            self.assertEqual(md.main(["--once"]), 2)
            connect.assert_not_called()

    def test_refuses_when_the_device_is_missing(self):
        with mock.patch.object(md, "_labflow_up", return_value=True), \
             mock.patch.object(md, "connect", return_value=False), \
             mock.patch.object(md, "launch") as launch:
            self.assertEqual(md.main(["--once"]), 3)
            launch.assert_not_called()

    def test_refuses_a_look_alike_android_box(self):
        with mock.patch.object(md, "_labflow_up", return_value=True), \
             mock.patch.object(md, "connect", return_value=True), \
             mock.patch.object(md, "is_mirror", return_value=False), \
             mock.patch.object(md, "launch") as launch:
            self.assertEqual(md.main(["--once"]), 4)
            launch.assert_not_called()

    def test_once_pushes_and_returns(self):
        pushed = {}
        with mock.patch.object(md, "_labflow_up", return_value=True), \
             mock.patch.object(md, "connect", return_value=True), \
             mock.patch.object(md, "is_mirror", return_value=True), \
             mock.patch.object(md, "push_reverse") as reverse, \
             mock.patch.object(md, "launch", side_effect=lambda a, i, u: pushed.setdefault("url", u)):
            self.assertEqual(md.main(["--once", "--port", "8790"]), 0)

        reverse.assert_called_once()
        self.assertEqual(reverse.call_args[0][2], 8790)
        self.assertEqual(pushed["url"], "http://127.0.0.1:8790/mirror")

    def test_patient_pin_is_added_to_the_url(self):
        pushed = {}
        with mock.patch.object(md, "_labflow_up", return_value=True), \
             mock.patch.object(md, "connect", return_value=True), \
             mock.patch.object(md, "is_mirror", return_value=True), \
             mock.patch.object(md, "push_reverse"), \
             mock.patch.object(md, "launch", side_effect=lambda a, i, u: pushed.setdefault("url", u)):
            md.main(["--once", "--patient", "jane-01"])

        self.assertIn("patient=jane-01", pushed["url"])


if __name__ == "__main__":
    unittest.main()
