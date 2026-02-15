# OpenClaw Multi-Instance Quick Start Guide

Get 3 OpenClaw instances running in under 5 minutes!

## ⚡ Super Quick Start (TL;DR)

```bash
# 1. Setup environment files
cd openclaw-deployment/shared-scripts
./manage-all.sh setup

# 2. Add your OpenRouter API keys
# Edit instance1/.env, instance2/.env, instance3/.env
# Replace "your_openrouter_api_key_here" with your actual keys

# 3. Start all instances
./manage-all.sh start

# 4. Check status
./manage-all.sh status

# Done! Access at:
# - http://localhost:18789 (instance1)
# - http://localhost:18790 (instance2)
# - http://localhost:18791 (instance3)
```

## 📝 Step-by-Step Guide

### Step 1: Get OpenRouter API Keys

1. Go to https://openrouter.ai/keys
2. Sign up or log in
3. Create 1-3 API keys (or use the same key for all instances)
4. Copy your API key(s) - they look like: `sk-or-v1-...`

### Step 2: Setup Environment Files

**Linux/WSL/macOS:**
```bash
cd openclaw-deployment/shared-scripts
./manage-all.sh setup
```

**Windows PowerShell:**
```powershell
cd openclaw-deployment\shared-scripts
.\manage-all.ps1 setup
```

This creates `.env` files for each instance.

### Step 3: Configure API Keys

Edit each `.env` file and add your OpenRouter API key:

**For instance1/.env:**
```env
OPENROUTER_API_KEY=sk-or-v1-your-first-key-here
```

**For instance2/.env:**
```env
OPENROUTER_API_KEY=sk-or-v1-your-second-key-here
```

**For instance3/.env:**
```env
OPENROUTER_API_KEY=sk-or-v1-your-third-key-here
```

**Note:** You can use the **same API key** for all instances if you prefer (shared rate limits).

### Step 4: Start All Instances

**Linux/WSL/macOS:**
```bash
./manage-all.sh start
```

**Windows PowerShell:**
```powershell
.\manage-all.ps1 start
```

Wait 30-60 seconds for all containers to start.

### Step 5: Verify Everything is Running

```bash
./manage-all.sh status
```

You should see:
- ✅ 3 containers running
- ✅ Gateway URLs listed
- ✅ All ports accessible

### Step 6: Access Your Instances

Open your browser and visit:

- **Instance 1:** http://localhost:18789
- **Instance 2:** http://localhost:18790
- **Instance 3:** http://localhost:18791

## 🎯 Common Use Cases

### Same API Key for All (Shared Rate Limits)

Use the **same** OpenRouter API key in all three `.env` files.

**Benefits:**
- Simple management
- One billing account
- Shared quota

**Drawbacks:**
- Shared rate limits
- All instances hit the same quota

### Different API Keys (Independent Rate Limits)

Use **different** OpenRouter API keys for each `.env` file.

**Benefits:**
- Independent rate limits
- Better load distribution
- Higher total throughput

**Drawbacks:**
- Manage multiple keys
- Potentially higher cost

### Mix of Free and Paid Models

**Instance 1** - Free models (`.env`):
```env
OPENROUTER_API_KEY=sk-or-v1-free-tier-key
```

**Instance 2** - Paid models (edit `instance2/config/openclaw.json`):
```json
"model": {
  "primary": "openrouter/anthropic/claude-3.5-sonnet"
}
```

**Instance 3** - Specific provider:
```json
"model": {
  "primary": "openrouter/google/gemini-pro"
}
```

## 🔧 Essential Commands

```bash
# Start all instances
./manage-all.sh start

# Stop all instances
./manage-all.sh stop

# Restart all instances
./manage-all.sh restart

# Check status
./manage-all.sh status

# View logs from all instances
./manage-all.sh logs

# View logs from specific instance
./manage-all.sh logs instance1

# Check health
./manage-all.sh health

# Open shell in container
./manage-all.sh shell instance1
```

## 🚨 Troubleshooting Quick Fixes

### "Can't connect to gateway"

**Solution:**
```bash
# Check if containers are running
docker ps

# If not running, start them
./manage-all.sh start

# Check logs for errors
./manage-all.sh logs
```

### "API key invalid"

**Solution:**
1. Verify your OpenRouter API key at https://openrouter.ai/keys
2. Check your `.env` file has the correct key
3. Restart the instance:
   ```bash
   cd instance1
   docker-compose restart
   ```

### "Port already in use"

**Solution:**
1. Check what's using the port:
   ```bash
   # Windows
   netstat -ano | findstr "18789"

   # Linux/macOS
   lsof -i :18789
   ```

2. Stop the conflicting service or change the port in:
   - `instanceN/docker-compose.yml`
   - `instanceN/config/openclaw.json`

### "Container keeps restarting"

**Solution:**
```bash
# Check logs for error
./manage-all.sh logs instance1

# Common issues:
# 1. Missing API key in .env
# 2. Invalid configuration in openclaw.json
# 3. Port conflict
```

## 📊 Monitoring Your Instances

### Check Resource Usage

```bash
# See CPU, memory usage
docker stats

# See which instance is using most resources
docker stats --no-stream
```

### Check API Usage

Visit your OpenRouter dashboard:
https://openrouter.ai/activity

## 🌐 Deploy to Production Server

### Quick Deploy to VPS

1. **Copy deployment to server:**
   ```bash
   scp -r openclaw-deployment user@your-server.com:~/
   ```

2. **SSH and install Docker:**
   ```bash
   ssh user@your-server.com
   curl -fsSL https://get.docker.com | sh
   ```

3. **Configure and start:**
   ```bash
   cd openclaw-deployment
   ./shared-scripts/manage-all.sh setup
   # Edit .env files
   ./shared-scripts/manage-all.sh start
   ```

4. **Open firewall ports:**
   ```bash
   sudo ufw allow 18789
   sudo ufw allow 18790
   sudo ufw allow 18791
   ```

5. **Access remotely:**
   - http://YOUR_SERVER_IP:18789
   - http://YOUR_SERVER_IP:18790
   - http://YOUR_SERVER_IP:18791

## 🎓 Next Steps

Once your instances are running:

1. **Configure channels** (WhatsApp, Telegram, Discord, etc.)
2. **Install skills** for extended functionality
3. **Set up webhooks** for automation
4. **Monitor usage** and optimize

See the full [README.md](README.md) for detailed configuration options.

## 💡 Pro Tips

1. **Test with one instance first** before starting all three
2. **Use different ports** if deploying to the same network
3. **Monitor your OpenRouter credits** to avoid surprises
4. **Keep .env files secure** - never commit to git
5. **Use the health check** regularly: `./manage-all.sh health`

## 🆘 Need Help?

- **Full documentation:** See [README.md](README.md)
- **OpenClaw docs:** https://docs.openclaw.ai
- **OpenRouter help:** https://openrouter.ai/docs
- **Issues:** https://github.com/openclaw/openclaw/issues

---

**That's it! You now have 3 parallel OpenClaw agents running! 🦞🦞🦞**
