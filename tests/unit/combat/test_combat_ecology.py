"""
TCK-20260619-COMBAT-ECOLOGY: Nemesis/grudge depth verification and fear_avoidance extension.

Scope note: grudge_history and combat_loss_counts are run-scoped only.
Cross-episode persistence requires Epic 3.2 (CampaignState) — BLOCKED.
"""
from __future__ import annotations
import pytest
from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState
from src.core.updates import SocialUpdate
from src.systems.social_systems.relationships import RelationshipService
from src.domains.combat_engagement.service import CombatEngagementDecisionService
from src.domains.combat_engagement.schema import CombatPosture


def _make_entity(eid: int, faction=Faction.HERO_GUILD, hp: int = 100):
    role = EntityRole.HERO if faction == Faction.HERO_GUILD else EntityRole.MONSTER
    return (
        V2EntityBuilder(eid)
        .kind("hero" if role == EntityRole.HERO else "monster")
        .location(0.0, 0.0)
        .identity(role=role, faction=faction)
        .combat(hp=hp, max_hp=100, attack_range=1, readiness=100.0, alive=hp > 0)
        .lifecycle(active=True)
        .build()
    )


def test_grudge_scope_is_defined():
    """
    Grudge state (grudge_history, nemesis_ids, combat_loss_counts) lives on SocialComponent,
    which is part of EntityState → AuthoritativeState. Scope is run-only; cross-episode
    persistence requires Epic 3.2 (CampaignState), not yet implemented.
    """
    entity = _make_entity(1)
    # All grudge-related fields exist on SocialComponent
    assert hasattr(entity.social, "grudge_history")
    assert hasattr(entity.social, "nemesis_ids")
    assert hasattr(entity.social, "combat_loss_counts")
    assert isinstance(entity.social.grudge_history, dict)
    assert isinstance(entity.social.nemesis_ids, (set, frozenset))
    assert isinstance(entity.social.combat_loss_counts, dict)


def test_combat_loss_increments_counter():
    """SocialUpdate.combat_loss_delta correctly increments combat_loss_counts via RelationshipService."""
    entity = _make_entity(1)
    # Simulate being defeated twice by entity 2
    upd1 = SocialUpdate(combat_loss_delta={2: 1})
    upd2 = SocialUpdate(combat_loss_delta={2: 1})
    social = RelationshipService.process_update(entity.social, upd1)
    social = RelationshipService.process_update(social, upd2)
    assert social.combat_loss_counts.get(2, 0) == 2


def test_fear_avoidance_posture_at_loss_threshold():
    """
    An entity that has been defeated by the same opponent >= 3 times
    should select CombatPosture.AVOID (fear_avoidance) when evaluating that opponent.
    """
    actor = _make_entity(1, Faction.HERO_GUILD)
    # Inject 3 losses against entity 2 directly into social state
    actor = replace(actor, social=replace(actor.social, combat_loss_counts={2: 3}))
    target = _make_entity(2, Faction.MONSTER_HORDE)
    state = AuthoritativeState(tick=1, seed=42, entities={1: actor, 2: target})

    result = CombatEngagementDecisionService.evaluate(actor, target, state)

    assert result.posture == CombatPosture.AVOID
    assert "fear_avoidance" in (result.reason or "")


def test_no_fear_avoidance_below_threshold():
    """With only 2 losses to the same opponent, fear_avoidance is NOT forced."""
    actor = _make_entity(1, Faction.HERO_GUILD)
    actor = replace(actor, social=replace(actor.social, combat_loss_counts={2: 2}))
    target = _make_entity(2, Faction.MONSTER_HORDE)
    state = AuthoritativeState(tick=1, seed=42, entities={1: actor, 2: target})

    result = CombatEngagementDecisionService.evaluate(actor, target, state)

    # With 2 losses and no other overrides, posture must NOT be forced-AVOID from fear_avoidance
    assert "fear_avoidance" not in (result.reason or "")
