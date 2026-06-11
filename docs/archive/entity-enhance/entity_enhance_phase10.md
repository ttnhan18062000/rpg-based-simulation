---
status: archive
authority: P2
audience: historical
layer: core
original_date: unknown
---

# Phase 10 — Optimization / Scaling / Rollout Hardening

Phase 1:

```text
world exposes options
```

Phase 2:

```text
entity understands itself
```

Phase 3:

```text
entity chooses adventure route family
```

Phase 4:

```text
entity judges combat engagement
```

Phase 5:

```text
entity handles uncertain information
```

Phase 6:

```text
entity converts reward into growth
```

Phase 7:

```text
entity uses cooperation as life strategy
```

Phase 8:

```text
entity actions reshape the world
```

Phase 9:

```text
long-run campaigns prove coherent life arcs
```

Phase 10:

```text
make the whole enhanced system safe, deterministic, performant, configurable, and releasable
```

Phase 10 is not about adding new intelligence.

It is about preventing this failure:

```text
The simulation becomes smarter,
but too slow, too memory-heavy, too hard to debug,
or too risky to enable by default.
```

The uploaded test export already includes many stability/performance/certification tests: long-run stability, determinism parity, arena stress, envelope violations, observability parity, API/websocket health, and release gate checks. Phase 10 should not duplicate those. It should add **feature-specific scaling and rollout gates for the new phases working together**.

---

# Phase 10 goal

Phase 10 answers:

```text
Can the enhanced entity/world/cognition stack run at scale
without breaking determinism, memory, tick budget, observability, or existing behavior?
```

It must prove:

```text
feature flags work
new phases are budgeted
dirty-entity updates are bounded
provider calls are capped
trace volume is bounded
memory growth is bounded
caches are invalidated correctly
determinism remains stable
old behavior can be restored
```

---

# Phase 10 success definition

Phase 10 is successful when you can run:

```text
baseline engine
new logic disabled

then

enhanced engine
selected phases enabled

then

full enhanced stack enabled
```

and get a report like:

```yaml
phase10_rollout_report:
  baseline:
    avg_tick_ms: 4.1
    p95_tick_ms: 8.9
    rss_mb: 180
    deterministic: true

  enhanced_selected:
    enabled_phases:
      - phase1_world_options
      - phase2_self_model
      - phase3_adventure_decision
    avg_tick_ms: 5.4
    p95_tick_ms: 11.2
    rss_mb: 193
    deterministic: true

  enhanced_full:
    enabled_phases:
      - phase1_world_options
      - phase2_self_model
      - phase3_adventure_decision
      - phase4_combat_engagement
      - phase5_information_belief
      - phase6_progression
      - phase7_cooperation
      - phase8_world_emergence
      - phase9_life_arc_campaigns
    avg_tick_ms: 7.8
    p95_tick_ms: 16.5
    rss_mb: 225
    deterministic: true

  verdict:
    rollout_safe_for_profile_class_b: true
```

The important proof:

```text
The new intelligence is bounded.
```

---

# Task 1 — Add Phase 10 coverage audit

## Description

Avoid duplicating existing performance/certification tests.

Existing uploaded tests already cover:

```text
long-run pure stability
long-run runtime stability
determinism parity
arena 50v50 stress
envelope violations
observability parity
API live health/status/websocket
release gate validation
```

Phase 10 should cover:

```text
combined overhead of phases 1-9
feature flag rollout behavior
phase budget enforcement
provider call limits
trace/event volume limits
cache invalidation correctness
semantic/performance trade-off reports
safe fallback when budget is exceeded
```

## Proposed document

```text
docs/test_coverage/phase10_optimization_scaling_coverage.md
```

## Checklist

- [x] Existing certification/performance tests are listed.
- [x] Existing observability parity tests are listed.
- [x] Phase 10 scope is defined as combined enhanced-system hardening.
- [x] No test duplicates raw long-run stability.
- [x] No test duplicates API/websocket behavior.
- [x] No test duplicates arena stress.
- [x] New tests focus on feature-budget and rollout safety.

