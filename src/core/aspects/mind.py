from typing import Any, TYPE_CHECKING, Union, Literal
from pydantic import BaseModel, Field, ConfigDict
from src.core.models.base import Aspect, SimulationModel
from src.core.models.enums import AIState, GoalType, EmotionType
from src.core.models.vectors import Vector2
from src.core.models.lived_structure import RoutineProfile, PlaceAttachment # [PHASE 3]
from src.core.models.strategy import StrategicState  # [PHASE 1]

if TYPE_CHECKING:
    from src.core.entities.entity import Entity

class DecisionDriver(SimulationModel):
    """A structured record explaining a bias or decision driver. [STAGE 1]"""
    model_config = ConfigDict(extra='forbid')
    
    kind: str # 'motive', 'personality', 'emotion', 'belief', 'social', 'biological'
    label: str
    weight: float
    description: str | None = None

class PersonalityProfile(SimulationModel):
    """RPG-focused behavioral traits that bias Utility AI scoring. [PHASE 1]"""
    model_config = ConfigDict(extra='forbid')
    
    archetype: str = "balanced"
    aggression: float = Field(default=0.5, ge=0.0, le=1.0) # Combat weight
    greed: float = Field(default=0.5, ge=0.0, le=1.0)      # Loot weight
    caution: float = Field(default=0.5, ge=0.0, le=1.0)    # Flee/Rest weight
    neuroticism: float = Field(default=0.5, ge=0.0, le=1.0) # Emotional volatility
    loyalty: float = Field(default=0.5, ge=0.0, le=1.0)    # Social/Protect weight
    ambition: float = Field(default=0.5, ge=0.0, le=1.0)   # Level-up/Quest weight
    curiosity: float = Field(default=0.5, ge=0.0, le=1.0)  # Exploration weight

class PersonalMotive(SimulationModel):
    """Long-term persistence motive that biases goal selection over time. [PHASE 1]"""
    model_config = ConfigDict(extra='forbid')
    
    motive_id: str
    kind: str # e.g. "build_wealth", "seek_safety", "prove_strength"
    priority: float = Field(default=1.0, ge=0.0, le=5.0)
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    frustration: float = Field(default=0.0, ge=0.0, le=1.0)
    active: bool = True
    target_id: int | None = None

class DecisionState(SimulationModel):
    """Internal state for AI goal selection and commitment."""
    model_config = ConfigDict(extra='forbid', use_enum_values=True)
    
    ai_state: AIState = AIState.IDLE
    goals: list[str] = Field(default_factory=list)
    last_reason: str = ""
    last_goal: GoalType | None = None
    goal_committed_at: int = 0
    goal_switch_count: int = 0
    goal_cooldowns: dict[GoalType, int] = Field(default_factory=dict)
    goal_scores: dict[GoalType, float] = Field(default_factory=dict)
    
    # Subjective motive weights and personality [PHASE 1]
    personality: PersonalityProfile = Field(default_factory=PersonalityProfile)
    motives: list[PersonalMotive] = Field(default_factory=list)
    motive_utility_biases: dict[GoalType, float] = Field(default_factory=dict) # Calculated from motives
    
    last_appraisal_tick: int = 0                                 # For throttled motive calculation
    boredom_multipliers: dict[GoalType, float] = Field(default_factory=dict)
    consecutive_idle_ticks: int = 0
    action_style: str = "balanced" # aggressive, evasive, balanced
    decision_drivers: list[str] = Field(default_factory=list)
    driver_details: list[DecisionDriver] = Field(default_factory=list)

class ThreatEstimate(SimulationModel):
    """Subjective assessment of another entity's power. [PHASE 1]"""
    model_config = ConfigDict(extra='forbid')
    
    overall: float = 0.0      # 0.0 to 1.0 logic threshold
    survivability: float = 0.5 # Estimated how hard they are to kill
    confidence: float = 0.5    # How certain we are of this estimate (0.0 to 1.0)
    melee_threat: float = 0.0
    ranged_threat: float = 0.0

class BeliefRecord(SimulationModel):
    """A subjective record of what an entity thinks it knows about another. [PHASE 1]"""
    model_config = ConfigDict(extra='forbid')
    
    entity_id: int
    pos: Vector2
    last_seen_tick: int = 0
    stale_ticks: int = 0
    
    # Apparent state (Subjective)
    apparent_kind: str = ""
    apparent_faction: str = ""
    apparent_role: str = ""
    apparent_class: str | None = None
    visible_weapon: str | None = None
    visible_injury: float = 0.0 # 0.0 to 1.0 (apparent damage)
    
    threat: ThreatEstimate = Field(default_factory=ThreatEstimate)
    observed_skills: set[str] = Field(default_factory=set)
    confidence: float = 0.5
    
    # [PHASE 2] Knowledge source quality — differentiates direct vs indirect knowledge
    knowledge_source: str = "direct"  # "direct" or "indirect"
    directness: float = Field(default=1.0, ge=0.0, le=1.0)
    source_confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    
    # Perceived reputation metrics [PHASE 2]
    apparent_reputation_tags: list[str] = Field(default_factory=list)
    apparent_trustworthiness: float = 0.0
    apparent_heroism: float = 0.0
    apparent_threat_notoriety: float = 0.0

