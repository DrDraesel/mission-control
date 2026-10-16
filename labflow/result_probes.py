"""Read-only result probes for the LabFlow web layer.

Each probe inspects ONE local lab app and returns a small JSON-safe summary:

    {"app": "bertec", "available": true, "count": 3, "latest": {...}}

Rules that every probe obeys:

* read-only - GET requests / filesystem stat only, never writes anything;
* timeout 3 seconds;
* NEVER raises - any failure returns ``available: false`` plus an ``error``
  string describing what went wrong.

The HTTP probes accept an injectable ``fetch`` callable for tests::

    fetch(url, timeout) -> (status: int, text: str)

A fetcher may also raise (connection refused, DNS, ...) and the probe will
translate that into ``available: false``.  The default fetcher is stdlib
``urllib`` so this module has no third-party dependencies.

Live endpoints verified 2026-10-16:

* bertec-jump  : http://127.0.0.1:8765/api/protocol/sessions
                 -> {"ok": true, "sessions": [{id, completed_at, protocol_label, ...}]}
* runtrack     : http://127.0.0.1:8780/api/sessions
                 -> {"sessions": [{id, patient_name, started_ts, ended_ts, status, ...}]}
                 (falls back to a plain TCP reachability check when the JSON
                 endpoint is missing so an older HTML-only build still reports
                 available=true with a note)
* neurosync    : filesystem - recordings dir under the neurosync project
                 (session folders contain raw.csv / report.json)
"""

from __future__ import annotations

import json
import os
import socket
from datetime import datetime, timezone
from pathlib import Path

TIMEOUT_S = 3.0

BERTEC_HOST, BERTEC_PORT = "127.0.0.1", 8765
RUNTRACK_HOST, RUNTRACK_PORT = "127.0.0.1", 8780
BERTEC_SESSIONS_URL = f"http://{BERTEC_HOST}:{BERTEC_PORT}/api/protocol/sessions"
RUNTRACK_SESSIONS_URL = f"http://{RUNTRACK_HOST}:{RUNTRACK_PORT}/api/sessions"

_REPO_ROOT = Path(__file__).resolve().parents[1]  # .../projects/mission-control
DEFAULT_NEUROSYNC_ROOT = Path(
    os.environ.get("LABFLOW_NEUROSYNC_DIR", str(_REPO_ROOT.parent / "neurosync" / "recordings"))
)


# --------------------------------------------------------------------------- #
# default fetcher (stdlib)
# --------------------------------------------------------------------------- #
def default_fetch(url: str, timeout: float = TIMEOUT_S):
    """GET ``url``; return ``(status, text)``. Raises on network failure."""
    import urllib.error
    import urllib.request

    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", "replace")
            return int(response.status), body
    except urllib.error.HTTPError as exc:  # 404 etc. still carries a status
        try:
            body = exc.read().decode("utf-8", "replace")
        except Exception:
            body = ""
        return int(exc.code), body


def _tcp_open(host: str, port: int, timeout: float = TIMEOUT_S) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _fail(app: str, error: str, **extra) -> dict:
    out = {"app": app, "available": False, "count": 0, "latest": None, "error": error}
    out.update(extra)
    return out


def _http_error_detail(text: str) -> str:
    try:
        doc = json.loads(text)
        detail = doc.get("detail") if isinstance(doc, dict) else None
        if isinstance(detail, str):
            return detail
    except Exception:
        pass
    return ""


def _latest_entry(entries: list, stamp_keys: list) -> dict:
    """Pick the newest entry: first non-empty timestamp, then the id."""

    def key(entry: dict):
        stamp = ""
        for name in stamp_keys:
            value = entry.get(name)
            if value:
                stamp = str(value)
                break
        return (stamp, str(entry.get("id", "")))

    return max(entries, key=key)


def _call_fetch(fetch, url: str, timeout: float):
    """Call an injected/default fetcher and normalise its result to (status, text)."""
    result = fetch(url, timeout)
    if isinstance(result, tuple) and len(result) == 2:
        status, text = result
        return int(status), str(text)
    # allow simple objects / dicts for convenience
    status = getattr(result, "status", None)
    text = getattr(result, "text", None)
    if status is None and isinstance(result, dict):
        status, text = result.get("status"), result.get("text")
    if status is None:
        raise TypeError("fetcher must return (status, text)")
    return int(status), "" if text is None else str(text)


# --------------------------------------------------------------------------- #
# probes
# --------------------------------------------------------------------------- #
def probe_bertec(fetch=None, url: str = BERTEC_SESSIONS_URL, timeout: float = TIMEOUT_S) -> dict:
    """Bertec Jump Lab - stored guided-protocol sessions (newest first)."""
    fetch = fetch or default_fetch
    try:
        status, text = _call_fetch(fetch, url, timeout)
    except Exception as exc:  # connection refused / timeout / anything
        return _fail("bertec", f"{type(exc).__name__}: {exc}", endpoint=url)
    if status != 200:
        detail = _http_error_detail(text)
        error = f"HTTP {status}" + (f" ({detail})" if detail else "")
        return _fail("bertec", error, endpoint=url)
    try:
        document = json.loads(text)
    except Exception as exc:
        return _fail("bertec", f"malformed JSON: {exc}", endpoint=url)
    if not isinstance(document, dict) or not isinstance(document.get("sessions"), list):
        return _fail(
            "bertec",
            "malformed response: expected {'ok': true, 'sessions': [...]}",
            endpoint=url,
        )
    sessions = [entry for entry in document["sessions"] if isinstance(entry, dict)]
    latest = None
    if sessions:
        top = _latest_entry(sessions, ["completed_at", "started_at"])
        latest = {
            "id": top.get("id"),
            "completed_at": top.get("completed_at"),
            "protocol_label": top.get("protocol_label"),
        }
    return {"app": "bertec", "available": True, "count": len(sessions), "latest": latest,
            "endpoint": url}


