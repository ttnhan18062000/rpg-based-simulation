---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES
phase: open
date: 2026-09-14
tags: [world]
---

# TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES

## Title
The one corpus world with a real `LAIR`-kind Place has its own region sitting at exactly `0.0`
`trauma_score` for a full 5000-tick run — no threshold value can open `check_for_lair_spawn()`'s
gate there, because that region records zero combat deaths at all, not because the threshold is
still too high

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
Found while proving `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`'s gate-reachability
fix end to end. That ticket lowered `BossService.BOSS_SPAWN_THRESHOLD` (`50.0` → `2.0`) and added
`BossService.BOSS_SPAWN_TRAUMA_THRESHOLD` (`20.0` → `8.0`), and proved via a real 3000-tick run that
a `world_boss` now spawns correctly (`check_for_boss_spawn()`, region-scoped).

The sibling mechanism, `check_for_lair_spawn()` (place-scoped, spawns `dragonkin`), shares the
identical gate but was **not** proven reachable. `generated_frontier_3_42` is the only corpus world
found with a real `LAIR`-kind Place (`moon_cave_lair`, in region `moon_cave`). A real 5000-tick
`Kernel.tick_once()` run against that world found `moon_cave`'s own `region.trauma_score` at exactly
`0.0` for the entire run — no death was ever recorded in that region. `trauma_score` accrues `+1.0`
per real entity death in that death's own region (`src/engine/world_dynamics.py`'s "Death-triggered
Trauma" block); if zero deaths occur in `moon_cave` across 5000 real ticks, no threshold value —
however low — can open the gate there, short of `0.0` itself (which would defeat the point of a
"some danger has happened here" gate).

This is a different, region-specific defect from the one the sibling ticket fixed: not a wrong
number, but a region that structurally never accumulates the stat the gate checks. Likely cause:
`moon_cave` is a remote/magical region (per its own `RegionDef` framing in
`data/content/world/runtime_regions.yaml`, kind `("magical",)`) that entities rarely or never path
into for combat — but this is not confirmed, only hypothesized.

## Scope
- Confirm directly why `moon_cave` records zero deaths across a real run — check whether entities
  (heroes, monsters) ever path into or spawn within that region at all, whether its own hazard/
  monster-density configuration is simply too low to ever produce combat, or whether there's a
  separate routing/pathing defect keeping entities out of it entirely.
- Check whether other LAIR-kind Places in other worlds (if any get added later, or if this repo's
  world corpus grows) would have the same problem — is this specific to `moon_cave`, or does it
  reveal a general pattern that LAIR-kind Places tend to sit in low-combat regions by design
  (defeating their own occupant-spawn gate)?
