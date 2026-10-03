---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260701-SIMQ-EMIT-INFORMATION2
artifact_type: test_plan
tags: [simq, information, cognition, event-emission]
---

# Test Plan: TCK-20260701-SIMQ-EMIT-INFORMATION2

## Regression Surface

The following existing tests must pass without modification after this ticket:

| File | Covers |
|---|---|
| `tests/unit/observability/test_event_extractor_cognition.py` | All 5 prior cognition/information emitters (self_model_updated, belief_assimilated, belief_updated, paid_information_transaction, lead_certainty_changed) |
| `tests/unit/domains/information/test_phase5_information_events.py` | InformationBeliefPhase events |
| `tests/unit/observability/cognition/test_cognition_event_mapper.py` | CognitionEventMapper |
| Any test touching `LeadContradictionSystem` | Lead contradiction detection and mutation |

Run scope before and after implementation:

```
pytest tests/unit/observability/ -x -q
pytest tests/unit/domains/information/ -x -q
```

---

## New Tests Required (per AC)

All new tests go in `tests/unit/observability/test_event_extractor_information2.py` unless noted.
Use the same MagicMock builder pattern as `test_event_extractor_cognition.py`.

### AC 1 — `lead_contradiction_resolved`

Location: `src/engine/pipeline_phases/lead_contradiction.py`

**Test file**: `tests/unit/engine/pipeline_phases/test_lead_contradiction.py`
(extend existing file if present, else create alongside it)

```
test_lead_contradiction_resolved_emitted_with_belief_contradiction
  - Build state where entity has a lead pointing to a depleted resource node
  - Call LeadContradictionSystem.enforce()
  - Assert "belief_contradiction" in [e.event_type for e in events]
  - Assert "lead_contradiction_resolved" in [e.event_type for e in events]
  - Assert both events share the same lead_id in payload

test_lead_contradiction_resolved_payload_fields
  - Verify payload of lead_contradiction_resolved has: lead_id, provider_id, subject, failure_count
  - failure_count must be >= 1 (incremented before emit)

test_lead_contradiction_resolved_not_emitted_without_contradiction
  - Build state where all leads are consistent with world state
  - Assert neither event type appears in output
```

### AC 2 — `lead_certainty_updated` (band-crossing only)

```
test_lead_certainty_updated_emitted_on_vague_to_approximate
  - prior_state: lead certainty = VAGUE
  - current_state: lead certainty = APPROXIMATE
  - Assert "lead_certainty_updated" in event types
  - Assert "lead_certainty_changed" also in event types (dual emit)

test_lead_certainty_updated_emitted_on_approximate_to_precise
  - prior: APPROXIMATE, current: PRECISE
  - Assert "lead_certainty_updated" emitted

test_lead_certainty_updated_not_emitted_when_no_change
  - prior: VAGUE, current: VAGUE
  - Assert "lead_certainty_updated" NOT in event types

test_lead_certainty_updated_not_emitted_new_lead
  - prior_state: lead does not exist
  - current_state: lead exists with APPROXIMATE
  - Assert "lead_certainty_updated" NOT emitted (no prior to compare against)

test_lead_certainty_updated_payload_has_certainty_delta
  - VAGUE → APPROXIMATE transition
  - Assert "certainty_delta" key is present in payload and > 0

test_lead_certainty_changed_payload_now_has_certainty_delta
  - Regression guard: existing lead_certainty_changed must also carry certainty_delta
  - Verify payload["certainty_delta"] is numeric (not missing/None)

test_lead_certainty_updated_exhausted_is_negative_delta
  - prior: APPROXIMATE, current: EXHAUSTED
  - Assert "lead_certainty_updated" emitted with certainty_delta < 0
```

### AC 3 — `belief_stale`

```
test_belief_stale_emitted_after_threshold
  - Entity has a VAGUE lead discovered at tick 0
  - Extract at tick = belief_stale_ticks + 1 (e.g. tick=51 if threshold=50)
  - Assert "belief_stale" in event types

test_belief_stale_not_emitted_before_threshold
  - Same lead, extract at tick = belief_stale_ticks - 1
  - Assert "belief_stale" NOT in event types

test_belief_stale_not_emitted_for_precise_lead
  - Lead certainty = PRECISE, age > threshold
  - Assert "belief_stale" NOT in event types (PRECISE leads are not stale)

test_belief_stale_not_emitted_for_exhausted_lead
  - Lead certainty = EXHAUSTED, age > threshold
  - Assert "belief_stale" NOT in event types

test_belief_stale_deduplication_across_ticks
  - First extract at tick=51 → "belief_stale" emitted
  - Second extract at tick=52 (same lead still stale) → "belief_stale" NOT emitted again
  - Confirms once-per-epoch dedup guard works
  - Must call EventExtractor.reset_run_state() in teardown

test_belief_stale_payload_has_lead_id_and_age
  - Assert payload contains "lead_id" and "age_ticks"

test_belief_stale_config_key_present_in_detection_params
  - Load config/simulation_quality/detection_params.yaml
  - Assert "belief_stale_ticks" key is present and is an int > 0
```

### AC 4 — `paid_info_changed_goal`

