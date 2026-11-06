"""InBody adapter — the real InBody app first, file imports second, CSV last.

Three read-only paths, in priority order:

1. **SQLite** (primary) — the InBodyStage1 app's database
   (``INBODY_DB``, default ``C:/Users/GAMEPOWER/tools/InBodyStage1/runtime/inbody.db``,
   or ``INBODY_DATABASE_URL=sqlite:///runtime/inbody.db``).  Opened with
   ``mode=ro`` (WAL-aware, every write refused).  ``immutable=1`` is *wrong*
   here: InBody keeps recent commits in ``-wal`` and does not necessarily
   checkpoint, so an immutable open sees an empty database.  When SQLite cannot
   read the live WAL, we read a temp copy instead — the original is never
   written.  One result per ``encounter_id``: the newest **non-superseded**
   ``results`` row (supersession is the app's own audit trail — a corrected
   result is a new row whose ``supersedes`` points at the one it replaces).

2. **Normalized-v1 JSON** (secondary) — files dropped into ``INBODY_IMPORT_DIR``
   (default ``<labflow data>/inbody``), validated against the same payload the
   app stores in ``results.content`` (``schemas/normalized-v1.json``).

3. **Manual CSV** (fallback) — the template
   ``measured_at,weight_kg,skeletal_muscle_kg,body_fat_kg,body_fat_pct,visceral_fat,lean_mass_kg,bmi``.
   Always ``unverified`` unless a ``device_serial`` column is present, and
   always labelled "manual entry — verify against the device printout".

``quality`` is carried from the measurement's own ``status`` (``verified`` /
``unverified``) and is never upgraded here: a superseded or unconfirmed
measurement cannot become ``verified``.

Linking is explicit only — the InBody patient id must match a LabFlow link
(``linked_sessions['inbody']['ids']`` or a ``body.inbody_patient_id`` recorded
at linking time).  Names are never matched.
"""

from __future__ import annotations

import csv
import json
import math
import os
import shutil
import sqlite3
import tempfile
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

SOURCE = "inbody"
APP = "inbody"

#: InBodyStage1 install root (override with ``INBODY_HOME``).
INBODY_HOME = Path(os.environ.get("INBODY_HOME") or "C:/Users/GAMEPOWER/tools/InBodyStage1")
DEFAULT_DB = INBODY_HOME / "runtime" / "inbody.db"

ANALYSIS = "InBody CSV import — manual entry, verify against the device printout"
MANUAL_ANALYSIS = "Manual body-composition entry — verify against the device printout"

#: Manual CSV template (also served to the UI by the API layer).
TEMPLATE_COLUMNS = (
    "measured_at",
    "weight_kg",
    "skeletal_muscle_kg",
    "body_fat_kg",
    "body_fat_pct",
    "visceral_fat",
    "lean_mass_kg",
    "bmi",
)

#: CSV column -> canonical InBody metric name.  The manual template keeps its
#: own column names (``body.weight_kg``) so existing spreadsheets and the API
#: contract stay valid; the equivalence to the device vocabulary is recorded in
#: provenance as ``canonical_metric``.
CSV_CANONICAL = {
    "weight_kg": "weight",
    "skeletal_muscle_kg": "skeletal_muscle_mass",
    "body_fat_kg": "body_fat_mass",
    "body_fat_pct": "percent_body_fat",
    "visceral_fat": "visceral_fat_level",
    "lean_mass_kg": "lean_body_mass",
    "bmi": "bmi",
}

#: ``results`` columns we read; anything missing degrades to NULL.
_RESULT_COLUMNS = (
    "id",
    "patient_id",
    "encounter_id",
    "test_timestamp",
    "ingested_at",
    "source_type",
    "source_identifier",
    "source_hash",
    "content",
    "supersedes",
)

_SERIAL_COLUMNS = ("device_serial", "serial", "device_id")
_LINK_COLUMNS = ("subject_id", "patient_id")
_SKIP_COLUMNS = {
    "measured_at",
    "subject_id",
    "patient_id",
    "notes",
    "measured_by",
    "device_serial",
    "serial",
    "device_id",
}

#: Required keys of a normalized-v1 payload (``schemas/normalized-v1.json``).
REQUIRED_FIELDS = ("encounter_id", "test_timestamp", "source_identifier", "measurements")


