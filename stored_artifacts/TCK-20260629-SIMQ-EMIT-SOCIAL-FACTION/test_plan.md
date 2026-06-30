---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-SOCIAL-FACTION
artifact_type: test_plan
tags: [simq, event-extractor, social, faction, diplomatic, testing]
---

# Test Plan: TCK-20260629-SIMQ-EMIT-SOCIAL-FACTION

## 1. Regression Surface — Existing Tests That Must Pass

Run before and after any changes to `src/observability/event_extractor.py`:

```bash
pytest tests/unit/observability/test_event_extractor_simq.py \
       tests/unit/observability/test_event_extractor_agency.py \
       tests/unit/observability/test_event_extractor_cognition.py \
       tests/unit/observability/test_event_extractor_economy.py \
       tests/unit/observability/test_event_extractor_world.py \
       -v
```

Key regression points:
- `test_event_extractor_agency.py` — `route_selected`/`action_executed` from property_updates;
  must not be broken by new property_updates checks for cooperation_event
- `test_event_extractor_economy.py` — `contract_lapsed` from EXPIRED status; fixing the
  OFFERED vs ACTIVE discrimination changes which test cases cover which event — update these
- `test_event_extractor_cognition.py` — `self_model_updated`, `belief_assimilated` from
  entity_updates; must not be broken by new faction_updates/world_events_add loops
- `test_event_extractor_simq.py` — baseline SimQ event extraction; must still pass

---

## 2. New Tests Required

**Test file:** `tests/unit/observability/test_event_extractor_social_faction.py`

All tests follow the mock pattern from `test_event_extractor_agency.py`:
- MagicMock-based `_entity()`, `_state()`, `_update_*()` builders
- `ObservabilityMode.NORMAL` unless testing mode suppression
- Assert on `[e.event_type for e in events]` plus `e.payload` assertions

---

### 2.1 SOCIAL — cooperation_event (PP-05)

| # | Test name | Condition | Assert |
|---|---|---|---|
| S-01 | `test_cooperation_event_emitted_when_decision_in_property_updates` | `property_updates["last_cooperation_decision"]` set | `"cooperation_event"` in types |
| S-02 | `test_cooperation_event_payload_has_entity_id` | same | payload `entity_id` matches eid |
| S-03 | `test_cooperation_event_not_emitted_when_no_decision` | `property_updates` has no `last_cooperation_decision` | `"cooperation_event"` not in types |

---

### 2.2 SOCIAL — contract_offer_created (PP-35, new contract)

| # | Test name | Condition | Assert |
|---|---|---|---|
| S-04 | `test_contract_offer_created_when_new_offered_contract` | Contract in curr but not prior, status=OFFERED | `"contract_offer_created"` in types |
| S-05 | `test_contract_offer_created_payload_has_contract_id` | Same | `payload["contract_id"]` correct |
| S-06 | `test_contract_offer_created_not_emitted_for_accepted_new_contract` | Contract in curr but not prior, status=ACTIVE | `"contract_offer_created"` not in types |

---

### 2.3 SOCIAL — contract_offer_accepted (regression fix scope)

| # | Test name | Condition | Assert |
|---|---|---|---|
| S-07 | `test_contract_offer_accepted_offered_to_active` | Status OFFERED→ACTIVE | `"contract_offer_accepted"` in types |
| S-08 | `test_contract_offer_accepted_not_active_to_active` | Status ACTIVE→ACTIVE (no change) | `"contract_offer_accepted"` not in types |

---

### 2.4 SOCIAL — contract_completed (bug fix — FULFILLED name)

| # | Test name | Condition | Assert |
|---|---|---|---|
| S-09 | `test_contract_completed_on_fulfilled_status` | Prior ACTIVE, curr FULFILLED (`.name == "FULFILLED"`) | `"contract_completed"` in types |
| S-10 | `test_contract_completed_payload_has_contract_id` | Same | `payload["contract_id"]` present |
| S-11 | `test_contract_completed_not_on_failed_status` | Prior ACTIVE, curr FAILED | `"contract_completed"` not in types |

---

### 2.5 SOCIAL — contract_lapsed (ACTIVE→EXPIRED only, not OFFERED→EXPIRED)

| # | Test name | Condition | Assert |
|---|---|---|---|
| S-12 | `test_contract_lapsed_on_active_to_expired` | Prior ACTIVE, curr EXPIRED | `"contract_lapsed"` in types, `"contract_expired_offer"` not |
| S-13 | `test_contract_lapsed_not_on_offered_to_expired` | Prior OFFERED, curr EXPIRED | `"contract_lapsed"` not in types |

---

### 2.6 SOCIAL — contract_expired_offer (PP-36, OFFERED expiry)

