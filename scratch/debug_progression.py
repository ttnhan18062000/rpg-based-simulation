
import sys
import os
sys.path.append(os.getcwd())

from src.core.state import AuthoritativeState, EntityState, IdentityComponent
from src.core.enums import EntityRole, Faction
from src.platform.rng import DeterministicRNG
from src.engine.kernel import Kernel
from src.config.profiles import RuntimeProfile, HardwareClass
from src.core.builder import V2EntityBuilder
from dataclasses import replace

def create_test_profile():
    return RuntimeProfile(
        name="test_profile",
        hardware_class=HardwareClass.CLASS_A,
        max_ram_mb=1024,
        max_cpu_percent=50.0,
        max_worker_count=4,
        max_queue_depth=100,
        max_replay_buffer_kb=1024,
        max_observability_budget_percent=5.0,
        max_tick_budget_ms=100.0
    )

hero = (V2EntityBuilder(1).kind("HERO").at((5, 5)).role(EntityRole.HERO).faction(Faction.HERO_GUILD).with_base_stats(atk=100).build())
goblin = (V2EntityBuilder(2).at((6, 5)).role(EntityRole.MONSTER).faction(Faction.MONSTER_HORDE).with_base_stats(hp=5).build())
hero = replace(hero, identity=replace(hero.identity, evolution_points=990))

state = AuthoritativeState(tick=1, seed=42, entities={1: hero, 2: goblin})
rng = DeterministicRNG(42)
profile = create_test_profile()
kernel = Kernel(profile, state, rng)

# Warmup 10 ticks (accumulate readiness)
for _ in range(10): kernel.tick_once()
# Tick 11: Execute attack
kernel.tick_once()

h_final = kernel.state.entities[1]
print(f"Level: {h_final.identity.evolution_level}")
print(f"Points: {h_final.identity.evolution_points}")
print(f"Kind: {h_final.kind}")
