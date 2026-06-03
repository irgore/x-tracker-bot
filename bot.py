"""X Following Tracker Discord Bot — slash commands + background polling."""
import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import discord
from discord.ext import commands, tasks

import db
from config import DISCORD_TOKEN, POLL_INTERVAL, STATE_DIR, HISTORY_FILE, MAX_SCROLL, X_SESSION
from scraper import fetch_following, build_follow_embed

log = logging.getLogger("x-tracker")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


# ── HELPERS ────────────────────────────────────────────────────────────────────

def _append_history(target: str, new_follows: list[dict]):
    """Append new follows to history.jsonl."""
    with open(HISTORY_FILE, "a") as f:
        for follow in new_follows:
            f.write(json.dumps({
                "ts": datetime.now(timezone.utc).isoformat(),
                "target": target,
                "username": follow["username"],
                "display_name": follow.get("display_name", ""),
                "bio": follow.get("bio", ""),
            }) + "\n")


async def _track_one(target: str) -> tuple[int, list[dict]]:
    """Track one user. Returns (code, new_follows). 0=ok, 1=news, 2=fail."""
    state = await db.get_state(target)
    loop = asyncio.get_event_loop()

    try:
        new_list = await loop.run_in_executor(
            None, lambda: fetch_following(target, headless=True, scroll_max=MAX_SCROLL, storage_state=X_SESSION)
        )
    except Exception as e:
        log.error(f"[!] Scrape failed for @{target}: {e}")
        return 2, []

    if not new_list:
        return 0, []

    old_following = state["following"]

    # First run — just save baseline
    if not old_following:
        merged = {f["username"]: f for f in new_list}
        await db.save_state(target, merged, datetime.now(timezone.utc).isoformat())
        log.info(f"📌 Baseline saved for @{target}: {len(merged)} accounts")
        return 0, []

    # Diff
    new_follows = [f for f in new_list if f["username"] not in old_following]
    if not new_follows:
        return 0, []

    # Save merged state
    merged = dict(old_following)
    for f in new_list:
        merged[f["username"]] = f
    await db.save_state(target, merged)

    # History
    _append_history(target, new_follows)
    return 1, new_follows


# ── BACKGROUND POLL ────────────────────────────────────────────────────────────

@tasks.loop(seconds=POLL_INTERVAL)
async def poll_following():
    """Poll all tracked accounts, send embeds for new follows."""
    all_tracked = await db.get_all_tracked()
    if not all_tracked:
        return

    # Group by username to avoid duplicate scrapes
    unique_targets: dict[str, list[dict]] = {}
    for entry in all_tracked:
        unique_targets.setdefault(entry["username"], []).append(entry)

    for target, entries in unique_targets.items():
        code, new_follows = await _track_one(target)
        if code == 1 and new_follows:
            # Send to all guilds/channels tracking this user
            for entry in entries:
                channel = bot.get_channel(entry["channel_id"])
                if not channel:
                    continue
                for follow in new_follows:
                    try:
                        embed = build_follow_embed(target, follow)
                        await channel.send(embed=embed)
                        await asyncio.sleep(0.3)
                    except Exception as e:
                        log.error(f"Failed to send embed: {e}")

            log.info(f"🟢 @{target}: {len(new_follows)} new follow(s)")
        elif code == 2:
            log.warning(f"⚠️ @{target}: scrape failed")

        await asyncio.sleep(2)  # pause between targets


@poll_following.before_loop
async def before_poll():
    await bot.wait_until_ready()


# ── SLASH COMMANDS ─────────────────────────────────────────────────────────────

@bot.tree.command(name="track", description="Track an X user's following list")
@discord.app_commands.describe(
    username="X username (without @)",
    channel="Channel to send alerts to (default: this channel)",
)
async def track_cmd(interaction: discord.Interaction, username: str, channel: discord.TextChannel = None):
    await interaction.response.defer(ephemeral=True)
    target = username.lower().lstrip("@")
    ch = channel or interaction.channel

    added = await db.add_tracking(interaction.guild_id, ch.id, target)
    if not added:
        await interaction.followup.send(f"⚠️ @{target} is already tracked.", ephemeral=True)
        return

    # Save baseline in background
    await interaction.followup.send(
        f"✅ Now tracking **@{target}** — alerts go to {ch.mention}\n"
        f"⏳ Scraping baseline... this takes ~30s on first run.",
        ephemeral=True,
    )

    code, _ = await _track_one(target)
    if code == 2:
        await interaction.followup.send(f"❌ Failed to scrape @{target} — check if the account exists.", ephemeral=True)
    elif code == 0:
        await interaction.followup.send(f"📌 Baseline saved for @{target}. New follows will be reported.", ephemeral=True)


