---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD
phase: done
date: 2026-08-21
tags: []
---

# TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD

## Title
Reserve a spatial-subscription placeholder field in the WS delta envelope

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Bandwidth analysis at real target scale (10,000 entities) shows interest management (filtering what's broadcast by what a viewer can see) is likely necessary, not safely deferrable as originally assumed. The author wants an unused region/chunk field reserved now in the delta message envelope so a future interest-management feature doesn't require a breaking protocol change later -- building the actual filtering logic stays out of scope for this epic.

## Scope
- Add one additional key (e.g. region or chunk) to the delta envelope produced by the entity-delta broadcast path, present but null/unset on every message
- Land in the same PR/session as the delta broadcast ticket or immediately after, since it has no implementation surface of its own until that envelope exists

## Out of Scope
- Any server-side filtering logic that reads or acts on the new field's value (belongs solely to the separate M3 interest-management epic, TCK-20260821-EPIC-LIVE-MAP-INTEREST-MANAGEMENT)
- Stubbing subscription semantics, per-viewer filtering hooks, or client-side sending of the field
- Any protocol_version bump (must be additive-only)

## Acceptance Criteria
- [x] the delta envelope from the entity-delta broadcast path includes an additional key (e.g. region or chunk) present but null/unset on every message
- [x] adding the field does not change any existing field's name/type/semantics, no protocol_version bump needed
- [x] no server-side filtering logic reads or acts on the new field's value anywhere in this ticket's diff (grep for the field name outside envelope construction/schema definition returns nothing)
- [x] tests for the delta envelope continue to pass unmodified except for the new field's presence

## Related Tickets
- TCK-20260821-WS-ENTITY-DELTA-BROADCAST
- TCK-20260821-EPIC-LIVE-MAP-RECONNECTION

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- src/api/ws/stream.py
- src/api/presenters/state_presenter.py

## Assumptions / Open Questions
- field name/type not yet decided (region vs chunk, string ID vs coordinate vs bounding box) -- only needs a placeholder reasonably compatible with whatever the downstream interest-management epic later chooses, not final granularity design
- layer corrected to `engine` post-write (initially set to `observability` by the write agent, self-flagged as a stretch — `engine` matches the sibling `TCK-20260821-WS-ENTITY-DELTA-BROADCAST` ticket it hard-depends on and the actual file both touch, `src/api/ws/stream.py`)

## Implementation Notes

Followed `staging_artifacts/TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD/plan.md`'s 6 steps exactly, no
deviations.

1. **`src/api/ws/stream.py::stream_ws`** — added `out_payload["region_id"] = None` immediately after
   the existing `out_payload["snapshot_as_of_tick"] = snapshot_as_of_tick` line (inside the
   `while True:` loop, on the per-connection `out_payload` copy, never on the shared `payload`
   object). Literal `None` only — no derivation from any entity/region state.
2. **`src/api/read_model_cache.py::ReadModelCache.compute_tick_delta`** — confirmed genuinely
   untouched. Its return statement is still exactly
   `return {"tick": tick, "changed": changed, "removed": removed, "events": events}` — no sixth key.
3. **`tests/api/test_ws_protocol.py`** — extended `test_ws_msgpack_delta_payload_shape` with
   `assert "region_id" in data` / `assert data["region_id"] is None` (identity check, not falsy);
   added `test_ws_delta_envelope_includes_null_spatial_placeholder_field` (json-format counterpart)
   and `test_ws_delta_envelope_new_field_does_not_change_existing_field_semantics` (asserts
   `tick`/`changed`/`removed`/`events`/`snapshot_as_of_tick` keep their pre-existing types/values
   alongside the new `region_id is None` check).
4. Ran the full scoped regression suite from `test_plan.md` — see Test Summary below.
5. Ran the two scoped AC #3 verification greps (not a bare whole-repo grep):
   - **Write-site** — `grep -rn 'out_payload\["region_id"\]\|payload\["region_id"\]' src/ tests/`
     returned exactly the one Step 1 write (`src/api/ws/stream.py:74`), plus a docstring mention in
     `src/domains/culture/deriver.py:68` (`entry.payload["region_id"]`, prose in a docstring, not
     code), plus six pre-existing, unrelated `payload["region_id"]` assertions in
     `tests/unit/observability/test_event_extractor_*.py` (observability event-extractor tests,
     confirmed pre-existing and harmless by architecture-review). This ticket's own new test
     assertions read the field via `data["region_id"]`, not `out_payload[...]`/`payload[...]`, so
     they correctly do not appear in this pattern's matches.
   - **Read-site** — `grep -rn '\["region_id"\]\|get("region_id")' src/api/ws/
     src/api/read_model_cache.py src/api/presenters/ frontend/src/` returned exactly two hits: the
     Step 1 write (`src/api/ws/stream.py:74`) and the pre-existing, unrelated
     `/ws/observability/events` query-param filter read (`src/api/ws/stream.py:222`, shifted by one
     line from the plan's cited 220-221 due to the new line's insertion earlier in the same file).
     Zero hits in any filtering/subscription/routing logic anywhere else on this scoped surface.
   Both results match the plan's expected outcome exactly.
6. **Docs/parity ledger**:
   - `docs/engine/contracts/api_protocol_contract.md` Section 2 — added a sentence noting the new
     `region_id` field, always `null` today, reserved for
     `TCK-20260821-EPIC-LIVE-MAP-INTEREST-MANAGEMENT`.
   - `docs/parity_ledger/infrastructure.yaml`, entry `INFRA-388` (amended in place, no new entry) —
     updated `text` to mention the envelope now includes `region_id` and to describe this ticket's
     addition; updated `v2_evidence` to note the exact `stream.py` assignment;
     updated `support_boundary` to note `region_id` is now reserved (always null) but
     spatial-subscription/region filtering itself remains out of scope, still deferred to the M3
     epic. Validated the YAML still parses (`yaml.safe_load`) and `tools/parity_ledger_scan.py` runs
     clean with no new errors.

**Note on `make knowledge-index-update`** (required by CLAUDE.md's "After Work" rule since
`docs/engine/contracts/api_protocol_contract.md` was modified): attempted and failed —
`tools/knowledge_search.py` lacks the execute bit in this worktree (Makefile's `$(shell for py in
...)` python-resolution silently fell through), and running it directly with the venv's `python3`
fails at model load with `OSError: We couldn't connect to 'https://huggingface.co'` (no network
access / no local HF cache in this sandbox). This matches this session's own memory note on known
environment gaps (SSL/network access needed for HuggingFace downloads) — a pre-existing environment
limitation, not something introduced by or fixable within this ticket's diff. Flagging explicitly
rather than silently skipping; a human/CI environment with network access should run
`make knowledge-index-update` before this lands, or Finalize should re-attempt it in an environment
where it can succeed.

