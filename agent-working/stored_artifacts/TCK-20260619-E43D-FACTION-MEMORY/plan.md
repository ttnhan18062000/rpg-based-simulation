# Implementation Plan — TCK-20260619-E43D-FACTION-MEMORY

## Phase 1 — Add FactionSocialMemory to social_memory.py

Add after `SocialMemoryDecay`:

```python
@dataclass(frozen=True)
class FactionSocialMemory:
    """Collective faction-level hostility record — persists across episodes
    regardless of whether individual faction members survive.

    entity_hostility  : entity_id → hostility score (0.0–1.0)
    episode_of_offense: entity_id → episode index of the triggering offense
    """
    faction_id: str
    entity_hostility: Dict[int, float] = field(default_factory=dict)
    episode_of_offense: Dict[int, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "faction_id": self.faction_id,
            "entity_hostility": {str(k): v for k, v in sorted(self.entity_hostility.items())},
            "episode_of_offense": {str(k): v for k, v in sorted(self.episode_of_offense.items())},
        }

    @classmethod
    def from_dict(cls, d: dict) -> "FactionSocialMemory":
        return cls(
            faction_id=d["faction_id"],
            entity_hostility={int(k): v for k, v in d.get("entity_hostility", {}).items()},
            episode_of_offense={int(k): v for k, v in d.get("episode_of_offense", {}).items()},
        )

    def with_offense(self, entity_id: int, hostility: float, episode: int) -> "FactionSocialMemory":
        """Return new record with entity offense added/updated (max hostility)."""
        new_hostility = dict(self.entity_hostility)
        existing = new_hostility.get(entity_id, 0.0)
        new_hostility[entity_id] = max(existing, hostility)
        new_episode = dict(self.episode_of_offense)
        new_episode.setdefault(entity_id, episode)
        return FactionSocialMemory(
            faction_id=self.faction_id,
            entity_hostility=new_hostility,
            episode_of_offense=new_episode,
        )
```

Add `FactionSocialMemoryExporter`:

```python
class FactionSocialMemoryExporter:
    """Builds FactionSocialMemory records from a list of social event dicts.

    Each event dict is expected to have:
      kind      : str — "betrayal" | "attack" | etc.
      faction_id: str — the offended faction
      entity_id : int — the offending entity
      magnitude : float — offense strength (0.0–1.0)
      episode   : int — episode index

    Only "betrayal" and "attack" kinds are treated as offenses.
    """

    OFFENSE_KINDS = frozenset({"betrayal", "attack"})

    @staticmethod
    def build_from_events(
        events: List[dict],
        existing: Optional[Dict[str, "FactionSocialMemory"]] = None,
    ) -> Dict[str, "FactionSocialMemory"]:
        result: Dict[str, FactionSocialMemory] = dict(existing or {})
        for event in events:
            kind = event.get("kind", "")
            if kind not in FactionSocialMemoryExporter.OFFENSE_KINDS:
                continue
            faction_id = event.get("faction_id")
            entity_id = event.get("entity_id")
            magnitude = float(event.get("magnitude", 1.0))
            episode = int(event.get("episode", 0))
            if faction_id is None or entity_id is None:
                continue
            record = result.get(faction_id, FactionSocialMemory(faction_id=faction_id))
            result[faction_id] = record.with_offense(entity_id, magnitude, episode)
        return result
```

## Phase 2 — Add faction_social_memories to CampaignState

In `state.py`:
- Import `FactionSocialMemory`
- Add field: `faction_social_memories: Dict[str, FactionSocialMemory] = field(default_factory=dict)`
- Extend `to_dict()` to include the field (str keys sorted)
- Extend `from_dict()` to reconstruct it

## Phase 3 — Tests

Add to `tests/unit/social/test_social_memory.py`:
- All tests from test_plan.md
- AC test: `test_faction_hostility_persists_after_key_member_death`

## Phase 4 — Parity ledger

Add `SOC-CROSS-EP-004` to `docs/parity_ledger/social_narrative.yaml`.

## Architecture gate checks

- All state via typed frozen records — YES (FactionSocialMemory is frozen)
- Determinism — YES (sorted dict keys, no randomness)
- No raw domain models from API — YES (no API surface changed)
- Durable state has typed model, stable location, serialization, tests — YES
