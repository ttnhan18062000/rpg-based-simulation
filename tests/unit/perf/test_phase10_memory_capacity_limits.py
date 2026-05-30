# TDD tests for Phase 10 MemoryCapacityLimits
import pytest
from src.domains.optimization.memory_limits import MemoryCapacityLimits, MemoryFact

def test_knowledge_facts_are_capped():
    limits = MemoryCapacityLimits(max_facts=3)
    limits.add_fact(MemoryFact(id="f1", salience=0.5, timestamp=1))
    limits.add_fact(MemoryFact(id="f2", salience=0.6, timestamp=2))
    limits.add_fact(MemoryFact(id="f3", salience=0.7, timestamp=3))
    limits.add_fact(MemoryFact(id="f4", salience=0.8, timestamp=4))
    
    assert len(limits.get_facts()) == 3

def test_opponent_models_are_capped():
    limits = MemoryCapacityLimits(max_opponents=2)
    limits.add_opponent("goblin_1", salience=0.9)
    limits.add_opponent("goblin_2", salience=0.8)
    limits.add_opponent("goblin_3", salience=0.7)
    
    assert len(limits.get_opponents()) == 2

def test_reward_ledger_is_capped():
    limits = MemoryCapacityLimits(max_rewards=2)
    limits.add_reward("quest_1", salience=1.0)
    limits.add_reward("quest_2", salience=0.5)
    limits.add_reward("quest_3", salience=0.8)
    
    assert len(limits.get_rewards()) == 2

def test_cooperation_memory_is_capped():
    limits = MemoryCapacityLimits(max_coop_memories=2)
    limits.add_coop_memory("ally_1", salience=0.5)
    limits.add_coop_memory("ally_2", salience=0.9)
    limits.add_coop_memory("ally_3", salience=0.2)
    
    assert len(limits.get_coop_memories()) == 2

def test_high_salience_memory_survives_eviction():
    limits = MemoryCapacityLimits(max_facts=2)
    limits.add_fact(MemoryFact(id="f_low", salience=0.1, timestamp=1))
    limits.add_fact(MemoryFact(id="f_mid", salience=0.5, timestamp=2))
    limits.add_fact(MemoryFact(id="f_high", salience=0.9, timestamp=3))
    
    # f_low has the lowest salience, it should be evicted first
    facts = limits.get_facts()
    assert "f_low" not in [f.id for f in facts]
    assert "f_high" in [f.id for f in facts]

def test_low_salience_memory_evicted_first():
    limits = MemoryCapacityLimits(max_facts=2)
    limits.add_fact(MemoryFact(id="f1", salience=0.8, timestamp=1))
    limits.add_fact(MemoryFact(id="f2", salience=0.2, timestamp=2))
    limits.add_fact(MemoryFact(id="f3", salience=0.9, timestamp=3))
    
    assert "f2" not in [f.id for f in limits.get_facts()]

def test_capacity_overflow_records_trace_summary():
    limits = MemoryCapacityLimits(max_facts=2)
    limits.add_fact(MemoryFact(id="f1", salience=0.8, timestamp=1))
    limits.add_fact(MemoryFact(id="f2", salience=0.2, timestamp=2))
    limits.add_fact(MemoryFact(id="f3", salience=0.9, timestamp=3))
    
    report = limits.generate_eviction_report()
    assert report["evicted_count"] == 1
    assert "f2" in report["evicted_ids"]
