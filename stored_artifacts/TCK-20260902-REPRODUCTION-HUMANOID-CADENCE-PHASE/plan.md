---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE
artifact_type: plan
tags: [lifecycle, engine]
---

# Implementation Plan — TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE

## Summary

Add a genuinely new `SystemCadence` field (`reproduction_humanoid`, default 200 ticks) and wire
it as a nested cadence check inside `WorldDynamicsSystem.resolve_dynamics()`'s existing
`cadence.world_dynamics`-gated block — following the exact precedent already present in that same
block for `cadence.boss_spawn` (step 3.4). On firing, a new `HumanoidReproductionService`
(new file, `src/world/reproduction_humanoid.py`) does a single O(n) pass over ADULT/alive/active
entities, then uses the existing indexed `SpatialQueryService.nearby_entities()` grid lookup
(not a naive all-pairs scan) to find same-`kind`, cooldown-clear, unpaired candidates within a
10-unit radius — reusing `CampService`'s own established "10-unit same location" numeric
convention. A matched pair produces a new CHILD-stage entity via a new
`EntityGenerator.spawn_humanoid_offspring()` method modeled directly on the shipped
`spawn_natural_creature_offspring()` pattern, calling the already-shipped
`V2EntityBuilder.birth_record()` with real parent ids/roles/genetic profiles. Both parents get a
`reproduction_cooldowns_add` upsert (400 ticks, 2x the cadence interval) and a reciprocal
`SocialBond` via the already-shipped `build_parent_bond_updates_for_birth()`. No marriage-contract
check is introduced anywhere. Scarcity suppression reuses `compute_regional_scarcity()` /
`migration_threshold` exactly as the natural-creature sibling did. The whole path ships behind a
new, dedicated `ENABLE_REPRODUCTION_HUMANOID_PATH` flag (default OFF).

## Decisions (resolving the three flagged investigation items)

### Decision 1 — New `SystemCadence` field, not a reused gate

Read `src/engine/cadence.py:4-35` directly: `SystemCadence` is a flat, frozen Pydantic model,
one plain snake_case `int` field per subsystem, grouped by tier comment (`# World /
Environmental (Very Slow)` at `cadence.py:31-35` currently holds `world_dynamics=50`,
`ecology=100`, `building_sabotage=100`, `boss_spawn=100`). Per the roadmap doc
(`docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md:29-31`, cited verbatim in
investigation.md), this path — unlike its two shipped siblings — is the one the roadmap
explicitly calls a "genuinely new cadence-gated sub-phase" for. Add `reproduction_humanoid: int =
Field(200, ge=1)` to that same World/Environmental block. Name follows the file's existing
plain-semantic-snake-case convention exactly (`world_dynamics`, `boss_spawn`, etc.) — never the
design-doc-only `wd_16`/`WD_16` label from `rpg_feature_atlas.html:947`, which is not a code
identifier anywhere in `src/` (confirmed by investigation's grep).

**Interval value: 200 ticks.** Read `src/domains/demographics/cohort.py:334`
(`DemographicCycleService.COHORT_INTERVAL: int = 200`) and `src/world/camp.py:19`
(`CAMP_SPAWN_INTERVAL = 30`) — the two nearest tick-scale analogs. 200 is chosen over 30 because
(a) it is a multiple of the outer `cadence.world_dynamics` gate (50) that the nested check will
run inside — see call-site decision below — so the nested `should_run` check aligns cleanly with
one out of every four `world_dynamics` passes instead of firing on an off-beat schedule; (b) it
matches `COHORT_INTERVAL`'s semantic scale (both are "how often does a population-level cycle
turn over"), which is a closer analogy than `CAMP_SPAWN_INTERVAL` (a per-camp monster-garrison
tick, not a demographic cycle).

**Call site: a new "3.10" step inside `resolve_dynamics()`'s existing `cadence.world_dynamics`
block, nested-should_run, following the boss_spawn precedent — not a separate top-level phase.**
Read `src/engine/world_dynamics.py:127-199` in full: the whole "3. Process Macro World Dynamics"
block is already gated by `if should_run(state.tick, None, cadence.world_dynamics):`
(`world_dynamics.py:131`). Step "3.4 Boss Spawning" at `world_dynamics.py:155-160` already nests
a *second, independent* cadence check (`if should_run(state.tick, None, cadence.boss_spawn):`)
inside that outer block — proving nesting a differently-cadenced sub-phase inside the
already-gated block is an established pattern in this exact file, not an architectural novelty
(investigation.md Risk #2 flagged this as "unusual" without having found this precedent; it is
in fact already done once in the same function). Step "3.9 Creature Territory Lifecycle"
(`world_dynamics.py:193-199`) is the closest structural precedent for a flag-gated additive
sub-step with its own `feature_flags.get(...)` check and `update.merge()` pattern. This ticket's
new step goes immediately after 3.9 as step "3.10 Humanoid Reproduction", combining both
patterns: `if flags.get("ENABLE_REPRODUCTION_HUMANOID_PATH", "OFF") == "ON" and
should_run(state.tick, None, cadence.reproduction_humanoid): ... update = update.merge(repro_update)`.
This call site has direct access to `state.entities` (needed for pairing) and `generator`
(needed to construct the child entity), unlike `apply_plan.py`'s cadence reads
(`cadence.biological`/`cadence.lifecycle`, `apply_plan.py:278-279`) which operate per-entity, not
on cross-entity pairs.

