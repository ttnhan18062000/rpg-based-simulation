---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260919-COMBAT-HOSTILITY-SOURCE-DIVERGENCE-UNIFICATION
artifact_type: investigation
tags: [combat, faction, root-cause]
---

# Investigation — TCK-20260919-COMBAT-HOSTILITY-SOURCE-DIVERGENCE-UNIFICATION

## The headline finding: there are 2 real call sites, not 3, and both want the same semantics

The ticket's own framing named three consumers — the opportunity-attack trigger, `skip_oa`/
escape-tag observability, and the hypothetical-position pathing check — as if they might need
three different answers. **Exhaustive repo-wide search finds only 2 structurally independent call
sites, and both are already funneling through one shared primitive.**

```
$ grep -rn "get_engaged_hostiles" src/ --include="*.py" | grep -v "def get_engaged_hostiles"
src/engine/movement.py:100:   len(LegalityServiceV2.get_engaged_hostiles_at_pos(p, entity, state_or_context)),
src/engine/movement.py:181:   engaged_hostiles = LegalityServiceV2.get_engaged_hostiles(entity, state_or_context)
src/engine/legality.py:514:   return LegalityServiceV2.get_engaged_hostiles_at_pos(entity.navigation.position, entity, state)
```

`LegalityServiceV2.get_engaged_hostiles(entity, state)` (`src/engine/legality.py:512-514`) is a
**trivial wrapper**: `return get_engaged_hostiles_at_pos(entity.navigation.position, entity,
state)`. So the two named consumers "opportunity-attack trigger" and "skip_oa/escape-tag" are not
two call sites at all — they are two things done with **one single call's result**
(`movement.py:181`), computed once at the entity's own real position. Reading the surrounding code
confirms this directly:

```python
# movement.py:181
engaged_hostiles = LegalityServiceV2.get_engaged_hostiles(entity, state_or_context)
...
# lines 206-225: escape-tag / FLED-learning consumer
if engaged_hostiles and skip_oa:
    escape_tag = {"combat_escape": "EVASIVE_SUCCESS", ...}
    ...
# lines 227-242: opportunity-attack trigger consumer
if engaged_hostiles and not skip_oa:
    ... CombatResolutionSystem.resolve_multi_attack(...)
```

Both consumers read the *same* `engaged_hostiles` value. An entity either had a real hostile
adjacent and fought it (`not skip_oa`), or had a real hostile adjacent and evaded it (`skip_oa`).
These are two outcomes of the same encounter, not two different questions about what "hostile"
means — they cannot have different semantics without literally calling the hostility check twice
with two different definitions for the same adjacent pair, which nothing in the code does today
and nothing in the domain logic asks for.

**So the real question collapses from "3 call sites, may want 3 answers" to "2 call sites, do
they want the same answer or different ones":**
1. `movement.py:181` (own position) → escape-tag **and** opportunity-attack trigger, combined.
2. `movement.py:100` (hypothetical sidestep position) → movement-planning avoidance.

## Does the pathing check (call site 2) actually want different, more permissive semantics?

The ticket's own hypothesis, stated as a real possibility to check: *"the pathing check asking
'would I be attacked here' might legitimately need the permissive legacy behaviour, while the
attack trigger clearly shouldn't."* Checked directly, not assumed — **the code's own comment says
otherwise**:

```python
# movement.py:97-102
# Threat-aware sorting: Prefer tiles that don't trigger OAs
sidesteps.sort(key=lambda p: (
    len(LegalityServiceV2.get_engaged_hostiles_at_pos(p, entity, state_or_context)),
    LegalityServiceV2.get_manhattan_dist(p, target_pos)
))
```

