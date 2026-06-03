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
    echo -e "${GREEN}[1/5]${NC} Creating virtualenv..."
    python3 -m venv .venv
else
    echo -e "${GREEN}[1/5]${NC} Virtualenv exists, skipping..."
fi

# 2. Install Python deps
echo -e "${GREEN}[2/5]${NC} Installing dependencies..."
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt

# 3. Install Playwright Chromium browser
echo -e "${GREEN}[3/5]${NC} Installing Playwright Chromium..."
.venv/bin/playwright install chromium
.venv/bin/playwright install-deps chromium 2>/dev/null || true

# 4. Setup .env
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo -e "${YELLOW}[4/5]${NC} Created .env — edit it with your tokens:"
    echo -e "   ${BOLD}nano .env${NC}"
    echo ""
    echo -e "   Required:"
    echo -e "   • ${BOLD}DISCORD_TOKEN${NC} — from https://discord.com/developers/applications"
    echo -e "   • ${BOLD}X_SESSION${NC} — path to X login session (run ${BOLD}./login.sh${NC} to generate)"
    echo ""
else
    echo -e "${GREEN}[4/5]${NC} .env exists, skipping..."
fi

# 5. Check X session
SESSION_PATH=$(grep -oP 'X_SESSION=\K.*' .env 2>/dev/null || echo "/root/.x-session.json")
if [ ! -f "$SESSION_PATH" ]; then
    echo -e "${YELLOW}[5/5]${NC} X session not found at ${BOLD}${SESSION_PATH}${NC}"
    echo -e "   Run ${BOLD}./login.sh${NC} to generate one (needs a browser/display)."
    echo -e "   On headless VPS: generate on local machine, then scp to server."
else
    echo -e "${GREEN}[5/5]${NC} X session found at ${BOLD}${SESSION_PATH}${NC}"
fi

echo ""
echo -e "${GREEN}${BOLD}✅ Setup complete!${NC}"
echo -e "   Run: ${BOLD}./run.sh${NC}"
echo -e "   Service: ${BOLD}cp x-tracker.service /etc/systemd/system && systemctl enable --now x-tracker${NC}"
echo ""
