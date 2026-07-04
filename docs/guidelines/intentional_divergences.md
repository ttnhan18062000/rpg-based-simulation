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
| **World Assembly** | Service Assembly | **Stabilized** | DEFERRED |
| **World / Environment** | Hazard-Kind Faction Endurance | **Bug Fix** | RATIFIED |
| **World / Authoring** | Worldtemplate.v1 Schema Removal | **Unified** | RATIFIED |
| **Engine / Observability** | Kernel Tick-Alignment Fix | **Bug Fix** | RATIFIED |
| **Worldbuilding / Information** | Single-Fire Compile-Time-Seeded Response | **Bounded** | RATIFIED |
| **Engine / Cognition-Information** | `information_belief` Pipeline-Wiring Merge Fix | **Bug Fix** | RATIFIED |
| **Engine / Cognition** | `self_model_bundle_set` Durable Materialization (`SelfModelPatch`) | **Bug Fix** | RATIFIED |

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
- **New Behavior**: Deterministic priority chain: `Lowest HP` > `Closest Distance` > `Lowest Entity ID`.
- **Rationale**: **Contract Hardening**. Prevents target oscillation and improves AI effectiveness in focused firing.
- **Verification**: `tests/parity/test_tactical_parity.py`

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
- **Verification**: `tests/unit/optimization/test_component_patches.py` (6 new `SelfModelPatch`
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

---
*Last updated: 2026-06-27 (DEV-002 feature flag default policy, TCK-20260627-P0A-ADVENTURE-FLAG).*
