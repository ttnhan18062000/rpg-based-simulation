---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-SOCIAL-FACTION
artifact_type: plan
tags: [simq, event-extractor, social, faction, diplomatic]
---

# Plan: TCK-20260629-SIMQ-EMIT-SOCIAL-FACTION

---

## Decisions

### D1: `alliance_proposed` — SCOPED OUT (architectural gap)
`faction_directives` is a local list in `pipeline.py:L171` consumed only by
`AdventureDecisionPhase`. It is never serialized into `StateUpdate`. EventExtractor
cannot emit `alliance_proposed`. Same architectural pattern as AGENCY ticket's
`defer_with_reason`. Documented via gap test F-23. Removed from AC.

### D2: `resource_seized` — SCOPED OUT (no distinct WorldEvent)
`MilitaryConflictPhase` emits `TERRITORY_TRANSFERRED` when siege_progress >= 1.0,
but there is no separate `resource_seized` `WorldEvent` in the pipeline output.
`TERRITORY_TRANSFERRED` covers region-ownership transfer, not per-resource granularity.
Blocked pending `WorldEvent` schema extension. Documented via gap test F-24.

### D3: `contract_milestone_completed` — SCOPED OUT (no field in ContractState)
`ContractState` (`src/core/strategic.py:L177`) has no milestone or progress tracking
field. Cannot be detected from state diff. Same pattern as `commitment_abandoned` in
AGENCY ticket. Documented via gap test S-23.

### D4: `social_memory_created` — SCOPED OUT (no persisted field)
No `social_memories` field exists in `src/core/strategic.py` (confirmed by grep).
`CooperationPhase` appends to `entity.timeline`, a transient in-memory buffer never
reaching `StateUpdate`. Undetectable from state diff. Documented via gap test S-24.

### D5: `diplomatic_transition` deduplication — one event per pair
`compute_transitions()` produces one `FactionUpdate` per faction in the pair (faction A
and faction B each carry the same relation in their `diplomatic_relations_set`). To
avoid double-emit, use canonical ordering: only emit the event when
`upd.faction_id < other_faction_id` (string comparison). Guarantees exactly one event
per ordered pair per tick. See test F-03.

### D6: `faction_extinct` cost guard — only when faction_updates non-empty
Detecting extinct factions requires iterating all entities (O(N)). Guard with
`if not update.faction_updates: skip` to bound tick-level cost. Extinctions only
coincide with ticks where faction state changed, making this safe to skip otherwise.

### D7: `betrayal_desertion` → conditional translation
`BetrayalDesertionEvent` (`src/observability/events.py:L302`) payload may carry
`faction_id` (faction-related desertion) or `contract_id` (contract breach). Add a
`_translate_betrayal_desertion()` function in `quality_hub.py`: if `faction_id` in
payload → `faction_tension_delta`; otherwise → `contract_lapsed`. EVENT-TRANSLATE
ticket (TCK-20260629-SIMQ-EVENT-TRANSLATE) is already DONE and did not cover this;
this ticket adds the mapping directly to `quality_hub.py`.

### D8: `leadership_changed` → `diplomatic_transition`
Simple 1:1 mapping. Added to `_TRANSLATE_SIMPLE` in `quality_hub.py`. EVENT-TRANSLATE
ticket did not cover this; added here per ticket AC.

### D9: `alliance_formed` → `alliance_accepted`
Engine may emit `alliance_formed` as a standalone event type (separate from the
FACTION_ALLIANCE_FORMED WorldEvent path). Add to `_TRANSLATE_SIMPLE` as a safety net;
the primary detection path is EventExtractor reading `diplomatic_relations_set` → ALLIED.

### D10: `faction_tension_delta` threshold — any non-zero delta
`quality_scoring_contract.md §FACTION` does not specify a threshold for
`faction_tension_delta`. Use `tension_delta != 0.0` (any non-zero delta), consistent
with how `xp_granted` uses any positive delta. The scorer handles significance weighting
internally.

