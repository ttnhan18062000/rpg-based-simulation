---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK
artifact_type: test_plan
tags: [ai, agent-monitoring, process-improvement]
---

# Test Plan — TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK

## Regression Surface

Existing tests that must keep passing unmodified (all currently green — 11 passed, verified via
`pytest tests/tools/test_epic_staleness_check.py -q` during investigation):

**Unit (`tests/tools/test_epic_staleness_check.py`, 11 tests):**
- `test_does_not_flag_never_started_real_obsiso_epic` — real-repo integration case
  (`TCK-20260702-OBSISO-EPIC`); must keep resolving to exactly the same single-candidate outcome
  after dedupe is added (no accidental collapse or duplication of unrelated real epics).
- `test_does_not_flag_recently_active_epic`
- `test_identifies_epic_tickets_vs_regular_tickets` — asserts `len(candidates) == 1` for a single
  epic among mixed-tier tickets; a naive/broken dedupe implementation must not accidentally reduce
  this to 0 or leave it at 1 for the wrong reason.
- `test_handles_hybrid_folder_shape` — folder-mode `len(candidates) == 1` baseline; must not
  regress once cross-mode dedupe logic is added (this fixture has no `tickets/inprogress/`
  counterpart, so a correct dedupe must be a no-op here).
- `test_handles_missing_or_malformed_sequence_md`
- `test_epic_with_all_children_stale`
- `test_does_not_flag_never_started_epic`
- `test_advisory_only_no_file_mutation` — real-repo byte-hash guard; dedupe change must not add any
  write path.
- `test_advisory_only_never_raises_on_missing_files`
- `test_working_log_dictreader_not_column_index`
- `test_working_log_row_missing_ticket_id_key_does_not_raise`

**Integration (sibling modules that import from `epic_staleness_check.py` and must not break):**
- `tests/tools/test_scope_orphan_fix.py` (7 tests) — imports/depends on
  `scope_ticket_relocate.py`, which imports `_section_body` from `epic_staleness_check.py`. Must
  stay green since this ticket touches the same module (different function, but same file).
- `tests/tools/test_epic_scope_orphan_check.py` (6 tests) — imports `_section_body` from
  `epic_staleness_check.py` via `epic_scope_orphan_check.py`. Same rationale.

No arena-combat / simulation-domain tests apply — this is pure `layer: ai` tooling with zero
overlap with `src/` gameplay code.

## New Tests Required

