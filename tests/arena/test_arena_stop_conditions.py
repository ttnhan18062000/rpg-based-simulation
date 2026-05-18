import pytest

from src.certification.harness import CertificationHarness
from src.certification.models import ScenarioExpectations, ArenaStopCondition
from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.builder import V2EntityBuilder
from src.core.enums import EntityRole, Faction
from src.core.state import AuthoritativeState


@pytest.fixture
def base_profile():
    return RuntimeProfile(
        name="ARENA_TEST",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=80.0,
        max_worker_count=0,
        max_tick_budget_ms=50.0,
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5.0,
    )


def make_arena_actor(
    entity_id: int,
    *,
    kind: str,
    faction: Faction,
    role: EntityRole,
    pos: tuple[float, float],
    hp: int = 100,
    atk: int = 10,
    alive: bool = True,
):
    """
    Build a valid arena actor for certification stop-condition tests.

    Important:
        CertificationHarness WIPE detection reads `entity.combat.alive`.
        Therefore tests must set `alive` explicitly instead of assuming hp=0
        or lifecycle.active=False is enough.

    Fraud this catches:
        - test relies on combat execution instead of stop-condition logic
        - entity has hp=0 but combat.alive=True
        - builder defaults hide whether a faction is considered alive
    """
    return (
        V2EntityBuilder(entity_id)
        .kind(kind)
        .location(*pos)
        .identity(
            role=role,
            faction=faction,
        )
        .combat(
            hp=hp,
            max_hp=max(100, hp),
            atk=atk,
            def_stat=0,
            attack_range=1,
            alive=alive,
            readiness=100.0,
        )
        .lifecycle(active=alive)
        .build()
    )


def test_arena_stop_condition_wipe(base_profile):
    """
    Verify ArenaStopCondition.WIPE.

    This test should not depend on tactical AI or combat resolution.
    It sets up the final semantic condition directly:
        only one faction has combat.alive=True.

    The harness checks WIPE at the start of each loop after t > 1, so an
    already-wiped state should terminate early instead of timing out.
    """
    a1 = make_arena_actor(
        1,
        kind="hero",
        faction=Faction.HERO_GUILD,
        role=EntityRole.HERO,
        pos=(0.0, 0.0),
        hp=100,
        atk=50,
        alive=True,
    )

    b1 = make_arena_actor(
        2,
        kind="monster",
        faction=Faction.MONSTER_HORDE,
        role=EntityRole.MONSTER,
        pos=(1.0, 0.0),
        hp=0,
        atk=10,
        alive=False,
    )

    state = AuthoritativeState(
        tick=100,
        seed=42,
        entities={
            1: a1,
            2: b1,
        },
    )

    # Guard: this is exactly what CertificationHarness uses for WIPE.
    alive_factions = {
        e.identity.faction
        for e in state.entities.values()
        if e.combat.alive
    }
    assert alive_factions == {Faction.HERO_GUILD}

    harness = CertificationHarness(
        base_profile,
        output_dir="reports/test_wipe",
    )
    expectations = ScenarioExpectations(reproducibility_required=False)

    result = harness.run_scenario(
        "WIPE_TEST",
        state,
        expectations,
        ticks=100,
    )

    assert result.stop_condition == ArenaStopCondition.WIPE
    assert result.final_state.tick < 200


def test_arena_stop_condition_timeout(base_profile):
    """
    Verify ArenaStopCondition.TIMEOUT.

    Both factions remain alive for the whole bounded run, so the harness should
    finish by tick limit instead of WIPE.
    """
    a1 = make_arena_actor(
        1,
        kind="hero",
        faction=Faction.HERO_GUILD,
        role=EntityRole.HERO,
        pos=(0.0, 0.0),
        hp=100,
        alive=True,
    )

    b1 = make_arena_actor(
        2,
        kind="monster",
        faction=Faction.MONSTER_HORDE,
        role=EntityRole.MONSTER,
        pos=(50.0, 50.0),
        hp=100,
        alive=True,
    )

    state = AuthoritativeState(
        tick=100,
        seed=42,
        entities={
            1: a1,
            2: b1,
        },
    )

    alive_factions = {
        e.identity.faction
        for e in state.entities.values()
        if e.combat.alive
    }
    assert alive_factions == {
        Faction.HERO_GUILD,
        Faction.MONSTER_HORDE,
    }

    harness = CertificationHarness(
        base_profile,
        output_dir="reports/test_timeout",
    )
    expectations = ScenarioExpectations(reproducibility_required=False)

    result = harness.run_scenario(
        "TIMEOUT_TEST",
        state,
        expectations,
        ticks=10,
    )

    assert result.stop_condition == ArenaStopCondition.TIMEOUT
    assert result.final_state.tick == 110