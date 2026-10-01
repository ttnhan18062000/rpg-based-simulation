"""TCK-20261001-PASSIVE-BIOLOGICAL-DEATH-CAUSE-RECORDED-AT-WRITER and
TCK-20261001-DEFEAT-REBIRTH-CONVERTED-TO-DEATH-BY-PASSIVE-HP-GATE (one batch).

`resolve_lifecycle` is the sole authority for HP-death deactivation. The passive writer
(`ApplyPath._compute_entity_changes`) only records a typed cause on the tick it drives HP to zero;
`resolve_lifecycle` reads it at N+1 (`kernel.py` runs refine before apply), so every classification
assertion here advances a tick explicitly.
"""
from __future__ import annotations

from dataclasses import replace

from src.config.profiles import PROD_SMALL
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction, PassiveDeathCause
from src.core.state import AuthoritativeState, LifecycleComponent
from src.core.updates import CombatUpdate, EntityUpdate, StateUpdate
from src.engine.apply import ApplyPath
from src.engine.combat import CombatResolutionSystem
from src.engine.kernel import Kernel
from src.platform.rng import DeterministicRNG
from src.systems.lifecycle_systems.lifecycle import LifecycleSystem

FAR_MAX_AGE = 100_000


def _starving(hp, hunger=0.0, sleep_debt=0.0, entity_id=1, **life):
    life.setdefault("max_age_ticks", FAR_MAX_AGE)
    return (
        V2EntityBuilder(entity_id).kind("HERO").location(0.0, 0.0)
        .biological(hunger=hunger, sleep_debt=sleep_debt)
        .combat(hp=hp)
        .lifecycle(active=True, age_ticks=0, **life)
        .build()
    )


def _kernel_ticks(entity, n):
    state = AuthoritativeState(tick=0, seed=42, entities={entity.id: entity})
    kernel = Kernel(profile=PROD_SMALL, state=state, rng=DeterministicRNG(42), flags={"no_frame_pacing": True})
    trace = []
    try:
        for _ in range(n):
            kernel.tick_once()
            trace.append(kernel.state.entities[entity.id])
    finally:
        kernel.shutdown()
    return trace


def _step(state, entity_updates=None):
    """One refine+apply cycle in kernel order: resolve_lifecycle first, then the apply path."""
    update = StateUpdate(entity_updates=dict(entity_updates or {}))
    refined = LifecycleSystem.resolve_lifecycle(state, update)
    return ApplyPath.apply_generation(state, refined)


# --- T1 / T2 / T5: classification from the recorded cause, one tick later -------------------------

def test_hunger_death_records_starvation_with_zeroing_tick_then_classifies_next_tick():
    n, n1 = _kernel_ticks(_starving(hp=2, hunger=95.0), 2)
    assert n.combat.hp == 0 and n.combat.alive is False
    assert n.lifecycle.passive_death_cause is PassiveDeathCause.STARVATION
    assert n.lifecycle.passive_death_cause_tick is not None
    assert n.lifecycle.active is True and n.lifecycle.death_reason is None  # not yet classified
    assert n1.lifecycle.death_reason == "STARVATION"
    assert n1.lifecycle.is_permadeath is True and n1.lifecycle.active is False
    # classified on the following step, never the zeroing step itself; N stays recorded
    assert n1.lifecycle.death_tick >= n.lifecycle.passive_death_cause_tick
    assert n1.lifecycle.passive_death_cause_tick == n.lifecycle.passive_death_cause_tick  # N preserved


def test_sleep_debt_death_records_sleep_deprivation_distinct_from_starvation():
    n, n1 = _kernel_ticks(_starving(hp=1, sleep_debt=98.0), 2)
    assert n.lifecycle.passive_death_cause is PassiveDeathCause.SLEEP_DEPRIVATION
    assert n1.lifecycle.death_reason == "SLEEP_DEPRIVATION"
    assert PassiveDeathCause.SLEEP_DEPRIVATION.value != PassiveDeathCause.STARVATION.value


def test_both_thresholds_breached_record_starvation_by_declared_precedence():
    """Declared rule (lifecycle_systems_contract.md): hunger outranks sleep debt as a recorded cause."""
    n, n1 = _kernel_ticks(_starving(hp=3, hunger=95.0, sleep_debt=98.0), 2)
    assert n.combat.hp == 0
    assert n1.lifecycle.death_reason == PassiveDeathCause.STARVATION.value


def test_non_fatal_passive_drain_records_nothing():
    (n,) = _kernel_ticks(_starving(hp=10, hunger=95.0), 1)
    assert n.combat.hp == 8 and n.combat.alive is True
    assert n.lifecycle.passive_death_cause is None and n.lifecycle.passive_death_cause_tick is None


def test_entity_already_at_zero_hp_with_no_passive_damage_invents_no_cause():
    (n,) = _kernel_ticks(_starving(hp=0), 1)
    assert n.lifecycle.passive_death_cause is None


