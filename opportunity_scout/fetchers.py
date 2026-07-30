from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Iterable

from .http import fetch_text
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


def fetch_reddit_subreddit(subreddit: str) -> list[Lead]:
    # Reddit's public RSS feed — no auth required, unlike the JSON API
    rss_url = f"https://www.reddit.com/r/{subreddit}/new/.rss"
    leads = fetch_rss_feed(rss_url)
    # Normalise source label to match the original reddit/r/<name> format
    for lead in leads:
        lead.source = f"reddit/r/{subreddit}"
        if not lead.source_id.startswith("reddit:"):
            lead.source_id = f"reddit:{lead.source_id}"
    return leads


def fetch_reddit(subreddits: Iterable[str], limit: int = 25) -> tuple[list[Lead], list[str]]:
    leads: list[Lead] = []
    errors: list[str] = []
    for subreddit in subreddits:
        try:
            leads.extend(fetch_reddit_subreddit(subreddit))
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
