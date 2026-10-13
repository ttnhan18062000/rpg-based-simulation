---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261012-SEARCH-MCP-SHARED-SERVER-AND-IDLE-UNLOAD
artifact_type: test_plan
tags: [ai, mcp, process-improvement]
---

# test_plan — TCK-20261012-SEARCH-MCP-SHARED-SERVER-AND-IDLE-UNLOAD

## Cases
- server and MCP return the same ids, order and scores for a fixture index (AC1)
- proxy used when health matches; model not loaded (AC2); fallback on refused, timeout, 503, mismatched fingerprint, failed search, switch off (AC3)
- real sockets for `_http_json`: ok, 503, slow, refused
- idle: timer armed as daemon, expiry unloads, later query cancels/rearms, 0 never unloads, next query reloads (AC4)
- `search_health` path and model_loaded (AC5); staleness computed locally on the proxy path (AC6)

## Proof Plan
- level: unit and socket-level tests plus a measured live run
- proof kind: behavioural tests and RSS measurement
- oracle source: ticket acceptance criteria AC1-AC8
- expected effect: identical answers from either path, no model in the MCP process when the server serves the same index, memory released when idle
- selected commands: `python -m pytest -q tests/tools/test_search_shared_path.py tests/tools/test_search_mcp.py tests/tools/test_search_server.py`; `python -m pytest tests/tools -k "search or mcp or knowledge"`; `git diff --stat -- .mcp.json`
