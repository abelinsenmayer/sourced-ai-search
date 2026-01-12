# Stop OpenSearch cluster using docker compose
Write-Host "Stopping OpenSearch cluster..."

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DockerComposeDir = Join-Path $ScriptDir "..\opensearch-cluster"

Set-Location $DockerComposeDir
docker compose down

Write-Host "OpenSearch cluster stopped."
