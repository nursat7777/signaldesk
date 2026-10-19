from sqlalchemy import create_engine, event

def make_engine(url):
    engine = create_engine(url, connect_args={'check_same_thread': False, 'timeout': 30} if url.startswith('sqlite:') else {})
    if engine.dialect.name == 'sqlite':
        @event.listens_for(engine, 'connect')
        def enable_fk(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute('PRAGMA foreign_keys=ON')
            cursor.close()
    return engine
