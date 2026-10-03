---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260903-ECONOMIC-VACANCY-SIGNAL
artifact_type: investigation
tags: [economy, lifecycle]
---

# Investigation — TCK-20260903-ECONOMIC-VACANCY-SIGNAL

## Current Behavior

**`EntityRole`** (`src/core/enums.py:6-12`) — `IntEnum` with `HERO=0, SHOPKEEPER=1, MONSTER=2,
CITIZEN=3, WORKER=4, GUARD=5`. No unique/singular "production role" concept exists; role is a
headcount tag, not a 1:1 assignment to anything.

**`BlacksmithSystem.enforce`** (`src/engine/blacksmith.py:114-248`) — confirmed genuinely
entity-agnostic. Any entity standing on a `blacksmith` tile with `known_recipes` (wholesale-learned
just by visiting, lines 139-151), sufficient `gold`, and sufficient materials can craft (lines
154-246). There is no identity/occupancy check anywhere in this function. Killing the "town
blacksmith" entity today does **not** reduce this system's own crafting capacity — any other
qualifying entity that walks onto the tile can still craft.

**`TownResolutionSystem.resolve`** (`src/engine/town_resolution.py:21-178`) —
`BuildingState.functional` (line 172) is flipped only by faction-level `MAINTENANCE_COST`
insolvency (lines 148-172: per-faction maintenance total vs. `state.global_resources[faction_key]`),
never by entity occupancy. **`BuildingState`** (`src/core/state.py:1101-1127`) has no
occupant/worker field of any kind — just `id, kind, position, hp, max_hp, functional, inventory,
price_modifiers`.

