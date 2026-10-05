"""Catalog hostility, not the 4-value legacy Faction enum, decides hostility at every swept site.

Fixture pairs (all from the real content catalog):
- goblin_warband / orc_clan: same legacy bucket (MONSTER_HORDE), catalog-hostile  -> raw enum under-detects
- hero_guild / town_council: different buckets, catalog-friendly                  -> raw enum over-detects
- neutral: neither ally nor enemy of hero_guild
"""
import pytest

from src.content_semantics import faction as faction_module
from src.content_semantics.faction import are_entities_allied, are_entities_hostile
from src.content_semantics.relation import RelationContext
from src.core.builder import V2EntityBuilder
from src.core.enums import Faction
from src.core.state import AuthoritativeState
from src.domains.cooperation.providers import CandidateBudget, PartnerCandidateProvider
from src.domains.cooperation.evaluators import HelpNeed
from src.engine.cognition import AppraisalSystem, SensoryFilter
from src.engine.combat import CombatResolutionSystem
from src.engine.legality import LegalityServiceV2
from src.systems.strategic_systems import intelligence
from src.systems.world_systems.intake import ConcernIntakeSystem

BUCKET = {
    "goblin_warband": Faction.MONSTER_HORDE,
    "orc_clan": Faction.MONSTER_HORDE,
    "hero_guild": Faction.HERO_GUILD,
    "town_council": Faction.TOWN_COUNCIL,
    "neutral": Faction.NEUTRAL,
}


def ent(eid, pos, faction_id, alive=True, hp=100):
    return (
        V2EntityBuilder(eid)
        .kind("HERO")
        .location(*pos)
        .identity(faction=BUCKET[faction_id], properties={"faction_id": faction_id})
        .combat(hp=hp if alive else 0, max_hp=100, atk=20, def_stat=5, attack_range=10, readiness=100.0, alive=alive)
        .lifecycle(active=True)
        .build()
    )


def world(*entities):
    return AuthoritativeState(tick=1, seed=42, entities={e.id: e for e in entities})


def concern_kinds(subject, others, state):
    return {c.kind: c.id for c in ConcernIntakeSystem.evaluate_salience(subject, [(o.id, o) for o in others], state)}


def test_fixture_pairs_are_what_the_docstring_claims():
    ctx = RelationContext(distance=1.0, combat_engaged=True)
    goblin, orc = ent(1, (0, 0), "goblin_warband"), ent(2, (1, 0), "orc_clan")
    hero, council, neutral = ent(3, (0, 0), "hero_guild"), ent(4, (1, 0), "town_council"), ent(5, (2, 0), "neutral")
    assert goblin.identity.faction == orc.identity.faction and are_entities_hostile(goblin, orc, ctx)
    assert hero.identity.faction != council.identity.faction and not are_entities_hostile(hero, council, ctx)
    assert not are_entities_hostile(hero, neutral, ctx) and not are_entities_allied(hero, neutral)


def test_one_shared_hostility_helper_is_imported_by_module_level_consumers():
    from src.ai.goals import scorers
    from src.domains.cooperation import providers
    from src.engine import cognition
    from src.systems.world_systems import intake

    for module in (scorers, providers, cognition, intake, intelligence):
        assert module.are_entities_hostile is faction_module.are_entities_hostile


class TestSplashFriendlyFire:
    def splash(self, attacker, victim):
        state = world(attacker, victim)
        return CombatResolutionSystem.resolve_aoe_attack(attacker, victim.navigation.position, radius=2, state=state)

    def test_same_bucket_catalog_hostile_victim_is_splashed(self):
        updates = self.splash(ent(1, (10, 10), "goblin_warband"), ent(2, (11, 10), "orc_clan"))
        assert 2 in updates and updates[2].damage_taken > 0

    def test_different_bucket_catalog_friendly_victim_is_not_splashed(self):
        assert 2 not in self.splash(ent(1, (10, 10), "hero_guild"), ent(2, (11, 10), "town_council"))

    def test_own_faction_and_neutral_are_never_splashed(self):
        assert 2 not in self.splash(ent(1, (10, 10), "orc_clan"), ent(2, (11, 10), "orc_clan"))
        assert 2 not in self.splash(ent(1, (10, 10), "hero_guild"), ent(2, (11, 10), "neutral"))


