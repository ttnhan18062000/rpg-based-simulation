---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260831-PARITY-LEDGER-ID-PATTERN-MULTISEGMENT
phase: done
date: 2026-08-31
tags: [bug, schema]
---

# TCK-20260831-PARITY-LEDGER-ID-PATTERN-MULTISEGMENT

## Title
Parity ledger `_ID_PATTERN`/schema regex rejects established multi-segment shard IDs (e.g. `WORLD-DEMO-XXX`)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`tools/parity_ledger_writer.py:48`'s `_ID_PATTERN = re.compile(r"^[A-Z]+-[0-9]{3}$")` (mirrored byte-for-byte in `docs/parity_ledger/schema.json`'s `properties.id.pattern`) requires exactly one hyphen — letters-only prefix, then exactly 3 digits. It structurally rejects any two-hyphen ID. This silently rejects the already-live, already-established `WORLD-DEMO-*`/`WORLD-CULT-*` multi-segment shard-ID convention: `WORLD-DEMO-001` through `WORLD-DEMO-006` in `docs/parity_ledger/world_dynamics.yaml` are all real, existing, valid-in-practice entries that the writer's own `validate_entry()` would reject if run against them today.

Discovered during `TCK-20260831-POPULATION-COHORT-SEEDING` (M2 batch, ticket 9/15) when adding a new `WORLD-DEMO-006` entry — the implementer worked around it by hand-reproducing the writer's validated write path (confirmed by Document-Update to be schema-valid in every other respect) rather than silently renaming the ID to dodge the regex or bypassing validation outright. This is a genuine pre-existing tool gap, not new breakage from that ticket.

**Second, independent blast radius found by Document-Update's follow-up check (not part of the original discovery):** `tools/gate_checks/parity_updater_static.py::next_available_id` mirrors the same `_ID_PATTERN`. Because it walks entries and skips any non-matching id, calling `next_available_id("world_dynamics.yaml")` today silently ignores all 6 `WORLD-DEMO-*` entries and returns `WORLD-102` (next bare `WORLD-NNN`) instead of the correct `WORLD-DEMO-007` — a second tool that would silently propose a colliding/wrong-convention ID for the next entry in this shard.

## Scope
- Extend `tools/parity_ledger_writer.py`'s `_ID_PATTERN` (and the byte-identical `docs/parity_ledger/schema.json` `properties.id.pattern`) to accept multi-segment prefixes, e.g. `^[A-Z]+(-[A-Z]+)*-[0-9]{3}$`.
- Extend `tools/gate_checks/parity_updater_static.py::next_available_id`'s matching logic (or whatever regex/parsing it shares) so it correctly recognizes and increments multi-segment shard IDs like `WORLD-DEMO-*` instead of silently falling back to the bare `WORLD-NNN` sequence.
- Verify `validate_entry()` and `next_available_id()` both pass against the full existing corpus of `WORLD-DEMO-*`/`WORLD-CULT-*` entries after the fix (regression test using real ledger content, not synthetic fixtures).
- Add/extend a test in `tests/tools/test_parity_ledger_writer.py` and/or `test_parity_ledger_schema.py` covering a multi-segment ID round-trip through both `validate_entry()` and `next_available_id()`.

## Out of Scope
- Changing or renaming any existing parity ledger entry IDs.
- Any change to parity ledger *content* (only the ID-pattern validation/generation logic).

## Acceptance Criteria
- [x] `validate_entry()` accepts `WORLD-DEMO-001` through `WORLD-DEMO-006` (and other existing multi-segment IDs across the ledger, e.g. `WORLD-CULT-001`) without error.
- [x] `next_available_id("world_dynamics.yaml")` (or the relevant shard) correctly proposes `WORLD-DEMO-007` given the existing `WORLD-DEMO-001..006` entries, not a bare `WORLD-NNN` id.
- [x] New/extended tests cover both functions against real multi-segment IDs, not just synthetic single-segment ones.
- [x] No existing single-segment ID (`WORLD-NNN`, `COMB-NNN`, etc.) behavior regresses.

## Related Tickets
- TCK-20260831-POPULATION-COHORT-SEEDING (where this was discovered)

## Related Docs
- docs/parity_ledger/schema.json
- docs/parity_ledger/world_dynamics.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- tools/parity_ledger_writer.py
- tools/gate_checks/parity_updater_static.py
- docs/parity_ledger/schema.json
- tests/tools/test_parity_ledger_writer.py
- tests/tools/test_parity_ledger_schema.py