# -- configuration ----------------------------------------------------------
def _path_from_database_url(url: str) -> Path | None:
    """``sqlite:///runtime/inbody.db`` -> absolute path under ``INBODY_HOME``."""
    raw = str(url or "").strip()
    if not raw.startswith("sqlite"):
        return None
    tail = raw.split("sqlite:", 1)[1]
    if tail.startswith("////"):
        return Path("/" + tail[4:])
    path = Path(tail.lstrip("/"))
    return path if path.is_absolute() else INBODY_HOME / path


def database_path(ctx: AdapterContext | None = None) -> Path | None:
    """Where the InBody SQLite lives, or ``None`` for an isolated data dir.

    ``INBODY_DB`` (or ``INBODY_DATABASE_URL``) always wins.  Otherwise the
    machine-wide install is read only for the real LabFlow data dir; a temp
    sandbox must not silently pick up real patient data.
    """
    explicit = os.environ.get("INBODY_DB")
    if explicit:
        return Path(explicit).expanduser()
    from_url = _path_from_database_url(os.environ.get("INBODY_DATABASE_URL") or "")
    if from_url is not None:
        return from_url
    if ctx is not None and ctx.sandboxed:
        return None
    return DEFAULT_DB


def inbody_dir(ctx: AdapterContext | None = None) -> Path | None:
    """Directory holding dropped normalized-v1 JSON / manual CSV files."""
    explicit = os.environ.get("INBODY_IMPORT_DIR")
    if explicit:
        return Path(explicit).expanduser()
    root = ctx.root(SOURCE) if ctx is not None else None
    return Path(root) if root else None


def connect_readonly(db_path) -> sqlite3.Connection:
    """Read-only, WAL-aware SQLite handle (never creates the file).

    ``mode=ro`` rather than ``immutable=1``: InBody leaves committed rows in the
    ``-wal`` file, and an immutable handle would not see them.
    """
    uri = f"file:{Path(db_path).as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=5.0)
    conn.row_factory = sqlite3.Row
    return conn


class _NeedsWal(Exception):
    """The live handle could not see the results table; retry via a copy."""


def _has_wal(db_path: Path) -> bool:
    return Path(str(db_path) + "-wal").is_file()


def _copy_for_read(db_path: Path) -> tuple[Path, Path]:
    """Copy db (+ ``-wal``/``-shm``) into a temp dir and open the copy."""
    folder = Path(tempfile.mkdtemp(prefix="mc-inbody-"))
    target = folder / Path(db_path).name
    shutil.copy2(db_path, target)
    for suffix in ("-wal", "-shm"):
        side = Path(str(db_path) + suffix)
        if side.is_file():
            try:
                shutil.copy2(side, Path(str(target) + suffix))
            except OSError:
                pass
    return folder, target


