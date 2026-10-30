"""Compose trend, scenario and saved benchmark context without business writes."""
import json
from sqlalchemy import select
from fastapi import HTTPException
from .db import records,cases,runs,snapshots
from .engine import digest,decimal,FACTORS
from .seed import sample
from .public_sources import directory,public_prices
from .procurement_trends import analyze_trend,business_today,PROFILE,MATERIAL
from .procurement_timing import default_inputs,simulate


def build_intelligence(conn,case_id=None,run_id=None):
    quote=sample();benchmark=None;case=None;run=None;today=business_today()
    if case_id:
        saved=conn.execute(select(cases).where(cases.c.id==case_id,cases.c.tenant=='demo')).mappings().first()
        if not saved:raise HTTPException(404,'Record not found')
        case=dict(saved);quote=json.loads(case['quote'])
        snap=conn.execute(select(snapshots).where(snapshots.c.id==case['snapshot_id'],snapshots.c.tenant=='demo')).mappings().first()
        if not snap or digest(json.loads(snap['payload']))!=snap['sha256']:raise HTTPException(409,'Dataset snapshot integrity failure')
        query=select(runs).where(runs.c.case_id==case_id)
        if run_id:query=query.where(runs.c.id==run_id)
        run=conn.execute(query.order_by(runs.c.created.desc()).limit(1)).mappings().first()
        if run_id and not run:raise HTTPException(404,'Analysis not found for this case')
        if run:
            benchmark=json.loads(run['result'])
            if digest(benchmark)!=run['sha256']:raise HTTPException(409,'Analysis evidence integrity failure')
    if quote.get('currency')!='INR':raise HTTPException(422,'Procurement Intelligence supports INR quotes only; no FX conversion is approved')
    if decimal(quote['quantity'])*FACTORS[quote['uom']]>decimal('1e9'):raise HTTPException(422,'Normalized case quantity exceeds the supported scenario limit of 1e9 metres')
    rows=[json.loads(p) for p in conn.execute(select(records.c.payload).where(records.c.tenant=='demo').order_by(records.c.source_id)).scalars()]
    trend=analyze_trend(quote,rows,today)
    inputs=default_inputs(quote)
    return {'case_id':case_id,'case_title':case['title'] if case else None,'run_id':run['id'] if run else None,
            'quote':quote,'benchmark':{'status':benchmark['status'],'median':benchmark.get('median'),'lower':benchmark.get('lower'),
                                     'upper':benchmark.get('upper'),'target':benchmark.get('target'),'quote_unit':quote['uom'],
                                     'quote_date':quote['date'],'hash':digest(benchmark)} if benchmark else None,
            'material_options':[{'id':MATERIAL,'name':'11 kV XLPE · Aluminium · 3 core × 95 sq. mm','specification':PROFILE}],
            'trend':trend,'default_inputs':inputs.model_dump(mode='json'),'recommendation':simulate(quote,benchmark,trend,inputs,today),
            'public_evidence':{'sources':directory(),'verified_prices':public_prices(),'included_in_trend':False},
            'saved_benchmark_unchanged':True,'read_only':True},benchmark
