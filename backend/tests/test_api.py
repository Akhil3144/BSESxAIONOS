import os,tempfile,json,csv,io,hashlib
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db import engine, reports, snapshots, evaluations, select
from backend.app.engine import digest
from backend.app.seed import sample
from pypdf import PdfReader
import pytest
@pytest.fixture(scope='module')
def env():
    with TestClient(app) as client:
        tokens={r:{'Authorization':'Bearer '+client.post('/api/login',json={'username':r,'password':os.environ['DEMO_PASSWORD']}).json()['token']} for r in ['admin','analyst','reviewer','evaluator']}
        seed=client.post('/api/demo/seed',headers=tokens['admin']);assert seed.status_code==200
        yield client,tokens

def test_auth(env):
    c,t=env;assert c.get('/api/records').status_code==401;assert c.get('/api/audit',headers=t['analyst']).status_code==403;assert c.post('/api/demo/seed',headers=t['analyst']).status_code==403

def test_dashboard_and_seed(env):
    c,t=env;d=c.get('/api/dashboard',headers=t['admin']).json();assert d['cases']==5;assert d['records']==40;assert d['supported']==5

def upload(c,t,rows):
    stream=io.StringIO();w=csv.DictWriter(stream,fieldnames=list(rows[0]));w.writeheader()
    for r in rows: w.writerow({**r,'specification':json.dumps(r['specification'])})
    return c.post('/api/import',headers=t['analyst'],files={'file':('records.csv',stream.getvalue(),'text/csv')})

def test_import_valid_invalid_duplicate_and_source(env):
    c,t=env;good=sample('NEW-PO','500','2024-01-01');bad=sample('BAD-PO','-1','not-date');r=upload(c,t,[good,bad]).json();assert r['accepted']==1;assert r['rejected']==1
    assert c.get('/api/sources/'+r['id'],headers=t['reviewer']).status_code==200
    assert upload(c,t,[good]).json()['rejected']==1

def test_holdout_fields_rejected(env):
    c,t=env;r=sample('LEAK');r['award_price']='123';assert upload(c,t,[r]).status_code==422

def test_mapping_and_xlsx(env):
    from openpyxl import Workbook
    c,t=env;r=sample('XLSX-DEMO','500','2024-01-01');r['source_column']=r.pop('id');r['specification']=json.dumps(r['specification']);wb=Workbook();ws=wb.active;ws.append(list(r));ws.append(list(r.values()));out=io.BytesIO();wb.save(out)
    response=c.post('/api/import',headers=t['analyst'],files={'file':('evidence.xlsx',out.getvalue())},data={'mapping':json.dumps({'source_column':'id'})});assert response.status_code==200;assert response.json()['accepted']==1

def test_snapshot_immutability(env):
    c,t=env;ss=c.get('/api/snapshots',headers=t['admin']).json();old=ss[0]['id'];new=c.post('/api/snapshots',headers=t['reviewer']).json();assert old!=new['id']
    with engine.connect() as db:
        s=db.execute(select(snapshots).where(snapshots.c.id==old)).mappings().one();assert digest(json.loads(s['payload']))==s['sha256'];assert len(json.loads(s['payload']))==40

