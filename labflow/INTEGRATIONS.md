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

## The five pieces

| App | Kind | Address / path | What it owns |
|---|---|---|---|
| **LabFlow** | FastAPI | `http://127.0.0.1:8790` | patient records, step workflow, measurement registry, notifications |
| **Bertec Jump** | FastAPI | `http://127.0.0.1:8765` | force plate acquisition, protocols, balance metrics, vision lane |
| **RunTrack** | Flask | `http://127.0.0.1:8780` | treadmill/cycling form studies, camera rig, clinical workspace |
| **NeuroSync** | Desktop (Qt) | `recordings/subjects/<subject>/<timestamp>/` | EEG capture, qEEG grid, reports |
| **Design system** | Files | `projects/design-system/` | `tokens.css`, `components.css`, `lab_theme.py` shared by the UIs |

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
