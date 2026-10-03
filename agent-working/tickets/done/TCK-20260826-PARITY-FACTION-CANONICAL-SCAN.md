---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260826-PARITY-FACTION-CANONICAL-SCAN
phase: done
date: 2026-08-26
tags: [ai, workflows, faction, determinism]
---

# TCK-20260826-PARITY-FACTION-CANONICAL-SCAN

## Title
Add `faction.yaml` to `CANONICAL_LEDGER_FILES` so the Parity-phase deterministic gate stops excluding a real, actively-maintained ledger shard

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`docs/parity_ledger/faction.yaml` is a real, actively-maintained parity ledger shard (15 entries,
`FAC-XXX`/`FACTION-TENSION-XXX` IDs, same `schema.json` shape as the other 9 shards — confirmed by
direct read) sitting directly under `docs/parity_ledger/`, but `tools/parity_ledger_scan.py`'s
`CANONICAL_LEDGER_FILES` tuple (the single source of truth consumed by `find_p0_intersection`,
and — via import — by `tools/gate_checks/parity_updater_static.py`'s `derive_mapping` /
`expected_subsystems_for_files` / `cross_reference_touched` / `next_available_id` /
`search_existing_entries` and by `tools/gate_checks/mechanics_auditor_static.py`) omits it. The
exclusion was deliberate when built (`TCK-20260705-WORKFLOW-PARITY-SKIP`, whose own docstring
justified it as "`faction.yaml` ... has 0 P0 entries today"), but that premise is no longer true:
`faction.yaml`'s `FAC-013` entry is `priority: P0` today (line 310), so `find_p0_intersection`'s
P0-safeguard scan can silently miss a real P0 regression whose changed file overlaps `FAC-013`'s
`v2_evidence`. Confirmed live this session (twice, on `TCK-20260822-PAID-INFO-INDEX-RETROFIT` and
`TCK-20260822-GUARD-SCAN-INDEX-RETROFIT`, both visible in `tickets/working_log.csv`) that a ticket
correctly documenting a parity change only in `faction.yaml` still fails the Parity-phase
cross-reference gate.

`tools/parity_index.py` (the newer SQLite-backed index, `TCK-20260731-PARITY-INDEX-IMPORTER`) already
globs all 9 shards including `faction.yaml`, deliberately independent of `CANONICAL_LEDGER_FILES` —
so this gap is confined to the "legacy" deterministic-gate side (`parity_ledger_scan.py` +
`gate_checks/parity_updater_static.py` + `gate_checks/mechanics_auditor_static.py`), not the SQLite
index.

## Scope
- Add `"faction.yaml"` to `CANONICAL_LEDGER_FILES` in `tools/parity_ledger_scan.py`, and correct that
  module's docstring/comments that currently describe `faction.yaml` as excluded and cite "0 P0
  entries today" (now false — `FAC-013` is P0).
- Update the Parity-phase agent prompt in `.claude/workflows/implement-ticket.js` (line ~1264, the
  `Update docs/parity_ledger/ entries (files: substrate.yaml, ...)` string) to list `faction.yaml` as
  a 9th valid target file, so the `parity-updater` agent itself knows it is an accepted destination.
- Update every existing test that currently asserts the old exclusion as correct behavior, since the
  fix inverts the behavior they pin:
  - `tests/tools/test_parity_ledger_scan.py::test_only_scans_canonical_eight_not_faction` — rewrite
    to assert inclusion (or replace with an equivalent positive-coverage test); update/remove the
    `"faction.yaml" not in CANONICAL_LEDGER_FILES` assertion.
  - `tests/tools/test_parity_index_baseline.py::test_faction_fixture_matches_live_legacy_scan_output`
    and `::test_faction_yaml_included_in_manifest_shard_list_but_excluded_from_legacy_fixture` (uses
    the `tests/tools/fixtures/parity_index_baseline/faction_case/faction.yaml` fixture).
  - `tests/tools/test_parity_index.py::.test_faction_evidence_case_present_in_new_index_despite_legacy_exclusion`.
  - Any other test in these three files whose name/assertions encode "faction.yaml is excluded from
    the legacy/canonical scan" as expected behavior — audit for it explicitly, don't assume the list
    above is exhaustive.
