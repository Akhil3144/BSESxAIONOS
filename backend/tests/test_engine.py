import copy
from decimal import Decimal
import pytest
from backend.app.engine import *
from backend.app.seed import sample

def history(n=8): return [sample(f'PO-{i}',str(100+i*10),'2024-01-01') for i in range(n)]
def test_best_median_band():
    b=benchmark(sample(price='200'),history()); assert b['best']=='100.00'; assert b['median']=='135.00'; assert b['lower']=='117.50'; assert b['upper']=='152.50'; assert b['opportunity']=='65000.00'
def test_conversion():
    r=history();r[0].update(uom='km',unit_price='100000',quantity='1');b=benchmark(sample(),r);assert b['included'][0]['normalized_price']=='100';assert '100000 / 1000' in b['included'][0]['transformation']
@pytest.mark.parametrize('field,value',[('specification',{'area_mm2':120}),('currency','USD'),('tax','inclusive'),('payment_days',60),('location','Mumbai'),('delivery','ex works'),('material','different')])
def test_incompatible(field,value):
    r=history();r[0][field]=value;b=benchmark(sample(),r);assert len(b['included'])==7;assert field in b['excluded'][0]['reasons'][0]
def test_original_preserved():
    r=history();before=copy.deepcopy(r);b=benchmark(sample(),r);assert r==before;assert b['included'][0]['original']==before[0]
def test_reproducible(): assert benchmark(sample(),history())==benchmark(sample(),history())
@pytest.mark.parametrize('n',[0,1,4])
def test_insufficient(n):
    b=benchmark(sample(),history(n));assert b['status']=='insufficient_evidence';assert 'target' not in b;assert 'opportunity' not in b
@pytest.mark.parametrize('price',['0','-5','NaN','Infinity','x'])
def test_invalid_quote(price):
    with pytest.raises(ValueError): benchmark(sample(price=price),history())
def test_future_and_self_holdout_excluded():
    r=history();r[0]['date']='2026-01-01';r[1]['holdout']=True;r[2]['id']=sample()['id'];b=benchmark(sample(),r);assert len(b['excluded'])==3
@pytest.mark.parametrize('quantity',['1','1000000'])
def test_unsupported_volume(quantity):
    r=history();r[0]['quantity']=quantity;assert len(benchmark(sample(),r)['excluded'])==1
def test_all_price_claims_lineage():
    b=benchmark(sample(),history());assert all(x['source_ref'] and x['original'] and x['rule_version'] for x in b['included']);assert 'confidence' not in b

def test_configured_quantiles():
    r={**DEFAULT_RULE,'lower_quantile':'0','upper_quantile':'1','target_quantile':'0.25'};b=benchmark(sample(),history(),r);assert b['lower']=='100.00';assert b['upper']=='170.00';assert b['target']=='117.50'
def test_invalid_method():
    with pytest.raises(ValueError): benchmark(sample(),history(),{**DEFAULT_RULE,'lower_quantile':'0.9','upper_quantile':'0.1'})

def test_malformed_history_has_exclusion_reason():
    b=benchmark(sample(),[{}]);assert b['status']=='insufficient_evidence';assert b['excluded'][0]['reasons']
