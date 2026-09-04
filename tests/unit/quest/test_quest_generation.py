import pytest
from src.quests.generator import QuestGenerator, QuestPressureProfile
from src.core.quests import QuestKind
from src.core.models.quests import QuestOpportunity
from src.domains.world_emergence.services import QuestOpportunityGenerator
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory, WorldEmergenceResult
from src.core.state import AuthoritativeState, RegionState
from src.core.updates import StateUpdate
from src.domains.world_emergence.phase import WorldEmergencePhase

def test_quest_generator_determinism():
    seed = 42
    level = 1
    tick = 100

    q1 = QuestGenerator.generate(seed, level, tick)
    q2 = QuestGenerator.generate(seed, level, tick)
    
    assert q1 is not None
    assert q2 is not None
    assert q1.id == q2.id
    assert q1.name == q2.name
    assert q1.reward.xp == q2.reward.xp

def test_level_banding_tier1():
    # Level 1 should get TIER 1 templates (Slimes or Woods)
    q = QuestGenerator.generate(123, 1, 10)
    assert q.quest_kind in [QuestKind.HUNT, QuestKind.EXPLORE]
    assert q.name in ["Clear the Slimes", "Survey the Woods"]

def test_level_banding_tier3():
    # Level 15 should get TIER 3 templates (Bandits or Outpost)
    q = QuestGenerator.generate(123, 15, 10)
    assert q.quest_kind in [QuestKind.BOUNTY, QuestKind.LIBERATE]
    assert q.name in ["Bounty: Bandit Leader", "Liberate the Outpost"]

def test_reward_scaling():
    # Level 1 vs Level 5 for the same template "Clear the Slimes"
    # Note: Seed might choose different templates if not careful.
    # We can test scaling by comparing same template if we find it.
    
    # Force seed that picks "Clear the Slimes" for both if possible
    # Or just check if level 10 rewards are higher than level 1 on average.
    
    q_low = QuestGenerator.generate(seed=1, level=1, tick=0)
    q_high = QuestGenerator.generate(seed=1, level=100, tick=0)
    
    # Level 100 will pick TIER 3, so naturally higher
    assert q_high.reward.xp > q_low.reward.xp
    assert q_high.reward.gold > q_low.reward.gold

def test_duplicate_suppression():
    # We'll use a seed that would normally pick a certain quest
    seed = 42
    level = 1
    tick = 10

    q_orig = QuestGenerator.generate(seed, level, tick)
    template_id = q_orig.id.rsplit("_", 1)[0]

    # Generate again but suppress the template of q_orig
    q_filtered = QuestGenerator.generate(seed, level, tick, existing_ids={template_id})

    assert q_filtered is not None
    assert q_filtered.id != q_orig.id
    assert q_filtered.name != q_orig.name


# ── Pressure-driven selection tests (TCK-20260703-SIMQ-UPLIFT3-QUEST-PRESSURE) ─

def test_quest_generation_favors_hunt_under_high_trauma():
    profile = QuestPressureProfile(trauma=1.0)
    hunt_count = 0
    for seed in range(30):
        q = QuestGenerator.generate(seed, 8, 100, pressure_profile=profile)
        if q.quest_kind == QuestKind.HUNT:
            hunt_count += 1
    assert hunt_count > 15


def test_quest_generation_favors_gather_under_high_scarcity():
    profile = QuestPressureProfile(scarcity=1.0)
    gather_count = 0
    for seed in range(30):
        q = QuestGenerator.generate(seed, 8, 100, pressure_profile=profile)
        if q.quest_kind == QuestKind.GATHER:
            gather_count += 1
    assert gather_count > 15


def test_quest_generation_neutral_profile_matches_legacy_none():
    for seed in range(30):
        q_none = QuestGenerator.generate(seed, 8, 100)
        q_neutral = QuestGenerator.generate(seed, 8, 100, pressure_profile=QuestPressureProfile())
        assert q_none.id == q_neutral.id


def test_level_gating_overrides_pressure():
    profile = QuestPressureProfile(trauma=1.0, hazard=1.0, scarcity=1.0)
    for seed in range(10):
        q = QuestGenerator.generate(seed, 1, 100, pressure_profile=profile)
        assert q.name in ["Clear the Slimes", "Survey the Woods"]
        assert q.name not in ["Bounty: Bandit Leader", "Liberate the Outpost"]


