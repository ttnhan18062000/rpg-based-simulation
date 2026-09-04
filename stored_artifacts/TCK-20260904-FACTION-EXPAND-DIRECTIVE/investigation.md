---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260904-FACTION-EXPAND-DIRECTIVE
artifact_type: investigation
tags: [faction, grand-strategy]
---

# Investigation — TCK-20260904-FACTION-EXPAND-DIRECTIVE

## Current Behavior

### FactionDecisionPhase — real, live extension point (confirmed)

`src/engine/faction_decision.py:109-169`. `FactionDecisionPhase.execute(state, policy=None)` is a
`@staticmethod`, stateless, iterating `state.factions.items()` and returning `list[FactionDirective]`.
Current if/elif structure per faction:

- `DEFEND_BORDER` (line 139): `fs.tension_level > 0.5 and len(fs.territory) > 0`.
- `elif TRADE_ROUTE` (line 148): `fs.military_strength > 0.7 and fs.tension_level < 0.3`.
- Unconditional secondary `COMMISSION_QUEST` (line 159): `len(fs.territory) > 0`, `priority=fs.tension_level`.

Constants live in `src/engine/faction_constants.py:8-10` (`DEFEND_BORDER`, `TRADE_ROUTE`,
`COMMISSION_QUEST` — plain string constants, no enum, "to avoid circular imports with scoring.py").
`FactionDirective` (`faction_decision.py:38-51`) is `@dataclass(frozen=True, slots=True)` with fields
`faction_id: str`, `directive_kind: str`, `target_faction: Optional[str] = None`,
`target_region: Optional[str] = None`, `priority: float = 1.0`, `created_tick: int = 0` — `target_region`
already exists on the base dataclass, so `EXPAND_TERRITORY` needs no new field, just population of the
existing one.

### Pipeline wiring — exact confirmed position

`src/engine/pipeline.py:226-231` (`AuthoritativeApplyPipeline.refine()`, "Enhanced RPG Phase 8b"):

```python
# --- Phase 2: Contracts & Production ---
update = run_phase("contracts", ...)
update = run_phase("blacksmith", update, lambda u: BlacksmithSystem.enforce(state, u))     # line 223
...
# --- Phase 8b: Faction Decision (runs before adventure routing) ---
# Must run every tick (no cadence gate) so faction_directives is stable input for scoring.
faction_directives: list = FactionDecisionPhase.execute(state, policy=None)                # line 230
...
# --- Phase 8c: faction_awareness ---                                                       # line 238
```

Confirmed exactly as the ticket states: `FactionDecisionPhase.execute()` is a **direct call**, not
`run_phase()`-wrapped (no feature flag, no cadence gate — `SystemCadence.faction_decision` exists as a
field but is not read anywhere in this call), positioned immediately after `blacksmith` and before
`faction_awareness`. `faction_directives` is a local `refine()` variable, currently consumed only by the
(dead, per STRAT-252) `AdventureRouteScorer` urgency table — it is **not currently threaded to any other
phase**, including `world_dynamics` (line 343, which calls `CampService.process_camps()` — see below).
This ticket must add that threading.

### FAC-003 parity rule — transient scratch, confirmed

`docs/parity_ledger/faction.yaml` FAC-003 (verified, P2): "FactionDecisionPhase reads state.factions
each decision tick and emits transient FactionDirective list; directives are not persisted in
AuthoritativeState." `tests/unit/domains/faction/test_faction_decision_phase.py` already has two
anti-drift guards enforcing this mechanically: `test_faction_directive_not_in_state_update` (asserts
`not hasattr(StateUpdate, "faction_directives")`) and `test_faction_decision_phase_returns_list_not_state_update`
(asserts `execute()` returns `list`, never `StateUpdate`). `EXPAND_TERRITORY` must satisfy both
unchanged — it is added as a new `directive_kind` string value, never a new field or a persisted
record.

### Population-pressure signal source — confirmed shape

`src/domains/demographics/cohort.py`:
- `compute_population_density(region: RegionState) -> float` (line 122): `total_pop / max(1, area)`,
  pure, 0.0 for cohort-less regions. Consumed today only by
  `src/domains/world_emergence/models.py:109` (`RegionalPressureModel`, unrelated subsystem).
- `compute_regional_scarcity(region_id: str, state: AuthoritativeState) -> float` (line 153): `1.0 -
  mean(remaining/max)` across resource nodes in the region's bounds; returns `1.0` (max scarcity) for
  a region with zero resource nodes or an unknown region id.
