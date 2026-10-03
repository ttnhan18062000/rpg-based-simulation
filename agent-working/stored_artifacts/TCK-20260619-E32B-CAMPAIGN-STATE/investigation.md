---
ticket_id: TCK-20260619-E32B-CAMPAIGN-STATE
phase: investigation
date: 2026-06-21
---

# Investigation: CampaignState Data Model

## Current Behavior (file:line refs)

### No CampaignState exists

Zero code for `CampaignState`, `EntityCarryForward`, `FactionCarryForward`,
`EpisodeSummary`, `WorldTimelineEntry`, or `NarrativeLedgerEntry` anywhere in `src/`.
Confirmed via grep — no partial implementations to reconcile.

### Existing campaign domain files

`src/domains/campaigns/` currently contains:

| File | Purpose |
|---|---|
| `schema.py` | `CampaignSpec`, `CampaignEvent`, `CampaignResult`, arc/scorecard dataclasses |
| `runner.py` | `SimulationAnalysisRunner` (renamed by E32A — analysis-only, amnesiac) |
| `spec.py` | `CampaignSpecLoader` — YAML → `CampaignSpec`; no multi-episode awareness |
| `classifier.py`, `behavior_change.py`, `diversity.py`, `scorecard.py`, `forbidden.py`, `reports.py` | Analysis tooling only |

**No `state.py` exists yet.** This ticket creates `src/domains/campaigns/state.py`.

### Authoritative entity state fields (carry-forward source)

The relevant fields that must be extracted into `EntityCarryForward` live in `EntityState`
(`src/core/state.py:L571`), composed from:

| Carry-forward field | Source component | Field name | Type |
|---|---|---|---|
| `level` | `IdentityComponent` (`state.py:L430`) | `evolution_level` | `int` |
| `xp` | `IdentityComponent` | `evolution_points` | `int` |
| `equipment` | `EquipmentComponent` (`state.py:L554`) | `slots: Dict[EquipSlot, str|None]`, `durability: Dict[EquipSlot, float]` | composed |
| `reputation` | `SocialComponent` (`src/core/models/social.py:L23`) | `public_reputation: float` | `float` |
| `alive` | `LifecycleComponent` (`state.py:L144`) | `active: bool` | `bool` |

**Key finding — field name mismatch:** The ticket scope says `level: int` and `xp: int`
but the live fields are `evolution_level` and `evolution_points` on `IdentityComponent`.
The `EntityCarryForward` fields `level` and `xp` are fine as carry-forward names (they
are a projection, not a direct copy of the component), but the extraction code in E32C
must read `entity.identity.evolution_level` and `entity.identity.evolution_points`.

**Key finding — reputation shape mismatch:** The ticket scope says
`reputation: dict  # faction_id → rep score`. The actual `SocialComponent` has
`public_reputation: float` (a single unified score, 0.0–2.0), not a per-faction dict.
There is no per-faction reputation dict in `SocialComponent`. Options:
1. Use `public_reputation: float` (single value, rename carry-forward field).
2. Synthesize a per-faction dict from `trust_history: Dict[int, float]` (entity-level
   trust, not faction-level reputation).
3. Leave `reputation: dict` as `{}` for now and note it as a stub for E43 (Social Memory).

This is an open question requiring a decision before implementation (see below).

**Key finding — equipment serialization:** `EquipmentComponent.slots` keys are
`EquipSlot` enum values. For JSON serialization `str(slot)` is needed. The `item_id`
values are `str | None`. Durability lives in `EquipmentComponent.durability`. The
carry-forward `equipment: dict` must capture both slots and durability to be
restoration-complete.

**Key finding — no FactionState in AuthoritativeState:** `AuthoritativeState`
(`state.py:L985`) has no `factions: Dict[str, FactionState]` field. Faction state is
only represented as `owner_faction_id: Optional[int]` on `RegionState` (`state.py:L207`)
and `faction: int` on `IdentityComponent`. There is no `FactionCarryForward` source
to read `alive: bool` or `tension: float` from — these fields do not yet exist in the
live engine. The `FactionCarryForward` model can be defined now (for E32C to populate),
but E32C must synthesize faction state by inspecting entity affiliations, not by reading
a nonexistent FactionState object.

### Existing schema pattern (reference: `schema.py`)

