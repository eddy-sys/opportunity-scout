from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Iterable

from .http import fetch_json, fetch_text
from .models import Lead


USER_AGENT = "OpportunityScout/0.1 by local-user"
TAG_RE = re.compile(r"<[^>]+>")


def strip_html(value: str) -> str:
    return html.unescape(TAG_RE.sub(" ", value or " ")).strip()


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    try:
        parsed = parsedate_to_datetime(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def fetch_reddit_subreddit(subreddit: str, limit: int = 25) -> list[Lead]:
    url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
    payload = fetch_json(url, headers={"User-Agent": USER_AGENT})
    leads: list[Lead] = []
    for child in payload.get("data", {}).get("children", []):
        data = child.get("data", {})
        created_utc = data.get("created_utc")
        created_at = (
            datetime.fromtimestamp(float(created_utc), tz=timezone.utc)
            if created_utc is not None
            else None
        )
        permalink = data.get("permalink") or ""
        full_url = f"https://www.reddit.com{permalink}" if permalink else data.get("url", "")
        leads.append(
            Lead(
                source=f"reddit/r/{subreddit}",
                source_id=f"reddit:{data.get('id', full_url)}",
                url=full_url,
                title=data.get("title", "").strip(),
                author=data.get("author", ""),
                created_at=created_at,
                raw_text=strip_html(data.get("selftext") or data.get("url") or ""),
            )
        )
    return leads


def fetch_reddit(subreddits: Iterable[str], limit: int = 25) -> tuple[list[Lead], list[str]]:
    leads: list[Lead] = []
    errors: list[str] = []
    for subreddit in subreddits:
        try:
            leads.extend(fetch_reddit_subreddit(subreddit, limit=limit))
        except Exception as exc:  # Keep other sources alive.
            errors.append(f"reddit/r/{subreddit}: {exc}")
    return leads, errors


def child_text(node: ET.Element, names: tuple[str, ...]) -> str:
    for name in names:
        found = node.find(name)
        if found is not None and found.text:
            return found.text.strip()
    for child in node:
        bare_name = child.tag.rsplit("}", 1)[-1]
        if bare_name in names and child.text:
            return child.text.strip()
    return ""


def rss_items(root: ET.Element) -> list[ET.Element]:
    channel = root.find("channel")
    if channel is not None:
        return channel.findall("item")
    return [node for node in root.findall("{http://www.w3.org/2005/Atom}entry")] or root.findall("entry")


def fetch_rss_feed(feed_url: str) -> list[Lead]:
    xml_text = fetch_text(feed_url, headers={"User-Agent": USER_AGENT})
    root = ET.fromstring(xml_text)
    leads: list[Lead] = []
    for item in rss_items(root):
        title = child_text(item, ("title",))
        link = child_text(item, ("link",))
        if not link:
            link_node = item.find("{http://www.w3.org/2005/Atom}link") or item.find("link")
            link = link_node.attrib.get("href", "") if link_node is not None else ""
        guid = child_text(item, ("guid", "id")) or link or title
        published = child_text(item, ("pubDate", "published", "updated"))
        summary = child_text(item, ("description", "summary", "content"))
        leads.append(
            Lead(
                source=f"rss:{feed_url}",
                source_id=f"rss:{guid}",
                url=link,
                title=strip_html(title),
                author=child_text(item, ("author", "creator")),
                created_at=parse_datetime(published),
                raw_text=strip_html(summary),
            )
        )
    return leads


def fetch_rss(feeds: Iterable[str]) -> tuple[list[Lead], list[str]]:
    leads: list[Lead] = []
    errors: list[str] = []
    for feed_url in feeds:
        try:
            leads.extend(fetch_rss_feed(feed_url))
        except Exception as exc:
            errors.append(f"rss:{feed_url}: {exc}")
    return leads, errors
