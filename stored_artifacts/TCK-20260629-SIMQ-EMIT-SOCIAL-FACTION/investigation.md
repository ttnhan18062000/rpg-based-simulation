---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-SOCIAL-FACTION
artifact_type: investigation
tags: [simq, event-extractor, social, faction, diplomatic]
---

# Investigation: TCK-20260629-SIMQ-EMIT-SOCIAL-FACTION

## 1. Current Behavior

### 1.1 EventExtractor — What Is Already Implemented

`src/observability/event_extractor.py:EventExtractor.extract()` already emits 5 of the
11 SOCIAL events required by this ticket (implemented in prior SIMQ work):

| Event type | Location in extractor | Detection method |
|---|---|---|
| `group_joined` | L302-L312 | State diff: `entity.group_id != prior_ent.group_id` AND `curr != None` |
| `group_expelled` | L313-L319 | State diff: `entity.group_id != prior_ent.group_id` AND `curr is None` |
| `contract_offer_accepted` | L333-L340 | Status diff: OFFERED → ACTIVE |
| `contract_completed` | L340-L346 | Status: `curr_status == "COMPLETED"` (**BUG — see §1.3**) |
| `contract_lapsed` | L347-L353 | Status: `curr_status == "EXPIRED"` (catches ALL EXPIRED, not just ACTIVE→EXPIRED) |

`entity.group_id` is a property at `src/core/state.py:L760` delegating to
`entity.identity.group_id`.

0 of 9 FACTION events are currently implemented. The extractor does not iterate
`update.faction_updates` or `update.world_events_add`.

### 1.2 WorldEvent Objects Already in StateUpdate

`events_from_transitions()` in `src/domains/faction/diplomatic_state_machine.py:L85`
produces `WorldEvent` objects that are injected into `StateUpdate.world_events_add` by
the pipeline (pipeline.py:L205-L211). These cover:

| WorldEventCategory | Pipeline phase | Corresponding FACTION event type |
|---|---|---|
| `FACTION_WAR_DECLARED` | 8d diplomatic_transitions | `war_declared` |
| `FACTION_PEACE_TREATY` | 8d diplomatic_transitions | _(no pillar event; not in AC)_ |
| `FACTION_ALLIANCE_FORMED` | 8d diplomatic_transitions | `alliance_accepted` |
| `BETRAYAL` | 8d diplomatic_transitions | `faction_tension_delta` (or `contract_lapsed` per ticket) |

`MilitaryConflictPhase.execute()` (pipeline.py:L219-L223) adds additional
`WorldEvent` objects:

| WorldEventCategory | Trigger | Corresponding FACTION event type |
|---|---|---|
| `SIEGE_BEGINS` | Siege initiated | _(observability only; not in AC)_ |
| `TERRITORY_TRANSFERRED` | siege_progress >= 1.0 | `territory_ownership_changed` + `military_conflict_resolved` |
| `WAR_ENDED_EXHAUSTION` | military_strength crosses 0.3 | `military_conflict_resolved` |

The EventExtractor currently reads `update.world_updates` (WorldUpdate objects for regions)
but does NOT read `update.world_events_add` (WorldEvent domain objects). A new loop over
`update.world_events_add` is required.

### 1.3 Critical Bug — `contract_completed` Never Fires

`ContractStatus` in `src/core/strategic.py:L59-L66` defines:
```python
FULFILLED = "FULFILLED"
COMPLETED = "FULFILLED"  # Alias for project-like completion
```

`COMPLETED` is a duplicate-value alias. In Python Enum, the first name is canonical.
`ContractStatus.COMPLETED.name` returns `"FULFILLED"`, not `"COMPLETED"`. The extractor
at L340 checks `curr_status == "COMPLETED"` using `.name`. This check **never matches**.
`contract_completed` is effectively never emitted. Fix: change the check to
`curr_status in ("FULFILLED", "COMPLETED")` or simply `"FULFILLED"`.

### 1.4 Detection Gap: OFFERED vs ACTIVE Contract Expiry

The current `contract_lapsed` check (L347: `curr_status == "EXPIRED"`) catches ALL
EXPIRED transitions, regardless of prior status. This collapses two distinct events:

- ACTIVE→EXPIRED (obligor missed milestone) → should emit `contract_lapsed`
- OFFERED→EXPIRED (offer timed out via `_resolve_contract_expirations`) → should emit `contract_expired_offer`

`reap_expired_offers()` (`contracts.py:L317`) uses `contracts_remove` — the contract
disappears from `entity.strategic.contracts` entirely. State diff: contract present in
`prior_contracts` with OFFERED status, absent from `curr_contracts` → `contract_expired_offer`.
`check_expirations()` (`contracts.py:L65`) transitions OFFERED→EXPIRED via status update —
detectable as OFFERED→EXPIRED status diff.

### 1.5 FactionUpdate Structure — Available Fields