The stated intent, in the code's own words, is explicitly **"prefer tiles that don't trigger
OAs"** — i.e., this heuristic exists specifically to avoid the exact mechanical consequence call
site 1 produces (`resolve_multi_attack()` firing). A heuristic whose entire purpose is "avoid
triggering the thing call site 1 triggers" cannot correctly use a *different* definition of
"hostile" than call site 1 without becoming systematically miscalibrated in exactly the same two
directions call site 1 already is: avoiding tiles next to friendly/neutral factions that would
never actually trigger a real attack (over-caution, wasted movement options), and failing to
avoid tiles next to real catalog-hostile rivals that share a legacy bucket, like
`bandit_company`/`goblin_warband` (under-caution, walking into real danger the heuristic exists
to prevent). **This is not a case where two consumers legitimately want different answers — it is
one consumer (call site 1) and one heuristic built to predict call site 1's own outcome (call site
2), and prediction only works if it uses the same rule being predicted.**

**Finding, stated plainly**: both real call sites want the same semantics — real, catalog-driven
hostility (`is_hostile_compat()`), not the raw legacy-enum comparison currently used by either.
The ticket's own speculative "they may want different answers" hypothesis is **not confirmed** —
the evidence points the other way, and the fix shape is simpler than three-call-sites framing
implied.

## Real call volume, measured (not assumed to be a rare corner case)

Instrumented both functions separately (wrapper vs. underlying primitive) over real
`Kernel.tick_once()` runs (`LocalSequentialExecutor`, seed 42, `WorldCompiler.compile()` for
corpus worlds):

| World | Ticks | Total `get_engaged_hostiles_at_pos` calls | Via wrapper (own-position: escape-tag + OA trigger) | Via direct sidestep-loop (hypothetical position) |
|---|---|---|---|---|
| `crowded_frontier` | 2000 | 38239 | 17787 | **20452** |
| `hero_guild_routing` | 2000 | 33984 | 14740 | **19244** |
| `quest_dense_frontier` | 2000 | 1266 | 760 | **506** |
| `metropolis`† | 30 | 123 | 57 | **66** |

†`metropolis` used per instruction, with its own limitation disclosed rather than treated as
clean: `TCK-20260919-PERF-SCENARIO-METROPOLIS-SPAWN-COLLISION` root-caused a real, deterministic
spawn-collision defect in `build_metropolis_state()`'s own construction, so its per-entity
position/task state is not a reliable control for this or any investigation — used here only for
directional confirmation, not as a clean baseline.

**The sidestep-avoidance call site is not a minor edge case — it is comparable to, and in 3 of 4
worlds larger than, the direct engagement call site.** This matters for scoping the fix: a
unification that only touches the attack/escape path (`movement.py:181` /
`get_engaged_hostiles`) and leaves the sidestep loop (`movement.py:100`) on the old semantics
would still leave roughly half of this primitive's real call volume uncorrected.

## Would swapping to `is_hostile_compat()` break the existing test fixtures?

Checked directly, not assumed. `tests/unit/movement/test_movement_spatial_regression.py`'s
escape-tag fixtures (`_build_evasive_retreat_pair`) build a hero (`Faction.HERO_GUILD`, no
`identity.properties["faction_id"]` set) and a monster (`Faction.MONSTER_HORDE`, same). Traced
through the real resolution path a catalog-aware swap would use:

1. `EntityIdentityResolver.resolve()` on either entity, with no `properties["faction_id"]`, falls
   through to Path 3 (`compatibility_projection`), which maps the raw legacy enum through
   `_FACTION_COMPAT`: `Faction.HERO_GUILD -> "hero_guild"`, `Faction.MONSTER_HORDE ->
   "monster_horde"`.
2. `data/content/social/factions.yaml` has a real catalog entry for `"hero_guild"`
   (`legacy_engine_bucket: HERO_GUILD`) but **no entry at all for `"monster_horde"`** — it is a
   synthetic compatibility-projection id with no catalog backing.
3. `FactionSemanticsService.is_hostile_compat("hero_guild", "monster_horde", ctx)`: no
   `perspectives`/`faction_relationships` entry exists between these two synthetic-for-monster
   ids, so it falls through to `is_hostile()`'s own fallback branch: since `defn_b` (for
   `"monster_horde"`) is `None`, it uses the legacy-bucket fallback rule — `bucket_a
   (HERO_GUILD) != bucket_b (MONSTER_HORDE)` → **`True`**.

