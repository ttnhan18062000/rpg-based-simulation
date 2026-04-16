"""Event Interpretation Service — translates raw simulation events into semantic social events. [PHASE 2]

This service analyzes simulation outcomes (combat results, movement, looting) and
produces InterpretedLifeEvent records that carry social meaning and deltas.
"""

from __future__ import annotations

import uuid
import logging
from typing import TYPE_CHECKING, List

from src.core.models.life_events import InterpretedLifeEvent
from src.core.models.enums import InterpretedLifeEventKind, EnemyTier, EntityRole, Domain
from src.core.models.vectors import Vector2

if TYPE_CHECKING:
    from src.core.entities.entity import Entity
    from src.core.models.world_state import WorldState
    from src.core.models.combat import CombatTraceRecord
    from src.systems.rng import DeterministicRNG

logger = logging.getLogger(__name__)

class EventInterpreterService:
    """Centralized service for semantic event interpretation."""

    @classmethod
    def interpret_combat_aftermath(
        cls,
        actor: Entity, 
        defender: Entity, 
        combat_result: CombatTraceRecord, 
        world: WorldState,
        rng: DeterministicRNG | None = None
    ) -> List[InterpretedLifeEvent]:
        """Detect near-death, ally-death, boss-encounter, and avenging ally from combat. [PHASE 2]"""
        events = []
        tick = world.tick
        
        # 1. Near-Death detection (Defender side)
        hp_ratio = defender.combat.hp / defender.combat.max_hp if defender.combat.max_hp > 0 else 0
        if hp_ratio < 0.2 and defender.combat.alive and combat_result.damage > 0:
            events.append(InterpretedLifeEvent(
                event_id=f"evt-{rng.next_hex(Domain.SOCIAL, defender.id, tick, sub_id=0)}" if rng else f"evt-{uuid.uuid4().hex[:8]}",
                kind=InterpretedLifeEventKind.NEAR_DEATH,
                tick=tick,
                actor_id=defender.id,
                subject_ids=[actor.id],
                location=defender.spatial.pos,
                severity=8.0,
                public_visibility=0.1,
                turning_point_candidate=True,
                relationship_deltas={actor.id: {"fear": 0.6, "trust": -0.4, "resentment": 0.5}}
            ))

        # 2a. Betrayal Detection: Victim's perspective (Turning Point & Sentiment)
        if actor.identity.faction == defender.identity.faction and actor.id != defender.id and combat_result.damage > 0:
             events.append(InterpretedLifeEvent(
                event_id=f"evt-{rng.next_hex(Domain.SOCIAL, defender.id, tick, sub_id=1)}" if rng else f"evt-{uuid.uuid4().hex[:8]}",
                kind=InterpretedLifeEventKind.BETRAYAL,
                tick=tick,
                actor_id=defender.id, # Perceiver
                subject_ids=[actor.id], # Perpetrator
                location=actor.spatial.pos,
                severity=9.0,
                public_visibility=0.7,
                turning_point_candidate=True,
                relationship_deltas={actor.id: {"trust": -1.0, "resentment": 1.0, "loyalty": -0.8}}
            ))
             
             # 2b. Betrayal Detection: Perpetrator's perspective (Reputation & Tags)
             events.append(InterpretedLifeEvent(
                event_id=f"evt-{rng.next_hex(Domain.SOCIAL, actor.id, tick, sub_id=2)}" if rng else f"evt-{uuid.uuid4().hex[:8]}",
                kind=InterpretedLifeEventKind.BETRAYAL,
                tick=tick,
                actor_id=actor.id, # Perpetrator
                subject_ids=[defender.id], # Victim
                location=actor.spatial.pos,
                severity=9.0,
                public_visibility=0.7,
                turning_point_candidate=False, 
                reputation_deltas={"trustworthiness": -2.0},
                tags_add=["Ally-Slayer"]
            ))

        # 3. Boss Encounter (Actor side)
        if defender.identity.role == EntityRole.WORLD_BOSS:
             events.append(InterpretedLifeEvent(
                event_id=f"evt-{rng.next_hex(Domain.SOCIAL, actor.id, tick, sub_id=3)}" if rng else f"evt-{uuid.uuid4().hex[:8]}",
                kind=InterpretedLifeEventKind.FIRST_BOSS_ENCOUNTER,
                tick=tick,
                actor_id=actor.id,
                subject_ids=[defender.id],
                location=actor.spatial.pos,
                severity=9.0,
                public_visibility=0.8,
                turning_point_candidate=True
            ))

        # 4. Death Interpretation (Ally Died / First Kill / Avenger)
        if not defender.combat.alive:
            # ... (lines 87-113)
            if actor.identity.kill_count == 1:
                 events.append(InterpretedLifeEvent(
                    event_id=f"evt-{rng.next_hex(Domain.SOCIAL, actor.id, tick, sub_id=4)}" if rng else f"evt-{uuid.uuid4().hex[:8]}",
                    kind=InterpretedLifeEventKind.FIRST_KILL,
                    tick=tick,
                    actor_id=actor.id,
                    subject_ids=[defender.id],
                    location=actor.spatial.pos,
                    severity=7.0,
                    public_visibility=0.5,
                    turning_point_candidate=True
                ))
            
            if actor.identity.faction != defender.identity.faction:
                  events.append(InterpretedLifeEvent(
                    event_id=f"evt-{rng.next_hex(Domain.SOCIAL, actor.id, tick, sub_id=5)}" if rng else f"evt-{uuid.uuid4().hex[:8]}",
                    kind=InterpretedLifeEventKind.SLAY_FOE,
                    tick=tick,
                    actor_id=actor.id,
                    subject_ids=[defender.id],
                    location=actor.spatial.pos,
                    severity=3.0,
                    public_visibility=0.6,
                    reputation_deltas={"heroism_score": 0.2, "threat_notoriety": 0.1}
                ))

        # Apply Reputation Modifiers to all generated events
        for event in events:
            cls._apply_reputation_modifiers(actor, event)

        return events

    @classmethod
    def _apply_reputation_modifiers(cls, actor: Entity, event: InterpretedLifeEvent) -> None:
        """Adjust social deltas based on actor's current reputation."""
        rep = actor.identity.reputation
        tags = set(rep.reputation_tags)
        
        for sid, deltas in event.relationship_deltas.items():
            # 1. Trust Penalty for Betrayers
            if ("Ally-Slayer" in tags or "BETRAYER" in tags or rep.trustworthiness < 0):
                if deltas.get("trust", 0) > 0:
                    deltas["trust"] *= 0.5
                if deltas.get("loyalty", 0) > 0:
                    deltas["loyalty"] *= 0.5
            
            # 2. Admiration Boost for Heroes
            if rep.heroism_score > 5.0 and deltas.get("admiration", 0) > 0:
                deltas["admiration"] *= 1.2
            
            # 3. Fear Boost for Notorious Threat
            if rep.threat_notoriety > 5.0 and deltas.get("fear", 0) > 0:
                deltas["fear"] *= 1.3

    @staticmethod
    def interpret_flight(
        actor: Entity, 
        threat_source_id: int, 
        threat_level: float, 
        world: WorldState,
        rng: DeterministicRNG | None = None
    ) -> List[InterpretedLifeEvent]:
        """Detect fleeing from a significant threat."""
        events = []
        if threat_level > 0.7:
            events.append(InterpretedLifeEvent(
                event_id=f"evt-{rng.next_hex(Domain.SOCIAL, actor.id, world.tick, sub_id=6)}" if rng else f"evt-{uuid.uuid4().hex[:8]}",
                kind=InterpretedLifeEventKind.FLED_FROM_THREAT,
                tick=world.tick,
                actor_id=actor.id,
                subject_ids=[threat_source_id],
                location=actor.spatial.pos,
                severity=4.0 * threat_level,
                public_visibility=0.3,
                reputation_deltas={"cowardice_score": 0.2}
            ))
        return events

    @staticmethod
    def interpret_position_hold(
        actor: Entity, 
        threats_nearby_count: int, 
        ticks_held: int, 
        world: WorldState,
        rng: DeterministicRNG | None = None
    ) -> List[InterpretedLifeEvent]:
        """Detect holding ground against multiple threats."""
        events = []
        if threats_nearby_count >= 2 and ticks_held >= 5:
            events.append(InterpretedLifeEvent(
                event_id=f"evt-{rng.next_hex(Domain.SOCIAL, actor.id, world.tick, sub_id=7)}" if rng else f"evt-{uuid.uuid4().hex[:8]}",
                kind=InterpretedLifeEventKind.HELD_POSITION,
                tick=world.tick,
                actor_id=actor.id,
                location=actor.spatial.pos,
                severity=5.0,
                public_visibility=0.6,
                reputation_deltas={"heroism_score": 0.5, "defender_score": 0.3}
            ))
        return events

    @staticmethod
    def interpret_looting(
        actor: Entity, 
        danger_level: float, 
        world: WorldState,
        rng: DeterministicRNG | None = None
    ) -> List[InterpretedLifeEvent]:
        """Detect looting while in observable danger."""
        events = []
        if danger_level > 0.5:
            events.append(InterpretedLifeEvent(
                event_id=f"evt-{rng.next_hex(Domain.SOCIAL, actor.id, world.tick, sub_id=8)}" if rng else f"evt-{uuid.uuid4().hex[:8]}",
                kind=InterpretedLifeEventKind.LOOTED_DURING_DANGER,
                tick=world.tick,
                actor_id=actor.id,
                location=actor.spatial.pos,
                severity=3.0,
                public_visibility=0.4,
                reputation_deltas={"greed_score": 0.4}
            ))
        return events

    @classmethod
    def interpret_tactical_outcome(
        cls,
        world: WorldState,
        actor: Entity,
        spatial_up: "SpatialUpdate",
        rng: DeterministicRNG | None = None
    ) -> InterpretedLifeEvent | None:
        """Analyze movement for tactical meaning (Disengage, Town Entry, etc.). [PHASE 2]"""
        # Basic implementation: Detect substantial movement away from danger
        # or reaching a safe zone (Town/Sanctuary)
        from src.core.models.enums import Material
        
        tick = world.tick
        pos = spatial_up.new_pos
        prev_pos = actor.spatial.pos
        
        # 1. Town Entry detection
        tile = world.grid.get(pos)
        prev_tile = world.grid.get(prev_pos)
        
        if tile == Material.TOWN and prev_tile != Material.TOWN:
            return InterpretedLifeEvent(
                event_id=f"evt-{rng.next_hex(Domain.SOCIAL, actor.id, tick, sub_id=9)}" if rng else f"evt-{uuid.uuid4().hex[:8]}",
                kind=InterpretedLifeEventKind.HOMECOMING if actor.kind == "hero" else InterpretedLifeEventKind.TRESPASS,
                tick=tick,
                actor_id=actor.id,
                location=pos,
                severity=2.0,
                public_visibility=0.3
            )
            
        return None

    @staticmethod
    def interpret_intel_confirmation(
        actor: Entity,
        source_id: int | str,
        tick: int,
        rng: DeterministicRNG | None = None
    ) -> InterpretedLifeEvent:
        """Detect confirmation of provided intel. [PHASE 3]"""
        return InterpretedLifeEvent(
            event_id=f"evt-{rng.next_hex(Domain.SOCIAL, actor.id, tick, sub_id=10)}" if rng else f"evt-{uuid.uuid4().hex[:8]}",
            kind=InterpretedLifeEventKind.INTEL_CONFIRMED,
            tick=tick,
            actor_id=actor.id,
            subject_ids=[source_id] if isinstance(source_id, int) else ([int(source_id)] if isinstance(source_id, str) and source_id.isdigit() else []),
            location=actor.spatial.pos,
            severity=3.0,
            public_visibility=0.2,
            relationship_deltas={int(source_id) if isinstance(source_id, str) and source_id.isdigit() else source_id: {"trust": 0.2, "respect": 0.1}} if isinstance(source_id, int) or (isinstance(source_id, str) and source_id.isdigit()) else {},
            details={"source_id": source_id}
        )

    @staticmethod
    def interpret_intel_refutation(
        actor: Entity,
        source_id: int | str,
        tick: int,
        rng: DeterministicRNG | None = None
    ) -> InterpretedLifeEvent:
        """Detect refutation of provided intel. [PHASE 3]"""
        return InterpretedLifeEvent(
            event_id=f"evt-{rng.next_hex(Domain.SOCIAL, actor.id, tick, sub_id=11)}" if rng else f"evt-{uuid.uuid4().hex[:8]}",
            kind=InterpretedLifeEventKind.INTEL_REFUTED,
            tick=tick,
            actor_id=actor.id,
            subject_ids=[source_id] if isinstance(source_id, int) else ([int(source_id)] if isinstance(source_id, str) and source_id.isdigit() else []),
            location=actor.spatial.pos,
            severity=5.0,
            public_visibility=0.2,
            relationship_deltas={int(source_id) if isinstance(source_id, str) and source_id.isdigit() else source_id: {"trust": -0.4, "resentment": 0.3}} if isinstance(source_id, int) or (isinstance(source_id, str) and source_id.isdigit()) else {},
            details={"source_id": source_id}
        )
