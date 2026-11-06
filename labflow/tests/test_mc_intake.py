"""Tests for the intake-kiosk bridge (``POST /api/intake``).

The kiosk (DrDraesel/Intakekiosk) keeps nothing; it POSTs one completed
check-in to the clinic's LabFlow.  These tests pin the contract it relies on:

* the kiosk's payload shape maps onto a LabFlow patient (name / dob / contact),
* a retried delivery with the same submission id never duplicates the patient,
* a payload without a name is a 400, not a crash,
* the CORS preflight is allowed for the loopback dev origin and refused for
  anything else (patient data must not be postable by an arbitrary page).
"""

from __future__ import annotations

import pathlib
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from labflow.app import create_app  # noqa: E402
from labflow.notify import NullNotifier  # noqa: E402
from labflow.patients import PatientStore  # noqa: E402


def _payload(submission_id="kiosk-abc-1", name="Ada Lovelace"):
    return {
        "id": submission_id,
        "submittedAt": "2026-11-06T15:04:05.000Z",
        "locale": "es-US",
        "category": "New patient",
        "attention": True,
        "patient": {
            "name": name,
            "dob": "1990-01-01",
            "phone": "305-555-0100",
            "email": "ada@example.test",
            "address": "1 Test Way",
            "insurance": "Demo Health",
            "memberId": "M-1",
        },
        "fields": {
            "name": {"value": name, "confirmed": True, "source": "voice", "timestamp": "t1"},
            "pain": {"value": "3 out of 10", "confirmed": True, "source": "voice", "timestamp": "t2"},
        },
        "transcript": [
            {"original": "The pain is three out of ten.", "timestamp": "t2", "source": "voice", "questionId": "pain"}
        ],
    }


class IntakeKioskTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = pathlib.Path(self._tmp.name)
        self.store = PatientStore(self.root)
        self.app = create_app(config={}, store=self.store, notifier=NullNotifier())
        self.client = TestClient(self.app)

    def test_kiosk_submission_creates_a_patient(self):
        response = self.client.post("/api/intake", json=_payload())
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["ok"])
        self.assertFalse(body["deduped"])

        patient = body["patient"]
        self.assertEqual(patient["name"], "Ada Lovelace")
        self.assertEqual(patient["dob"], "1990-01-01")
        self.assertEqual(patient["contact"], "305-555-0100")
        self.assertEqual(patient["status"], "active")
        intake = patient["intake"]
        self.assertEqual(intake["kiosk_submission_id"], "kiosk-abc-1")
        self.assertEqual(intake["source"], "intake_kiosk")
        self.assertEqual(intake["locale"], "es-US")
        self.assertTrue(intake["attention"])
        self.assertIn("pain", intake["fields"])
        self.assertEqual(intake["transcript"][0]["questionId"], "pain")

        # The flow is initialised, not left as a draft.
        listed = self.client.get("/api/patients").json()["patients"]
        self.assertEqual(len(listed), 1)

    def test_retried_delivery_is_deduped(self):
        first = self.client.post("/api/intake", json=_payload()).json()
        second = self.client.post("/api/intake", json=_payload()).json()
        self.assertTrue(second["deduped"])
        self.assertEqual(second["patient"]["id"], first["patient"]["id"])
        self.assertEqual(len(self.client.get("/api/patients").json()["patients"]), 1)

    def test_a_different_submission_creates_a_second_patient(self):
        self.client.post("/api/intake", json=_payload("kiosk-1", "Ada Lovelace"))
        self.client.post("/api/intake", json=_payload("kiosk-2", "Grace Hopper"))
        self.assertEqual(len(self.client.get("/api/patients").json()["patients"]), 2)

    def test_missing_name_is_400(self):
        payload = _payload()
        payload["patient"]["name"] = "   "
        response = self.client.post("/api/intake", json=payload)
        self.assertEqual(response.status_code, 400, response.text)
        self.assertIn("name", response.json()["error"])

    def test_cors_allows_the_loopback_kiosk_origin_only(self):
        allowed = self.client.options(
            "/api/intake",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        self.assertIn(allowed.status_code, (200, 204), allowed.text)
        self.assertEqual(allowed.headers.get("access-control-allow-origin"), "http://127.0.0.1:5173")

        refused = self.client.options(
            "/api/intake",
            headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"},
        )
        self.assertIsNone(refused.headers.get("access-control-allow-origin"))


if __name__ == "__main__":
    unittest.main()
