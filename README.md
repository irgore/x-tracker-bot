# X Following Tracker Bot

Discord bot yang track siapa yang di-follow akun X tertentu. Alerts ke Discord channel via embed.

## Setup (VPS baru)

```bash
git clone https://github.com/irgore/x-tracker-bot.git
cd x-tracker-bot
./setup.sh
nano .env          # masukin DISCORD_TOKEN
./run.sh
```

## Bikin Discord Bot

1. Buka https://discord.com/developers/applications
2. **New Application** → kasih nama (misal `X Tracker`) → **Create**
3. Tab **Bot**:
   - **Reset Token** → copy token (ini yang masuk ke `.env`)
   - Scroll ke bawah, enable **Message Content Intent**
4. Tab **OAuth2** → **URL Generator**:
   - **Scopes**: centang `bot` + `applications.commands`
   - **Bot Permissions**: centang:
     - `Send Messages`
     - `Embed Links`
     - `Use Slash Commands`
5. Copy URL yang muncul di bawah → buka di browser → invite ke server lu

## Slash Commands

| Command | Description |
|---------|-------------|
| `/track @user [channel]` | Mulai track, alerts ke channel (default: current) |
| `/untrack @user` | Stop tracking |
| `/tracked` | List semua tracked accounts |
| `/check @user` | Manual check sekarang |
| `/xhelp` | Help |

## Run as Service (24/7)

```bash
cp x-tracker.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now x-tracker

# cek status
systemctl status x-tracker

# lihat log
journalctl -u x-tracker -f

# restart setelah update
systemctl restart x-tracker
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
