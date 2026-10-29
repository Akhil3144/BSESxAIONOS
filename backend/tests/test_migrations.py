import os,subprocess,tempfile
from pathlib import Path
from sqlalchemy import create_engine,inspect,text

def test_alembic_fresh_and_repeat_upgrade():
    path=Path(tempfile.mkdtemp())/'migrated.db';env={**os.environ,'DATABASE_URL':'sqlite:///'+str(path)}
    for _ in range(2): subprocess.run(['.venv/bin/alembic','upgrade','head'],env=env,check=True,capture_output=True)
    engine=create_engine(env['DATABASE_URL']);inspector=inspect(engine);assert 'audit_events' in inspector.get_table_names();assert 'pdf_hex' in [x['name'] for x in inspector.get_columns('report_versions')]
    with engine.connect() as c: assert c.execute(text('SELECT version_num FROM alembic_version')).scalar()=='0002_report_archive'
