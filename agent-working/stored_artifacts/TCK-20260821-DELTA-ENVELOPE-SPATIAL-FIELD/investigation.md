---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD
artifact_type: investigation
tags: [api-design, engine]
---

# Investigation — TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD

## Context Scan Note

Per CLAUDE.md's Hard Rule, `mcp__knowledge-search__search_docs` was called first
(`query="delta envelope spatial subscription region chunk field interest management"`) — it
returned `{"error":"index not found","action":"run make knowledge-index"}`, i.e. the semantic index
is not built in this worktree. `graphify` was checked next: the `graphify` binary exists on `PATH`
but `graphify-out/` (the built graph) does not exist in this worktree, so `graphify query` has no
graph to run against. Both tools are confirmed unavailable here, consistent with the task framing.
Fell through to the documented fallback: `docs/REGISTRY.yaml` exists, but the fastest, most precise
path to prior work was the ticket's own `## Related Tickets` (`TCK-20260821-WS-ENTITY-DELTA-BROADCAST`,
already `DONE`) plus this epic's own `SEQUENCE.md`, which name the exact prerequisite directly —
read that ticket's `tickets/done/` entry and its full `Implementation Notes` in place of a registry
scan, since it names every touched file and the exact shape produced. No other done ticket in
`tickets/done/` or `docs/REGISTRY.yaml` (`type: ticket`) has `related_code_areas` or `tags`
overlapping `src/api/ws/stream.py` / `src/api/read_model_cache.py` / `src/api/presenters/state_presenter.py`
besides `TCK-20260821-WS-ENTITY-DELTA-BROADCAST` itself and the still-open sibling tickets in this
same epic batch (`PRESENT-MAP-STATIC`, `REST-MAP-STATIC-STATS` — both touch `state_presenter.py` but
for the unrelated `/map`/`/static`/`/stats` routes, not the WS delta path).

## Current Behavior

**`src/api/ws/stream.py::stream_ws`** (lines 18-86) is the live `/api/v1/ws` WebSocket handler.
After handshake negotiation (`fmt = "json"|"msgpack"`), it registers a tick listener
(`manager.add_tick_listener(on_tick)`, line 52) *before* sending the initial full-state payload
(`manager.get_state()`, line 56) — the connect-time race fix from ticket 4. `snapshot_as_of_tick` is
captured once from the initial payload's `tick` (line 63). Inside the `while True` loop (lines 65-78),
each dequeued `payload` (the dict produced once per tick by `ReadModelCache.compute_tick_delta`, fanned
out by reference to every connected listener's queue) is copied per-connection
(`out_payload = dict(payload)`, line 72) specifically to avoid a cross-connection mutation race, then
`out_payload["snapshot_as_of_tick"] = snapshot_as_of_tick` is set (line 73) before sending. This is the
exact, already-established pattern for attaching a per-connection field to the envelope without
mutating the shared dict — the natural precedent for this ticket's new field.

**`src/api/read_model_cache.py::ReadModelCache.compute_tick_delta`** (lines 118-151) is the single
place the delta envelope's *shape* is defined: it returns exactly
`{"tick": tick, "changed": changed, "removed": removed, "events": events}` (line 151), or `None` on a
quiet, non-heartbeat tick (`tick % 20 != 0`, line 148). `changed` is built via
`StatePresenter.present_entity_slim(entity)` for every dirty, `combat.alive` entity (line 144);
`removed` is entity IDs no longer in `state.entities` at all (line 141-142). This method is called
once per tick by `V2EngineManager._update_latest_state` (`src/api/engine_manager.py:159`), not
per-connection — its output is the one shared dict fanned out to every listener.

**`src/api/presenters/state_presenter.py::present_entity_slim`** (lines 132-158) is the per-entity
projection used inside `compute_tick_delta`'s `changed` list: 9 fields (`id`, `kind`, `x`, `y`, `hp`,
`max_hp`, `level`, `faction`, `weapon_range`), always absolute current values, never a diff. It has no
region/chunk/spatial field today, and per the ticket's own AC wording (see below) it should not gain
one for this ticket.

**Test coverage on the current shape**: `tests/unit/api/test_read_model_cache.py::
test_compute_tick_delta_fields_present_and_correct` (line 188-193) asserts
`set(payload.keys()) == {"tick", "changed", "removed", "events"}` — a **strict, exhaustive key-set
equality** on `compute_tick_delta`'s own return value. This is the one existing test in the whole
regression surface that would break on any change to `compute_tick_delta`'s return dict shape.
`tests/api/test_ws_protocol.py::test_ws_msgpack_delta_payload_shape` (lines 76-109), by contrast, only
asserts individual keys are present (`"changed" in data`, `"removed" in data`, `"tick" in data`,
`"snapshot_as_of_tick" in data`) on the *fully-assembled, post-`stream_ws`* payload — it does not do
exhaustive key-set equality, so it would not break from an additional top-level key being present.

