---
ticket_id: TCK-20260619-E32B-CAMPAIGN-STATE
phase: plan
date: 2026-06-21
---

# Implementation Plan: CampaignState Data Model

## Overview

Create `src/domains/campaigns/state.py` as a pure data-model module (no engine imports)
containing all dataclasses needed for multi-episode campaign persistence. Then add unit
tests and an import smoke test. No existing file is modified except the ticket itself.

---

## Resolved Decisions (not open questions — final answers)

| # | Decision | Resolution |
|---|---|---|
| OQ-1 | Reputation field shape | `reputation: float` — maps to `public_reputation` (only value in SocialComponent). E43 can add per-faction dict later. |
| OQ-2 | Equipment serialization | Full composite form: `{"slots": {slot_str: item_id_or_None, ...}, "durability": {slot_str: float, ...}}`. Restoration-complete. |
| OQ-3 | FactionCarryForward source | `faction_id: str`. E32C owns int→str mapping from `IdentityComponent.faction`. Noted in `FactionCarryForward` docstring. |
| OQ-4 | EpisodeSummary / WorldTimelineEntry stub fields | `EpisodeSummary`: `episode_index: int`, `completed_tick: int`. `WorldTimelineEntry`: `tick: int`, `episode_index: int`, `description: str`. |
| — | NarrativeLedgerEntry | Minimal stub only: `entry_id: str`, `tick: int`, `episode_index: int`. E32D extends. |
| — | `CampaignState` mutability | Plain `@dataclass` (no `frozen=True`, no `slots=True`). Sub-records (`EntityCarryForward`, `FactionCarryForward`, `EpisodeSummary`, `WorldTimelineEntry`, `NarrativeLedgerEntry`) are `@dataclass(frozen=True)`. |
| — | Serialization pattern | `to_dict()` / `from_dict(cls, d)` classmethods on all types. `to_dict()` sorts all dict keys for determinism, consistent with `to_canonical_dict()` convention. |

---

## Dependency Map

```
Step 1 (state.py: stub types)
  └── Step 2 (state.py: CampaignState + serialization)
        └── Step 3 (tests: unit test file)
              └── Step 4 (tests: regression run)
                    └── Step 5 (ticket finalization)
```

Steps 1 and 2 are both in the same new file; they are split here for verifiability.
Steps 3 and 4 both read from Step 2's output.

---

## Step 1 — Create `src/domains/campaigns/state.py` with stub/sub-record types

**Files changed:**
- `src/domains/campaigns/state.py` (new — created)

**What to implement:**

Create the file with the module docstring, imports, and the five sub-record/stub
dataclasses: `EntityCarryForward`, `FactionCarryForward`, `EpisodeSummary`,
`WorldTimelineEntry`, `NarrativeLedgerEntry`. All five are `@dataclass(frozen=True)`.

```python
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


@dataclass(frozen=True)
class EntityCarryForward:
    """Immutable snapshot of one entity's carry-forward state between episodes.

    Field mapping notes (for E32C extraction):
      level       ← entity.identity.evolution_level (NOT .level)
      xp          ← entity.identity.evolution_points (NOT .xp)
      equipment   ← {"slots": {str(slot): item_id, ...},
                      "durability": {str(slot): float, ...}}
                     (keys are EquipSlot enum names as strings)
      reputation  ← entity.social.public_reputation (single float 0.0–2.0)
      alive       ← entity.lifecycle.active
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
                    stores only the string form. E32C owns the int→str mapping.
      alive       — E32C synthesizes: faction is alive if ≥1 entity with this
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
    """
    episode_index: int
    completed_tick: int

    def to_dict(self) -> dict:
        return {
            "episode_index": self.episode_index,
            "completed_tick": self.completed_tick,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EpisodeSummary":
        return cls(
            episode_index=d["episode_index"],
            completed_tick=d["completed_tick"],
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
    """Minimal stub for a significant cross-episode narrative event.

    E32D (NarrativeLedger) will extend this type with additional fields.
    Do not add narrative logic in E32B.

    entry_id        — unique string key for deduplication
    tick            — simulation tick at which the event was recorded
    episode_index   — episode in which the event was recorded
    """
    entry_id: str
    tick: int
    episode_index: int

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "tick": self.tick,
            "episode_index": self.episode_index,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "NarrativeLedgerEntry":
        return cls(
            entry_id=d["entry_id"],
            tick=d["tick"],
            episode_index=d["episode_index"],
        )
```

**Verification:** `python3 -c "from src.domains.campaigns.state import EntityCarryForward; print('OK')`

**Scope guards:**
- Do NOT import anything from `src.engine` or `src.core.state`.
- Do NOT use `slots=True` on any class here (avoids frozen+slots interaction).
- Do NOT add narrative logic or extraction logic (E32C/E32D scope).

---

## Step 2 — Add `CampaignState` with `to_dict()` / `from_dict()` to the same file

**Files changed:**
- `src/domains/campaigns/state.py` (append to file created in Step 1)

**What to implement:**

Append `CampaignState` (plain mutable `@dataclass`) after the frozen sub-records. Include
`to_dict()` / `from_dict()` that serialize the full nested structure. All dict keys in
`to_dict()` output must be sorted for determinism.

```python
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
        )
```

**Key serialization details:**
- `persistent_entities` keys are `int` in memory; serialized as `str` in JSON (JSON
  requires string keys). `from_dict` converts back with `int(k)`.
- `to_dict()` sorts `persistent_entities` and `persistent_factions` by key for determinism.
- No `EquipSlot` enum values appear in `state.py` — equipment is already `dict` in
  `EntityCarryForward`. The enum-to-string conversion is E32C's responsibility at
  extraction time.

**Verification:** `python3 -c "from src.domains.campaigns.state import CampaignState; print('OK')`

