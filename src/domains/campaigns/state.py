"""
src/domains/campaigns/state.py
───────────────────────────────────────────────────────────────────────────────
CampaignState data model for multi-episode persistence.

This module is a pure data model — it must NOT import from src.engine or
src.core.state. The CampaignOrchestrator (E32C) owns population and extraction.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from src.domains.campaigns.progression_plan import ProgressionPlan
from src.domains.campaigns.social_memory import FactionSocialMemory, SocialMemoryRecord
from src.domains.culture.model import CultureCarryForward


@dataclass(frozen=True)
class NemesisRelation:
    """Typed record of a recurring antagonistic relationship between two entities.

    Stored in CampaignState.nemesis_relations keyed by "{protagonist_id}:{antagonist_id}".
    Formed when the same antagonist appears in 2+ negative interaction history entries
    (kind "betrayed" or "conflict") from different episodes in the protagonist's
    SocialMemoryRecord. Injects a BlockerState into the protagonist's strategic.blockers
    at episode start, causing FORM_PARTY routes to be blocked when the antagonist is a
    candidate (see GriefUrgencyImporter and generator.py FORM_PARTY logic).
    """
    protagonist_id: int    # entity experiencing the nemesis relationship
    antagonist_id: int     # entity who is the nemesis
    formation_episode: int # episode when nemesis was formally recognized
    antagonism_count: int  # number of distinct episodes with negative interactions
    strength: float        # 0.0–1.0; min(1.0, antagonism_count * 0.4)

    def to_dict(self) -> dict:
        return {
            "protagonist_id": self.protagonist_id,
            "antagonist_id": self.antagonist_id,
            "formation_episode": self.formation_episode,
            "antagonism_count": self.antagonism_count,
            "strength": round(self.strength, 6),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "NemesisRelation":
        return cls(
            protagonist_id=d["protagonist_id"],
            antagonist_id=d["antagonist_id"],
            formation_episode=d["formation_episode"],
            antagonism_count=d["antagonism_count"],
            strength=d["strength"],
        )


@dataclass(frozen=True)
class GriefUrgencyModifier:
    """Timed urgency modifier injected at episode start for entities who lost allies.

    Stored in CampaignState.grief_urgencies (keyed by grieving entity_id).
    Decays by decay_per_episode each episode; removed when urgency ≤ 0.
    Injected as a ConcernState(kind=SOCIAL_THREAT) into entity.strategic.concerns
    by GriefUrgencyImporter at the start of each episode.
    """
    entity_id: int          # entity that is grieving
    dead_ally_id: int       # entity whose death caused the grief
    episode: int            # episode when grief was created
    urgency: float          # 0.0–1.0 current urgency strength
    decay_per_episode: float = 0.25  # subtracted each episode boundary

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "dead_ally_id": self.dead_ally_id,
            "episode": self.episode,
            "urgency": round(self.urgency, 6),
            "decay_per_episode": self.decay_per_episode,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GriefUrgencyModifier":
        return cls(
            entity_id=d["entity_id"],
            dead_ally_id=d["dead_ally_id"],
            episode=d["episode"],
            urgency=d["urgency"],
            decay_per_episode=d.get("decay_per_episode", 0.25),
        )


@dataclass(frozen=True)
class EntityCarryForward:
    """Immutable snapshot of one entity's carry-forward state between episodes.

    Field mapping notes (for E32C extraction):
      level       <- entity.identity.evolution_level (NOT .level)
      xp          <- entity.identity.evolution_points (NOT .xp)
      equipment   <- {"slots": {str(slot): item_id, ...},
                      "durability": {str(slot): float, ...}}
                     (keys are EquipSlot enum names as strings)
      reputation  <- entity.social.public_reputation (single float 0.0-2.0)
      alive       <- entity.lifecycle.active
    """
    entity_id: int
    level: int
    xp: int
    equipment: dict          # {"slots": {...}, "durability": {...}}
    reputation: float        # public_reputation — single score; E43 adds per-faction detail
    alive: bool              # False = dead; carried but not spawned in next episode

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "level": self.level,
            "xp": self.xp,
            "equipment": self.equipment,
            "reputation": self.reputation,
            "alive": self.alive,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EntityCarryForward":
        return cls(
            entity_id=d["entity_id"],
            level=d["level"],
            xp=d["xp"],
            equipment=d.get("equipment", {}),
            reputation=d["reputation"],
            alive=d["alive"],
        )


@dataclass(frozen=True)
class FactionCarryForward:
    """Immutable snapshot of one faction's carry-forward state between episodes.

    Field mapping notes (for E32C):
      faction_id  — string key; E32C maps from IdentityComponent.faction (int)
                    using str() conversion or a registry lookup. This module
                    stores only the string form. E32C owns the int->str mapping.
      alive       — E32C synthesizes: faction is alive if >=1 entity with this
                    faction int is active in the final AuthoritativeState.
      tension     — E32C synthesizes from world pressure or regional trauma data.
    """
    faction_id: str
    alive: bool              # False = destroyed; not spawned in next episode
    tension: float

    def to_dict(self) -> dict:
        return {
            "faction_id": self.faction_id,
            "alive": self.alive,
            "tension": self.tension,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FactionCarryForward":
        return cls(
            faction_id=d["faction_id"],
            alive=d["alive"],
            tension=d["tension"],
        )


@dataclass(frozen=True)
class EpisodeSummary:
    """Minimal stub for a completed episode record. E32C adds richer fields.

    episode_index   — 0-based index of the completed episode
    completed_tick  — final tick of the completed episode
    run_id          — the episode's underlying Kernel run_id, used by SimQ tooling
                      to locate that episode's simulation_events.jsonl. Empty
                      string for legacy records / episodes run without a Kernel.
    """
    episode_index: int
    completed_tick: int
    run_id: str = ""

    def to_dict(self) -> dict:
        return {
            "episode_index": self.episode_index,
            "completed_tick": self.completed_tick,
            "run_id": self.run_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EpisodeSummary":
        return cls(
            episode_index=d["episode_index"],
            completed_tick=d["completed_tick"],
            run_id=d.get("run_id", ""),
        )


@dataclass(frozen=True)
class WorldTimelineEntry:
    """Minimal stub for a world-level event in the campaign timeline.

    tick            — simulation tick at which the event occurred
    episode_index   — episode in which the event occurred
    description     — human-readable label (calamity name, world shift type, etc.)
    """
    tick: int
    episode_index: int
    description: str

    def to_dict(self) -> dict:
        return {
            "tick": self.tick,
            "episode_index": self.episode_index,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "WorldTimelineEntry":
        return cls(
            tick=d["tick"],
            episode_index=d["episode_index"],
            description=d["description"],
        )


@dataclass(frozen=True)
class NarrativeLedgerEntry:
    """Structured record of a significant cross-episode narrative event.

    Implemented by E32D (NarrativeLedger). Populated in
    CampaignOrchestrator._advance_state() from AuthoritativeState.recent_world_events.

    episode         — 0-based index of the episode in which the event occurred
    tick            — simulation tick at which the event was recorded
    event_type      — "quest_completed" | "entity_death" | "faction_shift" | "calamity"
    subject_id      — entity/faction/node id (empty string if unavailable)
    payload         — event-specific numeric data (may be empty dict)
    significance    — 0.0–1.0 relevance weight
                      (quest_completed=0.7, entity_death=0.5, faction_shift=0.9)
    entry_id        — deterministic dedup key; format: "{episode}:{tick}:{event_type}:{subject_id}"
                      defaults to "" for legacy records loaded from prior checkpoints
    """
    episode: int
    tick: int
    event_type: str       # "quest_completed" | "entity_death" | "faction_shift" | "calamity"
    subject_id: str       # entity/faction/node id (empty string if unavailable)
    payload: dict         # event-specific numeric data
    significance: float   # 0.0-1.0 relevance weight
    entry_id: str = ""    # deterministic dedup key (optional; empty for legacy records)

    def to_dict(self) -> dict:
        return {
            "episode": self.episode,
            "tick": self.tick,
            "event_type": self.event_type,
            "subject_id": self.subject_id,
            "payload": self.payload,
            "significance": self.significance,
            "entry_id": self.entry_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "NarrativeLedgerEntry":
        return cls(
            episode=d["episode"],
            tick=d["tick"],
            event_type=d["event_type"],
            subject_id=d.get("subject_id", ""),
            payload=d.get("payload", {}),
            significance=d.get("significance", 0.0),
            entry_id=d.get("entry_id", ""),
        )


@dataclass
class CampaignState:
    """Mutable durable container for multi-episode campaign progress.

    Owned by CampaignOrchestrator (E32C). Accumulates across episodes via
    episode_history.append(), persistent_entities update, etc.

    NOT frozen — mutation by CampaignOrchestrator is intentional.
    Sub-records are frozen (EntityCarryForward, FactionCarryForward, etc.).
    """
    campaign_id: str
    episode_index: int
    episode_history: List[EpisodeSummary] = field(default_factory=list)
    persistent_entities: Dict[int, EntityCarryForward] = field(default_factory=dict)
    persistent_factions: Dict[str, FactionCarryForward] = field(default_factory=dict)
    world_timeline: List[WorldTimelineEntry] = field(default_factory=list)
    narrative_ledger: List[NarrativeLedgerEntry] = field(default_factory=list)
    social_memories: Dict[int, SocialMemoryRecord] = field(default_factory=dict)
    # E43B: per-entity cross-episode social snapshots keyed by entity_id (int).
    # Populated by SocialMemoryExporter at episode end; consumed by
    # SocialMemoryImporter at episode start. Serialized with str(k) keys.
    faction_social_memories: Dict[str, FactionSocialMemory] = field(default_factory=dict)
    # E43D: collective faction-level hostility records keyed by faction_id (str).
    # Populated by FactionSocialMemoryExporter at episode end. Persists across
    # episodes regardless of whether individual faction members survive.
    progression_plans: Dict[int, ProgressionPlan] = field(default_factory=dict)
    # E61B: long-term build-goal plans keyed by entity_id (int).
    # Populated by ProgressionPlanExporter at episode end; consumed by
    # ProgressionPlanImporter at episode start. Serialized with str(k) keys.
    region_cultures: Dict[str, CultureCarryForward] = field(default_factory=dict)
    # E62A: per-region cultural axis snapshots keyed by region_id (str).
    # Populated by CultureDriftExporter at episode end; consumed by
    # CultureDriftImporter at episode start. Derived from ChronicleHierarchy.
    grief_urgencies: Dict[int, GriefUrgencyModifier] = field(default_factory=dict)
    # E43F: timed grief/rage urgency modifiers keyed by grieving entity_id (int).
    # Detected at episode end (entity_death + ally social memory check);
    # injected as SOCIAL_THREAT ConcernState at episode start via GriefUrgencyImporter.
    nemesis_relations: Dict[str, NemesisRelation] = field(default_factory=dict)
    # E43G: nemesis relation records keyed by "{protagonist_id}:{antagonist_id}".
    # Detected at episode end (2+ negative interaction episodes from SocialMemoryRecord);
    # protagonist receives a BlockerState(SOCIAL) at episode start blocking FORM_PARTY
    # routes when the antagonist is among candidates (via GriefUrgencyImporter).

    def to_dict(self) -> dict:
        """Serialize to a JSON-safe dict. All dict keys sorted for determinism."""
        return {
            "campaign_id": self.campaign_id,
            "episode_index": self.episode_index,
            "episode_history": [e.to_dict() for e in self.episode_history],
            "persistent_entities": {
                str(k): v.to_dict()
                for k, v in sorted(self.persistent_entities.items())
            },
            "persistent_factions": {
                k: v.to_dict()
                for k, v in sorted(self.persistent_factions.items())
            },
            "world_timeline": [e.to_dict() for e in self.world_timeline],
            "narrative_ledger": [e.to_dict() for e in self.narrative_ledger],
            "social_memories": {
                str(k): v.to_dict()
                for k, v in sorted(self.social_memories.items())
            },
            "faction_social_memories": {
                k: v.to_dict()
                for k, v in sorted(self.faction_social_memories.items())
            },
            "progression_plans": {
                str(k): v.to_dict()
                for k, v in sorted(self.progression_plans.items())
            },
            "region_cultures": {
                k: v.to_dict()
                for k, v in sorted(self.region_cultures.items())
            },
            "grief_urgencies": {
                str(k): v.to_dict()
                for k, v in sorted(self.grief_urgencies.items())
            },
            "nemesis_relations": {
                k: v.to_dict()
                for k, v in sorted(self.nemesis_relations.items())
            },
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CampaignState":
        """Reconstruct from a dict (e.g., from JSON checkpoint). Inverse of to_dict()."""
        return cls(
            campaign_id=d["campaign_id"],
            episode_index=d["episode_index"],
            episode_history=[
                EpisodeSummary.from_dict(e) for e in d.get("episode_history", [])
            ],
            persistent_entities={
                int(k): EntityCarryForward.from_dict(v)
                for k, v in d.get("persistent_entities", {}).items()
            },
            persistent_factions={
                k: FactionCarryForward.from_dict(v)
                for k, v in d.get("persistent_factions", {}).items()
            },
            world_timeline=[
                WorldTimelineEntry.from_dict(e) for e in d.get("world_timeline", [])
            ],
            narrative_ledger=[
                NarrativeLedgerEntry.from_dict(e) for e in d.get("narrative_ledger", [])
            ],
            social_memories={
                int(k): SocialMemoryRecord.from_dict(v)
                for k, v in d.get("social_memories", {}).items()
            },
            faction_social_memories={
                k: FactionSocialMemory.from_dict(v)
                for k, v in d.get("faction_social_memories", {}).items()
            },
            progression_plans={
                int(k): ProgressionPlan.from_dict(v)
                for k, v in d.get("progression_plans", {}).items()
            },
            region_cultures={
                k: CultureCarryForward.from_dict(v)
                for k, v in d.get("region_cultures", {}).items()
            },
            grief_urgencies={
                int(k): GriefUrgencyModifier.from_dict(v)
                for k, v in d.get("grief_urgencies", {}).items()
            },
            nemesis_relations={
                k: NemesisRelation.from_dict(v)
                for k, v in d.get("nemesis_relations", {}).items()
            },
        )
