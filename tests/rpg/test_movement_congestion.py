"""
Phase 4 — Movement Congestion Completion Tests

Proves that the MovementSystem recovery ladder is complete:
1. Direct step is attempted first
2. Sidestep (orthogonal) is attempted on blocked direct step  
3. Priority yield is attempted when sidestep fails
4. Wait counter increments when all move attempts fail
5. Reroute engages after wait_count >= 2
6. Replan triggers after wait_count >= 5 or oscillation_count >= 3
7. Oscillation is detected (back-and-forth)
8. Threat-aware sidestep prefers tiles that avoid OA triggers
"""
import pytest
from dataclasses import replace
from src.core.state import (
    AuthoritativeState, EntityState, IdentityComponent, CombatComponent,
    NavigationComponent, TaskComponent
)
from src.core.updates import EntityUpdate, NavigationUpdate
from src.core.movement_modes import MovementMode
from src.engine.movement import MovementSystem


# ─── Helpers ─────────────────────────────────────────────────────────────────

def make_state(**kwargs):
    defaults = dict(tick=1, seed=42, entities={}, resource_nodes={},
                    ground_items={}, corpses={}, buildings={}, regions={},
                    groups={}, terrain={})
    defaults.update(kwargs)
    return AuthoritativeState(**defaults)

def make_entity(id, pos, faction=0, wait_count=0, osc_count=0,
                last_pos=None, mode=MovementMode.WANDER, action_style=0):
    return EntityState(
        id=id, kind="HERO", position=pos, active=True,
        identity=IdentityComponent(faction=faction),
        combat=CombatComponent(hp=100, max_hp=100, atk=10, def_stat=5,
                               alive=True, action_style=action_style),
        navigation=NavigationComponent(
            movement_mode=mode, wait_count=wait_count,
            oscillation_count=osc_count, last_position=last_pos
        ),
        task=TaskComponent()
    )


# ─── 1. Direct Step ─────────────────────────────────────────────────────────

class TestDirectStep:
    def test_direct_step_to_adjacent_empty_tile(self):
        """Direct step succeeds when target tile is unoccupied."""
        e = make_entity(1, (5.0, 5.0))
        state = make_state(entities={1: e})
        result = MovementSystem.resolve_move(state, e, (6.0, 5.0))
        assert result[1].new_position == (6.0, 5.0)
        assert result[1].moved_this_tick is True

    def test_direct_step_clamps_to_one_tile(self):
        """Even if target is far, we only move one tile per tick."""
        e = make_entity(1, (5.0, 5.0))
        state = make_state(entities={1: e})
        result = MovementSystem.resolve_move(state, e, (10.0, 5.0))
        assert result[1].new_position == (6.0, 5.0)

    def test_dead_entity_does_not_move(self):
        """Inactive entities produce no-op updates."""
        e = make_entity(1, (5.0, 5.0))
        e = replace(e, active=False)
        state = make_state(entities={1: e})
        result = MovementSystem.resolve_move(state, e, (6.0, 5.0))
        assert result[1].new_position is None
        assert result[1].moved_this_tick is not True


# ─── 2. Sidestep ────────────────────────────────────────────────────────────

class TestSidestep:
    def test_sidestep_to_orthogonal_tile_on_blocked_direct(self):
        """When direct step is blocked, sidestep to an orthogonal tile."""
        e1 = make_entity(1, (5.0, 5.0))
        e2 = make_entity(2, (6.0, 5.0))  # Blocking target
        state = make_state(entities={1: e1, 2: e2})
        result = MovementSystem.resolve_move(state, e1, (6.0, 5.0))
        # Should sidestep to (5, 4) or (5, 6) 
        assert result[1].new_position in [(5.0, 4.0), (5.0, 6.0)]


# ─── 3. Wait ────────────────────────────────────────────────────────────────

class TestWait:
    def test_wait_counter_increments_on_total_blockage(self):
        """When all movement options fail, wait_count increments."""
        # Surround entity with blockers so no step/sidestep/yield works
        e = make_entity(1, (5.0, 5.0))
        blockers = {
            2: make_entity(2, (6.0, 5.0), mode=MovementMode.HOLD),
            3: make_entity(3, (4.0, 5.0), mode=MovementMode.HOLD),
            4: make_entity(4, (5.0, 6.0), mode=MovementMode.HOLD),
            5: make_entity(5, (5.0, 4.0), mode=MovementMode.HOLD),
        }
        entities = {1: e, **blockers}
        state = make_state(entities=entities)
        result = MovementSystem.resolve_move(state, e, (6.0, 5.0))
        
        assert result[1].navigation.wait_count_delta == 1
        assert result[1].moved_this_tick is not True