## Mechanics / Engine Constraints

No `docs/mechanics/` chapter governs this — it's transport/API plumbing, not a simulation law. The
relevant constraint is `docs/observability/read_model_service_contract.md`'s Architecture Law:
"API presenters MUST NOT mutate authoritative state" and "No raw state exposure" — a null placeholder
field satisfies both trivially (it reads nothing from state). The stronger constraint is the ticket's
own Out of Scope: no server-side filtering logic may read or act on the new field's value anywhere in
this ticket's diff (verified by a grep-for-the-field-name check at Verify time), and no
`protocol_version` bump — confirmed there is no `protocol_version` field on the WS delta envelope
today (a `protocol_version` field does exist, but only on the *separate* `/api/v1/manifest` response
per `src/api/presenters/manifest_presenter.py:32`, an unrelated endpoint from a different sibling
ticket in this epic). Adding an always-null key to an already-JSON/msgpack-encoded dict is additive by
construction — no existing consumer keys off an exhaustive field set (`useSimulation.ts` only reads
`delta.changed`, `delta.removed`, `delta.events` — see below), so no protocol break occurs.

## Where The Field Belongs: Envelope-Level, Not Per-Entity (load-bearing distinction)

The ticket's Scope is unambiguous: "Add one additional key (e.g. region or chunk) **to the delta
envelope** produced by the entity-delta broadcast path, present but null/unset **on every message**."
"Envelope" here means the top-level per-tick delta dict (`{tick, changed, removed, events,
snapshot_as_of_tick}`), the same level `tick` and `snapshot_as_of_tick` live at — **not** a new key
nested inside each dict in `changed[]` (i.e. not a `present_entity_slim` field). This matches the
epic plan doc's own framing of Scope item 7: "an unused `region`/`chunk` field **the client doesn't
yet send and the server doesn't yet honor**" — phrased as something the *client will eventually send
as a subscription request* (a per-connection concept, analogous to what `format` already is in the
handshake), not a per-entity spatial coordinate (entities already have `x`/`y` in `present_entity_slim`
for that). A per-entity field would also fail the "present but null/unset on every message" framing
awkwardly (it would need to be null on every entity in every `changed[]` list, a much odder shape than
one null key on the envelope).

**Recommended implementation site**: `src/api/ws/stream.py`, alongside the existing
`out_payload["snapshot_as_of_tick"] = snapshot_as_of_tick` line (73) — e.g.
`out_payload["region"] = None` (or whatever field name is chosen; see Open Questions). This:
- Matches the ticket's own `## Related Code Areas` exactly (`src/api/ws/stream.py`,
  `src/api/presenters/state_presenter.py`) — `src/api/read_model_cache.py` is conspicuously **not**
  listed, which is consistent with not touching `compute_tick_delta`.
- Keeps `compute_tick_delta`'s return shape (and its one exhaustive-key-set test,
  `test_compute_tick_delta_fields_present_and_correct`) completely untouched — the delta-computation
  function stays a pure function of `(state, dirty_set, force_full_scan, tick)` describing *what
  changed*, while the envelope-augmentation step in `stream_ws` (which already exists precisely to
  attach per-connection metadata to the shared dict) is where connection/subscription-shaped metadata
  belongs. This is architecturally the right split: `snapshot_as_of_tick` and the future
  region/chunk subscription field are both properties of *the connection*, not of *the tick's
  entity changes* — `compute_tick_delta` has no way to know a connection's subscription anyway.
  This also happens to satisfy the AC's "tests for the delta envelope continue to pass unmodified
  except for the new field's presence" in the strongest way: with this placement, literally zero
  existing tests require any edit at all (see Test Plan).
- Is the field genuinely null on the **initial** connect payload too, or only on the **per-tick delta**
  messages? The AC says "on every message" from "the entity-delta broadcast path" — the initial
  payload (`manager.get_state()`, sent once at line 56-61) is the pre-existing minimal-summary
  payload, not itself part of "the entity-delta broadcast path" (that path is the `while True` loop).
  Recommend: only the per-tick delta messages (inside the loop) need the field; the one-time initial
  summary payload's shape is out of scope for this ticket and untouched.

