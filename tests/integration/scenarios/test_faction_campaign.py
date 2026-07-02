"""Integration tests for E53Cc/E53Cd — territory transfer and war exhaustion.

Tickets: TCK-20260619-E53Cc-TERRITORY-TRANSFER, TCK-20260619-E53Cd-WAR-EXHAUSTION
AC: test_war_declared_and_territory_transferred, test_war_exhaustion_ends_conflict
"""
from __future__ import annotations

import pytest
from dataclasses import replace


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_faction(fid: str, territory=(), relations=None, military_strength=1.0):
    from src.core.state import FactionState
    from src.core.enums import DiplomaticState
    return FactionState(
        faction_id=fid,
        territory=tuple(territory),
        military_strength=military_strength,
        diplomatic_relations={k: DiplomaticState(v) if isinstance(v, str) else v
                               for k, v in (relations or {}).items()},
    )


def _make_region(rid: str, bounds=(0, 0, 100, 100)):
    from src.core.state import RegionState
    return RegionState(id=rid, name=rid, bounds=bounds)


def _apply_world_updates(regions, world_updates):
    """Apply siege-relevant WorldUpdate fields to regions dict.

    Mirrors the logic in apply_plan.py lines 125-140 for
    service_availability and siege_state mutations.
    """
    new_regions = dict(regions)
    for r_id, wu in world_updates.items():
        if r_id not in new_regions:
            continue
        reg = new_regions[r_id]
        svc_avail = max(0.0, min(1.0, reg.service_availability + wu.service_availability_delta))
        if wu.siege_state_clear:
            siege = None
        elif wu.siege_state_set is not None:
            siege = wu.siege_state_set
        else:
            siege = reg.siege_state
        if siege is not None and wu.siege_progress_delta != 0.0:
            new_progress = max(0.0, min(1.0, siege.siege_progress + wu.siege_progress_delta))
            siege = replace(siege, siege_progress=new_progress)
        new_regions[r_id] = replace(reg, siege_state=siege, service_availability=svc_avail)
    return new_regions


def _apply_faction_updates(factions, faction_updates):
    """Apply territory_add/remove from FactionUpdate list to factions dict.

    Mirrors the logic in apply.py lines 328-354 for territory fields only.
    """
    new_factions = dict(factions)
    for fu in faction_updates:
        existing = new_factions.get(fu.faction_id)
        if existing is None:
            continue
        new_territory = (set(existing.territory) | set(fu.territory_add)) - set(fu.territory_remove)
        new_factions[fu.faction_id] = replace(existing, territory=tuple(sorted(new_territory)))
    return new_factions


def _make_initial_state(tick=1):
    """Build a 3-faction scenario: ALPHA/BETA at WAR; BETA owns border_region."""
    from src.core.state import AuthoritativeState
    from src.core.enums import DiplomaticState as DS

    factions = {
        "ALPHA": _make_faction("ALPHA", territory=["home_alpha"],
                               relations={"BETA": DS.WAR, "GAMMA": DS.NEUTRAL}),
        "BETA":  _make_faction("BETA", territory=["border_region", "home_beta"],
                               relations={"ALPHA": DS.WAR, "GAMMA": DS.NEUTRAL}),
        "GAMMA": _make_faction("GAMMA", territory=["home_gamma"],
                               relations={"ALPHA": DS.NEUTRAL, "BETA": DS.NEUTRAL}),
    }
    regions = {
        "home_alpha":   _make_region("home_alpha",   bounds=(0,   0,  50,  50)),
        "border_region": _make_region("border_region", bounds=(60,  0, 110,  50)),
        "home_beta":    _make_region("home_beta",    bounds=(120, 0, 170,  50)),
        "home_gamma":   _make_region("home_gamma",   bounds=(200, 0, 250,  50)),
    }
    return AuthoritativeState(tick=tick, seed=42, factions=factions, regions=regions)


