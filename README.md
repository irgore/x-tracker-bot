# X Following Tracker Bot

Discord bot yang track siapa yang di-follow akun X tertentu. Alerts ke Discord channel via embed.

## Setup

```bash
git clone https://github.com/irgore/x-tracker-bot.git
cd x-tracker-bot
./setup.sh
nano .env              # masukin DISCORD_TOKEN + X_SESSION
./run.sh
```

### Yang dibutuhkan di `.env`:
- **DISCORD_TOKEN** — bot token dari Discord Developer Portal
- **X_SESSION** — path ke file session X (default: `/root/.x-session.json`)

### Generate X Session

Bot butuh cookies login X buat bisa scrape /following list. Generate pakai `login.sh`:

```bash
./login.sh
```

**Step-by-step:**
1. Script buka browser Chromium
2. Login ke akun X/Twitter lu di browser tersebut
3. Setelah login sukses, balik ke terminal → tekan **Enter**
4. Session otomatis tersimpan ke `/root/.x-session.json`
5. Path ini udah di-set di `.env` sebagai `X_SESSION`

**⚠️ Headless VPS (ga ada display/GUI):**

Browser gabuka di VPS tanpa desktop. Solusi:
```bash
# 1. Clone repo di local machine (laptop/PC lu)
git clone https://github.com/irgore/x-tracker-bot.git
cd x-tracker-bot
./setup.sh

# 2. Generate session di local
./login.sh
# login ke X → tekan Enter → session tersimpan di /root/.x-session.json

# 3. Copy session file ke VPS
scp /root/.x-session.json root@ip-vps:/root/.x-session.json

# 4. Di VPS, pastikan .env udah bener
nano .env
# X_SESSION=/root/.x-session.json
```

**Session expired?**

Kalau bot tiba-tiba detect 0 new follows terus, kemungkinan cookies expired. Generate ulang:
```bash
./login.sh
systemctl restart x-tracker
```

## Bikin Discord Bot

1. Buka https://discord.com/developers/applications
2. **New Application** → kasih nama → **Create**
3. Tab **Bot** → **Reset Token** → copy token → enable **Message Content Intent**
4. Tab **OAuth2** → **URL Generator**:
   - Scopes: `bot` + `applications.commands`
   - Bot Permissions: `Send Messages`, `Embed Links`, `Use Slash Commands`
5. Copy URL → invite ke server lu

## Slash Commands

| Command | Description |
|---------|-------------|
| `/track @user [channel]` | Mulai track, alerts ke channel |
| `/untrack @user` | Stop tracking |
| `/tracked` | List semua tracked accounts |
| `/check @user` | Manual check sekarang |
| `/xhelp` | Help |

## Run as Service (24/7)

```bash
cp x-tracker.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now x-tracker

systemctl status x-tracker      # cek status
journalctl -u x-tracker -f      # lihat log
systemctl restart x-tracker     # restart setelah update
```

## Update

```bash
cd ~/x-tracker-bot
git pull
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
├── login.sh          # Generate X session
├── requirements.txt  # Python deps
├── .env.example      # Config template
└── x-tracker.service # Systemd unit
```