def probe_runtrack(fetch=None, url: str = RUNTRACK_SESSIONS_URL, timeout: float = TIMEOUT_S,
                   tcp_check=None) -> dict:
    """RunTrack - recorded sessions via its JSON API.

    Fallback: when the JSON endpoint is unavailable (older HTML-only build) a
    plain TCP check on the server port distinguishes "app running" from "app
    down"; the result then carries a note and ``count``/``latest`` stay None.
    """
    fetch = fetch or default_fetch
    tcp_check = tcp_check or _tcp_open
    try:
        status, text = _call_fetch(fetch, url, timeout)
    except Exception as exc:
        if tcp_check(RUNTRACK_HOST, RUNTRACK_PORT, timeout):
            return {"app": "runtrack", "available": True, "count": None, "latest": None,
                    "note": "port open but JSON endpoint unreachable: " f"{type(exc).__name__}: {exc}",
                    "endpoint": url}
        return _fail("runtrack", f"{type(exc).__name__}: {exc}", endpoint=url)

    if status != 200:
        detail = _http_error_detail(text)
        note = f"HTTP {status}" + (f" ({detail})" if detail else "")
        if tcp_check(RUNTRACK_HOST, RUNTRACK_PORT, timeout):
            return {"app": "runtrack", "available": True, "count": None, "latest": None,
                    "note": f"no sessions JSON ({note}); server port open", "endpoint": url}
        return _fail("runtrack", note, endpoint=url)

    try:
        document = json.loads(text)
    except Exception as exc:
        if tcp_check(RUNTRACK_HOST, RUNTRACK_PORT, timeout):
            return {"app": "runtrack", "available": True, "count": None, "latest": None,
                    "note": f"JSON endpoint returned non-JSON ({exc}); server port open",
                    "endpoint": url}
        return _fail("runtrack", f"malformed JSON: {exc}", endpoint=url)

    if not isinstance(document, dict) or not isinstance(document.get("sessions"), list):
        if tcp_check(RUNTRACK_HOST, RUNTRACK_PORT, timeout):
            return {"app": "runtrack", "available": True, "count": None, "latest": None,
                    "note": "response lacks 'sessions' list; server port open", "endpoint": url}
        return _fail("runtrack", "malformed response: expected {'sessions': [...]}", endpoint=url)

    sessions = [entry for entry in document["sessions"] if isinstance(entry, dict)]
    latest = None
    if sessions:
        top = _latest_entry(sessions, ["ended_ts", "started_ts"])
        latest = {
            "id": top.get("id"),
            "patient_name": top.get("patient_name"),
            "ended_ts": top.get("ended_ts") or top.get("started_ts"),
            "discipline": top.get("discipline"),
            "status": top.get("status"),
        }
    return {"app": "runtrack", "available": True, "count": len(sessions), "latest": latest,
            "endpoint": url}


def _neurosync_session_dirs(root: Path) -> list:
    """Session folders under ``root`` that contain CSV recordings.

    Handles both layouts: legacy ``recordings/<stamp>/raw.csv`` and the
    subject layout ``recordings/subjects/<subject>/<stamp>/raw.csv``.
    """
    dirs = []

    def add_if_session(folder: Path):
        if folder.is_dir() and (folder / "raw.csv").exists():
            dirs.append(folder)
            return
        if folder.is_dir() and any(folder.glob("*.csv")):
            dirs.append(folder)

    for child in sorted(root.iterdir()):
        if not child.is_dir():
            continue
        if child.name == "subjects":
            for subject in sorted(child.iterdir()) if child.is_dir() else []:
                if subject.is_dir():
                    for session in sorted(subject.iterdir()):
                        add_if_session(session)
            continue
        add_if_session(child)
    return dirs


def probe_neurosync(root=None, timeout: float = TIMEOUT_S) -> dict:
    """NeuroSync - recordings on disk (count of session folders, newest first)."""
    root = Path(root) if root is not None else DEFAULT_NEUROSYNC_ROOT
    try:
        if not root.is_dir():
            return _fail("neurosync", f"recordings dir not found: {root}", path=str(root))
        sessions = _neurosync_session_dirs(root)
        latest = None
        if sessions:
            newest = max(sessions, key=lambda folder: folder.stat().st_mtime)
            latest = {
                "id": newest.name,
                "modified_at": datetime.fromtimestamp(
                    newest.stat().st_mtime, tz=timezone.utc
                ).isoformat(timespec="seconds"),
                "path": str(newest),
            }
        return {"app": "neurosync", "available": True, "count": len(sessions),
                "latest": latest, "path": str(root)}
    except Exception as exc:
        return _fail("neurosync", f"{type(exc).__name__}: {exc}", path=str(root))


def probe_all(fetch=None, neurosync_root=None) -> dict:
    """Run every probe (each is failure-isolated) and return them by app name."""
    apps = {}
    for probe in (probe_bertec, probe_runtrack):
        try:
            summary = probe(fetch=fetch)
        except Exception as exc:  # belt and braces - probes must never take the page down
            summary = _fail(probe.__name__, f"{type(exc).__name__}: {exc}")
        apps[summary["app"]] = summary
    try:
        summary = probe_neurosync(root=neurosync_root)
    except Exception as exc:
        summary = _fail("neurosync", f"{type(exc).__name__}: {exc}")
    apps[summary["app"]] = summary
    return {"checked_at": _now_iso(), "apps": apps}


if __name__ == "__main__":  # manual live check:  python -m labflow.result_probes
    print(json.dumps(probe_all(), indent=2))
