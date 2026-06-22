"""Unit tests for DiplomaticState enum and FactionState migration (E53Ba)."""
import pytest


def test_diplomatic_state_enum_importable():
    """DiplomaticState is importable from src.core.enums with all expected members."""
    from src.core.enums import DiplomaticState

    assert DiplomaticState.NEUTRAL.value == "NEUTRAL"
    assert DiplomaticState.TENSE.value == "TENSE"
    assert DiplomaticState.HOSTILE.value == "HOSTILE"
    assert DiplomaticState.WAR.value == "WAR"
    assert DiplomaticState.ALLIED.value == "ALLIED"
    assert DiplomaticState.VASSAL.value == "VASSAL"


def test_diplomatic_state_str_coercion():
    """DiplomaticState("ALLIED") == DiplomaticState.ALLIED (str-enum coercion)."""
    from src.core.enums import DiplomaticState

    assert DiplomaticState("ALLIED") == DiplomaticState.ALLIED
    assert DiplomaticState("HOSTILE") == DiplomaticState.HOSTILE
    assert DiplomaticState("NEUTRAL") == DiplomaticState.NEUTRAL


def test_diplomatic_state_enum_round_trip():
    """FactionState with DiplomaticState values serializes and deserializes with round-trip fidelity."""
    from src.core.state import FactionState
    from src.core.enums import DiplomaticState

    fs = FactionState(
        faction_id="hero_guild",
        diplomatic_relations={
            "monster_horde": DiplomaticState.HOSTILE,
            "town_council": DiplomaticState.ALLIED,
        },
    )
    d = fs.to_canonical_dict()
    restored = FactionState.from_dict(d)

    assert restored == fs
    assert restored.diplomatic_relations["monster_horde"] == DiplomaticState.HOSTILE
    assert restored.diplomatic_relations["town_council"] == DiplomaticState.ALLIED


def test_canonical_dict_emits_string_values():
    """to_canonical_dict() emits plain string values (not enum objects) for JSON compatibility."""
    from src.core.state import FactionState
    from src.core.enums import DiplomaticState

    fs = FactionState(
        faction_id="f1",
        diplomatic_relations={"f2": DiplomaticState.WAR},
    )
    d = fs.to_canonical_dict()

    val = d["diplomatic_relations"]["f2"]
    assert val == "WAR"
    assert type(val) is str


def test_from_dict_coerces_string_values():
    """FactionState.from_dict() with string values reconstructs typed DiplomaticState values."""
    from src.core.state import FactionState
    from src.core.enums import DiplomaticState

    raw = {
        "faction_id": "f1",
        "diplomatic_relations": {"f2": "VASSAL"},
    }
    fs = FactionState.from_dict(raw)

    assert isinstance(fs.diplomatic_relations["f2"], DiplomaticState)
    assert fs.diplomatic_relations["f2"] == DiplomaticState.VASSAL


def test_faction_state_diplomatic_relations_apply():
    """FactionUpdate.diplomatic_relations_set only updates the specified key; other keys preserved."""
    from src.core.state import AuthoritativeState, FactionState
    from src.core.updates import StateUpdate, FactionUpdate
    from src.core.enums import DiplomaticState
    from src.engine.apply import ApplyPath

    fs = FactionState(
        faction_id="hero_guild",
        diplomatic_relations={
            "monster_horde": DiplomaticState.HOSTILE,
            "town_council": DiplomaticState.NEUTRAL,
        },
    )
    state = AuthoritativeState(tick=1, seed=0, factions={"hero_guild": fs})

    update = StateUpdate(
        faction_updates=[
            FactionUpdate(
                faction_id="hero_guild",
                diplomatic_relations_set={"town_council": DiplomaticState.ALLIED},
            )
        ]
    )
    new_state = ApplyPath.apply_partial(state, update)
    result = new_state.factions["hero_guild"]

    assert result.diplomatic_relations["monster_horde"] == DiplomaticState.HOSTILE
    assert result.diplomatic_relations["town_council"] == DiplomaticState.ALLIED


def test_faction_update_diplomatic_relations_set_not_noop():
    """FactionUpdate with non-empty diplomatic_relations_set is not a noop."""
    from src.core.updates import FactionUpdate
    from src.core.enums import DiplomaticState

    fu = FactionUpdate(faction_id="x", diplomatic_relations_set={"y": DiplomaticState.TENSE})
    assert not fu.is_noop()


