---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260821-WS-ENTITY-DELTA-BROADCAST
artifact_type: plan
tags: [api-design, engine]
---

# Implementation Plan — TCK-20260821-WS-ENTITY-DELTA-BROADCAST

## Summary

Add a per-tick entity delta broadcast to the existing `/api/v1/ws` connection by (1) adding a
stateless slim-entity presenter method, (2) adding a `DirtySet`-driven delta-computation method on
`ReadModelCache` that classifies dirty entities into `changed`/`removed` and applies V1's 20-tick
heartbeat/quiet-tick suppression rule, (3) wiring `V2EngineManager` to compute this delta once per
tick alongside (not replacing) the existing minimal-summary snapshot, and only notifying tick
listeners when the delta is non-`None`, and (4) having `stream_ws` attach a per-connection
`snapshot_as_of_tick` field to each dequeued delta before sending — copying the payload rather than
mutating it in place, since the same dict object is shared across every connected listener's queue.
No new thread-safety mechanism is introduced: the existing `loop.call_soon_threadsafe(queue.put_nowait,
...)` pattern is reused unchanged. All `AuthoritativeState`/`EntityState`-touching logic stays out of
`src/api/ws/stream.py`, in `StatePresenter`/`ReadModelCache`/`V2EngineManager`, per the architecture
guard test and the ticket's own Scope wording.

## Open Design Questions — Resolved

### 1. `events` field: permanent empty list, not wired to real content this ticket

**Decision: `events: []` unconditionally, every delta message, for the lifetime of this ticket.**

Rationale: the ticket's Acceptance Criteria (bullet 1) enumerate `changed`, `removed`, `tick`,
`snapshot_as_of_tick` — `events` is not named in any AC. The frontend's only consumer of this field,
`frontend/src/hooks/useSimulation.ts:159` (`if (delta.events && delta.events.length > 0) { ... }`),
already guards on both existence and non-empty length, so an unconditionally-empty array is handled
identically to an absent key — zero behavior risk. Wiring real `SimulationEvent` content would
require a second listener registration (`add_event_listener`, already used by the separate
`/ws/observe` endpoint — `src/api/ws/stream.py:81-141`) plus merge logic against the delta payload —
materially more surface area than any AC tests, and no test in `test_plan.md` exercises non-empty
`events`. This is a deliberate scope boundary, not an oversight: the field exists in the payload
shape (matching V1's `compute_delta()` shape and the ticket's Scope line), but sourcing real content
into it is out of scope for this ticket and should be filed as a follow-up ticket if ever needed, not
added here.

### 2. EntitySlim field drop-vs-derive: 5 of the 6 uncertain fields are dropped, 1 is derived

Investigated `src/core/state.py` directly (not inferred from names) for each of the six uncertain
fields from V1's `EntitySlimSchema` (`git show 677abbfb^:src_legacy/api/schemas.py:387-407`):

| V1 field | Decision | Evidence |
|---|---|---|
| `state` (behavior/status label) | **Drop** | Grepped every `work_kind=` literal in `src/`: only `"ENTITY_ACT"`, `"ENTITY_BRAIN"`, `"DRAIN_DEBT"` (`src/engine/scheduler.py:64,86,130`; `src/certification/scenarios.py:333,387`) — these are scheduler work-queue classifications ("what kind of compute to schedule this tick"), not a rendering-oriented "what is this entity currently doing" label. No enum/string field on any `EntityState` component reads as that. No confirmed source. |
| `tier` | **Drop** | `grep -n "tier" src/core/state.py` returns zero hits. No confirmed source. |
| `weapon_range` | **Derive** | `CombatComponent.range: int = 1` at `src/core/state.py:304`. The only numeric range-typed field on the combat component; name is a plausible direct match for "weapon range" (attack range). Map `weapon_range` → `entity.combat.range` verbatim, no unit conversion needed. |
| `combat_target_id` | **Drop** | The only trace of a per-entity "current attack target" is `TaskComponent.payload.get("target_id")` in `src/certification/scenarios.py:333,387` (`payload={"action": "ATTACK", "target_id": 12}`) — but `TaskComponent.payload: Dict[str, Any]` (`src/core/state.py:387`) is an explicitly untyped free-form dict, and this citation is a certification-fixture scenario, not confirmed as the live combat-target-assignment path in `src/domains/combat_engagement/`. Per this project's Durable State Rule ("Do not store durable meaning in `reason` strings, free-form `metadata`... or temporary local variables"), a free-form `payload` key does not qualify as a stable typed source for an API-shaped field. `GroupRecord.shared_target_id`/`escort_target_id` (`src/core/state.py:557,568`) exist but are group-level, not per-entity. No confirmed per-entity source. |
| `loot_progress` | **Drop** | `InteractionComponent` (`src/core/state.py:390-407`) has `target_node_id`/`progress`/`start_tick`, but its docstring and field name (`target_node_id`) tie it to resource-node harvesting/channeling, not looting a corpse/chest after combat. No dedicated loot-timer field exists on `EntityState` or any component. No confirmed source. |
| `loot_duration` | **Drop** | Same as above — no confirmed source. |

