import os
from alembic import context
from sqlalchemy import create_engine
from backend.app.db import m
config=context.config
url=os.getenv('DATABASE_URL',config.get_main_option('sqlalchemy.url'))
if context.is_offline_mode():
    context.configure(url=url,target_metadata=m,literal_binds=True)
    with context.begin_transaction(): context.run_migrations()
else:
    with create_engine(url).connect() as conn:
        context.configure(connection=conn,target_metadata=m,render_as_batch=url.startswith('sqlite'))
        with context.begin_transaction(): context.run_migrations()