def _rows_from(db_path: Path) -> list[dict]:
    """Every ``results`` row, or raise :class:`_NeedsWal` / ``sqlite3.Error``."""
    conn = connect_readonly(db_path)
    try:
        tables = {
            str(row["name"]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        if "results" not in tables:
            raise _NeedsWal("no 'results' table")
        columns = {str(row["name"]) for row in conn.execute("PRAGMA table_info(results)")}
        if "content" not in columns or "id" not in columns:
            raise ValueError("results table lacks id/content")
        select = ", ".join(name if name in columns else f"NULL AS {name}" for name in _RESULT_COLUMNS)
        return [dict(row) for row in conn.execute(f"SELECT {select} FROM results")]
    finally:
        conn.close()


def _load_result_rows(db_path: Path) -> tuple[list[dict], str | None]:
    """Rows from the live DB, falling back to a copy when the WAL is unreadable."""
    try:
        return _rows_from(db_path), None
    except _NeedsWal as exc:
        if not _has_wal(db_path):
            return [], str(exc)
    except ValueError as exc:
        return [], str(exc)
    except sqlite3.Error as exc:
        if not _has_wal(db_path):
            return [], str(exc)
    try:
        folder, copy = _copy_for_read(db_path)
    except OSError as exc:  # pragma: no cover - locked/vanished file
        return [], f"cannot read WAL database: {exc}"
    try:
        return _rows_from(copy), None
    except (_NeedsWal, ValueError, sqlite3.Error) as exc:
        return [], str(exc)
    finally:
        shutil.rmtree(folder, ignore_errors=True)


# -- shared helpers ---------------------------------------------------------
def _number(value) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, str):
        text = value.strip().replace(",", "")
        if not text:
            return None
        try:
            value = float(text)
        except ValueError:
            return None
    if not isinstance(value, (int, float)):
        return None
    number = float(value)
    return number if math.isfinite(number) else None


def analyse(content: dict, source_type: str, ingested_at: str = "") -> str:
    parts = [
        f"InBody {content.get('device_model') or 'device'} · "
        f"source {source_type or content.get('source_type') or 'unknown'}",
        f"encounter {content.get('encounter_id') or 'unknown'}",
    ]
    if content.get("source_identifier"):
        parts.append(f"source id {content['source_identifier']}")
    if ingested_at:
        parts.append(f"ingested {ingested_at}")
    return "; ".join(str(part) for part in parts)


def _observations_from_content(
    ctx: AdapterContext,
    content: dict,
    *,
    session_id: str,
    measured_at: str,
    inbody_patient: str,
    provenance: dict,
    source_type: str,
    ingested_at: str = "",
) -> AdapterResult:
    """Turn one normalized-v1 payload into ``body.*`` observations."""
    result = AdapterResult()
    measurements = content.get("measurements")
    if not isinstance(measurements, list) or not measurements:
        result.errors.append(
            {"source": SOURCE, "session_id": session_id, "error": "payload has no measurements"}
        )
        return result

    patient_id = ctx.find_patient(
        SOURCE, inbody_patient, content.get("patient_id"), session_id
    )
    label = (
        f"InBody patient {inbody_patient or 'unknown'} · "
        f"encounter {content.get('encounter_id') or '?'}"
    )
    if not patient_id:
        result.unlinked.append(
            {
                "source": SOURCE,
                "session_id": session_id,
                "link_id": inbody_patient,
                "measured_at": measured_at,
                "label": label,
                "reason": (
                    "no explicit LabFlow link for this InBody patient id "
                    f"({inbody_patient or 'unknown'}); names are never matched"
                ),
                "provenance": provenance,
            }
        )
        return result

    analysis = analyse(content, source_type, ingested_at)
    for measurement in measurements:
        if not isinstance(measurement, dict):
            continue
        metric = slug_token(measurement.get("metric"))
        value = _number(measurement.get("value"))
        if value is None:
            continue  # normalized-v1 allows null (unreadable on the printout)
        quality = normalize_quality(measurement.get("status"), default="unverified")
        note = str(measurement.get("quality_note") or "").strip()
        result.observations.append(
            Observation(
                subject_id=patient_id,
                source=SOURCE,
                session_id=session_id,
                measured_at=measured_at,
                metric=f"body.{metric}",
                value=value,
                unit=str(measurement.get("unit") or unit_for(metric)),
                quality=quality,
                provenance=provenance,
                analysis=f"{analysis} ({note})" if note else analysis,
            )
        )
    return result


# -- entry point ------------------------------------------------------------
def collect(ctx: AdapterContext) -> AdapterResult:
    """Every InBody result we can see, from all three paths."""
    result = AdapterResult()

    db = database_path(ctx)
    if db is None:
        # Isolated data dir: never reach into the machine-wide InBody install.
        result.notes.append(
            {
                "source": SOURCE,
                "level": "info",
                "note": "InBody database not read for this data dir (set INBODY_DB to point at it)",
            }
        )
    elif Path(db).is_file():
        result.extend(collect_db(ctx, db))
    else:
        # Normal state when the InBody app has never run on this PC.
        result.notes.append(
            {"source": SOURCE, "level": "info", "note": f"InBody database not found: {db}"}
        )

    seen: set[str] = set()
    folders = [inbody_dir(ctx), ctx.root(SOURCE)]
    for folder in folders:
        if folder is None or not Path(folder).is_dir():
            continue
        for pattern, handler in (("*.json", collect_json), ("*.csv", collect_csv)):
            for path in sorted(Path(folder).glob(pattern)):
                key = str(path.resolve())
                if key in seen:
                    continue
                seen.add(key)
                result.extend(handler(ctx, path))
    return result


# -- 1. SQLite --------------------------------------------------------------
def collect_db(ctx: AdapterContext, db_path) -> AdapterResult:
    """Newest non-superseded result per encounter from ``runtime/inbody.db``."""
    result = AdapterResult()
    db_path = Path(db_path)
    rows, error = _load_result_rows(db_path)
    if error is not None:
        result.errors.append({"source": SOURCE, "file": str(db_path), "error": error})
        return result

    superseded = {str(row["supersedes"]) for row in rows if row.get("supersedes")}
    current = [row for row in rows if str(row["id"]) not in superseded]

    # One result per encounter: newest by test time, then ingest time, then id.
    newest: dict[str, tuple[tuple[str, str, str], dict]] = {}
    for row in current:
        key = str(row.get("encounter_id") or row["id"])
        stamp = (
            str(row.get("test_timestamp") or ""),
            str(row.get("ingested_at") or ""),
            str(row["id"]),
        )
        held = newest.get(key)
        if held is None or stamp > held[0]:
            newest[key] = (stamp, row)

    for _key, (_stamp, row) in sorted(newest.items(), key=lambda item: item[1][0]):
        session_id = str(row["id"])
        content = _parse_content(row.get("content"))
        if content is None:
            result.errors.append(
                {"source": SOURCE, "session_id": session_id, "error": "results.content is not valid JSON"}
            )
            continue
        try:
            measured_at = normalize_timestamp(
                content.get("test_timestamp") or row.get("test_timestamp")
            )[0]
        except ObservationError as exc:
            result.errors.append({"source": SOURCE, "session_id": session_id, "error": str(exc)})
            continue

        source_type = str(row.get("source_type") or content.get("source_type") or "")
        provenance = {
            "app": APP,
            "device": str(content.get("device_model") or "InBody"),
            "file": str(db_path),
            "table": "results",
            "result_id": session_id,
            "encounter_id": str(row.get("encounter_id") or content.get("encounter_id") or ""),
            "source_identifier": str(
                row.get("source_identifier") or content.get("source_identifier") or ""
            ),
            "source_hash": str(row.get("source_hash") or ""),
            "device_model": str(content.get("device_model") or ""),
            "source_type": source_type,
            "import": "sqlite",
        }
        result.extend(
            _observations_from_content(
                ctx,
                content,
                session_id=session_id,
                measured_at=measured_at,
                inbody_patient=str(row.get("patient_id") or content.get("patient_id") or ""),
                provenance=provenance,
                source_type=source_type,
                ingested_at=str(row.get("ingested_at") or ""),
            )
        )
    return result


def _parse_content(raw) -> dict | None:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", "replace")
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


# -- 2. normalized-v1 JSON --------------------------------------------------
def collect_json(ctx: AdapterContext, path: Path) -> AdapterResult:
    """One dropped normalized-v1 file (a single object, or a list of them)."""
    result = AdapterResult()
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        result.errors.append({"source": SOURCE, "file": str(path), "error": str(exc)})
        return result

    records = payload if isinstance(payload, list) else [payload]
    for index, content in enumerate(records, start=1):
        if not isinstance(content, dict):
            result.errors.append(
                {"source": SOURCE, "file": str(path), "record": index, "error": "not a JSON object"}
            )
            continue
        missing = [field for field in REQUIRED_FIELDS if content.get(field) in (None, "", [])]
        if missing:
            result.errors.append(
                {
                    "source": SOURCE,
                    "file": str(path),
                    "record": index,
                    "error": f"normalized-v1 payload missing: {', '.join(missing)}",
                }
            )
            continue
        try:
            measured_at = normalize_timestamp(content["test_timestamp"])[0]
        except ObservationError as exc:
            result.errors.append(
                {"source": SOURCE, "file": str(path), "record": index, "error": str(exc)}
            )
            continue

        source_type = str(content.get("source_type") or "manual")
        provenance = {
            "app": APP,
            "device": str(content.get("device_model") or "InBody"),
            "file": str(path),
            "source_identifier": str(content.get("source_identifier")),
            "encounter_id": str(content["encounter_id"]),
            "device_model": str(content.get("device_model") or ""),
            "source_type": source_type,
            "import": "json",
        }
        result.extend(
            _observations_from_content(
                ctx,
                content,
                session_id=f"{Path(path).stem}:{content['encounter_id']}",
                measured_at=measured_at,
                inbody_patient=str(content.get("patient_id") or ""),
                provenance=provenance,
                source_type=source_type,
            )
        )
    return result


# -- 3. manual CSV ----------------------------------------------------------
def _header(name: str) -> str:
    return str(name or "").strip().lower().replace(" ", "_").replace("-", "_")


def collect_csv(ctx: AdapterContext, path: Path) -> AdapterResult:
    """Manual template import — always labelled, never silently verified."""
    result = AdapterResult()
    rel = f"inbody/{Path(path).name}"
    try:
        with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)
            fieldnames = [_header(name) for name in (reader.fieldnames or [])]
    except (OSError, UnicodeDecodeError, csv.Error) as exc:
        result.errors.append({"source": SOURCE, "file": rel, "error": str(exc)})
        return result

    if not fieldnames:
        result.errors.append({"source": SOURCE, "file": rel, "error": "empty CSV"})
        return result

    for index, raw_row in enumerate(rows, start=1):
        row = {
            _header(key): ("" if value is None else str(value).strip())
            for key, value in raw_row.items()
            if key
        }
        if not any(row.values()):
            continue

        try:
            measured_at = normalize_timestamp(row.get("measured_at"))[0]
        except ObservationError as exc:
            result.errors.append(
                {"source": SOURCE, "file": rel, "row": index, "error": f"measured_at: {exc}"}
            )
            continue

        subject = next((row[c] for c in _LINK_COLUMNS if row.get(c)), "") or Path(path).stem
        serial = next((row[c] for c in _SERIAL_COLUMNS if row.get(c)), "")
        session_id = f"{Path(path).stem}:{index}"
        provenance = {
            "app": APP,
            "device": "InBody",
            "file": rel,
            "row": str(index),
            "import": "csv",
        }
        if serial:
            provenance["device_serial"] = serial
        if row.get("notes"):
            provenance["notes"] = row["notes"]

        patient_id = ctx.find_patient(SOURCE, subject, Path(path).stem)
        if not patient_id:
            result.unlinked.append(
                {
                    "source": SOURCE,
                    "session_id": session_id,
                    "measured_at": measured_at,
                    "label": f"{Path(path).name} row {index}",
                    "reason": "no explicit patient link (subject_id column or <patient_id>.csv file name)",
                    "provenance": provenance,
                }
            )
            continue

        quality = "verified" if serial else "unverified"
        emitted = False
        for column, text in row.items():
            if column in _SKIP_COLUMNS or not text:
                continue
            value = _number(text)
            if value is None:
                continue
            metric = slug_token(column)
            observation_provenance = provenance
            canonical = CSV_CANONICAL.get(column)
            if canonical:
                observation_provenance = dict(provenance, canonical_metric=f"body.{canonical}")
            result.observations.append(
                Observation(
                    subject_id=patient_id,
                    source=SOURCE,
                    session_id=session_id,
                    measured_at=measured_at,
                    metric=f"body.{metric}",
                    value=value,
                    unit=unit_for(column),
                    quality=quality,
                    provenance=observation_provenance,
                    analysis=ANALYSIS,
                )
            )
            emitted = True
        if not emitted:
            result.errors.append(
                {"source": SOURCE, "file": rel, "row": index, "error": "no numeric body metrics"}
            )
    return result