Additionally, `display_name` (in V1's schema but already absent from the frontend's live
`EntitySlim` TypeScript interface, `frontend/src/types/api.ts:88-103` per investigation.md) is also
dropped — it was never in the six "uncertain" fields but has no live consumer either.

**Final V2 `EntitySlim` shape** (built by `StatePresenter.present_entity_slim`, Step 1):
`id, kind, x, y, hp, max_hp, level, faction, weapon_range` — 9 fields, all with a confirmed direct
or lightly-mapped V2 source (see Step 1 for exact citations per field, including the `faction`
int→string mapping via `src/core/enums.py:23-27`'s `Faction` `IntEnum`).

## Steps

### Step 1 — Add `StatePresenter.present_entity_slim` (new stateless method)

**Files:** `src/api/presenters/state_presenter.py`

**Change:** Add a new `@staticmethod present_entity_slim(entity: EntityState) -> Dict[str, Any]`
alongside the existing `present_entity` (heavy DTO, lines 38-129). Field-by-field source, each
verified against the real dataclass (not inferred):
- `id`: `entity.id` (`EntityState.id: int`, `src/core/state.py:668`)
- `kind`: `entity.kind` (`EntityState.kind: str`, `src/core/state.py:669`)
- `x`, `y`: `entity.position` (property at `src/core/state.py:760`, returns `navigation.position`
  tuple — same source `present_entity` already uses at line 46: `"position": entity.position`).
  Split into `x = entity.position[0]`, `y = entity.position[1]` to match V1's flat `x`/`y` ints
  (V1 typed them `int`; V2's are floats — do not silently truncate, pass through as-is; a client-side
  rounding concern, not this ticket's to solve, matches `present_entity`'s own untouched
  `"position"` tuple precedent of passing floats through unmodified).
- `hp`, `max_hp`: `entity.combat.hp`, `entity.combat.max_hp` (`CombatComponent`, `src/core/state.py:299-300`
  — same source `present_entity` already uses at lines 49-50).
- `level`: `entity.identity.evolution_level` (`IdentityComponent.evolution_level: int = 1`,
  `src/core/state.py:477` — same source `present_entity`'s `"identity"` block already uses at
  line 118: `"level": entity.identity.evolution_level`).
- `faction`: `entity.identity.faction` is `int`-typed (`IdentityComponent.faction: int = 0`,
  `src/core/state.py:474`, comment `# Faction.HERO_GUILD`). Map via
  `Faction(entity.identity.faction).name.lower()` using the `Faction(IntEnum)` at
  `src/core/enums.py:23-27` (`HERO_GUILD=0, MONSTER_HORDE=1, TOWN_COUNCIL=2, NEUTRAL=3`) — confirms
  `Faction.HERO_GUILD.name.lower() == "hero_guild"`, matching V1's default string
  `faction: str = "hero_guild"` (`src_legacy/api/schemas.py`) exactly. Wrap in a `try/except
  ValueError` falling back to the raw int-as-string if an out-of-range value is ever stored (defensive,
  since `IdentityComponent.faction` is a plain `int` field, not enum-typed, so nothing prevents an
  invalid value at the type level).
- `weapon_range`: `entity.combat.range` (`CombatComponent.range: int = 1`, `src/core/state.py:304`)
  — see Open Design Question 2 above for the derive rationale.
- Apply the project-wide aliveness filter precedent at the call site (Step 2), not inside this
  method — `present_entity_slim` itself should be a pure per-entity transform with no filtering
  logic, consistent with `present_entity`'s own shape (it also does not self-filter).

**Do NOT touch:** `present_entity` (the heavy DTO), `present_full`, `present_region`,
`present_map`, `present_static`, `present_stats`, `terrain_code_map` — this is a pure addition, no
existing method's body changes.

**Verify:** Test Plan item 1 (`changed` set includes only dirty+alive entities as slim absolute-value
dicts) and item 5 (fields are always absolute current values, never deltas — automatically satisfied
since `present_entity_slim` always reads live component values, never a diff).

---

### Step 2 — Add `ReadModelCache.compute_tick_delta` (new method, DirtySet-driven)

**Files:** `src/api/read_model_cache.py`

**Change:** Add a new method:
```python
def compute_tick_delta(
    self,
    state: AuthoritativeState,
    dirty_set: Optional[DirtySet],
    force_full_scan: bool,
    tick: int,
) -> Optional[Dict[str, Any]]:
```
Logic, ported from V1's `compute_delta()` (`git show 677abbfb^:src_legacy/api/routes/schemas
.py`/`stream.py` — read in full this session) but driven by `DirtySet` instead of a stored
old-vs-new full-snapshot diff (V2 has no per-connection prior-snapshot state to diff against, and
the ticket's own Scope requires driving off "the tick loop's existing DirtySet", not a re-implemented
diff):
1. If `force_full_scan` or `dirty_set is None`: treat every entity ID in `state.entities` as the
   candidate set (mirrors `ReadModelInvalidationPolicy.get_dirty_entity_ids`'s existing
   `force_full_scan`/`None` fallback at `read_model_cache.py:21-28` — reuse that exact function
   rather than re-deriving the fallback, to stay consistent with the one other place in this file
   that already makes this same force-full-scan/None decision).
2. Otherwise, iterate `dirty_set.all_dirty_entities` (`src/core/dirty.py:230-234` — this property
   already unions only the entity-scoped domain sets, excluding `resource_node_ids`/`building_ids`/
   `chest_ids`/etc., so using it directly is the safe choice per investigation.md's Anti-Drift
   Hazards).
3. For each candidate ID: if `eid not in state.entities` → append to `removed` (list of ints). Else
   if `state.entities[eid].combat.alive` → append `StatePresenter.present_entity_slim(state
   .entities[eid])` to `changed`. Else (present but dead) → include in neither list.
4. `events = []` unconditionally (Open Design Question 1).
5. Quiet-tick guard, ported verbatim from V1's `compute_delta()`: `if not changed and not removed
   and not events and tick % 20 != 0: return None`.
6. Otherwise return `{"tick": tick, "changed": changed, "removed": removed, "events": events}`.
   Do **not** include `snapshot_as_of_tick` here — that field is per-WS-connection, not per-tick,
   and is attached at the `stream_ws` layer in Step 4, not here (this method has no notion of which
   connection will receive its output — `_notify_listeners` fans the same dict out to every
   registered listener, see Step 3).

**Other writers to this file's shared state:** `ReadModelCache._entity_dtos` (the heavy-DTO cache
dict, `read_model_cache.py:39`) is written by `update()` (prune/invalidate, lines 102-116) and
`get_entity_dto()` (populate on miss, lines 126-139) — `compute_tick_delta` must **not** read from or
write into `_entity_dtos`, and must **not** introduce a second cache dict keyed by entity ID either
(test_plan.md's Anti-Drift Test Guards explicitly flags this exact collision risk: "a plausible
implementation mistake would be caching slim and full DTOs under the same key space by entity ID").
`present_entity_slim` calls in this method must go direct to `StatePresenter.present_entity_slim`,
uncached — the delta only ever touches the bounded dirty-entity subset per tick, so caching brings no
real benefit here and avoiding it entirely removes the collision risk rather than managing it.
`_minimal_summary` (`read_model_cache.py:38`, written by `update()` at line 97) is untouched by this
method — `compute_tick_delta` is called separately (Step 3), not from inside `update()`.

**Do NOT touch:** `update()`, `get_entity_dto()`, `get_entities_paged()`, `get_minimal_summary()`,
`reset_metrics()`, `_entity_dtos`, `_minimal_summary` — all existing cache behavior is unchanged.

**Verify:** Test Plan items 1, 2, 3, 4, 5, 8 (all target this method directly per test_plan.md's own
"Location: same file as test 1" grouping).

---

### Step 3 — Wire `V2EngineManager` to compute and conditionally broadcast the delta

**Files:** `src/api/engine_manager.py`

**Change:**
1. Add `self._latest_delta_payload: Optional[Dict[str, Any]] = None` in `__init__` near the existing
   `self._latest_snapshot: Dict[str, Any] = {}` (line 37) — a **separate** attribute, not a
   replacement for `_latest_snapshot`, because `_latest_snapshot` remains the minimal summary used by
   `get_state()` (lines 192-197, called both by `stream_ws`'s initial connect payload at
   `stream.py:56` and by the `tick` property at lines 314-317) — that shape and call path is
   explicitly unchanged by this ticket (ticket Scope only adds a *new* per-tick broadcast, it does
   not say to change the connect-time initial payload).
2. In `_update_latest_state` (lines 151-190), immediately after the existing `dirty_set`/`force_full`
   fetch and `self._read_cache.update(...)` call (lines 154-157), add:
   ```python
   self._latest_delta_payload = self._read_cache.compute_tick_delta(
       state, dirty_set, force_full, state.tick
   )
   ```
   This reuses the exact `dirty_set`/`force_full` values already fetched at lines 154-155 for
   `ReadModelCache.update()` — no duplicate fetch of `self._kernel.status.dirty_set`.
3. In `_run_loop` (lines 278-312), change line 301 from
   `self._notify_listeners(self._latest_snapshot)` to:
   ```python
   if self._latest_delta_payload is not None:
       self._notify_listeners(self._latest_delta_payload)
   ```
   This is the one and only call site of `_notify_listeners` (confirmed in investigation.md via
   `grep -rn "add_tick_listener"` — only hit besides the definition is `stream.py:52`) — re-verify
   this is still true at implementation time in case a second listener was registered elsewhere since
   investigation, per investigation.md's own Anti-Drift Hazards note.

**Other writers to `_notify_listeners`'s consumers:** `_notify_listeners` itself
(`engine_manager.py:102-108`) is not modified — it still iterates `self._listeners` and calls
`cb(payload)` for whatever `payload` it's given; only the *value* passed to it at the one call site
changes (from always-the-minimal-summary to delta-or-skip). `stream_ws`'s `on_tick` callback
(`stream.py:48-50`) is the only registered listener and is unmodified in this step (its
`queue.put_nowait(snapshot)` body doesn't care what shape `snapshot` is) — the `snapshot_as_of_tick`
merge happens downstream in Step 4, not here.

**Do NOT touch:** `get_state()`, `get_full_snapshot()`, `get_entities_paged()`, `get_entity()`,
`start()`, `stop()`, `pause()`/`resume()`/`step()`, the Prometheus metrics block (lines 159-190) —
none of these read or depend on `_latest_delta_payload`.

**Verify:** Test Plan items 3, 4 (quiet-tick suppression and heartbeat cadence, exercised through the
real `_run_loop`/`_update_latest_state` path per `tests/unit/api/test_engine_manager.py`'s existing
real-thread-loop pattern) and item 6 (listener-registration-before-snapshot ordering regression
guard).

---

### Step 4 — `stream_ws`: attach per-connection `snapshot_as_of_tick`, copy not mutate

**Files:** `src/api/ws/stream.py`

**Change:** In `stream_ws` (lines 18-78):
1. After the existing `initial_payload = manager.get_state()` call (line 56) — **do not reorder**
   relative to `manager.add_tick_listener(on_tick)` at line 52, which stays before this per the
   ticket's Scope and investigation.md's Anti-Drift Hazards — capture:
   ```python
   snapshot_as_of_tick = initial_payload.get("tick", 0) if initial_payload else 0
   ```
2. In the `while True` loop (lines 63-70), change:
   ```python
   payload = await queue.get()
   ```
   to also build a per-connection copy before sending:
   ```python
   payload = await queue.get()
   out_payload = dict(payload)
   out_payload["snapshot_as_of_tick"] = snapshot_as_of_tick
   ```
   then send `out_payload` (not `payload`) via the existing `fmt == "msgpack"` branch
   (`websocket.send_bytes(msgpack.packb(jsonable_encoder(out_payload)))`) or the JSON branch
   (`websocket.send_json(jsonable_encoder(out_payload))`) — both branches already exist unchanged
   (lines 67-70), only the variable sent changes from `payload` to `out_payload`.
   **Must copy, not mutate `payload` in place**: `_notify_listeners` (`engine_manager.py:102-108`)
   iterates all registered listeners and calls `cb(delta_payload)` with the **same** dict object for
   every listener — with multiple simultaneous `/api/v1/ws` connections, each connection's `on_tick`
   receives that identical object reference via its own `queue.put_nowait(snapshot)`
   (`stream.py:50`). If one connection's send loop wrote `payload["snapshot_as_of_tick"] = ...`
   directly onto the shared dict, every other connection reading the same object out of its own
   queue would race on that field and could observe another connection's `snapshot_as_of_tick`
   value. `dict(payload)` creates a per-connection shallow copy before the mutation, eliminating the
   race.
3. Do not add `snapshot_as_of_tick` to the one-time `initial_payload` sent at lines 57-61 — that
   payload's shape (the minimal summary) is unchanged by this ticket; only the per-tick delta
   messages that follow it carry the new field, per AC #1's wording ("plus tick and
   snapshot_as_of_tick" on the delta message itself).

**Do NOT touch:** the handshake logic (lines 30-41), `manager.add_tick_listener`/
`remove_tick_listener` calls (lines 52, 78), the `/ws/observe` handler (lines 81-141) or the
`/ws/observability/events` handler (lines 147-341) — both have their own independent
listener/queue/backpressure machinery this ticket does not touch. No import of
`AuthoritativeState`/`EntityState` is added anywhere in this file (architecture guard, Test Plan
item 9).

**Verify:** Test Plan item 6 (registration-before-snapshot ordering preserved), item 7 (msgpack
round-trip of the new delta shape including `snapshot_as_of_tick`), item 8 (`tick`/
`snapshot_as_of_tick` present and correct), item 9 (architecture guard still green).

---

### Step 5 — Add the new unit tests

**Files:** `tests/unit/api/test_read_model_cache.py` (new test cases for
`compute_tick_delta`), `tests/api/test_ws_protocol.py` (new msgpack delta round-trip test), and
either `tests/unit/api/test_engine_manager.py` or a new case in `tests/api/test_ws_protocol.py` for
the ordering-regression guard (test_plan.md leaves this location choice to implementation — pick
whichever avoids a subprocess spin-up if a unit-level drive of `add_tick_listener` + a manual
`_update_latest_state`/`_notify_listeners` call proves sufficient).

**Change:** Implement Test Plan items 1-9 exactly as specified in `test_plan.md`'s "New Tests
Required" section (function/method names there are illustrative, coverage is what's required). In
particular:
- Test 2 must construct a `DirtySet` whose `all_dirty_entities` includes an ID present in a
  prior-state fixture but **absent** from the current `state.entities` dict (a real
  `entities_remove`-style pop, not an `alive=False` flip) and assert it lands in `removed`, not
  `changed` — this is the primary guard against conflating "dead" (`combat.alive=False`, entity still
  present) with "removed" (gone from `state.entities` entirely, per `src/engine/apply.py:228-232`'s
  real `.pop()`).
- Test 5 must build two consecutive delta payloads for the same entity across two states where its
  `hp`/position changed, and assert each `changed` entry independently equals that state's true
  current value (never diff-shaped).

**Do NOT touch:** existing test bodies in `test_ws_protocol.py::test_ws_json_handshake` /
`::test_ws_msgpack_handshake`, `test_engine_manager.py`'s existing cases,
`test_state_presenter.py`'s existing cases, `test_read_model_cache.py`'s existing
`get_entity_dto`/`get_minimal_summary` cases — only add new test functions/cases, per test_plan.md's
Regression Surface requiring all of these to stay green unmodified.

**Verify:** Run the two scoped pytest commands from test_plan.md:
```
.venv/bin/python3 -m pytest tests/unit/api/ tests/architecture/test_api_read_model_guard.py -v
.venv/bin/python3 -m pytest tests/api/test_ws_protocol.py -v
```

---

### Step 6 — Update docs

**Files:** `docs/observability/read_model_service_contract.md`,
`docs/engine/contracts/frontend.md`, `tickets/inprogress/TCK-20260821-WS-ENTITY-DELTA-BROADCAST.md`
(the ticket's own `## Related Docs` line)

**Change:**
1. `docs/observability/read_model_service_contract.md`: add a new row to the `## Contract` table
   (currently `world_status`, `world_full`, `entity_status`, `entity_timeline`, `entities_paged` at
   lines 22-27) for the new read path, e.g. `tick_delta(dirty_set, force_full_scan, tick)` |
   `Per-tick entity delta or None` | `O(dirty)` | `ReadModelCache.compute_tick_delta()`. This doc's
   own stated purpose ("the unified facade for all API read paths") already covers this — this
   ticket adds a genuinely new read path through the same presenter chain.
2. `docs/engine/contracts/frontend.md`: narrow the `> Known gap (2026-07-16), narrowed 2026-08-24`
   callout (line 12) again, following the exact pattern already used when
   `TCK-20260821-REST-MAP-STATIC-STATS` narrowed it for `/map`/`/static`/`/stats`: note that a real
   per-tick entity-delta broadcast now exists on `/api/v1/ws` (not the `/api/v1/stream` SSE route
   §B describes, which does not exist in the real backend), even though `useSimulation.ts` isn't
   rewired to consume it yet (separate ticket `TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET`). Also
   update §B "Delta Sync (SSE)" (lines 41-44) to note the backend capability gap is now closed on the
   WS side, without claiming the frontend itself changed.
3. Fix the ticket's own `## Related Docs` line: it currently cites
   `docs/engine/read_model_service_contract.md`, which does not exist — correct it to
   `docs/observability/read_model_service_contract.md` (confirmed real path).

**Do NOT touch:** `docs/plans/live_map_reconnection_epic.md` (roadmap doc, not a living API
reference — matches the immediately-preceding sibling ticket's own conclusion for its own, larger
presenter changes) and `docs/mechanics/` (no chapter governs this — pure API/read-model delivery
change, not a simulation law).

**Verify:** No test verifies doc content directly; this step is verified by the Finalize phase's
`make knowledge-index-update` requirement (files under `docs/` were modified) and by manual review
that the table row/callout text is accurate against the implemented shape.

---

### Step 7 — Add a parity ledger entry for the delta-broadcast payload

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Add a new entry (next available `INFRA-NNN` ID) tracking this ticket's ported
`compute_delta()` behavior — the ACs the ticket itself already encodes as correctness properties:
`changed`/`removed` classification, absolute-not-delta `EntitySlim` values, 20-tick heartbeat
cadence, listener-before-snapshot ordering. Set `status: verified` once Step 5's tests pass, with
`v2_evidence` citing this ticket and `test_path` pointing at the new test(s) added in Step 5 (a real,
non-null `test_path` — do not leave it `null` the way the pre-existing, unrelated `INFRA-047/048/049`
entries currently are; that gap is explicitly out of this ticket's scope to fix, see Anti-Drift Notes,
but the new entry this step adds must not repeat it).

**Other writers to this file:** `docs/parity_ledger/infrastructure.yaml` is a flat YAML list appended
to by any ticket touching infrastructure-layer behavior; no other in-flight writer is known for this
specific file in this session. This step only appends one new entry — it does not edit
`INFRA-047`/`INFRA-048`/`INFRA-049` or any other existing entry.

**Do NOT touch:** `INFRA-047`, `INFRA-048`, `INFRA-049` (handshake-protocol entries, unrelated to
payload content, pre-existing `test_path: null` gap not introduced by and not to be fixed by this
ticket) or any other subsystem's YAML file (`combat_movement.yaml`, `town_resource.yaml`, etc.).

**Verify:** This step is procedural (Parity phase's job per this project's workflow, typically
executed by a `parity-updater` agent after Step 5's tests are confirmed passing) — no new test is
added by this step itself; it references Step 5's tests as its evidence.

## Scope Guards

- Do not add resource_node/building/chest/region fields to the delta payload — `DirtySet
  .all_dirty_entities` already excludes those sets by construction (`src/core/dirty.py:230-234`);
  that content remains `present_map`/`present_static`'s job (`TCK-20260821-PRESENT-MAP-STATIC`).
- Do not add a spatial-subscription/region-filtering field to the delta envelope — that is the
  separate `TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD` ticket.
- Do not reorder `stream_ws`'s listener-registration-before-snapshot sequence (lines 52 vs. 55-61).
- Do not import `AuthoritativeState` or `EntityState` (outside `TYPE_CHECKING`) anywhere in
  `src/api/ws/stream.py`, `src/api/routes/`, or `src/api/server.py`.
- Do not change the shape of the one-time initial connect payload (`manager.get_state()` /
  `initial_payload` in `stream_ws`) — it stays the minimal summary, unchanged by this ticket.
- Do not touch `/ws/observe` or `/ws/observability/events` (`stream.py:81-341`) — separate listener
  machinery, out of scope.
- Do not wire real `SimulationEvent` content into the delta's `events` field this ticket — ship
  `events: []` unconditionally (Open Design Question 1).
- Do not add `state`, `tier`, `combat_target_id`, `loot_progress`, or `loot_duration` to the V2
  `EntitySlim` shape — no confirmed V2 source exists for any of these (Open Design Question 2).
- Do not solve the 10k-entity bandwidth-scale concern (1.5-5MB/s projection) — explicitly out of
  scope, deferred to a separate gated M3 epic.
- Do not backfill `test_path: null` on the pre-existing `INFRA-047`/`INFRA-048`/`INFRA-049` entries —
  a real, unrelated, pre-existing gap noted for visibility only.
- Do not touch `docs/plans/live_map_reconnection_epic.md` or any `docs/mechanics/` chapter.

## Dependency Map

- Step 1 (presenter method) has no dependencies — can be implemented and unit-tested standalone.
- Step 2 (cache delta method) depends on Step 1 (`present_entity_slim`).
- Step 3 (engine manager wiring) depends on Step 2 (`compute_tick_delta`).
- Step 4 (stream_ws connection-level field) depends on Step 3 (the delta payload must already flow
  through `on_tick` before `snapshot_as_of_tick` can be merged onto it) but is otherwise independent
  in its own file.
- Step 5 (tests) depends on Steps 1-4 all being implemented; individual test cases can be written
  incrementally alongside each step (e.g. write Step 2's unit tests immediately after Step 2, rather
  than batching all tests to the end).
- Step 6 (docs) and Step 7 (parity ledger) depend on Steps 1-5 being complete and tests passing, but
  are independent of each other.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| On a tick where `DirtySet.all_dirty_entities` is non-empty, `/api/v1/ws` sends `changed` (slim dicts for dirty+alive entities) and `removed` (IDs gone from `state.entities`), plus `tick` and `snapshot_as_of_tick` | Steps 1, 2, 3, 4 | Test Plan items 1, 2, 8 |
| On a quiet tick (not a heartbeat), no message is sent | Steps 2, 3 | Test Plan item 3 |
| Registering listener before capturing baseline snapshot means no tick in that window is lost | Step 4 (verified unchanged), Step 3 (delta computed synchronously in `_update_latest_state` before `_notify_listeners`) | Test Plan item 6 |
| `EntitySlim` fields are always absolute current values, never deltas | Step 1 (`present_entity_slim` always reads live values), Step 2 (no diffing against prior state) | Test Plan item 5 |
| Delta payload is sent via msgpack when the client's handshake negotiated msgpack, not only JSON | Step 4 (reuses existing generic `fmt` branch in `stream_ws`'s send loop, unchanged) | Test Plan item 7 |

## Anti-Drift Notes

- **Removed vs. dead is a required test guard, not an implementation detail to skip**: V2's
  `combat.alive=False` (entity still present in `state.entities`) and actual key-removal via
  `apply.py:228-232`'s `.pop()` are two genuinely different lifecycle events. A naive implementation
  that only checks `alive` (without also checking dict presence) will silently misclassify a
  still-present-but-dead entity as "removed." Step 2's classification logic and Step 5's Test 2 are
  both written specifically to catch this. Do not simplify Step 2's three-way branch (removed /
  changed / neither) down to a two-way `alive` check.
