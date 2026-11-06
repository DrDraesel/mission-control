"""Mission Control API — one router, prefix ``/api/mc``.

Mounted by :mod:`labflow.app`; every route is read-mostly over
:class:`labflow.mc.ingest.Ingest` (the append-only observation store) and the
existing :class:`labflow.patients.PatientStore`, with chart aggregation
delegated to :func:`labflow.mc.chart.build_chart`.

Contract notes (binding — see ``labflow/docs/MC-EHR-SPEC.md``):

* **Error shape is always** ``{"detail": "..."}``: 400 for a validation
  problem (bad payload, missing provenance, malformed metric), 404 for an
  unknown patient.  FastAPI's default 422 for an unparseable body is avoided
  by reading the raw body here, so a broken push from another app gets the
  documented 400 instead of a pydantic detail list.
* **No silent subject merging.**  ``/ingest`` requires an existing LabFlow
  patient id as ``subject_id``; an unknown one is a 404, never an implicit
  create.  ``/link`` is the only way an unlinked session moves to a patient.
* **Quality is carried, never upgraded.**  This layer passes the caller's
  quality word straight into :class:`~labflow.mc.schema.Observation`; ingest
  keeps the lowest-trust row for a dedupe key.
* **Reads do not sync.**  ``GET`` endpoints never touch another app's tree;
  only ``POST /patients/{pid}/sync`` (adapters) and ``POST /ingest`` /
  ``POST /inbody`` (explicit pushes) write.

``build_router`` is a factory so the app can inject its own ``PatientStore``
(and tests their temp dirs) instead of relying on module-level state.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from labflow.mc import chart as chart_mod
from labflow.mc.adapters import build_context
from labflow.mc.adapters import inbody as inbody_adapter
from labflow.mc.export import DISCLAIMER, export_filename, render_chart_html
from labflow.mc.ingest import Ingest
from labflow.mc.schema import SOURCES, Observation, ensure_observation

__all__ = ["build_router", "DISCLAIMER"]

#: Sources the integrations page probes.  ``manual`` has no external tree.
_PROBED_SOURCES = ("bertec", "runtrack", "neurosync", "inbody")

#: Where each app's data actually lives, relative to its configured root.
_SOURCE_SUBPATHS = {
    "bertec": ("data", "protocols"),
    "runtrack": ("data", "runtrack.db"),
    "neurosync": ("recordings", "subjects"),
    "inbody": (),
}

_UNREACHABLE_HINTS = {
    "bertec": (
        "Start Bertec Jump on :8765 (or set MC_BERTEC_ROOT). Sessions are read "
        "from data/protocols/<session>/session.json."
    ),
    "runtrack": (
        "Start RunTrack on :8780 (or set MC_RUNTRACK_ROOT). Sessions are read "
        "from data/runtrack.db."
    ),
    "neurosync": (
        "Record a session in NeuroSync (or set MC_NEUROSYNC_ROOT). Summaries are "
        "read from recordings/subjects/<subject>/<timestamp>/summary.json."
    ),
    "inbody": (
        "Start InBody Stage 1 (DrDraesel/InBodyStage1) or set INBODY_DB to its "
        "runtime/inbody.db. Without it, use the manual form or a CSV (template "
        "on /mc/inbody)."
    ),
}

_TRUTHY = ("1", "true", "yes", "on")


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _detail(status: int, message: str) -> HTTPException:
    """A ``{"detail": ...}`` error with the spec's status codes."""
    return HTTPException(status_code=status, detail=message)


