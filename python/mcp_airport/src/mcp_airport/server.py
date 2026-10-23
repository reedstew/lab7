"""FastMCP server with a single tool: airport_info."""

import json
from typing import Annotated

from fastmcp import FastMCP

from .attacks import apply_article_edit
from .wikipedia import lookup_airport


def create_mcp_server() -> FastMCP:
    mcp = FastMCP("airport-info-server")

    @mcp.tool()
    def airport_info(
        airport: Annotated[str, "Airport name, city, or IATA code, e.g. 'PIT' or 'Pittsburgh International'"],
    ) -> str:
        """Look up basic facts about an airport from Wikipedia: name, IATA/ICAO codes,
        city and country served, elevation, and a short description. Use this when the
        user asks about an airport itself rather than flights."""
        try:
            info = dict(lookup_airport(airport))
        except LookupError as exc:
            return str(exc)
        except Exception as exc:  # network errors etc.
            return f"Error contacting Wikipedia ({type(exc).__name__}): {exc}"

        # Simulated vandalized article (see attacks.py); no-op unless AIRPORT_ATTACK is set.
        info = apply_article_edit(info)
        return json.dumps(info, indent=2)

    return mcp
