---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-DIRTY-SET-DEDUPES-UPDATES-BY-ID-SO-RECYCLED-ADDRESSES-DROP-WORK
artifact_type: investigation
tags: [engine, determinism]
---

# Investigation: is the `id()` de-dup the cause of the `audit_mode` divergence?

Probe scripts are scratch (not in the repo). All runs: `frontier_living_world`, seed 42, `audit_mode=True`,
`max_tick_budget_ms=1e9`, `LocalSequentialExecutor`, `CanonicalStateHasher` per tick, `dropped_work_total` 0.
Trees: bare `origin/main` `820329124` plus only this ticket file (Scope 2), and the same plus the fix.

## Scope 1 (discriminator) and Scope 2 (bare `main`)

24 identical trials of 8 ticks per process, four processes, interleaved; the strong-reference arm keeps a
reference to every entity-update object so no address can be reused.

| arm (bare `main`) | processes with >1 trace | trials off the majority trace | `id()` skips per trial |
|---|---|---|---|
| plain | 3 of 4 | 8 of 96 | 52 to 56 |
| strong references | 0 of 4 | 0 of 96 | 0 |

Divergence is present on bare `main`, so it is not caused by the retreat, entity-target or bravery tickets. With
address reuse impossible it vanished, and the skip count went to zero: the `id()` de-duplication is the cause on
this window, the premise holds. Caveat: 8-tick trials, one world; the strong arm also perturbs allocation, but
only for update objects.

## Fix and re-measurement

`DirtySetBuilder.mark_from_update` no longer de-duplicates by identity (nothing is stored). Marking is idempotent
for one entity's own update (set adds; the `town` flag follows that update alone), so re-marking an update seen on
an earlier call changes nothing. Retaining references (the rejected alternative) would have traded the bug for a
leak. Fixed tree, six processes of 24 trials: 0 trials off the single trace (`7f73059b13`, the same trace as the
unfixed majority) in 144.

The ticket's "~56 skipped updates per 8-tick trial" figure is a property of the removed code, so there is nothing
left to re-measure after the fix; the equivalent after-fix statement is the 0 of 144 above.

## Scope 4 (`get_frozen`, `src/engine/executor.py:256-262`)

Probe: before each `LocalSequentialExecutor.execute`, compare the cached frozen view with a fresh `deep_freeze`
where the cached `id` equals the live attribute's `id`. 300 ticks of `frontier_living_world`: 300 calls, **0 id
matches, 0 stale hits.** Not live on this evidence; **not proven safe**, and 0 matches in 300 calls also means the
cache is rarely or never hit (not investigated). Left as is; if its hit rate ever rises it has the same reuse
hazard, because the cache stores the frozen result and not the source object.

## Not done

Full-length (2000-tick) runs after the fix; other worlds; the unexplained "second trace appears only after trial
7" pattern is not explained by this mechanism alone and was not chased (the strong-reference and fixed arms never
showed a second trace at all).