**`LifecycleSystem.resolve_lifecycle`** (`src/systems/lifecycle_systems/lifecycle.py:40-184`,
re-exported via the `src/systems/lifecycle.py` shim, invoked at `src/engine/pipeline.py:389` as
phase `"lifecycle"`, PP-33 per `docs/audits/D19_domain_phase_inventory.md:208`) is the real
death-finalization site. It already builds `recent_deaths: List[EntityState]` (lines 47, 111),
marks death (`active=False`, `is_permadeath_set`, `death_tick_set`, `death_reason_set`, lines
109-121), and performs death-triggered side effects in the same function — heir/heirloom transfer
(lines 123-158, `TCK-20260824-DEFAULT-HEIR-ASSIGNMENT`'s logic) and faction influence/conquest
shift (lines 160-182). No role/production check exists today. This is the natural integration point
for a vacancy check (same per-death loop, same place succession already lives).

**`OccupationChangeGoalScorer`** (`src/ai/goals/occupation_change_scorer.py`) — confirmed distinct,
not to be duplicated: region-scoped headcount-vs-density-target-gap detector for `CITIZEN` entities
re-training into `SHOPKEEPER`/`WORKER`/`GUARD` (`_CANDIDATE_ROLES`, line 14). Scans all entities,
tallies live headcount per role whose region (via `LegalityServiceV2.get_region_for_position`,
`src/engine/legality.py:44`) matches the scoring entity's region (lines 42-52), compares against
`BASE_OCCUPATION_DENSITY`/`MIN_OCCUPATION_SLOTS` (`src/world/occupation_config.py`). Consumed only
inside `StrategicIntelligenceSystem`'s citizen goal tier — not death-triggered, not readable by any
economy system. Its region-matching *scan pattern* is directly reusable for this ticket's occupancy
check (see options below); the scorer class itself is not.

**`EconomyHealthMonitor`** (`src/economy/health_monitor.py`) — the ticket names this the closest
SHAPE precedent for a `SimulationEvent`-based alert (`GoldHoardingEvent`/`InflationSpiralEvent`,
`check_alerts`, lines 25-51). Confirmed true for the event-class shape, but its **wiring is the
wrong precedent** for this ticket's acceptance criteria: `check_alerts`'s output is dispatched at
`src/engine/kernel.py:474-493` through `self._event_listeners` callbacks — a read-only observability
side-channel invoked directly from the kernel's post-tick metrics hook, **not** through
`StateUpdate`/the authoritative apply path, and not persisted into durable state at all (nothing
reads it back on a later tick). This does not satisfy "commits...through the authoritative apply
path" or "remains detectable...across ticks" from the ticket's acceptance criteria.

**The actual durable, apply-path-committed, cross-tick-persistent mechanism** in this codebase is
`StateUpdate.world_events_add: List[WorldEvent]` (`src/core/updates.py:1009`) → merged and
window-bounded into `AuthoritativeState.recent_world_events` (`src/core/state.py:1234`) inside
`src/engine/apply.py:335-338,444` (`WORLD_EVENT_WINDOW = 500` — **correction, plan-phase review
2026-09-03**: this is a cap on the last 500 `WorldEvent` objects merged from
`prior_events + update.world_events_add` **globally, across every category and region** via a plain
list slice, not a 500-tick time window — there is no tick-based filtering in that code at all; see
`staging_artifacts/TCK-20260903-ECONOMIC-VACANCY-SIGNAL/plan.md`'s "Review Revision" section).
`WorldEvent`
(`src/domains/world_emergence/schema.py:53-60`, frozen dataclass) has fields `category:
WorldEventCategory, tick, region_id, subject, severity, payload`. `WorldEventCategory`
(schema.py:15-51) already contains adjacent economy-flavored kinds — `SHOP_STOCK_DEPLETED`,
`SERVICE_UNAVAILABLE`, `POPULATION_DEATH` — that a new vacancy-shaped category would sit naturally
beside.

Real precedent for a system **emitting** a `WorldEvent` from a `StateUpdate`-producing static method
on a per-domain-death basis: `DemographicCycleService.process_demographics`
(`src/domains/demographics/cohort.py:337-418`) appends one `WorldEvent` per cohort birth/death
(lines 375-384) and returns `StateUpdate(world_updates=..., world_events_add=world_events)`
(415-418).

Real precedent for an **authoritative (non-observability) system reading**
`state.recent_world_events` to drive behavior: `FactionAwarenessService.compute_tension_updates`
(`src/engine/faction_decision.py:174-200+`), which explicitly documents "Uses
`state.recent_world_events` which contains the PREVIOUS tick's event window (inherent one-tick lag
— state is frozen at tick entry...)" — the same one-tick-lag caveat repeated at
`src/engine/pipeline.py:141,148,234,237,338-339`. This, not `EconomyHealthMonitor`, is the correct
wiring precedent for "the emitted signal is actually readable by at least one consuming system" —
a PP-07/PP-20 consumer should read `state.recent_world_events` (one-tick-lagged, same as every
other `WorldEvent` consumer), not receive an in-memory-only same-tick callback.

## PlaceState / idea 66 — fresh finding, genuinely new since ticket creation

Confirmed by direct branch inspection, not assumption: `tickets/working_log.csv` records
`TCK-20260902-PLACE-SCHEMA-MIGRATION` as `DONE` with `stored_artifacts/TCK-20260902-PLACE-SCHEMA-MIGRATION`,
and its commit `cc61a882` exists in the overall repository. **But this worktree's current branch
(`m4-institutions-economic-signals-implementation`) does not contain that commit** —
`git merge-base --is-ancestor cc61a882 HEAD` returns false; the commit lives only on
`knowledge-canonical-hash-gap` (and its `origin` mirror), not yet merged to `main`. Concretely,
`grep -n "class PlaceState" src/core/state.py` returns nothing in this worktree, and
`tickets/inprogress/TCK-20260902-PLACE-SCHEMA-MIGRATION.md` is still `status: active` /
`phase: open` here (not moved to `tickets/done/` on this branch), and
`stored_artifacts/TCK-20260902-PLACE-SCHEMA-MIGRATION` does not exist in this worktree. **The
implementer of this ticket must not assume `PlaceState`/`occupant_entity_id` is importable** — it
either isn't merged into this branch yet, or a merge/rebase must land first.

Even setting the merge-timing gap aside, per
`docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md`'s "Target Shape" section and
`docs/brainstorm/rpg_expected_schemas.html:593`, `PlaceState.occupant_entity_id` is explicitly
scoped to **LAIR-kind Places only** — "anchors to a specific boss/creature," reused from today's
real `boss_region_id` pattern (a monster-lair concept, idea 47). It is not a general
worker/staffing field; the Target Shape's CITY-kind fields are `building_ids`/`entity_ids`
(population membership) plus `scale`, not a per-role occupant map. **`PlaceState.occupant_entity_id`
is not the missing "who occupies a production role" piece, even once merged** — it answers "which
entity anchors this monster lair," not "which entity is a City's sole blacksmith/shopkeeper."

## What "occupies a production-relevant role" could mean — options for Plan phase (not decided here)

1. **Region-scoped `EntityRole` uniqueness (lowest-footprint, reuses an existing pattern).** Mirror
   `OccupationChangeGoalScorer`'s own headcount scan (`occupation_change_scorer.py:42-52`, via
   `LegalityServiceV2.get_region_for_position`) inside `LifecycleSystem.resolve_lifecycle`: on a
   death, count other living entities in the deceased's region sharing `entity.identity.role` in
   the production-relevant set. If the deceased was the only one, emit the vacancy `WorldEvent`. No
   new durable state; consistent with the confirmed reality that role is a headcount tag, not a
   building assignment, anywhere in `BlacksmithSystem`/`TownResolutionSystem` today.
