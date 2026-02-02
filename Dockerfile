# Identity Service - production image for Ubuntu Server / docker-compose reuse.
# Build: docker build -t identity-service:latest .
# Run: pass IDENTITY_DATABASE_URL, SECRET_TOKEN_KEY, AUTH_ALGORITHM, TOKEN_TIME_DELTA_IN_MINUTES,
#      DEFAULT_USER_ROLE, TOKEN_URL (and optional Loki/Tempo/metrics) via env or docker-compose.
# Required env: IDENTITY_DATABASE_URL, IDENTITY_DATABASE_MIGRATION_URL, SECRET_TOKEN_KEY,
# AUTH_ALGORITHM, TOKEN_TIME_DELTA_IN_MINUTES, DEFAULT_USER_ROLE, TOKEN_URL.

FROM python:3.12-slim

WORKDIR /app

# Install system deps and Microsoft ODBC Driver 18 for SQL Server (required by pyodbc/aioodbc).
# python:3.12-slim is Debian Bookworm (12). Optional libgssapi-krb5-2 for debian-slim.
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && curl -sSL -o /tmp/packages-microsoft-prod.deb \
        "https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb" \
    && dpkg -i /tmp/packages-microsoft-prod.deb \
    && rm /tmp/packages-microsoft-prod.deb \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 unixodbc-dev libgssapi-krb5-2 \
    && apt-get purge -y curl \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code.
COPY . .

# Non-root user for production.
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
