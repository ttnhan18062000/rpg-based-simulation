---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260701-SIMQ-EMIT-AGENCY2
artifact_type: plan
tags: [simq, agency, event-emission]
---

# Plan — TCK-20260701-SIMQ-EMIT-AGENCY2

---

## Decisions (Open Questions Resolved)

### Q1: AbandonmentEvaluator parameters in EventExtractor context

**Decision: Default both `is_party_in_combat=False` and `is_greed_driven=False`.**

Rationale: The dominant abandonment trigger is the rejection-backoff cascade
(`project.failure_count >= _MAX_CONSECUTIVE_REJECTIONS` in `intelligence.py:L1167`),
not party-combat betrayal. `VOLUNTARY_QUIT` (penalty=0.2) is the correct
classification for this path. Deriving `is_party_in_combat` accurately would require
O(N) neighbor inspection across faction members — this data is not available from the
entity's own state snapshot in EventExtractor. `is_greed_driven` has no typed home in
`ProjectState` today. Defaulting both to `False` routes all non-survival abandonment
(HP ratio >= 0.2) to `VOLUNTARY_QUIT`, which is correct for the cascade path.
`GREEDY_DESERTION` is deferred until `is_greed_driven` has a typed project-level field.

### Q2: defer_with_reason reason field source

**Decision: Read `result.selected.reason` directly from the DEFER route option in `phase.py`.**

Confirmed in `src/domains/adventure/service.py`: both DEFER paths set a non-None
`reason` string on the `AdventureRouteOption`:
- L60: `reason="No candidate routes generated."` (no candidates produced)
- L114: `reason="All candidates are blocked."` (all candidates blocked)

The phase instrumentation writes `result.selected.reason` (with `or "unknown"` fallback)
into the EntityUpdate's `property_updates["last_defer_reason"]`. EventExtractor reads
this exact key. No translation layer or intermediate field is needed.

### Q3: rejection_cascade_tick emission threshold

**Decision: Emit when total per-tick entity rejection count >= 20.**

The threshold is `_MAX_CONSECUTIVE_REJECTIONS = 20` from
`src/systems/strategic_systems/intelligence.py:L27`. The emitter imports this constant
(does not copy it). The scorer's own significance thresholds (100, 500) in
`agency.py:L114-128` are an independent concern at the scorer layer; events with
count in [20, 99] will reach the scorer and return None (no-op), which is acceptable.
Emit at >= 20 (per-project threshold reused as per-tick population signal) not >= 1,
so the event has meaningful signal even when the scorer ignores low-count ticks.

---

## Scope Guards (Do NOT Touch)

- Do not change `AdventureDecisionService.decide()` routing logic.
- Do not change `AgencyScorer` weights or scoring ranges.
- Do not make `seen_routing_families` durable (it must NOT appear in `EntityUpdate`,
  `AuthoritativeState`, or any persistent store).
- Do not suppress or replace the existing `QuestEvent` emission for ACTIVE→ABANDONED
  transitions — `commitment_abandoned` co-exists with `project_abandoned`.
- Do not modify `AbandonmentEvaluator.evaluate_abandonment()` signature or logic.
- Do not modify `StrategicIntelligenceSystem` or `fused_strategic_pass()` for
  `rejection_cascade_tick` — use EventExtractor post-loop aggregation (Option A from
  investigation).
- Do not run `pytest tests/` (full suite). Scope to listed commands only.

---

## Ordered Implementation Steps

---

### Step 1 — Regression Baseline

**Purpose**: Confirm all existing tests pass before touching any code. Gate: all green.

**Files changed**: none.

**Command**:
```
pytest tests/unit/observability/test_event_extractor_agency.py \
       tests/unit/strategic/test_rejection_backoff.py \
       tests/simulation_quality/test_agency_scorer.py \
       tests/simulation_quality/test_timegate_penalties.py \
       -v --tb=short
```

**Accept when**: 0 failures, 0 errors.

---

### Step 2 — phase.py: Write defer signal before `continue`

