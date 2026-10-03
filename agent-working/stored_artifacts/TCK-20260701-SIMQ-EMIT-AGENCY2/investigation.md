---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260701-SIMQ-EMIT-AGENCY2
artifact_type: investigation
tags: [simq, agency, event-emission]
---

# Investigation — TCK-20260701-SIMQ-EMIT-AGENCY2

---

## Current Behavior (file:line refs)

### 1. defer_with_reason — BLOCKED by architecture; emission path requires phase modification

`src/domains/adventure/phase.py:L115-116`:
```python
if not result.selected or result.selected.family == RouteFamily.DEFER_WITH_REASON:
    continue
```
When an entity defers, `AdventureDecisionPhase.apply()` executes `continue` immediately.
No `EntityUpdate` is created. No entry is written to `StateUpdate.entity_updates` for the
deferring entity.

`src/observability/event_extractor.py:L186-204` (Agency section):
`route_selected` and `action_executed` are emitted by reading
`property_updates.get("last_routing_family")` from the EntityUpdate. Since no EntityUpdate
is created on DEFER, `property_updates` is never populated with a DEFER signal.
Result: zero `defer_with_reason` events are ever emitted — confirmed by calibration hit count
of 0 in `docs/simulation_quality/event_type_coverage.md §3.1`.

`src/domains/adventure/schema.py:L30`: `DEFER_WITH_REASON = "defer_with_reason"` is a
valid `RouteFamily` enum member. `result.selected` is an `AdventureRouteOption` whose
`.family` and `.reason` fields are populated on DEFER paths
(see `AdventureDecisionService`).

**Path to emission**: Modify `phase.py:L115-116` to write a deferred-entity signal into
`property_updates` before continuing — e.g. set `"last_defer_reason"` and `"last_defer_tick"`
on a minimal EntityUpdate. EventExtractor then detects this property in the existing
per-entity `e_upd_ext` block and emits `defer_with_reason`. This does not change routing
decision logic; it is purely observability instrumentation within the phase.

Note: the prior ticket's scope guard "Do NOT modify AdventureDecisionPhase" was specific to
TCK-20260629-SIMQ-EMIT-AGENCY (which avoided all phase touches). This ticket explicitly
scopes the DEFER emitter and therefore allows the targeted phase write.

---

### 2. commitment_abandoned — AbandonmentEvaluator is orphaned; state diff path is viable

`src/domains/commitment/abandonment.py:L25-58`: `AbandonmentEvaluator.evaluate_abandonment()`
exists with three return paths:
- `AbandonmentCategory.SURVIVAL` — HP ratio < 0.2
- `AbandonmentCategory.GREEDY_DESERTION` — in combat and greed-driven
- `AbandonmentCategory.VOLUNTARY_QUIT` — all other cases

**Critical finding**: `AbandonmentEvaluator` is NOT called from any live engine path.
The only references are the module definition itself and the re-export in
`src/domains/commitment/__init__.py:L8,14`. No pipeline phase, no system, no test
calls `evaluate_abandonment()` during a live simulation tick.

Actual project abandonment in the engine:
`src/systems/strategic_systems/intelligence.py:L1149-1178`:
```
# Section: "2. Project Abandonment (PH6)"
if project.failure_count >= _MAX_CONSECUTIVE_REJECTIONS:
    abandoned = replace(project, status=ProjectStatus.ABANDONED)
    return StrategicUpdate(
        projects_add_or_update=[abandoned],
        current_project_id_set="", ...
    )
```
This path sets `ProjectStatus.ABANDONED` directly. No classification is performed.

`src/observability/event_extractor.py:L426-438`: The existing QuestEvent loop detects
project status changes (ACTIVE → ABANDONED) and emits a `QuestEvent` with
`status=str(qstate.status)`. This is then translated to `project_abandoned` by
`_TRANSLATE_CONDITIONAL` in `quality_hub.py`. So `project_abandoned` is already covered.
`commitment_abandoned` is a DISTINCT event intended to capture behavioral classification
(voluntary vs survival), not just the raw status change.

**Open question (decision required)**: `evaluate_abandonment()` takes `is_party_in_combat`
and `is_greed_driven` as inputs that are not directly available from entity state in
EventExtractor. See Risks section.

