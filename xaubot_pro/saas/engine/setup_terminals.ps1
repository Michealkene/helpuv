# XAUBOT Pro - Setup Multiple MT5 Terminal Instances
# Run as Administrator on Windows VPS

Write-Host "============================================"
Write-Host "  XAUBOT Pro - MT5 Worker Setup"
Write-Host "============================================"

$NUM_WORKERS = 8
$MT5_SOURCE = "C:\Program Files\MetaTrader 5"

# Check if source MT5 exists
if (-not (Test-Path "$MT5_SOURCE\terminal64.exe")) {
    Write-Host "[ERROR] MetaTrader 5 not found at $MT5_SOURCE"
    Write-Host "  Please install MT5 first, then run this script."
    exit 1
}

for ($i = 1; $i -le $NUM_WORKERS; $i++) {
    $dest = "C:\MT5_Worker_$i"
    Write-Host "`n[Worker $i] Setting up $dest..."

    if (Test-Path $dest) {
        Write-Host "  Already exists - skipping"
        continue
    }

    Write-Host "  Copying MT5 terminal..."
    Copy-Item -Path $MT5_SOURCE -Destination $dest -Recurse -Force
    Write-Host "  Done!"
}

Write-Host "`n============================================"
Write-Host "  Setup complete! $NUM_WORKERS MT5 workers ready."
Write-Host "  Paths: C:\MT5_Worker_1 through C:\MT5_Worker_$NUM_WORKERS"
Write-Host "============================================"