- Add a new regression test proving `find_p0_intersection` now detects an intersection against a real
  or synthetic `faction.yaml` P0 entry (mirroring the existing
  `test_detects_p0_intersection_via_synthetic_fixture` pattern), and ideally one exercising the real
  `FAC-013` case directly against `docs/parity_ledger` so the fix's real-world effect is covered, not
  just a synthetic fixture.
- Check `docs/parity_ledger/README.md` and any other doc prose describing "8 canonical files" /
  "the canonical eight" for staleness and update if found.

## Out of Scope
- Any change to `tools/parity_index.py` / `tools/parity_index_baseline.py` — they already include
  `faction.yaml` deliberately, independent of `CANONICAL_LEDGER_FILES`; do not touch their logic.
- Renumbering, editing, or re-verifying the content of any existing `faction.yaml` entry (including
  `FAC-013`'s P0 status or evidence) — this ticket only fixes the tooling's file-set, not ledger
  content.
- Building a new merge-conflict guard or ID-collision CI check for `docs/parity_ledger/*.yaml` — that
  is `TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS`'s scope (backlog, different gap), not this one.
- Adding any other non-canonical `*.yaml` file under `docs/parity_ledger/` to `CANONICAL_LEDGER_FILES`
  — `ls docs/parity_ledger/` confirms `faction.yaml` is the only non-canonical, non-`README.md`/
  `schema.json` `*.yaml` file present today; if a future file appears, that is a new ticket.
- Reworking `next_available_id` / `search_existing_entries`'s default-shard-list behavior beyond the
  effect of the `CANONICAL_LEDGER_FILES` tuple change itself (they already accept an explicit
  `shard_filename` override and need no code change).

## Acceptance Criteria
- [x] `"faction.yaml" in CANONICAL_LEDGER_FILES` is true in `tools/parity_ledger_scan.py`.
- [x] `find_p0_intersection(["<path substring from FAC-013's v2_evidence>"], ledger_dir="docs/parity_ledger")`
      returns a hit including `("faction.yaml", "FAC-013", ...)` — proving the real live P0 gap is
      closed, not just a synthetic fixture.
- [x] `expected_subsystems_for_files` / `derive_mapping` (`tools/gate_checks/parity_updater_static.py`)
      include `faction.yaml` as a candidate for any `src/` path cited in its `v2_evidence` fields.
- [x] `.claude/workflows/implement-ticket.js`'s Parity-phase prompt text lists `faction.yaml` alongside
      the other 8 files.
- [x] All pre-existing tests that asserted the old exclusion are updated to assert the new inclusion
      behavior (or removed if superseded) — no test in the repo still asserts
      `"faction.yaml" not in CANONICAL_LEDGER_FILES` or equivalent exclusion behavior.
- [x] `pytest tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_updater_static.py tests/tools/test_parity_index.py tests/tools/test_parity_index_baseline.py tests/tools/test_gate_a_readpath_review.py` passes.
- [x] `next_available_id("faction.yaml")` and `search_existing_entries(<query>, shard_filename="faction.yaml")` continue to work unchanged (they already accept explicit shard names; verify no regression).

## Related Tickets
- TCK-20260705-WORKFLOW-PARITY-SKIP (built `find_p0_intersection` / `CANONICAL_LEDGER_FILES`, on the
  now-stale "faction.yaml has 0 P0 entries" premise this ticket corrects)
- TCK-20260705-GATE-DET-PARITY-UPDATER (built `derive_mapping` / `expected_subsystems_for_files` /
  `cross_reference_touched` in `tools/gate_checks/parity_updater_static.py`, which import
  `CANONICAL_LEDGER_FILES` by reference and inherit this fix automatically)
- TCK-20260705-GATE-DET-MECHANICS-AUDITOR (built `tools/gate_checks/mechanics_auditor_static.py`,
  which also imports `CANONICAL_LEDGER_FILES` and inherits this fix automatically)
- TCK-20260731-PARITY-INDEX-IMPORTER / TCK-20260731-PARITY-INDEX-BASELINE (built `tools/parity_index.py`,
  which already scans all 9 shards including `faction.yaml`, independent of `CANONICAL_LEDGER_FILES`
  — confirms this gap is confined to the legacy-gate side)
- TCK-20260824-PARITY-NEXT-ID-LOOKUP (built `next_available_id` / `search_existing_entries`, which
  default to `CANONICAL_LEDGER_FILES` and inherit this fix automatically for their default-scan case)
- TCK-20260822-PAID-INFO-INDEX-RETROFIT, TCK-20260822-GUARD-SCAN-INDEX-RETROFIT (this session's two
  live confirmations of the gate blocking a correct `faction.yaml`-only parity change)

## Related Docs
- docs/parity_ledger/schema.json (confirmed `faction.yaml` conforms — same `id` pattern, same
  `status`/`priority`/`proof_type` enums, same required-field rules)
- docs/parity_ledger/README.md
- docs/parity_ledger/faction.yaml

## Related Stored Artifacts
- stored_artifacts/TCK-20260705-WORKFLOW-PARITY-SKIP/investigation.md (original "0 P0 entries" empirical
  finding, now stale)
- stored_artifacts/TCK-20260705-GATE-DET-PARITY-UPDATER/
- stored_artifacts/TCK-20260731-PARITY-INDEX-IMPORTER/investigation.md (documents the deliberate
  independence of the SQLite index from `CANONICAL_LEDGER_FILES`)
- stored_artifacts/TCK-20260824-PARITY-NEXT-ID-LOOKUP/ (if present)

## Related Code Areas
- tools/parity_ledger_scan.py
- tools/gate_checks/parity_updater_static.py
- tools/gate_checks/mechanics_auditor_static.py
- .claude/workflows/implement-ticket.js
- tests/tools/test_parity_ledger_scan.py
- tests/tools/test_parity_updater_static.py
- tests/tools/test_parity_index.py
- tests/tools/test_parity_index_baseline.py
- tests/tools/test_gate_a_readpath_review.py
- tests/tools/fixtures/parity_index_baseline/faction_case/faction.yaml
- docs/parity_ledger/faction.yaml
- docs/parity_ledger/README.md

## Assumptions / Open Questions
- Tier set to `standard`, not the requester's initial `hotfix` guess: the requester explicitly asked
  to verify the tier once the blast radius was read, and investigation found real complexity beyond a
  single tuple edit — the change cascades correctly (by import) into
  `parity_updater_static.py`/`mechanics_auditor_static.py` (good: single source of truth), but it also
  inverts behavior pinned by 3+ existing regression tests across 3 test files (including one static
  fixture file) plus a hardcoded file-list string in `implement-ticket.js`'s Parity-phase prompt. That
  coordinated, multi-file blast radius is exactly the "substantive change" `standard` tier is for, per
  CLAUDE.md's Tier Routing table — not a self-evident one-liner.
- Assumes `faction.yaml`'s schema conformance (confirmed by direct read of its structure against
  `schema.json`) means no shard-specific parsing changes are needed anywhere in the scanned functions
  — only the file-set tuple and the prompt string.