---

## Files to Change

| File | Role |
|---|---|
| `src/observability/event_extractor.py` | Primary implementation: all SOCIAL and FACTION event emission |
| `src/simulation_quality/quality_hub.py` | Translation mappings: `leadership_changed`, `betrayal_desertion`, `alliance_formed` |
| `tests/unit/observability/test_event_extractor_social_faction.py` | NEW: all S-01..S-24 and F-01..F-24 test cases |
| `docs/parity_ledger/infrastructure.yaml` | Update SIMQ-CALIBRATED-001 (L3075) with SOCIAL+FACTION pillar status |

## Scope Guards — What NOT to Touch

- `src/domains/cooperation/phase.py` — no SimQ emission inside domain phases
- `src/domains/faction/diplomatic_state_machine.py` — no changes; already produces WorldEvents
- `src/domains/faction/military_conflict.py` — no changes
- `src/domains/faction/faction_decision.py`, `faction_awareness.py` — no changes
- `src/core/strategic.py`, `src/core/updates.py`, `src/core/state.py` — read-only; no field additions
- `src/pipeline/pipeline.py` — no changes; `faction_directives` gap is deliberate
- Any event_extractor lines below L354 (quest, resource_node, world_updates, entities_add)
  unless explicitly listed in a step below
- Do not import from `src/simulation_quality/` in EventExtractor or any domain phase

---

## Ordered Steps

---

### Step 1 — Baseline: Run existing regression suite (no file changes)

**Purpose:** Confirm green baseline before any edits.

**Command:**
```bash
pytest tests/unit/observability/test_event_extractor_simq.py \
       tests/unit/observability/test_event_extractor_agency.py \
       tests/unit/observability/test_event_extractor_cognition.py \
       tests/unit/observability/test_event_extractor_economy.py \
       tests/unit/observability/test_event_extractor_world.py \
       -v
```

**Acceptance:** All existing tests pass. Record count. Stop if any are red — investigate
before proceeding.

**Files changed:** none
**Dependencies:** none

---

### Step 2 — Fix contract diff block in event_extractor.py

**File:** `src/observability/event_extractor.py`
**Edit region:** L321-L353 (the `# Social: contract lifecycle events` block)

**Changes (in order within the block):**

**2a. Add `contract_offer_created` for new contracts**

The current `if prior_cs is None: continue` discards new contracts entirely.
Replace with: if `prior_cs is None` AND the contract's status name is `"OFFERED"`,
emit `contract_offer_created`; then `continue` (no further diff check for new contracts).

```python
if prior_cs is None:
    new_status = getattr(getattr(cs, "status", None), "name",
                         str(getattr(cs, "status", "")))
    if new_status == "OFFERED":
        events.append(SimulationEvent(
            event_type="contract_offer_created", event_category="social",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="event_extractor", message="",
            payload={"contract_id": cid},
        ))
    continue
```

**2b. Fix `contract_completed` enum alias bug**

`ContractStatus.COMPLETED` is an alias for `FULFILLED`; `.name` always returns
`"FULFILLED"`, never `"COMPLETED"`. Change:
```python
elif curr_status == "COMPLETED":   # BEFORE (never matches)
```
to:
```python
elif curr_status == "FULFILLED":   # AFTER (correct canonical name)
```

**2c. Split `contract_lapsed` vs `contract_expired_offer` by prior status**

Change:
```python
elif curr_status == "EXPIRED":
    events.append(SimulationEvent(event_type="contract_lapsed", ...))
```
to:
```python
elif curr_status == "EXPIRED":
    if prior_status == "ACTIVE":
        events.append(SimulationEvent(event_type="contract_lapsed", ...))
    elif prior_status == "OFFERED":
        events.append(SimulationEvent(event_type="contract_expired_offer", ...))
```

**2d. Add removal detection for `reap_expired_offers()` path**

After the `for cid, cs in curr_contracts.items()` loop, add a second loop to detect
contracts present in `prior_contracts` but absent from `curr_contracts`:

