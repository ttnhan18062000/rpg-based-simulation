---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261011-NEAREST-WORK-READS-THE-DECLARED-WORK-BUILDINGS-NOT-ONLY-THE-INN
artifact_type: plan
tags: []
---

# plan — TCK-20261011-NEAREST-WORK-READS-THE-DECLARED-WORK-BUILDINGS-NOT-ONLY-THE-INN

## Typed shape (durable state: needs rpg-planner's yes before code)
- **Content:** `BuildingDefinition.maintenance_shifts: int = Field(1, ge=0)`, the shifts a building needs each upkeep period (0 = no upkeep, no work offered). A coarse band per kind in `data/content/world/buildings.yaml` (D50).
- **State:** two typed ints on `BuildingState`, both in `to_canonical_dict` (serialised, inspectable, hashed):
  - `maintenance_shifts_needed: int = 0`, set once at compile from content (so the paying code reads state only, never the catalog, and a worker packet carries it).
  - `maintenance_shifts_done: int = 0`, the counter for the current period.
  Only `needed` could be read from the catalog by kind to avoid the second field; I propose both so state is self-contained (a worker packet has no catalog guarantee).
- **Update:** `BuildingUpdate.maintenance_shifts_done_delta: int = 0` (a shift paid) and `maintenance_shifts_done_set: Optional[int] = None` (the period reset). `merge` sums the delta and takes the set. `apply_plan.py:225` applies them (new value = set if given, else done + delta; the set wins over deltas of the same tick, so a reset tick cannot lose a paid shift: the order is reset first, then deltas).
- **Period reset point:** `TownResolutionSystem.resolve` step 4, on `is_tax_tick` (every `town_resolution * 2` ticks), in the same pass that meets upkeep: for each building the pass emits `maintenance_shifts_done_set=0` together with any `functional_set` or top-up it already emits. One place; no new cadence.
- **Upkeep derivation:** `required = maintenance_shifts_needed * WAGE_GOLD` replaces `MAINTENANCE_COST` (retired, with its constant and tests). `_meet_upkeep`: shortfall = max(0, required - building purse); the holder treasury tops up the shortfall, and the building closes when neither can pay (unchanged shape, new amount). Unworked upkeep stays in the purse.
- **Paying a shift:** `work_update` emits the WAGE with `treasury_pays` for any building whose holder faction exists, when `needed - done > 0`; `conservation._wage_result` caps the top-up at the remaining need (`(needed - done) * WAGE_GOLD` minus what the purse already covers) and returns `BuildingUpdate(maintenance_shifts_done_delta=1)` with the purse debit, in the same typed transfer (one apply path, no second writer).
- **Decision layer:** `work_shift.nearest_work` reads kinds with `maintenance_shifts_needed > 0` and `done < needed` in reach, whose payer can pay (purse + holder treasury `can_pay` for one wage). It reads only, no new scoring terms; `serves(...)` and `LeashService.way_in_range` stay as filters. No building name in code (D56).
- **Retired:** `MAINTENANCE_COST`, `SERVICE_KINDS["WORK"]`'s hard-coded inn, `TREASURY_WORK_KINDS`. `SERVICE_KINDS["WORK"]` is replaced by a state-derived check.
## Files
`src/core/state.py` (two fields, canonical dict), `src/core/updates.py` (BuildingUpdate), `src/engine/apply_plan.py` (apply), `src/engine/town_resolution.py` (period reset, derived upkeep), `src/core/conservation.py` (cap, counter), `src/engine/work_shift.py` (nearest_work, work_update), `src/engine/building_services.py` (WORK set), `src/content/schema.py` + `data/content/world/buildings.yaml`, `src/worldbuilding/compiler.py` (copy needed), `docs/` (Bible 03 EXCH-02, divergence 2.115, parity), registry pins, golden fixtures that hash buildings (to be listed by the test run).
## Order
1. Answers to Q1-Q3 and a yes on the two fields. 2. Content + state + update + apply (with the canonical-dict/golden fixture changes). 3. Upkeep derivation and period reset. 4. Shift counting and cap. 5. nearest_work. 6. Docs, measurement (free-meal-OFF arm: purse balances, top-up counts, wages per kind), divergence and parity.
