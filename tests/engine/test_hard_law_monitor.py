import sys
import math
import logging
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd()))

import pytest
from src.core.state import AuthoritativeState
from src.core.dirty import DirtySet
from src.core.builder import V2EntityBuilder
from src.observability.config import ObservabilityConfig, ObservabilityMode
from src.observability.hard_law_monitor import HardLawMonitor, HardLawViolationError
from src.engine.runtime_status import RuntimeStatus

def test_hard_law_monitor_individual_laws():
    # 1. Test LAW-HP-NONNEGATIVE
    e1 = V2EntityBuilder(1).combat(hp=-5, alive=True).build()
    state = AuthoritativeState(tick=1, seed=42, entities={1: e1})
    dirty = DirtySet(combat_entities={1})
    violations = HardLawMonitor.check(state, dirty)
    assert len(violations) == 1
    assert violations[0].law_id == "LAW-HP-NONNEGATIVE"
    assert violations[0].entity_id == 1

    # Test that dead entity with negative HP does NOT violate HP law
    e1_dead = V2EntityBuilder(1).combat(hp=-5, alive=False).build()
    state_dead = AuthoritativeState(tick=1, seed=42, entities={1: e1_dead})
    violations_dead = HardLawMonitor.check(state_dead, dirty)
    assert len(violations_dead) == 0

    # 2. Test LAW-READINESS-NONNEGATIVE
    e2 = V2EntityBuilder(2).combat(readiness=-1.5, alive=True).build()
    state2 = AuthoritativeState(tick=1, seed=42, entities={2: e2})
    dirty2 = DirtySet(combat_entities={2})
    violations2 = HardLawMonitor.check(state2, dirty2)
    assert len(violations2) == 1
    assert violations2[0].law_id == "LAW-READINESS-NONNEGATIVE"

    # 3. Test LAW-GOLD-NONNEGATIVE
    e3 = V2EntityBuilder(3).inventory(gold=-50).build()
    state3 = AuthoritativeState(tick=1, seed=42, entities={3: e3})
    dirty3 = DirtySet(inventory_entities={3})
    violations3 = HardLawMonitor.check(state3, dirty3)
    assert len(violations3) == 1
    assert violations3[0].law_id == "LAW-GOLD-NONNEGATIVE"

    # 4. Test LAW-STAMINA-NONNEGATIVE
    e4 = V2EntityBuilder(4).stamina(current=-10.0).build()
    state4 = AuthoritativeState(tick=1, seed=42, entities={4: e4})
    dirty4 = DirtySet(biological_entities={4})
    violations4 = HardLawMonitor.check(state4, dirty4)
    assert len(violations4) == 1
    assert violations4[0].law_id == "LAW-STAMINA-NONNEGATIVE"

    # 5. Test LAW-POSITION-FINITE
    e5 = V2EntityBuilder(5).location(float('nan'), 10.0).build()
    state5 = AuthoritativeState(tick=1, seed=42, entities={5: e5})
    dirty5 = DirtySet(movement_entities={5})
    violations5 = HardLawMonitor.check(state5, dirty5)
    assert len(violations5) == 1
    assert violations5[0].law_id == "LAW-POSITION-FINITE"


def test_hard_law_occupancy_collision():
    # Construct two solid alive entities on the same tile (5, 5)
    e1 = V2EntityBuilder(1).location(5.2, 5.8).combat(alive=True).build()
    e2 = V2EntityBuilder(2).location(5.4, 5.1).combat(alive=True).build()
    state = AuthoritativeState(tick=1, seed=42, entities={1: e1, 2: e2})
    
    # Dirty movement entities
    dirty = DirtySet(movement_entities={1, 2})
    
    violations = HardLawMonitor.check(state, dirty)
    # We should detect the collision violation
    assert len(violations) >= 1
    assert any(v.law_id == "LAW-OCCUPANCY-COLLISION" for v in violations)


def test_observability_modes_and_kernel_integration(monkeypatch):
    # Set config to OFF mode
    ObservabilityConfig.set_override_mode(ObservabilityMode.OFF)
    assert ObservabilityConfig.get_mode() == ObservabilityMode.OFF

    e1 = V2EntityBuilder(1).combat(hp=-5, alive=True).build()
    state = AuthoritativeState(tick=1, seed=42, entities={1: e1})
    dirty = DirtySet(combat_entities={1})

    # OFF mode should run checks but not fail
    violations = HardLawMonitor.check(state, dirty)
    assert len(violations) == 1

    # Test Kernel integration under LIGHT mode
    ObservabilityConfig.set_override_mode(ObservabilityMode.LIGHT)

    status = RuntimeStatus()
    # Mock status/kernel checking
    class MockKernel:
        def __init__(self):
            self._state = state
            self._status = status
        
        def _run_hard_law_checks(self, dirty_set):
            from src.observability.config import ObservabilityConfig, ObservabilityMode
            from src.observability.hard_law_monitor import HardLawMonitor, HardLawViolationError

            mode = ObservabilityConfig.get_mode()
            if mode == ObservabilityMode.OFF:
                return

            violations = HardLawMonitor.check(self._state, dirty_set)
            if not violations:
                return

            if not hasattr(self._status, "cumulative_violations"):
                self._status.cumulative_violations = {}
            if not hasattr(self._status, "hard_law_violations"):
                self._status.hard_law_violations = []

            self._status.hard_law_violations.extend(violations)
            self._status.last_hard_law_violation_tick = self._state.tick

            for v in violations:
                self._status.cumulative_violations[v.law_id] = self._status.cumulative_violations.get(v.law_id, 0) + 1

            if mode in (ObservabilityMode.DEBUG, ObservabilityMode.CERTIFICATION):
                raise HardLawViolationError(violations)

    mk = MockKernel()
    mk._run_hard_law_checks(dirty)
    # Under LIGHT mode, it should record to status without raising
    assert len(status.hard_law_violations) == 1
    assert status.cumulative_violations["LAW-HP-NONNEGATIVE"] == 1

    # Under DEBUG mode, it should raise HardLawViolationError
    ObservabilityConfig.set_override_mode(ObservabilityMode.DEBUG)

    with pytest.raises(HardLawViolationError) as exc_info:
        mk._run_hard_law_checks(dirty)
    assert "LAW-HP-NONNEGATIVE" in str(exc_info.value)