def test_end_to_end_case_report_review(env):
    c,t=env;sid=c.get('/api/snapshots',headers=t['admin']).json()[0]['id'];r=c.post('/api/cases',headers=t['analyst'],json={'title':'DEMO acceptance integration case','quote':sample('TEST-QUOTE'),'snapshot_id':sid});assert r.status_code==200;id=r.json()['id']
    run=c.post(f'/api/cases/{id}/run',headers=t['analyst']);assert run.status_code==200;assert run.json()['result']['status']=='supported'
    assert c.post(f'/api/cases/{id}/review',headers=t['analyst'],json={'action':'accepted','comment':'Should be forbidden'}).status_code==403
    for role,action in [('analyst','ready_for_review'),('reviewer','under_review'),('reviewer','accepted')]:
        response=c.post(f'/api/cases/{id}/review',headers=t[role],json={'action':action,'comment':'Reviewed source evidence and comparator methodology'});assert response.status_code==200,response.text
    assert c.post(f'/api/cases/{id}/run',headers=t['analyst']).status_code==409
    pdf=c.get(f'/api/cases/{id}/pack',headers=t['reviewer']);assert pdf.content.startswith(b'%PDF');reader=PdfReader(io.BytesIO(pdf.content));text=' '.join(p.extract_text() for p in reader.pages);assert 'Management summary' in text;assert sid in text;assert 'DEMO / SYNTHETIC' in text;assert 'Reviewer history' in text
    with engine.connect() as db:
        report=db.execute(select(reports).where(reports.c.id==pdf.headers['x-report-version'])).mappings().one();assert hashlib.sha256(pdf.content).hexdigest()==report['sha256'];assert json.loads(report['snapshot'])['case']['status']=='accepted'
    archived=c.get('/api/reports/'+pdf.headers['x-report-version'],headers=t['reviewer']);assert archived.content==pdf.content
    assert len(c.get(f'/api/cases/{id}/reports',headers=t['reviewer']).json())==1

def test_prediction_lock_and_reveal(env):
    c,t=env;sid=c.get('/api/snapshots',headers=t['admin']).json()[0]['id'];r=c.post('/api/evaluations',headers=t['evaluator'],json={'snapshot_id':sid});assert r.status_code==200,r.text;p=r.json();assert len(p['predictions'])==10;assert all('award' not in x and 'outcome' not in x['prediction']['quote'] for x in p['predictions'])
    for test in p['predictions']:
        quote=test['prediction']['quote'];assert all(x['original']['date']<quote['date'] and 'HOLDOUT' not in x['id'] for x in test['prediction']['included'])
    assert c.post('/api/evaluations/'+p['id']+'/reveal',headers=t['analyst']).status_code==403
    rr=c.post('/api/evaluations/'+p['id']+'/reveal',headers=t['evaluator']);assert rr.status_code==200;assert len(rr.json())==10;assert any(not x['covered'] for x in rr.json())
    finding=c.post('/api/evaluations/'+p['id']+'/finding',headers=t['reviewer'],json={'holdout_id':rr.json()[0]['id'],'comment':'Band coverage reviewed; provisional threshold requires approval'});assert finding.status_code==200
    with engine.connect() as db:
        saved=db.execute(select(evaluations).where(evaluations.c.id==p['id'])).mappings().one();assert digest(json.loads(saved['predictions']))==p['rubric']['prediction_sha256']

def test_rules_governance(env):
    c,t=env;body={'version':'reviewed-test-rule','minimum':6,'lower_quantile':'0.2','upper_quantile':'0.8','target_quantile':'0.5'}
    assert c.post('/api/rules',headers=t['analyst'],json=body).status_code==403
    assert c.post('/api/rules',headers=t['admin'],json=body).status_code==200
    assert c.post('/api/rules/reviewed-test-rule/approve',headers=t['admin']).status_code==403
    assert c.post('/api/rules/reviewed-test-rule/approve',headers=t['reviewer']).status_code==200
    assert c.post('/api/rules',headers=t['admin'],json=body).status_code==409

def test_external_ai_disabled_and_audit(env):
    c,t=env;cfg=c.get('/api/config',headers=t['admin']).json();assert cfg['llm']['external_transmission'] is False;assert all(x['status'].startswith('disabled') for x in cfg['integrations']);a=c.get('/api/audit',headers=t['reviewer']).json();assert a['chain_valid'];assert len(a['events'])>10

def test_unknown_case_and_invalid_transition(env):
    c,t=env;assert c.get('/api/cases/not-found',headers=t['admin']).status_code==404;id=c.get('/api/cases',headers=t['analyst']).json()[0]['id'];assert c.post('/api/cases/'+id+'/review',headers=t['reviewer'],json={'action':'under_review','comment':'Invalid state change'}).status_code==409

def test_corrupt_workbook_refused(env):
    c,t=env;r=c.post('/api/import',headers=t['analyst'],files={'file':('corrupt.xlsx',b'not a workbook')});assert r.status_code==422
