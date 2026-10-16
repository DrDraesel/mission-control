"""LabFlow patient store — one JSON file per patient, atomic writes.

Patient data stays local: everything is written under
``<root_dir>/patients/<id>.json``.  No network access, stdlib only.

Frozen API
----------
``PatientStore(root_dir)``

* ``create(name, intake=None)`` -> patient dict
* ``get(id)`` -> patient dict or None
* ``list()`` -> patient dicts, newest first
* ``save(patient)`` -> atomic tmp + ``os.replace``; returns the patient
* ``update_step(patient_id, station_id, **fields)`` -> patient
* ``add_measurement(patient_id, metric, value, unit, source)`` -> patient
* ``link_session(patient_id, app, session_id)`` -> patient
* ``delete(id)`` -> requires ``confirm=True``; True/False

Extra (additive) helpers: ``exists``, ``count``, ``set_status``.

Patient dict shape::

    {
      'id': 'jane-doe-1a2b',             # slug + 4 hex chars
      'name': 'Jane Doe',
      'dob': '1990-01-01',               # optional
      'contact': 'jane@example.com',     # optional
      'created_at': '2026-10-16T09:00:00.123456+00:00',
      'status': 'active' | 'completed' | 'draft',
      'intake': {field: value, ...},
      'steps': {station_id: {'state': 'pending'|'in_progress'|'done'|'skipped',
                             'started_at': str|None, 'completed_at': str|None,
                             'notes': str, 'results': [...]}},
      'measurements': [{'metric', 'value', 'unit', 'source', 'ts'}, ...],
      'linked_sessions': {app: {'ids': [session_id, ...]}},
    }
"""

from __future__ import annotations

import json
import os
import re
import secrets
import tempfile
from datetime import datetime, timezone
from pathlib import Path

__all__ = ["PatientStore", "utc_now_iso", "STEP_STATES", "PATIENT_STATUSES"]

#: Allowed ``steps[station_id]['state']`` values.
STEP_STATES = ("pending", "in_progress", "done", "skipped")
#: Allowed patient ``status`` values.
PATIENT_STATUSES = ("active", "completed", "draft")

_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")


def utc_now_iso() -> str:
    """Current UTC timestamp, ISO-8601 with microsecond precision.

    Microseconds keep ``list()`` ordering deterministic for patients created in
    the same second.
    """
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


def _slug(text) -> str:
    """Lowercase alphanumeric slug used as the patient-id prefix."""
    slug = re.sub(r"[^a-z0-9]+", "-", str(text or "").lower()).strip("-")
    return slug or "patient"


def new_step_entry() -> dict:
    """A fresh per-station step record (shared shape with the engine)."""
    return {
        "state": "pending",
        "started_at": None,
        "completed_at": None,
        "notes": "",
        "results": [],
    }


