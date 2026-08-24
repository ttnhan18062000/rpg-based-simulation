---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260821-WS-ENTITY-DELTA-BROADCAST
artifact_type: investigation
tags: [api-design, engine]
---

# Investigation — TCK-20260821-WS-ENTITY-DELTA-BROADCAST

## Search-Before-Grep Compliance

Attempted, in order, per this project's mandatory Context Scan, before any grep/file read:
1. `mcp__knowledge-search__search_docs(query="WebSocket entity delta broadcast stream")` →
   `{"error": "index not found", "action": "run make knowledge-index"}`.
2. `graphify query "entity delta broadcast websocket"` → `error: graph file not found:
   .../graphify-out/graph.json` (no `graphify-out/` directory exists in this worktree at all).
3. Fallback: `python3 tools/knowledge_search.py query "entity delta broadcast websocket dirty set"
   --top-k 5` → `knowledge index not found — run make knowledge-index`.

All three semantic-search tools are confirmed unavailable in this worktree (same finding as the
prior two child tickets in this batch, per their own investigation.md files). Fell through to the
documented fallback: direct reads of the ticket, epic plan doc, prior sibling-ticket stored
artifacts (`stored_artifacts/TCK-20260821-PRESENT-MAP-STATIC/`), and source.

## Current Behavior

### `/api/v1/ws` today sends only the minimal summary, every tick, unconditionally

`src/api/ws/stream.py::stream_ws` (lines 18-78):
- Accepts the connection, does a JSON handshake (`{"type":"handshake","format":"json"|"msgpack"}`),
  stores negotiated `fmt`.
- Registers `on_tick` via `manager.add_tick_listener(on_tick)` (line 52) **before** fetching and
  sending `initial_payload = manager.get_state()` (lines 55-61) — the connect-time ordering the
  ticket's Scope requires "already correct... do not reorder" is verified true in the current code
  as-is.
- `on_tick(snapshot)` (lines 48-50): `loop.call_soon_threadsafe(queue.put_nowait, snapshot)` — this
  callback runs on the engine's background thread (see below), and is already correctly marshaled
  onto the asyncio event loop via `call_soon_threadsafe`.
- The `while True: payload = await queue.get(); send(...)` loop (lines 63-70) already branches on
  `fmt` to choose `websocket.send_bytes(msgpack.packb(jsonable_encoder(payload)))` vs
  `websocket.send_json(jsonable_encoder(payload))` — **generically, for whatever `payload` is
  dequeued**. This means AC #5 (route the new delta payload through the negotiated msgpack format)
  is structurally already satisfied by this loop as long as the new delta dict is what flows through
  `on_tick`'s queue — no new msgpack-specific wiring is needed in `stream.py` itself. (The epic plan
  doc's "Real-Time Transfer" section states msgpack is negotiated "but never sent" — that claim does
  not match the code as it stands today; the code already sends msgpack per-tick when negotiated.
  Worth flagging as a stale claim in the epic doc, not a real gap.)

**What `snapshot` actually is today**: `V2EngineManager._run_loop` (src/api/engine_manager.py:301)
calls `self._notify_listeners(self._latest_snapshot)` unconditionally, every tick.
`self._latest_snapshot` is set in `_update_latest_state` (line 157) to
`self._read_cache.get_minimal_summary()` = `StatePresenter.present_minimal(state)` =
`{tick, world_time, entities_count, maturity, seed}` (`src/api/presenters/state_presenter.py:14-22`).
So today, every single tick, the WS connection is sent this same 5-field summary dict — never entity
positions, never changed/removed lists, never a quiet-tick skip. This confirms the ticket's Request
Summary precisely.

### The engine tick loop runs on a background thread — confirmed, matches ticket 3's finding

