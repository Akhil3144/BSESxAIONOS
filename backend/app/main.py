import os, json, csv, io, secrets, time, hashlib, uuid, zipfile
from datetime import date
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select, func
from .db import *
from .security import current, permit, check, hash_password
from .engine import validate, benchmark, DEFAULT_RULE, digest, decimal, money, resolve_rule, reference_issues
from .reporting import build_pack
from .agents import NegotiationIntelligenceAgent
from .ai import LLMConfig

TENANT='demo' # Pilot isolated deployment. Real tenancy disabled until governance configured.
def uid(): return str(uuid.uuid4())
def one(c,table,id):
    row=c.execute(select(table).where(table.c.id==id)).mappings().first()
    if not row: raise HTTPException(404,'Record not found')
    return dict(row)
def active_rule(c):
    r=c.execute(select(rules).where(rules.c.status.in_(['approved','demo_provisional'])).order_by(rules.c.id.desc())).mappings().first()
    if not r: raise HTTPException(409,'No active benchmark policy')
    return resolve_rule(json.loads(r['payload']))

def verified_snapshot(c,id):
    snap=scoped(c,snapshots,id)
    if digest(json.loads(snap['payload']))!=snap['sha256']: raise HTTPException(409,'Dataset snapshot integrity failure')
    return snap

def scoped(c,table,id):
    row=one(c,table,id)
    if row.get('tenant',TENANT)!=TENANT: raise HTTPException(404,'Record not found')
    return row

@asynccontextmanager
async def lifespan(app):
    initialize()
    with engine.begin() as c:
        if not c.execute(select(rules.c.id)).first(): c.execute(rules.insert().values(id=DEFAULT_RULE['version'],payload=dumps(DEFAULT_RULE),status='demo_provisional'))
        if os.getenv('DEMO_PASSWORD'):
            for name,role in [('analyst','analyst'),('reviewer','reviewer'),('admin','admin'),('evaluator','evaluator')]:
                if not c.execute(select(users.c.id).where(users.c.name==name)).first(): c.execute(users.insert().values(id=name,name=name,password=hash_password(os.environ['DEMO_PASSWORD']),role=role))
    yield
app=FastAPI(title='BSES x AIONOS - Procurement Negotiation Intelligence',lifespan=lifespan)
@app.get('/api/guide/pdf')
def manager_guide_pdf(u=Depends(current)):
    path=Path(__file__).resolve().parents[2]/'BSES_MANAGER_DEMO_GUIDE.pdf'
    if not path.is_file(): raise HTTPException(503,'Manager guide has not been generated')
    return FileResponse(path,media_type='application/pdf',filename='BSES_MANAGER_DEMO_GUIDE.pdf')
@app.get('/api/guide/markdown')
def manager_guide_markdown(u=Depends(current)):
    path=Path(__file__).resolve().parents[2]/'BSES_MANAGER_DEMO_GUIDE.md'
    if not path.is_file(): raise HTTPException(503,'Manager guide has not been generated')
    return FileResponse(path,media_type='text/markdown',filename='BSES_MANAGER_DEMO_GUIDE.md')

@app.get('/api/public-sources')
def get_public_sources(u=Depends(current)):
    from .public_sources import directory, public_prices, DATASET_STATUS, STATUS_DEFINITIONS
    with engine.connect() as c:
        procurement=[json.loads(p) for p in c.execute(select(records.c.payload).where(records.c.tenant==TENANT)).scalars()]
        quotations=[json.loads(p) for p in c.execute(select(cases.c.quote).where(cases.c.tenant==TENANT)).scalars()]
        historical=[json.loads(p) for p in c.execute(select(holdouts.c.quote).where(holdouts.c.tenant==TENANT)).scalars()]
    return {'dataset_status':DATASET_STATUS,'summary':{
        'Synthetic procurement records':sum(p.get('synthetic') is True for p in procurement),
        'Demonstration quotation cases':sum(p.get('synthetic') is True and str(p.get('id','')).startswith('DEMO-QUOTE-') for p in quotations),
        'Synthetic historical holdouts':sum(p.get('synthetic') is True for p in historical),
        'Primary category':'11 kV XLPE cable','Public reference sources':len(directory()),
        'Verified public price observations':len(public_prices()),'External live API connections':'None configured or verified for public procurement / prices'},
        'sources':directory(),'prices':public_prices(),'status_definitions':STATUS_DEFINITIONS}

