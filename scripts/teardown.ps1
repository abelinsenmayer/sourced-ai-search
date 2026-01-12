# Tear down OpenSearch cluster and remove all data
Write-Host "Tearing down OpenSearch cluster and removing all data..."

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DockerComposeDir = Join-Path $ScriptDir "..\opensearch-cluster"

Set-Location $DockerComposeDir

# Stop and remove containers
Write-Host "Stopping and removing containers..."
docker compose down -v

# Remove any leftover containers
Write-Host "Removing any leftover containers..."
docker container prune -f

# Remove any leftover volumes (including named volumes)
Write-Host "Removing Docker volumes..."
docker volume prune -f

# Remove any dangling images
Write-Host "Removing dangling images..."
docker image prune -f

Write-Host "OpenSearch cluster and all data have been removed."
Write-Host ""
Write-Host "Note: If you want to completely reset including networks, run:"
Write-Host "docker network prune -f"