```python
# PP-36: contract_expired_offer from reap path (contract removed entirely)
for cid, prior_cs in prior_contracts.items():
    if cid in curr_contracts:
        continue
    prior_status = getattr(getattr(prior_cs, "status", None), "name",
                           str(getattr(prior_cs, "status", "")))
    if prior_status == "OFFERED":
        events.append(SimulationEvent(
            event_type="contract_expired_offer", event_category="social",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="event_extractor", message="",
            payload={"contract_id": cid},
        ))
```

**Acceptance:** Steps 2a-2d each independently verifiable by the test cases in
§2.2-2.6 of the test plan (S-04..S-16). Existing `contract_offer_accepted` tests
(S-07, S-08) must still pass unchanged.

**Files changed:** `src/observability/event_extractor.py`
**Dependencies:** Step 1 (baseline green)

---

### Step 3 — Add `cooperation_event` and `reputation_delta` in entity loop

**File:** `src/observability/event_extractor.py`

**3a. `cooperation_event` (PP-05)**

Insert inside the `if e_upd_ext:` block that already reads `prop = e_upd_ext.property_updates`,
after the existing `belief_assimilated` / `belief_updated` block (around L215):

```python
# Social: cooperation_event (PP-05)
if prop.get("last_cooperation_decision") is not None:
    events.append(SimulationEvent(
        event_type="cooperation_event", event_category="social",
        tick=tick, entity_id=eid, severity="INFO",
        source_system="event_extractor", message="",
        payload={"entity_id": eid,
                 "decision": str(prop["last_cooperation_decision"])},
    ))
```

**3b. `reputation_delta` (PP-18)**

Insert after the group_joined/group_expelled block (after L319), still inside the
`for eid in dirty_eids:` entity loop, guarded by the same `hasattr` pattern:

```python
# Social: reputation_delta (PP-18, significant public reputation change)
if hasattr(entity, "social") and hasattr(prior_ent, "social"):
    curr_rep = getattr(entity.social, "public_reputation", 0.0)
    prior_rep = getattr(prior_ent.social, "public_reputation", 0.0)
    delta = curr_rep - prior_rep
    if abs(delta) > 0.05:
        events.append(SimulationEvent(
            event_type="reputation_delta", event_category="social",
            tick=tick, entity_id=eid, severity="INFO",
            source_system="event_extractor", message="",
            payload={"entity_id": eid, "delta": round(delta, 6)},
        ))
```

**Acceptance:** Tests S-01..S-03 (cooperation_event) and S-17..S-20 (reputation_delta).
Must not affect existing agency/cognition event tests that share the `prop` block.

**Files changed:** `src/observability/event_extractor.py`
**Dependencies:** Step 1. Independent of Step 2.

---

### Step 4 — Add faction_updates loop (diplomatic, alliance, territory, tension)

**File:** `src/observability/event_extractor.py`

Add a new section after the `calamity_spawned` / `entities_add` block (after the
`boss_spawned`/`raid_party_spawned` block at ~L440), before `return events`.

**Imports to add** (at top of file if not already present):
- `from src.core.updates import FactionUpdate` (likely already imported; verify)
- Need access to `DiplomaticState` enum. Import from wherever `FactionUpdate`
  references it: `from src.domains.faction.diplomatic_state_machine import DiplomaticState`
  (verify exact import path from `updates.py` header).

**New block — faction_updates loop:**