@app.get('/api/cases/{id}/public-sources')
def case_public_sources(id:str,u=Depends(current)):
    from .public_sources import comparison
    with engine.connect() as c:
        case=scoped(c,cases,id)
        run=c.execute(select(runs).where(runs.c.case_id==id).order_by(runs.c.created.desc()).limit(1)).mappings().first()
        result=json.loads(run['result']) if run else None
        if run and digest(result)!=run['sha256']: raise HTTPException(409,'Analysis evidence integrity failure')
    return comparison(json.loads(case['quote']),result,run['id'] if run else None)

@app.get('/api/health')
def health(): return {'status':'ok','mode':'restricted synthetic pilot','live_llm':False,'llm_configured':LLMConfig.from_env().ready,'external_integrations':'disabled'}
class Login(BaseModel):
    username:str=Field(max_length=100)
    password:str=Field(max_length=200)
_attempts={}
@app.post('/api/login')
def login(body:Login):
    key=body.username; stamp=time.time(); attempts=[t for t in _attempts.get(key,[]) if stamp-t<60]
    if len(attempts)>=8: raise HTTPException(429,'Too many attempts; retry in one minute')
    with engine.begin() as c:
        u=c.execute(select(users).where(users.c.name==body.username)).mappings().first()
        if not u or not check(body.password,u['password']):
            _attempts[key]=attempts+[stamp]; raise HTTPException(401,'Invalid credentials')
        token=secrets.token_urlsafe(32); c.execute(sessions.insert().values(id=hashlib.sha256(token.encode()).hexdigest(),user_id=u['id'],expires=int(stamp)+28800)); log(c,u['id'],'login',{})
        return {'token':token,'role':u['role'],'name':u['name']}
@app.post('/api/logout')
def logout(u=Depends(current),authorization:str=__import__('fastapi').Header(default='')):
    with engine.begin() as c: c.execute(sessions.delete().where(sessions.c.id==hashlib.sha256(authorization[7:].encode()).hexdigest()))
    return {'logged_out':True}
@app.get('/api/me')
def me(u=Depends(current)): return {k:u[k] for k in ['id','name','role']}

def import_rows(c,rows,name,raw,actor):
    batch=uid(); errors=[]; accepted=[]; seen=set(c.execute(select(records.c.source_id).where(records.c.tenant==TENANT)).scalars())
    for idx,row in enumerate(rows):
        issues=validate(row)+reference_issues(row)
        if row.get('id') in seen: issues.append('Duplicate source ID')
        if row.get('synthetic') is not True: issues.append('This deployment accepts explicitly synthetic records only')
        if issues: errors.append({'row':idx+1,'issues':issues,'raw':row})
        else: accepted.append(row); seen.add(row['id'])
    c.execute(batches.insert().values(id=batch,name=Path(name).name,sha256=hashlib.sha256(raw).hexdigest(),raw=raw.hex(),created=now(),tenant=TENANT,errors=dumps(errors)))
    for row in accepted: c.execute(records.insert().values(id=uid(),source_id=row['id'],batch_id=batch,payload=dumps(row),tenant=TENANT))
    log(c,actor,'import',{'batch':batch,'accepted':len(accepted),'rejected':len(errors)})
    return {'id':batch,'accepted':len(accepted),'rejected':len(errors),'errors':errors}