**Path to emission**: In the EventExtractor entity loop, after the project diff block
(`L426-438`), detect ACTIVE → ABANDONED project status transitions. Call
`AbandonmentEvaluator.evaluate_abandonment(entity.combat.hp, entity.combat.max_hp, ...)`.
Emit `commitment_abandoned` when `classification.category != AbandonmentCategory.SURVIVAL`.
`src/observability/` is NOT subject to the `src/simulation_quality/` coupling law (§2 of
the quality contract) — EventExtractor CAN import from `src/domains/commitment/`.

---

### 3. rejection_cascade_tick — no per-tick aggregate; per-entity tracking only

`src/systems/strategic_systems/intelligence.py:L27`:
```python
_MAX_CONSECUTIVE_REJECTIONS: int = 20
```
This is a per-entity, per-project counter (`project.failure_count`) incremented when
ALL intent results for an entity in a given tick are rejected. It does not represent
total rejected intent volume across the population in a tick.

`src/systems/strategic_systems/intelligence.py:L1155-1165`:
```python
_intent_results = entity.identity.latest_intent_results
if _intent_results:
    _any_accepted = any(r.accepted for r in _intent_results)
    if not _any_accepted:
        project = replace(project, failure_count=project.failure_count + 1)
    elif project.failure_count > 0:
        project = replace(project, failure_count=0)
```
No per-tick aggregate rejection count is computed or stored anywhere.

`src/systems/strategic_systems/intelligence.py:L710-712`:
`metric_counters` already written to StateUpdate by `resolve_blockers()` with
`"strategic_candidates"`. This field provides a clean path to propagate a
tick-level rejection count from the strategy pass into the StateUpdate without
touching the engine or observability layer.

`src/observability/event_extractor.py:L243-294`: EventExtractor already iterates
`e_upd_ext.intent_results` for accepted results (economy events). Rejected results
(`.accepted == False`) are currently silently skipped. The per-tick total rejected intent
count can be accumulated in a post-entity-loop step.

`src/simulation_quality/scorers/agency.py:L114-128`: Scorer checks `payload.get("count")`:
- count > 500 → `rejection_cascade_sustained` score
- count > 100 → `rejection_cascade` score
- count <= 100 → returns None

**Threshold alignment**: The ticket says "emit when count exceeds `_MAX_CONSECUTIVE_REJECTIONS=20`"
but the scorer's minimum scoring threshold is 100. This means events emitted with count in
[20, 100] will reach the scorer and return None (no-op). This is acceptable — the emitter
provides raw count signal; the scorer applies its own thresholds. The emitter fires whenever
any cascade activity exists (count >= 1 or count >= 20); the scorer decides significance.
Implementation should emit with `dominant_failure_reason` derived from the rejection reason
distribution across all entities in the tick.

**Path to emission (two options)**:

Option A — EventExtractor post-loop aggregation: After the entity loop in `extract()`,
iterate all entity updates, count rejected intent results, emit one `rejection_cascade_tick`
per tick when count >= threshold. No engine modification.

Option B — metric_counters injection: Add rejection count to `metric_counters` in
`fused_strategic_pass()`, then read it in EventExtractor. Requires modifying
StrategicIntelligenceSystem but gives the strategy pass itself visibility into cascade depth.

Option A is lower coupling and aligns with EventExtractor's existing pattern of
post-entity-loop emission (see resource node depletion section, L441-460).

---

### 4. route_family_first_use — stateful tracking needed in a stateless class

`src/observability/event_extractor.py:L191-204`: `route_selected` is already emitted when
`property_updates["last_routing_family"]` is set. The family value is available at this
exact emission point.

`EventExtractor` is a static-method-only class with no instance state. Module-level or
class-level state is required to track which families have been seen per entity.

No existing mechanism tracks per-entity routing family history anywhere in the engine or
observability layer.

`src/simulation_quality/scorers/agency.py:L57-59`: Scorer gives `route_novelty + entropy_reward`
combined delta for this event — this is the primary entropy signal for the AGENCY pillar.

