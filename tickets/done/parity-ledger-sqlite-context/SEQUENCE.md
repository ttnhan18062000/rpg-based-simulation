# Implementation Sequence — parity-ledger-sqlite-context

Epic: `TCK-20260731-PARITY-INDEX-EPIC`. Source:
`docs/plans/agent_infrastructure/parity_ledger_sqlite_context/idea_parity_ledger_sqlite_context_integration.md`.

## Order

1. `TCK-20260731-PARITY-INDEX-BASELINE` — Phase 0 baseline and v1 decisions.
2. `TCK-20260731-PARITY-INDEX-IMPORTER` — Phase 1 deterministic all-shard index; depends on 1.
3. `TCK-20260731-PARITY-IMPACT-PROOF` — Phase 2 query/equivalence proof; depends on 2.
4. `TCK-20260731-PARITY-READPATH-GATE` — Gate A payoff decision; depends on 3.

## Safety Boundary

Every step is read-only with respect to `docs/parity_ledger/*.yaml`. The legacy eight-shard
scanner/static-gate behavior is a protected comparison baseline; it is not replaced in this
batch. No context packet, retrieval cache, workflow, hook, monitoring, or mutation feature is
enabled by these tickets.

