"""Versioned consent documents and per-visit electronic signature receipts.

Clinical wording is supplied by IMW in local configuration, never generated here.
Receipts retain the exact text shown and are never edited by this interface.
"""
import hashlib
import json
import os
import re
import tempfile
import uuid
from pathlib import Path

from .patients import utc_now_iso


def _hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


class ConsentStore:
    def __init__(self, store, config):
        self.store = store
        self.required = config.get('consent_required', True) is not False
        raw = config.get('consent_document')
        self.document = None
        if isinstance(raw, dict):
            keys = ('id', 'version', 'title', 'text', 'approved_by', 'approved_at')
            if all(isinstance(raw.get(k), str) and raw[k].strip() for k in keys):
                if len(raw['text']) > 50000:
                    raise ValueError('Consent document exceeds 50,000 characters')
                self.document = {k: raw[k] for k in keys}
                self.document.update(approved=raw.get('approved') is True,
                                     sha256=_hash(raw['text']))

    def _folder(self, patient):
        # PatientStore validates ids; the folder is never chosen by a request body.
        path = self.store._path(patient['id'])
        if path is None:
            raise ValueError('Invalid patient id')
        return self.store.root_dir / 'consents' / path.stem

    def records(self, patient):
        folder = self._folder(patient)
        if not folder.exists():
            return []
        records = []
        for path in folder.glob('*.json'):
            # Fail closed on damaged evidence rather than silently treating it as signed.
            with path.open(encoding='utf-8') as handle:
                record = json.load(handle)
            if record.get('patient_id') != patient['id']:
                raise ValueError('Consent receipt patient mismatch')
            records.append(record)
        return sorted(records, key=lambda r: (r['recorded_at'], r['id']))

    @staticmethod
    def visit_id(patient):
        return patient.get('visit_id') or 'initial-' + patient['id']

    def status(self, patient):
        doc = self.document
        records = [r for r in self.records(patient)
                   if r.get('visit_id') == self.visit_id(patient)]
        last = records[-1] if records else None
        valid = bool(doc and doc['approved'] and last and last.get('action') == 'signed'
                     and last.get('document', {}).get('sha256') == doc['sha256']
                     and last.get('document', {}).get('version') == doc['version'])
        reason = ('signed' if valid else 'document_not_configured' if not doc or not doc['approved']
                  else 'withdrawn' if last and last.get('action') == 'withdrawn'
                  else 'document_changed' if last else 'signature_required')
        return {'required': self.required, 'valid': valid,
                'can_proceed': valid or not self.required, 'reason': reason,
                'visit_id': self.visit_id(patient), 'document': doc,
                'last_receipt': last, 'history_count': len(records)}

    def require(self, patient):
        if not self.status(patient)['can_proceed']:
            raise ValueError('Digital consent is required before starting the visit. Open Consent in the patient chart.')

    def _save(self, patient, receipt):
        folder = self._folder(patient)
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / (receipt['id'] + '.json')
        if path.exists():
            raise ValueError('Consent receipt already exists')
        fd, temporary = tempfile.mkstemp(dir=folder, suffix='.tmp')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as handle:
                json.dump(receipt, handle, ensure_ascii=False, indent=2, allow_nan=False)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return receipt

    def sign(self, patient, payload):
        doc = self.document
        if not doc or not doc['approved']:
            raise ValueError('The current IMW consent document has not been configured and approved')
        if payload.get('document_sha256') != doc['sha256'] or payload.get('document_version') != doc['version']:
            raise ValueError('Consent document changed; reload and read the current document')
        if payload.get('visit_id') != self.visit_id(patient):
            raise ValueError('Visit changed; reload the patient chart')
        if payload.get('read_and_agree') is not True or payload.get('electronic_signature') is not True:
            raise ValueError('Reading/agreement and intent to sign electronically must both be confirmed')
        name = payload.get('signer_name')
        relation = payload.get('signer_role')
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 120 or any(ord(c) < 32 for c in name):
            raise ValueError('Signer full name is required, maximum 120 characters')
        name = name.strip()
        if relation not in ('patient', 'authorized_representative'):
            raise ValueError('Select patient or authorized representative')
        if relation == 'patient' and ' '.join(name.casefold().split()) != ' '.join(patient['name'].casefold().split()):
            raise ValueError('Patient signature must match the selected patient name')
        relationship = payload.get('relationship', '')
        if not isinstance(relationship, str) or len(relationship) > 200:
            raise ValueError('Invalid representative relationship')
        if relation == 'authorized_representative' and not relationship.strip():
            raise ValueError('Representative relationship/authority is required')
        try:
            identifier = str(uuid.UUID(payload.get('submission_id', '')))
        except (ValueError, TypeError, AttributeError):
            raise ValueError('A valid consent submission id is required')
        request = {'document_sha256': doc['sha256'], 'document_version': doc['version'],
                   'visit_id': self.visit_id(patient), 'signer_name': name,
                   'signer_role': relation, 'relationship': relationship.strip()}
        request_hash = _hash(json.dumps(request, sort_keys=True))
        existing = next((r for r in self.records(patient) if r['id'] == identifier), None)
        if existing:
            if existing.get('request_sha256') != request_hash:
                raise ValueError('Consent submission id was reused with different details')
            return existing
        return self._save(patient, {'id': identifier, 'action': 'signed',
            'patient_id': patient['id'], 'patient_name': patient['name'], 'dob': patient.get('dob'),
            **request, 'recorded_at': utc_now_iso(), 'document': dict(doc),
            'read_and_agree': True, 'electronic_signature': True,
            'signature_method': 'typed_name_with_explicit_intent', 'request_sha256': request_hash})

    def withdraw(self, patient, payload):
        if not self.status(patient)['valid']:
            raise ValueError('No current signed consent to withdraw')
        reason = payload.get('reason', '')
        if not isinstance(reason, str) or not 1 <= len(reason.strip()) <= 500:
            raise ValueError('A withdrawal reason is required, maximum 500 characters')
        return self._save(patient, {'id': str(uuid.uuid4()), 'action': 'withdrawn',
            'patient_id': patient['id'], 'visit_id': self.visit_id(patient),
            'recorded_at': utc_now_iso(), 'reason': reason.strip()})
