# X Following Tracker Bot

Discord bot yang track siapa yang di-follow akun X/Twitter tertentu. Alerts dikirim ke Discord channel via embed.

## Persiapan Sebelum Mulai

Kamu butuh:
- VPS Ubuntu/Debian (minimal 1GB RAM)
- Discord Bot Token
- Cookies `auth_token` & `ct0` dari akun X/Twitter kamu

---

## Step 1 — Buat Discord Bot

1. Buka https://discord.com/developers/applications
2. Klik **New Application** → kasih nama → **Create**
3. Masuk tab **Bot** → klik **Reset Token** → copy token-nya (simpan, ini `DISCORD_TOKEN`)
4. Di tab yang sama, aktifkan **Message Content Intent**
5. Tab **OAuth2** → **URL Generator**:
   - Centang scope: `bot` + `applications.commands`
   - Bot Permissions: `Send Messages`, `Embed Links`, `Use Slash Commands`
6. Copy URL yang muncul → buka di browser → invite bot ke server Discord kamu

---

## Step 2 — Install di VPS

SSH ke VPS kamu, lalu jalankan:

```bash
git clone https://github.com/irgore/x-tracker-bot.git
cd x-tracker-bot
./setup.sh
```

Script `setup.sh` akan install Python dependencies + Playwright browser secara otomatis.

---

## Step 3 — Ambil Cookies X

> Cocok untuk headless VPS (tanpa GUI)

1. Buka `x.com` di browser laptop/HP kamu, login ke akun X
2. Tekan **F12** → tab **Application** → **Cookies** → klik `https://x.com`
3. Cari dan copy value dari:
   - `auth_token`
   - `ct0`
4. Di VPS, jalankan:
   ```bash
   cp x-session-template.json /root/.x-session.json
   nano /root/.x-session.json
   ```
5. Ganti `GANTI_INI_DENGAN_AUTH_TOKEN` dan `GANTI_INI_DENGAN_CT0` dengan value yang sudah kamu copy
6. Save: **Ctrl+X** → **Y** → **Enter**

---

## Step 4 — Konfigurasi .env

```bash
nano .env
```

Isi seperti ini:

```
DISCORD_TOKEN=token_discord_kamu
X_SESSION=/root/.x-session.json
POLL_INTERVAL=600
MAX_SCROLL=15
```

Keterangan:
- `POLL_INTERVAL=600` → cek setiap 10 menit
- `MAX_SCROLL=15` → scroll ~500 following

---

## Step 5 — Test Dulu

```bash
./run.sh
```

Kalau tidak ada error, buka Discord dan coba ketik `/xhelp`. Kalau bot respon, berarti berhasil.

---

## Step 6 — Jalankan 24/7

```bash
cp x-tracker.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now x-tracker
```

Cek status:
```bash
systemctl status x-tracker
```

Lihat log real-time:
```bash
journalctl -u x-tracker -f
```

---

## Troubleshooting Cepat

| Masalah | Solusi |
|---------|--------|
| Bot detect 0 new follows | Cookies expired → ulangi Step 3 → `systemctl restart x-tracker` |
| Bot tidak respon di Discord | `journalctl -u x-tracker -f` untuk lihat error |
| Update ke versi terbaru | `cd ~/x-tracker-bot && git pull && systemctl restart x-tracker` |

---

## Slash Commands

| Command | Description |
|---------|-------------|
| `/track @user [channel]` | Mulai track akun X |
| `/setchannel #channel` | Set default channel untuk alerts |
| `/untrack @user` | Stop tracking |
| `/tracked` | Lihat semua yang sedang di-track |
| `/check @user` | Cek manual sekarang |
| `/xhelp` | Bantuan |
