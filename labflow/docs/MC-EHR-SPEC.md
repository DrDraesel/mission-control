# Mission Control — master admin panel & lab record (build contract)

**What this is.** One place where every project's results land: patients/intake → each station's measurements → that app's own analysis and AI text → one chart per patient. An EHR-shaped record of the lab, not a certified EHR.

**What it is not.** Not a certified/HIPAA-qualified EHR, no e-signature, no billing, no regulatory audit trail. Every screen says so. The signed document remains the clinician's note inside RunTrack's clinical workspace.

---

## Where it lives

Inside the existing LabFlow app (`labflow/`, FastAPI, `:8790`) — it already owns the patient store, the workflow and the Telegram path. No second server.

New package: `labflow/mc/` — `schema.py`, `adapters/{bertec,runtrack,neurosync,inbody,intake}.py`, `ingest.py`, `chart.py`, `api.py`, `export.py`.
New UI: `labflow/static/mc/` — `index.html` (overview/patients), `patient.html` (chart), `integrations.html`, `inbody.html`, `mc.css`, `mc.js`.
Tests: `labflow/tests/test_mc_core.py`, `test_mc_api.py`, `test_mc_ui.py`.

## Canonical record

```python
Observation = {
  "subject_id": str,      # LabFlow patient id (from PatientStore)
  "source": str,          # "bertec" | "runtrack" | "neurosync" | "inbody" | "intake" | "manual"
  "session_id": str,      # source's own session id (stable)
  "measured_at": str,     # ISO-8601 with tz
  "metric": str,          # namespaced key: "bertec.asi", "runtrack.form_index", "eeg.alpha_rel"
  "value": float | str | None,
  "unit": str,            # "index", "deg", "mm/s", "%", "kg", "µV²", "bpm", "score"
  "quality": str,         # "verified" | "unverified" | "flagged" | "incomplete"
  "provenance": dict,     # {"app","device","file","protocol","firmware","processing_version"}
  "analysis": str,        # the source app's deterministic summary (its own words)
  "ai_text": str, "ai_model": str,   # optional assistant output, verbatim
}
```

Rules:
- **Metric namespaces are fixed:** `bertec.*`, `runtrack.*`, `eeg.*`, `body.*`, `vitals.*`, `intake.*`. An adapter may not invent a prefix outside its own.
- **Provenance is mandatory.** A number without a source session id and file/endpoint is rejected (`ValueError`).
- **Quality is carried, never upgraded.** `incomplete`/`flagged` from the source stays that way; MC never re-labels an uncalibrated Bertec session as verified.
- **No silent subject merging.** An adapter only attaches a session when the patient link is explicit (LabFlow `linked_sessions`, or a `patient_id`/`athlete` field that matches). Otherwise the session goes to an "unlinked" bucket that the UI shows.

## Storage

- Append-only `labflow/data/observations.jsonl`, one JSON object per line.
- Dedupe key = `sha1(source|session_id|metric|measured_at)`; ingest is idempotent.
- Index file `labflow/data/observations.index.json` rebuilt on demand (patient → session → metrics).
- **Everything under `labflow/data/` is gitignored. No patient data in git, ever.**

## Adapters (read-only, never write into the other apps)

**bertec** — `bertec-jump/data/protocols/*/session.json`
Known shape: `id, protocol_id, protocol_label, athlete, started_at, completed_at, quality, summary{segment: {means:{...}, flag_counts, fall_risk}}, kept_trials`.
Metrics: one per `summary[segment].means[*]` as `bertec.<segment>.<key>`; plus `bertec.kept_trials`, `bertec.quality`. `analysis` = protocol label + quality + the segments present.

**runtrack** — `runtrack/data/runtrack.db` (SQLite, read-only, `file:...?mode=ro`)
Table `sessions(id, patient_id, started_ts, ended_ts, duration_s, status, summary_json, view_plane, discipline)` and `patients`.
Metrics from `summary_json`: `runtrack.form_index`, `runtrack.symmetry_mean_pct`, `runtrack.trunk_lean_deg`, `runtrack.head_sway_norm`, `runtrack.external_power_est_watts`, plus joint means as `runtrack.joint.<joint>.mean`. `quality` = `verified` only when `status == 'complete'` and `view_plane != ''`; otherwise `unverified`. `analysis` = the summary's own `labels` list + form_index band notes.

