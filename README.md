# MicroservicesLab-IdentityService

Identity microservice built with FastAPI and SQLAlchemy for authentication and authorization in a microservices architecture.

## Features

- 🔐 JWT-based authentication
- 👥 User management with role-based access control (RBAC)
- 🔑 Permission-based authorization
- 🏢 Service catalog management
- 📊 Built-in observability (Prometheus metrics, Loki logging, Tempo tracing)
- 🐳 Docker-ready for containerized deployment
- ☁️ Azure-ready with SQL Database support

## Documentation

### Development
- **Database Setup**: [infrastructure/databases/README.md](infrastructure/databases/README.md) - Database drivers, connection strings, async runtime details
- **Environment Configuration**: [.env.azure.template](.env.azure.template) - Environment variable template

### Deployment
- **Azure Deployment Guide**: [AZURE_DEPLOYMENT_GUIDE.md](AZURE_DEPLOYMENT_GUIDE.md) - Complete guide for deploying to Azure
- **Quick Reference**: [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - Quick reference card for common commands
- **Docker Build Script**: [docker-build-push.ps1](docker-build-push.ps1) - Automated Docker build and push
- **Migration Script**: [run-migration.ps1](run-migration.ps1) - Alembic migration helper for Azure SQL

## Quick Start

### Local Development

1. **Clone and setup virtual environment**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1  # Windows
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   # Copy and edit .env file with your settings
   cp .env.template .env
   ```

3. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

4. **Start the service**
   ```bash
   uvicorn main:app --reload --port 8001
   ```

5. **Access API documentation**
   - Swagger UI: http://localhost:8001/docs
   - ReDoc: http://localhost:8001/redoc

### Docker Deployment

#### Build and Push to Docker Hub
```powershell
# Using the automated script
.\docker-build-push.ps1 -DockerHubUsername "yourusername"

# Or manually
docker build -t yourusername/microserviceslab-identityservice:latest .
docker push yourusername/microserviceslab-identityservice:latest
```

#### Run Docker Container
```powershell
docker run -d -p 8001:8001 --env-file .env yourusername/microserviceslab-identityservice:latest
```

### Azure Deployment

See [AZURE_DEPLOYMENT_GUIDE.md](AZURE_DEPLOYMENT_GUIDE.md) for complete instructions.

**Quick overview:**
1. Build and push Docker image to Docker Hub
2. Create Azure SQL Database with separate users (migration_admin, app_user)
3. Run Alembic migrations against Azure SQL
4. Deploy to Azure App Service with environment variables

```powershell
# Build and push Docker image
.\docker-build-push.ps1 -DockerHubUsername "yourusername" -Version "1.0.0"

# Setup Azure environment configuration
cp .env.azure.template .env.azure
# Edit .env.azure with your Azure SQL connection strings

# Run migrations
.\run-migration.ps1

# Deploy to Azure (see full guide for Azure CLI commands)
```

## Environment Variables

### Required Variables
```env
SECRET_TOKEN_KEY=your-secret-key-at-least-32-characters-long
AUTH_ALGORITHM=HS256
TOKEN_TIME_DELTA_IN_MINUTES=60
DEFAULT_USER_ROLE=User
TOKEN_URL=/token
SERVICE_ID=00000000-0000-0000-0000-000000000001
IDENTITY_DATABASE_URL=your-database-connection-string
IDENTITY_DATABASE_MIGRATION_URL=your-migration-connection-string
CORS_ALLOW_ORIGINS=*
```

See [.env.azure.template](.env.azure.template) for a complete list of available configuration options.

## API Endpoints

### Authentication
- `POST /token` - Login and get JWT token
- `POST /api/v1/users` - Register new user
- `GET /api/v1/users/me` - Get current user profile

### User Management (Admin)
- `GET /api/v1/users` - List all users
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user

### Role Management
- `GET /api/v1/roles` - List all roles
- `POST /api/v1/roles` - Create new role
- `GET /api/v1/roles/{role_id}/permissions` - Get role permissions
- `POST /api/v1/roles/{role_id}/permissions` - Assign permission to role

### Permission Management
- `GET /api/v1/permissions` - List all permissions
- `POST /api/v1/permissions` - Create new permission

### Service Management
- `GET /api/v1/services` - List all services
- `POST /api/v1/services` - Register new service
- `GET /api/v1/users/{user_id}/services` - Get user's assigned services
- `POST /api/v1/users/{user_id}/services` - Assign service to user

### Monitoring
- `GET /metrics` - Prometheus metrics (if enabled)

## Technology Stack

- **Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0+ with async support
- **Database**: Microsoft SQL Server 2022 (via aioodbc + pyodbc)
- **Authentication**: JWT with PyJWT, Passlib + bcrypt
- **Migrations**: Alembic
- **Observability**: Prometheus, Loki, Tempo (OpenTelemetry)
- **Containerization**: Docker
- **Cloud Platform**: Azure (SQL Database, App Service)

## Project Structure

```
MicroservicesLab-IdentityService/
├── application/          # Application layer (routers, schemas, services)
│   ├── routers/         # FastAPI route handlers
│   ├── schemas/         # Pydantic models
│   └── services/        # Business logic
├── core/                # Core functionality (settings, security)
├── domain/              # Domain layer (entities, interfaces, exceptions)
├── infrastructure/      # Infrastructure layer (database, repositories)
│   ├── databases/       # Database configuration and models
│   ├── repositories/    # Data access layer
│   └── observability/   # Logging, metrics, tracing
├── alembic/             # Database migrations
├── main.py              # Application entry point
└── requirements.txt     # Python dependencies
```

## Development Best Practices

- Python 3.12+ with type hints
- SQLAlchemy 2.x with Mapped types and mapped_column
- UUID primary keys for all entities
- Async/await patterns for database operations
- Pydantic v2 for data validation
- Comprehensive error handling
- Structured logging
- Security-first approach (no hardcoded credentials)

## License

[MIT License](LICENSE)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Support

For issues, questions, or contributions, please open an issue in the GitHub repository.