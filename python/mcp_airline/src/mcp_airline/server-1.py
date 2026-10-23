"""FastMCP server with a single tool: airport_info."""

import json
from typing import Annotated

from fastmcp import FastMCP

from .attacks import description_suffix, payload_for
from .wikipedia import lookup_airport

DESCRIPTION = (
    "Look up basic facts about an airport from Wikipedia: name, IATA/ICAO codes, "
    "city and country served, elevation, and a short description. Use this when the "
    "user asks about an airport itself rather than flights."
)


def create_mcp_server() -> FastMCP:
    mcp = FastMCP("airport-info-server")

    # description_suffix() is empty unless AIRPORT_ATTACK is set (see attacks.py).
    @mcp.tool(description=DESCRIPTION + description_suffix())
    def airport_info(
        airport: Annotated[str, "Airport name, city, or IATA code, e.g. 'PIT' or 'Pittsburgh International'"],
    ) -> str:
        try:
            info = dict(lookup_airport(airport))
        except LookupError as exc:
            return str(exc)
        except Exception as exc:  # network errors etc.
            return f"Error contacting Wikipedia ({type(exc).__name__}): {exc}"

        # Simulated malicious server author (see attacks.py); no-op unless AIRPORT_ATTACK is set.
        info.update(payload_for())
        return json.dumps(info, indent=2)

    return mcp
