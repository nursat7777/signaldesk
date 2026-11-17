"""Create a restrictive, non-destructive PostgreSQL backup for isolated Compose."""
import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from .compose_environment import configuration


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('environment', choices=['development', 'production'])
    parser.add_argument('--directory', required=True)
    args = parser.parse_args()
    env_file = '.env.'+args.environment
    values = configuration(args.environment, env_file)
    directory = Path(args.directory).resolve()
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    target = directory/(args.environment+'-'+timestamp+'.dump')
    # Exclusive creation prevents replacing an existing backup.
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    clean = {k: v for k, v in os.environ.items() if k not in values and k not in ('COMPOSE_PROJECT_NAME', 'COMPOSE_FILE')}
    with os.fdopen(fd, 'wb') as output:
        subprocess.run(['docker', 'compose', '--env-file', env_file, '--project-name', 'signaldesk-'+args.environment, '-f', 'compose.yaml', 'exec', '-T', 'db', 'pg_dump', '--format=custom', '--username='+values['POSTGRES_USER'], '--dbname='+values['POSTGRES_DB']], stdout=output, env=clean, check=True)
    if target.stat().st_size < 5:
        raise RuntimeError('Backup is empty; do not deploy')
    digest = hashlib.file_digest(target.open('rb'), 'sha256').hexdigest()
    manifest = {'environment': args.environment, 'timestamp': timestamp, 'filename': target.name, 'sha256': digest, 'restore_verified': False}
    manifest_path = target.with_suffix('.json')
    manifest_fd = os.open(manifest_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(manifest_fd, 'w') as output:
        json.dump(manifest, output)
    print('Backup saved; verify restore in a separate disposable database before promotion.')


if __name__ == '__main__':
    main()