- **The thread-safety broadcast mechanism is reused, not reinvented**: `loop.call_soon_threadsafe
  (queue.put_nowait, snapshot)` (`stream.py:50`) already correctly marshals the engine-thread-produced
  payload onto the asyncio event loop, and the bounded `asyncio.Queue(maxsize=10)` +
  `put_nowait`/`QueueFull`-drop-on-full backpressure behavior already exists and is unchanged by this
  ticket (a delta payload is generally smaller than the always-sent minimal summary over many ticks,
  so this ticket does not worsen backpressure risk). Do not add a new queue, a new thread-safety
  primitive, or a new backpressure policy — none of that is in scope.
- **`_notify_listeners`'s sole call site and sole listener must be re-verified at implementation
  time**: investigation.md confirmed (via `grep -rn "add_tick_listener"`) that `stream_ws`'s
  `on_tick` is the only registered listener anywhere in the codebase today, and `_run_loop:301` is
  the only call site of `_notify_listeners`. This plan's Step 3 assumes that remains true — if a
  second listener was added elsewhere between investigation and implementation, re-check that it can
  tolerate receiving `Optional[delta]`-shaped payloads (now sometimes skipped) instead of an
  always-fires minimal summary before proceeding.
- **The shared-dict-mutation hazard in Step 4 is the most likely regression to reintroduce**: because
  `_notify_listeners` calls every listener callback with the *same* `delta_payload` object reference
  (not a per-listener copy), any future refactor of `stream_ws`'s send loop that mutates `payload` in
  place instead of copying it first will reintroduce a cross-connection field-clobbering race under
  concurrent `/api/v1/ws` connections. Always `dict(payload)` before adding `snapshot_as_of_tick`.
