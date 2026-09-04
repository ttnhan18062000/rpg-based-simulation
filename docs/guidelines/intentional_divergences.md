---
status: active
layer: guidelines
authority: P1
audience: developer
---

# `src` Divergence Log

This document is the canonical record of intentional behavior shifts in `src` compared to original `src`. Every divergence listed here must have a rationale and be classified according to the `src_principle.md` standards.

## 1. Divergence Summary Table

| Subsystem | Feature | Rationale Class | Status |
| :--- | :--- | :--- | :--- |
| **RPG-CORE** | Melee Adjacency | **Hardened** | RATIFIED |
| **RPG-CORE** | Ranged LoS | **Enforced** | RATIFIED |
| **RPG-CORE** | AoE Radius | **Unified** | RATIFIED |
| **RPG-CORE** | Project Margin | **Stabilized** | RATIFIED |
| **RPG-CORE** | Lead/Concern Cap | **Bounded** | RATIFIED |
| **RPG-CORE** | Lead Suppression | **Stabilized** | RATIFIED |
| **RPG-CORE** | Attention Limits | **Bounded** | RATIFIED |
| **RPG-CORE** | Action Style | **Hardened** | RATIFIED |
| **RPG-CORE** | Interruption-Bypass Generalization | **Enforced** | RATIFIED |
| **World Assembly** | Service Assembly | **Stabilized** | DEFERRED |
| **World / Environment** | Hazard-Kind Faction Endurance | **Bug Fix** | RATIFIED |
| **World / Authoring** | Worldtemplate.v1 Schema Removal | **Unified** | RATIFIED |
| **Engine / Observability** | Kernel Tick-Alignment Fix | **Bug Fix** | RATIFIED |
| **Worldbuilding / Information** | Single-Fire Compile-Time-Seeded Response | **Bounded** | RATIFIED |
| **Engine / Cognition-Information** | `information_belief` Pipeline-Wiring Merge Fix | **Bug Fix** | RATIFIED |
| **Engine / Cognition** | `self_model_bundle_set` Durable Materialization (`SelfModelPatch`) | **Bug Fix** | RATIFIED |
| **World / Ecology** | Resource Ecology Kind-Emission Catalog Alignment | **Bug Fix** | RATIFIED |
| **World / Environment** | Non-Native Faction Hazard Exposure (`town_council`/`bandit_road`) | **Intentional Gameplay Change** | RATIFIED |
| **Engine / Observability** | DecisionTraceWriter Async Drain — Crash-Loss & Overflow-Drop Windows | **Bounded** | RATIFIED |
| **Engine / Combat-Progression** | Opportunity-Attack Kill Reward Orphaned on the Victim | **Bug Fix** | RATIFIED |
| **Engine / Combat-Progression** | Hero's Journey Rebirth Orphaned in the Real Dominant Kill Path | **Bug Fix** | RATIFIED |
| **Engine / Cognition-Strategy** | Adventure-Route Defer-Reason Observability Gap | **Bounded** | RATIFIED |
| **Strategic Cognition / Regional Danger** | Regional-Danger Stabilization No Longer Unconditionally Wins the Project Slot | **Enforced** | RATIFIED |
| **Knowledge Gateway MCP / Packet Cache** | Level 2 Packet-Cache Freshness/Verification Column Co-location | **Bounded** | RATIFIED |
| **Engine / Progression** | ALLOCATE_AP Action-Router Branch Kept Dormant | **Bounded** | ACTIVE |
| **Engine / Combat** | Wounds Permanent; `heal_wound()`/`get_diagnosis_quality()` Removed | **Bug Fix** | ACTIVE |
| **Social/Clan** | Clan Succession-on-Death | **Intentional Gameplay Change** | RATIFIED |
| **Engine / Progression** | Post-Spawn `class_id` Mutation via `class_id_set` (DEV-006) | **Intentional Gameplay Change** | ACTIVE |
| **Economy / Social** | Teaching Gated on Trust, Not Gold: TRAIN_COST Removed Entirely (DEV-007) | **Intentional Gameplay Change** | ACTIVE |

---

## 2. Detailed Records

### 2.1 Strict Channeling Enforcement
- **Subsystem**: Grid / Interaction
- **Old Behavior**: Legacy engine allowed "instant-harvest" bugs under specific tick conditions or race timings where the channeled duration was not strictly enforced before update application.
- **New Behavior**: `InteractionSystem.enforce` strictly verifies that `progress >= duration` before adding items to inventory. Aborts occur if the entity moves or interacts with another target.
- **Rationale**: **Bug Fix**. Prevents exploitation of timing bugs and ensures the "Channeling Law" is absolute.
- **Verification**: `tests/parity/test_resource_interaction_parity.py`

### 2.2 Lowercase Registry Keys
- **Subsystem**: Core / State
- **Old Behavior**: Item and resource registry keys used inconsistent casing (e.g., `Iron_Ore`, `iron_ore`, `IRON_ORE`).
- **New Behavior**: All keys are normalized to lowercase during registry loading and state serialization.
- **Rationale**: **Lifecycle Truth Fix**. Stabilizes state hashing and prevents "ghost" items caused by case-sensitivity drit.
- **Verification**: `tests/unit/test_registry_identity_integrity.py`

### 2.3 Immediate Interaction Completion (Tick 0)
- **Subsystem**: Interaction / Inventory
- **Old Behavior**: Interaction completion and item addition often lagged by 1 tick (reported in Tick N+1).
- **New Behavior**: Completion is resolved in the same tick (`Tick 0`) the threshold is reached. Inventory updates are immediately visible to the AI in the same resolution phase.
- **Rationale**: **Contract Hardening**. Synchronizes physical completion with logical state change, simplifying AI reasoning.
- **Verification**: `docs/engine/matrices/progression_surface_matrix.md`

### 2.4 Simplified Recipe Costs
- **Subsystem**: Town Loop / Blacksmith
- **Old Behavior**: `steel_sword` required 2 `iron_ore` and specific auxiliary materials.
- **New Behavior**: `steel_sword` cost simplified to 1 `iron_ore`.
- **Rationale**: **Intentional Gameplay Change**. Simplified specifically to support single-loop loop-integrity proof scenarios.
- **Verification**: `docs/archive/engine_history/resource_exit_support_boundary.md`
- **Note**: This divergence is restricted to single-loop baseline scenarios and may be removed later.

### 2.5 Proactive Strategic Redirection
- **Subsystem**: AI / Strategic
- **Old Behavior**: AI projects reacted to inventory changes in the next tick.
- **New Behavior**: `StrategicRedirectionSystem` detects inventory resolution and pivots project state within the same resolution phase.
- **Rationale**: **Contract Hardening**. Improves AI effectiveness and ensures the simulation doesn't "waste" a tick on now-obsolete goals.
- **Verification**: `docs/archive/engine_history/resource_intelligence_support.md`

### 2.6 Priority-Based Tactical Targeting
- **Subsystem**: Tactical AI
- **Old Behavior**: Nearest enemy was always selected.
- **New Behavior**: Deterministic priority chain: `Group Focus-Fire Bias` > `Target Stickiness/Hysteresis` > `Capability-Driven Priority` > `Lowest HP` > `Pressure-Scaled Distance` > `Lowest Entity ID`. As of `TCK-20260831-CAPABILITY-DRIVEN-TARGETING` (Logic ID COMB-316), the entity's own subjective `CapabilityEstimateService.estimate(...)` result against a hostile's specific `kind` is folded into the sort — a hostile the entity believes it is more likely to beat is prioritized higher, ahead of raw HP/distance but behind group cohesion and hysteresis. This is an ad-hoc, call-site-local, read-only call: `entity.self_model.capabilities.estimates` remains empty in production either way (`SelfModelUpdatePhase.apply()` still never passes `capability_context=`).
- **Rationale**: **Contract Hardening** (original HP/distance/ID chain) + **Intentional Gameplay Change** (the capability-driven addition — a deliberate new prioritization heuristic, not a bug fix or further hardening of an existing rule). Prevents target oscillation, improves AI effectiveness in focused firing, and makes entities press fights they believe they can win.
- **Verification**: `tests/unit/combat/test_capability_driven_targeting.py`

### 2.7 20% Retreat Threshold
- **Subsystem**: Tactical AI
- **Old Behavior**: Entities retreated at 25% HP.
- **New Behavior**: Entities retreat at 20% HP.
- **Rationale**: **Intentional Gameplay Change**. Aligns with the engine's more aggressive hero-bias scenarios.
- **Verification**: `tests/parity/test_tactical_parity.py`

### 2.8 Omitted Combat Variance/Evasion
- **Subsystem**: Combat Resolution
- **Old Behavior**: Combat included evasion checks and ~10% damage variance.
- **New Behavior**: Combat resolution is currently 100% deterministic (no variance, no evasion).
- **Rationale**: **Substrate Clarity**. Ensuring the base damage resolution is bit-identical and stable before layering stochastic noise.
- **Verification**: `tests/parity/test_combat_parity.py`

### 2.9 Legality Enforcement (LoS & Engagement)
- **Subsystem**: Combat / Legality
- **Old Behavior**: Ranged attacks often clipped corners; melee attacks could be initiated during "illegal" movement states (stale engagement).
- **New Behavior**: `LegalityService` enforces strict Line-of-Sight and engagement-registry truth. Moves that would violate engagement-lock are rejected.
- **Rationale**: **Contract Hardening**. Ensures combat is spatially honest and prevents "ghost-swing" exploits.
- **Verification**: `tests/test_legality.py`

### 2.10 Cognitive Boundedness (Attention & Detours)
- **Subsystem**: AI / Strategic
- **Old Behavior**: AI detours were recursively deep; attention was unbounded, leading to "omniscience" bugs.
- **New Behavior**: Strategic cognition is profile-capped. Attention is limited to `N` nearest neighbors; detours are capped at depth `3`.
- **Rationale**: **Contract Hardening**. Prevents performance spikes and ensures AI behavior is predictable and bounded.
- **Verification**: `test_resource_intelligence_contract.py`

### 2.11 API/CLI Normalization
- **Subsystem**: System Compatibility
- **Old Behavior**: CLI flags and API responses were loosely structured and often returned internal object references.
- **New Behavior**: Explicitly typed schemas for all CLI outputs and REST responses. Internal IDs are never exposed directly.
- **Rationale**: **Protocol Hardening**. Decouples internal engine state from external interface stability.
- **Verification**: `test_rest_parity.py`, `test_entry_parity.py`

### 2.12 Melee Adjacency (LEG-RPG-012)
- **Subsystem**: RPG-CORE
- **Rationale**: **Hardened**. Requires explicit spatial hash adjacency (Manhattan == 1) without legacy float "fudge factors".
- **Verification**: `tests/parity/test_interaction_parity.py`

### 2.13 Ranged LoS (LEG-RPG-013)
- **Subsystem**: RPG-CORE
- **Rationale**: **Enforced**. Strict Bresenham-based LoS check prevents "shooting through corners".
- **Verification**: `tests/parity/test_interaction_parity.py`

### 2.14 AoE Radius (LEG-RPG-014)
- **Subsystem**: RPG-CORE
- **Rationale**: **Unified**. Grid-aligned radius calculation prevents partial-tile damage bugs.
- **Verification**: `tests/parity/test_interaction_parity.py`

### 2.15 Strategic Stability (LEG-RPG-036, 109)
- **Subsystem**: AI / Strategic
- **Rationale**: **Stabilized**. Uses explicit 20% "loyalty margin" for project switching to prevent objective oscillation.
- **Verification**: `test_resource_intelligence_contract.py`

### 2.16 O(1) Memory Boundedness (LEG-RPG-039, 040, 110, 149)
- **Subsystem**: AI / Strategic
- **Rationale**: **Bounded**. Cognitive intake, leads, concerns, and attention are profile-capped to preserve performance.
- **Verification**: `test_resource_intelligence_contract.py`

### 2.17 Lead Suppression (LEG-RPG-042)
- **Subsystem**: AI / Strategic
- **Rationale**: **Stabilized**. Proactively suppresses leads rejected 3 times to prevent loops.
- **Verification**: `test_resource_intelligence_contract.py`

### 2.19 Service Assembly Gap (World Assembly)
- **Subsystem**: World Assembly
- **Old Behavior**: Not applicable — service assembly is a new feature.
- **New Behavior**: `WorldModuleAssemblyResolver.resolve_module_contribution()` validates and computes `service_refs: Dict[str, int]` for `worldmodule.v2` modules, but `assemble()` does not consume it. `WorldSpec` has no `services` field. All current real modules are `worldmodule.v1` so `service_refs` is always empty at runtime.
- **Rationale**: **Stabilized**. Service assembly is deferred until `ServiceNodeSpec` and `WorldSpec.services` are defined. Adding a half-wired loop before the output type exists would create dead code.
- **Verification**: `tests/unit/worldassembly/test_resolver.py::test_v2_service_refs_assembly_is_documented_gap`
- **Unblock condition**: Add `ServiceNodeSpec` to `worldbuilding/schema.py`, add `services: List[ServiceNodeSpec]` to `WorldSpec`, then add the service merge loop in `assemble()` parallel to the building loop. Update `SUB-367` in `substrate.yaml` to `status: verified` and remove this entry.

### 2.18 Action Style (LEG-RPG-155)
- **Subsystem**: AI / Tactical
- **Rationale**: **Hardened**. Maps `ActionStyle` enums to hard logic gates instead of fuzzy floats.
- **Verification**: `tests/parity/test_movement_parity.py`

### 2.20 Hazard-Kind Faction Endurance (TCK-20260701-HAZARD-NATIVE-IMMUNITY)
- **Subsystem**: World / Environment
- **Old Behavior**: `EnvironmentService.calculate_hazard_drain(region, entity)` accepted an
  `entity` parameter but never read it — every entity standing in a region took identical
  passive HP drain based solely on `region.hazard_level`/`calamity_intensity`, regardless of
  whether the entity was native to that habitat. This caused monsters spawned in their own
  high-hazard home region (e.g. `wolf_den`, `hazard_level: 2.0`) to die from their own
  region's hazard within a handful of ticks.
- **New Behavior**: Regions carry a `hazard_kind` tag (`RegionState.hazard_kind`, default
  `"PHYSICAL"`); factions declare which hazard kinds their members endure via
  `FactionDefinition.hazard_immunities` (default `[]`). `calculate_hazard_drain` resolves the
  entity's catalog faction id (`get_faction_id_str`) and, if that faction's
  `hazard_immunities` includes the region's `hazard_kind`
  (`FactionSemanticsService.get_hazard_immunities`), returns zero drain; otherwise the drain
  formula is unchanged. Endurance is declared per faction per hazard kind, never inferred
  from hostility-to-hero or from a legacy `Faction` enum bucket — a hazard kind nobody has
  declared endurance for (e.g. a synthetic `"TOXIC_GAS"`) drains every faction present
  equally, including two mutually hostile ones fighting in it together.
- **Rationale**: **Bug Fix**. The `entity` parameter's presence in the original signature,
  unused, is read as evidence a native-exemption was always intended but never wired up. An
  earlier implementation pass gated the exemption on
  `entity.identity.faction == Faction.MONSTER_HORDE and region.kind == "WILDERNESS"`; that
  design was rejected mid-review because it re-derived "endurance" from "is hostile to hero"
  (a coarse legacy-faction-bucket coupling), which could never model a hazard that hurts two
  mutually hostile factions equally. The typed-hazard-kind/typed-faction-endurance design
  fixes that coupling directly.
- **Verification**: `tests/unit/world/test_regional_consequences.py` (native/hostile/
  zero-hazard/shared-hazard/synthetic-fiend/default-no-regression cases),
  `tests/unit/content_semantics/test_semantics.py::test_get_hazard_immunities`,
  `tests/unit/content/test_catalog.py::test_faction_definition_hazard_immunities_field`,
  `tests/unit/content/test_catalog.py::test_faction_catalog_loads_with_hazard_immunities_authored`
- **Note**: `data/worlds/sandbox_world/`'s compiled artifacts have been recompiled by
  `TCK-20260701-SANDBOX-MONSTER-BALANCE` (done) — the exemption is now live in the committed
  artifacts (state hash `836b45e8913b46862240c6ba80f177f6` at seed 42), confirmed by a 200-tick
  empirical re-run showing 0/5 `wild_beast_pack` monster deaths and zero `hazard_drain_applied`
  events against them, both seed 42 and seed 137.

### 2.21 Worldtemplate.v1 Schema Removal (TCK-20260701-WORLDTEMPLATE-REMOVE)
- **Subsystem**: World / Authoring
- **Old Behavior**: `worldtemplate.v1` existed as a second world-authoring schema alongside
  `worldcomposition.v1`, using population "recipes" procedurally expanded by
  `WorldTemplateExpander`. Its compile path never resolved entity stats from the catalog —
  `WorldCompiler.compile()` was always called with `context=None` for this schema, so every
  entity (monster or citizen) received identical flat stat defaults.
- **New Behavior**: The schema is removed entirely — `WorldTemplateSpec`/
  `WorldTemplateExpander` and their CLI branches (`src/worldbuilding/cli.py`,
  `src/worldbuilding/repository.py`, `src/cli/entry.py`) are deleted. `create-template` is
  repointed to scaffold a minimal `worldcomposition.v1` file instead of a `worldtemplate.v1`
  one, keeping the documented bootstrap workflow (`docs/guides/simulation.md`) intact.
  `worldspec.v1`/`WorldSpec` (the compiler's internal canonical spec type, distinct from the
  removed authoring schema) and `worldcomposition.v1`'s resolution logic
  (`WorldAssemblyResolver`, the shared `*RecipeSpec` classes in `recipe.py`) are unchanged.
- **Rationale**: **Unified**. `sandbox_world` was the sole remaining `worldtemplate.v1` world
  (migrated by `TCK-20260701-SANDBOX-WORLDCOMP-MIGRATE`); every other world already used
  `worldcomposition.v1`, which provides equal-or-better capability via module reuse and
  resolves real catalog-driven stats. Patching the stat-resolution gap in a pipeline with a
  single remaining consumer was less sound than retiring it.
