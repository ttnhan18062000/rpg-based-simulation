---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK
artifact_type: plan
tags: [ai, agent-monitoring, process-improvement]
---

# Implementation Plan — TCK-20260711-EPIC-STALENESS-DEDUPE-CHECK

## Summary

`discover_candidate_epics()` in `tools/agent-monitoring/epic_staleness_check.py` (currently lines
119-188, live-read-confirmed — the ticket's cited "119-163" is stale line drift, not a real
discrepancy) runs two independent discovery loops — epic_id-mode over `tickets/inprogress/*.md`
(lines 122-139) and folder-mode over `tickets/todos/{folder}/` (lines 141-186) — into one flat
`candidates` list with no dedupe-by-`epic_id` before returning it at line 188. When the same epic
ticket exists in both locations (a real, if narrow, transient window per investigation.md Risk 1 —
`resolve_and_relocate_ticket()`'s non-atomic copy-then-unlink for epic tier — plus unguarded manual
copies per Risk 2), the epic is discovered twice and propagates as two separate report lines and an
inflated stale-count downstream through `_classify_candidates()`, `find_stale_epics()`, and
`compute_stale_epics_report()`.

The fix is a narrow, in-memory, key-based dedupe pass added directly inside
`discover_candidate_epics()`, immediately before its `return` statement — **not** a call into the
separate, unwired `epic_scope_orphan_check.py::check_single_epic_orphan()` module. Rationale: the
ticket's own AC text explicitly names `discover_candidate_epics()` as the fix site ("add dedupe
logic to `discover_candidate_epics()`"); the file already has an established local pattern for
exactly this kind of order-preserving dedupe (`_dedupe_preserve_order()`, line 59, used twice
elsewhere in the same file for string-list dedupe); and reusing `epic_scope_orphan_check.py` would
require importing across `tools/agent-monitoring/` modules and re-deriving existence-by-path-check
for a single narrow purpose, creating a new cross-module dependency where none exists today and
duplicating detection logic that already lives correctly in-list. `_dedupe_preserve_order()` itself
operates on plain strings and is reused elsewhere for that exact shape (child-ID dedupe within one
ticket's text) — it is **not** modified or repurposed for this fix; a new, separate helper is added
alongside it that dedupes `EpicCandidate` objects keyed by `.epic_id` instead, keeping both helpers
single-purpose.

Tie-break: when both a `tickets/inprogress/` (epic_id-mode) candidate and a `tickets/todos/{folder}/`
(folder-mode) candidate share the same `epic_id`, the epic_id-mode candidate survives. This is made
to hold explicitly, not accidentally, in two ways: (1) the epic_id-mode loop (lines 122-139) is kept
running strictly before the folder-mode loop (lines 141-186) in `discover_candidate_epics()` — this
plan's Step 1 states this ordering must not be reordered as part of the fix; (2) the new dedupe
helper implements "first occurrence wins" semantics (matching `_dedupe_preserve_order()`'s existing
style), so with epic_id-mode enumerated first, its candidate is always the one kept. This choice also
matches the documented authoritative resting place for epic-tier tickets in
`docs/ai/ticket-lifecycle.md:440` and the sibling ticket's own confirmation that `tickets/inprogress/`
placement for epic_id-mode epics is correct.

No parity ledger entry is added by this plan. Per investigation.md's Parity Ledger Overlap section,
this follows the precedent set by `TCK-20260710-EPIC-STALENESS-CHECK` (the ticket that built this
same file), whose Completion Summary states no parity entry applies because this is pure
Claude-agent-orchestration tooling (`layer: ai`), not a tracked simulation subsystem. This plan
carries that same position forward explicitly rather than silently assuming it, and flags it for the
Parity phase to confirm (not skip) — if Parity disagrees because this touches the same file family
as INFRA-265 (the sibling ticket's ledger entry), an entry should be added there, not here.

## Steps

### Step 1 — Add keyed dedupe helper and wire it into discover_candidate_epics()'s return
**Files:** `tools/agent-monitoring/epic_staleness_check.py`

**Change:**
1. Add a new helper function immediately after `_dedupe_preserve_order()` (after line 66, before
   `_frontmatter_block()` at line 69) that dedupes a list of `EpicCandidate` objects by `.epic_id`,
   first-occurrence-wins:
   ```python
   def _dedupe_candidates_by_epic_id(candidates: list) -> list:
       seen = set()
       result = []
       for candidate in candidates:
           if candidate.epic_id not in seen:
               seen.add(candidate.epic_id)
               result.append(candidate)
       return result
   ```
   This is a new, separate helper — do not modify `_dedupe_preserve_order()` itself (it is used
   elsewhere in this file for plain-string dedupe with different call sites and must keep that
   exact signature/behavior).
2. Change the `return candidates` statement at the end of `discover_candidate_epics()` (currently
   line 188) to `return _dedupe_candidates_by_epic_id(candidates)`.
3. Do **not** reorder the two discovery loops inside `discover_candidate_epics()` — the epic_id-mode
   loop (`if inprogress_dir.exists(): ...`, currently lines 122-139) must remain textually before the
   folder-mode loop (`if todos_dir.exists(): ...`, currently lines 141-186), so that first-occurrence
   dedupe naturally resolves the tie-break in favor of the epic_id-mode (`tickets/inprogress/`)
   candidate per this plan's Summary.

**Do NOT touch:**
- `_dedupe_preserve_order()` (line 59) — leave its body, signature, and both existing call sites
  (`_child_ids_from_text()` line 112, folder-mode sibling-files fallback line 176) exactly as-is.
- The body of either discovery loop (epic_id-mode lines 122-139, folder-mode lines 141-186) beyond
  what's needed to confirm loop order — no changes to `EpicCandidate` construction, field values, or
  the `_section_body`/`_frontmatter_field`/`_parse_epic_date`/`_child_ids_from_text` calls inside
  either loop.
- `EpicCandidate`'s dataclass shape (line 46-52) and `discover_candidate_epics()`'s parameter
  signature `(inprogress_dir: Path, todos_dir: Path)` — both are depended on directly by
  `epic_scope_orphan_check.py` and `scope_ticket_relocate.py`.
- `resolve_child_activity()`, `_classify_candidates()`, `find_stale_epics()`,
  `compute_stale_epics_report()`, `is_epic_stale()`, `is_epic_never_started()`, or any
  classification/reporting code below line 188 — the fix is scoped entirely to
  `discover_candidate_epics()`'s own return value.
- `resolve_and_relocate_ticket()` / `.claude/workflows/implement-ticket.js` / `epic_scope_orphan_check.py`
  / `done_checker_static.py` — all sibling-ticket territory, explicitly out of scope.

**Verify:**
- New test `test_discover_candidate_epics_dedupes_dual_presence` (added in Step 2) passes:
  `len(discover_candidate_epics(inprogress_dir, todos_dir)) == 1` for the dual-presence fixture, and
  the surviving candidate's `epic_id` equals the shared ticket_id.
- Baseline regression: `test_identifies_epic_tickets_vs_regular_tickets` and
  `test_handles_hybrid_folder_shape` both continue to assert `len(candidates) == 1` unchanged (no
  fixture in either test has a cross-location duplicate, so the new dedupe pass must be a no-op for
  both).
- `pytest tests/tools/test_epic_staleness_check.py -v` — all 11 pre-existing tests plus new tests
  green.

### Step 2 — Add discovery-level dual-presence regression test
**Files:** `tests/tools/test_epic_staleness_check.py`

**Change:** Append `test_discover_candidate_epics_dedupes_dual_presence` after the existing 11 tests
(do not insert between or renumber existing tests). Build a fixture using the established
`_write_ticket(path, ticket_id, tier, date_str, related_tickets="")` helper (test file line 42, reuse
exactly, do not modify its signature) called twice with the **same** `ticket_id` (e.g.
`TCK-20260701-DUAL-PRESENCE-EPIC`, `tier="epic"`):
1. Once writing directly into `inprogress_dir` (epic_id mode).
2. Once writing into a subdirectory of `todos_dir` (e.g. `todos_dir / "some-folder" / "TCK-...md"`,
   folder mode) — with a `SEQUENCE.md` alongside it if needed to satisfy the folder-mode discovery
   precondition (`has_sequence or epic_ticket_file is not None`), matching
   `test_handles_hybrid_folder_shape`'s existing fixture-writing pattern for folder mode.

Assert `len(discover_candidate_epics(inprogress_dir, todos_dir)) == 1` and that the single surviving
candidate's `.epic_id` equals the shared `ticket_id`. This is the test named in the ticket's AC 1 and
in test_plan.md's "New Tests Required" item 1.

**Do NOT touch:** Any of the existing 11 tests in this file, the `_write_ticket` helper's signature,
or `tests/tools/test_scope_orphan_fix.py` / `tests/tools/test_epic_scope_orphan_check.py` (sibling
test files — out of scope, must stay green via their own existing coverage, not touched by this
ticket).

**Verify:** `pytest tests/tools/test_epic_staleness_check.py::test_discover_candidate_epics_dedupes_dual_presence -v`
passes; full-file run (`pytest tests/tools/test_epic_staleness_check.py -v`) still shows all 11
pre-existing tests green plus this new one.

### Step 3 — Add end-to-end pipeline dedupe regression test
**Files:** `tests/tools/test_epic_staleness_check.py`

**Change:** Append `test_dual_presence_not_double_reported_in_stale_list` after the Step 2 test. Reuse
the same dual-presence fixture pattern as Step 2, plus a `working_log.csv`-equivalent activity row
old enough to cross the staleness window (mirror `test_epic_with_all_children_stale`'s existing
pattern for constructing an old-enough activity timestamp). Assert:
1. `find_stale_epics(...)` returns the shared `epic_id` **exactly once** in its result (not twice).
2. `compute_stale_epics_report(...)`'s "Stale epics:" section contains **exactly one** line for that
   `epic_id` (distinguishable duplicate lines would differ only by `source_path` per
   investigation.md's confirmed downstream-duplication finding — assert there is only one such line,
   not zero and not two).

This closes the gap test_plan.md flags explicitly: a fix that only dedupes
`discover_candidate_epics()`'s own return value could still be defeated by a future refactor of
`_classify_candidates()` that calls discovery twice and concatenates — this test exercises the full
discovery → classification → report path, not just the discovery function in isolation, so it would
catch that regression too.

**Do NOT touch:** `_classify_candidates()`, `find_stale_epics()`, or `compute_stale_epics_report()`
source code — this step is test-only. Do not assert on `resolve_and_relocate_ticket()` or
`epic_scope_orphan_check.py` internals — sibling-ticket surface, out of scope per test_plan.md's own
Anti-Drift Test Guards section.

**Verify:** `pytest tests/tools/test_epic_staleness_check.py::test_dual_presence_not_double_reported_in_stale_list -v` passes.

### Step 4 — Add tie-break lock-in test
**Files:** `tests/tools/test_epic_staleness_check.py`

**Change:** Append `test_dual_presence_prefers_inprogress_candidate` after the Step 3 test, using the
same dual-presence fixture as Step 2. Assert the single surviving candidate from
`discover_candidate_epics(inprogress_dir, todos_dir)` has `.mode == "epic_id"` and `.source_path`
pointing into `inprogress_dir` (not the `todos_dir` subfolder). This locks in the tie-break decision
made explicit in this plan's Summary (epic_id-mode wins because its loop runs first and the dedupe
helper is first-occurrence-wins) so a future refactor cannot silently flip which duplicate survives
without a test failing.

This test was listed as optional in test_plan.md, contingent on the Plan phase committing to a
specific tie-break — this plan does commit to one (see Summary), so the test is included, not
skipped.

**Do NOT touch:** `EpicCandidate`'s field shape or any discovery-loop internals — assertion-only
against the already-implemented Step 1 behavior.

**Verify:** `pytest tests/tools/test_epic_staleness_check.py::test_dual_presence_prefers_inprogress_candidate -v` passes.

## Scope Guards

- Do not touch `resolve_and_relocate_ticket()` (`tools/agent-monitoring/scope_ticket_relocate.py`) or
  `.claude/workflows/implement-ticket.js` — root-cause fix territory, owned by the already-closed
  sibling ticket TCK-20260711-EPIC-SCOPE-ORPHAN-FIX.
- Do not touch or wire in `epic_scope_orphan_check.py` (its `scan_epic_scope_orphans()` /
  `check_single_epic_orphan()` functions) — it is deliberately standalone/unwired per its own
  docstring and the sibling ticket's scope; this plan's dedupe fix does not call into it (see Summary
  rationale), and wiring it into any workflow phase is a distinct, undecided future ticket.
- Do not touch `done_checker_static.py` or add any new orphan-detection static check — explicitly out
  of scope per the ticket's Out of Scope section.
- Do not change classification/reporting semantics: `is_epic_stale()`, `is_epic_never_started()`,
  `resolve_child_activity()`, `_classify_candidates()`, `find_stale_epics()`,
  `compute_stale_epics_report()` — all settled, tested behavior from TCK-20260710-EPIC-STALENESS-CHECK
  (including Decision 5's "no `epic_date` fallback" rule). This ticket's fix lives entirely inside
  `discover_candidate_epics()`.
- Do not change `EpicCandidate`'s field shape or `discover_candidate_epics()`'s parameter signature —
  depended on directly by `epic_scope_orphan_check.py` and `scope_ticket_relocate.py`.
- Do not modify `_dedupe_preserve_order()` — add a new, separate helper for keyed `EpicCandidate`
  dedupe instead.
- Do not modify any of the existing 11 tests in `tests/tools/test_epic_staleness_check.py`, or
  `tests/tools/test_scope_orphan_fix.py`, or `tests/tools/test_epic_scope_orphan_check.py`.
- New tests must use `tmp_path`-scoped fixtures only (never touch the real `tickets/inprogress/` /
  `tickets/todos/` trees) — consistent with `test_advisory_only_no_file_mutation`'s existing
  hash-before/hash-after guard elsewhere in the same file. The dual-presence scenario is synthetic
  fixture-only; there is no live-repo dual-presence case to point a test at today (confirmed zero
  current orphans by the sibling ticket's `scan_epic_scope_orphans()`).
- Do not run `pytest tests/` repo-wide. Scoped command only (see Acceptance Criteria Map below).
- No parity ledger entry is added as part of this plan (see Summary) — flagged for Parity-phase
  confirmation, not silently skipped and not silently added.

## Dependency Map

- Step 1 (source fix) has no dependencies — it can be implemented and manually sanity-checked first.
- Step 2 (discovery-level test) depends on Step 1 being implemented (asserts the dedupe behavior Step
  1 introduces) — write together with or immediately after Step 1 since AC 1 requires this specific
  test.
- Step 3 (pipeline-level test) depends on Step 1 (same underlying dedupe) but is independent of Step
  2's test code (no shared fixture variables required, though it may reuse the same fixture-building
  pattern).
- Step 4 (tie-break test) depends on Step 1's specific tie-break implementation (epic_id-mode loop
  ordered first, first-occurrence-wins helper) — must be written after Step 1 is finalized, not
  before.
- Steps 2, 3, and 4 do not depend on each other and can be added in any order relative to one another,
  provided Step 1 lands first.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC 1: `discover_candidate_epics()`, given a fixture epic present in both `tickets/inprogress/` and `tickets/todos/{folder}/` simultaneously, dedupes and reports the epic exactly once | Step 1 (dedupe helper + wiring), Step 2 (fixture + assertion) | `test_discover_candidate_epics_dedupes_dual_presence` |
| AC 2: Existing `test_epic_staleness_check.py` coverage continues to pass unmodified | Step 1 (no behavior change for non-duplicate fixtures) | Full-file run: `pytest tests/tools/test_epic_staleness_check.py -v` (all 11 pre-existing tests green, unmodified) |
| (Anti-drift, not a literal AC but required by test_plan.md) Downstream double-nudge symptom is actually closed, not just the discovery function in isolation | Step 1, Step 3 | `test_dual_presence_not_double_reported_in_stale_list` |
| (Anti-drift, tie-break made explicit per investigation.md Risk 4) | Step 1 (ordering + first-occurrence-wins helper), Step 4 | `test_dual_presence_prefers_inprogress_candidate` |

## Anti-Drift Notes

- **Line-range drift**: the ticket's Scope section cites "lines 119-163"; the live function is
  119-188. Do not anchor edits to the stale line numbers — re-read the current file before editing,
  since the exact insertion points (e.g. "after line 66", "line 188") given in this plan are based on
  the file as read during planning and may have shifted slightly by implementation time due to
  unrelated changes.
- **Do not conflate this fix with the live-repo one-time sweep.** The sibling ticket already confirmed
  the real repo has zero current dual-presence orphans. All new tests must be synthetic `tmp_path`
  fixtures, never assertions against the real ticket trees.
- **Keying discipline**: the new dedupe helper must key strictly on `EpicCandidate.epic_id` (exact
  string equality) — not on `source_path.name`, folder name, or any looser match. A looser key risks
  merging genuinely distinct epics and would break `test_handles_hybrid_folder_shape` and
  `test_identifies_epic_tickets_vs_regular_tickets`, both of which must remain at
  `len(candidates) == 1` for their own, non-duplicate reasons.
- **No new write path.** The dedupe pass is a pure in-memory list filter over already-constructed
  `EpicCandidate` objects — it must never read, write, or touch any ticket file beyond what the two
  existing discovery loops already do. `test_advisory_only_no_file_mutation`'s real-repo
  byte-hash guard is the regression guard for this; it must stay green unmodified.
- **Parity ledger**: this plan takes the position that no parity ledger entry applies (see Summary),
  consistent with precedent, but this is a Parity-phase confirmation point, not a unilateral final
  decision — if Parity disagrees, add an entry there rather than retroactively editing this plan.

## Deviations

Steps 1-4 were implemented exactly as specified, with no changes to their scope, ordering, or
scope guards. One addition beyond this plan's 4 steps was made during implementation, at the
Implement-phase invocation's explicit direction (not a silent drift): `docs/guides/agent_monitoring.md`'s
"Epic Staleness Check" section was updated with a short paragraph describing the new
dedupe-by-`epic_id` behavior and its tie-break. This plan's Steps section did not originally call
out a doc-update step because neither the ticket's Scope nor this plan's Summary identified an
existing doc describing `discover_candidate_epics()`'s discovery semantics in enough detail to go
stale from this change; that doc was located and confirmed stale only during the Implement-phase
invocation (which named it explicitly, citing the sibling ticket's own Verify-phase gap as
precedent for checking). The addition is doc-only, matches the plan's Summary description of the
fix exactly, and required no change to any of the 4 steps' code or test content above.
