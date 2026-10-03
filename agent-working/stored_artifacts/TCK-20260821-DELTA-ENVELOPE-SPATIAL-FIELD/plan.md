---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD
artifact_type: plan
tags: [api-design, engine]
---

# Implementation Plan — TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD

## Summary

Add one always-null placeholder key, `region_id: Optional[str] = None`, to the per-tick WS delta
envelope assembled in `src/api/ws/stream.py::stream_ws`, at the same line that already attaches
per-connection metadata (`out_payload["snapshot_as_of_tick"] = snapshot_as_of_tick`, line 73). The
field reserves wire-protocol space for the future M3 interest-management epic
(`TCK-20260821-EPIC-LIVE-MAP-INTEREST-MANAGEMENT`) without building any filtering logic now.
`src/api/read_model_cache.py::ReadModelCache.compute_tick_delta` (the function that defines the
delta's core `{tick, changed, removed, events}` shape, `read_model_cache.py:151`) is deliberately
**not** touched — the new field is connection-shaped metadata, the same category as
`snapshot_as_of_tick`, not part of "what changed this tick." This placement requires zero edits to
the one exhaustive-key-set test on `compute_tick_delta`'s return value
(`test_compute_tick_delta_fields_present_and_correct`), keeping the diff and test-touch footprint
minimal. `src/api/presenters/state_presenter.py` is touched only optionally, for a documentation
comment — no functional change, since `present_entity_slim` operates per-entity inside `changed[]`,
not at the envelope level where this field belongs.

## Design Decisions (resolving investigation.md's Open Questions)

### Decision 1 — Field name and type: `region_id: Optional[str] = None`

**Resolved as recommended in investigation.md.** Citations for the naming precedent:
- `src/api/presenters/state_presenter.py:275` — `present_static`'s `regions[]` list already emits
  `"region_id": region.id` (string region identifier) for every region.
- `src/api/ws/stream.py:220-221` — `stream_live_events_ws` (the `/ws/observability/events` route,
  **not** `/ws/observe` — corrected per architecture-review; `/ws/observe` only filters by
  `entity_id`) already accepts and parses a `region_id` query-string filter (`if "region_id" in
  websocket.query_params: region_id = websocket.query_params["region_id"]`). Different endpoint,
  different message type — no namespace collision — but it establishes `region_id` as the
  codebase's existing name for this concept on a WS route in the same file.
- Frontend precedent (cited in investigation.md, not re-verified here since frontend changes are
  explicitly out of scope for this ticket): `frontend/src/types/api.ts` already types
  `Region.region_id` and `Entity.region_id`/`current_region_id`.

`Optional[str]` (not a bounding box, coordinate pair, or int) because a string ID is the shape
`region_id` already has everywhere else in this codebase (region IDs, not raw coordinates, are
what regions are addressed by) — a future interest-management filter naturally keys off a region ID
the same way `/ws/observe`'s existing filter already does. No competing convention was found in the
investigation; not treated as a genuinely open call.

### Decision 2 — Implementation site: `src/api/ws/stream.py`, not `read_model_cache.py`

**Resolved as recommended in investigation.md.** Rationale, with citations:
- `read_model_cache.py:151` — `compute_tick_delta` returns exactly `{"tick": tick, "changed":
  changed, "removed": removed, "events": events}`. This is a pure function of `(state, dirty_set,
  force_full_scan, tick)` — it has no notion of an individual connection's subscription state, so a
  connection-shaped placeholder field does not belong in its return value.
- `stream.py:72-73` already establishes the precise architectural pattern needed: `out_payload =
  dict(payload)` (copy-before-mutate, to avoid a cross-connection race on the shared dict fanned out
  by `_notify_listeners`) followed by `out_payload["snapshot_as_of_tick"] = snapshot_as_of_tick`
  (attaching per-connection metadata). `region_id` is the same category of thing —
  connection/subscription metadata, not "what changed this tick" — so it is added the same way,
  immediately after that line.
- Zero-test-collateral-damage: `tests/unit/api/test_read_model_cache.py::
  test_compute_tick_delta_fields_present_and_correct` (line 188-193) does `assert
  set(payload.keys()) == {"tick", "changed", "removed", "events"}` — a strict, exhaustive
  equality check directly on `compute_tick_delta`'s return value. Leaving `compute_tick_delta`
  untouched means this test requires no edit at all, satisfying test_plan.md's stated preference
  and the AC's "tests for the delta envelope continue to pass unmodified except for the new field's
  presence" in the strongest available way (here: not even that — zero existing tests change).
- Ticket's own `## Related Code Areas` names `src/api/ws/stream.py` and
  `src/api/presenters/state_presenter.py` but not `src/api/read_model_cache.py`, consistent with
  this placement.

## Steps

### Step 1 — Add the `region_id` placeholder key to the per-tick delta envelope

**Files:** `src/api/ws/stream.py`

**Change:** In `stream_ws`, immediately after the existing line
`out_payload["snapshot_as_of_tick"] = snapshot_as_of_tick` (stream.py:73), add:

```python
out_payload["region_id"] = None
```

This executes inside the `while True:` loop (stream.py:65-78), so it runs once per per-tick delta
message sent to each connection, on `out_payload` (the per-connection copy created at line 72 via
`dict(payload)`), never on the shared `payload` object that `_notify_listeners` fans out by
reference to every connected listener's queue. This preserves the existing copy-before-mutate
discipline that ticket `TCK-20260821-WS-ENTITY-DELTA-BROADCAST` established specifically to prevent
a cross-connection mutation race — do not assign to `payload` directly.

The one-time initial connect payload (`manager.get_state()`, sent at stream.py:56-61, before the
loop) is **not** touched — per investigation.md, the AC's "on every message" scopes to "the
entity-delta broadcast path" (the `while True` loop), and the initial payload is a separate,
pre-existing minimal-summary payload whose shape is out of scope for this ticket.

**Other writers to this shared resource:** `out_payload` is a fresh per-connection local dict
(`dict(payload)`, line 72) — no other code path writes to it. The only other writer touching the
underlying shared `payload` dict before the copy is
`ReadModelCache.compute_tick_delta` (`read_model_cache.py:118-151`), called once per tick by
`V2EngineManager._update_latest_state` (`src/api/engine_manager.py:159`) — that function is
addressed explicitly in Step 2 (left untouched) so there is no double-write or ordering conflict:
`compute_tick_delta` builds the base dict once per tick; `stream_ws` augments a private copy of it
once per connection per tick. This is the same non-conflicting relationship `snapshot_as_of_tick`
already has with `compute_tick_delta`'s output.

**Do NOT touch:**
- `manager.get_state()` / the initial-payload send path (stream.py:56-61) — out of scope, see above.
- Any other WS route in this file (e.g. `/ws/observe` at stream.py:89+, or its `region_id`
  query-param handling at stream.py:220-221) — unrelated message type, do not rename or repurpose
  its `region_id` local variable or merge the two concepts.
- The `fmt == "msgpack"` vs `fmt == "json"` branching (stream.py:75-78) — no change needed; both
  branches already serialize whatever is in `out_payload` via `jsonable_encoder`, so the new key
  flows through both encodings automatically.

**Verify:**
- `tests/api/test_ws_protocol.py::test_ws_msgpack_delta_payload_shape` (extended per Step 3 to
  assert `data["region_id"] is None`) — the msgpack-format case.
- New test `test_ws_delta_envelope_includes_null_spatial_placeholder_field` (Step 3) — the json
  case.

### Step 2 — Confirm `compute_tick_delta` remains untouched (no-op step, explicit scope guard)

**Files:** `src/api/read_model_cache.py` (read-only confirmation, no diff)

**Change:** None. This step exists to make explicit that
`ReadModelCache.compute_tick_delta` (`read_model_cache.py:118-151`) is deliberately left unmodified
per Decision 2 above. Its return statement stays exactly `return {"tick": tick, "changed": changed,
"removed": removed, "events": events}` (line 151) — no sixth key added here.

**Other writers to this shared resource:** `compute_tick_delta` is called once per tick, exclusively
by `V2EngineManager._update_latest_state` (`src/api/engine_manager.py:159`), which is itself not
modified by this ticket. No other caller of `compute_tick_delta` exists in the codebase per
investigation.md's grep confirmation. Because this step makes no change, there is no new
interaction with any writer to introduce.

**Do NOT touch:**
- `compute_tick_delta`'s return dict literal (`read_model_cache.py:151`).
- `StatePresenter.present_entity_slim` (`src/api/presenters/state_presenter.py:132-158`, the
  9-field per-entity projection used inside `changed[]`) — do not add a per-entity `region_id`
  there. The field is envelope-level, not per-entity; entities already carry `x`/`y` for spatial
  data. Adding a per-entity field here would also awkwardly require nulling it inside every
  `changed[]` entry, contradicting the "one key on the envelope" framing in the ticket's Scope.
- `ReadModelInvalidationPolicy.get_dirty_entity_ids` or the `candidate_ids` loop
  (`read_model_cache.py:133-144`) — no per-entity iteration is needed for an envelope-level null
  constant.

**Verify:** `tests/unit/api/test_read_model_cache.py::test_compute_tick_delta_fields_present_and_correct`
(line 188-193) passes unmodified, with no edit — this is the explicit proof this step made no
change.

### Step 3 — Add/extend integration tests asserting the field's presence and value

**Files:** `tests/api/test_ws_protocol.py`

**Change:**
1. Extend `test_ws_msgpack_delta_payload_shape` (lines 76-109) with an additional assertion:
   `assert data["region_id"] is None` (identity check, not a falsy check — per test_plan.md's
   anti-drift guard, this must fail if a future change accidentally defaults the field to `""` or
   `0` instead of `None`).
2. Add a json-format counterpart (new test or an extension of an existing json-mode delta test),
   `test_ws_delta_envelope_includes_null_spatial_placeholder_field`, asserting the same
   `data["region_id"] is None` over the json-format connection.
3. Add or fold in an assertion (per test_plan.md item 3,
   `test_ws_delta_envelope_new_field_does_not_change_existing_field_semantics`) that
   `tick`/`changed`/`removed`/`events`/`snapshot_as_of_tick` retain their existing types/values
   unchanged after the new field lands (e.g. `snapshot_as_of_tick == initial["tick"]` still holds,
   `changed`/`removed` are still lists).

**Other writers to this shared resource:** `tests/api/test_ws_protocol.py` is a test file; other
tests in it (`test_ws_json_handshake`, `test_ws_msgpack_handshake`) are unaffected and must remain
green. This suite spawns a live subprocess server (`python3 -m src serve`) per test_plan.md — no
concurrent-writer concern beyond normal test isolation.

**Do NOT touch:** `test_compute_tick_delta_fields_present_and_correct` in
`tests/unit/api/test_read_model_cache.py` — per Step 2, it stays unmodified since
`compute_tick_delta`'s shape did not change.

**Verify:** Run
`PATH=<venv>/bin:$PATH .venv/bin/python3 -m pytest tests/api/test_ws_protocol.py -v` — all cases
green, including the new/extended assertions.

### Step 4 — Run the full scoped regression surface

**Files:** none (verification only)

**Change:** Run both scoped commands from test_plan.md:
```
.venv/bin/python3 -m pytest tests/unit/api/ tests/architecture/test_api_read_model_guard.py -v
PATH=<venv>/bin:$PATH .venv/bin/python3 -m pytest tests/api/test_ws_protocol.py -v
```
`tests/architecture/test_api_read_model_guard.py` is re-run as a cheap correctness check — a
literal `None` assignment introduces no new `AuthoritativeState` access, so it should stay green,
but the guard specifically exists to catch an accidental state read creeping into the new field's
value (see Anti-Drift Notes).

**Do NOT touch:** Do not run the full `pytest tests/` suite (project rule) — scope stays to the
domain under modification.

**Verify:** All listed suites pass. `test_compute_tick_delta_fields_present_and_correct` passes
with zero modification (proves Step 2's no-op claim held).

### Step 5 — AC #3 verification guard (manual Verify-phase check, not a pytest test)

**Files:** none (verification only, scoped grep)

**Correction (architecture-review finding):** `region_id` is a pre-existing, load-bearing
identifier throughout this codebase (entity/region navigation state, economy presenters, world
consequences/threat/boss/camp/calamity systems, etc.) — a bare `grep -rn "region_id" src/ tests/`
returns **~724 hits**, not "two pre-existing occurrences" as an earlier draft of this plan and
investigation.md's Risks/Prior Work section incorrectly assumed. A bare whole-repo grep is not a
usable AC #3 verification mechanism; it must be scoped to the new envelope key specifically, not
the identifier name in general (which collides with the unrelated, much larger pre-existing
concept of region *navigation state* elsewhere in the codebase).

**Change:** Run two scoped checks instead:
1. Confirm the only *write* of this envelope's `region_id` key is the literal
   `out_payload["region_id"] = None` assignment added in `stream.py` (Step 1):
   `grep -rn 'out_payload\["region_id"\]\|payload\["region_id"\]' src/ tests/` — expect exactly the
   one Step 1 write plus the Step 3 test assertions reading it back off a received WS message.
2. Confirm no code anywhere *reads* this envelope key to filter, subscribe, or branch logic:
   `grep -rn '\["region_id"\]\|get("region_id")' src/api/ws/ src/api/read_model_cache.py
   src/api/presenters/ frontend/src/` (restricted to the WS/delta-envelope-adjacent surface, not
   the whole repo) — expect only the Step 1 write and Step 3 test reads; zero hits in any
   filtering/subscription/routing logic.

Both checks are scoped to where the *new envelope key* could plausibly be written or read, not to
the bare string `region_id`, which is meaningless as a scope-violation signal given how common that
identifier already is for an unrelated concept.

**Do NOT touch:** The pre-existing, unrelated `region_id` occurrences elsewhere in the codebase
(e.g. `state_presenter.py:275`'s `present_static` regions list, and `stream_live_events_ws`'s
`/ws/observability/events` query-param filter at `stream.py:220-221` — **not** `/ws/observe`, which
only filters by `entity_id`; investigation.md correctly attributes this, an earlier draft of this
plan mislabeled it) — none of these are in scope to rewrite, delete, or even inspect beyond
confirming they're unrelated.

**Verify:** Both scoped grep outputs reviewed and recorded in the ticket's Implementation Notes /
Test Summary at Finalize — not the bare whole-repo grep.

### Step 6 — Update docs and the parity ledger entry

**Files:** `docs/engine/contracts/api_protocol_contract.md`, `docs/parity_ledger/infrastructure.yaml`

**Change:**
- `docs/engine/contracts/api_protocol_contract.md` Section 2 ("WebSocket Protocol (BWS)"): add a
  one-line mention of the new reserved, always-null `region_id` field alongside the existing
  enumerated fields (`changed`/`removed`/`tick`/`events`/`snapshot_as_of_tick`), noting it is
  currently unpopulated and reserved for the future M3 interest-management epic
  (`TCK-20260821-EPIC-LIVE-MAP-INTEREST-MANAGEMENT`).
- `docs/parity_ledger/infrastructure.yaml`, entry `INFRA-388`: this is the same behavior being
  amended (the entry's `text` already documents this exact envelope shape and its
  `support_boundary` field already anticipates "spatial-subscription/region filtering are
  explicitly out of scope"), so update `INFRA-388`'s `text`/`v2_evidence`/`support_boundary` rather
  than opening a new entry. Add `src/api/ws/stream.py`'s new line to `v2_evidence` and note the
  placeholder field's addition in `text`. `INFRA-388` is `priority: P1`, not `P0`, so no new
  mandatory test_path is forced beyond what already exists.

**Other writers to this shared resource:** `docs/parity_ledger/infrastructure.yaml` is written to
by any ticket touching infrastructure/observability parity entries; per investigation.md's grep
confirmation, no other `docs/parity_ledger/*.yaml` entry references `compute_tick_delta`,
`present_entity_slim`, or `stream_ws`, so `INFRA-388` is the sole entry in play — no collision with
a concurrent writer to the same entry is expected within this ticket's scope. This step should run
via the `parity-updater` agent per project convention, in the same session as implementation.

**Do NOT touch:**
- `docs/observability/read_model_service_contract.md`'s `tick_delta` row — describes
  `compute_tick_delta`'s own return shape, which Step 2 confirms is untouched.
- `docs/engine/contracts/frontend.md` — frontend consumption (`useSimulation.ts`) is unaffected and
  explicitly out of scope.
- `docs/guidelines/intentional_divergences.md` — not a divergence from the Mechanics Bible or V1
  legacy behavior (neither ever had a spatial-subscription field); no entry needed.

**Verify:** Doc diff reviewed for accuracy against the actual code change in Step 1; no new
parity-ledger entry created (only `INFRA-388` amended).

## Scope Guards

- No server-side filtering, subscription-matching, or per-viewer visibility logic may be added
  anywhere in this ticket's diff — that is exclusively the scope of the separate epic
  `TCK-20260821-EPIC-LIVE-MAP-INTEREST-MANAGEMENT`.
- The field's value must be the literal `None`/`null` on every message, never derived from
  `entity.region_id`, `state.regions`, or any `region.bounds` lookup — even a non-null *derived*
  value (with no filtering attached yet) would itself constitute "using" the field and violate
  AC #3.
- No `protocol_version` field or bump — this envelope has no `protocol_version` field today (that
  field exists only on the unrelated `/api/v1/manifest` response,
  `src/api/presenters/manifest_presenter.py:32`, a different sibling ticket's territory
  `TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT`). Do not add one here.
- No client-side (`frontend/`) changes — the field is not sent by clients yet; nothing in
  `useSimulation.ts` or any frontend type needs updating for this ticket.
- No per-entity field inside `StatePresenter.present_entity_slim` or `changed[]` — the field is
  envelope-level only.
- Do not loosen `test_compute_tick_delta_fields_present_and_correct`'s exhaustive
  `set(payload.keys())` assertion to a subset check — it stays exhaustive and stays unmodified by
  this ticket (proves Step 2's placement choice).
- Do not tighten `test_ws_msgpack_delta_payload_shape`'s individual-key-membership assertion style
  into exhaustive key-set equality as a side effect of extending it in Step 3 — keep it additive
  (`in data` checks plus the new `is None` check), not converted to a `set(...) ==` form.

## Dependency Map

- Step 1 (stream.py change) has no dependency on Step 2 (it's a no-op confirmation) but Step 2's
  claim depends on Step 1 not touching `read_model_cache.py` — read together, not sequenced.
- Step 3 (tests) depends on Step 1 being complete (tests assert against the new field Step 1 adds).
- Step 4 (full scoped regression run) depends on Steps 1–3 being complete.
- Step 5 (grep guard) depends on Step 1 and Step 3 being complete (needs the final field name and
  all touched files in place to grep against).
- Step 6 (docs/parity ledger) depends on Step 1 being complete and stable (documents the actual
  shipped shape) but is otherwise independent of Steps 3–5 and can run in parallel with them.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1: delta envelope includes an additional key (e.g. region/chunk), present but null/unset on every message | Step 1 | `test_ws_delta_envelope_includes_null_spatial_placeholder_field` (json), extended `test_ws_msgpack_delta_payload_shape` (msgpack) — both in `tests/api/test_ws_protocol.py`, Step 3 |
| AC #2: adding the field does not change any existing field's name/type/semantics, no protocol_version bump needed | Step 1 (additive-only assignment), Step 2 (compute_tick_delta untouched) | `test_ws_delta_envelope_new_field_does_not_change_existing_field_semantics` (Step 3); `test_compute_tick_delta_fields_present_and_correct` passing unmodified (Step 4) |
| AC #3: no server-side filtering logic reads or acts on the new field's value anywhere in this ticket's diff | Step 1 (literal `None`, no derivation), Scope Guards | Step 5's two scoped grep checks (write-site and read-site, restricted to the WS/delta-envelope surface — not a bare whole-repo `region_id` grep), manual Verify-phase check |
| AC #4: tests for the delta envelope continue to pass unmodified except for the new field's presence | Step 1/2 placement choice (stream.py, not read_model_cache.py) | Step 4 full scoped regression run — `test_compute_tick_delta_fields_present_and_correct` unmodified; `test_ws_msgpack_delta_payload_shape` and other pre-existing WS protocol tests remain green with only the new assertions added |

## Anti-Drift Notes

- **Highest-risk drift**: implementing the field with a derived value instead of a hardcoded
  `None` "for convenience" (e.g. reaching for `present_static`'s existing region-from-coordinates
  logic since it's nearby). This silently crosses into the M3 interest-management epic's scope and
  violates AC #3 even without any filtering being attached — a non-null value is itself a form of
  "acting on" the field. Every test assertion for this field must use `is None` (identity), never a
  falsy/empty check, so a buggy default of `""` or `0` cannot pass silently.
- **Wrong placement risk**: `present_entity_slim` (state_presenter.py:132-158) has `x`/`y` fields
  nearby, which could tempt a per-entity `region_id` addition there. This ticket's field is
  envelope-level (same tier as `tick`/`snapshot_as_of_tick`), not per-entity — do not thread it
  through `compute_tick_delta`'s `candidate_ids`/`changed`/`removed` loop.
  `state_presenter.py` needs no functional diff for this ticket at all (it was listed in the
  ticket's Related Code Areas but investigation.md flags this as likely over-inclusive copy from
  ticket 4's own list) — a docstring comment noting the placeholder deliberately lives on the
  envelope, not per-entity, is optional and may be added by the implementer at their discretion,
  but is not required for any AC.
- **Copy-before-mutate discipline**: the new assignment must be on `out_payload` (the
  per-connection copy at stream.py:72), never on the shared `payload` object fanned out by
  reference to every listener's queue — mutating `payload` directly would reintroduce the
  cross-connection race that ticket `TCK-20260821-WS-ENTITY-DELTA-BROADCAST` specifically fixed.
- **No protocol_version conflation**: this ticket's field is unrelated to the `protocol_version`/
  `dictionary_version` discussion in the epic doc's §A "Data Manifest" section, which belongs to
  the separate `/api/v1/manifest` endpoint and ticket `TCK-20260821-MANIFEST-ID-LOOKUP-ENDPOINT`.
  Do not add a `protocol_version` field while touching this envelope.
- **Initial-payload scope boundary**: the one-time initial connect payload
  (`manager.get_state()`, stream.py:56-61) is not part of "the entity-delta broadcast path" per
  investigation.md's reading of the AC, and is not touched by this ticket — do not add the field
  there even for consistency; that would be an unscoped, unverified change to a payload shape this
  ticket's test plan does not cover.
- **This ticket builds no client-facing contract yet**: the field name/type choice (`region_id:
  Optional[str]`) is a best-effort compatible placeholder for whatever the M3 interest-management
  epic later decides, not a locked-in final design for that epic — if that epic later needs a
  different shape (e.g. a chunk coordinate or bounding box instead of a string ID), it is free to
  redesign this field at that time; this ticket does not bind that future decision beyond "reserve
  a null-safe key now."

## Unresolved Questions

None — both open questions from investigation.md are resolved above (Decision 1, Decision 2). No
placeholder steps remain.

## Deviations

None. All 6 steps were implemented exactly as specified. The two scoped AC #3 grep checks (Step 5)
returned exactly the hits the plan predicted: the write-site grep found the one Step 1 write plus
pre-existing, unrelated `payload["region_id"]` hits in observability event-extractor tests (plus one
incidental docstring mention in `src/domains/culture/deriver.py`, prose only, not code); the
read-site grep found the one Step 1 write plus the pre-existing `/ws/observability/events`
query-param read in `stream.py` (at line 222, not 220-221 as cited in the plan — shifted by one line
because the new `region_id` assignment was inserted earlier in the same file; same code, same
meaning, no scope violation). No new derived values, no per-entity placement, no protocol_version
field, and no `compute_tick_delta` edit were introduced.
