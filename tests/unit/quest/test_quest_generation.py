import pytest
from src.quests.generator import QuestGenerator
from src.core.quests import QuestKind

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
