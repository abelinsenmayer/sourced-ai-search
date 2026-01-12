# Setup OpenSearch with vector index and ingestion pipeline
Write-Host "Setting up OpenSearch vector index and ingestion pipeline..."

# Get the directory where this script is located
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$SrcDir = Join-Path $ScriptDir "..\src"

# Activate virtual environment if it exists
$VenvPath = Join-Path $ScriptDir "..\.venv"
if (Test-Path $VenvPath) {
    Write-Host "Activating virtual environment..."
    & "$VenvPath\Scripts\Activate.ps1"
}

# Run the setup script
Set-Location $SrcDir
python opensearch_setup.py

Write-Host "OpenSearch setup completed!"