def test_pressure_driven_selection_determinism():
    profile = QuestPressureProfile(trauma=0.8, scarcity=0.3)
    q1 = QuestGenerator.generate(42, 8, 100, pressure_profile=profile)
    q2 = QuestGenerator.generate(42, 8, 100, pressure_profile=profile)
    assert q1.id == q2.id
    assert q1.name == q2.name
    assert q1.reward.xp == q2.reward.xp


def test_quest_generation_missing_region_signal_defaults_neutral():
    q = QuestGenerator.generate(1, 8, 100, pressure_profile=QuestPressureProfile())
    assert q is not None


# ── QuestOpportunity model + generator tests (E23A) ───────────────────────────

def test_quest_opportunity_constructs():
    """QuestOpportunity dataclass constructs without error (AC1)."""
    opp = QuestOpportunity(
        id="rc_1_42",
        kind="resource_crisis",
        trigger_condition="iron_ore depleted in old_mine at tick 42",
        objective_chain=("fetch:iron_ore:3",),
        reward_spec={"gold": 50, "xp": 100, "faction_rep": 0.1},
        faction_source=None,
        expiry_ticks=200,
        source_event_id="RESOURCE_DEPLETED_old_mine_42",
    )
    assert opp.kind == "resource_crisis"
    assert opp.id == "rc_1_42"
    assert opp.objective_chain == ("fetch:iron_ore:3",)
    assert opp.faction_source is None


def test_resource_crisis_quest_generated_on_depletion():
    """from_resource_depleted() returns non-None QuestOpportunity with kind='resource_crisis' (AC2)."""
    event = WorldEvent(
        category=WorldEventCategory.RESOURCE_DEPLETED,
        tick=42,
        region_id="old_mine",
        subject="iron_ore",
        severity=1.0,
    )
    result = QuestOpportunityGenerator.from_resource_depleted(event, tick=42, seed=0)
    assert result is not None
    assert result.kind == "resource_crisis"
    assert result.source_event_id is not None
    assert len(result.objective_chain) > 0
    assert "iron_ore" in result.objective_chain[0]


def test_quest_generation_determinism():
    """Same input + same seed → same QuestOpportunity.id (AC3)."""
    event = WorldEvent(
        category=WorldEventCategory.RESOURCE_DEPLETED,
        tick=100,
        region_id="forest_node",
        subject="wood",
        severity=0.8,
    )
    r1 = QuestOpportunityGenerator.from_resource_depleted(event, tick=100, seed=7)
    r2 = QuestOpportunityGenerator.from_resource_depleted(event, tick=100, seed=7)
    assert r1 is not None and r2 is not None
    assert r1.id == r2.id
    assert r1.objective_chain == r2.objective_chain
    assert r1.reward_spec == r2.reward_spec


def test_world_emergence_phase_emits_quest_opportunities():
    """WorldEmergencePhase.execute() includes quest_opportunities in result (AC4)."""
    regions = {
        "old_mine": RegionState(id="old_mine", name="Old Mine", bounds=(0, 0, 10, 10))
    }
    state = AuthoritativeState(entities={}, regions=regions, tick=50, seed=0)
    update = StateUpdate()
    events = [
        WorldEvent(
            category=WorldEventCategory.RESOURCE_DEPLETED,
            tick=48,
            region_id="old_mine",
            subject="iron_ore",
            severity=1.0,
        )
    ]
    _, result = WorldEmergencePhase.execute(state, update, events)
    assert hasattr(result, "quest_opportunities")
    assert len(result.quest_opportunities) > 0
    assert result.quest_opportunities[0].kind == "resource_crisis"


def test_threat_response_quest_generated_on_high_severity():
    """from_threat_signal() returns non-None for high-severity ENTITY_DEATH event."""
    event = WorldEvent(
        category=WorldEventCategory.ENTITY_DEATH,
        tick=55,
        region_id="dark_forest",
        subject="hero",
        severity=0.9,
    )
    result = QuestOpportunityGenerator.from_threat_signal(event, tick=55, seed=0)
    assert result is not None
    assert result.kind == "threat_response"
    assert result.expiry_ticks == 100


def test_threat_response_not_generated_for_low_severity():
    """from_threat_signal() returns None when severity < 0.5 (below threshold)."""
    event = WorldEvent(
        category=WorldEventCategory.ENTITY_DEATH,
        tick=60,
        region_id="dark_forest",
        subject="wolf",
        severity=0.3,
    )
    result = QuestOpportunityGenerator.from_threat_signal(event, tick=60, seed=0)
    assert result is None