**The existing test would still pass under catalog-aware semantics** — not because the fixture
happens to be exempt from this change, but because a faction id with no real catalog entry falls
back to exactly the same bucket-comparison logic the legacy path already uses. This is a real,
traced result, not an assumption, and it is reassuring: the one existing test suite that exercises
this exact code path is not a blocker.

## Cost/safety check for the proposed fix's dependencies

- `RelationContext` (`src/content_semantics/relation.py:13-22`) has every field optional
  (`distance`, `combat_engaged`, `intruding`, species fields) — a minimal, cheap construction
  (`distance=1.0, combat_engaged=True`) is sufficient for an adjacency check, matching what
  `tactical.py`'s own hostiles-loop already builds.
- `EntityIdentityResolver.resolve()` (`src/entities/identity_resolver.py`) is a pure, in-memory,
  dict-lookup-based resolver with no I/O — cheap enough to call at the measured volume (up to
  ~20000 calls per 2000-tick run, i.e. ~10-19 per tick) without a real performance concern.
- Real measured call volume above (10-19 hostility checks per tick, worst case) confirms this is
  not a hot-path performance risk even before considering the resolver's own low cost.

## Fix shape (recommendation, not implemented)

**One unified source change, in one function, not two named predicates.** Both real call sites
(`get_engaged_hostiles` at the entity's own position, and the direct `get_engaged_hostiles_at_pos`
calls in the sidestep loop) should read real catalog hostility
(`FactionSemanticsService.is_hostile_compat()`, via `EntityIdentityResolver.resolve()` for real
`faction_id` strings) instead of the raw legacy `Faction` enum comparison currently used. This is
the opposite of the ticket's own "three call sites may want three answers, so scope the primitive
into named variants" hypothesis — the evidence here says they want *one* answer, so a single
targeted change closes the whole gap.

**Where the change actually lands, mechanically**: `LegalityServiceV2.get_engaged_hostiles_at_pos()`
(`src/engine/legality.py:517-559`) has **three internal implementations of the same hostility
test**, not one — a fast path using `state.occupancy_snapshot` (525-533), a fallback using
`SpatialQueryService.get_occupancy_map()` (535-547), and a further fallback iterating
`state.entities` directly (549-559) — each currently doing its own `my_faction != other.faction`
check. A real fix must update all three consistently, or the semantics would depend on which of
the three code paths a given call happens to hit (state shape-dependent, not call-site-dependent)
— a real, concrete detail of the fix's actual size that a "just swap the check" description would
undercount.

**What does NOT need to change**: `get_engaged_hostiles()` itself (the wrapper) needs no change —
it already delegates entirely to `get_engaged_hostiles_at_pos()`, so fixing the one function fixes
both real consumers automatically.

**Not fixed in this pass, per this ticket's own explicit scope** (investigation only). This is a
smaller, more mechanically bounded change than the ticket's own worry about "3 call sites with
different consumers" suggested — a real, positive finding from doing the investigation rather than
assuming the worst-case blast radius.

## `implemented_by` bindings recorded as a side effect (per explicit instruction)

Bound 3 of combat's 7 mechanisms — the ones whose implementing code was read with real, direct,
citable confidence during this investigation, not the full remaining 4 (which would need their
own direct reading pass, not assumed from this investigation's own work):
- `combat_resolution` → `src/engine/combat.py::CombatResolutionSystem`
- `tactical_decision` → `src/engine/tactical.py::TacticalDecisionSystem`
- `movement` → `src/engine/movement.py::MovementSystem`

`action_pacing_readiness`, `status_effects`, `skill_unlocks`, `combat_engagement` remain unbound —
not read closely enough in this investigation to bind with the same confidence, left for
`TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION`'s own dedicated pass.

Verified: `tools/mechanism_registry/registry.py::validate()` returns zero errors after the 3
additions; `pytest tests/unit/tools/test_mechanism_registry.py` (52/52 passed).
