# Mission Control

Two local-first tools that run on the lab PC — **no cloud, no accounts, data stays on the machine.**

## 1) LabFlow — patient-flow conductor (`labflow/`)
A local FastAPI app that drives a provider + patient **step-by-step** through a lab baseline: intake & consent → vitals (HR/temp/SpO₂) → HRV → InBody/weight → blood panels → squats/strength → EEG baseline → balance battery → treadmill form. Per step it launches the right lab app, offers manual capture fields, auto-detects results via read-only probes, keeps patient records + measurements in local JSON, and can send **operational-only** Telegram alerts ("step done → next step") — never clinical values.

- Open: `Start LabFlow.cmd` → http://127.0.0.1:8790
- Workflow order + stations: `labflow/workflow.yaml` (longest test last, intake pinned first)
- Tests: `.venv\Scripts\python.exe -m unittest discover -s labflow/tests` (202 tests)
- Config: copy `labflow/config.example.json` → `labflow/config.json` (the real config is local-only and gitignored; absent config = console notifier)

## 2) Open-source research crawler (`tools/`, `research/`)
A daily sweep (local cron, 9 AM) over GitHub + the web for new free/open-source tools that can replace paid software (video, graphics, 3D, web, faceless content). Dated reports live in `research/daily/*.md`; the dedupe ledger is kept alongside.

## Privacy & safety
- All patient/session data stays local (`labflow/data/` — gitignored, never committed).
- Telegram alerts carry a patient label + step names only — no measurements.
- **Not a medical device.** Research/orchestration tooling; clinical decisions are physician-led.