**Scope guards:**
- `CampaignState` must NOT have `frozen=True` or `slots=True`.
- No engine or pipeline imports.
- `to_dict()` must produce output that `json.dumps()` accepts without a custom encoder.

---

## Step 3 — Create `tests/unit/campaigns/test_campaign_state.py`

**Files changed:**
- `tests/unit/campaigns/test_campaign_state.py` (new)

**What to implement:**

All 10 tests from `test_plan.md` (AC-1 through AC-10) plus the AST import guard (Guard 4).
Tests are pure unit tests — no kernel, no AuthoritativeState, all state constructed from
literals.

Implement exactly:
- `test_campaign_state_constructs` (AC-1)
- `test_campaign_state_json_round_trip` (AC-2) — uses `reputation: float` per OQ-1
- `test_entity_carry_forward_fields` (AC-3)
- `test_entity_carry_forward_dead` (AC-4)
- `test_faction_carry_forward_destroyed` (AC-5)
- `test_entity_carry_forward_is_frozen` (AC-6)
- `test_faction_carry_forward_is_frozen` (AC-7)
- `test_campaign_state_is_mutable` (AC-8)
- `test_campaign_state_to_dict_is_json_safe` (AC-9)
- `test_campaign_state_importable` (AC-10)
- `test_campaign_state_module_has_no_engine_imports` (Guard 4)

**Import in test file:**
```python
from src.domains.campaigns.state import (
    CampaignState,
    EntityCarryForward,
    FactionCarryForward,
    EpisodeSummary,
    WorldTimelineEntry,
    NarrativeLedgerEntry,
)
```

**Scope guards:**
- No tests that populate `narrative_ledger` with real narrative data (E32D scope).
- No imports of `AuthoritativeState`, engine modules, or kernel.
- No tests for E32C extraction logic (that belongs in E32C's test file).

**Verification:** `pytest tests/unit/campaigns/test_campaign_state.py -x -v`

---

## Step 4 — Regression run: full campaign test surface

**Files changed:** none (read-only test run)

**Command:**
```bash
pytest tests/unit/campaigns/ tests/integration/campaigns/ \
       tests/perf/test_phase9_campaign_semantic_budget.py -x -v
```

**Expected:** all existing tests pass unchanged; new `test_campaign_state.py` tests also
pass. No existing file was modified, so pre-E32B tests must pass as-is.

**Scope guards:**
- If any existing test fails, investigate before proceeding — E32B must not silently break
  the existing campaign surface.

---

## Step 5 — Finalize ticket and update working log

**Files changed:**
- `tickets/inprogress/TCK-20260619-E32B-CAMPAIGN-STATE.md` → `tickets/done/TCK-20260619-E32B-CAMPAIGN-STATE.md`
- `tickets/working_log.csv` (append one row)
- `agent-monitoring/runs.jsonl` (append run entry)
- `agent-monitoring/events.jsonl` (append at least one event entry)

**What to do:**
1. Fill in ticket sections: `## Files Changed`, `## Completion Summary`, set status to `DONE`.
2. Move ticket file to `tickets/done/`.
3. Append working log row.
4. Write agent monitoring entries (run + event).
5. Stage `agent-monitoring/` (including `tools.jsonl`) in the commit.

**Scope guards:**
- Do NOT run `make knowledge-index-update` unless docs were modified (they were not).
- Do NOT run `graphify update` unless `src/` files were changed — they were (state.py),
  so run `graphify update .` after Step 2.
- Do NOT clean `data/runs/` unless populated during this ticket (no simulation runs in E32B).

---

## Deviations from Plan

None. Implementation followed the plan exactly:
- All 6 types created as specified in Steps 1 and 2.
- Test file created with 17 tests (plan listed 11 required; additional tests added for
  EpisodeSummary, WorldTimelineEntry, NarrativeLedgerEntry round-trips to improve coverage —
  these are additive, not contradictory).
- All resolved decisions (OQ-1 through OQ-4) applied as specified.
- No engine imports present; AST guard test confirms this.

---

## Acceptance Criteria → Step Mapping

| Acceptance Criterion | Verified In |
|---|---|
| `CampaignState(...)` constructs without error | Step 3, AC-1 |
| `CampaignState` serializes to JSON (round-trip) | Step 3, AC-2 |
| `EntityCarryForward` includes all carry-forward fields | Step 3, AC-3 |
| Dead entities (`alive=False`) representable | Step 3, AC-4 |
| Destroyed factions (`alive=False`) representable | Step 3, AC-5 |
| `EntityCarryForward` is immutable (frozen) | Step 3, AC-6 |
| `FactionCarryForward` is immutable (frozen) | Step 3, AC-7 |
| `CampaignState` is mutable (episode accumulation) | Step 3, AC-8 |
| `to_dict()` output is JSON-safe | Step 3, AC-9 |
| All types importable from `src.domains.campaigns.state` | Step 3, AC-10 |
| No engine imports in state.py | Step 3, Guard 4 |
| Existing campaign tests unbroken | Step 4, regression |

---

## Explicit Scope Guards (what NOT to touch)

- `src/core/state.py` — read-only reference in investigation. Do not modify.
- `src/domains/campaigns/schema.py` — existing types untouched.
- `src/domains/campaigns/runner.py` — renamed by E32A; no modification here.
- `src/engine/` — no imports, no modifications.
- `docs/parity_ledger/` — new parity entries deferred until E32C has a test path to cite.
- `docs/guidelines/v2_intentional_divergences.md` — no intentional behavior divergence in E32B.
- Any extraction logic (reading `AuthoritativeState`, inspecting `EquipmentComponent`, etc.) — E32C scope only.
- Any NarrativeLedger population logic — E32D scope only.