def test_faction_update_empty_diplomatic_relations_set_is_noop():
    """FactionUpdate with empty diplomatic_relations_set (default) counts as noop for that field."""
    from src.core.updates import FactionUpdate

    fu = FactionUpdate(faction_id="x")
    assert fu.is_noop()


# ── E53Bb: Diplomatic Action Handler Tests ────────────────────────────────────

def _make_factions(pairs):
    """Build a minimal factions dict: [(faction_id, military_strength, relations), ...]"""
    from src.core.state import FactionState
    result = {}
    for faction_id, military_strength, relations in pairs:
        result[faction_id] = FactionState(
            faction_id=faction_id,
            military_strength=military_strength,
            diplomatic_relations=relations,
        )
    return result


def test_diplomatic_action_alliance_proposal_both_allied():
    """AllianceProposal where proposer < 2x target strength → both set to ALLIED."""
    from src.engine.faction_decision import AllianceProposal
    from src.domains.faction.diplomatic_actions import handle
    from src.core.enums import DiplomaticState

    factions = _make_factions([
        ("faction_a", 1.0, {}),
        ("faction_b", 1.0, {}),
    ])
    action = AllianceProposal(
        faction_id="faction_a",
        directive_kind="ALLIANCE_PROPOSAL",
        from_faction="faction_a",
        to_faction="faction_b",
        proposer_strength=1.0,
    )
    updates = handle(action, factions)

    assert len(updates) == 2
    a_update = next(u for u in updates if u.faction_id == "faction_a")
    b_update = next(u for u in updates if u.faction_id == "faction_b")
    assert a_update.diplomatic_relations_set["faction_b"] == DiplomaticState.ALLIED
    assert b_update.diplomatic_relations_set["faction_a"] == DiplomaticState.ALLIED


def test_diplomatic_action_alliance_proposal_vassal():
    """AllianceProposal where proposer >= 2x target strength → target becomes VASSAL."""
    from src.engine.faction_decision import AllianceProposal
    from src.domains.faction.diplomatic_actions import handle
    from src.core.enums import DiplomaticState

    factions = _make_factions([
        ("empire", 3.0, {}),
        ("village", 1.0, {}),
    ])
    action = AllianceProposal(
        faction_id="empire",
        directive_kind="ALLIANCE_PROPOSAL",
        from_faction="empire",
        to_faction="village",
        proposer_strength=3.0,
    )
    updates = handle(action, factions)

    assert len(updates) == 2
    empire_update = next(u for u in updates if u.faction_id == "empire")
    village_update = next(u for u in updates if u.faction_id == "village")
    assert empire_update.diplomatic_relations_set["village"] == DiplomaticState.ALLIED
    assert village_update.diplomatic_relations_set["empire"] == DiplomaticState.VASSAL


def test_diplomatic_action_betrayal_valid():
    """Betrayal when current relation is ALLIED → both HOSTILE; betrayed gets +0.3 tension."""
    from src.engine.faction_decision import Betrayal
    from src.domains.faction.diplomatic_actions import handle
    from src.core.enums import DiplomaticState

    factions = _make_factions([
        ("traitor", 1.0, {"victim": DiplomaticState.ALLIED}),
        ("victim", 1.0, {"traitor": DiplomaticState.ALLIED}),
    ])
    action = Betrayal(
        faction_id="traitor",
        directive_kind="BETRAYAL",
        from_faction="traitor",
        to_faction="victim",
    )
    updates = handle(action, factions)

    assert len(updates) == 2
    traitor_upd = next(u for u in updates if u.faction_id == "traitor")
    victim_upd = next(u for u in updates if u.faction_id == "victim")
    assert traitor_upd.diplomatic_relations_set["victim"] == DiplomaticState.HOSTILE
    assert victim_upd.diplomatic_relations_set["traitor"] == DiplomaticState.HOSTILE
    assert victim_upd.tension_delta == pytest.approx(0.3)


def test_diplomatic_action_betrayal_invalid_not_allied():
    """Betrayal when current relation is not ALLIED → empty list (no-op)."""
    from src.engine.faction_decision import Betrayal
    from src.domains.faction.diplomatic_actions import handle
    from src.core.enums import DiplomaticState

    factions = _make_factions([
        ("faction_a", 1.0, {"faction_b": DiplomaticState.NEUTRAL}),
        ("faction_b", 1.0, {}),
    ])
    action = Betrayal(
        faction_id="faction_a",
        directive_kind="BETRAYAL",
        from_faction="faction_a",
        to_faction="faction_b",
    )
    updates = handle(action, factions)
    assert updates == []