`V2EngineManager.start()` spawns `self._thread = threading.Thread(target=self._run_loop, name=
"v2-engine-loop", daemon=True)` (engine_manager.py:245). `_run_loop` (lines 278-312) calls
`self._kernel.tick_once()`, then `self._update_latest_state(...)`, then `self._notify_listeners(...)`
— all on that background thread, not the asyncio event loop thread FastAPI/uvicorn runs on. This is
exactly why `stream_ws`'s `on_tick` callback must (and already does) use
`loop.call_soon_threadsafe(queue.put_nowait, snapshot)` rather than a plain `asyncio.Queue.put`
call, which is not thread-safe to call from a non-event-loop thread. **Any new delta-computation
logic added to this path must run synchronously on the engine thread** (it needs `self._kernel.state`
and the tick's `DirtySet`, both only available there) and must hand its finished dict to listeners
the same thread-safe way the existing code already does — no new thread-safety mechanism needs
inventing, the existing `call_soon_threadsafe` + bounded `asyncio.Queue(maxsize=10)` pattern already
covers a slow-consumer/backpressure case (queue silently drops via `put_nowait`'s `QueueFull`
being uncaught here — see Risks).

`_notify_listeners` (engine_manager.py:102-108) is called from **only one** call site
(`_run_loop`, line 301) and has **only one** registered listener in the entire codebase today
(`stream_ws`'s `on_tick`, confirmed via `grep -rn "add_tick_listener" src/ tests/` — the only hit
besides the definition itself is `stream.py:52`). This matters for design: repurposing what gets
passed to tick listeners (from the minimal-summary dict to a delta-or-None payload) has exactly one
real consumer to keep correct — no other subsystem depends on `add_tick_listener`'s current payload
shape or always-fires-every-tick semantics.

### DirtySet is already computed and available at the exact point needed

`_update_latest_state` (engine_manager.py:151-156) already fetches `dirty_set =
getattr(self._kernel.status, "dirty_set", None)` and `force_full_scan = getattr(self._kernel.status,
"force_full_scan", False)`, and passes both into `self._read_cache.update(state, dirty_set,
force_full)`. `DirtySet.all_dirty_entities` (`src/core/dirty.py:230-234`) unions
movement/combat/inventory/strategic/social/lifecycle/biological/attribute entity-id sets — this is
the exact "what changed" source the ticket's Scope names.

**Removed entities show up in `all_dirty_entities` too, but gone from `state.entities`**: confirmed
at `src/core/dirty.py:353-355` (`DirtySetBuilder.mark_from_update`) — `union_ids` (built from
`update.entities_add` and `update.entities_remove`) is unioned into every one of the domain sets
(`movement_entities=movement | union_ids`, etc. — `DirtySet.from_update`, lines 357-365), so a
removed entity's ID is present in `all_dirty_entities`. Confirmed separately that removal is a real
delete, not just an `alive=False` flag flip: `src/engine/apply.py:228-232` —
`if update.entities_remove: ... new_entities.pop(e_id, None)`. This means the delta-computation
logic can iterate `dirty_set.all_dirty_entities` once and classify each ID by whether it's still in
`state.entities` (and alive) — "changed" — or not — "removed" — matching AC #1's "removed (IDs gone
from state.entities)" wording exactly.

