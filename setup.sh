#!/bin/bash
# X Following Tracker Bot — one-command setup for new VPS
set -e
cd "$(dirname "$0")"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${CYAN}${BOLD}  ██╗  ██╗    ████████╗██████╗  █████╗  ██████╗██╗  ██╗███████╗██████╗ ${NC}"
echo -e "${CYAN}${BOLD}  ╚██╗██╔╝    ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗${NC}"
echo -e "${CYAN}${BOLD}   ╚███╔╝        ██║   ██████╔╝███████║██║     █████╔╝ █████╗  ██████╔╝${NC}"
echo -e "${CYAN}${BOLD}   ██╔██╗        ██║   ██╔══██╗██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗${NC}"
echo -e "${CYAN}${BOLD}  ██╔╝ ██╗       ██║   ██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║${NC}"
echo -e "${CYAN}${BOLD}  ╚═╝  ╚═╝       ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝${NC}"
echo -e "                         ${YELLOW}Following Tracker Bot${NC}  ${GREEN}by irgore${NC}"
echo ""

# 1. Create venv if not exists
if [ ! -d ".venv" ]; then
    echo -e "${GREEN}[1/4]${NC} Creating virtualenv..."
    python3 -m venv .venv
else
    echo -e "${GREEN}[1/4]${NC} Virtualenv exists, skipping..."
fi

# 2. Install Python deps
echo -e "${GREEN}[2/4]${NC} Installing dependencies..."
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt

# 3. Install Playwright Chromium browser
echo -e "${GREEN}[3/4]${NC} Installing Playwright Chromium..."
.venv/bin/playwright install chromium
.venv/bin/playwright install-deps chromium 2>/dev/null || true

# 4. Check .env
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo -e "${YELLOW}⚠️  Created .env from .env.example — edit it with your DISCORD_TOKEN:${NC}"
    echo -e "   ${BOLD}nano .env${NC}"
    echo ""
else
    echo -e "${GREEN}[4/4]${NC} .env exists, skipping..."
fi

echo ""
echo -e "${GREEN}${BOLD}✅ Setup complete!${NC}"
echo -e "   Run: ${BOLD}./run.sh${NC}"
echo -e "   Service: ${BOLD}cp x-tracker.service /etc/systemd/system && systemctl enable --now x-tracker${NC}"
echo ""
