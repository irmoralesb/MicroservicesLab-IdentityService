# MicroservicesLab-IdentityService

FastAPI-based identity microservice using SQLAlchemy 2.x with async sessions and SQL Server 2022 as the backing store.

## Database drivers

### pyodbc (sync driver, used for migrations)
- Best compatibility with SQL Server features; leveraged by Alembic through `IDENTITY_DATABASE_MIGRATION_URL`.
- SQLAlchemy URL example (SQL Server 2022, ODBC Driver 18):

```bash
mssql+pyodbc://<username>:<password>@<host>:1433/<database>?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes&LongAsMax=Yes
```

### aioodbc (async driver, optional runtime)
- Async DBAPI built on top of pyodbc; use with `create_async_engine` by switching the scheme to `mssql+aioodbc`.
- SQLAlchemy async URL example:

```bash
mssql+aioodbc://<username>:<password>@<host>:1433/<database>?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=yes&timeout=30&LongAsMax=Yes
```

## Current database implementation
- Runtime uses SQLAlchemy async engine with the `IDENTITY_DATABASE_URL` URL and automatically injects `LongAsMax=Yes` to preserve `MAX` semantics when pyodbc is the driver (see [databases/database.py](databases/database.py)).
- Engine opts into `pool_pre_ping` and a 30s timeout, and disables `fast_executemany`/`setinputsizes` to avoid driver quirks with SQL Server.
- Sessions are yielded by `get_monitored_db_session`, which tracks connection activation/deactivation metrics and commits when mutations are present.
- Alembic reads `IDENTITY_DATABASE_MIGRATION_URL` for migrations, keeping a separate sync-safe URL for schema changes.

## Async benefits in this service
- Non-blocking I/O keeps FastAPI workers responsive under concurrent requests.
- Connection pooling with health checks reduces transient failures from stale sockets.
- Awaitable sessions allow graceful rollbacks on errors while keeping event loop available for other requests.

## Environment setup
1. Copy `.env_template` to `.env` and fill in the values.
2. Ensure ODBC Driver 18 for SQL Server is installed and reachable from the host/container.

Required variables:

- `IDENTITY_DATABASE_URL` – async SQLAlchemy URL for application traffic (pyodbc or aioodbc).
- `IDENTITY_DATABASE_MIGRATION_URL` – sync SQLAlchemy URL for Alembic migrations.
- `LOG_LEVEL` – logging level (e.g., INFO, DEBUG).
- `CORS_ALLOW_ORIGINS` – comma-separated origins for CORS (e.g., https://app.example.com,https://admin.example.com).
- `METRICS_ENABLED` – enable Prometheus metrics (`true`/`false`).
- `METRICS_ENDPOINT` – path where metrics are exposed (default `/metrics`).