from monitoring.metrics import database_connections_activating, database_connections_deactivating
from contextlib import contextmanager
import os
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

IDENTITY_DATABASE_URL = os.getenv("IDENTITY_DATABASE_URL")
if not IDENTITY_DATABASE_URL:
    raise RuntimeError(
        "IDENTITY_DATABASE_URL environment variable is required")

IDENTITY_DATABASE_MIGRATION_URL = os.getenv("IDENTITY_DATABASE_MIGRATION_URL")
if not IDENTITY_DATABASE_MIGRATION_URL:
    raise RuntimeError(
        "IDENTITY_DATABASE_MIGRATION_URL environment variable is required")


parsed = urlparse(IDENTITY_DATABASE_URL)
query_params = parse_qs(parsed.query)
if 'LongAsMax' not in query_params:
    query_params['LongAsMax'] = ["Yes"]

parsed = parsed._replace(query=urlencode(query_params, doseq=True))
IDENTITY_DATABASE_URL = urlunparse(parsed)

engine = create_engine(
    IDENTITY_DATABASE_URL,
    pool_pre_ping=True,
    connect_args={
        "timeout": 30,
        "fast_executemany": False
    },
    use_setinputsizes=False
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

@contextmanager
def get_monitored_db_session():
    """
    Context manager for database sessions with connection monitoring.
    Usage in routers:

    def get_db():
        with get_monitored_db_session() as db:
            yield db
    """
    database_connections_activating()
    session = SessionLocal()
    try:
        yield session
        if session.new or session.dirty or session.deleted:
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
        database_connections_deactivating()