**Purpose**: Make the DEFER path visible to EventExtractor by writing a minimal
`EntityUpdate` into `entity_updates` before the `continue` statement. This is pure
observability instrumentation; it does not alter routing decisions.

**File**: `src/domains/adventure/phase.py`

**Change** (at L114-116, replacing the bare `continue`):
```python
# If deferred, record the deferral signal for observability before skipping.
if not result.selected or result.selected.family == RouteFamily.DEFER_WITH_REASON:
    if result.selected and result.selected.family == RouteFamily.DEFER_WITH_REASON:
        entity_updates[hero.id] = EntityUpdate(
            entity_id=hero.id,
            property_updates={
                "last_defer_reason": result.selected.reason or "unknown",
                "last_defer_tick": tick,
            },
        )
    continue
```

**Constraints**:
- The property key `"last_defer_reason"` is the canonical signal name. It must match
  exactly what EventExtractor reads (Step 3). Add an inline comment cross-referencing
  `event_extractor.py` so a rename triggers a visible code review.
- Do not create an `EntityUpdate` when `result.selected` is None (no selection at all)
  — only on explicit `DEFER_WITH_REASON`.

**Verification**: After this step, a simulated DEFER route in a unit test produces an
`EntityUpdate` with `property_updates["last_defer_reason"]` set. Step 2 is verifiable
in isolation before EventExtractor changes.

**Depends on**: Step 1.

---

### Step 3 — event_extractor.py: `defer_with_reason` emission + update old test

**Purpose**: Detect the `last_defer_reason` property in the existing `e_upd_ext` block
and emit `defer_with_reason`. Update one existing test that documented the old gap.

**File**: `src/observability/event_extractor.py`

**Change A** — Add `defer_with_reason` detection after the `route_selected` block
(L191-204). Place immediately after the `if routing_family:` block, before the
`self_model_updated` check:
```python
# Agency: defer_with_reason
defer_reason = prop.get("last_defer_reason")
if defer_reason:
    events.append(SimulationEvent(
        event_type="defer_with_reason", event_category="strategy",
        tick=tick, entity_id=eid, severity="INFO",
        source_system="event_extractor", message="",
        payload={"entity_id": eid, "reason": defer_reason, "tick": tick},
    ))
```

**Change B** — Update `test_defer_gap_no_update_means_no_agency_event()` in
`tests/unit/observability/test_event_extractor_agency.py`:
- The test currently documents the gap (no event emitted). After Step 2+3, this test
  name/assertion is stale. Rename to `test_defer_without_property_produces_no_event()`
  and update the setup to NOT include `last_defer_reason` in `property_updates`,
  confirming the emitter only fires when the property is present.

**Constraints**:
- `defer_with_reason` must NOT fire when `last_routing_family` is set (normal route
  selected path). The mutually exclusive property usage enforces this naturally.
- Property key `"last_defer_reason"` must match Step 2 exactly. If renamed, both files
  must change together.

**Verification**: Run:
```
pytest tests/unit/observability/test_event_extractor_agency.py -v
```
All existing tests pass with the updated test name/assertion.

**Depends on**: Step 2.

---

### Step 4 — event_extractor.py: `_seen_routing_families` + `reset_run_state()` + `route_family_first_use`

**Purpose**: Add per-run class-level novelty tracking for routing families, provide a
reset mechanism for test isolation, and emit `route_family_first_use` on first encounter.

**File**: `src/observability/event_extractor.py`

**Change A** — Add class-level state to `EventExtractor`:
```python
class EventExtractor:
    """Extracts curated low-volume SimulationEvents from state changes and committed updates."""

    # Per-run tracking for route novelty: entity_id → set of seen family strings.
    # NOT durable state — must be cleared at run start via reset_run_state().
    _seen_routing_families: dict[int, set[str]] = {}

    @classmethod
    def reset_run_state(cls) -> None:
        """Clear transient per-run state. Call at run start and in test teardown."""
        cls._seen_routing_families.clear()
```

