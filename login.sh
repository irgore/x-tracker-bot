#!/bin/bash
# Generate X/Twitter login session for the bot
# Opens a browser — login manually, then session is saved.
set -e
cd "$(dirname "$0")"

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

SESSION_PATH="${1:-/root/.x-session.json}"

echo ""
echo -e "${CYAN}${BOLD}  X Session Generator${NC}"
echo -e "  Session will be saved to: ${BOLD}${SESSION_PATH}${NC}"
echo ""

# Check if display available
if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    echo -e "${YELLOW}⚠️  No display detected — running in headed mode may fail.${NC}"
    echo -e "   If on a headless VPS, run this on your local machine instead,"
    echo -e "   then copy the session file to the VPS."
    echo ""
fi

.venv/bin/python3 -c "
from playwright.sync_api import sync_playwright
import sys

p = sync_playwright().start()
browser = p.chromium.launch(headless=False)
ctx = browser.new_context()
page = ctx.new_page()
page.goto('https://x.com/login')

print('')
print('  → Login to X in the browser window')
print('  → After login, come back here and press Enter')
print('')

try:
    input('  Press Enter when logged in...')
except KeyboardInterrupt:
    print('\n  Cancelled.')
    browser.close()
    p.stop()
    sys.exit(1)

ctx.storage_state(path='${SESSION_PATH}')
print(f'\n  ✅ Session saved to ${SESSION_PATH}')
browser.close()
p.stop()
"

echo ""
echo -e "${GREEN}${BOLD}Done!${NC} Add this to your .env:"
echo -e "   ${BOLD}X_SESSION=${SESSION_PATH}${NC}"
echo ""
