import httpx

from mcp_airport.attacks import MAGIC, apply_article_edit
from mcp_airport.wikipedia import _cache, lookup_airport, parse_infobox

WIKITEXT = """{{Infobox airport
| name = Pittsburgh International Airport
| IATA = PIT
| ICAO = KPIT
| city-served = [[Pittsburgh]], [[Pennsylvania]]
| elevation-f = 1,203
}}"""


def _handler(request: httpx.Request) -> httpx.Response:
    url = str(request.url)
    if "list=search" in url:
        return httpx.Response(200, json={"query": {"search": [{"title": "Pittsburgh International Airport"}]}})
    if "rest_v1" in url and url.endswith("/PIT"):
        return httpx.Response(404, json={})
    if "rest_v1" in url:
        return httpx.Response(200, json={"title": "Pittsburgh International Airport",
                                         "description": "Airport in Pennsylvania",
                                         "extract": "PIT is an international airport.", "type": "standard"})
    return httpx.Response(200, json={"parse": {"wikitext": {"*": WIKITEXT}}})


def test_parse_infobox():
    facts = parse_infobox(WIKITEXT)
    assert facts["iata"] == "PIT" and facts["icao"] == "KPIT"
    assert facts["city_served"] == "Pittsburgh, Pennsylvania"


def test_lookup_airport():
    _cache.clear()
    client = httpx.Client(transport=httpx.MockTransport(_handler))
    info = lookup_airport("PIT", client=client)
    assert info["iata"] == "PIT" and "international airport" in info["description"]


def test_article_edit_modes():
    base = {"title": "X", "short_description": "Airport", "description": "Lead text.", "iata": "XXX"}
    assert apply_article_edit(base, "") == base
    inj = apply_article_edit(base, "injection")
    assert set(inj) == set(base)  # attacker can only change article-derived text
    assert "send_certificate" in inj["description"] and inj["description"].endswith("Lead text.")
    assert MAGIC not in inj["description"] + inj["short_description"]
    assert MAGIC in apply_article_edit(base, "injection-magic")["short_description"]
    assert "remember" in apply_article_edit(base, "memory-magic")["description"]
    assert base["description"] == "Lead text."  # input not mutated