class TestDangerAndGriefConcerns:
    def test_danger_only_for_catalog_hostile_neighbour(self):
        state = world()
        assert "danger" in concern_kinds(ent(1, (0, 0), "goblin_warband"), [ent(2, (1, 0), "orc_clan")], state)
        assert "danger" not in concern_kinds(ent(1, (0, 0), "hero_guild"), [ent(2, (1, 0), "town_council")], state)

    def test_trauma_dead_ally_only_for_a_dead_member_of_the_same_catalog_faction(self):
        state = world()
        assert "trauma" in concern_kinds(ent(1, (0, 0), "orc_clan"), [ent(2, (1, 0), "orc_clan", alive=False)], state)
        assert "trauma" not in concern_kinds(ent(1, (0, 0), "orc_clan"), [ent(2, (1, 0), "goblin_warband", alive=False)], state)

    def test_dead_neutral_is_not_an_ally_of_a_hero(self):
        assert "trauma" not in concern_kinds(ent(1, (0, 0), "hero_guild"), [ent(2, (1, 0), "neutral", alive=False)], world())

    def test_trauma_record_id_still_names_an_ally_because_the_predicate_now_guarantees_it(self):
        kinds = concern_kinds(ent(1, (0, 0), "orc_clan"), [ent(2, (1, 0), "orc_clan", alive=False)], world())
        assert kinds["trauma"] == "trauma_dead_ally_2"


class TestFlanking:
    def flanked(self, defender_faction, flanker_faction):
        defender = ent(1, (5, 5), defender_faction)
        flankers = [ent(2, (5, 4), flanker_faction), ent(3, (5, 6), flanker_faction)]
        return LegalityServiceV2.check_flanking(1, world(defender, *flankers))[0]

    def test_same_bucket_catalog_hostile_flankers_flank(self):
        assert self.flanked("goblin_warband", "orc_clan") is True

    def test_different_bucket_catalog_friendly_neighbours_do_not_flank(self):
        assert self.flanked("hero_guild", "town_council") is False


class TestCognitionInputs:
    def test_saliency_ranks_catalog_hostile_above_catalog_friendly_at_equal_distance(self):
        hero = ent(4, (0, 0), "hero_guild")
        council = ent(5, (1, 0), "town_council")
        goblin = ent(6, (0, 1), "goblin_warband")
        ranked = SensoryFilter.filter_saliency(hero, [(5, council), (6, goblin)], max_targets=2)
        assert [e.id for e in ranked] == [6, 5]

    def test_outnumbered_panic_counts_catalog_hostiles_not_other_buckets(self):
        goblin = ent(1, (0, 0), "goblin_warband")
        orcs = [ent(i, (i, 0), "orc_clan") for i in (2, 3, 4)]
        hero = ent(10, (0, 0), "hero_guild")
        councillors = [ent(i, (i - 7, 0), "town_council") for i in (11, 12, 13)]
        panic_vs_hostile_same_bucket = AppraisalSystem.evaluate_emotional_state(goblin, orcs).panic_level
        panic_vs_friendly_other_bucket = AppraisalSystem.evaluate_emotional_state(hero, councillors).panic_level
        assert panic_vs_hostile_same_bucket > panic_vs_friendly_other_bucket


class TestStrategicAndCooperationInputs:
    def test_partner_pool_keeps_catalog_friendly_other_bucket_and_drops_catalog_hostile_same_bucket(self):
        need = (HelpNeed("combat_support_needed", 0.8, "t"),)
        budget = CandidateBudget(max_candidates=5, spatial_radius=10.0)

        hero = ent(1, (0, 0), "hero_guild")
        friend = ent(2, (1, 0), "town_council")
        pool = PartnerCandidateProvider.get_candidates(hero, world(hero, friend), need, budget)
        assert [c.entity_id for c in pool] == [2]

        goblin = ent(3, (0, 0), "goblin_warband")
        rival = ent(4, (1, 0), "orc_clan")
        pool = PartnerCandidateProvider.get_candidates(goblin, world(goblin, rival), need, budget)
        assert pool == ()

    def test_threat_resolved_ignores_catalog_friendly_neighbour_and_sees_same_bucket_enemy(self):
        hero = ent(1, (0, 0), "hero_guild")
        friend = ent(2, (1, 0), "town_council")
        assert intelligence._threat_resolved(hero, world(hero, friend)) is True

        goblin = ent(3, (0, 0), "goblin_warband")
        rival = ent(4, (1, 0), "orc_clan")
        assert intelligence._threat_resolved(goblin, world(goblin, rival)) is False