def test_diplomatic_action_trade_agreement():
    """TradeAgreement → both factions NEUTRAL and tension_delta -0.15."""
    from src.engine.faction_decision import TradeAgreement
    from src.domains.faction.diplomatic_actions import handle
    from src.core.enums import DiplomaticState

    factions = _make_factions([
        ("merchant_a", 1.0, {}),
        ("merchant_b", 1.0, {}),
    ])
    action = TradeAgreement(
        faction_id="merchant_a",
        directive_kind="TRADE_AGREEMENT",
        from_faction="merchant_a",
        to_faction="merchant_b",
    )
    updates = handle(action, factions)

    assert len(updates) == 2
    for upd in updates:
        assert upd.tension_delta == pytest.approx(-0.15)
    a_upd = next(u for u in updates if u.faction_id == "merchant_a")
    assert a_upd.diplomatic_relations_set["merchant_b"] == DiplomaticState.NEUTRAL


def test_diplomatic_action_noop_when_not_accepted():
    """TreatyOffer(accepted=False) → empty list (outgoing offer not yet responded)."""
    from src.engine.faction_decision import TreatyOffer
    from src.domains.faction.diplomatic_actions import handle

    factions = _make_factions([("f_a", 1.0, {}), ("f_b", 1.0, {})])
    action = TreatyOffer(
        faction_id="f_a",
        directive_kind="TREATY_OFFER",
        from_faction="f_a",
        to_faction="f_b",
        terms="trade",
        accepted=False,
    )
    updates = handle(action, factions)
    assert updates == []


def test_diplomatic_action_non_aggression_pact():
    """NonAggressionPact → both NEUTRAL, no tension change."""
    from src.engine.faction_decision import NonAggressionPact
    from src.domains.faction.diplomatic_actions import handle
    from src.core.enums import DiplomaticState

    factions = _make_factions([("f_a", 1.0, {}), ("f_b", 1.0, {})])
    action = NonAggressionPact(
        faction_id="f_a",
        directive_kind="NON_AGGRESSION_PACT",
        from_faction="f_a",
        to_faction="f_b",
    )
    updates = handle(action, factions)

    assert len(updates) == 2
    for upd in updates:
        assert upd.tension_delta == pytest.approx(0.0)
    a_upd = next(u for u in updates if u.faction_id == "f_a")
    assert a_upd.diplomatic_relations_set["f_b"] == DiplomaticState.NEUTRAL


# ── E53Bc: Diplomatic State Machine Tests ─────────────────────────────────────

def _make_faction(fid, tension=0.0, military_strength=1.0, territory=(), relations=None):
    from src.core.state import FactionState
    return FactionState(
        faction_id=fid,
        tension_level=tension,
        military_strength=military_strength,
        territory=territory,
        diplomatic_relations=relations or {},
    )


def test_diplomatic_state_transitions_valid():
    """Covers NEUTRAL→TENSE, TENSE→HOSTILE, HOSTILE→WAR, WAR→NEUTRAL, single-step."""
    from src.domains.faction.diplomatic_state_machine import compute_transitions
    from src.core.enums import DiplomaticState

    # Case 1: NEUTRAL → TENSE when pair_tension > 0.4
    factions = {
        "fa": _make_faction("fa", tension=0.5),
        "fb": _make_faction("fb", tension=0.0),
    }
    updates = compute_transitions(factions)
    assert any(u.diplomatic_relations_set.get("fb") == DiplomaticState.TENSE for u in updates if u.faction_id == "fa")

    # Case 2: TENSE → HOSTILE when pair_tension > 0.7
    from src.core.enums import DiplomaticState as DS
    factions2 = {
        "fa": _make_faction("fa", tension=0.8, relations={"fb": DS.TENSE}),
        "fb": _make_faction("fb", tension=0.0, relations={"fa": DS.TENSE}),
    }
    updates2 = compute_transitions(factions2)
    assert any(u.diplomatic_relations_set.get("fb") == DS.HOSTILE for u in updates2 if u.faction_id == "fa")

    # Case 3: NEUTRAL at tension=0.9 → only TENSE (single-step, not HOSTILE in one call)
    factions3 = {
        "fa": _make_faction("fa", tension=0.9),
        "fb": _make_faction("fb", tension=0.0),
    }
    updates3 = compute_transitions(factions3)
    assert any(u.diplomatic_relations_set.get("fb") == DS.TENSE for u in updates3 if u.faction_id == "fa")
    assert not any(u.diplomatic_relations_set.get("fb") == DS.HOSTILE for u in updates3)

    # Case 4: HOSTILE → WAR when military_strength aggressor > defender * 1.2
    factions4 = {
        "fa": _make_faction("fa", military_strength=2.0, relations={"fb": DS.HOSTILE}),
        "fb": _make_faction("fb", military_strength=1.0, relations={"fa": DS.HOSTILE}),
    }
    updates4 = compute_transitions(factions4)
    assert any(u.diplomatic_relations_set.get("fb") == DS.WAR for u in updates4 if u.faction_id == "fa")

    # Case 5: WAR → NEUTRAL when both military_strength < 0.3
    factions5 = {
        "fa": _make_faction("fa", military_strength=0.2, relations={"fb": DS.WAR}),
        "fb": _make_faction("fb", military_strength=0.1, relations={"fa": DS.WAR}),
    }
    updates5 = compute_transitions(factions5)
    assert any(u.diplomatic_relations_set.get("fb") == DS.NEUTRAL for u in updates5 if u.faction_id == "fa")


