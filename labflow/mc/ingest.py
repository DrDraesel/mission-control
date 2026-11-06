"""Mission Control storage — append-only observations, idempotent ingest.

Layout (all under LabFlow's own data dir, which is gitignored)::

    <data>/observations.jsonl         append-only, one JSON object per line
    <data>/observations.index.json    rebuilt on demand (patient -> session -> metrics)
    <data>/unlinked.json              sessions no patient could be attributed to

Why append-only: a measurement, once written, is the lab's record of what the
app said.  Nothing here rewrites or deletes a line.  Duplicates are prevented by
the sha1 key ``source|session_id|metric|measured_at``; a genuine *downgrade* of
quality (the app later says the session was incomplete) is appended as a new
line, and readers resolve each key to its **lowest-trust** row — so quality can
go down but never up.

``sync()`` is the only thing that touches another app's tree, and only to read.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .adapters import build_context, collect_all, default_roots
from .schema import (
    QUALITY_TRUST,
    Observation,
    ensure_observation,
)

__all__ = [
    "DISCLAIMER",
    "Ingest",
    "ObservationStore",
    "default_data_dir",
    "read_observations",
]

#: Carried into chart/export payloads so no surface can silently drop it.
DISCLAIMER = (
    "Lab record for research and operations. Not a certified EHR; "
    "not a medical device; clinical decisions are physician-led."
)


#: Serializes read-then-append and index rewrites inside this process (uvicorn
#: is single-process; cross-process use is one PC, one app).
_WRITE_LOCK = threading.Lock()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_data_dir() -> Path:
    """``labflow/data`` (``LABFLOW_DATA_DIR`` wins, matching ``app.py``)."""
    env = os.environ.get("LABFLOW_DATA_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[1] / "data"


class Ingest:
    """Reads every adapter, writes one append-only file.

    ``store`` may be a :class:`labflow.patients.PatientStore`, a path, or
    ``None`` (then a store is opened on ``data_dir``).  ``data_dir`` defaults to
    the store's root so patients and observations always sit side by side.
    """

    def __init__(self, store=None, data_dir=None, roots=None):
        from labflow.patients import PatientStore  # local import: keeps schema stdlib-pure

        if store is None:
            path = Path(data_dir) if data_dir else default_data_dir()
            self.store = PatientStore(path)
        elif isinstance(store, (str, os.PathLike)):
            self.store = PatientStore(Path(store))
        else:
            self.store = store

        root = getattr(self.store, "root_dir", None)
        self.data_dir = Path(data_dir) if data_dir else Path(root or default_data_dir())
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._roots = dict(roots) if roots else None

    # -- paths ---------------------------------------------------------------
    @property
    def observations_path(self) -> Path:
        return self.data_dir / "observations.jsonl"

    @property
    def index_path(self) -> Path:
        return self.data_dir / "observations.index.json"

    @property
    def unlinked_path(self) -> Path:
        return self.data_dir / "unlinked.json"

    # -- reading -------------------------------------------------------------
    def _load_rows(self) -> tuple[list[dict], int]:
        """Raw rows plus a count of unreadable lines (tolerated, never fatal)."""
        path = self.observations_path
        if not path.exists():
            return [], 0
        rows: list[dict] = []
        corrupt = 0
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    corrupt += 1
                    continue
                if isinstance(row, dict):
                    rows.append(row)
                else:
                    corrupt += 1
        return rows, corrupt

    def keys(self) -> dict[str, dict]:
        """Effective state per dedupe key: ``{key: {quality, trust, metric...}}``."""
        rows, _ = self._load_rows()
        state: dict[str, dict] = {}
        for row in rows:
            key = self._row_key(row)
            if key is None:
                continue
            trust = QUALITY_TRUST.get(str(row.get("quality")), 0)
            current = state.get(key)
            if current is None or trust <= current["trust"]:
                state[key] = {
                    "trust": trust,
                    "quality": row.get("quality"),
                    "subject_id": row.get("subject_id"),
                    "source": row.get("source"),
                    "session_id": row.get("session_id"),
                    "metric": row.get("metric"),
                    "measured_at": row.get("measured_at"),
                }
        return state

    @staticmethod
    def _row_key(row: dict) -> str | None:
        """Dedupe key of a stored row; ``None`` when the row is unusable.

        Corrupt-but-parseable lines must never take a whole sync down, so an
        unreadable row is skipped here rather than raising mid-run.
        """
        key = str(row.get("dedupe_key") or "").strip()
        if key:
            return key
        try:
            return Observation.from_dict(row).key
        except ValueError:
            return None

    def read(self, resolve: bool = True, subject_id: str | None = None) -> list[dict]:
        """Observations (resolved to one row per dedupe key by default)."""
        rows, _ = self._load_rows()
        if resolve:
            best: dict[str, tuple[int, dict]] = {}
            for row in rows:
                key = self._row_key(row)
                if key is None:
                    continue
                trust = QUALITY_TRUST.get(str(row.get("quality")), 0)
                current = best.get(key)
                if current is None or trust <= current[0]:
                    normalized = dict(row)
                    normalized["dedupe_key"] = key
                    best[key] = (trust, normalized)
            rows = [row for _, row in best.values()]
        else:
            rows = [dict(row) for row in rows]
        if subject_id is not None:
            rows = [row for row in rows if str(row.get("subject_id")) == str(subject_id)]
        return rows

    # Alias with an explicit name for callers that dislike ``read``.
    def read_observations(self, subject_id: str | None = None) -> list[dict]:
        return self.read(subject_id=subject_id)

    # -- writing -------------------------------------------------------------
    def _append(self, rows: Iterable[dict]) -> int:
        rows = list(rows)
        if not rows:
            return 0
        payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n" for row in rows)
        # Opening can lose a race with Windows AV/indexing on a live data dir;
        # retry the open only, so a partially written line is never repeated.
        handle = None
        last_error = None
        for attempt in range(6):
            try:
                handle = self.observations_path.open("a", encoding="utf-8", newline="\n")
                break
            except PermissionError as exc:  # pragma: no cover - Windows timing
                last_error = exc
                time.sleep(0.05 * (attempt + 1))
        if handle is None:
            raise last_error or PermissionError(f"cannot append to {self.observations_path}")
        with handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        return len(rows)

    def _patient_exists(self, patient_id: str) -> bool:
        getter = getattr(self.store, "get", None)
        if getter is None:
            return False
        return getter(patient_id) is not None

    def add(self, observations: Iterable, require_patient: bool = True) -> dict:
        """Validate + append observations.  Idempotent on the sha1 key.

        Returns ``{"added", "updated", "skipped", "total"}``.  ``updated`` counts
        rows appended because the source downgraded a record's quality — the
        only case in which an existing key gets a second line.
        """
        # Read-then-append must be atomic inside this process, or two concurrent
        # requests could both see a key as new and write it twice.
        with _WRITE_LOCK:
            state = self.keys()
            pending: list[dict] = []
            added = updated = skipped = 0

            for item in observations or []:
                observation = ensure_observation(item)  # raises ValueError on bad records
                if require_patient and not self._patient_exists(observation.subject_id):
                    raise ValueError(f"unknown patient: {observation.subject_id!r}")

                key = observation.key
                trust = QUALITY_TRUST[observation.quality]
                current = state.get(key)
                if current is None:
                    state[key] = {"trust": trust, "quality": observation.quality}
                    pending.append(observation.to_dict())
                    added += 1
                elif trust < current["trust"]:
                    # Same identity, worse trust: append so the downgrade is
                    # visible to readers.  The reverse (an upgrade) is
                    # impossible by design.
                    current["trust"] = trust
                    current["quality"] = observation.quality
                    pending.append(observation.to_dict())
                    updated += 1
                else:
                    skipped += 1

            self._append(pending)
        return {"added": added, "updated": updated, "skipped": skipped, "total": len(pending)}

    # -- unlinked bucket -----------------------------------------------------
    def _load_unlinked(self) -> list[dict]:
        if not self.unlinked_path.exists():
            return []
        try:
            data = json.loads(self.unlinked_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        sessions = data.get("sessions") if isinstance(data, dict) else data
        return [item for item in sessions or [] if isinstance(item, dict)]

    def unlinked(self) -> list[dict]:
        """Sessions no patient could be attributed to (never auto-attached)."""
        return sorted(
            self._load_unlinked(),
            key=lambda item: (str(item.get("measured_at") or ""), str(item.get("source") or "")),
            reverse=True,
        )

    def _save_unlinked(self, sessions: list[dict]) -> None:
        payload = {"updated_at": _utc_now(), "sessions": sessions}
        self._write_json(self.unlinked_path, payload)

    def _write_json(self, path: Path, payload) -> None:
        """Atomic JSON write (temp + fsync + replace), retried on Windows locks.

        ``os.replace`` can be refused for a few milliseconds while AV or the
        indexer holds the destination — the same reason ``app.py`` retries
        patient saves.  The temp file is rebuilt each attempt, so a retry can
        never duplicate content.
        """
        text = json.dumps(payload, indent=2, ensure_ascii=False)
        last_error = None
        for attempt in range(6):
            handle_fd, tmp_path = tempfile.mkstemp(
                dir=str(self.data_dir), prefix=f".{path.stem}.", suffix=".tmp"
            )
            try:
                with os.fdopen(handle_fd, "w", encoding="utf-8") as handle:
                    handle.write(text)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(tmp_path, str(path))
                return
            except PermissionError as exc:  # pragma: no cover - Windows timing
                last_error = exc
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                time.sleep(0.05 * (attempt + 1))
            except BaseException:
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
                raise
        raise last_error or PermissionError(f"cannot write {path}")

    def _merge_unlinked(self, entries: list[dict], replace: bool) -> list[dict]:
        if replace:
            merged = list(entries)
        else:
            existing = self._load_unlinked()
            keyed = {(item.get("source"), item.get("session_id")): item for item in entries}
            for item in existing:
                keyed.setdefault((item.get("source"), item.get("session_id")), item)
            merged = list(keyed.values())
        self._save_unlinked(merged)
        return merged

    # -- ingest run ----------------------------------------------------------
    def _require_patient(self, patient_id: str) -> dict:
        patient = self.store.get(patient_id)
        if patient is None:
            raise KeyError(f"unknown patient: {patient_id!r}")
        return patient

    def roots(self) -> dict:
        if self._roots is not None:
            return dict(self._roots)
        return default_roots(self.data_dir)

    def _link_hints(self) -> dict[str, dict[str, str]]:
        """Explicit external-id links stored as observations.

        A link recorded while working with another app (today: the InBody
        patient id) is a measurement like ``body.inbody_patient_id``; adapters
        see it as a verified link and never guess from a name.
        """
        hints: dict[str, dict[str, str]] = {}
        for row in self.read():
            if str(row.get("metric") or "") != "body.inbody_patient_id":
                continue
            value = str(row.get("value") or "").strip()
            subject = str(row.get("subject_id") or "").strip()
            if value and subject:
                hints.setdefault("inbody", {})[value] = subject
        return hints

    def sync(self, patient_id: str | None = None) -> dict:
        """Run every adapter and store what is new.

        ``patient_id`` scopes only *what is written*: every session is still read
        and linked against the whole patient list, so the unlinked bucket stays
        truthful, but rows for other patients are dropped before ``add``.
        (Filtering the patient list instead would make every other patient's
        session look unlinked — a lie the UI would then show.)
        """
        if patient_id is not None:
            self._require_patient(patient_id)
        patients = list(self.store.list())
        context = build_context(
            store=self.store,
            roots=self.roots(),
            data_dir=self.data_dir,
            patients=patients,
            links=self._link_hints(),
        )
        observations, unlinked, errors, notes = collect_all(context)
        if patient_id is not None:
            wanted = str(patient_id)
            observations = [item for item in observations if item.subject_id == wanted]

        batch = self.add(observations)
        # A full, clean read replaces the bucket (linked sessions must disappear
        # from it).  If any adapter failed we merge instead, so an unreadable
        # app cannot silently erase the sessions it used to report.
        bucket = self._merge_unlinked(unlinked, replace=not errors)
        index = self.rebuild_index()

        per_source: dict[str, dict] = {}
        for observation in observations:
            entry = per_source.setdefault(observation.source, {"found": 0, "unlinked": 0})
            entry["found"] += 1
        for item in unlinked:
            entry = per_source.setdefault(str(item.get("source")), {"found": 0, "unlinked": 0})
            entry["unlinked"] += 1

        return {
            "ok": True,
            "scope": patient_id or "all",
            "generated_at": _utc_now(),
            "added": batch["added"],
            "updated": batch["updated"],
            "skipped": batch["skipped"],
            "candidates": len(observations),
            "patients": len(patients),
            "unlinked_in_run": len(unlinked),
            "unlinked_total": len(bucket),
            "sources": per_source,
            "observations_total": index["counts"]["observations"],
            "errors": errors,
            "notes": notes,
        }

    # -- index ---------------------------------------------------------------
    def rebuild_index(self) -> dict:
        """Rebuild ``observations.index.json`` (patient -> session -> metrics)."""
        with _WRITE_LOCK:
            return self._rebuild_index()

    def _rebuild_index(self) -> dict:
        rows = self.read(resolve=True)
        patients: dict[str, dict] = {}
        sources: dict[str, int] = {}

        for row in rows:
            subject = str(row.get("subject_id"))
            source = str(row.get("source"))
            session_id = str(row.get("session_id"))
            metric = str(row.get("metric"))

            sources[source] = sources.get(source, 0) + 1
            patient_entry = patients.setdefault(
                subject, {"sessions": {}, "metrics": {}, "sources": {}, "last_activity": None}
            )
            session = patient_entry["sessions"].setdefault(
                session_id,
                {
                    "source": source,
                    "session_id": session_id,
                    "measured_at": row.get("measured_at"),
                    "quality": row.get("quality"),
                    "metrics": [],
                },
            )
            # The session card must show the worst quality in that session.
            if QUALITY_TRUST.get(str(row.get("quality")), 0) <= QUALITY_TRUST.get(
                str(session.get("quality")), 0
            ):
                session["quality"] = row.get("quality")
            if metric not in session["metrics"]:
                session["metrics"].append(metric)
            patient_entry["metrics"][metric] = row.get("measured_at")
            patient_entry["sources"][source] = patient_entry["sources"].get(source, 0) + 1
            stamp = str(row.get("measured_at") or "")
            if stamp and (patient_entry["last_activity"] is None or stamp > patient_entry["last_activity"]):
                patient_entry["last_activity"] = stamp

        for entry in patients.values():
            for session in entry["sessions"].values():
                session["metrics"].sort()
        index = {
            "built_at": _utc_now(),
            "counts": {
                "observations": len(rows),
                "patients": len(patients),
                "sessions": sum(len(p["sessions"]) for p in patients.values()),
                "sources": len(sources),
                "unlinked": len(self._load_unlinked()),
            },
            "sources": sources,
            "patients": patients,
        }
        self._write_json(self.index_path, index)
        return index

    def load_index(self) -> dict | None:
        if not self.index_path.exists():
            return None
        try:
            data = json.loads(self.index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return data if isinstance(data, dict) else None


#: Readable alias — the class is a store as much as an ingest runner.
ObservationStore = Ingest


def read_observations(data_dir=None, subject_id: str | None = None, store=None) -> list[dict]:
    """Module-level convenience used by the chart/API layers."""
    return Ingest(store=store, data_dir=data_dir).read(subject_id=subject_id)
