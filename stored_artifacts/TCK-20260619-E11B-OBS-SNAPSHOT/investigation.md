---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260619-E11B-OBS-SNAPSHOT
artifact_type: investigation
tags: [entity-differentiation, observability, personality, class-system, phase-1]
---

# Investigation — TCK-20260619-E11B-OBS-SNAPSHOT

## Current Behavior — LIGHT Mode Snapshot Structure

The LIGHT mode per-entity snapshot is implemented as `EntityInspectionSnapshot` (Pydantic
`BaseModel`) in `src/observability/live/entity_inspector.py` (L8–L24).

### Current fields (all fields, exact names and types):

| Field | Type | Value source |
|---|---|---|
| `entity_id` | `int` | constructor arg |
| `exists` | `bool` | constructor arg |
| `alive` | `bool = False` | `entity.combat.alive` |
| `position` | `Optional[tuple[float, float]]` | `entity.navigation.position` |
| `faction_id` | `Optional[int]` | `entity.identity.faction` |
| `region_id` | `Optional[str]` | `entity.navigation.region_id` |
| `current_goal` | `Optional[str]` | `entity.strategic.current_objective_id` |
| `current_target` | `Optional[str]` | `str(entity.navigation.target)` |
| `current_action` | `Optional[str]` | `entity.task.work_kind` |
| `combat_summary` | `Dict[str, Any]` | `{hp, max_hp, tactical_role}` |
| `inventory_summary` | `Dict[str, Any]` | `{gold, item_count, max_slots}` |
| `quest_summary` | `List[Dict[str, Any]]` | `entity.strategic.projects` (QuestState) |
| `strategic_summary` | `Dict[str, Any]` | `{current_project_id, blockers_count, …, boredom}` |
| `recent_timeline_events` | `List[Dict[str, Any]]` | `EntityTimelineStore.get_entity_timeline()` |
| `latest_rejection_reason` | `Optional[str]` | `entity.identity.latest_intent_results` / `navigation.last_failure_reason` |
| `latest_anomaly_flags` | `List[str]` | Computed: `HIGH_OSCILLATION`, `HIGH_WAIT_COUNT`, `HIGH_BOREDOM` |

