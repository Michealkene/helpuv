# OpenClaw Native Multi-Instance Management Script
# Manages multiple OpenClaw instances using native Node.js (no Docker!)

param(
    [Parameter(Position=0)]
    [string]$Command,

    [Parameter(Position=1)]
    [string]$Instance
)

$BasePath = "C:\Users\Administrator"
$Instances = @(
    @{Name="instance2"; Port=18790; Path="$BasePath\.openclaw-instance2"},
    @{Name="instance3"; Port=18791; Path="$BasePath\.openclaw-instance3"},
    @{Name="instance4"; Port=18792; Path="$BasePath\.openclaw-instance4"}
)

function Write-ColoredHeader {
    param([string]$Message, [string]$Color = "Cyan")
    Write-Host "`n===================================" -ForegroundColor $Color
    Write-Host $Message -ForegroundColor $Color
    Write-Host "===================================`n" -ForegroundColor $Color
}

function Initialize-Instances {
    Write-ColoredHeader "🚀 Setting Up Native OpenClaw Instances" "Cyan"

    foreach ($inst in $Instances) {
        Write-Host "Setting up $($inst.Name) (port $($inst.Port))..." -ForegroundColor Yellow

        # Create directories
        if (-not (Test-Path $inst.Path)) {
            New-Item -ItemType Directory -Path $inst.Path -Force | Out-Null
            Write-Host "  ✓ Created config directory" -ForegroundColor Green
        }

        $workspacePath = Join-Path $inst.Path "workspace"
        if (-not (Test-Path $workspacePath)) {
            New-Item -ItemType Directory -Path $workspacePath -Force | Out-Null
            Write-Host "  ✓ Created workspace directory" -ForegroundColor Green
        }

        # Create openclaw.json
        $configPath = Join-Path $inst.Path "openclaw.json"
        if (-not (Test-Path $configPath)) {
            $config = @{
                messages = @{
                    ackReactionScope = "group-mentions"
                }
                agents = @{
                    defaults = @{
                        maxConcurrent = 4
                        subagents = @{
                            maxConcurrent = 8
                        }
                        compaction = @{
                            mode = "safeguard"
                        }
                        workspace = Join-Path $inst.Path "workspace"
                        models = @{
                            "openrouter/auto" = @{
                                alias = "OpenRouter Auto"
                            }
                            "openrouter/openrouter/free" = @{
                                alias = "OpenRouter Free"
                            }
                        }
                        model = @{
                            primary = "openrouter/openrouter/free"
                        }
                    }
                }
                gateway = @{
                    mode = "local"
                    auth = @{
                        mode = "token"
                        token = "$($inst.Name)-token-change-me"
                    }
                    port = $inst.Port
                    bind = "127.0.0.1"
                    tailscale = @{
                        mode = "off"
                        resetOnExit = $false
                    }
                }
                auth = @{
                    profiles = @{
                        "openrouter:default" = @{
                            provider = "openrouter"
                            mode = "api_key"
                        }
                    }
                }
                plugins = @{
                    entries = @{}
                }
                channels = @{}
                skills = @{
                    install = @{
                        nodeManager = "npm"
                    }
                }
                meta = @{
                    instance = $inst.Name
                    description = "OpenClaw $($inst.Name) - Native Node.js"
                }
            }

            $config | ConvertTo-Json -Depth 10 | Set-Content -Path $configPath
            Write-Host "  ✓ Created openclaw.json" -ForegroundColor Green
        }

        # Create .env file
        $envPath = Join-Path $inst.Path ".env"
        if (-not (Test-Path $envPath)) {
            $envContent = @"
# OpenClaw $($inst.Name) - Environment Variables
# OpenRouter API Key (Free or Paid)
# Get your key from: https://openrouter.ai/keys
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Instance Identifier
INSTANCE_NAME=$($inst.Name)
INSTANCE_PORT=$($inst.Port)

# Optional: Logging
LOG_LEVEL=info
"@
            $envContent | Set-Content -Path $envPath
            Write-Host "  ✓ Created .env file" -ForegroundColor Green
        }

        Write-Host ""
    }

    Write-Host "`n✅ Setup complete!" -ForegroundColor Green
    Write-Host "`n📝 Next steps:" -ForegroundColor Yellow
    Write-Host "1. Edit .env files and add your OpenRouter API keys:"
    foreach ($inst in $Instances) {
        Write-Host "   - $($inst.Path)\.env"
    }
    Write-Host "2. Run: .\manage-native.ps1 start"
}

function Start-AllInstances {
    Write-ColoredHeader "🚀 Starting All Native OpenClaw Instances"

    # Check if OpenClaw is installed
    try {
        $null = Get-Command openclaw -ErrorAction Stop
    } catch {
        Write-Host "❌ OpenClaw is not installed!" -ForegroundColor Red
        Write-Host "Install it with: npm install -g openclaw@latest" -ForegroundColor Yellow
        return
    }

    foreach ($inst in $Instances) {
        # Load environment variables
        $envPath = Join-Path $inst.Path ".env"
        if (Test-Path $envPath) {
            Get-Content $envPath | ForEach-Object {
                if ($_ -match '^([^=]+)=(.+)$') {
                    [Environment]::SetEnvironmentVariable($matches[1], $matches[2], "Process")
                }
            }
        }

        Write-Host "Starting $($inst.Name) on port $($inst.Port)..." -ForegroundColor Yellow

        # Start as background job
        $jobName = "OpenClaw-$($inst.Name)"

        # Check if already running
        $existingJob = Get-Job -Name $jobName -ErrorAction SilentlyContinue
        if ($existingJob) {
            Write-Host "  ⚠️  Instance already running (Job ID: $($existingJob.Id))" -ForegroundColor Yellow
        } else {
            $scriptBlock = {
                param($homePath, $port)
                & openclaw gateway --home $homePath --port $port
            }

            Start-Job -Name $jobName -ScriptBlock $scriptBlock -ArgumentList $inst.Path, $inst.Port | Out-Null
            Start-Sleep -Milliseconds 500
            Write-Host "  ✓ Started (Job: $jobName)" -ForegroundColor Green
        }
    }

    Write-Host "`n✅ All instances started!" -ForegroundColor Green
    Write-Host "`nℹ️  View status with: .\manage-native.ps1 status" -ForegroundColor Cyan
    Start-Sleep -Seconds 2
    Get-AllStatus
}

