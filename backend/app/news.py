"""
Daily news headlines for Signal context.
Fetches top stories from RSS feeds — no API key required.
"""
import asyncio
import requests
import xml.etree.ElementTree as ET
from datetime import date

RSS_FEEDS = [
    ("BBC News", "https://feeds.bbci.co.uk/news/rss.xml"),
    ("The Guardian", "https://www.theguardian.com/world/rss"),
]

_cache: dict = {"date": None, "headlines": []}


def _fetch_sync(max_headlines: int) -> list[str]:
    global _cache
    today = date.today()
    if _cache["date"] == today and _cache["headlines"]:
        return _cache["headlines"]

    headlines = []
    for name, url in RSS_FEEDS:
        try:
            resp = requests.get(
                url,
                timeout=5,
                headers={"User-Agent": "Mozilla/5.0 (compatible; KuleshovBot/1.0)"},
            )
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item")[:max_headlines]:
                title = item.findtext("title", "").strip()
                if title:
                    headlines.append(title)
            if headlines:
                break
        except Exception as e:
            print(f"⚠️  News fetch failed ({name}): {e}")

    _cache = {"date": today, "headlines": headlines[:max_headlines]}
    return _cache["headlines"]


async def fetch_headlines(max_headlines: int = 5) -> list[str]:
    """Return today's top headlines (cached per day, non-blocking)."""
    return await asyncio.to_thread(_fetch_sync, max_headlines)
