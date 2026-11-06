"""Read-only adapters — one module per lab app, one shared context.

Each adapter exposes ``collect(ctx) -> AdapterResult`` and only ever *reads*
from its app's directory or SQLite file.  Nothing here writes to another app's
tree; the only writes in Mission Control happen in :mod:`labflow.mc.ingest`.

Linking rule (spec: "no silent subject merging"): a session attaches to a
patient only when the link is explicit — the patient's
``linked_sessions[source]['ids']``, or a field that *is* a LabFlow patient id,
or an exact (case/whitespace-insensitive) name match.  Ambiguous name matches
stay unlinked rather than guessing.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..schema import Observation

__all__ = [
    "ADAPTERS",
    "AdapterContext",
    "AdapterResult",
    "build_context",
    "collect_all",
    "default_roots",
    "project_root",
]

#: Repo root of Mission Control (``.../mission-control``).
def project_root() -> Path:
    """``mission-control/`` — three levels above ``labflow/mc/adapters``."""
    return Path(__file__).resolve().parents[3]


def _env_path(name: str) -> Path | None:
    value = os.environ.get(name)
    return Path(value).expanduser() if value else None


def default_roots(data_dir=None) -> dict[str, Path]:
    """Where each source lives by default.

    The apps are sibling projects on the lab PC (``projects/<app>``); every path
    can be overridden with ``MC_BERTEC_ROOT`` / ``MC_RUNTRACK_ROOT`` /
    ``MC_NEUROSYNC_ROOT``.  InBody has no app: its CSVs live inside LabFlow's own
    data dir, which is why ``data_dir`` matters here.
    """
    projects = project_root().parent
    inbody_dir = Path(data_dir) / "inbody" if data_dir else project_root() / "labflow" / "data" / "inbody"
    return {
        "bertec": _env_path("MC_BERTEC_ROOT") or projects / "bertec-jump",
        "runtrack": _env_path("MC_RUNTRACK_ROOT") or projects / "runtrack",
        "neurosync": _env_path("MC_NEUROSYNC_ROOT") or projects / "neurosync",
        "inbody": inbody_dir,
    }


def _norm(text) -> str:
    """Case- and whitespace-insensitive comparison key."""
    return " ".join(str(text or "").split()).casefold()


@dataclass
class AdapterResult:
    """What one adapter found on disk."""

    observations: list[Observation] = field(default_factory=list)
    #: Sessions we could see but could not attribute to a patient.
    unlinked: list[dict] = field(default_factory=list)
    #: Files we could not read at all (shown in the integrations panel).
    errors: list[dict] = field(default_factory=list)
    #: Non-fatal remarks ("InBody database not found") — not failures.
    notes: list[dict] = field(default_factory=list)

    def extend(self, other: "AdapterResult") -> "AdapterResult":
        self.observations.extend(other.observations)
        self.unlinked.extend(other.unlinked)
        self.errors.extend(other.errors)
        self.notes.extend(other.notes)
        return self

    def __bool__(self) -> bool:  # truthy when there is anything to report
        return bool(self.observations or self.unlinked or self.errors or self.notes)


@dataclass
class AdapterContext:
    """Everything an adapter needs: paths + the patients it may attach to."""

    roots: dict[str, Path] = field(default_factory=dict)
    store: Any = None
    patients: list[dict] = field(default_factory=list)
    #: ``source -> {external id -> patient id}`` for explicit non-session links
    #: (e.g. a ``body.inbody_patient_id`` recorded when the patient was linked).
    verified_links: dict[str, dict[str, str]] = field(default_factory=dict)
    #: True when the caller pointed us at an isolated data dir (tests, exports,
    #: a scratch lab).  Machine-wide app stores (the InBody SQLite) are then not
    #: read unless the caller names them explicitly with ``INBODY_DB``.
    sandboxed: bool = False

    # -- paths ---------------------------------------------------------------
    def root(self, source: str) -> Path | None:
        path = self.roots.get(source)
        return Path(path) if path else None

    # -- identity ------------------------------------------------------------
    @property
    def patient_ids(self) -> set[str]:
        return {str(p.get("id")) for p in self.patients if p.get("id")}

    def linked_index(self, source: str) -> dict[str, str]:
        """``session_id -> patient_id`` from each patient's explicit links."""
        index: dict[str, str] = {}
        for patient in self.patients:
            sessions = (patient.get("linked_sessions") or {}).get(source) or {}
            for session_id in sessions.get("ids") or []:
                index[str(session_id)] = str(patient.get("id"))
        return index

    def find_patient(self, source: str, *candidates, name=None) -> str | None:
        """Resolve an explicit link, or ``None`` (never a fuzzy guess).

        Order: explicit ``linked_sessions`` id, then a candidate that *is* a
        LabFlow patient id, then an exact normalized name match.  More than one
        name match is treated as ambiguous and stays unlinked.
        """
        linked = self.linked_index(source)
        values = [str(c) for c in candidates if c is not None and str(c).strip()]

        for value in values:
            if value in linked:
                return linked[value]

        hints = self.verified_links.get(source) or {}
        for value in values:
            if value in hints:
                return hints[value]

        known = self.patient_ids
        for value in values:
            if value in known:
                return value

        wanted = _norm(name)
        if wanted:
            matches = [str(p.get("id")) for p in self.patients if _norm(p.get("name")) == wanted]
            if len(matches) == 1:
                return matches[0]
        return None


