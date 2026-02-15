# OpenClaw Multi-Agent Setup - Installation Guide

Replicate this multi-agent OpenClaw setup on any machine.

## What You'll Get

- 4 parallel OpenClaw AI agents (1 original + 3 cloned instances)
- All using OpenRouter free models (no cost!)
- Unified dashboard to manage all agents in one place
- Each instance runs independently on its own port

## Architecture

```
Machine
├── Original OpenClaw       → port 18789
├── Instance 2              → port 18790
├── Instance 3              → port 18791
├── Instance 4              → port 18792
└── Dashboard (HTML)        → file:// or any local server
```

## Requirements

- **OS:** Windows 10/11, Linux, or macOS
- **Node.js:** v22 or later
- **npm** or **pnpm**
- **OpenRouter API Key** (free): https://openrouter.ai/keys

## Step 1: Install Node.js

### Windows
```powershell
# Using winget
winget install OpenJS.NodeJS.LTS

# Or download from: https://nodejs.org/
```

### Linux (Ubuntu/Debian)
```bash
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### macOS
```bash
brew install node@22
```

### Verify
```bash
node --version   # Should show v22.x.x or later
npm --version
```

## Step 2: Install OpenClaw

```bash
npm install -g openclaw@latest
```

Verify:
```bash
openclaw --version
```

## Step 3: Set Up the Original Instance

Run the onboarding wizard:

```bash
openclaw onboard
```

During onboarding:
1. Select **OpenRouter** as your provider
2. Enter your OpenRouter API key (get one from https://openrouter.ai/keys)
3. Select **openrouter/free** as the model
4. Choose gateway port **18789** (default)
5. Complete the wizard

Start the gateway:
```bash
openclaw gateway --port 18789 --verbose
```

Verify it's running:
```bash
curl http://127.0.0.1:18789/
```

## Step 4: Create Additional Instances

OpenClaw has a built-in `--profile` flag that isolates each instance in its own directory.

### Instance 2 (Port 18790)

Create the config:
```bash
mkdir -p ~/.openclaw-instance2/agents/main/agent
mkdir -p ~/.openclaw-instance2/workspace
```

Create `~/.openclaw-instance2/openclaw.json`:
```json
{
  "messages": {
    "ackReactionScope": "group-mentions"
  },
  "agents": {
    "defaults": {
      "maxConcurrent": 4,
      "subagents": {
        "maxConcurrent": 8
      },
      "compaction": {
        "mode": "safeguard"
      },
      "workspace": "~/.openclaw-instance2/workspace",
      "models": {
        "openrouter/auto": {
          "alias": "OpenRouter"
        },
        "openrouter/openrouter/free": {}
      },
      "model": {
        "primary": "openrouter/openrouter/free"
      }
    }
  },
  "gateway": {
    "mode": "local",
    "auth": {
      "mode": "token",
      "token": "CHANGE-THIS-TOKEN-instance2"
    },
    "port": 18790,
    "bind": "loopback",
    "tailscale": {
      "mode": "off",
      "resetOnExit": false
    }
  },
  "auth": {
    "profiles": {
      "openrouter:default": {
        "provider": "openrouter",
        "mode": "api_key"
      }
    }
  },
  "plugins": {
    "entries": {}
  },
  "channels": {},
  "skills": {
    "install": {
      "nodeManager": "npm"
    }
  },
  "meta": {}
}
```

Create `~/.openclaw-instance2/agents/main/agent/auth-profiles.json`:
```json
{
  "version": 1,
  "profiles": {
    "openrouter:default": {
      "type": "api_key",
      "provider": "openrouter",
      "key": "YOUR_OPENROUTER_API_KEY_HERE"
    }
  },
  "lastGood": {
    "openrouter": "openrouter:default"
  },
  "usageStats": {
    "openrouter:default": {
      "lastUsed": 0,
      "errorCount": 0
    }
  }
}
```

### Instance 3 (Port 18791)

Repeat the same steps but change:
- Directory: `~/.openclaw-instance3/`
- Port: `18791`
- Token: `CHANGE-THIS-TOKEN-instance3`

### Instance 4 (Port 18792)

Repeat again with:
- Directory: `~/.openclaw-instance4/`
- Port: `18792`
- Token: `CHANGE-THIS-TOKEN-instance4`

## Step 5: Start All Instances

### Option A: Manual Start (Separate Terminals)

Open 4 terminal windows:

```bash
# Terminal 1 - Original
openclaw gateway --port 18789

# Terminal 2 - Instance 2
openclaw --profile instance2 gateway --port 18790

