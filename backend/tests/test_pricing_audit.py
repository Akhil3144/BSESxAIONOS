import copy
from decimal import localcontext
import pytest
from backend.app.engine import benchmark,validate,DEFAULT_RULE
from backend.app.seed import sample

def rows(): return [sample(f'H-{i}',str(100+i*10),'2024-01-01') for i in range(8)]
@pytest.mark.parametrize('change',[{'specification':{'voltage_kv':11}},{'payment_days':'30.5'},{'specification':{'voltage_kv':True,'conductor':'Al','area_mm2':95,'cores':3,'insulation':'XLPE'}}])
def test_incomplete_or_invalid_business_input_refused(change):
    q=sample();q.update(change);assert validate(q)
def test_configured_quantity_neighborhood():
    r=rows();r[0]['quantity']='700';b=benchmark(sample(),r,{**DEFAULT_RULE,'quantity_ratio_min':'0.9','quantity_ratio_max':'1.1'});assert r[0]['id'] not in [x['id'] for x in b['included']]
def test_duplicate_observation_does_not_inflate_evidence():
    r=rows();r.append(copy.deepcopy(r[0]));b=benchmark(sample(),r);assert len(b['included'])==8;assert any('Duplicate' in str(x['reasons']) for x in b['excluded'])
def test_active_target_description_is_accurate():
    b=benchmark(sample(),rows(),{**DEFAULT_RULE,'target_quantile':'0.25'});assert 'median' not in b['explanation'];assert b['target']=='117.50';assert b['calculation']['target_unrounded']=='117.50'
def test_decimal_context_cannot_change_result():
    with localcontext() as c:
        c.prec=6;low=benchmark(sample(price='123456789.123'),rows())
    with localcontext() as c:
        c.prec=50;high=benchmark(sample(price='123456789.123'),rows())
    assert low==high
@pytest.mark.parametrize('change',[{'available_date':'2026-01-01'},{'freight_treatment':'excluded'},{'procurement_event_id':'SAME-EVENT'},{'source_type':'historical_award'}])
def test_timing_commercial_and_event_leakage(change):
    q=sample();q['procurement_event_id']='SAME-EVENT';r=rows();r[0].update(change);b=benchmark(q,r);assert r[0]['id'] not in [x['id'] for x in b['included']]
def test_old_rule_defaults_are_materialized_not_mutated():
    rule={k:DEFAULT_RULE[k] for k in ['version','minimum','lower_quantile','upper_quantile','target_quantile','outlier_policy','status']};original=copy.deepcopy(rule);b=benchmark(sample(),rows(),rule);assert rule==original;assert 'quantity_ratio_min' in b['rule'];assert b['engine_version']
def test_outliers_visible_but_not_silently_removed():
    r=rows();r[-1]['unit_price']='9999';b=benchmark(sample(),r);assert len(b['included'])==8;assert b['outlier_diagnostics']['flagged_ids']==['H-7'];assert b['outlier_diagnostics']['treatment']=='retain'
@pytest.mark.parametrize('rule',[{'quantity_ratio_min':'3','quantity_ratio_max':'1'},{'outlier_policy':'drop'},{'max_age_days':-1}])
def test_invalid_policy_refused(rule):
    with pytest.raises(ValueError):benchmark(sample(),rows(),{**DEFAULT_RULE,**rule})
def test_optional_historical_age_cutoff():
    b=benchmark(sample(),rows(),{**DEFAULT_RULE,'max_age_days':30});assert b['status']=='insufficient_evidence'

def test_duplicate_source_with_different_id_requires_reconciliation():
    r=rows();duplicate=copy.deepcopy(r[0]);duplicate['id']='DUPLICATE-LINE';r.append(duplicate);b=benchmark(sample(),r);assert len(b['included'])==8;assert 'Duplicate source observation' in str(b['excluded'])

def test_unconfigured_category_cannot_use_generic_description_equivalence():
    q=sample();q['material']='UNAPPROVED-CATEGORY'
    with pytest.raises(ValueError,match='Unconfigured material'):benchmark(q,rows())

def test_configured_supplier_diversity_can_require_abstention():
    b=benchmark(sample(),rows(),{**DEFAULT_RULE,'minimum_suppliers':2});assert b['status']=='insufficient_evidence';assert 'target' not in b;assert b['evidence_assessment']['supplier_count']==1
