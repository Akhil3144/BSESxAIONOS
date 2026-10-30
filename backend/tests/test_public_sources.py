import os,copy
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from backend.app.main import app
from backend.app.db import engine,cases,runs
from backend.app.public_sources import directory,public_prices,comparison
from backend.app.chat import answer_question
from backend.tests.test_chat import context

@pytest.fixture(scope='module')
def env():
    with TestClient(app) as c:
        headers={r:{'Authorization':'Bearer '+c.post('/api/login',json={'username':r,'password':os.environ['DEMO_PASSWORD']}).json()['token']} for r in ['admin','analyst','reviewer','evaluator']}
        c.post('/api/demo/seed',headers=headers['admin'])
        yield c,headers

def test_authenticated_read_access_and_no_mutations(env):
    c,h=env
    assert c.get('/api/public-sources').status_code==401
    for role in h:
        d=c.get('/api/public-sources',headers=h[role]).json()
        assert len(d['sources'])==3
        assert d['summary']['Verified public price observations']==0
        assert d['prices']==[]
        assert 'None configured' in d['summary']['External live API connections']
    assert c.post('/api/public-sources',headers=h['admin'],json={'price':500}).status_code==405

def test_unavailable_sources_do_not_produce_prices():
    sources=directory();assert public_prices()==[]
    assert all(s['observed_value'] is None and s['normalized_price_per_metre'] is None for s in sources)
    kei=next(s for s in sources if s['source_id']=='kei')
    assert kei['http_status']==404 and kei['verification_result']=='Unverified'
    assert kei['publication_date'] is None
    nfl=next(s for s in sources if s['source_id']=='nfl')
    assert nfl['http_status']==500 and 'indexed' in nfl['page_or_row']
    assert all(s['verification_result']!='Verified comparable' for s in sources)
    altered=directory();altered[0]['observed_value']=100
    assert directory()[0]['observed_value'] is None

def test_case_comparison_preserves_benchmark_and_scope(env):
    c,h=env;id=c.get('/api/demo/tour',headers=h['admin']).json()['case_id']
    assert c.get(f'/api/cases/{id}/public-sources').status_code==401
    assert c.get('/api/cases/missing/public-sources',headers=h['analyst']).status_code==404
    with engine.begin() as db:
        db.execute(cases.update().where(cases.c.id==id).values(tenant='other'))
    try:assert c.get(f'/api/cases/{id}/public-sources',headers=h['admin']).status_code==404
    finally:
        with engine.begin() as db:db.execute(cases.update().where(cases.c.id==id).values(tenant='demo'))
    before=c.get('/api/cases/'+id,headers=h['admin']).json()
    d=c.get(f'/api/cases/{id}/public-sources',headers=h['evaluator']).json()
    assert d['synthetic_historical_benchmark']==before['runs'][0]['result']['median']
    assert d['verified_public_reference_price'] is None
    assert 'area_mm2' in d['references'][2]['specification_match']
    assert before==c.get('/api/cases/'+id,headers=h['admin']).json()

@pytest.mark.parametrize('question',[
 'Where does the pricing data come from?','Which sources are real and which are synthetic?',
 'Show official procurement references.','Is there a public market price for this cable?',
 'Which website supports this technical specification?','Why does the public reference differ from our benchmark?',
 'Show the original source document.'])
def test_source_questions_do_not_fabricate_prices_or_call_llm(question):
    class Router:
        def route(self,*a):raise AssertionError('Public provenance must remain deterministic')
    c,r=context();before=copy.deepcopy(r);a=answer_question(c,r,question,router=Router())
    assert a['intent']=='public_sources'
    assert 'No verified public price' in a['answer'] and 'synthetic' in a['answer']
    assert '404' in a['answer'] and '500' in a['answer']
    assert len(a['data']['public_sources'])==3 and not a['citations']
    assert a['actions'][0]['type']=='view_sources' and r==before
