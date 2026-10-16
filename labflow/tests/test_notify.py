"""Tests for labflow.notify — message building with fake senders, no network."""

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

from labflow.notify import (  # noqa: E402
    ConsoleNotifier,
    Notifier,
    NullNotifier,
    TelegramNotifier,
    capture_hint,
    format_flow_completed,
    format_reminder,
    format_step_completed,
    format_step_started,
    launch_hint,
    make_notifier,
    patient_label,
    read_token_from_file,
    station_instruction,
)
from labflow.workflow import DEFAULT_WORKFLOW  # noqa: E402


class FakeResponse:
    def __init__(self, status_code=200):
        self.status_code = status_code
        self.ok = status_code == 200


class FakeSender:
    """Records (url, payload, timeout) calls; optionally raises or fails."""

    def __init__(self, status_code=200, exc=None):
        self.status_code = status_code
        self.exc = exc
        self.calls = []

    def __call__(self, url, payload, timeout):
        self.calls.append({"url": url, "payload": payload, "timeout": timeout})
        if self.exc is not None:
            raise self.exc
        return FakeResponse(self.status_code)

    def last_text(self):
        return self.calls[-1]["payload"]["text"]


VITALS = DEFAULT_WORKFLOW.get_station("vitals")
HRV = DEFAULT_WORKFLOW.get_station("hrv")
BALANCE = DEFAULT_WORKFLOW.get_station("balance")
EEG = DEFAULT_WORKFLOW.get_station("eeg_baseline")

PATIENT = {
    "id": "jane-doe-1a2b",
    "name": "Jane Doe",
    "intake": {"heart_rate_bpm": 61, "notes": "SEKRET-INTAKE"},
    "measurements": [{"metric": "weight_kg", "value": 82.4, "unit": "kg",
                      "source": "inbody", "ts": "2026-10-16T09:00:00+00:00"}],
    "steps": {"vitals": {"state": "done", "results": [{"spo2_pct": 97}]}},
}


class MessageBuildingTests(unittest.TestCase):
    def test_patient_label_first_name(self):
        self.assertEqual(patient_label(PATIENT), "Jane")
        self.assertEqual(patient_label({"name": "  "}), "Patient")
        self.assertEqual(patient_label({}), "Patient")
        self.assertEqual(patient_label(None), "Patient")
        self.assertEqual(patient_label(PATIENT, include_name=False), "Patient")

    def test_station_instruction_uses_description_and_url(self):
        text = station_instruction(BALANCE)
        self.assertIn("Bertec balance protocol", text)
        self.assertIn("open http://127.0.0.1:8765", text)
        self.assertIn("auto-capture from 'bertec protocol sessions'", text)

    def test_launch_and_capture_hints(self):
        self.assertEqual(launch_hint(BALANCE), "open http://127.0.0.1:8765")
        self.assertEqual(launch_hint(EEG), "run `neurosync record`")
        self.assertEqual(launch_hint(VITALS), "")  # manual: description carries it
        self.assertEqual(capture_hint(VITALS), "manual entry")
        self.assertEqual(capture_hint(BALANCE), "auto-capture from 'bertec protocol sessions'")

    def test_format_step_completed_frozen_format(self):
        text = format_step_completed(PATIENT, VITALS, HRV)
        title, body = text.split("\n\n")
        self.assertEqual(title, "LabFlow · Jane — Vitals (HR / Temp / SpO2) DONE")
        self.assertTrue(body.startswith("Next: HRV — "), body)

    def test_format_step_completed_last_station(self):
        text = format_step_completed(PATIENT, BALANCE, None)
        title, body = text.split("\n\n")
        self.assertEqual(title, "LabFlow · Jane — Balance Battery DONE")
        self.assertIn("Next:", body)
        self.assertIn("complete", body.lower())

    def test_format_step_started(self):
        text = format_step_started(PATIENT, VITALS, HRV)
        title, body = text.split("\n\n")
        self.assertEqual(title, "LabFlow · Jane — Vitals (HR / Temp / SpO2) STARTED")
        self.assertIn("Now: Vitals", body)
        self.assertIn("Next: HRV", body)

    def test_format_step_started_without_next(self):
        text = format_step_started(PATIENT, BALANCE, None)
        self.assertIn("STARTED", text)
        self.assertNotIn("Next:", text)

    def test_format_flow_completed_and_reminder(self):
        flow = format_flow_completed(PATIENT)
        self.assertEqual(flow.split("\n\n")[0], "LabFlow · Jane — Flow DONE")
        reminder = format_reminder(PATIENT, HRV)
        self.assertEqual(reminder.split("\n\n")[0], "LabFlow · Jane — Reminder")
        self.assertIn("Current step: HRV", reminder)


