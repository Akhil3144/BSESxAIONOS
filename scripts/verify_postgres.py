"""Verify actual PostgreSQL in an isolated schema; never reset a user's database."""
import os,sys,json,subprocess,uuid,socket
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sqlalchemy import create_engine,text,inspect
from sqlalchemy.engine import make_url
root=Path(__file__).resolve().parents[1];os.chdir(root)
report={'verified':False,'tests_passed':False}
url=os.getenv('TEST_POSTGRES_URL')
if not url:
    ports={}
    for port in [5432,5433,15432]:
        try:
            with socket.create_connection(('127.0.0.1',port),timeout=.5):ports[str(port)]='listening'
        except OSError as e:ports[str(port)]=type(e).__name__
    report.update(status='blocked: TEST_POSTGRES_URL not configured',local_ports=ports,instructions='Provide an authorized PostgreSQL test connection in TEST_POSTGRES_URL; script creates an isolated test schema.')
    Path('docs/postgresql-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));raise SystemExit(2)
parsed=make_url(url)
if parsed.get_backend_name()!='postgresql':raise SystemExit('TEST_POSTGRES_URL must use PostgreSQL')
admin=create_engine(parsed,connect_args={'connect_timeout':5});schema='bses_verify_'+uuid.uuid4().hex
try:
    with admin.begin() as c:
        version=c.execute(text('SELECT version()')).scalar();c.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
    scoped=parsed.update_query_dict({'options':'-csearch_path='+schema})
    env={**os.environ,'DATABASE_URL':scoped.render_as_string(hide_password=False),'TEST_DATABASE_URL':scoped.render_as_string(hide_password=False),'LLM_ENABLED':'false'}
    for _ in range(2):subprocess.run([str(root/'.venv/bin/alembic'),'upgrade','head'],env=env,check=True,capture_output=True,text=True)
    db=create_engine(scoped)
    with db.connect() as c:
        assert c.execute(text('SELECT version_num FROM alembic_version')).scalar()=='0002_report_archive'
        assert 'benchmark_runs' in inspect(c).get_table_names()
        tx=c.begin_nested();c.execute(text("INSERT INTO users(id,name,password,role) VALUES ('rollback-probe','rollback-probe','fixture','analyst')"));assert c.execute(text("SELECT name FROM users WHERE id='rollback-probe'")).scalar()=='rollback-probe';tx.rollback();assert c.execute(text("SELECT name FROM users WHERE id='rollback-probe'")).scalar() is None
    run=subprocess.run([str(root/'.venv/bin/python'),'-m','pytest','backend/tests','-q'],env=env,text=True,capture_output=True)
    Path('docs/postgresql-test-run.txt').write_text(run.stdout+run.stderr)
    report.update(verified=run.returncode==0,tests_passed=run.returncode==0,status='passed' if run.returncode==0 else 'failed',server=version,migration='0002_report_archive',transaction_rollback=True,verification_scope='Migrations twice, all calculation/API tests, insert/read/rollback, case workflow, review persistence, report/evaluation/audit. Not production/load/HA certification.')
    print(run.stdout)
except Exception as e:
    report.update(status='failed',error_type=type(e).__name__)
finally:
    # This schema was created above by this process, with an unpredictable fixed-prefix name.
    try:
        with admin.begin() as c:c.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
    except Exception:report['cleanup']='manual cleanup of isolated verification schema required'
    admin.dispose();Path('docs/postgresql-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
raise SystemExit(0 if report['verified'] else 1)