### Decision 2 — "Same-race" = `EntityState.kind`; "same-location" = 10-unit indexed radius, not O(n²)

**Same-race.** Read `src/core/state.py:497-518` (`IdentityComponent`) and `state.py:737-751`
(`EntityState`): no `race` field exists on either. `EntityState.kind: str` (`state.py:740`) is
the only candidate field, and it is exactly the field the natural-creature sibling already reads
this way (`spawn_natural_creature_offspring()` sets `kind="goblin_warrior"`/`"orc_warrior"`,
`src/systems/world_systems/generator.py:110-120`). Eligibility uses `entity_a.kind ==
entity_b.kind`.

**Same-location.** Read `src/world/camp.py:46-51`: `CampService.process_camps()`'s garrison
filter uses `abs(e.navigation.position[0]-camp.position[0]) < 10 and abs(...[1]-...[1]) < 10` —
a 10-unit-tolerance box, not exact equality. Read `src/engine/spatial_query.py:46-65`:
`SpatialQueryService.nearby_entities(state, pos, radius, dirty=None)` is a real indexed query —
it calls `WorldIndexService.get_indexes(state, dirty)` and walks only the tile buckets
(`indexes.entities_by_tile`) inside `[pos-radius, pos+radius]`, not every live entity. This is
the existing spatial index investigation.md asked to check for; it exists and must be reused
instead of a naive nested loop. Define `HUMANOID_PAIRING_RADIUS = 10.0` on the new service,
directly reusing `CampService`'s numeric convention (10), and define same-location as "entity B's
id is in `SpatialQueryService.nearby_entities(state, entity_a.navigation.position,
HUMANOID_PAIRING_RADIUS)`" (a circular radius check via the indexed grid, translating
`CampService`'s square-box convention into the indexed-query's circular one — same numeric scale,
indexed instead of brute-force).

**Performance bound (avoiding O(n²)).** The pairing scan is: (1) one O(n) pass over
`state.entities.items()` to build a `candidates` list filtered to
`identity.life_stage == LifeStage.ADULT and combat.alive and lifecycle.active` (same three-flag
convention already used at `world_dynamics.py:31`); (2) sort `candidates` by entity id ascending
for deterministic iteration order; (3) for each unpaired candidate `a` in that order, call
`SpatialQueryService.nearby_entities(state, a.navigation.position, HUMANOID_PAIRING_RADIUS)` —
an indexed grid lookup bounded by local tile density, not global entity count — and from the
returned ids pick the lowest-id unpaired candidate `b` (also in `candidates`, `b.kind ==
a.kind`, neither has an unexpired `reproduction_cooldowns` entry for the other) as the pair; mark
both paired and continue. Total cost is `O(n log n)` for the sort plus `O(n * k)` for the scan,
where `k` is local tile density (bounded, not `n`) — not `O(n²)` over the full world. No
settlement/city grouping field exists on live entity state to bucket by instead (confirmed:
`grep` for `city_id`/`settlement` across `state.py` finds only `LifecycleComponent.birth_city_id`,
a post-birth record field, not a live-position grouping), so the indexed spatial query is the
correct and only existing mechanism to reuse — not a new settlement bucket.

### Decision 3 — Cooldown duration: 400 ticks (2x the cadence interval)

