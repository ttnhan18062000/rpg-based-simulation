---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260902-ENTITIES-DOC-REWRITE
artifact_type: investigation
tags: [documentation]
---

# Investigation — TCK-20260902-ENTITIES-DOC-REWRITE

## Current Behavior

### The fictional doc (`docs/core/entities.md`, current content)
- L9: title claims "The Aspect-Oriented Model."
- L17: claims a shell class `Entity` at `src/core/entities/entity.py`. **Confirmed non-existent**:
  `src/core/entities/` does not exist anywhere in the repo; there is no `Entity` shell class.
- L33-59 "Aspect Decomposition": `IdentityAspect`, `SpatialAspect`, `CombatAspect`,
  `ProgressionAspect`, `MindAspect`. **Confirmed non-existent**: no `class .*Aspect` definition
  exists anywhere under `src/` (repo-wide grep, zero matches).
- L64-71 "Factions & Relations" table (`HERO_GUILD`, `GOBLIN_HORDE`, `WOLF_PACK`, `UNDEAD`,
  `ORC_TRIBE`) — plausible-looking but not independently re-verified against
  `src/core/enums.py::Faction` in this pass (out of the ticket's specifically-called-out fields;
  flagged as an open item below, not asserted true or false).
- L75-80 "Genetic Seeds": claims every entity has a `deterministic_seed` field that generates its
  `Aptitude` pool, and (earlier, L53) that aptitudes are "Genetic multipliers (0.8x - 1.2x)... two
  heroes of the same level can have radically different builds." **Investigated and found
  unsupported by current code**: `grep -rn "deterministic_seed"` across all of `src/` returns zero
  matches — no such field exists on `EntityState`, `AptitudeComponent`, or anywhere else.
  `AptitudeComponent` (`src/core/state.py:530-562`) does hold 9 per-stat float multiplier fields
  (`str_apt`, `agi_apt`, etc.) plus `learning_rate`/`stamina_efficiency`, but their *default* is
  `1.0` for all fields, and no `0.8`-`1.2` randomization range or seed-based assignment logic was
  found anywhere in `src/systems/world_systems/generator.py::EntityGenerator` (the real spawn path)
  or `src/core/builder.py::V2EntityBuilder`. World-level determinism is real (`AuthoritativeState.
  seed` + `src/platform/rng.py::DeterministicRNG`, domain-separated per-tick seeding), but the
  *specific* "deterministic_seed field → 0.8x-1.2x genetic aptitude roll" claim is not corroborated
  by any code path found in this investigation. This must not be carried forward as-is into the
  rewrite (see Anti-Drift Hazards).
- L48: `status_effects: List of active StatusEffect objects` under (fictional) `CombatAspect` —
  this one specific field claim IS coincidentally accurate: `CombatComponent.status_effects:
  List[StatusEffectState]` is real (`src/core/state.py:323`), matching `docs/core/state.md`'s
  Combat row (`status_effects`).

### The real architecture (`src/core/state.py`, ground truth)
`EntityState` (`src/core/state.py:723-961`, `@dataclass(frozen=True, slots=True)`) is the
authoritative entity atom. It composes 16 typed component fields, not 5 Aspects and not the 8 rows
`docs/core/state.md`'s summary table lists (that table is a deliberately-abbreviated top-level
summary, not the full field list):
- `interaction: InteractionComponent` (`state.py:402`) — `target_node_id`, `progress`,
  `start_tick`, `kind` (harvest/ground_item/corpse/chest/guild/inn/tavern).
- `identity: IdentityComponent` (`state.py:484`) — `role`, `faction`, `known_recipes`,
  `craft_target`, `evolution_level`, `evolution_points`, `veterancy_points`, `veterancy_rank`,
  `unspent_ap`, `territory_maturity`, `class_id`, `learned_skills`, `traits`,
  `active_breakthroughs`, `cooldowns`, `personality` (nested `PersonalityComponent`), `life_stage`,
  `group_id`, `properties`, `latest_intent_results`.
