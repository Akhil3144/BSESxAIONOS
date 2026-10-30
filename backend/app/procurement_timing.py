"""Provisional, explainable timing rules. Scenario assumptions never mutate a case."""
from datetime import date,timedelta
from decimal import Decimal
from pydantic import BaseModel,Field,ConfigDict
from .engine import decimal,money,financial_context,digest,FACTORS
from .procurement_trends import business_today,LABEL

TIMING_VERSION='procurement-timing-v1'
class TimingInputs(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)
    quantity_m:Decimal=Field(gt=0,le=Decimal('1e9'))
    current_quote_per_metre:Decimal=Field(gt=0,le=Decimal('1e12'))
    planned_purchase_date:date|None=None
    required_delivery_date:date|None=None
    supplier_lead_time_days:int|None=Field(default=None,ge=0,le=3650,strict=True)
    inventory_m:Decimal|None=Field(default=None,ge=0,le=Decimal('1e9'))
    requirement_confirmed:bool=False
    commercial_terms_confirmed:bool=False
    current_quote_confirmed:bool=False
    benchmark_applicability_reviewed:bool=False
    assumed_future_price_per_metre:Decimal|None=Field(default=None,gt=0,le=Decimal('1e12'))

def default_inputs(quote):
    return TimingInputs(quantity_m=decimal(quote['quantity'])*FACTORS[quote['uom']],
                        current_quote_per_metre=decimal(quote['unit_price'])/FACTORS[quote['uom']])

