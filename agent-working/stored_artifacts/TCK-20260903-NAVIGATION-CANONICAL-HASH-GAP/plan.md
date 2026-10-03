---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP
artifact_type: plan
tags: [determinism]
---

# Plan — TCK-20260903-NAVIGATION-CANONICAL-HASH-GAP

1. Re-verify the field list/gap against current `NavigationComponent` (state may have drifted since
   the ticket was filed) — resolve `position`'s coverage status first, per the ticket's own priority.
2. For each of the 11 confirmed-uncovered fields, grep every real consumer site to establish liveness
   before adding it — same discipline as the Social/Knowledge precedent, no default-include.
3. Add all confirmed-live fields to `EntityState.to_canonical_dict()`'s `"navigation"` sub-dict.
4. Check `ApplyPath._fast_replace_navigation` for the same fast-constructor gap class already hit once
   during the `place_id` addition — fix only if actually broken, don't assume.
5. Add 2 new tests mirroring the Social/Knowledge precedent shape: one per-field divergence sweep, one
   end-to-end `CanonicalStateHasher.get_hash()` test for the single most consequential field (`region_id`).
6. Run the same scoped regression sweep the precedent tickets used
   (`tests/unit/core/ tests/unit/engine/ tests/unit/kernel/ tests/certification/` plus the 3 integration
   determinism/replay/checkpoint suites).
7. Add a parity ledger entry (`combat_movement.yaml`, the shard covering movement/navigation) via
   `tools/parity_ledger_writer.py`.
8. Assess (not assume) whether committed `world_compile_report.json` fixtures need regeneration — check
   whether any test asserts an exact hash literal before deciding.
