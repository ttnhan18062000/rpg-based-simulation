---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260819-HOTFIX-STATUS-DRIFT-COLON-SUFFIX-GAP
phase: open
date: 2026-08-19
tags: [ai, agent-monitoring]
---

# TCK-20260819-HOTFIX-STATUS-DRIFT-COLON-SUFFIX-GAP

## Title
status_drift_check.py's documented colon-suffixed `## Status: X` gap was never picked up by the follow-up ticket its own docstring promised

## Status
OPEN

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
- [ ] Colon-suffixed `## Status: X` tickets are correctly detected/classified instead of silently
      skipped.
- [ ] Any genuine drift the improved detection surfaces among currently-`tickets/done/` colon-
      suffixed files is fixed, not just newly-reported.
- [ ] The test that currently pins the gap-having behavior is updated to assert correct detection.
- [ ] No regression to `parse_body_section`'s existing newline-separated-format behavior or its
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
(pending)

## Test Summary
(pending)

## Files Changed
(pending)

## Completion Summary
(pending)