function Stop-AllInstances {
    Write-ColoredHeader "🛑 Stopping All Native OpenClaw Instances"

    foreach ($inst in $Instances) {
        $jobName = "OpenClaw-$($inst.Name)"
        $job = Get-Job -Name $jobName -ErrorAction SilentlyContinue

        if ($job) {
            Write-Host "Stopping $($inst.Name)..." -ForegroundColor Yellow
            Stop-Job -Name $jobName
            Remove-Job -Name $jobName -Force
            Write-Host "  ✓ Stopped" -ForegroundColor Green
        } else {
            Write-Host "$($inst.Name) is not running" -ForegroundColor Gray
        }
    }

    Write-Host "`n✅ All instances stopped!" -ForegroundColor Green
}

function Get-AllStatus {
    Write-ColoredHeader "📊 Status of All OpenClaw Instances"

    Write-Host "Background Jobs:" -ForegroundColor Cyan
    $jobs = Get-Job -Name "OpenClaw-*" -ErrorAction SilentlyContinue
    if ($jobs) {
        $jobs | Format-Table Name, State, HasMoreData -AutoSize
    } else {
        Write-Host "  No instances running" -ForegroundColor Gray
    }

    Write-Host "`n🌐 Gateway URLs:" -ForegroundColor Cyan
    Write-Host "  Original: http://localhost:18789" -ForegroundColor Green
    foreach ($inst in $Instances) {
        Write-Host "  $($inst.Name): http://localhost:$($inst.Port)" -ForegroundColor Yellow
    }

    Write-Host "`n📡 Port Status:" -ForegroundColor Cyan
    foreach ($inst in $Instances) {
        $listening = Get-NetTCPConnection -LocalPort $inst.Port -ErrorAction SilentlyContinue
        if ($listening) {
            Write-Host "  ✅ Port $($inst.Port) - Listening" -ForegroundColor Green
        } else {
            Write-Host "  ❌ Port $($inst.Port) - Not listening" -ForegroundColor Red
        }
    }
}

function Get-InstanceLogs {
    param([string]$InstanceName)

    if ([string]::IsNullOrEmpty($InstanceName)) {
        Write-Host "Usage: .\manage-native.ps1 logs <instance2|instance3|instance4>" -ForegroundColor Yellow
        return
    }

    $jobName = "OpenClaw-$InstanceName"
    $job = Get-Job -Name $jobName -ErrorAction SilentlyContinue

    if ($job) {
        Write-ColoredHeader "📜 Logs for $InstanceName"
        Receive-Job -Name $jobName -Keep
    } else {
        Write-Host "❌ Instance $InstanceName is not running" -ForegroundColor Red
    }
}

function Restart-AllInstances {
    Write-ColoredHeader "🔄 Restarting All Instances"
    Stop-AllInstances
    Start-Sleep -Seconds 2
    Start-AllInstances
}

function Test-Health {
    Write-ColoredHeader "🏥 Health Check for All Instances"

    Write-Host "Original (port 18789):" -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:18789/health" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        Write-Host "  ✅ Healthy" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ Unhealthy or not responding" -ForegroundColor Red
    }

    foreach ($inst in $Instances) {
        Write-Host "`n$($inst.Name) (port $($inst.Port)):" -ForegroundColor Cyan
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:$($inst.Port)/health" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
            Write-Host "  ✅ Healthy" -ForegroundColor Green
        } catch {
            Write-Host "  ❌ Unhealthy or not responding" -ForegroundColor Red
        }
    }
}

function Show-Help {
    @"

OpenClaw Native Multi-Instance Management Script (No Docker!)

Usage: .\manage-native.ps1 <command> [options]

Commands:
    setup       - Create configuration directories and files
    start       - Start all instances as background jobs
    stop        - Stop all instances
    restart     - Restart all instances
    status      - Show status of all instances
    logs <name> - View logs from specific instance (instance2, instance3, instance4)
    health      - Check health of all instances
    help        - Show this help message

Examples:
    .\manage-native.ps1 setup              # First time setup
    .\manage-native.ps1 start              # Start all instances
    .\manage-native.ps1 logs instance2     # View logs for instance2
    .\manage-native.ps1 health             # Check health of all instances

Instance URLs:
    - Original:  http://localhost:18789 (your existing instance)
    - Instance2: http://localhost:18790
    - Instance3: http://localhost:18791
    - Instance4: http://localhost:18792

"@
}

# Main script logic
switch ($Command) {
    "setup" { Initialize-Instances }
    "start" { Start-AllInstances }
    "stop" { Stop-AllInstances }
    "restart" { Restart-AllInstances }
    "status" { Get-AllStatus }
    "logs" {
        if ($Instance) {
            Get-InstanceLogs -InstanceName $Instance
        } else {
            Write-Host "Please specify an instance: instance2, instance3, or instance4" -ForegroundColor Yellow
        }
    }
    "health" { Test-Health }
    "help" { Show-Help }
    default {
        if ($Command) {
            Write-Host "Unknown command: $Command`n" -ForegroundColor Red
        }
        Show-Help
    }
}