---

# Task 2 — Define feature flag matrix

## Description

Each major enhancement must be independently enabled/disabled.

Do not ship the entire enhanced logic as one huge switch.

## Proposed flags

```text
ENABLE_WORLD_CAPABILITY_LAYER
ENABLE_SELF_MODEL
ENABLE_ADVENTURE_DECISION
ENABLE_COMBAT_ENGAGEMENT
ENABLE_INFORMATION_BELIEF
ENABLE_PROGRESSION_CONVERSION
ENABLE_COOPERATION
ENABLE_WORLD_EMERGENCE
ENABLE_LIFE_ARC_CAMPAIGNS
ENABLE_ENHANCED_TRACE_EVENTS
```

## Flag modes

```text
OFF
SHADOW
ON
STRICT
```

Meaning:

| Mode     | Meaning                                                 |
| -------- | ------------------------------------------------------- |
| `OFF`    | feature does not run                                    |
| `SHADOW` | feature computes result but does not affect state       |
| `ON`     | feature affects state normally                          |
| `STRICT` | feature affects state and fails on invalid trace/budget |

## Checklist

- [x] Each phase has independent flag.
- [x] `OFF` preserves old behavior.
- [x] `SHADOW` computes diagnostics only.
- [x] `ON` enables behavior.
- [x] `STRICT` enables behavior plus hard validation.
- [x] Flags are deterministic.
- [x] Flags are included in run manifest/report.
- [x] Tests verify each flag can be toggled independently.

## TDD tests

```text
tests/unit/config/test_phase10_feature_flags.py
```

Test cases:

```text
test_all_enhancement_flags_default_to_off_or_shadow
test_feature_flag_off_skips_phase
test_feature_flag_shadow_emits_trace_without_state_mutation
test_feature_flag_on_allows_state_update
test_feature_flag_matrix_is_serialized_in_run_manifest
```

---

# Task 3 — Add phase budget manager

## Description

Each enhanced phase needs a budget.

Without this, one phase can starve the engine.

## Budget types

```text
max_entities_per_tick
max_provider_calls_per_tick
max_options_per_entity
max_trace_events_per_tick
max_phase_ms_per_tick
max_memory_entries_per_entity
max_cache_size
```

## Proposed model

```python
@dataclass(frozen=True)
class PhaseBudget:
    phase_name: str
    max_ms_per_tick: float
    max_entities_per_tick: int
    max_provider_calls_per_tick: int
    max_results_per_entity: int
    max_trace_events_per_tick: int
    max_memory_entries_per_entity: int
```

## Budget result

```python
@dataclass(frozen=True)
class PhaseBudgetResult:
    allowed: bool
    skipped_reason: str | None = None
    consumed_ms: float = 0.0
    consumed_entities: int = 0
    consumed_provider_calls: int = 0
    consumed_trace_events: int = 0
```

## Checklist

- [x] Each enhanced phase has a registered budget.
- [x] Budget is profile-dependent.
- [x] Budget can skip remaining entities.
- [x] Budget skip is recorded honestly.
- [x] Budget skip does not corrupt state.
- [x] Budget exhaustion can degrade behavior gracefully.
- [x] Budget manager is deterministic.
- [x] Budget report is emitted.

## TDD tests

```text
tests/unit/perf/test_phase10_phase_budget_manager.py
```

Test cases:

```text
test_budget_allows_phase_when_under_limit
test_budget_skips_phase_when_ms_limit_exceeded
test_budget_caps_entities_processed
test_budget_caps_provider_calls
test_budget_exhaustion_records_honest_reason
test_budget_skip_does_not_mutate_state
```

---

# Task 4 — Add dirty-entity / dirty-region scheduler

## Description

New logic must not run for every entity every tick.

