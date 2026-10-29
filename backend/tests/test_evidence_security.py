import os,json,io,csv
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select,func
from backend.app.main import app
from backend.app.db import engine,batches,snapshots,rules,evaluations
from backend.app.seed import sample
from backend.app.engine import digest
@pytest.fixture
def client():
    with TestClient(app) as c:
        t={r:{'Authorization':'Bearer '+c.post('/api/login',json={'username':r,'password':os.environ['DEMO_PASSWORD']}).json()['token']} for r in ['admin','analyst','reviewer','evaluator']}
        c.post('/api/demo/seed',headers=t['admin']);yield c,t

def upload(c,headers,row):
    f=io.StringIO();w=csv.DictWriter(f,fieldnames=list(row));w.writeheader();w.writerow({**row,'specification':json.dumps(row['specification'])});return c.post('/api/import',headers=headers,files={'file':('test.csv',f.getvalue())})
@pytest.mark.parametrize('field',['FinalAwardPrice','outcome','award_ratio','unknown_proxy'])
def test_outcomes_never_retained_in_generic_source_storage(client,field):
    c,t=client;row=sample('SECURITY-'+field);row[field]='secret holdout value'
    with engine.connect() as db:before=db.execute(select(func.count()).select_from(batches)).scalar()
    r=upload(c,t['analyst'],row);assert r.status_code==422
    with engine.connect() as db:assert db.execute(select(func.count()).select_from(batches)).scalar()==before

def test_payment_fraction_is_not_silently_truncated(client):
    c,t=client;row=sample('PAYMENT-FRACTION');row['payment_days']='30.5';r=upload(c,t['analyst'],row);assert r.status_code==200;assert r.json()['rejected']==1;assert r.json()['errors'][0]['raw']['payment_days']=='30.5'

def test_dashboard_does_not_expose_holdout_payload(client):
    c,t=client;sid=c.get('/api/snapshots',headers=t['admin']).json()[0]['id'];e=c.post('/api/evaluations',headers=t['evaluator'],json={'snapshot_id':sid}).json();c.post('/api/evaluations/'+e['id']+'/reveal',headers=t['evaluator']);d=c.get('/api/dashboard',headers=t['analyst']).json()
    assert all(set(x)=={'seq','actor','event','created'} for x in d['recent']);assert 'award' not in json.dumps(d['recent'])

def test_frozen_reference_integrity_checked(client):
    c,t=client;r=c.post('/api/snapshots',headers=t['reviewer']).json();sid=r['id'];case=c.post('/api/cases',headers=t['analyst'],json={'title':'Integrity case','quote':sample('INTEGRITY-QUOTE'),'snapshot_id':sid}).json()['id']
    with engine.begin() as db:db.execute(snapshots.update().where(snapshots.c.id==sid).values(payload='[]'))
    assert c.post('/api/cases/'+case+'/run',headers=t['analyst']).status_code==409
    assert c.post('/api/evaluations',headers=t['evaluator'],json={'snapshot_id':sid}).status_code==409

def test_evaluation_locks_active_policy_not_global_default(client):
    c,t=client
    # Use a fresh verified reference snapshot, independent of prior integrity probe.
    sid=c.post('/api/snapshots',headers=t['reviewer']).json()['id'];e=c.post('/api/evaluations',headers=t['evaluator'],json={'snapshot_id':sid});assert e.status_code==200
    expected=e.json()['rubric']['rule'];assert all(p['prediction']['rule']==expected for p in e.json()['predictions'])

def test_concurrent_audit_writes_preserve_one_chain(client):
    from concurrent.futures import ThreadPoolExecutor
    from backend.app.db import log
    c,t=client
    def append(i):
        with engine.begin() as db:log(db,'admin','concurrent_audit_probe',{'index':i})
    with ThreadPoolExecutor(max_workers=4) as executor:list(executor.map(append,range(12)))
    assert c.get('/api/audit',headers=t['reviewer']).json()['chain_valid'] is True

def test_no_procurement_authority_endpoints(client):
    c,t=client
    for path in ['/api/sap/purchase-order','/api/suppliers/DEMO/blacklist','/api/cases/DEMO/award','/api/suppliers/DEMO/send-offer']:
        assert c.post(path,headers=t['admin'],json={}).status_code in [404,405]

def test_dashboard_never_sums_different_currencies(client):
    c,t=client
    for i in range(6):
        row=sample(f'USD-HISTORY-{i}',str(100+i*10),'2024-01-01');row['currency']='USD';r=upload(c,t['analyst'],row);assert r.status_code==200;assert r.json()['accepted']==1
    sid=c.post('/api/snapshots',headers=t['reviewer']).json()['id'];quote=sample('USD-CASE','200');quote['currency']='USD'
    case=c.post('/api/cases',headers=t['analyst'],json={'title':'Synthetic USD currency isolation','quote':quote,'snapshot_id':sid}).json()['id'];run=c.post('/api/cases/'+case+'/run',headers=t['analyst']);assert run.status_code==200
    assert run.json()['result']['opportunity']=='75000.00'
    d=c.get('/api/dashboard',headers=t['analyst']).json();assert d['opportunity'] is None;assert d['opportunity_by_currency']['USD']=='75000.00';assert 'INR' in d['opportunity_by_currency']

def test_active_nondefault_quantile_and_locked_evaluation_survive_rule_change(client):
    c,t=client;sid=c.post('/api/snapshots',headers=t['reviewer']).json()['id']
    rule={'version':'audit-quarter-target','minimum':5,'lower_quantile':'0.1','upper_quantile':'0.9','target_quantile':'0.25','quantity_ratio_min':'0.5','quantity_ratio_max':'2'}
    assert c.post('/api/rules',headers=t['admin'],json=rule).status_code==200
    assert c.post('/api/rules/'+rule['version']+'/approve',headers=t['reviewer']).status_code==200
    locked=c.post('/api/evaluations',headers=t['evaluator'],json={'snapshot_id':sid});assert locked.status_code==200
    data=locked.json();assert data['rubric']['rule']['version']==rule['version'];assert all(p['prediction']['rule']['target_quantile']=='0.25' for p in data['predictions'])
    next_rule={**rule,'version':'audit-median-target','target_quantile':'0.5'}
    assert c.post('/api/rules',headers=t['admin'],json=next_rule).status_code==200
    assert c.post('/api/rules/'+next_rule['version']+'/approve',headers=t['reviewer']).status_code==200
    with engine.connect() as db:
        saved=db.execute(select(evaluations).where(evaluations.c.id==data['id'])).mappings().one()
        assert json.loads(saved['rubric'])['rule']['target_quantile']=='0.25';assert digest(json.loads(saved['predictions']))==data['rubric']['prediction_sha256']
