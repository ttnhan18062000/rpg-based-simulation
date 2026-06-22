# Investigation — TCK-20260619-E53Aa-FACTION-STATE

## Current Behavior

### What Exists Today

**GroupRecord** (`src/core/state.py:L513`):
`@dataclass(frozen=True, slots=True)` with `_canonical_cache` as the final field (`field(default=None, init=False, repr=False, compare=False)`). Uses `object.__setattr__` in `to_canonical_dict()` to populate the cache slot (the canonical way to bypass frozen in slots dataclasses). This is the direct neighbor where `FactionState` will be inserted.

**AuthoritativeState** (`src/core/state.py:L1001`):
`@dataclass(frozen=True, slots=True)`. Current public durable-state fields in insertion order:
- `entities`, `resource_nodes`, `ground_items`, `corpses`, `chests`, `buildings`, `camps`, `regions`, `local_scars` — then cache fields
- `groups`, `terrain`, `global_resources`, `home_storage`, `town_center`, `periodic_due_ticks`, `work_debt`, `movement_count`, `maturity`, `last_calamity_tick`, `blocked_tiles`, `town_tiles`, `building_tiles`, `town_entity_ids`, `rng_checkpoint`, `transaction_trace`, `rejection_registry`, `pressure_signals`
- Further: `pending_information_responses`, `information_source_profiles`, `feature_flags`, `recent_world_events`, `quest_registry`, `information_providers`

`__post_init__` clears all `_*_cache` slots via `object.__setattr__`. No faction field exists anywhere in `state.py` or `updates.py`.

**StateUpdate** (`src/core/updates.py:L836`):
`@dataclass(frozen=True, slots=True)`. Contains `information_providers_update: Dict[int, "InformationProviderState"]` as its last field (E42D addition). `is_noop()` at L888 checks every field. `merge_many()` at L918 handles all field types.

**StateUpdate.merge()** delegates to `merge_many([other])`. `merge_many()` opens local mutable copies of all collections, iterates `valid_others`, then calls `replace(self, ...)` at the end with all new values.

**RegionState** (`src/core/state.py:L207`):
Pattern to follow. Key details:
- Fields include `population_cohorts: Dict[str, Any] = field(default_factory=dict)` as the last public field (E52A addition), followed by `_canonical_cache`.
- `to_canonical_dict()` uses a cache guard, returns a fully sorted dict, then sets `_canonical_cache` via `object.__setattr__`.
- No `from_dict()` on `RegionState` — note that the ticket scope adds `from_dict` to `FactionState`. The canonical pattern for `from_dict` exists on `FactionSocialMemory` in `src/domains/campaigns/social_memory.py` (campaign layer only — referenced for pattern, not for import).

**WorldUpdate / apply_plan.py pattern** (`src/core/updates.py:L747`, `src/engine/apply_plan.py:L79`):
- `WorldUpdate` carries delta fields for `RegionState` (including `population_cohorts_set`).
- `apply_plan.py:L109-128` iterates `update.world_updates` and calls `replace(reg, ...)` with each field.
- **FactionUpdate is a sibling concept, not a child of WorldUpdate.** It is a new top-level update type (like `BuildingUpdate`, `CampUpdate`) keyed by `faction_id: str`.

**apply.py `ApplyPath.apply_generation()`** (`src/engine/apply.py:L187`):
- Calls `ApplyPlanBuilder.build_plan()` to get collection dicts, then reconstructs `AuthoritativeState` directly at L327.
- The `new_state = AuthoritativeState(...)` constructor at L327 does NOT include every field — omitted fields fall through to their `field(default_factory=...)`. Key omissions: `information_providers` is NOT passed (defaults to `{}`). This means any field with `field(default_factory=dict)` that is NOT explicitly passed through `apply.py` will silently reset to empty on every tick.
- **CRITICAL**: `factions` MUST be explicitly threaded through `apply.py`'s constructor call, similar to `quest_registry` (L373). Otherwise `state.factions` will be `{}` after every `apply_generation()` call.

### FactionSocialMemory (campaigns layer — pattern only)
`src/domains/campaigns/social_memory.py` — provides `to_dict()`/`from_dict()` pattern for a frozen dataclass. Its `from_dict` uses a simple `cls(...)` constructor call. Reference for the `FactionState.from_dict()` implementation shape; do NOT import or couple to it.

---

## Mechanics / Engine Constraints

