# 🚀 Start Here - Quick Setup Guide

Your existing OpenClaw is on port **18789**. These Docker instances will run alongside it.

## Port Configuration

- **Existing OpenClaw:** http://localhost:18789 (already running ✅)
- **Instance 1 (Docker):** http://localhost:18792
- **Instance 2 (Docker):** http://localhost:18790
- **Instance 3 (Docker):** http://localhost:18791

## 📝 Setup Steps

### Step 1: Install Docker Desktop

**Download and install Docker Desktop:**

1. Go to: https://www.docker.com/products/docker-desktop/
2. Download Docker Desktop for Windows
3. Run the installer
4. **Restart your computer** after installation
5. Launch Docker Desktop from Start menu
6. Wait for Docker to start (Docker icon in system tray)

**Verify Docker is installed:**
```powershell
docker --version
docker-compose --version
```

See detailed instructions in: [INSTALL_DOCKER.md](INSTALL_DOCKER.md)

### Step 2: Setup Environment Files

```powershell
cd C:\Users\Administrator\openclaw-deployment\shared-scripts
.\manage-all.ps1 setup
```

This creates `.env` files for each instance.

### Step 3: Configure API Keys

You need to add OpenRouter API keys to each instance.

**Get your OpenRouter API key:**
1. Go to https://openrouter.ai/keys
2. Copy your API key (format: `sk-or-v1-...`)

**Edit the .env files:**

Edit these 3 files:
- `C:\Users\Administrator\openclaw-deployment\instance1\.env`
- `C:\Users\Administrator\openclaw-deployment\instance2\.env`
- `C:\Users\Administrator\openclaw-deployment\instance3\.env`

Replace `your_openrouter_api_key_here` with your actual API key:

```env
OPENROUTER_API_KEY=sk-or-v1-YOUR-ACTUAL-KEY-HERE
```

**Options:**
- ✅ Use the **same key** for all 3 instances (simple, shared rate limits)
- ✅ Use **different keys** for each instance (independent rate limits)

### Step 4: Start Docker Instances

```powershell
cd C:\Users\Administrator\openclaw-deployment\shared-scripts
.\manage-all.ps1 start
```

Wait 30-60 seconds for containers to start.

### Step 5: Verify Everything is Running

```powershell
.\manage-all.ps1 status
```

You should see 3 containers running.

### Step 6: Access Your Instances

Open your browser:

- **Your original:** http://localhost:18789 ← Your existing OpenClaw
- **Instance 1:** http://localhost:18792
- **Instance 2:** http://localhost:18790
- **Instance 3:** http://localhost:18791

## 🎯 You Now Have 4 OpenClaw Instances!

1. **Original OpenClaw** (port 18789) - Your existing installation
2. **Docker Instance 1** (port 18792) - New containerized agent
3. **Docker Instance 2** (port 18790) - New containerized agent
4. **Docker Instance 3** (port 18791) - New containerized agent

All using OpenRouter free models! 🎉

## 📋 Essential Commands

```powershell
# Navigate to scripts directory
cd C:\Users\Administrator\openclaw-deployment\shared-scripts

# Start all Docker instances
.\manage-all.ps1 start

# Stop all Docker instances
.\manage-all.ps1 stop

# Check status
.\manage-all.ps1 status

# View logs
.\manage-all.ps1 logs

# Health check
.\manage-all.ps1 health
```

## 🔍 Troubleshooting

### Docker not found

Make sure Docker Desktop is running (check system tray for Docker icon).

### Port already in use

If you see port errors, check what's using the ports:
```powershell
netstat -ano | findstr "18790"
netstat -ano | findstr "18791"
netstat -ano | findstr "18792"
```

### API key errors

Verify your OpenRouter API key at: https://openrouter.ai/keys

### Containers won't start

Check logs:
```powershell
.\manage-all.ps1 logs instance1
```

## 📚 More Information

- **[QUICKSTART.md](QUICKSTART.md)** - Detailed quick start guide
- **[README.md](README.md)** - Complete documentation
- **[INSTALL_DOCKER.md](INSTALL_DOCKER.md)** - Docker installation help

## 💡 Next Steps After Setup

1. **Test each instance** - Visit each URL and verify it works
2. **Monitor usage** - Check OpenRouter dashboard for API usage
3. **Configure channels** - Add WhatsApp, Telegram, Discord, etc.
4. **Scale up** - Add more instances if needed
5. **Deploy to server** - Move to cloud for 24/7 availability

---

**Need help? Check the troubleshooting section or see README.md**
