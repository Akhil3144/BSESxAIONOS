"""Versioned public provenance, separate from synthetic benchmark inputs.

No import or normalization endpoint is enabled. An observation requires individual
source authentication and commercial/specification review before implementation.
"""
import json
from pathlib import Path
from copy import deepcopy

DATASET_STATUS='Synthetic demonstration data — public references are separate supporting evidence.'
STATUS_DEFINITIONS={
    'Verified comparable':'Exact required specifications and commercial terms have been validated sufficiently for the stated comparison.',
    'Reference only':'Authentic source exists, but some specifications or commercial terms are not comparable or remain unconfirmed.',
    'Unverified':'Source is missing, inaccessible, undated or has no authenticated price observation.',
}

def directory():
    return deepcopy(json.loads(Path(__file__).with_name('public_sources.json').read_text()))

def public_prices():
    # Deliberately empty: none of the configured sources has an authenticated price.
    return []

def comparison(quote,result=None,run_id=None):
    spec=quote.get('specification',{})
    refs=[]
    for source in directory():
        match='Not established'
        if source['product_specification']:
            expected=source['product_specification']
            fields=['voltage_kv','conductor','area_mm2','cores','insulation']
            differences=[k for k in fields if spec.get(k)!=expected[k]]
            match='Specification mismatch: '+', '.join(differences) if differences else 'Core fields match; armour, voltage class and standards remain unconfirmed'
        refs.append({**source,'specification_match':match,'comparability_status':source['verification_result']})
    return {'quote':quote,'synthetic_historical_benchmark':(result or {}).get('median'),
            'run_id':run_id,'verified_public_reference_price':None,'references':refs,
            'limitations':'No verified public price is currently available for this exact specification. Public references do not alter the synthetic fair-value band or negotiation target.'}

def source_answer():
    sources=directory()
    return (DATASET_STATUS+' Pricing inputs are synthetic procurement records, demonstration quotations and historical holdouts; they were not retrieved through external APIs. '
        'No verified public price is currently available for this exact specification. Public references do not change the benchmark or target. '
        'GeM provides procurement context; its homepage is accessible, but no exact price listing has been verified. '
        'The supplied KEI price-list URL returns HTTP 404 and requires replacement; no price is authenticated. '
        'The NFL indexed technical document specifies 11 kV UE, three-core 185 sq. mm armoured aluminium XLPE cable (page 1, Annexure I). '
        'Its direct download returned HTTP 500. This supports technical context only, differs from the seeded 95 sq. mm cases, and provides no verified selling price. '
        'Differences in list and selling prices, tax, freight, date, conductor area and commercial terms prevent assuming comparability. '
        'Open Data Sources for original links, retrieval timestamps and limitations. The Evidence Card retains the synthetic inputs separately.'),[
            {'source_id':s['source_id'],'name':s['name'],'url':s['original_url'],'role':s['role'],'status':s['verification_result']} for s in sources]
