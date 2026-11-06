"""Mission Control — the canonical observation record.

One number, one row, one owner (see ``labflow/docs/MC-EHR-SPEC.md``).

Every measurement that lands in Mission Control is an :class:`Observation`.
The rules encoded here are the contract's hard edges:

* **Namespaces are fixed.** ``bertec.*``, ``runtrack.*``, ``eeg.*``, ``body.*``,
  ``vitals.*``, ``intake.*``.  A source may only write the prefixes it owns
  (:data:`SOURCE_PREFIXES`), so no adapter can invent a channel.
* **Provenance is mandatory.**  A number without a source session id and a
  file/endpoint locator raises :class:`ObservationError` (a ``ValueError``).
* **Quality is carried, never invented.**  Callers pass what the source said;
  :func:`normalize_quality` only maps vocabulary, and unknown words become
  ``flagged`` — never ``verified``.
* **Identity is stable.**  The dedupe key is
  ``sha1(source|session_id|metric|measured_at)``; ingest is idempotent on it.

This module is stdlib-only and has no I/O.
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping

__all__ = [
    "SOURCES",
    "QUALITIES",
    "SOURCE_PREFIXES",
    "SOURCE_LABELS",
    "SOURCE_ORDER",
    "QUALITY_TRUST",
    "Observation",
    "ObservationError",
    "coerce_measured_at",
    "dedupe_key",
    "metric_prefix",
    "normalize_quality",
    "normalize_timestamp",
    "unit_for",
]

#: Every source Mission Control accepts.
SOURCES = ("bertec", "runtrack", "neurosync", "inbody", "intake", "manual")

#: The only legal ``quality`` values.
QUALITIES = ("verified", "unverified", "flagged", "incomplete")

#: Metric prefixes each source is allowed to write.
#:
#: ``manual`` may write the patient-entered namespaces but never a device's,
#: so a hand-typed number can never masquerade as a plate or EEG reading.
SOURCE_PREFIXES = {
    "bertec": ("bertec",),
    "runtrack": ("runtrack",),
    "neurosync": ("eeg",),
    "inbody": ("body",),
    "intake": ("intake", "vitals"),
    "manual": ("intake", "vitals", "body"),
}

#: Display labels (UI/AI text only, never logic).
SOURCE_LABELS = {
    "bertec": "Bertec",
    "runtrack": "RunTrack",
    "neurosync": "NeuroSync",
    "inbody": "InBody",
    "intake": "Intake",
    "manual": "Manual",
}

#: Stable presentation order for charts.
SOURCE_ORDER = ("bertec", "runtrack", "neurosync", "inbody", "intake", "manual")

#: Trust ranking used to enforce "quality is never upgraded".
#:
#: Higher is more trustworthy.  ``flagged`` and ``incomplete`` both rank below
#: ``unverified`` because a named problem is worse than an unnamed one.  Ingest
#: keeps the lowest-ranked quality ever seen for a dedupe key.
QUALITY_TRUST = {
    "verified": 3,
    "unverified": 2,
    "incomplete": 1,
    "flagged": 1,
}

#: Source vocabularies mapped onto :data:`QUALITIES`.
#:
#: Anything unrecognised but non-empty becomes ``flagged`` — we never turn an
#: unknown word into ``verified``.
_QUALITY_ALIASES = {
    "verified": "verified",
    "verify": "verified",
    "complete": "verified",
    "completed": "verified",
    "ok": "verified",
    "okay": "verified",
    "pass": "verified",
    "passed": "verified",
    "good": "verified",
    "valid": "verified",
    "unverified": "unverified",
    "unknown": "unverified",
    "none": "unverified",
    "pending": "unverified",
    "flagged": "flagged",
    "flag": "flagged",
    "warn": "flagged",
    "warning": "flagged",
    "suspect": "flagged",
    "uncalibrated": "flagged",
    "incomplete": "incomplete",
    "partial": "incomplete",
    "aborted": "incomplete",
}

#: Keys in ``provenance`` that count as a file/endpoint locator.
PROVENANCE_LOCATORS = ("file", "endpoint", "path", "dir", "url")

_METRIC_RE = re.compile(r"^(?P<prefix>[a-z]+)\.(?P<body>[A-Za-z0-9_][A-Za-z0-9_.\-]*)$")
_SUBJECT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._\-]*$")
_SEGMENT_RE = re.compile(r"[^A-Za-z0-9_]+")

_TIMESTAMP_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y%m%dT%H%M%S",
    "%Y-%m-%d_%H%M%S",
    "%Y-%m-%d",
)


class ObservationError(ValueError):
    """A record that would corrupt the chart — always a ``ValueError``."""


def dedupe_key(source, session_id, metric, measured_at) -> str:
    """``sha1(source|session_id|metric|measured_at)`` — the identity of a row."""
    payload = f"{source}|{session_id}|{metric}|{measured_at}"
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def normalize_timestamp(value) -> tuple[str, bool]:
    """Return ``(iso_utc, assumed_tz)`` for a timestamp-ish value.

    Naive timestamps are pinned to UTC and the caller is told so, because the
    apps write local wall-clock strings without an offset.  The assumption is
    recorded in provenance (``tz_assumed``) rather than silently baked in.
    """
    assumed = False
    if isinstance(value, datetime):
        stamp, assumed = value, value.tzinfo is None
    else:
        text = str(value or "").strip()
        if not text:
            raise ObservationError("measured_at is required")
        stamp = None
        normalized = text[:-1] + "+00:00" if text.endswith(("Z", "z")) else text
        try:
            stamp = datetime.fromisoformat(normalized)
            assumed = stamp.tzinfo is None
        except ValueError:
            for fmt in _TIMESTAMP_FORMATS:
                try:
                    stamp = datetime.strptime(text, fmt)
                except ValueError:
                    continue
                assumed = True
                break
        if stamp is None:
            raise ObservationError(f"unparseable timestamp: {value!r}")
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
        assumed = True
    return stamp.astimezone(timezone.utc).isoformat(), assumed


def coerce_measured_at(value) -> str:
    """Normalized ISO-8601 UTC timestamp, or raise :class:`ObservationError`."""
    return normalize_timestamp(value)[0]


def normalize_quality(value, default: str = "unverified") -> str:
    """Map a source's quality word onto :data:`QUALITIES`.

    ``None``/empty uses ``default``.  Unknown non-empty words become
    ``flagged``: a problem we cannot name is still a problem.
    """
    if value is None or isinstance(value, bool):
        return default
    text = str(value).strip().lower()
    if not text:
        return default
    if text in QUALITIES:
        return text
    return _QUALITY_ALIASES.get(text, "flagged")


def metric_prefix(metric) -> str:
    """The namespace of a metric key, or ``''`` when malformed."""
    match = _METRIC_RE.match(str(metric or ""))
    return match.group("prefix") if match else ""


def slug_token(text, default: str = "value") -> str:
    """Safe metric segment: ``eo firm`` -> ``eo_firm``."""
    token = _SEGMENT_RE.sub("_", str(text or "")).strip("_").lower()
    return token or default


def unit_for(name, default: str = "index") -> str:
    """Best-effort unit from a metric name's suffix.

    Only a convenience for adapters — it never changes a value.
    """
    key = str(name or "").lower()
    suffixes = (
        ("_uv2", "µV²"),
        ("_kg", "kg"),
        ("_cm", "cm"),
        ("_pct", "%"),
        ("_rel", "%"),
        ("_deg", "deg"),
        ("_mm_s", "mm/s"),
        ("_mm", "mm"),
        ("_ms", "ms"),
        ("_bpm", "bpm"),
        ("_hz", "Hz"),
        ("_watts", "W"),
        ("_w", "W"),
        ("_n", "N"),
        ("_s", "s"),
    )
    for suffix, unit in suffixes:
        if key.endswith(suffix):
            return unit
    return default


def _require_text(value, field_name, *, allow_pipe: bool = False) -> str:
    if value is None:
        raise ObservationError(f"{field_name} is required")
    text = str(value).strip()
    if not text:
        raise ObservationError(f"{field_name} is required")
    if "\n" in text or "\r" in text:
        raise ObservationError(f"{field_name} must be a single line")
    if not allow_pipe and "|" in text:
        # '|' is the dedupe-key separator; a value containing it would let two
        # different records hash to the same key.
        raise ObservationError(f"{field_name} must not contain '|'")
    return text


@dataclass(frozen=True)
class Observation:
    """One metric from one session of one source, for one patient."""

    subject_id: str
    source: str
    session_id: str
    measured_at: str
    metric: str
    value: Any = None
    unit: str = ""
    quality: str = "unverified"
    provenance: Mapping[str, Any] | None = None
    analysis: str = ""
    ai_text: str = ""
    ai_model: str = ""
    _key: str = field(default="", init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        subject = str(self.subject_id or "").strip()
        if not _SUBJECT_RE.match(subject):
            raise ObservationError(f"invalid subject_id: {self.subject_id!r}")

        source = str(self.source or "").strip().lower()
        if source not in SOURCES:
            raise ObservationError(f"unknown source: {self.source!r}")

        session = _require_text(self.session_id, "session_id")

        measured_at = coerce_measured_at(self.measured_at)

        metric = _require_text(self.metric, "metric")
        match = _METRIC_RE.match(metric)
        if not match:
            raise ObservationError(f"malformed metric (want '<namespace>.<name>'): {metric!r}")
        allowed = SOURCE_PREFIXES[source]
        if match.group("prefix") not in allowed:
            raise ObservationError(
                f"metric {metric!r} is outside source {source!r}'s namespace "
                f"({', '.join(allowed)})"
            )

        quality = normalize_quality(self.quality)
        if quality not in QUALITIES:  # defensive; aliases already land in QUALITIES
            raise ObservationError(f"unknown quality: {self.quality!r}")

        value = self._clean_value(self.value)
        unit = "" if self.unit is None else str(self.unit).strip()
        provenance = self._clean_provenance(self.provenance)

        # Quality floor: a source that only ever saw a warning cannot hand us a
        # "verified" word for the same record, because normalization already
        # maps the source vocabulary.  Callers may never *raise* quality here —
        # they pass what they saw.

        object.__setattr__(self, "subject_id", subject)
        object.__setattr__(self, "source", source)
        object.__setattr__(self, "session_id", session)
        object.__setattr__(self, "measured_at", measured_at)
        object.__setattr__(self, "metric", metric)
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "unit", unit)
        object.__setattr__(self, "quality", quality)
        object.__setattr__(self, "provenance", provenance)
        object.__setattr__(self, "analysis", str(self.analysis or ""))
        object.__setattr__(self, "ai_text", str(self.ai_text or ""))
        object.__setattr__(self, "ai_model", str(self.ai_model or ""))
        object.__setattr__(
            self, "_key", dedupe_key(source, session, metric, measured_at)
        )

    # -- validation helpers --------------------------------------------------
    @staticmethod
    def _clean_value(value):
        if value is None:
            return None
        if isinstance(value, bool):  # bool is an int; a flag is not a measurement
            raise ObservationError("value must be numeric or text, not boolean")
        if isinstance(value, (int, float)):
            number = float(value)
            if math.isnan(number) or math.isinf(number):
                raise ObservationError("value must be finite")
            return number
        if isinstance(value, str):
            text = value.strip()
            if not text:
                raise ObservationError("value must not be empty text")
            return text
        raise ObservationError(f"unsupported value type: {type(value).__name__}")

    @staticmethod
    def _clean_provenance(provenance) -> dict:
        if not isinstance(provenance, Mapping) or not provenance:
            raise ObservationError(
                "provenance is required: {app, file|endpoint, ...} identifying "
                "where this number came from"
            )
        cleaned = {str(k): v for k, v in provenance.items() if v is not None and v != ""}
        app = str(cleaned.get("app") or "").strip()
        if not app:
            raise ObservationError("provenance.app is required")
        if not any(str(cleaned.get(k) or "").strip() for k in PROVENANCE_LOCATORS):
            raise ObservationError(
                "provenance needs a file/endpoint locator "
                f"({', '.join(PROVENANCE_LOCATORS)})"
            )
        cleaned["app"] = app
        return cleaned

    # -- identity / serialization -------------------------------------------
    @property
    def key(self) -> str:
        """The sha1 dedupe key."""
        return self._key

    def dedupe_key(self) -> str:
        return self._key

    def to_dict(self) -> dict:
        """JSON-ready row, key order fixed so the file diffs cleanly."""
        return {
            "subject_id": self.subject_id,
            "source": self.source,
            "session_id": self.session_id,
            "measured_at": self.measured_at,
            "metric": self.metric,
            "value": self.value,
            "unit": self.unit,
            "quality": self.quality,
            "provenance": dict(self.provenance or {}),
            "analysis": self.analysis,
            "ai_text": self.ai_text,
            "ai_model": self.ai_model,
            "dedupe_key": self._key,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Observation":
        """Rebuild a row (extra keys such as ``dedupe_key`` are ignored)."""
        if not isinstance(data, Mapping):
            raise ObservationError("observation must be a mapping")
        return cls(
            subject_id=data.get("subject_id"),
            source=data.get("source"),
            session_id=data.get("session_id"),
            measured_at=data.get("measured_at"),
            metric=data.get("metric"),
            value=data.get("value"),
            unit=data.get("unit", ""),
            quality=data.get("quality", "unverified"),
            provenance=data.get("provenance"),
            analysis=data.get("analysis", ""),
            ai_text=data.get("ai_text", ""),
            ai_model=data.get("ai_model", ""),
        )

    def __str__(self) -> str:  # pragma: no cover - debugging aid
        return f"{self.metric}={self.value}{(' ' + self.unit) if self.unit else ''}"


def ensure_observation(item) -> Observation:
    """Coerce a mapping or an :class:`Observation` into a validated one."""
    if isinstance(item, Observation):
        return item
    if isinstance(item, Mapping):
        return Observation.from_dict(item)
    raise ObservationError(f"cannot coerce {type(item).__name__} into an Observation")
