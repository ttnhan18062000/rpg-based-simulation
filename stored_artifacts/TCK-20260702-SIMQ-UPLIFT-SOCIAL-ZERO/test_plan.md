# Test Plan — TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO

**Ticket:** TCK-20260702-SIMQ-UPLIFT-SOCIAL-ZERO  
**Date:** 2026-07-02  
**Tier:** standard  
**Phase:** investigation complete; implementation pending

---

## Regression Surface (existing tests that must pass)

All existing SimQ tests must pass without modification. Key suites:

| Suite | File | Guards |
|---|---|---|
| EventExtractor social/faction | `tests/unit/observability/test_event_extractor_social_faction.py` | cooperation_event, diplomatic_transition, alliance_accepted, war_declared, faction_tension_delta, social_memory_created, contract_* emission |
| EventExtractor information/cognition | `tests/unit/observability/test_event_extractor_lead_beliefs.py` | belief_assimilated, lead_certainty_updated, belief_stale, decision_diverged_by_belief |
| QualityHub translation | `tests/simulation_quality/test_quality_hub_event_translation.py` | All _TRANSLATE_SIMPLE and _TRANSLATE_CONDITIONAL entries |
| FactionScorer | `tests/simulation_quality/test_faction_scorer.py` | diplomatic_transition scoring, dormancy path, tension_active path |
| SocialScorer | `tests/simulation_quality/test_social_scorer.py` | cooperation_active, contract_honored, relationship_depth |
| InformationScorer | `tests/simulation_quality/test_information_scorer.py` | belief_active, intel_quality_up, knowledge_economy_active |
| DiplomaticStateMachine | `tests/unit/faction/test_diplomatic_state_machine.py` | NEUTRAL→TENSE, TENSE→HOSTILE, HOSTILE→WAR, alliance |
| CooperationPhase | `tests/unit/domains/cooperation/test_cooperation_phase.py` | Decision output, trust_delta write, contract intent |
| InformationBeliefPhase | `tests/unit/domains/information/test_information_belief_phase.py` | assimilation with pending_responses |
| FactionAwarenessService | `tests/unit/engine/test_faction_decision.py` | tension delta from RESOURCE_DEPLETED in territory |

Scoped regression command:
```
pytest tests/unit/observability/test_event_extractor_social_faction.py \
       tests/unit/observability/test_event_extractor_lead_beliefs.py \
       tests/simulation_quality/test_quality_hub_event_translation.py \
       tests/simulation_quality/test_faction_scorer.py \
       tests/simulation_quality/test_social_scorer.py \
       tests/simulation_quality/test_information_scorer.py \
       -v
```

---

## New Tests Required (per AC)

### T-1: FACTION — Diagnostic: confirm state.factions is empty in calibration worlds

**File:** `tests/simulation_quality/test_faction_activation_diagnostic.py`  
**Purpose:** Confirm root cause (c1) — world content gap.

```python
def test_sandbox_world_factions_empty():
    """state.factions must be empty or all factions have tension_level=0.0 and territory=()."""
    state = build_world_state("sandbox_world")
    if not state.factions:
        return  # confirmed empty — root cause validated
    for fid, fs in state.factions.items():
        assert fs.tension_level == 0.0, f"faction {fid} has non-zero tension — unexpected"
        assert fs.territory == (), f"faction {fid} has territory — unexpected"

def test_dungeon_crawl_factions_empty():
    state = build_world_state("dungeon_crawl")
    # Same assertion
```

### T-2: FACTION — DiplomaticStateMachine fires NEUTRAL→TENSE when tension seeded

**File:** `tests/simulation_quality/test_faction_activation_diagnostic.py`  
**Purpose:** Confirm the mechanics work once world content is corrected.

```python
def test_diplomatic_transition_fires_when_tension_above_threshold():
    factions = {
        "faction_a": FactionState(faction_id="faction_a", tension_level=0.5,
                                   diplomatic_relations={"faction_b": DiplomaticState.NEUTRAL}),
        "faction_b": FactionState(faction_id="faction_b", tension_level=0.5,
                                   diplomatic_relations={"faction_a": DiplomaticState.NEUTRAL}),
    }
    updates = compute_transitions(factions)
    assert any(
        "faction_b" in u.diplomatic_relations_set and
        u.diplomatic_relations_set["faction_b"] == DiplomaticState.TENSE
        for u in updates
    ), "Expected NEUTRAL→TENSE transition when pair_tension=0.5"
```

### T-3: FACTION — EventExtractor emits faction_tension_delta from FactionUpdate with tension

**File:** `tests/unit/observability/test_event_extractor_social_faction.py` (extend existing)  
**Purpose:** Confirm end-to-end: FactionUpdate → EventExtractor → faction_tension_delta.

