"""LabFlow — patient-flow conductor for a sports performance lab.

Operational workflow tool: drives a provider + patient step by step through a
multi-station baseline assessment (intake form -> vitals -> InBody ->
HRV -> blood panels -> EEG baseline -> balance battery -> treadmill running
form -> squats/strength).  Station order comes from the workflow config
(``workflow.yaml``, JSON-compatible YAML); the default rule is 'longest_last'.

* Patient data stays local — JSON files under the lab's own root dir.
* Telegram notifications contain no clinical values (step/next info only).
* Pure core: stdlib + requests (Telegram only); no web framework needed.

Convenience re-exports::

    from labflow import (
        Station, Workflow, DEFAULT_WORKFLOW,      # config
        PatientStore, utc_now_iso,                # storage
        FlowEngine,                               # conductor
        Notifier, ConsoleNotifier, TelegramNotifier, NullNotifier,
        make_notifier, read_token_from_file,      # alerts
    )
"""

from .workflow import DEFAULT_WORKFLOW, CAPTURE_TYPES, LAUNCH_TYPES, SORT_RULES, Station, Workflow
from .patients import PATIENT_STATUSES, STEP_STATES, PatientStore, utc_now_iso
from .engine import CLOSED_STATES, FlowEngine
from .notify import (
    ConsoleNotifier,
    Notifier,
    NullNotifier,
    TelegramNotifier,
    make_notifier,
    read_token_from_file,
)

__version__ = "1.0.0"

__all__ = [
    "Station",
    "Workflow",
    "DEFAULT_WORKFLOW",
    "LAUNCH_TYPES",
    "CAPTURE_TYPES",
    "SORT_RULES",
    "PatientStore",
    "STEP_STATES",
    "PATIENT_STATUSES",
    "utc_now_iso",
    "FlowEngine",
    "CLOSED_STATES",
    "Notifier",
    "ConsoleNotifier",
    "TelegramNotifier",
    "NullNotifier",
    "make_notifier",
    "read_token_from_file",
    "__version__",
]
