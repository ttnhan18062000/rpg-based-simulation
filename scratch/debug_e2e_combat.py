
from tests.helpers.combat_arena import CombatArena
from src.core.gameplay.classes import HeroClass
from src.core.models.enums import AIState

def debug_arena_failure():
    arena = CombatArena()
    # Entity 1: Melee Hero (Iron Sword, ATK 15, HP 100)
    arena.add_hero(1, pos=(5, 5), weapon="iron_sword", hp=100, atk=15)
    # Entity 2: Ranged Hero (Shortbow, ATK 12, HP 80, Ranger)
    arena.add_hero(2, pos=(2, 5), weapon="shortbow", hp=80, atk=12,
                   hero_class=HeroClass.RANGER)
    # Entity 3: Mob (Rusty Sword, ATK 8, HP 80)
    arena.add_mob(3, pos=(6, 5), weapon="rusty_sword", hp=80, atk=8)
    
    # Force them to stay awake (AOA Stabilization)
    for eid in [1, 2, 3]:
        ent = arena.entity(eid)
        if ent:
            ent.mind.routine.sleep_debt = 0.0
            ent.mind.routine.hunger_level = 0.0
            # Set a long disrupted_until_tick to prevent routine transitions
            ent.mind.routine.disrupted_until_tick = 1000
    
    print(f"Initial: Mob HP={arena.entity(3).combat.hp}, Pos={arena.entity(3).spatial.pos}")
    print(f"Initial: Hero1 Pos={arena.entity(1).spatial.pos}")
    print(f"Initial: Hero2 Pos={arena.entity(2).spatial.pos}")
    
    for t in range(100):
        arena.loop.tick_once()
        mob = arena.entity(3)
        if not mob or not mob.combat.alive:
            print(f"Target died at tick {t}")
            return
        
        # Log combat engagement
        if t % 5 == 0:
            print(f"Tick {t}: Mob HP={mob.combat.hp}, Pos={mob.spatial.pos}")
            h1 = arena.entity(1)
            h2 = arena.entity(2)
            # Use value since use_enum_values=True makes it an int in the model
            print(f"  H1: Pos={h1.spatial.pos}, Target={h1.combat.combat_target_id}, HP={h1.combat.hp}, State={h1.mind.decision.ai_state}")
            print(f"  H2: Pos={h2.spatial.pos}, Target={h2.combat.combat_target_id}, HP={h2.combat.hp}, State={h2.mind.decision.ai_state}")

    print("Target survived 100 ticks.")
    mob = arena.entity(3)
    if mob:
        print(f"Final Mob HP: {mob.combat.hp}/{mob.combat.max_hp}")

if __name__ == "__main__":
    debug_arena_failure()
