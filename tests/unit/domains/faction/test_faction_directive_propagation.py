"""Unit tests for faction directive propagation to AdventureRouteScorer (E53Ac)."""
import pytest


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_entity(role_value: int):
    """Build a minimal EntityState with the given role (int)."""
    from src.core.state import EntityState
    from unittest.mock import MagicMock

    entity = MagicMock(spec=EntityState)
    entity.id = 1
    entity.identity.role = role_value
    entity.identity.personality = None
    entity.identity.traits = set()
    entity.identity.properties = {}
    entity.attributes.intelligence = 5.0
    entity.self_model.needs.active_needs = {}
    entity.combat.alive = True
    entity.lifecycle.active = True
    entity.lifecycle.dependent_entity_ids = []
    return entity


def _make_route(family):
    """Build a minimal AdventureRouteOption with zero scores."""
    from src.domains.adventure.schema import AdventureRouteOption
    return AdventureRouteOption(
        family=family,
        score=0.0,
        confidence=0.0,
        expected_benefit=0.0,
        expected_risk=0.0,
    )


def _score(entity, route, faction_directives=None, factions=None):
    """Call AdventureRouteScorer.score() and return the scored route."""
    from src.domains.adventure.scoring import AdventureRouteScorer
    return AdventureRouteScorer.score(
        entity, route,
        faction_directives=faction_directives,
        factions=factions,
    )


# ── Acceptance Criteria Tests ─────────────────────────────────────────────────

def test_guard_patrol_urgency_boosted_by_faction_directive():
    """GUARD + HUNT_WEAK_ENEMY + DEFEND_BORDER directive → score delta +2.0."""
    from src.core.enums import EntityRole
    from src.domains.adventure.schema import RouteFamily
    from src.engine.faction_decision import FactionDirective
    from src.engine.faction_constants import DEFEND_BORDER

    entity = _make_entity(EntityRole.GUARD)
    route = _make_route(RouteFamily.HUNT_WEAK_ENEMY)
    directive = FactionDirective(faction_id="f1", directive_kind=DEFEND_BORDER, created_tick=1)

    baseline = _score(entity, route, faction_directives=None)
    result = _score(entity, route, faction_directives=[directive])

    assert result.score - baseline.score == pytest.approx(2.0, abs=1e-3)


def test_merchant_trade_urgency_boosted_by_allied_region_gather():
    """SHOPKEEPER + GATHER_RESOURCE + allied diplomatic_relations → score delta +1.5."""
    from src.core.enums import EntityRole, DiplomaticState
    from src.domains.adventure.schema import RouteFamily
    from src.core.state import FactionState

    entity = _make_entity(EntityRole.SHOPKEEPER)
    route = _make_route(RouteFamily.GATHER_RESOURCE)
    fs = FactionState(faction_id="f1", diplomatic_relations={"f2": DiplomaticState.ALLIED})
    factions = {"f1": fs}

    baseline = _score(entity, route, faction_directives=None)
    result = _score(entity, route, faction_directives=[], factions=factions)

    assert result.score - baseline.score == pytest.approx(1.5, abs=1e-3)


def test_merchant_trade_urgency_boosted_by_allied_region_sell():
    """SHOPKEEPER + SELL_LOOT_FOR_GOLD + allied diplomatic_relations → score delta +1.5."""
    from src.core.enums import EntityRole, DiplomaticState
    from src.domains.adventure.schema import RouteFamily
    from src.core.state import FactionState

    entity = _make_entity(EntityRole.SHOPKEEPER)
    route = _make_route(RouteFamily.SELL_LOOT_FOR_GOLD)
    fs = FactionState(faction_id="f1", diplomatic_relations={"f2": DiplomaticState.ALLIED})
    factions = {"f1": fs}

    baseline = _score(entity, route, faction_directives=None)
    result = _score(entity, route, faction_directives=[], factions=factions)

    assert result.score - baseline.score == pytest.approx(1.5, abs=1e-3)


def test_hero_quest_urgency_boosted_by_commission():
    """HERO + QUEST_OPPORTUNITY + COMMISSION_QUEST directive → score delta +3.0."""
    from src.core.enums import EntityRole
    from src.domains.adventure.schema import RouteFamily
    from src.engine.faction_decision import FactionDirective
    from src.engine.faction_constants import COMMISSION_QUEST

    entity = _make_entity(EntityRole.HERO)
    route = _make_route(RouteFamily.QUEST_OPPORTUNITY)
    directive = FactionDirective(faction_id="f1", directive_kind=COMMISSION_QUEST, created_tick=1)

    baseline = _score(entity, route, faction_directives=None)
    result = _score(entity, route, faction_directives=[directive])

    assert result.score - baseline.score == pytest.approx(3.0, abs=1e-3)


def test_no_faction_directives_scorer_unchanged():
    """faction_directives=None → identical score to baseline (no faction params)."""
    from src.core.enums import EntityRole
    from src.domains.adventure.schema import RouteFamily

    entity = _make_entity(EntityRole.GUARD)
    route = _make_route(RouteFamily.HUNT_WEAK_ENEMY)

    baseline = _score(entity, route)
    with_none = _score(entity, route, faction_directives=None)

    assert baseline.score == pytest.approx(with_none.score, abs=1e-6)


# ── Negative / Regression Tests ───────────────────────────────────────────────

def test_guard_no_boost_without_defend_border_directive():
    """GUARD + HUNT_WEAK_ENEMY + TRADE_ROUTE only → no boost."""
    from src.core.enums import EntityRole
    from src.domains.adventure.schema import RouteFamily
    from src.engine.faction_decision import FactionDirective
    from src.engine.faction_constants import TRADE_ROUTE

    entity = _make_entity(EntityRole.GUARD)
    route = _make_route(RouteFamily.HUNT_WEAK_ENEMY)
    directive = FactionDirective(faction_id="f1", directive_kind=TRADE_ROUTE, created_tick=1)

    result = _score(entity, route, faction_directives=[directive])
    baseline = _score(entity, route, faction_directives=None)

    assert result.score == pytest.approx(baseline.score, abs=1e-6)


def test_shopkeeper_no_boost_without_allied_faction():
    """SHOPKEEPER + GATHER_RESOURCE + only hostile relations → no boost."""
    from src.core.enums import EntityRole, DiplomaticState
    from src.domains.adventure.schema import RouteFamily
    from src.core.state import FactionState

    entity = _make_entity(EntityRole.SHOPKEEPER)
    route = _make_route(RouteFamily.GATHER_RESOURCE)
    fs = FactionState(faction_id="f1", diplomatic_relations={"f2": DiplomaticState.HOSTILE})
    factions = {"f1": fs}

    result = _score(entity, route, faction_directives=[], factions=factions)
    baseline = _score(entity, route, faction_directives=None)

    assert result.score == pytest.approx(baseline.score, abs=1e-6)


def test_hero_no_boost_without_commission_directive():
    """HERO + QUEST_OPPORTUNITY + DEFEND_BORDER only → no quest boost."""
    from src.core.enums import EntityRole
    from src.domains.adventure.schema import RouteFamily
    from src.engine.faction_decision import FactionDirective
    from src.engine.faction_constants import DEFEND_BORDER

    entity = _make_entity(EntityRole.HERO)
    route = _make_route(RouteFamily.QUEST_OPPORTUNITY)
    directive = FactionDirective(faction_id="f1", directive_kind=DEFEND_BORDER, created_tick=1)

    result = _score(entity, route, faction_directives=[directive])
    baseline = _score(entity, route, faction_directives=None)

    assert result.score == pytest.approx(baseline.score, abs=1e-6)