**State isolation concern**: Class-level `_seen_routing_families: dict[int, set[str]] = {}`
on EventExtractor persists across sequential simulation runs in the same process (e.g.,
pytest test runs). A reset/init mechanism must be provided and called at run start.
Without it, test isolation will fail: a second run in the same process will never emit
`route_family_first_use` for families already seen.

**Path to emission**: Add class-level `_seen_routing_families: dict[int, set[str]] = {}`
to EventExtractor. Co-locate the first-use check immediately after the existing
`route_selected` emission at `event_extractor.py:L191-204`. Provide a
`EventExtractor.reset_run_state()` classmethod to clear this dict at run start
(to be called from kernel/run initialization or test teardown).

---

## Mechanics/Engine Constraints

- `docs/simulation_quality/quality_scoring_contract.md §2` — Coupling law applies only to
  `src/simulation_quality/`. EventExtractor (`src/observability/`) CAN import domain code.
- `docs/engine/kernel.md` — The 6-phase loop calls EventExtractor after each tick.
  EventExtractor is called from the drain worker thread (INPROCESS mode), not from inside
  `kernel.tick_once()`. This means EventExtractor additions have zero simulation-thread impact.
- `docs/engine/authoritative_pipeline.md` — Phase 15 handles commitment resolution. Project
  status transitions (ACTIVE → ABANDONED) are applied authoritatively. EventExtractor
  reads post-application state via `prior_state` vs `current_state` diff.
- `docs/mechanics/04_strategic_cognition.md §Goal Hierarchy` — Commitment abandonment is
  a valid lifecycle event. The mechanics bible does not define a specific abandonment event
  emission requirement; this is a SimQ instrumentation addition.
- `docs/core/state.md` — Immutability law: EventExtractor reads from immutable snapshots.
  All proposed new emissions are read-only with respect to authoritative state.

---

## Parity Ledger Overlap

- **`SIMQ-CALIBRATED-001`** (infrastructure.yaml ~L3090): Current v2_evidence covers
  `route_selected` and `action_executed` from TCK-20260629-SIMQ-EMIT-AGENCY. After this
  ticket, v2_evidence must be extended to include TCK-20260701-SIMQ-EMIT-AGENCY2 and the
  4 new event types. Status remains `verified`; the entry is NOT divergent.

- **AgencyScorer parity entry** (infrastructure.yaml ~L2890-2904): Lists all AgencyScorer
  weights including `route_novelty`, `commitment_complete`, `defer_idle`, `stasis_N`,
  `rejection_cascade`, `rejection_cascade_sustained`, `action_taken`. These weights already
  exist and are already tested. This ticket does not change weights — only unlocks emission.
  The parity entry's test_path (`tests/simulation_quality/test_agency_scorer.py`) will
  already cover scorer behavior for the new events since the scorer handles them. No status
  change required on this entry; only v2_evidence annotation may be added.

---

## Prior Work

- **TCK-20260629-SIMQ-EMIT-AGENCY** (`stored_artifacts/TCK-20260629-SIMQ-EMIT-AGENCY/`):
  Added `route_selected` and `action_executed` via EventExtractor property_updates diff.
  Confirmed that DEFER path is architecturally invisible to state diff. Plan.md explicitly
  scoped out defer_with_reason, rejection_cascade_tick, route_family_first_use,
  commitment_abandoned. Tests in `tests/unit/observability/test_event_extractor_agency.py`
  (8 tests). The `test_defer_gap_no_update_means_no_agency_event()` test documents the gap
  and will need to be UPDATED in this ticket to reflect the new phase-level emit.

- **TCK-20260627-P1A-REJECTION-BACKOFF**: Introduced `_MAX_CONSECUTIVE_REJECTIONS = 20`
  constant in intelligence.py. The rejection backoff per-entity tracking at L1149-1178 is
  the authoritative source of the cascade threshold. This ticket reuses that constant value
  (should import, not duplicate).

- **TCK-20260627-P1F-ABANDONMENT-TYPE**: Introduced typed `AbandonmentClassification`
  dataclass and `AbandonmentCategory` enum in `abandonment.py`. This ticket uses these
  types to filter commitment_abandoned emission (only non-SURVIVAL categories emit).

---

## Risks and Open Questions

