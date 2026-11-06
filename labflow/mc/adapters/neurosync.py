"""NeuroSync adapter — read-only over
``neurosync/recordings/subjects/<subject>/<timestamp>/summary.json``.

An empty (or absent) ``recordings/`` tree is a normal state: the adapter returns
no rows, never an error.

Quality is the point of this adapter.  A session is ``verified`` only when its
own gate passed **and** it was not simulator data.  A simulated session is
ingested as ``unverified`` with ``provenance.simulated = true`` — a shape that
looks like EEG must never be mistaken for a recording of a person.

Non-scalar blocks (``device``, ``channels``, ``contact``, ``transport``,
``analysis.channels`` ...) are not flattened into metrics; they are recorded in
provenance, and their names are listed in ``provenance.skipped_non_scalar``.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..schema import (
    QUALITY_TRUST,
    Observation,
    ObservationError,
    normalize_quality,
    normalize_timestamp,
    slug_token,
)
from . import AdapterContext, AdapterResult

SOURCE = "neurosync"
APP = "neurosync"

#: Top-level keys we never turn into metrics (they are structures, not numbers).
_NON_SCALAR_KEYS = (
    "device",
    "channels",
    "scalp_channels",
    "poly_channels",
    "contact",
    "transport",
    "analysis",
    "stable_estimate",
    "vs_baseline",
    "methodology",
    "limits",
)


def recordings_dir(ctx: AdapterContext) -> Path | None:
    root = ctx.root(SOURCE)
    return root / "recordings" / "subjects" if root else None


def _relative(path: Path, root: Path | None) -> str:
    if root:
        try:
            return path.relative_to(root).as_posix()
        except ValueError:
            pass
    return path.as_posix()


def _is_simulated(summary: dict) -> bool:
    if summary.get("simulated") is True:
        return True
    device = summary.get("device")
    if isinstance(device, dict) and device.get("simulated") is True:
        return True
    label = str(summary.get("device_label") or "").lower()
    return "simulated" in label


def _gate(summary: dict) -> tuple[bool, str]:
    """The session's own validity gate -> ``(passed, reason)``."""
    for block_name in ("analysis", "stable_estimate"):
        block = summary.get(block_name)
        if isinstance(block, dict) and isinstance(block.get("valid"), bool):
            reason = str(block.get("reason") or block.get("note") or "").strip()
            return bool(block["valid"]), reason or ("gate passed" if block["valid"] else "gate failed")
    if isinstance(summary.get("valid"), bool):
        return bool(summary["valid"]), str(summary.get("reason") or "").strip()
    quality = summary.get("quality")
    if isinstance(quality, dict):
        for key in ("valid", "passed", "pass"):
            if isinstance(quality.get(key), bool):
                return bool(quality[key]), str(quality.get("reason") or "").strip()
    if isinstance(quality, str) and quality.strip():
        return normalize_quality(quality) == "verified", quality.strip()
    return False, "no validity gate recorded"


def _bands(summary: dict) -> dict:
    """Band powers live under ``stable_estimate`` / ``analysis``; older files
    put them at the top level."""
    for key in ("stable_estimate", "analysis"):
        block = summary.get(key)
        if isinstance(block, dict):
            bands = block.get("bands")
            if isinstance(bands, dict) and bands:
                return bands
    direct = summary.get("bands")
    return direct if isinstance(direct, dict) else {}


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _session_timestamp(summary: dict, folder: Path) -> str:
    for candidate in (summary.get("started_at"), summary.get("recorded_at"), folder.name):
        try:
            return normalize_timestamp(candidate)[0]
        except ObservationError:
            continue
    raise ObservationError(f"no usable timestamp for {folder}")


def collect(ctx: AdapterContext) -> AdapterResult:
    result = AdapterResult()
    base = recordings_dir(ctx)
    if base is None or not base.is_dir():
        return result

    root = ctx.root(SOURCE)
    for subject_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        for session_dir in sorted(p for p in subject_dir.iterdir() if p.is_dir()):
            summary_path = session_dir / "summary.json"
            if not summary_path.is_file():
                continue  # an in-progress capture, not a finished session
            try:
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
                result.errors.append(
                    {"source": SOURCE, "file": _relative(summary_path, root), "error": str(exc)}
                )
                continue
            if not isinstance(summary, dict):
                result.errors.append(
                    {
                        "source": SOURCE,
                        "file": _relative(summary_path, root),
                        "error": "summary.json is not an object",
                    }
                )
                continue
            result.extend(_collect_session(ctx, summary, session_dir, subject_dir, root))
    return result