**Change B** — Add `route_family_first_use` check immediately after the existing
`route_selected` / `action_executed` emission block (after L204):
```python
# Agency: route_family_first_use (once per novel family per entity per run)
seen = EventExtractor._seen_routing_families.setdefault(eid, set())
if routing_family not in seen:
    seen.add(routing_family)
    events.append(SimulationEvent(
        event_type="route_family_first_use", event_category="strategy",
        tick=tick, entity_id=eid, severity="INFO",
        source_system="event_extractor", message="",
        payload={"entity_id": eid, "family": routing_family, "tick": tick},
    ))
```

This block sits inside the `if routing_family:` guard, so it only fires when a real
route (not a defer) was selected.

**Constraints**:
- `_seen_routing_families` must be class-level (`dict[int, set[str]]`), not instance
  state (EventExtractor is a static-method-only class).
- `route_family_first_use` must only fire alongside `route_selected` — it is nested
  inside the `if routing_family:` block, not adjacent to `defer_with_reason`.
- `reset_run_state()` must clear the dict (`.clear()`), not reassign it, to avoid
  reference aliasing issues.
- **Wiring**: `EventExtractor.reset_run_state()` must be called from `Kernel.__init__()`
  in `src/engine/kernel.py` at L307, just before `self.validate(flags)` at L308.
  Add a local import inside `__init__` at that location:
  `from src.observability.event_extractor import EventExtractor`. The call must be
  unconditional (not gated on `obs_mode`) to guarantee test isolation even when
  observability is disabled. One Kernel instance = one simulation run, so
  `__init__` is the correct and only per-run reset site.

**Verification**: Run:
```
pytest tests/unit/observability/test_event_extractor_agency.py -v
```
Existing tests still pass (route_selected behavior unchanged).

**Depends on**: Step 3.

---

### Step 5 — event_extractor.py: `commitment_abandoned` emission

**Purpose**: After the existing ACTIVE→status QuestEvent emission block, detect
ACTIVE→ABANDONED project transitions, classify via `AbandonmentEvaluator` with
defaulted params (Q1 decision), and emit `commitment_abandoned` for non-survival cases.

**File**: `src/observability/event_extractor.py`

**Change A** — Add import at top of file:
```python
from src.domains.commitment.abandonment import AbandonmentEvaluator, AbandonmentCategory
from src.core.strategic import ProjectStatus
```

**Change B** — Extend the Quest progress block (L425-439). After the existing
`elif prior_qstate.status != qstate.status: events.append(QuestEvent(...))` branch,
add:
```python
                # Agency: commitment_abandoned (behavioral classification, not just
                # status change — coexists with the QuestEvent above which becomes
                # project_abandoned via _TRANSLATE_CONDITIONAL in quality_hub.py)
                if (prior_qstate is not None
                        and getattr(prior_qstate, "status", None) != ProjectStatus.ABANDONED
                        and getattr(qstate, "status", None) == ProjectStatus.ABANDONED):
                    _hp = getattr(getattr(entity, "combat", None), "hp", 100)
                    _max_hp = getattr(getattr(entity, "combat", None), "max_hp", 100)
                    _classification = AbandonmentEvaluator.evaluate_abandonment(
                        _hp, _max_hp,
                        is_party_in_combat=False,   # Q1: default; see plan decisions
                        is_greed_driven=False,       # Q1: default; see plan decisions
                    )
                    if _classification.category != AbandonmentCategory.SURVIVAL:
                        events.append(SimulationEvent(
                            event_type="commitment_abandoned", event_category="strategy",
                            tick=tick, entity_id=eid, severity="INFO",
                            source_system="event_extractor", message="",
                            payload={
                                "entity_id": eid,
                                "project_id": qid,
                                "category": _classification.category.value,
                                "penalty": _classification.penalty,
                                "tick": tick,
                            },
                        ))
```

