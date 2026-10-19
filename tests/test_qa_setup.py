"""Independent setup regression. All migration copies, config/env and DBs disposable."""
import os,shutil,subprocess,sys
from pathlib import Path

def test_alembic_loads_project_env_database_url(tmp_path):
 root=Path(__file__).resolve().parents[1]
 shutil.copytree(root/'backend/migrations',tmp_path/'migrations',ignore=shutil.ignore_patterns('__pycache__'))
 desired=tmp_path/'configured.sqlite3';fallback=tmp_path/'fallback.sqlite3'
 (tmp_path/'.env').write_text(f'DATABASE_URL=sqlite:///{desired}\n')
 config=tmp_path/'alembic.ini';config.write_text(f'[alembic]\nscript_location = {tmp_path}/migrations\nprepend_sys_path = {root}\npath_separator = os\nsqlalchemy.url = sqlite:///{fallback}\n')
 env={k:v for k,v in os.environ.items() if k!='DATABASE_URL'}
 result=subprocess.run([sys.executable,'-m','alembic','-c',str(config),'upgrade','head'],cwd=tmp_path,env=env,capture_output=True,text=True,timeout=20)
 assert result.returncode==0,result.stderr
 assert desired.exists(),'Migration ignored .env DATABASE_URL and did not create configured database'
 assert not fallback.exists(),'Migration used ini fallback despite .env DATABASE_URL'

def test_exported_database_url_precedes_dotenv(tmp_path):
 root=Path(__file__).resolve().parents[1];shutil.copytree(root/'backend/migrations',tmp_path/'migrations',ignore=shutil.ignore_patterns('__pycache__'))
 dotenv_db=tmp_path/'dotenv.sqlite3';explicit_db=tmp_path/'exported.sqlite3';fallback=tmp_path/'fallback.sqlite3'
 (tmp_path/'.env').write_text(f'DATABASE_URL=sqlite:///{dotenv_db}\n')
 config=tmp_path/'alembic.ini';config.write_text(f'[alembic]\nscript_location = {tmp_path}/migrations\nprepend_sys_path = {root}\npath_separator = os\nsqlalchemy.url = sqlite:///{fallback}\n')
 result=subprocess.run([sys.executable,'-m','alembic','-c',str(config),'upgrade','head'],cwd=tmp_path,env={**os.environ,'DATABASE_URL':f'sqlite:///{explicit_db}'},capture_output=True,text=True,timeout=20)
 assert result.returncode==0,result.stderr
 assert explicit_db.exists() and not dotenv_db.exists() and not fallback.exists()
