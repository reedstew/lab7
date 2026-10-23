"""Minimal Wikipedia client: find an airport article and extract basic facts."""

import os
import re
import time
from typing import Optional

import httpx

API = "https://en.wikipedia.org/w/api.php"
SUMMARY = "https://en.wikipedia.org/api/rest_v1/page/summary/"

# Wikimedia's robot policy requires a descriptive User-Agent with a way to contact you,
# otherwise requests get throttled or blocked (403/429). Set WIKIPEDIA_CONTACT to your
# email or GitHub URL before starting the server.
CONTACT = os.environ.get("WIKIPEDIA_CONTACT", "https://github.com/cmu-seai/airline-support-agent-template-f26")
HEADERS = {"User-Agent": f"mlip-lab7-airport-mcp/0.1 ({CONTACT}; CMU course lab) httpx"}

_cache: dict = {}  # query -> result, so repeated questions don't hit Wikipedia again

# Infobox fields we report, mapped to output keys
INFOBOX_FIELDS = {
    "iata": "iata",
    "icao": "icao",
    "city-served": "city_served",
    "location": "location",
    "elevation-f": "elevation_ft",
    "website": "website",
}


def _clean(value: str) -> str:
    """Strip wiki markup ([[a|b]], templates, refs, HTML) from an infobox value."""
    value = re.sub(r"<ref.*?(</ref>|/>)", "", value, flags=re.S)
    value = re.sub(r"<[^>]+>", "", value)
    value = re.sub(r"\{\{[^{}]*\}\}", "", value)
    value = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]*)\]\]", r"\1", value)
    return value.strip(" \n,")


def parse_infobox(wikitext: str) -> dict:
    """Extract selected `| key = value` lines from the article's infobox."""
    facts = {}
    for key, out in INFOBOX_FIELDS.items():
        m = re.search(rf"^\|\s*{re.escape(key)}\s*=\s*(.+)$", wikitext, flags=re.M | re.I)
        if m and (cleaned := _clean(m.group(1))):
            facts[out] = cleaned
    return facts


def _get_json(client: httpx.Client, url: str, params: Optional[dict] = None) -> dict:
    resp = client.get(url, params=params)
    if resp.status_code == 429:  # rate limited: wait once as instructed, then retry
        time.sleep(min(float(resp.headers.get("retry-after", 2)), 10))
        resp = client.get(url, params=params)
    resp.raise_for_status()
    return resp.json()


def lookup_airport(query: str, client: Optional[httpx.Client] = None) -> dict:
    """Return title, description and key facts for an airport from Wikipedia.

    Tries the REST summary directly first (works for exact titles and redirects such as
    "PIT"), then falls back to a search. The infobox is best-effort.
    Raises LookupError if no article is found.
    """
    key = query.strip().lower()
    if key in _cache:
        return _cache[key]
    own = client is None
    client = client or httpx.Client(headers=HEADERS, timeout=10, follow_redirects=True)
    try:
        summary = None
        for candidate in (query, f"{query} airport"):
            try:
                data = _get_json(client, SUMMARY + candidate.strip().replace(" ", "_"))
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404:
                    continue
                raise
            if data.get("type") == "standard":
                summary = data
                break

        if summary is None:
            search = _get_json(client, API, {
                "action": "query", "list": "search", "format": "json", "srlimit": 1,
                "srsearch": f"{query} airport",
            })
            hits = search.get("query", {}).get("search", [])
            if not hits:
                raise LookupError(f"No Wikipedia article found for '{query}'")
            summary = _get_json(client, SUMMARY + hits[0]["title"].replace(" ", "_"))

        title = summary.get("title", query)
        facts = {}
        try:
            parsed = _get_json(client, API, {
                "action": "parse", "page": title, "prop": "wikitext", "section": 0, "format": "json",
            })
            facts = parse_infobox(parsed.get("parse", {}).get("wikitext", {}).get("*", ""))
        except Exception:
            pass  # infobox is optional; the summary alone is enough

        result = {
            "title": title,
            "short_description": summary.get("description", ""),
            "description": summary.get("extract", ""),
            **facts,
            "url": summary.get("content_urls", {}).get("desktop", {}).get("page", ""),
        }
        _cache[key] = result
        return result
    finally:
        if own:
            client.close()