# ---------------------------------------------------------------------------
# Integration test
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_war_declared_and_territory_transferred():
    """3-faction scenario: ALPHA sieges BETA's border_region for 20 ticks.

    At +0.05 siege_progress per tick with no defending GUARD entities,
    progress reaches 1.0 at tick 20. On tick 21, MilitaryConflictPhase
    detects progress >= 1.0 and emits territory transfer.

    Assertions:
    - After transfer, ALPHA.territory contains 'border_region'
    - After transfer, BETA.territory does NOT contain 'border_region'
    - siege_state on border_region is None after transfer
    - service_availability on border_region is restored toward 1.0
    - At least one TERRITORY_TRANSFERRED WorldEvent is produced
    - GAMMA territory is not affected
    """
    from src.domains.world_emergence.schema import WorldEventCategory
    from src.engine.military_conflict import MilitaryConflictPhase

    state = _make_initial_state(tick=1)
    territory_transfer_events = []

    # Run 25 ticks — transfer should happen around tick 21
    for t in range(1, 26):
        state = replace(state, tick=t)
        su = MilitaryConflictPhase.execute(state)

        # Apply siege WorldUpdates
        new_regions = _apply_world_updates(state.regions, su.world_updates)

        # Apply FactionUpdate territory changes
        new_factions = _apply_faction_updates(state.factions, su.faction_updates)

        # Collect territory transfer events
        for ev in su.world_events_add:
            if ev.category == WorldEventCategory.TERRITORY_TRANSFERRED:
                territory_transfer_events.append(ev)

        state = replace(state, regions=new_regions, factions=new_factions)

    # At least one territory transfer event was emitted
    assert len(territory_transfer_events) >= 1, (
        "Expected TERRITORY_TRANSFERRED WorldEvent but none was emitted"
    )

    # ALPHA gained border_region
    alpha_territory = state.factions["ALPHA"].territory
    assert "border_region" in alpha_territory, (
        f"ALPHA should own border_region after siege; got territory={alpha_territory}"
    )

    # BETA lost border_region
    beta_territory = state.factions["BETA"].territory
    assert "border_region" not in beta_territory, (
        f"BETA should have lost border_region; got territory={beta_territory}"
    )

    # Siege state is cleared
    border = state.regions["border_region"]
    assert border.siege_state is None, (
        f"siege_state should be None after transfer; got {border.siege_state}"
    )

    # Service availability was restored (delta=+1.0, clamped to 1.0)
    assert border.service_availability == 1.0, (
        f"service_availability should be 1.0 after transfer; got {border.service_availability}"
    )

    # GAMMA is unaffected
    gamma_territory = state.factions["GAMMA"].territory
    assert "border_region" not in gamma_territory
    assert "home_gamma" in gamma_territory


@pytest.mark.slow
def test_siege_progress_accumulates_over_ticks():
    """service_availability decreases monotonically while siege is active (no GUARD defenders)."""
    from src.engine.military_conflict import MilitaryConflictPhase

    state = _make_initial_state(tick=1)
    prev_svc = 1.0

    for t in range(1, 10):  # 9 ticks, well before transfer
        state = replace(state, tick=t)
        su = MilitaryConflictPhase.execute(state)
        new_regions = _apply_world_updates(state.regions, su.world_updates)
        new_factions = _apply_faction_updates(state.factions, su.faction_updates)
        state = replace(state, regions=new_regions, factions=new_factions)

        current_svc = state.regions["border_region"].service_availability
        assert current_svc < prev_svc, (
            f"service_availability should decrease each tick; tick={t} prev={prev_svc} cur={current_svc}"
        )
        prev_svc = current_svc

    # After 9 ticks: 1.0 - 9*0.05 = 0.55
    import math
    assert math.isclose(prev_svc, 0.55, abs_tol=1e-6), (
        f"Expected ~0.55 after 9 siege ticks; got {prev_svc}"
    )


# ---------------------------------------------------------------------------
# E53Cd: War exhaustion integration test
# ---------------------------------------------------------------------------

def _apply_ms_drain(factions, faction_updates):
    """Apply military_strength_set from FactionUpdates (drain only)."""
    new_factions = dict(factions)
    for fu in faction_updates:
        existing = new_factions.get(fu.faction_id)
        if existing is None or fu.military_strength_set is None:
            continue
        new_factions[fu.faction_id] = replace(existing, military_strength=fu.military_strength_set)
    return new_factions


