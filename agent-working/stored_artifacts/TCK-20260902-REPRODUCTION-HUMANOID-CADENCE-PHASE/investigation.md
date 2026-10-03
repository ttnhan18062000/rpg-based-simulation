---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE
artifact_type: investigation
tags: [lifecycle, engine]
---

# Investigation — TCK-20260902-REPRODUCTION-HUMANOID-CADENCE-PHASE

## Current Behavior

### `src/engine/cadence.py` (full file, 55 lines)
`SystemCadence` (`ConfigDict(frozen=True)` Pydantic model, `cadence.py:4-35`) declares one
`int` field per periodic subsystem, grouped by tier: Core (`movement`, `combat`,
`interaction`, `resource_transactions` — cadence 1), Medium (`shop`, `town_resolution`,
`lifecycle`, `biological`, `groups` — cadence 1), Strategic (`strategic_intelligence`,
`concern_evaluation`, `detour_suggestion`, `social_memory`, `faction_decision` — cadence 10),
World/Environmental (`world_dynamics`=50, `ecology`=100, `building_sabotage`=100,
`boss_spawn`=100). Every field is a plain, semantically-named snake_case Python identifier —
there is no `WD-NN`/`PP-NN`-style label anywhere in this file. `should_run(tick, entity_id,
cadence)` (`cadence.py:38-54`) is a pure function: `cadence <= 1` always runs; with
`entity_id=None` it is a global check (`tick % cadence == 0`, used for world-level systems);
with a real `entity_id` it staggers across ticks (`(tick + entity_id) % cadence == 0`, used
for per-entity systems like `strategic_intelligence`).

**`should_run(tick, None, cadence.world_dynamics)` already gates the entire "3. Process Macro
World Dynamics" block** in `src/engine/world_dynamics.py:131` (confirmed by direct read,
`WorldDynamicsSystem.resolve_dynamics`). That block contains sub-steps 3.1–3.9 including "3.6
Process Camps" (`world_dynamics.py:166-168`, calls `CampService.process_camps`) and the
calamity/world-boss spawn path. **Neither shipped reproduction sibling ticket added a new
`SystemCadence` field.** `TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH` added its new spawn
branch *inside* `CampService.process_camps()` (already running under the existing
`cadence.world_dynamics` 50-tick gate), with its own inner tick-modulo constant
(`state.tick % CampService.CAMP_SPAWN_INTERVAL == 0`, 30) plus a brand-new
`FeatureMode.OFF` flag (`ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH`). Its sibling
`TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH` did the same inside `CalamityService`, reusing
the world-boss trigger's own constants (`CALAMITY_MIN_INTERVAL`=2000,
`CALAMITY_FORCE_INTERVAL`=5000) plus `ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH`.

**"WD-16" origin.** Grepping `src/engine/world_dynamics.py`, `src/engine/cadence.py`, and every
`docs/engine/*.md` file for `WD-1[0-9]` returns zero hits — "WD-16" is not a code identifier
anywhere in `src/`. It traces to exactly one place:
`docs/brainstorm/rpg_feature_atlas.html:947`, a design-doc-internal step-numbering scheme used
in a "Phase placement mapping" table (`WD-14`=`CampService`, `WD-15`=the dormant
population-pressure signal, `WD-08`=`CalamityService`'s substrate — none of these correspond to
real `SystemCadence` field names or line-addressable code constants). The row reads verbatim:
*"32 splits three ways: natural births reuse `WD-14` almost directly, magical births reuse
`WD-08`, and **the human/humanoid marriage-gated path** has no existing precedent at all —
needs a new cadence-gated sub-phase (proposed `WD-16`), paired with `WD-15`'s dormant
population-pressure signal."* This is the stale text the ticket asks to be flagged (see Docs
Requiring Update below) — both for the "marriage-gated" phrasing (superseded by the 2026-08-29
decoupling decision) and because "WD-16" is a design-doc label, not something that should be
copied verbatim into `cadence.py` as a field name. If a new `SystemCadence` field is added, it
must follow the file's existing semantic-name convention (e.g. `reproduction_humanoid` or
similar), never a literal `wd_16` identifier.

