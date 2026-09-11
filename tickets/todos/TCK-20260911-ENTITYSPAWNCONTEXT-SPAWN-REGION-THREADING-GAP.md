---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260911-ENTITYSPAWNCONTEXT-SPAWN-REGION-THREADING-GAP
phase: open
date: 2026-09-11
tags: [world]
---

# TCK-20260911-ENTITYSPAWNCONTEXT-SPAWN-REGION-THREADING-GAP

## Title
`WorldEntitySpawner.spawn_from_context()` hardcodes `EntitySpawnContext.spawn_region=None` — no campaign-spawned entity's authored spawn region reaches the live entity, even though the plumbing to carry it exists

## Status
OPEN

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
- [ ] Confirmed whether `spawn_region` is available to `spawn_from_context()` today (via
      `ctx`/`profile`) or needs upstream threading too.
- [ ] A disposition (wire / delete-the-dead-write-path) recorded with rationale.
- [ ] If wired: `properties["spawn_region"]` genuinely reflects each entity's real originating
      region post-fix, verified by a real test, not just by absence of errors.
- [ ] If deleted: `EntitySpawnContext.spawn_region` and its one write site removed, verified via
      existing `tests/unit/world/`, `tests/integration/` suites for entity spawning passing
      unchanged.

## Related Tickets
- `TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION` (origin of this finding;
  D-07's own narrative-disposition question depends on this if "authored region" is ever chosen)
- `TCK-20260909-WORLD-ENTITY-SPAWNER-POSITION-RESOLUTION` (Batch B — the sibling mechanism that
  did thread `spawn_position` through the same `spawn_from_context()` call, for comparison)
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (same "write with no consumer" shape, not
  filed there since it wasn't yet load-bearing for any open decision)

## Related Docs
- `docs/plans/deferred_tuning_decisions_register.md` D-07 (the open narrative question this
  threading gap is a prerequisite for, if answered a certain way)
- `docs/world/assembly_contract.md` (the determinism contract `spawn_from_context()` operates
  under — confirm any fix preserves it)

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
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
