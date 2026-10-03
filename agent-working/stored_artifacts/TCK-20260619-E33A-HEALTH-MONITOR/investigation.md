---
ticket_id: TCK-20260619-E33A-HEALTH-MONITOR
phase: investigation
date: 2026-06-21
---

# Investigation: EconomyHealthMonitor + Metrics

## Current Behavior (file:line refs)

### No macro-economy health tracking exists
There is no `EconomyHealthMonitor`, no `EconomyHealthSnapshot`, and no
`metric_windows.jsonl` economy section today. The absence is confirmed in
`docs/audits/D01_rpg_feature_impact.md` (Macro-Economy Health Metrics `[MISSING]`,
score 16/25, "Absence Penalty: 4 — economy can silently die").

### Existing per-tick metrics pipeline (reuse target)
The kernel already owns a `MetricWindowRecorder` at `_metric_recorder`
(kernel.py L231–242). It is instantiated when `ObservabilityMode != OFF`,
uses `window_size=100`, and writes to `<run_dir>/metric_windows.jsonl`
(`src/observability/reporting/metric_recorder.py` L302–327).
`MetricsService.extract_metrics(state)` is called at the end of each tick
(kernel.py L383–396) and feeds `MetricWindowRecorder.record_tick()`.
The `MetricWindowRecord` Pydantic model lives in
`src/observability/warehouse/models.py` L60–73 and already has a `gold_total_avg`
field — this is the downstream query target (`WarehouseAdapter.query_metric_windows`
at `src/observability/warehouse/base.py` L69).

### Gold is a first-class scalar on InventoryComponent
`src/core/models/inventory.py` L43: `gold: int = 0` — a dedicated field, not
reconstructed from `ItemStack`. The `gold_coin` item_id (`src/core/items.py` L69)
is a separate item definition used for physical coin stacks; the canonical wealth
quantity for per-entity gold is `entity.inventory.gold`.

Two currency IDs exist:
- `"gold_coin"` — `ItemKind.CURRENCY`, `stack_size=999`
- `"gold"` — `ItemKind.CURRENCY`, `stack_size=999999`

The ticket's pseudocode iterates `stack.item_id == "gold_coin"` over
`e.inventory.items`, which would miss gold held in the dedicated `inventory.gold`
field. **This is the primary schema discrepancy that must be resolved before
implementation.** See Risks and Open Questions below.

### Entity liveness
`EntityState.combat.alive: bool` (state.py L270; `CombatComponent.alive` field).
The ticket pseudocode writes `e.is_alive` — that attribute does not exist on
`EntityState`. The correct access is `e.combat.alive`.

### Governance phase
`docs/engine/governance_logic.md` defines governance as the "Town Governance"
stage of the `AuthoritativeApplyPipeline`, handled by `TownResolutionSystem`
(taxation/maintenance) and `WorldDynamicsSystem` (territorial influence). There
is no general-purpose "governance phase step" plugin mechanism in the kernel — the
kernel's `_phase_init` evaluates `ResourceGovernor` policy and the `_phase_scheduling`
selects work items (kernel.py L402–464). The six `TickPhase` values are FROZEN
(`src/engine/phases.py` L6, "Status: FROZEN").

The correct insertion point is the **PERSISTENCE phase hook** in `_tick_once_inner`
(kernel.py L349–351, after ADVANCEMENT), alongside where `_metric_recorder.record_tick()`
is already called (L381–396). The EconomyHealthMonitor.sample() is read-only (no
`StateUpdate` emitted), so it does not need to run in the RESOLUTION phase and must
not mutate `AuthoritativeState`.

Alternatively it can be invoked from `MetricsService.extract_metrics(state)` in
`src/engine/metrics.py` so the result flows into the existing metric pipeline.
This is the lower-risk integration path.

### MetricWindowRecord already has gold_total_avg
`MetricWindowRecord.gold_total_avg: float` (warehouse/models.py L70) is populated
per window. The `EconomyHealthSnapshot` Gini coefficient and velocity fields need
a home — either extend `MetricWindowRecord` or write a separate section within the
same `metric_windows.jsonl` line (using `metrics_json`). Both approaches avoid
a new output file.

