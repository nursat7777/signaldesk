from pathlib import Path
import pytest
from scripts.compose_environment import configuration


def example(tmp_path, env):
    text = Path('.env.'+env+'.example').read_text().replace('POSTGRES_PASSWORD=','POSTGRES_PASSWORD='+env+'-random-disposable-password-123456').replace('REPLACE_WITH_VERIFIED_DIGEST','a'*64)
    path = tmp_path/('.env.'+env)
    path.write_text(text)
    return path


def test_distinct_database_ports_projects_and_secrets(tmp_path):
    dev, prod = example(tmp_path, 'development'), example(tmp_path, 'production')
    assert configuration('development', dev)['POSTGRES_DB'] != configuration('production', prod)['POSTGRES_DB']


@pytest.mark.parametrize('replacement', [('APP_ENV=production', 'APP_ENV=development'), ('APP_PORT=8000', 'APP_PORT=8001'), ('GRAFANA_PORT=3000', 'GRAFANA_PORT=3001'), ('POSTGRES_DB=signaldesk_production', 'POSTGRES_DB=signaldesk_development'), ('@sha256:'+'a'*64, ':latest'), ('https://YOUR_PRODUCTION_DOMAIN', 'http://YOUR_PRODUCTION_DOMAIN')])
def test_misconfiguration_fails_closed(tmp_path, replacement):
    path = example(tmp_path, 'production')
    path.write_text(path.read_text().replace(*replacement))
    with pytest.raises(ValueError):
        configuration('production', path)


def test_shared_password_rejected(tmp_path):
    dev, prod = example(tmp_path, 'development'), example(tmp_path, 'production')
    prod.write_text(prod.read_text().replace('production-random-disposable-password', 'development-random-disposable-password'))
    with pytest.raises(ValueError, match='share POSTGRES_PASSWORD'):
        configuration('production', prod)
