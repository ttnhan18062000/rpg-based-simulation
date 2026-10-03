# Sequence — knowledge-gateway-mcp-phase1

Dependency-ordered implementation sequence for `TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE1-EPIC`'s
5 child tickets. Strictly sequential — each ticket's Investigate phase should confirm its
dependencies are actually DONE before starting, per this repo's `implement-epic` convention.

1. `TCK-20260815-KGMCP-P1-QUERY-ROUTER` — no dependencies within this epic (consumes only Phase 0's
   already-frozen contracts).
2. `TCK-20260815-KGMCP-P1-PACKET-ASSEMBLY` — depends on (1) for routing decisions/raw provider
   results.
3. `TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE` — depends on (1) and (2); wires both into a real
   callable MCP server.
4. `TCK-20260815-KGMCP-P1-FAILOPEN-TESTS` — depends on (3); tests the real server's failure
   semantics.
5. `TCK-20260815-KGMCP-P1-BASELINE-COMPARISON` — depends on (3); measures the real server against
   the Phase 0 baseline corpus. Closes the epic's own acceptance loop — the epic should not close
   until this ticket's results are recorded, whether or not thresholds are met.

(4) and (5) both depend only on (3), not on each other — they may be reordered relative to each
other if a hand-orchestrating session finds it more efficient, but both must land before the epic
closes.