# Terminal 3 - Instance 3
openclaw --profile instance3 gateway --port 18791

# Terminal 4 - Instance 4
openclaw --profile instance4 gateway --port 18792
```

### Option B: Background Processes (Linux/macOS)

```bash
# Start all in background
openclaw gateway --port 18789 &
openclaw --profile instance2 gateway --port 18790 &
openclaw --profile instance3 gateway --port 18791 &
openclaw --profile instance4 gateway --port 18792 &

# Verify
netstat -tlnp | grep -E '1878[9]|1879[012]'
```

### Option C: PowerShell Background Jobs (Windows)

```powershell
Start-Job -Name "OpenClaw-Original" -ScriptBlock { openclaw gateway --port 18789 }
Start-Job -Name "OpenClaw-Instance2" -ScriptBlock { openclaw --profile instance2 gateway --port 18790 }
Start-Job -Name "OpenClaw-Instance3" -ScriptBlock { openclaw --profile instance3 gateway --port 18791 }
Start-Job -Name "OpenClaw-Instance4" -ScriptBlock { openclaw --profile instance4 gateway --port 18792 }

# Check status
Get-Job
```

### Option D: Systemd Services (Linux - Recommended for Servers)

Create `/etc/systemd/system/openclaw@.service`:

```ini
[Unit]
Description=OpenClaw Instance %i
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
Environment=OPENCLAW_PROFILE=%i
ExecStart=/usr/bin/openclaw gateway --port %i
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable --now openclaw@18789
sudo systemctl enable --now openclaw@18790
sudo systemctl enable --now openclaw@18791
sudo systemctl enable --now openclaw@18792
```

## Step 6: Set Up the Dashboard

Copy the `dashboard/index.html` file to the new machine.

Open it in your browser:
```bash
# Linux/macOS
open dashboard/index.html
# or
xdg-open dashboard/index.html

# Windows
start dashboard/index.html
```

Or serve it with a simple HTTP server:
```bash
npx serve dashboard/
```

The dashboard shows all 4 instances in a grid with live status.

## Step 7: Verify Everything Works

Check all ports are listening:

```bash
# Linux/macOS
ss -tlnp | grep -E '1878[9]|1879[012]'

# Windows
netstat -ano | findstr "18789 18790 18791 18792"
```

Test each instance:
```bash
curl http://127.0.0.1:18789/
curl http://127.0.0.1:18790/
curl http://127.0.0.1:18791/
curl http://127.0.0.1:18792/
```

Access the chat UI:
- http://127.0.0.1:18789/chat?session=main
- http://127.0.0.1:18790/chat?session=main
- http://127.0.0.1:18791/chat?session=main
- http://127.0.0.1:18792/chat?session=main

## Quick Automated Setup Script

### Linux/macOS

Save as `setup-multi-openclaw.sh`:

```bash
#!/bin/bash
set -e

OPENROUTER_KEY="${1:?Usage: $0 <openrouter-api-key>}"

echo "=== Installing OpenClaw ==="
npm install -g openclaw@latest

echo "=== Setting up Original Instance ==="
openclaw onboard --install-daemon

echo "=== Creating Additional Instances ==="
for i in 2 3 4; do
  PORT=$((18788 + i))
  DIR="$HOME/.openclaw-instance${i}"

  echo "--- Setting up Instance $i (port $PORT) ---"
  mkdir -p "$DIR/agents/main/agent" "$DIR/workspace"

  cat > "$DIR/openclaw.json" << EOFCONFIG
{
  "messages": {"ackReactionScope": "group-mentions"},
  "agents": {
    "defaults": {
      "maxConcurrent": 4,
      "subagents": {"maxConcurrent": 8},
      "compaction": {"mode": "safeguard"},
      "workspace": "$DIR/workspace",
      "models": {
        "openrouter/auto": {"alias": "OpenRouter"},
        "openrouter/openrouter/free": {}
      },
      "model": {"primary": "openrouter/openrouter/free"}
    }
  },
  "gateway": {
    "mode": "local",
    "auth": {"mode": "token", "token": "instance${i}-$(openssl rand -hex 12)"},
    "port": $PORT,
    "bind": "loopback",
    "tailscale": {"mode": "off", "resetOnExit": false}
  },
  "auth": {
    "profiles": {
      "openrouter:default": {"provider": "openrouter", "mode": "api_key"}
    }
  },
  "plugins": {"entries": {}},
  "channels": {},
  "skills": {"install": {"nodeManager": "npm"}},
  "meta": {}
}
EOFCONFIG

  cat > "$DIR/agents/main/agent/auth-profiles.json" << EOFAUTH
{
  "version": 1,
  "profiles": {
    "openrouter:default": {
      "type": "api_key",
      "provider": "openrouter",
      "key": "$OPENROUTER_KEY"
    }
  },
  "lastGood": {"openrouter": "openrouter:default"},
  "usageStats": {"openrouter:default": {"lastUsed": 0, "errorCount": 0}}
}
EOFAUTH

  echo "  Instance $i configured at $DIR (port $PORT)"
