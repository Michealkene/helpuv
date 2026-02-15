# OpenClaw Multi-Instance Management Script (PowerShell)
# Manages multiple OpenClaw Docker instances on Windows

param(
    [Parameter(Position=0)]
    [string]$Command,

    [Parameter(Position=1)]
    [string]$Instance
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$DeploymentDir = Split-Path -Parent $ScriptDir

$Instances = @("instance1", "instance2", "instance3")
$Ports = @(18789, 18790, 18791)

function Write-ColoredHeader {
    param([string]$Message, [int]$InstanceIndex = 0)

    $Colors = @("Cyan", "Yellow", "Magenta")
    Write-Host "`n===================================" -ForegroundColor $Colors[$InstanceIndex]
    Write-Host $Message -ForegroundColor $Colors[$InstanceIndex]
    Write-Host "===================================`n" -ForegroundColor $Colors[$InstanceIndex]
}

function Test-EnvFiles {
    $missing = $false
    for ($i = 0; $i -lt $Instances.Length; $i++) {
        $instance = $Instances[$i]
        $envPath = Join-Path $DeploymentDir "$instance\.env"

        if (-not (Test-Path $envPath)) {
            $Colors = @("Cyan", "Yellow", "Magenta")
            Write-Host "⚠️  Missing .env file for $instance" -ForegroundColor $Colors[$i]
            Write-Host "   Copy .env.example to .env and configure your API keys"
            $missing = $true
        }
    }
    return -not $missing
}

function Start-AllInstances {
    Write-ColoredHeader "🚀 Starting All OpenClaw Instances"

    if (-not (Test-EnvFiles)) {
        Write-Host "`n⚠️  Please create .env files before starting instances" -ForegroundColor Red
        return
    }

    for ($i = 0; $i -lt $Instances.Length; $i++) {
        $instance = $Instances[$i]
        Write-ColoredHeader "Starting $instance" $i

        $instanceDir = Join-Path $DeploymentDir $instance
        Push-Location $instanceDir
        docker-compose up -d
        Pop-Location
    }

    Write-Host "`n✅ All instances started successfully!" -ForegroundColor Green
    Get-AllStatus
}

function Stop-AllInstances {
    Write-ColoredHeader "🛑 Stopping All OpenClaw Instances"

    for ($i = 0; $i -lt $Instances.Length; $i++) {
        $instance = $Instances[$i]
        Write-ColoredHeader "Stopping $instance" $i

        $instanceDir = Join-Path $DeploymentDir $instance
        Push-Location $instanceDir
        docker-compose down
        Pop-Location
    }

    Write-Host "`n✅ All instances stopped successfully!" -ForegroundColor Green
}

function Restart-AllInstances {
    Write-ColoredHeader "🔄 Restarting All OpenClaw Instances"
    Stop-AllInstances
    Start-Sleep -Seconds 2
    Start-AllInstances
}

function Get-AllStatus {
    Write-ColoredHeader "📊 Status of All OpenClaw Instances"

    Write-Host "Container Status:"
    docker ps -a --filter "name=openclaw-instance" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

    Write-Host "`n`n🌐 Gateway URLs:"
    for ($i = 0; $i -lt $Instances.Length; $i++) {
        $instance = $Instances[$i]
        $port = $Ports[$i]
        $Colors = @("Cyan", "Yellow", "Magenta")
        Write-Host "  $instance : http://localhost:$port" -ForegroundColor $Colors[$i]
    }
}

function Get-AllLogs {
    Write-ColoredHeader "📜 Viewing Logs for All Instances"
    Write-Host "Press Ctrl+C to stop viewing logs"
    Start-Sleep -Seconds 1

    docker ps -a --filter "name=openclaw-instance" --format "{{.Names}}" | ForEach-Object {
        docker logs $_ --tail 20
    }
}

function Get-InstanceLogs {
    param([string]$InstanceName)

    if ([string]::IsNullOrEmpty($InstanceName)) {
        Write-Host "Usage: .\manage-all.ps1 logs <instance1|instance2|instance3>" -ForegroundColor Yellow
        return
    }

    Write-ColoredHeader "📜 Viewing Logs for $InstanceName"
    $instanceDir = Join-Path $DeploymentDir $InstanceName
    Push-Location $instanceDir
    docker-compose logs -f --tail 100
    Pop-Location
}

function Enter-InstanceShell {
    param([string]$InstanceName)

    if ([string]::IsNullOrEmpty($InstanceName)) {
        Write-Host "Usage: .\manage-all.ps1 shell <instance1|instance2|instance3>" -ForegroundColor Yellow
        return
    }

    Write-ColoredHeader "🖥️  Opening Shell in $InstanceName"
    docker exec -it "openclaw-$InstanceName" bash
}

function Initialize-EnvFiles {
    Write-ColoredHeader "⚙️  Setting Up Environment Files"

    for ($i = 0; $i -lt $Instances.Length; $i++) {
        $instance = $Instances[$i]
        $envPath = Join-Path $DeploymentDir "$instance\.env"
        $examplePath = Join-Path $DeploymentDir "$instance\.env.example"

        $Colors = @("Cyan", "Yellow", "Magenta")

        if (-not (Test-Path $envPath)) {
            Write-Host "Creating .env for $instance" -ForegroundColor $Colors[$i]
            Copy-Item $examplePath $envPath
            Write-Host "   ✓ Created - Please edit and add your API keys" -ForegroundColor Green
        } else {
            Write-Host "✓ .env already exists for $instance" -ForegroundColor $Colors[$i]
        }
    }

    Write-Host "`n📝 Next steps:" -ForegroundColor Yellow
    Write-Host "1. Edit each instance's .env file and add your OpenRouter API keys"
    Write-Host "2. Run: .\manage-all.ps1 start"
}

function Update-AllInstances {
    Write-ColoredHeader "🔄 Updating All Instances"

    for ($i = 0; $i -lt $Instances.Length; $i++) {
        $instance = $Instances[$i]
        Write-ColoredHeader "Updating $instance" $i

        $instanceDir = Join-Path $DeploymentDir $instance
        Push-Location $instanceDir
        docker-compose pull
        docker-compose down
        docker-compose up -d
        Pop-Location
    }

    Write-Host "`n✅ All instances updated successfully!" -ForegroundColor Green
}

function Test-Health {
    Write-ColoredHeader "🏥 Health Check for All Instances"

    for ($i = 0; $i -lt $Instances.Length; $i++) {
        $instance = $Instances[$i]
        $port = $Ports[$i]
        $Colors = @("Cyan", "Yellow", "Magenta")

        Write-Host "`nChecking $instance (port $port)..." -ForegroundColor $Colors[$i]

        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$port/health" -TimeoutSec 5 -UseBasicParsing
            if ($response.StatusCode -eq 200) {
                Write-Host "  ✅ Healthy" -ForegroundColor Green
            } else {
                Write-Host "  ⚠️  Responded with status: $($response.StatusCode)" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "  ❌ Unhealthy or not responding" -ForegroundColor Red
        }
    }
}

function Show-Help {
    @"

OpenClaw Multi-Instance Management Script (PowerShell)

Usage: .\manage-all.ps1 <command> [options]

Commands:
    setup       - Create .env files from templates
    start       - Start all instances
    stop        - Stop all instances
    restart     - Restart all instances
    status      - Show status of all instances
    logs        - View logs from all instances
    logs <name> - View logs from specific instance (instance1, instance2, instance3)
    shell <name>- Open shell in specific instance
    update      - Pull latest images and restart all instances
    health      - Check health of all instances
    help        - Show this help message

Examples:
    .\manage-all.ps1 setup              # First time setup
    .\manage-all.ps1 start              # Start all instances
    .\manage-all.ps1 logs instance1     # View logs for instance1
    .\manage-all.ps1 shell instance2    # Open shell in instance2
    .\manage-all.ps1 health             # Check health of all instances

"@
}

# Main script logic
switch ($Command) {
    "setup" { Initialize-EnvFiles }
    "start" { Start-AllInstances }
    "stop" { Stop-AllInstances }
    "restart" { Restart-AllInstances }
    "status" { Get-AllStatus }
    "logs" {
        if ($Instance) {
            Get-InstanceLogs -InstanceName $Instance
        } else {
            Get-AllLogs
        }
    }
    "shell" { Enter-InstanceShell -InstanceName $Instance }
    "update" { Update-AllInstances }
    "health" { Test-Health }
    "help" { Show-Help }
    default {
        if ($Command) {
            Write-Host "Unknown command: $Command`n" -ForegroundColor Red
        }
        Show-Help
    }
}