class InterfaceTests(unittest.TestCase):
    def test_base_notifier_raises_not_implemented(self):
        base = Notifier()
        for call in (
            lambda: base.step_started(PATIENT, VITALS, HRV),
            lambda: base.step_completed(PATIENT, VITALS, None),
            lambda: base.flow_completed(PATIENT),
            lambda: base.reminder(PATIENT, VITALS),
        ):
            with self.assertRaises(NotImplementedError):
                call()

    def test_null_notifier_is_a_silent_noop(self):
        notifier = NullNotifier()
        self.assertEqual(notifier.kind, "null")
        self.assertTrue(notifier.step_started(PATIENT, VITALS, HRV))
        self.assertTrue(notifier.step_completed(PATIENT, VITALS, None))
        self.assertTrue(notifier.flow_completed(PATIENT))
        self.assertTrue(notifier.reminder(PATIENT, VITALS))

    def test_console_notifier_prefix_and_content(self):
        buffer = io.StringIO()
        notifier = ConsoleNotifier(stream=buffer)
        self.assertTrue(notifier.step_completed(PATIENT, VITALS, HRV))
        output = buffer.getvalue()
        self.assertTrue(output.startswith("LABFLOW: "), output)
        self.assertIn("Vitals", output)
        self.assertIn("Next: HRV", output)

    def test_console_notifier_default_stream(self):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            ConsoleNotifier().flow_completed(PATIENT)
        self.assertIn("LABFLOW:", buffer.getvalue())
        self.assertIn("flow", buffer.getvalue().lower())

    def test_console_notifier_reminder_needs_a_station(self):
        self.assertFalse(ConsoleNotifier(stream=io.StringIO()).reminder(PATIENT, None))


class TelegramNotifierTests(unittest.TestCase):
    def make(self, **kwargs):
        self.sender = FakeSender(**kwargs)
        return TelegramNotifier("123:ABC", "4242", sender=self.sender)

    def test_step_completed_payload_and_url(self):
        notifier = self.make()
        self.assertTrue(notifier.step_completed(PATIENT, VITALS, HRV))
        call = self.sender.calls[0]
        self.assertEqual(call["url"], "https://api.telegram.org/bot123:ABC/sendMessage")
        self.assertEqual(call["payload"]["chat_id"], "4242")
        self.assertTrue(call["payload"]["disable_web_page_preview"])
        title = call["payload"]["text"].split("\n\n")[0]
        self.assertEqual(title, "LabFlow · Jane — Vitals (HR / Temp / SpO2) DONE")
        self.assertIn("Next: HRV", call["payload"]["text"])

    def test_step_started_payload(self):
        notifier = self.make()
        self.assertTrue(notifier.step_started(PATIENT, BALANCE, None))
        text = self.sender.last_text()
        self.assertIn("STARTED", text)
        self.assertIn("127.0.0.1:8765", text)

    def test_flow_completed_payload(self):
        notifier = self.make()
        self.assertTrue(notifier.flow_completed(PATIENT))
        self.assertIn("Flow DONE", self.sender.last_text())

    def test_reminder_payload(self):
        notifier = self.make()
        self.assertTrue(notifier.reminder(PATIENT, VITALS))
        self.assertIn("Reminder", self.sender.last_text())
        self.assertFalse(notifier.reminder(PATIENT, None))
        self.assertEqual(len(self.sender.calls), 1)

    def test_timeout_is_forwarded(self):
        self.sender = FakeSender()
        notifier = TelegramNotifier("t", "1", timeout=7, sender=self.sender)
        notifier.flow_completed(PATIENT)
        self.assertEqual(self.sender.calls[0]["timeout"], 7)

    def test_never_includes_clinical_values(self):
        notifier = self.make()
        for text in (
            format_step_started(PATIENT, VITALS, HRV),
            format_step_completed(PATIENT, VITALS, HRV),
            format_flow_completed(PATIENT),
            format_reminder(PATIENT, VITALS),
        ):
            for forbidden in ("61", "82.4", "97", "SEKRET-INTAKE", "heart_rate_bpm",
                              "weight_kg", "spo2_pct", "results", "measurements"):
                self.assertNotIn(forbidden, text, msg=f"{forbidden!r} leaked into {text!r}")
        notifier.step_completed(PATIENT, VITALS, HRV)
        for forbidden in ("61", "82.4", "SEKRET-INTAKE"):
            self.assertNotIn(forbidden, self.sender.last_text())

    def test_include_patient_name_false(self):
        self.sender = FakeSender()
        notifier = TelegramNotifier("t", "1", include_patient_name=False, sender=self.sender)
        notifier.step_completed(PATIENT, VITALS, HRV)
        text = self.sender.last_text()
        self.assertIn("LabFlow · Patient —", text)
        self.assertNotIn("Jane", text)

    def test_missing_token_or_chat_id_returns_false_without_sending(self):
        for notifier in (
            TelegramNotifier("", "4242", sender=FakeSender()),
            TelegramNotifier("123:ABC", "", sender=FakeSender()),
        ):
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertFalse(notifier.flow_completed(PATIENT))
        self.assertEqual(self.sender.calls if hasattr(self, "sender") else [], [])

    def test_sender_exception_returns_false_and_logs(self):
        notifier = self.make(exc=ConnectionError("no route to host"))
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            self.assertFalse(notifier.step_completed(PATIENT, VITALS, HRV))
        self.assertIn("LABFLOW:", errors.getvalue())
        self.assertIn("no route to host", errors.getvalue())

    def test_non_200_response_returns_false(self):
        notifier = self.make(status_code=500)
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            self.assertFalse(notifier.flow_completed(PATIENT))
        self.assertIn("status=500", errors.getvalue())

    def test_send_message_low_level(self):
        notifier = self.make()
        self.assertTrue(notifier.send_message("hello"))
        self.assertEqual(self.sender.last_text(), "hello")

    def test_constructor_is_tolerant(self):
        notifier = TelegramNotifier(None, None)
        self.assertEqual(notifier.bot_token, "")
        self.assertEqual(notifier.chat_id, "")
        self.assertEqual(notifier.timeout, 10)
        self.assertTrue(notifier.include_patient_name)