def test_zero_hp_leftover_with_breached_thresholds_is_not_classified_as_passive():
    """The hostile case for a threshold-inferring design: already 0 HP, both thresholds breached."""
    ent = _starving(hp=0, hunger=99.0, sleep_debt=99.0)
    n, n1 = _kernel_ticks(ent, 2)
    assert n.lifecycle.passive_death_cause is None and n1.lifecycle.passive_death_cause is None
    assert n1.lifecycle.death_reason is None


# --- T6 / T6b: a recorded death outranks a passive cause; stale cause never surfaces --------------

def test_combat_death_on_same_tick_as_passive_zeroing_wins_and_clears_stale_cause():
    ent = _starving(hp=2, hunger=95.0)
    state = AuthoritativeState(tick=1, seed=42, entities={1: ent})
    kill = EntityUpdate(entity_id=1, combat=CombatUpdate(hp_delta=-2, alive_set=False, outcome_kind="KILL"))
    s1 = _step(state, {1: kill})
    life = s1.entities[1].lifecycle
    assert life.death_reason == "COMBAT"
    assert life.passive_death_cause is None and life.passive_death_cause_tick is None  # R2: stale cleared
    s2 = _step(s1)  # advance: R6 guard -> nothing re-classified, no second dispatch
    assert s2.entities[1].lifecycle.death_reason == "COMBAT"
    assert s2.entities[1].lifecycle.death_tick == life.death_tick


def test_passive_writer_skips_entity_that_already_carries_a_death_record():
    ent = _starving(hp=2, hunger=95.0, death_reason="OLD_AGE", is_permadeath=True)
    ent = replace(ent, lifecycle=replace(ent.lifecycle, active=False))
    s = ApplyPath.apply_generation(AuthoritativeState(tick=1, seed=42, entities={1: ent}), StateUpdate())
    assert s.entities[1].lifecycle.passive_death_cause is None


# --- T7 / A: typed, serialised, authoritative path -------------------------------------------------

def test_passive_cause_is_canonical_and_round_trips():
    life = LifecycleComponent(passive_death_cause=PassiveDeathCause.STARVATION, passive_death_cause_tick=7)
    canon = life.to_canonical_dict()
    assert canon["passive_death_cause"] == "STARVATION" and canon["passive_death_cause_tick"] == 7
    assert LifecycleComponent().to_canonical_dict()["passive_death_cause"] is None
    assert LifecycleComponent(passive_death_cause=PassiveDeathCause.STARVATION).to_canonical_dict() != \
        LifecycleComponent().to_canonical_dict()


def test_resolve_lifecycle_does_not_mutate_input_state_for_passive_cause():
    ent = replace(_starving(hp=0), lifecycle=replace(_starving(hp=0).lifecycle,
                  passive_death_cause=PassiveDeathCause.STARVATION, passive_death_cause_tick=3))
    state = AuthoritativeState(tick=4, seed=42, entities={1: ent})
    refined = LifecycleSystem.resolve_lifecycle(state, StateUpdate())
    assert state.entities[1].lifecycle.death_reason is None and state.entities[1].lifecycle.active is True
    assert refined.entity_updates[1].lifecycle.death_reason_set == "STARVATION"


def test_two_identical_runs_record_identical_causes_and_canonical_state():
    a = _kernel_ticks(_starving(hp=2, hunger=95.0), 3)[-1]
    b = _kernel_ticks(_starving(hp=2, hunger=95.0), 3)[-1]
    assert a.lifecycle.to_canonical_dict() == b.lifecycle.to_canonical_dict()


def test_event_extractor_stays_exact_match_on_combat_for_passive_reasons():
    import inspect
    from src.observability import event_extractor
    assert 'death_reason", None) == "COMBAT"' in inspect.getsource(event_extractor)


# --- Sibling: terminal DEFEAT / REBIRTH ------------------------------------------------------------

def _fight(defender_role, hp=1, hunger=0.0, sleep_debt=0.0, wounds=None):
    attacker = (V2EntityBuilder(1).kind("goblin").location(0.0, 0.0)
                .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE).combat(hp=100, atk=50).build())
    d = (V2EntityBuilder(2).kind("hero").location(1.0, 0.0)
         .identity(role=defender_role, faction=Faction.HERO_GUILD).combat(hp=hp, max_hp=40)
         .biological(hunger=hunger, sleep_debt=sleep_debt)
         .lifecycle(active=True, max_age_ticks=FAR_MAX_AGE).build())
    state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: d})
    cu = CombatResolutionSystem.resolve_multi_attack([attacker], d, state, is_opportunity_attack=True, is_lethal=False)
    return state, cu


def _defender_update(entity_id, cu):
    """Mirror movement.py's opportunity-attack call site: NO lifecycle update is lifted (T11'); the
    classification comes from resolve_lifecycle synthesizing its own LifecycleUpdate."""
    return EntityUpdate(entity_id=entity_id, combat=cu)


def test_terminal_defeat_is_recorded_with_its_own_reason_and_deactivated():
    state, cu = _fight(EntityRole.MONSTER)
    assert cu.outcome_kind == "DEFEAT"
    s1 = _step(state, {2: _defender_update(2, cu)})  # no incoming lifecycle update (T11')
    life = s1.entities[2].lifecycle
    assert life.death_reason == "DEFEAT" and life.death_reason != "COMBAT"
    assert life.active is False and life.is_permadeath is True and life.death_tick == 1