**Constraints**:
- The existing `QuestEvent` for ACTIVE→ABANDONED must remain. Do not remove or
  conditionally suppress it. `commitment_abandoned` is additive.
- Payload `category` must use `.value` (string), not the enum object, per anti-drift
  hazard note in investigation.
- `ProjectStatus.ABANDONED` must be imported; do not hardcode the string `"ABANDONED"`.
- HP access uses `getattr` with safe defaults (100/100) to avoid AttributeError if the
  entity's combat component is absent.

**Verification**: Isolated check — HP < 20% of max → no `commitment_abandoned`; HP >= 20% → emitted.

**Depends on**: Step 1 (independent of Steps 2-4, ordered here for sequential clarity).

---

### Step 6 — event_extractor.py: `rejection_cascade_tick` post-entity-loop emission

**Purpose**: After the main entity loop and before the resource node depletion block,
add a population-level aggregation pass that counts total rejected intent results and
emits one `rejection_cascade_tick` per tick when count >= `_MAX_CONSECUTIVE_REJECTIONS`.

**File**: `src/observability/event_extractor.py`

**Change A** — Add import at top (with other strategic imports):
```python
from src.systems.strategic_systems.intelligence import _MAX_CONSECUTIVE_REJECTIONS
```

**Change B** — Insert after the end of the `for eid in dirty_entity_ids:` loop,
immediately before the `# Resource node depletion and regeneration` comment (L441):
```python
        # Agency: rejection_cascade_tick — post-entity-loop population aggregate.
        # Count all rejected intent results across entities in this tick's updates.
        _total_rejections = 0
        _reason_counts: dict[str, int] = {}
        _all_upd = getattr(update, "entity_updates", {}) or {}
        for _e_upd in _all_upd.values():
            for _ir in (getattr(_e_upd, "intent_results", None) or []):
                if not getattr(_ir, "accepted", True):
                    _total_rejections += 1
                    _r = getattr(_ir, "reason", None) or "unknown"
                    _reason_counts[_r] = _reason_counts.get(_r, 0) + 1
        if _total_rejections >= _MAX_CONSECUTIVE_REJECTIONS:
            _dominant = max(_reason_counts, key=_reason_counts.__getitem__) if _reason_counts else "unknown"
            events.append(SimulationEvent(
                event_type="rejection_cascade_tick", event_category="strategy",
                tick=tick, entity_id=None, severity="WARNING",
                source_system="event_extractor", message="",
                payload={
                    "count": _total_rejections,
                    "tick": tick,
                    "dominant_failure_reason": _dominant,
                },
            ))
```

**Constraints**:
- Emit at most once per tick (no per-entity loop — this is a single post-loop block).
- Import `_MAX_CONSECUTIVE_REJECTIONS` from `intelligence.py`; do not hardcode `20`.
- `entity_id=None` on the event (population-level, not entity-scoped).
- Payload key must be `"count"` — confirmed by reading `src/simulation_quality/scorers/agency.py:L115`
  which reads `payload.get("count", 0)`. Do NOT use `"rejection_count"`.
- Safe `getattr` access for `intent_results` to handle EntityUpdates that lack this
  field.

**Verification**: Run:
```
pytest tests/unit/strategic/test_rejection_backoff.py -v
```
Rejection backoff logic in `intelligence.py` must be unaffected (EventExtractor
changes are read-only with respect to authoritative state).

**Depends on**: Step 1 (independent of Steps 2-5).

---

### Step 7 — Write new unit test file: `test_event_extractor_agency2.py`

**Purpose**: Cover all 4 new event types with unit tests matching the test plan's
Groups A–D plus the 5 anti-drift guards.

**File**: `tests/unit/observability/test_event_extractor_agency2.py` (new file)

**Contents** (by test group, in order):

**Group A — defer_with_reason** (4 tests):
- A-1: `test_defer_with_reason_emitted_when_property_set` — EntityUpdate with
  `property_updates={"last_defer_reason": "no_viable_route", "last_defer_tick": 5}` →
  one `defer_with_reason` event with `reason=="no_viable_route"`.