done

echo ""
echo "=== Starting All Instances ==="
openclaw gateway --port 18789 &
sleep 2
openclaw --profile instance2 gateway --port 18790 &
sleep 2
openclaw --profile instance3 gateway --port 18791 &
sleep 2
openclaw --profile instance4 gateway --port 18792 &
sleep 3

echo ""
echo "=== All Instances Started! ==="
echo ""
echo "Access your instances:"
echo "  Original:   http://127.0.0.1:18789/chat?session=main"
echo "  Instance 2: http://127.0.0.1:18790/chat?session=main"
echo "  Instance 3: http://127.0.0.1:18791/chat?session=main"
echo "  Instance 4: http://127.0.0.1:18792/chat?session=main"
echo ""
echo "Open the dashboard:"
echo "  open dashboard/index.html"
```

Usage:
```bash
chmod +x setup-multi-openclaw.sh
./setup-multi-openclaw.sh sk-or-v1-YOUR-API-KEY-HERE
```

### Windows PowerShell

Save as `setup-multi-openclaw.ps1`:

```powershell
param(
    [Parameter(Mandatory=$true)]
    [string]$OpenRouterKey
)

Write-Host "=== Installing OpenClaw ===" -ForegroundColor Cyan
npm install -g openclaw@latest

Write-Host "=== Setting up Original Instance ===" -ForegroundColor Cyan
openclaw onboard

Write-Host "=== Creating Additional Instances ===" -ForegroundColor Cyan

$BasePath = "$env:USERPROFILE"

for ($i = 2; $i -le 4; $i++) {
    $Port = 18788 + $i
    $Dir = "$BasePath\.openclaw-instance$i"

    Write-Host "--- Setting up Instance $i (port $Port) ---" -ForegroundColor Yellow

    New-Item -ItemType Directory -Path "$Dir\agents\main\agent" -Force | Out-Null
    New-Item -ItemType Directory -Path "$Dir\workspace" -Force | Out-Null

    $config = @{
        messages = @{ ackReactionScope = "group-mentions" }
        agents = @{
            defaults = @{
                maxConcurrent = 4
                subagents = @{ maxConcurrent = 8 }
                compaction = @{ mode = "safeguard" }
                workspace = "$Dir\workspace"
                models = @{
                    "openrouter/auto" = @{ alias = "OpenRouter" }
                    "openrouter/openrouter/free" = @{}
                }
                model = @{ primary = "openrouter/openrouter/free" }
            }
        }
        gateway = @{
            mode = "local"
            auth = @{
                mode = "token"
                token = "instance$i-$([guid]::NewGuid().ToString().Substring(0,12))"
            }
            port = $Port
            bind = "loopback"
            tailscale = @{ mode = "off"; resetOnExit = $false }
        }
        auth = @{
            profiles = @{
                "openrouter:default" = @{
                    provider = "openrouter"
                    mode = "api_key"
                }
            }
        }
        plugins = @{ entries = @{} }
        channels = @{}
        skills = @{ install = @{ nodeManager = "npm" } }
        meta = @{}
    } | ConvertTo-Json -Depth 10

    $config | Set-Content -Path "$Dir\openclaw.json"

    $auth = @{
        version = 1
        profiles = @{
            "openrouter:default" = @{
                type = "api_key"
                provider = "openrouter"
                key = $OpenRouterKey
            }
        }
        lastGood = @{ openrouter = "openrouter:default" }
        usageStats = @{
            "openrouter:default" = @{
                lastUsed = 0
                errorCount = 0
            }
        }
    } | ConvertTo-Json -Depth 10

    $auth | Set-Content -Path "$Dir\agents\main\agent\auth-profiles.json"

    Write-Host "  Instance $i configured at $Dir (port $Port)" -ForegroundColor Green
}

Write-Host "`n=== Starting All Instances ===" -ForegroundColor Cyan