2. **New durable per-building or per-region occupant field** (e.g. a staffing field added to
   `BuildingState` or `RegionState`) — architecturally valid (Durable State Rule: typed model,
   lifecycle, etc.) but a materially bigger schema surface than option 1, and risks pre-empting
   idea 66's own future `building_ids`/`entity_ids` Place-membership shape before that lands.
3. **Reuse `PlaceState.occupant_entity_id`** — rejected per the finding above: not present in this
   branch, and scoped to LAIR-kind only even once merged.

Plan phase must pick one of these explicitly (acceptance criterion 5 already requires this be
documented in `plan.md`); this investigation deliberately does not resolve it.

A second, related open question the schema doc does not settle: which role(s) count as
"production-relevant." `docs/brainstorm/rpg_expected_schemas.html:934-940`'s own example — "a
City's only blacksmith" — maps most naturally to `SHOPKEEPER` (per
`src/entities/identity_resolver.py`'s `"shopkeeper"` label and
`src/systems/world_systems/routine.py:138`'s `SHOPKEEPING` task-kind pairing), since there is no
dedicated `BLACKSMITH` role. But `WORKER` (`routine.py:142`, `HARVESTING`) is equally "production."
Scope doesn't specify whether the signal covers one role, both, or is role-parameterized — Plan must
decide.

## Mechanics / Engine Constraints

- `docs/engine/authoritative_pipeline.md` / `authoritative_mutation_pipeline_contract.md`: durable
  mutations must go through `StateUpdate` → apply path; the `world_events_add` →
  `recent_world_events` flow is the concrete instance of that law for typed, cross-tick-readable
  signals. Matches CLAUDE.md's Durable State Rule (typed model, stable location, defined
  lifecycle) — `recent_world_events`'s bounded last-500-events-globally window (`WORLD_EVENT_WINDOW`,
  `src/engine/apply.py:335`, a count of `WorldEvent` objects across the whole world, not a 500-tick
  clock — see plan.md's Review Revision section) *is* the defined lifecycle/expiry for this class of
  signal, which is materially different from "persists forever until explicitly filled."
- `docs/mechanics/03_economic_laws.md`: atomic conservation (Law of Materials) is already enforced
  in `BlacksmithSystem` via `ResourceTransferIntent`; this ticket's signal is additive/observational
  and must not alter that invariant.