All existing dataclasses in `schema.py` use `@dataclass(frozen=True, slots=True)` with
`from __future__ import annotations`. The ticket specifies `CampaignState` as a plain
`@dataclass` (mutable) and sub-records as `@dataclass(frozen=True)`. This is intentional:
`CampaignState` is a durable mutable container accumulated across episodes; the sub-records
it holds are immutable snapshots per entity/faction.

### JSON serialization requirement

`CampaignState` must serialize/deserialize to JSON (ticket AC). `@dataclass` objects are
not JSON-serializable by default. Two viable patterns used in this codebase:
1. `to_canonical_dict()` method (pattern used by `EntityState`, `AuthoritativeState`).
2. `dataclasses.asdict()` + `json.dumps()` with a custom encoder for non-primitive types
   (enums, sets, tuples).

**Recommended approach:** implement `to_dict()` / `from_dict()` classmethods on
`CampaignState` and frozen sub-records. `EquipmentComponent` slots use `EquipSlot` enum
keys — must be stringified in `to_dict()`.

---

## Mechanics / Engine Constraints

**Immutability Law** (`docs/core/state.md`): `AuthoritativeState` and all its components
are `frozen=True`. `CampaignState` is NOT part of `AuthoritativeState` — it is a
separate durable record that the `CampaignOrchestrator` (E32C) owns outside the tick
loop. This means `CampaignState` can be mutable (plain `@dataclass`), which is correct
per the ticket scope. Sub-records (`EntityCarryForward`, `FactionCarryForward`) should
remain frozen.