@app.post('/api/import')
async def upload(file:UploadFile=File(...),mapping:str=Form('{}'),u=Depends(current)):
    permit(u,'analyst','admin'); raw=await file.read(5*1024*1024+1)
    if len(raw)>5*1024*1024: raise HTTPException(413,'Upload exceeds 5 MiB')
    try:
        mp=json.loads(mapping)
        if not isinstance(mp,dict): raise ValueError('Mapping must be an object')
        if file.filename.lower().endswith('.csv'): rows=list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'))))
        elif file.filename.lower().endswith('.xlsx'):
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                if sum(i.file_size for i in z.infolist())>30*1024*1024: raise ValueError('Expanded workbook too large')
            from openpyxl import load_workbook
            values=load_workbook(io.BytesIO(raw),read_only=True,data_only=True).active.values; headers=next(values); rows=[dict(zip(headers,row)) for row in values]
        else: raise ValueError('Only CSV and XLSX are accepted')
        if len(rows)>5000: raise ValueError('Maximum 5000 records')
        clean=[]
        for row in rows:
            r={mp.get(k,k):v for k,v in row.items() if k}
            for k in ['specification']:
                if isinstance(r.get(k),str): r[k]=json.loads(r[k])
            if isinstance(r.get('synthetic'),str): r['synthetic']=r['synthetic'].lower()=='true'
            # Preserve original term values; validation must reject fractional days, never truncate.
            clean.append(r)
        if any(reference_issues(r) for r in clean): raise HTTPException(422,'Unmapped or outcome-bearing evidence must not enter reference storage; map only approved reference fields')
        with engine.begin() as c: return import_rows(c,clean,file.filename,raw,u['id'])
    except (ValueError,KeyError,TypeError,StopIteration,zipfile.BadZipFile) as e: raise HTTPException(422,str(e))
@app.get('/api/imports')
def imports(u=Depends(current)):
    with engine.connect() as c: return [dict(r) for r in c.execute(select(batches.c.id,batches.c.name,batches.c.sha256,batches.c.created,batches.c.errors).where(batches.c.tenant==TENANT)).mappings()]
@app.get('/api/sources/{batch_id}')
def source(batch_id:str,u=Depends(current)):
    with engine.begin() as c:
        b=scoped(c,batches,batch_id); log(c,u['id'],'source_download',{'id':batch_id})
    return Response(bytes.fromhex(b['raw']),media_type='application/octet-stream',headers={'Content-Disposition':'attachment; filename="source-evidence.bin"'})
@app.get('/api/records')
def list_records(u=Depends(current)):
    with engine.connect() as c: return [{'batch_id':r.batch_id,**json.loads(r.payload)} for r in c.execute(select(records).where(records.c.tenant==TENANT))]
@app.post('/api/snapshots')
def freeze(u=Depends(current)):
    permit(u,'admin','reviewer')
    with engine.begin() as c:
        rows=[json.loads(r) for r in c.execute(select(records.c.payload).where(records.c.tenant==TENANT).order_by(records.c.source_id)).scalars()]
        if not rows: raise HTTPException(422,'No reference records to freeze')
        id=uid(); c.execute(snapshots.insert().values(id=id,payload=dumps(rows),sha256=digest(rows),created=now(),tenant=TENANT)); log(c,u['id'],'dataset_frozen',{'id':id,'sha256':digest(rows)})
    return {'id':id,'count':len(rows),'sha256':digest(rows)}
@app.get('/api/snapshots')
def get_snapshots(u=Depends(current)):
    with engine.connect() as c: return [dict(r) for r in c.execute(select(snapshots.c.id,snapshots.c.sha256,snapshots.c.created).where(snapshots.c.tenant==TENANT)).mappings()]
class CaseIn(BaseModel):
    title:str=Field(min_length=3,max_length=200)
    quote:dict
    snapshot_id:str
