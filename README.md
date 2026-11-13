# Mission Control

The lab's local hub: **LabFlow** (the patient-flow conductor) and the **open-source research crawler**. Local-first — no cloud, no accounts.

## 1) LabFlow — patient-flow conductor (`labflow/`)

A local FastAPI app that drives a provider + patient **step-by-step** through a lab baseline: intake & consent → vitals (HR/temp/SpO₂) → HRV → InBody/weight → blood panels → squats/strength → EEG baseline → balance battery → treadmill form. Per step it launches the right lab app, offers manual capture fields, auto-detects results via read-only probes, keeps patient records + measurements in local JSON, and can send **operational-only** Telegram alerts ("step done → next step") — never clinical values.

- Open: `Start LabFlow.cmd` → http://127.0.0.1:8790
- Workflow order + stations: `labflow/workflow.yaml` (longest test last, intake pinned first)
- Tests: `.venv\Scripts\python.exe -m unittest discover -s labflow/tests`
- Config: copy `labflow/config.example.json` → `labflow/config.json` (the real config is local-only and gitignored; absent config = console notifier)
- **How it connects to Bertec, RunTrack, NeuroSync and the shared AI: [`labflow/INTEGRATIONS.md`](labflow/INTEGRATIONS.md)** — ports, endpoints, data contracts, and which links are verified live.

## 2) Open-source research crawler (`tools/`, `research/`)

A daily sweep (local cron, 9 AM) over GitHub + the web for new free/open-source tools that can replace paid software (video, graphics, 3D, web, faceless content). Dated reports live in `research/daily/*.md`; the dedupe ledger is kept alongside.

Run one day by hand:

```
.venv\Scripts\python.exe tools/daily_github_research.py
```

## Privacy & safety

- All patient/session data stays local (`labflow/data/` — gitignored, never committed; likewise `data/` and `recordings/` in the other apps).
- Telegram alerts carry a patient label + step names only — no measurements.
- **Not a medical device.** Research/orchestration tooling; clinical decisions are physician-led.

## Patient visit workflow and digital consent (review candidate)

The `intake_to_balance` profile follows **Intake → Digital consent → InBody → RunTrack → Bertec athlete / balance**. Select it in local `labflow/config.json` using `"workflow_profile": "intake_to_balance"`; the example configuration selects this profile. The original broad lab baseline remains available as `full_lab` and remains the compatibility default when the profile is omitted. Review open visits before switching profiles; no existing patient file is migrated automatically.

In `/mc`, click the patient's name to open the chart. The chart now shows the received intake, current step, step checklist, digital consent, saved consent history and a link into the guided visit for that patient. Consent receipts retain the exact configured document, version/hash, signer, server timestamp, patient and visit binding. An unconfigured/unapproved document cannot be signed. Intake may be reviewed before consent; assessment begins after the separate consent step.

See [patient workflow, consent configuration and verification](docs/PATIENT-WORKFLOW-CONSENT.md) for configuration and remaining clinic deployment dependencies. This candidate adds workflow mechanics; it does not certify live device capture, production authentication or clinical approval.