async def _json_body(request: Request) -> dict:
    """Parse a JSON object body, normalising every failure to a 400 detail.

    Using ``Request`` instead of a pydantic model keeps the error envelope
    identical for "bad JSON", "array instead of object" and "missing field"
    — the spec has one error shape, not two.
    """
    raw = await request.body()
    if not raw or not raw.strip():
        return {}
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise _detail(400, f"body must be valid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise _detail(400, "body must be a JSON object")
    return payload


def _as_str(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _source_path(root: Path | None, source: str) -> Path | None:
    if root is None:
        return None
    return Path(root).joinpath(*_SOURCE_SUBPATHS.get(source, ()))


def _session_keys(rows: list[dict]) -> set[tuple[str, str]]:
    return {(str(row.get("source")), str(row.get("session_id"))) for row in rows}


def _group_by_subject(rows: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("subject_id")), []).append(row)
    return grouped


def _per_source_sessions(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for source, _session in _session_keys(rows):
        counts[source] = counts.get(source, 0) + 1
    return counts


def _per_source_counts(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        source = str(row.get("source") or "")
        if source:
            counts[source] = counts.get(source, 0) + 1
    return counts


def _last_activity(rows: list[dict]) -> str | None:
    stamps = [str(row.get("measured_at")) for row in rows if row.get("measured_at")]
    return max(stamps) if stamps else None


# --------------------------------------------------------------------------- #
# router factory
# --------------------------------------------------------------------------- #
def build_router(store, data_dir=None, ingest: Ingest | None = None) -> APIRouter:
    """Build the ``/api/mc`` router for one ``PatientStore``.

    ``store`` is the live LabFlow :class:`~labflow.patients.PatientStore`
    (injected by ``create_app``).  ``data_dir`` defaults to the store's root so
    patients and observations always sit side by side; ``ingest`` may be passed
    pre-wired (tests use this to point adapters at empty fixture roots, so a
    test never reads a real lab tree).
    """
    if ingest is None:
        ingest = Ingest(store=store, data_dir=data_dir)
    data_root = Path(ingest.data_dir)

    router = APIRouter(prefix="/api/mc", tags=["mission-control"])

    # Ingest is read-then-append (dedupe keys are checked against the file
    # before writing), so two concurrent HTTP writes could append the same row
    # twice.  MC writes are rare and short; one lock serialises them.
    _write_lock = threading.Lock()

    # -- shared helpers ----------------------------------------------------
    def _ing() -> Ingest:
        return ingest

    def _patient_or_404(patient_id: str) -> dict:
        patient = store.get(patient_id)
        if patient is None:
            raise _detail(404, f"unknown patient: {patient_id!r}")
        return patient

    def _observation_rows(subject_id: str | None = None) -> list[dict]:
        return _ing().read(subject_id=subject_id)

    def _linked_session_counts() -> dict[str, int]:
        """Explicit links per source, straight from the patient records."""
        counts: dict[str, int] = {}
        for patient in store.list():
            linked = patient.get("linked_sessions") or {}
            if not isinstance(linked, Mapping):
                continue
            for source, bucket in linked.items():
                ids = (bucket or {}).get("ids") if isinstance(bucket, Mapping) else None
                if isinstance(ids, list):
                    counts[str(source)] = counts.get(str(source), 0) + len(ids)
        return counts

    def _integrations() -> list[dict]:
        """Per-source path, reachability, sessions found, last checked."""
        rows = _observation_rows()
        in_observations = _per_source_sessions(rows)
        unlinked_counts: dict[str, int] = {}
        for item in _ing().unlinked():
            source = str(item.get("source"))
            unlinked_counts[source] = unlinked_counts.get(source, 0) + 1

        roots = _ing().roots()
        checked = _now_iso()
        report = []
        for source in _PROBED_SOURCES:
            raw_root = roots.get(source)
            root = Path(raw_root) if raw_root else None
            path = _source_path(root, source)
            reachable = bool(path is not None and path.exists())
            mode = "manual+csv" if source == "inbody" else "read-only"
            if source == "inbody":
                # InBody Stage 1 is a real SQLite-backed app, not just a CSV
                # drop folder: probe its database first.  The context keeps a
                # sandboxed data dir from probing the machine's real DB.
                ctx = build_context(store, roots, data_dir=getattr(_ing(), "data_dir", None))
                db = inbody_adapter.database_path(ctx)
                if db is not None and Path(db).exists():
                    path = Path(db)
                    reachable = True
                    mode = "sqlite (read-only)"
            sessions = in_observations.get(source, 0) + unlinked_counts.get(source, 0)
            entry = {
                "source": source,
                "path": str(path) if path is not None else None,
                "root": str(root) if root is not None else None,
                "reachable": reachable,
                "sessions": sessions,
                "sessions_linked": in_observations.get(source, 0),
                "sessions_unlinked": unlinked_counts.get(source, 0),
                "last_checked": checked,
                "mode": mode,
            }
            if not reachable:
                entry["hint"] = _UNREACHABLE_HINTS.get(source, "Path not found.")
            report.append(entry)
        return report

    # -- overview -----------------------------------------------------------
    @router.get("/overview")
    def overview():
        rows = _observation_rows()
        linked = _linked_session_counts()
        observations_path = _ing().observations_path
        last_ingest = None
        if observations_path.exists():
            last_ingest = datetime.fromtimestamp(
                observations_path.stat().st_mtime, tz=timezone.utc
            ).isoformat()
        per_source = _per_source_sessions(rows)
        return {
            "ok": True,
            "counts": {
                "patients": len(store.list()),
                "observations": len(rows),
                "sessions": len(_session_keys(rows)),
                "unlinked_sessions": len(_ing().unlinked()),
                "sources": _per_source_counts(rows),
                "sessions_by_source": per_source,
                "linked_sessions": {source: linked.get(source, 0) for source in SOURCES if source != "manual"},
            },
            "last_ingest": last_ingest,
            "integrations": _integrations(),
            "disclaimer": DISCLAIMER,
        }

    # -- patients -----------------------------------------------------------
    @router.get("/patients")
    def patients():
        rows = _observation_rows()
        grouped = _group_by_subject(rows)
        payload = []
        for patient in store.list():
            patient_id = str(patient.get("id"))
            patient_rows = grouped.get(patient_id, [])
            payload.append(
                {
                    "id": patient.get("id"),
                    "name": patient.get("name"),
                    "dob": patient.get("dob"),
                    "contact": patient.get("contact"),
                    "status": patient.get("status"),
                    "created_at": patient.get("created_at"),
                    "observations": len(patient_rows),
                    "sources": _per_source_counts(patient_rows),
                    "sessions": _per_source_sessions(patient_rows),
                    "last_activity": _last_activity(patient_rows),
                }
            )
        return {
            "ok": True,
            "patients": payload,
            "totals": {
                "patients": len(payload),
                "with_observations": sum(1 for item in payload if item["observations"]),
            },
            "disclaimer": DISCLAIMER,
        }

    # -- chart --------------------------------------------------------------
    @router.get("/patients/{patient_id}/chart")
    def chart(patient_id: str, refresh: str = "0"):
        _patient_or_404(patient_id)
        # refresh=1 rebuilds the derived index before aggregating; it never
        # runs adapters (that is POST .../sync) and never writes observations.
        if str(refresh).strip().lower() in _TRUTHY:
            _ing().rebuild_index()
        try:
            payload = chart_mod.build_chart(
                store, patient_id, data_dir=data_root, ingest=_ing()
            )
        except KeyError as exc:  # patient vanished between the two reads
            raise _detail(404, f"unknown patient: {patient_id!r}") from exc
        return {"ok": True, **payload}

    # -- sync ---------------------------------------------------------------
    @router.post("/patients/{patient_id}/sync")
    def sync(patient_id: str):
        _patient_or_404(patient_id)
        try:
            with _write_lock:
                result = _ing().sync(patient_id=str(patient_id))
        except KeyError as exc:
            raise _detail(404, f"unknown patient: {patient_id!r}") from exc
        except ValueError as exc:
            raise _detail(400, str(exc)) from exc
        return {"ok": True, "patient_id": patient_id, **result}

    # -- ingest (push from an app) ------------------------------------------
    @router.post("/ingest")
    async def ingest_payload(request: Request):
        payload = await _json_body(request)

        source = _as_str(payload.get("source")).lower()
        subject_id = _as_str(payload.get("subject_id"))
        session_id = _as_str(payload.get("session_id"))
        measured_at = payload.get("measured_at")

        if not source:
            raise _detail(400, "source is required")
        if not subject_id:
            raise _detail(400, "subject_id is required")
        if not session_id:
            raise _detail(400, "session_id is required")
        if measured_at in (None, ""):
            raise _detail(400, "measured_at is required")
        _patient_or_404(subject_id)  # explicit link only — never auto-create

        provenance = payload.get("provenance")
        if not isinstance(provenance, Mapping) or not provenance:
            raise _detail(
                400,
                "provenance is required: {app, file|endpoint, ...} identifying "
                "where this number came from",
            )

        raw_metrics = payload.get("metrics")
        if isinstance(raw_metrics, Mapping):
            raw_metrics = [
                {"metric": key, **value} if isinstance(value, Mapping) else {"metric": key, "value": value}
                for key, value in raw_metrics.items()
            ]
        if not isinstance(raw_metrics, list) or not raw_metrics:
            raise _detail(400, "metrics is required: a non-empty list of {metric, value, unit}")

        shared = {
            "subject_id": subject_id,
            "source": source,
            "session_id": session_id,
            "measured_at": measured_at,
            "unit": payload.get("unit") or "",
            "quality": payload.get("quality"),
            "provenance": dict(provenance),
            "analysis": payload.get("analysis") or "",
            "ai_text": payload.get("ai_text") or "",
            "ai_model": payload.get("ai_model") or "",
        }

        observations: list[Observation] = []
        try:
            for index, item in enumerate(raw_metrics):
                if not isinstance(item, Mapping):
                    raise ValueError(f"metrics[{index}] must be an object")
                metric = _as_str(item.get("metric"))
                if not metric:
                    raise ValueError(f"metrics[{index}].metric is required")
                if "value" not in item:
                    raise ValueError(f"metrics[{index}].value is required")
                fields = dict(shared)
                fields["metric"] = metric
                fields["value"] = item.get("value")
                if item.get("unit") not in (None, ""):
                    fields["unit"] = item.get("unit")
                if item.get("quality") not in (None, ""):
                    fields["quality"] = item.get("quality")
                observations.append(ensure_observation(fields))
            with _write_lock:
                batch = _ing().add(observations)
        except ValueError as exc:  # ObservationError is a ValueError
            raise _detail(400, str(exc)) from exc

        return {
            "ok": True,
            "source": source,
            "subject_id": subject_id,
            "session_id": session_id,
            "received": len(observations),
            "added": batch["added"],
            "updated": batch["updated"],
            "skipped": batch["skipped"],
            "total": batch["total"],
        }

    # -- inbody manual entry ------------------------------------------------
    @router.post("/patients/{patient_id}/inbody")
    async def inbody_entry(patient_id: str, request: Request):
        _patient_or_404(patient_id)
        payload = await _json_body(request)

        measured_at = payload.get("measured_at") or _now_iso()
        values: dict[str, Any] = {}
        for key in ("values", "metrics", "body"):
            block = payload.get(key)
            if isinstance(block, Mapping):
                values.update({str(k): v for k, v in block.items()})
        for column in inbody_adapter.TEMPLATE_COLUMNS:
            if column in payload and payload[column] not in (None, ""):
                values[column] = payload[column]
        values.pop("measured_at", None)

        cleaned = {
            key: value
            for key, value in values.items()
            if value not in (None, "") and not isinstance(value, bool)
        }
        if not cleaned:
            raise _detail(
                400,
                "no body metrics given (want at least one of "
                + ", ".join(inbody_adapter.TEMPLATE_COLUMNS[1:])
                + ")",
            )

        try:
            observations = inbody_adapter.build_manual(
                str(patient_id),
                measured_at,
                cleaned,
                entered_by=_as_str(payload.get("entered_by") or payload.get("measured_by")),
                device_serial=_as_str(payload.get("device_serial") or payload.get("serial")),
                notes=_as_str(payload.get("notes")),
            )
        except ValueError as exc:
            raise _detail(400, str(exc)) from exc
        if not observations:
            raise _detail(400, "no numeric body metrics given")

        try:
            with _write_lock:
                batch = _ing().add(observations)
        except ValueError as exc:
            raise _detail(400, str(exc)) from exc

        quality = observations[0].quality
        return {
            "ok": True,
            "patient_id": patient_id,
            "session_id": observations[0].session_id,
            "measured_at": observations[0].measured_at,
            "quality": quality,
            "received": len(observations),
            "added": batch["added"],
            "updated": batch["updated"],
            "skipped": batch["skipped"],
            "note": "Manual entry — verify against the device printout",
        }

    # -- explicit link of an unlinked session -------------------------------
    @router.post("/patients/{patient_id}/link")
    async def link_session(patient_id: str, request: Request):
        _patient_or_404(patient_id)
        payload = await _json_body(request)
        source = _as_str(payload.get("source")).lower()
        session_id = _as_str(payload.get("session_id") or payload.get("link_id"))
        if not source:
            raise _detail(400, "source is required")
        if source not in SOURCES:
            raise _detail(400, f"unknown source: {source!r}")
        if not session_id:
            raise _detail(400, "session_id (or link_id) is required")

        try:
            with _write_lock:
                store.link_session(str(patient_id), source, session_id)
                # Drop the stale unlinked-bucket entry *before* syncing: a
                # one-patient sync merges (never replaces) that bucket, so
                # pruning first is what makes the link visible to the next
                # read.  This only rewrites MC's own unlinked.json (runtime
                # data, not another app's tree).
                removed = _drop_unlinked(_ing(), source, session_id)
                result = _ing().sync(patient_id=str(patient_id))
        except ValueError as exc:
            raise _detail(400, str(exc)) from exc

        still_unlinked = any(
            str(item.get("source")) == source and str(item.get("session_id")) == session_id
            for item in _ing().unlinked()
        )
        return {
            "ok": True,
            "linked": {"patient_id": patient_id, "source": source, "session_id": session_id},
            "removed_from_unlinked": removed,
            "attached": bool(result.get("added")) or not still_unlinked,
            "still_unlinked": still_unlinked,
            "added": result.get("added", 0),
            "updated": result.get("updated", 0),
            "skipped": result.get("skipped", 0),
            "sync": result,
        }

    # -- integrations -------------------------------------------------------
    @router.get("/integrations")
    def integrations():
        return {
            "ok": True,
            "integrations": _integrations(),
            "checked_at": _now_iso(),
            "disclaimer": DISCLAIMER,
        }

    # -- export -------------------------------------------------------------
    @router.get("/patients/{patient_id}/export.html", response_class=HTMLResponse)
    def export_chart(patient_id: str):
        patient = _patient_or_404(patient_id)
        rows = _observation_rows(subject_id=str(patient_id))
        document = render_chart_html(patient, rows)
        filename = export_filename(patient)
        return HTMLResponse(
            content=document,
            media_type="text/html; charset=utf-8",
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                # The document is generated from live data; never serve a stale copy.
                "Cache-Control": "no-store",
            },
        )

    return router


# --------------------------------------------------------------------------- #
# unlinked-bucket pruning (data only)
# --------------------------------------------------------------------------- #
def _drop_unlinked(ing: Ingest, source: str, session_id: str) -> bool:
    """Remove one ``(source, session_id)`` from ``unlinked.json``.

    The bucket is written by :class:`~labflow.mc.ingest.Ingest`; there is no
    public "mark linked" method, so the API layer rewrites the same documented
    envelope atomically.  Returns True when an entry was actually removed.
    """
    path = ing.unlinked_path
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    sessions = data.get("sessions") if isinstance(data, Mapping) else data
    if not isinstance(sessions, list):
        return False

    kept = [
        item
        for item in sessions
        if not (
            isinstance(item, Mapping)
            and str(item.get("source")) == source
            and str(item.get("session_id")) == session_id
        )
    ]
    if len(kept) == len(sessions):
        return False

    text = json.dumps({"updated_at": _now_iso(), "sessions": kept}, indent=2, ensure_ascii=False)
    handle_fd, tmp_path = tempfile.mkstemp(
        dir=str(ing.data_dir), prefix=".unlinked.", suffix=".tmp"
    )
    try:
        with os.fdopen(handle_fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, str(path))
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
    return True
