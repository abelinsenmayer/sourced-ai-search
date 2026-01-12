# Start OpenSearch cluster using docker compose
Write-Host "Starting OpenSearch cluster..."

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DockerComposeDir = Join-Path $ScriptDir "..\opensearch-cluster"

Set-Location $DockerComposeDir
docker compose up -d

Write-Host "Waiting for OpenSearch to be ready..."
# Wait for the cluster to respond to health checks
$ready = $false
$maxAttempts = 30
$attempt = 0

while (-not $ready -and $attempt -lt $maxAttempts) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:9200/_cluster/health" -ErrorAction Stop
        if ($response.status -eq "green" -or $response.status -eq "yellow") {
            $ready = $true
            Write-Host "OpenSearch cluster is ready!"
        }
    } catch {
        Write-Host "OpenSearch is not ready yet. Waiting 5 seconds... (Attempt $($attempt + 1)/$maxAttempts)"
        Start-Sleep -Seconds 5
        $attempt++
    }
}

if (-not $ready) {
    Write-Host "Timeout waiting for OpenSearch to be ready."
    exit 1
}
