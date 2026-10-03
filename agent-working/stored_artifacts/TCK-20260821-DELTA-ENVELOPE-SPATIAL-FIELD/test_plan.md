---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD
artifact_type: test_plan
tags: [api-design, engine]
---

# Test Plan — TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD

## Regression Surface

**Unit** (`tests/unit/api/`):
- `tests/unit/api/test_read_model_cache.py` — all `compute_tick_delta` cases (7 cases,
  lines 106-207), including the exhaustive-key-set case
  `test_compute_tick_delta_fields_present_and_correct` (line 188-193,
  `assert set(payload.keys()) == {"tick", "changed", "removed", "events"}`). **Must stay green
  unmodified** if the field is added in `stream.py` per this ticket's investigation.md
  recommendation; **will need exactly one line updated** (the set literal) if the field is instead
  added inside `compute_tick_delta` — either is acceptable per the AC's "except for the new field's
  presence" clause, but the two placements have different blast radii and the planner's chosen
  placement determines which applies.
- `tests/unit/api/test_engine_manager.py` — `test_tick_listener_registered_before_snapshot_loses_no_tick`
  (line 221) and `test_delta_payload_is_none_or_dict_and_notify_listeners_receives_it` (line 242):
  neither touches `stream_ws`'s per-connection field assembly, so both are unaffected regardless of
  placement choice.
- `tests/architecture/test_api_read_model_guard.py` — asserts no file outside the
  `ReadModelService`/`V2EngineManager`/`ReadModelCache`/`StatePresenter` chain accesses
  `AuthoritativeState` directly. A literal `None` assignment in `stream_ws` introduces no new state
  access, so this guard is unaffected — but re-run it as a cheap correctness check since it's exactly
  the guard that would catch an accidental state read creeping into the new field's value.

**Integration** (`tests/api/`):
- `tests/api/test_ws_protocol.py` — `test_ws_json_handshake`, `test_ws_msgpack_handshake` (pre-existing,
  unrelated to the delta shape, must stay green), and
  `test_ws_msgpack_delta_payload_shape` (lines 76-109) — asserts individual key membership
  (`"changed" in data`, `"removed" in data`, `"tick" in data`, `"snapshot_as_of_tick" in data`), not
  exhaustive key-set equality, so it passes unmodified with an additional top-level key present
  regardless of placement choice. This suite spawns a live subprocess server (`python3 -m src serve`)
  and requires the venv's `python3` on `PATH` (pre-existing environment characteristic, not
  introduced by this ticket).

## New Tests Required

1. **Test name**: `test_ws_delta_envelope_includes_null_spatial_placeholder_field`
   **Category**: integration
   **Verifies**: AC #1 — the per-tick delta message received over `/api/v1/ws` (json format) includes
   the new key (e.g. `region_id`) and its value is `None`/`null` on every delta message, not just
   sometimes. Extend the existing msgpack-shape test's json counterpart, or add a new case
   parallel to `test_ws_msgpack_delta_payload_shape`, asserting `data[field_name] is None` alongside
   the existing `"changed" in data` style assertions.
   **Where**: `tests/api/test_ws_protocol.py`

