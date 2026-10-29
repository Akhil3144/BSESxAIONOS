"""Versioned, deterministic pricing. No inferred commercial or market adjustments."""
from decimal import Decimal, InvalidOperation, localcontext, ROUND_HALF_EVEN
from datetime import date
from statistics import median
from functools import wraps
import copy, hashlib, json, re

ENGINE_VERSION = 'deterministic-pricing-v2'
VERSION = 'demo-quantiles-v2'
DEFAULT_RULE = {'version': VERSION, 'minimum': 5, 'lower_quantile': '0.25', 'upper_quantile': '0.75', 'target_quantile': '0.50', 'outlier_policy': 'retain', 'quantity_ratio_min': '0.5', 'quantity_ratio_max': '2', 'max_age_days': None, 'iqr_multiplier': '1.5', 'minimum_suppliers': 1, 'status': 'PROVISIONAL - requires BSES SME approval'}
FACTORS = {'m': Decimal('1'), 'km': Decimal('1000')}
REQUIRED = ['id','material','specification','supplier','date','quantity','uom','currency','unit_price','tax','payment_days','location','delivery','source_ref']
SPEC_FIELDS = {'CABLE-XLPE-11KV-95': ['voltage_kv','conductor','area_mm2','cores','insulation']}
REFERENCE_FIELDS=set(REQUIRED+['synthetic','source_type','available_date','freight_treatment','price_basis','procurement_event_id'])

def canonical(value): return json.dumps(value, sort_keys=True, separators=(',', ':'), default=str,allow_nan=False)
def digest(value): return hashlib.sha256(canonical(value).encode()).hexdigest()
def decimal(v):
    if isinstance(v,bool): raise ValueError('Boolean is not a number')
    try: d=Decimal(str(v))
    except (InvalidOperation,ValueError,TypeError): raise ValueError('Invalid numeric value')
    if not d.is_finite(): raise ValueError('Non-finite number')
    return d

def financial_context(fn):
    @wraps(fn)
    def call(*args,**kwargs):
        with localcontext() as ctx:
            ctx.prec=50;ctx.rounding=ROUND_HALF_EVEN
            return fn(*args,**kwargs)
    return call
@financial_context
def money(v): return str(decimal(v).quantize(Decimal('.01')))

def is_outcome_key(key):
    key=re.sub('[^a-z]','',str(key).lower())
    return any(word in key for word in ['award','outcome','negotiated','finalprice','holdout'])

def reference_issues(row):
    issues=[]
    if any(is_outcome_key(k) for k in row):issues.append('Holdout/outcome fields prohibited in reference import')
    unknown=set(row)-REFERENCE_FIELDS
    if unknown:issues.append('Unmapped reference fields prohibited: '+', '.join(sorted(unknown)))
    if str(row.get('source_type','')).lower() not in ['', 'purchase_order','tender','historical_quotation','reverse_auction','contract_reference']:
        issues.append('Unapproved or outcome-bearing source type')
    return issues

def validate(row):
    if not isinstance(row,dict):return ['Record must be an object']
    errors=[]
    for k in REQUIRED:
        if row.get(k) is None or str(row.get(k)).strip()=='':errors.append(f'Missing {k}')
    for k in ['id','material','supplier','tax','location','delivery','source_ref']:
        if not isinstance(row.get(k),str) or not row[k].strip():errors.append(f'Invalid {k}')
    try:
        if not 0<decimal(row.get('unit_price',0))<=Decimal('1e12') or not 0<decimal(row.get('quantity',0))<=Decimal('1e9'):errors.append('Price must be positive <= 1e12 and quantity positive <= 1e9')
    except ValueError:errors.append('Invalid numeric value')
    for key in ['date','available_date']:
        if key=='available_date' and row.get(key) in [None,'']:continue
        try:date.fromisoformat(str(row.get(key,'')))
        except ValueError:errors.append('Invalid ISO '+key)
    if row.get('uom') not in FACTORS:errors.append('Unsupported UoM')
    if row.get('currency') not in ['INR','USD','EUR']:errors.append('Unsupported currency')
    try:
        days=decimal(row.get('payment_days',-1))
        if days<0 or days!=days.to_integral_value() or days>3650:errors.append('Payment days must be a whole number from 0 to 3650')
    except ValueError:errors.append('Invalid payment_days')
    if row.get('material') not in SPEC_FIELDS:errors.append('Unconfigured material/category specification profile')
    spec=row.get('specification')
    if not isinstance(spec,dict) or not spec:errors.append('Structured technical specification required')
    else:
        missing=[k for k in SPEC_FIELDS.get(row.get('material'),[]) if k not in spec]
        if missing:errors.append('Incomplete specification: '+', '.join(missing))
        for key,value in spec.items():
            if not isinstance(key,str) or isinstance(value,bool) or value is None or isinstance(value,(dict,list)) or isinstance(value,str) and not value.strip():errors.append('Invalid specification attribute '+str(key))
            elif isinstance(value,(int,float)):
                try:
                    if decimal(value)<=0:errors.append('Invalid specification value '+key)
                except ValueError:errors.append('Invalid specification value '+key)
    return errors