`src/core/updates.py:L844` FactionUpdate fields:
- `diplomatic_relations_set: Dict[str, DiplomaticState]`
- `military_strength_set: Optional[float]`
- `territory_add: Tuple[str, ...]`
- `territory_remove: Tuple[str, ...)`
- `tension_delta: float` (implied by FactionAwarenessService usage at faction_decision.py:L197)

`StateUpdate.faction_updates: List[FactionUpdate]` at `updates.py:L919` — accumulated
from phases 8b (faction_decision), 8c (faction_awareness), 8d (diplomatic_transitions),
and 8e (military_conflict). All are available to EventExtractor via `update.faction_updates`.

### 1.6 Cooperation Event — PP-05 Signal

`CooperationPhase.execute()` (`src/domains/cooperation/phase.py:L136`) writes
`property_updates["last_cooperation_decision"] = decision` into `EntityUpdate`. The
EventExtractor already reads `prop = e_upd_ext.property_updates`. Detecting
`cooperation_event` requires checking `prop.get("last_cooperation_decision") is not None`.

### 1.7 Reputation Delta — PP-18 Signal

`EntityState.social` has fields `public_reputation`, `heroism_score`, `notoriety_score`
(state.py:L730-L732). The state diff of these fields against `prior_ent.social` with a
significance threshold of 0.05 (per ticket AC) is sufficient to emit `reputation_delta`.
The entity loop already has both `entity` and `prior_ent` in scope.

### 1.8 What Cannot Be Detected — Blocked Events

| Event | Reason blocked | Parallel from prior tickets |
|---|---|---|
| `alliance_proposed` | `faction_directives` is a local variable in pipeline.py:L171; not injected into StateUpdate | Same as `defer_with_reason` in AGENCY ticket |
| `contract_milestone_completed` | `ContractState` has no milestone field (strategic.py:L177-L188); milestones are not tracked | Same pattern as `commitment_abandoned` in AGENCY |
| `social_memory_created` | No `social_memories` list confirmed in EntityState strategic component; requires verification | Unknown until code read |
| `resource_seized` | MilitaryConflictPhase emits `TERRITORY_TRANSFERRED` WorldEvent but no distinct resource seizure event; may not map 1:1 to a territory-transfer | Needs decision |

### 1.9 Existing Engine Events — Translation Mappings

`src/observability/events.py:L276-L285` defines `LeadershipChangedEvent`
(event_type=`leadership_changed`, Logic ID SOC-228). Per ticket, maps to
`diplomatic_transition` in QualityHub._translate().

`src/observability/events.py:L302-L333` defines `BetrayalDesertionEvent`
(event_type=`betrayal_desertion`, Logic ID SOC-230). Per ticket, maps to
`faction_tension_delta` if faction context, or `contract_lapsed` if contract context.
Both mappings should go in TCK-20260629-SIMQ-EVENT-TRANSLATE (per ticket Related Tickets).
Verify whether that ticket is already done before adding mappings here.

---

## 2. Mechanics / Engine Constraints

- `docs/mechanics/04_strategic_cognition.md` — Social memory and cooperation laws govern
  when entities record significant interactions. `social_memory_created` requires
  verifying whether the social memory state survives as a typed field.
- Engine contract `docs/engine/kernel.md` 6-phase loop — EventExtractor runs post-apply,
  receiving the final committed StateUpdate and both prior and current state snapshots.
- `docs/engine/authoritative_pipeline.md` — All faction mutations flow through
  `FactionUpdate` records in StateUpdate; FactionState is never mutated directly.
- ALLIED and VASSAL are terminal diplomatic states — no further tension-driven transitions
  fire from them (`diplomatic_state_machine.py:L48`). This bounds the `alliance_accepted`
  detection: once ALLIED, the pair won't re-enter the transition loop.
- `MilitaryConflictPhase` note (military_conflict.py:L153): `RegionState.owner_faction_id`
  is NOT set during territory transfer (documented as FAC-010). Authoritative ownership
  is `FactionState.territory`. Existing `region_ownership_changed` event from
  `WorldUpdate.owner_faction_id_set` is therefore a DIFFERENT signal from
  `territory_ownership_changed` (FactionUpdate.territory_add). Both may fire for the same
  physical transfer from different perspectives; this is intentional (per ticket §Out of Scope note).

---

## 3. Parity Ledger Overlap

| Entry ID | File | Status | Overlap |
|---|---|---|---|
| SIMQ-CALIBRATED-001 | `docs/parity_ledger/infrastructure.yaml:L3075` | `missing` | Must be updated after this ticket to add SOCIAL and FACTION pillars to the calibration progress note |

No entries in `social_narrative.yaml` or `faction.yaml` directly reference SIMQ EMIT
event gaps. The faction.yaml entry covering diplomatic_transitions (FAC-E53Bd note at
faction.yaml:L129) flags the naming mismatch: WorldEventCategory uses uppercase
`FACTION_WAR_DECLARED` while the SimQ pillar expects lowercase `war_declared`
event_type — this is the translation gap this ticket bridges via EventExtractor.

---

## 4. Prior Work