def _apply_diplomatic_transitions(factions):
    """Run DiplomaticStateMachine.compute_transitions() and apply results."""
    from src.domains.faction.diplomatic_state_machine import compute_transitions
    from src.core.enums import DiplomaticState
    transition_updates = compute_transitions(factions)
    new_factions = dict(factions)
    for fu in transition_updates:
        existing = new_factions.get(fu.faction_id)
        if existing is None:
            continue
        new_relations = {
            k: DiplomaticState(v) if not isinstance(v, DiplomaticState) else v
            for k, v in {**existing.diplomatic_relations, **fu.diplomatic_relations_set}.items()
        }
        new_factions[fu.faction_id] = replace(existing, diplomatic_relations=new_relations)
    return new_factions


@pytest.mark.slow
def test_war_exhaustion_ends_conflict():
    """2-faction WAR drains military_strength until DiplomaticStateMachine fires WAR→NEUTRAL.

    Setup: ALPHA, BETA both start at ms=0.302.
    Each tick: Phase 8d (compute_transitions) + Phase 8e (military_conflict drain).
    After 3 drain ticks: ms = 0.302 - 3*0.001 = 0.299 < 0.3.
    On tick 4: Phase 8d sees ms < 0.3 for both → WAR→NEUTRAL fires.

    Assertions:
    - ALPHA–BETA relation transitions to NEUTRAL
    - WAR_ENDED_EXHAUSTION WorldEvent is emitted (on the tick ms crosses 0.3)
    - military_strength of both factions is below 0.3 at end
    - Orphaned siege (if any) is cleared after transition to NEUTRAL
    """
    from src.core.state import AuthoritativeState
    from src.core.enums import DiplomaticState as DS
    from src.engine.military_conflict import MilitaryConflictPhase
    from src.domains.world_emergence.schema import WorldEventCategory

    factions = {
        "ALPHA": _make_faction("ALPHA", military_strength=0.302, relations={"BETA": DS.WAR}),
        "BETA":  _make_faction("BETA",  military_strength=0.302, relations={"ALPHA": DS.WAR}),
    }
    regions = {}  # no territory, no sieges — pure exhaustion test

    exhaustion_events = []
    reached_neutral = False

    for t in range(1, 20):
        state = AuthoritativeState(tick=t, seed=42, factions=factions, regions=regions)

        # Phase 8d: diplomatic transitions (WAR→NEUTRAL fires when both ms < 0.3)
        factions = _apply_diplomatic_transitions(factions)

        # Check if peace was reached
        alpha_rel = factions["ALPHA"].diplomatic_relations.get("BETA", DS.NEUTRAL)
        if alpha_rel == DS.NEUTRAL:
            reached_neutral = True
            break

        # Phase 8e: military conflict (drain + events)
        su = MilitaryConflictPhase.execute(state)

        # Collect exhaustion events
        for ev in su.world_events_add:
            if ev.category == WorldEventCategory.WAR_ENDED_EXHAUSTION:
                exhaustion_events.append(ev)

        # Apply military_strength drain
        factions = _apply_ms_drain(factions, su.faction_updates)

    # WAR→NEUTRAL was reached
    assert reached_neutral, (
        f"Expected WAR→NEUTRAL transition via exhaustion; final factions: "
        f"ALPHA={factions['ALPHA'].diplomatic_relations}, BETA={factions['BETA'].diplomatic_relations}"
    )

    # ALPHA–BETA are now NEUTRAL
    assert factions["ALPHA"].diplomatic_relations.get("BETA") == DS.NEUTRAL
    assert factions["BETA"].diplomatic_relations.get("ALPHA") == DS.NEUTRAL

    # WAR_ENDED_EXHAUSTION event was emitted before peace was declared
    assert len(exhaustion_events) >= 1, (
        "Expected WAR_ENDED_EXHAUSTION WorldEvent before/at exhaustion threshold"
    )

    # Both factions below the peace threshold
    assert factions["ALPHA"].military_strength < 0.3
    assert factions["BETA"].military_strength < 0.3
