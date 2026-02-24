# Run Alembic Migrations Against Azure SQL Database
# This script helps run migrations safely against Azure SQL

param(
    [Parameter(Mandatory=$false)]
    [string]$EnvFile = ".env.azure",
    
    [Parameter(Mandatory=$false)]
    [ValidateSet("upgrade", "current", "history", "downgrade")]
    [string]$Command = "upgrade",
    
    [Parameter(Mandatory=$false)]
    [string]$Revision = "head",
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Alembic Migration Script for Azure SQL" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "⚠ Virtual environment is not activated" -ForegroundColor Yellow
    Write-Host "Attempting to activate .venv..." -ForegroundColor Yellow
    
    if (Test-Path ".venv\Scripts\Activate.ps1") {
        & .venv\Scripts\Activate.ps1
        Write-Host "✓ Virtual environment activated" -ForegroundColor Green
    } else {
        Write-Host "✗ Error: .venv not found" -ForegroundColor Red
        Write-Host "Please create a virtual environment first: python -m venv .venv" -ForegroundColor Yellow
        exit 1
    }
}

# Check if env file exists
if (-not (Test-Path $EnvFile)) {
    Write-Host "✗ Error: Environment file not found: $EnvFile" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please create $EnvFile with your Azure SQL connection strings:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Example $EnvFile content:" -ForegroundColor Cyan
    Write-Host @"
IDENTITY_DATABASE_URL=mssql+aioodbc://app_user:password@server.database.windows.net:1433/dbname?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no
IDENTITY_DATABASE_MIGRATION_URL=mssql+aioodbc://migration_admin:password@server.database.windows.net:1433/dbname?driver=ODBC+Driver+18+for+SQL+Server&Encrypt=yes&TrustServerCertificate=no
SECRET_TOKEN_KEY=migration-key-at-least-32-characters-long
AUTH_ALGORITHM=HS256
TOKEN_TIME_DELTA_IN_MINUTES=60
DEFAULT_USER_ROLE=User
TOKEN_URL=/token
SERVICE_ID=00000000-0000-0000-0000-000000000001
"@ -ForegroundColor Gray
    Write-Host ""
    exit 1
}

# Backup current .env if exists
$envBackup = $null
if (Test-Path ".env") {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $envBackup = ".env.backup_$timestamp"
    Write-Host "Backing up current .env to $envBackup" -ForegroundColor Yellow
    Copy-Item ".env" $envBackup
}

try {
    # Copy Azure env file
    Write-Host "Using environment file: $EnvFile" -ForegroundColor Cyan
    Copy-Item $EnvFile ".env" -Force
    Write-Host "✓ Environment configured" -ForegroundColor Green
    Write-Host ""
    
    # Show current migration status
    Write-Host "Current Migration Status:" -ForegroundColor Cyan
    Write-Host "----------------------------------------" -ForegroundColor DarkGray
    alembic current
    Write-Host ""
    
    # Execute command based on parameter
    switch ($Command) {
        "upgrade" {
            Write-Host "========================================" -ForegroundColor Cyan
            Write-Host "Running Migration: Upgrade to $Revision" -ForegroundColor Cyan
            Write-Host "========================================" -ForegroundColor Cyan
            
            if ($DryRun) {
                Write-Host "DRY RUN MODE - No changes will be made" -ForegroundColor Yellow
                Write-Host ""
                Write-Host "Would execute: alembic upgrade $Revision" -ForegroundColor Yellow
            } else {
                Write-Host "⚠ This will modify the database schema!" -ForegroundColor Yellow
                Write-Host "Press Ctrl+C to cancel, or" -ForegroundColor Yellow
                Read-Host "Press Enter to continue"
                Write-Host ""
                
                alembic upgrade $Revision
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host ""
                    Write-Host "✓ Migration completed successfully!" -ForegroundColor Green
                } else {
                    Write-Host ""
                    Write-Host "✗ Migration failed!" -ForegroundColor Red
                    exit 1
                }
            }
        }
        
        "current" {
            Write-Host "Current database revision:" -ForegroundColor Cyan
            alembic current --verbose
        }
        
        "history" {
            Write-Host "Migration History:" -ForegroundColor Cyan
            Write-Host "----------------------------------------" -ForegroundColor DarkGray
            alembic history --verbose
        }
        
        "downgrade" {
            Write-Host "========================================" -ForegroundColor Cyan
            Write-Host "WARNING: Downgrading to $Revision" -ForegroundColor Red
            Write-Host "========================================" -ForegroundColor Cyan
            
            if ($DryRun) {
                Write-Host "DRY RUN MODE - No changes will be made" -ForegroundColor Yellow
                Write-Host ""
                Write-Host "Would execute: alembic downgrade $Revision" -ForegroundColor Yellow
            } else {
                Write-Host "⚠ This will REVERSE database changes!" -ForegroundColor Red
                Write-Host "⚠ This operation can cause data loss!" -ForegroundColor Red
                Write-Host ""
                $confirmation = Read-Host "Type 'YES' to confirm downgrade"
                
                if ($confirmation -eq "YES") {
                    alembic downgrade $Revision
                    
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host ""
                        Write-Host "✓ Downgrade completed" -ForegroundColor Green
                    } else {
                        Write-Host ""
                        Write-Host "✗ Downgrade failed!" -ForegroundColor Red
                        exit 1
                    }
                } else {
                    Write-Host "Downgrade cancelled" -ForegroundColor Yellow
                }
            }
        }
    }
    
    # Show final status
    if ($Command -in @("upgrade", "downgrade") -and -not $DryRun) {
        Write-Host ""
        Write-Host "Final Migration Status:" -ForegroundColor Cyan
        Write-Host "----------------------------------------" -ForegroundColor DarkGray
        alembic current --verbose
    }
    
} finally {
    # Restore original .env
    if ($envBackup -and (Test-Path $envBackup)) {
        Write-Host ""
        Write-Host "Restoring original .env file" -ForegroundColor Yellow
        Copy-Item $envBackup ".env" -Force
        Remove-Item $envBackup
        Write-Host "✓ Original .env restored" -ForegroundColor Green
    } elseif (Test-Path ".env") {
        # If no backup, remove the temporary .env
        Remove-Item ".env"
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Migration Script Completed" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