@financial_context
def resolve_rule(rule=None):
    r={**copy.deepcopy(DEFAULT_RULE),**copy.deepcopy(rule or {})}
    if isinstance(r['minimum'],bool) or not isinstance(r['minimum'],int) or r['minimum']<3:raise ValueError('Invalid minimum')
    if not 0<=decimal(r['lower_quantile'])<=decimal(r['target_quantile'])<=decimal(r['upper_quantile'])<=1:raise ValueError('Invalid quantiles')
    if not 0<decimal(r['quantity_ratio_min'])<=decimal(r['quantity_ratio_max']):raise ValueError('Invalid quantity eligibility bounds')
    if r['outlier_policy']!='retain':raise ValueError('Only explicit retain-and-flag outlier treatment is supported')
    if decimal(r['iqr_multiplier'])<=0:raise ValueError('Invalid IQR multiplier')
    if r['max_age_days'] is not None and (type(r['max_age_days']) is not int or r['max_age_days']<0):raise ValueError('Invalid age cutoff')
    if type(r['minimum_suppliers']) is not int or r['minimum_suppliers']<1:raise ValueError('Invalid supplier evidence threshold')
    return r

def quantile(values,q):
    p=(len(values)-1)*decimal(q);lo=int(p);hi=min(lo+1,len(values)-1)
    return values[lo]+(values[hi]-values[lo])*(p-lo)