- A-2: `test_defer_with_reason_not_emitted_without_defer_property` — `property_updates={}`
  → no `defer_with_reason`.
- A-3: `test_defer_with_reason_not_emitted_when_routing_present` — `property_updates={"last_routing_family": "recover"}` → no `defer_with_reason`.
- A-4: `test_defer_with_reason_payload_structure` — payload has `entity_id`, `reason`,
  `tick`; `event_category == "strategy"`.

**Group B — commitment_abandoned** (5 tests):
- B-1: ACTIVE→ABANDONED, HP 80/100 → `commitment_abandoned` with `category=="voluntary_quit"`.
- B-2: ACTIVE→ABANDONED, HP 15/100 → no `commitment_abandoned` (survival filtered).
- B-3: ACTIVE→COMPLETED → no `commitment_abandoned`.
- B-4: HP 50/100 → payload `category` is `str`, value in `{"voluntary_quit", "greedy_desertion"}`.
- B-5: ACTIVE→ABANDONED, HP >= 20% → both `commitment_abandoned` AND a `QuestEvent` present.

**Group C — rejection_cascade_tick** (5 tests):
- C-1: 25 entities each with 1 rejected intent_result → one `rejection_cascade_tick`, `count >= 20`.
- C-2: 5 entities each with 1 rejected result → no event (5 < 20).
- C-3: 100 entities each with 3 rejected results → exactly one `rejection_cascade_tick`.
- C-4: 30 entities, 20 with reason `"INSUFFICIENT_CAPACITY"`, 10 with `"OUT_OF_STOCK"` →
  `dominant_failure_reason == "INSUFFICIENT_CAPACITY"`.
- C-5: all `accepted=True` → no event.

**Group D — route_family_first_use** (5 tests; each calls `EventExtractor.reset_run_state()` in setup):
- D-1: first use of `"gather_resource"` for entity 1 → one `route_family_first_use`, `family=="gather_resource"`.
- D-2: same entity, same family called twice → only first call emits.
- D-3: entity 1, call with `"gather_resource"` then `"recover"` → both emit.
- D-4: entity 1 and entity 2 each first-use `"gather_resource"` → both emit.
- D-5: use family, call `reset_run_state()`, use same family → emits again.

**Anti-drift guards** (5 tests):
- Guard 1: `"last_defer_reason"` appears in both `phase.py` source and `event_extractor.py` source.
- Guard 2: `EventExtractor.reset_run_state()` exists and runs without error.
- Guard 3: ACTIVE→ABANDONED with HP >= 20% produces both `commitment_abandoned` and
  a `QuestEvent` in the same event list.
- Guard 4: `AbandonmentCategory.SURVIVAL.value=="survival"`,
  `VOLUNTARY_QUIT.value=="voluntary_quit"`, `GREEDY_DESERTION.value=="greedy_desertion"`.
- Guard 5: `_MAX_CONSECUTIVE_REJECTIONS == 20` (import from `intelligence.py`, assert value).

**Run command (incremental)**:
```
# Group A
pytest tests/unit/observability/test_event_extractor_agency2.py -k "defer" -v
# Group B
pytest tests/unit/observability/test_event_extractor_agency2.py -k "commitment" -v
# Group C
pytest tests/unit/observability/test_event_extractor_agency2.py -k "cascade" -v
# Group D
pytest tests/unit/observability/test_event_extractor_agency2.py -k "route_family" -v
# Full file
pytest tests/unit/observability/test_event_extractor_agency2.py -v
```

**Depends on**: Steps 2, 3, 4, 5, 6.

---

### Step 8 — Add scorer tests to `test_agency_scorer.py`

**Purpose**: Verify AgencyScorer handles the 4 new event types correctly (positive-
and no-op paths).

**File**: `tests/simulation_quality/test_agency_scorer.py` (existing — add to it)

