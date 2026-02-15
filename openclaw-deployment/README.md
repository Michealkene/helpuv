# OpenClaw Multi-Instance Deployment

This deployment setup allows you to run **multiple OpenClaw instances** in parallel using Docker, each with its own configuration and API keys.

## 📁 Directory Structure

```
openclaw-deployment/
├── instance1/
│   ├── docker-compose.yml      # Docker Compose config for instance 1
│   ├── .env.example            # Environment template
│   ├── .env                    # Your API keys (create from .env.example)
│   ├── config/
│   │   └── openclaw.json       # OpenClaw configuration (port 18789)
│   └── workspace/              # Instance 1 workspace
├── instance2/
│   ├── docker-compose.yml      # Docker Compose config for instance 2
│   ├── .env.example            # Environment template
│   ├── .env                    # Your API keys (create from .env.example)
│   ├── config/
│   │   └── openclaw.json       # OpenClaw configuration (port 18790)
│   └── workspace/              # Instance 2 workspace
├── instance3/
│   ├── docker-compose.yml      # Docker Compose config for instance 3
│   ├── .env.example            # Environment template
│   ├── .env                    # Your API keys (create from .env.example)
│   ├── config/
│   │   └── openclaw.json       # OpenClaw configuration (port 18791)
│   └── workspace/              # Instance 3 workspace
├── shared-scripts/
│   ├── manage-all.sh           # Bash management script (Linux/WSL/macOS)
│   └── manage-all.ps1          # PowerShell management script (Windows)
└── README.md                   # This file
```

## 🚀 Quick Start

### 1. Prerequisites

- **Docker Desktop** (Windows/macOS) or **Docker Engine** (Linux)
- **Docker Compose v2**
- **Node.js 22+** (for local development, not required for Docker)

### 2. Initial Setup

#### Option A: Using the Management Script (Recommended)

**On Linux/WSL/macOS:**
```bash
cd openclaw-deployment/shared-scripts
./manage-all.sh setup
```

**On Windows (PowerShell):**
```powershell
cd openclaw-deployment\shared-scripts
.\manage-all.ps1 setup
```

This will create `.env` files for each instance from the templates.

#### Option B: Manual Setup

Copy the environment templates for each instance:

```bash
# Instance 1
cp instance1/.env.example instance1/.env

# Instance 2
cp instance2/.env.example instance2/.env

# Instance 3
cp instance3/.env.example instance3/.env
```

### 3. Configure API Keys

Edit each instance's `.env` file and add your OpenRouter API keys.

**Important:** You can use:
- **Different API keys** for each instance (independent rate limits)
- **The same API key** for all instances (shared rate limits)

#### Get OpenRouter API Keys