- **Verification**: `tests/cli/test_world_cli.py`, `tests/unit/worldbuilding/
  test_world_repository.py` (added regression coverage); `tests/unit/worldbuilding/
  test_world_recipes.py` deleted (tested only the removed expansion path).

### 2.22 Kernel Tick-Alignment Fix (TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER)
- **Subsystem**: Engine / Observability
- **Old Behavior**: `Kernel._phase_advancement()` (`src/engine/kernel.py:702-736`) reassigns
  `self._state` to the post-advance tick (via `ApplyPath.apply_generation(...,
  next_tick=self._state.tick + 1, ...)`) before calling `_phase_observability(prior_state,
  update)`. Three Resolution-phase-stamped properties — `last_assimilated_tick`
  (`src/domains/information/phase.py:77`), `last_calamity_tick_set`
  (`src/world/calamity.py:56`), and `RuntimeStatus.last_transition_tick`
  (`src/engine/runtime_status.py:79`, via `reset_dwell()` called from `_phase_init()`,
  `kernel.py:535-541`) — are all stamped using the pre-advance tick. `EventExtractor.extract()`'s
  and `_phase_observability`'s `== tick` checks (`event_extractor.py:286`,
  `event_extractor.py:899`, `kernel.py:836`) compared these against the post-advance `tick`
  local instead, so the equality check could never match through the real
  `Kernel.tick_once()` loop: `belief_assimilated`/`belief_updated`, `calamity_spawned`, and
  `GovernorModeChanged` had never fired through any real run in the codebase's history,
  regardless of scenario content.
- **New Behavior**: The 3 comparison sites now compare against `prior_state.tick` (already an
  in-scope parameter at each call site) instead of the shared post-advance `tick` variable. The
  tick label used for every emitted `SimulationEvent.tick` field (including
  `InvariantViolation`'s and `GovernorModeChanged`'s own `tick`/`payload["tick"]`) is
  unchanged — only the internal gating comparison for these 3 specific stamped properties was
  corrected.
- **Rationale**: **Bug Fix**. A Resolution-phase-stamped value must be compared against the
  state snapshot it was stamped against (the pre-advance state), not a later-advanced one, or
  the equality check can never match. This is not a design tradeoff; it is a straightforward
  off-by-one-tick comparison defect discovered while empirically verifying
  `TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER`'s Step 6 against the real Kernel loop.
- **Verification**: `tests/integration/observability/test_kernel_event_recording.py`
  (`test_belief_assimilated_fires_through_real_tick_once_loop`,
  `test_calamity_spawned_fires_through_real_tick_once_loop`,
  `test_governor_mode_changed_fires_through_real_tick_once_loop` — all passing); zero
  regressions in `tests/unit/observability/test_event_extractor_cognition.py`,
  `tests/unit/observability/test_event_extractor_world.py` (same-state-twice pattern, inert
  under this fix).
- **Note**: `belief_assimilated`/`belief_updated` confirmed firing (calibration_hits == 1 per
  run) across all 7 `urban_political_*` calibration runs; `GovernorModeChanged` confirmed
  firing naturally (63-73 occurrences) in existing `dungeon_crawl_seed{42,123,456}_2000t` /
  `sandbox_world_seed42_2000t` baselines (infrastructure telemetry, not SimQ-scored).
  `calamity_spawned`'s fix mechanism is verified correct by its dedicated unit test, but a
  one-off diagnostic run (`dungeon_crawl_seed42_5200t`, not added to `grade_anchors.json`) did
  not naturally produce the event — `CalamityService` additionally gates the spawn behind
  `calamity_intensity > 0.3`, only raised by a hero-kind entity dying in a `hazard_level > 0.5`
  region, which did not occur in that run. This is a separate, pre-existing content/mechanics
  precondition, not fixed by this entry. See `docs/parity_ledger/infrastructure.yaml::INFRA-258`.

### 2.23 Single-Fire Compile-Time-Seeded Response (TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER)
- **Subsystem**: Worldbuilding / Information
- **Old Behavior**: N/A — `pending_information_responses` did not exist as a compile-time-seedable
  field before this ticket.
- **New Behavior**: A `PendingInformationResponseSpec` entry declared in world composition YAML
  (e.g. `data/worlds/urban_political/world.yaml`'s `pop_0` seed) is resolved by
  `WorldCompiler.compile()` into `AuthoritativeState.pending_information_responses` at compile
  time (tick 0), and `InformationBeliefPhase.apply()`'s Branch A assimilates it exactly **once**.
  `ApplyPath.apply_generation()` (`src/engine/apply.py:179-416`, esp. lines 356-408) does not carry
  `pending_information_responses` (or `information_source_profiles`) forward from `prior_state`
  when rebuilding `AuthoritativeState` on each subsequent tick advancement
  (`src/engine/kernel.py:702-722`, `Kernel._phase_advancement()`), so the seed becomes permanently
  empty from tick 1 onward.
- **Rationale**: **Bounded**. This is a property of the compile-vs-apply state reconstruction
  model, not something `InformationBeliefPhase`/Branch A manages itself, and it is not a defect
  needing mitigation — it is the correct, deterministic, one-shot-inbox outcome for a compile-time
  seed: exactly one `belief_assimilated` event per run, not an unbounded per-tick recurrence. The
  same single-fire trait applies to `information_source_profiles` (shipped by the sibling ticket
  `TCK-20260702-SIMQ-UPLIFT2-INFORMATION`), noted here for traceability only — no action item.
- **Verification**: `tests/integration/scenarios/test_phase5_information_belief_scenarios.py::test_pending_information_response_fires_exactly_once_not_carried_forward`
  (drives 5 tick advancements, confirms exactly 1 `belief_assimilated` total and
  `pending_information_responses == []` from the first `apply_generation()` onward).
- **Note**: Confirmed via real calibration runs (not just the direct-pipeline test) —
  `calibration_hits == 1` for `belief_assimilated`/`belief_updated` in every `urban_political_*`
  scenario regardless of scenario length (200/500/1000 ticks), consistent with single-fire-at-tick-0
  behavior. See `docs/parity_ledger/infrastructure.yaml::INFRA-257`.

### 2.24 `information_belief` Pipeline-Wiring Merge Fix (TCK-20260703-SIMQ-UPLIFT3-BRANCH-B)
- **Subsystem**: Engine / Cognition-Information
- **Old Behavior**: `src/engine/pipeline.py:152`'s `information_belief` call site called
  `InformationBeliefPhase.apply(state, source_profiles, pending_resps)` directly and used its
  return value as the tick's entire `StateUpdate`, discarding the prior `update` instead of merging
  with it — the only one of this file's 4 `information_belief`-adjacent phase call sites not
  following the established `u.merge(...)` pattern (`faction_awareness`, `diplomatic_transitions`,
  and `military_conflict` all wrap their phase's output in `u.merge(...)`). With both
  `ENABLE_SELF_MODEL_COGNITION` and `ENABLE_BELIEF_ASSIMILATION` ON, this silently wiped
  `self_model`'s same-tick `entity_updates` contribution entirely — empirically reproduced this
  session by temporarily reverting the fix and observing `refined.entity_updates` collapse to `{}`.
  This combination had never been exercised by any shipped calibration profile, so the defect was
  never observed in a real run.
- **New Behavior**: The call site now wraps the phase's output in `u.merge(...)`, matching all 3
  siblings exactly: `lambda u: u.merge(InformationBeliefPhase.apply(state, source_profiles,
  pending_resps))`. No signature change to `InformationBeliefPhase.apply()` or
  `src/domains/information/phase.py`.
- **Rationale**: **Bug Fix**. This is a straightforward pipeline-wiring defect — a call site not
  following its own file's established merge pattern for no principled reason — not a design
  tradeoff, following the same class as `§2.22`'s kernel tick-alignment fix.
- **Verification**: `tests/integration/domains/test_fused_loop.py::test_information_belief_merge_preserves_self_model_writes_both_flags_on`
  (both flags ON, self_model's write and an unrelated entity's update both survive the merge);
  `tests/integration/domains/test_fused_loop.py::test_branch_b_on_compiled_urban_political_state_self_model_and_branch_a_coexist`
  (real compiled `urban_political` state, Branch A and self_model's write coexist correctly);
  `tests/integration/domains/test_fused_loop.py::test_belief_assimilation_persists_facts` (regression
  guard — `ENABLE_BELIEF_ASSIMILATION` alone, `ENABLE_SELF_MODEL_COGNITION` OFF — passes unmodified,
  confirming the fix is a no-op whenever `self_model`'s phase-skip branch contributes nothing to
  merge).
- **Note**: This fix is required, alongside `INFRA-259`'s `events=[]` fix and `§2.25`'s
  `SelfModelPatch` materialization fix, for `InformationBeliefPhase`'s Branch B to be reachable
  end-to-end. None of the three individually turns Branch B on in any shipped calibration
  profile — `ENABLE_SELF_MODEL_COGNITION` stays `OFF` everywhere. See
  `docs/parity_ledger/infrastructure.yaml::INFRA-260`.

### 2.25 `self_model_bundle_set` Durable Materialization — `SelfModelPatch` (TCK-20260703-SIMQ-UPLIFT3-BRANCH-B)
- **Subsystem**: Engine / Cognition
- **Old Behavior**: `EntityUpdate.self_model_bundle_set` was never materialized into durable
  `EntityState.self_model` by the authoritative apply path. `src/engine/patches.py::extract_patches()`
  had no patch class reading `update.self_model_bundle_set`, and `src/engine/apply.py`'s
  `_fast_replace_entity()` read a `changes["self_model"]` key that nothing ever populated — every
  entity's `self_model` was silently discarded on every apply pass, for every entity, every world,
  every tick, since `self_model_bundle_set` was introduced. This affected Branch A's already-shipped
  writes identically; the existing `test_belief_assimilation_persists_facts` only ever asserted
  `self_model.knowledge is not None`, never that its content matched what was written, which is why
  this was never caught.
- **New Behavior**: A new `SelfModelPatch(ComponentPatch)` (`src/engine/patches.py`, structural
  mirror of `KindPatch` — whole-object replace-if-present) is wired into `extract_patches()`. When
  `update.self_model_bundle_set` is non-`None`, it sets `changes["self_model"]`, which
  `_fast_replace_entity()` already correctly read but was never fed. `entity.self_model` now
  genuinely persists across tick boundaries and accumulates real assimilation history instead of
  always starting from `SelfModelBundle.empty()`.
- **Rationale**: **Bug Fix**. This is a missing apply-path wiring for an existing typed update
  field (`self_model_bundle_set`), completing Pattern 2 (Decision/Mutation Separation via Typed
  Update Records, `docs/guidelines/design_patterns.md`) for this field — not a new pattern or a
  design tradeoff. A blast-radius sweep of all 15 identified consumers of `entity.self_model` found
  8 intended positive fix effects (self-model assimilation becomes genuinely cumulative), 2 orphaned
  consumers with zero live callers, 3 false positives/already-decoupled telemetry paths, 1 pure
  passthrough, and 1 pre-existing, unrelated docstring/code divergence (corrected as
  `docs/parity_ledger/substrate.yaml::SUB-374` — `self_model` was already, and remains, included in
  the authoritative canonical hash; a stale docstring claimed otherwise). The only consumers with any
  live conditional behavior change (`AdventureRouteGenerator`/`scoring.py`) require both
  `ENABLE_SELF_MODEL_COGNITION` and `ENABLE_ADVENTURE_ROUTING` ON simultaneously — no shipped
  `config/`/`data/worlds/` runtime profile combines these flags today.
- **Verification**: `tests/unit/domains/optimization/test_component_patches.py` (6 new `SelfModelPatch`
  tests — noop detection, merge, apply-sets-changes-key); `tests/integration/optimization/test_component_patch_apply_parity.py::test_self_model_patch_apply_parity_durable_materialization`
  (direct end-to-end regression guard through `ApplyPath.apply_generation()`, full bundle equality);
  `tests/unit/core/test_entity_integrity.py::test_self_model_participates_in_canonical_hash` and
  `::test_self_model_fix_preserves_existing_baseline_hashes_when_flag_off`;
  `tests/integration/domains/test_fused_loop.py::test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization`
  (proves the full seed → assimilate → materialize → route sequence across a real tick boundary).
- **Note**: Hash stability empirically confirmed — compiled `urban_political`'s real resolved world
  (seed 42, shipped default flags), advanced 50 ticks, and computed the canonical hash both with
  `SelfModelPatch` present and with it temporarily reverted: bit-identical
  (`15081e225da292dd91ae8179922729ec0103f1b9a09cc64be8e14f49c8549591`), confirming 0 impact on
  existing calibration baselines since `self_model` stays constant `SelfModelBundle.empty()` while
  `ENABLE_SELF_MODEL_COGNITION` is OFF. A `calibrate_simq.py` spot-check (`urban_political`, seed 42,
  200t) confirmed `INFORMATION`/`COGNITION` pillar grades unchanged at `B`. See
  `docs/parity_ledger/substrate.yaml::SUB-374`.

### 2.26 Resource Ecology Kind-Emission Catalog Alignment (TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP)
- **Subsystem**: World / Ecology
- **Old Behavior**: `ResourceEcologyService.process_ecology` (`src/world/ecology.py:124-125,138`)
  emitted hardcoded uppercase literals (`"WOOD"`/`"STONE"`/`"IRON"`) as a seeded `ResourceNodeState`'s
  `kind`, none of which matched any `ResourceRegistry` entry (catalog ids are lowercase —
  `wood_node`/`iron_vein` — and no `"stone"`-type resource existed in the catalog at all).
  `yields_item` was hand-computed via `kind.lower() + "_ore"` / `"wood_log"` string suffixing,
  coupled to the same broken literals. This caused a `KeyError: Resource not found in
  ResourceRegistry: STONE` crash in `ResourceOpportunityProvider.get_opportunities`
  (`src/world/providers/resources.py:60`, the one call site that read `ResourceRegistry.get(node.kind)`
  unguarded), reachable only when `ENABLE_ADVENTURE_ROUTING=ON`. The defect was general (all 3
  literals were wrong), not `STONE`-specific — `STONE` merely surfaced first because it is the
  fallback branch (fires for every region whose `kind` is neither `FOREST` nor `MOUNTAIN`).
- **New Behavior**: Emission now selects real, `ResourceRegistry`-registered catalog ids —
  `wood_node` (`FOREST`), `iron_vein` (`MOUNTAIN`), `stone_outcrop` (fallback/else branch) — and
  `yields_item` is derived from `ResourceRegistry.get(kind).yield_item` instead of hand-computed
  suffixing, so it cannot drift out of sync with the catalog again. `stone_outcrop` (+ a paired
  `stone` material item) is a newly-authored catalog resource
  (`data/content/world/resources.yaml`, `data/content/world/items.yaml`) preserving the original
  three-terrain-kind seeding design intent, not a design change. The one remaining unguarded
  `ResourceRegistry.get()` call site (`src/world/providers/resources.py:60`) now guards with
  `.contains()` first, matching `src/town/guild.py:67-69` and
  `src/engine/intent/action_intent.py:73-74`'s existing pattern.
- **Rationale**: **Bug Fix**. `src/core/registries.py:195-198` documents catalog-backed registries
  as authoritative for all active development; these literals predate that transition
  (introduced 2026-05-18, per `git blame`) and were never migrated. This is staleness/oversight, not
  a deliberate design decision — no evidence a `STONE` resource was ever intentionally scoped and
  then dropped.
- **Verification**: `tests/unit/world/test_resource_ecology.py` (new Group F tests —
  `test_seeded_node_kind_registered_for_forest_region`,
  `test_seeded_node_kind_registered_for_mountain_region`,
  `test_seeded_node_kind_registered_for_other_region`,
  `test_process_ecology_never_emits_unregistered_kind`); new
  `tests/unit/world/providers/test_resource_opportunity_provider.py` (provider-level
  `.contains()` guard test plus a `stone_outcrop` opportunity-surfacing test). All 25 pre-existing
  `test_resource_ecology.py` tests plus `tests/unit/core/test_engine_integrity.py` re-run unmodified
  as a regression gate (`test_engine_integrity.py`'s hardcoded `kind="WOOD"` test fixture literal
  updated to `"wood_node"`/`yields_item="wood"` for consistency — a fixture literal, not new
  behavior).
- **Note**: Re-running `simq_routing_test`'s calibration (`ENABLE_ADVENTURE_ROUTING=ON`,
  seed{42,123,456}, 500t) — previously blocked entirely by this crash — now completes for all 3
  seeds. All 3 regions in this world (`hometown`, `goblin_camp`, `old_mine`) compile to
  `kind` values other than `FOREST`/`MOUNTAIN`, so every pre-fix ecology-seeded node in this world
  was `"STONE"`, making the crash 100% deterministic once ecology's tick-200 seed check fired. This
  is therefore the first calibration of this world to run to completion since the 2026-07-01
  hazard-kind recompile; substantial grade drift across all 10 pillars for all 3 seeds was found and
  `grade_anchors.json` updated in place, with one gate violation (`seed456` AGENCY=F, traced to a
  pre-existing, unrelated tick-176 entity stasis dynamic) flagged for follow-up. Since the anchor
  fixture schema has no representable slot for `F` (`GRADE_ORDER = [D,C,B,A,S]`), `seed456`'s AGENCY
  anchor is recorded as `D` (the schema's floor), not the true observed grade — this keeps
  `test_grade_within_anchor_band` correctly failing on any future re-run that still grades `F`
  rather than silently absorbing it. See `docs/simulation_quality/eval_matrix_results.md`'s dated
  NOTE and AC6 section for full detail.

### 2.27 Hometown Resource-Opportunity Gating Fix (TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP)
- **Subsystem**: World / Resource Opportunities
- **Old Behavior**: wood_node/herb_patch's catalog source_region_tags (data/content/world/
  resources.yaml) did not include "hometown", even though frontier_village_core.yaml already placed
  both kinds' nodes there (TCK-20260627-P0B-URBAN-RESOURCE-NODES). ResourceOpportunityProvider gates
  purely on the kind-level catalog allowlist, never on a node's own placement region (ResourceNodeState
  has no region field), so hometown-standing entities never received gather_resource opportunities
  regardless of role or seed.
- **New Behavior**: wood_node's source_region_tags additively gains "hometown" (now
  ["near_forest", "hometown"]); herb_patch's additively gains "hometown" (now ["near_forest",
  "moon_cave", "hometown"]), via the same metadata.source_region_tags override mechanism used for
  stone_outcrop. Purely additive — no other world/region's existing tag coverage changes.
