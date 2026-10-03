---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261002-VISUAL-ASSETS-STORE-MCP-TOOLS
artifact_type: investigation
tags: [architecture, mcp, testing, documentation]
---

# Investigation — TCK-20261002-VISUAL-ASSETS-STORE-MCP-TOOLS

- `search_docs` / `graphify query` again return nothing relevant for `visual_assets/`; findings are from direct reads of the landed code.
- The boundary checker already forbids drawing code from naming the catalog (identifiers, string literals, imports of `visual_assets.catalog`), and from importing the human-gated and tracked-catalog layers (`adoption`, `revoke`, `catalogwrite`, `release`, `gc`). It does not yet restrict which other store layers the server imports.
- `export_handoff` returns a `handoff_id` (candidate id plus a hash of `package.json`); several handoffs may exist for one candidate and intake tells them apart (its id covers all three files).
- `intake` takes a directory and a `created_at`; the quarantine is the only thing it writes. The review area and the tracked catalog are never touched by intake.
- Existing tool-surface test forbids tool names containing `submit` and `store_`; those are exactly the new tools, so the test is replaced by an exact-set test plus a forbidden-verbs test.