def test_entity_need_quest_stub_returns_none():
    """from_entity_need() returns None — diplomatic_errand is a stub until Phase 5."""
    result = QuestOpportunityGenerator.from_entity_need(
        entity_id=1, need_kind="food", ticks_unsatisfied=50, tick=100
    )
    assert result is None


# ── EXPLORE target_pos tests (TCK-20260807-QUEST-EVALUATOR-GATHER-BOUNTY-LIBERATE-GAP) ──
# Prior to this fix, QuestGenerator never populated QuestState.metadata at all, so
# QuestResolutionSystem.evaluate_explore() (src/engine/quests.py) could never detect
# arrival -- every EXPLORE quest was permanently unfulfillable in live gameplay.

def _force_explore_quest(seed_start: int, level: int, tick: int, origin_pos):
    for seed in range(seed_start, seed_start + 200):
        q = QuestGenerator.generate(seed, level, tick, origin_pos=origin_pos)
        if q is not None and q.quest_kind == QuestKind.EXPLORE:
            return q
    raise AssertionError("no EXPLORE quest drawn in 200 seeds -- test setup problem")


def test_explore_quest_gets_target_pos_when_origin_given():
    q = _force_explore_quest(0, level=1, tick=10, origin_pos=(100.0, 100.0))
    assert "target_pos" in q.metadata
    tx, ty = q.metadata["target_pos"]
    dist = ((tx - 100.0) ** 2 + (ty - 100.0) ** 2) ** 0.5
    assert QuestGenerator._EXPLORE_TARGET_MIN_DIST <= dist <= QuestGenerator._EXPLORE_TARGET_MAX_DIST


def test_explore_quest_target_pos_deterministic():
    q1 = _force_explore_quest(5, level=1, tick=20, origin_pos=(0.0, 0.0))
    q2 = _force_explore_quest(5, level=1, tick=20, origin_pos=(0.0, 0.0))
    assert q1.metadata["target_pos"] == q2.metadata["target_pos"]


def test_explore_quest_without_origin_pos_has_no_target_pos():
    q = _force_explore_quest(0, level=1, tick=10, origin_pos=None)
    assert "target_pos" not in q.metadata


def test_non_explore_quest_has_empty_metadata_regardless_of_origin():
    # Level 15 always draws a TIER 3 (BOUNTY/LIBERATE) template -- never EXPLORE.
    q = QuestGenerator.generate(123, 15, 10, origin_pos=(5.0, 5.0))
    assert q.quest_kind != QuestKind.EXPLORE
    assert q.metadata == {}


def test_evaluate_explore_completes_quest_once_entity_reaches_target_pos():
    from src.core.state import EntityState, NavigationComponent
    from src.core.strategic import StrategicComponent
    from src.engine.quests import QuestResolutionSystem

    q = _force_explore_quest(0, level=1, tick=10, origin_pos=(0.0, 0.0))
    target_pos = q.metadata["target_pos"]

    entity = EntityState(
        id=1,
        kind="hero",
        navigation=NavigationComponent(position=target_pos),
        strategic=StrategicComponent(projects={q.id: q}),
    )
    updates = QuestResolutionSystem.evaluate_explore(state=None, entity=entity)
    assert len(updates) == 1
    assert updates[0].quest_id == q.id
    assert updates[0].progress_delta >= q.goal_value


def test_evaluate_explore_does_not_complete_quest_far_from_target_pos():
    from src.core.state import EntityState, NavigationComponent
    from src.core.strategic import StrategicComponent
    from src.engine.quests import QuestResolutionSystem

    q = _force_explore_quest(0, level=1, tick=10, origin_pos=(0.0, 0.0))

    entity = EntityState(
        id=1,
        kind="hero",
        navigation=NavigationComponent(position=(0.0, 0.0)),
        strategic=StrategicComponent(projects={q.id: q}),
    )
    updates = QuestResolutionSystem.evaluate_explore(state=None, entity=entity)
    assert updates == []


# ── HUNT target_kind tests (TCK-20260807-QUEST-HUNT-TARGET-METADATA-GAP) ────────────────────
# Prior to this fix, no HUNT template carried any metadata at all, so
# QuestResolutionSystem.evaluate_combat_victory() could never match a real generated HUNT
# quest to a killed entity -- every HUNT quest was permanently unfulfillable.

def _force_hunt_quest(seed_start: int, level: int, tick: int):
    for seed in range(seed_start, seed_start + 200):
        q = QuestGenerator.generate(seed, level, tick)
        if q is not None and q.quest_kind == QuestKind.HUNT:
            return q
    raise AssertionError("no HUNT quest drawn in 200 seeds -- test setup problem")


