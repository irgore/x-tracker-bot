#!/bin/bash
# X Following Tracker Bot — run
cd "$(dirname "$0")"

if [ ! -f ".env" ]; then
    echo "❌ .env not found. Run ./setup.sh first."
    exit 1
fi

exec .venv/bin/python3 main.py