**Tests** (E-1 through E-5):
- E-1: `defer_with_reason` envelope → `ScoreRecord` with `pillar=PillarId.AGENCY`, `delta < 0` (`defer_idle` weight is negative).
- E-2: `commitment_abandoned` → returns `None` (scorer intentionally no-ops).
- E-3: `rejection_cascade_tick` with `payload={"count": 501}` → `ScoreRecord` tagged `"rejection_cascade_sustained"`.
- E-4: `rejection_cascade_tick` with `payload={"count": 150}` → `ScoreRecord` tagged `"rejection_cascade"`.
- E-5: `route_family_first_use` with `payload={"family": "recover", "entity_id": 1}` → `ScoreRecord` with tags containing `"route_novelty"` and `"entropy_reward"`.

Note: Tests E-3 and E-4 use payload key `"count"` — this is the confirmed emitter key
(Step 6 Change B uses `"count"`) and the confirmed scorer key (`agency.py:L115` reads
`payload.get("count", 0)`). Both sides are aligned; no further key reconciliation is needed.

**Run command**:
```
pytest tests/simulation_quality/test_agency_scorer.py -v
```

**Depends on**: Steps 3, 4, 5, 6.

---

### Step 9 — Update `event_type_coverage.md §3.1`

**Purpose**: Remove the 4 gap rows from §3.1 since all emitters are now implemented.

**File**: `docs/simulation_quality/event_type_coverage.md`

**Change**: Delete rows for `defer_with_reason`, `commitment_abandoned`,
`rejection_cascade_tick`, `route_family_first_use` from §3.1 (currently at L148-151).
If §3.1 becomes empty after removal, replace the table with a note:
`> All AGENCY pillar events are now emitted. See §2 for covered events.`

**Depends on**: Steps 3, 4, 5, 6 (all 4 emitters implemented).

---

### Step 10 — Update parity ledger: `infrastructure.yaml`

**Purpose**: Extend `SIMQ-CALIBRATED-001` v2_evidence to include this ticket and
the 4 new event types. Status remains `verified`.

**File**: `docs/parity_ledger/infrastructure.yaml`

**Change**: Locate entry with `id: SIMQ-CALIBRATED-001`. In its `v2_evidence` field,
append:
```
TCK-20260701-SIMQ-EMIT-AGENCY2: adds defer_with_reason, commitment_abandoned,
  rejection_cascade_tick, route_family_first_use emitters; all 4 tested in
  tests/unit/observability/test_event_extractor_agency2.py
```

No status change — entry remains `verified`. No new parity entries needed (the
AgencyScorer parity entry already covers scorer behavior for all event types; this
ticket only unlocks emission).

**Depends on**: Step 9.

---

### Step 11 — Final Regression Run

**Purpose**: Confirm no regression across all affected domains.

**Command**:
```
pytest -m "not slow" \
       tests/unit/observability/ \
       tests/simulation_quality/ \
       tests/unit/strategic/test_rejection_backoff.py \
       -v --tb=short
```

**Accept when**: 0 failures, 0 errors. All new tests (test_event_extractor_agency2.py)
pass. All existing tests in `test_event_extractor_agency.py` pass with the updated
`test_defer_gap` test name/assertion.

**Depends on**: Steps 7, 8, 9, 10.

---

## Dependency Map

```
Step 1 (baseline)
  └─► Step 2 (phase.py defer write)
        └─► Step 3 (extractor defer_with_reason + update old test)
              └─► Step 4 (seen_routing_families + route_family_first_use)

Step 1 ──────────► Step 5 (commitment_abandoned)

Step 1 ──────────► Step 6 (rejection_cascade_tick)

Steps 2+3+4+5+6 ─► Step 7 (new test file — all groups)
Steps 3+4+5+6 ───► Step 8 (scorer tests)

Steps 3+4+5+6 ───► Step 9 (event_type_coverage.md update)
Step 9 ──────────► Step 10 (parity ledger update)

Steps 7+8+9+10 ──► Step 11 (final regression)
```