## Assumptions / Open Questions
- None — the regex gap and its second blast radius (`next_available_id`) were both directly confirmed against live source and the real ledger corpus during `TCK-20260831-POPULATION-COHORT-SEEDING`'s Document-Update phase, not assumed.

## Implementation Notes
- `tools/parity_ledger_writer.py::_ID_PATTERN`: extended from `^[A-Z]+-[0-9]{3}$` to
  `^[A-Z]+(-[A-Z]+)*-[0-9]{3}$` (exactly the pattern the ticket suggested), accepting any number
  of letters-only hyphen segments before the final 3-digit numeric suffix.
- `docs/parity_ledger/schema.json`'s `properties.id.pattern`: updated to the byte-identical
  `^[A-Z]+(-[A-Z]+)*-[0-9]{3}$` string, keeping the two representations in sync per the module's
  own documented invariant.
- `tools/gate_checks/parity_updater_static.py::_ID_PATTERN`: changed from
  `^([A-Z]+)-([0-9]{3})$` to `^([A-Z]+(?:-[A-Z]+)*)-([0-9]{3})$` — same accepted ID space as the
  writer's pattern, but keeps its own pre-existing convention of capturing prefix/suffix as
  separate groups for arithmetic (a non-capturing group is used internally for the repeated
  segment so the two capture groups stay exactly `(prefix, suffix)`).
- `tools/gate_checks/parity_updater_static.py::next_available_id`: this was the substantive fix.
  The previous implementation tracked a single running `prefix`/`width`/`max_suffix` across all
  matching entries in file order, which is only correct when a shard has exactly one id family.
  `docs/parity_ledger/world_dynamics.yaml` genuinely has three: bare `WORLD-NNN`, and multi-segment
  `WORLD-DEMO-NNN` / `WORLD-CULT-NNN`. Once the regex started matching multi-segment ids too, a
  single global `max_suffix` would let one family's higher numeric suffix leak into another
  family's proposed id (e.g. a `WORLD-119` entry could skew a `WORLD-CULT-*` proposal to
  `WORLD-CULT-120`). Fixed by tracking `max_suffix`/`width` in per-prefix dicts (keyed on the full
  captured prefix, e.g. `"WORLD-DEMO"` as one key, `"WORLD"` as a separate key) and reporting
  against whichever prefix belongs to the last matching entry encountered in the shard's own file
  order — this preserves the function's pre-existing "last-matching-entry wins" idiom for
  single-family shards (all existing tests for `COMB-*`/`TOWN-*`/`INFRA-*` shards are unchanged
  and still pass) while making the multi-family case correct instead of accidentally-correct.
  Confirmed against the real `world_dynamics.yaml`: `WORLD-DEMO-006` is literally the last entry in
  the file (appended after `WORLD-119` and the `WORLD-CULT-*` block), so `next_available_id`
  correctly proposes `WORLD-DEMO-007`.
- No changes were made to `validate_entry()`'s logic itself (only the regex it references) or to
  any ledger *content* — out of scope, and confirmed untouched via `git diff`.

## Test Summary
Ran (via `.venv/bin/python3 -m pytest`, since bare `python3` lacks `pydantic` in this sandbox):
- `tests/tools/test_parity_ledger_writer.py` — 20 tests, all pass (7 new: 4 parametrized
  `test_writer_accepts_multi_segment_ids` cases + 1
  `test_real_world_demo_and_world_cult_entries_pass_validate_entry` real-corpus test scanning
  `docs/parity_ledger/world_dynamics.yaml` directly and asserting all 9 real `WORLD-DEMO-*`/
  `WORLD-CULT-*` entries pass `validate_entry()`).
- `tests/tools/test_parity_ledger_schema.py` — 1 test, passes unchanged.
- `tests/tools/test_parity_updater_static.py` — 19 tests, all pass (3 new:
  `test_next_available_id_accepts_multi_segment_id`,
  `test_next_available_id_groups_max_suffix_per_prefix_family_not_globally` (regression guard for
  the cross-family leak bug described above), and
  `test_next_available_id_against_real_world_dynamics_shard` (real-corpus proof — asserts
  `next_available_id("world_dynamics.yaml", ledger_dir="docs/parity_ledger")` returns
  `"WORLD-DEMO-007"` against the actual committed shard, not a synthetic fixture)).
