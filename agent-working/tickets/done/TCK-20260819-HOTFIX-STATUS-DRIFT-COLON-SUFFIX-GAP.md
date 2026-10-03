---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260819-HOTFIX-STATUS-DRIFT-COLON-SUFFIX-GAP
phase: done
date: 2026-08-19
tags: [ai, agent-monitoring]
---

# TCK-20260819-HOTFIX-STATUS-DRIFT-COLON-SUFFIX-GAP

## Title
status_drift_check.py's documented colon-suffixed `## Status: X` gap was never picked up by the follow-up ticket its own docstring promised

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P3

## Request Summary
`tools/gate_checks/status_drift_check.py` (`make status-drift-check`, live-confirmed wired to a
real Makefile target — not run from `.github/workflows/test.yml`, so it's a manual/on-demand
report, not a CI gate) detects stale `## Status` body text in `tickets/done/*.md`. Its own
docstring documents a "Known, intentional limitation": same-line colon-suffixed tickets
(`## Status: X` with no newline before the value) resolve to `""` via the shared
`parse_body_section` extraction (whose own regex requires a newline directly after the heading)
and are silently skipped — "12 files corpus-wide, 6 non-`DONE` as of 2026-07-18... Candidate for a
future, separately-scoped ticket." That future ticket was never created; a dedicated test,
`test_same_line_colon_status_format_not_newly_flagged`, currently pins the gap-having behavior as
correct rather than testing a fix for it. This is a real, confirmed, still-open gap — small, and
explicitly scoped by the tool's own author, just never followed up.