- **Do not cache slim DTOs in `ReadModelCache._entity_dtos`** (the existing heavy-DTO cache, keyed by
  entity ID) — this is the exact collision test_plan.md's Anti-Drift Test Guards calls out: a slim
  and a full DTO sharing the same ID-keyed cache dict would let one silently overwrite or shadow the
  other. Step 2's design avoids this entirely by not caching slim DTOs at all.
- **`entity.identity.faction` is a plain `int`, not an enum-typed field** — nothing at the type level
  prevents an out-of-range value being stored. Step 1's `Faction(...)` conversion must handle a
  `ValueError` defensively (fallback to raw int-as-string) rather than assuming every stored value is
  a valid `Faction` member.
- **Existing subprocess tests (`test_ws_json_handshake`) assume every early tick produces a
  message** — the default spawn (10 entities, all moving) makes an empty `DirtySet` on tick 2
  extremely unlikely in practice (movement alone dirties nearly every entity nearly every tick), but
  this is a real behavioral dependency the existing test's `asyncio.wait_for(ws.recv(), timeout=5.0)`
  now has on delta content instead of an unconditional minimal-summary send. Re-run this test after
  implementation (Step 5) rather than assuming it still passes unmodified — test_plan.md's Regression
  Surface already flags this as a "must be re-run to confirm" item, not a settled fact.

