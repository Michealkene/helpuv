# Native Node.js Multi-Instance Setup (No Docker!)

This setup runs multiple OpenClaw instances using native Node.js - **much lighter** than Docker!

## Why This is Better for Your Laptop

- ✅ **No Docker overhead** - saves 2-4GB RAM
- ✅ **Faster startup** - instances start in seconds
- ✅ **Lower CPU usage** - no virtualization layer
- ✅ **Better battery life** - less background processes
- ✅ **Simpler** - just Node.js processes

## Setup

You already have:
- ✅ Node.js 22 installed
- ✅ OpenClaw installed globally via npm
- ✅ One instance running on port 18789

Let's add 3 more instances using separate configuration directories!

## Architecture

```
C:\Users\Administrator\.openclaw\          (Original - port 18789)
C:\Users\Administrator\.openclaw-instance2\ (New - port 18790)
C:\Users\Administrator\.openclaw-instance3\ (New - port 18791)
C:\Users\Administrator\.openclaw-instance4\ (New - port 18792)
```

Each instance runs as a separate Node.js process with its own config.

## Quick Start

### Step 1: Create Instance Directories

```powershell
# Create separate config directories
mkdir C:\Users\Administrator\.openclaw-instance2
mkdir C:\Users\Administrator\.openclaw-instance3
mkdir C:\Users\Administrator\.openclaw-instance4

# Create workspace directories
mkdir C:\Users\Administrator\.openclaw-instance2\workspace
mkdir C:\Users\Administrator\.openclaw-instance3\workspace
mkdir C:\Users\Administrator\.openclaw-instance4\workspace
```

### Step 2: Create Configuration Files

Each instance needs its own `openclaw.json` with a different port.

See the configuration templates below.

### Step 3: Start Each Instance

```powershell
# Instance 2 (port 18790)
openclaw gateway --home C:\Users\Administrator\.openclaw-instance2 --port 18790

# Instance 3 (port 18791)
openclaw gateway --home C:\Users\Administrator\.openclaw-instance3 --port 18791

# Instance 4 (port 18792)
openclaw gateway --home C:\Users\Administrator\.openclaw-instance4 --port 18792
```

## Running in Background (Windows)

Use PowerShell jobs or separate terminal windows:

### Option 1: Separate Terminal Windows

Open 3 PowerShell windows and run one command in each:
- Window 1: `openclaw gateway --home C:\Users\Administrator\.openclaw-instance2 --port 18790`
- Window 2: `openclaw gateway --home C:\Users\Administrator\.openclaw-instance3 --port 18791`
- Window 3: `openclaw gateway --home C:\Users\Administrator\.openclaw-instance4 --port 18792`

### Option 2: Background Jobs (PowerShell)

```powershell
# Start as background jobs
Start-Job -ScriptBlock { openclaw gateway --home C:\Users\Administrator\.openclaw-instance2 --port 18790 }
Start-Job -ScriptBlock { openclaw gateway --home C:\Users\Administrator\.openclaw-instance3 --port 18791 }
Start-Job -ScriptBlock { openclaw gateway --home C:\Users\Administrator\.openclaw-instance4 --port 18792 }

# Check job status
Get-Job

# View job output
Receive-Job -Id 1
```

### Option 3: Windows Service (Advanced)

Use NSSM (Non-Sucking Service Manager) to run as Windows services:

```powershell
# Install NSSM
winget install NSSM.NSSM

# Create service for instance 2
nssm install OpenClaw-Instance2 "C:\Program Files\nodejs\node.exe" "C:\Users\Administrator\AppData\Roaming\npm\node_modules\openclaw\openclaw.mjs" gateway --home C:\Users\Administrator\.openclaw-instance2 --port 18790

# Start service
nssm start OpenClaw-Instance2
```

## Resource Comparison

| Method | RAM Usage | CPU Idle | Startup Time |
|--------|-----------|----------|--------------|
| Docker Desktop | 2-4GB | 5-10% | 30-60s |
| Native Node.js | 200-400MB per instance | <1% | 3-5s |
| **Savings** | **~3GB** | **~5-9%** | **~25-55s** |

## Access Your Instances

- **Original:** http://localhost:18789
- **Instance 2:** http://localhost:18790
- **Instance 3:** http://localhost:18791
- **Instance 4:** http://localhost:18792

## Managing Instances

You can start/stop individual instances by closing their terminal windows or stopping their jobs/services.

## Pros vs Docker

✅ **Much lighter** - uses 1/10th the resources
✅ **Faster** - starts instantly
✅ **Simpler** - no Docker Desktop needed
✅ **Better for laptops** - saves battery
✅ **Same functionality** - all OpenClaw features work

## Cons vs Docker

❌ **Less isolation** - all run on same OS
❌ **Manual management** - no Docker GUI
❌ **Shared dependencies** - all use same Node.js version

## Which Should You Use?

**Use Native Node.js if:**
- Laptop/desktop with limited resources ✅
- Want fast startup and low overhead ✅
- Running for personal use ✅
- Don't need strict isolation ✅

**Use Docker if:**
- Deploying to server 🖥️
- Need strict isolation 🔒
- Running in production 🏭
- Want easy backup/restore 💾
