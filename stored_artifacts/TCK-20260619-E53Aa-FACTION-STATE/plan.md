# Plan — TCK-20260619-E53Aa-FACTION-STATE

## Overview

Add `FactionState` and `FactionUpdate` durable typed models to the V2 core, wire
`factions` into `AuthoritativeState`, update the `StateUpdate` merge/noop path,
apply faction updates through `apply.py`, and cover everything with the required
unit tests.

---

## Scope Guards — What NOT to Touch

| Off-limits | Why |
|---|---|
| `Faction(IntEnum)` in `src/core/enums.py:L15` | Numeric entity-identity tag; unrelated to `FactionState`. Never import, modify, or reference from the new code. |
| `RegionState` and `population_cohorts` | E52A work; pattern reference only, not a target. |
| `GroupRecord` (except the blank line after its closing `to_canonical_dict`) | `FactionState` is inserted after `GroupRecord`'s final line (L566 `return res`), in the blank block at L568. |
| `information_providers` threading omission in `apply.py` | That field's intentional reset-each-tick is an existing deliberate behavior; do not alter it while adding `factions`. |
| `__post_init__` cache-clearing block in `AuthoritativeState` | Do not add `factions` here — it is a normal durable field, not a cache slot. |
| `apply_plan.py` / `ApplyPlanBuilder` | Faction updates do NOT flow through `build_plan()`. They are applied directly in `apply.py`, following the `quest_registry` pattern (L316-325). |

---

## Dependency Map

```
Step 1 (FactionState in state.py)
  └── Step 2 (factions field on AuthoritativeState) — needs FactionState type
  └── Step 3 (FactionUpdate in updates.py) — independent of Step 2
        └── Step 4 (StateUpdate faction_updates field) — needs FactionUpdate type
              └── Step 5 (apply.py apply logic) — needs FactionUpdate + factions field
                    └── Step 6 (tests) — needs all of Steps 1–5
```

Steps 1 and 3 are independently writable in parallel (different files). Step 2
requires Step 1. Step 4 requires Step 3. Step 5 requires Steps 2 + 4. Step 6
requires all prior steps.

---

## Step 1 — Add `FactionState` frozen dataclass to `src/core/state.py`

**Location:** Insert the new class in the blank block after `GroupRecord.to_canonical_dict`
closes (after L566 `return res`, before L569 `@dataclass(frozen=True, slots=True)
class EquipmentComponent`).

**File:** `src/core/state.py`

**What to add** (place the full block between the blank line at L568 and the
`EquipmentComponent` decorator at L569):

```python
@dataclass(frozen=True, slots=True)
class FactionState:
    """Authoritative durable state for a named faction (E53 family)."""
    faction_id: str
    territory: Tuple[str, ...] = ()           # region_ids controlled
    resources: Dict[str, int] = field(default_factory=dict)
    diplomatic_relations: Dict[str, str] = field(default_factory=dict)
    active_doctrines: Tuple[str, ...] = ()
    military_strength: float = 1.0
    tension_level: float = 0.0
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)

    def to_canonical_dict(self) -> Dict[str, Any]:
        if self._canonical_cache is not None:
            return self._canonical_cache
        res: Dict[str, Any] = {
            "faction_id": self.faction_id,
            "territory": list(self.territory),
            "resources": dict(sorted(self.resources.items())),
            "diplomatic_relations": dict(sorted(self.diplomatic_relations.items())),
            "active_doctrines": list(self.active_doctrines),
            "military_strength": self.military_strength,
            "tension_level": self.tension_level,
        }
        object.__setattr__(self, "_canonical_cache", res)
        return res

    @classmethod
    def from_dict(cls, d: dict) -> "FactionState":
        return cls(
            faction_id=d["faction_id"],
            territory=tuple(d.get("territory", [])),
            resources=dict(d.get("resources", {})),
            diplomatic_relations=dict(d.get("diplomatic_relations", {})),
            active_doctrines=tuple(d.get("active_doctrines", [])),
            military_strength=float(d.get("military_strength", 1.0)),
            tension_level=float(d.get("tension_level", 0.0)),
        )
```

