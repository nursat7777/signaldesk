import os
from pathlib import Path
from dotenv import load_dotenv
from alembic import context
from backend.database import make_engine
from backend.models import Base

config = context.config
# Match runtime: explicit process environment takes precedence over project .env.
project_root = Path(config.config_file_name).resolve().parent if config.config_file_name else Path.cwd()
load_dotenv(project_root / ".env", override=False)
url = os.getenv('DATABASE_URL', config.get_main_option('sqlalchemy.url'))
if context.is_offline_mode():
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True, dialect_opts={'paramstyle': 'named'})
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = make_engine(url)
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=Base.metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
