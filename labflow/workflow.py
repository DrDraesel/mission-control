"""LabFlow workflow configuration — stations, ordering rules and validation.

LabFlow is an operational workflow tool for a sports performance lab: it walks a
provider + patient step by step through a multi-station baseline assessment
(intake form -> vitals -> InBody -> HRV -> blood panels -> EEG baseline ->
balance battery -> treadmill running form -> squats/strength).  This module is
the pure *config* layer: what the stations are, in what order they run, and
whether the config is sane.

Design notes
------------
* The station order comes from a CONFIG file.  ``workflow.yaml`` is
  **JSON-compatible YAML**: keep the file JSON so LabFlow needs no YAML
  dependency — :meth:`Workflow.from_yaml` parses it with :func:`json.loads`.
* Default rule ``'longest_last'``: stations are sorted by ``typical_minutes``
  ascending, with ``pinned`` stations kept first (in config order) — i.e. the
  longest test runs last (matches the lab's rule "longest test last").
  ``'config'`` uses the file order as-is.
* The lab owns all data locally.  This module never touches the network.
* Telegram notifications (see :mod:`labflow.notify`) contain no clinical values.

Frozen API
----------
``Station(id, name, app, description, typical_minutes, launch, capture,
requires, pinned=False, notes='', alert_text='')``

    ``launch``  = ``{'type': 'url'|'command'|'manual', 'value': str}``
    ``capture`` = ``{'type': 'manual'|'auto'|'ref', 'fields': [...],
                     'probe': str|None}``

``Workflow(name, version, sort_rule='longest_last', stations=[...])`` with
``from_yaml(path)``, ``from_dict(data)``, ``to_dict()``, ``to_json()``,
``ordered_stations()``, ``validation_errors()`` and ``get_station(id)``.

``DEFAULT_WORKFLOW`` — the seed workflow for the baseline assessment.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

__all__ = [
    "LAUNCH_TYPES",
    "CAPTURE_TYPES",
    "SORT_RULES",
    "Station",
    "Workflow",
    "DEFAULT_WORKFLOW",
]

#: Allowed ``Station.launch['type']`` values.
LAUNCH_TYPES = ("url", "command", "manual")
#: Allowed ``Station.capture['type']`` values.
CAPTURE_TYPES = ("manual", "auto", "ref")
#: Allowed ``Workflow.sort_rule`` values.
SORT_RULES = ("longest_last", "config")


def _clean(text) -> str:
    """Collapse whitespace of ``text`` into a single-spaced string."""
    return " ".join(str(text or "").split())


@dataclass
class Station:
    """One station of the assessment workflow.

    Canonical field order (frozen)::

        Station(id, name, app, description, typical_minutes, launch, capture,
                requires, pinned=False, notes='', alert_text='')

    ``requires`` (list of station ids that should already be done) defaults to
    ``[]`` when omitted/None so configs round-trip from JSON without it — it is
    reserved metadata; the engine does not re-order on it.

    ``alert_text`` is optional copy for the provider UI.  Telegram alerts use
    the frozen two-line format and deliberately ignore this field.

    ``launch`` and ``capture`` are normalised to dicts in ``__post_init__`` so
    every consumer can rely on the documented shape.
    """

    id: str
    name: str
    app: str
    description: str
    typical_minutes: float
    launch: dict
    capture: dict
    requires: list = field(default_factory=list)
    pinned: bool = False
    notes: str = ""
    alert_text: str = ""

    def __post_init__(self):
        if self.requires is None:
            self.requires = []
        elif isinstance(self.requires, str):
            self.requires = [self.requires]
        else:
            self.requires = list(self.requires)

        if not isinstance(self.launch, dict):
            self.launch = {"type": "manual", "value": ""}
        else:
            self.launch = dict(self.launch)

        if not isinstance(self.capture, dict):
            self.capture = {"type": "manual", "fields": [], "probe": None}
        else:
            self.capture = dict(self.capture)
            self.capture.setdefault("fields", [])
            self.capture.setdefault("probe", None)
        if not isinstance(self.capture.get("fields"), list):
            self.capture["fields"] = []

    # -- serialisation -------------------------------------------------
    def to_dict(self) -> dict:
        """Return the plain-dict form (JSON-serialisable), keys in frozen order."""
        capture = self.capture or {}
        return {
            "id": self.id,
            "name": self.name,
            "app": self.app,
            "description": self.description,
            "typical_minutes": self.typical_minutes,
            "launch": dict(self.launch or {}),
            "capture": {
                "type": capture.get("type"),
                "fields": list(capture.get("fields") or []),
                "probe": capture.get("probe"),
            },
            "requires": list(self.requires or []),
            "pinned": bool(self.pinned),
            "notes": self.notes or "",
            "alert_text": self.alert_text or "",
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Station":
        """Build a Station from the dict form (missing keys become blanks)."""
        data = dict(data or {})
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            app=data.get("app", ""),
            description=data.get("description", ""),
            typical_minutes=data.get("typical_minutes"),
            launch=data.get("launch") or {"type": "manual", "value": ""},
            capture=data.get("capture")
            or {"type": "manual", "fields": [], "probe": None},
            requires=data.get("requires") or [],
            pinned=bool(data.get("pinned", False)),
            notes=data.get("notes") or "",
            alert_text=data.get("alert_text") or "",
        )

    # -- presentation helpers (used by engine + notifier copy) ----------
    def launch_hint(self) -> str:
        """One-line hint for how the provider opens/launches the station."""
        launch = self.launch or {}
        ltype = str(launch.get("type") or "")
        value = str(launch.get("value") or "")
        if ltype == "url":
            return f"Open {value}"
        if ltype == "command":
            return f"Run: {value}"
        return f"Manual: {value}" if value else "Manual step"

    def capture_prompt(self) -> str:
        """One-line description of what data the station captures."""
        capture = self.capture or {}
        ctype = capture.get("type")
        fields = ", ".join(str(f) for f in (capture.get("fields") or []))
        if ctype == "auto":
            probe = capture.get("probe")
            text = f"Auto-capture from '{probe}'" if probe else "Auto-capture"
            return f"{text} (fields: {fields})" if fields else text
        if ctype == "ref":
            return f"External reference (record: {fields})" if fields else "External reference"
        if ctype == "manual":
            return f"Enter: {fields}" if fields else "Manual entry"
        return f"Unknown capture type: {ctype!r}"

    def minutes_text(self) -> str:
        """Format ``typical_minutes`` for humans, defensive against junk."""
        try:
            return f"{self.typical_minutes:g} min"
        except (TypeError, ValueError):
            return "duration unknown"


@dataclass
class Workflow:
    """The ordered collection of stations that make up the flow.

    ``sort_rule`` selects :meth:`ordered_stations` behaviour:
    ``'longest_last'`` (default) or ``'config'``.
    """

    name: str
    version: str = "1.0"
    sort_rule: str = "longest_last"
    stations: list = field(default_factory=list)

    def __post_init__(self):
        self.name = str(self.name or "LabFlow")
        self.version = str(self.version or "1.0")
        self.sort_rule = str(self.sort_rule or "longest_last")
        normalised = []
        for item in self.stations or []:
            if isinstance(item, Station):
                normalised.append(item)
            elif isinstance(item, dict):
                normalised.append(Station.from_dict(item))
            else:
                raise ValueError(f"station must be a Station or dict, got {type(item)!r}")
        self.stations = normalised

    # -- constructors ---------------------------------------------------
    @classmethod
    def from_dict(cls, data: dict) -> "Workflow":
        """Build a Workflow from the plain-dict form."""
        data = dict(data or {})
        # tolerate either a flat document or one wrapped under 'workflow'
        if "stations" not in data and isinstance(data.get("workflow"), dict):
            data = dict(data["workflow"])
        return cls(
            name=data.get("name", "LabFlow"),
            version=data.get("version", "1.0"),
            sort_rule=data.get("sort_rule", "longest_last"),
            stations=data.get("stations") or [],
        )

    @classmethod
    def from_yaml(cls, path) -> "Workflow":
        """Load a workflow config file.

        ``workflow.yaml`` is JSON-compatible YAML: keep the file JSON to avoid
        a YAML dependency — this method parses it with :func:`json.loads`.
        A document wrapped as ``{"workflow": {...}}`` is also accepted.
        """
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            raise ValueError(f"cannot read workflow file {path!r}: {exc}") from exc
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "workflow.yaml is JSON-compatible YAML; keep it JSON to avoid a "
                f"dependency. Parse error: {exc}"
            ) from exc
        if not isinstance(data, dict):
            raise ValueError("workflow config must be a JSON object at the top level")
        return cls.from_dict(data)

    # -- serialisation ---------------------------------------------------
    def to_dict(self) -> dict:
        """Plain-dict form with stations serialised in config order."""
        return {
            "name": self.name,
            "version": self.version,
            "sort_rule": self.sort_rule,
            "stations": [station.to_dict() for station in self.stations],
        }

    def to_json(self, indent: int = 2) -> str:
        """JSON string suitable for writing straight to ``workflow.yaml``."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    # -- lookups -----------------------------------------------------------
    def get_station(self, station_id) -> "Station | None":
        """Return the Station with this id, or None."""
        for station in self.stations:
            if station.id == station_id:
                return station
        return None

    def ordered_stations(self) -> list:
        """Stations in execution order per ``sort_rule``.

        ``'longest_last'``: pinned stations first (keeping config order among
        themselves), then the rest sorted by ``typical_minutes`` ascending —
        ties keep config order (stable sort).  ``'config'``: as listed.
        An unknown rule falls back to config order (``validation_errors()``
        reports it).
        """
        if self.sort_rule == "longest_last":
            pinned = [s for s in self.stations if s.pinned]
            rest = [s for s in self.stations if not s.pinned]
            rest.sort(key=_minutes_key)
            return list(pinned) + rest
        return list(self.stations)

    # -- validation ---------------------------------------------------------
    def validation_errors(self) -> list:
        """Return a list of human-readable config problems (empty == valid).

        Checked: duplicate station ids; missing station id/name; missing or
        non-numeric or negative ``typical_minutes``; unknown ``capture.type``;
        missing capture fields (``manual`` needs ``fields``, ``auto`` needs
        ``probe``); unknown ``launch.type`` (``url``/``command`` need a value);
        unknown ``sort_rule``.
        """
        errors = []
        if not self.stations:
            errors.append("workflow has no stations")
        if self.sort_rule not in SORT_RULES:
            errors.append(f"unknown sort_rule: {self.sort_rule!r}")

        counts = {}
        for index, station in enumerate(self.stations):
            sid = station.id if str(station.id or "").strip() else f"#{index}"
            if not str(station.id or "").strip():
                errors.append(f"station at index {index}: missing id")
            else:
                counts[station.id] = counts.get(station.id, 0) + 1
            if not str(station.name or "").strip():
                errors.append(f"station {sid!r}: missing name")

            minutes = station.typical_minutes
            if minutes is None:
                errors.append(f"station {sid!r}: missing typical_minutes")
            elif isinstance(minutes, bool) or not isinstance(minutes, (int, float)):
                errors.append(f"station {sid!r}: typical_minutes must be a number")
            elif minutes < 0:
                errors.append(f"station {sid!r}: negative typical_minutes ({minutes})")

            launch = station.launch if isinstance(station.launch, dict) else None
            if launch is None:
                errors.append(f"station {sid!r}: launch must be a dict")
            else:
                ltype = launch.get("type")
                if ltype not in LAUNCH_TYPES:
                    errors.append(f"station {sid!r}: unknown launch.type {ltype!r}")
                elif ltype in ("url", "command") and not str(launch.get("value") or "").strip():
                    errors.append(f"station {sid!r}: launch.value required for type {ltype!r}")

            capture = station.capture if isinstance(station.capture, dict) else None
            if capture is None:
                errors.append(f"station {sid!r}: capture must be a dict")
            else:
                ctype = capture.get("type")
                if ctype not in CAPTURE_TYPES:
                    errors.append(f"station {sid!r}: unknown capture.type {ctype!r}")
                elif ctype == "manual" and not (capture.get("fields") or []):
                    errors.append(f"station {sid!r}: manual capture requires fields")
                elif ctype == "auto" and not str(capture.get("probe") or "").strip():
                    errors.append(f"station {sid!r}: auto capture requires probe")

        for sid, count in counts.items():
            if count > 1:
                errors.append(f"duplicate station id: {sid!r} ({count} occurrences)")
        return errors