**Roadmap intent, however, does call for a real new cadence-gated sub-phase here** —
`docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md:29-31` (2026-08-29 plan-owner
decision doc) explicitly distinguishes this path from its two siblings: *"natural creatures
reuse Camp's maturity mechanic, magical/demonic beings reuse the calamity substrate,
human/humanoid needs a **genuinely new** cadence-gated sub-phase."* So unlike the two shipped
siblings (which purely reused the existing `cadence.world_dynamics` gate + an inner constant),
this ticket is the one place in the epic where adding a real `SystemCadence` field is the
intended design — Plan must decide the exact call-site wiring (a new field checked via
`should_run(tick, None, cadence.<new_field>)`, called from `world_dynamics.py`'s "3." block
alongside 3.6/3.9, or from a new step) and the interval value (no existing numeric anchor;
`DemographicCycleService.COHORT_INTERVAL`=200 and `CampService.CAMP_SPAWN_INTERVAL`=30 are the
two nearest analogs on the World/Environmental cadence tier).

### `src/domains/demographics/cohort.py` (420 lines)
`compute_regional_scarcity(region_id, state)` (`cohort.py:153-180`) returns `1.0 -
mean(remaining/max_charges)` across resource nodes inside the region's bounds; returns `1.0`
(max scarcity) if the region is missing or has zero in-bounds resource nodes — a real "safe
default," not "no pressure." `PopulationCohort.migration_threshold` (`cohort.py:35-43`,
default `0.7`) is the per-bracket threshold this ticket's scope compares scarcity against.
`_check_migration`/`DemographicCycleService.process_demographics` (`cohort.py:242-243`,
`:358-359`) both **skip evaluation entirely when `region.population_cohorts` is empty** — this
is the load-bearing convention `TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH`'s plan.md
(Decision 2) reused verbatim for its own scarcity-gate (treat missing region / empty cohorts as
eligible, not suppressed-forever), reading the threshold from the `"young"` bracket with a
`0.7` dataclass-default fallback when that bracket is absent. This ticket's own scarcity gate
(Scope bullet 7) should follow the identical convention rather than re-deriving it, per the
established sibling precedent.

### Birth-record schema (shipped, `TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA`)
`LifecycleComponent` (`src/core/state.py:151-190`) carries `parent_a_entity_id`,
`parent_b_entity_id` (`Optional[int]`), `birth_tick` (`int`, `0` = no-record sentinel),
`birth_city_id` (`Optional[int]`), and `reproduction_cooldowns: Dict[int, int]`
(`partner_entity_id -> cooldown_expiry_tick`). The only authoritative writer is
`LifecyclePatch.apply()` (`src/engine/patches.py:69-...`), driven by `LifecycleUpdate`'s
matching `*_set`/`reproduction_cooldowns_add` fields (`src/core/updates.py`) — the latter is a
**per-key upsert merge** (`{**self.x, **other.x}`, `other` wins on conflict), specifically so
two same-tick writers updating different partners' cooldowns cannot clobber each other.
`V2EntityBuilder.birth_record()` (`src/core/builder.py:622-...`, read in full) is the
construction-time convenience: sets the five Lifecycle fields, optionally combines a
`GeneticProfile` (see next paragraph), and seeds the **child's own** `SocialBond`s toward each
non-`None` parent at `familiarity=0.8`/`sentiment=0.8` via `.social(bonds=...)`. The **parents'**
reciprocal bond is a *separate* mechanism: the module-level
`build_parent_bond_updates_for_birth(parent_ids, child_entity_id, birth_tick, ...)` helper
(`builder.py`) returns `List[EntityUpdate]` with `SocialUpdate(bond_updates=[SocialBondUpdate(...)])`
targeting the two *already-existing* parent entities, meant to be applied through the normal
authoritative pipeline (`RelationshipService.process_update()`,
`src/systems/social_systems/relationships.py:51-62`) by whichever caller triggers a birth — this
ticket is that caller and has not yet been built. **No no-marriage-precondition test exists in
this ticket's own scope yet**, but the birth-record ticket's guard
(`test_no_marriage_precondition_in_birth_record_schema_or_apply_path`) already locks the
schema/apply path itself free of any `ContractState`/`ContractStatus` reference — this new
cadence phase must not introduce one either (AC3).