### R-1 (Decision required): AbandonmentEvaluator parameter derivation
`evaluate_abandonment()` requires `is_party_in_combat` (bool) and `is_greed_driven` (bool).
In EventExtractor, `is_party_in_combat` would require inspecting group/party membership and
checking if any group member is in combat — this is not readily available from entity state
without O(N) neighbor inspection. `is_greed_driven` has no clear mapping in current
`ProjectState` fields.

**Decision options**:
- A) Default both to `False` — all non-survival abandonment classifies as VOLUNTARY_QUIT.
  Simpler, deterministic, but loses GREEDY_DESERTION distinction.
- B) Derive `is_party_in_combat` from `entity.identity.group_id is not None` AND any entity
  in same faction having `hp < max_hp` this tick — approximate but available in state diff.
- C) Skip `AbandonmentEvaluator` entirely and emit whenever HP ratio >= 0.2, with `category`
  hardcoded to `"voluntary"`. Decouples from the evaluator but ignores it.

Recommended: Option A until `is_greed_driven` has a typed home in `ProjectState`.
Rationale: VOLUNTARY_QUIT (penalty=0.2) is the correct default for the most common
abandonment path (failure_count cascade). GREEDY_DESERTION (penalty=0.8) applies to a
party-combat scenario that is not the dominant abandonment trigger.

### R-2 (Decision required): defer_with_reason payload — what is the "reason"?
`AdventureRouteOption.reason` (schema.py:L52) is an `Optional[str]` free-text field
populated by `AdventureDecisionService`. For a DEFER result, this may be None or a
human-readable string. The ticket payload spec says `"reason"` should be included.
Need to confirm what AdventureDecisionService writes into `result.selected.reason` on DEFER.

### R-3: EventExtractor class-level state in tests
`_seen_routing_families` persists across test functions unless explicitly reset.
Test file must call `EventExtractor.reset_run_state()` in setup/teardown, or tests must
be ordered to avoid cross-contamination. Failure to reset will cause
`route_family_first_use` tests to fail on any non-first run.

### R-4: rejection_cascade_tick payload — dominant_failure_reason
Deriving dominant failure reason requires iterating all rejected intent_results across all
entity updates and building a frequency counter. The most common `ir.reason` string becomes
`dominant_failure_reason`. If `intent_results` is missing or all accepted, no reason exists.
Need a safe fallback (e.g., `"unknown"`).

### R-5: scorer return None for commitment_abandoned
`agency.py:L75-76` currently returns None for `commitment_abandoned`. This is intentional
per the existing scorer design (no scoring contribution defined yet). The emitter can still
emit the event — the scorer's current no-op is not a blocker. If a scoring contribution is
desired, that requires a weights change (out of scope per ticket).

---

## Anti-Drift Hazards

- **Property name coupling**: The defer signal property name added to `phase.py` (e.g.
  `"last_defer_reason"`) must exactly match what EventExtractor reads. Any rename silently
  drops all defer events. Add a constant to a shared location or use the same string literal
  in both places with a cross-reference comment.

- **AbandonmentCategory string value**: `AbandonmentCategory` is a `str, Enum`. Payload
  `category` should use `.value` (the string) not the enum member name. Confirm
  `AbandonmentCategory.SURVIVAL.value == "survival"` (see abandonment.py:L13).

- **_MAX_CONSECUTIVE_REJECTIONS import vs copy**: Do not hardcode `20` in the emitter.
  Import `_MAX_CONSECUTIVE_REJECTIONS` from `intelligence.py` to keep threshold in sync.
  Note: the constant is module-private by convention but importable. Alternatively, expose
  it via a public attribute.

- **Test isolation for class-level state**: Without `EventExtractor.reset_run_state()`,
  sequential test runs in pytest will contaminate `_seen_routing_families`. The anti-drift
  guard is a parametrized test that runs the same family twice in separate simulate-reset-simulate
  cycles and asserts the second cycle fires again.

- **QuestEvent → project_abandoned translation not displaced**: The ACTIVE→ABANDONED diff
  in EventExtractor currently emits a `QuestEvent` which becomes `project_abandoned` via
  translation. Adding `commitment_abandoned` emission for the same transition must NOT
  suppress or replace the existing QuestEvent emission. Both events should co-exist: the
  scorer uses `project_abandoned` (via translation) and `commitment_abandoned` separately.
