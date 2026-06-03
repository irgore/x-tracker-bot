import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", "600"))  # 10 min default
STATE_DIR = Path(os.getenv("STATE_DIR", str(Path.home() / ".x-tracker-state")))
STATE_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = Path(os.getenv("DB_PATH", str(STATE_DIR / "bot.db")))
HISTORY_FILE = STATE_DIR / "history.jsonl"
MAX_SCROLL = int(os.getenv("MAX_SCROLL", "15"))
X_SESSION = os.getenv("X_SESSION", str(Path.home() / ".x-session.json"))