### Genetics inheritance (shipped, `TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE`)
`GeneticsSystem.combine_profiles(parent_a, parent_b, *, combat_lean, seed)` (`src/systems/
lifecycle_systems/genetics.py`) is a pure, deterministic per-attribute convex-combination +
seeded-perturbation function, structurally clamped to `[0.8, 1.3]`. `V2EntityBuilder.birth_record()`
already wires this in: pass `parent_a_genetic_profile`/`parent_b_genetic_profile` (each an
optional `GeneticProfile`, falling back internally to `GeneticsSystem.generate_profile_from_seed(parent_id
or 0)` when `None`) and `parent_a_role`/`parent_b_role` (raw `EntityRole` ints — `combat_lean`
is `True` only when both equal `EntityRole.HERO`; every other pairing, including `None`/`None`,
falls through to the neutral default) and `birth_record()` calls `combine_profiles()` and writes
the result via a second internal `.lifecycle(genetic_profile=combined)` call. **This ticket's
job is only to supply these kwargs with real live-entity values** (`parent_a.identity.role`,
`parent_b.identity.role`, and each parent's own `lifecycle.genetic_profile` if any — noted by
the genetics ticket's own Anti-Drift Notes as typically `None` for first-generation parents,
since no live spawn path populates a parent's own `genetic_profile` today; the builder's
`generate_profile_from_seed(parent_id or 0)` fallback covers this deterministically, "not a
defect requiring a broader fix").

### Live entity fields for "same-location" / "same-race" / eligibility (verified directly)
- **No `race` field exists anywhere on `IdentityComponent` or `EntityState`.** The closest real
  field is `EntityState.kind: str` (`src/core/state.py:740`) — the same field
  `spawn_natural_creature_offspring()` sets to `"goblin_warrior"`/`"orc_warrior"`, and
  `EntityGenerator.spawn_hero()` presumably sets to something like `"hero"`. "Same-race" in this
  ticket's scope must be implemented as `entity_a.kind == entity_b.kind`, and this mapping
  should be stated explicitly in the plan/implementation, since "race" is not a literal field
  name anywhere in the schema.
- **`entity.identity.life_stage`** (`IdentityComponent.life_stage: LifeStage`, default `ADULT`)
  is the ADULT-eligibility check; `LifeStage` (`state.py:436-440`) is `CHILD`/`ADULT`/`ELDER`.
- **`entity.combat.alive`** and **`entity.lifecycle.active`** are the two existing liveness
  flags used together everywhere else in the engine (e.g.
  `WorldDynamicsSystem.resolve_dynamics`'s own hazard-drain loop, `world_dynamics.py:31`:
  `if entity.combat and entity.combat.alive and entity.lifecycle and entity.lifecycle.active`).
- **"Same-location" has two existing precedents, neither an exact-equality check:**
  `CampService.process_camps()`'s garrison-count filter uses a `10×10` bounding box
  (`abs(e.navigation.position[0]-camp.position[0]) < 10 and abs(...[1]-...[1]) < 10`,
  `camp.py:49-51`); `SpatialQueryService.nearby_entities()`/`get_entities_near()`
  (`src/engine/spatial_query.py`) provide an **indexed** radius query backed by
  `WorldIndexService`/`DomainView`'s cached spatial grid, avoiding a full `O(n²)`
  all-entities-vs-all-entities scan. Given the eligibility check is "same-location," not
  "within a radius," the plan should pick one of: (a) exact `navigation.position` tuple
  equality (simplest, matches "co-located" literally, but brittle against float movement
  jitter), or (b) a small bounding box/radius reusing the `10`-unit convention already
  established by `CampService`. Either way, the population this phase iterates over should be
  built via the spatial index (or grouped by rounded position) rather than a naive nested loop
  over every live ADULT entity pair — see Risks below on the `O(n²)` cost.

### Feature flags (`src/domains/optimization/feature_flags.py`, full file read)
Both shipped siblings registered their own dedicated `FeatureMode.OFF` flag following the
DEV-002 default-OFF policy: `ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH`
(`feature_flags.py:141-146`) and `ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH`
(`:147-153`). Per the natural-creature ticket's own Decision 3, each reproduction path gets its
**own** flag (`ENABLE_REPRODUCTION_<PATH>`), never a shared one — so this ticket needs its own
new entry, e.g. `ENABLE_REPRODUCTION_HUMANOID_PATH` (exact name is a Plan-phase naming
decision, but must follow the `ENABLE_REPRODUCTION_<PATH>` convention already set by the two
siblings, not deviate).

## Mechanics / Engine Constraints

- **`docs/mechanics/05_world_evolution.md` §5, Migration Law**: "When `scarcity(region) >
  cohort.migration_threshold` (default 0.7), 30% of that cohort (min 1) emigrates..." — this
  ticket's scarcity-suppression gate (Scope bullet 7) must cite and reuse this law's underlying
  functions (`compute_regional_scarcity`, `PopulationCohort.migration_threshold`) exactly as the
  Natural-Creature Reproduction subsection (added directly below the Migration Law in the same
  chapter) already does, including the skip-when-empty convention.
- **`docs/mechanics/05_world_evolution.md` §5, Age Bracket Thresholds**: `age_ticks < 3000` →
  young, `3000–6999` → adult, `≥7000` → elder — these are **entity-level `age_ticks` brackets**,
  distinct from `IdentityComponent.life_stage` (`CHILD`/`ADULT`/`ELDER`), which is the field this
  ticket's ADULT-eligibility check actually reads (per Scope bullet 3, "both entities ADULT life
  stage"). Do not conflate the two — the Natural-Creature ticket deliberately kept both systems
  independent (its own maturation clock manipulates `age_ticks`, not `life_stage`, directly).
- **`docs/mechanics/01_entity_anatomy.md`, Birth Record + Genetic Inheritance subsections**
  (added by the two hard-dependency tickets): document the exact schema/combination formula this
  ticket's cadence phase must call into — no new formula is introduced here, only a new caller.
- **Durable State Rule (`CLAUDE.md`)**: the produced birth (new entity + parent cooldown writes +
  parent bond writes) must go through `V2EntityBuilder.birth_record()` for the new entity
  (`entities_add`) and through typed `EntityUpdate`/`StateUpdate` (via
  `LifecycleUpdate.reproduction_cooldowns_add` for each parent, and
  `build_parent_bond_updates_for_birth()`'s `EntityUpdate.social` for each parent's reciprocal
  bond) for mutations to the two already-existing parent entities — never a direct
  `dataclasses.replace()` on live state.
- **No marriage-contract precondition** — explicit 2026-08-29 build-order decoupling
  (`docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md:26-27`). AC3 requires this be
  verifiable by grep (`ContractKind.MARRIAGE`/`MarriageState` absent from the new code), mirroring
  the birth-record schema ticket's own architecture-guard test pattern.

## Docs Requiring Update

- `docs/mechanics/05_world_evolution.md`: needs a new subsection under `## 6. Calamities & World
  Threats` (or a new `## 5.x` subsection nearer the Migration Law, per Plan's judgment),
  parallel to the existing "Natural-Creature Reproduction" and "Magical/Demonic Reproduction"
  subsections, documenting the new cadence sub-phase's flag, trigger interval, eligibility
  checks (ADULT/alive/same-location/same-race/cooldown/scarcity), the genetics-inheritance call,
  the parent/child `SocialBond` seeding, and — per AC7 — explicitly stating that individual
  births from this path do not yet feed back into the aggregate `population_cohorts` signal
  (closed by `TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE`).
- `docs/parity_ledger/world_dynamics.yaml`: needs a new entry (next available `WORLD-1xx` id —
  `WORLD-120` is the current max as of this Investigate-phase read; confirm at implementation
  time other concurrent tickets have not advanced it) documenting this mechanism, cross-
  referencing `SOC-259` (birth-record schema), `SOC-260` (genetics inheritance), `WORLD-120`
  (the sibling natural-creature path, same scarcity-gate pattern), and `WORLD-DEMO-001`
  (the underlying Migration Law, P1, reused not reimplemented).
- `docs/brainstorm/rpg_feature_atlas.html`: only if Plan decides, per the ticket's own Out of
  Scope carve-out ("note it as a disclosed gap ... unless Plan decides it's trivial enough to
  bundle in"), to bundle the tiny stale-text fix into this ticket rather than filing it as a
  separate follow-up ticket. The exact text to correct is at `rpg_feature_atlas.html:947`, in
  the "Phase placement mapping" table's "Reproduction, Marriage, Coming of Age" row: *"...and
  the human/humanoid **marriage-gated** path has no existing precedent at all — needs a new
  cadence-gated sub-phase (proposed `WD-16`)..."* — the "marriage-gated" phrasing is stale
  relative to the 2026-08-29 decoupling decision (this path is explicitly NOT marriage-gated per
  this ticket's own scope), and the informal "`WD-16`" label should not be copied verbatim into
  any real code identifier (see Current Behavior above). If Plan instead files the small
  follow-up ticket AC8 also allows, resolve this bullet with the phrase "Resolved during
  implementation, condition not met."

Two docs were considered and explicitly excluded. `docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md`
(path: `docs/plans/rpg_design_roadmap/rpg_m3_family_species_epic.md`) does not need to change for
this ticket: it is a forward-looking roadmap/build-order document, not a description of shipped
mechanics, and neither hard-dependency sibling ticket touched it when they shipped their own
reproduction paths. `docs/engine/kernel.md` (path: `docs/engine/kernel.md`) also does not need to
change: it documents the 7-phase deterministic loop structure and cadence-registration pattern in
general terms, and this ticket's cadence entry is a semantic addition to `SystemCadence`
following the file's own existing pattern, not a change to the loop's phase structure itself —
neither shipped sibling ticket touched it either.

## Parity Ledger Overlap

- `SOC-259` (`docs/parity_ledger/social_narrative.yaml`, `status: verified`, `priority: P2`) —
  birth-record durable schema. This ticket is the schema's real trigger-path consumer for the
  human/humanoid case.
- `SOC-260` (`docs/parity_ledger/social_narrative.yaml`, `status: verified`, `priority: P2`) —
  genetics combination. This ticket is `GeneticsSystem.combine_profiles()`'s second real caller
  context (the first, `birth_record()` itself, already exists; this ticket is what actually
  drives it with live parent data for the first time in a running simulation).
- `WORLD-120` (`docs/parity_ledger/world_dynamics.yaml`, `status: verified`, `priority: P2`) —
  sibling natural-creature path, same scarcity-gate reuse pattern this ticket must follow.
  Cross-reference, not modify.
- `WORLD-DEMO-001` (`docs/parity_ledger/world_dynamics.yaml`, `status: verified`, `priority: P1`)
  — the underlying Migration Law (`compute_regional_scarcity`/`migration_threshold`) this
  ticket's scarcity gate reuses verbatim. **No `test_path` gap found** on direct read of this
  entry (P1, not P0 — does not carry the hard "P0 entries require a passing `test_path`"
  obligation from CLAUDE.md, but its existing test coverage should still not regress).
- **No P0 entries were found overlapping this ticket's scope.** All four cited entries above are
  P1/P2.

## Prior Work

- `TCK-20260902-REPRODUCTION-BIRTH-RECORD-SCHEMA` (done) — schema + `V2EntityBuilder.birth_record()`
  + `build_parent_bond_updates_for_birth()`. Hard dependency, already landed.
- `TCK-20260902-REPRODUCTION-GENETICS-INHERITANCE` (done) — `GeneticsSystem.combine_profiles()` +
  `birth_record()` genetics kwargs. Hard dependency, already landed.
- `TCK-20260902-REPRODUCTION-NATURAL-CREATURE-PATH` (done) — closest structural precedent: flag-
  gated periodic spawn trigger, scarcity-gate reuse with the skip-when-empty convention,
  parentless `birth_record()` call. This ticket differs in three structural ways the plan must
  address explicitly: (1) it operates on **existing** entity **pairs**, not a single
  camp/territory anchor spawning a fresh entity — so eligibility scanning is a different shape
  (entity-pair matching vs. per-camp iteration); (2) it **does** populate real parent ids,
  genetics, and cooldowns (the sibling left all of these at their parentless/`None` defaults);
  (3) per the roadmap doc, it is the one path in the epic intended to get a **real new
  `SystemCadence` field**, not just reuse `cadence.world_dynamics` + an inner constant.
- `TCK-20260902-REPRODUCTION-MAGICAL-DEMONIC-PATH` (done) — same flag-per-path convention, same
  parentless-birth-record pattern, no scarcity gate (explicitly not applicable to a calamity-
  driven spawn). Confirms the "own dedicated flag per path" naming convention this ticket must
  follow (`ENABLE_REPRODUCTION_<PATH>`).
- `TCK-20260831-CREATURE-TERRITORY-LIFECYCLE` — cited by the natural-creature ticket as a sibling
  precedent for reusing `CampService`'s trauma-multiplier shape; same general "reuse an existing
  per-tick service loop rather than inventing new plumbing" spirit relevant here, though this
  ticket's actual home (an entity-pair scan) has no equivalent existing per-tick loop to slot
  into.

## Risks and Open Questions

1. **Cooldown duration has no existing numeric anchor.** The birth-record-schema ticket's plan.md
   explicitly deferred "cooldown *values* or *when* a cooldown gets written" to "a future
   reproduction-trigger ticket" — this is that ticket. `DemographicCycleService.COHORT_INTERVAL`
   (200) and `CampService.CAMP_SPAWN_INTERVAL` (30) are the nearest tick-scale analogs but neither
   is semantically "how long between two people's births" — Plan must choose and justify a value;
   this is a genuine open design decision, not something Investigate should collapse.
2. **New `SystemCadence` field wiring is unresolved.** Unlike the two siblings, this ticket is
   expected (per the roadmap doc) to add a real field to `SystemCadence` and call
   `should_run(tick, None, cadence.<field>)` — but from where? `world_dynamics.py`'s existing "3."
   block is already itself gated by `cadence.world_dynamics`; nesting a second, independent
   cadence check inside it (a different-cadence sub-phase inside an already-cadence-gated block)
   is architecturally unusual and needs an explicit Plan decision on call-site placement — a new
   "3.10" step in `world_dynamics.py`, a separate top-level call from `resolve_dynamics`, or a
   different phase host entirely (e.g. `apply_plan.py`, which already reads `cadence.biological`/
   `cadence.lifecycle` directly, `apply_plan.py:278-279`).
3. **`O(n²)` cost of same-location/same-race entity-pair scanning.** No existing service in the
   codebase does a full live-entity pairwise scan; `SpatialQueryService` exists specifically to
   avoid this. Left unaddressed, a naive nested loop over every ADULT/alive entity in a populated
   world risks violating `docs/engine/performance_contract.md`'s hardware-class scaling limits.
   This should be explicitly designed around at Plan time (bucket entities by rounded position
   and `kind` first, then only compare within-bucket pairs), not left to be discovered as a perf
   regression later.
4. **"Same-location" exact semantics are undefined by the ticket text.** Exact `navigation.position`
   tuple equality vs. a small bounding box (matching `CampService`'s existing `10`-unit
   convention) — see Current Behavior above. This changes both the eligibility-test fixtures and
   the entity-grouping strategy from risk #3; Plan should resolve this explicitly rather than
   implicitly picking one via test-writing.
5. **First-generation parents typically have no `genetic_profile` of their own.** As the genetics
   ticket's Anti-Drift Notes already state, this is an accepted, intentional gap (the builder's
   `generate_profile_from_seed(parent_id or 0)` fallback covers it deterministically) — not a
   defect this ticket needs to fix, but the cadence phase's caller code must correctly pass
   `None` (not omit the kwarg or pass a wrong default) when a parent's own `lifecycle.genetic_profile`
   is unset, so the fallback actually engages.
6. **`parent_a_role`/`parent_b_role` for combat-lean bias.** `birth_record()` expects raw
   `EntityRole` ints. This ticket must read `parent.identity.role` from each live parent entity
   and pass it through — trivial, but easy to silently omit (which would default `combat_lean` to
   `False`/neutral for every pairing, silently losing AC-relevant genetics behavior from the
   sibling ticket without any test failure locally to this ticket, since that behavior lives in
   `GeneticsSystem`/`builder.py`, not here).

## Anti-Drift Hazards

- **Do not literally name the new `SystemCadence` field `wd_16`/`WD_16`.** That label is a
  design-doc-only step-numbering artifact (`rpg_feature_atlas.html:947`), not a code convention —
  every existing `SystemCadence` field is a plain semantic snake_case name.
- **Do not conflate `age_ticks` brackets (young/adult/elder, §5 Age Bracket Thresholds) with
  `IdentityComponent.life_stage` (CHILD/ADULT/ELDER)** — this ticket's ADULT-eligibility check
  reads `life_stage`, per Scope bullet 3's explicit wording ("ADULT life stage"), not `age_ticks`.
- **Do not add a marriage-contract precondition anywhere** — explicit, resolved 2026-08-29
  decision; verify via grep for `ContractKind.MARRIAGE`/`MarriageState`/`ContractState` in the new
  code, mirroring the birth-record schema's own architecture-guard test.
- **Do not write to `region.population_cohorts`/`WorldUpdate.population_cohorts_set` anywhere in
  this ticket's new code.** Per AC7 and the epic's own build order, this is explicitly closed by
  `TCK-20260902-REPRODUCTION-POPULATION-PRESSURE-CLOSURE`, not this ticket — the two shipped
  siblings both added an explicit architecture-guard test for this same boundary
  (`test_natural_creature_reproduction_does_not_write_population_cohorts`); this ticket should add
  an equivalent guard.
- **Do not introduce a shared/reused flag name** — each reproduction path gets its own
  `ENABLE_REPRODUCTION_<PATH>`-pattern flag per the natural-creature ticket's Decision 3; do not
  reuse `ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH` or
  `ENABLE_REPRODUCTION_MAGICAL_DEMONIC_PATH`.
- **Do not modify `V2EntityBuilder.birth_record()`, `GeneticsSystem.combine_profiles()`,
  `LifecyclePatch.apply()`, or any of the four files the birth-record/genetics tickets already
  extended** — this ticket is purely a new caller of that already-shipped, tested surface, not a
  schema-extension ticket.
- **Do not skip the per-key `reproduction_cooldowns_add` merge shape** — cooldown writes for two
  different parents in the same tick must go through the existing per-key-upsert
  `LifecycleUpdate.reproduction_cooldowns_add` field, never a wholesale-replace dict, or two
  same-tick births/cooldown-sets in the same tick will silently clobber each other exactly the
  scenario that field's shape was designed to survive.
- **Do not build the entity-pairing scan as a naive full nested loop without at least a
  position/kind pre-bucketing step** — see Risks #3 above; this is a real, not hypothetical,
  performance hazard given the eventual world sizes this engine targets.