This test already exists (test_faction_tension_delta_on_nonzero_tension_delta). Verify it passes as-is — if so, (a) is already ruled out for faction_tension_delta.

### T-4: SOCIAL — CooperationPhase sets last_cooperation_decision in property_updates

**File:** `tests/unit/domains/cooperation/test_cooperation_phase.py` (extend or create)  
**Purpose:** Confirm CooperationPhase produces EntityUpdate.property_updates["last_cooperation_decision"] when flag is ON.

```python
def test_cooperation_phase_sets_property_when_enabled():
    state = build_minimal_state_with_active_entities(count=3)
    # Do NOT mock feature flags — CooperationPhase checks state.social_cooperation_enabled
    state = replace(state, social_cooperation_enabled=True)
    update = StateUpdate()
    result = CooperationPhase.execute(state, update)
    found = any(
        "last_cooperation_decision" in e_upd.property_updates
        for e_upd in result.entity_updates.values()
    )
    assert found, "CooperationPhase must set last_cooperation_decision in property_updates for eligible entities"
```

### T-5: SOCIAL — cooperation_event emitted when CooperationPhase runs end-to-end

**File:** `tests/integration/test_simq_social_activation.py` (new)  
**Purpose:** Integration test: run 50 ticks with ENABLE_SOCIAL_COOPERATION=ON and verify ≥1 SOCIAL calibration_hit in quality_scores.

```python
def test_social_scores_non_zero_with_cooperation_enabled():
    """AC verification: ≥1 SOCIAL event after enabling CooperationPhase."""
    state = build_calibration_state("sandbox_world", seed=42)
    state = inject_feature_flag(state, "ENABLE_SOCIAL_COOPERATION", FeatureMode.ON)
    records = run_calibration(state, ticks=100, collect_quality_records=True)
    social_records = [r for r in records if r.pillar == PillarId.SOCIAL]
    assert len(social_records) >= 1, (
        f"Expected ≥1 SOCIAL quality record after 100 ticks with CooperationPhase ON. Got 0."
    )
```

### T-6: INFORMATION — InformationBeliefPhase produces last_assimilated_tick when responses seeded

**File:** `tests/unit/domains/information/test_information_belief_phase.py` (extend)  
**Purpose:** Confirm that with pending_responses and source_profiles non-empty, the phase writes property_updates["last_assimilated_tick"].

```python
def test_information_belief_phase_writes_assimilation_tick():
    actor = build_active_entity(id=1)
    state = build_minimal_state(entities={1: actor})
    pending = [{"actor_id": 1, "subject": "ore_vein", "query_kind": "material_source",
                "source_id": "info_npc_1", "raw_response": {"location": "east"}, "cost_paid": 10}]
    profiles = [InformationSourceProfile(source_id="info_npc_1", region_id="r1")]
    result = InformationBeliefPhase.apply(state, profiles, pending_responses=pending)
    assert 1 in result.entity_updates
    assert result.entity_updates[1].property_updates.get("last_assimilated_tick") == state.tick
```

### T-7: INFORMATION — belief_assimilated emitted when last_assimilated_tick set

**File:** `tests/unit/observability/test_event_extractor_lead_beliefs.py` (extend or verify)  
**Purpose:** Confirm EventExtractor emits belief_assimilated when `prop["last_assimilated_tick"] == tick`. This may already exist — verify.

### T-8: FACTION — FactionAwarenessService fires tension_delta when faction has territory and RESOURCE_DEPLETED event

**File:** `tests/unit/engine/test_faction_decision.py` (extend)

```python
def test_faction_awareness_fires_when_faction_has_territory():
    factions = {"f1": FactionState(faction_id="f1", territory=("region_1",))}
    events = [WorldEvent(category=WorldEventCategory.RESOURCE_DEPLETED, region_id="region_1", tick=5)]
    state = build_minimal_state(factions=factions)
    updates = FactionAwarenessService.compute_tension_updates(state, events)
    assert any(u.faction_id == "f1" and u.tension_delta > 0 for u in updates)
```

This test likely already exists — verify pass status.

### T-9: End-to-end calibration verification post-fix (AC §4)

**File:** `tests/integration/test_simq_pillar_activation.py` (new)  
**Purpose:** After all fixes applied, run calibration with corrected world content and flags and confirm ≥1 hit per pillar (or document which pillars remain zero with rationale).