- Also ran `tests/tools/test_parity_index.py`, `tests/tools/test_parity_index_baseline.py`, and
  `tests/tools/test_gate_a_readpath_review.py` (all import `derive_mapping` from the same module)
  as a broader regression check — 61 passed, 10 skipped, 0 failed.
- Grepped `tests/` for every other importer of `_ID_PATTERN`/`next_available_id`/
  `parity_ledger_writer`/`parity_updater_static` — no other test file references these symbols
  beyond what was run above.
- Manually verified live behavior against the real repo state (not just tests):
  `validate_entry()` accepts `WORLD-DEMO-001`, `WORLD-DEMO-006`, `WORLD-CULT-001`, `WORLD-CULT-003`
  (and still rejects `not-a-valid-id`, `world-001`, `WORLD-DEMO-01`, `WORLD--001`); and
  `next_available_id('world_dynamics.yaml')` returns `WORLD-DEMO-007`,
  `next_available_id('combat_movement.yaml')` still returns `COMB-320` (matching the shard's real
  highest id `COMB-319`), confirming no single-segment regression.

Total: 40/40 targeted tests pass, 61/61 broader-regression tests pass (10 skipped, pre-existing
and unrelated to this change).

## Files Changed
- `tools/parity_ledger_writer.py` — extended `_ID_PATTERN` to accept multi-segment prefixes.
- `docs/parity_ledger/schema.json` — extended `properties.id.pattern` to the byte-identical regex.
- `tools/gate_checks/parity_updater_static.py` — extended `_ID_PATTERN`; reworked
  `next_available_id` to track max suffix per full prefix family instead of globally.
- `tests/tools/test_parity_ledger_writer.py` — added multi-segment `validate_entry()` acceptance
  tests (parametrized synthetic cases) and a real-corpus regression test against
  `docs/parity_ledger/world_dynamics.yaml`.
- `tests/tools/test_parity_updater_static.py` — added multi-segment `next_available_id()` tests
  (synthetic single-family, synthetic mixed-family regression guard, and real-corpus proof against
  `docs/parity_ledger/world_dynamics.yaml`).
- `docs/engine/contracts/knowledge_gateway_mcp_contract.md` — Document-Update phase: updated a
  stale quoted regex citation (`^[A-Z]+-[0-9]{3}$`) in the Parity Ledger provider adapter's
  `stable_entity_ids: "FULL"` justification to the new `^[A-Z]+(-[A-Z]+)*-[0-9]{3}$`, with a note
  attributing the extension to this ticket.
- `docs/parity_ledger/infrastructure.yaml` — Parity phase: updated `INFRA-381` (the entry
  documenting `next_available_id`/`search_existing_entries`'s own behavior) — refreshed
  `v2_evidence` line citations and description (from "max numeric suffix per shard" to "max numeric
  suffix per full prefix family"), appended a note on the cross-family-leak fix to `text`, expanded
  `test_path` from 1 to 4 tests, and extended `support_boundary`. Written via
  `tools/parity_ledger_writer.py::write_entry`, not raw-edited.
- `tickets/inprogress/TCK-20260831-PARITY-LEDGER-ID-PATTERN-MULTISEGMENT.md` — this ticket file
  (Implementation Notes, Test Summary, Files Changed, Completion Summary, Status, Acceptance
  Criteria checkboxes filled in).

No `staging_artifacts/` were created or rewritten for this ticket — hotfix tier does not require
`plan.md`/`investigation.md`/`test_plan.md`, and none were created during this run.

## Completion Summary
Extended the parity ledger's id-pattern validation and generation logic to accept multi-segment
shard-id prefixes (e.g. `WORLD-DEMO-001`, `WORLD-CULT-001`), fixing a structural gap where
`tools/parity_ledger_writer.py::_ID_PATTERN` and `docs/parity_ledger/schema.json`'s
`properties.id.pattern` rejected the already-live `WORLD-DEMO-*`/`WORLD-CULT-*` entries in
`docs/parity_ledger/world_dynamics.yaml`. Also fixed `tools/gate_checks/parity_updater_static.py`'s
`next_available_id`, which previously tracked a single global max-suffix across all matching
entries in a shard — correct only for single-family shards — by reworking it to track the max
suffix per full id-prefix family, so it now correctly proposes `WORLD-DEMO-007` for the real shard
instead of silently ignoring the `WORLD-DEMO-*` family (or, worse, letting one family's suffix
leak into another's proposed id). Verified all four acceptance criteria directly against the real
ledger content, not just synthetic fixtures, and confirmed zero regression across all existing
tests that import these symbols.
