"""LabFlow flow engine — drives a patient through the ordered stations.

Operational workflow tool: the engine is the conductor.  It knows the ordered
station list, keeps the patient's per-station state moving, and pushes a
notification after every mutation.  Patient data stays local (only the
notifier may leave the machine, and it carries no clinical values).

Guarantees
----------
* The engine never prints — all output goes through the notifier callbacks
  (a notifier that raises is logged to stderr; the flow never crashes).
* All persistence goes through the :class:`~labflow.patients.PatientStore`
  (atomic writes).

Frozen API
----------
``FlowEngine(store, workflow, notifier=None)``

* ``start_patient(patient_id)`` — initialises every station ``pending`` in
  ``workflow.ordered_stations()`` order; flips a ``'draft'`` patient to
  ``'active'``.  Existing step state is preserved (idempotent).
* ``current_step(patient)`` — first station not ``done``/``skipped`` in order,
  or ``None``.  (A patient that was never started is "at" the first station.)
* ``begin_step(patient_id)`` — marks the current station ``in_progress`` and
  fires ``notifier.step_started(patient, station, next_station)``.
* ``complete_step(patient_id, notes='', results=None)`` — marks it ``done``,
  appends results, fires ``notifier.step_completed(patient, station,
  next_station)``; when it was the last open station it also flips the patient
  to ``'completed'`` and fires ``notifier.flow_completed(patient)``.
* ``skip_step(patient_id, reason)`` — marks it ``skipped`` (closed for flow
  purposes) and notifies exactly like a completion.
* ``redo_step(patient_id, station_id)`` — resets that station to ``pending``
  (timestamps cleared, notes audited, results kept) and fires
  ``notifier.reminder(patient, station)``; reopens a completed flow.
* ``next_instruction(patient)`` — provider-facing text: station name,
  description, launch hint and capture prompt.
* ``progress(patient)`` — ``{'done', 'total', 'pct', 'current'}`` where
  ``done`` counts closed stations (``done`` + ``skipped``) and ``pct`` is
  floored to an int, so a flow whose last station was skipped still reports
  100%.

Return values: mutations return the saved patient dict (or ``None`` when there
is no current step).
"""

from __future__ import annotations

import sys

from .notify import NullNotifier
from .patients import new_step_entry, utc_now_iso

__all__ = ["FlowEngine", "CLOSED_STATES"]

#: Step states that close a station for flow purposes.
CLOSED_STATES = ("done", "skipped")


