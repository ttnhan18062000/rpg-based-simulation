---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260821-WS-ENTITY-DELTA-BROADCAST
artifact_type: test_plan
tags: [api-design, engine]
---

# Test Plan — TCK-20260821-WS-ENTITY-DELTA-BROADCAST

## Regression Surface

- **unit** — `tests/unit/api/test_engine_manager.py`: exercises real `V2EngineManager.start()`/
  `stop()` against a real background-thread tick loop (`_poll_until` polling pattern). Any change to
  `_run_loop`/`_update_latest_state`/`_notify_listeners` must keep these green — they are the
  existing coverage for the exact code path this ticket modifies.
- **unit** — `tests/unit/api/test_read_model_cache.py`: covers `ReadModelCache.update`,
  `get_minimal_summary`, `get_entity_dto` hit/miss semantics against a real
  `AuthoritativeState`/`DirtySet`. A new slim-entity method added to this class must not change the
  existing `get_entity_dto`/`get_minimal_summary` behavior or its cache-hit/miss counters.
- **unit** — `tests/unit/api/test_state_presenter.py` (added by `TCK-20260821-PRESENT-MAP-STATIC`):
  covers `present_map`/`present_static`/`terrain_code_map`. A new `present_entity_slim`-style method
  added to the same class must not disturb these.
- **unit** — `tests/unit/api/test_dependencies.py`, `test_read_model_service.py`,
  `test_economy_route.py`, `test_stats_route.py`, `test_static_route.py`, `test_map_route.py`: no
  direct dependency on this ticket's changes, but live in the same `tests/unit/api/` directory —
  included in the scoped run as a cheap cross-file regression check, matching the sibling ticket's
  precedent.
- **architecture** — `tests/architecture/test_api_read_model_guard.py`: AST-scans
  `src/api/routes/`, `src/api/ws/`, `src/api/server.py` for non-`TYPE_CHECKING` imports of
  `AuthoritativeState`/`EntityState`. Directly load-bearing for this ticket since the whole design
  hinges on keeping delta-building logic out of `src/api/ws/stream.py`.
- **integration (subprocess, real server)** — `tests/api/test_ws_protocol.py`
  (`test_ws_json_handshake`, `test_ws_msgpack_handshake`): the only existing tests that connect to
  the real `/api/v1/ws` route end-to-end (spawns `python3 -m src serve`, connects a real
  `websockets` client, does the real handshake). Both currently assert only `"tick" in data` on the
  first post-handshake message and the second received message — loose enough that they should
  keep passing once the per-tick payload becomes delta-shaped instead of the minimal summary, but
  must be re-run to confirm, since they are real black-box coverage of the exact wire path this
  ticket changes.

## New Tests Required

All new unit tests target the new delta-computation logic (`StatePresenter`/`ReadModelCache`/
`V2EngineManager`, exact split left to the plan phase) and the `stream_ws` route behavior. Exact
function/method names below are illustrative pending the plan phase's actual naming — the *coverage*
each entry describes is what's required, not the literal signature.

1. **`changed` set includes only dirty + alive entities, as slim absolute-value dicts**
   Category: unit. Verifies: given an `AuthoritativeState` with a mix of dirty-and-alive,
   dirty-and-dead, and clean entities plus a `DirtySet` marking the first two groups dirty, the
   computed `changed` list contains exactly the dirty-and-alive entity's slim dict (matching AC #1's
   "slim dicts for dirty+alive entities"), and the dirty-and-dead entity does NOT appear in
   `changed`. Location: `tests/unit/api/test_read_model_cache.py` or a new
   `tests/unit/api/test_state_presenter.py` addition (co-locate with wherever the slim-dict method
   lands).