- `docs/mechanics/04_strategic_cognition.md`: goal hierarchy owns strategic decisions from signals;
  PP-07/PP-20 are tactical/system-level consumers, not goal-scorers. Reading a vacancy signal at the
  PP-07/PP-20 system level (rather than adding a new `GoalScorer`) matches this boundary and the
  ticket's own Out of Scope guard against duplicating `OccupationChangeGoalScorer`.

## Docs Requiring Update

- `docs/parity_ledger/town_resource.yaml`: PP-07 (`BlacksmithSystem`) and PP-20
  (`TownResolutionSystem`) parity entries (e.g. `TOWN-017`, town_resource.yaml:194-201) live here;
  wiring a new vacancy-signal consumer into either system changes its documented behavior boundary
  and needs a new or updated entry with a passing `test_path`.
- `docs/audits/D19_domain_phase_inventory.md`: PP-07/PP-20/PP-33 rows' description columns (lines
  97, 175, 208) document current per-phase behavior; if the implementation changes what PP-07 or
  PP-20 "enforces"/"resolves" by making them read and react to a vacancy signal, these description
  cells need updating to stay accurate.
- `docs/core/state.md`: only if Plan phase selects Option 2 above (a new durable occupant field on
  `BuildingState`/`RegionState` rather than the region+role headcount check of Option 1). Resolved
  during implementation, condition not met if Option 1 is chosen instead — this bullet is
  conditional per `TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED`'s marker
  convention and should be left in this form (not rewritten to Format 2) until the implementer or
  doc-updater confirms which branch was taken.

The `docs/brainstorm/rpg_expected_schemas.html` doc (path: `docs/brainstorm/rpg_expected_schemas.html`,
under `docs/`) is not required to change for this ticket: it is a forward-looking brainstorm/schema
sketch (status: brainstorm, not authoritative), already correctly frames `EconomicVacancyEvent`/
`vacated_role`/`filled_by_entity_id` as open "New" concepts, and this ticket does not need to
promote or rewrite that speculative document as part of shipping the real, scoped-down (region_id,
signal-only, no `filled_by_entity_id`) implementation.

The `docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md` doc (path: same) is not
required to change for this ticket: this ticket's scope explicitly substitutes `region_id` for
`location_place_id` specifically to avoid touching idea 66's Place-model plan, and the investigation
above confirms `occupant_entity_id` there is LAIR-scoped and structurally unaffected by this
ticket's SHOPKEEPER/WORKER-scoped vacancy signal.

## Parity Ledger Overlap

No existing entry anywhere in `docs/parity_ledger/*.yaml` covers vacancy — reconfirmed here (no
`text:` field in `town_resource.yaml`, `progression.yaml`, or `social_narrative.yaml` mentions
occupancy/vacancy/sole-occupant), consistent with the ticket-creation-time repo-wide zero-hit grep
for `"vacan"`.

