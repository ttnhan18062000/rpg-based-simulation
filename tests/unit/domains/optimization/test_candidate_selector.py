import pytest
from dataclasses import replace
from src.core.state import AuthoritativeState
from src.core.dirty import DirtySet, CandidateSelector
from src.core.updates import StateUpdate
from src.core.builder import V2EntityBuilder

def test_force_full_scan_returns_all_entities():
    # Test case 1: force_full_scan = True returns all entities regardless of dirty_set
    state = AuthoritativeState(tick=1, seed=100)
    e1 = V2EntityBuilder(1).build()
    e2 = V2EntityBuilder(2).build()
    e3 = V2EntityBuilder(3).build()
    state = replace(state, entities={1: e1, 2: e2, 3: e3})
    
    # Create update with dirty_set only containing 1, but force_full_scan=True
    ds = DirtySet(movement_entities={1})
    update = StateUpdate(force_full_scan=True, dirty_set=ds)
    
    candidates = CandidateSelector.entities(state, update, {"movement"})
    assert candidates == (1, 2, 3)

def test_none_dirty_set_returns_all_entities():
    # Test case 2: dirty_set = None returns all entities
    state = AuthoritativeState(tick=1, seed=100)
    e1 = V2EntityBuilder(1).build()
    e2 = V2EntityBuilder(2).build()
    state = replace(state, entities={1: e1, 2: e2})
    
    update = StateUpdate(force_full_scan=False, dirty_set=None)
    
    candidates = CandidateSelector.entities(state, update, {"movement"})
    assert candidates == (1, 2)

def test_single_domain_selection():
    # Test case 3: dirty_set with movement entities returns only movement entities for domain={"movement"}
    state = AuthoritativeState(tick=1, seed=100)
    e1 = V2EntityBuilder(10).build()
    e2 = V2EntityBuilder(20).build()
    e3 = V2EntityBuilder(30).build()
    state = replace(state, entities={10: e1, 20: e2, 30: e3})
    
    ds = DirtySet(movement_entities={20}, combat_entities={30})
    update = StateUpdate(dirty_set=ds)
    
    candidates = CandidateSelector.entities(state, update, {"movement"})
    assert candidates == (20,)

def test_multi_domain_union():
    # Test case 4: multiple domains requested returns exact union
    state = AuthoritativeState(tick=1, seed=100)
    e1 = V2EntityBuilder(5).build()
    e2 = V2EntityBuilder(15).build()
    e3 = V2EntityBuilder(25).build()
    state = replace(state, entities={5: e1, 15: e2, 25: e3})
    
    ds = DirtySet(movement_entities={5}, strategic_entities={25})
    update = StateUpdate(dirty_set=ds)
    
    candidates = CandidateSelector.entities(state, update, {"movement", "strategic"})
    assert candidates == (5, 25)

def test_include_inactive_false_excludes_inactive():
    # Test case 5: include_inactive=False correctly excludes inactive entities even during force_full_scan and dirty scan
    state = AuthoritativeState(tick=1, seed=100)
    e1 = V2EntityBuilder(1).lifecycle(active=True).build()
    e2 = V2EntityBuilder(2).lifecycle(active=False).build()
    state = replace(state, entities={1: e1, 2: e2})
    
    # Test during full scan
    update_full = StateUpdate(force_full_scan=True)
    c_full = CandidateSelector.entities(state, update_full, {"movement"}, include_inactive=False)
    assert c_full == (1,)
    
    # Test during dirty scan
    ds = DirtySet(movement_entities={1, 2})
    update_dirty = StateUpdate(dirty_set=ds)
    c_dirty = CandidateSelector.entities(state, update_dirty, {"movement"}, include_inactive=False)
    assert c_dirty == (1,)

def test_include_inactive_true_includes_inactive():
    # Test case 6: include_inactive=True includes inactive entities during full scan
    state = AuthoritativeState(tick=1, seed=100)
    e1 = V2EntityBuilder(100).lifecycle(active=True).build()
    e2 = V2EntityBuilder(200).lifecycle(active=False).build()
    state = replace(state, entities={100: e1, 200: e2})
    
    update = StateUpdate(force_full_scan=True)
    candidates = CandidateSelector.entities(state, update, {"movement"}, include_inactive=True)
    assert candidates == (100, 200)

def test_result_order_is_deterministic():
    # Test case 7: result order is deterministic (sorted integer tuple)
    state = AuthoritativeState(tick=1, seed=100)
    e1 = V2EntityBuilder(50).build()
    e2 = V2EntityBuilder(10).build()
    e3 = V2EntityBuilder(30).build()
    state = replace(state, entities={10: e2, 30: e3, 50: e1})
    
    # Unordered set insertion
    ds = DirtySet(movement_entities={50, 30, 10})
    update = StateUpdate(dirty_set=ds)
    
    candidates = CandidateSelector.entities(state, update, {"movement"})
    assert type(candidates) is tuple
    assert candidates == (10, 30, 50)
