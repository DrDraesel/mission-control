# Mission Control patient visit and digital consent

Development candidate, November 13, 2026. Repository: DrDraesel/mission-control. No real records, device codes or service credentials are included.

## Intended visit

| Step | Existing app / receiving home | Completion evidence |
| --- | --- | --- |
| Intake | Intakekiosk → `POST /api/intake` → Mission Control patient record | Staff review of the received intake and selected identity |
| Digital consent | Mission Control patient chart | Signature receipt for the current approved document and visit; then staff completion |
| InBody | InBodyStage1 → Mission Control InBody adapter / ingest | Source result/session already received in the chart with explicit patient and visit binding |
| RunTrack | Existing RunTrack application and adapter | Recorded session in the chart, explicitly bound to this visit |
| Bertec athlete / balance | Existing bertec-jump application and adapter | Recorded session in the chart, explicitly bound to this visit; quality/calibration status retained |

The profile is `labflow/patient-workflow.yaml`, with configuration order enforced rather than duration sorting. Configure `workflow_profile: intake_to_balance` in local `labflow/config.json`. `full_lab` retains the prior broader assessment. The application does not silently migrate active visits when a profile changes; choose the profile before beginning a new workflow deployment.

## Patient-facing and staff controls

`/mc` lists patients with clickable name buttons. `/mc/patient/{id}` shows the patient name/DOB, incoming intake, current step, checklist, signing screen and consent history download. **Open guided visit** selects that same patient in the existing LabFlow station UI. The API includes a `station_id` alias so existing station UI mutations carry their expected current-step identifier.

Incoming kiosk check-in is not a signature. An imported `consent_signed` checkbox cannot satisfy the new gate. Intake review may be completed before the separate consent step. Consent cannot be skipped, and no assessment can begin/complete after withdrawal or a document-version change until a valid current signature is recorded. Linking another app's session cannot complete intake/consent.

The five-step profile also rejects assessment completion without a matching chart observation. The source must match the current step, the observation's `subject_id` must be the selected patient, and its `provenance.visit_id` must equal the visit ID returned by `GET /api/patients/{id}`. This intentionally holds old adapter data that lacks an encounter binding; a matching name or patient alone does not establish the visit. The physical assessment steps can be skipped through the existing explicit skip action, with that action retained in the step record; skipped means no completed measurement.

## Consent configuration

The repository includes no new clinical consent wording and no claim that a blank legacy consent is the current clinic packet. Use the current IMW-approved visit document. Configure `consent_document` with:

- `id`, `version`, `title`, and the exact plain `text` shown to the patient (up to 50,000 characters).
- `approved: true` only after the clinic has selected the applicable document; retain `approved_by` and `approved_at`.
- `consent_required: true` (default). The explicit false setting exists for isolated legacy workflow regression tests; it is not the intended patient-visit configuration.

`config.example.json` has an unapproved placeholder. An absent/unapproved document blocks signing and assessments. Do not replace the placeholder by copying test wording. Procedure-specific consent requirements remain part of the appropriate clinical workflow; this visit-level mechanism does not establish that one generic document authorizes every service.

Patients or authorized representatives enter their full name and independently confirm agreement and intent to sign electronically. The server validates the displayed document version/hash and patient/visit binding. Representative relationship/authority is retained as entered; staff identity/authority verification is still an operational responsibility. The patient signer name must match the selected chart name, allowing only whitespace/case normalization.

Receipts are separate local files at `labflow/data/consents/{patient_id}/{receipt_id}.json` (or the configured data root), outside git. Each stores the exact signed document text, its approval metadata/hash/version, patient/DOB, visit, signer, typed-signature method, explicit intent and server timestamp. The interface never edits earlier receipts. Retrying the same submission id with the same details returns the same receipt; changed details conflict. Withdrawal creates another receipt and blocks further workflow advancement. Existing signed receipts remain available for download. These files are retained evidence, not a claim of filesystem tamper-proofing or institutional identity verification.

New patient records receive a visit ID. Legacy records use a stable initial-visit identifier. A new visit must receive a new visit ID; previous signatures cannot authorize it. The existing patient store is still a single active workflow per record; multi-visit registration/reconciliation needs completion before production deployment.

## Verification and actual limits

Run `python -m unittest discover -s labflow/tests -q`. Dedicated fictional tests exercise intake receipt/list/chart, unsigned blocking, document approval, signatures, retries/conflicts, wrong patient/visit/document, representative metadata, restart persistence, withdrawals, document updates, and the five-step assessment sequence with actual chart ingestion. Existing frozen workflow regressions explicitly use legacy consent-disabled configuration and are separate from default-on gate tests. JavaScript syntax checks cover both changed UI scripts.

An attempted headless browser verification was blocked by the execution environment's browser socket restriction. No completed browser interaction, visual certification, physical device capture or clinic deployment is claimed.

Still required for live operation: select the current clinic consent packet; complete staff authentication/authorization and protected network/storage/backup deployment; verify kiosk payload on the clinic PC; implement/verify source-to-Mission-Control visit ID propagation; validate original report storage and all-data transfer (current observations alone do not transfer original files/full analyses/review history); verify RunTrack/Bertec sessions and calibration quality on the devices. InBodyStage1 still has its synthetic-only restriction and disabled vendor adapter. USB HOST on the InBody 380 supports flash-drive export/printer accessories, not a documented direct USB-host-to-PC cable path. Wi-Fi-free acquisition can use device USB export or the documented serial/LookinBody route. A device setup code is never saved in this repository.