## Deviations

Implementation matched this plan step-for-step with one minor deviation, found during this ticket's
second Implement turn (the first turn had already written the code but failed mid-flight on a
transient connectivity error before reaching Step 7):

- **Step 1 — `Faction` import placement**: the plan's Step 1 prose doesn't specify where the
  `Faction(entity.identity.faction).name.lower()` import should live. The as-implemented first draft
  put `from src.core.enums import Faction` inline inside `present_entity_slim`'s body. This turn
  moved it to a module-level import alongside `state_presenter.py`'s existing
  `from src.core.state import ...` line — `src/core/enums.py` has no imports back into `src.api` or
  `src.core.state`, so there is no circular-import hazard the inline placement could have been
  guarding against, and a function-local import for a plain `IntEnum` lookup is an unnecessary
  abstraction under this project's code-quality rules. No behavior change.

Step 7 (parity ledger entry `INFRA-388`) and the ticket's closing sections (Implementation Notes,
Test Summary, Files Changed, Completion Summary, Acceptance Criteria checkboxes) were completed
exactly as this plan specified — re-verifying the next available `INFRA-NNN` ID directly against the
file at write time (found `INFRA-387` as the last existing entry, added `INFRA-388`) rather than
trusting any earlier count, per the plan's own "Other writers to this file" note about this being a
shared, append-only file.