2. **Test name**: `test_ws_delta_envelope_spatial_field_present_in_msgpack_mode_too`
   **Category**: integration
   **Verifies**: the field survives msgpack round-tripping (msgpack has no native `null` distinct
   from omission the way JSON does at the wire level for some encoders — worth confirming explicitly
   rather than assuming JSON coverage implies msgpack coverage, especially since this envelope is
   already routed through both formats per ticket 4's AC). Extend
   `test_ws_msgpack_delta_payload_shape` directly with `assert data[field_name] is None`.
   **Where**: `tests/api/test_ws_protocol.py` (extend existing test rather than duplicate the
   subprocess-server setup cost of a new test)

3. **Test name**: `test_ws_delta_envelope_new_field_does_not_change_existing_field_semantics`
   **Category**: integration / anti-drift
   **Verifies**: AC #2 — `tick`, `changed`, `removed`, `events`, `snapshot_as_of_tick` all keep their
   pre-existing types/values unchanged (e.g. `snapshot_as_of_tick == initial["tick"]` still holds,
   `changed`/`removed` are still lists) after the new field is added — guards against an
   implementation that accidentally restructures the envelope while adding the new key.
   **Where**: `tests/api/test_ws_protocol.py` (can be folded into extending
   `test_ws_msgpack_delta_payload_shape` rather than a fully separate test, at the implementer's
   discretion, as long as the assertion exists)

4. **Test name**: `test_compute_tick_delta_field_name_not_read_or_filtered_grep_guard` — **not** a
   pytest test; this is AC #3's grep check ("grep for the field name outside envelope
   construction/schema definition returns nothing"). Not automatable as a pytest assertion without
   knowing the final field name in advance — record as a manual/Verify-phase check:
   `grep -rn "<field_name>" src/ tests/` and confirm every hit is either (a) the literal assignment
   site in `stream.py`/wherever it's placed, (b) the new test(s) above, or (c) a doc/parity-ledger
   mention. Any hit inside filtering/query logic is a scope violation.

**If the planner places the field inside `compute_tick_delta` instead of `stream_ws`** (see
investigation.md Open Questions), add instead:
5. **Test name**: `test_compute_tick_delta_includes_null_spatial_placeholder`
   **Category**: unit
   **Verifies**: `compute_tick_delta`'s returned dict includes the new key with value `None`, and
   update `test_compute_tick_delta_fields_present_and_correct`'s `set(payload.keys())` literal to
   include it (see Regression Surface above).
   **Where**: `tests/unit/api/test_read_model_cache.py`

## Scoped Pytest Commands

```
.venv/bin/python3 -m pytest tests/unit/api/ tests/architecture/test_api_read_model_guard.py -v
PATH=<venv>/bin:$PATH .venv/bin/python3 -m pytest tests/api/test_ws_protocol.py -v
```

Matches the exact scoped commands ticket 4 used and verified (`tests/unit/api/`,
`tests/architecture/test_api_read_model_guard.py`, `tests/api/test_ws_protocol.py`) — this ticket
touches the same files, so the same regression domain applies. Do not run the full `pytest tests/`
suite (project rule). `tests/api/test_ws_protocol.py` requires the venv's `python3` on `PATH` since it
spawns `python3 -m src serve` as a real subprocess — same pre-existing environment note ticket 4's
Test Summary recorded, not new to this ticket.

## Anti-Drift Test Guards

- **Exhaustive key-set assertion as a tripwire, not an obstacle**:
  `test_compute_tick_delta_fields_present_and_correct`'s `set(payload.keys()) == {...}` is exactly the
  kind of test that would silently start failing if a future ticket (this one or a later one) adds
  fields to `compute_tick_delta`'s return value without updating the test — keep this assertion
  exhaustive (don't loosen it to a subset check) so it continues to force a deliberate decision on
  every future field addition to that function, the same discipline this ticket benefits from now.
- **`test_ws_msgpack_delta_payload_shape`'s individual-key-membership style (not exhaustive) is
  correct for the wire-level test** — do not "tighten" it to exhaustive key-set equality as a side
  effect of this ticket's changes; that would make every future envelope-level addition (e.g. the
  real interest-management fields M3 eventually adds) require touching this integration test too,
  which is exactly the fragility the ticket's own "no protocol_version bump" / additive-only framing
  is trying to avoid downstream.
- **Grep guard for AC #3** (see New Tests Required #4) is the primary anti-scope-creep guard for this
  ticket specifically — it is the one gate check most likely to be quietly skipped since it isn't a
  pytest assertion. Explicitly run it at Verify, not just assumed satisfied by code review.
- **A guard against accidentally deriving a value instead of hardcoding `None`**: assert the field's
  value with `is None` (identity), not a falsy/empty-string check, in every new test above — a
  buggy-but-passing implementation that defaults to `""` or `0` instead of `None` would pass a loose
  falsy check but violate the ticket's explicit "present but null/unset" AC wording.
