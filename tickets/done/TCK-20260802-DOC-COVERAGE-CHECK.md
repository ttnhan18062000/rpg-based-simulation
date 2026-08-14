---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260802-DOC-COVERAGE-CHECK
phase: done
date: 2026-08-02
tags: [workflows, documentation, investigator]
---

# TCK-20260802-DOC-COVERAGE-CHECK

## Title
Add a deterministic docs_to_update coverage check to done-checker's static pre-check

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Follow-up to `TCK-20260802-DOC-UPDATE-DISCIPLINE`. That ticket added a `docs_to_update` obligation
to the Investigate phase and an advisory (non-blocking) cross-check during Implement. Discussion
with the user surfaced a real residual gap: if the implementer wrongly self-reports
`behavior_changed=false` for a change that actually introduced new logic/features/settings, NEITHER
of those two mechanisms ever fires (both are gated on `behavior_changed=true`) — documentation
staleness can slip through completely silently.

`done-checker`'s own DoD condition 6 ("Docs updated") is currently **pure LLM judgment with zero
static backing** — unlike conditions 3/4/7/10/12 (and, as of the prior ticket, `ticket_field_values_valid`),
which all already cite a deterministic `tools/gate_checks/done_checker_static.py` script instead of
relying on judgment alone. This ticket adds that backing: a new static check,
`check_docs_to_update_coverage`, that independently re-compares Investigate's `docs_to_update` list
against the *actual* final diff (via `git status --porcelain`) — **regardless of what
`behavior_changed` was self-reported as**, since Investigate's obligation is derived from ticket
scope/acceptance criteria, not from the implementer's later self-report. This closes the silent-skip
case the Implement-phase advisory cannot reach.

Design decision confirmed with the user: since `docs_to_update` only exists as a JS-runtime variable
today, this check must read it back from `investigation.md`'s "## Docs Requiring Update" prose
section (not a new durable sidecar file) — which means that section's format must be tightened to a
strict, machine-parseable form: one bullet per path, path backtick-wrapped, e.g.
`` - `docs/mechanics/03_economic_laws.md`: reason ``.

Unlike the Implement-phase advisory (deliberately non-blocking), this new check is a **real,
blocking** static check — by Verify time, Architecture-Verify/Test/Parity have already run and the
implementation is stable, so a genuine mismatch here is a high-confidence signal of an incomplete
ticket, not premature judgment on a still-evolving plan.

## Scope
- `.claude/agents/investigator.md`: tighten the "## Docs Requiring Update" section format to one
  backtick-wrapped `docs/` path per bullet (`- \`docs/path.md\`: reason`), with "None." as the
  explicit empty sentinel.
- `.claude/workflows/implement-ticket.js`: mirror the same format instruction in the Investigate
  phase prompt's section-list description (kept consistent with investigator.md, not duplicated
  divergently).
- `tools/gate_checks/done_checker_static.py`:
  - `_git_touched_paths()`: read-only `git status --porcelain` wrapper, fail-open (empty set) on
    any subprocess error.
  - `_parse_docs_to_update(section_text)`: regex-extract backtick-wrapped `docs/` paths from the
    tightened bullet format; treats empty/"None"/"None."/"N/A" as zero required docs.
  - `check_docs_to_update_coverage(ticket_id, tier)`: NA for hotfix (no investigation.md exists);
    PASS if no docs were flagged; FAIL if the section is non-empty but unparseable (format
    regression); FAIL if any flagged path isn't in `_git_touched_paths()`'s result; PASS otherwise.
  - Wire into `run_static_precheck` as a 7th aggregated check (`docs_to_update_coverage`).
- `.claude/workflows/implement-ticket.js`'s Verify-phase prompt: add condition 6 to the "cite JSON
  output verbatim" instruction list (currently "conditions 3, 4, 7, 10, 12").
