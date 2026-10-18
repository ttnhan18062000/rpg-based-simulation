import pytest
from dataclasses import replace
from src.certification.harness import CertificationHarness
from src.certification.scenarios import build_scenario_state, get_scenario_expectations
from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.enums import Faction
from src.core.quests import QuestStatus
from src.core.state import BuildingState, RegionState
from src.core.treasury import treasury_key

# EXCH-02 (#536, divergences 2.108-2.112): a quest reward is never minted. It is paid by the treasury of the faction holding the ground of the
# building the quest was posted at, or recorded as OWED when that treasury is short. The arena posts the quest at a shop standing on neutral ground.
NEUTRAL_TREASURY = treasury_key(Faction.NEUTRAL)
REWARD_GOLD = 50


def _stage(treasury_gold):
    """The quest arena with one real giver: building 1 on neutral ground, the quest posted there, the neutral treasury holding `treasury_gold`."""
    state = build_scenario_state("COMBAT_ARENA_QUESTS")
    hero = state.entities[11]
    quest = replace(hero.strategic.projects["test_hunt"], source_building_id=1)
    hero = replace(hero, strategic=replace(hero.strategic, projects={"test_hunt": quest}))
    return replace(
        state,
        entities={**state.entities, 11: hero},
        buildings={1: BuildingState(id=1, kind="shop", position=(1.0, 1.0), functional=True)},
        regions={"arena": RegionState(id="arena", name="Arena", bounds=(0, 0, 100, 100), owner_faction_id=int(Faction.NEUTRAL))},
        global_resources={NEUTRAL_TREASURY: float(treasury_gold)},
    )


def _run(state):
    profile = RuntimeProfile(
        name="QUEST_ARENA_TEST", hardware_class=HardwareClass.CLASS_B,
        max_ram_mb=512, max_cpu_percent=80.0, max_worker_count=1,
        max_tick_budget_ms=100.0, max_queue_depth=100,
        max_replay_buffer_kb=1024, max_observability_budget_percent=5.0
    )
    scenario_id = "COMBAT_ARENA_QUESTS"
    harness = CertificationHarness(profile, output_dir="reports/arena_quests")
    # Run for 5 ticks to allow the hero to kill the goblin and collect reward
    result = harness.run_scenario(scenario_id, state, get_scenario_expectations(scenario_id), ticks=5)
    assert result.conformance_passed
    return result.final_state

@pytest.mark.extra_slow
def test_arena_quest_progression_paid_by_a_funded_treasury():
    """A hero in the arena completes a quest; a funded treasury pays the reward: treasury -50, hero +50, nothing minted."""
    start = _stage(treasury_gold=1000)
    final_state = _run(start)
    hero = final_state.entities[11]

    # Verify quest completion
    quest = hero.strategic.projects["test_hunt"]
    assert quest.current_value == 1.0
    # Quest should be REWARDED (as ApplyPath automates Active -> Completed -> Rewarded)
    assert quest.quest_status == QuestStatus.REWARDED

    # The conserved flow: the payer loses exactly what the receiver gains.
    assert hero.inventory.gold == REWARD_GOLD
    assert final_state.global_resources[NEUTRAL_TREASURY] == 1000 - REWARD_GOLD
    assert hero.inventory.gold + final_state.global_resources[NEUTRAL_TREASURY] == start.entities[11].inventory.gold + 1000
    assert not final_state.owed

    # Hero should have leveled up, meaning they spent their XP
    assert hero.identity.evolution_level == 2
    # Current points are what's left after leveling up (110 - 100 = 10)
    assert hero.identity.evolution_points == 10


@pytest.mark.extra_slow
def test_arena_quest_reward_is_owed_when_the_treasury_is_short():
    """A treasury that cannot pay pays nothing and the reward becomes a debt (OWED) to the hero; experience is still granted."""
    final_state = _run(_stage(treasury_gold=0))
    hero = final_state.entities[11]

    assert hero.strategic.projects["test_hunt"].quest_status == QuestStatus.REWARDED
    assert hero.inventory.gold == 0
    assert final_state.global_resources[NEUTRAL_TREASURY] == 0
    owed = [o for o in final_state.owed.values() if o.creditor_id == hero.id]
    assert len(owed) == 1
    assert owed[0].amount == REWARD_GOLD
    assert owed[0].reason == "QUEST_REWARD"
    assert hero.identity.evolution_level == 2


@pytest.mark.extra_slow
def test_arena_quest_with_no_giver_pays_experience_only():
    """A quest posted nowhere has no payer: no coin is minted, experience is still granted."""
    state = build_scenario_state("COMBAT_ARENA_QUESTS")
    final_state = _run(state)
    hero = final_state.entities[11]

    assert hero.strategic.projects["test_hunt"].quest_status == QuestStatus.REWARDED
    assert hero.inventory.gold == 0
    assert not final_state.owed
    assert hero.identity.evolution_level == 2
