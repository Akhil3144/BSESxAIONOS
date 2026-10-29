import os, json, hashlib
from datetime import datetime, timezone
from sqlalchemy import create_engine, event, MetaData, Table, Column, String, Text, Integer, ForeignKey, UniqueConstraint, select
from sqlalchemy.pool import StaticPool
DB_URL=os.getenv('DATABASE_URL','sqlite:///./data/app.db')
if DB_URL.startswith('sqlite:///'):
    os.makedirs(os.path.dirname(DB_URL[10:]) or '.',exist_ok=True)
engine=create_engine(DB_URL,connect_args={'check_same_thread':False} if DB_URL.startswith('sqlite') else {})
if DB_URL.startswith('sqlite'):
    @event.listens_for(engine,'connect')
    def fk(conn,record):
        conn.isolation_level=None
        conn.execute('PRAGMA foreign_keys=ON')
    @event.listens_for(engine,'begin')
    def serialize_sqlite_transaction(conn):
        # Reserve the writer lock before reading an audit predecessor; avoids hash-chain forks.
        conn.exec_driver_sql('BEGIN IMMEDIATE')
m=MetaData()
users=Table('users',m,Column('id',String,primary_key=True),Column('name',String,unique=True,nullable=False),Column('password',String,nullable=False),Column('role',String,nullable=False))
sessions=Table('sessions',m,Column('id',String,primary_key=True),Column('user_id',ForeignKey('users.id'),nullable=False),Column('expires',Integer,nullable=False))
batches=Table('import_batches',m,Column('id',String,primary_key=True),Column('name',String),Column('sha256',String,nullable=False),Column('raw',Text,nullable=False),Column('created',String),Column('tenant',String,nullable=False),Column('errors',Text,nullable=False))
records=Table('source_records',m,Column('id',String,primary_key=True),Column('batch_id',ForeignKey('import_batches.id'),nullable=False),Column('source_id',String,nullable=False),Column('payload',Text,nullable=False),Column('tenant',String,nullable=False),UniqueConstraint('tenant','source_id'))
snapshots=Table('dataset_snapshots',m,Column('id',String,primary_key=True),Column('payload',Text,nullable=False),Column('sha256',String,nullable=False),Column('created',String),Column('tenant',String,nullable=False))
rules=Table('benchmark_rules',m,Column('id',String,primary_key=True),Column('payload',Text,nullable=False),Column('status',String,nullable=False),Column('created_by',ForeignKey('users.id')),Column('reviewed_by',ForeignKey('users.id')))
cases=Table('negotiation_cases',m,Column('id',String,primary_key=True),Column('title',String,nullable=False),Column('quote',Text,nullable=False),Column('snapshot_id',ForeignKey('dataset_snapshots.id'),nullable=False),Column('status',String,nullable=False),Column('tenant',String,nullable=False),Column('created',String))
runs=Table('benchmark_runs',m,Column('id',String,primary_key=True),Column('case_id',ForeignKey('negotiation_cases.id'),nullable=False),Column('result',Text,nullable=False),Column('sha256',String,nullable=False),Column('created',String),Column('rule_id',ForeignKey('benchmark_rules.id'),nullable=False))
reviews=Table('review_actions',m,Column('id',String,primary_key=True),Column('case_id',ForeignKey('negotiation_cases.id'),nullable=False),Column('run_id',ForeignKey('benchmark_runs.id'),nullable=False),Column('actor',ForeignKey('users.id'),nullable=False),Column('action',String),Column('comment',Text),Column('created',String))
reports=Table('report_versions',m,Column('id',String,primary_key=True),Column('pdf_hex',Text),Column('run_id',ForeignKey('benchmark_runs.id'),nullable=False),Column('sha256',String,nullable=False),Column('snapshot',Text,nullable=False),Column('created',String))
holdouts=Table('holdout_test_cases',m,Column('id',String,primary_key=True),Column('quote',Text,nullable=False),Column('outcome',String,nullable=False),Column('tenant',String,nullable=False))
evaluations=Table('evaluation_runs',m,Column('id',String,primary_key=True),Column('snapshot_id',ForeignKey('dataset_snapshots.id'),nullable=False),Column('predictions',Text,nullable=False),Column('rubric',Text,nullable=False),Column('results',Text),Column('created',String),Column('tenant',String,nullable=False))
suppliers=Table('supplier_performance_records',m,Column('id',String,primary_key=True),Column('payload',Text,nullable=False),Column('tenant',String,nullable=False))
audit=Table('audit_events',m,Column('seq',Integer,primary_key=True,autoincrement=True),Column('actor',String,nullable=False),Column('event',String,nullable=False),Column('payload',Text,nullable=False),Column('previous',String,nullable=False),Column('hash',String,nullable=False),Column('created',String,nullable=False))
def now(): return datetime.now(timezone.utc).isoformat()
def dumps(x): return json.dumps(x,sort_keys=True,default=str)
def log(conn,actor,event_name,payload):
    # Serialize audit predecessors on PostgreSQL; SQLite uses explicit BEGIN IMMEDIATE.
    if engine.dialect.name=='postgresql': conn.exec_driver_sql('LOCK TABLE audit_events IN EXCLUSIVE MODE')
    prev=conn.execute(select(audit.c.hash).order_by(audit.c.seq.desc()).limit(1)).scalar() or '0'*64
    stamp=now(); body=dumps(payload); h=hashlib.sha256((prev+actor+event_name+body+stamp).encode()).hexdigest()
    conn.execute(audit.insert().values(actor=actor,event=event_name,payload=body,previous=prev,hash=h,created=stamp))
def initialize():
    m.create_all(engine)