**Key implementation rules:**
- `territory` and `active_doctrines` are `Tuple[str, ...]` — use `tuple(...)` in
  `from_dict`, never bare assignment from JSON which returns `list`.
- `resources` and `diplomatic_relations` dicts are `sorted()` in `to_canonical_dict`
  for determinism.
- `_canonical_cache` slot uses the standard `object.__setattr__` bypass (same
  pattern as `GroupRecord` L509 and `RegionState`).
- `faction_id` is a plain `str` (catalog-registered). Never replace or reference
  `Faction(IntEnum)` from `src/core/enums.py`.

**Verification:** `FactionState(faction_id="x")` constructs without error; frozen
(assignment raises `FrozenInstanceError`); `from_dict(fs.to_canonical_dict()) == fs`.

---

## Step 2 — Add `factions` field to `AuthoritativeState`

**File:** `src/core/state.py`, `AuthoritativeState` class (L1001+)

**Location:** Append after `information_providers: Dict[int, "InformationProviderState"]`
at L1073, which is the current last field of the class.

```python
    # Epic 5.3: Durable faction-level state (E53Aa)
    factions: Dict[str, FactionState] = field(default_factory=dict)
```

**Key implementation rules:**
- `FactionState` is already defined earlier in the same file (Step 1), so no
  forward-reference quote is needed if Step 1 is done first. If editing in the
  same pass, use `"FactionState"` with quotes as a precaution.
- The field has `default_factory=dict` — satisfies `slots=True` (no bare `{}`)
  and keeps all existing `AuthoritativeState(tick=0, seed=0)` calls valid.
- Place it as the last field before `__post_init__` (currently L1075). Do not
  insert among the `init=False` cache fields (L1024–1043); those are private
  transient caches.
- Do NOT add `factions` to `__post_init__`'s `object.__setattr__` block — it
  is a durable field, not a cache slot.
- The `AuthoritativeState` comment block `# VERIFIED v2: authoritative_world_objects`
  (L1007) is already present; leave it intact. A new parity entry covering
  `factions` will be created in the Parity phase (Step 6b, post-implementation).

**Also update `to_readonly()` (~L1138):**
Add `factions=ReadOnlyDict(self.factions)` inside the `replace(self, ...)` call,
alongside `quest_registry=ReadOnlyDict(self.quest_registry)` and
`information_providers=ReadOnlyDict(self.information_providers)`. This wraps the
dict container (the FactionState values are already frozen, but the container must
be read-only to match the contract applied to all other Dict fields).

**Verification:** `AuthoritativeState(tick=0, seed=0).factions == {}` passes; 
`"factions" in {f.name for f in dataclasses.fields(AuthoritativeState)}` is True;
`to_readonly()` returns without error and `.factions` is a `ReadOnlyDict`.

---

## Step 3 — Add `FactionUpdate` frozen dataclass to `src/core/updates.py`

**File:** `src/core/updates.py`

**Location:** Insert the new class immediately before the `StateUpdate` class
definition at L836. Place it after the `QuestOpportunityRewardIntent` dataclass
(whichever comes last just before `StateUpdate`).

```python
@dataclass(frozen=True, slots=True)
class FactionUpdate:
    """Typed mutation record for a single faction's durable state (E53Aa)."""
    faction_id: str
    tension_delta: float = 0.0
    military_strength_set: Optional[float] = None
    territory_add: Tuple[str, ...] = ()
    territory_remove: Tuple[str, ...] = ()
    resources_delta: Dict[str, int] = field(default_factory=dict)
    diplomatic_relations_set: Dict[str, str] = field(default_factory=dict)
    active_doctrines_set: Optional[Tuple[str, ...]] = None

    def is_noop(self) -> bool:
        return (
            self.tension_delta == 0.0
            and self.military_strength_set is None
            and not self.territory_add
            and not self.territory_remove
            and not self.resources_delta
            and not self.diplomatic_relations_set
            and self.active_doctrines_set is None
        )
```

