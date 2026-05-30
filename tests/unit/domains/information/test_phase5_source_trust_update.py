"""
tests/unit/domains/information/test_phase5_source_trust_update.py

Phase 5 — SourceTrustUpdateService unit tests.
"""

import pytest
from src.core.builder import V2EntityBuilder
from src.core.strategic import StrategicComponent, SourceTrustEntry
from src.domains.information.trust import SourceTrustUpdateService


def _entity(e_id, initial_trust_map=None):
    b = V2EntityBuilder(e_id)
    sc = StrategicComponent(source_trust=initial_trust_map or {})
    b.replace_strategic(sc)
    return b.build()


def test_confirmed_increases_trust_slightly():
    actor = _entity(1)
    
    # Defaults to 0.5 trust
    entry = SourceTrustUpdateService.update(actor, 2, "CONFIRMED")
    
    assert entry.trust == 0.58
    assert entry.interactions == 1
    assert entry.last_outcome == "CONFIRMED"


def test_contradiction_decreases_trust_slightly():
    # Setup initial trust
    init_entry = SourceTrustEntry(entity_id=2, trust=0.7, interactions=5)
    actor = _entity(1, {2: init_entry})
    
    entry = SourceTrustUpdateService.update(actor, 2, "CONTRADICTED")
    
    assert entry.trust == 0.58  # 0.7 - 0.12 = 0.58
    assert entry.interactions == 6
    assert entry.last_outcome == "CONTRADICTED"


def test_trust_clamps_at_boundaries():
    init_entry = SourceTrustEntry(entity_id=2, trust=0.95, interactions=1)
    actor = _entity(1, {2: init_entry})
    
    entry = SourceTrustUpdateService.update(actor, 2, "CONFIRMED")
    assert entry.trust == 1.0  # Clamps to 1.0
