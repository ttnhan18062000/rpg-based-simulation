---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260821-WS-ENTITY-DELTA-BROADCAST
phase: done
date: 2026-08-21
tags: [engine]
---

# TCK-20260821-WS-ENTITY-DELTA-BROADCAST

## Title
Broadcast per-tick entity deltas over the live WebSocket

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
There is no per-tick entity-position broadcast in any shape today -- the live stream only ever carries a minimal summary (tick, world_time, entities_count, maturity, seed), never entity positions or changed/removed lists. The author wants a lightweight delta broadcast (changed/removed/events, driven off the tick loop's existing DirtySet) added onto the existing WebSocket connection, including tick/snapshot_as_of_tick fields so clients can detect drift.

## Scope
- Add a per-tick delta broadcast (changed/removed/events) onto the existing /api/v1/ws connection, driven off the tick loop's existing DirtySet
- Build a slim per-entity dict via StatePresenter/ReadModelCache (new method), never touching AuthoritativeState fields directly in src/api/ws/
- Route the new delta payload through the already-negotiated msgpack format when the client requested msgpack in the handshake, not just JSON
- Include tick and snapshot_as_of_tick fields on every delta message so clients can detect drift
- Preserve stream_ws's existing listener-before-snapshot registration order (already correct); do not reorder it

## Out of Scope
- Any change to the cross-request REST /map,/static fetch vs WS connect-time race -- solved by the new tick/snapshot_as_of_tick fields for client-side drift detection, not by reordering stream_ws
- resource_node/building/chest state changes in the delta (DirtySet only covers entity-domain sets) -- that remains present_map/present_static's job (TCK-20260821-PRESENT-MAP-STATIC)
- Any spatial-subscription/region filtering field or logic (see the separate TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD ticket)

## Acceptance Criteria
- [x] On a tick where DirtySet.all_dirty_entities is non-empty, /api/v1/ws sends changed (slim dicts for dirty+alive entities) and removed (IDs gone from state.entities), plus tick and snapshot_as_of_tick
- [x] On a quiet tick (not a heartbeat), no message is sent
- [x] Registering listener before capturing baseline snapshot means no tick in that window is lost (test: fire a tick between registration and snapshot-capture, confirm reflected not lost)
- [x] EntitySlim fields are always absolute current values, never deltas (test: two consecutive changed-messages for same entity each independently equal true current state)
- [x] Delta payload is sent via msgpack when the client's handshake negotiated msgpack, not only JSON

## Related Tickets
- TCK-20260821-EPIC-LIVE-MAP-RECONNECTION

## Related Docs
- docs/observability/read_model_service_contract.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/api/ws/stream.py
- src/api/engine_manager.py
- src/core/dirty.py
- src/api/presenters/state_presenter.py
- src/api/read_model_cache.py
- tests/api/test_ws_protocol.py

## Assumptions / Open Questions
- No existing slim-entity cache/dict comparable to V1's _snapshot_to_slim_dict exists -- new StatePresenter/ReadModelCache method needed, not just wiring existing methods
- Bandwidth at 10k-entity scale projects 1.5-5MB/s per viewer even with delta-only encoding -- explicitly out of scope for this ticket to solve (separate gated M3 epic), noted here as context only

## Implementation Notes

This ticket's implementation was completed across two Implement-agent turns: the first turn made
substantial code and test changes but failed mid-flight on a transient API/SSL connectivity error
while retrying an integration test, before reaching Step 7 (parity ledger) or filling in the
ticket's closing sections. This second turn resumed from the on-disk state, verified the prior
turn's diff against plan.md step-by-step, fixed one issue, and completed Steps 7 and the ticket
hygiene work.

Verification of the prior turn's diff against `staging_artifacts/TCK-20260821-WS-ENTITY-DELTA-BROADCAST/plan.md`:
- `StatePresenter.present_entity_slim` (Step 1): matches plan exactly -- 9 fields (`id`, `kind`,
  `x`, `y`, `hp`, `max_hp`, `level`, `faction`, `weapon_range`), `Faction(...)` conversion wrapped
  in `try/except ValueError` with raw-int-as-string fallback. One fix made this turn: the
  `from src.core.enums import Faction` import was inline inside the method body; moved to a
  module-level import alongside the file's existing `from src.core.state import ...` line, since
  there is no circular-import hazard (`src/core/enums.py` has zero imports from `src.api` or
  `src.core.state`) and a function-local import for a plain enum lookup is an unnecessary
  abstraction the project's code-quality rules don't call for.
- `ReadModelCache.compute_tick_delta` (Step 2): matches plan exactly -- reuses
  `ReadModelInvalidationPolicy.get_dirty_entity_ids` for the `force_full_scan`/`None` fallback
  (no re-derived fallback logic), three-way classification (removed / changed / neither) correctly
  keys "removed" off `eid not in state.entities` rather than `combat.alive`, quiet-tick guard is
  `tick % 20 != 0` ported verbatim from V1, `events` is unconditionally `[]`, no caching into
  `_entity_dtos` or any new ID-keyed cache. No changes needed.
- `V2EngineManager` wiring (Step 3): `_latest_delta_payload` added as a separate attribute (not a
  replacement for `_latest_snapshot`), computed in `_update_latest_state` reusing the already-fetched
  `dirty_set`/`force_full`, and `_run_loop`'s sole `_notify_listeners` call site now gates on
  `is not None`. No changes needed.
- `stream_ws` (Step 4): `snapshot_as_of_tick` captured after the initial-payload send (listener
  registration at line 52 still precedes it, unchanged), each dequeued payload is copied via
  `dict(payload)` before the field is added -- avoiding the shared-dict-mutation race the plan
  specifically calls out (the same delta dict object is fanned out by reference to every connected
  listener's queue). No `AuthoritativeState`/`EntityState` import present in this file. No changes
  needed.
- Tests (Step 5): all 9 test_plan.md items are covered across `test_read_model_cache.py` (items
  1-5, 8, plus the anti-drift DTO-cache-collision guard), `test_engine_manager.py` (item 6,
  listener-before-snapshot ordering, driven at the unit level via a real thread loop rather than a
  subprocess), and `test_ws_protocol.py` (item 7, msgpack round-trip of the new delta shape). No
  changes needed.
- Docs (Step 6): `read_model_service_contract.md` gained the `tick_delta(...)` contract-table row;
  `frontend.md`'s known-gap callout and §B "Delta Sync (SSE)" section were narrowed to note the
  backend-capability half of the gap is closed on `/api/v1/ws` (not the nonexistent `/api/v1/stream`
  SSE route), while `useSimulation.ts` itself remains unrewired (tracked separately). The ticket's
  own `## Related Docs` line already correctly cited `docs/observability/read_model_service_contract.md`.
  No changes needed.

This turn's own work (Step 7 and closing):
- Added `INFRA-385` to `docs/parity_ledger/infrastructure.yaml` (re-checked the file directly for
  the next available ID at time of writing, per the shared-worktree caution in the task -- last
  existing entry was `INFRA-384`). Did not touch `INFRA-047`/`048`/`049`'s pre-existing
  `test_path: null` gap (confirmed out of scope) or the pre-existing unrelated `proof_type: unit`
  schema violation on `INFRA-383` (discovered incidentally while schema-validating the new entry;
  not introduced by this ticket, not touched).
- Ran the full scoped test suite: `tests/unit/api/`, `tests/architecture/test_api_read_model_guard.py`
  (54 passed) and `tests/api/test_ws_protocol.py` (3 passed, including the new msgpack delta
  round-trip test, run with the venv's `python3` prepended to `PATH` since the test spawns
  `python3 -m src serve` as a subprocess). All 57 tests pass; no test needed editing.

## Test Summary

`.venv/bin/python3 -m pytest tests/unit/api/ tests/architecture/test_api_read_model_guard.py -v`
-- 54 passed, including 7 new `compute_tick_delta` cases in `test_read_model_cache.py` and 2 new
cases in `test_engine_manager.py` (listener-before-snapshot ordering, delta-payload shape/None
gating).

`PATH=<venv>/bin:$PATH .venv/bin/python3 -m pytest tests/api/test_ws_protocol.py -v` -- 3 passed
(2 pre-existing handshake tests unmodified and still green, 1 new msgpack delta round-trip test).
This suite spawns a live subprocess server (`python3 -m src serve`) and requires the venv's
`python3` on `PATH`, a pre-existing environment characteristic of this test file noted in the
sibling tickets, not investigated further here.

No test was edited to make it pass; all failures (there were none by the time this turn ran) would
have been treated as real regressions per the Gate Integrity rule.

## Files Changed
- `src/api/presenters/state_presenter.py` -- new `present_entity_slim` static method; `Faction`
  import moved to module level (this turn's fix)
- `src/api/read_model_cache.py` -- new `compute_tick_delta` method
- `src/api/engine_manager.py` -- new `_latest_delta_payload` attribute, wiring in
  `_update_latest_state` and `_run_loop`
- `src/api/ws/stream.py` -- `snapshot_as_of_tick` capture and per-connection dict copy in `stream_ws`
- `tests/unit/api/test_read_model_cache.py` -- 7 new `compute_tick_delta` test cases
- `tests/unit/api/test_engine_manager.py` -- 2 new test cases (ordering guard, delta payload shape)
- `tests/api/test_ws_protocol.py` -- 1 new msgpack delta round-trip test
- `docs/observability/read_model_service_contract.md` -- new `tick_delta` contract-table row;
  Method column corrected during Document-Update to note it's a direct
  `V2EngineManager._update_latest_state()` call, not proxied via `ReadModelService`
- `docs/engine/contracts/frontend.md` -- narrowed known-gap callout and §B Delta Sync note
- `docs/engine/contracts/api_protocol_contract.md` -- Section 2's WebSocket streaming-payload
  description replaced (was stale "tick-by-tick state updates" one-liner) with the real
  conditional delta shape and 20-tick heartbeat suppression behavior (caught by Document-Update,
  originally missed from this list -- Architecture-Verify flagged the traceability gap)
- `docs/parity_ledger/infrastructure.yaml` -- new `INFRA-385` entry (this turn)
- `tickets/inprogress/TCK-20260821-WS-ENTITY-DELTA-BROADCAST.md` -- Status, Acceptance Criteria,
  Implementation Notes, Test Summary, Files Changed, Completion Summary (this turn)
- `staging_artifacts/TCK-20260821-WS-ENTITY-DELTA-BROADCAST/plan.md` -- Deviations section added
  (this turn)

## Completion Summary
Added a per-tick entity-delta broadcast to the existing `/api/v1/ws` connection: a new
`StatePresenter.present_entity_slim` projects each entity to a 9-field slim dict, a new
`ReadModelCache.compute_tick_delta` classifies `DirtySet`-dirty entities into `changed`/`removed`
with V1's 20-tick quiet-tick suppression rule, `V2EngineManager` computes this delta once per tick
and only notifies listeners when it's non-`None`, and `stream_ws` attaches a per-connection
`snapshot_as_of_tick` field via a dict copy to avoid a cross-connection mutation race. All 5
acceptance criteria are met and verified by new tests; the parity ledger gained `INFRA-385`
tracking this behavior. Implementation spanned two agent turns due to a transient connectivity
failure in the first turn's test retry; this turn verified the first turn's diff against plan.md
line-by-line, fixed one minor import-placement issue, completed the parity-ledger step, and ran the
full scoped test suite (57/57 passing) before closing out the ticket's documentation sections.