- `docs/ai/ticket-lifecycle.md`: update the Investigate section (format requirement) and the Verify
  section (Step 0b's check count and condition 6's evidence source).
- Tests: `tests/tools/test_done_checker_static.py` (new function coverage + updated aggregate-count
  assertions), plus a small static-source test for the JS prompt wiring if warranted.

## Out of Scope
- A durable JSON sidecar for `docs_to_update` — user explicitly chose the investigation.md-parsing
  approach over this.
- Making the Implement-phase advisory check (from the prior ticket) blocking — it stays advisory;
  this ticket adds a *separate*, later, blocking checkpoint instead of changing that one.
- Any change to `doc_staleness_check.py` (the Implement-phase gate) — untouched by this ticket.
- A validator that cross-references `agent-orchestration/terminal-statuses.yaml`'s `phases` fields
  against real code (unrelated, already handled by `TCK-20260802-TERMSTATUS-DRIFT-FIX`).

## Acceptance Criteria
- [x] `investigator.md`'s "Docs Requiring Update" section instructions require one backtick-wrapped
      `docs/` path per bullet line, with "None." as the explicit empty case.
- [x] `implement-ticket.js`'s Investigate prompt mirrors the same format requirement.
- [x] `check_docs_to_update_coverage`: NA for hotfix; PASS when no docs flagged; FAIL when the
      section is non-empty but no path parses; FAIL when a flagged path isn't in the diff; PASS
      when all flagged paths are touched.
- [x] The check is independent of `behavior_changed` — it reads only from `investigation.md` and
      real git state, never from any Implement-phase self-report.
- [x] `run_static_precheck` aggregates 7 checks (was 6); existing 6 checks' behavior unchanged.
- [x] Verify-phase prompt cites condition 6 as script-backed alongside 3/4/7/10/12.
- [x] `docs/ai/ticket-lifecycle.md` reflects the new check count and condition 6's real backing.
- [x] All 65 existing `test_done_checker_static.py` tests still pass unmodified except the two
      aggregate-count assertions (6→7), which are updated deliberately.

## Related Tickets
- TCK-20260802-DOC-UPDATE-DISCIPLINE (introduced `docs_to_update`, the Implement-phase advisory)
- TCK-20260705-GATE-DET-DONE-CHECKER (introduced `done_checker_static.py` itself)
- TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM (added the 6th check, `ticket_field_values_valid`,
  establishing the "extra check beyond the numbered 5" precedent this ticket follows)

## Related Docs
- docs/ai/ticket-lifecycle.md

## Related Stored Artifacts
None yet — this ticket's own staging_artifacts/.

## Related Code Areas
- tools/gate_checks/done_checker_static.py
- .claude/agents/investigator.md
- .claude/workflows/implement-ticket.js
- tests/tools/test_done_checker_static.py

## Assumptions / Open Questions
- Assuming `git status --porcelain` (full working tree, not scoped to `docs/`) is the right ground
  truth for "was this doc touched" at Verify time — same working-tree-based approach the Parity
  phase already uses for its own docs/parity_ledger/ cross-reference, and the same accepted
  concurrent-session residual risk already documented for `clean_data_runs_early`.
- No unresolved questions blocking implementation.