- **Rationale**: **Bug Fix**. The original P0B ticket's evident intent (placing nodes in hometown) was
  never fully realized for opportunity-matching purposes; this closes that gap.
- **Verification**: tests/unit/core/test_registry_bridge.py, tests/unit/strategic/test_opportunities.py
- **Status**: ACTIVE

### 2.28 Corpus Resource-Region Tag-Gap Fix (TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT)
- **Subsystem**: World / Resource Opportunities
- **Old Behavior**: wood_node, iron_vein, herb_patch, healing_flower_patch, and spirit_wisp each had a
  resource kind physically placed in a region by its composing world module, but the catalog's
  source_region_tags allowlist (data/content/world/resources.yaml) omitted that region id, so
  ResourceOpportunityProvider silently returned zero gather_resource opportunities for entities standing
  there. Same root mechanism as §2.27 (hometown), recurring at corpus scale across 5 additional regions.
- **New Behavior**: All five changes are purely additive extensions of `metadata.source_region_tags`
  (or new blocks where none existed):
  - `wood_node`: `["near_forest", "hometown"]` → `["near_forest", "hometown", "orc_stronghold",
    "swamp_border_territory"]`
  - `iron_vein`: `["old_mine", "mountain_pass_zone"]` → `["old_mine", "mountain_pass_zone",
    "orc_stronghold", "trading_hometown"]`
  - `herb_patch`: `["near_forest", "moon_cave", "hometown"]` → `["near_forest", "moon_cave", "hometown",
    "swamp_border_territory"]`
  - `healing_flower_patch`: no `metadata` block (fell through to the `node_flower`→`("near_forest",)`
    legacy_id heuristic) → new `metadata.source_region_tags: ["near_forest", "sacred_grove"]`
    (`"near_forest"` explicitly re-included so the prior heuristic coverage is preserved, not
    silently dropped)
  - `spirit_wisp`: no `metadata` block (resolved to `()`, no legacy_id branch matches this kind) → new
    `metadata.source_region_tags: ["sacred_grove", "haunted_battlefield"]`
- **Rationale**: **Bug Fix** (same class as §2.26/§2.27 — authoring staleness, not a deliberate design
  decision). Each affected region already had a resource node physically placed there by its composing
  world module (`orc_clan_territory.yaml`, `forest_warden_grove.yaml`, `sunken_swamp_border.yaml`,
  `undead_battlefield.yaml`, `trading_company_hub.yaml`); the catalog's gating tags simply never caught
  up to that placement.
- **Verification**: `tests/unit/strategic/test_opportunities.py`, `tests/unit/core/test_registry_bridge.py`,
  `tests/integration/content/test_resource_region_coverage_corpus.py` (parity ledger `TOWN-189`)
- **Status**: ACTIVE

### 2.32 River Ford Resource-Region Tag-Gap Fix (TCK-20260807-GUILD-SCARCITY-REGION-COVERAGE-GAP)
- **Subsystem**: World / Resource Opportunities
- **Old Behavior**: `herb_patch` had a resource node physically placed in `river_ford` by its
  composing world module (`river_crossing.yaml`, `resources: {herb_patch: 3}`, composed by
  `highland_traverse` and `quest_dense_frontier` — both new worlds authored after §2.28's
  2026-07-06 audit), but the catalog's `source_region_tags` allowlist
  (`data/content/world/resources.yaml`) omitted `river_ford`, so `ResourceOpportunityProvider`
  silently returned zero `gather_resource` opportunities for entities standing there, and
  `GuildAction.visit()`'s parallel scarcity computation silently reported `scarcity=0.0` ("fully
  abundant") instead of the real, low-charge value. Same root mechanism as §2.28, discovered via a
  fresh corpus-wide re-verification prompted by `GuildAction.visit()` becoming a live,
  role-agnostic consumer of this same gating data
  (`TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`) — the corpus had drifted with 3 new regions since
  §2.28's audit (`river_ford`, plus `deep_forest`/`survivor_outpost`, see §2.29's 2026-08-07
  update for those two).
- **New Behavior**: purely additive extension of `metadata.source_region_tags`:
  `herb_patch`: `["near_forest", "moon_cave", "hometown", "swamp_border_territory"]` →
  `[..., "river_ford"]`.
- **Rationale**: **Bug Fix** (same class as §2.26/§2.27/§2.28 — authoring staleness following new
  world content, not a deliberate design decision). `river_crossing.yaml` declares
  `biomes: ["near_forest"]` — a biome `herb_patch`'s `source_region_tags` already fully trusted —
  and its own description explicitly states "Freshwater herb growth lines the banks," strong
  self-evident authoring intent, matching the evidentiary bar §2.28 used for its own fixes.
