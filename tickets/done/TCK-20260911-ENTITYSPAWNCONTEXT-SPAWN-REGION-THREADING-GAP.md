---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260911-ENTITYSPAWNCONTEXT-SPAWN-REGION-THREADING-GAP
phase: done
date: 2026-09-11
tags: [world]
---

# TCK-20260911-ENTITYSPAWNCONTEXT-SPAWN-REGION-THREADING-GAP

## Title
`WorldEntitySpawner.spawn_from_context()` hardcodes `EntitySpawnContext.spawn_region=None` — no campaign-spawned entity's authored spawn region reaches the live entity, even though the plumbing to carry it exists

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
Found during `TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION`'s own
investigation, while checking whether a survivor's original `spawn_region` could be recovered from
anywhere on the live entity instead of adding a new `EntityCarryForward` field. It cannot, and this
is why: `WorldEntitySpawner.spawn_from_context()` (`src/worldassembly/entity_spawner.py:58-60`)
constructs every entity's `EntitySpawnContext` with `spawn_region=None`, unconditionally —

```python
spawn = EntitySpawnContext(
    position=position,
    spawn_region=None,
    initial_alive=True,
    initial_active=True,
)
```

— even though `EntitySpawnContext.spawn_region` is a real field, and
`src/entities/archetype_factory.py:66-67` already has live code that would thread it into the
built entity's `properties["spawn_region"]` if given a non-`None` value:

```python
if spawn.spawn_region is not None:
    properties["spawn_region"] = spawn.spawn_region
```

The `profile` object `spawn_from_context()` iterates over (a `ResolvedEntityProfile`) already
knows its own resolved `spawn_position` (an x/y tuple) at this point — Batch B
(`TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION`) threaded that through. The *region name*
(`spawn_region`, a string) that position was resolved from is a different, separate piece of
information that was never threaded the same way — `spawn_from_context()` simply never looks it up
from the profile/context to pass along.

Net effect: `properties["spawn_region"]` — despite the write-side code existing and being
reachable — is always `None`-guarded-off in practice for every campaign-spawned entity, and has
**zero readers anywhere in `src/`** even when set by a different, non-campaign caller. Structurally
this is the same "write with no consumer" shape the unreachable-code audit
(`TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT`) found repeatedly elsewhere — not filed there
because it's inert-by-construction rather than dead code proper (the write path exists but the
value feeding it is always `None`), and because at audit time nothing depended on it being fixed.

**That's no longer true.** `TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION`'s own
`docs/plans/deferred_tuning_decisions_register.md` (D-07) now depends on this gap being closed if
the narrative answer to "where should survivors reappear" is ever decided to be "their original
authored region" rather than "their last known position" (the wiring fix's current pragmatic
default, chosen specifically because `spawn_region` isn't recoverable today).