class TokenFileTests(unittest.TestCase):
    def test_reads_token_with_quotes_and_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / ".env"
            path.write_text(
                "# hermes env\nOTHER=1\nexport TELEGRAM_BOT_TOKEN=\"123456:ABCDEFgh\"\n",
                encoding="utf-8",
            )
            self.assertEqual(read_token_from_file(path), "123456:ABCDEFgh")

    def test_reads_single_quoted_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / ".env"
            path.write_text("TELEGRAM_BOT_TOKEN='999:xyz'\n", encoding="utf-8")
            self.assertEqual(read_token_from_file(path), "999:xyz")

    def test_missing_or_unmatched_files_return_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            no_token = pathlib.Path(tmp) / "plain.env"
            no_token.write_text("OTHER=1\n", encoding="utf-8")
            self.assertIsNone(read_token_from_file(no_token))
            self.assertIsNone(read_token_from_file(pathlib.Path(tmp) / "missing.env"))
            self.assertIsNone(read_token_from_file(None))
            empty = pathlib.Path(tmp) / "empty.env"
            empty.write_text("TELEGRAM_BOT_TOKEN=\n", encoding="utf-8")
            self.assertIsNone(read_token_from_file(empty))


class MakeNotifierTests(unittest.TestCase):
    def test_defaults_to_console(self):
        self.assertIsInstance(make_notifier(), ConsoleNotifier)
        self.assertIsInstance(make_notifier({}), ConsoleNotifier)
        self.assertIsInstance(make_notifier("garbage"), ConsoleNotifier)
        self.assertEqual(make_notifier().kind, "console")

    def test_explicit_console_and_null(self):
        self.assertIsInstance(make_notifier({"type": "console"}), ConsoleNotifier)
        self.assertIsInstance(make_notifier({"type": "null"}), NullNotifier)

    def test_telegram_with_direct_token(self):
        notifier = make_notifier({"type": "telegram", "bot_token": "123:ABC", "chat_id": "42"})
        self.assertIsInstance(notifier, TelegramNotifier)
        self.assertEqual(notifier.bot_token, "123:ABC")
        self.assertEqual(notifier.chat_id, "42")
        self.assertTrue(notifier.include_patient_name)
        self.assertEqual(notifier.timeout, 10)

    def test_telegram_with_token_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / ".env"
            path.write_text("export TELEGRAM_BOT_TOKEN=555:fromfile\n", encoding="utf-8")
            notifier = make_notifier(
                {"type": "telegram", "bot_token_file": str(path), "chat_id": 7}
            )
        self.assertIsInstance(notifier, TelegramNotifier)
        self.assertEqual(notifier.bot_token, "555:fromfile")
        self.assertEqual(notifier.chat_id, "7")

    def test_telegram_falls_back_to_console_without_token(self):
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            missing_token = make_notifier({"type": "telegram", "chat_id": "42"})
            missing_chat = make_notifier({"type": "telegram", "bot_token": "1:x"})
            missing_file = make_notifier(
                {"type": "telegram", "bot_token_file": "no/such.env", "chat_id": "42"}
            )
        for notifier in (missing_token, missing_chat, missing_file):
            self.assertIsInstance(notifier, ConsoleNotifier)
        self.assertIn("console", errors.getvalue())

    def test_unknown_type_falls_back_to_console(self):
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            notifier = make_notifier({"type": "carrier-pigeon"})
        self.assertIsInstance(notifier, ConsoleNotifier)
        self.assertIn("unknown notifier type", errors.getvalue())

    def test_options_passed_through(self):
        notifier = make_notifier({
            "type": "telegram", "bot_token": "1:x", "chat_id": "9",
            "include_patient_name": False, "timeout": "3",
        })
        self.assertFalse(notifier.include_patient_name)
        self.assertEqual(notifier.timeout, 3)
        bad_timeout = make_notifier({
            "type": "telegram", "bot_token": "1:x", "chat_id": "9", "timeout": "soon",
        })
        self.assertEqual(bad_timeout.timeout, 10)


if __name__ == "__main__":
    unittest.main()
