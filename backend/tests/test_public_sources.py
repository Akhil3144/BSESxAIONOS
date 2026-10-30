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
    assert kei['http_status']==200 and kei['verification_result']=='Unverified'
    assert kei['historical_verifications'][0]['http_status']==404
    assert 'scribd.com' in kei['current_url'] and 'rajelectricals.co.in' in kei['original_url']
    assert kei['publication_date'] is None
    nfl=next(s for s in sources if s['source_id']=='nfl')
    assert nfl['http_status']==200 and 'PDF pages 9' in nfl['page_or_row']
    assert nfl['historical_verifications'][0]['http_status']==500
    assert nfl['historical_verifications'][0]['product_specification']['area_mm2']==185
    assert 95 in nfl['product_specification']['area_mm2']
    assert 'Uttarakhand' in nfl['publisher'] and 's3waas.gov.in' in nfl['current_url']
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
    assert d['references'][2]['specification_match']=='Not directly comparable'
    assert 'armoured' in d['references'][2]['comparison_detail']
    assert 'area_mm2' not in d['references'][2]['comparison_detail']
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


def test_comparison_uses_replacement_scope_and_reports_missing_and_mismatched_fields():
    c,r=context();q=copy.deepcopy(r[0]['result']['quote'])
    q['specification']['area_mm2']=25
    ref=comparison(q)['references'][2]
    assert ref['specification_match']=='Not directly comparable'
    assert 'area_mm2' in ref['comparison_detail']
    q['specification']=copy.deepcopy(directory()[2]['product_specification'])
    q['specification']['area_mm2']=95
    ref=comparison(q)['references'][2]
    assert ref['specification_match']=='Technical fields match; commercial comparability unconfirmed'
    assert ref['comparability_status']=='Reference only'
    assert comparison(q)['verified_public_reference_price'] is None


def test_availability_requires_authentication_and_rejects_unknown_sources(env):
    c,h=env
    assert c.get('/api/public-sources/kei/availability').status_code==401
    assert c.get('/api/public-sources/unknown/availability',headers=h['admin']).status_code==404


@pytest.mark.parametrize('code,status',[ (200,'Available'),(404,'Unavailable'),(500,'Unavailable'),(403,'Access restricted'),(429,'Access restricted'),(302,'Access restricted or redirected')])
def test_availability_status_and_no_price_promotion(code,status):
    import httpx
    from backend.app.source_availability import check_availability
    requests=[]
    def handle(req):
        requests.append(req)
        return httpx.Response(code,content=b'%PDF-1.7 test',headers={'Location':'http://127.0.0.1/private'})
    before=directory()
    d=check_availability('nfl',transport=httpx.MockTransport(handle))
    assert d['http_status']==code and d['status']==status and d['checked_at']
    assert len(requests)==1 and requests[0].url.host=='cdnbbsr.s3waas.gov.in'
    assert directory()==before and public_prices()==[]
    if code in (404,500):assert 'benchmark' in d['message'] and str(code) in d['message']


@pytest.mark.parametrize('error_kind',['timeout','network','pdf_html'])
def test_availability_network_failures_and_unexpected_content_are_clear(error_kind):
    import httpx
    from backend.app.source_availability import check_availability
    def handle(req):
        if error_kind=='timeout':raise httpx.ReadTimeout('sensitive internal details')
        if error_kind=='network':raise httpx.ConnectError('sensitive internal details')
        return httpx.Response(200,text='<html>Sign in required</html>')
    d=check_availability('nfl',transport=httpx.MockTransport(handle))
    assert d['status']!='Available' and d['message']
    assert 'sensitive internal' not in d['message']


def test_availability_cache_does_not_rewrite_provenance(monkeypatch):
    from backend.app import source_availability as module
    import time
    payload={'source_id':'gem','status':'Unavailable','http_status':500,'message':'test'}
    monkeypatch.setitem(module._cache,'gem',(time.monotonic(),payload))
    d=module.check_availability('gem')
    assert d['cached'] and d['http_status']==500
    assert directory()[0]['http_status']==200