## Test Summary

- `.venv/bin/python3 -m pytest tests/unit/api/ tests/architecture/test_api_read_model_guard.py -v`
  — **54 passed**, 0 failed. Includes
  `tests/unit/api/test_read_model_cache.py::test_compute_tick_delta_fields_present_and_correct`
  passing **unmodified** (proves Step 2's no-op claim: `compute_tick_delta`'s exhaustive
  `set(payload.keys()) == {"tick", "changed", "removed", "events"}` assertion required zero edits).
- `PATH=<venv>/bin:$PATH .venv/bin/python3 -m pytest tests/api/test_ws_protocol.py -v` — **5
  passed**, 0 failed: `test_ws_json_handshake`, `test_ws_msgpack_handshake`,
  `test_ws_msgpack_delta_payload_shape` (extended), `test_ws_delta_envelope_includes_null_spatial_placeholder_field`
  (new), `test_ws_delta_envelope_new_field_does_not_change_existing_field_semantics` (new).
- Did not run the full `pytest tests/` suite, per project rule — scope stayed to the domain under
  modification (`tests/unit/api/`, `tests/architecture/test_api_read_model_guard.py`,
  `tests/api/test_ws_protocol.py`), matching `test_plan.md`'s Scoped Pytest Commands exactly.

## Files Changed

- `src/api/ws/stream.py` — added `out_payload["region_id"] = None` (1 line, inside `stream_ws`'s
  `while True:` loop).
- `tests/api/test_ws_protocol.py` — extended `test_ws_msgpack_delta_payload_shape` with two
  assertions; added two new tests
  (`test_ws_delta_envelope_includes_null_spatial_placeholder_field`,
  `test_ws_delta_envelope_new_field_does_not_change_existing_field_semantics`).
- `docs/engine/contracts/api_protocol_contract.md` — one-sentence addition to Section 2 documenting
  the new reserved `region_id` field.
- `docs/parity_ledger/infrastructure.yaml` — amended `INFRA-388`'s `text`, `v2_evidence`, and
  `support_boundary` in place (no new entry created).
- `staging_artifacts/TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD/plan.md` — no substantive rewrite
  required; plan was followed exactly with zero deviations (see plan.md's own note, added this run).
- `tickets/inprogress/TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD.md` — this file: Status, Acceptance
  Criteria checkboxes, Implementation Notes, Test Summary, Files Changed, Completion Summary.

`src/api/read_model_cache.py` was read and confirmed untouched — not listed above since no diff was
made there (Step 2 was a deliberate no-op).

## Completion Summary

Added a single always-null `region_id: Optional[str]` placeholder key
(`out_payload["region_id"] = None`) to the per-tick WS delta envelope in
`src/api/ws/stream.py::stream_ws`, reserving wire-protocol space for the future M3
interest-management epic without building any filtering/subscription logic. `compute_tick_delta`'s
core `{tick, changed, removed, events}` shape was left completely untouched, so its one
exhaustive-key-set test required no edit. Extended/added three integration tests in
`tests/api/test_ws_protocol.py` (json + msgpack + existing-field-unchanged, all using `is None`
identity checks). Both scoped AC #3 verification greps (write-site and read-site) confirmed no
server-side code anywhere reads or acts on the new field. Updated
`docs/engine/contracts/api_protocol_contract.md` and amended `INFRA-388` in
`docs/parity_ledger/infrastructure.yaml` in place. All 54 scoped unit/architecture tests and all 5
scoped WS-protocol integration tests pass.