### `slots=True` Implications
Every field on a `slots=True` dataclass must be declared at class definition time — there is no `__dict__`. Adding a field after the fact is not possible without redefining the class. New fields must have defaults (since `AuthoritativeState.__init__` has required positional args `tick` and `seed` — all new fields must have `field(default_factory=...)` or `field(default=...)` to avoid breaking existing instantiation).

### Frozen Dataclass Rules
- `object.__setattr__(self, "_canonical_cache", res)` is the approved bypass for cache population inside `to_canonical_dict()`.
- `replace(obj, field=new_value)` is the approved mutation path for producing a new instance.
- Do not call `dataclasses.replace()` on `AuthoritativeState` directly in apply.py — the existing pattern constructs a fresh `AuthoritativeState(...)` with all fields specified.

### Dict Field Defaults
`Dict` and `List` fields require `field(default_factory=dict)` / `field(default_factory=list)` — never a bare `{}` or `[]` default (Python class-level mutable default trap; also forbidden by `slots=True`).

### Tuple Fields
`territory: Tuple[str, ...]` and `active_doctrines: Tuple[str, ...]` default to `()` (immutable, safe as class-level default). `field(default=())` is correct; no `default_factory` needed.

### apply_plan.py vs apply.py Split
- `apply_plan.py` handles collection-level changes (regions, groups, nodes, etc.) via `build_plan()`.
- `apply.py` handles the final `AuthoritativeState(...)` reconstruction including scalar fields, trace, registries.
- Faction apply logic does NOT fit cleanly into `build_plan()` (which is structured around pre-declared collection keys). It should be handled directly in `apply.py` `apply_generation()`, analogous to how `quest_registry` (L316-325) is handled: compute `new_factions` dict before the `AuthoritativeState(...)` call, then pass it as `factions=new_factions`.

### `StateUpdate.is_noop()` Must Be Updated
The new `faction_updates: list[FactionUpdate]` field must be added to the `is_noop()` check: `... and not self.faction_updates`.

### `StateUpdate.merge_many()` Must Be Updated
`faction_updates` is a list (append semantics, no merge logic needed per entry — unlike `entity_updates` which merges by id). Pattern: same as `new_world_events_add = list(self.world_events_add)` extended by `other.world_events_add`.

---

## Parity Ledger Overlap

### social_narrative.yaml
Scanned for faction entries. The file contains references to `faction_reputation`, `faction_social_memories`, and `FactionSocialMemory` at the campaign layer (E43 family). None of these describe tick-level `FactionState`. No existing parity entry covers `AuthoritativeState.factions` — this is a net-new capability.

**Entries that may need new parity entries after this ticket:**
- A new entry in `social_narrative.yaml` or a new `faction.yaml` ledger file covering:
  - `FactionState` durable model (state tick-level)
  - `factions: Dict[str, FactionState]` in `AuthoritativeState`
  - `FactionUpdate` apply path (tension_delta, territory_add/remove)

### world_dynamics.yaml
One entry (line 718): `text: Spawned entity faction is valid.` — references `Faction(IntEnum)` on entity identity. Not affected by this ticket.

### substrate.yaml
Contains `authoritative_state_model` and `authoritative_world_objects` verified entries (referenced in state.py L1002 comments). Adding `factions` to `AuthoritativeState` extends the world objects contract. The existing `VERIFIED v2: authoritative_world_objects` comment should be preserved and a new parity entry added post-implementation.

**Recommended new parity entry ID:** `FAC-001` (suggest creating `docs/parity_ledger/faction.yaml` for the E53 family, or add to `substrate.yaml` under a new section).

---

## Prior Work

### E52A — PopulationCohort (exact model to follow)

The E52A pattern is the canonical reference for this ticket:

| E52A step | E53Aa equivalent |
|---|---|
| Add `PopulationCohort` frozen dataclass in `state.py` | Add `FactionState` in `state.py` adjacent to `GroupRecord` (~L514) |
| Add `population_cohorts: Dict[str, PopulationCohort]` to `RegionState` | Add `factions: Dict[str, FactionState]` to `AuthoritativeState` |
| Add `population_cohorts_set` to `WorldUpdate` | Add `faction_updates: list[FactionUpdate]` to `StateUpdate` |
| Update `apply_plan.py` replace call | Update `apply.py` constructor call to pass `factions=new_factions` |
| `DemographicCycleService` reads/writes cohorts via `StateUpdate` | Out of scope for this ticket (E53Ad) |

**Key difference from E52A:** E52A's new state lives nested inside `RegionState` (applied via `WorldUpdate` → `apply_plan.py`). E53Aa's `FactionState` lives at the top level of `AuthoritativeState` (applied directly in `apply.py` `apply_generation()`, analogous to `quest_registry`).

