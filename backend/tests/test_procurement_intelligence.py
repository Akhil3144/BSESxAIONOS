import copy,json,os
from datetime import date,timedelta
from decimal import Decimal,localcontext
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select,func
from backend.app.main import app
from backend.app.db import engine,records,cases,runs,snapshots,holdouts,reviews,evaluations,reports,batches
from backend.app.seed import sample
from backend.app.engine import benchmark,digest
from backend.app.procurement_trends import analyze_trend,calendar_months,percent,LABEL
from backend.app.procurement_timing import simulate,TimingInputs,default_inputs
from backend.app.procurement_chat import QUESTIONS
from backend.app.chat import answer_question

TODAY=date(2026,10,30)

def observations(prices=(600,610,620)):
    return [sample(f'TREND-{month}-{i}',str(price),f'2026-{month:02d}-{day:02d}') for month,price in zip((8,9,10),prices) for i,day in enumerate((1,20))]

def context(prices=(600,610,620)):
    q=sample(price='600')
    b=benchmark(q,[sample(f'B-{i}',str(580+i*10),'2024-01-01') for i in range(6)])
    t=analyze_trend(q,observations(prices),TODAY,fill_demo=False)
    return q,b,t

def confirmed(**kw):
    return TimingInputs(quantity_m='1000',current_quote_per_metre=kw.pop('price','600'),planned_purchase_date=kw.pop('planned',TODAY),
        required_delivery_date=kw.pop('delivery',TODAY+timedelta(days=7)),supplier_lead_time_days=kw.pop('lead',5),
        requirement_confirmed=True,commercial_terms_confirmed=True,current_quote_confirmed=True,benchmark_applicability_reviewed=True,**kw)

def test_month_rollover_and_partial_current_month():
    assert [m.isoformat() for m in calendar_months(date(2027,1,2))]==['2026-11-01','2026-12-01','2027-01-01']
    t=analyze_trend(sample(),[],TODAY)
    assert [m['label'] for m in t['months']]==['August 2026','September 2026','October 2026']
    assert [m['partial_month'] for m in t['months']]==[False,False,True]

def test_monthly_means_and_percentages_use_decimal_unrounded_values():
    q=sample();rows=observations((150,300,450))
    t=analyze_trend(q,rows,TODAY,fill_demo=False)
    assert [m['price_per_metre'] for m in t['months']]==['150.00','300.00','450.00']
    assert [m['change_pct'] for m in t['months']]==[None,'100.00','50.00']
    assert t['overall_change_pct']=='200.00' and t['direction']=='rising'
    assert t['lowest_month']['month']=='2026-08' and t['highest_month']['month']=='2026-10'
    assert percent('640','610')=='4.92' and percent('1','0') is None
    with localcontext() as c:
        c.prec=5
        assert analyze_trend(q,rows,TODAY,fill_demo=False)['calculation_hash']==t['calculation_hash']

def test_normalization_and_multiple_observations_are_averaged_not_latest_only():
    rows=observations();rows[0]['unit_price']='500';rows[1].update(unit_price='600000',uom='km',quantity='1')
    t=analyze_trend(sample(),rows,TODAY,fill_demo=False)
    assert t['months'][0]['price_per_metre']=='550.00'
    km=next(e for e in t['evidence'] if e['original_unit']=='km')
    assert km['original_unit_price']=='600000' and km['normalized_price_per_metre']=='600'
    assert km['original']['uom']=='km' and '/ 1000' in km['normalization']

def test_missing_month_never_bridges_changes_and_abstains():
    rows=[r for r in observations() if not r['date'].startswith('2026-09')]
    t=analyze_trend(sample(),rows,TODAY,fill_demo=False)
    assert t['months'][1]['price_per_metre'] is None
    assert t['months'][2]['change_pct'] is None and t['overall_change_pct'] is None
    assert t['status']=='insufficient_evidence'

@pytest.mark.parametrize('bad',['0','-1','NaN','Infinity','invalid'])
def test_invalid_prices_excluded(bad):
    rows=observations();rows[0]['unit_price']=bad
    t=analyze_trend(sample(),rows,TODAY,fill_demo=False)
    assert len(t['excluded'])==1 and t['observation_count']==5 and t['status']=='insufficient_evidence'

