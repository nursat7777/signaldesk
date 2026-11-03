from backend.database import normalize_url

def test_managed_provider_urls_select_psycopg():
    assert normalize_url('postgres://u:p@db/name') == 'postgresql+psycopg://u:p@db/name'
    assert normalize_url('postgresql://u:p@db/name') == 'postgresql+psycopg://u:p@db/name'
    assert normalize_url('sqlite:///legacy.sqlite3') == 'sqlite:///legacy.sqlite3'
