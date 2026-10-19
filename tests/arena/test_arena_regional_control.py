import pytest
from src.certification.harness import CertificationHarness
from src.certification.scenarios import build_scenario_state, get_scenario_expectations
from src.config.profiles import RuntimeProfile, HardwareClass
from dataclasses import replace
from src.core.enums import Faction
from src.core.treasury import treasury_key

# EXCH-02 (#536, divergences 2.108-2.112): coin is never minted. A kill pays nothing to the killer; the dead keep their purse on the corpse until
# someone loots it. The per-head levy is retired (tax is a tenth of a sale or a wage, paid to the place holder's treasury), and the +10 building mint is gone.
MONSTER_PURSE = 5
HERO_PURSE = 100


def _stage_purse(state, gold=MONSTER_PURSE):
    """Give the monster (id 14) a real purse, so the coin a kill moves is visible and conserved."""
    monster = state.entities[14]
    return replace(state, entities={**state.entities, 14: replace(monster, inventory=replace(monster.inventory, gold=gold))})


def _corpse_gold(state):
    return sum(c.gold for c in state.corpses.values())

@pytest.mark.extra_slow
def test_arena_regional_control():
    """Verify regional influence, conquest, and taxation."""
    profile = RuntimeProfile(
        name="REGIONAL_ARENA_TEST", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512, max_cpu_percent=80.0, max_worker_count=1,
        max_tick_budget_ms=100.0, max_queue_depth=100,
        max_replay_buffer_kb=1024, max_observability_budget_percent=5.0
    )
    
    scenario_id = "COMBAT_ARENA_REGIONAL"
    state = _stage_purse(build_scenario_state(scenario_id))
    expectations = get_scenario_expectations(scenario_id)
    
    harness = CertificationHarness(profile, output_dir="reports/arena_regional")
    
    # Tick 99 -> Tick 100
    # Hero (ID 13) kills Monster (ID 14)
    # Monster death -> +5.0 influence
    # -45.0 + 5.0 = -40.0
    
    result = harness.run_scenario(scenario_id, state, expectations, ticks=1)
    
    assert result.conformance_passed
    final_state = result.final_state
    region = final_state.regions["test_wilderness"]
    
    # 1. Verify Influence Shift
    assert region.influence == -40.0
    
    # 2. Verify Gold: the kill moves the monster's purse onto its corpse. It is not minted and not paid to the hero.
    hero = final_state.entities[13]
    assert hero.inventory.gold == HERO_PURSE
    assert _corpse_gold(final_state) == MONSTER_PURSE
    assert hero.inventory.gold + _corpse_gold(final_state) == HERO_PURSE + MONSTER_PURSE  # conserved

    # 3. Now run one more tick (prior_tick will be 100)
    result2 = harness.run_scenario(scenario_id, final_state, expectations, ticks=1)
    hero2 = result2.final_state.entities[13]
    # No taxation because region is still unowned (Influence -40.0); the corpse purse stays where it fell.
    assert hero2.inventory.gold == HERO_PURSE
    assert _corpse_gold(result2.final_state) == MONSTER_PURSE

@pytest.mark.extra_slow
def test_arena_conquest_and_debuff():
    """
    Verify that monster-owned conquered regions apply hero combat debuffs
    and taxation.

    Logic under test:
        When a region is conquered by MONSTER_HORDE and suppression is active,
        heroes inside that region receive the regional conquest debuff:

            atk      = int(base_atk * 0.8)
            def_stat = int(base_def * 0.8)
            speed    = int(base_speed * 0.9)

    Important:
        This test must use the scenario's actual combat values, not
        LevelingService-derived attribute bonuses.

        The COMBAT_ARENA_REGIONAL hero starts with:
            atk=100
            def_stat=20
            speed=10

        Therefore expected debuffed values are:
            atk=int(100 * 0.8) = 80
            def=int(20 * 0.8)  = 16
            speed=int(10 * 0.9) = 9

    Fraud this catches:
        - conquered-region debuff is not applied
        - debuff uses wrong multiplier
        - test falsely adds attribute-derived bonuses that are not part of
          arena scenario combat initialization
        - a per-head levy or a minted kill reward comes back (EXCH-02: coin moves, it is not created)
    """
    profile = RuntimeProfile(
        name="CONQUEST_ARENA_TEST",
        hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512,
        max_cpu_percent=80.0,
        max_worker_count=1,
        max_tick_budget_ms=100.0,
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5.0,
    )

    scenario_id = "COMBAT_ARENA_REGIONAL"
    state = _stage_purse(build_scenario_state(scenario_id))

    region = state.regions["test_wilderness"]

    conquered_region = replace(
        region,
        influence=-60.0,
        owner_faction_id=Faction.MONSTER_HORDE,
        suppression_active=True,
    )

    # Set tick=100 so taxation is evaluated during this run.
    state = replace(
        state,
        regions={"test_wilderness": conquered_region},
        tick=100,
    )

    harness = CertificationHarness(
        profile,
        output_dir="reports/arena_conquest",
    )
    expectations = get_scenario_expectations(scenario_id)

    result = harness.run_scenario(
        scenario_id,
        state,
        expectations,
        ticks=1,
    )

    final_state = result.final_state
    hero = final_state.entities[13]

    assert hero.combat.atk == 80
    assert hero.combat.def_stat == 16
    assert hero.combat.speed == 9

    # No per-head levy any more (it was 2.0 to the holder's treasury) and no minted kill reward (it was 5.0 to the hero): the hero keeps
    # exactly the coin it had, the monster's purse lies on its corpse, and the holding faction's treasury is untouched.
    assert hero.inventory.gold == HERO_PURSE
    assert _corpse_gold(final_state) == MONSTER_PURSE
    assert hero.inventory.gold + _corpse_gold(final_state) == HERO_PURSE + MONSTER_PURSE  # conserved

    faction_key = treasury_key(Faction.MONSTER_HORDE)
    assert final_state.global_resources.get(faction_key, 0.0) == 0.0
