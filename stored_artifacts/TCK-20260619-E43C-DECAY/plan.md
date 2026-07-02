# Plan — TCK-20260619-E43C-DECAY

## Goal
Add `SocialMemoryDecay` to `social_memory.py` and wire it into `SocialMemoryImporter.apply()`.

## Steps

### 1. Add `SocialMemoryDecay` class to `social_memory.py`
Insert after the `SocialMemoryRecord` class and before `SocialMemoryExporter`.

```python
class SocialMemoryDecay:
    """Applies per-episode score decay toward neutral for cross-episode social memory.

    Grudges (negative scores) decay slower than friendships (positive scores),
    reflecting that betrayal is harder to forget than cooperation.

    Constants
    ---------
    FRIENDSHIP_DECAY : float
        Fraction lost per episode for positive relationship scores.
        0.40 → 40% loss per episode (half-life ≈ 3 episodes).
    GRUDGE_DECAY : float
        Fraction lost per episode for negative relationship scores.
        0.10 → 10% loss per episode (half-life ≈ 7 episodes).
    """

    FRIENDSHIP_DECAY: float = 0.40
    GRUDGE_DECAY: float = 0.10

    @staticmethod
    def apply_decay(record: SocialMemoryRecord) -> SocialMemoryRecord:
        """Return a new SocialMemoryRecord with all scores decayed one episode.

        Positive scores (friendships) decay by FRIENDSHIP_DECAY.
        Negative scores (grudges) decay by GRUDGE_DECAY.
        Faction reputation always decays by FRIENDSHIP_DECAY (neutral drift).

        Parameters
        ----------
        record : SocialMemoryRecord
            The record to decay. Not mutated.

        Returns
        -------
        SocialMemoryRecord
            New frozen record with decayed scores, rounded to 4 decimal places.
        """
        new_scores: Dict[int, float] = {}
        for entity_id, score in record.relationship_scores.items():
            decay_rate = (
                SocialMemoryDecay.GRUDGE_DECAY if score < 0
                else SocialMemoryDecay.FRIENDSHIP_DECAY
            )
            new_scores[entity_id] = round(score * (1.0 - decay_rate), 4)

        new_faction_rep: Dict[str, float] = {
            fid: round(score * (1.0 - SocialMemoryDecay.FRIENDSHIP_DECAY), 4)
            for fid, score in record.faction_reputation.items()
        }

        return dc_replace(record, relationship_scores=new_scores, faction_reputation=new_faction_rep)
```

### 2. Wire decay into `SocialMemoryImporter.apply()`
At the start of `apply()`, call `SocialMemoryDecay.apply_decay(record)` and use
the decayed record for all subsequent merge logic.

### 3. Add unit tests
Append to `tests/unit/social/test_social_memory.py`:
- 8 new test functions covering decay rates, AC values, importer integration,
  edge cases (zero scores, empty dicts, immutability).

### 4. Add parity ledger entry
Append `SOC-CROSS-EP-003` to `docs/parity_ledger/social_narrative.yaml`.

## Architecture Review
- No randomness → deterministic.
- `dc_replace` already imported as alias for `dataclasses.replace`.
- Returns new frozen record → no mutation.
- No API exposure → no raw domain model risk.
- Decay wired inside importer → transparent to `CampaignOrchestrator` callers.
