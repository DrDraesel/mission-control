"""LabFlow web layer — a small local FastAPI app over the LabFlow core.

Lets lab staff run a patient through the station flow visually: create a
patient from the intake form, see the next step big and clear, launch the
right instrument app per station, capture results (manual fields + read-only
probes of the lab apps) and record measurements.

Run::

    .venv\\Scripts\\python.exe -m uvicorn labflow.app:app --host 127.0.0.1 --port 8790

(``Start LabFlow.cmd`` does exactly this and opens the browser.)

Local-only: binds 127.0.0.1, patient JSON files stay under ``labflow/data``
(override with the ``LABFLOW_DATA_DIR`` env var, or ``data_dir`` in
``labflow/config.json``).  The only outbound traffic is the core notifier
(Telegram, labels only — never clinical values).

Optional ``labflow/config.json`` (local, gitignored-style; absent == console
notifier)::

    {"notify": {"type": "telegram", "bot_token_file": "...", "chat_id": "...",
                "include_patient_name": true},
     "port": 8790, "data_dir": "..."}

API — every response is JSON with an ``ok`` boolean:

* ``GET  /``                                -> the static UI
* ``GET  /api/patients``                    -> list (with progress)
* ``POST /api/patients`` {name, intake}     -> create + initialise the flow
* ``GET  /api/patients/{id}``               -> patient + workflow + steps + next
* ``POST /api/patients/{id}/begin``         -> begin the current station
* ``POST /api/patients/{id}/complete``      -> complete the current station
* ``POST /api/patients/{id}/skip``          -> skip the current station
* ``POST /api/patients/{id}/redo``          -> reopen a station
* ``POST /api/patients/{id}/measurement``   -> append a measurement
* ``POST /api/patients/{id}/link``          -> link a lab-app session + complete
* ``GET  /api/patients/{id}/probes``        -> read-only probe of the lab apps
* ``GET  /api/workflow``                    -> serialized workflow (ordered)
* ``GET  /api/next/{patient_id}``           -> next-step instruction text

Flow-state rules (documented decisions):

* 404 for an unknown patient (and unknown station on redo).
* 400 for a malformed request (missing name / metric / station_id) and for a
  patient name longer than :data:`MAX_NAME_LENGTH` characters (the id is
  derived from the name; an overlong slug overflows the Windows file path).
* 409 when the requested station is not the current step, or the flow is
  already complete.  Completing the *current* step that is still ``pending``
  is allowed and auto-begins it — the engine records ``started_at`` itself, so
  staff can hit Done without a separate Begin click.
* The core engine completes "the current station"; this layer therefore
  rejects a ``station_id`` that is not the current station instead of
  silently completing a different one.
* Repeat-click / double-click guard (idempotency): every mutation runs while
  holding a per-patient in-process lock (see ``_patient_lock``) and the
  request's ``station_id`` is re-validated against the freshly persisted
  state inside that lock — a second rapid "Done"/"Skip"/"Begin" click for the
  station that just closed gets a 409 ``ok:false`` instead of silently
  advancing (or re-closing) a station, and concurrent saves cannot lose each
  other's writes.
* Robustness: every save is retried across transient Windows file locks
  (``_retrying_save``); if the OS still refuses after the retries the
  endpoint answers 503 with the documented ``{"ok": false, ...}`` JSON
  envelope — mutations never return a plain-text 500.
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path

from fastapi import Body, FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from labflow.engine import FlowEngine
from labflow.notify import make_notifier
from labflow.patients import PatientStore
from labflow.result_probes import probe_all
from labflow.workflow import DEFAULT_WORKFLOW, Workflow

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
CONFIG_PATH = BASE_DIR / "config.json"
WORKFLOW_PATH = BASE_DIR / "workflow.yaml"
DEFAULT_PORT = 8790

#: Patient-name cap (F3 in the 2026-10-16 review): the patient id is derived
#: from the name (slug + hex), so an unbounded name overflows the Windows
#: ~260-char path limit inside ``tempfile.mkstemp`` and used to surface as a
#: FileNotFoundError 500.  120 chars is far beyond any real name.
MAX_NAME_LENGTH = 120


# --------------------------------------------------------------------------- #
# config / construction helpers
# --------------------------------------------------------------------------- #
def load_config(path=None) -> dict:
    """Load the optional local config file; return {} when absent/broken."""
    target = Path(path) if path is not None else CONFIG_PATH
    try:
        text = target.read_text(encoding="utf-8")
        data = json.loads(text)
    except (OSError, json.JSONDecodeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def default_data_dir(config=None) -> Path:
    """Where patient JSON files live (env > config > ``labflow/data``)."""
    env = os.environ.get("LABFLOW_DATA_DIR")
    if env:
        return Path(env)
    config = config if isinstance(config, dict) else {}
    configured = config.get("data_dir")
    if configured:
        return Path(configured)
    return BASE_DIR / "data"


def load_workflow(path=None) -> Workflow:
    """``workflow.yaml`` when present, else the built-in DEFAULT_WORKFLOW."""
    target = Path(path) if path is not None else WORKFLOW_PATH
    if target.exists():
        try:
            return Workflow.from_yaml(target)
        except ValueError:
            # fall back to the seed rather than refusing to boot the lab
            return DEFAULT_WORKFLOW
    return DEFAULT_WORKFLOW


class ApiError(Exception):
    """JSON error with an HTTP status (rendered as {"ok": false, ...})."""

    def __init__(self, status_code: int, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def _retry_windows_lock(func, *args, **kwargs):
    """Retry a *repeat-safe* call when Windows briefly locks a saved file.

    ``os.replace`` on Windows occasionally raises ``PermissionError``
    (WinError 32) while an indexer/AV briefly holds a freshly written file.
    Only used around calls that are explicitly safe to repeat — the engine's
    ``start_patient`` is documented idempotent, and the store's ``save`` is a
    whole-payload atomic write (a failed ``os.replace`` leaves the target
    untouched), so re-running either cannot duplicate or corrupt state.
    """
    delay = 0.05
    for attempt in range(4):
        try:
            return func(*args, **kwargs)
        except PermissionError:
            if attempt == 3:
                raise
            time.sleep(delay)
            delay *= 2.


def _retrying_save(save_func):
    """Wrap ``PatientStore.save`` so one transient Windows lock is retried.

    ``save`` is the single write choke point of the app (the engine's step
    updates, the final status flip, ``store.create``'s draft save, the
    measurement/link helpers — all funnel through it) and it is repeat-safe
    by construction: the payload goes to a fresh tmp file and a failed
    ``os.replace`` cleans up and leaves the target untouched.  Retrying *this
    unit* — rather than re-running whole endpoints — matters because
    ``FlowEngine.complete_step``/``skip_step`` perform **two** saves (step
    update + final status flip): an endpoint-level retry could silently
    complete the *next* station instead of just re-writing the failed one.
    """

    def save(patient):
        return _retry_windows_lock(save_func, patient)

    return save


def create_app(config=None, store=None, workflow=None, notifier=None, engine=None,
               probe_fn=None, static_dir=None) -> FastAPI:
    """Build the FastAPI app.  Every collaborator is injectable for tests."""
    config = config if isinstance(config, dict) else load_config()
    store = store if store is not None else PatientStore(default_data_dir(config))
    # Every write in the app (draft save in create, step updates, status
    # flips, measurements, links) funnels through store.save — retry the
    # transient Windows lock at that single, repeat-safe choke point.
    store.save = _retrying_save(store.save)
    workflow = workflow if workflow is not None else load_workflow()
    if notifier is None:
        notify_cfg = config.get("notify")
        notifier = make_notifier(notify_cfg if isinstance(notify_cfg, dict) else {})
    engine = engine if engine is not None else FlowEngine(store, workflow, notifier)
    static_root = Path(static_dir) if static_dir is not None else STATIC_DIR

    app = FastAPI(title="LabFlow", version="1.0.0", docs_url="/docs", redoc_url=None)

    # -- error rendering -------------------------------------------------
    @app.exception_handler(ApiError)
    async def _api_error(_request: Request, exc: ApiError):
        return JSONResponse(status_code=exc.status_code, content={"ok": False, "error": exc.message})

    @app.exception_handler(KeyError)
    async def _key_error(_request: Request, exc: KeyError):
        detail = exc.args[0] if exc.args else str(exc)
        return JSONResponse(status_code=404, content={"ok": False, "error": str(detail)})

    @app.exception_handler(ValueError)
    async def _value_error(_request: Request, exc: ValueError):
        return JSONResponse(status_code=400, content={"ok": False, "error": str(exc)})

    @app.exception_handler(OSError)
    async def _os_error(_request: Request, exc: OSError):
        """OS/file errors must still honour the JSON ``ok`` envelope.

        Raised when the OS will not release a patient file even after the
        retries (transient Windows lock, permissions, disk trouble).  503 is
        "try again later" — and the answer is JSON, never a plain-text 500.
        """
        return JSONResponse(
            status_code=503,
            content={"ok": False, "error": f"file system error: {exc}"},
        )

    # -- mutation serialisation ------------------------------------------
    # One lock per patient id, taken by every mutating endpoint around its
    # whole read-check-mutate-save sequence.  Why a lock instead of only
    # retrying: the 2026-10-16 review showed that concurrent saves to one
    # patient file fail with WinError 5/32 *and*, worse, two requests that
    # read the same snapshot overwrite each other (lost writes + duplicate
    # notifications).  A retry cannot fix that — it must be serialised.  The
    # lock also closes the check-then-act window between _require_current
    # and the engine call (that is the double-click guard together with the
    # fresh-state station_id re-check below).
    _lock_registry_guard = threading.Lock()
    _patient_locks: dict[str, threading.Lock] = {}

    def _patient_lock(patient_id) -> threading.Lock:
        """The lock guarding all mutations of one patient file."""
        key = str(patient_id)
        with _lock_registry_guard:
            lock = _patient_locks.get(key)
            if lock is None:
                lock = threading.Lock()
                _patient_locks[key] = lock
            return lock

    # -- helpers -----------------------------------------------------------
    def _patient_or_404(patient_id: str) -> dict:
        patient = store.get(patient_id)
        if patient is None:
            raise ApiError(404, f"unknown patient: {patient_id!r}")
        return patient

    def _station_payload(station, order=None, step=None) -> dict:
        data = station.to_dict()
        if order is not None:
            data["order"] = order
        if step is not None:
            entry = step if isinstance(step, dict) else {}
            data["state"] = entry.get("state") or "pending"
            data["started_at"] = entry.get("started_at")
            data["completed_at"] = entry.get("completed_at")
            data["step_notes"] = entry.get("notes") or ""
            data["results"] = list(entry.get("results") or [])
        data["minutes_text"] = station.minutes_text()
        data["launch_hint"] = station.launch_hint()
        data["capture_prompt"] = station.capture_prompt()
        return data

    def _ordered() -> list:
        return workflow.ordered_stations()

    def _current_payload(patient) -> dict | None:
        station = engine.current_step(patient)
        if station is None:
            return None
        index = next((i for i, s in enumerate(_ordered()) if s.id == station.id), None)
        entry = (patient.get("steps") or {}).get(station.id)
        return _station_payload(station, index, entry)

    def _steps_payload(patient) -> list:
        payload = []
        for index, station in enumerate(_ordered()):
            entry = (patient.get("steps") or {}).get(station.id)
            payload.append(_station_payload(station, index, entry))
        return payload

    def _patient_view(patient) -> dict:
        current = _current_payload(patient)
        return {
            "patient": patient,
            "workflow": _workflow_payload(),
            "steps": _steps_payload(patient),
            "current": current,
            "next": current,
            "next_instruction": engine.next_instruction(patient),
            "progress": engine.progress(patient),
        }

    def _workflow_payload() -> dict:
        return {
            "name": workflow.name,
            "version": workflow.version,
            "sort_rule": workflow.sort_rule,
            "stations": [_station_payload(station, index) for index, station in enumerate(_ordered())],
            "validation_errors": workflow.validation_errors(),
        }

    def _require_current(patient_id: str, patient: dict, station_id):
        """Return the current station, guarding an explicit station_id mismatch.

        This is also the repeated/double-click idempotency guard: every
        mutation calls it *inside* the patient's lock with a fresh load, so a
        second rapid "Done"/"Skip" click naming the station that just closed
        gets a 409 ``ok:false`` guard error instead of advancing (or
        re-closing) a station — exactly one advance, exactly one
        ``step_completed`` notification per click pair.
        """
        station = engine.current_step(patient)
        if station is None:
            raise ApiError(409, "flow already complete — no current step")
        if station_id not in (None, ""):
            if str(station_id) != station.id:
                raise ApiError(
                    409,
                    f"station {station_id!r} is not the current step (current: {station.id!r})",
                )
        return station

    # -- static ------------------------------------------------------------
    app.mount("/static", StaticFiles(directory=str(static_root)), name="static")

    @app.get("/")
    def index():
        return FileResponse(str(static_root / "index.html"))

    @app.get("/mirror")
    def mirror():
        """Portrait station display for the Circolo mirror (1080x1920).

        Read-only: it polls the same JSON API as the main UI, so the mirror
        never mutates a patient — the front desk stays the only writer.
        """
        return FileResponse(str(static_root / "mirror.html"))

    # -- patients ----------------------------------------------------------
    @app.get("/api/patients")
    def list_patients():
        patients = []
        for patient in store.list():
            patients.append({
                "id": patient.get("id"),
                "name": patient.get("name"),
                "status": patient.get("status"),
                "created_at": patient.get("created_at"),
                "dob": patient.get("dob"),
                "contact": patient.get("contact"),
                "progress": engine.progress(patient),
            })
        return {"ok": True, "patients": patients}

    @app.post("/api/patients")
    def create_patient(payload: dict = Body(default={})):
        name = str(payload.get("name") or "").strip()
        if not name:
            raise ApiError(400, "name is required")
        if len(name) > MAX_NAME_LENGTH:
            raise ApiError(
                400,
                f"name must be {MAX_NAME_LENGTH} characters or fewer "
                f"(got {len(name)})",
            )
        intake = payload.get("intake")
        intake = intake if isinstance(intake, dict) else {}
        # No per-patient lock here (the id does not exist yet, and every
        # create gets a unique id/file); the draft save is protected by the
        # store.save retry above.
        patient = store.create(
            name,
            intake=intake,
            dob=payload.get("dob") or intake.get("dob") or intake.get("date_of_birth"),
            contact=payload.get("contact") or intake.get("contact"),
        )
        # initialise the flow right away (draft -> active, every station pending);
        # start_patient is idempotent, so a transient Windows file lock may be retried
        patient = _retry_windows_lock(engine.start_patient, patient["id"]) or patient
        return {"ok": True, "patient": patient, "progress": engine.progress(patient)}

    @app.get("/api/patients/{patient_id}")
    def get_patient(patient_id: str):
        patient = _patient_or_404(patient_id)
        return {"ok": True, **_patient_view(patient)}

    @app.post("/api/patients/{patient_id}/begin")
    def begin_step(patient_id: str, payload: dict = Body(default={})):
        with _patient_lock(patient_id):
            patient = _patient_or_404(patient_id)
            _require_current(patient_id, patient, payload.get("station_id"))
            updated = engine.begin_step(patient_id) or patient
            return {"ok": True, **_patient_view(updated)}

    @app.post("/api/patients/{patient_id}/complete")
    def complete_step(patient_id: str, payload: dict = Body(default={})):
        with _patient_lock(patient_id):
            patient = _patient_or_404(patient_id)
            _require_current(patient_id, patient, payload.get("station_id"))
            notes = payload.get("notes")
            results = payload.get("results")
            updated = engine.complete_step(
                patient_id, notes=notes if isinstance(notes, str) else "", results=results
            )
            if updated is None:
                raise ApiError(409, "flow already complete — no current step")
            return {"ok": True, **_patient_view(updated)}

    @app.post("/api/patients/{patient_id}/skip")
    def skip_step(patient_id: str, payload: dict = Body(default={})):
        with _patient_lock(patient_id):
            patient = _patient_or_404(patient_id)
            _require_current(patient_id, patient, payload.get("station_id"))
            reason = payload.get("reason")
            updated = engine.skip_step(patient_id, reason if isinstance(reason, str) else "")
            if updated is None:
                raise ApiError(409, "flow already complete — no current step")
            return {"ok": True, **_patient_view(updated)}

    @app.post("/api/patients/{patient_id}/redo")
    def redo_step(patient_id: str, payload: dict = Body(default={})):
        with _patient_lock(patient_id):
            patient = _patient_or_404(patient_id)
            station_id = payload.get("station_id")
            if not station_id:
                raise ApiError(400, "station_id is required")
            if workflow.get_station(station_id) is None:
                raise ApiError(404, f"unknown station: {station_id!r}")
            updated = engine.redo_step(patient_id, station_id) or patient
            return {"ok": True, **_patient_view(updated)}

    @app.post("/api/patients/{patient_id}/measurement")
    def add_measurement(patient_id: str, payload: dict = Body(default={})):
        with _patient_lock(patient_id):
            patient = _patient_or_404(patient_id)
            metric = str(payload.get("metric") or "").strip()
            if not metric:
                raise ApiError(400, "metric is required")
            updated = store.add_measurement(
                patient_id, metric, payload.get("value"), payload.get("unit"), payload.get("source")
            )
            measurements = updated.get("measurements") or []
            return {
                "ok": True,
                "patient": updated,
                "measurement": measurements[-1] if measurements else None,
            }

    @app.post("/api/patients/{patient_id}/link")
    def link_session(patient_id: str, payload: dict = Body(default={})):
        """Link a lab-app session id and close the current step with it."""
        with _patient_lock(patient_id):
            _patient_or_404(patient_id)
            app_name = str(payload.get("app") or "").strip()
            session_id = payload.get("session_id")
            if not app_name:
                raise ApiError(400, "app is required")
            if session_id is None or str(session_id) == "":
                raise ApiError(400, "session_id is required")
            updated = store.link_session(patient_id, app_name, session_id)

            step_completed = False
            station = engine.current_step(updated)
            if station is not None:
                completed = engine.complete_step(
                    patient_id,
                    notes=f"Linked {app_name} session {session_id}",
                    results={"linked_session": {"app": app_name, "id": str(session_id)},
                             "station": station.id},
                )
                if completed is not None:
                    updated = completed
                    step_completed = True
            return {
                "ok": True,
                "linked": {"app": app_name, "session_id": str(session_id)},
                "step_completed": step_completed,
                **_patient_view(updated),
            }

    @app.get("/api/patients/{patient_id}/probes")
    def get_probes(patient_id: str):
        _patient_or_404(patient_id)
        runner = probe_fn or probe_all  # resolved per call so tests can patch probe_all
        patient = store.get(patient_id) or {}
        station = engine.current_step(patient)
        station_probe = None
        if station is not None:
            capture = station.capture if isinstance(station.capture, dict) else {}
            station_probe = capture.get("probe")
        return {"ok": True, "probes": runner(), "station_probe": station_probe}

    # -- workflow / next ----------------------------------------------------
    @app.get("/api/workflow")
    def get_workflow():
        return {"ok": True, "workflow": _workflow_payload()}

    @app.get("/api/next/{patient_id}")
    def get_next(patient_id: str):
        patient = _patient_or_404(patient_id)
        return {
            "ok": True,
            "instruction": engine.next_instruction(patient),
            "current": _current_payload(patient),
            "progress": engine.progress(patient),
        }

    return app


app = create_app()


if __name__ == "__main__":  # manual run:  python -m labflow.app
    import uvicorn

    _config = load_config()
    uvicorn.run(
        "labflow.app:app",
        host="127.0.0.1",
        port=int(_config.get("port") or DEFAULT_PORT),
        reload=False,
    )
