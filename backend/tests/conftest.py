"""Set isolation before any application module imports, regardless of test order."""
import os,tempfile
from pathlib import Path
os.environ['DATABASE_URL']=os.getenv('TEST_DATABASE_URL') or 'sqlite:///'+str(Path(tempfile.mkdtemp(prefix='bses-tests-'))/'test.db')
os.environ['DEMO_PASSWORD']='test-only-strong-password'
os.environ['LLM_ENABLED']='false'
os.environ['LLM_CHAT_ENABLED']='false'