**Key implementation rules:**
- `tension_delta` accumulates (additive); `military_strength_set` overwrites (Optional,
  `None` means no change).
- `territory_add` / `territory_remove` are `Tuple[str, ...]` — use set-difference
  semantics when applying in Step 5.
- `is_noop()` must check every field. Zero-valued float `0.0` is falsy but compare
  with `== 0.0` explicitly to be safe and readable.
- `Optional` and `Tuple` imports are already present in `updates.py`; verify before
  adding new import lines.

**Verification:** `FactionUpdate(faction_id="x").is_noop() is True`;
`FactionUpdate(faction_id="x", tension_delta=0.1).is_noop() is False`.

---

## Step 4 — Add `faction_updates` to `StateUpdate`; update `is_noop()` and `merge_many()`

**File:** `src/core/updates.py`, `StateUpdate` class (L836+)

### 4a — Add field (after `information_providers_update` at L886):

```python
    # E53Aa: Faction durable-state mutation records
    faction_updates: List[FactionUpdate] = field(default_factory=list)
```

### 4b — Update `is_noop()` (L888–911):

Append the following condition to the final `and` chain (after
`not self.information_providers_update`):

```python
                and not self.faction_updates
```

The final two lines of `is_noop()` become:
```python
                not self.quest_opportunity_reward_intents and
                not self.information_providers_update and
                not self.faction_updates)
```

### 4c — Update `merge_many()`:

**Initialization block** (after `new_information_providers_update = dict(self.information_providers_update)`
at L963, add):

```python
        new_faction_updates = list(self.faction_updates)
```

**Loop body** (after `new_information_providers_update.update(other.information_providers_update)`
at L1028, add):

```python
            new_faction_updates.extend(
                fu for fu in other.faction_updates if not fu.is_noop()
            )
```

**`replace(self, ...)` call** (after `information_providers_update=new_information_providers_update,`
at L1087, add):

```python
            faction_updates=new_faction_updates,
```

**Key implementation rules:**
- `faction_updates` uses list-append semantics (same as `world_events_add`); no
  per-entry merge logic is needed at this layer.
- Filter `is_noop()` updates during merge to prevent list growth from zero-delta
  entries (see Open Question 2 in investigation — recommended: yes, filter noop).
- `List` is already imported at the top of `updates.py`.

**Verification:** `StateUpdate().is_noop() is True`; 
`StateUpdate(faction_updates=[FactionUpdate(faction_id="x", tension_delta=0.1)]).is_noop() is False`;
`upd1.merge(upd2).faction_updates` contains both factions' updates.

---

## Step 5 — Apply `FactionUpdate` list in `apply.py`

**File:** `src/engine/apply.py`, `ApplyPath.apply_generation()` method

**Location:** In the block just before the `AuthoritativeState(...)` constructor
call at L327, add faction resolution after the `quest_registry` block (L316–325):

```python
        # Epic 5.3Aa: Apply faction updates to durable factions dict
        new_factions = dict(getattr(prior_state, "factions", {}))
        for fu in update.faction_updates:
            if fu.is_noop():
                continue
            existing = new_factions.get(fu.faction_id)
            if existing is None:
                # First encounter: create a baseline FactionState
                from src.core.state import FactionState
                existing = FactionState(faction_id=fu.faction_id)
            # Apply tension_delta (accumulate)
            new_tension = existing.tension_level + fu.tension_delta
            # Apply military_strength_set (overwrite if provided)
            new_ms = fu.military_strength_set if fu.military_strength_set is not None else existing.military_strength
            # Apply territory add/remove (set semantics)
            new_territory = (set(existing.territory) | set(fu.territory_add)) - set(fu.territory_remove)
            # Apply resources_delta (accumulate per key)
            new_resources = dict(existing.resources)
            for k, v in fu.resources_delta.items():
                new_resources[k] = new_resources.get(k, 0) + v
            # Apply diplomatic_relations_set (overwrite provided keys)
            new_relations = {**existing.diplomatic_relations, **fu.diplomatic_relations_set}
            # Apply active_doctrines_set (overwrite if provided)
            new_doctrines = fu.active_doctrines_set if fu.active_doctrines_set is not None else existing.active_doctrines
            new_factions[fu.faction_id] = replace(existing,
                tension_level=new_tension,
                military_strength=new_ms,
                territory=tuple(sorted(new_territory)),
                resources=new_resources,
                diplomatic_relations=new_relations,
                active_doctrines=new_doctrines,
            )
```

