# Docker Build and Push Script for MicroservicesLab-IdentityService
# This script builds and pushes the Docker image to Docker Hub

param(
    [Parameter(Mandatory=$true)]
    [string]$DockerHubUsername,
    
    [Parameter(Mandatory=$false)]
    [string]$Version = "latest",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipBuild,
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipPush,
    
    [Parameter(Mandatory=$false)]
    [switch]$TestLocal
)

$ImageName = "microserviceslab-identityservice"
$FullImageName = "$DockerHubUsername/$ImageName"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Docker Build & Push Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Image: $FullImageName" -ForegroundColor Yellow
Write-Host "Version: $Version" -ForegroundColor Yellow
Write-Host ""

# Check if Docker is running
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker is running: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Error: Docker is not running or not installed" -ForegroundColor Red
    Write-Host "Please start Docker Desktop and try again" -ForegroundColor Yellow
    exit 1
}

# Check if logged in to Docker Hub
if (-not $SkipPush) {
    Write-Host ""
    Write-Host "Checking Docker Hub authentication..." -ForegroundColor Cyan
    $dockerInfo = docker info 2>&1 | Out-String
    if ($dockerInfo -match "Username:") {
        Write-Host "✓ Logged in to Docker Hub" -ForegroundColor Green
    } else {
        Write-Host "✗ Not logged in to Docker Hub" -ForegroundColor Red
        Write-Host "Please run: docker login" -ForegroundColor Yellow
        exit 1
    }
}

# Build the Docker image
if (-not $SkipBuild) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Building Docker Image..." -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    $startTime = Get-Date
    
    # Build with both latest and version tag if version is specified
    if ($Version -eq "latest") {
        docker build -t "${FullImageName}:latest" .
    } else {
        docker build -t "${FullImageName}:${Version}" -t "${FullImageName}:latest" .
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Docker build failed!" -ForegroundColor Red
        exit 1
    }
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    Write-Host ""
    Write-Host "✓ Build completed successfully in $($duration.TotalSeconds) seconds" -ForegroundColor Green
    
    # Show image details
    Write-Host ""
    Write-Host "Image Details:" -ForegroundColor Cyan
    docker images $FullImageName
}

# Test locally if requested
if ($TestLocal) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Testing Docker Image Locally..." -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Note: This requires valid database connection strings" -ForegroundColor Yellow
    Write-Host ""
    
    $testTag = if ($Version -eq "latest") { "latest" } else { $Version }
    
    # Check if .env file exists for testing
    if (Test-Path ".env") {
        Write-Host "Using .env file for configuration" -ForegroundColor Green
        docker run -d -p 8001:8001 --env-file .env --name identity-test "${FullImageName}:${testTag}"
    } else {
        Write-Host "No .env file found. Skipping local test." -ForegroundColor Yellow
        Write-Host "To test locally, create a .env file with required variables or provide them manually" -ForegroundColor Yellow
    }
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✓ Container started successfully" -ForegroundColor Green
        Write-Host "Container name: identity-test" -ForegroundColor Yellow
        Write-Host "API Documentation: http://localhost:8001/docs" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "To view logs: docker logs identity-test" -ForegroundColor Cyan
        Write-Host "To stop: docker stop identity-test" -ForegroundColor Cyan
        Write-Host "To remove: docker rm identity-test" -ForegroundColor Cyan
        
        # Wait a few seconds and check if container is still running
        Start-Sleep -Seconds 5
        $containerStatus = docker ps --filter "name=identity-test" --format "{{.Status}}"
        if ($containerStatus) {
            Write-Host ""
            Write-Host "✓ Container is running: $containerStatus" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "✗ Container stopped. Check logs with: docker logs identity-test" -ForegroundColor Red
        }
    }
}

# Push to Docker Hub
if (-not $SkipPush) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "Pushing to Docker Hub..." -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    
    # Push version tag
    if ($Version -ne "latest") {
        Write-Host "Pushing version: $Version" -ForegroundColor Yellow
        docker push "${FullImageName}:${Version}"
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Failed to push version tag!" -ForegroundColor Red
            exit 1
        }
        Write-Host "✓ Version $Version pushed successfully" -ForegroundColor Green
    }
    
    # Push latest tag
    Write-Host "Pushing latest tag..." -ForegroundColor Yellow
    docker push "${FullImageName}:latest"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to push latest tag!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "✓ All tags pushed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Docker Hub URL: https://hub.docker.com/r/$FullImageName" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Script completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "1. Verify the image on Docker Hub" -ForegroundColor Yellow
Write-Host "2. Set up Azure SQL Database (see AZURE_DEPLOYMENT_GUIDE.md)" -ForegroundColor Yellow
Write-Host "3. Run Alembic migrations" -ForegroundColor Yellow
Write-Host "4. Deploy to Azure Web App" -ForegroundColor Yellow
Write-Host ""