def test_defeat_wins_over_pending_passive_cause_on_a_starving_entity():
    state, cu = _fight(EntityRole.MONSTER, hunger=99.0, sleep_debt=99.0)
    ent = state.entities[2]
    state = replace(state, entities={**state.entities, 2: replace(ent, lifecycle=replace(
        ent.lifecycle, passive_death_cause=PassiveDeathCause.STARVATION, passive_death_cause_tick=0))})
    s1 = _step(state, {2: _defender_update(2, cu)})
    assert s1.entities[2].lifecycle.death_reason == "DEFEAT"
    assert s1.entities[2].lifecycle.passive_death_cause is None


def test_lethal_hit_on_a_former_hero_is_an_ordinary_recorded_combat_death():
    """TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION: no role is exempt from death. A
    lethal hit on a HERO defender is KILL (no REBIRTH/PERMADEATH outcome exists), recorded as COMBAT
    with is_permadeath and the usual lineage dispatch. Both former rebirth sites are exercised."""
    from src.engine.combat import CombatResolutionSystem as C
    for resolve in ("multi", "single"):
        attacker = (V2EntityBuilder(1).kind("goblin").location(0.0, 0.0)
                    .identity(role=EntityRole.MONSTER, faction=Faction.MONSTER_HORDE)
                    .combat(hp=100, atk=50).build())
        hero = (V2EntityBuilder(2).kind("hero").location(1.0, 0.0)
                .identity(role=EntityRole.HERO, faction=Faction.HERO_GUILD)
                .combat(hp=1, max_hp=40).lifecycle(active=True, max_age_ticks=FAR_MAX_AGE).build())
        state = AuthoritativeState(tick=1, seed=42, entities={1: attacker, 2: hero})
        if resolve == "multi":
            cu = C.resolve_multi_attack([attacker], hero, state, is_opportunity_attack=True, is_lethal=True)
        else:
            cu = C.resolve_attack(attacker, hero, state, is_opportunity_attack=True, is_lethal=True)
        assert cu.outcome_kind == "KILL", (resolve, cu.outcome_kind)
        s1 = _step(state, {2: EntityUpdate(entity_id=2, combat=cu)})
        life = s1.entities[2].lifecycle
        assert life.death_reason == "COMBAT" and life.is_permadeath is True
        assert life.active is False and life.death_tick == 1


def test_no_rebirth_or_permadeath_outcome_kind_can_be_produced_for_any_role():
    from src.engine.combat import CombatResolutionSystem as C
    for role in (EntityRole.HERO, EntityRole.MONSTER, EntityRole.CITIZEN):
        for is_lethal in (True, False):
            state, _ = _fight(role)
            attacker, hero = state.entities[1], state.entities[2]
            hero = replace(hero, identity=replace(hero.identity, role=role))
            cu = C.resolve_multi_attack([attacker], hero, state, is_opportunity_attack=True, is_lethal=is_lethal)
            assert cu.outcome_kind in ("KILL", "DEFEAT"), (role, is_lethal, cu.outcome_kind)
            assert not hasattr(cu, "generation_delta")


def test_retired_rebirth_surface_is_absent():
    """Absence of the retired literals/fields (RA-style guard against reintroduction)."""
    import inspect
    from src.core.state import LifecycleComponent, CorpseState
    from src.core.updates import CombatUpdate, LifecycleUpdate
    from src.engine import combat, combat_rewards
    assert not hasattr(LifecycleComponent(), "generation") and not hasattr(CorpseState, "generation")
    assert not hasattr(LifecycleUpdate(), "generation_delta")
    assert not hasattr(CombatUpdate(), "generation_delta") and not hasattr(CombatUpdate(), "is_permadeath_set")
    for mod in (combat, combat_rewards):
        src = inspect.getsource(mod)
        assert "rebirth_eligible" not in src and '"REBIRTH"' not in src and '"PERMADEATH"' not in src


def test_is_permadeath_stays_a_separately_tracked_lifecycle_fact():
    """RA1: `is_permadeath` / `LifecycleUpdate.is_permadeath_set` are deliberately KEPT even though every
    recorded death now sets them True (resolve_lifecycle already did for old age). They are the STR-02
    hook: only a future *declared* resurrection process may leave a recorded death with is_permadeath
    False. Do not 'simplify' them away as redundant with death_reason."""
    from src.core.updates import LifecycleUpdate
    assert hasattr(LifecycleComponent(), "is_permadeath")
    assert hasattr(LifecycleUpdate(), "is_permadeath_set")
    assert LifecycleComponent().is_permadeath is False  # a surviving entity is not permadeath


def test_terminal_outcome_set_has_exactly_the_live_outcomes():
    from src.core.combat_constants import TERMINAL_COMBAT_OUTCOME_KINDS
    assert set(TERMINAL_COMBAT_OUTCOME_KINDS) == {"KILL", "DEFEAT"}