def _links_from_patients(patients: list[dict]) -> dict[str, dict[str, str]]:
    """Explicit non-session links recorded on the patient (InBody patient id)."""
    hints: dict[str, dict[str, str]] = {}
    for patient in patients:
        patient_id = str(patient.get("id") or "")
        if not patient_id:
            continue
        intake = patient.get("intake")
        if isinstance(intake, dict) and intake.get("inbody_patient_id") not in (None, ""):
            hints.setdefault("inbody", {})[str(intake["inbody_patient_id"])] = patient_id
        for entry in patient.get("measurements") or []:
            if not isinstance(entry, dict):
                continue
            if str(entry.get("metric") or "") != "body.inbody_patient_id":
                continue
            if entry.get("value") not in (None, ""):
                hints.setdefault("inbody", {})[str(entry["value"])] = patient_id
    return hints


def _is_lab_data_dir(path) -> bool:
    """True for the real ``labflow/data`` (as opposed to a temp sandbox)."""
    try:
        return Path(path).resolve() == (project_root() / "labflow" / "data").resolve()
    except OSError:  # pragma: no cover - unresolvable path
        return False


def build_context(
    store=None,
    roots: dict | None = None,
    data_dir=None,
    patients=None,
    links: dict | None = None,
) -> AdapterContext:
    """Assemble an :class:`AdapterContext` from a ``PatientStore``."""
    resolved = dict(roots) if roots else default_roots(data_dir)
    if store is not None and data_dir is None:
        data_dir = getattr(store, "root_dir", None)
    if data_dir is not None and not roots:
        # InBody has no app of its own; dropped files belong to LabFlow's data dir.
        resolved["inbody"] = Path(data_dir) / "inbody"
    if patients is None:
        patients = store.list() if store is not None else []
    patients = list(patients)

    verified = _links_from_patients(patients)
    for source, mapping in (links or {}).items():
        verified.setdefault(source, {}).update(mapping)
    sandboxed = data_dir is not None and not _is_lab_data_dir(data_dir)
    return AdapterContext(
        roots=resolved,
        store=store,
        patients=patients,
        verified_links=verified,
        sandboxed=sandboxed,
    )


def collect_all(ctx: AdapterContext) -> tuple[list[Observation], list[dict], list[dict], list[dict]]:
    """Run every adapter; return ``(observations, unlinked, errors, notes)``."""
    observations: list[Observation] = []
    unlinked: list[dict] = []
    errors: list[dict] = []
    notes: list[dict] = []
    for source, adapter in ADAPTERS.items():
        try:
            result = adapter(ctx)
        except Exception as exc:  # noqa: BLE001 - one broken app must not stop sync
            errors.append({"source": source, "error": f"{type(exc).__name__}: {exc}"})
            continue
        observations.extend(result.observations)
        unlinked.extend(result.unlinked)
        errors.extend(result.errors)
        notes.extend(result.notes)
    return observations, unlinked, errors, notes


# Imported last: the submodules import this module's names, so they must exist
# before the imports below run.
from . import bertec, inbody, intake, neurosync, runtrack  # noqa: E402

#: Registry, in chart presentation order.
ADAPTERS = {
    "bertec": bertec.collect,
    "runtrack": runtrack.collect,
    "neurosync": neurosync.collect,
    "inbody": inbody.collect,
    "intake": intake.collect,
}