class FlowEngine:
    """Conducts one patient through the workflow, one station at a time."""

    def __init__(self, store, workflow, notifier=None):
        self.store = store
        self.workflow = workflow
        #: Silent by default; pass ``make_notifier(config)`` for real alerts.
        self.notifier = notifier if notifier is not None else NullNotifier()

    # -- internal helpers -------------------------------------------------
    def _ordered(self) -> list:
        return self.workflow.ordered_stations()

    def _station(self, station_id):
        return self.workflow.get_station(station_id)

    def _load(self, patient_id) -> dict:
        patient = self.store.get(patient_id)
        if patient is None:
            raise KeyError(f"unknown patient: {patient_id!r}")
        return patient

    def _entry(self, patient, station_id) -> dict:
        entry = (patient.get("steps") or {}).get(station_id)
        return entry if isinstance(entry, dict) else {}

    def _is_closed(self, patient, station_id) -> bool:
        return self._entry(patient, station_id).get("state") in CLOSED_STATES

    def _next_after(self, patient, station_id):
        """First open station after ``station_id`` in execution order."""
        ids = [station.id for station in self._ordered()]
        if station_id not in ids:
            return None
        for sid in ids[ids.index(station_id) + 1:]:
            if not self._is_closed(patient, sid):
                return self._station(sid)
        return None

    def _notify(self, event, patient, station=None, next_station=None) -> bool:
        """Call a notifier method defensively — never lets it break the flow."""
        try:
            callback = getattr(self.notifier, event, None)
            if not callable(callback):
                return False
            if event == "flow_completed":
                callback(patient)
            elif event == "reminder":
                callback(patient, station)
            else:
                callback(patient, station, next_station)
            return True
        except Exception as exc:  # pragma: no cover - defensive
            try:
                print(f"LABFLOW: notifier error in {event}: {exc}", file=sys.stderr)
            except Exception:
                pass
            return False

    # -- flow control ------------------------------------------------------
    def start_patient(self, patient_id) -> dict:
        """Initialise all stations ``pending`` in execution order; save.

        Idempotent: existing step state (done/skipped/...) is preserved, only
        missing steps are added as ``pending``.  ``'draft'`` becomes
        ``'active'``.  No notification is sent (nothing happened yet).
        """
        patient = self._load(patient_id)
        steps = patient.get("steps")
        if not isinstance(steps, dict):
            steps = {}

        ordered = {}
        for station in self._ordered():
            entry = steps.get(station.id)
            if not isinstance(entry, dict):
                entry = new_step_entry()
            else:
                entry = dict(entry)
                for key, default in new_step_entry().items():
                    entry.setdefault(key, default)
            ordered[station.id] = entry
        # keep steps for stations that are no longer in the workflow
        for sid, entry in steps.items():
            if sid not in ordered and isinstance(entry, dict):
                ordered[sid] = entry

        patient["steps"] = ordered
        if patient.get("status") in (None, "", "draft"):
            patient["status"] = "active"
        return self.store.save(patient)

    def current_step(self, patient):
        """First station in execution order not ``done``/``skipped``."""
        for station in self._ordered():
            if not self._is_closed(patient, station.id):
                return station
        return None

    def begin_step(self, patient_id):
        """Mark the current station ``in_progress``; notify ``step_started``."""
        patient = self._load(patient_id)
        station = self.current_step(patient)
        if station is None:
            return None
        entry = self._entry(patient, station.id)
        started_at = entry.get("started_at") or utc_now_iso()
        patient = self.store.update_step(
            patient_id, station.id, state="in_progress", started_at=started_at
        )
        self._notify(
            "step_started", patient, station,
            next_station=self._next_after(patient, station.id),
        )
        return patient

    def complete_step(self, patient_id, notes="", results=None):
        """Mark the current station ``done``; notify ``step_completed``.

        ``results`` may be a single item or a list; it is appended to the
        station's ``results`` list.  Completing the last open station sets the
        patient to ``'completed'`` and fires ``flow_completed``.
        """
        patient = self._load(patient_id)
        station = self.current_step(patient)
        if station is None:
            return None
        entry = self._entry(patient, station.id)
        now = utc_now_iso()

        merged_results = list(entry.get("results") or [])
        if results:
            merged_results.extend(results if isinstance(results, list) else [results])

        updates = {
            "state": "done",
            "started_at": entry.get("started_at") or now,
            "completed_at": now,
            "results": merged_results,
        }
        if notes:
            updates["notes"] = notes
        patient = self.store.update_step(patient_id, station.id, **updates)

        next_station = self.current_step(patient)
        if next_station is None:
            patient = self.store.save({**patient, "status": "completed"})
        self._notify("step_completed", patient, station, next_station=next_station)
        if next_station is None:
            self._notify("flow_completed", patient, station)
        return patient

    def skip_step(self, patient_id, reason=""):
        """Mark the current station ``skipped`` and advance the flow."""
        patient = self._load(patient_id)
        station = self.current_step(patient)
        if station is None:
            return None
        entry = self._entry(patient, station.id)
        now = utc_now_iso()
        note = str(entry.get("notes") or "")
        line = f"Skipped: {reason}" if str(reason or "").strip() else "Skipped."
        notes = f"{note}\n{line}".strip() if note else line

        patient = self.store.update_step(
            patient_id, station.id,
            state="skipped",
            started_at=entry.get("started_at") or now,
            completed_at=now,
            notes=notes,
        )
        next_station = self.current_step(patient)
        if next_station is None:
            patient = self.store.save({**patient, "status": "completed"})
        self._notify("step_completed", patient, station, next_station=next_station)
        if next_station is None:
            self._notify("flow_completed", patient, station)
        return patient

    def redo_step(self, patient_id, station_id):
        """Reset one station to ``pending`` and notify a ``reminder``.

        Timestamps are cleared, the redo is appended to the station notes and
        captured ``results`` are kept (the lab owns all data).  Redoing a
        station reopens a ``'completed'`` patient.
        """
        patient = self._load(patient_id)
        station = self._station(station_id)
        if station is None:
            raise KeyError(f"unknown station: {station_id!r}")
        entry = self._entry(patient, station_id)
        note = str(entry.get("notes") or "")
        line = f"Redo requested at {utc_now_iso()}"
        notes = f"{note}\n{line}".strip() if note else line

        patient = self.store.update_step(
            patient_id, station_id,
            state="pending",
            started_at=None,
            completed_at=None,
            notes=notes,
        )
        if patient.get("status") == "completed":
            patient = self.store.save({**patient, "status": "active"})
        self._notify("reminder", patient, station)
        return patient

    # -- read-only views ----------------------------------------------------
    def next_instruction(self, patient) -> str:
        """Provider-facing text for the current step (name, how to launch, what
        to capture).  Returns a completion line when the flow is done."""
        station = self.current_step(patient)
        if station is None:
            return "All stations complete — no next step."

        lines = [f"{station.name} — {station.minutes_text()}"]
        if station.description:
            lines.append(str(station.description))
        if station.requires:
            lines.append("Requires: " + ", ".join(str(r) for r in station.requires))
        lines.append("Launch: " + station.launch_hint())
        lines.append("Capture: " + station.capture_prompt())
        if station.notes:
            lines.append("Note: " + str(station.notes))
        if station.alert_text:
            lines.append(str(station.alert_text))
        return "\n".join(lines)

    def progress(self, patient) -> dict:
        """``{'done', 'total', 'pct', 'current'}`` for this patient.

        ``done`` counts closed stations (``done`` + ``skipped``); ``pct`` is
        floored to an int; ``current`` is the current station id or ``None``.
        """
        stations = self._ordered()
        total = len(stations)
        done = sum(1 for station in stations if self._is_closed(patient, station.id))
        pct = int(done * 100 / total) if total else 0
        current = self.current_step(patient)
        return {
            "done": done,
            "total": total,
            "pct": pct,
            "current": current.id if current is not None else None,
        }