**Then add `factions=new_factions` to the `AuthoritativeState(...)` constructor
call** (L327–374). Add it immediately after `quest_registry=new_quest_registry,`
at L373:

```python
            quest_registry=new_quest_registry,
            factions=new_factions,
```

**Key implementation rules:**
- `getattr(prior_state, "factions", {})` guards against states constructed before
  this field existed (replay safety).
- `replace(existing, ...)` is the approved frozen-dataclass mutation path; never
  direct assignment.
- `territory` is stored as `tuple(sorted(...))` for determinism.
- The `from src.core.state import FactionState` import inside the function is only
  needed if `FactionState` is not already imported at the top of `apply.py`. Check
  imports first; add to the top-of-file import block if missing (preferred).
- This does NOT go through `apply_plan.py` / `ApplyPlanBuilder`. Faction state is
  top-level on `AuthoritativeState`, analogous to `quest_registry`.

**Verification:** `test_faction_state_factions_persist_across_ticks` — calling
`ApplyPath.apply_generation(state, StateUpdate(), next_tick=2)` on a state with
`factions={"hero_guild": FactionState(...)}` must return a new state where
`"hero_guild"` is still present with unchanged `tension_level`.

---

## Step 6 — Write `tests/unit/faction/test_faction_state.py`

**Files to create:**
- `tests/unit/faction/__init__.py` (empty)
- `tests/unit/faction/test_faction_state.py`

**Required tests** (verbatim from `test_plan.md`):

| Test | AC covered |
|---|---|
| `test_faction_state_serialization_round_trip` | `from_dict(to_canonical_dict()) == fs`; tuple fields survive; dict keys are sorted |
| `test_authoritative_state_has_factions_field` | Default `factions={}` on `AuthoritativeState(tick=0, seed=0)`; field in `dataclasses.fields()`; can pass populated factions; frozen raises `FrozenInstanceError` |
| `test_faction_update_apply_tension_delta` | `tension_delta` accumulates; unchanged fields unmodified |
| `test_faction_update_territory_add_remove` | Set-union / set-difference semantics on `territory` |
| `test_faction_update_military_strength_set` | Overwrites, not accumulates |
| `test_faction_update_is_noop` | Zero-delta update returns `True`; non-zero returns `False` |
| `test_state_update_merge_faction_updates` | Merge concatenates both lists |
| `test_state_update_is_noop_with_faction_updates` | Empty `StateUpdate()` is noop; `StateUpdate(faction_updates=[...])` is not |
| `test_faction_state_factions_persist_across_ticks` | `apply_generation()` with no-op `StateUpdate` preserves pre-existing factions (guards `apply.py` omission hazard) |

Implement each test exactly as specified in `test_plan.md`. Do not add extra
abstraction layers or shared fixtures beyond a simple inline helper if needed
for state construction.

**Verification command:**

```bash
pytest tests/unit/faction/ -x -v
pytest tests/unit/core/test_authoritative_state_contract.py -x -v
pytest tests/integration/pipeline/test_state_isolation.py -x -v
pytest tests/unit/optimization/test_state_update_compactor.py -x -v
```

All must pass. No regressions in the regression surface files listed in
`test_plan.md`.

---

## Acceptance Criteria → Step Mapping

