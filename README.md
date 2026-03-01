# MicroservicesLab-IdentityService

Identity microservice built with FastAPI and SQLAlchemy.

## Documentation
- For database drivers, connection strings, async runtime details, and environment variables see [databases/README.md](databases/README.md).

## Azure Web App

To run this service on Azure Web App for Containers using the Docker image:

1. **Port**: The container **listens on port 80 by default**, which matches Azure's default. Do **not** set `WEBSITES_PORT` unless you need a different port. If you previously had `WEBSITES_PORT=8000`, **remove it** so the app uses port 80 and Azure can reach it.

2. **Required application settings** (all must be set in Azure; no `.env` is copied into the image):
   - `IDENTITY_DATABASE_URL` – Async connection string (e.g. `mssql+aioodbc://...?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&...`)
   - `IDENTITY_DATABASE_MIGRATION_URL` – Same format, for Alembic migrations
   - If you use Azure **Connection strings** instead of Application settings, name them exactly **`IDENTITY_DATABASE_URL`** and **`IDENTITY_DATABASE_MIGRATION_URL`** (or `IdentityDatabaseUrl` / `IdentityDatabaseMigrationUrl`). The app reads both the standard names and Azure’s prefixed names (`SQLCONNSTR_*`, `SQLAZURECONNSTR_*`, `CUSTOMCONNSTR_*`).
   - `SECRET_TOKEN_KEY` – JWT secret (min 32 chars)
   - `AUTH_ALGORITHM` – e.g. `HS256`
   - `TOKEN_TIME_DELTA_IN_MINUTES` – Integer > 0
   - `DEFAULT_USER_ROLE` – e.g. `User`
   - `TOKEN_URL` – e.g. `/token`
   - `SERVICE_ID` – UUID for this service (RBAC/tracing)

3. **Optional for Azure**: `LOKI_ENABLED=false`, `METRICS_ENABLED=false`, `TRACING_ENABLED=false` (Tempo/Loki/Prometheus are disabled by default), `CORS_ALLOW_ORIGINS`, `LOG_LEVEL`.

4. **Health check**: In Configuration → General settings, set **Health check path** to `/health`.

5. **After deploy**: Open the main site (e.g. `https://your-app.azurewebsites.net`). You should get `/`, `/docs`, and `/health`. Do not use the SCM URL (`https://your-app.scm.azurewebsites.net`).