def _minutes_key(station: Station) -> float:
    """Sort key: numeric minutes, junk sorts as 0 (validation reports it)."""
    minutes = station.typical_minutes
    if isinstance(minutes, bool) or not isinstance(minutes, (int, float)):
        return 0.0
    return float(minutes)


def _station(station_id, name, app, minutes, *, description, launch, capture,
             pinned=False, notes="", alert_text="", requires=None) -> Station:
    return Station(
        id=station_id,
        name=name,
        app=app,
        description=description,
        typical_minutes=minutes,
        launch=launch,
        capture=capture,
        requires=requires or [],
        pinned=pinned,
        notes=notes,
        alert_text=alert_text,
    )


#: Seed workflow for the baseline assessment.  Config order is the natural
#: narrative order; ``ordered_stations()`` applies 'longest_last' on top of it:
#: pinned intake first, then vitals/HRV (5m) ... balance (25m) and the
#: treadmill running-form session (30m) last.
DEFAULT_WORKFLOW = Workflow(
    name="Sports Performance Lab Baseline Assessment",
    version="1.0",
    sort_rule="longest_last",
    stations=[
        _station(
            "intake", "Intake & Consent", "labflow", 15,
            description="Collect the intake form and signed consent before any measurement.",
            launch={"type": "manual", "value": "tablet intake form"},
            capture={"type": "manual", "fields": [
                "full_name", "date_of_birth", "contact", "medical_history",
                "medications", "consent_signed"], "probe": None},
            pinned=True,
            notes="Provider reviews consent before vitals.",
            alert_text="Hand the patient the intake form and confirm consent.",
        ),
        _station(
            "vitals", "Vitals (HR / Temp / SpO2)", "vitals", 5,
            description="Record resting heart rate, temperature and SpO2.",
            launch={"type": "manual", "value": "vitals cart"},
            capture={"type": "manual", "fields": [
                "heart_rate_bpm", "temperature_c", "spo2_pct"], "probe": None},
            notes="Seated rest for five minutes first.",
        ),
        _station(
            "hrv", "HRV", "hrv", 5,
            description="Capture a short resting HRV recording and enter the summary metrics.",
            launch={"type": "manual", "value": "HRV capture app"},
            capture={"type": "manual", "fields": [
                "rmssd_ms", "sdnn_ms", "mean_hr_bpm"], "probe": None},
            notes="Quiet room, no talking during capture.",
        ),
        _station(
            "inbody", "InBody Body Composition", "inbody", 10,
            description="Run the InBody scan and record weight / body composition.",
            launch={"type": "manual", "value": "InBody device"},
            capture={"type": "manual", "fields": [
                "weight_kg", "skeletal_muscle_mass_kg", "body_fat_pct", "bmi"],
                "probe": None},
            notes="Light clothing; fasted if possible.",
        ),
        _station(
            "blood_panels", "Blood Panels (external reference)", "external_lab", 10,
            description="Note the external blood panel draw and keep the lab reference id for the record.",
            launch={"type": "manual", "value": "external lab draw"},
            capture={"type": "ref", "fields": ["panel", "lab", "reference_id"],
                     "probe": None},
            notes="Reference only: results arrive from the partner lab.",
        ),
        _station(
            "squats_strength", "Squats & Strength", "strength", 15,
            description="Run the squat / strength battery and record loads and reps.",
            launch={"type": "manual", "value": "strength rack"},
            capture={"type": "manual", "fields": [
                "exercise", "load_kg", "sets", "reps", "rpe"], "probe": None},
            notes="Warm-up sets before working sets.",
        ),
        _station(
            "eeg_baseline", "EEG Baseline", "neurosync", 20,
            description="Launch NeuroSync and record the resting-state EEG baseline.",
            launch={"type": "command", "value": "neurosync record"},
            capture={"type": "auto", "fields": ["recording_id"],
                     "probe": "neurosync recordings"},
            notes="Eyes-closed resting-state baseline.",
        ),
        _station(
            "balance", "Balance Battery", "bertec", 25,
            description="Run the Bertec balance protocol battery and keep the session id.",
            launch={"type": "url", "value": "http://127.0.0.1:8765"},
            capture={"type": "auto", "fields": ["session_id", "protocol"],
                     "probe": "bertec protocol sessions"},
            notes="Barefoot with the safety harness on.",
        ),
        _station(
            "treadmill_form", "Treadmill Running Form", "runtrack", 30,
            description="Run the treadmill running-form session and keep the RunTrack session id.",
            launch={"type": "url", "value": "http://127.0.0.1:8780"},
            capture={"type": "auto", "fields": ["session_id", "metrics"],
                     "probe": "runtrack sessions"},
            notes="Longest test last; cool-down included.",
        ),
    ],
)
