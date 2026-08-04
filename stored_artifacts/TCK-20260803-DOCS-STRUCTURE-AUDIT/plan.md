---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260803-DOCS-STRUCTURE-AUDIT
artifact_type: plan
tags: [documentation, registry]
---

# Implementation Plan — TCK-20260803-DOCS-STRUCTURE-AUDIT

## Summary

The investigation found the `docs/` tree structurally healthy: all 26 top-level subfolders
are real and populated, `_SKIP_DOC_SUBDIRS`'s four entries (`archive`, `parity_ledger`,
`scenarios`, `entity`) are all correct (two are load-bearing exclusions, two are currently
inert no-ops given `collect_docs()`'s `*.md`-only glob but are retained because they hold
actively-referenced non-`.md` content), and no folder qualifies for deletion. There is
therefore no functional code change to make to `_SKIP_DOC_SUBDIRS` or `collect_docs()`. This
plan's job is to turn that negative-but-conclusive finding into a durable, checkable
artifact rather than a silent no-op: (1) record the audit's conclusion directly next to the
constant it audited, in code, backed by a new regression test that would fail if the
`scenarios`/`entity` rationale ever goes undocumented or an entry's inert status silently
changes; (2) record the one legitimate adjacent finding (dead `"superpowers"`/`"specs"`
branches in `validate_frontmatter.py`) as a follow-up recommendation without touching that
file; (3) run the existing scoped test suite to confirm nothing regressed; and (4) close the
ticket itself with its Acceptance Criteria explicitly checked against a "confirmed healthy,
no change needed" outcome, which the ticket's own AC #3 requires be stated rather than left
implicit.

**Design decision — where to record the audit conclusion:** an in-code comment block
immediately above `_SKIP_DOC_SUBDIRS` in `tools/generate_registry.py` (not a note in
`docs/ai/README.md`). Rationale:
1. Proximity: the next person to edit `_SKIP_DOC_SUBDIRS` (e.g. adding a fifth entry) will
   read the comment immediately above it, not a prose paragraph in a different file three
   directories away.
2. The investigation and test_plan already scaffold this exact placement — test_plan.md's
   recommended guard test explicitly checks "`tools/generate_registry.py`'s module docstring
   or an inline comment adjacent to `_SKIP_DOC_SUBDIRS`," not any `docs/` file.
3. `docs/ai/README.md`'s Doc Registry Integration section documents the registry *convention*
   in general; it is not the right place for one-ticket audit trivia about two specific inert
   entries, and editing it would be a `docs/` prose content change — the investigation's own
   "Docs Requiring Update" section concluded `None`, and AC #7 requires no document's prose
   body content be modified by this ticket. Keeping the record in code avoids that entirely.
4. A code comment is versioned and travels with `_SKIP_DOC_SUBDIRS` through any future
   refactor of the constant; a separate doc note would silently drift out of sync with the
   code it describes.