@financial_context
def benchmark(quote,rows,rule=None):
    rule=resolve_rule(rule);errors=validate(quote)
    if errors:raise ValueError('; '.join(errors))
    included=[];excluded=[];seen=set();seen_sources=set();quotedate=date.fromisoformat(quote['date'])
    for row in rows:
        reasons=validate(row)
        if not isinstance(row,dict):excluded.append({'id':'missing source id','reasons':reasons});continue
        if row.get('holdout') or row.get('id')==quote['id'] or row.get('source_ref')==quote['source_ref']:reasons.append('Holdout/self record prohibited')
        if row.get('procurement_event_id') and row.get('procurement_event_id')==quote.get('procurement_event_id'):reasons.append('Same procurement event as withheld/current case')
        if row.get('source_type') and str(row['source_type']).lower() not in ['', 'purchase_order','tender','historical_quotation','reverse_auction','contract_reference']:reasons.append('Outcome-bearing or unapproved source type')
        if any(is_outcome_key(k) for k in row):reasons.append('Outcome or derived holdout fields prohibited')
        if row.get('id') in seen:reasons.append('Duplicate observation ID')
        seen.add(row.get('id'))
        if not reasons:
            source_key=digest({k:row.get(k) for k in ['source_ref','material','specification','date','quantity','uom','unit_price','supplier']})
            if source_key in seen_sources:reasons.append('Duplicate source observation under another ID; reviewer reconciliation required')
            seen_sources.add(source_key)
        if str(row.get('date','9999'))>=quote['date']:reasons.append('Observation must precede quotation')
        if row.get('available_date') and str(row['available_date'])>=quote['date']:reasons.append('Evidence was unavailable at quotation time')
        for key in ['material','specification','currency','tax','location','delivery','freight_treatment','price_basis']:
            if row.get(key)!=quote.get(key):reasons.append(f'Incompatible {key}; no approved adjustment')
        if not reasons:
            if decimal(row['payment_days'])!=decimal(quote['payment_days']):reasons.append('Incompatible payment_days; no approved adjustment')
            age=(quotedate-date.fromisoformat(row['date'])).days
            if rule['max_age_days'] is not None and age>rule['max_age_days']:reasons.append('Observation exceeds configured historical age cutoff')
            ratio=decimal(row['quantity'])*FACTORS[row['uom']]/(decimal(quote['quantity'])*FACTORS[quote['uom']])
            if not decimal(rule['quantity_ratio_min'])<=ratio<=decimal(rule['quantity_ratio_max']):reasons.append('Quantity outside provisional configured eligibility band')
        if reasons:excluded.append({'id':row.get('id','missing source id'),'reasons':reasons});continue
        p=decimal(row['unit_price'])/FACTORS[row['uom']]*FACTORS[quote['uom']]
        included.append({'id':row['id'],'supplier':row['supplier'],'source_ref':row['source_ref'],'original':copy.deepcopy(row),'normalized_price':str(p),'transformation':f"{row['unit_price']} / {FACTORS[row['uom']]} * {FACTORS[quote['uom']]} = {p}",'rule_version':rule['version']})
    supplier_count=len({x['supplier'] for x in included})
    result={'engine_version':ENGINE_VERSION,'rule':rule,'included':included,'excluded':excluded,'quote':copy.deepcopy(quote),'status':'insufficient_evidence','limitations':['Provisional method; BSES SME approval pending.','No market-price, inflation, FX, freight or commercial adjustment is inferred.','Quantile band is descriptive; it is not a calibrated confidence interval.','Retains all eligible observations; no outliers silently removed.'],'evidence_quality':f'{len(included)} eligible of {len(rows)} source observations; {supplier_count} distinct suppliers','evidence_assessment':{'eligible_count':len(included),'supplier_count':supplier_count,'required_count':rule['minimum'],'required_suppliers':rule['minimum_suppliers'],'confidence_calibrated':False},'narrative_status':'deterministic explanation; live LLM unavailable'}
    values=sorted(decimal(x['normalized_price']) for x in included)
    flagged=[]
    if len(values)>=4:
        q1=quantile(values,'0.25');q3=quantile(values,'0.75');spread=(q3-q1)*decimal(rule['iqr_multiplier'])
        flagged=[x['id'] for x in included if decimal(x['normalized_price'])<q1-spread or decimal(x['normalized_price'])>q3+spread]
    result['outlier_diagnostics']={'method':'provisional IQR diagnostic','multiplier':rule['iqr_multiplier'],'flagged_ids':flagged,'treatment':'retain'}
    if flagged:result['limitations'].append('Potential outliers retained and flagged for human review.')
    if supplier_count==1:result['limitations'].append('Evidence comes from a single supplier; supplier diversity is limited.')
    if len(included)<rule['minimum'] or supplier_count<rule['minimum_suppliers']:
        result['explanation']='Insufficient comparable evidence. No target or opportunity is recommended.'
    else:
        lower=quantile(values,rule['lower_quantile']);upper=quantile(values,rule['upper_quantile']);target=quantile(values,rule['target_quantile']);quoted=decimal(quote['unit_price'])
        result.update(status='supported',best=money(values[0]),median=money(median(values)),lower=money(lower),upper=money(upper),target=money(target),opportunity=money(max(Decimal(0),quoted-target)*decimal(quote['quantity'])),quote_difference_pct=money((quoted-target)/target*100))
        result['calculation']={'lower_unrounded':str(lower),'upper_unrounded':str(upper),'target_unrounded':str(target),'opportunity_formula':'max(0, quote - unrounded target) * quoted quantity','rounding':'half-even to 0.01','precision':50}
        position='above' if quoted>upper else 'below' if quoted<lower else 'within';method='median' if decimal(rule['target_quantile'])==Decimal('.5') else f"quantile {rule['target_quantile']}"
        result['explanation']=f'The quotation is {position} the provisional comparable band. The target is the configured {method} of {len(values)} eligible observations. Review every comparator and its source before accepting this advisory recommendation.'
    result['questions']=['Request a documented price breakdown and explanation of differences from the comparable transactions.','Confirm specification, quantity, tax, payment and delivery equivalence.','What evidence supports any requested price adjustment?']
    result['challenge_points']=['Use the included, normalized historical observations as negotiation evidence.'] if result['status']=='supported' else ['Obtain additional eligible evidence before proposing a target.']
    result['concessions']=['Discuss volume commitment or payment alternatives only after documenting and approving their price effects.']
    result['walk_away']='No approved walk-away threshold exists; procurement reviewer decision required.'
    result['fingerprint']=digest(result)
    return result