- `attributes: AttributeComponent` (`state.py:452`) — 9 primary stat ints (`strength`, `agility`,
  `vitality`, `endurance`, `intelligence`, `spirit`, `wisdom`, `perception`, `charisma`); matches
  `docs/core/attributes_and_classes.md`'s 9-attribute table field-for-field.
- `inventory: InventoryComponent` — defined in `src/core/models/inventory.py` (imported into
  `state.py:16`), not defined inline in `state.py` itself.
- `strategic: StrategicComponent` (`src/core/strategic.py:383`) — `home_region_id`, `blockers`,
  `leads`, `directives`, `projects`, `concerns`, `candidate_zones`, `hypotheses`, `source_trust`,
  `contracts`, `turning_points`, `beliefs`, `committed_intentions`, `current_project_id`,
  `current_objective_id`, `profile` (`CognitionProfile`), `primary_overload_source`,
  `last_overload_tick`, `boredom`. This is the real "Strategic" component `docs/core/state.md`
  already documents at its abbreviated level — `entities.md`'s fictional `MindAspect.strategic`
  sub-field is a rough, incomplete echo of this real component.
- `social: SocialComponent` — defined in `src/core/models/social.py` (imported at `state.py:17`),
  not defined inline.
- `biological: BiologicalComponent` (`state.py:125`) — `sleep_debt`, `hunger`, `rest_pressure`,
  `last_meal_tick`, `last_sleep_tick`, `well_rested_until`.
- `lifecycle: LifecycleComponent` (`state.py:152`) — `age_ticks`, `max_age_ticks`,
  `is_permadeath`, `death_tick`, `death_reason`, `generation`, `heir_entity_id`, `heirlooms`,
  `active`.
- `aptitude: AptitudeComponent` (`state.py:530`) — see above; 9 per-stat multipliers plus
  `learning_rate`/`stamina_efficiency`, all default `1.0`.
- `combat: CombatComponent` (`state.py:306`) — `hp`, `max_hp`, `atk`, `def_stat`, `speed`, `range`,
  `evasion`, `move_cost`, `tactical_role`, `action_style`, `alive`, `readiness`, `readiness_speed`,
  `wounds` (`List[WoundState]`), `scars` (`List[ScarState]`), `status_effects`
  (`List[StatusEffectState]`), `latest_result`.
- `equipment: EquipmentComponent` (`state.py:707`) — `slots: Dict[EquipSlot, str|None]`,
  `durability: Dict[EquipSlot, float]`.
- `navigation: NavigationComponent` (`state.py:369`) — `position`, `target`, `path`,
  `moved_recently`, `movement_mode`, `last_failure_reason`, congestion-recovery fields
  (`wait_count`, `oscillation_count`, `last_position`), leash fields (`home_position`,
  `leash_radius`), `region_id`, `chase_ticks`, `max_chase_ticks`, `returning_home`.
- `task: TaskComponent` (`state.py:395`) — `work_kind`, `payload`.
- `stamina: StaminaComponent` (`state.py:57`) — `current`, `max_stamina`, `regen_rate`,
  `rest_regen_rate`, `exhaustion_threshold`, `exhaustion_penalty`, plus class-level drain constants
  (`ATTACK_COST`, `MOVE_COST`, `HARVEST_COST`, `SKILL_COST_MULT`).
- `self_model: SelfModelBundle` — defined in `src/core/self_model.py`, imported at `state.py:19`.
  Not named anywhere in the ticket's spot-check list or in either sibling doc's summary table —
  a real gap in both `entities.md` (never mentioned) and `state.md` (also not in its 8-row table).
- `cognition: CognitionModel` — defined in `src/core/cognition.py`, imported at `state.py:20`. Same
  gap as `self_model`: real, composed, undocumented in either sibling doc's top-level table.

`EntityState` also carries `id: int`, `kind: str`, and three `InitVar`-only construction helpers
(`init_position`, `init_group_id`, `init_properties`) consumed once in `__post_init__`
(`state.py:838-852`) and not stored as fields themselves — the real analog of `entities.md`'s "Core
Properties" (`id`, `kind`) claim, minus the fictional `next_act_at` field (not found anywhere in
`EntityState` or `AuthoritativeState`; `TaskComponent.work_kind`/`payload` and the kernel's own
scheduling state are the real analogs, not a field on the entity itself).