@app.post('/api/cases')
def create_case(body:CaseIn,u=Depends(current)):
    permit(u,'analyst','admin')
    issues=validate(body.quote)
    if issues: raise HTTPException(422,issues)
    if body.quote.get('synthetic') is not True: raise HTTPException(422,'Synthetic pilot only')
    with engine.begin() as c:
        scoped(c,snapshots,body.snapshot_id); id=uid(); c.execute(cases.insert().values(id=id,title=body.title,quote=dumps(body.quote),snapshot_id=body.snapshot_id,status='draft',tenant=TENANT,created=now())); log(c,u['id'],'case_created',{'id':id})
    return {'id':id}
@app.get('/api/cases')
def get_cases(u=Depends(current)):
    with engine.connect() as c: return [dict(r) for r in c.execute(select(cases).where(cases.c.tenant==TENANT).order_by(cases.c.created.desc())).mappings()]
@app.get('/api/cases/{id}')
def get_case(id:str,u=Depends(current)):
    with engine.connect() as c:
        case=scoped(c,cases,id); case['quote']=json.loads(case['quote']); rr=c.execute(select(runs).where(runs.c.case_id==id).order_by(runs.c.created.desc())).mappings().all(); case['runs']=[{**dict(r),'result':json.loads(r['result'])} for r in rr]; case['reviews']=[dict(r) for r in c.execute(select(reviews).where(reviews.c.case_id==id)).mappings()]
        return case
class ChatIn(BaseModel):
    model_config=ConfigDict(extra='forbid')
    message:str=Field(min_length=1,max_length=2000)
    run_id:str|None=None
@app.post('/api/cases/{id}/chat')
def case_chat(id:str,body:ChatIn,u=Depends(current)):
    from .chat import answer_question
    with engine.connect() as c:
        case=scoped(c,cases,id); snap=verified_snapshot(c,case['snapshot_id'])
        rr=[dict(r) for r in c.execute(select(runs).where(runs.c.case_id==id).order_by(runs.c.created.desc())).mappings()]
        if body.run_id:
            index=next((i for i,r in enumerate(rr) if r['id']==body.run_id),None)
            if index is None: raise HTTPException(404,'Analysis not found for this case')
            rr=rr[index:]
        if not rr: raise HTTPException(409,'Calculate this case before asking case questions')
        parsed=[]
        source_ids={r['id'] for r in json.loads(snap['payload'])}
        for run in rr[:2]:
            result=json.loads(run['result'])
            if digest(result)!=run['sha256'] or any(x['id'] not in source_ids for x in result['included']): raise HTTPException(409,'Analysis evidence integrity failure')
            parsed.append({**run,'result':result})
    answer=answer_question(case,parsed,body.message,u['role'])
    with engine.begin() as c: log(c,u['id'],'case_assistant',{'case':id,'run':answer['run_id'],'intent':answer['intent'],'mode':answer['mode']})
    return answer

@app.get('/api/demo/tour')
def demo_tour(u=Depends(current)):
    # Read-only selection. It never seeds, recalculates, reviews or reveals outcomes.
    with engine.connect() as c:
        cc=c.execute(select(cases).where(cases.c.tenant=='demo').order_by(cases.c.created)).mappings().all()
        primary=next((dict(x) for x in cc if x['title']=='DEMO / SYNTHETIC - 11 kV XLPE cable lot 1'),None)
        if not primary: raise HTTPException(409,'An administrator must initialize the synthetic demonstration in Settings first')
        snap=verified_snapshot(c,primary['snapshot_id'])
        if json.loads(primary['quote']).get('synthetic') is not True or not all(r.get('synthetic') is True for r in json.loads(snap['payload'])): raise HTTPException(409,'Guided demo requires an entirely synthetic dataset')
        run=c.execute(select(runs).where(runs.c.case_id==primary['id']).order_by(runs.c.created.desc()).limit(1)).mappings().first()
        if not run or digest(json.loads(run['result']))!=run['sha256']: raise HTTPException(409,'Verified demo analysis required')
        return {'case_id':primary['id'],'run_id':run['id'],'snapshot_id':primary['snapshot_id'],'synthetic':True,'read_only':True,'review_actions_automatic':False}