def build_manual(
    patient_id: str,
    measured_at,
    values: dict,
    *,
    entered_by: str = "",
    device_serial: str = "",
    notes: str = "",
) -> list[Observation]:
    """Observations for a hand-entered InBody record (used by the API layer).

    Hand entry is ``unverified`` unless a device serial was transcribed, which
    only ever raises it to ``verified`` *by provenance* — never by a claim.
    """
    measured = normalize_timestamp(measured_at)[0]
    provenance: dict = {
        "app": APP,
        "device": "InBody",
        "endpoint": "POST /api/mc/patients/{pid}/inbody",
        "entry": "manual",
    }
    if entered_by:
        provenance["entered_by"] = str(entered_by)
    if device_serial:
        provenance["device_serial"] = str(device_serial)
    if notes:
        provenance["notes"] = str(notes)

    quality = "verified" if device_serial else "unverified"
    session_id = f"manual-inbody:{measured}"
    observations: list[Observation] = []
    for key, raw in (values or {}).items():
        number = _number(raw)
        if number is None:
            continue
        column = slug_token(key)
        canonical = CSV_CANONICAL.get(column)
        provenance_for_metric = provenance
        if canonical:
            provenance_for_metric = dict(provenance, canonical_metric=f"body.{canonical}")
        observations.append(
            Observation(
                subject_id=patient_id,
                source=SOURCE,
                session_id=session_id,
                measured_at=measured,
                metric=f"body.{column}",
                value=number,
                unit=unit_for(column),
                quality=quality,
                provenance=provenance_for_metric,
                analysis=MANUAL_ANALYSIS,
            )
        )
    return observations
