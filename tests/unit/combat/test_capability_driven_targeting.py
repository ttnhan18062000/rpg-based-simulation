"""Tests for capability-driven target-selection scoring in
TacticalDecisionSystem.target_score() (TCK-20260831-CAPABILITY-DRIVEN-TARGETING).

target_score() (src/engine/tactical.py) now calls
CapabilityEstimateService.estimate(entity, context=CapabilityContext.for_combat(enemy_ids=[h.kind]))
per candidate hostile and folds the resulting combat.enemy_type.<kind> estimate
into the sort tuple as -capability_confidence, placed ahead of h.combat.hp and
distance but behind group focus-fire bias and target-selection hysteresis --
so a hostile the acting entity subjectively believes it can beat is prioritized
even over a weaker/closer hostile.

This is an ad-hoc, scorer-local, read-only call -- it does not go through
SelfModelUpdatePhase, and entity.self_model.capabilities.estimates remains
empty in production either way (see docs/cognition/capability_and_knowledge_contract.md).

target_score() is a private closure inside evaluate_entity_intent() with no
external readers besides the sort call itself, so every test below asserts on
the observable outcome of evaluate_entity_intent() (the chosen target_id),
never on a hardcoded tuple index.
"""

from dataclasses import replace

from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState
from src.engine.tactical import TacticalDecisionSystem


# ── Helpers ───────────────────────────────────────────────────────────────────

def _entity(
    eid,
    faction,
    kind="hero",
    hp=100,
    max_hp=100,
    pos=(0.0, 0.0),
    attack_range=10,
    atk=10,
    def_stat=5,
    readiness=100.0,
):
    role = EntityRole.HERO if faction == Faction.HERO_GUILD else EntityRole.MONSTER
    return (
        V2EntityBuilder(eid)
        .kind(kind)
        .location(*pos)
        .identity(role=role, faction=faction)
        .combat(
            hp=hp,
            max_hp=max_hp,
            atk=atk,
            def_stat=def_stat,
            attack_range=attack_range,
            readiness=readiness,
            alive=hp > 0,
        )
        .lifecycle(active=True)
        .build()
    )


def _attacker(atk=10, def_stat=5, attack_range=10, pos=(0.0, 0.0)):
    return _entity(
        1, Faction.HERO_GUILD, kind="hero", pos=pos, attack_range=attack_range,
        atk=atk, def_stat=def_stat,
    )


# Goblin (_ENEMY_DANGER=0.5) and dragon (_ENEMY_DANGER=0.95) are both
# `_ENEMY_DANGER`-known ids with a wide danger spread (capability_estimate.py:59-66).
# The goblin is placed with worse HP/distance than the dragon so that, absent the
# capability signal, HP/distance alone would prefer the dragon -- proving any
# goblin-preferring outcome below is driven by the capability term, which sorts
# ahead of h.combat.hp and distance in the tuple.
def _goblin(attack_range=1, pos=(5.0, 0.0), hp=100):
    return _entity(10, Faction.MONSTER_HORDE, kind="goblin", pos=pos, hp=hp, attack_range=attack_range)


def _dragon(attack_range=1, pos=(1.0, 0.0), hp=10):
    return _entity(20, Faction.MONSTER_HORDE, kind="dragon", pos=pos, hp=hp, attack_range=attack_range)


# ── Test 1: differentiated enemy kinds change the sort outcome (AC1) ──────────

def test_target_score_reflects_capability_estimate_for_differentiated_enemy_kinds():
    attacker = _attacker(atk=10, def_stat=5)
    goblin = _goblin()
    dragon = _dragon()

    state = AuthoritativeState(tick=1, seed=42, world_time=1, entities={1: attacker, 10: goblin, 20: dragon})
    update = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)

    # Goblin has worse HP and is farther away than dragon -- HP/distance alone
    # would prefer the dragon. The capability-driven term (attacker is more
    # confident it can beat a goblin than a dragon) overrides that and wins.
    assert update.task.payload_set["target_id"] == goblin.id


# ── Test 2: uniform hostile kind leaves ordering unchanged (regression guard) ──

def test_target_score_unaffected_when_all_hostiles_share_the_same_kind():
    attacker = _attacker(atk=10, def_stat=5)
    weak_close = _entity(10, Faction.MONSTER_HORDE, kind="monster", pos=(1.0, 0.0), hp=10, attack_range=1)
    strong_far = _entity(20, Faction.MONSTER_HORDE, kind="monster", pos=(5.0, 0.0), hp=100, attack_range=1)

    state = AuthoritativeState(tick=1, seed=42, world_time=1, entities={1: attacker, 10: weak_close, 20: strong_far})
    update = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)

    # Same kind -> identical capability contribution for both candidates -> the
    # pre-existing HP ordering decides, exactly as before this ticket.
    assert update.task.payload_set["target_id"] == weak_close.id


