# Choose Your Deployment Method

You have **two options** for running multiple OpenClaw instances. Choose based on your needs:

## 🚀 Option 1: Native Node.js (RECOMMENDED for Laptops)

**Best for:** Personal use, laptops, limited resources

### Pros
✅ **Ultra lightweight** - uses ~300MB RAM per instance vs 2-4GB for Docker
✅ **Fast startup** - 3-5 seconds vs 30-60 seconds
✅ **Low CPU usage** - <1% idle vs 5-10% with Docker
✅ **Better battery life** - no Docker daemon running
✅ **Simple** - just Node.js processes
✅ **No installation needed** - you already have Node.js!

### Cons
❌ Less isolation between instances
❌ Manual process management (use PowerShell jobs)
❌ Harder to backup/restore

### Resource Usage
- **RAM:** ~300-400MB per instance
- **CPU (idle):** <1%
- **Startup time:** 3-5 seconds
- **Total overhead:** Minimal

### Quick Start
```powershell
cd C:\Users\Administrator\openclaw-deployment\shared-scripts
.\manage-native.ps1 setup
# Edit .env files with API keys
.\manage-native.ps1 start
```

**📖 Full guide:** [NATIVE_SETUP.md](NATIVE_SETUP.md)

---

## 🐳 Option 2: Docker Containers

**Best for:** Servers, production deployments, strict isolation

### Pros
✅ **Strong isolation** - each instance fully containerized
✅ **Easy backup** - just backup volumes
✅ **Portable** - run anywhere Docker runs
✅ **VS Code integration** - nice Docker extension GUI
✅ **Production-ready** - industry standard

### Cons
❌ **Heavy** - Docker Desktop uses 2-4GB RAM
❌ **Slower startup** - 30-60 seconds
❌ **Higher CPU usage** - 5-10% idle
❌ **Battery drain** - Docker daemon always running
❌ **Requires installation** - Docker Desktop needed

### Resource Usage
- **RAM:** 2-4GB (Docker Desktop) + 400MB per instance
- **CPU (idle):** 5-10%
- **Startup time:** 30-60 seconds
- **Total overhead:** Heavy

### Quick Start
```powershell
# 1. Install Docker Desktop first
# 2. Then:
cd C:\Users\Administrator\openclaw-deployment\shared-scripts
.\manage-all.ps1 setup
# Edit .env files with API keys
.\manage-all.ps1 start
```

**📖 Full guide:** [QUICKSTART.md](QUICKSTART.md)

---

## 📊 Side-by-Side Comparison

| Feature | Native Node.js | Docker |
|---------|----------------|--------|
| **RAM Usage** | ~300MB/instance | 2-4GB + 400MB/instance |
| **CPU (Idle)** | <1% | 5-10% |
| **Startup Time** | 3-5 seconds | 30-60 seconds |
| **Installation** | None (already have Node.js) | Docker Desktop required |
| **Isolation** | Process-level | Container-level |
| **Management** | PowerShell jobs | Docker commands/GUI |
| **VS Code Integration** | No | Yes (Docker extension) |
| **Backup/Restore** | Manual | Easy (volumes) |
| **Best For** | Laptops, personal use | Servers, production |

---

## 🎯 Recommendation

### Choose Native Node.js if:
- ✅ You're on a **laptop** with limited resources
- ✅ You want **fast startup** and **low overhead**
- ✅ **Battery life** matters
- ✅ This is for **personal/development** use
- ✅ You don't need strict container isolation

### Choose Docker if:
- ✅ You're deploying to a **server/VPS**
- ✅ You need **strong isolation** between instances
- ✅ You're running in **production**
- ✅ Resources aren't a concern
- ✅ You want easy **backup/restore**

---

## 💡 My Recommendation for You

Since you mentioned **Docker slows your laptop down**, I recommend:

### ⭐ Use Native Node.js Method ⭐

**Why:**
- Your laptop will thank you (saves 3-4GB RAM!)
- Starts in seconds instead of minutes
- Much better battery life
- You already have everything installed
- Perfect for running multiple free OpenRouter agents

**Quick Start:**
```powershell
cd C:\Users\Administrator\openclaw-deployment\shared-scripts
.\manage-native.ps1 setup
```

Then edit the `.env` files and run:
```powershell
.\manage-native.ps1 start
```

---

## 🔄 Can I Switch Later?

Yes! The configurations are compatible. You can:
- Start with Native Node.js (faster to test)
- Switch to Docker later if needed (for production deployment)
- Or run some instances native and some in Docker

---

## 📚 Next Steps

1. **Choose your method** (I recommend Native for laptops!)
2. **Follow the appropriate guide:**
   - Native: [NATIVE_SETUP.md](NATIVE_SETUP.md)
   - Docker: [QUICKSTART.md](QUICKSTART.md)
3. **Get your OpenRouter API keys:** https://openrouter.ai/keys
4. **Start your instances!**

Need help deciding? Just ask!
