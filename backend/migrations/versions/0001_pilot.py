"""Initial restricted pilot schema. Do not edit after deployment."""
from alembic import op
from sqlalchemy import MetaData, Table, Column, String, Text, Integer, ForeignKey, UniqueConstraint
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
reports=Table('report_versions',m,Column('id',String,primary_key=True),Column('run_id',ForeignKey('benchmark_runs.id'),nullable=False),Column('sha256',String,nullable=False),Column('snapshot',Text,nullable=False),Column('created',String))
holdouts=Table('holdout_test_cases',m,Column('id',String,primary_key=True),Column('quote',Text,nullable=False),Column('outcome',String,nullable=False),Column('tenant',String,nullable=False))
evaluations=Table('evaluation_runs',m,Column('id',String,primary_key=True),Column('snapshot_id',ForeignKey('dataset_snapshots.id'),nullable=False),Column('predictions',Text,nullable=False),Column('rubric',Text,nullable=False),Column('results',Text),Column('created',String),Column('tenant',String,nullable=False))
suppliers=Table('supplier_performance_records',m,Column('id',String,primary_key=True),Column('payload',Text,nullable=False),Column('tenant',String,nullable=False))
audit=Table('audit_events',m,Column('seq',Integer,primary_key=True,autoincrement=True),Column('actor',String,nullable=False),Column('event',String,nullable=False),Column('payload',Text,nullable=False),Column('previous',String,nullable=False),Column('hash',String,nullable=False),Column('created',String,nullable=False))

revision='0001_pilot'
down_revision=None
branch_labels=None
depends_on=None
def upgrade(): m.create_all(op.get_bind())
def downgrade(): raise RuntimeError('Destructive downgrade disabled; restore a reviewed backup instead')