Use dirty scheduling.

## Dirty entity triggers

```text
hp_changed
stamina_changed
inventory_changed
equipment_changed
knowledge_changed
new_opportunity_seen
project_blocked
reward_received
combat_event_received
cooperation_event_received
```

## Dirty region triggers

```text
resource_depleted
death_cluster
camp_changed
quest_pressure_changed
service_pressure_changed
rumor_seed_created
```

## Proposed service

```python
class DirtyWorkScheduler:
    def mark_entity_dirty(self, entity_id: int, reason: str) -> None: ...
    def mark_region_dirty(self, region_id: str, reason: str) -> None: ...
    def next_entities(self, phase_name: str, budget: PhaseBudget) -> tuple[int, ...]: ...
    def next_regions(self, phase_name: str, budget: PhaseBudget) -> tuple[str, ...]: ...
```

## Checklist

- [x] Dirty reasons are canonical constants.
- [x] Duplicate dirty marks are coalesced.
- [x] Scheduler respects phase budget.
- [x] Scheduler preserves deterministic ordering.
- [x] Clean entities are skipped.
- [x] Dirty reasons appear in trace/perf report.
- [x] Dirty state does not grow unbounded.
- [x] Scheduler can clear processed entries safely.

## TDD tests

```text
tests/unit/perf/test_phase10_dirty_work_scheduler.py
```

Test cases:

```text
test_dirty_entity_mark_is_recorded
test_duplicate_dirty_mark_is_coalesced
test_scheduler_returns_deterministic_order
test_scheduler_respects_entity_budget
test_clean_entities_are_not_returned
test_processed_dirty_entries_are_cleared
test_dirty_reason_is_preserved_in_report
```

---

# Task 5 — Add provider call budget and scoped query enforcement

## Description

Phase 1 introduced providers.

By Phase 10, every provider call must be scoped and budgeted.

Forbidden pattern:

```python
get_all_affordances(entity, world)
```

Required pattern:

```python
get_affordances(entity, context, budget)
```

## Provider budget metrics

```text
provider_calls_total
provider_calls_by_kind
results_returned_total
results_returned_by_kind
max_results_returned
global_scan_attempts
budget_skips
```

## Checklist

- [x] Every provider accepts context and budget.
- [x] Provider result count is capped.
- [x] Provider call count is capped.
- [x] Full-world scan requires explicit debug flag.
- [x] Global scan attempt is recorded as warning/error.
- [x] Provider call metrics are included in report.
- [x] Provider output ordering is deterministic.
- [x] Provider cache is invalidated by dirty events.

## TDD tests

```text
tests/unit/world/providers/test_phase10_provider_budget_enforcement.py
```

Test cases:

```text
test_provider_requires_scoped_context
test_provider_caps_results
test_provider_budget_exhaustion_returns_partial_result_with_reason
test_global_scan_attempt_is_rejected_without_debug_flag
test_provider_output_order_is_deterministic
```

---

# Task 6 — Add cache strategy and invalidation tests

## Description

Optimization will need caches.

But stale caches are dangerous.

Cache only stable or scoped data:

```text
registry lookups
nearest service index
region resource index
known opportunity candidates
route family definitions
static item/recipe definitions
```

Do not cache:

```text
current HP
current inventory truth
current gold truth
current combat target status
current resource node charges without invalidation
```

## Proposed cache types

```text
StaticDefinitionCache
SpatialIndexCache
RegionResourceIndex
ServiceLocationIndex
OpportunityCandidateCache
ProviderResultCache
```

## Invalidation triggers

```text
entity_moved
resource_depleted
shop_stock_changed
service_unavailable
region_pressure_changed
knowledge_changed
inventory_changed
equipment_changed
```

## Checklist

