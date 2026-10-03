---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260701-SIMQ-EMIT-AGENCY2
artifact_type: test_plan
tags: [simq, agency, event-emission]
---

# Test Plan — TCK-20260701-SIMQ-EMIT-AGENCY2

---

## Regression Surface

Files that must not regress after this ticket:

| File | Reason |
|---|---|
| `tests/unit/observability/test_event_extractor_agency.py` | Prior agency emit tests (route_selected, action_executed). NOTE: `test_defer_gap_no_update_means_no_agency_event()` documents the old gap and will need updating once `defer_with_reason` is wired via phase write. |
| `tests/unit/strategic/test_rejection_backoff.py` | Rejection backoff logic in evaluate_strategic_intent(); must not be disturbed by any rejection count changes |
| `tests/simulation_quality/test_agency_scorer.py` | AgencyScorer scorer logic for all existing event types |
| `tests/simulation_quality/test_timegate_penalties.py::TestAgencyTimegate` | Stasis gate behavior for defer_with_reason; existing stasis logic must be preserved |

Run before beginning implementation:
```
pytest tests/unit/observability/test_event_extractor_agency.py tests/unit/strategic/test_rejection_backoff.py tests/simulation_quality/test_agency_scorer.py tests/simulation_quality/test_timegate_penalties.py -v
```

---

## New Tests Required (per AC)

All new tests go in `tests/unit/observability/test_event_extractor_agency2.py`
(new file — companion to the existing agency test file, prefixed with `2` for this pass).

### AC-1: All 4 event types emitted under correct conditions

#### Group A: defer_with_reason

**Test A-1** `test_defer_with_reason_emitted_when_property_set`
- Setup: entity with no routing update (DEFER path), but EntityUpdate in update with
  `property_updates = {"last_defer_reason": "no_viable_route", "last_defer_tick": 5}`
- Assert: events contain one `defer_with_reason` event
- Assert: event payload contains `reason == "no_viable_route"`

**Test A-2** `test_defer_with_reason_not_emitted_without_defer_property`
- Setup: entity with EntityUpdate but `property_updates = {}` (no defer signal)
- Assert: no `defer_with_reason` event in output

**Test A-3** `test_defer_with_reason_not_emitted_when_routing_present`
- Setup: entity with `property_updates = {"last_routing_family": "recover"}` (a real route)
- Assert: no `defer_with_reason` event (the routing path, not defer path)

**Test A-4** `test_defer_with_reason_payload_structure`
- Setup: defer property set with a specific reason string
- Assert: payload has keys `entity_id`, `reason`, `tick`
- Assert: `event_category == "strategy"`

#### Group B: commitment_abandoned

**Test B-1** `test_commitment_abandoned_emitted_on_abandoned_project_not_survival`
- Setup: prior state has project `proj_x` with `status=ACTIVE`; current state has same
  project with `status=ABANDONED`; entity HP = 80, max_hp = 100 (ratio 0.8, not survival)
- Assert: events contain one `commitment_abandoned` event
- Assert: payload `category == "voluntary_quit"` (or `"greedy_desertion"` if conditions met)

**Test B-2** `test_commitment_abandoned_not_emitted_when_survival_category`
- Setup: prior project ACTIVE → current ABANDONED; entity HP = 15, max_hp = 100 (ratio 0.15)
- Assert: no `commitment_abandoned` event (survival case is filtered out)
- Rationale: AbandonmentEvaluator returns SURVIVAL when HP < 0.2; emitter skips.

**Test B-3** `test_commitment_abandoned_not_emitted_for_non_abandonment_transitions`
- Setup: prior project ACTIVE → current COMPLETED (not ABANDONED)
- Assert: no `commitment_abandoned` event

**Test B-4** `test_commitment_abandoned_payload_uses_typed_category`
- Setup: ACTIVE→ABANDONED with HP ratio 0.5
- Assert: payload `category` is a string (not an enum object)
- Assert: payload `category` in `{"voluntary_quit", "greedy_desertion"}`
- Assert: payload includes `entity_id` and `tick`

**Test B-5** `test_commitment_abandoned_and_project_abandoned_both_emitted`
- Setup: ACTIVE→ABANDONED transition with HP ratio >= 0.2
- Assert: both `commitment_abandoned` AND QuestEvent (which becomes `project_abandoned`)
  are present — neither displaces the other
- Rationale: anti-drift guard for coexistence with existing QuestEvent emission

#### Group C: rejection_cascade_tick

