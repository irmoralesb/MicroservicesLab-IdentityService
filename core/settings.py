# """
# Centralized settings module using Pydantic v2 BaseSettings
# 
# This module manages all application configuration, environment variables,
# and validation using Pydantic v2's BaseSettings with SettingsConfigDict.
# All configuration is validated on startup, providing "fail-fast" behavior.
# """

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from datetime import timedelta
from typing import Optional
import os
import uuid

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Pydantic v2 will automatically:
    - Read from environment variables matching field names (case-insensitive by default)
    - Validate types and constraints
    - Raise validation errors if required settings are missing or invalid
    """
    
    # Auth Configuration
    secret_token_key: str = Field(
        description="Secret key for JWT token signing. Required.",
        min_length=32,  # Enforce minimum key length for security
    )
    auth_algorithm: str = Field(
        min_length=3,
        description="JWT algorithm to use (e.g., HS256, RS256)",
    )
    token_time_delta_in_minutes: int = Field(
        description="Token expiration time in minutes. Must be positive.",
        gt=0,  # Greater than 0 - this is the fail-fast validation
    )
    
    # Database Configuration
    identity_database_url: str = Field(
        description="Database connection URL for application user",
    )
    identity_database_migration_url: str = Field(
        description="Database connection URL for migrations (admin user)",
    )
    
    # CORS Configuration
    cors_allow_origins: str = Field(
        default="*",
        description="CORS allowed origins (comma-separated or *)",
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Application log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    
    # Azure Monitor / Application Insights Configuration
    applicationinsights_connection_string: str = Field(
        default="",
        description="Application Insights connection string from Azure Portal",
    )
    azure_monitor_enabled: bool = Field(
        default=True,
        description="Enable Azure Monitor observability (Application Insights + Log Analytics)",
    )
    azure_monitor_sample_rate: float = Field(
        default=1.0,
        description="Trace sampling rate (0.0 to 1.0, where 1.0 means 100%)",
        ge=0.0,
        le=1.0,
    )
    azure_monitor_log_level: str = Field(
        default="INFO",
        description="Minimum log level exported to Azure Monitor (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )

    token_url: str = Field(
        description="This is the token URL, for instance /token"
    )

    max_failed_password_attempts: int = Field(
        default=3,
        description="Maximum failed password attempts"
    )

    lockout_duration_in_minutes: int =Field(
        default=60,
        description="Lockout duration after max number of failed password atteps was reached"
    )

    # Service Configuration
    service_id: uuid.UUID = Field(
        description="Id of this microservice for RBAC scoping and tracing"
    )
    
    @model_validator(mode='before')
    @classmethod
    def handle_azure_connection_strings(cls, data):
        """
        Handle Azure App Service connection string naming convention.
        Azure automatically prepends 'SQLCONNSTR_' to connection string settings.
        This validator aggressively checks OS environment for all required variables.
        """
        if not isinstance(data, dict):
            data = {}
        
        # Get all environment variables directly from OS
        import sys
        env_vars = dict(os.environ)
        
        # Create a case-insensitive lookup for environment variables
        env_lower = {k.lower(): (k, v) for k, v in env_vars.items()}
        
        # Debug output - print to stdout so it appears in Docker logs
        print("=" * 80, flush=True)
        print("DEBUG: All environment variables:", list(env_vars.keys()), flush=True)
        print("DEBUG: Current data dict keys:", list(data.keys()), flush=True)
        print("=" * 80, flush=True)
        
        # Mapping of field names to possible environment variable names
        field_mappings = {
            'identity_database_url': [
                'IDENTITY_DATABASE_URL',
                'SQLAZURECONNSTR_IDENTITY_DATABASE_URL',  # Azure SQL connection strings
                'SQLCONNSTR_IDENTITY_DATABASE_URL',
                'identity_database_url',
                'sqlazureconnstr_identity_database_url',
                'sqlconnstr_identity_database_url'
            ],
            'identity_database_migration_url': [
                'IDENTITY_DATABASE_MIGRATION_URL',
                'SQLAZURECONNSTR_IDENTITY_DATABASE_MIGRATION_URL',  # Azure SQL connection strings
                'SQLCONNSTR_IDENTITY_DATABASE_MIGRATION_URL',
                'identity_database_migration_url',
                'sqlazureconnstr_identity_database_migration_url',
                'sqlconnstr_identity_database_migration_url'
            ],
            'secret_token_key': [
                'SECRET_TOKEN_KEY',
                'secret_token_key',
                'SQLCONNSTR_SECRET_TOKEN_KEY',  # In case they put it in connection strings
                'sqlconnstr_secret_token_key'
            ]
        }
        
        # Try to find and set each required field
        for field_name, possible_names in field_mappings.items():
            if field_name not in data or not data.get(field_name):
                for env_name in possible_names:
                    if env_name in env_vars:
                        data[field_name] = env_vars[env_name]
                        print(f"DEBUG: Mapped {env_name} -> {field_name}", flush=True)
                        break
                    # Also try case-insensitive lookup
                    elif env_name.lower() in env_lower:
                        original_key, value = env_lower[env_name.lower()]
                        data[field_name] = value
                        print(f"DEBUG: Mapped {original_key} -> {field_name} (case-insensitive)", flush=True)
                        break
        
        print("DEBUG: Final data dict keys after mapping:", list(data.keys()), flush=True)
        print("=" * 80, flush=True)
        
        return data


    model_config = SettingsConfigDict(
        env_file=".env" if os.path.exists(".env") else None,  # Optional: load from .env file
        env_file_encoding="utf-8",
        case_sensitive=False,  # Allow both SECRET_TOKEN_KEY and secret_token_key
        extra="ignore",  # Ignore extra fields from env that aren't defined in Settings
    )
    
    @field_validator("token_time_delta_in_minutes", mode="before")
    @classmethod
    def validate_token_delta_not_default(cls, v):
        """
        Ensure token_time_delta_in_minutes is not the default "0".
        This replaces the old check: if _token_time_delta_in_minutes == "0"
        """
        if v == "0" or v == 0:
            raise ValueError("token_time_delta_in_minutes must be greater than 0")
        return v
    
    @property
    def token_expiry_delta(self) -> timedelta:
        """
        Convert token_time_delta_in_minutes (int) to timedelta object.
        This replaces the old:
        token_time_delta_in_minutes = timedelta(minutes=int(_token_time_delta_in_minutes))
        """
        return timedelta(minutes=self.token_time_delta_in_minutes)


# Create a single global settings instance
# This will validate all env vars on application startup (fail-fast)
app_settings: Settings = Settings() # type: ignore

# """
# USAGE IN auth.py:
# ================
# 
# 1. Import at top of auth.py:
#    from core.settings import settings
# 
# 2. Replace all the old configuration code with simple references:
#    - secret_token_key → settings.secret_token_key
#    - auth_algorithm → settings.auth_algorithm
#    - token_time_delta_in_minutes → settings.token_expiry_delta
#    - USER_ROLE_NAME → settings.default_user_role
# 
# 3. Remove all the old validation logic:
#    - Remove the _secret_token_key checks
#    - Remove the _auth_algorithm checks
#    - Remove the _token_time_delta_in_minutes checks
#    - Remove the manual timedelta creation
# 
# 4. The settings module will validate everything on app startup automatically.
#    If any required setting is missing or invalid, the app will fail to start
#    with a clear error message.
# 
# ENVIRONMENT VARIABLES TO SET:
# ==============================
# SECRET_TOKEN_KEY=your-secret-key-here-at-least-32-chars
# AUTH_ALGORITHM=HS256
# TOKEN_TIME_DELTA_IN_MINUTES=30
# DEFAULT_USER_ROLE=User  (optional, defaults to "User")
# 
# EXAMPLE .env file:
# ====================
# SECRET_TOKEN_KEY=super-secret-key-that-is-at-least-32-characters-long
# AUTH_ALGORITHM=HS256
# TOKEN_TIME_DELTA_IN_MINUTES=60
# DEFAULT_USER_ROLE=User
# """