Nearby but distinct entries that must **not** be conflated with this work: `TOWN-017` (`text:
Blacksmith visits resolve recipe/crafting/material-gating behavior.`, `status: verified`,
`town_resource.yaml:194-201`) and its neighbors `TOWN-026`/`TOWN-028`/`TOWN-043` (blacksmith
blocker/crafting-resolution tests) describe today's entity-agnostic crafting behavior. This ticket
must not silently break or contradict `TOWN-017`'s verified parity by making crafting entity-gated
as a side effect of wiring PP-07 to the vacancy signal; if the chosen consumer wiring does add such
a gate, `TOWN-017`'s `text`/`status` must be revisited in the same session per the Authoritative
Mechanics Rule. None of the entries actually in this ticket's likely change surface are `priority:
P0` in the excerpts read (`TOWN-017` and neighbors are `status: verified` at standard priority);
implementer should re-confirm priority on whichever exact entries end up modified.

## Prior Work

- `TCK-20260824-DEFAULT-HEIR-ASSIGNMENT` (DONE): confirmed via source (heir/heirloom logic at
  `src/systems/lifecycle_systems/lifecycle.py:123-158`) — entirely resource/inheritance transfer,
  zero production/occupation-continuity logic. Confirms only that `resolve_lifecycle` is where
  death-triggered side effects already live, useful as the integration site, not as reusable logic.
- `TCK-20260824-OCCUPATION-CHANGE-TRIGGER` (DONE): source-confirmed
  (`src/ai/goals/occupation_change_scorer.py`) as the region-scoped headcount-vs-density-target
  pattern this ticket's Option 1 would structurally mirror. Reuse the *scan pattern*
  (`LegalityServiceV2.get_region_for_position` region-matching), not the `GoalScorer` class itself,
  per this ticket's Out of Scope guard against a second parallel detector.
- `docs/REGISTRY.yaml` query (`type: ticket`, `tags` ∩ `{economy, lifecycle, vacancy, occupation,
  production}`, or `path` containing `OCCUPATION`/`VACANCY`/`HEIR`) surfaced only these two plus
  unrelated lifecycle/economy tickets (reproduction, marriage, harvest/loot, simq scoring, etc.) —
  no additional undiscovered overlap.

## Risks and Open Questions

- **[Blocking for Plan]** What counts as "occupies a production-relevant role" — 3 real options
  above, not pre-decided; acceptance criterion 5 already requires Plan to document this explicitly.
- **[Blocking for Plan]** Which role(s) — `SHOPKEEPER`, `WORKER`, or both — count as
  "production-relevant"; not specified by the ticket text or the schema doc.
- The acceptance criterion requiring "a measurable production-throughput delta vs. a same-seed
  control run" is **not automatically produced by emitting the vacancy `WorldEvent` alone** —
  `BlacksmithSystem.enforce` is entity-agnostic, so any other qualifying entity can still craft
  after the death. The regression test's throughput delta may therefore come from simply having one
  fewer live entity in the world, independent of whether the vacancy signal is ever read by
  anything. Whether the test is meant to prove (a) the natural throughput impact of losing any
  production-capable entity (satisfiable without wiring the signal into an enforcement path), or (b)
  a throughput impact caused specifically by a consumer reading/acting on the signal (which starts
  to resemble the explicitly out-of-scope "recovery mechanism" territory if it goes as far as
  gating/throttling) is not resolved in the ticket text and should not be silently picked either
  way — flag for Plan.
- `TCK-20260902-PLACE-SCHEMA-MIGRATION`'s commit is not yet merged into this branch's history; if a
  merge/rebase lands mid-ticket, re-verify `PlaceState` still doesn't change the Option 3 conclusion
  above (low risk — `occupant_entity_id` remains LAIR-scoped per the design doc regardless of merge
  timing — but worth a recheck rather than an assumption).

## Anti-Drift Hazards

- Do not fork a second headcount-gap detector duplicating `OccupationChangeGoalScorer` (ticket's own
  Out of Scope) — reuse only the region-matching scan pattern, not a parallel `GoalScorer` or
  duplicate density-target math.
- Do not implement `filled_by_entity_id` resolution (apprentice promotion / import / stays-vacant) —
  explicitly out of scope. The vacancy is a durable, unresolved-until-something-else-fills-it
  signal, but given `recent_world_events`'s bounded last-500-events-globally window (a count of
  `WorldEvent` objects across the whole world, not a 500-tick clock), "remains detectable...if
  unfilled" is itself bounded by that window, not literally unbounded — Plan should state this
  explicitly rather than silently assuming unbounded persistence.
- Do not wire the signal into `BlacksmithSystem` in a way that makes crafting entity-gated for the
  first time (breaking `TOWN-017`'s verified parity) unless that is a deliberate, documented
  decision reflected in the same-session parity ledger update.
- Do not touch `PlaceState`/idea 66 Place-model integration even opportunistically because it is
  adjacent in the codebase right now — ticket scope explicitly defers that, and it isn't even merged
  into this branch.
- Do not silently reinterpret "sole occupant" as a global (world-wide) role count instead of the
  schema doc's clearly region/City-scoped framing ("a City's only blacksmith") — get the scope
  (region vs. world) right per whichever option Plan selects.
