# Turbo Run and Audit Script for RPG Simulation
# This script runs a high-speed simulation and audits the logs for "fraud" (logic errors).

$Ticks = 1000
$LogFile = "logs/stress_test.jsonl"

# 1. Create logs directory
if (!(Test-Path -Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

Write-Host "--- Starting Turbo Simulation ($Ticks ticks) ---" -ForegroundColor Cyan
# 2. Run Headless CLI Simulation using Start-Process to avoid PS pipe encoding issues
# Disable Kafka and Prometheus to maximize local speed and avoid timeouts
$env:DISABLE_KAFKA = "1"
$env:prometheus_multiproc_dir = "" 
Start-Process python -ArgumentList "-m src cli --ticks $Ticks --entities 20 --workers 4" -RedirectStandardOutput $LogFile -NoNewWindow -Wait

if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne $null) {
    Write-Host "[ERROR] Simulation crashed!" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "--- Simulation Complete. Running Semantic Audit ---" -ForegroundColor Cyan

# 3. Run Audit Script
python scripts/audit_logs.py $LogFile

Write-Host "--- Diagnostic Cycle Finished ---" -ForegroundColor Green