**Frozen Lifecycle Law:** State transitions in the kernel produce new `AuthoritativeState`
objects. The extraction of carry-forward data must happen post-episode (after the kernel
has finalized the last tick's `AuthoritativeState`), reading the final immutable snapshot.
No mutation of `AuthoritativeState` is involved.

**Canonical serialization:** `to_canonical_dict()` in this codebase sorts all dict keys
for determinism. The `to_dict()` method on `CampaignState` should follow the same
convention for checkpoint reproducibility.

**No durable state in reason strings:** Per architecture rules, `NarrativeLedgerEntry`
fields (to be added in E32D) must be typed fields — not free-form `reason` strings or
`metadata` dicts.

---

## Parity Ledger Overlap (IDs + status)

### `docs/parity_ledger/substrate.yaml`

No existing entry covers campaign-episode persistence or cross-episode state carry-forward.
The `SUB-0xx` series covers world generation determinism, authoritative world objects, and
entity snapshot immutability — none of which directly addresses multi-episode persistence.

**New entry required** after E32B lands: an entry tracking that `CampaignState`
serializes/deserializes deterministically (round-trip identity under same seed).

### `docs/parity_ledger/social_narrative.yaml`

No entry covers `NarrativeLedger` or campaign-level narrative records. The social entries
cover `public_reputation`, narrative memory, and social appraisal within a single episode.

**New entry required** when E32D (NarrativeLedger) lands: entry tracking that
`NarrativeLedger` records significant cross-episode events.

### No existing parity entries require updating for E32B alone.

E32B introduces new types only — it does not change any existing behavior. Parity ledger
additions (not updates) will be needed; however these entries are best added once E32C
(which populates the model) is complete and has a test path to cite.

---

## Prior Work

### TCK-20260619-E32A-RENAME-RUNNER (DONE)

- Renamed `CampaignRunner` → `SimulationAnalysisRunner` in `runner.py` and all callers.
- Freed the `campaign` namespace.
- 6 tests pass. No behavior change.
- Files changed: `runner.py`, 3 test files, 1 doc.

### TCK-20260619-E32-CAMPAIGN-RUNTIME (DONE — epic scoped)

- Epic scoping investigation in `staging_artifacts/TCK-20260619-E32-CAMPAIGN-RUNTIME/investigation.md`.
- Confirmed: zero code for `CampaignState`. E32A complete. E32B → E32C → E32D → E32E
  strictly sequential.
- The gap table from the epic investigation estimated ~50 lines for `CampaignState`.

### TCK-20260619-E31-SCENARIO-RUNTIME (DONE — prerequisite)

- `ScenarioRuntimeService` exists in `src/engine/scenario_runtime.py:L96`.
- E32C will use `ScenarioRuntimeService` to run each episode.
- E32B does not depend on `ScenarioRuntimeService` directly.

### No stored artifacts for E32B specifically — this is the first child standard ticket.

---

## Risks and Open Questions

### OQ-1 (DECISION REQUIRED): Reputation field shape

The ticket specifies `reputation: dict  # faction_id → rep score` on
`EntityCarryForward`. No per-faction reputation dict exists in `SocialComponent`. The
closest field is `public_reputation: float` (a single unified 0.0–2.0 score).

Three options:
- **A (Recommended):** Use `reputation: float` (rename to match actual data). Simple,
  honest about what exists now. E43 (Social Memory) can add per-faction detail later.
- **B:** Use `reputation: dict[str, float]` but populate it as
  `{"public": entity.social.public_reputation}` now, leaving room for faction keys later.
- **C:** Use `trust_history: Dict[int, float]` (entity-level trust scores, not
  faction-level). Semantically wrong for the stated purpose.

Option A is safest for now. Option B provides forward-compatibility at the cost of a
semi-empty dict that E43 will fill. A decision is needed before E32C is implemented.

### OQ-2 (DECISION REQUIRED): Equipment serialization format

`EquipmentComponent.slots: Dict[EquipSlot, str|None]` and
`EquipmentComponent.durability: Dict[EquipSlot, float]`.

The `equipment: dict` field on `EntityCarryForward` needs a defined shape for JSON:
- `{"HEAD": "iron_helm", "MAIN_HAND": "sword_iron", ...}` (slots only, no durability)
- `{"slots": {"HEAD": "iron_helm", ...}, "durability": {"HEAD": 0.85, ...}}` (full)

The full form is required for restoration fidelity (durability is a meaningful gameplay
state). Recommend the composite form.

### OQ-3 (DECISION REQUIRED): FactionCarryForward source

`FactionCarryForward` fields `alive` and `tension` have no live source in
`AuthoritativeState`. E32C must synthesize these from entity affiliations (e.g., a
faction is `alive=False` if zero entities with that `faction` int value are `active`).
The faction namespace in the engine is `int` (on `IdentityComponent.faction`) not `str`
(the ticket uses `faction_id: str`). This mismatch must be resolved before E32C.

Recommendation: define `faction_id: str` as a string key (using str conversion of the
int or a registry lookup), document this in E32C's plan, and note the gap in
`FactionCarryForward` docstring.

### OQ-4: EpisodeSummary and WorldTimelineEntry — stub or full?

The ticket scope includes `episode_history: list[EpisodeSummary]` and
`world_timeline: list[WorldTimelineEntry]` but does not define these types' fields. They
are referenced by E32C (which populates them) and E32D (which adds narrative entries).

For E32B: these types should be defined as minimal stubs with at minimum `episode_index`
and `completed_tick` fields, enough for E32C to populate without guessing. Richer fields
can be added in E32C/E32D.

### Anti-Drift Hazard: `slots=True` incompatibility with `list` accumulation

`CampaignState` is specified as a plain (mutable) `@dataclass`. If `slots=True` is added
for consistency with other codebase patterns, `list.append()` mutations would fail
(frozen+slots). The mutable `CampaignState` must NOT use `slots=True` unless all
mutations go through `replace()`. Verify this in implementation.

---

## Anti-Drift Hazards

1. **`frozen=True` on sub-records, NOT on `CampaignState`:** `EntityCarryForward` and
   `FactionCarryForward` must be frozen (they are per-episode immutable snapshots). The
   outer `CampaignState` must NOT be frozen (it accumulates across episodes via
   `episode_history.append()` etc. in E32C).

2. **No mutation of `AuthoritativeState`:** Extraction of carry-forward data must be a
   pure read from the final tick's `AuthoritativeState`. E32B defines the target types;
   E32C implements the extraction. E32B must not introduce any apply-path imports or
   mutation logic.

3. **JSON round-trip must be deterministic:** `to_dict()` must sort all dict keys.
   `from_dict()` must reconstruct frozen sub-records exactly. Test round-trip identity.

4. **`NarrativeLedgerEntry` is E32D scope:** E32B should define the field
   `narrative_ledger: list[NarrativeLedgerEntry]` with a minimal stub
   `NarrativeLedgerEntry` type (enough to type-check), and annotate it clearly as
   expanded in E32D. Do not implement NarrativeLedger logic in E32B.

5. **`evolution_level` ≠ `level`:** The carry-forward field is named `level` (E32B's
   choice) but the source is `entity.identity.evolution_level`. E32C's extraction code
   must use the correct source path.