- **Verification**: `tests/unit/strategic/test_opportunities.py::test_resource_opportunities_river_ford_herb_patch`,
  `tests/integration/content/test_resource_region_coverage_corpus.py::test_no_entity_of_any_role_spawns_in_an_unresolved_region_corpus_wide`
  (parity ledger `TOWN-191`, `STRAT-244`'s 2026-08-07 update note)
- **Status**: ACTIVE

### 2.29 Hazard-Zone Resource-Free Regions (TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT)
- **Subsystem**: World / Resource Opportunities — Content Disposition
- **Situation**: `bandit_road`, `goblin_camp`, and `wolf_den` carry zero resource-node content
  corpus-wide — neither `scalable_bandit_camp.yaml` nor `bandit_road_trade_pressure.yaml` declares any
  `resources:`/`resource_recipes:` for `bandit_road`; `goblin_camp_conflict.yaml` declares none for
  `goblin_camp`; `wolf_den_near_forest.yaml` declares resources but its first-declared region is
  `near_forest`, so the compiler places all of that module's nodes there, never in `wolf_den` itself.
  Unlike the 5 regions closed by §2.28, no resource kind's `preferred_biomes` names any of these three
  regions — there is no self-evident authoring intent either way.
- **Decision**: This absence of resource content is an **intentional hazard-zone gap**, decided by human
  review (2026-07-08) — hazard/combat regions do not offer foraging by design. No new resource content
  is authored for any of the three regions.
- **Rationale**: **Intentional Gameplay Change**.
- **Verification**: `tests/unit/strategic/test_opportunities.py::test_resource_opportunities_bandit_road_and_wolf_den_no_resource_nodes`
  (bandit_road, wolf_den) and the pre-existing
  `test_resource_opportunities_goblin_camp_and_haunted_battlefield_no_resource_nodes` (goblin_camp)
- **Status**: ACTIVE
- **Update (2026-08-07, TCK-20260807-GUILD-SCARCITY-REGION-COVERAGE-GAP)**: extended this same
  disposition class to 2 more zero-content regions found by a fresh corpus-wide re-verification
  (prompted by `GuildAction.visit()` — a role-agnostic consumer of this same gating mechanism —
  going live via `TCK-20260807-QUEST-GUILDACTION-DEAD-WIRING`): `deep_forest`
  (`forest_warden_grove.yaml` places its flat `resources:` dict entirely in the module's
  first-declared region, `sacred_grove`, the identical compiler-placement quirk that produced
  `wolf_den`'s gap — `deep_forest` itself receives zero nodes) and `survivor_outpost`
  (`survivor_camp_shelter.yaml` declares no `resources:` block at all — a "shelter" module with no
  foraging content by design). Verification extended to
  `tests/unit/strategic/test_opportunities.py::test_resource_opportunities_deep_forest_and_survivor_outpost_no_resource_nodes`
  and a new corpus-wide, all-roles regression test,
  `tests/integration/content/test_resource_region_coverage_corpus.py::test_no_entity_of_any_role_spawns_in_an_unresolved_region_corpus_wide`
  (the original regression test in that file only checked hero-role spawns, a scope that was
  correct while `GuildAction` was dormant but stale now that it is a live, role-agnostic
  consumer of the same coverage data).

### 2.30 Non-Native Faction Hazard Exposure — `town_council` at `bandit_road` (TCK-20260710-TOWN-COUNCIL-HAZARD-DA)
- **Subsystem**: World / Environment — Content Disposition
- **Situation**: `town_council`'s 2 `merchant_caravan_frontier_guard` entities are stationed at
  `bandit_road` (`hazard_level: 2.0`, `hazard_kind: "NATURAL_TERRAIN"`) in both `urban_political`
  and `generated_frontier_3_42`. `town_council` declares no `hazard_immunities`
  (`data/content/social/factions.yaml`), so these entities take full, unmitigated hazard drain via
  `EnvironmentService.calculate_hazard_drain`, unlike `bandit_road`'s native `bandit_company`
  (`hazard_immunities: ["NATURAL_TERRAIN"]`) and the region's other populating faction,
  `merchant_league` (also `["NATURAL_TERRAIN"]`, granted by
  `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE`). Two independent investigations
  (`TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE` Risk #2,
  `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE` Root cause 2) found this
  identical case and both declined to rule on it, deferring it as "may be intentional
  conflict-pressure flavor" without recording a decision. A blast-radius check (this ticket)
  confirmed `town_council` is populated in exactly one hazardous region across both worlds —
  `bandit_road` — and nowhere else corpus-wide within the two named worlds
  (`trading_company_hub.yaml`'s `hometown`/`trading_hometown` region spawns only
  `merchant_league`, never `town_council`, in either world's actual resolved spec).
- **Decision**: This exposure is **ratified as intentional**, decided by DA ruling under
  `TCK-20260710-TOWN-COUNCIL-HAZARD-DA` (2026-07-10). `town_council`'s guards are not native to
  `bandit_road` — they are dispatched there specifically because it is a bandit-contested
  wilderness road, i.e. the thematic opposite of "native habitat," which
  `docs/mechanics/05_world_evolution.md` §3 establishes as the criterion for declared endurance.
  The mechanics doc's own worked example (a hero party and a hostile wolf pack both taking full,
  equal `TOXIC_GAS` drain inside a hazard neither declares endurance for) establishes that
  non-native factions taking unmitigated drain in a hazard they are not adapted to is designed
  behavior, not an oversight — `town_council`'s guard escort taking slow attrition on a contested
  road over a long campaign is the same shape of case. No content or code change is made;
  `data/content/social/factions.yaml` and `docs/parity_ledger/world_dynamics.yaml` (`WORLD-029`,
  `WORLD-060`) are left unchanged by this ruling.
- **Rationale**: **Intentional Gameplay Change**. Endurance under this mechanism is strictly a
  faction-declared, native-habitat property (`TCK-20260701-HAZARD-NATIVE-IMMUNITY`'s design,
  reaffirmed by this ruling) — `town_council` was never native to `bandit_road`, so extending it
  an immunity here would require inferring endurance from something other than declared nativity
  (e.g. "is the last remaining unmitigated faction in the region"), which is the same
  blanket/inferred-immunity anti-pattern that mechanism's own rejected first-pass design
  (`entity.identity.faction == Faction.MONSTER_HORDE and region.kind == "WILDERNESS"`) was
  rejected for.
- **Verification**: `tests/unit/worldassembly/test_corpus_diversity.py::test_population_stability[urban_political]`,
  `::test_population_stability[generated_frontier_3_42]` (both pass at the existing 300-tick floor
  with this exposure present and unmodified, confirmed 2026-07-10);
  `::test_hazard_kind_matches_populating_faction_immunity[urban_political]`,
  `::test_hazard_kind_matches_populating_faction_immunity[generated_frontier_3_42]`
  (region-level immunity match already satisfied by `bandit_company`/`merchant_league`, unaffected
  by this ruling).
- **Status**: ACTIVE

### 2.31 DecisionTraceWriter Async Drain — Crash-Loss & Overflow-Drop Windows (TCK-20260702-OBSISO-TRACE-ASYNC)
- **Subsystem**: Engine / Observability
- **Old Behavior**: `DecisionTraceWriter.write_trace()` wrote `decision_trace.jsonl` and called
  `DecisionTraceIndex.append_entry()` (which itself flushes `decision_trace_index.json`)
  synchronously, in-line, from inside `AdventureDecisionPhase.apply()`'s per-hero loop — a
  direct §3 hot-path file-I/O violation of
  `docs/architecture/observability_hot_path_safety_contract.md`, but with the effect that every
  written record was durable on disk by the time `write_trace()` returned.
- **New Behavior**: `write_trace()` is now a bounded in-memory enqueue only
  (`self._queue.try_push(_DecisionTraceQueueItem(entry=entry))`); the actual
  `decision_trace.jsonl` write and `DecisionTraceIndex.append_entry()` call happen off-path on a
  private `QueueDrainWorker` (`_write_entry_to_file`), following the same per-instance
  `BoundedObservabilityQueue`/`QueueDrainWorker` pattern already shipped and accepted for
  `EventRecorder`/`simulation_events.jsonl`. This introduces two independent, bounded windows
  where an entry that was successfully enqueued is not guaranteed to reach disk:
  - **Crash-loss window**: any entries still sitting in the queue (not yet drained) at the
    moment of an unclean process kill are lost. Bounded by the worker's `interval_sec=0.01s`
    default drain cadence (`QueueDrainWorker.__init__`, `src/observability/queue.py`) — not
    unbounded, since the worker drains the full queue on every cycle.
  - **Queue-overflow-drop window**: `_DecisionTraceQueueItem.severity` is hardcoded to
    `"INFO"` (it exists only to satisfy `BoundedObservabilityQueue.try_push()`'s shared
    severity-eviction interface, not to express real priority for trace entries). Under
    sustained queue saturation (occupancy at `ObservabilityConfig.get_max_queue_size()`), new
    decision-trace entries are silently dropped rather than blocking the hot path — real,
    design-level data loss, independent of the crash-loss window above, bounded by `max_size`.
- **Decision**: Both windows are accepted as-is. No periodic off-path fsync/force-drain
  mechanism is introduced.
- **Rationale**: **Bounded**. (a) `EventRecorder` already carries the identical crash-loss and
  overflow-drop profile on the identical `BoundedObservabilityQueue`/`QueueDrainWorker`
  primitive for `simulation_events.jsonl`, shipped and accepted with no fsync mechanism of its
  own — introducing one only for the trace writer would be an unexplained, unjustified
  inconsistency between two components sharing the same underlying pattern. (b) The ticket's own
  Assumptions section names this as the expected fallback-avoidance outcome ("crash-loss
  window... is acceptable if documented"), and no contract owner has recorded disagreement.
- **Verification**:
  `tests/integration/observability/test_decision_trace_determinism.py` (proves queue occupancy
  stays well under `max_size` — i.e. `dropped_count == 0` — across a real two-run seeded scenario,
  the occupancy-headroom proof the determinism guarantee itself depends on);
  `tests/unit/observability/test_decision_trace.py::test_worker_thread_does_not_survive_close`,
  `::test_close_is_idempotent` (demonstrate the buffered-vs-persisted boundary: `close()`
  synchronously drains and persists all remaining queued entries before returning, bounding the
  crash-loss window to "process is still running").
- **Status**: ACTIVE

### 2.33 Opportunity-Attack Kill Reward Orphaned on the Victim (TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE)
- **Subsystem**: Engine / Combat-Progression
- **Old Behavior**: `MovementSystem.resolve_move`'s opportunity-attack branch
  (`src/engine/movement.py`, triggered when an entity tries to move away from
  `engaged_hostiles`) called `CombatResolutionSystem.resolve_multi_attack(attackers, entity,
  ...)` and attached the entire resulting `CombatUpdate` — including its
  `resource_transfers` (the kill's XP/gold reward, correctly computed by `resolve_multi_attack`
  itself) — onto `entity`'s own `EntityUpdate` (`updates[entity.id] = EntityUpdate(entity_id=
  entity.id, combat=combat_update)`). `entity` here is the retreating/moving unit — the
  **victim** of the attack, not the `attackers` who should receive the reward. Even had the
  attribution been correct, `resource_transfers` was never lifted out of the nested
  `CombatUpdate.combat` field into the top-level `EntityUpdate.resource_transfers` field that
  `ResourceTransactionSystem.resolve_all()` actually reads (`src/engine/economy.py:58`) — a
  second, independent defect. Confirmed via direct grep that nothing in the codebase ever reads
  `.combat.resource_transfers` back out — the reward was written to a field nothing consumes,
  on every single occurrence. Empirically, this is not a rare edge case: a real 2000-tick
  instrumented run of `sandbox_world` (seed 42) showed the deliberate `ATTACK` action firing
  **zero** times, while this opportunity-attack path fired 560 times and produced 9 real
  deaths — i.e. this was the dominant, near-exclusive real combat-kill path in the corpus, and
  its reward was unconditionally discarded. This fully explains the corpus-wide
  `growth_trajectory` ≈ 0 finding from `TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS`'s own
  full-corpus lifecycle-score run — not because kills were too rare to matter, but because the
  path that reliably produces them could never reward anyone regardless of volume.
- **New Behavior**: after building `combat_update`, if it carries `resource_transfers` and a
  resolved `attacker_id`, a second `EntityUpdate(entity_id=combat_update.attacker_id,
  resource_transfers=combat_update.resource_transfers)` is built and merged into `updates`
  (using `.merge()` defensively, since `updates` can already hold an entry for the same id from
  an earlier occupancy-swap branch in the same function). `attacker_id` follows the same
  "first attacker" attribution convention `entity_killed`'s own event shaper already uses for
  multi-attacker kills (`src/observability/event_shapers.py:158`). Verified end-to-end: before
  the fix, `entity.identity.evolution_points`/`evolution_level` never changed across a real
  2000-tick `sandbox_world` run despite confirmed kills; after the fix, the same scenario
  produces a real `evolution_points_delta > 0` on the attacker.
- **Rationale**: **Bug Fix**. Reward misattribution plus a missing lift onto the field the
  authoritative resolution path actually reads — not a design tradeoff, same class as `§2.24`'s
  pipeline-wiring merge fix and `§2.25`'s missing apply-path materialization.
- **Note (deliberately out of scope for this fix)**: the same call site hardcodes
  `is_lethal=False`, so `resolve_multi_attack`'s `outcome_kind` can never be `"KILL"` on this
  path (only `"DEFEAT"`), meaning `entity_killed`/`hero_death_unrecorded`
  (`event_shapers.py:157`, gated specifically on `outcome_kind == "KILL"`) never fire for this
  entire class of real deaths either. The XP/gold reward itself is gated on `alive`, not
  `outcome_kind`, so this fix is sufficient to unblock progression without touching `is_lethal`
  — whether opportunistic strikes during a retreat should ever count as a full "kill" outcome is
  a game-design judgment call left to a follow-up, not assumed here.
- **Verification**:
  `tests/unit/movement/test_tactical_movement.py::test_opportunity_attack_lethal_grants_resource_transfers_to_attacker`
  (real lethal opportunity-attack scenario through the full `AuthoritativeApplyPipeline.refine()`
  path: asserts the victim's own `EntityUpdate` carries no `resource_transfers` and the
  attacker's own `identity.evolution_points_delta > 0` after full resolution).
- **Status**: ACTIVE

### 2.34 Hero's Journey Rebirth Orphaned in the Real Dominant Kill Path (TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION)
- **Subsystem**: Engine / Combat-Progression
- **Old Behavior**: `CombatResolutionSystem.resolve_attack()` (`src/engine/combat.py`) was the
  only one of 4 real kill-resolution functions (`resolve_attack`, `resolve_skill_usage`,
  `resolve_multi_attack`, `resolve_aoe_attack`) that read `classification.rebirth_eligible`
  (`CombatRewardClassificationService.classify_defeated_target()`'s own output, `True` iff the
  defeated defender's role is `HERO`) and branched into `REBIRTH`/`PERMADEATH` outcomes with
  `generation_delta`/`is_permadeath_set`. The other 3 functions — including `resolve_multi_attack`
  — already computed the same `classification` object for `xp_gain`/`gold_gain`, but never
  consumed its `rebirth_eligible` field at all. This session's own direct instrumentation
  (`TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF`, `TCK-20260808-PROGRESSION-GROWTH-ECONOMY-
  UNREACHABLE-IN-PRACTICE`) already established `resolve_attack` fires **zero** times in real
  2000-tick corpus runs (the AI never selects the plain `ATTACK` action) while `resolve_multi_attack`
  (via `movement.py`'s opportunity-attack mechanic) is the corpus's real, dominant kill path —
  making Hero's Journey rebirth structurally unreachable regardless of HERO population size or
  kill rate, not merely rare. Confirmed real, not assumed: `entity_lifecycle_score.py`'s own
  `life_arc_detector_reachable` field read `null` (never observed) across every real run this
  session's own tools produced, at every tick length tested (200 through 2000).
- **New Behavior**: `resolve_multi_attack()` now ports the same rebirth/permadeath branch
  `resolve_attack()` already had, reusing the classification it already computes, and sets
  `generation_delta`/`is_permadeath_set` on its own returned `CombatUpdate` (previously omitted
  entirely). `movement.py`'s own opportunity-attack call site now also lifts those two fields into
  a `LifecycleUpdate` on the victim's own top-level `EntityUpdate` — the identical "computed but
  never lifted to the field the authoritative apply path actually reads" pattern already found and
  fixed once this session (§2.33) for the same call site's own `resource_transfers`.
- **Rationale**: **Bug Fix**. A real mechanic, already correctly implemented once, silently
  inaccessible because it only existed in the one combat-resolution function the real corpus never
  exercises — same class as §2.33 and §2.24/§2.25.
- **Note (deliberately deferred, disclosed)**: `resolve_skill_usage()`/`resolve_aoe_attack()` have
  the identical gap but 0 real calls observed in this session's own direct instrumentation —
  porting there too would be speculative without real data showing either path is corpus-active;
  left as a residual, lower-priority gap for a future ticket if that changes.
- **Verification**:
  `tests/unit/movement/test_tactical_movement.py::test_opportunity_attack_lethal_hero_defender_triggers_rebirth`
  (real lethal opportunity-attack scenario, `EntityRole.HERO` defender, through the full
  `AuthoritativeApplyPipeline.refine()` path: asserts the victim's own `EntityUpdate.lifecycle.
  generation_delta == 1`).
- **Status**: ACTIVE

### 2.35 Adventure-Routing Phase Discarding All Earlier-Tick Updates (TCK-20260808-ROUTING-FLAG-FACTION-INFORMATION-RNG-COUPLING)
- **Subsystem**: Engine / Pipeline
- **Old Behavior**: `AuthoritativeApplyPipeline.refine()`'s (`src/engine/pipeline.py`)
  `adventure_decision` phase call site was the one phase in the file whose `run_phase(...)` lambda
  did not wrap its own result in `u.merge(...)` — every sibling phase (`information_belief`,
  `cooperation`, `diplomatic_transitions`, etc.) correctly does. `AdventureDecisionPhase.apply()`
  (`src/domains/adventure/phase.py`) is itself correctly self-contained — it starts from a fresh
  `StateUpdate()` and returns only its own hero-routing entity updates, by design, with no `u`
  parameter at all. The bug was entirely at the call site: the lambda's `u` was captured but never
  used, so `run_phase` returned that fresh, near-empty `StateUpdate` directly, **replacing** (not
  merging into) the entire accumulated `update` from every phase that had already run earlier in
  the same tick (`information_belief`, `cooperation`, `contracts`/`blacksmith`, `faction_decision`,
  `faction_awareness`, `diplomatic_transitions`). Real, controlled proof (not assumed): a
  monkey-patched `frontier_marches` seed-42 probe showed `diplomatic_state_machine.compute_
  transitions()` computing the identical 58 `FactionUpdate` objects regardless of the routing flag
  (ruling out the RNG-consumption-order hypothesis this ticket was originally filed under), while
  `refine()`'s own returned `faction_updates` count was 58 with routing OFF and **0** with routing
  ON — the discard happened strictly inside `refine()`, after the merge, before return.
- **New Behavior**: the lambda now wraps `AdventureDecisionPhase.apply(...)`'s result in
  `u.merge(...)`, matching the established pattern every other phase in the file already uses.
  Verified via the same controlled probe: post-fix, `refine()`'s `faction_updates` count and
  content are identical (58 updates) with routing ON or OFF, and the fix does not regress
  `AdventureDecisionPhase`'s own behavior (heroes still receive real strategic projects across a
  live multi-tick run with routing ON).
- **Rationale**: **Bug Fix**. Any world with `ENABLE_ADVENTURE_ROUTING=ON` silently lost every
  pipeline phase's output that ran before `adventure_decision` in the same tick, every tick — not
  a routing-specific interaction, a missing merge call.
- **Note (real scope check, not assumed)**: the 2 existing routing-enabled worlds
  (`hero_guild_routing`, `simq_routing_test`) share this code path, but their own already-committed
  `grade_anchors.json` SOCIAL/FACTION/INFORMATION anchors are unaffected — SOCIAL because neither
  world enables `ENABLE_SOCIAL_COOPERATION`, FACTION/INFORMATION because both worlds are already
  documented FACTION/INFORMATION-inert by deliberate tier-purity design (no content authored). Real
  ECONOMY-signal impact (from the unconditional `contracts`/`blacksmith` phase, which also runs
  before `adventure_decision`) was checked and re-verified for both worlds — see
  `docs/simulation_quality/eval_matrix_results.md`'s own drift-tracking entry for this ticket if
  a real anchor update landed.
- **Verification**:
  `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py::test_adventure_decision_does_not_discard_earlier_phase_updates`
  (real `AuthoritativeApplyPipeline.refine()` run with `ENABLE_ADVENTURE_ROUTING=ON`, a `HERO`
  entity present, and a queued `diplomatic_transitions`-eligible faction pair: asserts the returned
  `StateUpdate.faction_updates` is non-empty, not silently discarded).
- **Status**: ACTIVE

---

### 2.36 Readiness Never Regenerated Outside Town REST (TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION)
- **Subsystem**: Combat / Engine
- **Old Behavior**: `docs/engine/contracts/minimal_kernel.md` Section 5 ("Readiness-Gated Action
  Semantics") has documented, as an active P1 kernel law, that "Entities gain readiness based on
  their `readiness_speed` (passive)". No such field or passive regeneration existed anywhere in
  `src/` (confirmed via grep) — `CombatComponent` had no `readiness_speed` field, and
  `ApplyPath._compute_entity_changes` (`src/engine/apply.py`) never regenerated readiness. The
  only restoration path was a narrow, town-specific `REST`-at-inn/home action
  (`src/engine/town_resolution.py`, `+10.0`). Every other consumer of readiness only ever
  decreased it: movement (`move_cost * terrain_cost`), attacks (`-100.0` full reset), and region
  suppression drain (`-5.0`/tick). A real, instrumented probe (`urban_political`, 330 samples
  across a 2000-tick run) found `LegalityServiceV2.verify_attack_legality()` FALSE in 100% of
  cases, 55% specifically via `ReasonCode.INSUFFICIENT_READINESS` — readiness monotonically
  decayed to 0 within the first ~15-40 ticks of any run (via ordinary ambient `WANDER` movement,
  not just deliberate pursuit) and then stayed there permanently. This was the single largest real
  contributor to the corpus-wide near-zero combat/kill rate this session's own growth/progression
  investigation chain (`TCK-20260808-LEVEL-UP-GATED-PROGRESSION-CASCADE-DEAD`) traced back to.
- **New Behavior**: Added `CombatComponent.readiness_speed: float = 10.0`
  (`src/core/state.py`) and a passive per-tick regen block in
  `ApplyPath._compute_entity_changes` (`src/engine/apply.py`), mirroring the existing Stamina
  regen block's own pattern — readiness below 100.0 climbs by `readiness_speed` each tick, capped
  at 100.0. While implementing this, also found and fixed a latent, independent bug: `EntityState.
  to_readonly()` (`src/core/state.py`, `CORE-PERF-010`'s manual-reconstruction optimization)
  rebuilds `CombatComponent` via an explicit hardcoded keyword-argument list on every entity whose
  `wounds`/`scars` aren't already tuples — this list omitted the new field, silently resetting any
  non-default `readiness_speed` back to the dataclass default every readonly-conversion pass. Both
  are now covered by direct regression tests (`tests/unit/combat/test_readiness_regen.py`).
  Separately (same investigation, same subsystem, small enough to land together): both
  `LegalityServiceV2.verify_attack_legality()` and `TacticalDecisionSystem`'s own hostile-detection
  loop hardcoded `RelationContext(intruding=False)`; `RelationProjectionService.project_relation()`
  treats an explicit `False` (not `None`) as a confirmed non-intrusion for
  `contextual_intruder_groups`-classified relationships, permanently forcing them to "neutral"
  regardless of real combat engagement. No real territorial-intrusion detector exists anywhere in
  `src/` (confirmed via grep), so both call sites now simply leave `intruding` unset (`None`),
  which correctly defers to `combat_engaged` instead of asserting a false negative.
- **Rationale**: **Bug Fix**. The readiness gap is a confirmed divergence from an already-documented
  authoritative kernel contract (not a new design decision), and the `intruding` hardcode is a
  confirmed logic bug with no real detector ever backing the hardcoded value.
- **Note (real scope check, not assumed)**: real re-verification (`dungeon_crawl`, 600-tick run,
  same `is_attack_legal` probe methodology) shows the legal rate moving from a confirmed 0%
  baseline to a real, non-zero 1.3% (2/159 real-hostile samples) — genuine, measurable progress,
  but **not** a full resolution. Movement and attack both draw from the same `readiness` pool, and
  an entity that must travel to reach a target can still arrive with insufficient readiness even
  with passive regen active; a parameter sweep (`readiness_speed` 10/20/30/50) showed no clearly
  superior single value within this ticket's own testing, and INSUFFICIENT_READINESS remained the
  dominant reason at every tested value. Closing this further is a broader combat-pacing question
  (e.g. separating movement cost from attack-readiness cost) explicitly out of this ticket's own
  proportionate scope — disclosed honestly rather than force-tuned further. The `intruding` fix is
  similarly disclosed as real but not proven to be the dominant real-corpus driver of
  `FRIENDLY_FIRE_ILLEGAL` in the specific world tested (`urban_political`'s own original population
  contains no `wild_beast_pack`/`swamp_tribe` entities to exercise it).
- **Verification**:
  `tests/unit/combat/test_readiness_regen.py` (5 tests: passive regen, 100.0 clamp,
  `readiness_speed=0` disables regen, `to_readonly()` field-drop regression, and the
  `contextual_intruder_groups` hostility regression).
- **Status**: ACTIVE

---

### 2.37 Bravery Never Affected the Real-Time Flee Decision (TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-PERSONALITY)
- **Subsystem**: Combat / Strategic Cognition
- **Old Behavior**: `AppraisalSystem.evaluate_emotional_state()` (`src/engine/cognition.py`) — the
  hard, first-checked real-time flee gate consumed by `src/engine/tactical.py`'s own
  `PANIC_RETREAT` branch (`if emotion.is_fleeing: ...`, checked *before* any goal-competition
  layer runs) — computed `panic` from regional dread, nemesis/grudge history, HP percentage, and
  outnumbered ratio, but never referenced `subject.identity.personality.bravery`. This
  contradicted `bravery`'s own dataclass field comment, present since the field was added:
  `bravery: float = 0.0  # Biases combat vs flee` (`src/core/state.py:420`). A separate, real,
  already-verified mechanism (`STRAT-226` in `docs/parity_ledger/strategic_cognition.yaml`,
  `AdventureRouteScorer`'s bravery/caution risk multiplier) *does* bias strategic route selection
  by bravery — but that governs a different, longer-horizon decision; the tactical, per-tick
  panic/flee gate had no bravery term of its own until this ticket, meaning a maximally brave and
  a maximally cowardly entity fled at identical HP/context thresholds in real gameplay.
- **New Behavior**: `panic -= subject.identity.personality.bravery * 0.3` is now applied before
  the `is_fleeing = panic > 0.4` decision. Bravery is real-valued in `[0.0, 1.0)`, RNG-assigned
  per entity at generation (`src/worldbuilding/compiler.py:304`) — a zero-bravery entity is
  unaffected (subtracting 0), a maximally brave entity's effective flee threshold rises from 0.4
  toward ~0.7.
- **Rationale**: **Bug Fix**. The field's own comment already declared this intent; the function
  simply never implemented it.
- **Note (real scope check, not assumed)**: investigation also confirmed, but did **not**
  implement, two related findings: (1) the real opportunity-attack "pursuit prevents escape"
  mechanic the user recalled already exists and already applies uniformly to the entire real
  population — its one documented escape hatch (`ActionStyle.EVASIVE` + `MovementMode.RETREAT`
  skipping the OA, `src/engine/movement.py:185-186`) is structurally unreachable, since no real
  entity-generation path (`generator.py`, `worldbuilding/compiler.py`) ever assigns anything but
  the default `ActionStyle.BALANCED`; (2) `bravery` has zero species/archetype correlation in real
  content (`data/content/entities/entity_archetypes.yaml` has no personality fields at all) — it
  is pure per-entity RNG, so a "wolf" archetype does not yet get systematically higher bravery
  than any other entity. Both are real, evaluated, and deferred: wiring `ActionStyle` would
  meaningfully change corpus-wide OA/escape dynamics while `TCK-20260809-COMBAT-ATTACK-LEGALITY-
  ALWAYS-FALSE-INVESTIGATION`'s own downstream effects (landed earlier this same session) are
  still being absorbed; species-correlated bravery requires a real content/design decision not made
  here. This fix changes *which* entities flee at a given state, not combat *frequency* — no full
  corpus re-verification was run (judged disproportionate for this narrow, unit-testable change).
- **Verification**:
  `tests/unit/strategic/test_cognition_immediate_fixes.py::
  test_bravery_dampens_panic_and_raises_flee_threshold` (also re-confirms the pre-existing
  `test_near_death_panic_progression` baseline is unaffected for the zero-bravery default case).
- **Status**: ACTIVE

---

### 2.38 Movement Double-Costed Readiness and Stamina for the Same Fatigue Concern (TCK-20260809-COMBAT-PACING-READINESS-MOVEMENT-DECOUPLE)
- **Subsystem**: Combat / Engine
- **Old Behavior**: A successful move (`MovementSystem.resolve_move()`, `src/engine/movement.py`,
  and the position-swap path in `src/engine/pipeline_phases/movement.py`) drained **both**
  `combat.readiness` (`readiness_cost = move_cost * terrain_cost`, or a flat `-move_cost` on the
  position-swap path) **and** `stamina` (`StaminaComponent.MOVE_COST`, a flat per-move cost with
  its own separate `StaminaService.tick_regen()` and exhaustion mechanic,
  `docs/combat/combat_movement_overhaul_spec.md` §5) — two distinct resources charged for the same
  single fatigue concern. `readiness`'s own documented contract
  (`docs/engine/contracts/minimal_kernel.md` §5) describes it as a pure attack-eligibility/
  cooldown gate ("Entities are eligible to act only when their readiness threshold is met"), not a
  movement-fatigue resource — `stamina` already existed to fill that role. This was the real cause
  `TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION`'s own §2.36 entry disclosed but
  explicitly deferred: even with passive readiness regeneration active, an entity that had to
  travel to reach a hostile could still arrive readiness-depleted, capping the real corpus-wide
  attack-legal rate at ~1.3% (`dungeon_crawl`, 600-tick real probe).
- **New Behavior**: Removed the `readiness_delta` cost from both real movement-application sites,
  leaving `stamina` as the sole movement-fatigue cost. `verify_movement_legality()`'s own smaller
  readiness pre-check (`readiness >= move_cost`, a much lower bar than the 100.0 attack threshold)
  was left untouched — it still provides a brief, real movement lockout immediately after an
  attack resets readiness to 0, which is correct and not disruptive.
- **Rationale**: **Bug Fix**. Confirmed a genuine double-cost against `stamina`'s own already-real,
  already-documented fatigue role — not a new design decision, closing a real gap the prior
  ticket's own investigation had already traced to this exact mechanism and explicitly named as
  the next real lever.
- **Note (real scope check, not assumed)**: real re-verification (same `is_attack_legal` probe
  methodology as §2.36, live compiled worlds): legal rate moved from 1.3% to a real, measured
  28.5% (`dungeon_crawl`, 600 ticks) and 36.6% (`urban_political`, 600 ticks) —
  `INSUFFICIENT_READINESS` no longer appears at all in either world's own real reason-code
  breakdown. The remaining illegal reasons are `OUT_OF_RANGE` (now dominant — expected, since
  random sampling catches entities mid-approach) and `FRIENDLY_FIRE_ILLEGAL`. Scoped pytest
  (`tests/unit/movement/`, `tests/unit/combat/`, `tests/unit/core/`, `tests/unit/kernel/`,
  `tests/unit/tactical/`, `tests/unit/domains/optimization/`, `tests/unit/worldbuilding/`,
  `tests/unit/worldassembly/`, `tests/unit/strategic/`, `tests/unit/entities/`,
  `tests/unit/content/`, `tests/unit/resource/`, `tests/unit/social/`, plus integration combat/
  pipeline/determinism suites): zero new regressions — the only failures present were the 2
  pre-existing, already-confirmed-unrelated ones from earlier this session.
- **Verification**:
  `tests/unit/movement/test_phase4_movement.py::test_successful_move_no_longer_costs_readiness`,
  `tests/unit/movement/test_position_swap.py::test_mutual_adjacent_position_swap_succeeds`
  (extended with a readiness-unchanged assertion).
- **Status**: ACTIVE

---

### 2.39 WorldEntitySpawner/ArchetypeEntityFactory Zero Personality (TCK-20260809-WORLDENTITYSPAWNER-ZERO-PERSONALITY)
- **Subsystem**: Entities / World Assembly
- **Old Behavior**: `ArchetypeEntityFactory.build_entity()` (`src/entities/archetype_factory.py`)
  and `WorldEntitySpawner._spawn_legacy_guard()` (`src/worldassembly/entity_spawner.py`) — the two
  branches `WorldEntitySpawner.spawn_from_context()` itself dispatches every entity to — never set
  `PersonalityComponent` at all, leaving every entity spawned through either path at the class's
  own all-zero default regardless of real `species_id`/`faction_id`. Same class of bug as
  `WorldCompiler.compile()`'s own earlier all-zero-personality bug
  (`TCK-20260619-P0-ENTITY-INIT`), for a separate, newer construction path that fix never covered.
  `docs/world/assembly_contract.md`'s own real, authoritative contract additionally stated "No
  randomness is introduced during spawning" — accurate at the time, but meant this path's own
  entities could never get the real, per-entity variance the `WorldCompiler.compile()` path
  already had.
- **New Behavior**: Extracted the shared bravery-bias/`ActionStyle` helpers
  (`_load_personality_bias_config`, `_PERSONALITY_BIAS_FALLBACK`, `get_bravery_bias`,
  `get_action_style_for_bravery` — previously module-level in `src/worldbuilding/compiler.py`,
  `TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION`/`TCK-20260809-COMBAT-ACTIONSTYLE-WIRING`)
  into a new `src/content_semantics/personality.py`, matching this repo's own established
  precedent for cross-cutting semantic helpers shared across `worldbuilding`/`worldassembly`/
  `engine` (`content_semantics/faction.py`, `relation.py`, `role.py`) — avoids a backward
  dependency from `src/entities/` onto a specific `worldbuilding` compiler module. Added
  `build_personality_for_entity(entity_id, faction_id, seed)` to the same new module (same
  `DeterministicRNG`/`Domain.WORLD`/`sub_id` convention `WorldCompiler.compile()` already uses),
  shared by both real construction branches. Threaded `seed: int = 42` (matching
  `CatalogScenarioStateBuilder.build()`'s own pre-existing default exactly) through
  `build_entity()`'s own signature and `spawn_from_context()`'s own signature, and wired
  `CatalogScenarioStateBuilder.build()`'s own already-existing `seed` parameter down into
  `spawn_from_context()` (previously computed but never passed through at all).
- **Rationale**: **Bug Fix**. The same real, confirmed pattern as the earlier
  `TCK-20260619-P0-ENTITY-INIT` fix, for a construction path that fix never covered — not a new
  design decision.
- **Note (real scope check, not assumed)**: real impact remains confirmed limited to
  certification/integration test infrastructure — `CatalogScenarioStateBuilder` (the only real
  caller of `WorldEntitySpawner`) has zero callers itself in the live SimQ scoring pipeline. This
  fix does not currently change any real, scored combat outcome or SimQ grade — it closes a
  confirmed, real, but currently-dormant gap. Real, live end-to-end verification (not
  unit-test-only): ran `CatalogScenarioStateBuilder.build()` against the real
  `wolf_territory_pressure` scenario — 15/15 real entities got non-zero personality; the 3 real
  `wild_beast_pack` wolf/spider entities showed bravery 0.617-0.989 (correctly biased high) with
  2/3 landing `AGGRESSIVE` `ActionStyle`. Also caught and fixed, during this ticket's own Test
  phase: the extraction broke 2 pre-existing tests that referenced
  `compiler._load_personality_bias_config` directly (moved to `test_personality.py`, the real new
  owner of that logic) and `src/content/matrix.py`'s own `social/personality_bias` content-usage-
  matrix entry, whose `evidence_tests` field still pointed at the old, moved test location.
- **Verification**: `tests/unit/content_semantics/test_personality.py` (9 tests),
  `tests/unit/entities/test_archetype_entity_factory.py` (4 new tests),
  `tests/unit/worldassembly/test_entity_spawner_legacy_guard.py` (4 tests, new),
  `tests/integration/worldassembly/test_world_entity_spawner.py` (4 new tests).
- **Status**: ACTIVE

### 2.40 Interruption-Bypass Generalization (TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION)
- **Subsystem**: Strategic Cognition / Project Interruption
- **Old Behavior**: `evaluate_project_switch()`'s lock-bypass gate (`src/systems/strategic_systems/intelligence.py`)
  allowed exactly two hardcoded cases: `kind == "detour"` (unconditional), or `kind == "danger"
  and score > 80` (unconditional, ignoring the current project's own score/retention entirely).
  No production `ProjectState(` construction site in `src/` ever set `kind="danger"` — this branch
  was reachable only via a directly hand-constructed `ProjectState`, not any live corpus scenario.
- **New Behavior**: `"detour"` remains the sole unconditional structural bypass. Any other
  candidate, regardless of `kind`, may bypass an active lock only when its score — normalized to
  a percentage of its own system's declared max (`_ADVENTURE_ROUTE_SCORE_MAX=2.9` for
  `ProjectKind`-typed candidates, classified via `isinstance(kind, ProjectKind)`;
  `_GOAL_UTILITY_SCORE_MAX=100.0` otherwise) — both exceeds the current project's own normalized
  effective score and clears an 80%-of-max urgency floor (`_INTERRUPTION_URGENCY_FLOOR_PCT`). This
  is a real, deliberate tightening of the (previously unreachable-in-production) danger-kind case,
  not a change to any observed live behavior: a `kind=="danger", score>80` candidate that would
  have bypassed unconditionally before now additionally requires the current project's own score
  not dominate it. The pre-existing raw `retention_margin`/`effective_current_score` formula
  (STRAT-005/006) and the final unconditional `candidate.score > effective_current_score`
  comparison are unchanged. Also fixed a co-dependent defect: `RouteToProjectMapper.map_to_states()`
  (`src/domains/adventure/mapper.py`) previously hardcoded `score=1.0` for every System-A
  (`AdventureRouteScorer`) project regardless of its real computed score; it now carries the real
  `AdventureRouteOption.score` through, and `AdventureDecisionPhase.apply()`
  (`src/domains/adventure/phase.py`) now routes its project handoff through
  `StrategicIntelligenceSystem.evaluate_project_switch()` instead of unconditionally overwriting
  `current_project_id` — both were prerequisites for the normalized comparison to be real rather
  than comparing a live score against a placeholder.
- **Rationale**: **Enforced**. Generalizes a hardcoded kind-string special case into the score/
  urgency rule it was already implicitly modeling, closing the gap where any future project `kind`
  (present or not-yet-invented) had no path to legitimately interrupt a locked project regardless
  of how urgent it actually was.
- **Verification**: `tests/unit/strategic/test_interruption_resistance.py::TestGenericInterruptionBypass::test_danger_bypass_blocked_when_effective_current_not_cleared`.
- **Status**: ACTIVE

---

### 2.41 Adventure-Route Defer-Reason Observability Gap (TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE)
- **Subsystem**: Engine / Cognition-Strategy
- **Old Behavior**: `AdventureDecisionPhase.apply()` wrote
  `property_updates={"last_defer_reason": result.selected.reason or "unknown",
  "last_defer_tick": tick}` on an entity's `EntityUpdate` whenever
  `AdventureDecisionService.decide()` returned `RouteFamily.DEFER_WITH_REASON`
  (`src/domains/adventure/phase.py:157-165`, pre-deletion). `event_extractor.py:620-626` read
  this key to emit a `defer_with_reason` SimulationEvent (`event_category: "strategy"`), feeding
  the AGENCY SimQ pillar.
- **New Behavior**: `AdventureGoalScorer.score()` (`src/ai/goals/adventure_scorer.py`) carries the
  same DEFER_WITH_REASON signal only as `GoalScore.metadata` (`route_family`, `raw_score`) — it
  does not write `last_defer_reason`/`last_defer_tick` to any `EntityUpdate.property_updates`, and
  the tier-5 arbitration path (`StrategicIntelligenceSystem.evaluate_strategic_intent()`) has no
  site that threads this metadata into a committed `EntityUpdate` without a larger
  `StrategicUpdate` schema change. `defer_with_reason` events no longer fire for adventure-routing
  deferrals.
- **Rationale**: **Bounded**. The DEFER_WITH_REASON signal is discarded by the shared tier-5
  utility-floor check (`src/systems/strategic_systems/intelligence.py:1450`,
  `if g_score.utility < 20.0 or (...): continue`) before any `StrategicUpdate`-returning site
  inside `evaluate_strategic_intent()` is ever reached — `AdventureGoalScorer`'s DEFER_WITH_REASON
  branch always scores `utility=0.0` by design (`adventure_scorer.py`'s DEFER_WITH_REASON early
  return). Porting this signal for real therefore requires special-casing sub-floor scores inside
  the shared tier-5 scoring loop itself (`intelligence.py:1394-1414`), a change that affects every
  `GoalKind` scorer's ineligible/deferred case, not just adventure's — deliberately bounded out of
  `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`'s narrow relocate-and-delete scope. A future
  ticket should design how sub-floor scorer signals surface (e.g., a
  `StrategicUpdate.property_updates` field populated from inside the shared loop before the floor
  filter runs, not merely threaded through the existing return sites) as its own reviewed change.
- **Broadened disclosure (TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT, 2026-08-13)**:
  The SAME deleted `AdventureDecisionPhase.apply()` was also the sole writer of
  `last_routing_family`/`last_routing_tick` (pre-deletion `phase.py:178-179`, readable via
  `git show 1825f914^:src/domains/adventure/phase.py`), written unconditionally on every
  **winning** route (i.e. whenever `evaluate_project_switch()` — now
  `evaluate_strategic_intent()`'s `ADVENTURE_ROUTE` branch — returns a non-`None` committed
  candidate), not just on the DEFER_WITH_REASON path this section otherwise describes. This case is
  **not** covered by the "Rationale: Bounded" argument above: a winning `ADVENTURE_ROUTE`
  candidate does not hit the sub-floor discard — it reaches a real commit site
  (`RouteToProjectMapper.map_to_states()`, `intelligence.py:1478-1495`) — it simply never writes
  `EntityUpdate.property_updates` there. `event_shapers.py:750-773` (live path,
  `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` defaults `ON`) and `event_extractor.py:594-618` (rollback
  path) both read `last_routing_family` to emit `route_selected`, `action_executed`, and
  `route_family_first_use` — 3 of AGENCY's 4 adventure-routing event types. All three are
  therefore also silently dead for every routing-capable world, not just the
  DEFER_WITH_REASON-driven `defer_with_reason` event this section originally documented — a
  strictly larger observability blast radius than previously disclosed here. Restoring this half
  is **not** a narrow observability fix: it requires a new field on the shared
  `StrategicUpdate` durable-update schema (`src/core/updates.py`; no such field exists today), a
  `StrategicUpdate.merge()` change, and threading it through two call sites in
  `intelligence.py` — the `ADVENTURE_ROUTE` win branch where the family is known
  (`intelligence.py:1478-1495`) and the outer refine-loop merge site
  (`intelligence.py:917-927`) that today only assigns `.strategic`, never `.property_updates` —
  because `RouteFamily -> ProjectKind` is a many-to-one mapping
  (`src/domains/adventure/mapper.py:31-47`), the specific family cannot be reconstructed after the
  fact from the committed `ProjectState.kind` at that outer site. This is deliberately **not**
  ported as part of this recalibration-only ticket (recalibrate-and-disclose decision, not a
  reflexive fix, given the area's active-churn history) — tracked instead by
  `TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE`. The `last_defer_reason` half of this
  section is unaffected by this broadened disclosure — it stays exactly as already
  `Bounded`/deliberately-not-ported, per the Rationale above.
- **Restoration (TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE, 2026-08-13)**: The
  `last_routing_family`/`last_routing_tick` write-path gap described in the broadened-disclosure
  paragraph above is now fixed. `StrategicUpdate` (`src/core/updates.py`) gained a dedicated
  `last_routing_family_set: Optional[str]` / `last_routing_tick_set: Optional[int]` scalar pair,
  following the existing `overload_source_set`/`overload_tick_set` "set last-write-wins"
  convention, with `is_noop()`/`merge()` support. `intelligence.py`'s `ADVENTURE_ROUTE` win branch
  (the shared `switch_up` return site, gated on `if switch_up:` so a candidate that wins the
  tier-5 competition but is then rejected by `evaluate_project_switch()` does not set the field)
  now sets `last_routing_family_set = best_candidate.metadata["route_family"].value` — the
  `.value` string, not the raw `RouteFamily` enum (`RouteFamily(str, Enum)` would otherwise make
  `str(family)` yield `"RouteFamily.X"`, not the deleted phase's original contract).
  **Implementation correction**: this ticket's own plan.md originally targeted
  `StrategicIntelligenceSystem.evaluate_all_strategic_intents()` (`intelligence.py:884-929`) as
  "the outer refine-loop merge site" for copying the resolved value into
  `EntityUpdate.property_updates`. That function is not referenced anywhere in `src/` and is not
  wired into the live tick pipeline — confirmed by a repo-wide grep during Implement. The actual
  live merge site is `StrategicIntelligenceSystem.fused_strategic_pass()`
  (`intelligence.py:291-642`, wired via `src/engine/pipeline.py:333`,
  `run_phase("strategic_intelligence", update, lambda u:
  StrategicIntelligenceSystem.fused_strategic_pass(state, u, cadence=cadence))`), which has its
  own separate `strat_up`-to-`EntityUpdate` merge site (`intelligence.py:~627-635`). Implement
  applied the identical copy-then-set `property_updates["last_routing_family"]`/
  `["last_routing_tick"]` fix at the correct, live site, and added a dedicated regression test
  (`tests/unit/strategic/test_fused_strategic_pass_routing_family.py`) exercising
  `fused_strategic_pass()` directly, in addition to the originally-planned
  `evaluate_all_strategic_intents()` coverage (kept since that function remains real, callable
  code, just not pipeline-referenced).
  **Open finding — AC3 not satisfied for the calibration worlds**: with the corrected write path
  verified working end-to-end at the unit/integration level (a winning `ADVENTURE_ROUTE`
  candidate's `StrategicUpdate` and resulting `EntityUpdate.property_updates` both carry
  `last_routing_family`/`last_routing_tick`, and `StrategyShaper.shape()` emits `route_selected`/
  `action_executed`/`route_family_first_use` for such an update), a fresh
  `tools/calibrate_simq.py` run against all 6 named run_keys (`simq_routing_test`/
  `hero_guild_routing` × seeds 42/123/456, `_500t`) still shows `AGENCY: {"grade": "C", "score":
  0.0}`, events=0, byte-identical to the pre-fix state. DEBUG-level tracing of
  `evaluate_strategic_intent()`'s tier-5 goal-selection log
  (`"[Tick N] Entity E strategic goal selection: chosen=..., rejected=..."`) across full 500-tick
  runs of both worlds at all sampled seeds shows `ADVENTURE_ROUTE`'s utility (capped at
  `_ADVENTURE_ROUTE_SCORE_MAX = 2.9`, normalized onto the shared 0-100 competition scale, observed
  ~20-26) never once outscoring `COMBAT_ENGAGE` (observed ~100-144) or `REGION_STABILIZATION`
  (observed flat 100.0) whenever either is active — and in these two worlds (a goblin raiding
  party plus, for `hero_guild_routing`, additional region-stabilization pressure), one or the
  other is active on effectively every evaluated tick for every hero. This is a separate,
  unrelated mechanism from the write-path bug this ticket fixes: it is the tier-5 goal-competition
  scale (`_score_scale_max()`, `intelligence.py:108-126`) interacting with
  `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`'s architecture change from an unconditional
  standalone phase (which never competed against other `GoalKind`s at all) to a competing
  `GoalScorer`. This ticket does not touch that competition/scale logic (out of scope per its own
  Scope Guards), so `grade_anchors.json` was left unchanged (the current `C`/`0.0` AGENCY values
  for all 6 run_keys are still the freshly-measured, correct values — there is nothing to
  recalibrate), and `docs/simulation_quality/eval_matrix_results.md`'s AGENCY Cross-World Design
  Note was likewise left as-is rather than being rewritten to claim a restoration that fresh
  measurement does not support. A follow-up ticket is recommended to investigate whether
  `ADVENTURE_ROUTE`'s utility ceiling/normalization should be revisited for routing-capable worlds
  with near-constant combat/danger pressure — that is a goal-competition design question, not an
  emission-wiring bug, and is explicitly not decided here.
- **Related finding — HARVESTING tier-5 starvation on `hero_guild_routing_seed456_500t` /
  `simq_routing_test_seed456_500t` (TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT, 2026-08-13)**:
  the same tier-5-goal-competition-dominance phenomenon this section documents for `ADVENTURE_ROUTE`
  (Restoration addendum above) independently and additionally suppresses `HARVESTING` on these two
  run_keys. DEBUG-trace evidence: `HARVESTING` wins tier-5 goal arbitration exactly 1/371 evaluated
  ticks on `hero_guild_routing_seed456_500t` and 1/335 on `simq_routing_test_seed456_500t` — the
  same two competitors (`COMBAT_ENGAGE`, `REGION_STABILIZATION`) dominate both worlds' tick budgets
  for the same structural reason (§2.43's `REGION_STABILIZATION` scorer floors at 100.0;
  `CombatEngageScorer` floors at 40 and commonly reaches 70-140+; `HarvestScorer`'s distance-decayed
  `50.0/dist` formula rarely exceeds 30). This directly suppresses ECONOMY (harvesting/crafting/trade
  events never fire) on both run_keys and PROGRESSION indirectly (via `capability_growth_stalled` —
  gear/gold growth requires harvesting/crafting, which essentially never runs). Recalibrated in
  `grade_anchors.json` by this ticket (`hero_guild_routing_seed456_500t` ECONOMY/PROGRESSION,
  `simq_routing_test_seed456_500t` PROGRESSION) — see this ticket's own investigation.md Finding 1.
  This is a distinct `GoalKind` (`HARVESTING`, not `ADVENTURE_ROUTE`) and a mechanistically distinct
  formula (distance-decay, not a hard scale cap), but the same downstream starvation *class* as this
  section's existing `ADVENTURE_ROUTE` disclosure. Not fixed here — a recalibrate-and-disclose
  decision, matching this ticket's own scope guards. If `TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-
  NEVER-WINS-TIER5` (the open follow-up already tracking the `ADVENTURE_ROUTE` half of this same
  phenomenon) is ever picked up, `HARVESTING`'s distance-decay formula should be considered in the
  same pass, since it loses to the identical two competitors for a structurally analogous reason.
- **Verification**: `tests/unit/observability/test_event_extractor_agency2.py::TestAntiDriftGuards::test_defer_property_name_constant_matches_phase_and_extractor`;
  `tests/unit/core/test_strategic_update_routing_family.py`;
  `tests/unit/strategic/test_adventure_route_materialization.py`;
  `tests/unit/strategic/test_fused_strategic_pass_routing_family.py`;
  `tests/unit/strategic/test_evaluate_all_strategic_intents_routing_family.py`;
  `tests/unit/observability/test_event_shapers_strategy.py`.
- **Restoration (partial) — TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5,
  2026-08-13**: The tier-5 competition-scale mismatch this section's "Open finding" paragraph
  above identified (`ADVENTURE_ROUTE`'s utility normalized against `_ADVENTURE_ROUTE_SCORE_MAX
  =2.9`, a denominator calibrated for a faction-directive-inclusive input configuration the live
  path never actually receives — see `docs/mechanics/04_strategic_cognition.md` §6.6/§6.10 for the
  full corrected derivation) is now fixed. `AdventureGoalScorer.score()`
  (`src/ai/goals/adventure_scorer.py`) normalizes against a new, dedicated
  `_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX = 2.4` module-level constant instead —
  `max(empirical raw_score corpus maximum = 0.7439 across the same 6-run_key corpus,
  theoretical safety floor = 2.4 derived from RECOVER's own real max-urgency ceiling)` rounded up
  to 1 decimal place. `_ADVENTURE_ROUTE_SCORE_MAX` itself stays exactly `2.9`, untouched, and
  continues to serve only the Generalized Bypass gate (`evaluate_project_switch()`) —
  `RegionStabilizationGoalScorer`/`SocialContractGoalScorer` are unaffected (confirmed by direct
  regression tests). A fresh, clean `calibrate_simq.py` run against all 6 named run_keys post-fix
  measured a real, non-forced, evidence-grounded outcome: `route_selected`/`action_executed`/
  `route_family_first_use` each fired exactly once (nonzero) for `hero_guild_routing_seed42_500t`
  only (AGENCY grade `B`, `normalized_score=0.0236`, `event_count=3` — reproduced identically on
  an independent re-run at the same seed, confirming determinism). The other 5 run_keys
  (`simq_routing_test_seed{42,123,456}_500t`, `hero_guild_routing_seed{123,456}_500t`) still
  measured 0 events (`AGENCY: {"grade": "C", "score": 0.0}`, unchanged) — consistent with
  investigation.md Risk #2's own caution that `ResolveBlockerScorer`'s flat `utility=80.0` floor
  and `CombatEngageScorer`'s floor of `40.0` may still structurally dominate even a corrected
  Adventure ceiling's typical output on most ticks in these two danger-heavy calibration worlds.
  This is a real, mixed restoration — not a full flip to nonzero for all 6 run_keys — and is
  reported here as measured, not assumed. `grade_anchors.json`'s AGENCY entry for
  `hero_guild_routing_seed42_500t` was recalibrated to `{"grade": "B", "score": 0.0236}`; the
  other 5 run_keys' AGENCY entries were left at `{"grade": "C", "score": 0.0}`, matching the
  still-correct, still-measured reality for those run_keys. Whether the still-zero outcome on the
  other 5 run_keys is itself archetype-correct (mirroring `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`'s
  precedent) is an open design/product question, explicitly not decided by this ticket — a
  candidate for a future, separately-scoped DA-ruling ticket if desired.
- **Status**: ACTIVE (write-path restored; AGENCY event emission for `simq_routing_test`/
  `hero_guild_routing` now fires for 1 of 6 named run_keys following the tier-5-competition-scale
  fix above; the other 5 remain at zero events, a real and current measurement, not a residual
  gap awaiting further restoration work)

### 2.42 Social-Contract Acceptance No Longer Unconditionally Wins the Project Slot (TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER)
- **Subsystem**: Strategic Cognition / Social Contracts
- **Old Behavior**: `ContractService.accept_contract()` (`src/systems/social_systems/contracts.py`)
  built a `ProjectState`/`ObjectiveState` inline and wrote `current_project_id_set` directly on
  acceptance — an accepted RECRUITMENT or LOAN contract always won the entity's project slot,
  unconditionally overwriting whatever project was active, regardless of that project's own score
  or lock state. This was a confirmed arbiter-bypass site (same defect class as the adventure and
  interruption-bypass sites closed in §2.40/§2.41).
- **New Behavior**: `accept_contract()` now only transitions contract status — it no longer
  constructs project/objective state or writes `current_project_id_set`. A new
  `SocialContractGoalScorer` (`src/ai/goals/social_contract_scorer.py`), registered under a new
  `GoalKind.SOCIAL_CONTRACT` (`src/core/strategic.py`), scans an entity's ACTIVE RECRUITMENT/LOAN
  contracts and produces a tier-5 candidate (`raw_score = clamp(trust*1.0 + urgency*1.0 +
  value*0.9 - risk_weight*0.3, 0.0, 2.9)`). `StrategicIntelligenceSystem`'s tier-5
  winner-construction site (`src/systems/strategic_systems/intelligence.py:1468-1503`) now
  materializes a `SOCIAL_CONTRACT` win into a real `ProjectState` (kind mapped via
  `ContractService.get_project_mapping()`: RECRUITMENT -> COMBAT, LOAN -> SOCIAL) through the same
  `evaluate_project_switch()` arbiter every other candidate competes through — a contract can now
  legitimately lose to a higher-locked existing project. This is the disclosed, explicit point of
  the change, not a regression: it closes the confirmed arbiter-bypass site (see parity ledger
  `STRAT-254`, `docs/parity_ledger/strategic_cognition.yaml`, and `SOC-208`,
  `docs/parity_ledger/social_narrative.yaml`).
- **Rationale**: **Enforced**. Generalizes the same GoalScorer-wrapper pattern already applied to
  adventure routing (§2.35/§2.41) and the interruption-bypass gate (§2.40) to the remaining
  confirmed social-contract arbiter-bypass site — a contract's urgency now has to actually clear
  the same score/retention bar as every other strategic candidate rather than winning by
  construction.
- **Verification**: `tests/unit/strategic/test_social_contract_materialization.py::test_high_lock_current_project_retains_against_low_urgency_contract`,
  `tests/unit/strategic/test_social_contract_materialization.py::test_high_urgency_contract_interrupts_locked_current_project`,
  `tests/unit/social/test_contract_lifecycle.py::test_accept_contract_no_longer_sets_current_project_id_directly`.
- **Status**: ACTIVE

---

### 2.43 Regional-Danger Stabilization No Longer Unconditionally Wins the Project Slot (TCK-20260811-REGION-STABILIZATION-GOAL-SCORER)
- **Subsystem**: Strategic Cognition / Regional Danger
- **Old Behavior**: `EventInterpreter.interpret_regional_danger()` (`src/systems/world_systems/events.py`)
  computed `should_pivot = urgency > profile.interruption_resistance` and, if true, built a
  `ProjectState`/`ObjectiveState` inline (`kind="stabilize"`, a bare string with no matching
  `ProjectKind` member) and wrote `current_project_id_set` directly — an entity always pivoted to
  regional-danger stabilization the instant urgency exceeded its own interruption resistance,
  unconditionally overwriting whatever project was active regardless of that project's own score or
  lock state. This was a confirmed arbiter-bypass site (same defect class as the adventure,
  interruption-bypass, and social-contract sites closed in §2.40/§2.41/§2.42).
- **New Behavior**: `interpret_regional_danger()` now only generates a `danger`-kind `ConcernState`
  — it no longer builds project/objective state or writes `current_project_id_set`. A new
  `RegionStabilizationGoalScorer` (`src/ai/goals/region_stabilization_scorer.py`), registered under
  a new `GoalKind.REGION_STABILIZATION` (`src/core/strategic.py`), resolves the entity's current
  region and produces a tier-5 candidate via the shared `EventInterpreter.compute_danger_urgency()`
  helper (`raw_score = urgency * 2.9`). `StrategicIntelligenceSystem`'s tier-5 winner-construction
  site (`src/systems/strategic_systems/intelligence.py:1505-1539`) materializes a
  `REGION_STABILIZATION` win into a real `ProjectState(kind=ProjectKind.STABILIZE, ...)` (a new,
  real enum member replacing the old bare string) through the same `evaluate_project_switch()`
  arbiter every other candidate competes through — regional danger can now legitimately lose to a
  higher-locked existing project. `profile.interruption_resistance` still governs pivoting, but only
  through the single, unified `retention_margin` mechanism (§2) every other tier-5 candidate already
  goes through; the old direct `should_pivot` urgency-vs-resistance formula is not preserved
  anywhere post-migration. This is the disclosed, explicit point of the change, not a regression: it
  closes the confirmed arbiter-bypass site (see parity ledger `STRAT-255`,
  `docs/parity_ledger/strategic_cognition.yaml`).
- **Separately (not a divergence, a first-time-live disclosure)**: unlike the adventure-route and
  social-contract wrapper migrations (§2.41/§2.42), which wrapped already-live decision paths,
  `interpret_regional_danger()` itself has zero production callers, before or after this migration —
  it exists only for its own concern-generation unit tests. `RegionStabilizationGoalScorer` instead
  re-implements the hazard-threshold/urgency decision to read `state.regions` directly via the
  shared `compute_danger_urgency()` helper, which means **registering this scorer makes
  LEG-RPG-116 (regional-danger-driven stabilization) live-reachable in production for the first time
  ever** — cadence-gated (`SystemCadence.strategic_intelligence`) and work-queue-budgeted
  (`StrategicWorkQueue.build()`), the same throttling every other tier-5 scorer already operates
  under, not "unconditional every tick." See `docs/mechanics/04_strategic_cognition.md` §2a and
  `STRAT-255`'s `support_boundary` field for the full disclosure.
- **Rationale**: **Enforced**. Generalizes the same GoalScorer-wrapper pattern already applied to
  adventure routing (§2.35/§2.41), the interruption-bypass gate (§2.40), and social-contract
  acceptance (§2.42) to the remaining confirmed regional-danger arbiter-bypass site — regional
  danger's urgency now has to actually clear the same score/retention bar as every other strategic
  candidate rather than winning by construction.
- **Verification**: `tests/unit/strategic/test_region_stabilization_materialization.py::test_high_lock_current_project_retains_against_low_urgency_regional_danger`,
  `tests/unit/strategic/test_region_stabilization_materialization.py::test_high_urgency_regional_danger_interrupts_locked_current_project`,
  `tests/unit/strategic/test_event_interpretation.py::TestStrategicPivotOnDanger::test_project_pivot_when_urgency_exceeds_resistance`,
  `tests/unit/strategic/test_event_interpretation.py::TestStrategicPivotOnDanger::test_no_pivot_when_resistance_high`.
- **Status**: ACTIVE

### 2.44 Level 2 Packet-Cache Freshness/Verification Column Co-location (TCK-20260816-KGMCP-P3-PACKET-CACHE-SCHEMA-MIGRATIONS)
- **Subsystem**: Knowledge Gateway MCP / Packet Cache
- **Old Behavior**: No equivalent — this is a new table
  (`retrieval_context_packet_cache_rows`, `tools/retrieval_cache.py`,
  `migration_002_add_level2_tables`), not a modification of prior behavior.
- **New Behavior**: The new table carries `freshness` and `verification` columns on the same row
  as lookup-identity fields (`packet_id`, `normalized_intent`, `query_key_hash`), which
  `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md` §3's
  Non-collapse rule Bullet 1 says a lookup-table row should "never" carry.
- **Rationale**: **Bounded**. The divergence is schema-only and explicitly bounded: no lookup
  function exists on this table yet (this ticket adds no `check_*`/`write_*`-style function,
  guarded by `tests/tools/test_retrieval_cache.py::TestLevel2Migrations::test_no_actual_read_write_functions_added_for_the_new_level2_table`),
  so Bullet 2's function-return-shape rule is not violated by this ticket. The wire contract's own
  `required: [status, freshness, verification, ...]` list
  (`docs/engine/contracts/knowledge_gateway_mcp/knowledge_context_response.schema.json`)
  operationally justifies persisting last-computed values as row state.
- **Verification**: `TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING` (the next ticket in
  this ticket's own sibling sequence) must add a test asserting that whatever lookup function it
  introduces for `retrieval_context_packet_cache_rows` never returns the raw
  `freshness`/`verification` column values off a row without a separate, explicit revalidation
  step first — i.e. Bullet 2 stays enforced procedurally by that ticket's own function design,
  even though Bullet 1's schema-level "never" is knowingly overridden by this ticket's table
  shape.
- **Status**: ACTIVE

### 2.45 Level 2 Lookup Identity Includes Exact `budget_tokens`, Not `budget_class` (TCK-20260816-KGMCP-P3-PACKET-CACHE-READ-WRITE-WIRING)
- **Subsystem**: Knowledge Gateway MCP / Packet Cache
- **Old Behavior**: `docs/engine/contracts/knowledge_gateway_mcp/evidence_cache_identity_contract.md`
  §1 states `budget_class` is "the caller's budget tier (token/latency budget bucket), not the raw
  numeric budget," and names it as the only budget-related field in lookup identity. Level 1's
  `compute_lookup_identity()` (`tools/knowledge_gateway_cache.py:137-154`, unmodified by this
  ticket) follows this literally: it stores only the bucketed `budget_class` (thresholds 500/2000
  tokens), never the raw integer.
- **New Behavior**: Level 2's new, additively-named `compute_context_packet_lookup_identity()`
  (`tools/knowledge_gateway_cache.py`) includes the literal `budget_tokens` integer as a 7th
  lookup-identity field, used both in `packet_id`'s hash input (`PD1`) and in
  `check_context_packet_cache()`'s Python-side disambiguation comparison against stored rows
  (`PD3`).
- **Rationale**: **Bounded**. `assemble_within_budget()`'s real truncation behavior (added by
  `TCK-20260816-KGMCP-P3-PACKET-DEDUP-BUDGET-ENFORCEMENT`) is driven by the literal
  `effective_budget` integer, not by `budget_class`'s coarse bucket — two requests for the same
  query with different `budget_tokens` values that fall in the same bucket (e.g. 600 and 1800, both
  "medium") can produce differently-truncated packets (different `included_statements`/`answer`/
  `budget_returned`/`budget_truncated`/`omitted_statement_count`). Using only `budget_class` at
  Level 2 risks silently serving a packet truncated for one caller's actual budget to a different
  caller who requested a materially different budget in the same bucket — a genuine correctness
  defect specific to a packet-cache layer whose stored payload itself varies continuously with the
  exact budget value, not merely its bucket. §1 predates Level 2's existence and did not anticipate
  a caching layer with this property. Bounded because the divergence is scoped only to Level 2's
  new, additively-named identity function — Level 1's `compute_lookup_identity()` is unmodified,
  and Level 1's own latent exposure to the same class of imprecision (out of this ticket's scope to
  fix there) is untouched.
- **Verification**: `test_identical_repeated_knowledge_context_call_is_a_genuine_level2_cache_hit`
  (AC1) plus
  `tests/tools/test_retrieval_cache.py::TestContextPacketCache::test_level2_lookup_disambiguates_by_budget_tokens_not_just_budget_class`
  — asserts two calls differing only in `budget_tokens` within the same `budget_class` bucket do
  not collide on the same Level 2 row/`packet_id`.
- **Status**: ACTIVE

---

### 2.46 Noise-Fill Terrain Draws Namespaced Under Domain.INIT, Not Domain.WORLD (TCK-20260821-COMPILER-NOISE-FILL)
- **Subsystem**: Worldbuilding / WorldCompiler
- **Old Behavior**: `WorldCompiler.compile()`'s region-painting loop (`src/worldbuilding/compiler.py`)
  only ever performed a single flat-terrain fill per region (`terrain[(x, y)] = r_terrain`). No
  per-tile RNG draw existed in this loop at all, so there was no Domain-namespacing question to
  answer.
- **New Behavior**: A region declaring a populated `terrain_variants` list now gets per-tile
  terrain sampled via `DeterministicRNG.weighted_choice()`, keyed under `Domain.INIT` rather than
  sequenced within `Domain.WORLD`'s existing entity/resource/building draw order (which uses
  `entity_id`/`sub_id` conventions of 0/1 for position, 10-14 for personality/class, ≥100 for
  reroll). The noise-fill draw's `entity_id` is `(region_hash ^ tile_offset) & 0xFFFFFFFF` (a
  string-hash of the region's `id` XORed with a 16-bits-per-axis tile offset) and `sub_id=1`,
  distinct from any existing `Domain.WORLD` key convention.
- **Rationale**: **Bounded**. `DeterministicRNG` is a stateless composite-key hash — each of
  `get_float`/`get_int`/`choice`/`weighted_choice`/`sample` constructs a fresh `random.Random(seed)`
  per call from `(base_seed, domain, tick, entity_id, sub_id)`, with no sequential stream to
  reorder (`src/platform/rng.py:85-108`). Namespacing the new noise-fill draw under a distinct
  `Domain` (`Domain.INIT`) eliminates composite-key collision risk with `Domain.WORLD`'s existing
  draws by construction, rather than requiring careful entity_id/sub_id coordination to avoid
  collision within the same Domain. `Domain.INIT`'s one existing production consumer
  (`Kernel.__init__`'s run-suffix draw, `src/engine/kernel.py:122`,
  `get_int(Domain.INIT, 0, 0, 1000, 9999)`, implicit `sub_id=0`) is structurally isolated from this
  ticket's draws both by call-ordering (`compile()` always finishes and returns before any `Kernel`
  is constructed in every real call path) and by RNG statelessness (each call builds its own
  independent `random.Random` instance, so no shared mutable state exists even if their keys
  happened to coincide). This is a scoping/collision-avoidance choice, not a behavior-correctness
  fix — there was no bug in `Domain.INIT`'s prior single use.
- **Verification**:
  `tests/unit/worldbuilding/test_world_compiler.py::test_domain_world_entity_resource_building_draws_unaffected_by_terrain_variants_declaration`
  — compiles the same spec with `terrain_variants` populated vs. `None` at the same seed and
  asserts every entity/resource node/building position is identical, proving the new `Domain.INIT`
  draw cannot perturb `Domain.WORLD`'s existing draw sequence.
- **Status**: ACTIVE

### 2.47 `MemoryUpdatePhase` Gains Its First Pipeline Call Site (TCK-20260824-CAUSAL-MEMORY-ROUTE-SCORING)
- **Subsystem**: Engine / Cognition
- **Old Behavior**: `MemoryUpdatePhase.run()`/`.apply()` (`src/domains/memory/phase.py`) existed
  and was unit-tested in isolation, but `AuthoritativeApplyPipeline.refine()`
  (`src/engine/pipeline.py`) had zero call sites for it (`TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING`).
  `entity.cognition.memory.causal` could never become non-empty in a real run, so
  `AdventureRouteScorer.score()`'s `memory_adjustment` term (`docs/parity_ledger/strategic_cognition.yaml::STRAT-227`)
  was formula-verified by unit test but not observable end-to-end. `run()`'s trigger-event
  parameter was also a single `trigger_event` dict, unable to represent more than one entity
  triggering a memory update in the same tick.
- **New Behavior**: `AuthoritativeApplyPipeline.refine()` registers a `"memory_update"` phase
  between `actor_validity` and `self_model` (`src/engine/pipeline.py:145-159`), gated by a new
  flag `ENABLE_MEMORY_UPDATE`, calling `MemoryUpdatePhase.apply(state, u, _memory_trigger_events)`.
  `run()`'s signature changed from a single `trigger_event` dict to a `trigger_events` list matched
  by `entity_id`, so multiple entities triggering in the same tick are all updated. `.apply()`
  writes via the typed `EntityUpdate.cognition_bundle_set` -> new `CognitionPatch`
  (`src/core/updates.py`, `src/engine/patches.py`) authoritative-apply path, structurally mirroring
  `SelfModelUpdatePhase.apply()` — it never mutates `state.entities` directly. Trigger events are
  now sourced from a real producer: a new `WorldEventCategory.COMBAT_LOSS` `WorldEvent`, emitted
  unconditionally by `ActionRoutingPhase.route()` whenever a defender survives a damaging ATTACK
  (`src/engine/pipeline_phases/actions.py:169-188`; see `docs/parity_ledger/combat_movement.yaml::COMB-312`),
  threaded through the existing one-tick-lagged `state.recent_world_events` channel.
- **Rationale**: **Bug Fix**. This is a missing apply-path wiring for an existing typed cognition
  subsystem (memory), completing Pattern 2 (Decision/Mutation Separation via Typed Update Records,
  `docs/guidelines/design_patterns.md`) for `cognition_bundle_set` — not a new pattern or a design
  tradeoff. The phase itself defaults `OFF` per DEV-002's established rollout policy for
  Phase-10-era cognition phases (`ENABLE_MEMORY_UPDATE` follows the same convention as
  `ENABLE_SELF_MODEL_COGNITION`, `ENABLE_BELIEF_ASSIMILATION`, etc.) — the default-OFF gating is
  not itself a new divergence, it is DEV-002's policy applied to a new flag. The `COMBAT_LOSS`
  `WorldEvent` producer is **not** flag-gated and is unconditional in every real run, independent
  of `ENABLE_MEMORY_UPDATE`.
- **Verification**: `tests/integration/scenarios/test_causal_memory_route_scoring_e2e.py` (3-tick
  scenario driving the real pipeline end-to-end: `entity.cognition.memory.causal.entries` becomes
  non-empty with `avoid_enemy` advice, and `AdventureRouteScorer.score()` produces the documented
  `-1.0` `memory_adjustment` for `HUNT_WEAK_ENEMY`);
  `tests/unit/actions/test_action_routing_combat_loss_world_event.py` (COMBAT_LOSS producer);
  `tests/integration/domains/memory/test_memory_update_phase_apply_trigger_events.py`
  (`trigger_events` list, multi-entity matching by `entity_id`).
- **Status**: ACTIVE

### 2.48 Clan Succession-on-Death Diverges from Group's Dissolve-on-Death (TCK-20260831-CLAN-STATE-SCHEMA)
- **Subsystem**: Social/Clan
- **Old Behavior**: `Group` (the existing multi-entity coordination unit) unconditionally
  dissolves when its leader dies or deactivates — `GroupSystem.update_groups()`,
  `src/systems/world_systems/groups.py:93-108` (Logic IDs SOC-176/SOC-189), no re-election or
  succession branch exists on leader death.
- **New Behavior**: `ClanState`'s schema is designed to support succession instead of
  dissolution on leader death — `leader_entity_id` is an independently reassignable field, not
  structurally tied to member-removal logic the way Group's dissolution is. This ticket
  (TCK-20260831-CLAN-STATE-SCHEMA) adds only the schema shape; it does not implement any
  succession-execution logic, event, or lifecycle action.
- **Rationale**: **Intentional Gameplay Change**. The brainstorm doc's own stated rationale for
  `dissolved_tick` is explicitly framed around avoiding "cross-generational Clans silently
  break[ing]" (`docs/brainstorm/rpg_expected_schemas.html:617`), implying Clans are meant to be
  multi-generational political entities, unlike Group's small, disposable adventuring parties.
  A `leader_entity_id` that can never be reassigned without dissolving the whole Clan would give
  no signal beyond what `dissolved_tick` alone already provides.
- **Verification**: `tests/unit/domains/faction/test_clan_succession.py` (succession/dissolution
  logic — `test_clan_succession_promotes_highest_sociability_on_leader_death`,
  `test_clan_succession_no_promotion_when_leader_alive`,
  `test_clan_succession_same_tick_death_effective_state`,
  `test_clan_dissolves_when_members_and_assets_both_empty`) and
  `tests/unit/domains/faction/test_clan_state.py::test_clan_state_is_wired_into_authoritative_state`
  (wiring into `AuthoritativeState`/`StateUpdate`/`apply.py`) — landed by
  TCK-20260903-CLAN-LIFECYCLE-SUCCESSION (idea 40/M4), SOC-264. `ClanLifecycleService`
  (`src/systems/social_systems/clan_lifecycle.py`) implements margin-free succession
  (no 0.2 sociability-margin gate, contrast SOC-228) and dual-gated dissolution
  (`member_entity_ids` AND `asset_ids` both empty), wired into the pipeline via
  `ClanLifecyclePhase` (`src/engine/pipeline_phases/clan_lifecycle.py`).
- **Status**: RATIFIED

### 2.49 Post-Spawn `class_id` Mutation via `class_id_set` Diverges from PROG-108's Spawn-Only Framing (TCK-20260831-CLASS-TIER-BRANCHING) — cross-referenced as **DEV-006**
- **Subsystem**: Engine / Progression
- **Old Behavior**: `IdentityComponent.class_id` (`src/core/state.py:482`) was assigned exactly once,
  at world-compile time, by `V2EntityBuilder.identity(class_id=...)` (`src/core/builder.py:176,198`)
  from `spawn_tables.yaml`'s `classtable.v1` entry. `PROG-108`
  (`docs/parity_ledger/progression.yaml`) records this as verified law: "Entity class_id is
  assigned by role from spawn_tables.yaml at world compilation." No apply-path file ever wrote
  `class_id` after spawn — confirmed by a full-repo search across every `*Update`/`*Patch` class.
- **New Behavior**: `IdentityUpdate.class_id_set: Optional[str]` (`src/core/updates.py`) is a new
  last-write-wins field, following the exact shape of `role_set`/`life_stage_set`, that is wired
  into `IdentityPatch.apply()` (`src/engine/patches.py`) — reading `class_id_set` into a local
  `cls_id` var and passing `class_id=cls_id` into the component's final `replace()` call. This
  makes `IdentityPatch.apply()` a real, live, currently-tested post-spawn writer of `class_id`,
  generalized from (but not copying) `EvolutionSystem`'s hardcoded, linear `kind_set` mapping
  (`src/engine/evolution.py::_get_evolved_kind`) — `CLASS_TIER_REGISTRY`
  (`src/core/classes.py`) defines >=2 mutually-exclusive next-tier options per base class
  (`WARRIOR` -> `WARRIOR_CHAMPION` | `WARRIOR_GUARDIAN`; `MAGE` -> `MAGE_ARCHMAGE` |
  `MAGE_STORMWEAVER`), so this is a branch choice, not a single linear chain. A new
  `ClassTierService.apply_bonuses()` (`src/progression/class_tiers.py`) applies each tier's
  `attribute_bonuses` live, recomputed from the durable `class_id` on every
  `SkillScalingService.get_effective_stats()` call — mirroring `BreakthroughService.apply_bonuses()`'s
  exact live-recompute mechanism, not a one-time stored delta, to survive subsequent unrelated
  `stats_dirty` recomputes (see `docs/mechanics/attribute_progression_contract.md` "Derived Stat
  Recalculation Order").
- **Rationale**: **Intentional Gameplay Change**. This is a deliberate new mechanic (mutually-exclusive
  class-tier branching), not a correction or hardening of existing behavior. PROG-108's spawn-time
  claim remains true and its `status` stays `verified` — the new fact (class_id can *also* mutate
  post-spawn via `class_id_set`) is additive, not a falsification; `docs/parity_ledger/progression.yaml`
  PROG-108's `divergence_note` cross-references this entry, and a new `PROG-122` entry records the
  branching mechanism itself.
- **Verification**: `tests/unit/progression/test_class_tiers.py::test_branch_selection_diverges_class_id`
  (two entities, identical starting `class_id="WARRIOR"`/attributes, diverge in `identity.class_id`
  and derived combat stats purely from different `class_id_set` inputs — same "identical starting
  state, diverging input" shape as `test_goblin_evolution`);
  `::test_class_id_set_applies_via_identity_patch` (apply-path wiring, `is_noop()`/`merge()`
  last-write-wins); `::test_tier_bonus_survives_subsequent_stats_dirty_event` (tier bonus is not
  silently wiped by the next unrelated `stats_dirty` event); `tests/integration/combat/test_class_tier_win_rate.py::test_tier_bonus_does_not_decrease_win_rate`
  (a tier's stat bonuses do not decrease average combat win-rate against a fixed opponent roster).
  `tests/unit/entity/test_entity_archetypes.py::test_hero_archetypes_cover_combat_mage_rogue`
  (PROG-108's own `test_path`) is unaffected — it only exercises `WorldCompiler.compile()`, no
  ticks/apply-path, so it cannot observe `class_id_set` regardless.
- **Scope note**: This ticket ships the registry, the typed field, and the apply-path wiring only.
  No live AI/decision producer calls `class_id_set` in production gameplay code yet — a
  fully-wired-but-uninvoked-in-production end state accepted by this project's own precedent
  (`TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION`, `breakthroughs_add`/`traits_add`). That
  "wired but not yet invoked by production code" state does not make this divergence itself
  deferred — the mechanism is active, tested, and callable today.
- **Status**: ACTIVE

---

## 3. Unsupported / Retired Behavior

The following legacy behaviors have been intentionally omitted or retired.

| ID | Feature | Rationale | Status |
| :--- | :--- | :--- | :--- |
| **LEG-RPG-021** | Tactical Geometry Exploits | Strict grid legality is enforced; diagonal "clipping" and pathing exploits are removed. | RETIRED |
| **LEG-RPG-031** | Legacy Guild Intel | Replaced by `StrategicIntelligenceSystem` and `LeadState` models. | RETIRED |
| **LEG-RPG-033** | Generic Building Triggers | Replaced by explicit `InteractionSystem` channeling. | RETIRED |
| **LEG-RPG-054** | Complex Turning Points | Social salience is simplified to salience-weighted life events. | UNSUPPORTED |
| **LEG-RPG-058** | Territory Ownership | Factional territory is handled via regional influence rather than explicit tile ownership. | UNSUPPORTED |
| **LEG-RPG-061** | Legacy XP Rewards | XP is now an atomic `RewardState` part of quest resolution, not direct combat emission. | UNSUPPORTED |
| **LEG-RPG-130** | Luck-Based Crit | Critical hits are currently 100% deterministic or omitted to prioritize substrate stability. | UNSUPPORTED |
| **LEG-RPG-153** | Combat Exhaustion | Simple stamina drain replaces complex exhaustion debuffs. | UNSUPPORTED |
| **LEG-RPG-158** | Backstab Logic | Flanking is handled via geometric bracketing; specific "backstab" facing checks are omitted. | UNSUPPORTED |

> [!NOTE]
> Items marked **UNSUPPORTED** are not currently present in the hardening baseline. They may be restored once the core state machine is certified.

---

## 5. Economy Divergences

### DEV-001 — Faction-Scoped Discount Gating (TCK-20260619-E33D-REP-DISCOUNTS)
- **Subsystem**: Economy / Shop Pricing
- **Original Design Intent**: The ticket pseudocode specified `if faction_id != shop_faction: return base_price` — discounts only applied when the buyer's faction matched the shop's faction.
- **Actual Behavior**: Discount is applied universally based on `entity.social.public_reputation` only. No per-faction gating is performed.
- **Rationale**: **Bounded** — `SocialComponent` has no `faction_rep: Dict[str, float]` field. Adding one is a schema change outside the scope of this ticket. Faction-scoped discounts are deferred to a future ticket.
- **Verification**: `tests/integration/scenarios/test_macro_economy.py::test_reputation_discount_applies`
- **Status**: ACTIVE (faction-gating deferred)

### DEV-002 — Feature Flag Default Policy: All Phase 10 Flags Default to OFF (TCK-20260627-P0A-ADVENTURE-FLAG)
- **Subsystem**: Engine / Feature Rollout
- **Situation**: `FeatureFlagManager` (line 13–24 in `src/domains/optimization/feature_flags.py`) initialises all 10 Phase 10 flags to `FeatureMode.OFF`. The audit (D04 §6.1, D06 F1/F4) raised this as a P0 blocker because balance and behavioural measurements were collected against a simulation with the adventure decision pipeline disabled.
- **Decision**: Keep all 10 flags as `FeatureMode.OFF` by default. The OFF default is an intentional gated-rollout policy enforced by a sentinel test (`test_adventure_routing_defaults_off()` in `tests/integration/scenarios/test_balance_regression.py`).
- **Rationale**: **Stabilized** — Changing the default to `ON` requires re-running `tools/balance_measure.py` to regenerate E12A baseline constants and updating `ATTRITION_CAP`, `ECONOMIC_GOLD_FLOOR`, and `BLOCKER_FREQUENCY_E12A` in `test_balance_regression.py`. That re-baselining is a distinct workstream. The OFF default is not a bug; it is a deliberate rollout gate that prevents unreviewed pipeline changes from silently affecting all simulation runs.
- **Required action for scenario/test authors**: Any scenario or test that exercises a flag-gated pipeline must explicitly enable the flag via `FeatureFlagManager.set_flag_mode()` or the `overrides` constructor argument. See `_build_kernel(enable_routing=True)` in `test_balance_regression.py` as the canonical example.
- **Unblock condition**: After `tools/balance_measure.py` is re-run with a specific flag `ON` and new baseline constants are established and committed, that flag's default may be changed to `ON` and this entry updated or removed.
- **Verification**: `tests/integration/scenarios/test_balance_regression.py::test_adventure_routing_defaults_off`
- **Status**: ACTIVE

### DEV-003 — Two of DEV-002's 10 Phase-10 Flags Flipped ON by Default (TCK-20260824-ROLLOUT-FLAG-DECISIONS)
- **Subsystem**: Engine / Feature Rollout
- **Situation**: `ENABLE_BELIEF_ASSIMILATION` and `ENABLE_SOCIAL_COOPERATION` are 2 of the 10 flags
  DEV-002's default-OFF policy covers. Both were already set `"ON"` in this project's own real,
  regularly-run SimQ corpus profiles (`config/simulation_quality/profiles/sandbox_world.yaml` and
  `urban_political.yaml` for the former; `urban_political.yaml` alone for the latter) at the time
  this ticket reviewed all 8 originally-undecided Phase 10 flags.
- **Decision**: Flip both flags' code default to `FeatureMode.ON`, closing the gap between the code
  default and what every real corpus profile already exercises.
- **Rationale**: **Stabilized** — DEV-002's own stated unblock condition is re-running
  `tools/balance_measure.py` and updating its `ATTRITION_CAP`/`ECONOMIC_GOLD_FLOOR`/
  `BLOCKER_FREQUENCY_E12A` baseline constants. That tool measures adventure-routing/economy/hunger
  metrics specific to the ticket that originally wrote DEV-002 (`TCK-20260627-P0A-ADVENTURE-FLAG`,
  about `ENABLE_ADVENTURE_ROUTING`) — neither metric is in either flipped flag's domain (belief/
  social-cooperation), so re-running it would not produce meaningful new evidence for these two
  flags specifically. **This ticket did not run `tools/balance_measure.py`** — stated plainly, not
  glossed over. Instead, it treats continuous, real SimQ-corpus-profile usage (this project's own
  standing validation mechanism for exactly the social/cognition domain these two flags touch) as
  satisfying DEV-002's underlying intent — real, running, already-proven-safe production usage —
  even though it is not the literal tool DEV-002 names. The other 6 of the 10 flags remain
  `FeatureMode.OFF` under DEV-002's original policy, unaffected by this entry.
- **Verification**: `tests/unit/config/test_phase10_feature_flags.py` (`_DELIBERATE_ON_DEFAULT_FLAGS`
  allowlist, both flags added)
- **Status**: ACTIVE

### DEV-004 — ALLOCATE_AP Action-Router Branch Kept Dormant (TCK-20260824-ALLOCATE-AP-BRANCH-DECISION)
- **Subsystem**: Engine / Progression
- **Situation**: `CoreActions.execute_allocate_ap` (`src/engine/domain/core_actions.py:146-176`) is
  dispatched from `ActionRouter.execute_action` (`src/engine/domain/action_router.py:49-50`) and
  reachable via two live call chains (`SimulationDomainLogic.execute_action` and
  `ActionIntentAdapter.execute`'s router-payload fallback), but no code anywhere in `src/` ever
  constructs an `{"action": "ALLOCATE_AP", ...}` payload — the only such payload constructor in the
  repo is a test fixture (`tests/unit/quest/test_progression_regression.py`). The one real
  gap-resolution pipeline that could drive AP spending (`gaps.py` → `generator.py` →
  `ConversionIntentResolver.resolve`'s `ConversionKind.ALLOCATE_AP` branch,
  `src/domains/progression/resolver.py:82-89`) never calls `ActionRouter` at all — it returns an
  `EntityUpdate` directly (`src/domains/progression/phase.py:73`) — and that whole
  `ProgressionConversionPhase` is gated behind `ENABLE_PROGRESSION_EVOLUTION`, which defaults to
  `FeatureMode.OFF` per DEV-003's standing policy, with an already-filed, not-yet-run follow-up
  (`tickets/todos/TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION.md`).
- **Decision**: Keep `execute_allocate_ap` wired but dormant. No new producer is built by this
  ticket.
  - `resolver.py`'s `ConversionKind.ALLOCATE_AP` branch (`src/domains/progression/resolver.py:82-89`)
    stays a decrement-only, zero-attribute-gain no-op. This is **documented, not fixed** — fixing it
    is a change to the aptitude-multiplier gap resolution pipeline outside this ticket's scope, and
    it is unreachable today regardless of correctness since the whole phase sits behind the
    `FeatureMode.OFF` flag from DEV-003.
  - `AllocateAttributeAction` (`src/actions/attributes.py`) is **deleted** as dead code (zero `src/`
    callers outside its own file and its own test file). It held the only correct PROG-015/PROG-069
    aptitude-multiplier logic in the repo (`src/actions/attributes.py:39-43`). A follow-up ticket
    porting that logic into `core_actions.execute_allocate_ap` and correcting the resulting
    PROG-068/069/015 parity gap is **recommended but not created** by this ticket.
  - **Update (2026-08-30, TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION)**: that follow-up has
    now run a real 4-leg corpus trial (see `docs/architecture/rollout_flag_decisions_m1.md` §
    "ENABLE_PROGRESSION_EVOLUTION — Validation Trial Result") — no longer "not-yet-run" as this
    entry originally described it. It confirms the `resolver.py` `ALLOCATE_AP` branch is unreachable
    today for two independent reasons, not one: the flag stays OFF (unchanged), and separately its
    only trigger path (a ledger XP entry) has no live producer anywhere in `src/`
    (`RewardLedgerService` has zero callers) — a diagnostic replay showed 100% of sampled decisions
    converging on `SAVE_FOR_LATER`. The trial also surfaced a new, disclosed defect independent of
    this dormancy question: flipping the flag ON deterministically crashes
    `CanonicalStateHasher.get_hash()` (`property_updates["last_progression_decision"]` stores a
    non-JSON-serializable raw `ProgressionDecisionResult`), a concrete blocking prerequisite for any
    future flip-ON decision, on top of the reward-ledger gap. This decision (keep dormant) and the
    flag's default are unchanged by this update.
- **Rationale**: **Bounded** — building a real producer requires either flipping
  `ENABLE_PROGRESSION_EVOLUTION` ON (which duplicates the scope/evidence-gathering job of the
  already-filed `TCK-20260826-PROGRESSION-EVOLUTION-FLAG-VALIDATION`, per DEV-003's own standing
  "defer, don't wire yet, wait for real evidence" policy) or building an entirely new AI/goal
  producer (new-feature scope beyond a decide-the-fate chore ticket). Cites `SUB-376`
  (`docs/parity_ledger/substrate.yaml`) and `ENTITY-008` (`docs/event_ledger/entity.yaml`) as the
  prior investigation that first established this exact reachability finding — this entry ratifies,
  not re-derives, their conclusion.
- **Verification**: `tests/unit/quest/test_progression_regression.py::test_execute_allocate_ap_silently_no_ops_for_unhandled_attribute`
  (documents the live-path's current buggy-but-decided-dormant behavior) and
  `tests/integration/progression/test_allocate_ap_dormancy.py::test_allocate_ap_unreachable_via_real_kernel_tick`
  (proves zero `attribute_changed` events are attributable to either path in a real tick today).
- **Status**: ACTIVE

### DEV-005 — Wounds Are Permanent; heal_wound()/get_diagnosis_quality() Removed (TCK-20260824-WOUND-HEALING-DECISION)
- **Subsystem**: Engine / Combat
- **Situation**: `WoundService.heal_wound()` (`src/engine/rpg_depth.py`, deleted by this ticket) had
  zero `src/` callers — its only 5 references were 4 unit tests in
  `tests/unit/core/test_rpg_depth.py` that directly exercised the dead function itself.
  `MedicalService.get_diagnosis_quality()` (`src/engine/rpg_depth.py`, also deleted) had zero
  callers anywhere, including tests. The only production constructor of `WoundUpdate`
  (`CombatResolutionSystem._get_wound_infliction()`, `src/engine/combat.py:605-617`) never
  populates `wounds_heal` or `scars_add` — confirmed zero production producers for wound healing
  and scar formation, independent of `ENABLE_COMBAT_ENGAGEMENT`'s gate state, by both a full-repo
  grep of `WoundUpdate(` constructors (`src/` has exactly one, and it never passes `wounds_heal`/
  `scars_add`) and a real, non-mocked `Kernel.tick_once()` integration test
  (`tests/integration/combat/test_wound_healing_permanence.py::test_wound_healed_and_scar_gained_have_zero_production_producers`)
  that reads authoritative state directly across a deterministic 40-tick run: a real wound is
  inflicted at tick 9, and across the whole run no wound ever transitions `healed: False -> True`
  and no `ScarState` is ever added. `MedicalService.get_diagnosis_quality()`'s only plausible
  consumer, by name/docstring ("diagnosis accuracy", "healing quality"), was a hypothetical
  WIS-gated heal-success roll feeding `heal_wound()` — it is an unfinished half of the same
  never-wired healing pipeline, not a separately-dead subsystem.
  - **Note on how this was verified**: this ticket's Step 4 was originally planned to prove the
    above via `wound_sustained`/`wound_healed`/`scar_gained` *events*
    (`src/observability/event_extractor.py`), but building that test surfaced a separate,
    independently-discovered bug — `event_extractor.py`'s wound/scar diff blocks are
    `isinstance(x, list)`-gated, while the real apply path always commits wounds/scars as tuples,
    so none of the three events currently fire through any real `Kernel.tick_once()` run,
    regardless of producer existence. That bug is unrelated to the healing-permanence decision (it
    affects `wound_sustained` too, which does have a real producer) and is tracked separately by
    `TCK-20260829-HOTFIX-WOUND-SCAR-EVENT-EXTRACTOR-TUPLE-BLIND`. Step 4 was re-scoped to prove
    zero `wounds_heal`/`scars_add` producers at the authoritative-state level instead — reading
    `kernel.state.entities[...].combat.wounds`/`.scars` directly — which does not depend on that
    separate bug being fixed first.
- **Decision**: Wounds are declared permanent. No healing trigger is built. Both
  `heal_wound()` and `get_diagnosis_quality()` (plus the now-empty `MedicalService` class) are
  **deleted**, not annotated dormant — following the `DEV-004` precedent of deletion for
  zero-caller dead code (`AllocateAttributeAction`). Their 4 dependent unit tests
  (`TestScarPermanence`'s 3 tests, `TestEffectiveStats::test_effective_stats_with_scars`) are
  rewritten to hand-construct the `WoundState`→`ScarState` transition inline, preserving their
  coverage of `WoundService.get_scar_stat_penalties()` and `SkillScalingService.get_effective_stats()`
  with scars. Scar formation is deferred to a separate, later mechanic tracked by
  `TCK-20260824-TACTICAL-WOUND-SCAR-WIRING` (not yet implemented as of this entry — that ticket's
  current scope only reads existing `ScarState` data, it does not itself build a scar-formation
  producer; flagged for the ticket owner, not a blocker for this decision).
  - **Update (2026-08-29, TCK-20260824-TACTICAL-WOUND-SCAR-WIRING)**: that ticket has now landed,
    confirming the prediction above — it wires `WoundService.get_wound_stat_penalties()`/
    `get_scar_stat_penalties()` into `TacticalDecisionSystem` (`src/engine/tactical.py`) as three
    new read-only decision signals, and still does not construct any `ScarState` or populate
    `WoundUpdate.scars_add`; scar formation remains a zero-producer follow-up, unchanged by this
    ticket. See `docs/mechanics/02_combat_laws.md` Section 5 for the documented tactical behavior.
- **Rationale**: **Bug Fix** / dead-code removal. `heal_wound()`'s and `get_diagnosis_quality()`'s
  zero-caller status (confirmed by full-repo search) matches the same evidentiary bar `DEV-004`
  used for `AllocateAttributeAction`'s deletion — no live or planned call site references either
  function today, and no test beyond the 4 rewritten fixture-builders exercised them.
- **Verification**: `tests/unit/core/test_rpg_depth.py::TestScarPermanence` (3 tests, rewritten),
  `::TestEffectiveStats::test_effective_stats_with_scars` (rewritten),
  `::TestSkillScaling::test_wound_heal_through_apply` (unchanged — apply-path consumer regression
  guard, proves `WoundUpdate.wounds_heal` plumbing still works even though nothing produces it);
  `tests/integration/combat/test_wound_healing_permanence.py::test_wound_healed_and_scar_gained_have_zero_production_producers`
  (proves, via a real `Kernel.tick_once()` run reading authoritative state directly, that a wound
  is genuinely inflicted while `healed` never flips and no `ScarState` is ever added, in the same
  run). See `docs/parity_ledger/combat_movement.yaml::COMB-296` and
  `docs/event_ledger/entity.yaml::ENTITY-018` for the corrected reachability record (`wound_healed`/
  `scar_gained` scope only — `wound_sustained`'s separate event-layer bug is owned by
  `TCK-20260829-HOTFIX-WOUND-SCAR-EVENT-EXTRACTOR-TUPLE-BLIND`, not corrected here).
- **Status**: ACTIVE

### DEV-007 — Teaching Gated on Trust, Not Gold: TRAIN_COST Removed Entirely (TCK-20260831-TRUST-GATED-TEACHING)
- **Subsystem**: Economy / Social
- **Situation**: `CoreActions.execute_train()` (`src/engine/domain/core_actions.py`) was a
  single-party action with no teacher/target concept: it unconditionally built a
  `ResourceTransferIntent(source_id="CLASS_HALL", source_kind="TOWN_SERVICE", gold_delta=-50, ...)`
  alongside a `recipes_learned` grant nested in that intent's `identity_upd`. That 50-gold
  `TRAIN_COST` was never actually an enforced affordability gate:
  `ResourceTransactionResolver.resolve()`'s `TOWN_SERVICE` branch checks
  `target_inventory.gold < intent.gold_cost`, and `execute_train()`'s intent never set
  `gold_cost` (default `0`), so the check was always `gold < 0` = `False` — the transaction was
  always accepted regardless of gold balance; gold was merely deducted-and-floored-at-0 as a
  side effect. `CLASS_HALL` is also an untracked abstract sink (no `CLASS_HALL`-keyed balance
  exists anywhere in `AuthoritativeState`), so removing this leg does not break any tracked-object
  source/sink pairing under Mechanics Bible Ch.3 §1 (Atomic Conservation Law).
- **Decision**: `execute_train()` becomes a two-party action (`entity` = teacher,
  `payload["target_id"]` = student), gated entirely on trust via a new
  `ContractKind.TEACH` routed through `SocialAppraisalSystem.appraise_contract()`'s existing
  shared hard-cancel prelude (`trust_score < 0.2` or `bond.sentiment < -0.8` — the same threshold
  RECRUITMENT/TEAM_UP/TRADE already use, unmodified). The student (target) appraises the teacher
  (entity), mirroring `execute_recruit`/`execute_team_up`/`execute_trade`'s existing
  target-appraises-offer convention. The 50-gold `TRAIN_COST` and its `ResourceTransferIntent`
  are removed entirely — trust **replaces** gold, it does not gate alongside it. On acceptance,
  `IdentityUpdate(recipes_learned=[skill_id])` is set directly on the target's `EntityUpdate`
  (mirroring `execute_allocate_ap`'s existing direct-assignment pattern), not nested in a
  `ResourceTransferIntent`. The orphaned, unwired duplicate `ClassHallAction.train()`
  (`src/town/class_hall.py`) — which does perform a real gold-affordability check but has no
  caller anywhere in `src/` — is explicitly left untouched; reconciling the two is a separate,
  future architectural cleanup, not required by any acceptance criterion here.
  **Addendum (2026-09-02, TCK-20260902-CLASSHALL-DEAD-CODE)**: this deferred cleanup has now
  landed — `src/town/class_hall.py` and its dedicated test (`test_class_hall_training` in
  `tests/unit/world/test_recovery_class_hall.py`) were deleted after a re-confirmed zero-caller
  grep across `src/`, `tests/`, and `tools/`. No further reconciliation is outstanding.
- **Rationale**: **Intentional Gameplay Change**. The originating design source
  (`docs/brainstorm/rpg_feature_atlas.html`, idea 6, "Build teaching on trust, not new state")
  explicitly frames this as trust gating "instead of gold," and the pre-existing gold check
  provided no real economic enforcement to preserve (see Situation above) — removing it trades a
  cosmetic-only gold deduction for a real, previously-absent social gate.
- **Verification**: `tests/unit/social/test_teach.py::test_teach_no_gold_leg_regardless_of_gold_balance`
  (proves teaching succeeds with `gold=0` on both parties and emits no `ResourceTransferIntent`),
  `::test_teach_refused_below_trust_hard_cancel_threshold` (proves the trust gate itself),
  `tests/unit/social/test_appraisal_logic.py::test_teach_kind_appraisal_accepts_once_prelude_passes`,
  `tests/unit/resource/test_resource_v2_boundary.py::test_class_hall_train_refactor` (full-pipeline
  regression, updated for the two-party/no-gold shape).
- **Status**: ACTIVE

---
*Last updated: 2026-09-02 (DEV-007 addendum, TCK-20260902-CLASSHALL-DEAD-CODE — deferred
`ClassHallAction.train()` cleanup landed).*
