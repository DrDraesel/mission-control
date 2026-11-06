"""Mission Control — the lab's master panel and per-patient record.

An EHR-*shaped* record of the lab, not a certified EHR.  One canonical
:class:`~labflow.mc.schema.Observation` per number, read-only adapters over the
other apps, an append-only store, and one chart per patient.

Public surface (used by ``mc.api`` and the UI)::

    from labflow.mc import Ingest, build_chart, DISCLAIMER

    ingest = Ingest(store)                    # PatientStore (or a path)
    ingest.sync()                             # every adapter -> observations.jsonl
    ingest.sync("jane-doe-1a2b")              # one patient
    ingest.add([observation, ...])            # explicit push (API/manual entry)
    ingest.read()                             # resolved rows
    ingest.unlinked()                         # sessions waiting for an explicit link
    ingest.rebuild_index()                    # observations.index.json

    build_chart(store, "jane-doe-1a2b")       # patient + timeline + cards + latest

Contract: ``labflow/docs/MC-EHR-SPEC.md``.  Nothing in this package writes into
another app's directory, and no patient data is ever committed (``labflow/data``
is gitignored).
"""

from .adapters import (
    ADAPTERS,
    AdapterContext,
    AdapterResult,
    build_context,
    collect_all,
    default_roots,
)
from .chart import build_chart, group_sessions, latest_by_metric
from .ingest import DISCLAIMER, Ingest, ObservationStore, default_data_dir, read_observations
from .schema import (
    QUALITIES,
    QUALITY_TRUST,
    SOURCE_LABELS,
    SOURCE_ORDER,
    SOURCE_PREFIXES,
    SOURCES,
    Observation,
    ObservationError,
    dedupe_key,
    normalize_quality,
    normalize_timestamp,
)

__version__ = "1.0.0"

__all__ = [
    # record
    "Observation",
    "ObservationError",
    "SOURCES",
    "QUALITIES",
    "SOURCE_PREFIXES",
    "SOURCE_LABELS",
    "SOURCE_ORDER",
    "QUALITY_TRUST",
    "dedupe_key",
    "normalize_quality",
    "normalize_timestamp",
    # adapters
    "ADAPTERS",
    "AdapterContext",
    "AdapterResult",
    "build_context",
    "collect_all",
    "default_roots",
    # storage
    "Ingest",
    "ObservationStore",
    "DISCLAIMER",
    "default_data_dir",
    "read_observations",
    # chart
    "build_chart",
    "group_sessions",
    "latest_by_metric",
]
