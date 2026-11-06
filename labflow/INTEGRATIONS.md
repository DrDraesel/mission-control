# How the lab platform connects internally

Everything here is **local-first**: five apps on one Windows PC, talking over loopback
or reading each other's files. Nothing leaves the machine except the two optional
outbound paths listed at the bottom.

```
                    ┌─────────────────────────────┐
                    │  LabFlow  (:8790, FastAPI)  │  patient + workflow conductor
                    │  labflow/workflow.yaml      │
                    └───┬─────────┬─────────┬─────┘
        read-only probe │         │         │  read-only probe
                        ▼         ▼         ▼
        ┌──────────────────┐ ┌──────────┐ ┌──────────────────────┐
        │ Bertec  (:8765)  │ │ RunTrack │ │ NeuroSync            │
        │ plate + vision   │ │ (:8780)  │ │ (desktop Qt, no port)│
        │ data/protocols/  │ │ SQLite   │ │ recordings/subjects/ │
        └──────────────────┘ └──────────┘ └──────────────────────┘
```

## The seven pieces

| App | Kind | Address / path | What it owns |
|---|---|---|---|
| **LabFlow / Mission Control** | FastAPI | `http://127.0.0.1:8790` | patient records, step workflow, measurement registry, master panel, notifications |
| **Bertec Jump** | FastAPI | `http://127.0.0.1:8765` | force plate acquisition, protocols, balance metrics, vision lane |
| **RunTrack** | Flask | `http://127.0.0.1:8780` | treadmill/cycling form studies, camera rig, clinical workspace |
| **NeuroSync** | Desktop (Qt) | `recordings/subjects/<subject>/<timestamp>/` | EEG capture, qEEG grid, reports |
| **InBody Stage 1** (`DrDraesel/InBodyStage1`) | Local web app (Python) | `http://127.0.0.1:8080` · DB `runtime/inbody.db` | body composition: import (manual/normalized/PDF-OCR/spreadsheet), rules, trends, clinician + patient summaries, append-only history |
| **Intake Kiosk** (`DrDraesel/Intakekiosk`) | React/Vite (kiosk UI) | local dev server, or the Vercel demo | voice/text patient intake (EN/ES/RU), 23-question health interview — **in-memory only, no persistence** |
| **Design system** | Files | `projects/design-system/` | `tokens.css`, `components.css`, `lab_theme.py` shared by the UIs |

> **Port note:** InBody Stage 1 defaults to **8080**, the same port Strata uses. Run InBody on `8088`
> (or keep Strata stopped) — two listeners on 8080 is the kind of collision that looks like "the app
> is broken" for an hour.

## InBody Stage 1 contract (the body-composition source of truth)

- **DB:** SQLite at `runtime/inbody.db` (`INBODY_DATABASE_URL`). Tables: `patients`, `encounters`,
  `results` (with `content` = normalized JSON, `supersedes`, `source_hash`), `analyses`, `reviews`,
  `audit`, `outbox`.
- **Normalized payload** (`schemas/normalized-v1.json`): required `encounter_id`, `test_timestamp`,
  `source_identifier`, `measurements[{metric,value,unit,status?}]`; optional `patient_id`,
  `device_model`, `source_type` ∈ manual | mock_api | pdf | image | spreadsheet.
- **REST:** `GET /patients/{id}/inbody`, `/inbody/{result_id}`, `/inbody/trends`,
  `POST /patients/{id}/inbody/import`, `POST /inbody/webhook`, `/health`.
- **Mission Control reads it read-only** (DB or API) and maps measurements to `body.*`.
  It never writes into the InBody store; corrections stay in InBody's own append-only history.

## Intake Kiosk → Mission Control

- The kiosk keeps everything **in browser memory** and stores nothing itself. On **Review & finish**
  it POSTs the completed check-in to `http://127.0.0.1:8790/api/intake` (override with `VITE_MC_URL`).
- LabFlow maps it to a patient (`name`, `dob`, `phone`) and keeps the structured fields, the original
  transcript, locale and the attention flag in `patient.intake`. A retried delivery with the same
  submission id returns the **same** patient — no duplicates.
- CORS is open only for `http://127.0.0.1:5173` and `http://localhost:5173`; any other origin is refused.
- Run the kiosk locally (`npm run dev`) on the clinic PC. Do **not** use the public Vercel demo with
  real answers — it has no clinic endpoint and its data is synthetic by design.
- If delivery fails the kiosk shows **"NOT delivered"** in the staff view: the answers then exist only
  in that browser tab.


## Contracts (what each side actually promises)

**Bertec → LabFlow**
- `GET /api/status` — plate state (`streaming`, `zeroed`, rate, uncalibrated flag).
- `GET /api/protocol/sessions` — completed protocol sessions for the station probe.
- Data on disk: `data/protocols/` (JSON per session, atomic writes).

**RunTrack → LabFlow**
- `GET /api/sessions` — recorded sessions for the form station.
- Data on disk: `data/runtrack.db` + per-session folders (SQLite, no server-side DB).

**NeuroSync → LabFlow**
- No port. LabFlow lists `recordings/` and treats a session directory with `summary.json` as a completed EEG station.
- Read-only: LabFlow never writes into `recordings/`.

**LabFlow → provider**
- Telegram step alerts (`labflow/config.json` → `notify`), operational text only: patient label + step names, **never** measurements.
- Absent config ⇒ console notifier; nothing is sent.

**Shared AI (optional)**
- Ollama `http://127.0.0.1:11434` (`qwen3.8:latest`) — used by RunTrack's coach and NeuroSync's AI panel.
- Strata `http://127.0.0.1:8080/v1` when the Q2_0 server is running (text-only; not vision).

## Status of each link (verified, not assumed)

| Link | Status |
|---|---|
| LabFlow ↔ Bertec probe | live (`/api/protocol/sessions`) |
| LabFlow ↔ RunTrack probe | live (`/api/sessions`) |
| LabFlow ↔ NeuroSync probe | live (filesystem) |
| LabFlow → Telegram | live (token read from the Hermes `.env`, chat id in local config) |
| Ollama | live on `:11434` |
| Strata | installed; server must be started manually after a reboot |
| Email delivery | **not configured** — no SMTP credentials on this PC |
| agentring (agent → phone) | installed, **not paired** — needs relay + Firebase + voice key + an Android phone |
| Second GitHub mirror (dual-push) | script ready (`projects/dual-push.ps1`), **no second account exists** |

## Ports and launchers

```
8790  LabFlow          Start LabFlow.cmd
8780  RunTrack         Start Run Lab.cmd
8765  Bertec Jump      (uvicorn) — see bertec-jump/README.md
8791  Bertec vision worker (spawned by the app; must be free before start)
11434 Ollama           ollama serve
8080  Strata           serve/server.py --engine strata --config <profile> --port 8080
```

Only one process may own a given port. A stale vision worker on `:8791` or a stale
Bertec on `:8765` is the usual cause of "it starts but shows nothing".

## What is deliberately *not* connected

- **No cloud sync of patient data.** Each PC keeps its own records; there is no replication.
- **No clinical values in notifications.** Step names and patient labels only.
- **No third-party relay for PHI.** agentring, if piloted, carries job status only.