```python
# Faction events from FactionUpdate records (PP-08/09/10/11)
_seen_diplo_pairs: set[frozenset] = set()
for upd in (getattr(update, "faction_updates", None) or []):
    fid = upd.faction_id

    # FACTION: diplomatic_transition (PP-10) — one event per ordered pair
    for other_fid, new_state in (upd.diplomatic_relations_set or {}).items():
        pair = frozenset({fid, other_fid})
        if pair not in _seen_diplo_pairs:
            _seen_diplo_pairs.add(pair)
            events.append(SimulationEvent(
                event_type="diplomatic_transition", event_category="faction",
                tick=tick, entity_id=None, severity="INFO",
                source_system="event_extractor", message="",
                payload={
                    "faction_id": fid,
                    "target_faction_id": other_fid,
                    "new_state": str(new_state),
                },
            ))
            # FACTION: alliance_accepted (PP-08/10) — when new state is ALLIED
            if str(new_state).upper() in ("ALLIED", "DIPLOMATICSTATE.ALLIED"):
                events.append(SimulationEvent(
                    event_type="alliance_accepted", event_category="faction",
                    tick=tick, entity_id=None, severity="INFO",
                    source_system="event_extractor", message="",
                    payload={"faction_id": fid, "partner_id": other_fid},
                ))

    # FACTION: territory_ownership_changed (PP-11)
    for region_id in (upd.territory_add or ()):
        events.append(SimulationEvent(
            event_type="territory_ownership_changed", event_category="faction",
            tick=tick, entity_id=None, severity="WARNING",
            source_system="event_extractor", message="",
            payload={"faction_id": fid, "region_id": region_id},
        ))

    # FACTION: faction_tension_delta (PP-09) — any non-zero delta
    if getattr(upd, "tension_delta", 0.0) != 0.0:
        events.append(SimulationEvent(
            event_type="faction_tension_delta", event_category="faction",
            tick=tick, entity_id=None, severity="INFO",
            source_system="event_extractor", message="",
            payload={"faction_id": fid, "delta": upd.tension_delta},
        ))
```

**Note on `alliance_accepted` detection:** The DiplomaticState enum `.name` or `.value`
must be checked. Use `str(new_state)` and check for the `ALLIED` token rather than
a direct enum comparison to avoid import coupling. Alternatively: check
`getattr(new_state, "name", str(new_state)) == "ALLIED"`. Prefer the latter for
clarity. Adjust based on actual enum representation at verification time.

**Acceptance:** Tests F-01..F-07, F-14..F-16, F-17..F-19.
`faction_updates == []` must produce no events (test F-04, F-19).
Dedup test F-03: two FactionUpdates for same pair → exactly 1 `diplomatic_transition`.

**Files changed:** `src/observability/event_extractor.py`
**Dependencies:** Step 1. Independent of Steps 2 and 3.

---

### Step 5 — Add world_events_add loop (war_declared, military_conflict_resolved)

**File:** `src/observability/event_extractor.py`

Add after the faction_updates block added in Step 4, before `return events`.

**Import to add** (at top of file):
```python
from src.domains.world_emergence.schema import WorldEventCategory
```

**New block — world_events_add loop:**

```python
# Faction events from WorldEvent domain objects (PP-10/11)
_MILITARY_RESOLVED = frozenset({
    WorldEventCategory.TERRITORY_TRANSFERRED,
    WorldEventCategory.WAR_ENDED_EXHAUSTION,
})
for we in (getattr(update, "world_events_add", None) or []):
    cat = getattr(we, "category", None)
    if cat == WorldEventCategory.FACTION_WAR_DECLARED:
        events.append(SimulationEvent(
            event_type="war_declared", event_category="faction",
            tick=tick, entity_id=None, severity="CRITICAL",
            source_system="event_extractor", message="",
            payload={"faction_pair": str(getattr(we, "subject", ""))},
        ))
    elif cat in _MILITARY_RESOLVED:
        events.append(SimulationEvent(
            event_type="military_conflict_resolved", event_category="faction",
            tick=tick, entity_id=None, severity="WARNING",
            source_system="event_extractor", message="",
            payload={
                "subject": str(getattr(we, "subject", "")),
                "category": str(cat),
            },
        ))
```

**Note:** `WorldEvent.subject` is `Optional[str]` (`schema.py:L56`). Use
`getattr(we, "subject", "")` to safely handle None.