def test_alliance_reduces_shared_territory_threat():
    """ALLIED state suppresses TENSE→HOSTILE even when both factions share territory."""
    from src.domains.faction.diplomatic_state_machine import compute_transitions
    from src.core.enums import DiplomaticState as DS

    # Two ALLIED factions sharing territory — should NOT trigger TENSE→HOSTILE
    factions = {
        "fa": _make_faction("fa", tension=0.5, territory=("region_01",), relations={"fb": DS.ALLIED}),
        "fb": _make_faction("fb", tension=0.5, territory=("region_01",), relations={"fa": DS.ALLIED}),
    }
    updates = compute_transitions(factions)
    assert updates == [], f"Expected no updates for ALLIED pair, got: {updates}"


def test_no_transitions_when_below_thresholds():
    """No transitions when tension=0.2 (below 0.4 threshold) and no shared territory."""
    from src.domains.faction.diplomatic_state_machine import compute_transitions

    factions = {
        "fa": _make_faction("fa", tension=0.2),
        "fb": _make_faction("fb", tension=0.1),
    }
    updates = compute_transitions(factions)
    assert updates == []


def test_tense_to_hostile_from_shared_territory():
    """TENSE → HOSTILE fires when factions share territory even at tension < 0.7."""
    from src.domains.faction.diplomatic_state_machine import compute_transitions
    from src.core.enums import DiplomaticState as DS

    factions = {
        "fa": _make_faction("fa", tension=0.5, territory=("region_01",), relations={"fb": DS.TENSE}),
        "fb": _make_faction("fb", tension=0.0, territory=("region_01",), relations={"fa": DS.TENSE}),
    }
    updates = compute_transitions(factions)
    assert any(u.diplomatic_relations_set.get("fb") == DS.HOSTILE for u in updates if u.faction_id == "fa")


def test_war_to_neutral_exhaustion():
    """WAR → NEUTRAL when both military_strength < 0.3."""
    from src.domains.faction.diplomatic_state_machine import compute_transitions
    from src.core.enums import DiplomaticState as DS

    factions = {
        "fa": _make_faction("fa", military_strength=0.25, relations={"fb": DS.WAR}),
        "fb": _make_faction("fb", military_strength=0.15, relations={"fa": DS.WAR}),
    }
    updates = compute_transitions(factions)
    assert any(u.diplomatic_relations_set.get("fb") == DS.NEUTRAL for u in updates if u.faction_id == "fa")
    assert any(u.diplomatic_relations_set.get("fa") == DS.NEUTRAL for u in updates if u.faction_id == "fb")


def test_vassal_suppresses_transitions():
    """VASSAL state (like ALLIED) suppresses all threshold-driven transitions."""
    from src.domains.faction.diplomatic_state_machine import compute_transitions
    from src.core.enums import DiplomaticState as DS

    factions = {
        "fa": _make_faction("fa", tension=0.9, military_strength=5.0, relations={"fb": DS.VASSAL}),
        "fb": _make_faction("fb", tension=0.9, military_strength=0.1, relations={"fa": DS.VASSAL}),
    }
    updates = compute_transitions(factions)
    assert updates == [], f"Expected no updates for VASSAL pair, got: {updates}"


# ---------------------------------------------------------------------------
# E53Bd — WorldEvent emission and NarrativeLedger wiring
# ---------------------------------------------------------------------------