Steps 5 and 6 are independent of Steps 2–4 and may be executed in parallel with them,
but must be completed before Steps 7, 8, 9.

---

## Acceptance Criteria → Step Mapping

| AC | Steps |
|---|---|
| All 4 event types emitted under correct conditions | 2, 3, 4, 5, 6 |
| `commitment_abandoned` payload uses `AbandonmentClassification` fields (typed) | 5 |
| `rejection_cascade_tick` fires at most once per tick (population aggregate, entity_id=None) | 6, C-3 |
| `route_family_first_use` fires exactly once per novel family per entity per run | 4, D-1/D-2 |
| `event_type_coverage.md §3.1` updated — 4 entries removed | 9 |
| No regression in existing agency / routing tests | 1, 11 |

---

## Files to Change

| File | Step(s) | Nature |
|---|---|---|
| `src/domains/adventure/phase.py` | 2 | Add defer EntityUpdate before `continue` |
| `src/observability/event_extractor.py` | 3, 4, 5, 6 | Add 4 emitters + class state + import |
| `tests/unit/observability/test_event_extractor_agency.py` | 3 | Update 1 existing test name/assertion |
| `tests/unit/observability/test_event_extractor_agency2.py` | 7 | New file — 19 tests + 5 guards |
| `tests/simulation_quality/test_agency_scorer.py` | 8 | Add 5 scorer tests |
| `docs/simulation_quality/event_type_coverage.md` | 9 | Remove 4 §3.1 rows |
| `docs/parity_ledger/infrastructure.yaml` | 10 | Extend SIMQ-CALIBRATED-001 v2_evidence |

---

## Pre-implementation Verification Note

~~Before writing any code, confirm the scorer payload key for `rejection_cascade_tick`
by reading `src/simulation_quality/scorers/agency.py:L114`. If the scorer reads
`payload.get("count")` (not `payload.get("rejection_count")`), use `"count"` as
the emitter key in Step 6 and the test payloads in Step 8.~~

**Resolved (architecture review 2026-07-01):** Scorer confirmed at
`src/simulation_quality/scorers/agency.py:L115` reads `payload.get("count", 0)`.
Step 6 and Step 8 have been updated accordingly. No open question remains.

---

## Corrections from Architecture Review (2026-07-01)

Three violations were identified and corrected before implementation began.

### Correction 1 — Step 6 payload key mismatch
- **Before**: Step 6 Change B used `"rejection_count"` as the payload key while the
  scorer at `agency.py:L115` reads `payload.get("count", 0)`. The constraints section
  marked this as an open check ("Scorer key check required before writing").
- **After**: Key changed to `"count"` in Step 6 Change B. Constraints updated to state
  definitively that `"count"` is the required key (confirmed, not pending). Step 8 Note
  updated to reflect confirmed alignment.

### Correction 2 — reset_run_state() wiring point unspecified
- **Before**: Step 4 described `reset_run_state()` as "must be cleared at run start"
  without naming the exact call site.
- **Investigation**: `src/engine/kernel.py` reviewed. `EventExtractor.extract()` is
  called in `Kernel._phase_observability()` (L815) per tick. There is no dedicated
  `_init_run()` method. One `Kernel` instance = one simulation run. `Kernel.__init__()`
  is the correct per-run entry point.
- **After**: Step 4 Constraints now specify: call `EventExtractor.reset_run_state()`
  from `Kernel.__init__()` at `src/engine/kernel.py:L307` (just before
  `self.validate(flags)` at L308), unconditionally, with a local import.

### Correction 3 — Ticket AC wording
- **Before**: AC said "`rejection_cascade_tick` fires at most once per entity per tick"
  — incorrect because this is a population aggregate with `entity_id=None`, not a
  per-entity event.
- **After**: AC in ticket and in the AC → Step Mapping table now reads "fires at most
  once per tick (population aggregate, entity_id=None)".

### Deviations from original plan
None. All corrections are pre-implementation clarifications that resolve ambiguity;
no scope, behavior, or architecture decisions were changed.