**Acceptance:** Tests F-08..F-10 (war_declared) and F-11..F-13 (military_conflict_resolved).
Empty `world_events_add` must produce no events (test F-10).
`getattr(..., "world_events_add", None) or []` pattern handles StateUpdate without the
attribute (anti-drift guard from test_plan §4).

**Files changed:** `src/observability/event_extractor.py`
**Dependencies:** Step 1. Independent of Steps 2-4.

---

### Step 6 — Add faction_extinct detection

**File:** `src/observability/event_extractor.py`

Add after the world_events_add loop (Step 5), before `return events`.
Cost-guarded by `update.faction_updates` non-empty check (Decision D6).

**New block:**

```python
# FACTION: faction_extinct (PP-08/PP-33) — only when faction state changed this tick
if getattr(update, "faction_updates", None):
    # Build set of faction_ids that have at least one living entity in current state
    _living_faction_ids: set[str] = set()
    for _ent in (getattr(current_state, "entities", {}) or {}).values():
        _hp = getattr(_ent, "hp", None)
        _fac = getattr(getattr(_ent, "identity", None), "faction", None)
        if _fac is not None and (_hp is None or _hp > 0):
            _living_faction_ids.add(str(_fac))

    for _fid, _fstate in (getattr(current_state, "factions", {}) or {}).items():
        if str(_fid) in _living_faction_ids:
            continue
        # Faction has no living entities — check prior state had living members
        _prior_living = any(
            getattr(getattr(_pe, "identity", None), "faction", None) is not None
            and str(getattr(getattr(_pe, "identity", None), "faction", "")) == str(_fid)
            and (getattr(_pe, "hp", None) is None or getattr(_pe, "hp", 1) > 0)
            for _pe in (getattr(prior_state, "entities", {}) or {}).values()
        )
        if _prior_living:
            events.append(SimulationEvent(
                event_type="faction_extinct", event_category="faction",
                tick=tick, entity_id=None, severity="WARNING",
                source_system="event_extractor", message="",
                payload={"faction_id": str(_fid)},
            ))
```

**Acceptance:** Tests F-20..F-22.
F-22: faction with living entities must not emit `faction_extinct`.
F-20: faction with no living entities where prior had living → must emit.
Guard: when `faction_updates == []`, the entire block is skipped (no O(N) scan).

**Files changed:** `src/observability/event_extractor.py`
**Dependencies:** Step 4 (logically follows the faction section). Independent of Steps 2, 3, 5.

---

### Step 7 — Add translation mappings to quality_hub.py

**File:** `src/simulation_quality/quality_hub.py`

EVENT-TRANSLATE ticket (TCK-20260629-SIMQ-EVENT-TRANSLATE) is DONE but did not
include `leadership_changed`, `betrayal_desertion`, or `alliance_formed`. Add them here.

**7a. Add to `_TRANSLATE_SIMPLE` dict (L20-L27):**
```python
"leadership_changed":  "diplomatic_transition",
"alliance_formed":     "alliance_accepted",
```

**7b. Add conditional translator function (before `_TRANSLATE_CONDITIONAL` dict):**
```python
def _translate_betrayal_desertion(env: ObservabilityEventEnvelope) -> str:
    """Betrayal maps to faction_tension_delta if faction context, else contract_lapsed."""
    if (env.payload or {}).get("faction_id"):
        return "faction_tension_delta"
    return "contract_lapsed"
```

**7c. Add entry to `_TRANSLATE_CONDITIONAL` dict (L67-L72):**
```python
"betrayal_desertion": _translate_betrayal_desertion,
```

**Acceptance:** Tests in `tests/simulation_quality/test_quality_hub_event_translation.py`
for new mappings (these tests should be added in Step 8 if the test file does not yet
have coverage for these three event types).

**Files changed:** `src/simulation_quality/quality_hub.py`
**Dependencies:** Step 1 (baseline). Fully independent of Steps 2-6.

---

### Step 8 — Write test file: test_event_extractor_social_faction.py

**File:** `tests/unit/observability/test_event_extractor_social_faction.py` (NEW)

