#!/bin/bash
# OpenClaw Multi-Agent Automated Setup Script
# Usage: ./setup-multi-openclaw.sh <openrouter-api-key>
set -e

OPENROUTER_KEY="${1:?Usage: $0 <openrouter-api-key>}"
BASE_DIR="$HOME"

echo ""
echo "============================================"
echo "  OpenClaw Multi-Agent Setup"
echo "  Setting up 4 parallel AI agents"
echo "============================================"
echo ""

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "Node.js is required. Install v22+:"
    echo "  curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -"
    echo "  sudo apt-get install -y nodejs"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 22 ]; then
    echo "Node.js v22+ required. Current: $(node -v)"
    exit 1
fi

# Install OpenClaw
echo "[1/4] Installing OpenClaw..."
npm install -g openclaw@latest

# Setup instances 2-4
for i in 2 3 4; do
    PORT=$((18788 + i))
    DIR="$BASE_DIR/.openclaw-instance${i}"
    TOKEN="instance${i}-$(openssl rand -hex 12 2>/dev/null || echo $(date +%s)${i})"

    echo "[${i}/4] Setting up Instance $i (port $PORT)..."

    mkdir -p "$DIR/agents/main/agent" "$DIR/workspace"

    # Write config
    cat > "$DIR/openclaw.json" << EOFCFG
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
    "auth": {"mode": "token", "token": "$TOKEN"},
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
EOFCFG

    # Write auth
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

    chmod 600 "$DIR/agents/main/agent/auth-profiles.json"
    echo "  Done: $DIR"
done

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "Start all instances:"
echo ""
echo "  openclaw gateway --port 18789 &"
echo "  openclaw --profile instance2 gateway --port 18790 &"
echo "  openclaw --profile instance3 gateway --port 18791 &"
echo "  openclaw --profile instance4 gateway --port 18792 &"
echo ""
echo "Access:"
echo "  http://127.0.0.1:18789/chat?session=main"
echo "  http://127.0.0.1:18790/chat?session=main"
echo "  http://127.0.0.1:18791/chat?session=main"
echo "  http://127.0.0.1:18792/chat?session=main"
echo ""
echo "Dashboard: open dashboard/index.html"
echo ""