However the ticket AC specifies a `metric_windows.jsonl` output with
`gini_coefficient`, `transaction_velocity`, and `avg_price_index` per entry. The
existing `MetricWindowRecord` shape does not include these fields. They can be
packed into `metrics_json` (the free-form JSON dump field) as a backwards-compatible
extension, or `MetricWindowRecord` can be extended with optional fields.

---

## Mechanics / Engine Constraints

- **Atomic Conservation Law** (`docs/mechanics/03_economic_laws.md` §1): gold
  transfers are source→sink atomic. The monitor is read-only — it observes totals,
  it does not transfer. No conservation law applies to the monitor itself.
- **Durable State Rule** (CLAUDE.md Architecture Rule): `EconomyHealthSnapshot` must
  have a typed model (dataclass or Pydantic), a defined lifecycle (one per
  WINDOW_SIZE ticks, not durable across ticks), and test-visible serialization.
  Since it does not survive the tick (written to JSONL, not stored in
  `AuthoritativeState`), it does not need a lifecycle entry in state but must be
  typed.
- **Read-only constraint**: The monitor must read from `state` under the read-only
  view if invoked during COLLECTION, or from the post-ADVANCEMENT mutable state if
  invoked during PERSISTENCE. Since `_metric_recorder.record_tick` is called after
  ADVANCEMENT (L381), sampling there is safe and consistent.
- **Tick phase freeze**: `TickPhase` enum is frozen. The monitor is not a new phase
  — it is a hook within an existing phase (PERSISTENCE). No phase registration needed.
- **ResourceGovernor degradation**: `governance_logic.md` §3 specifies that
  SURVIVAL mode skips governance entirely. The monitor should be skipped when the
  governor is in SURVIVAL mode (check `self._status.current_mode`).
- **Gini formula (ticket-specified)**:
  `G = (2 * sum((i+1)*v for i,v in enumerate(sorted(values)))) / (n * sum(values)) - (n+1)/n`
  This matches the standard discrete Gini for sorted 1-indexed wealth vector.
  Edge cases: all-zero wealth → return 0.0; single entity → G = 0.0.

---

## Parity Ledger Overlap (IDs + status)

No existing entry in `docs/parity_ledger/town_resource.yaml` (TOWN-001 through
TOWN-176) covers macro-economy health metrics or Gini coefficient computation.

The closest relevant entries:
- **TOWN-008** (`verified`): "Replay and observability consume authoritative results
  rather than defining them." The EconomyHealthMonitor must follow this law — it
  reads state, never defines it.
- **TOWN-126/127/128** (`verified`): Item quantity/weight/identity preserved through
  all economic operations. Gold read by the monitor is authoritative.

**New parity entry required**: A `TOWN-177` (or next available ID) entry must be
added to `town_resource.yaml` after implementation:

```
id: TOWN-177
text: EconomyHealthMonitor samples gold distribution read-only once per WINDOW_SIZE
  ticks and writes EconomyHealthSnapshot to metric_windows.jsonl without mutating
  AuthoritativeState.
status: missing   # → verified after implementation
priority: P1
v2_evidence: null
test_path: tests/unit/economy/test_economy_health_monitor.py::test_gini_coefficient_computed_correctly
```

No infrastructure.yaml entries are directly affected (the monitor does not touch
replay or telemetry internals).

---

## Prior Work

**TCK-20260619-E12A-BALANCE-MEASURE** (`stored_artifacts/TCK-20260619-E12A-BALANCE-MEASURE/investigation.md`):
- Confirmed `MetricsService.extract_metrics(state) → WorldMetrics` with
  `total_gold: float` (sum across all entity inventories). This is the correct gold
  extraction pattern to reuse.
- Confirmed `state.entities` → entity dict, `state.resource_nodes` available.
- Confirmed that harvesting/crafting event counts are NOT tracked as
  `SimulationEvent` — they are processed but not logged. This means
  `transaction_velocity` (trades/tick) will have no event source to count from
  without a separate counter mechanism. The ticket marks this TODO.
- Confirmed `AdventureRouteOption.blockers` is strings-only — irrelevant to this
  ticket but contextually consistent.

The balance investigation also confirmed that `urban_political` world (27 entities,
seed 202) is the canonical test world for economic measurements.

---

## Risks and Open Questions

