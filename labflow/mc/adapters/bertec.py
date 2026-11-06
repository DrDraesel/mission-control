"""Bertec Jump adapter — read-only over ``bertec-jump/data/protocols/*/session.json``.

Known session shape (verified against the live app)::

    {id, protocol_id, protocol_label, athlete, started_at, completed_at,
     quality, summary: {<segment>: {means: {<metric>: number}, flag_counts,
                                    fall_risk, kept_trials, requires_spotter}},
     kept_trials, processing_version, safety, methodology}

Metrics are ``bertec.<segment>.<metric>`` plus ``bertec.kept_trials`` and
``bertec.quality``.  The quality word is **carried**: a session the app marked
``incomplete`` (the normal state when the plate is uncalibrated or a segment
was abandoned) stays ``incomplete`` here, because Mission Control has no way to
make that measurement trustworthy.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from ..schema import (
    Observation,
    ObservationError,
    normalize_quality,
    normalize_timestamp,
    slug_token,
    unit_for,
)
from . import AdapterContext, AdapterResult

SOURCE = "bertec"
APP = "bertec-jump"


def protocols_dir(ctx: AdapterContext) -> Path | None:
    root = ctx.root(SOURCE)
    return root / "data" / "protocols" if root else None


def _relative(path: Path, root: Path | None) -> str:
    if root:
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            pass
    return path.as_posix()


def _number(value) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _kept_trials(data: dict) -> int:
    kept = data.get("kept_trials")
    if isinstance(kept, list):
        return len(kept)
    if isinstance(kept, (int, float)) and not isinstance(kept, bool):
        return int(kept)
    summary = data.get("summary")
    if isinstance(summary, dict):
        total = 0
        for block in summary.values():
            if isinstance(block, dict):
                trials = block.get("kept_trials")
                if isinstance(trials, list):
                    total += len(trials)
                elif isinstance(trials, (int, float)) and not isinstance(trials, bool):
                    total += int(trials)
        return total
    return 0


def collect(ctx: AdapterContext) -> AdapterResult:
    result = AdapterResult()
    base = protocols_dir(ctx)
    if base is None or not base.is_dir():
        return result

    root = ctx.root(SOURCE)
    for session_path in sorted(base.glob("*/session.json")):
        try:
            data = json.loads(session_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            result.errors.append(
                {"source": SOURCE, "file": _relative(session_path, root), "error": str(exc)}
            )
            continue
        if not isinstance(data, dict):
            result.errors.append(
                {"source": SOURCE, "file": _relative(session_path, root), "error": "not a JSON object"}
            )
            continue
        result.extend(_collect_session(ctx, data, session_path, root))
    return result


def _collect_session(ctx: AdapterContext, data: dict, session_path: Path, root) -> AdapterResult:
    result = AdapterResult()

    session_id = str(data.get("id") or session_path.parent.name).strip()
    label = str(data.get("protocol_label") or data.get("protocol_id") or session_id)
    athlete = data.get("athlete") or ""

    try:
        measured_at, assumed_tz = normalize_timestamp(data.get("completed_at") or data.get("started_at"))
    except ObservationError as exc:
        result.errors.append(
            {"source": SOURCE, "session_id": session_id, "error": str(exc), "label": label}
        )
        return result

    file_ref = _relative(session_path, root)
    provenance = {
        "app": APP,
        "device": "Bertec force plate",
        "file": file_ref,
        "protocol": str(data.get("protocol_id") or ""),
        "protocol_label": label,
        "processing_version": str(data.get("processing_version") or ""),
        "source_quality": str(data.get("quality") or ""),
    }
    if assumed_tz:
        provenance["tz_assumed"] = "UTC"
    if data.get("safety"):
        provenance["safety_note"] = str((data["safety"] or {}).get("message") or "")[:400]

    patient_id = ctx.find_patient(SOURCE, session_id, session_path.parent.name, athlete, name=athlete)
    if not patient_id:
        result.unlinked.append(
            {
                "source": SOURCE,
                "session_id": session_id,
                "measured_at": measured_at,
                "label": label,
                "reason": "no explicit patient link (athlete field is empty or ambiguous)",
                "provenance": provenance,
            }
        )
        return result

    raw_quality = str(data.get("quality") or "").strip()
    quality = normalize_quality(raw_quality)
    summary_block = data.get("summary")
    summary: dict = summary_block if isinstance(summary_block, dict) else {}
    segments = [str(name) for name in summary.keys()]
    analysis = (
        f"{label}; quality: {raw_quality or 'not recorded'}; "
        f"segments: {', '.join(segments) if segments else 'none'}"
    )

    def add(metric: str, value, unit: str) -> None:
        result.observations.append(
            Observation(
                subject_id=patient_id,
                source=SOURCE,
                session_id=session_id,
                measured_at=measured_at,
                metric=metric,
                value=value,
                unit=unit,
                quality=quality,
                provenance=provenance,
                analysis=analysis,
            )
        )

    for segment, block in summary.items():
        if not isinstance(block, dict):
            continue
        means = block.get("means")
        if not isinstance(means, dict):
            continue
        seg_token = slug_token(segment)
        for key, value in means.items():
            number = _number(value)
            if number is None:
                continue
            add(f"bertec.{seg_token}.{slug_token(key)}", number, unit_for(key))

    add("bertec.kept_trials", float(_kept_trials(data)), "count")
    if raw_quality:
        add("bertec.quality", raw_quality, "")
    return result