class PatientStore:
    """JSON-file-per-patient store with atomic writes.

    Every write goes to a temp file in the same directory, is flushed and
    fsync'ed, then ``os.replace``d over the target — a crash never leaves a
    half-written patient file behind.
    """

    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.patients_dir = self.root_dir / "patients"
        self.patients_dir.mkdir(parents=True, exist_ok=True)

    # -- paths -----------------------------------------------------------
    def _path(self, patient_id):
        """Path for an id, or None if the id is unsafe/unsuitable."""
        pid = str(patient_id or "")
        if not _ID_RE.match(pid) or ".." in pid or pid.endswith(".") or pid.endswith(" "):
            return None
        return self.patients_dir / f"{pid}.json"

    def exists(self, patient_id) -> bool:
        """True when this patient id has a file on disk."""
        path = self._path(patient_id)
        return bool(path and path.exists())

    def count(self) -> int:
        """Number of stored patient files."""
        return len(list(self.patients_dir.glob("*.json")))

    # -- ids ---------------------------------------------------------------
    def _new_id(self, name) -> str:
        slug = _slug(name)
        for _ in range(20):
            candidate = f"{slug}-{secrets.token_hex(2)}"
            if not self.exists(candidate):
                return candidate
        raise RuntimeError("could not allocate a unique patient id")

    # -- CRUD ---------------------------------------------------------------
    def create(self, name, intake=None, dob=None, contact=None) -> dict:
        """Create and persist a new patient (status ``'draft'``).

        ``dob`` / ``contact`` are optional additive keywords (the frozen
        schema marks them optional fields of the patient dict).

        The id is ``slug + '-' + 4 hex chars`` and is guaranteed unique on
        disk (collisions retry with a fresh suffix).
        """
        name = str(name or "").strip()
        if not name:
            raise ValueError("patient name is required")
        patient = {"id": self._new_id(name), "name": name}
        if dob:
            patient["dob"] = str(dob)
        if contact:
            patient["contact"] = str(contact)
        patient.update(
            {
                "created_at": utc_now_iso(),
                "status": "draft",
                "intake": dict(intake or {}),
                "steps": {},
                "measurements": [],
                "linked_sessions": {},
            }
        )
        self.save(patient)
        return patient

    def get(self, patient_id):
        """Load a patient dict, or None for unknown/corrupt/unsafe ids."""
        path = self._path(patient_id)
        if path is None or not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return None
        return data if isinstance(data, dict) else None

    def list(self) -> list:
        """All patients, newest first (created_at then id, descending)."""
        patients = []
        for path in self.patients_dir.glob("*.json"):
            patient = self.get(path.stem)
            if patient is not None:
                patients.append(patient)
        patients.sort(
            key=lambda p: (str(p.get("created_at") or ""), str(p.get("id") or "")),
            reverse=True,
        )
        return patients

    def save(self, patient) -> dict:
        """Atomically write a patient dict (tmp file + ``os.replace``)."""
        if not isinstance(patient, dict):
            raise ValueError("patient must be a dict")
        path = self._path(patient.get("id"))
        if path is None:
            raise ValueError(f"invalid patient id: {patient.get('id')!r}")
        if not str(patient.get("name") or "").strip():
            raise ValueError("patient name is required")

        payload = json.dumps(patient, indent=2, ensure_ascii=False)
        handle_fd, tmp_path = tempfile.mkstemp(
            dir=str(self.patients_dir), prefix=f".{path.stem}.", suffix=".tmp"
        )
        try:
            with os.fdopen(handle_fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, str(path))
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
        return patient

    # -- step helpers --------------------------------------------------------
    def _load_or_raise(self, patient_id) -> dict:
        patient = self.get(patient_id)
        if patient is None:
            raise KeyError(f"unknown patient: {patient_id!r}")
        return patient

    def update_step(self, patient_id, station_id, **fields) -> dict:
        """Merge ``fields`` into ``steps[station_id]`` (created if missing).

        Allowed keys: ``state``, ``started_at``, ``completed_at``, ``notes``,
        ``results``.  ``state`` is validated against :data:`STEP_STATES`.
        """
        patient = self._load_or_raise(patient_id)
        sid = str(station_id or "")
        if not sid:
            raise ValueError("station_id is required")
        state = fields.get("state")
        if state is not None and state not in STEP_STATES:
            raise ValueError(f"unknown step state: {state!r}")
        steps = patient.setdefault("steps", {})
        entry = steps.get(sid)
        if not isinstance(entry, dict):
            entry = new_step_entry()
            steps[sid] = entry
        for key, value in fields.items():
            entry[key] = value
        self.save(patient)
        return patient

    def add_measurement(self, patient_id, metric, value, unit, source) -> dict:
        """Append a measurement ``{metric, value, unit, source, ts}`` (local only)."""
        patient = self._load_or_raise(patient_id)
        if not str(metric or "").strip():
            raise ValueError("metric is required")
        patient.setdefault("measurements", []).append(
            {
                "metric": str(metric),
                "value": value,
                "unit": str(unit or ""),
                "source": str(source or ""),
                "ts": utc_now_iso(),
            }
        )
        self.save(patient)
        return patient

    def link_session(self, patient_id, app, session_id) -> dict:
        """Register an external app session id under ``linked_sessions[app]``."""
        patient = self._load_or_raise(patient_id)
        app = str(app or "").strip()
        if not app:
            raise ValueError("app is required")
        if session_id is None or str(session_id) == "":
            raise ValueError("session_id is required")
        sessions = patient.setdefault("linked_sessions", {})
        bucket = sessions.get(app)
        if not isinstance(bucket, dict):
            bucket = {"ids": []}
            sessions[app] = bucket
        ids = bucket.setdefault("ids", [])
        sid = str(session_id)
        if sid not in ids:
            ids.append(sid)
        self.save(patient)
        return patient

    def delete(self, patient_id, confirm=False) -> bool:
        """Delete a patient file.  Requires ``confirm=True`` (else ValueError).

        Returns True when a file was removed, False when the id was unknown.
        """
        if not confirm:
            raise ValueError("delete requires confirm=True")
        path = self._path(patient_id)
        if path is None or not path.exists():
            return False
        try:
            path.unlink()
        except OSError:
            return False
        return True

    def set_status(self, patient_id, status) -> dict:
        """Set patient ``status`` (one of :data:`PATIENT_STATUSES`)."""
        if status not in PATIENT_STATUSES:
            raise ValueError(f"unknown patient status: {status!r}")
        patient = self._load_or_raise(patient_id)
        patient["status"] = status
        self.save(patient)
        return patient