Implement all test cases from `test_plan.md §2`:
- S-01..S-03: cooperation_event
- S-04..S-06: contract_offer_created
- S-07..S-08: contract_offer_accepted (regression)
- S-09..S-11: contract_completed bug fix
- S-12..S-13: contract_lapsed narrowing
- S-14..S-16: contract_expired_offer
- S-17..S-20: reputation_delta
- S-21..S-22: group_joined / group_expelled (regression)
- S-23..S-24: gap documentation tests (contract_milestone_completed, social_memory_created)
- F-01..F-04: diplomatic_transition
- F-05..F-07: alliance_accepted
- F-08..F-10: war_declared
- F-11..F-13: military_conflict_resolved
- F-14..F-16: territory_ownership_changed
- F-17..F-19: faction_tension_delta
- F-20..F-22: faction_extinct
- F-23..F-24: gap documentation tests (alliance_proposed, resource_seized)

**Pattern:** Follow `test_event_extractor_agency.py` builder pattern:
`MagicMock`-based `_entity()`, `_state()`, `_update_*()` helpers.
Assert on `[e.event_type for e in events]` plus payload assertions.

**Anti-drift guards to include** (test_plan §4):
- Import guard: verify `src.simulation_quality` is not imported by `event_extractor`
- Dedup guard (F-03): 4 factions, 6 pairs, all transition simultaneously → exactly 6 events
- `faction_updates == []` → no AttributeError
- `world_events_add` missing attribute → no AttributeError
- `contract_completed` fires for `ContractStatus.FULFILLED`-named status

**Dependencies:** Steps 2-7 (tests verify all implemented behavior)

---

### Step 9 — Run full regression suite + new tests

**Command:**
```bash
pytest tests/unit/observability/test_event_extractor_simq.py \
       tests/unit/observability/test_event_extractor_agency.py \
       tests/unit/observability/test_event_extractor_cognition.py \
       tests/unit/observability/test_event_extractor_economy.py \
       tests/unit/observability/test_event_extractor_world.py \
       tests/unit/observability/test_event_extractor_social_faction.py \
       tests/simulation_quality/test_quality_hub_event_translation.py \
       -v
```

**Acceptance:** All tests pass. Zero regressions in existing suites.
Any failure → fix in the corresponding step's file before proceeding.

**Dependencies:** Step 8

---

### Step 10 — Update parity ledger

**File:** `docs/parity_ledger/infrastructure.yaml`
**Location:** L3075 — entry `SIMQ-CALIBRATED-001`

Update `status` from `missing` to `verified` (or `divergent` if partial) and update
`v2_evidence` to reference this ticket and the new test file:
```yaml
status: verified
v2_evidence: >
  TCK-20260629-SIMQ-EMIT-SOCIAL-FACTION implements SOCIAL (6 new events + 3 bug fixes)
  and FACTION (7 new events) pillar emission. Blocked gaps (alliance_proposed,
  resource_seized, contract_milestone_completed, social_memory_created) documented in
  test_event_extractor_social_faction.py gap tests S-23, S-24, F-23, F-24.
  Translation mappings added: leadership_changed, betrayal_desertion, alliance_formed.
  Tests: tests/unit/observability/test_event_extractor_social_faction.py.
```

**Dependencies:** Step 9 (ledger updated only after tests pass)

---

### Step 11 — Finalize ticket

- Update `tickets/inprogress/TCK-20260629-SIMQ-EMIT-SOCIAL-FACTION.md`:
  - Status: DONE
  - Fill Implementation Notes, Test Summary, Files Changed, Completion Summary
  - Update AC checklist: check off implemented items; mark blocked items with note
