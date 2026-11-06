"""RunTrack adapter — read-only SQLite over ``runtrack/data/runtrack.db``.

The database is opened as ``file:...?mode=ro&immutable=1``: SQLite then refuses
every write and takes no locks, so a running RunTrack instance is never blocked
and nothing here can mutate another app's data.  (``immutable`` also means we
may not see a write that is mid-transaction — acceptable for a results reader,
which re-syncs later.)

Metrics (spec + verified shape)::

    runtrack.form_index             score
    runtrack.symmetry_mean_pct      %
    runtrack.trunk_lean_deg         deg      (from {mean, std})
    runtrack.head_sway_norm         index
    runtrack.external_power_est_watts  W
    runtrack.joint.<joint>.mean     deg

``quality`` is ``verified`` only when the session itself said ``complete``
*and* a view plane was recorded; everything else is ``unverified``.
"""

from __future__ import annotations

import json
import math
import sqlite3
from pathlib import Path

from ..schema import Observation, normalize_timestamp, slug_token
from . import AdapterContext, AdapterResult

SOURCE = "runtrack"
APP = "runtrack"

_KNOWN_COLUMNS = (
    "id",
    "patient_id",
    "started_ts",
    "ended_ts",
    "status",
    "summary_json",
    "view_plane",
    "discipline",
)


def database_path(ctx: AdapterContext) -> Path | None:
    root = ctx.root(SOURCE)
    return root / "data" / "runtrack.db" if root else None


def connect_readonly(db_path: Path) -> sqlite3.Connection:
    """Open ``db_path`` read-only, no locks, no journal side files."""
    uri = f"file:{Path(db_path).as_posix()}?mode=ro&immutable=1"
    conn = sqlite3.connect(uri, uri=True, timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn


def _number(value) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def _scalar_or_mean(value) -> float | None:
    """Accept ``1.2`` or ``{"mean": 1.2, ...}``."""
    if isinstance(value, dict):
        return _number(value.get("mean"))
    return _number(value)


def metrics_from_summary(summary: dict) -> list[tuple[str, float, str]]:
    """The spec's metric set, in a stable order."""
    found: list[tuple[str, float, str]] = []

    direct = (
        ("form_index", "runtrack.form_index", "score"),
        ("symmetry_mean_pct", "runtrack.symmetry_mean_pct", "%"),
        ("head_sway_norm", "runtrack.head_sway_norm", "index"),
        ("external_power_est_watts", "runtrack.external_power_est_watts", "W"),
    )
    for key, metric, unit in direct:
        number = _number(summary.get(key))
        if number is not None:
            found.append((metric, number, unit))

    lean = _scalar_or_mean(summary.get("trunk_lean_deg"))
    if lean is not None:
        found.append(("runtrack.trunk_lean_deg", lean, "deg"))

    joints = summary.get("joints")
    if isinstance(joints, dict):
        for joint, block in joints.items():
            mean = _scalar_or_mean(block)
            if mean is None:
                continue
            found.append((f"runtrack.joint.{slug_token(joint)}.mean", mean, "deg"))
    return found


def _analysis(summary: dict, status: str, view_plane: str, discipline: str) -> str:
    parts = []
    header = f"{discipline or 'session'} · status {status or 'unknown'} · view {view_plane or 'unrecorded'}"
    parts.append(header)

    labels = summary.get("labels")
    if isinstance(labels, list):
        parts.extend(str(label) for label in labels if str(label or "").strip())

    form = summary.get("form")
    if isinstance(form, dict):
        for name, block in form.items():
            if not isinstance(block, dict):
                continue
            band = block.get("band")
            band_text = ""
            if isinstance(band, (list, tuple)) and len(band) == 2:
                band_text = f", band {band[0]}–{band[1]}"
            state = "in band" if block.get("in_band") else "out of band"
            parts.append(f"{name}: {block.get('value')} ({state}{band_text})")
    return "; ".join(parts)


def collect(ctx: AdapterContext) -> AdapterResult:
    result = AdapterResult()
    db_path = database_path(ctx)
    if db_path is None or not db_path.is_file():
        return result

    try:
        conn = connect_readonly(db_path)
    except sqlite3.Error as exc:
        result.errors.append({"source": SOURCE, "file": str(db_path), "error": str(exc)})
        return result

    try:
        tables = {
            str(row["name"])
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        if "sessions" not in tables:
            return result

        columns = {str(row["name"]) for row in conn.execute("PRAGMA table_info(sessions)")}
        if "id" not in columns:
            return result
        fields = ", ".join(
            f"s.{name}" if name in columns else f"NULL AS {name}" for name in _KNOWN_COLUMNS
        )
        has_patients = "patients" in tables
        join = "LEFT JOIN patients p ON p.id = s.patient_id" if has_patients else ""
        name_column = "p.name" if has_patients else "NULL"
        sql = (
            f"SELECT {fields}, {name_column} AS patient_name "
            f"FROM sessions s {join} ORDER BY s.id"
        )
        rows = conn.execute(sql).fetchall()
    except sqlite3.Error as exc:
        result.errors.append({"source": SOURCE, "file": str(db_path), "error": str(exc)})
        return result
    finally:
        conn.close()

    for row in rows:
        result.extend(_collect_row(ctx, row, db_path))
    return result


def _collect_row(ctx: AdapterContext, row: sqlite3.Row, db_path: Path) -> AdapterResult:
    result = AdapterResult()
    data = dict(row)
    session_id = str(data.get("id"))
    status = str(data.get("status") or "")
    view_plane = str(data.get("view_plane") or "").strip()
    discipline = str(data.get("discipline") or "")
    patient_name = str(data.get("patient_name") or "")

    raw_summary = data.get("summary_json")
    summary: dict = {}
    if isinstance(raw_summary, str) and raw_summary.strip():
        try:
            parsed = json.loads(raw_summary)
        except json.JSONDecodeError:
            parsed = None
        summary = parsed if isinstance(parsed, dict) else {}

    measured_at, assumed_tz = normalize_timestamp(data.get("ended_ts") or data.get("started_ts"))
    label = f"{patient_name or 'unlinked'} · {discipline or 'session'} #{session_id}"

    provenance = {
        "app": APP,
        "device": "RunTrack camera rig",
        "file": "data/runtrack.db",
        "table": "sessions",
        "row": str(session_id),
        "status": status,
        "view_plane": view_plane,
        "discipline": discipline,
    }
    if assumed_tz:
        provenance["tz_assumed"] = "UTC"

    patient_id = ctx.find_patient(SOURCE, session_id, patient_name, name=patient_name)
    if not patient_id:
        result.unlinked.append(
            {
                "source": SOURCE,
                "session_id": session_id,
                "measured_at": measured_at,
                "label": label,
                "reason": "no explicit patient link (RunTrack patient name matches no LabFlow patient)",
                "provenance": provenance,
            }
        )
        return result

    quality = "verified" if status == "complete" and view_plane else "unverified"
    analysis = _analysis(summary, status, view_plane, discipline) if summary else (
        f"{discipline or 'session'} · status {status or 'unknown'} · no summary stored"
    )

    for metric, value, unit in metrics_from_summary(summary):
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
    return result
