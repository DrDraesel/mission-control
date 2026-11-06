# What is in GitHub, what can't be, and how to rebuild a machine

All five repos are **public**, and none of them contains patient data, credentials, models or vendor SDKs. This file is the boundary: what lives in git, what must be copied by hand, and how to stand a lab PC back up from the repos alone.

## Tracked vs excluded, per repo

| Repo | In git | Deliberately excluded |
|---|---|---|
| `runtrack` | app code, templates/static, tests, `docs/`, pose config, launchers | `data/` (SQLite DB + session folders incl. video), `.venv/`, `ai_settings.env`, logs, `graphify-out/`, generated verification JPGs |
| `neurosync` | app code, tests, `docs/`, `METHODS.md`, launchers | `recordings/` (raw EEG CSV, summaries, charts), `logs/`, `.venv/`, `ai_settings.env`, `runtime_status.json` |
| `bertec-jump` | service/UI/protocol code, tests, `docs/`, static assets | `data/` (force traces, trials, vision clips), `config.json`, `vendor/` + `sdk.zip` (FTDI/plate SDK), `models/` (pose weights), `.venv/` |
| `mission-control` | LabFlow code, workflow YAML, tests, `research/daily/*.md`, `docs/` | `labflow/data/` (patients, observations), `labflow/config.json` (holds the Telegram chat id), `data/`, `*.db`, `sandbox/`, `videos/`, `content/`, `.venv/` |
| `design-system` | tokens, components, Qt theme, preview, sync script | nothing sensitive |

**Never committed, in any repo:** patient names/DOB/contact, EEG or force-plate traces, session videos, `.env`/API keys/SMTP passwords, device SDK archives you do not have redistribution rights for, model weights over ~100 MB.

## What cannot be pushed to GitHub, and why

| Item | Why | What to do instead |
|---|---|---|
| Patient records and recordings | PHI; public repos | stays in the local `data/` and `recordings/` trees; move a machine by copying those folders over the LAN |
| `config.json` (LabFlow) | contains the Telegram chat id and a token file path | copy `config.example.json` and fill it in locally |
| `ai_settings.env` | API keys | re-enter on each machine |
| Bertec `vendor/` + `sdk.zip` | third-party redistribution terms | re-install on the target PC per `bertec-jump/docs/` |
| Pose model weights (`models/`) | size / licence | download on the target machine |
| Raw `.venv` | machine-specific binaries | run `setup.cmd` |
| Session videos | size + PHI | keep local |

## Rebuild a machine from the repos

```bash
git clone https://github.com/DrDraesel/runtrack.git
git clone https://github.com/DrDraesel/neurosync.git
git clone https://github.com/DrDraesel/bertec-jump.git
git clone https://github.com/DrDraesel/mission-control.git
git clone https://github.com/DrDraesel/design-system.git
```

Then, per app: `setup.cmd` (creates `.venv`, Python 3.11) → copy any `data/` or `recordings/` you want to bring over → launch.

| App | Launch | Port | First-run requirement |
|---|---|---|---|
| RunTrack | `Start Run Lab.cmd` | 8780 | cameras; optional `OLLAMA_URL` / `AI_API_*` |
| NeuroSync | `Start NeuroSync.cmd` | — (Qt) | headset powered; Dragon needs pairing mode |
| Bertec Jump | uvicorn per `bertec-jump/README.md` | 8765 | plate on USB, then **zero it** before any measurement |
| LabFlow / Mission Control | `Start LabFlow.cmd` | 8790 | copy `labflow/config.example.json` → `config.json`; patient data starts empty |
| Design system | `sync.sh` (copies `lab_theme.py` into apps) | — | none |

Nothing syncs between machines. Each PC keeps its own patient history — by design.

## Credentials the platform expects (none are in git)

| Purpose | Variable / file | Where it goes |
|---|---|---|
| Telegram step alerts | bot token from `%LOCALAPPDATA%\\hermes\\.env`, chat id in `labflow/config.json` | local only |
| Local AI | `OLLAMA_URL`, `OLLAMA_MODEL` (default `http://127.0.0.1:11434`, `qwen3.8:latest`) | env |
| Any OpenAI-compatible AI | `AI_API_URL`, `AI_API_KEY`, `AI_API_MODEL` | env or `ai_settings.env` |
| Email delivery | `MAIL_SMTP_HOST`, `MAIL_SMTP_PORT`, `MAIL_SMTP_USER`, `MAIL_SMTP_PASS`, `MAIL_FROM` | not configured yet |
| agentring | relay URL, Firebase project, voice key | not configured yet |

## Public-repo hygiene rules

1. Before adding a file: would I be comfortable with it on the open internet? If it names a person, measures a person, or authenticates anything — no.
2. `git status` before every commit; `data/` must never appear.
3. If a secret ever lands in a commit, rotate it first, then rewrite history — deleting the file in a later commit is not enough.
4. Reports and charts generated from real sessions stay in the local data trees, never in `docs/` or `verification/` (those are for synthetic fixtures only).