@pytest.mark.parametrize('change',[{'specification':{**sample()['specification'],'area_mm2':120}}, {'currency':'USD'}, {'tax':'included'}, {'synthetic':False}, {'date':'2026-11-01'}, {'available_date':'2026-11-01'}, {'outcome':'999'}])
def test_incompatible_public_future_and_outcome_records_are_not_blended(change):
    rows=observations();rows[0].update(change)
    t=analyze_trend(sample(),rows,TODAY,fill_demo=False)
    assert len(t['excluded'])==1 and t['observation_count']==5
    assert all(e['classification']=='Synthetic demonstration' for e in t['evidence'])

def test_duplicates_and_malformed_records_are_visible():
    rows=observations();t=analyze_trend(sample(),rows+[copy.deepcopy(rows[0]),{},None],TODAY,fill_demo=False)
    assert t['observation_count']==6 and len(t['excluded'])==3

def test_deterministic_minimum_fixtures_do_not_modify_inputs_or_old_month_values():
    q=sample();rows=observations()[:1];before=copy.deepcopy(rows)
    a=analyze_trend(q,rows,TODAY);b=analyze_trend(q,rows,TODAY)
    assert a==b and len(a['generated_ids'])==5 and rows==before
    assert a['label']==LABEL and a['observation_count']==6
    november=analyze_trend(q,[],date(2026,11,20))
    october=analyze_trend(q,[],TODAY)
    assert [e for e in october['evidence'] if e['observation_date'].startswith('2026-10')]==[e for e in november['evidence'] if e['observation_date'].startswith('2026-10')]
    first_day=analyze_trend(q,[],date(2026,10,1))
    assert [e for e in first_day['evidence'] if e['observation_date'].startswith('2026-10')]==[e for e in october['evidence'] if e['observation_date'].startswith('2026-10')]
    assert all(e['observation_date']<=first_day['as_of'] for e in first_day['evidence'])

def test_no_fixtures_for_incompatible_case_and_no_public_record_fallback():
    q=sample();q['specification']['area_mm2']=120
    assert analyze_trend(q,[],TODAY)['observation_count']==0
    q=sample();q['synthetic']=False
    assert analyze_trend(q,[],TODAY)['observation_count']==0

def test_default_recommendation_abstains_on_unknown_deadline_and_stale_quote():
    q,b,t=context();s=simulate(q,b,t,default_inputs(q),TODAY)
    assert s['state']=='INSUFFICIENT EVIDENCE' and s['inventory_covers_full_requirement'] is None
    assert any('delivery date' in v for v in s['missing_inputs'])
    assert any('validity' in v for v in s['missing_inputs'])

def test_buy_now_requires_valid_band_and_deadline_but_does_not_infer_inventory():
    q,b,t=context();s=simulate(q,b,t,confirmed(),TODAY)
    assert s['state']=='BUY NOW' and s['delivery_feasible'] is True
    assert s['inventory_covers_full_requirement'] is None and s['warnings']

def test_premium_with_urgent_delivery_is_negotiated_without_blind_postponement():
    q,b,t=context();s=simulate(q,b,t,confirmed(price='700'),TODAY)
    assert s['state']=='NEGOTIATE / MONITOR'
    assert any('negotiate promptly' in v for v in s['warnings'])

@pytest.mark.parametrize('lead,delay',[(8,0),(5,4)])
def test_lead_time_and_planned_date_must_meet_delivery(lead,delay):
    q,b,t=context();s=simulate(q,b,t,confirmed(lead=lead,planned=TODAY+timedelta(days=delay)),TODAY)
    assert s['state']=='INSUFFICIENT EVIDENCE' and s['delivery_feasible'] is False

