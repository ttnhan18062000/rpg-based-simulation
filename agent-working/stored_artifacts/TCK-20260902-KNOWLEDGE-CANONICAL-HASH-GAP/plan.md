---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP
artifact_type: plan
tags: [cognition, determinism]
---

# Plan — TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP

1. Re-verify the field gap against current `src/core/strategic.py`/`src/core/state.py` (drift found and
   corrected — see investigation.md).
2. Add the 9 confirmed-live fields to `EntityState.to_canonical_dict()`'s `"strategic"` sub-dict;
   exclude `profile` with an inline comment.
3. Handle enum fields (`ContractState.kind`/`status`, `TurningPointState.kind`) with explicit `str()`,
   matching the existing `projects` field convention. Handle `source_trust`'s int keys with `str()`,
   matching the existing int-keyed history-dict convention.
4. Add regression tests in `tests/unit/core/test_entity_integrity.py`, mirroring the existing
   `test_self_model_participates_in_canonical_hash` precedent: one dedicated to `source_trust` (P0
   severity), one covering the other 8 fields, one confirming `profile`'s exclusion is intentional (not a
   left-over gap).
5. Run the existing canonical-hash/determinism/certification test suites unchanged.
6. Add a parity ledger entry (`STRAT-268`) via `tools/parity_ledger_writer.py`.
7. Correct the ticket's own stale claims (consumer, field count, misfiled doc path) before closing.
