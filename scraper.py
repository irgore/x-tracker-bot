"""X/Twitter following-list scraper — Playwright-based (optimized for speed)."""
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"


def enrich_profile(handle: str) -> dict:
    """Fetch profile via FxTwitter API with retry."""
    import logging
    log = logging.getLogger("x-tracker")
    for attempt in range(3):
        try:
            r = httpx.get(f"https://api.fxtwitter.com/{handle}", timeout=15, follow_redirects=True)
            if r.status_code == 200:
                data = r.json()
                user = data.get("user", {})
                if user:
                    # FxTwitter puts verified inside verification object
                    if "verified" not in user and "verification" in user:
                        user["verified"] = user["verification"].get("verified", False)
                    log.info(f"✅ FxTwitter OK for @{handle}: {user.get('followers', 0)} followers")
                    return user
                else:
                    log.warning(f"⚠️ FxTwitter returned no user data for @{handle}: {data.get('message', 'unknown')}")
            elif r.status_code == 429:
                log.warning(f"⚠️ FxTwitter rate-limited for @{handle}, attempt {attempt+1}/3")
                import time; time.sleep(2 * (attempt + 1))
                continue
            else:
                log.warning(f"⚠️ FxTwitter {r.status_code} for @{handle}: {r.text[:200]}")
        except Exception as e:
            log.error(f"❌ FxTwitter error for @{handle} (attempt {attempt+1}/3): {e}")
            import time; time.sleep(1)
    log.error(f"❌ FxTwitter failed for @{handle} after 3 attempts")
    return {}


def _classify_account(followers: int, age_days: int, verified: bool) -> tuple[int, str, str, int]:
    """Returns (tier_emoji, tier_label, color_hex, discord_color)."""
    if followers > 100_000:
        return "🔥", "Mega", "gold", 0xFFD700
    elif followers > 10_000:
        return "⭐", "Big", "purple", 0x9B59B6
    elif followers > 1_000:
        return "📈", "Mid", "blue", 0x3498DB
    elif followers > 100:
        return "🌱", "Small", "green", 0x2ECC71
    else:
        return "🐣", "Micro", "gray", 0x95A5A6


def _account_age_days(joined_str: str) -> int:
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(joined_str)
        return (datetime.now(timezone.utc) - dt).days
    except Exception:
        return -1


def _years_ago(joined_str: str) -> str:
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(joined_str)
        delta = datetime.now(timezone.utc) - dt
        years = delta.days // 365
        if years > 0:
            return f"{years} year{'s' if years > 1 else ''} ago"
        months = delta.days // 30
        if months > 0:
            return f"{months} month{'s' if months > 1 else ''} ago"
        return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
    except Exception:
        return joined_str or "unknown"


def build_follow_embed(target: str, f: dict) -> dict:
    """Build a Discord embed dict for a new follow."""
    import discord

    profile = enrich_profile(f["username"])
    if not profile:
        import logging
        logging.getLogger("x-tracker").warning(f"⚠️ FxTwitter empty for @{f['username']}, using scraped data only")
    followers = profile.get("followers", 0)
    following_count = profile.get("following", 0)
    tweets = profile.get("tweets", 0)
    joined = profile.get("joined", "")
    verified = profile.get("verified", False)
    avatar = profile.get("avatar_url", "").replace("_normal", "_400x400") or f.get("avatar", "").replace("_normal", "_400x400")
    banner = profile.get("banner_url", "")
    bio = profile.get("description", "") or f.get("bio", "")
    name = profile.get("name", "") or f.get("display_name", f["username"])
    location = profile.get("location", "")

    age_days = _account_age_days(joined)
    tier_emoji, tier_label, _, color = _classify_account(followers, age_days, verified)

    warnings = []
    if 0 < age_days < 30:
        warnings.append("⚠️ New account (<30d)")
    elif 0 < age_days < 90:
        warnings.append("🕐 Young account (<90d)")
    if verified:
        warnings.append("✓ Verified")
    if followers < 100 and 0 < age_days < 90:
        warnings.append("🚨 Low followers + new = likely throwaway")

    desc_parts = [f"{tier_emoji} **{tier_label}** account"]
    if warnings:
        desc_parts.append(" · ".join(warnings))
    if bio:
        desc_parts.append(f"\n> {bio[:380]}")

    links = (
        f"[Profile](https://x.com/{f['username']}) · "
        f"[Tweets](https://x.com/{f['username']}/with_replies) · "
        f"[Search](https://x.com/search?q=from%3A{f['username']}) · "
        f"[Archive](https://archive.org/search?query={f['username']})"
    )
    desc_parts.append(links)

    embed = discord.Embed(
        title=f"{'✓ ' if verified else ''}@{f['username']}",
        url=f"https://x.com/{f['username']}",
        description="\n".join(desc_parts),
        color=color,
    )
    embed.set_author(name=f"🟢 @{target} just followed")
    embed.add_field(name="Name", value=name, inline=True)
    embed.add_field(name="Followers", value=f"{followers:,}", inline=True)
    embed.add_field(name="Following", value=f"{following_count:,}", inline=True)
    embed.add_field(name="Tweets", value=f"{tweets:,}", inline=True)
    embed.add_field(name="Created", value=_years_ago(joined), inline=True)
    if location:
        embed.add_field(name="Location", value=location, inline=True)
    if avatar:
        embed.set_thumbnail(url=avatar)
    if banner:
        embed.set_image(url=banner)
    embed.set_footer(text="X Following Tracker")
    return embed