- [x] Static registries cache safely.
- [x] Dynamic provider results have TTL or dirty invalidation.
- [x] Resource cache invalidates on depletion/respawn.
- [x] Shop cache invalidates on stock change.
- [x] Service cache invalidates on availability change.
- [x] Region pressure cache invalidates on pressure update.
- [x] Cache keys include enough context.
- [x] Cache sizes are bounded.
- [x] Cache output deterministic.

## TDD tests

```text
tests/unit/perf/test_phase10_cache_invalidation.py
```

Test cases:

```text
test_resource_cache_invalidates_on_node_depletion
test_shop_cache_invalidates_on_stock_change
test_service_cache_invalidates_on_service_unavailable
test_region_cache_invalidates_on_pressure_change
test_provider_cache_key_includes_query_context
test_cache_size_is_bounded
test_stale_cache_does_not_recommend_depleted_resource
```

---

# Task 7 — Add trace/event volume governor

## Description

The new phases add many trace events.

If uncontrolled, observability will become a performance problem.

## Trace categories

```text
self_model
adventure_decision
combat_engagement
information_belief
progression
cooperation
world_emergence
campaign_semantic
```

## Controls

```text
max_events_per_tick
max_events_per_entity_per_window
event_sampling_for_low_severity
always_keep_forbidden_behavior_events
always_keep_hard_law_events
summarize_repeated_events
```

## Checklist

- [x] Trace events have category/severity.
- [x] Low-severity repeated events can be summarized.
- [x] Critical events are never dropped.
- [x] Trace volume is bounded.
- [x] Trace governor reports dropped/summarized counts.
- [x] Trace governor does not affect authoritative state.
- [x] Observability parity remains intact.
- [x] Scenario scorecards still receive required evidence events.

## TDD tests

```text
tests/unit/observability/test_phase10_trace_volume_governor.py
```

Test cases:

```text
test_trace_governor_caps_low_severity_events
test_trace_governor_keeps_hard_law_events
test_trace_governor_summarizes_repeated_events
test_trace_governor_reports_dropped_counts
test_trace_governor_does_not_change_state_hash
test_required_scenario_evidence_events_are_not_dropped
```

---

# Task 8 — Add memory/capacity hard limits

## Description

New aspects can grow without bound:

```text
knowledge facts
unknowns
opponent models
source trust records
reward ledger
cooperation memories
life-arc traces
rumor memories
```

Each needs a bounded capacity policy.

## Capacity policies

```text
drop_low_salience
merge_similar
summarize_old
decay_to_neutral
archive_to_trace_only
keep_high_salience
```

## Required caps

```text
max_knowledge_facts_per_entity
max_unknowns_per_entity
max_opponent_models_per_entity
max_source_trust_entries_per_entity
max_reward_ledger_entries_per_entity
max_cooperation_memories_per_entity
max_life_trace_events_per_entity
```

## Checklist

- [x] Each new memory-like structure has a cap.
- [x] Eviction policy is deterministic.
- [x] High-salience records are preserved.
- [x] Low-salience records are evicted first.
- [x] Eviction emits trace summary.
- [x] Capacity overflow does not crash.
- [x] Memory cap included in profile.
- [x] Tests verify bounded growth.

## TDD tests

```text
tests/unit/perf/test_phase10_memory_capacity_limits.py
```

Test cases:

```text
test_knowledge_facts_are_capped
test_opponent_models_are_capped
test_reward_ledger_is_capped
test_cooperation_memory_is_capped
test_high_salience_memory_survives_eviction
test_low_salience_memory_evicted_first
test_capacity_overflow_records_trace_summary
```

---

# Task 9 — Add determinism parity suite for enhanced phases

## Description

Existing tests already check determinism/observability parity.

Phase 10 needs a focused suite:

```text
new phases ON/OFF/SHADOW
same seed
same feature set
same final hash
same semantic report
```

## Test matrix

```text
baseline OFF
phase1 only
phase1+2+3
phase1+2+3+4
phase1+2+3+4+5+6+7+8
full stack shadow
full stack on
```

