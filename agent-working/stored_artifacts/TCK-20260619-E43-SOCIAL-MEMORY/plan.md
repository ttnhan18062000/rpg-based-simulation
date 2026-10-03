# Plan — TCK-20260619-E43-SOCIAL-MEMORY

## Approach

Add `SocialMemoryRecord` as a durable cross-episode model. Add exporter/importer hooks into `CampaignOrchestrator._advance_state()`. Implement decay and faction memory. Add consequence events.

## Sequence

**E43A → E43B → E43C/E43D parallel → E43E** (C and D can run in parallel after B)

---

## E43A · SocialMemoryRecord Model

New file `src/domains/campaigns/social_memory.py`:

```python
@dataclass(frozen=True, slots=True)
class InteractionRecord:
    episode: int
    tick: int
    kind: str   # "helped", "betrayed", "traded", "fought_alongside", "conflict"
    other_entity_id: Optional[int]
    faction_id: Optional[str]
    magnitude: float  # 0.0–1.0

@dataclass(frozen=True, slots=True)
class SocialMemoryRecord:
    entity_id: int
    interaction_history: Tuple[InteractionRecord, ...] = ()
    relationship_scores: Dict[int, float] = field(default_factory=dict)   # entity_id → score
    faction_reputation: Dict[str, float] = field(default_factory=dict)    # faction_id → score
    last_betrayal_tick: Optional[int] = None
    last_cooperation_tick: Optional[int] = None
```

---

## E43B · SocialMemoryExporter + Importer

```python
class SocialMemoryExporter:
    @staticmethod
    def export(entity: EntityState, episode: int) -> SocialMemoryRecord:
        """Serialize entity's social state at episode end."""
        ...

class SocialMemoryImporter:
    @staticmethod
    def apply(entity: EntityState, record: SocialMemoryRecord) -> EntityUpdate:
        """Apply legacy reputation deltas to entity's initial state in new episode."""
        # Decay first, then apply
        decayed = SocialMemoryDecay.apply_decay(record)
        return EntityUpdate(entity_id=entity.id, faction_reputation_delta=decayed.faction_reputation, ...)
```

Hook both into `CampaignOrchestrator._advance_state()` (from E32C) as callbacks:
- `SocialMemoryExporter.export()` called for each alive entity at episode end
- `SocialMemoryImporter.apply()` called at episode N+1 start before first tick

---

## E43C · Relationship Decay Mechanics

```python
class SocialMemoryDecay:
    FRIENDSHIP_DECAY = 0.40    # 40% loss per episode (half-life ~3 episodes)
    GRUDGE_DECAY = 0.10        # 10% loss per episode (half-life ~7 episodes)
    BETRAYAL_GRUDGE_WEIGHT = 5.0

    @staticmethod
    def apply_decay(record: SocialMemoryRecord) -> SocialMemoryRecord:
        new_scores = {}
        for entity_id, score in record.relationship_scores.items():
            decay = SocialMemoryDecay.GRUDGE_DECAY if score < 0 else SocialMemoryDecay.FRIENDSHIP_DECAY
            new_scores[entity_id] = score * (1.0 - decay)
        return replace(record, relationship_scores=new_scores)
```

---

## E43D · Faction Memory

```python
@dataclass(frozen=True, slots=True)
class FactionSocialMemory:
    faction_id: str
    entity_hostility: Dict[int, float] = field(default_factory=dict)  # entity_id → hostility
    episode_of_offense: Dict[int, int] = field(default_factory=dict)  # entity_id → episode#
```

Register `faction_social_memories: Dict[str, FactionSocialMemory]` in `CampaignState`. Populated by `SocialMemoryExporter`. Persists collective hostility even after individual members die.

---

## E43E · Consequence Events

Add to `src/observability/events.py`:
- `LEGENDARY_ARRIVAL` — entity with reputation ≥ 0.9 in this faction enters faction territory
- `KNOWN_TRAITOR_SPOTTED` — entity with past betrayal against this faction encountered
- `OLD_DEBT_COLLECTED` — entity fulfills past obligation from prior episode

Trigger conditions: check `SocialMemoryRecord.faction_reputation` + `FactionSocialMemory.entity_hostility` at entity-encounter evaluation time (in the social phase of the 6-phase kernel).

After E43E: create `docs/simulation/domains/social_memory_contract.md`. Update `docs/simulation/domains/social_systems_contract.md`. Update `docs/parity_ledger/social_narrative.yaml`. Run `make knowledge-index-update`.