def test_wolf_hunt_quest_gets_real_target_kind():
    """q_wolf_hunt (level 6-12) must carry metadata["target_kind"]="wolf" -- a real, corpus-
    grounded entity.kind value (both hungry_wolf and alpha_wolf archetypes declare
    species: "wolf" in entity_archetypes.yaml)."""
    q = _force_hunt_quest(0, level=8, tick=10)
    assert q.name == "Wolf Cull"
    assert q.metadata.get("target_kind") == "wolf"


def test_slime_cull_quest_has_no_target_kind():
    """q_slime_cull (level 1-5) must NOT carry a target_kind -- no "slime" species/archetype exists
    anywhere in the real content corpus, so fabricating one would silently mask a real content
    gap rather than leave it honestly disclosed as uncompletable."""
    found_slime = False
    for seed in range(200):
        q = QuestGenerator.generate(seed, 1, 10)
        if q is not None and q.name == "Clear the Slimes":
            found_slime = True
            assert "target_kind" not in q.metadata
    assert found_slime, "q_slime_cull never drawn in 200 seeds -- test setup problem"


def test_evaluate_combat_victory_completes_wolf_hunt_quest_on_matching_kill():
    from src.core.state import EntityState
    from src.core.strategic import StrategicComponent
    from src.engine.quests import QuestResolutionSystem

    q = _force_hunt_quest(0, level=8, tick=10)
    assert q.metadata.get("target_kind") == "wolf"

    attacker = EntityState(id=1, kind="hero", strategic=StrategicComponent(projects={q.id: q}))
    victim = EntityState(id=2, kind="wolf")

    updates = QuestResolutionSystem.evaluate_combat_victory(attacker, "wolf", victim_entity=victim)
    assert len(updates) == 1
    assert updates[0].quest_id == q.id
    assert updates[0].progress_delta == 1.0


def test_evaluate_combat_victory_does_not_progress_wolf_hunt_quest_on_unrelated_kill():
    from src.core.state import EntityState
    from src.core.strategic import StrategicComponent
    from src.engine.quests import QuestResolutionSystem

    q = _force_hunt_quest(0, level=8, tick=10)
    assert q.metadata.get("target_kind") == "wolf"

    attacker = EntityState(id=1, kind="hero", strategic=StrategicComponent(projects={q.id: q}))
    victim = EntityState(id=2, kind="goblin")

    updates = QuestResolutionSystem.evaluate_combat_victory(attacker, "goblin", victim_entity=victim)
    assert updates == []


def test_wolf_hunt_quest_reaches_completed_status_through_real_kill_loop():
    """End-to-end: real QuestGenerator.generate() -> real
    QuestResolutionSystem.evaluate_combat_victory() -> real QuestService.add_progress(), driven
    by repeated real "wolf" kills, actually reaches QuestStatus.COMPLETED. Not just an
    evaluator-returns-an-update check -- the full progress-accumulation lifecycle."""
    from src.core.state import EntityState
    from src.core.strategic import StrategicComponent
    from src.core.quests import QuestStatus
    from src.engine.quests import QuestResolutionSystem
    from src.quests.service import QuestService

    q = _force_hunt_quest(0, level=8, tick=10)
    assert q.name == "Wolf Cull"
    attacker = EntityState(id=1, kind="hero", strategic=StrategicComponent(projects={q.id: q}))
    victim = EntityState(id=2, kind="wolf")

    current = q
    kills = 0
    for _ in range(int(q.goal_value) + 1):
        upd_list = QuestResolutionSystem.evaluate_combat_victory(attacker, "wolf", victim_entity=victim)
        assert upd_list, "expected a QuestUpdate on every real wolf kill while quest is ACTIVE"
        for u in upd_list:
            current = QuestService.add_progress(current, u.progress_delta)
        attacker = EntityState(id=1, kind="hero", strategic=StrategicComponent(projects={current.id: current}))
        kills += 1
        if current.quest_status != QuestStatus.ACTIVE:
            break

    assert current.quest_status == QuestStatus.COMPLETED
    assert kills > 0


def test_from_resource_depleted_rejects_wrong_category():
    """from_resource_depleted() returns None when given a non-RESOURCE_DEPLETED event."""
    event = WorldEvent(
        category=WorldEventCategory.ENTITY_DEATH,
        tick=10,
        region_id="town",
        subject="goblin",
        severity=1.0,
    )
    result = QuestOpportunityGenerator.from_resource_depleted(event, tick=10, seed=0)
    assert result is None