No existing numeric anchor exists anywhere in the codebase for "how long between two people's
births" (confirmed by investigation.md and by this plan's own reads above —
`reproduction_cooldowns: Dict[int, int]` at `src/core/state.py:167` stores only a
"partner_id -> expiry_tick" shape with no default duration constant). Chosen value: **400
ticks**, defined as a `REPRODUCTION_COOLDOWN_TICKS = 400` constant on the new
`HumanoidReproductionService`. Reasoning: it must be a small multiple of the 200-tick cadence
interval (Decision 1) so that "a repeat check on the same pair before cooldown clears does not
produce a second birth" (AC5) is provable across at least one skipped cadence firing, not just
the same firing — 400 = 2x 200 guarantees the pair remains blocked through the very next cadence
firing after the birth, then becomes eligible again on the second one after. This is the same
"multiple of the driving interval" reasoning already used for the interval choice itself
(Decision 1), applied one level down, rather than an arbitrary new scale like
`CAMP_SPAWN_INTERVAL` (30, too short — would clear before the very next cadence firing) or
`COHORT_INTERVAL` alone (200, too short — would clear exactly on the next firing, leaving the
AC5 "before cooldown clears" test with no tick window to assert against).

## Steps

### Step 1 — Add `reproduction_humanoid` field to `SystemCadence`
**Files:** `src/engine/cadence.py`
**Change:** Add `reproduction_humanoid: int = Field(200, ge=1)` inside the existing `# World /
Environmental (Very Slow)` block (`cadence.py:31-35`), alongside `world_dynamics`, `ecology`,
`building_sabotage`, `boss_spawn`. Per Decision 1 above. No other field, comment block, or
`should_run()` logic changes — `should_run()` (`cadence.py:38-54`) is generic and needs no
modification to support the new field.
**Do NOT touch:** Any other `SystemCadence` field, the tier grouping comments for other tiers, or
`should_run()`'s body.
**Verify:** `test_new_cadence_entry_fires_per_should_run_pattern` (new).

### Step 2 — Register `ENABLE_REPRODUCTION_HUMANOID_PATH` feature flag
**Files:** `src/domains/optimization/feature_flags.py`
**Change:** Add `"ENABLE_REPRODUCTION_HUMANOID_PATH": FeatureMode.OFF` immediately after the
existing `"ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH"` entry (`feature_flags.py:147-153`), with a
comment in the same style as the two existing sibling entries (`feature_flags.py:141-146,
147-153`) describing the new gameplay behavior and citing the DEV-002 default-OFF policy. Per
investigation.md's confirmed convention: each reproduction path gets its own dedicated flag,
never a shared one.
**Do NOT touch:** `ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH` or
`ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH` entries, or any other flag.
**Verify:** `test_flag_off_produces_no_birth_regression_guard` (new).

