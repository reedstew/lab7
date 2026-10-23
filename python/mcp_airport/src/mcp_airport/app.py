"""Entry point: PORT=8001 start-airport-server (HTTP) or no PORT for stdio."""

import os
import sys

from .server import create_mcp_server


def main() -> None:
    mcp = create_mcp_server()
    port = os.environ.get("PORT")
    if port:
        host = os.environ.get("HOST", "127.0.0.1")
        print(f"MCP airport server on http://{host}:{port}/mcp "
              f"(AIRPORT_ATTACK={os.environ.get('AIRPORT_ATTACK', 'off')})", file=sys.stderr)
        mcp.run(transport="http", host=host, port=int(port))
    else:
        mcp.run()


if __name__ == "__main__":
    main()