def _collect_session(
    ctx: AdapterContext, summary: dict, session_dir: Path, subject_dir: Path, root
) -> AdapterResult:
    result = AdapterResult()

    session_id = str(summary.get("session_id") or session_dir.name)
    subject_name = str(summary.get("subject_name") or "").strip()
    device_label = str(summary.get("device_label") or summary.get("device_type") or "EEG")
    condition = ""
    for candidate in (
        summary.get("condition"),
        summary.get("measurement_condition"),
        (summary.get("analysis") or {}).get("condition") if isinstance(summary.get("analysis"), dict) else None,
    ):
        if str(candidate or "").strip():
            condition = str(candidate).strip()
            break

    try:
        measured_at = _session_timestamp(summary, session_dir)
    except ObservationError as exc:
        result.errors.append({"source": SOURCE, "session_id": session_id, "error": str(exc)})
        return result

    passed, gate_reason = _gate(summary)
    simulated = _is_simulated(summary)

    provenance: dict = {
        "app": APP,
        "device": device_label,
        "file": _relative(session_dir / "summary.json", root),
        "subject": subject_dir.name,
        "condition": condition,
        "quality_gate": gate_reason,
    }
    channels = summary.get("channels")
    if isinstance(channels, list) and channels:
        provenance["channels"] = ",".join(str(c) for c in channels)
    skipped = [key for key in _NON_SCALAR_KEYS if isinstance(summary.get(key), (dict, list))]
    if skipped:
        provenance["skipped_non_scalar"] = ",".join(skipped)
    if simulated:
        provenance["simulated"] = True

    patient_id = ctx.find_patient(
        SOURCE, session_id, session_dir.name, subject_dir.name, summary.get("subject_key"), name=subject_name
    )
    if not patient_id:
        result.unlinked.append(
            {
                "source": SOURCE,
                "session_id": session_id,
                "measured_at": measured_at,
                "label": f"{subject_name or subject_dir.name} · {device_label}",
                "reason": "no explicit patient link (subject folder matches no LabFlow patient)",
                "provenance": provenance,
            }
        )
        return result

    # Quality: worst of (what the app said, what the gate allows, simulation).
    raw_quality = summary.get("quality")
    words = []
    if isinstance(raw_quality, str) and raw_quality.strip():
        words.append(normalize_quality(raw_quality))
    words.append("verified" if passed and not simulated else "unverified")
    if simulated:
        words.append("unverified")
    quality = min(words, key=lambda word: QUALITY_TRUST[word])

    reason_text = f" ({gate_reason})" if gate_reason else ""
    analysis = (
        f"{device_label} · condition: {condition or 'not recorded'} · "
        f"quality gate {'passed' if passed else 'failed'}{reason_text}"
        + (" · simulated data" if simulated else "")
    )

    ai_text, ai_model = "", ""
    ai_block = summary.get("ai_doctor")
    if isinstance(ai_block, dict):
        if ai_block.get("ok") is not False:
            ai_text = str(ai_block.get("text") or "")
        ai_model = str(ai_block.get("model") or ai_block.get("provider") or "")
    elif isinstance(ai_block, str):
        ai_text = ai_block

    def add(metric: str, value: float, unit: str) -> None:
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
                ai_text=ai_text,
                ai_model=ai_model,
            )
        )

    bands = _bands(summary)
    absolute: dict[str, float] = {}
    for band, block in bands.items():
        if not isinstance(block, dict):
            continue
        token = slug_token(band)
        rel = _number(block.get("relative_pct", block.get("relative")))
        if rel is not None:
            add(f"eeg.{token}_rel", rel, "%")
        power = _number(block.get("power_uv2", block.get("absolute")))
        if power is not None:
            absolute[token] = power
            add(f"eeg.{token}_abs", power, "µV²")

    theta, beta = absolute.get("theta"), absolute.get("beta")
    if theta is not None and beta not in (None, 0.0):
        add("eeg.tbr", round(theta / beta, 4), "index")

    add("eeg.quality", 1.0 if passed else 0.0, "score")
    return result