`docs/core/strategic.py` cross-check: `StrategicComponent` (`src/core/strategic.py:383-416`) is
confirmed as described above. Verified against real code, not assumed from `state.md`'s summary
alone.

### Real construction path (V2EntityBuilder / EntityGenerator)
- `src/core/builder.py::V2EntityBuilder.__init__` (`builder.py:88-107`) is the sole real
  entity-construction path referenced by this ticket's ground truth — it instantiates all 16
  components (`identity`, `inventory`, `combat`, `navigation`, `strategic`, `social`, `biological`,
  `lifecycle`, `attributes`, `aptitude`, `equipment`, `interaction`, `task`, `stamina`,
  `self_model`, `cognition`), confirming `EntityState`'s composition list above field-for-field.
- `src/systems/world_systems/generator.py::EntityGenerator` (`generator.py:20-33`) is the real
  spawn/ID-assignment mechanism: `get_next_id()` (`generator.py:30-32`) is a simple monotonic
  counter (`self._last_id += 1`), used by `spawn_hero`/monster-spawn methods, each of which builds
  via `V2EntityBuilder(entity_id)....identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD,
  ...)`. `AuthoritativeState.__post_init__` (`state.py:1218-1263`) additionally guards
  `next_entity_id` against collisions with any pre-existing integer entity keys. Neither mechanism
  resembles `entities.md`'s "monotonic integer id assigned by the Entity shell" framing (there is
  no `Entity` shell), but the *substance* of "unique monotonic integer id" is accurate and should
  be preserved, reattributed to `EntityGenerator`/`AuthoritativeState`.
- No `next_act_at` field, `WorkerPacket` class, or literal "Generation-Based Apply" / "Phase-Locked
  Mutation" / "Shallow Packetization" terminology was independently re-verified in this pass beyond
  what `docs/core/state.md`'s existing "Frozen Lifecycle Law" section already documents accurately
  (snapshot → deliberation → refinement → transition via `AuthoritativeState.apply()`). The rewrite
  should describe entity mutation timing by pointing to `docs/core/state.md`'s existing accurate
  section rather than re-describing (and risking re-diverging from) it.

## Mechanics / Engine Constraints
This is a documentation-only rewrite with zero source changes (`Out of Scope` explicitly excludes
all `src/` files). No Mechanics Bible formula or Engine Contract phase rule is being altered, so
there is no mechanics/engine constraint that *restricts what the doc rewrite may say* beyond one
thing worth flagging directly: **the rewrite must not assert `AptitudeComponent` multipliers are
applied on attribute-point allocation** — `docs/parity_ledger/progression.yaml` entry `PROG-069`
(status: `divergent`, priority: `P0`) documents that `execute_allocate_ap`
(`src/engine/domain/core_actions.py`) applies AP spend as a flat delta with **no aptitude lookup**;
the only code that ever applied the aptitude multiplier to AP allocation
(`AllocateAttributeAction`, `src/actions/attributes.py:39-43`) was dead code, deleted per `DEV-004`
(`docs/guidelines/intentional_divergences.md`). This is a real, docs-adjacent constraint even
though it lives in a parity ledger entry, not a mechanics chapter: it directly bears on whether the
rewritten doc's aptitude description is accurate. Separately, `docs/core/attributes_and_classes.md`
§3 ("Level-Up Attribute Gains") documents a *different* function, `level_up_attributes()`, as
correctly applying aptitude-modified per-level attribute gains — this is the accurate mechanism to
cite for "aptitudes affect stat growth," not the AP-allocation path. See Anti-Drift Hazards.

## Docs Requiring Update
- `docs/core/entities.md`: rewrite the "Aspect-Oriented Model" description (fictional `Entity`
  shell, `IdentityAspect`/`SpatialAspect`/`CombatAspect`/`ProgressionAspect`/`MindAspect`) to
  describe the real Component-based architecture — `EntityState`'s 16 composed components in
  `src/core/state.py` (plus `StrategicComponent` in `src/core/strategic.py`) — aligned with
  `docs/core/state.md`'s existing accurate framing, and correct the unsupported `deterministic_seed`
  / "0.8x-1.2x genetic aptitude roll" claim per the Current Behavior findings above.