### E42D — InformationProviderState (most recent AuthoritativeState field addition)
Added `information_providers: Dict[int, "InformationProviderState"]` to `AuthoritativeState` (L1073) and `information_providers_update: Dict[int, ...]` to `StateUpdate`. However, **it is NOT passed in `apply.py` `AuthoritativeState(...)` constructor** (L327–374) — it resets to `{}` each tick. This is likely intentional for E42D (cache-like updates) but is a hazard for `factions`. `FactionState` is durable and MUST be explicitly threaded through.

---

## Risks and Open Questions

### Risk 1: apply.py constructor omission (HIGH)
`apply.py:L327` constructs `AuthoritativeState(...)` with explicit keyword args. `factions` must be added here or it silently resets to `{}` on every tick. Verify by checking that `information_providers` is indeed reset-by-default and understand whether that was intentional.

### Risk 2: `slots=True` field ordering
`AuthoritativeState` has a mix of init fields and non-init cache fields. New `factions` field must be placed after all `_readonly_cache`-style fields (which are `init=False`) to avoid Python's "non-default argument follows default argument" error. The ticket notes placement "after `groups`" — verify that `groups` (L1045) is before the last batch of `repr=False, compare=False` fields. It is: `groups` is at L1045 with a `default_factory`, so `factions` can be added anywhere after `groups` and before the `repr=False` cache fields, or after them (all have defaults).

### Risk 3: `to_canonical_dict()` on `AuthoritativeState`
Check whether `AuthoritativeState` has a `to_canonical_dict()` or `fingerprint()` that enumerates fields. If so, `factions` must be included. (Fingerprint uses `_readonly_cache` which may hash all fields — verify.)

### Risk 4: `from_dict` round-trip completeness
`FactionState.from_dict()` must handle the `Tuple[str, ...]` fields correctly — JSON deserializes tuples as lists, so `from_dict` must call `tuple(d.get("territory", []))`. This is a common trap.

### Risk 5: Dict fields with mutable values in `to_canonical_dict()`
`resources: Dict[str, int]` and `diplomatic_relations: Dict[str, str]` must be sorted in `to_canonical_dict()` for determinism. Pattern: `dict(sorted(self.resources.items()))`.

### Open Question 1
Is `information_providers` intentionally reset each tick? If so, there may be a deliberate architectural pattern where session-local state uses `apply.py` omission as a reset mechanism. `FactionState` is NOT session-local — it must persist across ticks.

### Open Question 2
Should `FactionUpdate.is_noop()` be checked inside `merge_many()` to skip no-op faction updates? Analogous to how `entity_updates` merges only non-noop entries. Recommend: yes, filter noop `FactionUpdate` entries during merge.

---

## Anti-Drift Hazards

| Hazard | Description | Guard |
|---|---|---|
| Touching `Faction(IntEnum)` | `src/core/enums.py:L15` — numeric enum on entity identity. Must NOT be removed or modified. `FactionState.faction_id` is a `str`; `IdentityComponent.faction` remains an `int`. These are separate concepts. | Never import or reference `FactionState` from enums.py; never change `Faction(IntEnum)`. |
| Breaking `AuthoritativeState slots=True` | Adding a field without a default will break all existing `AuthoritativeState(tick=0, seed=0)` instantiations. | `factions: Dict[str, FactionState] = field(default_factory=dict)` — always provide default. |
| `apply.py` omission of `factions` | If `factions=new_factions` is not in the `AuthoritativeState(...)` call at apply.py:L327, the field silently resets to `{}` each tick. | Add explicit `factions=new_factions` in the constructor call. |
| Cache field ordering in `slots=True` | Fields with `init=False` must not precede fields with defaults in `__init__` signature. Inserting `factions` after `groups` (L1045) and before the existing non-init cache fields is safe. | Do not insert before `_readonly_cache` non-init fields. |
| `merge_many()` missing `faction_updates` | If `faction_updates` list is not initialized and extended in `merge_many()`, merged `StateUpdate` objects will lose faction mutations. | Add `new_faction_updates = list(self.faction_updates)` and extend in the for-loop. |
| Mutable default in frozen dataclass | `resources: Dict[str, int] = {}` would be a syntax error under slots=True. | Always use `field(default_factory=dict)`. |
| JSON tuple deserialization | `territory` and `active_doctrines` are `Tuple[str, ...]`; JSON round-trip returns lists. | `from_dict` must call `tuple(d.get("territory", []))`. |
