"""Offline, transactional import. Stop writers and back up SQLite before running.

python -m scripts.import_sqlite /absolute/backup.sqlite3
Target: DATABASE_URL. Target must be migrated and contain no application rows.
Active sessions and pending OAuth transactions are deliberately invalidated.
"""
import argparse
import os
from pathlib import Path
from sqlalchemy import create_engine, func, select
from backend.database import make_engine
from backend.models import Base

TABLES = ('clients', 'users', 'campaigns', 'assignments', 'daily_metrics')

def import_sqlite(source_path, target_url):
    source_path = Path(source_path).resolve(strict=True)
    # mode=ro prevents creating or modifying the legacy database.
    source = create_engine(f'sqlite:///file:{source_path.as_posix()}?mode=ro&uri=true')
    target = make_engine(target_url)
    try:
        if target.dialect.name != 'postgresql':
            raise ValueError('Target must be PostgreSQL')
        with source.connect() as src, target.begin() as dst:
            # Prevent concurrent imports/writes while testing target emptiness.
            dst.exec_driver_sql('LOCK TABLE clients, users, campaigns, assignments, daily_metrics, sessions, oauth_transactions IN ACCESS EXCLUSIVE MODE')
            for table in Base.metadata.sorted_tables:
                if dst.scalar(select(func.count()).select_from(table)):
                    raise ValueError('Target is not empty; import aborted without changes')
            counts = {}
            for name in TABLES:
                table = Base.metadata.tables[name]
                rows = [dict(row) for row in src.execute(select(table)).mappings()]
                if rows:
                    dst.execute(table.insert(), rows)
                actual = [dict(row) for row in dst.execute(select(table)).mappings()]
                keys = [c.name for c in table.primary_key]
                order = lambda row: tuple(row[k] for k in keys)
                if sorted(rows, key=order) != sorted(actual, key=order):
                    raise RuntimeError(f'Value verification failed for {name}; rolled back')
                counts[name] = len(rows)
            return counts
    finally:
        source.dispose()
        target.dispose()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    args = parser.parse_args()
    print(import_sqlite(args.source, os.environ['DATABASE_URL']))