## Scope
- Re-measure the current corpus-wide count of colon-suffixed `## Status: X` files in
  `tickets/done/*.md` (the 12/6 figures above are 5 weeks stale — confirm live, don't assume).
- Extend `status_drift_check.py` (or `parse_body_section`, whichever the implementer judges is the
  correct layer — see Assumptions) to also extract the value from a same-line
  `## Status: X` format, not just the newline-separated format.
- Update or replace `test_same_line_colon_status_format_not_newly_flagged` to assert the new,
  correct detection behavior instead of pinning the gap.
- Fix any newly-surfaced drift the extended detection finds among the re-measured corpus (matching
  this tool's own established pattern from its prior two rediscovery rounds — see docstring
  history — of finding and fixing real drift once detection improves, not just improving detection
  in the abstract).

## Out of Scope
- Wiring `status-drift-check` into `.github/workflows/test.yml` as an automated CI gate — a
  separate design decision (several sibling `agent-monitoring-*`/`parity-index` Makefile targets
  are deliberately annotated "on-demand only — not CI"; whether `status-drift-check` should join
  the CI-gated set or the on-demand set wasn't determined by this investigation and shouldn't be
  bundled into a hotfix-tier scope change).
- Any change to `parse_body_section`'s behavior for other callers beyond what's needed to also
  support the colon-suffixed shape (check `tools/generate_registry.py` and any other caller before
  changing shared extraction logic, to avoid an unintended behavior change elsewhere).

## Acceptance Criteria
- [x] Colon-suffixed `## Status: X` tickets are correctly detected/classified instead of silently
      skipped.
- [x] Any genuine drift the improved detection surfaces among currently-`tickets/done/` colon-
      suffixed files is fixed, not just newly-reported.
- [x] The test that currently pins the gap-having behavior is updated to assert correct detection.
- [x] No regression to `parse_body_section`'s existing newline-separated-format behavior or its
      other callers.

## Related Tickets
- TCK-20260718-STATUS-DRIFT-REPAIR, TCK-20260718-STATUS-SUFFIX-TRIM (the two prior rounds of
  fixes to this same checker, for context on its history — not blocking this ticket)
- TCK-20260819-HOTFIX-EPIC-STALENESS-FOLDER-BLOCKED-GAP (sibling finding from the same session
  investigation into this tooling tree's checker-consistency gaps, unrelated root cause)

## Related Docs
None beyond the module's own docstring (self-documenting).

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- tools/gate_checks/status_drift_check.py
- tools/generate_registry.py (`parse_body_section` — shared extraction logic, verify other callers
  before changing)
- tests/tools/test_status_drift_check.py

## Assumptions / Open Questions
- Whether the fix belongs in `parse_body_section` itself (fixing the newline-required regex for
  everyone) or in a `status_drift_check.py`-local pre-processing/fallback step (narrower blast
  radius) is left to the implementer, informed by checking every other `parse_body_section` caller
  first.

## Implementation Notes

**Corpus re-measurement (live, 2026-08-19):** `grep -rlE "^## Status\s*:" tickets/done/*.md`
found 12 files, same count as the 5-week-old figure cited in the ticket — not stale after all,
just coincidentally unchanged. Of those 12: `infra-01-automated-testing.md` doesn't start with
`TCK-` so it's already exempt under the checker's existing legacy-naming rule regardless of the
colon-suffix fix. Of the 11 `TCK-`-prefixed ones, 5 already read `## Status: DONE` and 6 read
`## Status: INPROGRESS` — matching the ticket's cited "6 non-DONE" figure exactly.

**Layer decision — local fallback, not a `parse_body_section` change:** Checked every other
caller of `parse_body_section` (`ticket_field_values.py::check_body_field_enum` for `## Tier`/
`## Priority`, `ticket_stats_report.py` for `## Tier`/`## Type`/`## Priority`,
`generate_registry.py::collect_tickets` itself for `## Title`/`## Tier`/`## Type`/`## Priority`/
`## Related Code Areas`, `src/api/agent_ops_dashboard/ingest.py::parse_ticket_file` for the same
five fields, `done_checker_audit.py` for `## Tier`). All of them rely on the newline-separated
"capture until the next `## ` heading" semantics for fields other than Status, and none of them
were in scope to re-verify against a colon-suffix corpus for this hotfix. Changing the shared
regex risked an unquantified behavior change for those callers (e.g. a colon-suffixed `## Tier:
standard` line elsewhere in the corpus suddenly resolving where it used to return `""`, changing
what `check_body_field_enum` validates) — exactly what the ticket's Out of Scope explicitly warned
against bundling into a hotfix. Implemented the fix as a **local fallback in
`status_drift_check.py`** instead: a new `_COLON_SUFFIX_STATUS_RE` regex plus a wrapper function
`_extract_status_value(body)` that calls the real `parse_body_section` first and only falls back
to the colon-suffix regex when that returns `""`. `check_ticket_status_drift` now calls
`_extract_status_value` instead of `parse_body_section` directly. `parse_body_section` itself and
`module.parse_body_section is real_parse_body_section` (the existing anti-drift identity guard)
are both untouched — confirmed by the full `test_generate_registry.py` suite (34 tests) plus
`test_status_drift_check.py`'s own `test_uses_real_dashboard_extraction_function` passing
unchanged.

**Real drift fixed:** all 6 non-DONE colon-suffixed files (`TCK-20260322-BWS_PROTO`,
`TCK-20260401-FINAL-CONVERGENCE`, `TCK-20260401-FINAL-NON-PARTIAL-TASKS`,
`TCK-20260403-FINAL-CONVERGENCE`, `TCK-20260405-SKILL-SCALING`, `TCK-20260407-PH0-FIX`) had
frontmatter already reading `status: historical, phase: done`, matching the exact
pre-Finalize-phase legacy pattern TCK-20260718-STATUS-DRIFT-REPAIR's docstring documents — genuine
drift, not files that are actually still in progress. Edited each file's `## Status: INPROGRESS`
line in place to `## Status: DONE`, preserving all surrounding text/formatting per-file (each had
a different tail shape — trailing prose, `**Tier:**` bold block, `## Priority:` on the very next
line, etc. — verified individually before editing, no blind find/replace).

**Test update:** `test_same_line_colon_status_format_not_newly_flagged` (which asserted PASS for
an `INPROGRESS` colon-suffixed fixture — pinning the gap) renamed to
`test_same_line_colon_status_format_now_flagged` and now asserts `FAIL` with the ticket filename
and `INPROGRESS` value in the evidence string. Added a companion
`test_same_line_colon_status_format_done_passes` to prove the fallback isn't a blanket rejection
of the colon-suffixed shape — a genuinely-DONE colon-suffixed file still passes cleanly.

**Live `make status-drift-check` confirmation:** ran before and after the fix (via `git stash`) —
the FAIL set is byte-identical in both runs: 5 pre-existing, unrelated FAILs
(`TCK-20260806-PUSH-SHADOW-VALIDATION-PERF`, `TCK-20260806-PUSH-SHAPER-REGISTRY-COMBAT`,
`TCK-20260816-KGMCP-BUDGET-TOLERANCE-DEDUP-COVERAGE-CLOSURE` — all multi-line newline-format
`DONE`-plus-trailing-prose bleed, a different, already-known issue class — and 2 genuinely
`BLOCKED` tickets, `TCK-20260817-STANDARD-SIMQ-NARRATIVE-EVENT-EMISSION-REGRESSION-FRONTIER` and
`TCK-20260818-STANDARD-QUEUEDRAINWORKER-CI-THREAD-LEAK-BISECTION`). None of these 5 are
colon-suffixed and none are newly surfaced by this fix — confirmed out of scope per the ticket's
Out of Scope note and left untouched. The 6 colon-suffixed drift files no longer appear in the
FAIL list post-fix (previously silently skipped, now correctly extracted as `DONE`).

## Test Summary
- `.venv/bin/python3 -m pytest tests/tools/test_status_drift_check.py -v --tb=short` — **19
  passed**, 0 failed (17 pre-existing + 2 new: the renamed
  `test_same_line_colon_status_format_now_flagged` and new
  `test_same_line_colon_status_format_done_passes`).
- `.venv/bin/python3 -m pytest tests/tools/test_generate_registry.py tests/tools/test_status_drift_check.py -v --tb=short`
  (regression check for every other `parse_body_section` caller under `tests/`, found via
  `grep -rln "parse_body_section" tests/`) — **70 passed**, 0 failed. No regression.
- `make status-drift-check` — real end-to-end run, exit 1 (expected: 5 pre-existing unrelated
  FAILs remain, none newly introduced by this change — see Implementation Notes for the
  before/after `git stash` diff confirming byte-identical FAIL sets). The 6 colon-suffix drift
  files are no longer silently skipped and no longer appear as FAILs (fixed for real).

## Files Changed
- `tools/gate_checks/status_drift_check.py` — added `_COLON_SUFFIX_STATUS_RE` and
  `_extract_status_value()`; `check_ticket_status_drift` now calls the latter instead of
  `parse_body_section` directly; docstrings updated (module-level "Colon-suffix fix" section,
  `check_ticket_status_drift`'s exemption list).
- `tests/tools/test_status_drift_check.py` — renamed/rewrote
  `test_same_line_colon_status_format_not_newly_flagged` to
  `test_same_line_colon_status_format_now_flagged` (asserts FAIL instead of pinning PASS); added
  `test_same_line_colon_status_format_done_passes`.
- `tickets/done/TCK-20260322-BWS_PROTO.md` — `## Status: INPROGRESS` → `## Status: DONE`.
- `tickets/done/TCK-20260401-FINAL-CONVERGENCE.md` — `## Status: INPROGRESS` → `## Status: DONE`.
- `tickets/done/TCK-20260401-FINAL-NON-PARTIAL-TASKS.md` — `## Status: INPROGRESS` →
  `## Status: DONE`.
- `tickets/done/TCK-20260403-FINAL-CONVERGENCE.md` — `## Status: INPROGRESS` → `## Status: DONE`.
- `tickets/done/TCK-20260405-SKILL-SCALING.md` — `## Status: INPROGRESS` → `## Status: DONE`.
- `tickets/done/TCK-20260407-PH0-FIX.md` — `## Status: INPROGRESS` → `## Status: DONE`.
- `tickets/inprogress/TCK-20260819-HOTFIX-STATUS-DRIFT-COLON-SUFFIX-GAP.md` — this ticket file
  (Status, Acceptance Criteria, Implementation Notes, Test Summary, Files Changed, Completion
  Summary).
- `agent-monitoring/tools.jsonl` — auto-updated by the monitoring tooling on each tool run in this
  session (per project convention, always staged alongside the rest).

## Completion Summary
Extended `status_drift_check.py`'s Status-value extraction to also detect the previously-silently-
skipped same-line colon-suffixed `## Status: X` shape, via a narrow local fallback
(`_extract_status_value`) rather than a change to the shared `parse_body_section` — keeping the
fix's blast radius contained to this one checker and leaving every other `parse_body_section`
caller (confirmed via grep and a full regression run) untouched. Re-measured the live corpus
(still 12 colon-suffixed files / 6 non-DONE, matching the ticket's cited figures) and fixed all 6
genuine drift cases — legacy tickets whose frontmatter already read `phase: done` but whose body
`## Status` line was never updated from `INPROGRESS` to `DONE`. The test that had pinned the gap
as correct behavior now asserts the fix instead. CI wiring remains explicitly out of scope, as
specified.
