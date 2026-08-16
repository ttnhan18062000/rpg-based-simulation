# Sequence — knowledge-gateway-mcp-phase4

Dependency-ordered implementation sequence for `TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE4-EPIC`'s
child tickets.

1. `TCK-20260816-KGMCP-P4-PARITY-ADAPTER` — no dependencies within this epic (wires the router's
   already-reserved `requirement_completeness_verification` row to a real
   `tools/parity_index.py`-backed adapter).
2. `TCK-20260816-KGMCP-P4-CHANGED-PATH-CONTEXT` — no hard dependency on (1), but its own
   Investigate phase should check whether (1) is DONE before considering the routing-integration
   option (b) (preferring the Parity adapter's `impact(changed_path=...)` call) available.
3. `TCK-20260816-KGMCP-P4-WORKFLOW-RECOMMENDATION-EVALUATION` — no dependency on (1) or (2);
   investigation-only, can run in any order relative to them, but sequenced third so its own
   evaluation can reference whatever real capabilities (1) and (2) added by the time it runs.
4. `TCK-20260816-KGMCP-P4-DIRECT-TOOL-COMPARISON` — depends on (1) and (2) both being DONE; measures
   the real gateway (with the Parity adapter and changed_paths option both live) against real
   direct-tool calls for the frozen 7-entry corpus.

Strictly sequential — each ticket's Investigate phase should confirm its dependencies are DONE
before starting.