Per AC 1 ("given a fixture epic present in both `tickets/inprogress/` and
`tickets/todos/{folder}/` simultaneously, is confirmed via a new test to dedupe and report the epic
exactly once"):

1. **`test_discover_candidate_epics_dedupes_dual_presence`**
   - Category: unit
   - Verifies: build a fixture where the *same* `ticket_id` (e.g.
     `TCK-20260701-DUAL-PRESENCE-EPIC`) exists as an epic-tier ticket both directly under
     `inprogress_dir` (epic_id mode) and inside `todos_dir/some-folder/` (folder mode, with a
     matching `SEQUENCE.md` or as the folder's own epic ticket file) — reuse the existing
     `_write_ticket(path, ticket_id, tier, date_str, related_tickets="")` helper (test file line 42)
     for both writes, same `ticket_id` argument both times. Asserts
     `len(discover_candidate_epics(inprogress_dir, todos_dir)) == 1` and that the single surviving
     candidate's `epic_id` equals the shared ticket_id. This directly targets the AC's literal
     wording ("discover_candidate_epics() ... confirmed ... to dedupe").
   - Location: `tests/tools/test_epic_staleness_check.py` (append after the existing 11, same file,
     same fixture-writing conventions).

2. **`test_dual_presence_not_double_reported_in_stale_list`**
   - Category: integration (exercises the full discovery → classification → report pipeline, not
     just the discovery function in isolation)
   - Verifies: with the same dual-presence fixture as test 1, plus a `working_log.csv`-equivalent
     activity row old enough to cross the staleness window (mirroring
     `test_epic_with_all_children_stale`'s pattern), `find_stale_epics(...)` returns the epic's
     `epic_id` **exactly once** (not twice), and `compute_stale_epics_report(...)`'s "Stale epics:"
     section contains exactly one line for that `epic_id`. This is the anti-drift guard that proves
     the dedupe fix actually prevents the double-nudge symptom described in the ticket's Request
     Summary, not just a narrower unit-level dedupe that downstream code could still defeat.
   - Location: `tests/tools/test_epic_staleness_check.py`.

3. **(Optional, if the Plan phase's tie-break decision — see investigation.md Risk 4 — needs
   explicit coverage) `test_dual_presence_prefers_inprogress_candidate`**
   - Category: unit
   - Verifies: when the dedupe survivor is deterministically the `epic_id`-mode
     (`tickets/inprogress/`) candidate rather than the folder-mode one (asserting on
     `candidate.mode == "epic_id"` and/or `candidate.source_path` pointing at `inprogress_dir`),
     locking in whichever tie-break the implementation picks so a future refactor cannot silently
     flip it.
   - Location: `tests/tools/test_epic_staleness_check.py`. Only add this if the Plan phase commits
     to a specific tie-break; if the implementation treats the two candidates as interchangeable
     (unlikely, since `mode`/`source_path` differ), skip this test and only assert survivor count +
     `epic_id`, per test 1.

Per AC 2 ("Existing test_epic_staleness_check.py coverage ... continues to pass unmodified") — no
new test needed; covered by the Regression Surface section's pytest command below, run both before
and after the change.

## Scoped Pytest Commands

Before implementation (baseline, confirm current green state):
```
pytest tests/tools/test_epic_staleness_check.py -v
```

After implementation (full regression + new tests, matching the sibling ticket's precedent of
bundling all agent-monitoring-tooling files that share this module's dependency graph):
```
pytest tests/tools/test_epic_staleness_check.py tests/tools/test_scope_orphan_fix.py tests/tools/test_epic_scope_orphan_check.py -v
```

Never: `pytest tests/` (repo-wide). This ticket's blast radius is a single file plus its two known
importers; no other domain is touched.

## Anti-Drift Test Guards

- **`test_handles_hybrid_folder_shape` and `test_identifies_epic_tickets_vs_regular_tickets` must
  stay at `len(candidates) == 1`, unchanged.** These are the two existing tests whose fixtures have
  no cross-location duplicate; a dedupe implementation that over-eagerly collapses candidates by any
  key looser than exact `epic_id` match (e.g. accidentally keying by `source_path.name` or by folder
  name) would risk merging genuinely distinct epics or leaving these baselines at the wrong count.
  Keeping both green is the guard against an overly-aggressive or mis-keyed dedupe.
- **`test_does_not_flag_never_started_real_obsiso_epic`** (real-repo integration test) is the guard
  against the dedupe fix accidentally touching live-repo discovery behavior — `TCK-20260702-OBSISO-EPIC`
  has no dual-presence counterpart today, so its classification must be byte-identical
  before/after this change.
- **`test_advisory_only_no_file_mutation`** guards against the dedupe implementation introducing any
  write path (it must remain a pure in-memory filter over the `candidates` list — no ticket file
  should ever be read-write-touched by this fix).
- New test 2 (`test_dual_presence_not_double_reported_in_stale_list`) is itself the primary
  anti-drift guard against scope creep in the *other* direction: a fix that only deduplicates inside
  `discover_candidate_epics()`'s own return value but that some future refactor of
  `_classify_candidates()` could bypass (e.g. by calling `discover_candidate_epics()` twice, once
  per mode, and concatenating) would still leave the observable double-nudge symptom. Testing the
  full `find_stale_epics()` / `compute_stale_epics_report()` path, not just
  `discover_candidate_epics()` in isolation, closes that gap.
- Do not add assertions inside these new tests that reach into `resolve_and_relocate_ticket()` or
  `epic_scope_orphan_check.py` — those are the sibling ticket's already-closed, already-tested
  surface; pulling them into this ticket's test file would blur the two tickets' boundaries the
  ticket's own Out of Scope section draws.