MemoryRecord = BeliefRecord # Alias for backward compatibility during transition

from pydantic import model_validator

class PerceptionMemory(SimulationModel):
    """Short-term sensory memory and threat tracking. [AOA STABILIZATION]"""
    model_config = ConfigDict(extra='forbid')
    
    threat_table: dict[int, float] = Field(default_factory=dict)
    terrain_memory: dict[tuple[int, int], int] = Field(default_factory=dict)
    entity_memory: dict[int, MemoryRecord] = Field(default_factory=dict)
    
    @model_validator(mode="after")
    def _validate_memory(self) -> "PerceptionMemory":
        """Force coercion of memory records if they came in as dicts."""
        for eid, rec in self.entity_memory.items():
            if isinstance(rec, dict):
                self.entity_memory[eid] = MemoryRecord.model_validate(rec)
        return self

    memory_stale_ticks: dict[int, int] = Field(default_factory=dict)
    attention_pool: list[int] = Field(default_factory=list)
    max_attention_slots: int = 5
    hero_familiarity: dict[int, float] = Field(default_factory=dict)

class EmotionState(SimulationModel):
    """Short-term emotional spikes and long-term mood."""
    model_config = ConfigDict(extra='forbid', use_enum_values=True)
    
    # Emotional dimensions (AOA Pillar 2: Phased Appraisal)
    panic: float = Field(default=0.0, ge=0.0, le=1.0)
    stuck: float = Field(default=0.0, ge=0.0, le=1.0)
    bravery: float = Field(default=0.5, ge=0.0, le=1.0)
    dread: float = Field(default=0.0, ge=0.0, le=1.0)
    joy: float = Field(default=0.0, ge=0.0, le=1.0)
    
    mood: float = Field(default=0.5, ge=0.0, le=1.0)
    grudges: dict[int, float] = Field(default_factory=dict)

class NavigationState(SimulationModel):
    """Pathfinding and movement history."""
    model_config = ConfigDict(extra='forbid')
    
    cached_path: list[Vector2] | None = Field(default=None, repr=False)
    cached_path_target: Vector2 | None = Field(default=None, repr=False)
    pos_history: list[Vector2] = Field(default_factory=list)
    chase_ticks: int = 0
    engaged_ticks: int = 0

# SocialBondPerception merged into SocialBondRecord in life_events.py [PHASE 2]

class SocialStance(SimulationModel):
    """Subjective relationship mapping and faction standings. [PHASE 2]"""
    model_config = ConfigDict(extra='forbid')
    
    known_bonds: dict[int, "SocialBondRecord"] = Field(default_factory=dict)
    faction_standing: dict[str, float] = Field(default_factory=dict) # FactionID -> Affinity
    
    # [PHASE 2] Influence on decision making
    social_utility_biases: dict[GoalType, float] = Field(default_factory=dict)


class NarrativeDetail(SimulationModel):
    """Base for all typed narrative event details. [AOA STABILIZATION]"""
    model_config = ConfigDict(extra='forbid')

class CombatNarrative(NarrativeDetail):
    """Details for combat-related narrative events (kills, deaths)."""
    type: Literal["combat"] = "combat"
    target_id: int
    target_kind: str
    damage_dealt: int = 0
    was_fatal: bool = False

class LootNarrative(NarrativeDetail):
    """Details for inventory/gold acquisition narrative events."""
    type: Literal["loot"] = "loot"
    item_id: str | None = None
    gold_amount: int = 0
    source: str = "" # e.g. "chest", "corpse", "node"

class DiscoveryNarrative(NarrativeDetail):
    """Details for world exploration events."""
    type: Literal["discovery"] = "discovery"
    location_id: str
    location_name: str
    rarity: str = "common"

class SocialNarrative(NarrativeDetail):
    """Details for major social shifts (Nemesis declaration, betrayal). [PHASE 2]"""
    type: Literal["social"] = "social"
    target_id: int
    change_type: str = "interaction" # interaction, milestone, nemesis, ally
    bond_type: str = "trust" # trust, fear, rivalry
    old_value: float = 0.0
    new_value: float = 0.0

class InterpretedEvent(SimulationModel):
    """A single entry in the narrative memory log. [AOA STABILIZATION]
    
    Pillar 2: Rendering & Explainability. All entries must use typed details
    to ensure the API layer can reliably shape results for the UI.
    """
    model_config = ConfigDict(extra='forbid')
    
    tick: int
    type: str # e.g. "glory", "trauma", "discovery", "social"
    impact: float = 0.0 # Salience/Importance score
    details: Union[CombatNarrative, LootNarrative, DiscoveryNarrative, SocialNarrative, dict[str, Any]] = Field(default_factory=dict)

MemoryLogEntry = InterpretedEvent # Backward compatibility alias

