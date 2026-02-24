# Azure Deployment Guide - MicroservicesLab-IdentityService

This guide covers:
1. Building and pushing Docker image to Docker Hub
2. Setting up Azure SQL Database
3. Running Alembic migrations
4. Deploying to Azure App Service (Web App)

---

## 1. Build and Push Docker Image to Docker Hub

### Prerequisites
- Docker Desktop installed and running
- Docker Hub account created
- Logged in to Docker Hub CLI: `docker login`

### Step 1.1: Build the Docker Image

```powershell
# Navigate to the project directory
cd C:\Users\irmor\Projects\Microservices\MicroservicesLab-IdentityService

# Build the Docker image with your Docker Hub username
docker build -t <your-dockerhub-username>/microserviceslab-identityservice:latest .

# Example:
docker build -t yourusername/microserviceslab-identityservice:latest .

# Optional: Build with a specific version tag
docker build -t yourusername/microserviceslab-identityservice:1.0.0 .
```

### Step 1.2: Test the Docker Image Locally (Optional but Recommended)

```powershell
# Create a test .env file or use environment variables
docker run -d -p 8001:8001 `
  -e SECRET_TOKEN_KEY="your-secret-key-at-least-32-chars-long" `
  -e AUTH_ALGORITHM="HS256" `
  -e TOKEN_TIME_DELTA_IN_MINUTES="60" `
  -e DEFAULT_USER_ROLE="User" `
  -e TOKEN_URL="/token" `
  -e SERVICE_ID="00000000-0000-0000-0000-000000000001" `
  -e IDENTITY_DATABASE_URL="mssql+aioodbc://dbuser:password@host:1433/dbname?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no" `
  -e IDENTITY_DATABASE_MIGRATION_URL="mssql+aioodbc://adminuser:password@host:1433/dbname?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no" `
  yourusername/microserviceslab-identityservice:latest

# Test the API
curl http://localhost:8001/docs

# Stop the container when done testing
docker ps  # Get container ID
docker stop <container-id>
```

### Step 1.3: Push to Docker Hub

```powershell
# Push the latest tag
docker push yourusername/microserviceslab-identityservice:latest

# If you created a version tag, push it too
docker push yourusername/microserviceslab-identityservice:1.0.0
```

### Step 1.4: Verify Upload

Visit Docker Hub: `https://hub.docker.com/r/yourusername/microserviceslab-identityservice`

---

## 2. Azure SQL Database Setup - Best Practices

### Step 2.1: Create Azure SQL Database

**Option A: Using Azure Portal (Recommended for first-time setup)**

