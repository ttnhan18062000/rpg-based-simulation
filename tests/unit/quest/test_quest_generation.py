import pytest
from src.quests.generator import QuestGenerator
from src.core.quests import QuestKind
from src.core.models.quests import QuestOpportunity
from src.domains.world_emergence.services import QuestOpportunityGenerator
from src.domains.world_emergence.schema import WorldEvent, WorldEventCategory, WorldEmergenceResult
from src.core.state import AuthoritativeState, RegionState
from src.core.updates import StateUpdate
from src.domains.world_emergence.phase import WorldEmergencePhase

def test_quest_generation_determinism():
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