def fetch_following(target: str, *, headless: bool = True, scroll_max: int = 15,
                    storage_state: Optional[str] = None) -> list[dict]:
    """Scrape the /following page of a target X user via Playwright.
    
    Optimized for speed: shorter waits, fewer scrolls, early exit.
    """
    from playwright.sync_api import sync_playwright

    results = []
    seen = set()
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        ctx_opts = {"user_agent": UA, "viewport": {"width": 1280, "height": 900}}
        if storage_state and Path(storage_state).exists():
            context = browser.new_context(storage_state=storage_state, **ctx_opts)
        else:
            context = browser.new_context(**ctx_opts)

        page = context.new_page()
        page.set_extra_http_headers({"Accept-Language": "en-US,en;q=0.9"})
        url = f"https://x.com/{target}/following"

        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20_000)
            # Wait for UserCell to appear (max 10s) instead of fixed sleep
            try:
                page.wait_for_selector('[data-testid="UserCell"]', timeout=10_000)
            except Exception:
                page.wait_for_timeout(3000)  # fallback
        except Exception as e:
            print(f"  [!] Failed to load {url}: {e}", file=sys.stderr)
            browser.close()
            return []

        # Check if redirected to profile (not logged in)
        if "/following" not in page.url:
            print(f"  [!] Redirected to {page.url} — login required", file=sys.stderr)
            browser.close()
            return []

        empty_streak = 0
        for i in range(scroll_max):
            cells = page.query_selector_all('[data-testid="UserCell"]')
            new_this_scroll = 0
            for cell in cells:
                try:
                    links = cell.query_selector_all('a[href^="/"]')
                    if not links:
                        continue
                    href = links[0].get_attribute("href") or ""
                    handle = href.strip("/").split("/")[0]
                    if not handle or handle in ("i", "search", "settings", "explore", "home"):
                        continue
                    if handle in seen:
                        continue

                    cell_text = (cell.inner_text() or "").lower()
                    if any(kw in cell_text for kw in ["click to follow", "follow back", "suggested for you"]):
                        continue

                    display_name = ""
                    name_el = cell.query_selector('div[dir="ltr"] span')
                    if name_el:
                        display_name = (name_el.inner_text() or "").strip()

                    bio = ""
                    bio_els = cell.query_selector_all('div[dir="auto"]')
                    if bio_els:
                        bio = (bio_els[-1].inner_text() or "").strip()[:300]

                    avatar = ""
                    img_el = cell.query_selector('img[src*="profile_images"]')
                    if img_el:
                        avatar = img_el.get_attribute("src") or ""

                    seen.add(handle)
                    results.append({"username": handle.lower(), "display_name": display_name, "bio": bio, "avatar": avatar})
                    new_this_scroll += 1
                except Exception:
                    continue

            empty_streak = 0 if new_this_scroll > 0 else empty_streak + 1
            if empty_streak >= 2:  # reduced from 3
                break

            page.evaluate("window.scrollBy(0, 800)")
            page.wait_for_timeout(1000)  # reduced from 1500

        browser.close()
    return results