## Checklist

- [x] Same seed produces same final hash.
- [x] Same seed produces same semantic scorecard.
- [x] SHADOW mode does not change authoritative hash.
- [x] ON mode can change behavior, but deterministic across repeated runs.
- [x] Feature flags are part of manifest.
- [x] Provider ordering is deterministic.
- [x] Cache ordering is deterministic.
- [x] Budget skips are deterministic.

## TDD tests

```text
tests/certification/test_phase10_enhanced_determinism_parity.py
```

Test cases:

```text
test_shadow_mode_preserves_baseline_hash
test_full_stack_on_is_deterministic_across_runs
test_provider_budget_skips_are_deterministic
test_cache_enabled_and_disabled_have_same_authoritative_result_when_expected
test_semantic_scorecard_deterministic_for_same_seed
```

---

# Task 10 — Add rollout profile matrix

## Description

Different hardware classes should enable different feature sets.

Do not assume full stack is safe everywhere.

## Example profiles

```yaml
profile_class_a:
  enabled:
    - phase1_world_options
    - phase2_self_model
  shadow:
    - phase3_adventure_decision
  disabled:
    - phase8_world_emergence
    - phase9_life_arc_campaigns

profile_class_b:
  enabled:
    - phase1_world_options
    - phase2_self_model
    - phase3_adventure_decision
    - phase4_combat_engagement
    - phase5_information_belief
    - phase6_progression
  shadow:
    - phase7_cooperation
    - phase8_world_emergence

profile_class_c:
  enabled:
    - full_stack
```

## Checklist

- [x] Profiles define enabled/shadow/disabled phases.
- [x] Profiles define budgets per phase.
- [x] Profiles define memory caps.
- [x] Profiles define trace limits.
- [x] Profile is stored in run manifest.
- [x] Invalid profile fails fast.
- [x] Profile can be overridden for tests.

## TDD tests

```text
tests/unit/config/test_phase10_rollout_profiles.py
```

Test cases:

```text
test_profile_class_a_enables_only_low_cost_features
test_profile_class_b_enables_mid_stack_features
test_profile_class_c_can_enable_full_stack
test_invalid_phase_in_profile_fails_fast
test_rollout_profile_serialized_in_manifest
```

---

# Task 11 — Add graceful degradation behavior

## Description

When budget is exceeded, the engine should degrade gracefully.

Not crash.

Not silently ignore.

## Degradation examples

```text
skip low-priority self-model updates
reduce provider result count
delay world emergence phase
switch detailed traces to summary mode
disable expensive cooperation candidate search
fallback to existing tactical behavior
fallback to current strategic goal scorer
```

## Degradation levels

```text
NORMAL
CONSTRAINED
DEGRADED
CRITICAL
```

These already appear in existing observability/status patterns, so Phase 10 should reuse the concept instead of inventing a new health state.

## Checklist

- [x] Budget pressure can enter constrained mode.
- [x] Constrained mode reduces optional evaluations.
- [x] Degraded mode skips expensive phases.
- [x] Critical mode disables enhanced logic except hard-law safety.
- [x] Degradation is recorded honestly.
- [x] Degradation does not corrupt state.
- [x] Recovery from degradation is possible.
- [x] Scenario scorecard records degradation.

## TDD tests

```text
tests/integration/perf/test_phase10_graceful_degradation.py
```

Test cases:

```text
test_budget_pressure_enters_constrained_mode
test_constrained_mode_reduces_provider_results
test_degraded_mode_skips_world_emergence
test_critical_mode_disables_optional_enhanced_phases
test_degradation_reason_recorded_in_report
test_recovery_from_degraded_to_normal_when_pressure_drops
```

---

# Task 12 — Add integrated performance scenarios

## Description

These are not generic performance tests.

They specifically test the combined overhead of phases 1-9.

## Scenario 10.1 — Small full-stack profile

