"""The actual intake → consent → next-step API flow, with fictional records."""
import tempfile
import unittest
import uuid
from pathlib import Path

from fastapi.testclient import TestClient
from labflow.app import create_app
from labflow.patients import PatientStore
from labflow.notify import NullNotifier

DOCUMENT = {'id':'fictional-consent','version':'test-1','title':'Fictional visit consent',
            'text':'Fictional test only. I agree to this simulated visit. No clinical consent is supplied.',
            'approved':True,'approved_by':'Fictional test reviewer','approved_at':'2026-11-13'}


class ConsentFlow(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store=PatientStore(Path(self.tmp.name))
        self.config={'consent_document':dict(DOCUMENT)}
        self.client=self.client_for(self.config)
        response=self.client.post('/api/intake',json={'id':'fictional-checkin',
            'patient':{'name':'Avery Example','dob':'1990-05-16'},
            'fields':{'goals':'Fictional assessment'},'transcript':[]})
        self.assertEqual(response.status_code,200)
        self.patient=response.json()['patient']
        self.path='/api/patients/'+self.patient['id']

    def client_for(self, config):
        return TestClient(create_app(config=config,store=self.store,notifier=NullNotifier()))

    def signature(self, **changes):
        consent=self.client.get(self.path+'/consent').json()
        return {'submission_id':str(uuid.uuid4()),'visit_id':consent['visit_id'],
                'document_sha256':consent['document']['sha256'],
                'document_version':consent['document']['version'],
                'signer_name':'Avery Example','signer_role':'patient',
                'read_and_agree':True,'electronic_signature':True,**changes}

    def test_kiosk_chart_signature_receipt_and_next_step(self):
        listed=self.client.get('/api/mc/patients').json()['patients']
        self.assertTrue(any(p['id']==self.patient['id'] for p in listed))
        self.assertEqual(self.client.get('/mc/patient/'+self.patient['id']).status_code,200)
        self.assertEqual(self.client.post(self.path+'/complete',json={}).status_code,400)
        payload=self.signature()
        signed=self.client.post(self.path+'/consent',json=payload)
        self.assertEqual(signed.status_code,200,signed.text)
        receipt=signed.json()['receipt']
        self.assertEqual(receipt['document']['text'],DOCUMENT['text'])
        self.assertEqual(receipt['dob'],'1990-05-16')
        self.assertEqual(self.client.post(self.path+'/consent',json=payload).json()['receipt']['id'],receipt['id'])
        self.assertEqual(len(self.client.get(self.path+'/consent/receipts').json()['receipts']),1)
        complete=self.client.post(self.path+'/complete',json={'station_id':'intake'})
        self.assertEqual(complete.status_code,200,complete.text)
        self.assertNotEqual(complete.json()['current']['id'],'intake')
        restarted=self.client_for(self.config).get(self.path).json()
        self.assertTrue(restarted['consent']['valid'])

    def test_missing_or_unapproved_document_fails_closed_by_default(self):
        for config in ({},{'consent_document':dict(DOCUMENT,approved=False)}):
            client=self.client_for(config)
            self.assertFalse(client.get(self.path).json()['consent']['can_proceed'])
            self.assertEqual(client.post(self.path+'/complete',json={}).status_code,400)
            self.assertEqual(client.post(self.path+'/consent',json=self.signature()).status_code,400)

    def test_cannot_skip_link_or_measure_around_consent(self):
        for action,payload in [('skip',{}),('link',{'app':'inbody','session_id':'test'}),
                               ('measurement',{'metric':'weight','value':80})]:
            response=self.client.post(self.path+'/'+action,json=payload)
            self.assertEqual(response.status_code,400,response.text)
        self.assertEqual(self.store.get(self.patient['id'])['linked_sessions'],{})
        self.assertEqual(self.store.get(self.patient['id'])['measurements'],[])
        self.assertEqual(self.client.post(self.path+'/consent',json=self.signature()).status_code,200)
        self.assertEqual(self.client.post(self.path+'/skip',json={}).status_code,400)

    def test_wrong_identity_visit_document_and_missing_intent_rejected(self):
        for fields in ({'signer_name':'Other Example'},{'visit_id':'another-visit'},
                       {'document_version':'obsolete'},{'document_sha256':'wrong'},
                       {'read_and_agree':False},{'electronic_signature':False},
                       {'signer_role':'authorized_representative'}):
            with self.subTest(fields=fields):
                self.assertEqual(self.client.post(self.path+'/consent',json=self.signature(**fields)).status_code,400)
        self.assertEqual(len(self.client.get(self.path+'/consent/receipts').json()['receipts']),0)

    def test_withdrawal_document_change_and_new_visit_block_advance(self):
        payload=self.signature()
        self.client.post(self.path+'/consent',json=payload)
        self.client.post(self.path+'/complete',json={})
        new_doc=self.client_for({'consent_document':dict(DOCUMENT,version='test-2',text='Updated fictional text')})
        self.assertFalse(new_doc.get(self.path).json()['consent']['valid'])
        self.assertEqual(new_doc.post(self.path+'/begin',json={}).status_code,400)
        withdrawn=self.client.post(self.path+'/consent/withdraw',json={'reason':'Fictional patient withdrawal'})
        self.assertEqual(withdrawn.status_code,200,withdrawn.text)
        self.assertEqual(self.client.post(self.path+'/begin',json={}).status_code,400)
        self.client.post(self.path+'/consent',json=payload)  # old retry cannot undo withdrawal
        self.assertFalse(self.client.get(self.path).json()['consent']['valid'])
        self.assertEqual(len(self.client.get(self.path+'/consent/receipts').json()['receipts']),2)
        self.client.post(self.path+'/consent',json=self.signature())
        self.assertTrue(self.client.get(self.path).json()['consent']['valid'])
        patient=self.store.get(self.patient['id']);patient['visit_id']='a-new-visit';self.store.save(patient)
        self.assertFalse(self.client.get(self.path).json()['consent']['valid'])

    def test_request_id_conflict_and_representative(self):
        payload=self.signature(signer_role='authorized_representative',signer_name='Jordan Example',relationship='Parent / authorized representative (fictional)')
        self.assertEqual(self.client.post(self.path+'/consent',json=payload).status_code,200)
        payload['relationship']='Changed authority'
        self.assertEqual(self.client.post(self.path+'/consent',json=payload).status_code,400)
        self.assertEqual(len(self.client.get(self.path+'/consent/receipts').json()['receipts']),1)

    def test_five_step_visit_requires_result_for_correct_patient_and_visit(self):
        self.client=self.client_for(dict(self.config,workflow_profile='intake_to_balance'))
        view=self.client.get(self.path).json()
        self.assertEqual([step['id'] for step in view['steps']],
                         ['intake','consent','inbody','runtrack','bertec_balance'])
        self.assertEqual(self.client.post(self.path+'/complete',json={'station_id':'intake'}).status_code,200)
        self.assertEqual(self.client.get(self.path).json()['current']['id'],'consent')
        self.assertEqual(self.client.post(self.path+'/complete',json={}).status_code,400)
        self.client.post(self.path+'/consent',json=self.signature())
        self.assertEqual(self.client.post(self.path+'/complete',json={'station_id':'consent'}).status_code,200)
        self.assertEqual(self.client.post(self.path+'/link',json={'app':'runtrack','session_id':'unknown'}).status_code,400)
        self.assertEqual(self.client.post(self.path+'/complete',json={'results':{'result_id':'unknown'}}).status_code,400)
        visit_id=self.client.get(self.path).json()['consent']['visit_id']
        def ingest(source, session, visit):
            prefix={'inbody':'body','runtrack':'runtrack','bertec':'bertec'}[source]
            return self.client.post('/api/mc/ingest',json={
                'source':source,'subject_id':self.patient['id'],'session_id':session,
                'measured_at':'2026-11-13T10:00:00-05:00','quality':'unverified',
                'provenance':{'app':'fictional-test','endpoint':'fictional://result','visit_id':visit},
                'metrics':[{'metric':prefix+'.example','value':1,'unit':'index'}]})
        self.assertEqual(ingest('inbody','wrong-visit','another-visit').status_code,200)
        self.assertEqual(self.client.post(self.path+'/link',json={'app':'inbody','session_id':'wrong-visit'}).status_code,400)
        for source, session, expected in [('inbody','body-test','runtrack'),
                                           ('runtrack','run-test','bertec_balance'),
                                           ('bertec','balance-test',None)]:
            self.assertEqual(ingest(source,session,visit_id).status_code,200)
            response=self.client.post(self.path+'/link',json={'app':source,'session_id':session})
            self.assertEqual(response.status_code,200,response.text)
            current=response.json()['current']
            self.assertEqual(current['id'] if current else None,expected)
        chart=self.client.get('/api/mc/patients/'+self.patient['id']+'/chart').json()
        self.assertIn('inbody',str(chart))
        self.assertEqual(self.client.get(self.path).json()['patient']['status'],'completed')

    def test_chart_has_consent_and_guided_next_step_controls(self):
        page=self.client.get('/mc/patient/'+self.patient['id']).text
        for identifier in ('visit-next','show-consent','consent-form','consent-document',
                           'complete-intake','guided-visit','visit-intake'):
            self.assertIn('id="'+identifier+'"',page)