def test_deferral_needs_decline_coverage_and_safe_later_order():
    q,b,t=context((650,640,630))
    inputs=confirmed(planned=TODAY+timedelta(days=7),delivery=TODAY+timedelta(days=40),inventory_m='1000')
    assert simulate(q,b,t,inputs,TODAY)['state']=='CONSIDER DEFERRING'
    for inventory in [None,Decimal('999')]:
        assert simulate(q,b,t,inputs.model_copy(update={'inventory_m':inventory}),TODAY)['state']=='NEGOTIATE / MONITOR'
    rising=context()[2]
    assert simulate(q,b,rising,inputs,TODAY)['state']=='NEGOTIATE / MONITOR'

@pytest.mark.parametrize('flag',['requirement_confirmed','commercial_terms_confirmed','current_quote_confirmed','benchmark_applicability_reviewed'])
def test_missing_confirmations_prevent_buy_now(flag):
    q,b,t=context();assert simulate(q,b,t,confirmed().model_copy(update={flag:False}),TODAY)['state']=='INSUFFICIENT EVIDENCE'

def test_stale_or_sparse_trend_and_weak_benchmark_abstain():
    q,b,t=context();t['status']='insufficient_evidence'
    assert simulate(q,b,t,confirmed(),TODAY)['state']=='INSUFFICIENT EVIDENCE'
    assert simulate(q,None,context()[2],confirmed(),TODAY)['state']=='INSUFFICIENT EVIDENCE'

def test_scenario_decimal_costs_no_forecasts_and_read_only():
    q,b,t=context();before=copy.deepcopy((q,b,t))
    inputs=confirmed().model_copy(update={'quantity_m':Decimal('5000'),'current_quote_per_metre':Decimal('600.01'),'assumed_future_price_per_metre':Decimal('610')})
    s=simulate(q,b,t,inputs,TODAY)
    assert s['costs']['current_purchase_cost']=='3000050.00'
    assert s['future_price_scenario']['assumed_purchase_cost']=='3050000.00'
    assert s['state']=='INSUFFICIENT EVIDENCE' and not s['volume_comparable']
    assert (q,b,t)==before and s['read_only']
    assert simulate(q,b,t,confirmed(),TODAY)['future_price_scenario'] is None

@pytest.mark.parametrize('key,value',[('quantity_m','0'),('quantity_m','NaN'),('current_quote_per_metre','-1'),('inventory_m','-1'),('supplier_lead_time_days',1.5),('supplier_lead_time_days',True),('assumed_future_price_per_metre','Infinity')])
def test_invalid_simulator_input_rejected(key,value):
    payload=default_inputs(sample()).model_dump(mode='json');payload[key]=value
    with pytest.raises(ValueError):TimingInputs.model_validate(payload)

@pytest.mark.parametrize('question',QUESTIONS)
def test_chat_matches_deterministic_trend_and_never_routes_these_questions_to_llm(question):
    q,b,t=context();r=simulate(q,b,t,default_inputs(q),TODAY)
    class Router:
        def route(self,*a):raise AssertionError('Procurement numbers must be deterministic')
    a=answer_question({'id':'C','snapshot_id':'S'},[{'id':'R','result':b}],question,router=Router(),intelligence={'trend':t,'recommendation':r})
    assert a['intent']=='procurement_intelligence' and LABEL in a['answer']
    assert a['data']['trend_hash']==t['calculation_hash']
    assert all(c['evidence_id'] in {e['evidence_id'] for e in t['evidence']} for c in a['citations'])
    if '5,000' in question:assert a['data']['timing']['costs']['current_purchase_cost']=='3000000.00'
    if '5%' in question:assert a['data']['timing']['costs']['current_purchase_cost']=='630000.00'
    if 'recommending Buy' in question:assert 'not currently recommending Buy Now' in a['answer']
    if 'next month' in question:assert 'Future prices are uncertain' in a['answer']

@pytest.fixture(scope='module')
def env():
    with TestClient(app) as c:
        h={r:{'Authorization':'Bearer '+c.post('/api/login',json={'username':r,'password':os.environ['DEMO_PASSWORD']}).json()['token']} for r in ['admin','analyst','reviewer','evaluator']}
        c.post('/api/demo/seed',headers=h['admin']);yield c,h

