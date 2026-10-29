"""Create a private local demo secret if missing; launch only on loopback."""
import os,secrets,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1];os.chdir(root)
p=root/'.env'
if not p.exists():
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as f: f.write('DEMO_PASSWORD='+secrets.token_urlsafe(24)+'\n')
for line in p.read_text().splitlines():
    if line and not line.startswith('#') and '=' in line:
        k,v=line.split('=',1);os.environ.setdefault(k,v)
if not os.environ.get('DEMO_PASSWORD'): raise SystemExit('Set DEMO_PASSWORD in .env')
(root/'data').mkdir(exist_ok=True)
subprocess.run([str(root/'.venv/bin/alembic'),'upgrade','head'],check=True)
print('Restricted pilot: http://127.0.0.1:8000 | user: admin | password stored privately in .env',flush=True)
os.execv(str(root/'.venv/bin/uvicorn'),['uvicorn','backend.app.main:app','--host','127.0.0.1','--port','8000'])
