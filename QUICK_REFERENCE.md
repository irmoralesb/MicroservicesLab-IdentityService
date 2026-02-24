# Azure Deployment - Quick Reference Card

## 📦 1. Build and Push Docker Image

### Quick Start (Using PowerShell Script)
```powershell
# Build and push (you'll be prompted for confirmation)
.\docker-build-push.ps1 -DockerHubUsername "yourusername"

# Build and push with version tag
.\docker-build-push.ps1 -DockerHubUsername "yourusername" -Version "1.0.0"

# Build only (no push)
.\docker-build-push.ps1 -DockerHubUsername "yourusername" -SkipPush

# Build and test locally
.\docker-build-push.ps1 -DockerHubUsername "yourusername" -TestLocal
```

### Manual Commands
```powershell
# Build
docker build -t yourusername/microserviceslab-identityservice:latest .

# Test locally
docker run -d -p 8001:8001 --env-file .env yourusername/microserviceslab-identityservice:latest

# Push
docker push yourusername/microserviceslab-identityservice:latest
```

---

## 🗄️ 2. Azure SQL Database Setup

### Create Database (Azure CLI)
```bash
# Variables
RESOURCE_GROUP="microserviceslab-rg"
SQL_SERVER="microserviceslab-sql-server"
DATABASE_NAME="identityservice-db"

# Create SQL Server
az sql server create \
  --name $SQL_SERVER \
  --resource-group $RESOURCE_GROUP \
  --location eastus \
  --admin-user sqladmin \
  --admin-password "YourStrongPassword123!"

# Create Database
az sql db create \
  --resource-group $RESOURCE_GROUP \
  --server $SQL_SERVER \
  --name $DATABASE_NAME \
  --service-objective S0

# Enable Azure services access
az sql server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --server $SQL_SERVER \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### Create Database Users (SSMS/Azure Query Editor)
```sql
-- Connect to master database first
USE master;
GO

-- Create logins
CREATE LOGIN migration_admin WITH PASSWORD = 'StrongPassword123!';
CREATE LOGIN app_user WITH PASSWORD = 'StrongPassword456!';
GO

-- Connect to your database
USE identityservice_db;
GO

-- Create users and assign roles
CREATE USER migration_admin FOR LOGIN migration_admin;
ALTER ROLE db_owner ADD MEMBER migration_admin;

CREATE USER app_user FOR LOGIN app_user;
ALTER ROLE db_datareader ADD MEMBER app_user;
ALTER ROLE db_datawriter ADD MEMBER app_user;
GRANT EXECUTE TO app_user;
GO
```

### Connection Strings
```
Migration (Admin):
mssql+aioodbc://migration_admin:password@server.database.windows.net:1433/dbname?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no

Application (Limited):
mssql+aioodbc://app_user:password@server.database.windows.net:1433/dbname?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no
```

---

## 🔄 3. Run Alembic Migrations

### Using PowerShell Script
```powershell
# Create .env.azure file first with connection strings

# Run migration (will prompt for confirmation)
.\run-migration.ps1

# Check current status
.\run-migration.ps1 -Command current

# View migration history
.\run-migration.ps1 -Command history

# Dry run (no changes)
.\run-migration.ps1 -DryRun
```

### Manual Commands
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Copy Azure environment
Copy-Item .env.azure .env

# Run migrations
alembic upgrade head

# Check status
alembic current

# Restore original .env
Copy-Item .env.local .env
```

---

## 🌐 4. Deploy to Azure Web App

### Create Web App (Azure CLI)
```bash
# Variables
RESOURCE_GROUP="microserviceslab-rg"
APP_SERVICE_PLAN="microserviceslab-plan"
WEB_APP_NAME="microserviceslab-identity"

# Create App Service Plan
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --is-linux \
  --sku B1

# Create Web App
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $WEB_APP_NAME \
  --deployment-container-image-name yourusername/microserviceslab-identityservice:latest
```