- **Direct precedent for consuming this signal as a faction/region-scoped gate**:
  `src/world/reproduction_humanoid.py:71` reads `compute_regional_scarcity(region.id, state) >
  threshold` to gate reproduction eligibility, and `src/world/camp.py:114-116` reads the same function
  to gate natural-creature reproduction inside `CampService.process_camps()` itself — i.e. `CampService`
  already imports and calls `compute_regional_scarcity` today, for an unrelated purpose (reproduction
  eligibility, not faction expansion). This is a strong, real precedent for the same
  "read-scarcity-inline-as-a-gate" style `FactionDecisionPhase`'s new branch should use, applied instead
  over `fs.territory` (the faction's own regions) to decide whether the faction is under population
  pressure.

Neither function takes or emits anything faction-scoped today — both are pure, `AuthoritativeState`
(or `RegionState`) reads with no faction awareness. The new `EXPAND_TERRITORY` branch must bridge
`fs.territory` (regions the faction owns) against these region-level functions itself; no existing
helper does this bridging.

### RegionState.owner_faction_id — confirmed exact shape and mutation status

`src/core/state.py:273`: `owner_faction_id: Optional[int] = None  # Faction that currently controls the
region`. Confirmed **not the authoritative ownership record** — `docs/systems/faction_contract.md`
("Note on `RegionState.owner_faction_id`") and parity entry `FAC-010`'s `divergence_note` both state
territory transfer via `MilitaryConflictPhase` updates `FactionState.territory` only, never
`RegionState.owner_faction_id` — "the int/str type mismatch with `FactionState.faction_id: str` is a
known limitation (FAC-010)." So `RegionState.owner_faction_id` is a real, typed, `Optional[int]` field
(mutable via `WorldUpdate.owner_faction_id_set`, applied at `src/engine/apply_plan.py:119`), but is
**not kept in sync** with the authoritative `FactionState.territory` tuple by any current code path —
it is set only at world-compile time (or left `None`), never touched by the faction/military-conflict
machinery. The ticket's own scope ("target any faction-less region via the existing
`RegionState.owner_faction_id` field") is consistent with this: it reads the field as a real signal of
"nobody has claimed this region at world-gen," accepting that it is a separate, weaker notion of
ownership than `FactionState.territory`. This divergence should be called out explicitly in
`plan.md`/`FAC-003`'s updated text, not silently glossed over — a region with
`owner_faction_id=None` is not necessarily un-owned by any `FactionState.territory` tuple, and vice
versa. **Target resolution should sort by region id for determinism**, following the exact idiom
`find_adjacent_regions`/`_check_migration` already use (`cohort.py:202`, `:264-267`) — `min(...,
key=lambda r: (..., r.id))` or `sorted(state.regions.items())` — since `state.regions` is a plain
`Dict[str, RegionState]` with no inherent iteration order guarantee across runs.

### CampService — confirmed current shape, post both now-landed sibling tickets

`src/world/camp.py`, `CampService.process_camps(state, generator) -> StateUpdate` (line 22). Iterates
`state.camps.items()` only — **no directive/faction awareness of any kind today**, and no parameter to
receive one. Called from `src/engine/world_dynamics.py:174-175`
(`WorldDynamicsSystem.resolve_dynamics()`, itself called at `pipeline.py:343`, phase `"world_dynamics"`,
**after** `faction_decision`/phase 8b in the same `refine()` call — confirmed by line order, so
`faction_directives` is in scope and available to thread down by the time `world_dynamics` runs).
`resolve_dynamics(state, update, generator, cadence=None)` has **no existing `faction_directives`
parameter** — adding one as a new trailing optional (`faction_directives: list | None = None`) is
backward-compatible with all 9 existing call sites confirmed via grep (`tests/unit/world/
test_world_dynamics.py`, `test_sovereignty_events.py`, `test_creature_territory_lifecycle.py`,
`test_reproduction_humanoid_cadence.py`, `test_camp_lifecycle.py`,
`tests/integration/world/test_phase9_stability.py`) — all use positional `state, update, generator`
plus keyword `cadence=`, none pass a 4th positional arg that a new trailing param would shadow.

`CampService.process_camps()` has **no dynamic camp-creation mechanism** — confirmed:
`StateUpdate`/`CampUpdate` (`src/core/updates.py:891-911`) has no `camps_add`-shaped field, only
per-existing-camp mutation (`maturity_delta`, `active_set`, `last_raid_tick_set`, `totem_tier_set`,
`stockpile_delta`, `palisade_integrity_set`). `TCK-20260701-SIMQ-EMIT-CAMP`'s working-log entry
("No dynamic camp construction exists in simulation... CampService only evolves existing camps") is
still accurate. Any `EXPAND_TERRITORY → CampService` consumption this ticket adds must therefore act
on **existing** `state.camps` entries that fall inside the directive's `target_region` — it cannot
spawn a new camp there.

## CRITICAL re-verification: Camp/Nest as a conquest target, post both now-landed sibling tickets

Both `TCK-20260904-CAMP-NEST-CLASSIFICATION` and `TCK-20260904-CAMPSTATE-PLACE-BRIDGE` are DONE and
landed earlier in this batch. Re-verified directly against current source (not the tickets' own prose):

- `grep -n "CampState(" src/` → exactly one production call site:
  `src/worldbuilding/compiler.py:339`, inside `WorldCompiler.compile()`'s Place-construction loop
  (`compiler.py:336-343`), **conditional** on `p_spec.kind in ("CAMP", "NEST") and
  getattr(p_spec, "creature_kind", None) is not None`.
- `creature_kind: Optional[str]` exists on both `PlaceRecipeSpec` (`src/worldbuilding/recipe.py:37`)
  and `PlaceSpec` (`src/worldbuilding/schema.py:58`), validated against the Camp+Nest race set, `None`
  by default, threaded through the Composition path too (`src/worldassembly/resolver.py:822`).
- `WorldCompiler.compile()`'s final `AuthoritativeState(...)` call now passes `camps=camps`
  (`compiler.py:716`) — confirmed present, unlike the pre-bridge state.
- **But**: per `TCK-20260904-CAMPSTATE-PLACE-BRIDGE`'s own Completion Summary (re-confirmed, not just
  quoted): "no real content (including `hero_guild_routing`) sets `creature_kind`, so `state.camps`
  remains `{}` for every currently-compiled world." Confirmed independently: `grep -rn "creature_kind"
  data/worlds/` → no matches in any real world YAML on disk.

**Conclusion: the recommendation to defer Camp/Nest-as-conquest-target still holds, but for a
narrower and different reason than originally stated.** The mechanism to *construct* a `CampState`
tied to declared content now exists and is real (not "not yet in code" as the ticket's own Assumptions
section frames idea 35). The actual blocker is purely a **content-authoring gap**: zero real world
files opt into `creature_kind`, so `state.camps` is `{}` in every real compiled world today, exactly
as it was before both sibling tickets landed, for a different underlying reason (previously: no
construction path at all; now: construction path exists but is unexercised by any real content). A
Camp/Nest EXPAND_TERRITORY target would be correctly *wireable* today, but would have **zero real
targets to select** in any world on disk, and could only be exercised via synthetic test fixtures —
identical to the "wired but inert" pattern the CAMPSTATE-PLACE-BRIDGE ticket itself shipped and
disclosed for its own bridge. This ticket's own scope decision to stay on `RegionState.owner_faction_id`
only (not Camp/Nest) remains the correct, narrower target-resolution choice — it does not need to
change — but `plan.md` should record this re-verified, corrected reasoning rather than repeating the
original (now partially stale) "not yet in code" framing.

## Material-possession predicate — re-verified final shape, and why not to hard-gate on it here

`TCK-20260904-MATERIAL-POSSESSION-PREDICATE` landed just before this ticket in the batch.
`src/domains/progression/material_predicate.py::recipe_materials(recipe_id) -> Tuple[str, ...]` reads
exclusively through `src/core/recipes.py::RecipeRegistry` (3 entries: `iron_sword`, `iron_shield`,
`health_potion`), by that ticket's own explicit Acceptance Criteria. Its own Completion Summary
discloses (re-confirmed directly against the module docstring, `material_predicate.py:1-35`): the
predicate's practical hit-rate against **organically-populated** `entity.identity.known_recipes` is
**zero** in production, because `known_recipes` is populated exclusively by
`src/engine/blacksmith.py::BlacksmithSystem.enforce()` (unconditionally wired every tick,
`pipeline.py:223`) via a disjoint 14-entry `craft_*`-prefixed catalog that shares no ids with
`recipes.py`'s 3-entry catalog. This is a confirmed, disclosed, structural namespace mismatch, not a
transient gap.

**Recommendation for this ticket**: do not use `recipe_materials()` as a hard gate for
`EXPAND_TERRITORY` emission — doing so would make the branch practically unreachable against any real
entity's organically-populated `known_recipes`, silently defeating the acceptance criterion that
requires the directive to be "tested for both trigger and no-trigger cases" in a way that reflects real
production behavior. The ticket's own Assumptions section already frames material-possession
informing as a **soft, non-blocking** recommendation ("this ticket can proceed with
population-pressure-only gating if the predicate isn't ready") — this re-verification confirms that
soft framing was the right call, and additionally that the predicate isn't merely "not ready" but
**structurally near-inert against real content today**, regardless of readiness. Population-pressure
gating alone (`compute_population_density`/`compute_regional_scarcity` over `fs.territory`) is the
correct sole hard gate; if `plan.md` still wants to consult `recipe_materials()` for a soft
priority/tie-break modifier, it must disclose the same inertness caveat inline, matching the
originating ticket's own disclosure pattern rather than silently assuming it works.

## Mechanics / Engine Constraints

- `docs/systems/faction_contract.md` (`layer: systems`, `status: authoritative`) is the actual
  authoritative source for `FactionDirective`/`FactionDecisionPhase` behavior — **not** one of the 6
  Mechanics Bible chapters. `DEFEND_BORDER`/`TRADE_ROUTE`/`COMMISSION_QUEST` are documented only here,
  never in `docs/mechanics/05_world_evolution.md` or `04_strategic_cognition.md`. `EXPAND_TERRITORY`
  should follow the same documentation home, not introduce a new one.
- FAC-003 (`docs/parity_ledger/faction.yaml`) directly constrains the transient-scratch requirement:
  "directives are not persisted in AuthoritativeState." Any implementation that adds a
  `StateUpdate`/`AuthoritativeState` field for `EXPAND_TERRITORY` (rather than reading it as a pure
  local value inside the same `refine()` call) would violate this and must not happen.
- `docs/mechanics/06_worldbuilding_foundation.md` (declarative topology / sovereignty) governs
  `RegionState.owner_faction_id`'s semantics at world-compile time — confirmed no conflicting rule
  there; the field is genuinely optional/unclaimed-by-default per that chapter's declarative-topology
  model, consistent with using it as a "faction-less" signal.
- `docs/world/raid_boss_camp_contract.md`'s "Camp" section is the authoritative behavioral doc for
  `CampService.process_camps()` — any new directive-consumption branch added there is a real behavioral
  change this doc must describe, matching the precedent set by the Camp/Nest classification and Nest
  spread subsections it already carries for the two sibling tickets' additions.

## Docs Requiring Update

- `docs/systems/faction_contract.md`: add `EXPAND_TERRITORY` to the "Directive Kinds" table (constant,
  value, emission condition) and to the `FactionDirective Schema` code comment (`directive_kind` value
  list, currently "one of: DEFEND_BORDER | TRADE_ROUTE | COMMISSION_QUEST"); note the new
  `CampService` consumption path in the "Pipeline Position" section's phase-8b/world_dynamics
  description.
- `docs/parity_ledger/faction.yaml`: FAC-003's `text`/`v2_evidence`/`test_path` must be updated to
  include the 4th directive kind and its `CampService` consumption point, per this ticket's own
  explicit Scope line.
- `docs/world/raid_boss_camp_contract.md`: the "## Camp — `camp.py`" section needs a new subsection (or
  cross-reference) describing the new `faction_directives`-consuming branch inside
  `CampService.process_camps()` — this is a real, new input to documented behavior, not merely
  infrastructure.

The `docs/mechanics/05_world_evolution.md` chapter (path: `docs/mechanics/05_world_evolution.md`,
under `docs/mechanics/`) is not required to change for this ticket: it documents regional
trauma/ecology/calamity mechanics and region ownership/influence generally (line 46: "Regions can be
claimed and controlled by specific factions based on their active Influence"), but has never
documented `FactionDecisionPhase`'s directive-kind vocabulary — confirmed via grep, none of
`DEFEND_BORDER`/`TRADE_ROUTE`/`COMMISSION_QUEST` appear there either. `docs/systems/faction_contract.md`
is the established documentation home for directive kinds; adding a fourth one there is consistent
with precedent and does not require also touching this chapter.

The `docs/mechanics/04_strategic_cognition.md` chapter §6.10 (path:
`docs/mechanics/04_strategic_cognition.md`, under `docs/mechanics/`) is not required to change for
this ticket: §6.10 documents `faction_directives`' (disclosed-dead) consumption by
`AdventureRouteScorer`/`AdventureGoalScorer`'s urgency-scoring path specifically (STRAT-252) — a
different, unrelated consumer from the `CampService` consumption path this ticket adds. This ticket's
own Acceptance Criteria do not require extending the urgency-scoring table for `EXPAND_TERRITORY`, and
doing so would be scope creep into a path already flagged elsewhere as not live.

The `docs/audits/D19_domain_phase_inventory.md` §6 Faction Decision row (path:
`docs/audits/D19_domain_phase_inventory.md`, under `docs/audits/`) is not required to change for this
ticket: audits are dated point-in-time snapshots, cite-only per CLAUDE.md and the precedent set by
`TCK-20260904-CAMPSTATE-PLACE-BRIDGE`'s own Completion Summary ("`docs/audits/*` hits were left
untouched (cite-only per CLAUDE.md, and audits are dated point-in-time snapshots, not living reference
docs)").

## Parity Ledger Overlap

- `docs/parity_ledger/faction.yaml` FAC-003 (status `verified`, priority P2): direct target of this
  ticket's required update, per explicit Scope line. Not P0, so a passing `test_path` is a strong
  expectation but not a hard release gate — the ticket's own test_path
  (`tests/unit/domains/faction/test_faction_decision_phase.py`) already exists and must gain
  `EXPAND_TERRITORY` coverage.
- `docs/parity_ledger/strategic_cognition.yaml` FACTION-DIR-001 / STRAT-252: overlaps conceptually
  (both concern `faction_directives` consumption) but is **not** touched by this ticket's scope — the
  urgency-scoring consumer is a separate, already-disclosed-dead path; STRAT-252's text describing that
  dead path remains accurate and unaffected by adding a new, different (`CampService`) consumer
  elsewhere.
- `docs/parity_ledger/world_dynamics.yaml` WORLD-109/WORLD-124 (both re-verified above, `CampState`
  construction): overlap conceptually (both concern `CampService`/`state.camps`) but are not P0 and are
  not directly modified by this ticket — this ticket adds a new *input* to `CampService.process_camps()`
  without changing camp construction/classification, which those entries document. No update required
  to those specific entries unless `plan.md` decides the new consumption branch changes their
  described behavior (it should not, since `state.camps` remains `{}` for all real content regardless).
- No P0 entries found directly overlapping this ticket's scope.

## Prior Work

- `TCK-20260619-E53Ab-DECISION-PHASE` (`tickets/done/`): original `FactionDecisionPhase` +
  `FactionDirective` implementation — the direct precedent this ticket must mirror for
  constant/branch/test structure.
- `TCK-20260619-E53Ac-DIRECTIVE-PROP` (`stored_artifacts/`): the original (now largely superseded by
  `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`) directive-propagation ticket — useful context for
  why `faction_directives` threading to a second consumer (`CampService`, this ticket) is a genuinely
  new pattern, not a repeat of the original propagation mechanism (which targeted
  `AdventureRouteScorer`, not `CampService`).
- `TCK-20260904-CAMP-NEST-CLASSIFICATION` / `TCK-20260904-CAMPSTATE-PLACE-BRIDGE`
  (`stored_artifacts/`): both re-verified in detail above — confirm `CampService`'s current shape,
  `NEST_RACE_KINDS`, `ENABLE_CAMP_NEST_SPREAD`, and the still-inert (content-gap-blocked)
  `CampState`-construction bridge.
- `TCK-20260904-MATERIAL-POSSESSION-PREDICATE` (`tickets/done/`, `stored_artifacts/`): re-verified
  above — confirms `recipe_materials()`'s real shape and its structural near-inertness against
  production `known_recipes`.
- `src/world/reproduction_humanoid.py:71` and `src/world/camp.py:114-116`: direct code precedent for
  gating a world-dynamics-adjacent mechanic on `compute_regional_scarcity(region.id, state) >
  threshold`, the pattern this ticket's new branch should follow.

## Risks and Open Questions

1. **Exact population-pressure threshold and aggregation over `fs.territory` is undecided** — no
   existing faction-scoped precedent picks a specific density/scarcity threshold for a
   faction-level (as opposed to single-region) decision. `plan.md` must pick and justify one (e.g. max
   scarcity across `fs.territory` regions, or mean density), consistent with the existing
   `migration_threshold` default (0.7) used elsewhere in `cohort.py`, or propose its own with rationale
   — this is a real design decision, not a mechanical translation.
2. **What "consumption" at `CampService` concretely does is not specified by the ticket and has no
   precedent to copy verbatim.** Given `CampService` cannot construct new camps and `state.camps` is
   `{}` in every real world today, the consumption branch will be real, tested, and reachable via
   direct unit-test construction of a non-empty `state.camps` dict (matching the exact testing pattern
   `test_camp_lifecycle.py` already uses), but will have **zero observable effect in any currently
   compiled real world** — an "wired but inert against real content" outcome, structurally identical to
   `TCK-20260904-CAMPSTATE-PLACE-BRIDGE`'s own disclosed outcome. This must be stated explicitly in
   `plan.md`'s scope description, not discovered later as a surprise or treated as a implementation
   defect.
3. **Feature-flag gating is undecided.** `DEFEND_BORDER`/`TRADE_ROUTE`/`COMMISSION_QUEST` are
   unconditional (no flag). `CampService.process_camps()` itself is also unconditional (flagged
   explicitly as a risk by `TCK-20260904-CAMPSTATE-PLACE-BRIDGE`'s own investigation, "not
   feature-flag-gated at all"). Given `state.camps` is `{}` for all real content today, an unflagged
   `EXPAND_TERRITORY` consumption branch has zero real-world behavioral risk today — but `plan.md`
   should make an explicit call (flagged vs. unflagged) rather than defaulting silently, since the
   moment real content ever sets `creature_kind`, this becomes live gameplay behavior with no flag to
   fall back on.
4. **`RegionState.owner_faction_id` vs. `FactionState.territory` divergence** (documented above under
   Current Behavior) means a region flagged as a valid `EXPAND_TERRITORY` target
   (`owner_faction_id is None`) could, in principle, already be counted in some *other* faction's
   `FactionState.territory` tuple if that ever drifted out of sync (no current code path causes this,
   but nothing enforces the two stay consistent either). Low risk given current code paths never write
   `owner_faction_id_set` during territory transfer, but worth a defensive check
   (`region_id not in fs.territory` for every faction) in the target-resolution logic if `plan.md` wants
   to be strict, or an explicit disclaimer if not.

## Anti-Drift Hazards

- Do not add Camp/Nest-as-conquest-target logic to `EXPAND_TERRITORY`'s target resolution — confirmed
  above that real content still cannot exercise it (zero `creature_kind`-bearing world files), even
  though the underlying `CampState`-construction mechanism now technically exists.
- Do not attempt City-ownership-aware resolution (idea 35) — still design-only, no implementation
  ticket exists.
- Do not add a `camps_add`-shaped field to `StateUpdate`/`CampUpdate` to let `EXPAND_TERRITORY`
  "create" a camp in a targeted region — `CampService` has no camp-construction mechanism today and
  adding one is far outside this ticket's stated multi-file-but-bounded scope.
- Do not persist `EXPAND_TERRITORY` (or any field derived from it) into `AuthoritativeState` or
  `StateUpdate` — FAC-003's transient-scratch rule is mechanically enforced by two existing anti-drift
  tests that must keep passing unmodified in structure (only their coverage should grow).
- Do not use `recipe_materials()` as a hard gate for `EXPAND_TERRITORY` emission — confirmed
  structurally near-inert against real `known_recipes`; population-pressure signals
  (`compute_population_density`/`compute_regional_scarcity`) are the correct sole hard gate.
- Do not silently change `resolve_dynamics()`'s or `CampService.process_camps()`'s existing positional
  parameter order — the new `faction_directives` parameter must be added as a trailing optional
  (default `None` or `()`), preserving all 9 existing call sites' positional-plus-`cadence=` calling
  convention confirmed above.
- Do not touch `src/world/creature_territory.py`, `src/worldbuilding/compiler.py`'s
  `CampState`-construction branch, or the Camp/Nest classification table
  (`docs/mechanics/05_world_evolution.md` §6) — all are the sibling tickets' already-closed, unrelated
  scope.