def db_state():
    with engine.connect() as c:
        return {t.name:digest([dict(row) for row in c.execute(select(t)).mappings()]) for t in [records,cases,runs,snapshots,holdouts,reviews,evaluations,reports,batches]}

def test_api_auth_tenant_scope_and_read_only_scenarios(env):
    c,h=env;assert c.get('/api/procurement-intelligence').status_code==401
    assert c.post('/api/procurement-intelligence/simulate',json={}).status_code==401
    id=c.get('/api/demo/tour',headers=h['admin']).json()['case_id'];before=db_state()
    for role in h:
        d=c.get('/api/procurement-intelligence',params={'case_id':id},headers=h[role]);assert d.status_code==200
        data=d.json();assert data['public_evidence']['included_in_trend'] is False
        assert data['trend']['label']==LABEL and data['recommendation']['state']=='INSUFFICIENT EVIDENCE'
        p=c.post('/api/procurement-intelligence/simulate',params={'case_id':id},json=data['default_inputs'],headers=h[role]);assert p.status_code==200 and p.json()['read_only']
    assert db_state()==before
    assert c.get('/api/procurement-intelligence?case_id=unknown',headers=h['admin']).status_code==404
    with engine.begin() as db:db.execute(cases.update().where(cases.c.id==id).values(tenant='other'))
    try:assert c.get('/api/procurement-intelligence?case_id='+id,headers=h['admin']).status_code==404
    finally:
        with engine.begin() as db:db.execute(cases.update().where(cases.c.id==id).values(tenant='demo'))

def test_empty_database_context_recreates_only_dedicated_fixtures_without_writes(env):
    c,h=env;before=db_state();d=c.get('/api/procurement-intelligence',headers=h['analyst']).json()
    assert d['case_id'] is None and d['benchmark'] is None
    assert d['trend']['observation_count']>=6 and d['recommendation']['state']=='INSUFFICIENT EVIDENCE'
    assert db_state()==before

def test_chat_uses_scenario_inputs_and_protects_run_scope(env):
    c,h=env;id=c.get('/api/demo/tour',headers=h['admin']).json()['case_id']
    d=c.get('/api/procurement-intelligence?case_id='+id,headers=h['admin']).json()
    inputs=d['default_inputs'];inputs['quantity_m']='5000'
    a=c.post('/api/cases/'+id+'/chat',headers=h['analyst'],json={'message':QUESTIONS[4],'timing_inputs':inputs}).json()
    assert a['data']['timing']['inputs']['quantity_m']=='5000'
    assert a['intent']=='procurement_intelligence' and a['data']['timing']['state']=='INSUFFICIENT EVIDENCE'
    inputs['quantity_m']='0'
    assert c.post('/api/cases/'+id+'/chat',headers=h['analyst'],json={'message':QUESTIONS[4],'timing_inputs':inputs}).status_code==422


@pytest.mark.parametrize('field,value',[('planned_purchase_date',date(2026,1,1)),('required_delivery_date',date(1,1,1)),('required_delivery_date',date(9999,1,1))])
def test_scenario_dates_outside_supported_range_fail_cleanly(field,value):
    q,b,t=context()
    with pytest.raises(ValueError):simulate(q,b,t,confirmed().model_copy(update={field:value}),TODAY)


@pytest.mark.parametrize('change',[{'currency':'USD'},{'quantity':'1000000000','uom':'km'}])
def test_unsupported_case_currency_and_normalized_volume_fail_without_relabeling_prices(env,change):
    c,h=env;id=c.get('/api/demo/tour',headers=h['admin']).json()['case_id']
    with engine.begin() as db:
        original=db.execute(select(cases.c.quote).where(cases.c.id==id)).scalar()
        quote=json.loads(original);quote.update(change)
        db.execute(cases.update().where(cases.c.id==id).values(quote=json.dumps(quote)))
    try:assert c.get('/api/procurement-intelligence?case_id='+id,headers=h['admin']).status_code==422
    finally:
        with engine.begin() as db:db.execute(cases.update().where(cases.c.id==id).values(quote=original))