| # | Test name | Condition | Assert |
|---|---|---|---|
| S-14 | `test_contract_expired_offer_on_offered_to_expired` | Prior OFFERED, curr EXPIRED | `"contract_expired_offer"` in types |
| S-15 | `test_contract_expired_offer_on_reap_removal` | Contract in prior with OFFERED, absent from curr | `"contract_expired_offer"` in types |
| S-16 | `test_contract_expired_offer_payload_has_contract_id` | Same | `payload["contract_id"]` present |

---

### 2.7 SOCIAL — reputation_delta (PP-18)

| # | Test name | Condition | Assert |
|---|---|---|---|
| S-17 | `test_reputation_delta_emitted_on_significant_change` | `entity.social.public_reputation` differs by > 0.05 | `"reputation_delta"` in types |
| S-18 | `test_reputation_delta_payload_has_delta` | Same | `payload["delta"]` and `payload["entity_id"]` present |
| S-19 | `test_reputation_delta_not_emitted_below_threshold` | Differs by 0.03 | `"reputation_delta"` not in types |
| S-20 | `test_reputation_delta_not_emitted_on_zero_change` | No change | `"reputation_delta"` not in types |

---

### 2.8 SOCIAL — group_joined / group_expelled (regression)

| # | Test name | Condition | Assert |
|---|---|---|---|
| S-21 | `test_group_joined_on_group_id_set` | entity.group_id None→non-None | `"group_joined"` in types |
| S-22 | `test_group_expelled_on_group_id_cleared` | entity.group_id non-None→None | `"group_expelled"` in types |

---

### 2.9 SOCIAL — Blocked event gap documentation

| # | Test name | What it documents |
|---|---|---|
| S-23 | `test_gap_contract_milestone_completed_not_emitted` | No ContractState milestone field; event cannot be detected; comment cites strategic.py L177 |
| S-24 | `test_gap_social_memory_created_not_emitted` | social_memory_created requires entity.strategic.social_memories field; blocked pending investigation |

