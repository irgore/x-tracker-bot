#!/bin/bash
# X Following Tracker Bot — one-command setup for new VPS
set -e
cd "$(dirname "$0")"

echo "=== X Following Tracker Bot Setup ==="

# 1. Create venv if not exists
if [ ! -d ".venv" ]; then
    echo "[1/4] Creating virtualenv..."
    python3 -m venv .venv
else
    echo "[1/4] Virtualenv exists, skipping..."
fi

# 2. Install Python deps
echo "[2/4] Installing dependencies..."
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt

# 3. Install Playwright Chromium browser
echo "[3/4] Installing Playwright Chromium..."
.venv/bin/playwright install chromium
.venv/bin/playwright install-deps chromium 2>/dev/null || true

# 4. Check .env
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  Created .env from .env.example — edit it with your DISCORD_TOKEN:"
    echo "   nano .env"
    echo ""
else
    echo "[4/4] .env exists, skipping..."
fi

echo ""
echo "✅ Setup complete!"
echo "   Run: ./run.sh"