**Aliveness filter precedent**: `entity.combat.alive` (bool, `CombatComponent`, `src/core/state.py`
~line 309) is the existing project-wide alive filter — already used identically in
`StatePresenter.present_stats`'s `alive_count = sum(1 for e in state.entities.values() if
e.combat.alive)` (added by the immediately-preceding sibling ticket, TCK-20260821-REST-MAP-STATIC-STATS)
and matches V1's own `_snapshot_to_slim_dict`'s `if not e.combat.alive: continue` filter verbatim.
"Changed" should use this same filter (dirty AND `combat.alive`), consistent with both V1 and the
newest V2 precedent.

### No EntitySlim-equivalent presenter/cache method exists in V2 — confirmed, not just assumed

`StatePresenter` (`src/api/presenters/state_presenter.py`) has `present_minimal`, `present_full`,
`present_entity` (the full/heavy DTO — combat, inventory, strategic, quests, social, navigation,
biological, identity, intent_results, ~90 lines), `present_region`, `terrain_code_map`, `present_map`,
`present_static`, `present_stats`. **No slim/lightweight per-entity method exists.**
`ReadModelCache.get_entity_dto` (`src/api/read_model_cache.py:126-139`) wraps `present_entity` (the
heavy one) with per-entity-ID caching keyed by dirty invalidation — also not slim. The ticket's own
Assumptions section ("No existing slim-entity cache/dict comparable to V1's `_snapshot_to_slim_dict`
exists") is confirmed correct, not speculative. A new `StatePresenter` method (e.g.
`present_entity_slim`) plus either a new `ReadModelCache` method or a manager-level delta-building
method (see Anti-Drift Hazards for the read-model-service-contract implication) is required, not
optional wiring of something pre-existing.

**V1's `EntitySlimSchema` field list** (`git show 677abbfb^:src_legacy/api/schemas.py:387-407`), for
reference against the frontend's still-live `EntitySlim` TypeScript interface
(`frontend/src/types/api.ts:88-103`, fields match V1's schema exactly): `id, kind, display_name, x,
y, hp, max_hp, state, level, tier, faction, weapon_range, combat_target_id, loot_progress,
loot_duration`. Checked each against actual V2 `EntityState`/component fields
(`src/core/state.py`) for a direct source:

| Field | V2 source found? |
|---|---|
| `id`, `kind` | Direct (`entity.id`, `entity.kind`) |
| `x`, `y` | Direct (`entity.position` property, line 760, returns `navigation.position`) |
| `hp`, `max_hp` | Direct (`entity.combat.hp`, `.max_hp`) |
| `level` | Direct (`entity.identity.evolution_level`) |
| `faction` | Present but typed `int` (`IdentityComponent.faction: int = 0 # Faction.HERO_GUILD`), not the frontend's `string` — needs a mapping decision, not a straight passthrough |
| `state` (behavior/AI status label) | **No direct source found.** No enum/string field on any component reads as a generic "what is this entity currently doing" label. |
| `tier` | **No direct source found** on any entity component (same drop/derive gap class ticket 1 hit for chest `tier`). |
| `weapon_range` | Candidate: `entity.combat.range` (`CombatComponent.range: int = 1`) — plausible but not confirmed as semantically identical to V1's `weapon_range`. |
| `combat_target_id` | **No direct source found.** `shared_target_id`/`escort_target_id` exist but on a different component (group/escort context, `src/core/state.py:557,568`), not a per-entity "who am I currently attacking" field. |
| `loot_progress`, `loot_duration` | **No direct source found** — no loot-timer concept located on `EntityState` or its components. |
| `display_name` | Not in the frontend's `EntitySlim` interface at all (frontend dropped it) — can likely be dropped from the V2 slim shape too. |

