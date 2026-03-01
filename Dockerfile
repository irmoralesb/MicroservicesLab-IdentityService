# Identity Service - production image for Ubuntu Server / docker-compose reuse.
# Build: docker build -t identity-service:latest .
# Run: pass IDENTITY_DATABASE_URL, SECRET_TOKEN_KEY, AUTH_ALGORITHM, TOKEN_TIME_DELTA_IN_MINUTES,
#      DEFAULT_USER_ROLE, TOKEN_URL (and optional Loki/Tempo/metrics) via env or docker-compose.
# Listens on port 80 by default (Azure default). Required env: IDENTITY_DATABASE_URL, IDENTITY_DATABASE_MIGRATION_URL,
# SECRET_TOKEN_KEY, AUTH_ALGORITHM, TOKEN_TIME_DELTA_IN_MINUTES, DEFAULT_USER_ROLE, TOKEN_URL, SERVICE_ID.

FROM python:3.12-slim

WORKDIR /app

# Temporary workaround: allow SHA1 so Microsoft's repo is accepted (Debian policy as of 2026-02-01)
RUN mkdir -p /etc/crypto-policies/back-ends \
    && printf '%s\n' '[hash_algorithms]' 'sha1 = "always"' '[asymmetric_algorithms]' 'rsa1024 = "always"' \
       > /etc/crypto-policies/back-ends/sequoia.config

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

# Listen on port 80 by default so Azure App Service (which forwards to 80 by default) reaches the app.
# Run as root so we can bind to port 80; Azure runs the container in an isolated environment.
# To use a different port, set WEBSITES_PORT in App Service (e.g. WEBSITES_PORT=8000).
EXPOSE 80

# Trust Azure's reverse proxy headers so /docs and redirects use correct URL (https, host).
CMD ["sh", "-c", "port=${WEBSITES_PORT:-${PORT:-80}} && echo \"Listening on port $port\" && exec uvicorn main:app --host 0.0.0.0 --port $port --proxy-headers --forwarded-allow-ips='*'"]
