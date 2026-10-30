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
        expected=source.get('product_specification')
        match='Not directly comparable'
        detail='No exact authenticated product specification is available for this reference.'
        if expected:
            missing=[k for k in expected if k not in spec]
            differences=[k for k,v in expected.items() if k in spec and
                         (spec[k] not in v if k=='area_mm2' and isinstance(v,list) else spec[k]!=v)]
            detail='; '.join(filter(None,[
                'Specification mismatch: '+', '.join(differences) if differences else '',
                'Unconfirmed case fields: '+', '.join(missing) if missing else '',
            ]))
            if not missing and not differences:
                match='Technical fields match; commercial comparability unconfirmed'
                detail='Matching technical fields do not establish a comparable selling price, tax or freight terms.'
        refs.append({**source,'specification_match':match,'comparison_detail':detail,
                     'comparability_status':source['verification_result']})
    return {'quote':quote,'synthetic_historical_benchmark':(result or {}).get('median'),
            'run_id':run_id,'verified_public_reference_price':None,'references':refs,
            'limitations':'No verified public price is currently available for this exact specification. Public references do not alter the synthetic fair-value band or negotiation target.'}

def source_answer(quote=None):
    sources=directory()
    answer=(DATASET_STATUS+' Pricing inputs are synthetic procurement records, demonstration quotations and historical holdouts; they were not extracted from these references or retrieved through external APIs. '
        'No verified public price is currently available for this exact specification. Public references do not change the benchmark or target. '
        'GeM provides procurement context; no exact price listing has been verified. '
        'The KEI Scribd page is a third-party published price-list copy — authenticity and comparability pending. It is not an official live KEI API. '
        'The government-hosted Uttarakhand Power Corporation specification is technical evidence, not price evidence. Its scope includes 11 kV aluminium XLPE three-core cable in 95 sq. mm and other sizes (PDF pages 9–11). '
        'The prior Raj Electricals URL (HTTP 404) and NFL URL (HTTP 500), and their verification records, remain in provenance history. '
        'Source cards show recorded availability and allow a fresh bounded availability check; browser access may differ. '
        'Differences or missing specifications and commercial terms prevent assuming comparability. '
        'Open Data Sources for original links and the separate synthetic Evidence Card inputs.')
    if quote:
        technical=comparison(quote)['references'][2]
        answer+=' Selected material: '+technical['specification_match']+'. '+technical['comparison_detail']+'.'
    return answer,[{'source_id':s['source_id'],'name':s['name'],'url':s['current_url'],
                    'role':s['role'],'status':s['verification_result']} for s in sources]
