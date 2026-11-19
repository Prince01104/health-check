"""Daily health headlines from public RSS feeds. No API key. Pure Python, so it is easy to test.

Only the headline, the source name and a link are used. Nothing from the user is sent to the feed.
If every feed fails, the app simply shows its own health tips instead.
"""
from __future__ import annotations

import datetime as dt
import email.utils
import re
import urllib.request
import xml.etree.ElementTree as ET

FEEDS = [
    "https://news.google.com/rss/search?q=health+when:2d&hl=en-IN&gl=IN&ceid=IN:en",
    "https://www.who.int/rss-feeds/news-english.xml",
]
TIMEOUT = 5
MAX_BYTES = 1_000_000
# Headlines about violence or self-harm do not belong on a health-screening home screen.
BLOCK = re.compile(r"\b(suicide|self[- ]harm|murder|rape|killed|kills|dead body|massacre|porn)\b", re.I)


def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "HealthCheckApp/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:      # https only (see FEEDS)
        return resp.read(MAX_BYTES)


def _ago(pub: str | None) -> str:
    try:
        when = email.utils.parsedate_to_datetime(pub or "")
        mins = (dt.datetime.now(dt.timezone.utc) - when).total_seconds() / 60
    except (TypeError, ValueError):
        return ""
    if mins < 0:
        return ""
    if mins < 60:
        return f"{int(mins)} min ago"
    if mins < 24 * 60:
        return f"{int(mins // 60)} h ago"
    return f"{int(mins // (24 * 60))} d ago"


def parse(xml_bytes: bytes, default_source: str = "") -> list[dict]:
    """RSS bytes -> [{"title","source","link","ago"}]. Anything odd is skipped, never raised."""
    if b"<!DOCTYPE" in xml_bytes[:2000].upper() or b"<!ENTITY" in xml_bytes.upper():
        return []                                              # no DTDs in a news feed: refuse (entity tricks)
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return []
    out = []
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        src_el = item.find("source")
        source = ((src_el.text if src_el is not None else "") or default_source).strip()
        if " - " in title and not source:
            title, source = title.rsplit(" - ", 1)
        elif source and title.endswith(" - " + source):
            title = title[: -len(source) - 3]
        title = re.sub(r"\s+", " ", title).strip()
        if not title or not link.startswith("https://") or BLOCK.search(title):
            continue
        out.append({"title": title[:160], "source": source[:40] or "News", "link": link[:600],
                    "ago": _ago(item.findtext("pubDate"))})
    return out


def headlines(limit: int = 5, fetch=_fetch) -> list[dict]:
    """Try each feed in turn and return up to `limit` headlines (empty list if none work)."""
    for url in FEEDS:
        try:
            items = parse(fetch(url), "WHO" if "who.int" in url else "")
        except Exception:                                     # network down, blocked, timeout...
            continue
        seen, uniq = set(), []
        for it in items:
            key = it["title"].lower()[:60]
            if key not in seen:
                seen.add(key)
                uniq.append(it)
        if uniq:
            return uniq[:limit]
    return []
