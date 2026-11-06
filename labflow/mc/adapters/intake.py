"""Intake adapter — the patient's own record, already owned by LabFlow.

Reads ``PatientStore`` patients (``intake`` dict + ``measurements`` list); it
never writes back.  Two synthetic sessions per patient so the timeline stays
readable:

* ``<pid>:intake``       — the intake form fields, ``intake.*``
* ``<pid>:measurements`` — the measurement log, ``vitals.*`` (or its own
  namespace when the logged metric already carries one)

Everything here is ``unverified``: it is self-reported or hand-entered, and the
spec never lets Mission Control upgrade that.
"""

from __future__ import annotations

from ..schema import (
    Observation,
    ObservationError,
    normalize_timestamp,
    slug_token,
    unit_for,
)
from . import AdapterContext, AdapterResult

SOURCE = "intake"
APP = "labflow"

#: Named namespaces a logged measurement may already use.
_ALLOWED_METRIC_PREFIXES = ("intake", "vitals", "body")


def collect(ctx: AdapterContext) -> AdapterResult:
    result = AdapterResult()
    for patient in ctx.patients:
        result.extend(_collect_patient(patient))
    return result


def _collect_patient(patient: dict) -> AdapterResult:
    result = AdapterResult()
    patient_id = str(patient.get("id") or "").strip()
    if not patient_id:
        return result

    created_at = patient.get("created_at")
    try:
        measured_at = normalize_timestamp(created_at)[0] if created_at else None
    except ObservationError:
        measured_at = None
    if measured_at is None:
        return result  # no timeline anchor; an undated intake is not a record

    provenance: dict = {
        "app": APP,
        "file": f"patients/{patient_id}.json",
        "endpoint": "PatientStore",
        "entry": "intake",
    }

    def add(session_suffix: str, metric: str, value, unit: str, analysis: str, when=None):
        result.observations.append(
            Observation(
                subject_id=patient_id,
                source=SOURCE,
                session_id=f"{patient_id}:{session_suffix}",
                measured_at=when or measured_at,
                metric=metric,
                value=value,
                unit=unit,
                quality="unverified",
                provenance=provenance,
                analysis=analysis,
            )
        )

    intake = patient.get("intake")
    intake = intake if isinstance(intake, dict) else {}
    skipped = []
    for field_name, value in intake.items():
        if isinstance(value, (dict, list, tuple)):
            skipped.append(str(field_name))
            continue
        if value is None or value == "" or isinstance(value, bool):
            continue
        column = slug_token(field_name)
        try:
            add(
                "intake",
                f"intake.{column}",
                value,
                unit_for(field_name, default=""),
                "Intake form — self-reported, not clinically verified",
            )
        except ObservationError:
            skipped.append(str(field_name))
    if skipped:
        provenance["skipped_non_scalar"] = ",".join(sorted(set(skipped)))

    measurements = patient.get("measurements")
    measurements = measurements if isinstance(measurements, list) else []
    for entry in measurements:
        if not isinstance(entry, dict):
            continue
        metric = str(entry.get("metric") or "").strip()
        if not metric:
            continue
        if "." not in metric:
            metric = f"vitals.{slug_token(metric)}"
        elif metric.split(".", 1)[0] not in _ALLOWED_METRIC_PREFIXES:
            metric = f"vitals.{slug_token(metric)}"
        value = entry.get("value")
        if value is None or value == "":
            continue
        try:
            when = normalize_timestamp(entry.get("ts"))[0] if entry.get("ts") else measured_at
        except ObservationError:
            when = measured_at
        source_note = str(entry.get("source") or "manual").strip()
        try:
            add(
                "measurements",
                metric,
                value,
                str(entry.get("unit") or unit_for(metric, default="")),
                f"Measurement log — entered via {source_note}",
                when=when,
            )
        except ObservationError:
            continue
    return result