`docs/core/state.md` and `docs/core/attributes_and_classes.md` were read as reference material only
(both are already accurate per this investigation's cross-checks and are explicitly Out of Scope
for modification per the ticket) — not required-to-change docs. `docs/parity_ledger/progression.yaml`
(the `PROG-069` entry) is also not required to change: the ticket's Out of Scope explicitly excludes
parity ledger updates, and this investigation's cross-check confirms `PROG-069`'s existing status
(`divergent`, `v2_evidence`, `test_path`) is already correct and does not itself need editing — it
is cited here only as a constraint on what `entities.md`'s rewritten content may claim, not as a
ledger entry requiring a status change.

## Parity Ledger Overlap
- `docs/parity_ledger/progression.yaml::PROG-069` (status: `divergent`, priority: `P0`, `test_path:
  tests/unit/quest/test_progression_regression.py::test_execute_allocate_ap_silently_no_ops_for_unhandled_attribute`)
  — directly overlaps `entities.md`'s Aptitude/ProgressionAspect claim. Flagged above as a
  Mechanics/Engine Constraint on the rewrite's content, not as a ledger entry to modify (Out of
  Scope per the ticket). The P0 entry already has a passing `test_path`, confirmed to exist on disk
  (`tests/unit/quest/test_progression_regression.py`).
- No other parity ledger entry across `substrate.yaml`, `combat_movement.yaml`,
  `strategic_cognition.yaml`, `town_resource.yaml`, `social_narrative.yaml`, `world_dynamics.yaml`,
  or `infrastructure.yaml` was found citing `entities.md`'s specific wrong claims (`Entity` shell
  path, Aspect class names, `deterministic_seed`) by text search in this pass — those fictional
  names don't correspond to anything real enough to be a ledger subject. `social_narrative.yaml`
  does reference `AptitudeComponent` once (line 578, re: `group_id`), unrelated to the
  ProgressionAspect claim.

## Prior Work
- `TCK-20260330-AOA-COMPOSITION-COMPLETED` (`tickets/done/`, 2026-03-30): documents the actual
  historical AOA implementation — `Entity` refactored to explicit typed aspect fields (`identity`,
  `spatial`, `combat`, `progression`, `mind`, `interaction`, `inventory`), `MindAspect` decomposed
  into `decision`/`perception`/`emotion`/`navigation`/`narrative`. This is exactly the architecture
  `entities.md` currently (and now wrongly) describes — it was real, once.
