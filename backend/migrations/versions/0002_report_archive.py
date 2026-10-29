"""Retain byte-identical exported reports for authorized historical retrieval."""
from alembic import op
import sqlalchemy as sa
revision='0002_report_archive'
down_revision='0001_pilot'
branch_labels=None
depends_on=None
def upgrade(): op.add_column('report_versions',sa.Column('pdf_hex',sa.Text(),nullable=True))
def downgrade(): raise RuntimeError('Destructive downgrade disabled; restore a reviewed backup instead')