**Design decision — "file a follow-up ticket recommendation":** record the
`validate_frontmatter.py` dead-code finding as a named, scoped recommendation inside this
ticket's own `## Implementation Notes` / `## Completion Summary` (suggested ticket ID shape,
one-line scope, precedent citation) rather than creating a new `tickets/inprogress/*.md` file
in this pass. Actually scoping a new ticket is a distinct workflow action (the `ticket-scoper`
agent / Scope phase, with its own investigation and staging artifacts) that this audit ticket
does not own and whose Out of Scope section does not authorize ("Designing or building the
doc-updater agent itself... a separate follow-up ticket"). Writing a precise, actionable
recommendation in this ticket's Completion Summary gives a future session everything needed
to scope it (file, function, line range, precedent ticket) without this ticket overstepping
into creating and owning that new ticket's lifecycle.

## Steps

### Step 1 — Document the audit conclusion next to `_SKIP_DOC_SUBDIRS`, with a regression guard test

**Files:** `tools/generate_registry.py`, `tests/tools/test_generate_registry.py`

**Change:**
- In `tools/generate_registry.py`, replace the single-line comment currently at line 41
  (`# Subdirectories under docs/ to skip entirely (not indexed in the registry).`) with an
  expanded comment block directly above `_SKIP_DOC_SUBDIRS` (line 42) that states, per entry:
  - `archive`, `parity_ledger` — real exclusions: contain `.md` files that would otherwise be
    indexed; skip-list membership is load-bearing.
  - `scenarios`, `entity` — currently inert no-ops: contain zero `.md` files as of the audit
    date (they hold `.yaml`/`.mmd` content instead), so `collect_docs()`'s `*.md`-only
    `rglob` already excludes them regardless of this set's membership. Retained anyway for
    forward-compatibility documentation and because their content is actively referenced
    elsewhere (`docs/scenarios/phase1/*.yaml` by
    `tests/unit/strategic/test_scenario_runner.py`; `docs/entity/*.mmd` by
    `docs/strategy/world_capability_design.md` and `docs/guides/diagram_index.md`) — do not
    remove without re-verifying those references first.
  - A one-line note that this was audited and confirmed accurate by
    `TCK-20260803-DOCS-STRUCTURE-AUDIT` (date 2026-08-03), following the same
    audit-confirmation pattern `TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES` established for this
    same constant.
- In `tests/tools/test_generate_registry.py`, add a new test method
  `test_skip_doc_subdirs_inert_entries_documented` to the existing `TestRealDocsTree` class
  (line 526), placed immediately after `test_skip_doc_subdirs_exist_on_disk` (line 539-550).
  It should: read the source of `tools/generate_registry.py` (or import its module and inspect
  `__doc__`/the comment via `inspect.getsource`), and assert that the substrings `"scenarios"`
  and `"entity"` both appear in the comment block adjacent to `_SKIP_DOC_SUBDIRS` — matching
  the exact assertion shape test_plan.md specifies. Keep the assertion structural (substring
  presence), not a byte-for-byte string match, so future comment wording edits don't
  spuriously break it.

**Do NOT touch:** `collect_docs()` (lines 186-238) itself — no glob-pattern or skip-logic
change, only the comment text changes. Do not modify `_SKIP_DOC_SUBDIRS`'s actual set
membership — all four entries stay exactly as they are. Do not touch
`test_doc_entry_skips_archive_subdir` or `test_doc_entry_skips_parity_ledger_subdir`.

**Verify:** New test `test_skip_doc_subdirs_inert_entries_documented` passes; existing
`test_skip_doc_subdirs_exist_on_disk` still passes unchanged.

### Step 2 — Record the `validate_frontmatter.py` follow-up as a recommendation (no code change)

**Files:** `tickets/inprogress/TCK-20260803-DOCS-STRUCTURE-AUDIT.md` (`## Implementation
Notes` section only)

**Change:** Add a note under Implementation Notes recommending a future hotfix-tier ticket:
approximate scope "remove the dead `\"superpowers\"`/`\"specs\"` branches from
`detect_content_type()` in `tools/validate_frontmatter.py` (around line 123-127), since
`docs/specs/` and `docs/superpowers/` no longer exist as top-level `docs/` subfolders
(consolidated into `docs/archive/specs/` by `TCK-20260616-DOCS-ARCHIVE-SPECS-PERF-PLANS`) and
files under `docs/archive/specs/` already classify correctly via the `\"archive\"` branch."
Cite `TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES` as the direct precedent (same dead-path-segment
pattern, same fix shape, in the sibling tool `generate_registry.py`). This is a note only —
no ticket file is created, no `validate_frontmatter.py` line is edited.

**Do NOT touch:** `tools/validate_frontmatter.py` itself, in any way. Do not create a new
`tickets/inprogress/*.md` or `tickets/todos/*.md` file for this recommendation.

**Verify:** No test — this is a documentation-only note inside the ticket body. Manually
confirm the note names the file, function, approximate line range, and precedent ticket ID
(so a future session can act on it without re-deriving this investigation).

### Step 3 — Run the scoped regression suite

**Files:** None changed; verification only.

**Change:** Run `.venv/bin/python3 -m pytest tests/tools/test_generate_registry.py -q` and
confirm all tests pass, including the new `test_skip_doc_subdirs_inert_entries_documented`
from Step 1 and the pre-existing `test_registry_exits_zero_on_real_docs_tree` /
`test_check_flag_detects_no_drift_against_real_registry` (which run against the real `docs/`
tree and would catch any accidental structural drift from Steps 1-2).

**Do NOT touch:** Do not run the full suite (`pytest tests/`) — out of scope per project
testing rules and per this ticket's Scoped Pytest Commands. Do not run
`tests/unit/strategic/test_scenario_runner.py` — `docs/scenarios/` is being kept unchanged,
so it is not implicated; running it is unnecessary but not harmful if done as a sanity check.

**Verify:** `.venv/bin/python3 -m pytest tests/tools/test_generate_registry.py -q` exits 0
with all tests passing.

### Step 4 — Close out the ticket: check Acceptance Criteria against the "confirmed healthy" outcome

**Files:** `tickets/inprogress/TCK-20260803-DOCS-STRUCTURE-AUDIT.md`

**Change:** Update the ticket body (not frontmatter structure) to reflect the deliberate
closing state:
- Check off all 7 `## Acceptance Criteria` boxes, since each is satisfied either by
  `investigation.md` (AC #1, #2), by Step 1's code comment (AC #4), by the explicit "no
  folder qualifies" statement being recorded here (AC #3), by AC #5 being not-applicable
  (`_SKIP_DOC_SUBDIRS` membership did not change — only its adjacent comment did) stated
  explicitly rather than silently skipped, by Step 3's passing test run (AC #6), and by no
  `docs/*.md` file having been touched anywhere in this plan (AC #7).
- Fill `## Implementation Notes` with: the audit's bottom line (structure healthy, no
  deletions, no `_SKIP_DOC_SUBDIRS` set change), the Step 2 follow-up recommendation, and a
  pointer to `investigation.md`'s per-folder table for full detail.
- Fill `## Test Summary` with the Step 3 pytest command and result.
- Fill `## Files Changed` with `tools/generate_registry.py` (comment only) and
  `tests/tools/test_generate_registry.py` (new test).
- Fill `## Completion Summary` stating explicitly: "No structural changes to `docs/` or to
  `_SKIP_DOC_SUBDIRS`'s membership were made — the audit confirmed the existing structure and
  skip-list are accurate. This is the deliberate, correct outcome of a clean audit, not a
  failure to find something." Flip `## Status` to `DONE`.

**Do NOT touch:** The ticket's frontmatter block (`status`, `layer`, `authority`, `tags`,
etc.) beyond what the standard ticket-close workflow (Finalize phase) already governs — this
step only fills in the body's narrative sections and checkboxes. Do not alter `## Scope`,
`## Out of Scope`, `## Acceptance Criteria`'s wording, or `## Related *` sections — only their
checkbox state (for AC) may change from unchecked to checked.

**Verify:** All 7 AC checkboxes are checked; `## Status` reads `DONE`; `## Completion
Summary` is non-empty and states the "confirmed healthy, no change needed" conclusion
explicitly (satisfies AC #3's "must state explicitly" requirement).

## Scope Guards

- Do not modify `docs/archive/`'s or `docs/parity_ledger/`'s exclusion status or any content
  inside those two folders — both are explicitly Out of Scope and confirmed correct.
- Do not delete `docs/scenarios/` or `docs/entity/`, and do not remove their entries from
  `_SKIP_DOC_SUBDIRS` — both are confirmed actively referenced (a live test dependency and
  live doc cross-references respectively); doing so would break
  `tests/unit/strategic/test_scenario_runner.py` and orphan two doc cross-references.
- Do not edit `tools/validate_frontmatter.py` — the dead `"superpowers"`/`"specs"` check
  found there is Step 2's recommendation target, not this ticket's implementation target.
- Do not widen `collect_docs()`'s `*.md`-only `rglob` (lines 186-238) to index `.yaml`,
  `.mmd`, `.json`, or any other file type — explicitly a separate, larger, out-of-scope
  decision per the ticket.
- Do not modify the prose body content of any individual `docs/*.md` file — this ticket is
  structure/naming/existence only, per its own Scope and Out of Scope sections and AC #7.
- Do not rename or restructure any `docs/` subfolder — no folder in this audit qualified as
  genuinely dead, so there is nothing to safely remove or rename.
- Do not run the full test suite (`pytest tests/`) — stay scoped to
  `tests/tools/test_generate_registry.py` per the test plan.
- Do not create a new ticket file for the Step 2 recommendation — record it as a note only.

## Dependency Map

- Step 1 is independent — can start immediately.
- Step 2 is independent of Step 1 — can run in parallel or any order.
- Step 3 depends on Step 1 (the new test added in Step 1 must exist before it can be run and
  counted in the pass/fail result).
- Step 4 depends on Steps 1, 2, and 3 all being complete — it summarizes their outcomes into
  the ticket body and cannot be written accurately before they finish.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — investigation records file count + dead/orphaned status for all 26 folders | Pre-satisfied by `investigation.md` (Investigate phase, no plan step needed) | N/A — artifact review |
| AC #2 — `scenarios`/`entity` findings state contents, references, keep/remove rationale | Pre-satisfied by `investigation.md` (Investigate phase, no plan step needed) | N/A — artifact review |
| AC #3 — dead folder removed via `git rm`, or ticket states explicitly none qualify | Step 4 (Completion Summary states explicitly no folder qualified) | Manual review of ticket body |
| AC #4 — `_SKIP_DOC_SUBDIRS` reflects audit conclusions; unchanged is acceptable if stated explicitly | Step 1 (in-code comment) + Step 4 (ticket body restates it) | `test_skip_doc_subdirs_inert_entries_documented`, `test_skip_doc_subdirs_exist_on_disk` |
| AC #5 — if `_SKIP_DOC_SUBDIRS` changes, update its regression test | N/A — set membership did not change, only its comment did; Step 1 adds a *new* test as a bonus guard, not a required update to an existing one | `test_skip_doc_subdirs_exist_on_disk` (unchanged, still passing) |
| AC #6 — `pytest tests/tools/test_generate_registry.py -q` passes after any change | Step 3 | Full file run, all green |
| AC #7 — no document's prose body content modified | Scope Guards (all steps) | Manual diff review: no `docs/*.md` file appears in the changeset |

## Anti-Drift Notes

- The two "inert" `_SKIP_DOC_SUBDIRS` entries (`scenarios`, `entity`) are inert *only* because
  `collect_docs()` globs `*.md` exclusively — if a future ticket widens that glob (explicitly
  out of scope here), these entries would become load-bearing again. The Step 1 comment must
  say this so a future reader doesn't mistake "inert today" for "safe to delete."
- The "146 files" figure for `docs/archive/` in the ticket's own scoping text is stale (actual
  is 452 total / 439 `.md`, per investigation). Do not use "146" anywhere in Step 4's ticket
  update; do not add a new hard-coded file-count assertion for `docs/archive/` in any test —
  the test_plan explicitly flags this as a future maintenance hazard since the count keeps
  growing.
- `TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES`'s removal of `superpowers`/`specs` does not transfer
  as precedent for removing `scenarios`/`entity` — that removal applied because those
  directories didn't exist on disk at all. `scenarios` and `entity` exist and hold live,
  referenced content; this is a materially different case and Step 1's comment must not blur
  that distinction.
- Step 2's recommendation is deliberately *not* self-executing — do not let Step 2 drift into
  actually editing `tools/validate_frontmatter.py`, even though the fix is small and the
  precedent (`TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES`) is a template for exactly this kind of
  fix. That file and function are outside this ticket's `Related Code Areas`.