**This is a real, non-trivial drop-vs-derive decision set**, same class of work as ticket 1's
building/chest/resource-node field gaps — flagged here with the fields actually checked so the plan
phase doesn't have to re-derive this table, but the actual per-field decision is left to planning,
not decided here (per this project's Uncertainty Rule: "vague leads stay vague until evidence
narrows them").

### `events` field — AC omits it, Scope mentions it; frontend tolerates its absence

Ticket Scope line 33 says the broadcast should carry "(changed/removed/events)", but the enumerated
Acceptance Criteria (bullet 1) only lists `changed`, `removed`, `tick`, `snapshot_as_of_tick` —
`events` is not mentioned in any AC. Checked the frontend consumer for how strictly it depends on
`events` being populated: `frontend/src/hooks/useSimulation.ts:159` —
`if (delta.events && delta.events.length > 0) { ... }` — this guards on both existence and non-empty
length, so an absent key or an empty array is handled safely; nothing breaks if `events` is always
`[]`. V2 does have a separate, already-wired event-listener mechanism (`add_event_listener`,
`_event_listeners`, used today only by the separate `/ws/observe` endpoint) that could in principle
populate this field with real content, but wiring that in is materially more scope (a second
listener registration + merge logic) than what any AC actually tests. **Flagged as an open
question for the plan phase**, not resolved here: ship `events: []` unconditionally (shape-complete,
zero behavior risk, matches what the AC actually tests) vs. wire real `SimulationEvent` content
into it (matches the Scope line's letter, more surface area, untested by any AC).

## Mechanics / Engine Constraints

No `docs/mechanics/` chapter governs this — this is a pure API/read-model delivery-layer change, not
a simulation law (no formula, no entity behavior, no economic/combat rule changes). The relevant
constraint is architectural, not mechanics-bible: `docs/observability/read_model_service_contract.md`
(see Docs Requiring Update — the ticket's own Related Docs cites this at the wrong path,
`docs/engine/read_model_service_contract.md`, which does not exist; the real file lives under
`docs/observability/`) — "No API route, WebSocket handler, or external consumer may access
`AuthoritativeState` directly. All responses must be shaped through this service or the equivalent
`V2EngineManager` methods (which delegate to `ReadModelCache → StatePresenter`)." The architecture
guard test enforcing this, `tests/architecture/test_api_read_model_guard.py`, AST-scans
`src/api/routes/`, `src/api/ws/`, and `src/api/server.py` for any top-level import of
`AuthoritativeState` or `EntityState` outside a `TYPE_CHECKING` block — `src/api/ws/stream.py` is
directly inside this guard's scanned root, so the delta-building logic must live in
`src/api/engine_manager.py` (which already imports `AuthoritativeState` freely, outside the guarded
roots) and/or `StatePresenter`/`ReadModelCache`, never in `stream.py` itself. This matches the
ticket's own Scope wording ("never touching AuthoritativeState fields directly in src/api/ws/")
exactly — the ticket author already anticipated this constraint correctly.

## Docs Requiring Update

- `docs/observability/read_model_service_contract.md`: its `## Contract` table enumerates every
  read-path method backed by `ReadModelCache → StatePresenter` (`world_status`, `world_full`,
  `entity_status`, `entity_timeline`, `entities_paged`); this ticket adds a genuinely new read path
  (the per-tick delta payload) through the same presenter chain and the table should gain a row for
  it, consistent with the doc's own stated purpose ("the unified facade for all API read paths").
  Note: the ticket's own `## Related Docs` cites this file at `docs/engine/read_model_service_contract.md`,
  which does not exist — the real path is `docs/observability/read_model_service_contract.md` (see
  Risks and Open Questions).
- `docs/engine/contracts/frontend.md`: its `> Known gap (2026-07-16), narrowed 2026-08-24` callout
  and its §B "Delta Sync (SSE)" section both describe the frontend's still-unrewired `EventSource`
  contract against `/api/v1/stream` (a route that does not exist in the real backend — confirmed by
  the epic doc's own route-surface grep). This ticket closes the backend-capability half of that gap
  (a real per-tick entity-delta broadcast now exists, on `/api/v1/ws`, not `/api/v1/stream`) even
  though `useSimulation.ts` itself isn't rewired to consume it yet (that's the separate, dependent
  ticket `TCK-20260821-REWIRE-USESIMULATION-WEBSOCKET`). The callout should be narrowed again to
  reflect this, matching the exact pattern already used when `TCK-20260821-REST-MAP-STATIC-STATS`
  narrowed it for `/map`/`/static`/`/stats`.
- `docs/parity_ledger/infrastructure.yaml`: no existing entry tracks the entity-delta-broadcast
  payload shape or its correctness properties (grepped `stream_ws|add_tick_listener|on_tick` across
  every `docs/parity_ledger/*.yaml` — no hits; the three WS-related P0 entries that do exist,
  INFRA-047/048/049, are scoped to handshake-protocol compatibility only, not payload content — see
  Parity Ledger Overlap). This is a direct legacy-behavior port (V1's `compute_delta()`), and the
  ticket's own ACs encode real, previously-external-reviewed correctness properties (connect-time
  listener-before-snapshot ordering, EntitySlim fields always absolute never delta, 20-tick
  heartbeat cadence) that are exactly the kind of law the parity ledger exists to track per this
  project's Authoritative Mechanics Rule ("If no entry exists, add one"). A new entry should be
  added once implemented, with a real `test_path` (Parity phase's job, not decided here).

`docs/plans/live_map_reconnection_epic.md` (path: `docs/plans/live_map_reconnection_epic.md`, under
`docs/`) is not required to change for this ticket: it is a roadmap/scope-planning document, not a
living API reference — confirmed by the immediately-preceding sibling ticket's own investigation,
which reached the same conclusion for its own (larger) presenter changes ("it's a roadmap doc, not a
living API reference"). No implementation happens on the epic doc itself per its own "Acceptance
Signal for This Epic" section.

## Parity Ledger Overlap

- **INFRA-047** ("WebSocket endpoint still supports legacy handshake semantics"), **INFRA-048**
  ("JSON handshake mode remains supported"), **INFRA-049** ("MessagePack handshake mode remains
  supported") — all P0, `docs/parity_ledger/infrastructure.yaml` (~lines 501-520). All three are
  scoped to the **handshake protocol itself**, not the per-tick payload shape this ticket changes —
  this ticket does not alter `stream_ws`'s handshake negotiation logic at all, so these entries'
  described behavior is not directly modified. **Flagged as pre-existing gap, not introduced by this
  ticket**: all three already carry `test_path: null` today, despite being P0 (which per this
  project's rule "P0 entries require a passing test_path" is already a gap before this ticket
  touches anything). `tests/api/test_ws_protocol.py::test_ws_json_handshake` and
  `::test_ws_msgpack_handshake` do exercise both handshake modes end-to-end today and would be a
  reasonable `test_path` to backfill onto these three entries — but backfilling a pre-existing,
  unrelated gap is not this ticket's stated scope and is noted here for visibility, not committed to.
- No entry currently exists for the delta-broadcast payload content itself (see Docs Requiring
  Update above) — this is a gap, not a divergence to reconcile.

## Prior Work

- `stored_artifacts/TCK-20260821-PRESENT-MAP-STATIC/investigation.md` and `plan.md` — direct sibling
  precedent for exactly this kind of work: porting a legacy `src_legacy/api/` shape onto V2's
  `StatePresenter`/`ReadModelCache`, including the drop-vs-derive field-gap methodology this
  investigation reused above for the `EntitySlim` field table, and the precedent that "no docs
  required" is a real, defensible outcome for a pure new-presenter-method change (not applicable
  here in full, since this ticket's read_model_service_contract.md and frontend.md hits are genuine,
  but the reasoning pattern — check every doc directory, don't assume — was followed the same way).
- `stored_artifacts/TCK-20260821-REST-MAP-STATIC-STATS/` (referenced but not fully read in this
  pass — confirmed via `present_stats`'s docstring in `state_presenter.py` that it added the
  `combat.alive` filter precedent this investigation reuses for the "changed" set's aliveness
  filter, and added `V2EngineManager.total_spawned`/`total_deaths` counters).
- Legacy reference implementation (fully recoverable, not live code):
  `git show 677abbfb^:src_legacy/api/routes/stream.py` — `compute_delta()`'s exact diff/heartbeat
  logic (diff two `dict[int, EntitySlimSchema]` snapshots into changed/removed, skip empty ticks
  unless `tick % 20 == 0`) and `_snapshot_to_slim_dict()`'s `combat.alive` filter, both read and
  cited above. `git show 677abbfb^:src_legacy/api/schemas.py:387-407` — `EntitySlimSchema`'s field
  list, used for the drop-vs-derive table above.

## Risks and Open Questions

- **Ticket's own `## Related Docs` cites a path that does not exist**:
  `docs/engine/read_model_service_contract.md`. The real file is
  `docs/observability/read_model_service_contract.md` (confirmed via `find`). This should be
  corrected when the ticket is updated during implementation — a minor metadata gap, not a scope
  problem, but worth fixing so `## Related Docs` stays accurate.
- **`events` field scope is genuinely ambiguous** (Scope mentions it, AC doesn't test it, frontend
  tolerates its absence) — see "Current Behavior" above. Recommend the plan phase explicitly decide
  and state which of the two options (always-empty-list vs. real event-wiring) it is choosing, since
  this is exactly the kind of "multiple valid implementations" case this project's Clarification Rule
  says should be resolved explicitly, not silently defaulted.
- **`EntitySlim` field drop-vs-derive decisions are not pre-resolved** (see field table above) — six
  of fourteen V1 fields (`state`, `tier`, `weapon_range` [uncertain], `combat_target_id`,
  `loot_progress`, `loot_duration`) have no confirmed direct V2 source. This is real, scoped design
  work for the plan phase, flagged precisely (per this project's Uncertainty Rule) rather than
  guessed at here.
- **Backpressure/slow-consumer behavior is pre-existing and unchanged by this ticket, but worth
  naming**: `queue = asyncio.Queue(maxsize=10)` (stream.py:43) combined with
  `queue.put_nowait(snapshot)` inside `on_tick` (called via `call_soon_threadsafe`, so its own
  exceptions are swallowed by the event loop's exception handler, not raised back to the engine
  thread) means a slow WS consumer whose queue fills will silently drop tick payloads once `put_nowait`
  raises `QueueFull` inside the scheduled callback. This is already true today for the minimal-summary
  payload and is not changed or worsened by adding a delta payload of similar or smaller size (a
  delta is bounded by dirty-entity count, generally smaller than an unconditional every-tick minimal
  summary in aggregate over many ticks) — noted for completeness, not a new risk this ticket
  introduces, and explicitly out of this epic's stated scope to solve (see epic doc's "Explicitly not
  adopted wholesale" section on backpressure playbooks).
- **`entity.identity.faction` is `int`-typed** (`IdentityComponent.faction: int = 0 #
  Faction.HERO_GUILD`) while the frontend's `EntitySlim.faction` is `string` — a mapping decision
  is needed (likely an enum-name lookup), not a bare passthrough; flagged so the plan phase doesn't
  discover this as a runtime type mismatch instead of a design decision.

## Anti-Drift Hazards

- **Do not reorder `stream_ws`'s listener-registration-before-snapshot sequence** (lines 52 vs.
  55-61) — already correct, ticket Scope explicitly says preserve it, and it is the exact fix an
  external design review flagged as a real correctness requirement (registering the tick-listener
  callback before taking the snapshot avoids a genuine "deltas arriving between snapshot and
  subscribe are lost" race, per the epic doc's §D). Any refactor of `stream_ws` to plumb the new
  delta logic through must keep this ordering intact and ideally add or preserve a test that would
  catch a reordering regression (see test_plan.md).
- **Do not touch `AuthoritativeState`/`EntityState` from `src/api/ws/stream.py`** — the architecture
  guard test (`tests/architecture/test_api_read_model_guard.py`) will fail CI on any non-
  `TYPE_CHECKING` import of either name from that file (or `src/api/routes/`, `src/api/server.py`).
  All delta-building logic belongs in `engine_manager.py` and/or `StatePresenter`/`ReadModelCache`.
- **Do not change `_notify_listeners`'s calling frequency without checking for other consumers
  first** — today it's safe to change what's passed (dict → Optional[dict]) since `stream_ws`'s
  `on_tick` is the only registered listener anywhere in the codebase, but this should be re-verified
  at implementation time in case a listener was added elsewhere between investigation and
  implementation.
- **Do not conflate this ticket's `/api/v1/ws` delta broadcast with the separate `/ws/observe` and
  `/ws/observability/events` endpoints** in the same file (`stream.py:81-341`) — both already have
  their own independent listener/queue/backpressure machinery (event-listener-based, and a
  `LiveEventPublisher`/`LiveEventSubscriber` pub-sub system respectively) that this ticket's scope
  does not touch. Only the first `@router.websocket("/ws")` handler (`stream_ws`, lines 18-78) is in
  scope.
- **Do not let bandwidth/scale concerns creep into this ticket's scope** — the ticket's own
  Assumptions section already correctly flags the 10k-entity 1.5-5MB/s projection as explicitly out
  of scope (a separate gated M3 epic per the epic doc's roadmap reference). Do not add interest-
  management, region filtering, or the spatial-subscription envelope field (that's the explicitly
  separate, dependent ticket `TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD`).
- **`resource_node`/`building`/`chest` state changes must not leak into this delta** — the ticket's
  own Out of Scope is explicit that `DirtySet` only covers entity-domain sets here and that
  remains `present_map`/`present_static`'s job. `DirtySet` does separately track
  `resource_node_ids`/`building_ids`/`chest_ids` etc. (`src/core/dirty.py:223-228`) — easy to
  accidentally pull one of those sets into `all_dirty_entities`-style iteration by mistake since
  they live on the same dataclass; `all_dirty_entities`'s own property definition
  (`src/core/dirty.py:230-234`) already correctly excludes them (it only unions the
  entity-scoped sets), so using that property directly rather than hand-rolling a union is the safe
  choice.
