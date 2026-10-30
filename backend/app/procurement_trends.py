"""Read-only, versioned synthetic trend aggregation. Never feeds the pricing engine."""
from copy import deepcopy
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo
from decimal import Decimal
import random
from .engine import decimal, money, financial_context, digest, validate, reference_issues, FACTORS
from .seed import sample

VERSION='procurement-trends-v1'
LABEL='SYNTHETIC DEMONSTRATION — NOT LIVE MARKET PRICES'
PROFILE=sample()['specification']
MATERIAL='CABLE-XLPE-11KV-95'
MIN_PER_MONTH=2
MAX_FRESHNESS_DAYS=35

def business_today():
    return datetime.now(ZoneInfo('Asia/Kolkata')).date()

def calendar_months(as_of):
    ordinal=as_of.year*12+as_of.month-1
    return [date((ordinal-i)//12,(ordinal-i)%12+1,1) for i in (2,1,0)]

@financial_context
def percent(current,previous):
    return money((decimal(current)-decimal(previous))/decimal(previous)*100) if previous is not None and decimal(previous)>0 else None

def qualify(row,quote,as_of,months):
    reasons=validate(row)
    if not isinstance(row,dict):return reasons
    reasons+=reference_issues(row)
    if row.get('synthetic') is not True:reasons.append('Public/non-synthetic observations are separate; no blending methodology approved')
    if row.get('id')==quote.get('id') or row.get('source_ref')==quote.get('source_ref'):reasons.append('Current quotation is not historical trend evidence')
    if any(word in str(row.get('id','')).upper() for word in ['HOLDOUT']):reasons.append('Holdout observations prohibited')
    try:
        day=date.fromisoformat(row.get('date',''))
        if day>as_of or day.strftime('%Y-%m') not in months:reasons.append('Outside the three-month as-of window')
        if row.get('available_date') and date.fromisoformat(row['available_date'])>as_of:reasons.append('Observation not yet available')
    except (ValueError,TypeError):pass # validate() already records malformed dates
    for key in ['material','specification','currency','tax','location','delivery','freight_treatment','price_basis']:
        if row.get(key)!=quote.get(key):reasons.append('Incompatible '+key)
    try:
        if decimal(row.get('payment_days'))!=decimal(quote.get('payment_days')):reasons.append('Incompatible payment_days')
        ratio=decimal(row['quantity'])*FACTORS[row['uom']]/(decimal(quote['quantity'])*FACTORS[quote['uom']])
        if not Decimal('.5')<=ratio<=2:reasons.append('Incompatible quantity; no volume adjustment approved')
    except (ValueError,KeyError,ZeroDivisionError):reasons.append('Cannot normalize price or quantity')
    if row.get('currency')!='INR':reasons.append('Only INR per metre trend supported')
    return reasons

def generated_observation(month,index,as_of):
    # Stable seed per month, never changes prior values when the viewing window moves.
    rng=random.Random(f'{VERSION}:20261030:{month.isoformat()}:{index}')
    day=date(month.year,month.month,1) # two independent fictional quotes; stable dates, no future observations
    price=540+(month.year-2026)*3+month.month*7+rng.randrange(-4,5)
    # Keep illustrative price within sensible positive limits in any future year.
    price=max(100,price)
    row=sample(f'DEMO-TREND-v1-{month:%Y%m}-{index+1}',str(price),day.isoformat())
    row.update(supplier=f'DEMO trend supplier {index+1} (fictional)',source_type='historical_quotation')
    return row

@financial_context
def analyze_trend(quote,rows,as_of=None,fill_demo=True):
    as_of=as_of or business_today()
    months=calendar_months(as_of);keys=[m.strftime('%Y-%m') for m in months]
    included=[];excluded=[];seen=set();seen_sources=set()
    for row in rows:
        reasons=qualify(row,quote,as_of,keys)
        if isinstance(row,dict):
            if row.get('id') in seen:reasons.append('Duplicate observation ID')
            seen.add(row.get('id'))
            identity=digest({k:row.get(k) for k in ['source_ref','date','unit_price','uom','supplier','material','specification']})
            if identity in seen_sources:reasons.append('Duplicate source observation')
            seen_sources.add(identity)
        if reasons:
            excluded.append({'id':row.get('id') if isinstance(row,dict) else None,'reasons':reasons});continue
        included.append((deepcopy(row),'Retained synthetic procurement observation'))
    generated=[]
    if fill_demo and quote.get('synthetic') is True and quote.get('material')==MATERIAL and quote.get('specification')==PROFILE:
        for month,key in zip(months,keys):
            count=sum(r['date'].startswith(key) for r,_ in included)
            for index in range(MIN_PER_MONTH-count):
                row=generated_observation(month,index,as_of)
                # Never adapt generated terms to a selected incompatible case.
                if row['id'] not in seen and not qualify(row,quote,as_of,keys):
                    included.append((row,'Dedicated deterministic trend fixture; not part of benchmark snapshots'))
                    generated.append(row['id']);seen.add(row['id'])
    evidence=[]
    for row,origin in included:
        normalized=decimal(row['unit_price'])/FACTORS[row['uom']]
        evidence.append({'evidence_id':row['id'],'source_id':row['source_ref'],'source_identity':origin,
                         'observation_date':row['date'],'material':row['material'],'specification':row['specification'],
                         'original_unit_price':row['unit_price'],'original_unit':row['uom'],'currency':row['currency'],
                         'normalized_price_per_metre':str(normalized),'normalization':f"{row['unit_price']} / {FACTORS[row['uom']]} = {normalized} INR/m",
                         'classification':'Synthetic demonstration','original':row,'limitations':'Illustrative synthetic record; no public website or external API supplied this price.'})
    evidence.sort(key=lambda r:(r['observation_date'],r['evidence_id']))
    monthly=[];previous=None
    for month,key in zip(months,keys):
        observations=[e for e in evidence if e['observation_date'].startswith(key)]
        values=[decimal(e['normalized_price_per_metre']) for e in observations]
        mean=sum(values,Decimal(0))/len(values) if values else None
        monthly.append({'month':key,'label':month.strftime('%B %Y'),'price_per_metre':money(mean) if mean is not None else None,
                        'mean_unrounded':str(mean) if mean is not None else None,'change_pct':percent(mean,previous) if mean is not None else None,
                        'observation_count':len(values),'evidence_ids':[e['evidence_id'] for e in observations],
                        'partial_month':key==as_of.strftime('%Y-%m')})
        previous=mean # never bridge a missing month as a month-over-month change
    full=all(m['observation_count']>=MIN_PER_MONTH for m in monthly)
    means=[decimal(m['mean_unrounded']) for m in monthly if m['mean_unrounded'] is not None]
    overall=percent(monthly[-1]['mean_unrounded'],monthly[0]['mean_unrounded']) if len(means)==3 else None
    direction='insufficient evidence'
    if overall is not None:direction='rising' if decimal(overall)>0 else 'falling' if decimal(overall)<0 else 'flat'
    volatility=None
    if len(means)>=2:
        avg=sum(means)/len(means);sd=(sum((p-avg)**2 for p in means)/len(means)).sqrt()
        volatility=money(sd/avg*100)
    latest=evidence[-1] if evidence else None
    freshness=(as_of-date.fromisoformat(latest['observation_date'])).days if latest else None
    present=[m for m in monthly if m['price_per_metre'] is not None]
    response={'version':VERSION,'as_of':as_of.isoformat(),'timezone':'Asia/Kolkata','label':LABEL,
              'material':quote.get('material'),'specification':quote.get('specification'),'currency':'INR','unit':'m',
              'status':'complete' if full and freshness is not None and freshness<=MAX_FRESHNESS_DAYS else 'insufficient_evidence',
              'months':monthly,'overall_change_pct':overall,'direction':direction,'volatility_pct':volatility,
              'volatility_method':'Population coefficient of variation of available monthly means; not forecast risk',
              'latest_observation':latest,'lowest_month':min(present,key=lambda m:decimal(m['mean_unrounded'])) if present else None,
              'highest_month':max(present,key=lambda m:decimal(m['mean_unrounded'])) if present else None,
              'freshness_days':freshness,'observation_count':len(evidence),'evidence':evidence,'excluded':excluded,
              'generated_ids':generated,'generation_seed':'20261030 + version + calendar month + fixture index',
              'method':{'aggregation':'Unweighted arithmetic mean of eligible original prices normalized to INR/m; no FX, tax, freight or volume adjustment',
                        'minimum_observations_per_month':MIN_PER_MONTH,'freshness_limit_days':MAX_FRESHNESS_DAYS,'rounding':'Decimal precision 50; half-even display to 0.01; changes use unrounded means'},
              'limitations':['Synthetic trend fixtures are separate from frozen benchmark inputs and holdout outcomes.',
                             'The current calendar month is partial; small sample means do not establish market prices or causality.',
                             'No future price forecast. Public references are separate supporting context, with zero verified comparable prices.']}
    response['calculation_hash']=digest(response)
    return response
