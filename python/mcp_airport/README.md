# Airport Info MCP Server

One tool, `airport_info(airport)`, backed by Wikipedia.

```bash
uv pip install -e .            # or: pip install -e .
PORT=8001 start-airport-server
npx @modelcontextprotocol/inspector http://localhost:8001/mcp
```

Set `WIKIPEDIA_CONTACT` (your email or GitHub URL): Wikimedia blocks requests without a contactable User-Agent.

`AIRPORT_ATTACK` simulates a compromised source for Tasks 2 and 3 (see `attacks.py`):
`injection`, `injection-magic`, `memory`, `memory-magic`. Unset = benign.