def test_events_from_transitions_war_declared():
    """HOSTILE→WAR transition produces FACTION_WAR_DECLARED WorldEvent."""
    from src.domains.faction.diplomatic_state_machine import compute_transitions, events_from_transitions
    from src.domains.world_emergence.schema import WorldEventCategory
    from src.core.enums import DiplomaticState as DS

    factions = {
        "fa": _make_faction("fa", military_strength=1.5, relations={"fb": DS.HOSTILE}),
        "fb": _make_faction("fb", military_strength=1.0, relations={"fa": DS.HOSTILE}),
    }
    transition_upds = compute_transitions(factions)
    world_events = events_from_transitions(transition_upds, [], factions, tick=5)

    war_events = [e for e in world_events if e.category == WorldEventCategory.FACTION_WAR_DECLARED]
    assert len(war_events) == 1
    assert war_events[0].subject == "fa:fb"
    assert war_events[0].tick == 5


def test_events_from_transitions_peace_treaty():
    """WAR→NEUTRAL exhaustion transition produces FACTION_PEACE_TREATY WorldEvent."""
    from src.domains.faction.diplomatic_state_machine import compute_transitions, events_from_transitions
    from src.domains.world_emergence.schema import WorldEventCategory
    from src.core.enums import DiplomaticState as DS

    factions = {
        "fa": _make_faction("fa", military_strength=0.2, relations={"fb": DS.WAR}),
        "fb": _make_faction("fb", military_strength=0.15, relations={"fa": DS.WAR}),
    }
    transition_upds = compute_transitions(factions)
    world_events = events_from_transitions(transition_upds, [], factions, tick=10)

    peace_events = [e for e in world_events if e.category == WorldEventCategory.FACTION_PEACE_TREATY]
    assert len(peace_events) == 1
    assert peace_events[0].subject == "fa:fb"


def test_events_from_transitions_alliance_formed():
    """Alliance updates produce FACTION_ALLIANCE_FORMED WorldEvent (deduped to one per pair)."""
    from src.core.enums import DiplomaticState as DS
    from src.core.updates import FactionUpdate
    from src.domains.faction.diplomatic_state_machine import events_from_transitions
    from src.domains.world_emergence.schema import WorldEventCategory

    alliance_upds = [
        FactionUpdate(faction_id="fa", diplomatic_relations_set={"fb": DS.ALLIED}),
        FactionUpdate(faction_id="fb", diplomatic_relations_set={"fa": DS.ALLIED}),
    ]
    world_events = events_from_transitions([], alliance_upds, {}, tick=3)

    alliance_events = [e for e in world_events if e.category == WorldEventCategory.FACTION_ALLIANCE_FORMED]
    assert len(alliance_events) == 1
    assert alliance_events[0].subject == "fa:fb"


def test_treaty_flows_through_narrative_ledger():
    """FACTION_PEACE_TREATY WorldEvent → NarrativeLedger entry with significance=0.75."""
    from src.domains.campaigns.orchestrator import CampaignOrchestrator
    from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory

    orchestrator = CampaignOrchestrator.__new__(CampaignOrchestrator)

    class FakeState:
        recent_world_events = [
            WorldEvent(
                category=WorldEventCategory.FACTION_PEACE_TREATY,
                tick=7,
                subject="fa:fb",
            )
        ]

    entries = orchestrator._extract_narrative_entries(FakeState(), episode_index=1)

    assert len(entries) == 1
    entry = entries[0]
    assert entry.event_type == "peace_treaty"
    assert entry.significance == 0.75
    assert entry.subject_id == "fa:fb"
    assert entry.tick == 7
    assert entry.entry_id == "1:7:peace_treaty:fa:fb"


def test_war_declared_flows_through_narrative_ledger():
    """FACTION_WAR_DECLARED WorldEvent → NarrativeLedger entry with significance=0.95."""
    from src.domains.campaigns.orchestrator import CampaignOrchestrator
    from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory

    orchestrator = CampaignOrchestrator.__new__(CampaignOrchestrator)

    class FakeState:
        recent_world_events = [
            WorldEvent(
                category=WorldEventCategory.FACTION_WAR_DECLARED,
                tick=2,
                subject="alpha:beta",
            )
        ]

    entries = orchestrator._extract_narrative_entries(FakeState(), episode_index=0)

    assert len(entries) == 1
    assert entries[0].event_type == "war_declared"
    assert entries[0].significance == 0.95
    assert entries[0].subject_id == "alpha:beta"
