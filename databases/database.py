from observability.metrics.prometheus import database_connections_activating, database_connections_deactivating
from contextlib import asynccontextmanager
from core.settings import app_settings
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

IDENTITY_DATABASE_URL = app_settings.identity_database_url
if not IDENTITY_DATABASE_URL:
    raise RuntimeError(
        "IDENTITY_DATABASE_URL environment variable is required")

IDENTITY_DATABASE_MIGRATION_URL = app_settings.identity_database_migration_url
if not IDENTITY_DATABASE_MIGRATION_URL:
    raise RuntimeError(
        "IDENTITY_DATABASE_MIGRATION_URL environment variable is required")


parsed = urlparse(IDENTITY_DATABASE_URL)
query_params = parse_qs(parsed.query)
if 'LongAsMax' not in query_params:
    query_params['LongAsMax'] = ["Yes"]

parsed = parsed._replace(query=urlencode(query_params, doseq=True))
IDENTITY_DATABASE_URL = urlunparse(parsed)

engine = create_async_engine(
    IDENTITY_DATABASE_URL,
    pool_pre_ping=True,
    connect_args={
        "timeout": 30,
        "fast_executemany": False
    },
    use_setinputsizes=False
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False, autocommit=False, autoflush=False, class_=AsyncSession)
Base = declarative_base()


@asynccontextmanager
async def get_monitored_db_session():
    """
    Context manager for database sessions with connection monitoring.
    Usage in routers:

    def get_db():
        with get_monitored_db_session() as db:
            yield db
    """
    database_connections_activating()
    session = AsyncSessionLocal()
    try:
        yield session
        if session.new or session.dirty or session.deleted:
            await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
        database_connections_deactivating()