### Configure Environment Variables
```bash
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --settings \
    SECRET_TOKEN_KEY="your-secret-key-min-32-chars" \
    AUTH_ALGORITHM="HS256" \
    TOKEN_TIME_DELTA_IN_MINUTES="60" \
    DEFAULT_USER_ROLE="User" \
    TOKEN_URL="/token" \
    SERVICE_ID="your-service-uuid" \
    IDENTITY_DATABASE_URL="your-app-connection-string" \
    IDENTITY_DATABASE_MIGRATION_URL="your-migration-connection-string" \
    CORS_ALLOW_ORIGINS="https://your-frontend.com" \
    LOG_LEVEL="INFO"
```

---

## 🔍 5. Monitoring & Troubleshooting

### View Logs
```bash
# Stream logs
az webapp log tail --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME

# Enable logging
az webapp log config \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --docker-container-logging filesystem
```

### Restart Web App
```bash
az webapp restart --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME
```

### Update Docker Image
```bash
az webapp config container set \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --docker-custom-image-name yourusername/microserviceslab-identityservice:1.0.1
```

---

## ✅ Deployment Checklist

### Before Deployment
- [ ] Docker image built and pushed to Docker Hub
- [ ] Azure SQL Database created
- [ ] Database users created (migration_admin, app_user)
- [ ] Firewall rules configured
- [ ] Connection strings tested
- [ ] Alembic migrations run successfully
- [ ] Environment variables prepared

### During Deployment
- [ ] Azure Web App created
- [ ] Environment variables configured
- [ ] Container settings verified
- [ ] Port settings correct (8001)
- [ ] CORS origins configured

### After Deployment
- [ ] Test API endpoint: https://yourapp.azurewebsites.net/docs
- [ ] Check logs for errors
- [ ] Verify database connectivity
- [ ] Test authentication flow
- [ ] Monitor performance
- [ ] Set up alerts

---

## 🔐 Required Environment Variables

```env
# Auth (Required)
SECRET_TOKEN_KEY=your-secret-key-at-least-32-characters-long
AUTH_ALGORITHM=HS256
TOKEN_TIME_DELTA_IN_MINUTES=60
DEFAULT_USER_ROLE=User
TOKEN_URL=/token
SERVICE_ID=00000000-0000-0000-0000-000000000001

# Database (Required)
IDENTITY_DATABASE_URL=mssql+aioodbc://app_user:pass@server.database.windows.net:1433/db?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no
IDENTITY_DATABASE_MIGRATION_URL=mssql+aioodbc://admin:pass@server.database.windows.net:1433/db?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no

# CORS (Required for frontend)
CORS_ALLOW_ORIGINS=https://your-frontend.com,https://app.yourdomain.com

# Logging (Optional)
LOG_LEVEL=INFO

# Observability (Optional - if using Loki/Tempo/Prometheus)
LOKI_ENABLED=false
METRICS_ENABLED=true
TRACING_ENABLED=false
```

---

## 📚 Additional Resources

- Full Guide: `AZURE_DEPLOYMENT_GUIDE.md`
- Docker Build Script: `docker-build-push.ps1`
- Migration Script: `run-migration.ps1`
- Azure Documentation: https://docs.microsoft.com/azure
- Docker Hub: https://hub.docker.com

---

## 🆘 Common Issues

**Container fails to start**
- Check logs: `az webapp log tail`
- Verify all required env vars are set
- Check database connectivity

**Database connection fails**
- Verify firewall rules
- Check connection string format
- Ensure `Encrypt=yes` is present

**Migrations fail**
- Verify migration_admin has db_owner role
- Check if already applied: `alembic current`
- Review alembic logs for errors

**Port binding issues**
- Set `WEBSITES_PORT=8001` in App Settings
- Verify Dockerfile EXPOSE 8001

---

**Last Updated**: February 22, 2026