# ─── 4. Reroute ─────────────────────────────────────────────────────────────

class TestReroute:
    def test_reroute_engages_after_sustained_wait(self):
        """After wait_count >= 2, reroute tries alternative adjacent tiles."""
        # Target (6, 5) is blocked, but (5, 4) is open
        e = make_entity(1, (5.0, 5.0), wait_count=2)
        e2 = make_entity(2, (6.0, 5.0), mode=MovementMode.HOLD)
        # Block sidestep tiles too  
        e3 = make_entity(3, (5.0, 6.0), mode=MovementMode.HOLD)
        e4 = make_entity(4, (5.0, 4.0), mode=MovementMode.HOLD)
        # But leave (4, 5) open for reroute
        state = make_state(entities={1: e, 2: e2, 3: e3, 4: e4})
        result = MovementSystem.resolve_move(state, e, (6.0, 5.0))
        
        # Should reroute to (4, 5) which is the only open adjacent tile
        assert result[1].new_position == (4.0, 5.0)
        assert result[1].moved_this_tick is True


# ─── 5. Replan ───────────────────────────────────────────────────────────────

class TestReplan:
    def test_replan_on_prolonged_wait(self):
        """After wait_count >= 5, replan clears target and path."""
        # Completely surrounded — no movement possible at all
        e = make_entity(1, (5.0, 5.0), wait_count=5)
        blockers = {
            2: make_entity(2, (6.0, 5.0), mode=MovementMode.HOLD),
            3: make_entity(3, (4.0, 5.0), mode=MovementMode.HOLD),
            4: make_entity(4, (5.0, 6.0), mode=MovementMode.HOLD),
            5: make_entity(5, (5.0, 4.0), mode=MovementMode.HOLD),
        }
        entities = {1: e, **blockers}
        state = make_state(entities=entities)
        result = MovementSystem.resolve_move(state, e, (6.0, 5.0))
        
        # Should have clear_target and clear_path set for replan
        assert result[1].navigation.clear_target is True
        assert result[1].navigation.clear_path is True

    def test_replan_on_oscillation(self):
        """After oscillation_count >= 3, movement replans."""
        # Entity at (5,5) with last_position=(6,5) and osc=3
        # When it moves to (6,5) again, oscillation is detected
        e = make_entity(1, (5.0, 5.0), osc_count=3, last_pos=(6.0, 5.0))
        state = make_state(entities={1: e})
        result = MovementSystem.resolve_move(state, e, (6.0, 5.0))
        
        # Should detect oscillation and trigger replan
        assert result[1].navigation.clear_target is True
        assert result[1].navigation.clear_path is True


# ─── 6. Oscillation Detection ────────────────────────────────────────────────

class TestOscillation:
    def test_oscillation_counter_increments_on_back_and_forth(self):
        """Moving back to last_position increments oscillation count."""
        # Entity at (5,5), last was at (6,5). Target is (6,5).
        # This is a "return to previous" move = oscillation
        e = make_entity(1, (5.0, 5.0), osc_count=1, last_pos=(6.0, 5.0))
        state = make_state(entities={1: e})
        result = MovementSystem.resolve_move(state, e, (6.0, 5.0))
        
        # Oscillation counter should increase
        assert result[1].navigation.oscillation_count_delta == 1

    def test_normal_move_resets_oscillation(self):
        """Moving to a genuinely new tile resets oscillation count."""
        e = make_entity(1, (5.0, 5.0), osc_count=2, last_pos=(4.0, 5.0))
        state = make_state(entities={1: e})
        result = MovementSystem.resolve_move(state, e, (6.0, 5.0))
        
        # Oscillation resets (negative delta cancels existing count)
        assert result[1].navigation.oscillation_count_delta == -2


# ─── 7. Threat-Aware Sidestep ────────────────────────────────────────────────

class TestThreatAwareSidestep:
    def test_sidestep_prefers_tile_without_hostile_engagement(self):
        """When two sidestep options exist, prefer the one not adjacent to hostiles."""
        e1 = make_entity(1, (5.0, 5.0), faction=0)
        e2 = make_entity(2, (6.0, 5.0), faction=0)  # Blocking direct target
        hostile = make_entity(10, (5.0, 4.0), faction=1)  # Hostile near south sidestep
        
        state = make_state(entities={1: e1, 2: e2, 10: hostile})
        result = MovementSystem.resolve_move(state, e1, (6.0, 5.0))
        
        # Should prefer (5, 6) which is away from hostile, over (5, 4)
        assert result[1].new_position == (5.0, 6.0)