- Propose a real fix: could be region content authoring (more monster density/hazard near lairs),
  a different trigger stat for Lair-occupant spawning specifically (not the same region-wide
  `trauma_score` a world boss's gate uses), or something else — bring findings + options to
  peer/user review before implementing, matching this week's established pattern for reachability
  defects.

## Out of Scope
- The world-boss side of the gate (`check_for_boss_spawn()`) — already fixed and proven reachable
  in the sibling ticket; this ticket is specifically about the Lair-occupant path.
- Any change to `BOSS_SPAWN_THRESHOLD`/`BOSS_SPAWN_TRAUMA_THRESHOLD` themselves — already resolved
  by the sibling ticket; this is about a region-specific trauma-accrual gap, not the threshold
  values.

## Acceptance Criteria
- [ ] A real, evidence-backed explanation for why `moon_cave` (or LAIR regions generally) never
      accumulate trauma_score.
- [ ] A proposed fix (not yet built without review) that would make at least one real LAIR-kind
      Place's occupant demonstrably spawnable within a realistic run length.
- [ ] Findings brought to peer/user review before implementation.

## Related Tickets
- `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY` (fixed the shared gate's threshold
  values and the tier-5/loot defects; this ticket covers the remaining region-specific gap)
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` (sibling shape — "spawn placement and
  region geography not lining up"; checked directly, this ticket's own cause is spatial isolation,
  not that investigation's dangling-reference bug, but the pattern family is shared)
- `TCK-20260915-WORLDBUILDING-DANGLING-REGION-REFERENCE-SILENT-FALLTHROUGH` (the specific bug
  checked and ruled out for this ticket's own region)

## Related Docs
- `docs/plans/deferred_tuning_decisions_register.md` D-05 (records this as a known remaining gap)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/world/boss.py` (`BossService.check_for_lair_spawn()`)
- `src/engine/world_dynamics.py` (Death-triggered Trauma block, the real `trauma_score` producer)
- `data/content/world/runtime_regions.yaml` (`moon_cave`'s own region definition)
- `data/worlds/generated_frontier_3_42/` (the one corpus world with a real LAIR place)

## Assumptions / Open Questions
- Whether `moon_cave`'s zero-combat state is a content-authoring gap (too little threat placed
  there) or a routing/pathing defect (entities never go there) is the central open question.

## Implementation Notes
**2026-09-15, checked against `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`'s own
region-composition finding (peer's explicit request before picking this up) — same general shape,
different specific mechanism.**

**Ruled out: this is NOT the same dangling-region-reference bug** found in that investigation
(`TCK-20260915-WORLDBUILDING-DANGLING-REGION-REFERENCE-SILENT-FALLTHROUGH`). Checked directly:
`moon_cult_ruins.yaml`'s sole population, `moon_cult_apprentice_circle`
(`data/content/entities/populations.yaml`), declares `preferred_regions: ["moon_cave"]` — and
`moon_cult_ruins.yaml` itself defines a region with exactly that id, `"moon_cave"`. The reference
is correct; entities from this population should spawn exactly where intended, unlike
`merchant_caravan`'s dangling `"trade_road"` reference.

**The real mechanism is spatial isolation, confirmed via a static comparison of region bounds
across `generated_frontier_3_42`'s full module composition** (`frontier_village_core`,
`old_mine_resource_loop`, `bandit_road_trade_pressure`, `goblin_camp_conflict`, `moon_cult_ruins`,
`orc_clan_territory`):

| Region | Module | `grid_bounds` |
|---|---|---|
| `moon_cave` | `moon_cult_ruins` | `[100, 70, 130, 110]` |
| `orc_clan_territory`'s own region | `orc_clan_territory` | `[160, 60, 200, 100]` |
| `old_mine` (old_mine_resource_loop's own region) | `old_mine_resource_loop` | `[20, 60, 60, 105]` |

**No other module's region in this composition overlaps or comes close to `moon_cave`'s own
bounds** — the nearest, `orc_clan_territory`, has a ~30-unit x-axis gap; `old_mine_resource_loop`
has a ~40-unit gap. `moon_cave` sits spatially isolated from every other populated region in this
world. `moon_cult_ruins` itself places only one population there (`moon_cult_apprentice_circle`,
4 `apprentice_mage`, faction `arcane_circle`) with **no opposing hostile faction ever placed in or
adjacent to that region** — so even correctly-spawned entities have no adversary in combat-
engagement range (this arc's combat_engagement radius is 10.0 units elsewhere; a 30+ unit gap is
far outside that regardless of the exact figure used by whatever detection radius applies here).

**Same general shape as the sibling investigation's finding** ("spawn placement and region
geography not lining up with what a mechanic needs to fire"), but a **different specific root
cause**: not a reference to a nonexistent region resolving to the wrong place, but a real region
correctly populated with its own intended entities, isolated from any faction that could ever
fight them there. The two findings do not collapse into one — they're siblings in pattern, not the
same underlying bug — but they may share the same eventual fix category (content-authoring:
composing hostile presence nearer to isolated Lair-kind regions) rather than a code fix.

**Not yet checked (remaining scope of this ticket)**: whether ANY entity ever paths into
`moon_cave` at all for non-combat reasons (the module's own quest content —
`mcult_investigate_ritual_site`, `mcult_defend_arcane_circle` — could route heroes there without
necessarily producing combat), and whether that's a separate, real gap from the spatial-isolation
finding above. Not traced this session — the static composition check above answers the specific
question peer asked before taking this ticket; the ticket's own full scope (a real, reviewed fix
proposal) remains open.

**2026-09-15, parked here per explicit direction — not proposing or building a fix.** Both
candidate directions this investigation surfaced are design decisions, not code defects with an
obvious single answer, and this cluster has a capped investment budget:
1. **Content-authoring fix**: compose real hostile presence nearer `moon_cave` (e.g. extend
   `moon_cult_ruins` itself, or a future world's own module placement) so the region's sole
   population has an adversary within combat-engagement range.
2. **Mechanic-design fix**: give Lair-occupant spawning its own trigger condition, separate from
   the same region-wide `trauma_score` a world-boss gate uses (per this ticket's own original
   Scope item 3) — since a Lair, by design, may need a fundamentally different kind of "danger has
   happened here" signal than a world-boss region does.

Left open, not closed — no fix decided or built. See §"Named finding" below for the pattern this
and the sibling investigation's finding both instantiate.

**Named finding (recorded here per explicit request — a third pattern class for this arc, distinct
from "dead code" and "systems fed by nothing"): mechanics whose preconditions depend on world
geometry that nothing validates.** The mechanic is live, the entities are correctly spawned, the
content references resolve — and the precondition can never be met because composition placed the
participants where they will never meet. Two confirmed instances so far, same failure expressed
through different causes:
- This ticket: `moon_cave`'s sole population has no hostile faction ever composed within range —
  a real gap in composition, not a reference bug.
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`'s own finding: `merchant_caravan`'s
  dangling `"trade_road"` reference lands its population in the map's far corner, away from the
  hostile factions that do exist.

**This predicts where else to look**: any mechanic requiring two things to be spatially
co-located is exposed to this class, and nothing in the compile path currently checks that a
world's actual composition satisfies what its own mechanics need to function — only that content
references resolve syntactically (and per the sibling ticket's own finding, not even always
that).

**Confirmed as a third instance**: `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` was
checked next and confirmed to share this pattern, doubly so — the reference world its own original
probe used has zero `hero`-kind entities composed into it at all (the entity kind its producer
requires simply doesn't exist there), and even in a world that does compose heroes, their own
module hardcodes their spawn region to the safe village, never any hazardous region the mechanic
needs them to visit. Three real, distinct mechanics (Lair-occupant spawning, cross-faction combat
volume, calamity-intensity production) now confirmed to share this one shape — a real, non-
speculative case for a compile-time check that validates world composition against what its own
mechanics structurally require, not just that content references resolve.

**A clean counter-example, checked next, protects the pattern from overclaiming**:
`TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` looked like a strong fourth-instance
candidate (another "system fed by nothing" symptom) but does **not** share this pattern. Checked
directly: entities are correctly co-located, deaths genuinely happen where the mechanic needs
them to, and the death is detected — by one consumer (`world_dynamics.py`'s trauma block, which
checks `alive_set is False` directly) but not another (`resolve_lifecycle()`'s own filter, which
checks `outcome_kind in ("KILL", "PERMADEATH")` — missing `"DEFEAT"`, confirmed empirically to be
100% of real deaths, 20/20, in the sampled run). A real, single-cause classification divergence
between two independent readers of the same event, not a geometry/composition gap. See that
ticket's own Implementation Notes for the full trace. This is the intended shape of checking each
instance rather than assuming — a pattern with one confirmed exception is more credible than one
presented as universal.

**Full write-up of the pattern, all four instances checked (including this exception), and the
implication — moved out of this ticket into its own standalone document, since the finding has
outgrown living inside one ticket's notes**: `docs/plans/world_composition_precondition_gap_finding.md`.

## Test Summary
_(not started)_

## Files Changed
_(not started)_

## Completion Summary
**Parked by explicit user decision, not abandoned or unresolved.** The root cause is fully known:
`moon_cave` is spatially isolated from every other populated region in its world's composition
(~30-unit gap to the nearest), and its sole population has no hostile faction ever composed within
combat range — confirmed via a real static comparison of region bounds, not inferred. Two real
candidate fix directions are recorded above. The user's explicit decision, given the investment
cap on this cluster, was to record the finding and not build a fix now — "we know exactly why this
doesn't fire and chose not to fix it now" is the accurate state, distinct from "this doesn't fire
and we don't know why." See `docs/plans/world_composition_precondition_gap_finding.md` for the
durable record of this finding alongside its two sibling instances.