2. **`removed` set is IDs gone from `state.entities`, not just `alive=False`**
   Category: unit. Verifies AC #1's "removed (IDs gone from state.entities)" literally: construct a
   `DirtySet` whose `all_dirty_entities` includes an ID that is present in a prior-state fixture but
   absent from the current `state.entities` dict (simulating a real removal via
   `entities_remove`/`apply.py`'s `pop`), confirm that ID lands in `removed`, not `changed`, and that
   a merely-dead-but-still-present entity (alive=False, still in `state.entities`) lands in neither
   (excluded from `changed` by the aliveness filter, and NOT in `removed` since it's still present).
   Location: same file as test 1.
3. **Quiet tick (DirtySet empty, not a heartbeat tick) produces no message**
   Category: unit. Verifies AC #2 directly: call the delta-computation function with an empty
   `DirtySet` and a `tick` value where `tick % 20 != 0`, assert it returns `None` (or the equivalent
   "don't send" signal the implementation chooses) — mirrors V1's exact
   `if not changed and not removed and not serialized_events and tick % 20 != 0: return None` guard.
   Location: same file as test 1.
4. **Heartbeat tick (quiet, `tick % 20 == 0`) still produces a message**
   Category: unit. Verifies the heartbeat-cadence half of the same guard: an empty `DirtySet` at a
   tick divisible by 20 still returns a non-`None` payload (with empty `changed`/`removed`), so
   clients can detect the connection is still alive during long quiet stretches. Location: same file
   as test 1.
5. **`EntitySlim` fields are always absolute current values, never deltas**
   Category: unit. Verifies AC #4 directly: build two consecutive delta payloads for the same
   entity across two different `AuthoritativeState`s where the entity's `hp`/`position` changed
   between them (e.g. hp 100 → 80), assert each payload's `changed` entry for that entity
   independently equals that state's true current `hp`/`x`/`y` — i.e. the second payload's entity
   dict does not encode "-20" or any diff-shaped value, it encodes the real current `hp`. This is
   the exact AC #4 wording ("two consecutive changed-messages for same entity each independently
   equal true current state"). Location: same file as test 1.
6. **Listener-registration-before-snapshot ordering is preserved and loses no tick**
   Category: unit or integration. Verifies AC #3: using a fake/controllable `V2EngineManager` (or
   the real one with a manually-fired tick between `add_tick_listener` and the initial
   `get_state()` snapshot call, matching `stream_ws`'s exact call order), confirm a tick fired in
   that window is reflected (not silently lost) once the WS consumer starts reading from its queue.
   Given `stream_ws` itself already has this ordering correct today (confirmed in investigation.md),
   this test's real job is to be a regression guard against a future refactor accidentally
   reordering it, not to fix a bug — write it as a guard against silent reintroduction. Location:
   `tests/unit/api/test_engine_manager.py` (drive `add_tick_listener` + a manual tick directly, no
   subprocess needed) or as a new case in `tests/api/test_ws_protocol.py` if unit-level driving of
   the exact race proves awkward without a real server.
7. **msgpack-encoded delta payload round-trips correctly**
   Category: integration (subprocess, real server — extends the existing pattern in
   `tests/api/test_ws_protocol.py`). Verifies AC #5: connect with `format: "msgpack"`, wait for a
   real delta message (not just the initial payload), `msgpack.unpackb` it, and assert it has the
   `changed`/`removed`/`tick`/`snapshot_as_of_tick` shape (not just `"tick" in data` as the existing
   test does for the initial payload). This is real coverage that the new delta shape survives the
   `jsonable_encoder` → `msgpack.packb` path with no serialization-only field (e.g. a
   non-JSON-native type slipping into the slim dict) breaking msgpack encoding. Location:
   `tests/api/test_ws_protocol.py`, new test alongside `test_ws_msgpack_handshake`.
8. **`tick`/`snapshot_as_of_tick` fields are present and correct on every delta message**
   Category: unit (and cheaply re-confirmed by test 7's integration pass). Verifies AC #1's field
   requirement precisely: both fields present on a non-`None` delta payload, `tick` matches the
   state's own `tick`, `snapshot_as_of_tick` reflects the tick the WS connection's baseline snapshot
   was captured at (per the connect-time race-avoidance design in the epic doc — exact semantics
   depend on the plan phase's chosen implementation, but the field's presence and non-drifting value
   across consecutive deltas from the same connection is directly testable). Location: same file as
   test 1, plus one assertion added to test 7.
9. **`src/api/ws/stream.py` still imports no `AuthoritativeState`/`EntityState` after this change**
   Category: architecture guard (already exists — `tests/architecture/test_api_read_model_guard.py`
   — no new test file needed, just confirm it still passes after implementation). Listed explicitly
   here because it is the single most direct enforcement of this ticket's own stated architecture
   constraint ("never touching AuthoritativeState fields directly in src/api/ws/") and must be
   re-run, not assumed to still pass.

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/unit/api/ tests/architecture/test_api_read_model_guard.py -v
.venv/bin/python3 -m pytest tests/api/test_ws_protocol.py -v
```

Two separate scoped commands: the first is the fast in-process unit + architecture-guard pass
(mirrors the exact scoped command the sibling `TCK-20260821-PRESENT-MAP-STATIC` ticket used); the
second is the slower subprocess-based real-server integration pass specific to the WS wire protocol
— kept separate since it spawns a real `python3 -m src serve` process per test and takes materially
longer. Never run the bare `pytest tests/`, per this project's Testing Rule.

## Anti-Drift Test Guards

- **Test 2** (removed = gone-from-dict, not alive=False) is the primary guard against the easy
  mistake of conflating "dead" with "removed" — V2's `combat.alive` flag and actual dict-key removal
  are two genuinely different lifecycle events (confirmed in investigation.md:
  `src/engine/apply.py:228-232` does a real `.pop()`), and a naive implementation checking only
  `alive` would silently misclassify a still-present-but-dead entity as "removed" when it should be
  entirely absent from both lists, or vice versa.
- **Test 5** (absolute values, never deltas) is the primary guard against the most consequential
  architectural property this ticket's AC calls out explicitly — it's what makes the payload safe
  for a slow client to have messages coalesced/dropped under backpressure (already true of the
  existing `asyncio.Queue(maxsize=10)` + `put_nowait` drop-on-full behavior) without any
  sequence-number/generation-tracking machinery. A regression here (e.g. someone "optimizing" by
  sending only changed sub-fields) would silently break client-side reconciliation in a way no
  existing test would otherwise catch.
- **Test 6** (registration-before-snapshot ordering) guards against exactly the race the epic doc's
  external design review found and fixed — reordering `stream_ws`'s two lines back to
  snapshot-then-register would reintroduce a real, silent tick-loss bug with no other test in the
  suite positioned to catch it (the existing `test_ws_protocol.py` tests don't fire a tick in that
  specific narrow window).
- **Test 9** (architecture guard still green) guards against the most likely form of scope-creep for
  this specific ticket: pulling `AuthoritativeState`/`EntityState` directly into `stream.py` for
  convenience while building the delta payload, instead of routing it through
  `engine_manager.py`/`StatePresenter`/`ReadModelCache` as the ticket's own Scope requires.
- **Regression Surface's inclusion of `test_state_presenter.py`/`test_read_model_cache.py`** guards
  against the new slim-entity method accidentally sharing (and corrupting) the existing
  `_entity_dtos` cache dict `ReadModelCache.get_entity_dto` uses for the heavy `present_entity` DTO —
  a plausible implementation mistake would be caching slim and full DTOs under the same key space by
  entity ID, silently returning a full-fat cached DTO where a slim one was requested (or vice versa)
  once both code paths are exercised against the same cache instance.
- **No test in this plan exercises `resource_node`/`building`/`chest`/`region` delta content** —
  deliberately, matching the ticket's Out of Scope. If a future test accidentally starts asserting on
  those fields being present in the entity-delta payload, that's a scope-creep signal, not a gap to
  fill in this ticket.