# ── Test 3: capability estimate is derived from the acting entity's own stats ──

def test_target_score_capability_estimate_derived_from_acting_entitys_own_stats():
    goblin = _goblin()
    dragon = _dragon()

    zero_stat_attacker = _attacker(atk=0, def_stat=0)
    state_zero = AuthoritativeState(
        tick=1, seed=42, world_time=1, entities={1: zero_stat_attacker, 10: goblin, 20: dragon}
    )
    update_zero = TacticalDecisionSystem.evaluate_entity_intent(state_zero, zero_stat_attacker)

    # A zero-stat attacker's raw capability estimate is 0.0 against every enemy
    # kind (atk + def*0.5 == 0 numerator) -- the capability term ties between
    # goblin and dragon, so HP/distance decide as before, selecting the dragon
    # (lower HP, closer).
    assert update_zero.task.payload_set["target_id"] == dragon.id

    capable_attacker = _attacker(atk=10, def_stat=5)
    state_capable = AuthoritativeState(
        tick=1, seed=42, world_time=1, entities={1: capable_attacker, 10: goblin, 20: dragon}
    )
    update_capable = TacticalDecisionSystem.evaluate_entity_intent(state_capable, capable_attacker)

    # Only the attacker's own atk/def_stat changed -- the hostiles are byte-
    # identical in both scenarios. The choice flipping to the goblin proves the
    # capability estimate is read from the acting entity, not from the hostile.
    assert update_capable.task.payload_set["target_id"] == goblin.id


# ── Test 4: no write-back to entity.self_model (AC3 / durable-state rule) ─────

def test_target_score_does_not_mutate_entity_self_model():
    attacker = _attacker(atk=10, def_stat=5)
    goblin = _goblin()
    dragon = _dragon()
    self_model_before = attacker.self_model

    state = AuthoritativeState(tick=1, seed=42, world_time=1, entities={1: attacker, 10: goblin, 20: dragon})
    TacticalDecisionSystem.evaluate_entity_intent(state, attacker)

    assert attacker.self_model is self_model_before
    assert attacker.self_model.capabilities.estimates == {}


# ── Test 5: COMB-254 legality filter still runs after the re-scored sort (AC4) ─

def test_comb254_legality_filter_still_runs_after_capability_scored_sort():
    # Melee-range attacker (range 1): the capability-preferred goblin is placed
    # out of range (illegal), while the less-preferred dragon is adjacent
    # (legal). If the legality filter were bypassed by the new sort key, the
    # (illegal, out-of-range) goblin would be attacked; the filter must still
    # force the legal dragon.
    attacker = _attacker(atk=10, def_stat=5, attack_range=1)
    goblin = _goblin(attack_range=1, pos=(5.0, 0.0))
    dragon = _dragon(attack_range=1, pos=(1.0, 0.0))

    state = AuthoritativeState(tick=1, seed=42, world_time=1, entities={1: attacker, 10: goblin, 20: dragon})
    update = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)

    assert update.task.payload_set["target_id"] == dragon.id


# ── Test 6: reads only entity-owned fields and the hostile's kind ─────────────

def test_target_score_reads_only_entity_owned_and_hostile_kind_data():
    attacker = _attacker(atk=10, def_stat=5)
    goblin = _goblin()
    dragon = _dragon()
    state = AuthoritativeState(tick=1, seed=42, world_time=1, entities={1: attacker, 10: goblin, 20: dragon})
    baseline = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)

    # The hostile's own combat stats (other than kind/hp/position, which feed
    # separate, pre-existing tuple fields) are not read by the capability
    # formula at all -- changing the dragon's atk/def_stat must not change the
    # outcome.
    dragon_diff_stats = replace(
        dragon, combat=replace(dragon.combat, atk=999, def_stat=999)
    )
    state_diff = AuthoritativeState(
        tick=1, seed=42, world_time=1, entities={1: attacker, 10: goblin, 20: dragon_diff_stats}
    )
    update_diff = TacticalDecisionSystem.evaluate_entity_intent(state_diff, attacker)

    assert update_diff.task.payload_set["target_id"] == baseline.task.payload_set["target_id"]


# ── Test 7: deterministic ──────────────────────────────────────────────────────

def test_target_score_capability_signal_is_deterministic():
    attacker = _attacker(atk=10, def_stat=5)
    goblin = _goblin()
    dragon = _dragon()
    state = AuthoritativeState(tick=1, seed=42, world_time=1, entities={1: attacker, 10: goblin, 20: dragon})

    update_1 = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)
    update_2 = TacticalDecisionSystem.evaluate_entity_intent(state, attacker)

    assert update_1.task.payload_set["target_id"] == update_2.task.payload_set["target_id"]
    assert update_1.task.payload_set == update_2.task.payload_set