- Move to `tickets/done/TCK-20260629-SIMQ-EMIT-SOCIAL-FACTION.md`
- Move `staging_artifacts/TCK-20260629-SIMQ-EMIT-SOCIAL-FACTION/` to `stored_artifacts/`
- Append row to `tickets/working_log.csv` (bottom, not after header)
- Clean up: `rm -rf data/runs/* reports/release_proof/*` (if populated)
- Run `make knowledge-index-update` (docs/parity_ledger modified)
- Write agent-monitoring entries: one run entry + at least one event entry
- Stage `agent-monitoring/` including `tools.jsonl` in the commit
- Commit: `TCK-20260629-SIMQ-EMIT-SOCIAL-FACTION: emit SOCIAL+FACTION pillar events`

**Dependencies:** Step 10

---

## Deviations

1. **events.py: `"faction"` added to `EventCategory` Literal** — Plan did not mention this.
   Required because `SimulationEvent` is a Pydantic model that validates `event_category`.
   `"faction"` was missing from the `EventCategory = Literal[...]` definition. Added it to
   `src/observability/events.py` so all faction events pass Pydantic validation.

2. **Type-guarded iteration for `faction_updates` and `world_events_add`** — Plan used
   `or []` pattern. Changed to `isinstance(..., (list, tuple))` guard + empty tuple fallback
   to prevent old test MagicMock updates from passing the truthy check and triggering the
   faction_extinct O(N) entity scan or other side effects.

3. **`reputation_delta`: `isinstance` guard on `public_reputation` values** — Plan used
   direct `getattr(entity.social, "public_reputation", 0.0)`. Added
   `isinstance(curr_rep, (int, float))` check before `abs(delta) > 0.05` comparison to
   prevent TypeError when old test helpers have MagicMock-auto-generated `.social.public_reputation`.

4. **`faction_extinct` guard changed from truthy check to `isinstance` list check** — Plan
   used `if getattr(update, "faction_updates", None):`. Changed to
   `isinstance(_faction_upd_list, list) and _faction_upd_list` to prevent MagicMock updates
   from old tests from entering the O(N) entity scan.

All deviations are defensive: they do not change behavior when correct typed objects are
passed. The core logic matches the plan exactly.

## Dependency Map

```
Step 1 (baseline)
  ├── Step 2 (contract diff block)          → Step 8 (tests)
  ├── Step 3 (cooperation + reputation)     → Step 8
  ├── Step 4 (faction_updates loop)         → Step 6 → Step 8
  ├── Step 5 (world_events_add loop)        → Step 8
  └── Step 7 (quality_hub translations)    → Step 8
                                              │
                                              ▼
                                           Step 9 (full regression run)
                                              │
                                              ▼
                                           Step 10 (parity ledger)
                                              │
                                              ▼
                                           Step 11 (finalize)
```

Steps 2, 3, 4, 5, 7 are independent of each other and can be executed in any order
(or in parallel) after Step 1. Step 6 must follow Step 4 (logically co-located in
the faction section of event_extractor.py).

---

## Acceptance Criteria → Steps

| AC | Covered by |
|---|---|
| All 11 SOCIAL event types emitted (6 new + 3 bug fix + 2 already done) | Steps 2, 3 |
| All 9 FACTION event types emitted (7 new; 2 scoped out as gaps D1, D2) | Steps 4, 5, 6 |
| Translation mappings for `leadership_changed`, `betrayal_desertion` added | Step 7 |
| No import of `src/simulation_quality/` from EventExtractor | Anti-drift guard in Step 8 |
| Faction events carry `faction_id` in payload; social events carry `entity_id` | Steps 2-6, verified in Step 8 |
| Unit tests per phase emission site | Step 8 |
| SOCIAL and FACTION pillars show non-zero events in calibration run | Verified by existing calibration harness after Steps 2-7 |

---

## Unresolved Questions

None. All decisions resolved by investigation evidence and prior ticket patterns (see
Decisions D1-D10 above). The `DiplomaticState` import path for the ALLIED check in
Step 4 should be verified at implementation time by reading the `updates.py` import
header — use `getattr(new_state, "name", str(new_state)) == "ALLIED"` as the safe
fallback if the enum is not importable without a circular dependency.
