---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-MCP-TOOLS
artifact_type: plan
tags: [architecture, mcp, testing, documentation]
---

# Plan — TCK-20261002-VISUAL-ASSETS-STORE-MCP-TOOLS

1. `store/readmodel.py`: shaped, bounded, read-only listing and summaries of intakes, sources, artifacts and release candidates (no raw file contents, no absolute paths). It lives in the store because drawing code may not even mention the catalog.
2. `drawing/handoff.handoff_directory(handoff_id)`: validates the id pattern and resolves it inside the experiment workspace (never a caller-supplied path).
3. `drawing/server/store_readonly_tools.py`: `submit_candidate(handoff_id)`, `store_list(kind)`, `store_show(kind, id)`; server instructions state the gates in one sentence.
4. Boundary rule: the drawing `server` may import from the store only an explicit allowlist (`intake`, `readmodel`, `contracts`, `identities`, `errors`, `config`); every other store layer is a violation, with planted tests.
5. Tests: read model and handoff lookup in CI; exact tool surface; stdio tests (with Aseprite for the real chain); one test comparing the documented command names to the CLI parser.
6. Docs rewritten from "designed" to built, with a command table (gate, writes, tracked); plan and ADR; status notes in the two older plan READMEs; epic close-out and moving the folder.

## Where the ticket and reality differ
- The ticket names `store.catalog.release`; it is `store/release.py`. The boundary rule becomes an allowlist for the server (stricter than the gate-layer blacklist).
- Drawing code may not reference the catalog at all, so the listing logic is a store layer (`readmodel`), not code in the tool module.
- The tool module reads the clock for `created_at` (like the CLI; library code never does).