@app.post('/api/cases/{id}/run')
def calculate(id:str,u=Depends(current)):
    permit(u,'analyst','admin')
    with engine.begin() as c:
        case=scoped(c,cases,id)
        if case['status'] not in ['draft','changes_requested']: raise HTTPException(409,'Reopen via changes requested before recalculation')
        snap=verified_snapshot(c,case['snapshot_id']); rule=active_rule(c)
        result=NegotiationIntelligenceAgent().analyze(json.loads(case['quote']),json.loads(snap['payload']),[json.loads(p) for p in c.execute(select(suppliers.c.payload).where(suppliers.c.tenant==TENANT)).scalars()],rule); id_run=uid(); c.execute(runs.insert().values(id=id_run,case_id=id,result=dumps(result),sha256=digest(result),created=now(),rule_id=rule['version'])); log(c,u['id'],'benchmark_run',{'case':id,'run':id_run,'snapshot':case['snapshot_id'],'hash':digest(result)})
        return {'id':id_run,'result':result}
TRANSITIONS={'draft':['ready_for_review'],'ready_for_review':['under_review'],'under_review':['changes_requested','accepted','rejected'],'changes_requested':['ready_for_review'],'accepted':['archived','changes_requested'],'rejected':['archived','changes_requested'],'archived':[]}
class ReviewIn(BaseModel):
    action:str
    comment:str=Field(min_length=5,max_length=5000)
@app.post('/api/cases/{id}/review')
def review(id:str,body:ReviewIn,u=Depends(current)):
    if body.action=='ready_for_review': permit(u,'analyst','admin')
    else: permit(u,'reviewer','admin')
    with engine.begin() as c:
        case=scoped(c,cases,id); run=c.execute(select(runs).where(runs.c.case_id==id).order_by(runs.c.created.desc())).mappings().first()
        if not run: raise HTTPException(409,'Calculate evidence before review')
        if body.action not in TRANSITIONS[case['status']]: raise HTTPException(409,'Invalid workflow transition')
        if body.action=='accepted' and json.loads(run['result'])['status']!='supported': raise HTTPException(409,'Insufficient-evidence recommendations cannot be accepted')
        c.execute(reviews.insert().values(id=uid(),case_id=id,run_id=run['id'],actor=u['id'],action=body.action,comment=body.comment,created=now())); c.execute(cases.update().where(cases.c.id==id).values(status=body.action)); log(c,u['id'],'review',{'case':id,'run':run['id'],**body.model_dump()})
    return {'status':body.action}
