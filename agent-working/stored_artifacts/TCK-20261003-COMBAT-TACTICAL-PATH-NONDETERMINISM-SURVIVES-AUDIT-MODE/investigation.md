---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE
artifact_type: investigation
tags: [engine, combat, determinism, root-cause]
---

# Investigation: run-to-run divergence that survives `audit_mode`

The full record, with the numbers, is in the ticket's `## Implementation Notes` (the citation of record; it is
not restated here so the two cannot disagree). Summary of method and result:

- **Method.** Four identical seed-42 `frontier_living_world` runs (2000 ticks) in fresh processes, plus a seed-43
  positive control, each with `audit_mode=True`, `max_tick_budget_ms=1e9`, `LocalSequentialExecutor`, the
  canonical state hash (`CanonicalStateHasher.get_hash`) and per-entity canonical hashes recorded every tick,
  with `total_dropped_work` and `RuntimeMode` read from the kernel's status. Then 8-tick trials, 16 to 24 per
  process, with the strategic work-queue's inputs and output recorded per call, and a shadow check for `id()`
  reuse in `DirtySetBuilder.mark_from_update`.
- **Result.** Confirmed (3 runs identical, 1 differing; one run diverged at tick 512 and re-converged); first
  divergent tick 5, entities 16 and 36; proximate mechanism measured (entity 16's strategic-dirty membership
  changes the work queue's tier-7 sweep selection at tick 4); upstream cause a strong but **unproven** lead
  (`id()`-keyed de-duplication, `src/core/dirty.py:142-146`).
- **Ruled out on evidence.** `tactical.py` as the source (divergence is in strategic scheduling before any
  tactical decision differs); the `kernel.py` mid-tick throttle and the governor (nothing dropped, mode 0).
- **Not done.** The strong-reference discriminator, a bare-`origin/main` comparison, the `get_frozen` cache in
  `src/engine/executor.py:257`, and an explanation for the second trace appearing only after trial 7 in three of
  five experiments. All handed to `TCK-20261005-DIRTY-SET-DEDUPES-UPDATES-BY-ID-SO-RECYCLED-ADDRESSES-DROP-WORK`.