### Step 3 — Add `EntityGenerator.spawn_humanoid_offspring()`
**Files:** `src/systems/world_systems/generator.py`
**Change:** Add a new method modeled directly on `spawn_natural_creature_offspring()`
(`generator.py:85-120`, read in full and cited above), but with real parent data instead of the
parentless defaults:
```
def spawn_humanoid_offspring(
    self, pos, state, kind, parent_a_id, parent_b_id, birth_tick, birth_city_id,
    parent_a_genetic_profile, parent_b_genetic_profile, parent_a_role, parent_b_role,
) -> EntityState
```
Unlike the sibling's fast-forwarded `age_ticks = 3000 - CAMP_SPAWN_INTERVAL` maturation trick
(`generator.py:108`, `118`), this entity is a real newborn: `life_stage=LifeStage.CHILD`,
`age_ticks=0` (no maturation-clock shortcut — this path has no analogous "must appear
battle-ready soon" requirement the natural-creature sibling had). Calls
`.birth_record(parent_a_entity_id=parent_a_id, parent_b_entity_id=parent_b_id,
birth_tick=birth_tick, birth_city_id=birth_city_id,
parent_a_genetic_profile=parent_a_genetic_profile, parent_b_genetic_profile=parent_b_genetic_profile,
parent_a_role=parent_a_role, parent_b_role=parent_b_role)` — the already-shipped
`V2EntityBuilder.birth_record()` signature (`src/core/builder.py:622-635`, read in full) accepts
every one of these kwargs already; no change to `birth_record()` itself.
**Do NOT touch:** `spawn_natural_creature_offspring()`, `spawn_magical_demonic_entity()`,
`spawn_hero()`, or `V2EntityBuilder.birth_record()`/`GeneticsSystem.combine_profiles()`
themselves — this step is purely a new caller.
**Verify:** `test_eligible_adult_alive_same_location_same_race_pair_produces_birth` (new).

### Step 4 — Add `HumanoidReproductionService` (new file)
**Files:** `src/world/reproduction_humanoid.py` (new)
**Change:** New service, structurally parallel to `CampService`/`CalamityService`
(`process_camps`/`process_world_dynamics` return a `StateUpdate`). Public entry point:
`HumanoidReproductionService.process_reproduction(state: AuthoritativeState, generator:
EntityGenerator) -> StateUpdate`. Body, per Decision 2's performance bound:
1. Build `candidates`: one pass over `state.entities.items()` filtered to
   `entity.identity.life_stage == LifeStage.ADULT and entity.combat.alive and
   entity.lifecycle.active` (same three-flag convention as `world_dynamics.py:31`), sorted by
   entity id ascending.
2. `HUMANOID_PAIRING_RADIUS = 10.0`, `REPRODUCTION_COOLDOWN_TICKS = 400` — class constants per
   Decisions 2 and 3.
3. For each unpaired candidate `a`, call `SpatialQueryService.nearby_entities(state,
   a.navigation.position, HUMANOID_PAIRING_RADIUS)`; from the returned ids, select the
   lowest-id unpaired candidate `b` where `b.kind == a.kind` and neither
   `a.lifecycle.reproduction_cooldowns.get(b.id, 0) > state.tick` nor
   `b.lifecycle.reproduction_cooldowns.get(a.id, 0) > state.tick`.
4. Per matched pair, compute the birth region via
   `WorldDynamicsSystem._get_region_for_pos(state, a.navigation.position)`-equivalent (reuse
   `SpatialQueryService.get_region_at(state, a.navigation.position)` directly — the private
   helper on `WorldDynamicsSystem` just wraps this same call, `world_dynamics.py:248-250`) and
   apply the scarcity gate: skip the pair if `region is not None and
   region.population_cohorts` is non-empty and `compute_regional_scarcity(region.id, state) >
   region.population_cohorts.get("young", PopulationCohort(bracket="young")).migration_threshold`
   — the exact skip-when-empty convention `cohort.py:242-243`/`:358-359` already establishes and
   the natural-creature sibling's plan.md (Decision 2) already reused verbatim; this ticket
   reuses it a second time, not re-derives it.
5. On a surviving pair: call `generator.spawn_humanoid_offspring(...)` (Step 3), passing
   `parent_a_genetic_profile=a.lifecycle.genetic_profile`, `parent_b_genetic_profile=
   b.lifecycle.genetic_profile` (both typically `None` for first-generation parents per
   investigation.md Risk #5 — pass through as-is, `None` included, so `birth_record()`'s own
   `generate_profile_from_seed(parent_id or 0)` fallback engages), and
   `parent_a_role=a.identity.role`, `parent_b_role=b.identity.role` (investigation.md Risk #6).
6. Build the `StateUpdate`: `entities_add=[child]`; two `EntityUpdate(entity_id=a.id,
   lifecycle=LifecycleUpdate(reproduction_cooldowns_add={b.id: state.tick +
   REPRODUCTION_COOLDOWN_TICKS}))` / same for `b` keyed on `a.id`; merge in
   `build_parent_bond_updates_for_birth([a.id, b.id], child.id, state.tick, ...)` (already
   shipped in `src/core/builder.py`) for the parents' reciprocal `SocialBond`s.
**Do NOT touch:** `CampService`, `CalamityService`, `DemographicCycleService`,
`compute_regional_scarcity()`, `find_adjacent_regions()`, or write to
`WorldUpdate.population_cohorts_set` anywhere in this file (per the epic's build order — closed
later by `TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE`, not here).
**Verify:** `test_eligible_adult_alive_same_location_same_race_pair_produces_birth`,
`test_both_parents_cooldown_set_and_repeat_check_before_cooldown_clears_produces_no_second_birth`,
`test_eligibility_suppressed_when_regional_scarcity_exceeds_migration_threshold`,
`test_eligibility_allowed_when_regional_scarcity_below_migration_threshold`,
`test_ineligible_pairs_produce_no_birth`,
`test_social_bond_seeded_between_each_parent_and_child_at_high_familiarity_sentiment`.

### Step 5 — Wire the call site into `WorldDynamicsSystem.resolve_dynamics()`
**Files:** `src/engine/world_dynamics.py`
**Change:** Immediately after step "3.9 Creature Territory Lifecycle" (`world_dynamics.py:193-199`),
inside the existing `if should_run(state.tick, None, cadence.world_dynamics):` block
(`world_dynamics.py:131`), add:
```
# 3.10 Humanoid Reproduction
flags = getattr(state, "feature_flags", None) or {}
if (flags.get("ENABLE_REPRODUCTION_HUMANOID_PATH", "OFF") == "ON"
        and should_run(state.tick, None, cadence.reproduction_humanoid)):
    from src.world.reproduction_humanoid import HumanoidReproductionService
    repro_update = HumanoidReproductionService.process_reproduction(state, generator)
    if not repro_update.is_noop():
        update = update.merge(repro_update)
```
This combines the flag-gate pattern of step 3.9 (`world_dynamics.py:194-199`) with the nested
independent-cadence pattern already used by step 3.4 for `cadence.boss_spawn`
(`world_dynamics.py:155-160`) — see Decision 1's call-site reasoning. Other writers to `update`
inside this same "3." block that this new step must not collide with: step 3.7's
`demo_update` merge (`world_dynamics.py:170-185`, writes `world_updates` for
`population_cohorts` — this ticket's step never touches that key, per the scope guard) and step
3.9's `territory_update` merge (`world_dynamics.py:193-199`, writes its own
`entities_add`/`world_updates` disjoint from this ticket's). `StateUpdate.merge()` (used by both
existing precedents) is the same accumulation mechanism this new step reuses, so
`entities_add` lists concatenate rather than overwrite, and `world_updates`/`entity_updates`
dicts merge key-by-key — consistent with how 3.7 and 3.9 already coexist in the same block.
**Do NOT touch:** Steps 3.1–3.9, the "4. Regional Transformations" or "5. Global Object
Lifecycle" blocks below it, or the outer `cadence.world_dynamics` gate itself.
**Verify:** `test_humanoid_reproduction_commits_through_authoritative_apply_path` (new,
integration) plus the full existing Regression Surface list in test_plan.md (this file is the
single highest-blast-radius file touched by this ticket).

### Step 6 — Architecture-guard tests
**Files:** `tests/unit/world/test_reproduction_humanoid_cadence.py` (new)
**Change:** Add `test_no_marriage_contract_referenced_in_humanoid_reproduction_path` (source-text
grep of `src/world/reproduction_humanoid.py` and `generator.py`'s new method for
`ContractKind.MARRIAGE`/`MarriageState`/`ContractState`, plus a behavioral assertion that a
successful birth requires no `strategic.contracts` entry — mirrors the birth-record schema
ticket's `test_no_marriage_precondition_in_birth_record_schema_or_apply_path` pattern exactly)
and `test_no_population_cohorts_write_in_humanoid_reproduction_path` (asserts
`HumanoidReproductionService.process_reproduction()`'s returned `StateUpdate` never sets
`population_cohorts_set` on any `WorldUpdate`, mirroring both shipped siblings' identical guard).
**Do NOT touch:** The existing sibling guard tests in `test_natural_creature_reproduction.py` /
`test_calamity_magical_demonic_reproduction.py` — this step adds this ticket's own guards, it
does not modify the siblings' guards.
**Verify:** Both new tests pass; `grep -rn "ContractKind.MARRIAGE\|MarriageState"
src/world/reproduction_humanoid.py src/systems/world_systems/generator.py` returns nothing
(AC3's explicit grep-verifiability requirement).

### Step 7 — Full new-tests file
**Files:** `tests/unit/world/test_reproduction_humanoid_cadence.py` (continues Step 6's file)
**Change:** Add the remaining tests enumerated in test_plan.md's "New Tests Required" #1–2, #4–5,
#8–10 (test #3 and #7 land in Step 6; #6's pair lands alongside #4/#5). Fixture shapes follow
`test_natural_creature_reproduction.py`'s existing helpers (`_region`, `_node`) directly — reuse,
do not reinvent. The genetics-real-parent-data guard (both parents `identity.role ==
EntityRole.HERO` → child's `GeneticProfile` shows combat-lean bias) is included per test_plan.md's
Anti-Drift Test Guards section, proving Step 4's `parent_a_role`/`parent_b_role` threading
(investigation.md Risk #6) actually works end-to-end through this ticket's own call site, not
just through `combine_profiles()`'s pre-existing unit tests.
**Do NOT touch:** `tests/unit/progression/test_lifecycle.py`,
`tests/unit/progression/test_genetics.py`, or any test file in the Regression Surface list — run
them, do not edit them.
**Verify:** Full scoped pytest command from test_plan.md (both blocks) passes.

### Step 8 — Docs: mechanics chapter + parity ledger entry
**Files:** `docs/mechanics/05_world_evolution.md`, `docs/parity_ledger/world_dynamics.yaml`
**Change:** Add a new subsection to `05_world_evolution.md` parallel to the existing
"Natural-Creature Reproduction" and "Magical/Demonic Reproduction" subsections (placement per
investigation.md's Docs Requiring Update — nearer the Migration Law, matching the siblings'
placement), documenting: the `ENABLE_REPRODUCTION_HUMANOID_PATH` flag, the 200-tick
`reproduction_humanoid` cadence and its 3.10 call site, the ADULT/alive/same-`kind`/same-location
(10-unit radius)/cooldown-clear (400-tick) eligibility, the genetics-inheritance call, the
parent/child `SocialBond` seeding, the scarcity-suppression reuse, and — per AC7 — an explicit
statement that individual births from this path do not yet feed the aggregate
`population_cohorts` signal (closed by `TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE`).
Add one new entry to `docs/parity_ledger/world_dynamics.yaml`. Current max id as of this Plan
read is `WORLD-121` (`docs/parity_ledger/world_dynamics.yaml:1725`, the magical-demonic sibling)
— use `WORLD-122`, but the implementer must re-grep `^- id: WORLD-1` immediately before writing
the entry in case a concurrent ticket has advanced the max in the meantime (per
investigation.md's own caveat). Entry fields: `status: verified`, `priority: P2`,
`v2_evidence` citing `src/world/reproduction_humanoid.py`, `src/engine/cadence.py`'s new field,
and `world_dynamics.py`'s 3.10 step; cross-reference `SOC-259` (birth-record schema), `SOC-260`
(genetics inheritance), `WORLD-121`/`WORLD-120` (sibling reproduction paths, same
flag-per-path/scarcity-gate-reuse conventions), and `WORLD-DEMO-001` (Migration Law, reused not
reimplemented); `test_path` pointing at
`tests/unit/world/test_reproduction_humanoid_cadence.py::test_eligible_adult_alive_same_location_same_race_pair_produces_birth`.
**Do NOT touch:** Any other parity ledger entry's `status`/`v2_evidence`, or
`docs/engine/kernel.md`/`docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md` (both
explicitly excluded by investigation.md's Docs Requiring Update section — no change needed).
**Verify:** No automated test; verified by review against AC7's wording and
`validate_frontmatter.py`/parity-ledger schema check.

### Step 9 — Stale doc-text fix (bundled, per ticket's Out-of-Scope carve-out)
**Files:** `docs/brainstorm/rpg_feature_atlas.html`
**Change:** This is a one-line text correction, small enough to bundle per the ticket's own
Out-of-Scope wording ("unless Plan decides it's trivial enough to bundle in"). At
`rpg_feature_atlas.html:947` (verified present by investigation.md's direct read), the "Phase
placement mapping" table row currently reads: *"...and the human/humanoid **marriage-gated**
path has no existing precedent at all — needs a new cadence-gated sub-phase (proposed
`WD-16`)..."* — edit only the word "marriage-gated" (remove it / replace with neutral phrasing
noting the 2026-08-29 decoupling) and leave a footnote or adjacent clarifying phrase that
`WD-16` was this design doc's own internal step-numbering label, not the eventual code identifier
(`reproduction_humanoid`, per Decision 1) — do not delete the `WD-16` label itself, since it
still identifies the design-doc row; just clarify it is not a code reference. No other row,
table, or section of this file is touched.
**Do NOT touch:** Any other row in the "Phase placement mapping" table, idea-32's other card
content, or any other section of `rpg_feature_atlas.html`.
**Verify:** Manual review only — no automated test covers a brainstorm doc's prose.

## Scope Guards

- **No marriage-contract precondition anywhere** — no `ContractKind.MARRIAGE`, `MarriageState`,
  or `ContractState` reference in `src/world/reproduction_humanoid.py`,
  `generator.py`'s new method, or the new `world_dynamics.py` call site. Enforced by Step 6's
  guard test.
- **Do not write `WorldUpdate.population_cohorts_set` anywhere in this ticket's new code** — that
  remains exclusively `DemographicCycleService`'s. Enforced by Step 6's guard test.
- **Do not modify `V2EntityBuilder.birth_record()`, `GeneticsSystem.combine_profiles()`,
  `LifecyclePatch.apply()`,** or any file the birth-record/genetics tickets already shipped and
  tested — this ticket is purely a new caller (Steps 3–4).
- **Do not modify `CampService`, `CalamityService`, `DemographicCycleService`,
  `compute_regional_scarcity()`, or `find_adjacent_regions()`** — read-only reuse throughout.
- **Do not modify steps 3.1–3.9, 4, or 5 of `world_dynamics.py`** — Step 5 only inserts a new
  3.10 after 3.9, touching no existing line above it.
- **Do not reuse `ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH` or
  `ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH`** — this path gets its own dedicated flag (Step 2).
- **Do not literally name the new cadence field `wd_16`/`WD_16`** — that is a design-doc-only
  label, never a code identifier (Decision 1).
- **Do not conflate `age_ticks` brackets with `IdentityComponent.life_stage`** — the ADULT
  eligibility check reads `life_stage`, never `age_ticks` (Decision 2 / Step 4).
- **Do not close the population-pressure feedback loop** (nudging `population_cohorts` on birth)
  — that is `TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE`'s scope, not this ticket's.
- **Do not build a naive all-pairs nested loop** — Step 4 must use the indexed
  `SpatialQueryService.nearby_entities()` bucketed scan, per Decision 2's performance bound.
- **Do not touch `docs/engine/kernel.md` or
  `docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md`** — both explicitly excluded.
- **Do not edit any table row in `rpg_feature_atlas.html` other than the single sentence
  identified in Step 9.**

## Dependency Map

- Step 1 (cadence field) — independent, no dependency.
- Step 2 (feature flag) — independent, no dependency.
- Step 3 (`spawn_humanoid_offspring`) — independent of Steps 1/2, but Step 4 depends on it.
- Step 4 (`HumanoidReproductionService`) — depends on Step 3 (calls
  `generator.spawn_humanoid_offspring`); reads but does not depend on Step 1/2's field/flag
  existing at import time (both are read only at the Step 5 call site).
- Step 5 (call-site wiring) — depends on Steps 1, 2, and 4 all existing (reads
  `cadence.reproduction_humanoid`, checks the flag, imports `HumanoidReproductionService`).
- Step 6 (architecture guards) — depends on Step 4 (tests the service directly).
- Step 7 (full test suite) — depends on Steps 1–5 all landing (exercises the full path end to
  end, including the cadence field and call site).
- Step 8 (mechanics doc + parity ledger) — depends on Steps 1–5 being final (documents the
  actual shipped shape); should land after Step 7's tests pass, not before.
- Step 9 (stale doc-text fix) — fully independent; can land in any order, including first.

Recommended execution order: 1, 2, 3, 4, 5, 6, 7, 8, 9 (9 can be done any time, listed last only
because it is lowest-priority/independent).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| New WD-16-style cadence entry fires periodically per `SystemCadence`'s pattern | Steps 1, 5 | `test_new_cadence_entry_fires_per_should_run_pattern` |
| Eligible pair produces birth with parent_a_id/parent_b_id/birth_tick/birth_city_id + GeneticProfile | Steps 3, 4 | `test_eligible_adult_alive_same_location_same_race_pair_produces_birth` |
| No marriage-contract state read/checked anywhere (grep-verifiable) | Steps 4, 5 (absence) | `test_no_marriage_contract_referenced_in_humanoid_reproduction_path` |
| SocialBond seeded between each parent and child at high familiarity/sentiment | Steps 3, 4 | `test_social_bond_seeded_between_each_parent_and_child_at_high_familiarity_sentiment` |
| Both parents' cooldowns set; repeat check before clearing produces no second birth | Step 4 | `test_both_parents_cooldown_set_and_repeat_check_before_cooldown_clears_produces_no_second_birth` |
| Eligibility suppressed when scarcity exceeds migration_threshold (both cases) | Step 4 | `test_eligibility_suppressed_when_regional_scarcity_exceeds_migration_threshold`, `test_eligibility_allowed_when_regional_scarcity_below_migration_threshold` |
| Mechanics doc + parity ledger entry document the sub-phase and the pop-cohorts gap | Step 8 | Manual/doc review; parity schema validation |
| Note filed on stale "gated on marriage" atlas text | Step 9 | Manual review |

## Anti-Drift Notes

- **`WD-16` is a design-doc label, never a code identifier** (`rpg_feature_atlas.html:947`) —
  the real field name is `reproduction_humanoid` (Step 1).
- **`life_stage` vs `age_ticks`**: ADULT eligibility reads `IdentityComponent.life_stage`
  (`state.py:515`), never the §5 Age Bracket Thresholds' `age_ticks` brackets — those are a
  separate, unrelated axis the natural-creature sibling manipulates for its own maturation
  trick; this ticket does not touch `age_ticks` for eligibility purposes (only sets it to `0` at
  spawn time in Step 3, since this is a real newborn, not a fast-forwarded one).
- **First-generation parents typically have `genetic_profile=None`** — pass this through as-is
  in Step 4 (do not substitute a default), so `birth_record()`'s own
  `generate_profile_from_seed(parent_id or 0)` fallback engages deterministically
  (investigation.md Risk #5).
- **`parent_a_role`/`parent_b_role` must be threaded through explicitly** — omitting this
  silently defaults `combat_lean` to `False` for every pairing with no local test failure, since
  that behavior lives in `GeneticsSystem`/`builder.py`, not this ticket's own code
  (investigation.md Risk #6). Step 7's genetics-real-parent-data guard exists specifically to
  catch this.
- **`reproduction_cooldowns_add` is a per-key upsert merge, never a wholesale replace**
  (`updates.py:449`, `:476-477`) — Step 4 must use `LifecycleUpdate(reproduction_cooldowns_add=
  {other_id: expiry_tick})` for each parent separately, never construct a full replacement dict,
  or two same-tick births involving overlapping parents would clobber each other.
- **No P0 parity entries overlap this ticket's scope** — all four cited entries (`SOC-259`,
  `SOC-260`, `WORLD-120`, `WORLD-DEMO-001`) are P1/P2; this ticket's own new entry
  (`WORLD-122` or next available) is also P2, matching its shipped siblings.
- **Re-check the parity ledger's actual max id at implementation time** — `WORLD-121` was the
  max as of this Plan-phase read; another concurrent ticket may have advanced it before this
  ticket's Step 8 runs.

## Deviations (recorded during Implement)

- **Genetic-profile resolution moved into `HumanoidReproductionService`, not passed through as
  raw `None`.** Decision 2/Step 4's original wording ("pass this through as-is... `None`
  included, so `birth_record()`'s own `generate_profile_from_seed(parent_id or 0)` fallback
  engages deterministically") turned out to describe `birth_record()`'s *inner* per-parent
  fallback only. Direct read of `V2EntityBuilder.birth_record()` (`src/core/builder.py:655`)
  shows an *outer* gate: `if parent_a_genetic_profile is not None or parent_b_genetic_profile is
  not None:` — `combine_profiles()` is skipped entirely, and `lifecycle.genetic_profile` stays
  `None`, when **both** supplied profiles are `None`, which is the common case for
  first-generation parents (Risk #5). A new test
  (`test_eligible_adult_alive_same_location_same_race_pair_produces_birth`) caught this
  immediately (asserted `genetic_profile is not None`, got `None`). Fix: `process_reproduction()`
  now resolves each parent's profile itself —
  `a.lifecycle.genetic_profile or GeneticsSystem.generate_profile_from_seed(a.id)` — before
  calling `spawn_humanoid_offspring()`, mirroring the exact resolution pattern the pre-existing
  `test_birth_record_writes_genetic_profile_via_authoritative_apply_path()`
  (`tests/integration/optimization/test_component_patch_apply_parity.py`) already uses for the
  same reason. This does not touch `birth_record()`/`combine_profiles()` themselves — the Scope
  Guard against modifying those files is intact — it just supplies them a concrete value instead
  of relying on an inner fallback that never fires when both sides are `None`.
- **Offspring `identity.role`/`identity.faction` (`EntityRole.CITIZEN`/`Faction.TOWN_COUNCIL`).**
  Neither the ticket body nor this plan specified what role/faction the newly spawned humanoid
  entity itself should carry (as opposed to `parent_a_role`/`parent_b_role`, which only feed
  `combine_profiles()`'s combat-lean bias). Chose `EntityRole.CITIZEN`/`Faction.TOWN_COUNCIL` —
  the same "generic humanoid civilian" pairing `src/worldbuilding/compiler.py`'s
  `get_role_enum()`/`get_faction_enum()` already use as their own default/CITIZEN-adjacent
  fallback — rather than inventing a new default.
- **`spawn_humanoid_offspring()` gained a `difficulty_tier: int = 1` keyword param and the same
  `DIFFICULTY_TIERS`-scaled base-stat block (`base_hp=50*mults.hp`, etc.) as
  `spawn_natural_creature_offspring()`/`spawn_magical_demonic_entity()`.** Step 3's pseudocode
  signature omitted this, but some base-stat source was required and every sibling spawn method in
  `generator.py` already uses this exact pattern — reusing it kept the new method consistent
  with its neighbors rather than inventing a new stat table.
- **`birth_city_id` is always passed as `None`** from `HumanoidReproductionService`. No live "city"
  registry exists anywhere in `AuthoritativeState` (confirmed by grep — `birth_city_id` is only
  ever written as `None` by both shipped siblings too), so there is no real value to compute here;
  this matches both siblings' own precedent exactly.
- **`tests/tools/test_parity_updater_static.py::test_next_available_id_against_real_world_dynamics_shard`
  updated from `WORLD-122` to `WORLD-123`.** This hardcoded baseline asserted the real shard's
  next-available id before this ticket's own Step 8 wrote `WORLD-122` into
  `docs/parity_ledger/world_dynamics.yaml` — a direct, legitimate consequence of this ticket's own
  ledger write (the exact "hardcoded baseline drift caused by this session's own legitimate
  change" case, not a silent or unrelated edit), so it was updated in the same ticket rather than
  filed as a separate follow-up.