## Scope
- Confirm the exact plumbing gap: does `CompileContext`/`ResolvedEntityProfile` (or something
  reachable from `spawn_from_context()`'s own `ctx`/`profile` arguments) already know each entity's
  originating `spawn_region`, or does that information itself need threading further upstream
  first (e.g. from `PopulationSpec.spawn_region` through `resolver.py`'s profile construction)?
  Do not assume — Batch B's own investigation may already answer this; re-check rather than infer.
- Record a disposition: **wire it** (thread `spawn_region` from the profile into
  `EntitySpawnContext`, confirm `properties["spawn_region"]` is then genuinely populated and
  useful) or **delete the dead write path** (`archetype_factory.py:66-67` and the
  `EntitySpawnContext.spawn_region` field) if, on closer investigation, nothing would ever consume
  it even once wired — matching this whole audit arc's own superseded-vs-missing discipline: don't
  wire on the pre-judged assumption that wiring is automatically the right call.
- This is a hotfix-tier disposition-only ticket per the established pattern from the
  `*-DEAD-CODE-DISPOSITION` tickets — if "wire it" is the finding and something bigger than a
  narrow plumbing fix turns up (e.g. `properties["spawn_region"]` itself needs a real consumer
  built, not just a value to hold), re-scope as a standard-tier ticket rather than scope-creeping
  this one.

## Out of Scope
- Actually changing D-07's narrative disposition (last-known-position vs. authored-region) — that
  remains an open campaign-design question, not something this ticket's own wiring fix decides.
- `TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION`'s own `last_position` fix —
  proceeds independently, does not wait on this ticket.

## Acceptance Criteria
- [x] Confirmed whether `spawn_region` is available to `spawn_from_context()` today (via
      `ctx`/`profile`) or needs upstream threading too. **It needed upstream threading** —
      `ResolvedEntityProfile` had no `spawn_region` field at all (only `spawn_position`), so
      `resolver.py` was computing `pop_spec.spawn_region` for position resolution but never passing
      it into the profile object `spawn_from_context()` actually reads.
- [x] A disposition (wire / delete-the-dead-write-path) recorded with rationale. **Wire it** — cheap
      (one new field, two `resolver.py` call sites, one hardcoded-`None` fix), and not aged-out like
      the optimization package: the classic `WorldCompiler.compile()` pipeline already sets
      `properties["spawn_region"]` correctly; this was purely the archetype-native pipeline never
      getting the same treatment.
- [x] `properties["spawn_region"]` genuinely reflects each entity's real originating region
      post-fix, verified by a real test
      (`test_spawn_region_threads_into_entity_properties`), not just by absence of errors.
- [x] Legacy-guard path (no `archetype_id`) confirmed unaffected — it never read `spawn.spawn_region`
      before or after this fix, verified by `test_spawn_region_none_when_profile_has_none`.
- [x] No regression in `tests/integration/worldassembly/`, `tests/unit/worldassembly/`,
      `tests/integration/campaigns/`. 10 of 11 initially-observed `test_corpus_diversity.py`
      failures reproduced identically against a pre-fix baseline (confirmed by reverting this
      ticket's 3 diffed files and re-running the same 11 tests) — pre-existing environment/timing
      flakiness (wall-clock kernel throttle, `kernel.py:585-596`, non-deterministic under
      `audit_mode=False`), not caused by this change. Not touched per Gate Integrity.

## Related Tickets
- `TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION` (origin of this finding;
  D-07's own narrative-disposition question depends on this if "authored region" is ever chosen)
- `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION` (Batch B — the sibling mechanism that
  did thread `spawn_position` through the same `spawn_from_context()` call, for comparison)
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (same "write with no consumer" shape, not
  filed there since it wasn't yet load-bearing for any open decision)
- `TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH` (open, gated behind the
  knowledge-layer disposition) — cross-referenced there as a working precedent: this ticket's fix
  pattern (add a field to `ResolvedEntityProfile`, set it at both `resolver.py` construction sites,
  read it at `spawn_from_context()` instead of hardcoding a default) is the same shape that
  ticket's own Direction 1 (tag `population_id` in `WorldEntitySpawner`) would need.

## Related Docs
- `docs/plans/deferred_tuning_decisions_register.md` D-07 — **amended 2026-09-13**: the threading
  gap this ticket named is now closed, but only partway. `identity.properties["spawn_region"]` is
  now genuinely populated; `EntityCarryForward` (no region field exists on it) and
  `StrategicComponent.home_region_id` (a separate, real mechanism for a different purpose) are
  still not reached. D-07's own "authored region" survivor-placement option is **not yet viable**
  — that needs a further, separate hop (campaign-side carry-forward of `properties["spawn_region"]`
  at episode end), not a byproduct of this fix.
- `docs/world/assembly_contract.md` (the determinism contract `spawn_from_context()` operates
  under — preserved: the fix reads an existing, already-deterministic profile field, no new
  randomness or ordering dependency introduced)

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- `src/worldassembly/entity_spawner.py` (`WorldEntitySpawner.spawn_from_context()`,
  `EntitySpawnContext(spawn_region=None, ...)`)
- `src/entities/archetype_factory.py` (`ArchetypeEntityFactory.build_entity()`, lines 66-67)
- `src/worldassembly/models.py` (`ResolvedEntityProfile` — check whether `spawn_region` is already
  on this model)
- `src/worldassembly/resolver.py` (where `PopulationSpec.spawn_region` gets consumed during
  profile resolution — check whether it's dropped there or survives to the profile)

## Assumptions / Open Questions
- Whether the information gap is purely at `spawn_from_context()`'s own call site (an easy,
  narrow fix) or extends further upstream into profile resolution (a bigger fix) is not yet
  confirmed — Scope requires checking this directly before disposition.
- Whether anything would meaningfully consume `properties["spawn_region"]` once wired is also
  open — a real disposition question, not assumed to be "wire it" by default.

## Implementation Notes
Confirmed the gap extends one level upstream of the ticket's own guess: `ResolvedEntityProfile`
(`src/worldassembly/models.py`) had no `spawn_region` field at all — only `spawn_position` (the
resolved x/y). `resolver.py`'s population-resolution loop already computes
`getattr(pop_spec, "spawn_region", None)` to feed `_resolve_spawn_position()`, but the region name
itself was never passed into either `ResolvedEntityProfile(...)` construction call, so it never
survived to reach `spawn_from_context()`.

Added `spawn_region: Optional[str] = None` to `ResolvedEntityProfile`; set it at both construction
sites in `resolver.py` from the same `pop_spec.spawn_region` already used for position resolution
(matching the classic `WorldCompiler.compile()` pipeline's own convention at `compiler.py:545`,
which sets the identical field the same way); changed `entity_spawner.py`'s hardcoded
`spawn_region=None` to `spawn_region=profile.spawn_region`. `archetype_factory.py`'s existing
`if spawn.spawn_region is not None: properties["spawn_region"] = spawn.spawn_region` guard needed
no change — it was already correct, just never fed a real value.

Disposition: wire, not delete. Unlike the optimization-package deletions, this isn't aged-out —
the classic pipeline already does this correctly and has a live consumer-shaped write path; the
archetype-native pipeline simply never got equivalent treatment. The legacy-guard spawn path (no
`archetype_id`) still never reads `spawn.spawn_region` at all — confirmed unaffected, out of this
ticket's own scope (Related Code Areas never named it).

**Downstream effects recorded per peer review, not left implicit:**
- `docs/plans/deferred_tuning_decisions_register.md` D-07 amended: the threading gap it flagged as
  blocking the "authored region" survivor-placement option is closed, but only as far as
  `identity.properties["spawn_region"]` — `EntityCarryForward` and `StrategicComponent.
  home_region_id` are not reached, so the authored-region option is not yet viable. Stated
  precisely rather than overstated.
- `TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH` cross-referenced with this
  fix's pattern as a working precedent for its own Direction 1. While cross-referencing, found and
  flagged (not resolved — out of this ticket's scope, that ticket stays gated) that its own "never
  sets `population_id` anywhere" claim is now stale: `TCK-20260911-REGION-DECLARED-POPULATION-
  SPAWNED-ENTITY-DIVERGENCE` (done since that ticket was filed) already added `population_id`
  tagging to the same two files. Flagged as unverified-but-promising, not claimed as resolved —
  that ticket's own worked-example empirical check would need to be re-run to confirm.

**CI/regression triage**: initial full run surfaced 11 failures, all in
`tests/unit/worldassembly/test_corpus_diversity.py`. Per CI Failure Triage discipline, did not
assume regression from a guess — reverted this ticket's 3 diffed files to their pre-fix state and
re-ran the identical 11 tests: 10 failed identically against the unmodified baseline (1 flipped
pass/fail between runs, consistent with the same non-deterministic timing rather than either
code state). Root cause is the already-documented wall-clock kernel throttle
(`kernel.py:585-596`) breaking determinism under `audit_mode=False` — pre-existing, unrelated to
this fix, not touched here per Gate Integrity. Restored the fix from backup after the comparison.

## Test Summary
- `tests/integration/worldassembly/test_world_entity_spawner.py`: 14 passed (12 pre-existing + 2
  new — `test_spawn_region_threads_into_entity_properties`,
  `test_spawn_region_none_when_profile_has_none`).
- `tests/unit/worldassembly/`: 546 passed, 11 failed — all 11 failures in
  `test_corpus_diversity.py`, confirmed pre-existing via baseline comparison (see Implementation
  Notes), not a regression from this fix.
- `tests/integration/campaigns/test_survivor_identity_reconstruction.py`: passed (part of the same
  full run).
- `python3 tools/validate_frontmatter.py` — passed for this ticket.

## Files Changed
- `src/worldassembly/models.py` — added `ResolvedEntityProfile.spawn_region`.
- `src/worldassembly/resolver.py` — set `spawn_region` at both `ResolvedEntityProfile(...)`
  construction sites.
- `src/worldassembly/entity_spawner.py` — read `profile.spawn_region` instead of hardcoding `None`.
- `tests/integration/worldassembly/test_world_entity_spawner.py` — added 2 tests.
- `docs/plans/deferred_tuning_decisions_register.md` — D-07 amended with precise reach of this fix.
- `tickets/todos/TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH.md` —
  cross-referenced this fix's precedent and flagged its own stale `population_id` claim.

## Completion Summary
Wired `spawn_region` through the archetype-native spawn pipeline, matching the classic pipeline's
existing behavior. The upstream gap (missing `ResolvedEntityProfile` field) was one level deeper
than the ticket's own filed guess — confirmed via direct investigation before implementing. Real
test evidence added; pre-existing, unrelated test-suite flakiness triaged and ruled out via a
baseline comparison rather than assumed. Both downstream effects (D-07's narrative-option reach,
the actor-ID mismatch ticket's precedent and stale claim) recorded explicitly per peer review.
