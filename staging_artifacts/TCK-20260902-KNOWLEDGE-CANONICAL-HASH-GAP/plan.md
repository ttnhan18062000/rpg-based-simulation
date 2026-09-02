---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP
artifact_type: plan
tags: [cognition, determinism]
---

# Plan — TCK-20260902-KNOWLEDGE-CANONICAL-HASH-GAP

1. Re-verify the 6-field gap from `investigation.md` directly against current `src/core/state.py:768-783`.
2. Resolve `source_trust` first: check for any prior observed replay-mismatch incident referencing it
   (search `agent-monitoring/` and past hotfix tickets) before deciding — if none is found, that is not
   evidence it's safe to exclude, only that no one has caught it yet; default to adding it.
3. For each of the remaining 5 fields, decide covered-vs-excluded and record the reasoning inline as a
   code comment where excluded.
4. Implement `to_canonical_dict()` changes for the fields decided as covered.
5. Add/update a determinism test per added field, `source_trust` first: construct two entities differing
   only in that field, assert their canonical hashes differ (fails pre-fix, passes post-fix).
6. Run existing canonical-hash/replay determinism test suite unchanged — must still pass.
7. Update `docs/parity_ledger/strategic_cognition.yaml` via `tools/parity_ledger_writer.py` with the new
   coverage status and real test-path evidence.
8. Update `docs/core/state.md` if it states a `StrategicComponent` field count.
9. Check whether any committed `world_compile_report.json` fixture's `state_hash` changes; if so,
   regenerate and note it explicitly in Implementation Notes.