| Acceptance Criterion | Step(s) |
|---|---|
| `FactionState` is constructible and frozen | Step 1 |
| `to_canonical_dict()` / `from_dict()` round-trip | Step 1 |
| `AuthoritativeState(tick=0, seed=0)` has `factions={}` | Step 2 |
| Existing `AuthoritativeState` tests pass | Steps 2, 5 (no regressions) |
| `FactionUpdate` applies `tension_delta` (accumulates) | Steps 3, 5 |
| `FactionUpdate` applies `territory_add/remove` (set semantics) | Steps 3, 5 |
| `FactionUpdate` applies `military_strength_set` (overwrites) | Steps 3, 5 |
| `test_faction_state_serialization_round_trip` passes | Steps 1, 6 |
| `test_authoritative_state_has_factions_field` passes | Steps 1, 2, 6 |
| `test_faction_update_apply_tension_delta` passes | Steps 1–5, 6 |

---

## Unresolved Questions

### UQ-1 — Is `information_providers` intentional reset-each-tick?

The investigation confirmed `information_providers` is **not** passed in the
`apply.py` `AuthoritativeState(...)` constructor (L327–374), causing it to reset
to `{}` on every tick. The investigation notes "likely intentional for E42D
(cache-like updates) but is a hazard for `factions`." This is resolved for the
purposes of this ticket: `factions=new_factions` MUST be explicitly threaded
through. No action needed on `information_providers` in this ticket — but the
behavior should be confirmed with the E42D ticket author or a test before any
later ticket relies on `information_providers` persisting across ticks.

### UQ-2 — `FactionUpdate.is_noop()` filtering inside `merge_many()` — confirmed yes

The investigation raised this as "Open Question 2" and recommended filtering
noop `FactionUpdate` entries during merge. This plan adopts that recommendation
(Step 4c uses `fu for fu in other.faction_updates if not fu.is_noop()`). If
there is a reason to preserve zero-delta entries in the merged list (e.g., for
audit / trace purposes in a later ticket), revisit before E53Ad.

### UQ-3 — `AuthoritativeState.to_readonly()` / fingerprint coverage of `factions`

The investigation flagged (`Risk 3`) that `AuthoritativeState` may have a
`to_canonical_dict()` or `fingerprint()` method that enumerates fields. If so,
`factions` must be included there. Verify by reading `to_readonly()` and any
`fingerprint` method in `src/core/state.py` before finalizing Step 2. If
`factions` is missing from an explicit field enumeration, add it. This check is
a precondition for marking Step 2 complete.

### UQ-4 — Parity ledger file location for FAC-001

The investigation recommends creating `docs/parity_ledger/faction.yaml` for
the E53 family (vs. adding to `substrate.yaml`). This decision affects the
Parity phase (post-implementation, outside the 6 implementation steps). The
implementer should confirm whether to create a new `faction.yaml` file or
extend `substrate.yaml` with a new section. A new file is preferred for
scalability given E53B–E53D will add further faction entries.

---

## Deviations from Plan

### Deviation 1 — Tension clamping in apply.py

The plan's Step 5 code snippet applies `new_tension = existing.tension_level + fu.tension_delta` without clamping. The plan header mentions "clamp 0.0-1.0" in the description text. Implementation applies `max(0.0, min(1.0, new_tension))` to keep tension in the valid [0.0, 1.0] range, consistent with a percentage semantics. No test was added specifically for clamping since it is a guard, not a testable AC item — can be added in E53Ad.

### Deviation 2 — `Tuple` import added to updates.py

`Tuple` was not in the `typing` imports of `src/core/updates.py`. Added alongside existing `Dict`, `Any`, `Optional`, `List`. No functional impact.

### Deviation 3 — `factions` field placed after `information_providers`

The ticket scope says "place after `groups` field." The plan Step 2 says "append after `information_providers`." Implementation followed the plan (after `information_providers`) since that is the last public durable field before `__post_init__`. This matches the intent of both docs: `groups` is much earlier and placing `factions` immediately before `__post_init__` keeps related durable-registry fields together.

### Deviation 4 — Using `"FactionState"` forward-reference string in AuthoritativeState

Used `Dict[str, "FactionState"]` with quoted forward reference in `AuthoritativeState` to be safe (Step 1 and Step 2 were done in sequence in the same file, but `from __future__ import annotations` at the top of state.py makes all annotations strings anyway — no functional difference).
