docker run -d -p 8001:8001 `
  -e SECRET_TOKEN_KEY="GUID" `
  -e AUTH_ALGORITHM="HS256" `
  -e TOKEN_TIME_DELTA_IN_MINUTES="60" `
  -e DEFAULT_USER_ROLE="User" `
  -e TOKEN_URL="/token" `
  -e SERVICE_ID="GUID" `
  -e IDENTITY_DATABASE_URL="<connection-string>" `
  -e IDENTITY_DATABASE_MIGRATION_URL="<connection-string>" `
  username/microsvclab-identitysvc:latest