class NarrativeMemory(SimulationModel):
    """Long-term history and narrative directives. [AOA STABILIZATION]"""
    model_config = ConfigDict(extra='forbid')
    
    memory_log: list[InterpretedEvent] = Field(default_factory=list)
    memory_locations: dict[str, float] = Field(default_factory=dict)
    region_fatigue: dict[str, float] = Field(default_factory=dict)
    
    # [PHASE 2] Durable turning-point memories — capped at 20
    turning_points: list["TurningPointRecord"] = Field(default_factory=list)

    def add_turning_point(self, record: "TurningPointRecord", max_records: int = 20) -> None:
        """Add a new turning point with salience-based eviction. [PHASE 2]"""
        # Ensure we don't already have this exact event
        if any(tp.event_id == record.event_id for tp in self.turning_points):
            return
            
        self.turning_points.append(record)
        
        # Prune if over capacity
        if len(self.turning_points) > max_records:
            # Sort by salience (lowest first) and then by tick (oldest first)
            self.turning_points.sort(key=lambda x: (x.salience_score, x.tick))
            # Remove the least salient item
            self.turning_points.pop(0)
            # Re-sort by tick for chronological order
            self.turning_points.sort(key=lambda x: x.tick)

class RoutineState(SimulationModel):
    """Biological needs and daily schedule state. [PHASE 3]"""
    model_config = ConfigDict(extra='forbid')
    
    sleep_debt: float = Field(default=0.0, ge=0.0, le=1.0)
    hunger_level: float = Field(default=0.0, ge=0.0, le=1.0)
    is_sleeping: bool = False
    
    # Pillar 2: Activity tracking [PHASE 3]
    active_routine_id: str | None = None
    disrupted_until_tick: int = 0
    
    # Schedule (Expressed in hours: 0-23, where 1 hour = 10 ticks)
    active_start_hour: int = 6
    active_end_hour: int = 22

class MindAspect(Aspect):
    """Decomposed Mind Aspect using specialized sub-models. [AOA STABILIZATION]
    
    Pillar 1: Domain-Driven Separation. Logic is split across Decision,
    Perception, Emotion, Navigation, and Narrative domains to maintain
    clear ownership lines.
    """
    model_config = ConfigDict(extra='forbid')
    
    decision: DecisionState = Field(default_factory=DecisionState)
    perception: PerceptionMemory = Field(default_factory=PerceptionMemory)
    emotion: EmotionState = Field(default_factory=EmotionState)
    navigation: NavigationState = Field(default_factory=NavigationState)
    narrative: NarrativeMemory = Field(default_factory=NarrativeMemory)
    routine: RoutineState = Field(default_factory=RoutineState)
    social: SocialStance = Field(default_factory=SocialStance)
    
    # Fundamental continuity stratum [PHASE 1]
    strategic: StrategicState = Field(default_factory=StrategicState)
    
    # Pillar 2: Lived Structure [PHASE 3]
    routine_profiles: list[RoutineProfile] = Field(default_factory=list)
    place_attachments: list[PlaceAttachment] = Field(default_factory=list)
    
    bonuses: dict[str, Any] = Field(default_factory=dict)

    @property
    def ai_state(self) -> AIState:
        """AOA Shim: Redirects to decision.ai_state for legacy systems."""
        return self.decision.ai_state

    @ai_state.setter
    def ai_state(self, value: AIState) -> None:
        """AOA Shim: Redirects mutation to decision.ai_state."""
        self.decision.ai_state = value

    @property
    def memory(self) -> dict[int, Any]:
        """AOA Shim: Redirects to perception.entity_memory for legacy systems."""
        return self.perception.entity_memory

    @memory.setter
    def memory(self, value: dict[int, Any]) -> None:
        """AOA Shim: Redirects mutation to perception.entity_memory."""
        self.perception.entity_memory = value

    def total_glory(self) -> float:
        return sum(
            e.impact for e in self.narrative.memory_log
            if e.type.lower() == "glory"
        )

    def total_trauma(self) -> float:
        # Includes specialized survival trauma
        return sum(
            e.impact for e in self.narrative.memory_log
            if e.type.lower() in ("trauma", "survival")
        )
    
    # Memory pruning is now handled authoritatively in ActionSystem [PHASE 0 FIX]

# [PHASE 2] Import for forward reference resolution
from src.core.models.life_events import TurningPointRecord, SocialBondRecord, ReputationProfile  # noqa: E402

PersonalityProfile.model_rebuild()
PersonalMotive.model_rebuild()
ThreatEstimate.model_rebuild()
BeliefRecord.model_rebuild()
MemoryRecord.model_rebuild()
PerceptionMemory.model_rebuild()
EmotionState.model_rebuild()
NavigationState.model_rebuild()
NarrativeDetail.model_rebuild()
CombatNarrative.model_rebuild()
LootNarrative.model_rebuild()
DiscoveryNarrative.model_rebuild()
SocialNarrative.model_rebuild()
MemoryLogEntry.model_rebuild()
NarrativeMemory.model_rebuild()
RoutineState.model_rebuild()
SocialBondRecord.model_rebuild()
SocialStance.model_rebuild()
StrategicState.model_rebuild()
MindAspect.model_rebuild()