**Test C-1** `test_rejection_cascade_tick_emitted_above_threshold`
- Setup: update with N entity updates, each having >= 1 rejected intent_result;
  total rejected count > threshold (e.g., 25 entities each with 1 rejection = 25 total)
- Assert: events contain one `rejection_cascade_tick` event
- Assert: payload `count >= 20`

**Test C-2** `test_rejection_cascade_tick_not_emitted_below_threshold`
- Setup: update with 5 entity updates, each having 1 rejected intent_result (5 total)
  below threshold (assuming threshold = 20)
- Assert: no `rejection_cascade_tick` event

**Test C-3** `test_rejection_cascade_tick_fires_at_most_once_per_tick`
- Setup: 100 entity updates each with 3 rejected intent_results (300 total rejections)
- Assert: exactly one `rejection_cascade_tick` event (not one per entity)

**Test C-4** `test_rejection_cascade_tick_payload_has_dominant_failure_reason`
- Setup: 30 entities each with 2 rejected results: 20 with `reason="INSUFFICIENT_CAPACITY"`,
  10 with `reason="OUT_OF_STOCK"`
- Assert: payload `dominant_failure_reason == "INSUFFICIENT_CAPACITY"`

**Test C-5** `test_rejection_cascade_tick_not_emitted_when_all_accepted`
- Setup: N entity updates with intent_results all having `accepted=True`
- Assert: no `rejection_cascade_tick` event

#### Group D: route_family_first_use

**Test D-1** `test_route_family_first_use_fires_on_first_family`
- Setup: entity 1, routing family "gather_resource" (first occurrence for entity 1)
  (call `EventExtractor.reset_run_state()` in setup)
- Assert: events contain one `route_family_first_use` event
- Assert: payload `family == "gather_resource"`, `entity_id == 1`

**Test D-2** `test_route_family_first_use_not_fires_on_repeat_family`
- Setup: call extract twice with entity 1 and family "gather_resource" both times
- Assert: first call produces `route_family_first_use`
- Assert: second call produces NO `route_family_first_use`

**Test D-3** `test_route_family_first_use_fires_for_each_new_family`
- Setup: entity 1, first call with "gather_resource", second call with "recover"
- Assert: both calls produce `route_family_first_use` (different families)

**Test D-4** `test_route_family_first_use_independent_per_entity`
- Setup: entity 1 and entity 2 each first-use "gather_resource"
  (first entity 1, then entity 2)
- Assert: both produce `route_family_first_use` (entity IDs track independently)

**Test D-5** `test_route_family_first_use_reset_clears_seen_state`
- Setup: entity 1 uses "gather_resource" in first extract call; call
  `EventExtractor.reset_run_state()`; use "gather_resource" again
- Assert: second call after reset produces `route_family_first_use` again
- Rationale: confirms reset mechanism works for test isolation

### AC-2: commitment_abandoned payload uses AbandonmentClassification fields (typed)
Covered by Tests B-4 and B-1 — payload `category` is string value from AbandonmentCategory.

### AC-3: rejection_cascade_tick fires at most once per entity per tick
Covered by Test C-3 — one event regardless of entity count.

### AC-4: route_family_first_use fires exactly once per novel family per entity per run
Covered by Tests D-1, D-2, D-3, D-4.

### AC-5: event_type_coverage.md §3.1 updated — 4 entries removed
Manual verification (no automated test). Acceptance gate: inspect the file — the 4 rows for
`defer_with_reason`, `commitment_abandoned`, `rejection_cascade_tick`, `route_family_first_use`
are gone from §3.1 after implementation.

### AC-6: No regression in existing agency / routing tests
Covered by regression surface runs above.

---

## Additional: AgencyScorer Unit Tests (scorer-side validation)

In `tests/simulation_quality/test_agency_scorer.py` (existing file — add to it):

**Test E-1** `test_scorer_handles_defer_with_reason_event`
- Feed `ObservabilityEventEnvelope(event_type="defer_with_reason", ...)` to scorer
- Assert: returns a ScoreRecord with `pillar=PillarId.AGENCY` and `delta < 0`
  (defer_idle weight is negative)

**Test E-2** `test_scorer_handles_commitment_abandoned_returns_none`
- Feed `commitment_abandoned` envelope to scorer
- Assert: returns None (scorer intentionally no-ops — verify the contract is stable)

**Test E-3** `test_scorer_handles_rejection_cascade_tick_at_500`
- Feed `rejection_cascade_tick` with `payload={"count": 501}`
- Assert: returns ScoreRecord with tag `"rejection_cascade_sustained"`