1. Go to [https://openrouter.ai/keys](https://openrouter.ai/keys)
2. Create one or more API keys
3. Add them to your `.env` files

**Example for instance1/.env:**
```env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
INSTANCE_NAME=instance1
OPENCLAW_GATEWAY_TOKEN=instance1-secure-token-here
OPENCLAW_PORT=18789
LOG_LEVEL=info
```

### 4. Start All Instances

**Using Management Script:**

```bash
# Linux/WSL/macOS
./shared-scripts/manage-all.sh start

# Windows PowerShell
.\shared-scripts\manage-all.ps1 start
```

**Manual Start:**

```bash
# Start instance 1
cd instance1 && docker-compose up -d

# Start instance 2
cd ../instance2 && docker-compose up -d

# Start instance 3
cd ../instance3 && docker-compose up -d
```

### 5. Access the Gateways

Once started, you can access each instance:

- **Instance 1:** http://localhost:18789
- **Instance 2:** http://localhost:18790
- **Instance 3:** http://localhost:18791

## 📋 Management Commands

### Using the Management Script

The management scripts provide easy control over all instances:

#### Start/Stop/Restart

```bash
# Linux/WSL/macOS
./manage-all.sh start      # Start all instances
./manage-all.sh stop       # Stop all instances
./manage-all.sh restart    # Restart all instances

# Windows PowerShell
.\manage-all.ps1 start
.\manage-all.ps1 stop
.\manage-all.ps1 restart
```

#### Check Status

```bash
# Linux/WSL/macOS
./manage-all.sh status

# Windows PowerShell
.\manage-all.ps1 status
```

#### View Logs

```bash
# View logs from all instances
./manage-all.sh logs

# View logs from specific instance
./manage-all.sh logs instance1
./manage-all.sh logs instance2
./manage-all.sh logs instance3

# Windows PowerShell
.\manage-all.ps1 logs
.\manage-all.ps1 logs instance1
```

#### Health Check

```bash
# Linux/WSL/macOS
./manage-all.sh health

# Windows PowerShell
.\manage-all.ps1 health
```

#### Open Shell in Container

```bash
# Linux/WSL/macOS
./manage-all.sh shell instance1

# Windows PowerShell
.\manage-all.ps1 shell instance1
```

#### Update All Instances

```bash
# Linux/WSL/macOS
./manage-all.sh update

# Windows PowerShell
.\manage-all.ps1 update
```

## 🔧 Configuration

### Instance Configuration

Each instance has its own configuration file at `instanceN/config/openclaw.json`:

```json
{
  "agents": {
    "defaults": {
      "maxConcurrent": 4,
      "subagents": {
        "maxConcurrent": 8
      },
      "models": {
        "openrouter/openrouter/free": {}
      },
      "model": {
        "primary": "openrouter/openrouter/free"
      }
    }
  },
  "gateway": {
    "port": 18789,  // Different for each instance
    "bind": "0.0.0.0"
  }
}
```

### Customizing Models

To use different models for each instance, edit the `openclaw.json` file:

**Instance 1 - Free models:**
```json
"model": {
  "primary": "openrouter/openrouter/free"
}
```

**Instance 2 - Paid models:**
```json
"model": {
  "primary": "openrouter/anthropic/claude-3.5-sonnet"
}
```

**Instance 3 - Mixed:**
```json
"model": {
  "primary": "openrouter/google/gemini-pro"
}
```

### Port Configuration

Default ports:
- **Instance 1:** 18789
- **Instance 2:** 18790
- **Instance 3:** 18791

To change ports, edit both:
1. `instanceN/docker-compose.yml` - ports section
2. `instanceN/config/openclaw.json` - gateway.port

## 🔐 Security Considerations

### Gateway Tokens

Each instance has its own gateway token in:
- `instanceN/config/openclaw.json` (token field)
- `instanceN/.env` (OPENCLAW_GATEWAY_TOKEN)

**Change the default tokens** before deploying to production!

### API Key Management

- **Never commit `.env` files** to version control
- Use different API keys per instance for better isolation
- Store API keys securely (use secrets management in production)

### Network Exposure

By default, instances bind to `0.0.0.0` (accessible from other machines).

To restrict to localhost only, edit `docker-compose.yml`:

```yaml
ports:
  - "127.0.0.1:18789:18789"  # Only accessible from localhost
```

## 🌐 Deployment to Server

### Deploy to Cloud Server (DigitalOcean, AWS, Vultr, etc.)

1. **Clone this deployment to your server:**
   ```bash
   scp -r openclaw-deployment user@your-server:~/
   ```

2. **SSH into your server:**
   ```bash
   ssh user@your-server
   ```

3. **Install Docker:**
   ```bash
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER
   ```

4. **Configure and start:**
   ```bash
   cd openclaw-deployment
   ./shared-scripts/manage-all.sh setup
   # Edit .env files with your API keys
   ./shared-scripts/manage-all.sh start
   ```

5. **Access remotely:**
   - http://your-server-ip:18789
   - http://your-server-ip:18790
   - http://your-server-ip:18791

### Firewall Configuration

Open the required ports:

```bash
# Ubuntu/Debian
sudo ufw allow 18789
sudo ufw allow 18790
sudo ufw allow 18791

# CentOS/RHEL
sudo firewall-cmd --add-port=18789/tcp --permanent
sudo firewall-cmd --add-port=18790/tcp --permanent
sudo firewall-cmd --add-port=18791/tcp --permanent
sudo firewall-cmd --reload
```

## 🔄 Adding More Instances

To add a 4th instance:

1. **Create new directory:**
   ```bash
   mkdir -p instance4/config instance4/workspace
   ```

2. **Copy configuration:**
   ```bash
   cp instance3/docker-compose.yml instance4/
   cp instance3/.env.example instance4/
   cp instance3/config/openclaw.json instance4/config/
   ```

3. **Update configuration:**
   - Edit `instance4/docker-compose.yml` - change port to 18792
   - Edit `instance4/config/openclaw.json` - change port to 18792
   - Edit container name to `openclaw-instance4`

4. **Add to management script:**
   - Edit `shared-scripts/manage-all.sh`
   - Add "instance4" to the INSTANCES array

## 📊 Monitoring

### View Resource Usage

```bash
# CPU and Memory usage
docker stats

# Disk usage
docker system df
```

### Container Health

```bash
# Check all containers
docker ps -a

# Inspect specific instance
docker inspect openclaw-instance1
```

## 🐛 Troubleshooting

### Instance won't start

1. Check logs:
   ```bash
   ./manage-all.sh logs instance1
   ```

2. Verify API key is set:
   ```bash
   cat instance1/.env | grep OPENROUTER_API_KEY
   ```

3. Check port conflicts:
   ```bash
   netstat -ano | findstr "18789"  # Windows
   lsof -i :18789                   # Linux/macOS
   ```

### API Key Issues

Verify your OpenRouter API key:
```bash
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Container Permission Errors

If you see permission errors, fix ownership:
```bash
sudo chown -R 1000:1000 instance*/config instance*/workspace
```

### Can't Access Gateway Remotely

1. Check firewall rules
2. Verify `bind: "0.0.0.0"` in openclaw.json
3. Ensure ports are exposed in docker-compose.yml

## 📚 Additional Resources

- [OpenClaw Documentation](https://docs.openclaw.ai)
- [OpenClaw GitHub](https://github.com/openclaw/openclaw)
- [OpenRouter Documentation](https://openrouter.ai/docs)
- [Docker Documentation](https://docs.docker.com)

## 🤝 Support

For issues with:
- **OpenClaw:** https://github.com/openclaw/openclaw/issues
- **This deployment:** Check troubleshooting section above

## 📄 License

This deployment configuration is MIT licensed. OpenClaw itself is licensed under its own terms.

---

**Happy multi-agent deployment! 🦞🦞🦞**
