"""Fail-closed isolated Compose launcher. No shared .env or volumes by default."""
import argparse
import os
import re
import subprocess
from pathlib import Path
from dotenv import dotenv_values


def configuration(environment, env_file):
    if environment not in ('development', 'production'):
        raise ValueError('Invalid deployment environment')
    values = dotenv_values(env_file)
    expected = 'signaldesk_'+environment
    if values.get('APP_ENV') != environment or values.get('POSTGRES_DB') != expected or values.get('POSTGRES_USER') != expected:
        raise ValueError('Environment, database and database role must match the isolated target')
    if len(values.get('POSTGRES_PASSWORD', '')) < 24:
        raise ValueError('Use a distinct random database password of at least 24 characters')
    if values.get('APP_PORT') != ('8001' if environment == 'development' else '8000'):
        raise ValueError('Development and production must bind different application ports')
    if values.get('GRAFANA_PORT') != ('3001' if environment == 'development' else '3000'):
        raise ValueError('Development and production must bind different Grafana ports')
    if values.get('PROMETHEUS_CONFIG') != './observability/prometheus.'+environment+'.yaml':
        raise ValueError('Use the matching environment monitoring configuration')
    if environment == 'production':
        image = values.get('APP_IMAGE', '')
        if not re.fullmatch(r'ghcr.io/[a-z0-9_.-]+/[a-z0-9_.-]+@sha256:[a-f0-9]{64}', image):
            raise ValueError('Production requires an immutable image digest')
        if not values.get('FRONTEND_URL', '').startswith('https://'):
            raise ValueError('Production requires HTTPS ingress')
    # Compare the sibling configuration when present; never print credentials.
    other = Path(env_file).parent / ('.env.production' if environment == 'development' else '.env.development')
    if other.exists():
        sibling = dotenv_values(other)
        for key in ('POSTGRES_PASSWORD', 'GOOGLE_CLIENT_SECRET', 'ALERT_WEBHOOK_TOKEN', 'GRAFANA_ADMIN_PASSWORD'):
            if values.get(key) and values.get(key) == sibling.get(key):
                raise ValueError('Development and production must not share '+key)
    return values


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('environment', choices=['development', 'production'])
    parser.add_argument('action', choices=['config', 'up', 'ps', 'logs', 'stop'])
    args = parser.parse_args()
    env_file = '.env.'+args.environment
    configuration(args.environment, env_file)
    command = ['docker', 'compose', '--env-file', env_file, '--project-name', 'signaldesk-'+args.environment, '-f', 'compose.yaml', '-f', 'compose.observability.yaml']
    actions = {'config': ['config', '--quiet'], 'up': ['up', '-d', '--no-build', '--wait', '--wait-timeout', '180'], 'ps': ['ps'], 'logs': ['logs', '--tail=100'], 'stop': ['stop']}
    # Avoid inherited shell credentials overriding the selected environment file.
    clean = {k: v for k, v in os.environ.items() if k not in dotenv_values(env_file) and k not in ('COMPOSE_PROJECT_NAME', 'COMPOSE_FILE')}
    subprocess.run(command+actions[args.action], env=clean, check=True)


if __name__ == '__main__':
    main()
