from sqlalchemy import create_engine, event

def normalize_url(url):
    # Managed providers commonly return postgres://; explicitly select psycopg 3.
    if url.startswith(('postgres://', 'postgresql://')):
        return 'postgresql+psycopg://' + url.split('://', 1)[1]
    return url

def make_engine(url):
    url = normalize_url(url)
    engine = create_engine(url, connect_args={'check_same_thread': False, 'timeout': 30} if url.startswith('sqlite:') else {})
    if engine.dialect.name == 'sqlite':
        @event.listens_for(engine, 'connect')
        def enable_fk(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute('PRAGMA foreign_keys=ON')
            cursor.close()
    return engine
