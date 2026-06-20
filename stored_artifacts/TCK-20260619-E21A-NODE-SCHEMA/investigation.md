---
status: historical
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260619-E21A-NODE-SCHEMA
artifact_type: investigation
tags: [resource-ecology, state-schema, event-taxonomy, phase-2]
---

# Investigation — TCK-20260619-E21A-NODE-SCHEMA
## Epic 2.1A · ResourceNodeState Schema Extension + RESOURCE_RECOVERED Event

## Current Behavior

### ResourceNodeState (`src/core/state.py:L808`)

```python
@dataclass(frozen=True, slots=True)
class ResourceNodeState:
    id: int
    kind: str
    position: tuple[float, float]
    yields_item: str
    remaining_charges: int
    max_charges: int
    required_ticks: int
    respawn_cooldown: int = 100
    cooldown_remaining: int = 0
    _canonical_cache: Any = field(default=None, init=False, repr=False, compare=False)
    _readonly_cache: Any = field(default=None, init=False, repr=False, compare=False)
```

`to_canonical_dict()` at L826 outputs keys: `id`, `kind`, `position`, `yields_item`,
`remaining_charges`, `max_charges`, `required_ticks`, `respawn_cooldown`, `cooldown_remaining`.
Uses `_canonical_cache` with `object.__setattr__` to update despite `frozen=True`.

`regen_rate_per_tick` is absent — no per-tick charge regen field exists.

### WorldEventCategory (`src/domains/world_emergence/schema.py:L12`)

Current members: `ENTITY_DEATH`, `NEAR_DEATH`, `RESOURCE_HARVESTED`, `RESOURCE_DEPLETED`,
`QUEST_COMPLETED`, `QUEST_FAILED`, `CAMP_CLEARED`, `CAMP_RAID`, `SHOP_STOCK_DEPLETED`,
`SERVICE_UNAVAILABLE`, `REGION_ENTERED`, `REGION_AVOIDED`, `RUMOR_CONFIRMED`,
`RUMOR_CONTRADICTED`, `PARTY_ABANDONED`.

`RESOURCE_RECOVERED` is absent — counterpart to `RESOURCE_DEPLETED` missing.

## Caller Safety Analysis

All callers of `ResourceNodeState(...)` use keyword arguments. Verified via grep across
`src/` and `tests/` — no positional-only callers found. The new `regen_rate_per_tick=0`
default is therefore backward-safe for all 30+ call sites.

Key call sites:
- `src/worldbuilding/compiler.py:L208` — keyword args only
- `src/world/ecology.py:L62` — keyword args only
- `src/perf/scenarios.py:L97` — keyword args only
- `src/certification/scenarios.py:L430, L469` — keyword args only
- `tests/unit/resource/test_resource_contract.py` — keyword args only
- `tests/unit/core/test_hardening_e5.py` — keyword args only

## Mechanics/Engine Constraints

- `docs/mechanics/03_economic_laws.md` § harvesting: Resource nodes have `remaining_charges`,
  depleted nodes enter cooldown. Regen logic belongs to E21B — this ticket is schema-only.
- `frozen=True, slots=True` requires new field in class body (not post-init). Field must
  appear before the internal `_canonical_cache` / `_readonly_cache` fields.
- `to_canonical_dict()` caches result via `object.__setattr__` — new field must be added
  to the `res` dict before `object.__setattr__(self, "_canonical_cache", res)`.
- No authoritative pipeline changes needed — this is pure schema extension.

## Parity Ledger Overlap

Checked `docs/parity_ledger/town_resource.yaml`. No existing entry covers
`regen_rate_per_tick` or `RESOURCE_RECOVERED`. These are new behaviors introduced
by this ticket (schema-only). After E21B adds regen logic, a new parity entry will be
needed in `town_resource.yaml`. This ticket does not require a parity update — no
observable behavior changes (default=0 preserves existing behavior for all callers).

## Prior Work

- `TCK-20260425-PH6-M3-HARVEST` — implemented authoritative depletion + cooldowns.
  Confirmed `cooldown_remaining` field exists and `respawn_cooldown=100` default is in place.
- `stored_artifacts/TCK-20260425-PH6-M3-HARVEST/investigation.md` — referenced node
  structure matches current state in `src/core/state.py`.

## Risks and Open Questions

1. **Field ordering** — `regen_rate_per_tick: int = 0` must go after `cooldown_remaining`
   (last keyword-defaulted field before the `field(...)` caches). Confirmed safe.
2. **Cache invalidation** — `_canonical_cache` is set lazily on first call. Adding the
   field to `res` before the `object.__setattr__` call is sufficient.
3. **No behavior risk** — default 0 means no regen fires; existing tests unaffected.

## Anti-Drift Hazards

- Do not add `regen_rate_per_tick` to `ResourceDefinition` in `src/content/schema.py`
  (that is a catalog schema, not runtime state — out of scope).
- Do not add any regen logic or event emission (E21B scope).
- Do not change `WorldEvent` dataclass or any consumer of `WorldEventCategory`.
