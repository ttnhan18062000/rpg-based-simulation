from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional

@dataclass(frozen=True, slots=True)
class SocialBond:
    """A first-class directed relationship record."""
    target_id: int
    familiarity: float = 0.0 # Interaction depth (0.0 to 1.0)
    sentiment: float = 0.0   # Bias/Liking (-1.0 to 1.0)
    last_interaction_tick: int = 0

@dataclass(frozen=True, slots=True)
class BetrayalRecord:
    """A record of a specific betrayal event."""
    contract_id: str
    betrayer_id: int
    victim_id: int
    severity: float = 1.0
    tick: int = 0

@dataclass(frozen=True, slots=True)
class SocialComponent:
    """State for reputation, trust, and betrayal history."""
    trust_history: Dict[int, float] = field(default_factory=dict)       # EntityID -> Trust Score (VERIFIED v2: SocialComponent.trust)
    familiarity_history: Dict[int, float] = field(default_factory=dict) # EntityID -> Familiarity
    debt_history: Dict[int, float] = field(default_factory=dict)        # EntityID -> Debt (Social/Gold)
    fear_history: Dict[int, float] = field(default_factory=dict)        # EntityID -> Fear Score
    grudge_history: Dict[int, float] = field(default_factory=dict)      # EntityID -> Grudge Score (Nemesis)
    salience_history: Dict[int, float] = field(default_factory=dict)    # EntityID -> Interaction Salience
    
    # PH15 Recovery: First-class bonds
    bonds: Dict[int, SocialBond] = field(default_factory=dict)         # EntityID -> Bond
    
    # Domain 4 Hardening: Nemesis & Place Memory
    nemesis_ids: Set[int] = field(default_factory=set) # Promoted from grudge_history
    place_attachment: Dict[str, float] = field(default_factory=dict) # RegionID -> Attachment Score
    
    betrayal_count: int = 0
    betrayal_records: List[BetrayalRecord] = field(default_factory=list)
    public_reputation: float = 1.0   # Unified reputation score (0.0 to 2.0)
    heroism_score: float = 0.0       # Cumulative good deeds
    notoriety_score: float = 0.0     # Cumulative bad deeds
    
    # Domain 7 Hardening: Social Fatigue
    last_offer_tick: int = -1
    rejection_count: Dict[int, int] = field(default_factory=dict) # SourceID -> Count
