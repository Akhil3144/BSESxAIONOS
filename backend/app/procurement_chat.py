"""Deterministic procurement trend and timing answers; no forecast generation."""
import re
from .engine import decimal,money,financial_context
from .procurement_trends import analyze_trend,LABEL,business_today
from .procurement_timing import TimingInputs,default_inputs,simulate

QUESTIONS=[
 'How have cable prices changed over the last three months?',
 'What is the percentage price increase?',
 'Which month had the lowest observed price?',
 'Which month had the highest observed price?',
 'Is now a reasonable time to buy cable?',
 'Should procurement wait until next month?',
 'Why is the system recommending Buy Now?',
 'What happens if we purchase 5,000 metres today?',
 'What if the supplier increases the quotation by 5%?',
 'Which source records support the price trend?',
 'What information is missing before making a purchasing decision?',
 'Can you explain the buying recommendation in simple terms?',
]

def is_procurement_question(message):
    s=message.lower()
    return any(k in s for k in ['three months','three-month','last 3 months','price trend','price increase','lowest observed','highest observed',
                               'time to buy','buy now','buying recommendation','purchasing decision','procurement wait','next month','purchase timing','price movement',
                               'increases the quotation','increase the quotation','increases its quote']) or bool(re.search(r'purchase\s+[\d,]+\s*(?:metres|meters)',s))

def answer_procurement(message,quote,benchmark,context=None):
    return _answer(message,quote,benchmark,context)

@financial_context
def _answer(message,quote,benchmark,context):
    trend=context['trend'] if context else analyze_trend(quote,[])
    rec=context['recommendation'] if context else simulate(quote,benchmark,trend,default_inputs(quote))
    inputs=TimingInputs.model_validate(rec['inputs']);s=message.lower();data={'trend_hash':trend['calculation_hash'],'timing':rec}
    citations=[{'evidence_id':e['evidence_id'],'source_ref':e['source_id'],'date':e['observation_date'],
                'normalized_price':e['normalized_price_per_metre'],'kind':'trend'} for e in trend['evidence']]
    prefix=LABEL+'. '
    if 'lowest observed' in s or 'highest observed' in s:
        month=trend['lowest_month'] if 'lowest' in s else trend['highest_month']
        answer=(f"{month['label']} has the {'lowest' if 'lowest' in s else 'highest'} observed monthly mean: INR {month['price_per_metre']}/m from {month['observation_count']} observations." if month else 'No qualifying monthly price is available.')
    elif re.search(r'purchase\s+([\d,]+)\s*(?:metres|meters)',s):
        match=re.search(r'purchase\s+([\d,]+)\s*(?:metres|meters)',s)
        raw=inputs.model_dump(mode='json');raw.update(quantity_m=match.group(1).replace(',',''),planned_purchase_date=business_today().isoformat())
        try:
            scenario=simulate(quote,benchmark,trend,TimingInputs.model_validate(raw));data['timing']=scenario
            answer=f"At the entered/saved quote, {raw['quantity_m']} metres would cost INR {scenario['costs']['current_purchase_cost']} before excluded tax/freight. {scenario['state']}: "+'; '.join(scenario['reasons'])+'. This does not place a purchase or change the case.'
        except ValueError:answer='Enter a procurement quantity greater than zero and no more than 1,000,000,000 metres.'
    elif any(k in s for k in ['increases the quotation','increase the quotation','increases its quote']):
        match=re.search(r'(-?\d+(?:\.\d+)?)\s*(?:%|percent)',s)
        if not match or not 0<=decimal(match.group(1))<=100:
            answer='Specify a hypothetical quotation increase from 0% to 100%.'
        else:
            pct=decimal(match.group(1));price=inputs.current_quote_per_metre*(1+pct/100)
            if price>decimal('1e12'):
                return prefix+'Hypothetical quotation exceeds the supported 1e12 INR per metre input limit.',data,citations
            scenario=simulate(quote,benchmark,trend,inputs.model_copy(update={'current_quote_per_metre':price}));data['timing']=scenario
            answer=f"Hypothetical {pct}% increase: INR {money(price)}/m; purchase cost INR {scenario['costs']['current_purchase_cost']} for {inputs.quantity_m} metres. {scenario['state']}: "+'; '.join(scenario['reasons'])+'. This is an assumed supplier-quote change, not a forecast or supplier commitment.'
    elif any(k in s for k in ['time to buy','buy now','buying recommendation','purchasing decision','procurement wait','next month','purchase timing']):
        answer=f"The current conditional recommendation is {rec['state']}: "+'; '.join(rec['reasons'])+'.'
        if 'buy now' in s and rec['state']!='BUY NOW':answer+=' The system is not currently recommending Buy Now.'
        if rec['missing_inputs']:answer+=' Missing or unvalidated inputs: '+'; '.join(rec['missing_inputs'])+'.'
        if 'next month' in s or 'wait' in s:answer+=' Do not wait solely because past prices fell. Confirm delivery, lead time and usable inventory. Future prices are uncertain; enter an explicit assumed price in the simulator rather than treat it as a prediction.'
        answer+=' Human review is required. Unknown inventory is never assumed to provide coverage.'
    elif 'source records' in s:
        answer='The trend uses these original synthetic observations: '+', '.join(e['evidence_id'] for e in trend['evidence'])+'. Open Procurement Intelligence → Underlying trend evidence for original dates, prices, units and normalization. No GeM, KEI or government document supplied these numerical prices.'
    else:
        lines=[f"{m['label']}: INR {m['price_per_metre']}/m ({m['observation_count']} observations; month-on-month {m['change_pct']+'%' if m['change_pct'] is not None else 'not available'})." if m['price_per_metre'] is not None else f"{m['label']}: no qualifying observations." for m in trend['months']]
        answer=' '.join(lines)+f" Overall three-month movement: {trend['overall_change_pct']+'%' if trend['overall_change_pct'] is not None else 'not available'}; trend {trend['direction']}. The current month is partial. No cause or future price is inferred."
    return prefix+answer,data,citations