**neurosync** — `neurosync/recordings/subjects/<subject>/<timestamp>/summary.json`
Known shape: device, quality, band powers, `simulated` flag, condition.
Metrics: `eeg.<band>_rel` (%), `eeg.<band>_abs` (µV²), `eeg.tbr`, `eeg.quality`. `quality` = `verified` only when the session's own quality gate passed and `simulated` is not true; simulated sessions are ingested as `unverified` with `provenance.simulated = true`. `analysis` = device + condition + the app's quality note.
If `recordings/` is empty, the adapter returns `[]` — never an error.

**inbody** — no API without a contract, so: manual entry + CSV import.
Template (documented in the UI): `measured_at,weight_kg,skeletal_muscle_kg,body_fat_kg,body_fat_pct,visceral_fat,lean_mass_kg,bmi`. Metrics under `body.*`; `quality` = `unverified` (entered by hand) unless the CSV carries a device serial, then `verified` by provenance only. The UI must label it "manual entry — verify against the device printout".

**intake** — from `PatientStore` `intake` + `measurements` (vitals etc.). Metrics under `intake.*` and `vitals.*`.

## API (FastAPI router mounted by `labflow/app.py`, prefix `/api/mc`)

| Method | Path | Returns |
|---|---|---|
| GET | `/api/mc/overview` | counts (patients, linked sessions per source, observations), last ingest time, integration status list |
| GET | `/api/mc/patients` | patient list with counts per source + last activity |
| GET | `/api/mc/patients/{pid}/chart?refresh=0` | the chart payload: patient, timeline, per-source cards, latest measurements by metric |
| POST | `/api/mc/patients/{pid}/sync` | run adapters for that patient, return what was added |
| POST | `/api/mc/ingest` | push from an app: `{source, session_id, subject_id, measured_at, metrics:[{metric,value,unit}], quality, provenance, analysis, ai_text, ai_model}` |
| POST | `/api/mc/patients/{pid}/inbody` | manual body-composition entry |
| POST | `/api/mc/patients/{pid}/link` | `{source, session_id}` — explicit link of an unlinked session |
| GET | `/api/mc/integrations` | per-source: path/endpoint, reachable, sessions found, last checked |
| GET | `/api/mc/patients/{pid}/export.html` | self-contained chart HTML (print to PDF) |

Error shape: `{"detail": "..."}` with 400 for validation, 404 for unknown patient.

## UI (served by LabFlow at `:8790`, design-system styling)

- **`/mc`** — master panel: patient table (name, age, last activity, per-source chips), "Sync all", unlinked-session count, integration health strip. One primary action: **New patient / intake**.
- **`/mc/patient/{pid}`** — the chart: header (name, DOB, status), timeline of sessions newest-first with source badge and quality badge, per-source cards (Bertec / RunTrack / NeuroSync / InBody / Intake) showing the latest values with units and provenance on hover, the app's own `analysis` text, AI text with model + timestamp, and **Export chart HTML**.
- **`/mc/integrations`** — table of sources: path, reachable yes/no, sessions found, last checked, and what to do when unreachable.
- **`/mc/inbody`** — manual entry form with the CSV template download.

Every page carries the footer: *"Lab record for research and operations. Not a certified EHR; not a medical device; clinical decisions are physician-led."*

Charts: no external JS libraries, inline SVG only.

## Tests (synthetic only)

`test_mc_core.py` — adapters against tmp copies of the three known shapes (bertec session.json, runtrack sqlite, neurosync summary.json), including: empty dirs return `[]`; simulated NeuroSync session is `unverified`; uncalibrated/incomplete Bertec stays `incomplete`; observation without provenance raises; dedupe makes a second ingest add 0.
`test_mc_api.py` — every endpoint with a temp data dir; 404 unknown patient; ingest validation 400; export HTML contains the disclaimer.
`test_mc_ui.py` — pages render (TestClient) with the disclaimer, the patient table, and the chart cards; no external script tags.

## Ownership (parallel agents)

- **A (core):** `mc/schema.py`, `mc/adapters/*`, `mc/ingest.py`, `mc/chart.py`, `test_mc_core.py`.
- **B (API + export):** `mc/api.py`, `mc/export.py`, mount in `labflow/app.py`, `test_mc_api.py`.
- **C (UI):** `labflow/static/mc/*`, `test_mc_ui.py`, screenshots under `labflow/verification/`.

Do not edit another owner's files. `app.py` is B's alone.