- `TCK-20260405-DOCS` (`tickets/done/`, 2026-04-05): "Comprehensive Documentation Update (AOA
  Pivot)" — explicitly updated all `docs/` files to reflect the AOA architecture completed five
  days earlier, including "Aspects instead of flat stats." This is almost certainly the ticket that
  wrote `entities.md`'s current content. Its acceptance criteria were satisfied *at the time*; the
  doc simply was never revisited when the architecture was later replaced by the Component system
  (that replacement's own ticket was not identified in this pass — out of scope to trace further,
  per the ticket's own instruction not to re-litigate AOA history).
- `TCK-20260330-CORE-STABILIZATION` (`tickets/done/`, 2026-03-30): listed as AOA-COMPOSITION's
  successor; not read in full (out of scope beyond confirming it exists and chains from the same
  AOA lineage — no additional entities.md-specific detail expected there beyond what the other two
  tickets already establish).
- No `stored_artifacts/` entry concerns `docs/core/entities.md`'s own content accuracy (confirmed
  by the ticket's own prior search, and not contradicted by anything found in this investigation).

## Risks and Open Questions
- **Open, non-blocking**: the Factions & Relations table (`HERO_GUILD`, `GOBLIN_HORDE`,
  `WOLF_PACK`, `UNDEAD`, `ORC_TRIBE`) was not independently re-verified against
  `src/core/enums.py::Faction` in this investigation pass (time-boxed to the ticket's explicitly
  named spot-check fields). The implementer must verify this table against the real `Faction` enum
  values before carrying it forward verbatim — do not assume it is accurate just because it reads
  plausibly.
- **Resolved, not open**: the ticket's Assumptions section flagged uncertainty about whether the
  Genetic Seeds section is accurate. This investigation resolves that: it is **not** accurate as
  written (no `deterministic_seed` field, no found 0.8x-1.2x randomization logic). Per the ticket's
  own scope language ("if investigation finds these sections are also inaccurate, that inaccuracy
  should still be fixed under this ticket's scope"), the rewrite must either drop the specific
  `deterministic_seed`/range claim or replace it with what's actually verifiable: `AptitudeComponent`
  exists with 9 per-stat multiplier fields (default `1.0`), and world-level determinism is real via
  `AuthoritativeState.seed` + `DeterministicRNG`, but the two are not shown to be connected by any
  code path found here.
- **Open, blocking-if-unresolved**: whether the rewritten doc should describe `self_model` and
  `cognition` as full components (they are real, composed fields on `EntityState`) even though
  neither sibling doc (`state.md`'s 8-row table, `entities.md`'s 5-Aspect list) currently mentions
  them at all. Recommendation: include them, since the ticket's acceptance criteria require the doc
  to match `src/core/state.py`'s real composition and explicitly says "no contradiction between the
  two sibling docs" — omitting real components to match `state.md`'s intentionally-abbreviated
  table would itself be an inaccuracy. This is a judgment call for planning/implementation, not
  something this investigation can resolve unilaterally since it slightly exceeds `state.md`'s
  current scope (though it does not contradict it — `state.md`'s table is a summary, not a
  closed/exhaustive list, per its own prose "composed of highly-granular components").
- Not a risk to scope, but worth flagging: `EntityState` also composes `InventoryComponent`
  (`src/core/models/inventory.py`) and `SocialComponent` (`src/core/models/social.py`), which are
  defined outside `state.py` itself despite being core `EntityState` fields. The rewrite should
  cite their real module paths, not imply they live in `state.py`.

## Anti-Drift Hazards
- **Do not invent a new accurate-sounding but unverified architecture name.** The failure mode
  that created this ticket was a doc confidently describing a plausible-sounding but fictional
  design (`Entity` shell, Aspects). The rewrite must cite real file:line locations for every class
  and field claim, the same discipline this investigation applied.
- **Do not carry forward the `deterministic_seed`/0.8x-1.2x aptitude-range claim unverified.** It
  reads as plausible (mirrors real determinism elsewhere in the engine) but no code path was found
  substantiating that specific mechanism. If a future check finds it correct after all, that
  contradicts this investigation and should be re-verified with a specific file:line citation
  before being kept, not restored on the assumption this investigation missed something.
- **Do not describe AptitudeComponent as multiplying attribute-point allocation gains.** Per
  `PROG-069` (P0, divergent), that path is flat/unmodified. Cite `level_up_attributes()`
  (`docs/core/attributes_and_classes.md` §3) instead if describing how aptitudes affect stat
  growth — that mechanism is the one still verified accurate.
- **Do not silently drop `self_model` and `cognition` without a decision** (see Risks above) —
  omitting real, composed `EntityState` fields would just be a different flavor of the same
  inaccuracy this ticket exists to fix.
- **Do not touch `docs/core/state.md` or `docs/core/attributes_and_classes.md`** even to "improve"
  them while cross-referencing — both are explicitly Out of Scope and already accurate; any edit to
  either is scope creep.
- **Do not touch any `src/` file.** This is docs-only; the real Component architecture is correct
  as implemented. There is nothing to fix in code.
- **Frontmatter discipline**: the ticket requires keeping `entities.md`'s existing frontmatter
  shape (`status: authoritative`, `layer: core`, `authority: P0`, `audience: developer`) and only
  updating `last_verified` — do not change `status`/`layer`/`authority`/`audience`, and do not
  add a `content_type` override field (none is present today; `detect_content_type()` in
  `tools/validate_frontmatter.py` will infer `doc` from the `docs/` path, which is correct).