**Test E-4** `test_scorer_handles_rejection_cascade_tick_at_100`
- Feed `rejection_cascade_tick` with `payload={"count": 150}`
- Assert: returns ScoreRecord with tag `"rejection_cascade"`

**Test E-5** `test_scorer_handles_route_family_first_use`
- Feed `route_family_first_use` with `payload={"family": "recover", "entity_id": 1}`
- Assert: returns ScoreRecord with tags containing `"route_novelty"` and `"entropy_reward"`

---

## Scoped Pytest Commands

**Phase 1 — regression baseline (run before writing any code):**
```
pytest tests/unit/observability/test_event_extractor_agency.py \
       tests/unit/strategic/test_rejection_backoff.py \
       tests/simulation_quality/test_agency_scorer.py \
       tests/simulation_quality/test_timegate_penalties.py \
       -v --tb=short
```

**Phase 2 — new unit tests (run as you write each group):**
```
# defer_with_reason group
pytest tests/unit/observability/test_event_extractor_agency2.py -k "defer" -v

# commitment_abandoned group
pytest tests/unit/observability/test_event_extractor_agency2.py -k "commitment" -v

# rejection_cascade_tick group
pytest tests/unit/observability/test_event_extractor_agency2.py -k "cascade" -v

# route_family_first_use group
pytest tests/unit/observability/test_event_extractor_agency2.py -k "route_family" -v
```

**Phase 3 — full new test file:**
```
pytest tests/unit/observability/test_event_extractor_agency2.py -v
```

**Phase 4 — scorer tests:**
```
pytest tests/simulation_quality/test_agency_scorer.py -v
```

**Phase 5 — full non-slow suite:**
```
pytest -m "not slow" tests/unit/observability/ tests/simulation_quality/ -v --tb=short
```

**Do NOT run:**
```
pytest tests/   # full suite — too broad; violates Testing Rule
```

---

## Anti-Drift Test Guards

**Guard 1 — Phase write / EventExtractor name coupling:**
```python
def test_defer_property_name_constant_matches_phase_and_extractor():
    """If the property name changes in phase.py it must change in event_extractor.py too.
    This test asserts both sides use the same string literal (or shared constant)."""
    # Verify the defer signal key used in phase.py (property_updates dict key) is the
    # same string that EventExtractor looks up. If this test fails after a rename,
    # the mismatch will be caught before a silent event drop.
    from src.domains.adventure import phase as phase_mod
    import inspect
    source = inspect.getsource(phase_mod.AdventureDecisionPhase.apply)
    assert "last_defer_reason" in source  # update if key name changes
    from src.observability.event_extractor import EventExtractor
    extractor_source = inspect.getsource(EventExtractor.extract)
    assert "last_defer_reason" in extractor_source
```

**Guard 2 — reset_run_state() exists and works:**
```python
def test_event_extractor_has_reset_run_state():
    from src.observability.event_extractor import EventExtractor
    assert hasattr(EventExtractor, "reset_run_state"), (
        "EventExtractor must expose reset_run_state() classmethod for test isolation "
        "and run-boundary clearing of _seen_routing_families"
    )
    EventExtractor.reset_run_state()  # must not raise
```

**Guard 3 — commitment_abandoned does not displace project_abandoned:**
Already captured as Test B-5. The QuestEvent that produces `project_abandoned` (via
`_TRANSLATE_CONDITIONAL`) must be present alongside `commitment_abandoned` for any
ACTIVE→ABANDONED transition.

**Guard 4 — AbandonmentCategory string values are stable:**
```python
def test_abandonment_category_string_values():
    from src.domains.commitment.abandonment import AbandonmentCategory
    assert AbandonmentCategory.SURVIVAL.value == "survival"
    assert AbandonmentCategory.VOLUNTARY_QUIT.value == "voluntary_quit"
    assert AbandonmentCategory.GREEDY_DESERTION.value == "greedy_desertion"
```
If `abandonment.py` renames a category value, the emitter's payload will silently change.
This guard locks the contract.

**Guard 5 — _MAX_CONSECUTIVE_REJECTIONS is not duplicated:**
The emitter must not hardcode `20`. If both the evaluator and the emitter threshold come
from the same constant, this guard verifies they match:
```python
def test_rejection_cascade_emitter_uses_same_threshold_as_intelligence():
    from src.systems.strategic_systems.intelligence import _MAX_CONSECUTIVE_REJECTIONS
    # Import the threshold used by the emitter (wherever it lives post-implementation)
    # and assert they are equal.
    assert _MAX_CONSECUTIVE_REJECTIONS == 20  # update if constant moves
```