@financial_context
def simulate(quote,benchmark,trend,inputs,as_of=None):
    today=as_of or business_today();planned=inputs.planned_purchase_date or today
    if planned<today:raise ValueError('Planned purchase date cannot be before the analysis date')
    if planned>today+timedelta(days=3650) or (inputs.required_delivery_date and inputs.required_delivery_date>today+timedelta(days=3650)):
        raise ValueError('Scenario dates must be within ten years of the analysis date')
    if inputs.required_delivery_date and inputs.required_delivery_date<today:
        raise ValueError('Required delivery date cannot be before the analysis date')
    quantity=inputs.quantity_m;price=inputs.current_quote_per_metre
    reasons=[];missing=[];warnings=[];state='INSUFFICIENT EVIDENCE'
    # Scope is intentionally the same cable family, unit and terms as the saved case.
    from .procurement_trends import PROFILE,MATERIAL
    if quote.get('material')!=MATERIAL or quote.get('specification')!=PROFILE or quote.get('currency')!='INR':
        missing.append('Selected material is not the supported INR 11 kV aluminium, three-core 95 sq. mm XLPE specification')
    if trend['status']!='complete':missing.append('At least two comparable observations in every month, with a latest observation within 35 days, are required')
    if not benchmark or benchmark.get('status')!='supported':missing.append('A supported saved historical fair-value range is required')
    if not inputs.required_delivery_date:missing.append('Required delivery date is unknown')
    if inputs.supplier_lead_time_days is None:missing.append('Supplier lead time is unknown')
    for value,label in [(inputs.requirement_confirmed,'Purchase requirement is unconfirmed'),
                        (inputs.commercial_terms_confirmed,'Commercial terms and source reliability have not been reviewed'),
                        (inputs.current_quote_confirmed,'Current quotation validity is unconfirmed; the saved quotation may be stale'),
                        (inputs.benchmark_applicability_reviewed,'Applicability of the older historical benchmark has not been reviewed')]:
        if not value:missing.append(label)
    base_qty=decimal(quote['quantity'])*FACTORS[quote['uom']]
    volume_ok=Decimal('.5')<=quantity/base_qty<=2
    if not volume_ok:missing.append('Scenario quantity is outside 0.5–2 times the saved case quantity; benchmark volume applicability is unvalidated')
    expected_arrival=planned+timedelta(days=inputs.supplier_lead_time_days) if inputs.supplier_lead_time_days is not None else None
    last_order=inputs.required_delivery_date-timedelta(days=inputs.supplier_lead_time_days) if inputs.required_delivery_date and inputs.supplier_lead_time_days is not None else None
    feasible=expected_arrival<=inputs.required_delivery_date if expected_arrival and inputs.required_delivery_date else None
    if feasible is False:missing.append('Entered purchase date and lead time cannot meet required delivery; obtain a confirmed expedited plan')
    if inputs.inventory_m is None:warnings.append('Usable inventory is unknown; deferral cannot be supported from inventory coverage')
    if last_order and planned>today and planned<=last_order:
        warnings.append('A feasible later order date does not establish a lower future price')
    lower=upper=target=historical=None
    if benchmark and benchmark.get('status')=='supported':
        factor=FACTORS[quote['uom']]
        lower=decimal(benchmark.get('calculation',{}).get('lower_unrounded',benchmark['lower']))/factor
        upper=decimal(benchmark.get('calculation',{}).get('upper_unrounded',benchmark['upper']))/factor
        target=decimal(benchmark.get('calculation',{}).get('target_unrounded',benchmark['target']))/factor
        historical=decimal(benchmark['median'])/factor
    within=lower<=price<=upper if lower is not None else None
    slack=(last_order-today).days if last_order else None
    if not missing:
        falling=all(decimal(trend['months'][i]['mean_unrounded'])<decimal(trend['months'][i-1]['mean_unrounded']) for i in (1,2))
        if price>upper:
            state='NEGOTIATE / MONITOR';reasons.append('Entered quote exceeds the saved fair-value band; challenge the premium rather than infer a benefit from waiting')
            if slack<=7:warnings.append('Delivery is approaching: negotiate promptly and obtain a confirmed supply plan; do not postpone solely to seek a lower price')
        elif within and planned==today and slack<=7:
            state='BUY NOW';reasons.append('Confirmed scenario requirement, reviewed commercial inputs, quote within the saved fair-value band, and a latest order date within seven days support prompt human-reviewed procurement')
        elif within and planned>today and slack>=14 and feasible and inputs.inventory_m is not None and inputs.inventory_m>=quantity and falling:
            state='CONSIDER DEFERRING';reasons.append('Usable same-specification inventory covers the full entered requirement, the later order meets delivery, and all three monthly means decline; consider deferral only after human confirmation')
        else:
            state='NEGOTIATE / MONITOR';reasons.append('No demonstrated advantage to an immediate or delayed order; monitor revised quotes and validate price and delivery terms')
            if price<lower:warnings.append('Quote is below the supported band; verify construction, quality and terms before treating it as an opportunity')
    else:reasons=missing[:]
    costs={'current_purchase_cost':money(quantity*price),'historical_reference_per_metre':money(historical) if historical is not None else None,
           'target_per_metre':money(target) if target is not None else None,
           'fair_value_lower_per_metre':money(lower) if lower is not None else None,'fair_value_upper_per_metre':money(upper) if upper is not None else None,
           'difference_from_historical_cost':money((price-historical)*quantity) if historical is not None else None,
           'potential_negotiation_opportunity':money(max(Decimal(0),price-target)*quantity) if target is not None else None,
           'comparison_basis':'Saved historical reference; illustrative extrapolation only when scenario volume or terms are unvalidated. Excludes tax/freight not included in the quote; opportunity is not realized savings.'}
    future=None
    if inputs.assumed_future_price_per_metre is not None:
        future={'classification':'User-entered assumed price — not a forecast','assumed_price_per_metre':str(inputs.assumed_future_price_per_metre),
                'assumed_purchase_cost':money(quantity*inputs.assumed_future_price_per_metre),
                'difference_from_current_cost':money(quantity*(inputs.assumed_future_price_per_metre-price))}
    result={'version':TIMING_VERSION,'label':LABEL,'as_of':today.isoformat(),'state':state,'reasons':reasons,'missing_inputs':missing,'warnings':warnings,
            'inputs':inputs.model_dump(mode='json'),'planned_purchase_date':planned.isoformat(),'costs':costs,
            'expected_arrival':expected_arrival.isoformat() if expected_arrival else None,'latest_order_date':last_order.isoformat() if last_order else None,
            'delivery_feasible':feasible,'days_until_latest_order':slack,'quote_within_historical_band':within,'volume_comparable':volume_ok,
            'inventory_covers_full_requirement':inputs.inventory_m>=quantity if inputs.inventory_m is not None else None,
            'future_price_scenario':future,'future_price_notice':'Future market prices are uncertain. No future cable price is predicted.',
            'advisory':'Conditional synthetic demonstration only. Human review required; entered lead times are assumptions, not supplier commitments.',
            'rule':{'urgency_buffer_days':7,'deferral_minimum_slack_days':14,'inventory_policy':'Known usable same-specification inventory must cover the entire scenario requirement for deferral','falling_policy':'Both consecutive monthly means must decline','status':'Provisional demonstration enhancement; no approved production purchasing policy'},
            'trend_hash':trend['calculation_hash'],'benchmark_hash':digest(benchmark) if benchmark else None,'read_only':True}
    result['calculation_hash']=digest(result)
    return result