```
test_paid_info_changed_goal_emitted_when_project_changes
  - prior_state: entity current_project_id = "info_seeking_1"
  - current_state: entity current_project_id = "harvesting_2" (seeking project removed, new active)
  - intent_results contains accepted INFORMATION_PURCHASE
  - Assert "paid_info_changed_goal" in event types

test_paid_info_changed_goal_not_emitted_when_project_unchanged
  - prior_state and current_state: same current_project_id
  - intent_results contains accepted INFORMATION_PURCHASE
  - Assert "paid_info_changed_goal" NOT in event types

test_paid_info_changed_goal_not_emitted_without_purchase
  - current_project_id changed but no INFORMATION_PURCHASE intent
  - Assert "paid_info_changed_goal" NOT in event types

test_paid_info_changed_goal_category_is_strategy
  - Confirm event_category = "strategy" (not "economy")
```

### AC 5 — `decision_diverged_by_belief`

```
test_decision_diverged_by_belief_emitted_when_stale_belief_and_non_top_project
  - Entity has project A (score=80, kind=HARVESTING) and project B (score=20, kind=SOCIAL)
  - Entity's current_project_id = project B (non-top)
  - Entity has a VAGUE lead
  - Assert "decision_diverged_by_belief" in event types

test_decision_diverged_by_belief_not_emitted_when_top_project_active
  - Entity has project A (score=80) as active and project B (score=20)
  - Entity has VAGUE lead
  - Assert "decision_diverged_by_belief" NOT emitted (active IS the top project)

test_decision_diverged_by_belief_not_emitted_without_vague_lead
  - Entity's active project is non-top but all leads are APPROXIMATE or PRECISE
  - Assert "decision_diverged_by_belief" NOT emitted

test_decision_diverged_by_belief_payload_has_required_fields
  - Assert payload has "active_project_kind", "top_project_kind", "active_project_score",
    "top_project_score"

test_decision_diverged_by_belief_is_collapse_default_false
  - Assert payload["is_collapse"] = False in all per-entity emits
```

### AC 6 — `decision_divergence_detected` (COGNITION)

```
test_decision_divergence_detected_emitted_when_tier_mismatch
  - Entity active project kind = SOCIAL (SOCIAL tier)
  - Highest-scoring project kind = RECOVERY (SURVIVAL tier)
  - Assert "decision_divergence_detected" in event types

test_decision_divergence_detected_not_emitted_when_tiers_match
  - Active = HARVESTING (ECONOMY), top = CRAFTING (ECONOMY)
  - Assert "decision_divergence_detected" NOT emitted

test_decision_divergence_detected_not_emitted_when_active_is_top
  - Active project is the highest-scoring one (regardless of tier)
  - Assert "decision_divergence_detected" NOT emitted

test_decision_divergence_detected_payload_fields
  - Assert payload has "active_project_kind", "top_project_kind", "active_tier", "top_tier"
  - Assert payload["is_collapse"] = False

test_decision_divergence_detected_survival_over_social
  - Active = SOCIAL (score=30), top = COMBAT (score=90)
  - Confirm event fires (SOCIAL tier vs SURVIVAL tier mismatch)

test_decision_divergence_detected_and_decision_diverged_can_coexist
  - Construct state satisfying both detection conditions
  - Assert both "decision_divergence_detected" (COGNITION) and
    "decision_diverged_by_belief" (INFORMATION) are in event types
  - Confirms the two events are independent emits from the same code block
```

### Integration guard

```
tests/unit/observability/test_event_extractor_information2.py::
test_no_regression_on_existing_cognition_events
  - Construct a state that triggers all prior cognition events
  - Run extract()
  - Assert all 5 prior event types still present (regression guard)
```

---

## Scoped Pytest Commands

Run after each implementation step to confirm no regression:

```bash
# Prior cognition emit regression
pytest tests/unit/observability/test_event_extractor_cognition.py -x -q

# New information2 tests (as they are added)
pytest tests/unit/observability/test_event_extractor_information2.py -x -q

# Lead contradiction system (existing + new resolution tests)
pytest tests/unit/engine/ -x -q -k "contradiction"

# Detection params config guard
pytest tests/unit/observability/test_event_extractor_information2.py::test_belief_stale_config_key_present_in_detection_params -x -v

# Full observability unit scope
pytest tests/unit/observability/ -x -q

# Domains / information phase
pytest tests/unit/domains/information/ -x -q

# Smoke: not slow
pytest tests/ -m "not slow" -x -q --timeout=30
```

---

## Anti-Drift Test Guards

| Guard | Why |
|---|---|
| `test_belief_stale_deduplication_across_ticks` with `reset_run_state()` teardown | Prevents per-run tracking dict from leaking into subsequent tests |
| `test_belief_stale_config_key_present_in_detection_params` | Ensures `belief_stale_ticks` remains in config after any config cleanup |
| `test_lead_certainty_changed_payload_now_has_certainty_delta` | Locks in the payload fix for the existing CognitionScorer dead-code branches |
| `test_decision_divergence_detected_and_decision_diverged_can_coexist` | Guards that the two events are separate emits and cannot be accidentally merged |
| `test_lead_contradiction_resolved_emitted_with_belief_contradiction` | Both events must appear together — if future refactor separates the function they could desync |
| `test_no_regression_on_existing_cognition_events` | Full regression guard against the 5 prior events being removed |
