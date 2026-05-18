import sys
from pathlib import Path
sys.path.append(str(Path.cwd()))

import unittest
from src.core.state import AuthoritativeState, EntityState, NavigationComponent, CombatComponent
from src.engine.scheduler import DeterministicScheduler
from src.engine.policy import GovernorPolicy
from src.engine.lod import LODService

class TestLOD(unittest.TestCase):
    def test_lod_scheduling(self):
        # Create 2000 entities
        entities = {}
        # 1000 near (0,0)
        for i in range(1, 1001):
            entities[i] = EntityState(
                id=i, 
                kind="hero",
                navigation=NavigationComponent(position=(0.0, 0.0)),
                combat=CombatComponent(readiness=100.0)
            )
        # 1000 far (1000, 1000)
        for i in range(1001, 2001):
            entities[i] = EntityState(
                id=i, 
                kind="goblin",
                navigation=NavigationComponent(position=(1000.0, 1000.0)),
                combat=CombatComponent(readiness=100.0)
            )
            
        state = AuthoritativeState(tick=100, seed=42, entities=entities, town_center=(0.0, 0.0))
        scheduler = DeterministicScheduler()
        
        # Scenario 1: LOD Disabled
        policy_off = GovernorPolicy(
            lod_enabled=False, 
            system_cadence=GovernorPolicy().system_cadence.model_copy(update={"strategic_intelligence": 1})
        )
        work_off, _ = scheduler.select_work(state, policy_off)
        print(f"Work items (LOD OFF): {len(work_off)}")
        self.assertEqual(len(work_off), 2000)
        
        # Scenario 2: LOD Enabled
        policy_on = GovernorPolicy(
            lod_enabled=True,
            system_cadence=GovernorPolicy().system_cadence.model_copy(update={"strategic_intelligence": 1})
        )
        work_on, _ = scheduler.select_work(state, policy_on)
        print(f"Work items (LOD ON): {len(work_on)}")
        
        # Expected:
        # 1000 near entities (LOD 0) -> all run
        # 1000 far entities (LOD 3, cadence 10) -> approx 1/10 run
        # (tick 100 + id) % 10 == 0
        # For IDs 1001 to 2000:
        # (100 + 1001) % 10 = 1
        # (100 + 1010) % 10 = 0 (Match!)
        # There are exactly 100 such IDs in the range [1001, 2000].
        
        self.assertEqual(len(work_on), 1100)
        print("LOD scheduling test passed!")

if __name__ == "__main__":
    unittest.main()