## Implementation Notes
- `tools/gate_checks/done_checker_static.py`: added `_git_touched_paths()` (read-only `git status
  --porcelain` wrapper, fail-open to `set()` on any subprocess error), `_path_touched()` (handles
  git's own collapsing of a wholly-new untracked directory to just the directory path — a required
  file under such a directory wouldn't exact-string-match otherwise), `_parse_docs_to_update()`
  (regex-extracts backtick-wrapped `docs/` paths from investigation.md's bullet list; "None"/"None."/
  "N/A"/empty all parse to `[]`), and `check_docs_to_update_coverage()` (NA/hotfix, FAIL/missing
  file, PASS/no-docs-flagged, FAIL/unparseable-non-none-section, FAIL/missing-path,
  PASS/all-touched). Wired as the 7th entry in `run_static_precheck`.
- Discovered mid-implementation: `git status --porcelain` collapses a brand-new untracked directory
  to just `docs/` rather than listing files inside it individually — real git behavior, not a bug.
  Handled via `_path_touched()`'s directory-prefix matching rather than requiring exact-string
  membership.
- `.claude/agents/investigator.md` and `.claude/workflows/implement-ticket.js`'s Investigate prompt:
  both now specify the identical tightened bullet format (backtick-wrapped path immediately after
  `- `), kept as close to word-for-word identical as the two files' surrounding prose allows, so they
  can't drift apart on what the required format is.
- `.claude/workflows/implement-ticket.js`'s Verify prompt: added `6` to the "cite JSON output
  verbatim" condition list.
- Collateral line-number drift (same class the prior `TCK-20260802-TERMSTATUS-DRIFT-FIX` hotfix
  just closed): the Investigate/Verify prompt edits added lines earlier in `implement-ticket.js`,
  shifting `FINALIZE_INCOMPLETE`'s two call sites from `:1377`/`:1389` to `:1380`/`:1392` again.
  Updated both Python conformance-test assertions and `terminal-statuses.yaml`'s header comment
  once more (its own disclaimer note — added by the prior hotfix — already flags that this drifts;
  fixed anyway since it was trivial while already here). `review.verdict`/`archVerify.verdict`/the
  `SCOPE_AGENT_FAILED` bypass citations were unaffected — my edits landed after those call sites in
  the file, so their line numbers didn't move.
- `docs/ai/ticket-lifecycle.md`: Investigate section notes the tightened format requirement and its
  reason (machine-parsed by the new check); Verify section's Step 0b updated to 7 checks and
  condition 6's table row now cites the real script backing.

## Test Summary
`pytest tests/tools/test_done_checker_static.py tests/tools/test_doc_staleness_check.py
tests/tools/test_doc_staleness_gate_wiring.py tests/tools/test_finalize_knowledge_index_refresh.py
tests/tools/test_current_run_sidecar_orchestrator.py tests/agent_orchestration_claude_adapter/
tests/agent_orchestration/ -q` — 408 passed, 0 failed (85 in `test_done_checker_static.py` — 65
pre-existing + 20 new/updated for `docs_to_update_coverage`/`_git_touched_paths`/`_path_touched`/
`_parse_docs_to_update`/the Verify-prompt condition-6 citation). Also ran the broader
`tests/tools/ tests/agent_orchestration/ tests/agent_orchestration_claude_adapter/` sweep — see
Files Changed for the two conformance-test line-number updates this ticket's own edits required.

## Files Changed
- tools/gate_checks/done_checker_static.py
- tests/tools/test_done_checker_static.py
- .claude/agents/investigator.md
- .claude/workflows/implement-ticket.js
- docs/ai/ticket-lifecycle.md
- agent-orchestration/terminal-statuses.yaml (collateral line-citation fix)
- tests/agent_orchestration_claude_adapter/test_terminal_status_extractor.py (collateral)
- tests/agent_orchestration_claude_adapter/test_terminal_status_conformance.py (collateral)

## Completion Summary
Added `check_docs_to_update_coverage` as a 7th static check in `done-checker`'s `run_static_precheck`,
giving DoD condition 6 ("Docs updated") real deterministic backing for the first time. Unlike the
Implement-phase advisory from the predecessor ticket (deliberately non-blocking, gated on
`behavior_changed`), this new check is a real blocking condition that reads only `investigation.md`
and actual git state — closing the specific silent-skip case where an implementer wrongly reports
`behavior_changed=false` and both the doc-staleness gate and its advisory never fire at all. Required
tightening the "Docs Requiring Update" section to a strict, machine-parseable bullet format in both
`investigator.md` and `implement-ticket.js`'s Investigate prompt.