### Risk 1 — Gold access path mismatch (HIGH)
The ticket pseudocode reads:
```python
sum(stack.quantity for stack in e.inventory.items if stack.item_id == "gold_coin")
```
But the canonical gold wealth of an entity is `e.inventory.gold` (an `int` scalar,
`InventoryComponent.gold`). The `items` list holds stackable items (equipment,
materials, consumables); gold is tracked separately. The `"gold_coin"` item ID exists
as a physical item type (found in loot nodes) but is not how entities hold their
monetary wealth at runtime.

**Decision required**: Should `entity_gold` for Gini be:
  (a) `e.inventory.gold` — the authoritative scalar (recommended), or
  (b) `sum(stack.quantity for stack in e.inventory.items if stack.item_id in {"gold_coin","gold"})` — physical item stacks only, or
  (c) Both summed together?

Using option (a) aligns with how all other subsystems read wealth
(`cognition/capability_estimate.py` L222, `cognition/need_interpretation.py` L151,
`api/presenters/state_presenter.py` L59). **Recommended: use `e.inventory.gold`.**

### Risk 2 — Entity liveness attribute (HIGH)
`e.is_alive` does not exist. The correct path is `e.combat.alive`. The pseudocode
must be corrected before implementation.

### Risk 3 — transaction_velocity source (MEDIUM)
No event source exists for counting trades per tick/window. The ticket leaves this
as `TODO: count trades in window`. Implementation will need to either:
  (a) Leave it as 0.0 with a structured TODO, or
  (b) Hook into the shop/blacksmith resolution systems to emit a count (significant
  scope expansion), or
  (c) Proxy with `MetricsService` data if a trade-count field is added there.
This is explicitly out of scope for E33A per the ticket; it is not an AC blocker.

### Risk 4 — avg_price_index source (MEDIUM)
No per-commodity price index is tracked anywhere in current state. The ticket leaves
this as `TODO`. Implementation will write `{}` as the empty dict. Not an AC blocker.

### Risk 5 — Integration point ambiguity (MEDIUM)
The ticket says "wire into governance phase" but `governance_logic.md` defines
governance as a sub-phase of the `AuthoritativeApplyPipeline` (RESOLUTION phase
territory), and the tick phase enum is frozen. The safest integration point is the
PERSISTENCE phase alongside the existing `_metric_recorder.record_tick()` call
in kernel.py L381, or as a call inside `MetricsService.extract_metrics()`.

**Decision required**: Where should `EconomyHealthMonitor.sample()` be called?
  (a) Inside `MetricsService.extract_metrics()` — cleanest, no kernel change, output
  flows into existing MetricWindowRecord via `metrics_json` field, or
  (b) Directly in `_tick_once_inner` after `_metric_recorder.record_tick()` — requires
  kernel change but gives explicit control over output format.

Recommended: option (a) first; promote to (b) if AC requires a distinct
`metric_windows.jsonl` structure that `MetricWindowRecord` cannot accommodate.

### Risk 6 — Output format vs. existing metric_windows.jsonl (LOW)
The existing `metric_windows.jsonl` is written by `MetricWindowRecorder` and
consumed by the warehouse `ingest_run()` pipeline. Adding new fields via
`metrics_json` is backwards-compatible. A schema-breaking change (new top-level
keys in the JSONL line) would require a warehouse schema migration.

---

## Anti-Drift Hazards

1. **`e.is_alive` vs `e.combat.alive`**: If the pseudocode is copied verbatim, the
   monitor will raise `AttributeError` at runtime. Must correct before implementing.

2. **`gold_coin` item scan vs `inventory.gold` field**: The ticket's pseudocode
   would return 0 for most entities, producing a Gini of 0.0 regardless of actual
   wealth. This would silently pass tests if tests use the same wrong path.

3. **New `TickPhase` value**: The phase enum is FROZEN. Any attempt to add
   `TickPhase.GOVERNANCE_HEALTH` will break the phase contract. Do not add new
   phases.

4. **Durable state mutation**: `EconomyHealthSnapshot` must never be stored in
   `AuthoritativeState` fields. It is a transient computation result written only
   to JSONL. If stored in state, determinism tests will catch it but only at high cost.

5. **SURVIVAL mode skip**: If the monitor runs during SURVIVAL mode governance
   degradation, it reads a state where many entities may be in emergency conditions;
   results are valid but should be tagged. More importantly, the monitor must not
   block or raise when invoked during degraded mode — it is observability only.