**Missing fields (this ticket's target):** `role`, `class_id`, `personality` are absent from
`EntityInspectionSnapshot` entirely. `faction_id` is present (maps `entity.identity.faction`)
but `role` and `class_id` are not surfaced despite being in `IdentityComponent`.

`personality` as a separate `PersonalityComponent` on `entity.identity.personality` is
completely invisible in the current snapshot.

**LIGHT mode configuration** (`src/observability/config.py` L50–66):
`OBS_ENTITY_TIMELINE=True` — the timeline store is enabled. Default mode resolves to LIGHT
if no env override is set (config.py L298). `OBS_ENTITY_TIMELINE` is what gates
`EntityTimelineStore` use in the Kernel.

---

## Snapshot Serialization Path

**The only snapshot serialization site is `EntityInspector.inspect_entity()`** in
`src/observability/live/entity_inspector.py` (L30–135). It is a `@staticmethod` that:

1. Resolves the entity from `manager.latest_state.entities.get(entity_id)` (L42–44)
2. Builds dicts for each summary section (L46–116)
3. Constructs and returns `EntityInspectionSnapshot(...)` in one call (L118–135)

There is no intermediate serialization layer, no separate schema/presenter, and no
file-based snapshot path — the inspector builds the Pydantic model directly.

**Add-field pattern** (confirmed from existing fields): new scalar fields are added to
`EntityInspectionSnapshot` as class attributes with defaults, then populated by adding
the corresponding assignment in `inspect_entity()`'s constructor call (L118–135).

**Access path for the new fields:**
- `role` → `entity.identity.role` (int, `src/core/state.py` L429)
- `class_id` → `entity.identity.class_id` (str, `src/core/state.py` L438)
- `personality` → `entity.identity.personality` (PersonalityComponent, `src/core/state.py` L443)
  - Serialized via `.to_canonical_dict()` → `{greed, bravery, sociability, industry}` (state.py L381–391)
  - Or can be built inline as `dict(greed=…, bravery=…, sociability=…, industry=…)`

**`entity.personality` does NOT exist** — the correct path is `entity.identity.personality`.
(The ticket's "Implementation Notes" says `entity.personality` but the dataclass layout
in state.py L443 places it inside `IdentityComponent`, not at top-level EntityState.)

---

## PersonalityComponent Fields

**Source:** `src/core/state.py` L372–391

```python
@dataclass(frozen=True, slots=True)
class PersonalityComponent:
    greed: float = 0.0        # Biases loot/harvest
    bravery: float = 0.0      # Biases combat vs flee
    sociability: float = 0.0  # Biases social goals
    industry: float = 0.0     # Biases work/harvest goals
```

All four are `float` with default `0.0`. The component is `frozen=True` (immutable).

`to_canonical_dict()` returns: `{"greed": float, "bravery": float, "sociability": float, "industry": float}`.

`IdentityComponent` (state.py L443) holds `personality: PersonalityComponent = field(default_factory=PersonalityComponent)`.
`IdentityComponent.to_canonical_dict()` (L450–468) already includes
`"personality": self.personality.to_canonical_dict()` — so canonical serialization is
already defined and tested elsewhere.

**Access in EntityInspector:**
```python
personality = {
    "greed": entity.identity.personality.greed,
    "bravery": entity.identity.personality.bravery,
    "sociability": entity.identity.personality.sociability,
    "industry": entity.identity.personality.industry,
}
# or equivalently:
personality = entity.identity.personality.to_canonical_dict()
```

---

## Mechanics / Engine Constraints

- `PersonalityComponent` is part of `IdentityComponent` which is `frozen=True, slots=True`.
  Reading it is safe from any thread — no mutation can occur after world compilation.
- `EntityState` is frozen and has a `to_readonly()` method (state.py L697–L780). The
  inspector already reads from `manager.latest_state` which is the completed tick state.
  No locking is required for reading personality fields.
- `ObservabilityConfig.get_mode()` defaults to `LIGHT`. `OBS_ENTITY_TIMELINE=True` in LIGHT
  ensures the inspector is reachable; personality fields do not depend on timeline at all —
  they come directly from the entity state.
- Adding fields to `EntityInspectionSnapshot` is **additive** (Pydantic model with
  `Optional`/`Dict` defaults). Existing callers that deserialize from the snapshot are
  forward-compatible as long as new fields have defaults. Use `Optional[str] = None`
  for scalars and `Dict[str, Any] = Field(default_factory=dict)` for the personality dict.
- **No mechanics formula is involved** — personality is a static vector seeded at world
  compile (done by TCK-20260619-P0-ENTITY-INIT). No tick-level mutation occurs.

---

## Parity Ledger Overlap

Searched `docs/parity_ledger/infrastructure.yaml` for `EntityInspectionSnapshot`,
`entity_inspector`, `personality`, `class_id`, `live.*snapshot`, `faction_id`.
**Result: zero matching entries.**

The prior ticket TCK-20260520-SIM-OBS-PHASE5-M22 that implemented `EntityInspectionSnapshot`
did not create a parity ledger entry for it. The current snapshot field set is therefore
**untracked in the parity ledger**.

**Required action for this ticket:**
- Add a new `INFRA-205` entry (next sequential after INFRA-204 at line 2307) to
  `docs/parity_ledger/infrastructure.yaml` capturing the LIGHT-mode snapshot field contract,
  including the three new fields: `role`, `class_id`, `personality`.
- Status: `verified`, priority: `P1`.
- Test path: the new test `tests/unit/observability/test_personality_snapshot.py::test_light_snapshot_includes_personality`.

No existing parity entries need status changes — there are none to update.

---

## Prior Work

| Ticket | Relevance |
|---|---|
| TCK-20260520-SIM-OBS-PHASE5-M22 | Implemented `EntityInspectionSnapshot` and `EntityInspector`. Defined the M22 field set. Did not include `role`, `class_id`, or `personality`. |
| TCK-20260619-P0-ENTITY-INIT | **Prerequisite (done).** Seeds `PersonalityComponent` on every entity at world compile; assigns `class_id` by role. This ticket depends on that seeding being in place. |
| TCK-20260618-AUDIT-D15 | Produced `docs/audits/D15_entity_decision_inspection.md`. Gap 6 (LIGHT mode cognition limitation) is a related but different problem. This ticket addresses a different gap: personality data absent from live snapshot. |
| TCK-20260619-E11-ENTITY-IDENTITY | Parent epic scoping this work. |

---

## Risks and Open Questions

### Risk 1 — Ticket's entity access path is incorrect
The ticket's "Implementation Notes" says `entity.personality`, but the actual path is
`entity.identity.personality`. If implementation follows the ticket literally, it will
raise `AttributeError`. **Mitigation:** use `entity.identity.personality` as confirmed
from `src/core/state.py` L443.

### Risk 2 — PersonalityComponent all-zeros if seeding not verified
If TCK-20260619-P0-ENTITY-INIT did not run or its seeding does not cover the entities
used in the new test, personality will be all `0.0`. The test must verify fields are
**present and non-None** (per AC), not that they are non-zero. Verifying non-None is
trivially satisfied since `float` can't be `None`. The real test should assert the dict
has the four expected keys (`greed`, `bravery`, `sociability`, `industry`) and all values
are `float`.

### Risk 3 — `role` is an `int` (enum value), not a string label
`IdentityComponent.role` is `int = 0` (state.py L429). The snapshot will expose an int.
If the consumer expects a string like `"HERO"`, a secondary lookup is needed. The ticket
scope says "from `entity.identity.role`" — surface as `int` matching the existing
`faction_id: Optional[int]` pattern. No enum resolution needed.

### Open Question 1 — Should `personality` be a nested dict or top-level fields?
The AC says "dict of `{greed, bravery, sociability, industry}`". Using a
`Dict[str, Any] = Field(default_factory=dict)` with key `"personality"` is consistent
with `combat_summary`, `inventory_summary`, `strategic_summary`. Confirm before
implementation.

### Open Question 2 — Does `IdentityComponent.to_canonical_dict()` need updating?
It already includes `"personality"` (state.py L464). No change needed there.

---

## Anti-Drift Hazards

1. **`entity.personality` typo in ticket** — must not be copied verbatim; always use
   `entity.identity.personality`.
2. **New fields with no defaults** — if fields are added to `EntityInspectionSnapshot`
   without defaults, all existing call sites constructing the snapshot with
   `exists=False` (three sites in entity_inspector.py L33, L40, L44) will break.
   All new fields must have `Optional`/default values.
3. **Parity ledger drift** — since no INFRA entry exists for the snapshot field contract,
   any future change to snapshot fields will have no documented baseline. Adding INFRA-205
   in this ticket closes that gap.
4. **Test using wrong personality path** — test must use `entity.identity.personality`,
   not `entity.personality`.
