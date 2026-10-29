from pathlib import Path
import csv,json,sys,urllib.request,os,argparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
root=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--recalculate',action='store_true',help='Append new engine results for draft demo cases before exporting');args=parser.parse_args()
password=dict(l.split('=',1) for l in (root/'.env').read_text().splitlines() if '=' in l)['DEMO_PASSWORD']
def call(path,body=None,token=None):
    req=urllib.request.Request('http://127.0.0.1:8000/api'+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json',**({'Authorization':'Bearer '+token} if token else {})})
    return urllib.request.urlopen(req).read()
token=json.loads(call('/login',{'username':'admin','password':password}))['token'];call('/demo/seed',{},token)
cc=[c for c in json.loads(call('/cases',token=token)) if c['title'].startswith('DEMO / SYNTHETIC - 11 kV XLPE cable lot')];(root/'output/pdf').mkdir(parents=True,exist_ok=True)
for i,c in enumerate(cc[:5]):
    if args.recalculate and c['status'] in ['draft','changes_requested']:call('/cases/'+c['id']+'/run',{},token)
    (root/f'output/pdf/DEMO-negotiation-pack-{i+1}.pdf').write_bytes(call('/cases/'+c['id']+'/pack',token=token))
rows=json.loads(call('/records',token=token));rows=[{k:v for k,v in r.items() if k!='batch_id'} for r in rows if r['id'].startswith('DEMO-PO-')]
with (root/'demo-data/synthetic-procurement.csv').open('w') as f:
    writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader()
    for row in rows: writer.writerow({**row,'specification':json.dumps(row['specification'])})
(root/'docs/API_OPENAPI.json').write_bytes(urllib.request.urlopen('http://127.0.0.1:8000/openapi.json').read())
print('Exported five synthetic PDF packs, source CSV and generated OpenAPI contract.')