```text
30 entities
1000 ticks
phases 1-8 ON
phase 9 report generation after run
```

Expected:

```text
within class B budget
no unbounded memory growth
route diversity report generated
```

---

## Scenario 10.2 — Medium selected-stack profile

```text
100 entities
2000 ticks
phases 1-6 ON
phases 7-8 SHADOW
```

Expected:

```text
shadow events generated
authoritative state affected only by ON phases
budget respected
```

---

## Scenario 10.3 — Large conservative profile

```text
500 entities
1000 ticks
phases 1-3 ON
others OFF
```

Expected:

```text
core route decision system remains affordable
no provider explosion
```

---

## Scenario 10.4 — Event-heavy world emergence

```text
100 entities
1000 recent events
dirty regions only
phase8 ON
```

Expected:

```text
bounded event window
dirty region processing only
quest/rumor seed caps respected
```

---

## Scenario 10.5 — Cooperation candidate explosion guard

```text
200 entities in town
many possible allies
phase7 ON
```

Expected:

```text
candidate provider caps results
no all-pairs scan
budget skip recorded if needed
```

## Checklist

- [x] Scenario 10.1 executes inside budget thresholds.
- [x] Scenario 10.2 maps shadows to non-authoritative logic.
- [x] Scenario 10.3 caps provider counts for large footprints.
- [x] Scenario 10.4 limits the emergence search space.
- [x] Scenario 10.5 prevents O(N^2) all-pairs social queries.

## Test file

```text
tests/perf/test_phase10_integrated_enhanced_stack_budget.py
```

---

# Task 13 — Add rollout gate

## Description

Before enabling enhanced logic by default, a gate should validate:

```text
performance
determinism
semantic improvement
no forbidden behavior
no hard-law violations
bounded memory
trace volume bounded
feature flags correct
```

## Proposed gate script

```text
scripts/phase10_enhanced_rollout_gate.py
```

## Gate checks

```text
required reports exist
all required scenarios pass
determinism parity passes
performance under profile budget
semantic scorecard above threshold
forbidden behavior count = 0
hard law violation count = 0
trace dropped critical = 0
memory caps respected
```

## Checklist

- [x] Gate reads generated reports.
- [x] Gate validates required scenarios.
- [x] Gate validates performance budget.
- [x] Gate validates semantic scorecard.
- [x] Gate validates determinism parity.
- [x] Gate validates no forbidden behavior.
- [x] Gate fails with actionable reason.
- [x] Gate report uses bounded language.

## TDD tests

```text
tests/certification/test_phase10_enhanced_rollout_gate.py
```

Test cases:

```text
test_rollout_gate_rejects_missing_reports
test_rollout_gate_rejects_performance_regression
test_rollout_gate_rejects_forbidden_behavior
test_rollout_gate_rejects_determinism_failure
test_rollout_gate_accepts_valid_bundle
test_rollout_gate_uses_bounded_language
```

---

# Task 14 — Add developer diagnostics

## Description

When a scenario fails, developers need to know why.

Add diagnostics for:

```text
phase skipped due to budget
provider returned no options
requirement blocked route
memory evicted useful fact
trace event dropped
feature flag disabled phase
cache stale / invalidated
degradation mode active
```

## Diagnostic report

```yaml
failure_diagnostics:
  entity_id: 12
  failed_behavior: repeated_failed_route
  likely_causes:
    - provider_returned_no_alternative_sources
    - route_generator_repeated_blocked_route
    - knowledge_unknown_not_connected_to_information_need
  evidence_events:
    - ev_1001
    - ev_1034
  suggested_inspection:
    - check RequirementEvaluator result for moon_resin
    - check InformationProvider source scope
    - check route-family classifier
```

## Checklist

- [x] Diagnostics identify skipped phases.
- [x] Diagnostics identify missing provider options.
- [x] Diagnostics identify repeated blocker loops.
- [x] Diagnostics identify hidden knowledge suspicion.
- [x] Diagnostics link to evidence events.
- [x] Diagnostics avoid false certainty.
- [x] Diagnostics generated for failed campaign scorecards.