@bot.tree.command(name="untrack", description="Stop tracking an X user")
async def untrack_cmd(interaction: discord.Interaction, username: str):
    await interaction.response.defer(ephemeral=True)
    removed = await db.remove_tracking(interaction.guild_id, username.lower().lstrip("@"))
    if removed:
        await interaction.followup.send(f"✅ Stopped tracking @{username}.", ephemeral=True)
    else:
        await interaction.followup.send(f"⚠️ @{username} wasn't being tracked.", ephemeral=True)


@bot.tree.command(name="tracked", description="List all tracked X users")
async def tracked_cmd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    rows = await db.get_tracked(interaction.guild_id)
    if not rows:
        await interaction.followup.send("📭 No accounts tracked in this server.", ephemeral=True)
        return

    lines = []
    for r in rows:
        ch = bot.get_channel(r["channel_id"])
        ch_name = ch.mention if ch else f"#{r['channel_id']}"
        lines.append(f"• **@{r['username']}** → {ch_name} (since {r['added_at'][:10]})")

    embed = discord.Embed(
        title="📋 Tracked Accounts",
        description="\n".join(lines),
        color=0x3498DB,
    )
    await interaction.followup.send(embed=embed, ephemeral=True)


@bot.tree.command(name="check", description="Manually check a user's following now")
async def check_cmd(interaction: discord.Interaction, username: str):
    await interaction.response.defer(ephemeral=True)
    target = username.lower().lstrip("@")

    await interaction.followup.send(f"⏳ Scraping @{target}...", ephemeral=True)
    code, new_follows = await _track_one(target)

    if code == 2:
        await interaction.followup.send(f"❌ Scrape failed for @{target}.", ephemeral=True)
    elif code == 1 and new_follows:
        await interaction.followup.send(f"🟢 Found {len(new_follows)} new follow(s) — posting to channel.", ephemeral=True)
        for entry in await db.get_all_tracked():
            if entry["username"] == target:
                channel = bot.get_channel(entry["channel_id"])
                if channel:
                    for follow in new_follows:
                        embed = build_follow_embed(target, follow)
                        await channel.send(embed=embed)
                        await asyncio.sleep(0.3)
    else:
        state = await db.get_state(target)
        count = len(state["following"])
        await interaction.followup.send(f"📭 No new follows for @{target} ({count} tracked).", ephemeral=True)


@bot.tree.command(name="xhelp", description="Show X Tracker commands")
async def help_cmd(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🤖 X Following Tracker",
        description="Track who X users follow in real-time.",
        color=0x1DA1F2,
    )
    embed.add_field(name="/track @user", value="Start tracking a user's following", inline=False)
    embed.add_field(name="/untrack @user", value="Stop tracking", inline=False)
    embed.add_field(name="/tracked", value="List all tracked users", inline=False)
    embed.add_field(name="/check @user", value="Manual check now", inline=False)
    embed.add_field(name="Poll Interval", value=f"{POLL_INTERVAL // 60} min", inline=True)
    embed.set_footer(text="X Following Tracker Bot")
    await interaction.response.send_message(embed=embed, ephemeral=True)


# ── EVENTS ─────────────────────────────────────────────────────────────────────

@bot.event
async def on_ready():
    log.info(f"Logged in as {bot.user} (ID: {bot.user.id})")
    await bot.tree.sync()
    log.info("Slash commands synced")
    if not poll_following.is_running():
        poll_following.start()
        log.info(f"Polling started (every {POLL_INTERVAL}s)")


def run():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        stream=sys.stdout,
    )
    bot.run(DISCORD_TOKEN)