These tests are intentionally empty-assertion tests with doc comments (same pattern as AGENCY ticket's `defer_with_reason` gap tests).

---

### 2.10 FACTION — diplomatic_transition (PP-10)

| # | Test name | Condition | Assert |
|---|---|---|---|
| F-01 | `test_diplomatic_transition_emitted_from_faction_update` | `faction_updates` contains FactionUpdate with `diplomatic_relations_set` | `"diplomatic_transition"` in types |
| F-02 | `test_diplomatic_transition_payload_has_faction_id_and_target` | Same | `payload["faction_id"]`, `payload["target_faction_id"]`, `payload["new_state"]` |
| F-03 | `test_diplomatic_transition_deduped_per_pair` | Two FactionUpdates for same pair (a→b and b→a) | exactly 1 `"diplomatic_transition"` event |
| F-04 | `test_diplomatic_transition_not_emitted_on_empty_faction_updates` | `faction_updates == []` | `"diplomatic_transition"` not in types |

---

### 2.11 FACTION — alliance_accepted (PP-08/PP-10)

| # | Test name | Condition | Assert |
|---|---|---|---|
| F-05 | `test_alliance_accepted_emitted_when_allied_state_set` | FactionUpdate with `diplomatic_relations_set` containing ALLIED | `"alliance_accepted"` in types |
| F-06 | `test_alliance_accepted_payload_has_faction_pair` | Same | `payload["faction_id"]` and `payload["partner_id"]` |
| F-07 | `test_alliance_accepted_not_emitted_for_tense_transition` | FactionUpdate with TENSE (not ALLIED) | `"alliance_accepted"` not in types |

---

### 2.12 FACTION — war_declared (PP-10, WorldEvent)

| # | Test name | Condition | Assert |
|---|---|---|---|
| F-08 | `test_war_declared_emitted_from_world_events_add` | `world_events_add` contains WorldEvent with `category==FACTION_WAR_DECLARED` | `"war_declared"` in types |
| F-09 | `test_war_declared_payload_has_faction_pair` | Same | `payload["faction_pair"]` derived from WorldEvent.subject |
| F-10 | `test_war_declared_not_emitted_on_empty_world_events` | `world_events_add == []` | `"war_declared"` not in types |

---

### 2.13 FACTION — military_conflict_resolved (PP-11, WorldEvent)

| # | Test name | Condition | Assert |
|---|---|---|---|
| F-11 | `test_military_conflict_resolved_on_territory_transferred` | WorldEvent TERRITORY_TRANSFERRED | `"military_conflict_resolved"` in types |
| F-12 | `test_military_conflict_resolved_on_war_ended_exhaustion` | WorldEvent WAR_ENDED_EXHAUSTION | `"military_conflict_resolved"` in types |
| F-13 | `test_military_conflict_resolved_payload_has_subject` | Either trigger | `payload["subject"]` matches WorldEvent.subject |

---

### 2.14 FACTION — territory_ownership_changed (PP-11)

| # | Test name | Condition | Assert |
|---|---|---|---|
| F-14 | `test_territory_ownership_changed_on_territory_add` | FactionUpdate with `territory_add=("region_1",)` | `"territory_ownership_changed"` in types |
| F-15 | `test_territory_ownership_changed_payload_has_faction_and_region` | Same | `payload["faction_id"]` and `payload["region_id"]` |
| F-16 | `test_territory_ownership_changed_not_emitted_on_territory_remove` | FactionUpdate with only `territory_remove` | `"territory_ownership_changed"` not in types |

---

### 2.15 FACTION — faction_tension_delta (PP-09)

| # | Test name | Condition | Assert |
|---|---|---|---|
| F-17 | `test_faction_tension_delta_on_nonzero_tension_delta` | FactionUpdate with `tension_delta=0.1` | `"faction_tension_delta"` in types |
| F-18 | `test_faction_tension_delta_payload_has_delta` | Same | `payload["faction_id"]` and `payload["delta"]` |
| F-19 | `test_faction_tension_delta_not_emitted_on_zero_delta` | FactionUpdate with `tension_delta=0.0` | `"faction_tension_delta"` not in types |

---

### 2.16 FACTION — faction_extinct (state diff on factions)

| # | Test name | Condition | Assert |
|---|---|---|---|
| F-20 | `test_faction_extinct_emitted_when_no_living_entities` | Faction in current_state.factions; no living entity with matching faction; prior state had living entities | `"faction_extinct"` in types |
| F-21 | `test_faction_extinct_payload_has_faction_id` | Same | `payload["faction_id"]` |
| F-22 | `test_faction_extinct_not_emitted_when_living_entities_remain` | Faction has >= 1 living entity | `"faction_extinct"` not in types |

---

### 2.17 FACTION — Blocked event gap documentation

| # | Test name | What it documents |
|---|---|---|
| F-23 | `test_gap_alliance_proposed_not_emitted` | `faction_directives` is local var in pipeline.py:L171; not in StateUpdate; same architectural constraint as `defer_with_reason` in AGENCY ticket |
| F-24 | `test_gap_resource_seized_not_emitted` | No distinct `resource_seized` WorldEvent from MilitaryConflictPhase; TERRITORY_TRANSFERRED covers the region but not per-resource granularity; blocked pending WorldEvent schema extension |

---

## 3. Scoped pytest Commands

```bash
# New social+faction tests only
pytest tests/unit/observability/test_event_extractor_social_faction.py -v

# All extractor tests (regression + new)
pytest tests/unit/observability/test_event_extractor_simq.py \
       tests/unit/observability/test_event_extractor_agency.py \
       tests/unit/observability/test_event_extractor_cognition.py \
       tests/unit/observability/test_event_extractor_economy.py \
       tests/unit/observability/test_event_extractor_world.py \
       tests/unit/observability/test_event_extractor_social_faction.py \
       -v

# SimQ quality hub translation (verify leadership_changed / betrayal_desertion mappings)
pytest tests/simulation_quality/test_quality_hub_event_translation.py -v

# Full observability + simq suite (target: all pass, no scope creep)
pytest tests/unit/observability/ tests/simulation_quality/ -m "not slow" -v
```

---

## 4. Anti-Drift Test Guards

- **No import of `src/simulation_quality/` from EventExtractor or tests.** Assert at module
  level: `import ast; assert "simulation_quality" not in ast.unparse(...)` or use the
  existing import-guard pattern from cognition and agency tests.

- **Payload must include `entity_id` for all SOCIAL events.** FACTION events carry
  `faction_id` in payload, not `entity_id`. A mixed-payload test should verify each
  event category uses the correct key.

- **Contract bug fix guard:** Add a test that directly asserts `contract_completed` fires
  for a contract with `ContractStatus.FULFILLED` (name="FULFILLED"). This prevents
  regression of the enum alias bug if someone later changes the alias ordering.

- **Deduplication guard for diplomatic_transition:** Test with 4 factions (6 pairs) where
  all transition simultaneously; assert exactly 6 `diplomatic_transition` events (one per
  pair), not 12 (one per FactionUpdate).

- **`faction_updates` iteration must not break when list is empty.** Test with
  `StateUpdate()` (default, empty faction_updates) to verify no AttributeError.

- **`world_events_add` iteration guard:** Test with a StateUpdate that has no
  `world_events_add` attribute (uses `getattr(update, "world_events_add", None) or []`
  pattern consistent with existing `entities_add` handling at extractor:L425).
