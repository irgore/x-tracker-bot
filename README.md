# X Following Tracker Bot

Discord bot yang track siapa yang di-follow akun X tertentu. Alerts ke Discord channel via embed.

## Setup (VPS baru)

```bash
chmod +x setup.sh run.sh
./setup.sh
nano .env          # masukin DISCORD_TOKEN
./run.sh
```

## Slash Commands

| Command | Description |
|---------|-------------|
| `/track @user [channel]` | Mulai track, alerts ke channel (default: current) |
| `/untrack @user` | Stop tracking |
| `/tracked` | List semua tracked accounts |
| `/check @user` | Manual check sekarang |
| `/xhelp` | Help |

## Run as Service (systemd)

```bash
sudo cp x-tracker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now x-tracker
```

## Files

```
x-tracker-bot/
├── main.py           # Entry point
├── bot.py            # Discord bot, slash commands, background poll
├── scraper.py        # Playwright X scraper
├── db.py             # SQLite storage
├── config.py         # Env loading
├── setup.sh          # One-command setup
├── run.sh            # Run script
├── requirements.txt  # Python deps
├── .env.example      # Config template
└── x-tracker.service # Systemd unit (optional)
```