Start-Job -Name "OpenClaw-Original" -ScriptBlock { openclaw gateway --port 18789 }
Start-Sleep -Seconds 2
Start-Job -Name "OpenClaw-Instance2" -ScriptBlock { openclaw --profile instance2 gateway --port 18790 }
Start-Sleep -Seconds 2
Start-Job -Name "OpenClaw-Instance3" -ScriptBlock { openclaw --profile instance3 gateway --port 18791 }
Start-Sleep -Seconds 2
Start-Job -Name "OpenClaw-Instance4" -ScriptBlock { openclaw --profile instance4 gateway --port 18792 }
Start-Sleep -Seconds 3

Write-Host "`n=== All Instances Started! ===" -ForegroundColor Green
Write-Host ""
Write-Host "Access your instances:"
Write-Host "  Original:   http://127.0.0.1:18789/chat?session=main"
Write-Host "  Instance 2: http://127.0.0.1:18790/chat?session=main"
Write-Host "  Instance 3: http://127.0.0.1:18791/chat?session=main"
Write-Host "  Instance 4: http://127.0.0.1:18792/chat?session=main"
Write-Host ""
Write-Host "Check status: Get-Job"
```

Usage:
```powershell
.\setup-multi-openclaw.ps1 -OpenRouterKey "sk-or-v1-YOUR-API-KEY-HERE"
```

## Using Different API Keys

To use a different OpenRouter API key for each instance, edit the
`auth-profiles.json` file in each instance directory:

```
~/.openclaw-instance2/agents/main/agent/auth-profiles.json
~/.openclaw-instance3/agents/main/agent/auth-profiles.json
~/.openclaw-instance4/agents/main/agent/auth-profiles.json
```

Change the `key` field to a different API key.

## Stopping Instances

### Linux/macOS
```bash
# Find and kill processes
lsof -i :18790 -t | xargs kill
lsof -i :18791 -t | xargs kill
lsof -i :18792 -t | xargs kill
```

### Windows
```powershell
# Stop PowerShell jobs
Get-Job -Name "OpenClaw-*" | Stop-Job
Get-Job -Name "OpenClaw-*" | Remove-Job

# Or kill by port
netstat -ano | findstr "18790" | ForEach-Object { $_.Split()[-1] } | ForEach-Object { taskkill /PID $_ /F }
```

## Adding More Instances

To add a 5th instance:
1. Create `~/.openclaw-instance5/` with the same structure
2. Use port `18793`
3. Copy `auth-profiles.json` with your API key
4. Start with: `openclaw --profile instance5 gateway --port 18793`
5. Update `dashboard/index.html` to add the new instance to the `INSTANCES` array

## Troubleshooting

### Instance won't start
- Check if the port is already in use: `netstat -ano | findstr "PORT"`
- Check the config file is valid JSON
- Run with `--verbose` flag for detailed logs

### API key errors
- Verify your key at https://openrouter.ai/keys
- Make sure `auth-profiles.json` has the correct key
- Check the `key` field is not empty

### Config validation errors
- Don't add unknown keys to `openclaw.json`
- The `meta` field should be an empty object: `"meta": {}`
- Run `openclaw --profile NAME doctor --fix` to auto-fix

### Dashboard shows "Offline"
- Make sure all instances are running
- Check if browser can access the ports
- Try refreshing the dashboard

## Security Notes

- Gateway tokens are in the config files - change them from defaults!
- API keys are stored in plain text in `auth-profiles.json`
- On shared systems, restrict file permissions: `chmod 600 auth-profiles.json`
- The dashboard is a local HTML file - no data is sent externally

## File Structure Reference

```
~/.openclaw/                          # Original instance
├── openclaw.json                     # Config (port 18789)
├── agents/main/agent/
│   └── auth-profiles.json            # API key
└── workspace/                        # Agent workspace

~/.openclaw-instance2/                # Instance 2
├── openclaw.json                     # Config (port 18790)
├── agents/main/agent/
│   └── auth-profiles.json            # API key
└── workspace/

~/.openclaw-instance3/                # Instance 3
├── openclaw.json                     # Config (port 18791)
├── agents/main/agent/
│   └── auth-profiles.json            # API key
└── workspace/

~/.openclaw-instance4/                # Instance 4
├── openclaw.json                     # Config (port 18792)
├── agents/main/agent/
│   └── auth-profiles.json            # API key
└── workspace/

openclaw-deployment/
├── dashboard/
│   └── index.html                    # Unified dashboard
├── shared-scripts/
│   ├── manage-native.ps1             # Windows management script
│   └── manage-all.sh                 # Linux/macOS management script
├── INSTALL_GUIDE.md                  # This file
└── setup-multi-openclaw.sh/.ps1      # Automated setup scripts
```

## License

MIT - Use freely, modify as needed.

## Credits

- OpenClaw: https://github.com/openclaw/openclaw
- OpenRouter: https://openrouter.ai