## TDD tests

```text
tests/unit/diagnostics/test_phase10_developer_diagnostics.py
```

Test cases:

```text
test_diagnostics_report_budget_skip
test_diagnostics_report_no_provider_options
test_diagnostics_report_repeated_blocker_loop
test_diagnostics_report_hidden_knowledge_suspicion
test_diagnostics_include_evidence_event_ids
```

---

# Phase 10 test files to add

```text
tests/unit/config/test_phase10_feature_flags.py
tests/unit/config/test_phase10_rollout_profiles.py

tests/unit/perf/test_phase10_phase_budget_manager.py
tests/unit/perf/test_phase10_dirty_work_scheduler.py
tests/unit/perf/test_phase10_cache_invalidation.py
tests/unit/perf/test_phase10_memory_capacity_limits.py

tests/unit/world/providers/test_phase10_provider_budget_enforcement.py
tests/unit/observability/test_phase10_trace_volume_governor.py
tests/unit/diagnostics/test_phase10_developer_diagnostics.py

tests/integration/perf/test_phase10_graceful_degradation.py
tests/perf/test_phase10_integrated_enhanced_stack_budget.py

tests/certification/test_phase10_enhanced_determinism_parity.py
tests/certification/test_phase10_enhanced_rollout_gate.py

docs/test_coverage/phase10_optimization_scaling_coverage.md
scripts/phase10_enhanced_rollout_gate.py
```

---

# Phase 10 non-goals

Do **not** add new gameplay features here:

```text
new monsters
new quests
new social systems
new combat formulas
new crafting economy
new faction politics
new world ecology
new memory models
```

Do **not** duplicate existing tests for:

```text
generic long-run stability
generic determinism parity
arena stress
API observability
websocket behavior
release gate baseline
basic envelope violations
```

Those already exist in the current uploaded test suite.

---

# Phase 10 completion criteria

Phase 10 is done when this is true:

```text
The enhanced simulation stack can be enabled gradually,
profile by profile,
with clear budgets,
bounded memory,
deterministic results,
bounded trace volume,
safe degradation,
and a rollout gate that prevents unsafe activation.
```

Minimum proof:

```text
feature flags work
SHADOW mode does not change authoritative state
ON mode is deterministic
provider calls are capped
dirty scheduling skips clean entities
memory structures are bounded
trace volume is bounded
degradation is honest and recoverable
full-stack profile runs inside budget
rollout gate catches invalid bundles
```

---

# Priority Plan

## What changes in Phase 10

Before Phase 10:

```text
the enhanced logic can work
```

After Phase 10:

```text
the enhanced logic can be safely shipped, profiled, disabled, scaled, and debugged
```

## Implementation order

```text
1. Coverage audit
2. Feature flag matrix
3. Rollout profiles
4. Phase budget manager
5. Dirty work scheduler
6. Provider budget enforcement
7. Cache/invalidation strategy
8. Trace volume governor
9. Memory/capacity limits
10. Determinism parity suite
11. Graceful degradation
12. Integrated performance scenarios
13. Rollout gate
14. Developer diagnostics
```

## What to stop

Stop adding intelligence before proving budget safety.

Stop assuming “we will optimize later.”

Stop allowing every phase to run whenever it wants.

Stop allowing unbounded memory, unbounded traces, unbounded provider calls, or unbounded candidate generation.

## Consequence if ignored

The enhanced design may look correct, but it will not be production-safe.

The most likely failure will be:

```text
entities become smarter
world becomes richer
but performance collapses
debug traces explode
memory grows over long runs
determinism becomes fragile
and rollout becomes risky
```

Phase 10 prevents that.

It turns the enhanced simulation from a research prototype into an engine feature that can be enabled safely.