| Source | Key finding for this ticket |
|---|---|
| `staging_artifacts/TCK-20260628-SIMQ-INVESTIGATION/investigation.md` | Established that EventExtractor is the correct injection point; `social` and `faction` event categories both flow through it |
| `staging_artifacts/TCK-20260629-SIMQ-EMIT-STATE-DIFF/investigation.md` | Established `update.entity_updates.keys()` as dirty set; resource_nodes loop pattern |
| `stored_artifacts/TCK-20260629-SIMQ-EMIT-AGENCY/` | Established pattern: blocked events (no StateUpdate trace) are documented in tests with gap comments; `faction_directives` follows the same pattern as `event_recorder` |
| `stored_artifacts/TCK-20260629-SIMQ-EMIT-ECONOMY/` | Established that `resource_transfers` are cleared before EventExtractor runs; `intent_results` survived; relevant because `reap_expired_offers` uses `contracts_remove` which also leaves no trace in curr_state contracts dict — confirmed gap pattern |
| `tickets/done/TCK-20260629-SIMQ-EMIT-ECONOMY.md` | Model for implementation: state diff first, property_updates second, world_updates/faction_updates third |

---

## 5. Risks and Open Questions

### Requiring a Decision Before Implementation

1. **`alliance_proposed` — blocked, document or scope differently?**
   `faction_directives` is a local list in pipeline.py:L171 consumed only by
   AdventureDecisionPhase. It is never serialized into StateUpdate. EventExtractor
   cannot emit `alliance_proposed`. Same architectural pattern as AGENCY's `defer_with_reason`.
   Decision: document as gap (same pattern), exclude from AC, update AC before implementing.

2. **`resource_seized` — no distinct WorldEvent exists.**
   MilitaryConflictPhase.execute() emits `TERRITORY_TRANSFERRED` when siege_progress >= 1.0.
   There is no separate `resource_seized` WorldEvent. `resource_seized` may need to be:
   (a) emitted alongside `territory_ownership_changed` when `TERRITORY_TRANSFERRED` fires, OR
   (b) dropped from scope as not yet emittable from current phase output.
   Decision needed before implementation.

3. **`contract_milestone_completed` — no milestone field in ContractState.**
   `ContractState` (strategic.py:L177) has no milestone or progress tracking.
   This event cannot be emitted from state diff. Same pattern as `commitment_abandoned` in AGENCY.
   Decision: document as gap, exclude from AC for this ticket.

4. **`social_memory_created` — field path unverified.**
   CooperationPhase appends events to `entity.timeline` (phase.py:L65) but this is a
   transient in-memory buffer, not a persisted state field. If `entity.strategic` has no
   `social_memories` list, this event is undetectable from state diff.
   Decision: verify field before scoping in; if absent, document as gap.

5. **`contract_lapsed` scope correction — fix or leave?**
   Current code emits `contract_lapsed` for ALL EXPIRED statuses (ACTIVE→EXPIRED and
   OFFERED→EXPIRED). Per ticket, `contract_lapsed` = "Obligor missed milestone; contract
   lapses" which implies only ACTIVE→EXPIRED. OFFERED→EXPIRED should be `contract_expired_offer`.
   Fixing this changes existing behavior that existing tests rely on. Scoped fix required.

6. **`diplomatic_transition` deduplication.**
   `compute_transitions()` produces two FactionUpdate records per pair (one per faction).
   Both carry the same `diplomatic_relations_set` entry. EventExtractor must deduplicate
   by faction-pair to avoid emitting duplicate `diplomatic_transition` events.
   Proposed: emit once per pair, using `frozenset({faction_id, other_id})` as dedup key.

7. **`faction_extinct` — detection timing.**
   A faction becomes extinct when no living entities belong to it. But entity
   faction membership is on `entity.identity.faction` (not FactionState). Detecting
   extinct factions requires iterating `current_state.entities` by faction, which is
   O(entities). Should this run every tick or only when faction_updates are non-empty?
   Proposed: only when `len(update.faction_updates) > 0` to bound cost.

---

## 6. Anti-Drift Hazards

- **Do not read `diplomatic_relations` from FactionState directly** for the
  `diplomatic_transition` event — use `update.faction_updates` (the committed delta).
  Reading state diff on FactionState would require iterating all pairs on every tick.

- **Do not import from `src/simulation_quality/`** in EventExtractor or any PP phase.
  EventExtractor is observability layer; quality module consumes events, not vice versa.

- **`contract_completed` bug fix is in scope for this ticket** (the check is in the
  contract-diff block that this ticket modifies). Fix the enum name check while
  touching that code path.

- **`tension_delta` in FactionUpdate** is a float delta (not an absolute set). Only
  emit `faction_tension_delta` when `abs(upd.tension_delta) >= threshold`. The
  quality_scoring_contract.md §FACTION does not specify a threshold — use 0.0 (any
  non-zero delta) to be safe, consistent with how `xp_granted` uses any positive delta.

- **`group_id` vs `identity.group_id`** — EventExtractor currently reads
  `entity.group_id` (the property at state.py:L760). Do not change this to
  `entity.identity.group_id` directly; the property is the canonical access path.
