import random, json, uuid
from datetime import date,timedelta
from sqlalchemy import select
from .db import *
from .engine import digest, benchmark, DEFAULT_RULE
from .agents import NegotiationIntelligenceAgent

def sample(id='QUOTE-DEMO-01',price='620',day='2025-06-01'):
    return {'id':id,'material':'CABLE-XLPE-11KV-95','specification':{'voltage_kv':11,'conductor':'Al','area_mm2':95,'cores':3,'insulation':'XLPE'},'supplier':'DEMO Supplier A','date':day,'quantity':'1000','uom':'m','currency':'INR','unit_price':price,'tax':'exclusive GST','payment_days':30,'location':'Delhi','delivery':'delivered','source_ref':id,'synthetic':True}
def seed_data(c,actor,importer):
    if c.execute(select(records.c.id).where(records.c.tenant=='demo')).first(): return {'status':'already seeded; no records changed'}
    rng=random.Random(20261029); rows=[]
    for i in range(40):
        r=sample(f'DEMO-PO-{i+1:03}',str(450+rng.randrange(90)),(date(2023,1,1)+timedelta(days=i*15)).isoformat()); r['supplier']=f'DEMO Supplier {chr(65+i%4)}'; r['quantity']=str(800+i%5*100); r['source_type']='purchase_order' if i%2 else 'tender'
        if i%11==0: r['specification']={**r['specification'],'area_mm2':120}
        if i%13==0: r['payment_days']=60
        if i%7==0: r['unit_price']=str(int(r['unit_price'])*1000); r['uom']='km'; r['quantity']='1'
        rows.append(r)
    importer(c,rows,'DEMO-synthetic-evidence.json',dumps(rows).encode(),actor)
    sid=str(uuid.uuid4()); c.execute(snapshots.insert().values(id=sid,payload=dumps(rows),sha256=digest(rows),created=now(),tenant='demo'))
    for i in range(4):
        p={'supplier':f'DEMO Supplier {chr(65+i)}','legal_name':f'Synthetic Cable Company {i+1} (fictional)','record_type':'internal_performance','on_time_deliveries':17+i,'deliveries':20,'quality_issues':i%2,'source_ref':f'DEMO-PERF-{i+1}','observed':'2025-01-01','official_debarment':'Unavailable; no legal finding inferred','synthetic':True}
        c.execute(suppliers.insert().values(id=str(uuid.uuid4()),payload=dumps(p),tenant='demo'))
    for i in range(5):
        q=sample(f'DEMO-QUOTE-{i+1}',str(590+i*14)); id=str(uuid.uuid4()); c.execute(cases.insert().values(id=id,title=f'DEMO / SYNTHETIC - 11 kV XLPE cable lot {i+1}',quote=dumps(q),snapshot_id=sid,status='draft',tenant='demo',created=now())); result=NegotiationIntelligenceAgent().analyze(q,rows,[json.loads(p) for p in c.execute(select(suppliers.c.payload).where(suppliers.c.tenant=='demo')).scalars()]); c.execute(runs.insert().values(id=str(uuid.uuid4()),case_id=id,result=dumps(result),sha256=digest(result),created=now(),rule_id=DEFAULT_RULE['version']))
    for i in range(10):
        q=sample(f'DEMO-HOLDOUT-{i+1}',str(580+i*2),(date(2024,8,1)+timedelta(days=i*12)).isoformat()); c.execute(holdouts.insert().values(id=q['id'],quote=dumps(q),outcome=str(480+i*4 if i<8 else 650),tenant='demo'))
    log(c,actor,'demo_seed',{'records':40,'cases':5,'holdouts':10,'snapshot':sid})
    return {'records':40,'cases':5,'holdouts':10,'snapshot_id':sid,'synthetic':True}