- Assumes `ls docs/parity_ledger/` is complete and no other non-canonical `*.yaml` shard exists besides
  `faction.yaml` (confirmed: `combat_movement.yaml, faction.yaml, infrastructure.yaml, progression.yaml,
  social_narrative.yaml, strategic_cognition.yaml, substrate.yaml, town_resource.yaml, world_dynamics.yaml`
  — exactly the canonical 8 plus `faction.yaml`, plus `README.md`/`schema.json`).
- `layer: ai` chosen over `layer: testing` because this ticket's core surface area is Claude
  agent/orchestration gate-check tooling (`tools/gate_checks/`, `implement-ticket.js`'s Parity phase),
  matching the precedent set by the directly-related `TCK-20260705-WORKFLOW-PARITY-SKIP` and
  `TCK-20260824-PARITY-NEXT-ID-LOOKUP` tickets (both `layer: ai`) — the test-file changes are
  necessary follow-through, not the primary subsystem.
- Open question for Investigate/Plan: whether `docs/parity_ledger/README.md` or any other doc prose
  needs a wording update beyond what a grep search in this scoping pass found (none found, but the
  scoping pass's search was not exhaustive across all of `docs/`).

## Implementation Notes
Followed `staging_artifacts/TCK-20260826-PARITY-FACTION-CANONICAL-SCAN/plan.md`'s 10 steps exactly,
plus one additional step added per Plan-review's advisory note (a positive-control test on
`mechanics_auditor_static.find_entry`).

- **Step 1**: Appended `"faction.yaml"` as the 9th element of `CANONICAL_LEDGER_FILES` in
  `tools/parity_ledger_scan.py` (single source of truth, consumed by import elsewhere — no other
  file duplicates this list). Corrected the module docstring and `find_p0_intersection`'s docstring
  to drop the now-false "faction.yaml excluded / 0 P0 entries" claim.
- **Step 2**: Appended `, faction.yaml` to the Parity-phase prompt file-list string in
  `.claude/workflows/implement-ticket.js` (line ~1264).
- **Steps 3–4** (`tests/tools/test_parity_ledger_scan.py`): renamed and inverted
  `test_only_scans_canonical_eight_not_faction` → `test_scans_canonical_nine_including_faction`
  (now asserts inclusion and the correct hit tuple); added
  `test_detects_real_fac013_p0_intersection` against the real `docs/parity_ledger` directory and the
  real `FAC-013` P0 entry (`v2_evidence` citing `src/observability/event_extractor.py`).
- **Steps 5–6** (`tests/tools/test_parity_updater_static.py`): renamed/inverted
  `test_excludes_faction_yaml` → `test_includes_faction_yaml`; added
  `test_expected_subsystems_includes_faction_for_real_ledger_path` against the real ledger and the
  same `FAC-013` evidence path.
- **Step 7** (`tests/tools/test_parity_index_baseline.py`): confirmed the `faction_case` fixture's
  entry is `FAC-001`/P0/`src/factions/diplomacy.py` before writing exact-tuple assertions. Renamed
  `test_manifest_records_legacy_eight_shard_faction_gap` → `test_manifest_records_no_legacy_shard_gap`
  (now asserts `excluded_from_legacy_scan == []`); inverted
  `test_faction_fixture_matches_live_legacy_scan_output`'s expected hit; renamed
  `test_faction_yaml_included_in_manifest_shard_list_but_excluded_from_legacy_fixture` →
  `..._and_legacy_fixture` with inverted assertions. No production code changed in
  `tools/parity_index_baseline.py` — `excluded_from_legacy_scan` is computed from
  `CANONICAL_LEDGER_FILES` and recomputed to `[]` automatically.
- **Step 8** (`tests/tools/test_parity_index.py`): renamed
  `test_faction_evidence_case_present_in_new_index_despite_legacy_exclusion` →
  `..._present_in_both_legacy_and_new_index`. Left the `legacy_hits == []` assertion value unchanged
  (still `[]` post-fix, but now because the fixture's `FAC-801` entry is priority `P1`, not because
  `faction.yaml` is unscanned — comment updated to state this). Inverted the `derive_mapping`
  assertion to `legacy_mapping["src/factions/diplomacy.py"] == {"faction.yaml"}`. Left
  `TestAllShardsCoverage` and all `tools/parity_index.py`-facing assertions untouched (Out of Scope).
- **Step 9** (`tests/tools/test_gate_a_readpath_review.py`): rewrote the `FACTION_EXCLUSION` prose
  constant to describe the corrected state instead of asserting the now-false "structurally blind"
  claim, per the plan's Anti-Drift design call. Left the two `shards_scanned_legacy: 8` integer
  literals and their assertion untouched (explicitly out of scope per ticket/plan).
- **Step 10** (new `tests/tools/test_parity_prompt_ledger_file_list.py`): added a static-prose guard
  asserting all 9 canonical filenames, including `faction.yaml`, appear in the Parity-phase prompt
  string inside `implement-ticket.js`.
- **Step 11 (added per Plan-review's advisory note, additional to the plan's 10 steps)**: added
  `test_find_entry_locates_real_fac013_in_faction_yaml` to `tests/tools/test_mechanics_auditor_static.py`,
  asserting `mechanics_auditor_static.find_entry("FAC-013", ledger_dir="docs/parity_ledger")` now
  returns `(entry, "faction.yaml")` — mirrors the Step 4/6 real-ledger pattern for the third function
  (`find_entry`) that consumes `CANONICAL_LEDGER_FILES` by import but had no dedicated real-ledger
  positive-control test in the plan.

No production code changes were needed in `tools/gate_checks/parity_updater_static.py` or
`tools/gate_checks/mechanics_auditor_static.py` — both import `CANONICAL_LEDGER_FILES` by reference
and inherited the fix automatically, exactly as the investigation predicted. No changes were made to
`tools/parity_index.py` / `tools/parity_index_baseline.py` logic, or to any `docs/parity_ledger/*.yaml`
content, per the ticket's Out of Scope.

## Test Summary
Ran the ticket's exact AC #6 command plus the new file and the mechanics_auditor_static file:
`pytest tests/tools/test_parity_ledger_scan.py tests/tools/test_parity_updater_static.py
tests/tools/test_parity_index.py tests/tools/test_parity_index_baseline.py
tests/tools/test_gate_a_readpath_review.py tests/tools/test_mechanics_auditor_static.py
tests/tools/test_parity_prompt_ledger_file_list.py` → **102 passed, 10 skipped** (skips pre-existing,
unrelated to this ticket). No test outside `tests/tools/` was run, per the plan's Scope Guards
("never run pytest tests/ in full").

## Files Changed
- `tools/parity_ledger_scan.py` — `CANONICAL_LEDGER_FILES` tuple + docstrings
- `.claude/workflows/implement-ticket.js` — Parity-phase prompt file list
- `tests/tools/test_parity_ledger_scan.py` — inverted/renamed exclusion test, added real-ledger P0 test
- `tests/tools/test_parity_updater_static.py` — inverted/renamed exclusion test, added real-ledger test
- `tests/tools/test_parity_index_baseline.py` — inverted/renamed 3 exclusion-pinning tests
- `tests/tools/test_parity_index.py` — renamed test, updated comment, inverted `derive_mapping` assertion
- `tests/tools/test_gate_a_readpath_review.py` — corrected `FACTION_EXCLUSION` prose constant
- `tests/tools/test_mechanics_auditor_static.py` — added `find_entry` real-ledger positive-control test (advisory step 11)
- `tests/tools/test_parity_prompt_ledger_file_list.py` — new file, static-prose guard test
- `staging_artifacts/TCK-20260826-PARITY-FACTION-CANONICAL-SCAN/plan.md` — added Deviations section
- `tickets/inprogress/TCK-20260826-PARITY-FACTION-CANONICAL-SCAN.md` — this file

## Completion Summary
Added `faction.yaml` as the 9th element of `tools/parity_ledger_scan.py`'s single-source-of-truth
`CANONICAL_LEDGER_FILES` tuple, which by import automatically fixed `find_p0_intersection`,
`derive_mapping`, `expected_subsystems_for_files`, `cross_reference_touched`, and `find_entry` to
stop being structurally blind to `faction.yaml` — closing the real gap where `FAC-013` (a `P0`
parity-ledger entry) was invisible to the deterministic Parity-phase safeguard. Updated the matching
hardcoded file-list prose in `implement-ticket.js`'s Parity-phase prompt, rewrote the 7 existing
tests (across 4 test files) that pinned the old exclusion as correct behavior, corrected one stale
prose constant in a fifth test file, and added 4 new positive-control tests (3 from the plan, 1 from
the Plan-review's advisory note) proving the fix against the real, non-synthetic ledger. All 10
planned steps plus the added advisory test step are complete; the full scoped test command in AC #6
passes (102 passed, 10 pre-existing skips).