@app.get('/api/cases/{id}/pack')
def pack(id:str,run_id:str|None=None,u=Depends(current)):
    permit(u,'analyst','reviewer','admin')
    with engine.begin() as c:
        case=scoped(c,cases,id); query=select(runs).where(runs.c.case_id==id)
        if run_id: query=query.where(runs.c.id==run_id)
        rr=c.execute(query.order_by(runs.c.created.desc())).mappings().first()
        if not rr: raise HTTPException(409,'Calculate a benchmark first')
        if digest(json.loads(rr['result']))!=rr['sha256']: raise HTTPException(409,'Benchmark result integrity failure')
        run={**dict(rr),'result':json.loads(rr['result'])}; actions=[dict(r) for r in c.execute(select(reviews).where(reviews.c.case_id==id,reviews.c.run_id==rr['id'])).mappings()]; context=[json.loads(r) for r in c.execute(select(suppliers.c.payload).where(suppliers.c.tenant==TENANT)).scalars() if json.loads(r)['supplier']==run['result']['quote']['supplier']]
        latest=c.execute(select(runs.c.id).where(runs.c.case_id==id).order_by(runs.c.created.desc()).limit(1)).scalar()
        if latest!=rr['id']: case['status']='historical analysis; see review history for this run'
        context=run['result'].get('supplier_context',context); snapshot={'case':case,'run':run,'reviews':actions,'supplier_context':context}; pdf=build_pack(case,run,actions,context); rid=uid(); c.execute(reports.insert().values(id=rid,run_id=run['id'],pdf_hex=pdf.hex(),sha256=hashlib.sha256(pdf).hexdigest(),snapshot=dumps(snapshot),created=now())); log(c,u['id'],'report_export',{'report':rid,'run':run['id']})
    return Response(pdf,media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="negotiation-{id}-{rid}.pdf"','X-Report-Version':rid})
@app.get('/api/cases/{id}/reports')
def report_versions(id:str,u=Depends(current)):
    permit(u,'analyst','reviewer','admin')
    with engine.connect() as c:
        scoped(c,cases,id)
        return [dict(r) for r in c.execute(select(reports.c.id,reports.c.sha256,reports.c.created,reports.c.run_id).join(runs).where(runs.c.case_id==id).order_by(reports.c.created.desc())).mappings()]
@app.get('/api/reports/{id}')
def frozen_report(id:str,u=Depends(current)):
    permit(u,'analyst','reviewer','admin')
    with engine.begin() as c:
        r=one(c,reports,id); run=one(c,runs,r['run_id']); scoped(c,cases,run['case_id'])
        if not r['pdf_hex']: raise HTTPException(409,'Legacy export has a snapshot/hash but no archived bytes; create a new report version')
        pdf=bytes.fromhex(r['pdf_hex'])
        if hashlib.sha256(pdf).hexdigest()!=r['sha256']: raise HTTPException(409,'Report integrity failure')
        log(c,u['id'],'frozen_report_download',{'report':id})
        return Response(pdf,media_type='application/pdf',headers={'Content-Disposition':f'attachment; filename="negotiation-report-{id}.pdf"'})

@app.get('/api/suppliers')
def get_suppliers(u=Depends(current)):
    with engine.connect() as c: return [json.loads(r) for r in c.execute(select(suppliers.c.payload).where(suppliers.c.tenant==TENANT)).scalars()]
@app.get('/api/dashboard')
def dashboard(u=Depends(current)):
    with engine.connect() as c:
        cc=c.execute(select(cases).where(cases.c.tenant==TENANT)).mappings().all(); results=[]; attention={x['id'] for x in cc if x['status'] in ['changes_requested','rejected']}
        for case in cc:
            r=c.execute(select(runs.c.result).where(runs.c.case_id==case['id']).order_by(runs.c.created.desc()).limit(1)).scalar()
            if r:
                parsed=json.loads(r); results.append(parsed)
                if parsed['status']=='insufficient_evidence': attention.add(case['id'])
        opportunities={}
        for result in results:
            if result['status']=='supported':
                currency=result['quote']['currency']; opportunities[currency]=opportunities.get(currency,decimal(0))+decimal(result.get('opportunity','0'))
        evals=c.execute(select(evaluations.c.results).where(evaluations.c.tenant==TENANT)).scalars().all()
        return {'cases':len(cc),'attention':len(attention),'pending':sum(x['status'] in ['ready_for_review','under_review'] for x in cc),'accepted':sum(x['status']=='accepted' for x in cc),'supported':sum(x['status']=='supported' for x in results),'insufficient':sum(x['status']=='insufficient_evidence' for x in results),'opportunity':money(next(iter(opportunities.values()))) if len(opportunities)==1 else ('0.00' if not opportunities else None),'opportunity_currency':next(iter(opportunities)) if len(opportunities)==1 else None,'opportunity_by_currency':{k:money(v) for k,v in opportunities.items()},'records':c.execute(select(func.count()).select_from(records).where(records.c.tenant==TENANT)).scalar(),'tests':sum(len(json.loads(e)) for e in evals if e),'recent':[dict(r) for r in c.execute(select(audit.c.seq,audit.c.actor,audit.c.event,audit.c.created).order_by(audit.c.seq.desc()).limit(8)).mappings()]}
class EvalIn(BaseModel): snapshot_id:str
@app.post('/api/evaluations')
def predict(body:EvalIn,u=Depends(current)):
    permit(u,'evaluator','admin')
    with engine.begin() as c:
        snap=verified_snapshot(c,body.snapshot_id); rule=active_rule(c); rows=json.loads(snap['payload']); tests=c.execute(select(holdouts.c.id,holdouts.c.quote).where(holdouts.c.tenant==TENANT)).all()
        if not tests: raise HTTPException(422,'No eligible holdout cases')
        holdout_ids={id for id,q in tests}; holdout_sources={json.loads(q)['source_ref'] for id,q in tests}; clean_rows=[r for r in rows if r['id'] not in holdout_ids and r['source_ref'] not in holdout_sources]; predictions=[{'id':id,'prediction':benchmark(json.loads(q),clean_rows,rule)} for id,q in tests]; id=uid(); rubric={'version':'demo-evaluation-v2','rule':rule,'excluded_holdout_reference_ids':[r['id'] for r in rows if r not in clean_rows],'band_coverage':'lower <= award <= upper','absolute_percentage_error':'abs(target-award)/award*100','business_thresholds':'pending BSES approval','temporal_cutoff':'strictly before quote date','prediction_sha256':digest(predictions)}
        c.execute(evaluations.insert().values(id=id,snapshot_id=body.snapshot_id,predictions=dumps(predictions),rubric=dumps(rubric),created=now(),tenant=TENANT)); log(c,u['id'],'predictions_locked',{'id':id,'sha256':digest(predictions)})
    return {'id':id,'predictions':predictions,'rubric':rubric}
@app.post('/api/evaluations/{id}/reveal')
def reveal(id:str,u=Depends(current)):
    permit(u,'evaluator','admin')
    with engine.begin() as c:
        e=scoped(c,evaluations,id)
        if e['results']: return json.loads(e['results'])
        pp=json.loads(e['predictions'])
        if digest(pp)!=json.loads(e['rubric'])['prediction_sha256']: raise HTTPException(409,'Prediction integrity failure')
        results=[]
        for p in pp:
            h=scoped(c,holdouts,p['id']); actual=decimal(h['outcome']); b=p['prediction']; ok=b['status']=='supported'; results.append({'id':p['id'],'award':str(actual),'status':b['status'],'covered':decimal(b['lower'])<=actual<=decimal(b['upper']) if ok else False,'absolute_percentage_error':money(abs(decimal(b['target'])-actual)/actual*100) if ok else None,'band_to_award_variance':money(max(decimal(b['lower'])-actual,actual-decimal(b['upper']),decimal(0))) if ok else None,'comparator_count':len(b['included']),'lineage_failures':sum(not x['source_ref'] for x in b['included']),'reviewer_finding':'Pending human evaluation'})
        c.execute(evaluations.update().where(evaluations.c.id==id).values(results=dumps(results))); log(c,u['id'],'holdout_revealed',{'id':id,'results':results})
        return results
class FindingIn(BaseModel):
    holdout_id:str
    comment:str=Field(min_length=5,max_length=5000)
@app.post('/api/evaluations/{id}/finding')
def finding(id:str,body:FindingIn,u=Depends(current)):
    permit(u,'evaluator','reviewer','admin')
    with engine.begin() as c:
        e=scoped(c,evaluations,id)
        if not e['results']: raise HTTPException(409,'Reveal outcomes before recording a finding')
        rr=json.loads(e['results']); match=next((r for r in rr if r['id']==body.holdout_id),None)
        if not match: raise HTTPException(404,'Unknown holdout')
        match['reviewer_finding']=body.comment
        c.execute(evaluations.update().where(evaluations.c.id==id).values(results=dumps(rr)))
        log(c,u['id'],'evaluation_finding',{'evaluation':id,**body.model_dump()})
    return {'recorded':True}

@app.get('/api/evaluations')
def list_evals(u=Depends(current)):
    permit(u,'evaluator','admin','reviewer')
    with engine.connect() as c: return [dict(r) for r in c.execute(select(evaluations).where(evaluations.c.tenant==TENANT)).mappings()]
@app.get('/api/audit')
def get_audit(u=Depends(current)):
    permit(u,'reviewer','admin')
    with engine.connect() as c:
        rows=[dict(r) for r in c.execute(select(audit).order_by(audit.c.seq)).mappings()]
    prev='0'*64; valid=True
    for r in rows:
        valid &= r['previous']==prev and r['hash']==hashlib.sha256((prev+r['actor']+r['event']+r['payload']+r['created']).encode()).hexdigest(); prev=r['hash']
    return {'chain_valid':bool(valid),'events':rows,'limitations':'Application hash chain; not externally anchored or privileged-admin tamper-proof.'}
@app.get('/api/config')
def config(u=Depends(current)):
    with engine.connect() as c: rr=[dict(r) for r in c.execute(select(rules)).mappings()]
    return {'rules':rr,'mode':'DEMO / SYNTHETIC only','llm':LLMConfig.from_env().public(),'integrations':[{'provider':p,'status':'disabled - licensed access, documentation and tested credentials required'} for p in ['Fastmarkets','S&P Global / Platts','D&B Direct+','LSEG World-Check One',"Moody’s Orbis",'CPPP / approved authority','BSES SAP / SRM']], 'retention':'Pending approved policy; no automatic deletion','roles':['analyst','reviewer','evaluator','admin']}
class RuleIn(BaseModel):
    version:str=Field(pattern=r'^[a-z0-9-]{3,60}$')
    minimum:int=Field(ge=3,le=100)
    lower_quantile:str
    upper_quantile:str
    target_quantile:str
    quantity_ratio_min:str='0.5'
    quantity_ratio_max:str='2'
    max_age_days:int|None=Field(default=None,ge=0)
    minimum_suppliers:int=Field(default=1,ge=1)
    iqr_multiplier:str='1.5'
@app.post('/api/rules')
def propose_rule(body:RuleIn,u=Depends(current)):
    permit(u,'admin'); r={**body.model_dump(),'outlier_policy':'retain','status':'pending BSES SME approval'}
    try:
        r=resolve_rule(r)
    except Exception: raise HTTPException(422,'Invalid quantiles')
    with engine.begin() as c:
        if c.execute(select(rules.c.id).where(rules.c.id==r['version'])).first(): raise HTTPException(409,'Version exists')
        c.execute(rules.insert().values(id=r['version'],payload=dumps(r),status='pending',created_by=u['id'])); log(c,u['id'],'rule_proposed',r)
    return r
@app.post('/api/rules/{id}/approve')
def approve_rule(id:str,u=Depends(current)):
    permit(u,'reviewer')
    with engine.begin() as c:
        r=one(c,rules,id)
        if r['status']!='pending' or r['created_by']==u['id']: raise HTTPException(409,'Independent pending-rule review required')
        c.execute(rules.update().where(rules.c.status.in_(['approved','demo_provisional'])).values(status='superseded')); c.execute(rules.update().where(rules.c.id==id).values(status='approved',reviewed_by=u['id'])); log(c,u['id'],'rule_approved',{'id':id})
    return {'status':'approved internally; BSES business approval remains external'}
@app.post('/api/demo/seed')
def seed(u=Depends(current)):
    permit(u,'admin')
    from .seed import seed_data
    with engine.begin() as c: return seed_data(c,u['id'],import_rows)
@app.middleware('http')
async def response_security(request,call_next):
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['Cache-Control']='no-store'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' blob: data:; object-src 'none'; frame-ancestors 'none'"
    return response

app.mount('/',StaticFiles(directory=str(Path(__file__).resolve().parents[2]/'frontend'),html=True),name='frontend')
