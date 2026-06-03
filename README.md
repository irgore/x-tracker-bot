# X Following Tracker Bot

Discord bot yang track siapa yang di-follow akun X tertentu. Alerts ke Discord channel via embed.

## Apa yang dilakukan bot ini?

- Track akun X tertentu (siapa yang mereka follow)
- Kirim notifikasi ke Discord channel kalau ada following baru
- Pakai slash commands buat manage tracking
- Jalan 24/7 sebagai systemd service

## Prerequisites

- VPS/server (Ubuntu/Debian recommended)
- Python 3.10+
- Akun Discord + bot token
- Akun X/Twitter (buat cookies)

---

## Step-by-Step Setup

### Step 1: Buat Discord Bot

1. Buka https://discord.com/developers/applications
2. **New Application** → kasih nama (misal "X Tracker") → **Create**
3. Tab **Bot** → **Reset Token** → copy token (ini `DISCORD_TOKEN` lu)
4. Di tab yang sama, enable **Message Content Intent**
5. Tab **OAuth2** → **URL Generator**:
   - Scopes: `bot` + `applications.commands`
   - Bot Permissions: `Send Messages`, `Embed Links`, `Use Slash Commands`
6. Copy URL yang muncul → buka di browser → invite ke server Discord lu

### Step 2: Install di VPS

```bash
git clone https://github.com/irgore/x-tracker-bot.git
cd x-tracker-bot
./setup.sh
```

### Step 3: Ambil Cookies X

Bot butuh cookies akun X lu buat scrape /following list. Ada 2 cara:

#### Cara A: Manual (Recommended buat VPS)

1. Buka `x.com` di browser laptop/HP lu
2. Login ke akun X
3. **F12** → tab **Application** → **Cookies** → `https://x.com`
4. Cari dan copy value **auth_token** dan **ct0**
5. Di VPS, copy template:
   ```bash
   cp x-session-template.json /root/.x-session.json
   nano /root/.x-session.json
   ```
6. Ganti `GANTI_INI_DENGAN_AUTH_TOKEN` dan `GANTI_INI_DENGAN_CT0` dengan value yang lu copy
7. Save (Ctrl+X → Y → Enter)

#### Cara B: Pakai login.sh (Butuh browser di mesin yang sama)

```bash
./login.sh
```
Browser kebuka → login ke X → balik ke terminal → Enter → session tersimpan otomatis.

⚠️ Cara ini cuma jalan kalau mesin lu ada GUI/display (bukan headless VPS).

### Step 4: Edit .env

```bash
nano .env
```

Isi dengan:
```
DISCORD_TOKEN=token_discord_lu
X_SESSION=/root/.x-session.json
POLL_INTERVAL=600
MAX_SCROLL=15
```

**Penjelasan:**
- `DISCORD_TOKEN` — token dari Step 1
- `X_SESSION` — path ke file cookies dari Step 3
- `POLL_INTERVAL` — seberapa sering check (detik). `600` = 10 menit
- `MAX_SCROLL` — kedalaman scroll halaman following. `15` = ~500 following

### Step 5: Test Run

```bash
./run.sh
```

Kalau gak ada error, bot udah jalan. Buka Discord, coba `/xhelp`.

### Step 6: Set 24/7 Service (Opsional)

```bash
cp x-tracker.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now x-tracker
```

---

## Slash Commands

- `/track @user [channel]` — mulai track, alerts ke channel
- `/untrack @user` — stop tracking
- `/tracked` — list semua tracked accounts
- `/check @user` — manual check sekarang
- `/xhelp` — help

## Troubleshooting

### Bot detect 0 new follows terus
Cookies expired. Ulangi Step 3 + restart:
```bash
systemctl restart x-tracker
```

### Bot gak respon di Discord
Cek log:
```bash
journalctl -u x-tracker -f
```

### Update ke versi terbaru
```bash
cd ~/x-tracker-bot
git pull
systemctl restart x-tracker
```

## File Structure

```
x-tracker-bot/
├── main.py                 # Entry point
├── bot.py                  # Discord bot, slash commands, background poll
├── scraper.py              # Playwright X scraper
├── db.py                   # SQLite storage
├── config.py               # Env loading
├── setup.sh                # One-command setup
├── run.sh                  # Run script
├── login.sh                # Generate X session (GUI only)
├── x-session-template.json # Template buat manual cookie setup
├── requirements.txt        # Python deps
├── .env.example            # Config template
└── x-tracker.service       # Systemd unit
```
