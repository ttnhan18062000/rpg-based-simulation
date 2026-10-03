# Sequence — knowledge-gateway-mcp-phase2

Dependency-ordered implementation sequence for `TCK-20260815-KNOWLEDGE-GATEWAY-MCP-PHASE2-EPIC`'s
child tickets.

1. `TCK-20260815-KGMCP-P2-CACHE-SCHEMA-MIGRATIONS` — no dependencies within this epic (implements
   `cache_migration_plan.md`'s already-designed migration functions against
   `knowledge-index/retrieval_cache.db`).
2. `TCK-20260815-KGMCP-P2-REDACTION-WRITE-PATH` — depends on (1) for the schema to write into;
   implements `redaction_retention_policy.md`'s rules as real code for the first time.
3. `TCK-20260815-KGMCP-P2-CACHE-READ-WRITE-WIRING` — depends on (1) and (2); wires cache
   lookup/fingerprint-validation/write into the real Phase 1 gateway call path.
4. `TCK-20260815-KGMCP-P2-BASELINE-RECOMPARISON` — depends on (3); re-runs the Phase 1
   acceptance-measurement methodology against the real cache-hit path, honestly reporting §4.1/§4.2.

Strictly sequential — each ticket's Investigate phase should confirm its dependencies are DONE
before starting.
