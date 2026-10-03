---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260902-SOCIAL-CANONICAL-HASH-GAP
artifact_type: plan
tags: [social, determinism]
---

# Plan — TCK-20260902-SOCIAL-CANONICAL-HASH-GAP

1. Re-verify the field gap against current `src/core/models/social.py`/`src/core/state.py` (undercount
   found and corrected — see investigation.md).
2. Add the 7 confirmed-live fields to `EntityState.to_canonical_dict()`'s `"social"` sub-dict.
   `nemesis_ids` (a `Set[int]`) serialized via `sorted(...)`, not `asdict`.
3. Add regression tests in `tests/unit/core/test_entity_integrity.py`: one covering all 7 fields in a
   loop, one dedicated end-to-end `CanonicalStateHasher.get_hash()` check on `nemesis_ids` (mirroring the
   Knowledge ticket's `source_trust`-specific test).
4. Run the existing canonical-hash/determinism/social-domain test suites unchanged.
5. Add a parity ledger entry (`SOC-263`) via `tools/parity_ledger_writer.py`.
6. Land independently from `TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP`, per that ticket's own explicit
   "do not batch" scope guard — separate branch/PR.
