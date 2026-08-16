# Sequence — knowledge-gateway-mcp-phase3

Dependency-ordered implementation sequence for `TCK-20260816-KNOWLEDGE-GATEWAY-MCP-PHASE3-EPIC`'s
child tickets.

1. `TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS` — no dependencies within this epic
   (implements `cache_migration_plan.md`'s already-reserved `migration_002_add_level2_tables`
   against `knowledge-index/retrieval_cache.db`, adding a new real content-bearing table for
   §10.3's `CachedPacket` payload; leaves the existing marker-only `retrieval_packet_cache_rows`
   untouched).
2. `TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT` — depends on (1) for the row shape the
   assembled packet will eventually be written into (though this ticket's own scope is packet
   assembly/budget logic, not cache I/O); implements real multi-provider deduplication and real
   caller-budget enforcement in `tools/knowledge_gateway_packet_assembly.py`.
3. `TCK-20260816-KGMCP-P3-PACKET-DEPENDENCY-INVALIDATION` — depends on (1) for the schema's
   dependency-record columns/tables to populate; investigates reuse of
   `evidence_cache_identity_contract.md` §5's `changed_paths` intersection logic at the
   packet level.
4. `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING` — depends on (1), (2), and (3); wires
   real Level 2 cache lookup/write into the live `_run_knowledge_context()`, checking Level 2 first
   for an exact packet match and falling back to Level 1/live providers on a Level 2 miss.
5. `TCK-20260816-KGMCP-P3-PILOT-ACCEPTANCE-MEASUREMENT` — depends on (4); runs proposal §21's Phase
   3 pilot acceptance criteria honestly against the real Level 2 cache-hit path, reusing the frozen
   corpus/methodology precedent from Phase 1/Phase 2.

Strictly sequential — each ticket's Investigate phase should confirm its dependencies are DONE
before starting.