1. Navigate to Azure Portal (https://portal.azure.com)
2. Click "Create a resource" > "Databases" > "SQL Database"
3. Configure the database:
   - **Subscription**: Select your subscription
   - **Resource Group**: Create new or use existing
   - **Database name**: `identityservice-db` (or your preferred name)
   - **Server**: Create new server:
     - **Server name**: `microserviceslab-sql-server` (must be globally unique)
     - **Location**: Choose closest to your users
     - **Authentication**: SQL authentication
     - **Server admin login**: `sqladmin`
     - **Password**: Use a strong password (store securely in Azure Key Vault)
   - **Compute + storage**: 
     - For production: Standard S0 or higher
     - For development: Basic (cheaper) or use serverless
   - **Backup storage redundancy**: Geo-redundant (production) or Local (dev)
4. Click "Review + create" > "Create"

**Option B: Using Azure CLI**

```bash
# Set variables
RESOURCE_GROUP="microserviceslab-rg"
LOCATION="eastus"
SQL_SERVER="microserviceslab-sql-server"
DATABASE_NAME="identityservice-db"
ADMIN_USER="sqladmin"
ADMIN_PASSWORD="YourStrongPassword123!"

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create SQL Server
az sql server create \
  --name $SQL_SERVER \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION \
  --admin-user $ADMIN_USER \
  --admin-password $ADMIN_PASSWORD

# Create database
az sql db create \
  --resource-group $RESOURCE_GROUP \
  --server $SQL_SERVER \
  --name $DATABASE_NAME \
  --service-objective S0 \
  --backup-storage-redundancy Local

# Configure firewall to allow Azure services
az sql server firewall-rule create \
  --resource-group $RESOURCE_GROUP \
  --server $SQL_SERVER \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

### Step 2.2: Configure Firewall Rules

**Important**: Add firewall rules to allow connections:

1. In Azure Portal, navigate to your SQL Server
2. Under "Security" > "Networking"
3. Add your IP address for local testing
4. Enable "Allow Azure services and resources to access this server" (for Web App)
5. Save changes

### Step 2.3: Create Database Users (Best Practice)

**Best Practice**: Use separate users for migrations (admin) and application (limited permissions)

Connect to your Azure SQL Database using SQL Server Management Studio (SSMS), Azure Data Studio, or the Azure Portal Query Editor:

```sql
-- 1. Create the database (if not already created via portal)
-- Already created via Azure Portal or CLI

-- 2. Connect to the master database first, then create logins
USE master;
GO

-- Create migration admin login (for Alembic migrations)
CREATE LOGIN migration_admin WITH PASSWORD = 'StrongPassword123!Migration';
GO

-- Create application user login (limited permissions for runtime)
CREATE LOGIN app_user WITH PASSWORD = 'StrongPassword123!App';
GO

-- 3. Now connect to your identityservice-db database
USE identityservice_db;
GO

-- Create user for migration admin
CREATE USER migration_admin FOR LOGIN migration_admin;
GO

-- Grant migration admin full permissions (for schema changes)
ALTER ROLE db_owner ADD MEMBER migration_admin;
GO

-- Create user for application
CREATE USER app_user FOR LOGIN app_user;
GO

-- Grant application user limited permissions
ALTER ROLE db_datareader ADD MEMBER app_user;
ALTER ROLE db_datawriter ADD MEMBER app_user;
GO

-- Grant specific permissions application needs
GRANT EXECUTE TO app_user;  -- For stored procedures if needed
GRANT VIEW DEFINITION TO app_user;  -- To view schema
GO
```

### Step 2.4: Get Connection Strings

Your connection strings will look like:

**Migration Connection String (admin user):**
```
mssql+aioodbc://migration_admin:StrongPassword123!Migration@microserviceslab-sql-server.database.windows.net:1433/identityservice-db?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no
```

**Application Connection String (app user):**
```
mssql+aioodbc://app_user:StrongPassword123!App@microserviceslab-sql-server.database.windows.net:1433/identityservice-db?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no
```

**Important Connection String Parameters:**
- `Encrypt=yes`: Required for Azure SQL
- `TrustServerCertificate=no`: Validates SSL certificate
- `LongAsMax=Yes`: (Will be added by alembic env.py automatically)

---

## 3. Running Alembic Migrations on Azure SQL Database

### Step 3.1: Local Migration Setup

Create a `.env.azure` file for Azure migrations (DO NOT commit this):

```env
# Azure SQL Database Configuration
IDENTITY_DATABASE_URL=mssql+aioodbc://app_user:StrongPassword123!App@microserviceslab-sql-server.database.windows.net:1433/identityservice-db?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no
IDENTITY_DATABASE_MIGRATION_URL=mssql+aioodbc://migration_admin:StrongPassword123!Migration@microserviceslab-sql-server.database.windows.net:1433/identityservice-db?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no

# Auth settings (needed but won't be used for migration)
SECRET_TOKEN_KEY=migration-key-at-least-32-characters-long
AUTH_ALGORITHM=HS256
TOKEN_TIME_DELTA_IN_MINUTES=60
DEFAULT_USER_ROLE=User
TOKEN_URL=/token
SERVICE_ID=00000000-0000-0000-0000-000000000001
```

### Step 3.2: Run Migrations from Local Machine

**Best Practice**: Run migrations from your local machine first, then automate via CI/CD

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Copy Azure environment file
Copy-Item .env.azure .env

# Run Alembic migrations
alembic upgrade head

# Verify migration
alembic current

# Restore original .env if needed
Copy-Item .env.local .env
```

### Step 3.3: Alternative - Run Migrations in Container

If you prefer to run migrations inside a container:

```powershell
# Build migration runner image (optional separate image)
docker run --rm `
  -e IDENTITY_DATABASE_MIGRATION_URL="your-migration-connection-string" `
  -e SECRET_TOKEN_KEY="temp-key" `
  -e AUTH_ALGORITHM="HS256" `
  -e TOKEN_TIME_DELTA_IN_MINUTES="60" `
  -e DEFAULT_USER_ROLE="User" `
  -e TOKEN_URL="/token" `
  -e SERVICE_ID="00000000-0000-0000-0000-000000000001" `
  yourusername/microserviceslab-identityservice:latest `
  alembic upgrade head
```

### Step 3.4: Migration Best Practices

✅ **DO:**
- Run migrations before deploying new application version
- Test migrations on a staging database first
- Use migration admin user with full permissions
- Back up database before running migrations
- Keep migration files in version control
- Review generated migrations before applying

❌ **DON'T:**
- Run migrations automatically on app startup in production
- Use application user for migrations (lacks permissions)
- Skip testing migrations in staging environment
- Modify existing migration files (create new ones)

---

## 4. Deploy to Azure App Service (Web App)

### Step 4.1: Create Azure App Service

**Using Azure Portal:**

1. Navigate to Azure Portal
2. Click "Create a resource" > "Web App"
3. Configure:
   - **Subscription**: Your subscription
   - **Resource Group**: Same as SQL Database
   - **Name**: `microserviceslab-identity` (must be globally unique)
   - **Publish**: Container
   - **Operating System**: Linux
   - **Region**: Same as SQL Database
   - **Pricing Plan**: Choose based on needs (B1 Basic for dev, P1V2+ for production)
4. Click "Next: Container"
5. Configure container:
   - **Image Source**: Docker Hub
   - **Access Type**: Public
   - **Image and tag**: `yourusername/microserviceslab-identityservice:latest`
   - **Startup Command**: (leave empty, uses CMD from Dockerfile)
6. Click "Review + create" > "Create"

**Using Azure CLI:**

```bash
# Variables
RESOURCE_GROUP="microserviceslab-rg"
LOCATION="eastus"
APP_SERVICE_PLAN="microserviceslab-plan"
WEB_APP_NAME="microserviceslab-identity"
DOCKER_IMAGE="yourusername/microserviceslab-identityservice:latest"

# Create App Service Plan
az appservice plan create \
  --name $APP_SERVICE_PLAN \
  --resource-group $RESOURCE_GROUP \
  --is-linux \
  --sku B1

# Create Web App with Docker container
az webapp create \
  --resource-group $RESOURCE_GROUP \
  --plan $APP_SERVICE_PLAN \
  --name $WEB_APP_NAME \
  --deployment-container-image-name $DOCKER_IMAGE
```

### Step 4.2: Configure Environment Variables

In Azure Portal:
1. Navigate to your Web App
2. Go to "Configuration" under "Settings"
3. Click "New application setting" and add each variable:

**Required Environment Variables:**

```
SECRET_TOKEN_KEY=your-production-secret-key-min-32-chars-store-in-keyvault
AUTH_ALGORITHM=HS256
TOKEN_TIME_DELTA_IN_MINUTES=60
DEFAULT_USER_ROLE=User
TOKEN_URL=/token
SERVICE_ID=<your-service-uuid>
IDENTITY_DATABASE_URL=mssql+aioodbc://app_user:password@server.database.windows.net:1433/dbname?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no
IDENTITY_DATABASE_MIGRATION_URL=mssql+aioodbc://migration_admin:password@server.database.windows.net:1433/dbname?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no
CORS_ALLOW_ORIGINS=https://your-frontend-domain.com
LOG_LEVEL=INFO
```

**Optional Environment Variables (if using observability):**

```
LOKI_ENABLED=true
LOKI_URL=http://your-loki-instance:3100
METRICS_ENABLED=true
TRACING_ENABLED=true
TEMPO_ENDPOINT=http://your-tempo-instance:4317
```

**Using Azure CLI:**

```bash
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --settings \
    SECRET_TOKEN_KEY="your-secret-key" \
    AUTH_ALGORITHM="HS256" \
    TOKEN_TIME_DELTA_IN_MINUTES="60" \
    DEFAULT_USER_ROLE="User" \
    TOKEN_URL="/token" \
    SERVICE_ID="00000000-0000-0000-0000-000000000001" \
    IDENTITY_DATABASE_URL="your-application-connection-string" \
    IDENTITY_DATABASE_MIGRATION_URL="your-migration-connection-string" \
    CORS_ALLOW_ORIGINS="*"
```

### Step 4.3: Configure Container Settings

```bash
# Enable container logging
az webapp log config \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --docker-container-logging filesystem

# Set port (if needed, default is 8001 as per Dockerfile)
az webapp config appsettings set \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --settings WEBSITES_PORT=8001
```

### Step 4.4: Enable Continuous Deployment (Optional)

Enable webhook for automatic deployment when Docker image updates:

```bash
az webapp deployment container config \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --enable-cd true
```

This provides a webhook URL to add to your Docker Hub repository settings.

### Step 4.5: Verify Deployment

```powershell
# Get the web app URL
az webapp show \
  --resource-group $RESOURCE_GROUP \
  --name $WEB_APP_NAME \
  --query defaultHostName -o tsv

# Test the API
curl https://microserviceslab-identity.azurewebsites.net/docs
```

---

## 5. Best Practices Summary

### Security Best Practices

1. **Use Azure Key Vault** for storing secrets (SECRET_TOKEN_KEY, DB passwords)
2. **Enable Managed Identity** for the Web App to access Key Vault
3. **Separate Users**: Use different SQL users for migrations vs application
4. **Least Privilege**: Application user should only have read/write, not schema modification
5. **SSL/TLS**: Always use `Encrypt=yes` for Azure SQL connections
6. **Firewall Rules**: Restrict database access to only necessary IP ranges
7. **Regular Password Rotation**: Change database passwords periodically

### Database Migration Best Practices

1. **Run migrations BEFORE deploying** new application code
2. **Use staging environment** to test migrations
3. **Backup before migrating** production database
4. **Version control** all migration files
5. **Never modify** existing migration files, create new ones
6. **Separate credentials** for migration admin vs app user
7. **CI/CD Integration**: Automate migrations in your deployment pipeline

### Monitoring Best Practices

1. **Enable Application Insights** in Azure Web App
2. **Configure log streaming** to view container logs
3. **Set up alerts** for errors and performance issues
4. **Monitor database metrics** (DTU/CPU usage, connections)
5. **Health check endpoint**: Consider adding `/health` endpoint
6. **Structured logging**: Your app already uses Loki (configure if available)

### Deployment Best Practices

1. **Use health checks**: Azure can restart unhealthy containers
2. **Configure auto-scaling** based on load
3. **Use deployment slots** for blue-green deployments
4. **Tag Docker images** with version numbers, not just `latest`
5. **Regular updates**: Keep base images and dependencies updated
6. **Monitor costs**: Review Azure cost analysis regularly

---

## 6. Troubleshooting

### Common Issues

**Issue**: Container fails to start
- Check logs: `az webapp log tail --resource-group $RESOURCE_GROUP --name $WEB_APP_NAME`
- Verify all required environment variables are set
- Check database connectivity

**Issue**: Database connection fails
- Verify firewall rules allow Web App IP
- Check connection string format (must include `Encrypt=yes`)
- Ensure database users exist with correct permissions

**Issue**: Migrations fail
- Verify migration admin user has db_owner role
- Check if migration was already applied: `alembic current`
- Review migration file for issues

**Issue**: Port binding issues
- Ensure EXPOSE 8001 in Dockerfile matches your app port
- Set WEBSITES_PORT=8001 in App Settings if needed

---

## 7. Next Steps

1. ✅ Set up Azure Key Vault for secrets management
2. ✅ Configure Application Insights for monitoring
3. ✅ Set up CI/CD pipeline (Azure DevOps or GitHub Actions)
4. ✅ Create staging environment for testing
5. ✅ Configure auto-scaling rules
6. ✅ Set up backup and disaster recovery
7. ✅ Document API endpoints for frontend integration

---

## Appendix: Useful Commands

```powershell
# View Web App logs
az webapp log tail --resource-group microserviceslab-rg --name microserviceslab-identity

# Restart Web App
az webapp restart --resource-group microserviceslab-rg --name microserviceslab-identity

# Update Docker image
az webapp config container set \
  --resource-group microserviceslab-rg \
  --name microserviceslab-identity \
  --docker-custom-image-name yourusername/microserviceslab-identityservice:1.0.1

# SSH into container (for debugging)
az webapp ssh --resource-group microserviceslab-rg --name microserviceslab-identity

# View database firewall rules
az sql server firewall-rule list \
  --resource-group microserviceslab-rg \
  --server microserviceslab-sql-server
```

---

**Created**: February 22, 2026
**Last Updated**: February 22, 2026