**Discrepancy flagged, not blocking**: `state_presenter.py` is listed in `## Related Code Areas` but,
under this recommended design, requires no code change — `present_entity_slim` doesn't touch envelope
assembly. This may be an over-inclusive copy from the ticket-writer (ticket 4's own Related Code Areas
list is near-identical) rather than a signal that a presenter-level change is needed. A
docstring/comment addition there (e.g. noting on `present_entity_slim` that the spatial placeholder
deliberately lives on the envelope, not per-entity, to prevent a future contributor from "fixing" this
inconsistency) is optional, not required — left for the planner to decide whether it's worth doing.

## Docs Requiring Update

- `docs/engine/contracts/api_protocol_contract.md`: Section 2 ("WebSocket Protocol (BWS)") explicitly
  enumerates the streaming payload's fields (`changed`/`removed`/`tick`/`events`, plus
  `snapshot_as_of_tick`) — this is the exact wire-envelope contract this ticket adds a key to; must
  gain a one-line mention of the new reserved, always-null field and a pointer to the future M3
  interest-management epic that will eventually populate it.
- `docs/parity_ledger/infrastructure.yaml`: the `INFRA-388` entry (added by ticket 4, `status:
  verified`, `priority: P1`) already documents this exact envelope shape in its `text`, and its
  `support_boundary` field already explicitly anticipates this: "spatial-subscription/region
  filtering are explicitly out of scope (separate follow-up tickets if ever needed)." This ticket
  changes the envelope shape INFRA-388 describes and should update `text`/`v2_evidence`/
  `support_boundary` (add `src/api/ws/stream.py`'s new line to `v2_evidence` if not already covered,
  and note the placeholder field's addition) rather than opening a new entry, since it's the same
  behavior being amended, not a new one.

The `docs/observability/read_model_service_contract.md` `tick_delta` row (path:
`docs/observability/read_model_service_contract.md`) is not required to change for this ticket under
the recommended implementation: that row's "Returns" column and "Backing" column describe
`ReadModelCache.compute_tick_delta()`'s own return shape specifically, which this ticket's recommended
design leaves untouched (the field is attached downstream in `stream_ws`, not inside
`compute_tick_delta`). If the planner instead chooses to add the field inside `compute_tick_delta`
(see Open Questions), this doc's row would need updating too — flagged here so that decision and this
doc's status travel together.

The `docs/engine/contracts/frontend.md` doc (path: `docs/engine/contracts/frontend.md`) is not
required to change for this ticket: its existing "Known gap" callout and §2 `onmessage` bullet
describe the frontend's `changed`/`removed` consumption, which is unaffected — `useSimulation.ts` is
explicitly out of scope for this ticket (Out of Scope: "client-side sending of the field"), and the
new key is additive/unused so it doesn't change what the frontend does or doesn't parse.

The `docs/guidelines/intentional_divergences.md` doc (path: `docs/guidelines/intentional_divergences.md`)
is not required to change for this ticket: this is not a divergence from the Mechanics Bible (no
`docs/mechanics/` chapter governs the WS wire protocol), and no V1 legacy behavior is being changed —
V1's own `src_legacy/api/routes/stream.py::compute_delta()` never had a spatial-subscription field
either, so there is no legacy-vs-V2 behavior gap to record.

## Parity Ledger Overlap

- `INFRA-388` (`docs/parity_ledger/infrastructure.yaml`, `status: verified`, `priority: P1`,
  `test_path: tests/unit/api/test_read_model_cache.py::
  test_compute_tick_delta_changed_includes_only_dirty_and_alive_entities`) — directly overlapping,
  see "Docs Requiring Update" above. Not `P0`, so no new mandatory passing `test_path` is forced by
  the parity-ledger rule alone, but the entry's own text becomes stale without an update since it
  currently documents the envelope as `{tick, changed, removed, events, snapshot_as_of_tick}` with no
  sixth field.
- No other `docs/parity_ledger/*.yaml` entry references `compute_tick_delta`, `present_entity_slim`,
  or `stream_ws` (grep confirmed only `INFRA-388` names these symbols).

## Prior Work

- `tickets/done/TCK-20260821-WS-ENTITY-DELTA-BROADCAST.md` and
  `stored_artifacts/TCK-20260821-WS-ENTITY-DELTA-BROADCAST/` (investigation.md, plan.md) — the direct,
  hard-dependency prerequisite. Built the envelope this ticket extends; its `plan.md` "Open Design
  Question 2" (referenced in `present_entity_slim`'s own docstring) is the precedent for how prior
  field-inclusion decisions in this exact area were documented and should be followed for this
  ticket's field-name decision too.
- `docs/plans/live_map_reconnection_epic.md` Scope item 7 and its "Bandwidth/interest-management
  reassessment" subsection under §D — the design rationale for *why* this field is being reserved now
  (10,000-entity-scale bandwidth projection of 1.5-5MB/s per viewer without interest-management
  filtering), and confirms building the filtering itself is explicitly deferred to the sibling epic
  `TCK-20260821-EPIC-LIVE-MAP-INTEREST-MANAGEMENT` (`tickets/todos/live-map-interest-management/`,
  confirmed to exist as a scope-only epic ticket, not yet broken into child tickets).
- V1 legacy precedent (`src_legacy/api/routes/stream.py::compute_delta()`, referenced but not
  re-read in full here since it's out of scope — ticket 4's investigation already covered it) never
  had a spatial-subscription field either; this is new-to-both-versions placeholder work, not a port.

## Risks and Open Questions

- **Field name/type — genuinely undecided, flagged by the ticket itself, not assumed here.** The
  ticket's own Assumptions/Open Questions section states this explicitly. Recommendation (not a
  decision): `region_id: Optional[str] = None`. Rationale: `region_id` is the naming convention
  already used consistently elsewhere in this exact codebase area — `StatePresenter.present_static`'s
  `regions[].region_id` (state_presenter.py:275), the frontend's `Region.region_id` and
  `Entity.region_id`/`current_region_id` (`frontend/src/types/api.ts:186,188,309`), and even an
  unrelated sibling WS route's existing query-param filter, `region_id`
  (`src/api/ws/stream.py:220-221`, a different endpoint, `/ws/observability/events` — same name, no
  namespace collision since it's a different message type). A bare `"chunk"` key would be defensible
  too (matches "chunk" language in the epic doc) but has no existing naming precedent anywhere in this
  codebase to anchor to. This is a real decision for the planner/ticket, not something to lock in
  silently here.
- **Placement decision (envelope-assembly site) is a recommendation, not certainty.** The case above
  (stream.py, alongside `snapshot_as_of_tick`) is architecturally the cleaner fit and requires zero
  test edits, but an equally defensible reading of `## Related Code Areas` not including
  `read_model_cache.py` is simply an oversight by the ticket-writer (ticket 4's own list also wasn't
  perfectly exhaustive against its actual Files Changed — it omitted nothing there, but this ticket's
  list is shorter than what ticket 4 needed). If the planner instead places the field inside
  `compute_tick_delta`'s return dict, `test_compute_tick_delta_fields_present_and_correct`'s exhaustive
  `set(payload.keys())` assertion **will** need a one-line update to include the new key — permitted
  by the AC's "except for the new field's presence" clause, but not "unmodified," so it's a strictly
  larger test-touch footprint than the stream.py placement. Flagging so the planner makes this call
  deliberately rather than by default.
- **`state_presenter.py`'s inclusion in Related Code Areas may not require any diff at all** under the
  recommended design — see "Discrepancy flagged" above. Not a blocker; a planner call.

## Anti-Drift Hazards

- **The single easiest way to violate this ticket's Out of Scope**: writing the new field with any
  value other than a literal `None`/`null` "for convenience" (e.g. defaulting it to the entity's own
  region derived from `region.bounds`/`state.regions`, since `present_static`'s `present_region`
  logic for deriving a region from coordinates already exists nearby and would be an easy, wrong,
  "helpful" shortcut) — this would silently cross into the M3 interest-management epic's scope and
  violate AC #3's "no server-side filtering logic reads or acts on the new field's value" (a derived,
  non-null value is itself a form of using the field, even with no filtering attached yet — and
  "unset on every message" in the AC is explicit that it must stay null).
- **Do not thread the field through `compute_tick_delta`'s `candidate_ids`/`changed`/`removed` loop**
  — there's no reason to iterate per-entity for an envelope-level null constant, but the proximity of
  `present_entity_slim` (which does have `x`/`y`) makes it an easy, wrong place to reach for if someone
  interprets "spatial" as "belongs near the other spatial fields."
- **Do not add a `protocol_version` field while touching this envelope** — the ticket AC is explicit
  ("no protocol_version bump — must be additive-only"), and the epic doc's §A "Data Manifest" section
  discusses a `protocol_version`/`dictionary_version` split for the *separate* `/api/v1/manifest`
  endpoint; conflating the two during implementation would be scope creep into a different sibling
  ticket's territory (`TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT`).
- **The `dict(payload)` copy-before-mutate discipline in `stream_ws` (line 72) must be preserved** —
  any new field assignment must happen on `out_payload`, never on the shared `payload` object (which
  is the same dict instance fanned out by reference to every connected listener's queue); mutating
  `payload` directly would reintroduce the cross-connection mutation race ticket 4 specifically fixed.