```python
@pytest.mark.parametrize("pillar", [PillarId.FACTION, PillarId.SOCIAL])
def test_pillar_non_zero_after_activation(pillar):
    """Acceptance: at least one pillar among FACTION/SOCIAL scores ≥1 calibration_hit post-fix."""
    records = run_full_calibration(world="sandbox_world", seed=42, ticks=200,
                                   flags={"ENABLE_SOCIAL_COOPERATION": FeatureMode.ON},
                                   world_overrides={"faction_tension_seed": 0.5})
    hits = [r for r in records if r.pillar == pillar]
    assert len(hits) >= 1, f"Expected ≥1 {pillar} hit post-fix, got 0"
```

---

## Scoped Pytest Commands

### Phase 1 — Regression (before any code changes):
```bash
pytest tests/unit/observability/test_event_extractor_social_faction.py \
       tests/unit/observability/test_event_extractor_lead_beliefs.py \
       tests/simulation_quality/ \
       -v --tb=short -x
```

### Phase 2 — New diagnostic tests (root cause confirmation):
```bash
pytest tests/simulation_quality/test_faction_activation_diagnostic.py -v
```

### Phase 3 — Feature flag and phase activation tests:
```bash
pytest tests/unit/domains/cooperation/test_cooperation_phase.py \
       tests/unit/domains/information/test_information_belief_phase.py \
       tests/unit/engine/test_faction_decision.py \
       -v --tb=short
```

### Phase 4 — Integration (post-fix AC verification):
```bash
pytest tests/integration/test_simq_social_activation.py \
       tests/integration/test_simq_pillar_activation.py \
       -v --tb=short -s
```

### Full scoped suite (no slow tests):
```bash
pytest tests/unit/observability/ tests/unit/domains/cooperation/ \
       tests/unit/domains/information/ tests/unit/engine/test_faction_decision.py \
       tests/simulation_quality/ tests/integration/test_simq_social_activation.py \
       -m "not slow" -v --tb=short
```

---

## Anti-Drift Test Guards

### G-1: Calibration_hits must be non-zero after fix (regression guard)

After fix is implemented and verified, add an assertion in `tests/simulation_quality/test_calibration_coverage.py` (create if absent):

```python
EXPECTED_NON_ZERO_PILLARS_AFTER_FIX = {PillarId.SOCIAL, PillarId.FACTION}

def test_calibration_hits_non_zero_for_activated_pillars():
    """Guard: SOCIAL and FACTION pillars must have ≥1 calibration hit after activation fix.
    
    If this test fails, either:
    - CooperationPhase was re-disabled (ENABLE_SOCIAL_COOPERATION reverted to OFF)
    - World content was reverted (faction tension_level reset to 0.0)
    - EventExtractor emission was broken
    """
    records = load_calibration_records()  # from data/calibration/
    hits_by_pillar = Counter(r.pillar for r in records)
    for pillar in EXPECTED_NON_ZERO_PILLARS_AFTER_FIX:
        assert hits_by_pillar[pillar] >= 1, (
            f"Regression: {pillar} dropped to 0 calibration_hits. "
            f"Check ENABLE_SOCIAL_COOPERATION flag and faction world content."
        )
```

### G-2: Feature flag state must be recorded in calibration metadata

Any calibration run infrastructure must record which feature flags were active. Without this, a calibration corpus cannot be interpreted (did SOCIAL score 0 because broken, or because the flag was OFF?).

### G-3: CooperationPhase feature flag test

```python
def test_cooperation_phase_is_skipped_when_flag_off():
    """Guard: CooperationPhase must produce no property_updates when ENABLE_SOCIAL_COOPERATION=OFF."""
    state = build_minimal_state_with_active_entities(count=3)
    # Default state — flag not set, social_cooperation_enabled not set
    update = StateUpdate()
    result = CooperationPhase.execute(state, update)
    # Must not set last_cooperation_decision for any entity
    for e_upd in result.entity_updates.values():
        assert "last_cooperation_decision" not in e_upd.property_updates, (
            "CooperationPhase must not set last_cooperation_decision when disabled"
        )
```

### G-4: FactionState default tension guard

```python
def test_faction_state_default_tension_is_zero():
    """Guard: FactionState default tension_level must remain 0.0.
    
    If this changes, the diplomatic state machine will fire without world content seeding it,
    which may cause unexpected test failures across the codebase.
    """
    fs = FactionState(faction_id="test")
    assert fs.tension_level == 0.0
    assert fs.territory == ()
```

### G-5: event_type_coverage.md must record calibration_hits after any calibration refresh

The table in `docs/simulation_quality/event_type_coverage.md` §1.1 currently shows `calibration_hits=0` for all FACTION/SOCIAL/INFORMATION events. After fix:
- Update rows to reflect verified non-zero hits with a note referencing this ticket.
- Include the world+tick-count+flags used for verification.
- Run `make knowledge-index-update` after any doc update.
