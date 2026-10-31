---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261029-PR-RENDER-KNOWN-GAPS-MISSES-GAPS-STATED-WITHOUT-FAIL
phase: done
date: 2026-10-29
tags: [delivery]
---

# TCK-20261029-PR-RENDER-KNOWN-GAPS-MISSES-GAPS-STATED-WITHOUT-FAIL

## Title
`pr_render.py` writes "Known gaps: none stated" when a ticket does state gaps but not with the word `FAIL`, and gives no way to put them in that line.

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found by platform-planner on PR #786 (fyi, 2026-10-29), verified by agent-working-planner.

`tools/delivery/pr_render.py::extract_known_gaps()` collects a gap only from a line containing the
literal substring `FAIL` in a ticket's `## Test Summary` or `## Completion Summary`. A ticket that
records real gaps any other way gets `- Known gaps: none stated` in the PR body's
`## Verification`. The implementer cannot correct that line by hand, because `--check` compares
the body against the rendered text and fails on any edit (correctly: the body is rendered, not
written).

PR #786 (TCK-20261021-PROMTAIL-TO-ALLOY-LOG-SHIPPING) shows the result. Its Completion Summary says
"All acceptance criteria met and proven live except as stated in the record, section 6". The gaps
(ntfy not re-proven this run, `TargetDown{job="alloy"}` not isolated, the dropped-entries term of
`LogShippingErrors` proven by design only) were stated by hand in `## Review notes`. So the body
says "Known gaps: none stated" in Verification and lists the gaps in Review notes. That contradicts
the reason the slot exists (`docs/guides/delivery_process.md`: "`## Known gaps` is load-bearing and
deliberate ... makes reporting it the default").

## Scope
1. Give tickets one explicit, greppable way to state a gap that is not a `FAIL`: a line in
   `## Test Summary` or `## Completion Summary` that begins `Known gap:` (after an optional list
   marker; case-sensitive prefix). `extract_known_gaps()` collects these lines as well as `FAIL`
   lines, keeping today's per-ticket bullet format and de-duplicating a line that matches both.
2. Make the empty case say what was checked instead of asserting nothing exists: replace
   `- Known gaps: none stated` with
   `- Known gaps: none stated (no FAIL or Known gap: line in any ticket's Test/Completion Summary)`,
   in both the ticket path and the no-tickets path (`pr_render.py` around :420 and :549).
3. Update the tests in `tests/tools/test_delivery_pr_render.py` (AC6 block, ~:186-:214): a
   `Known gap:` line surfaces; a `FAIL` line still surfaces; a line with both appears once;
   prose that merely mentions "gap" does not surface; the new empty-case wording.
4. Docs: `docs/guides/delivery_process.md` (Verification template ~:294 and the `## Known gaps`
   paragraph ~:320) and the module docstring at `pr_render.py:18-24` name the `Known gap:` marker.
   Also add the marker to the closure guidance a closing agent reads: CLAUDE.md is a governing
   file, so do NOT edit it; instead put the sentence in `delivery_process.md` and say in the PR that
   a CLAUDE.md pointer is left for the owner to decide.
5. Check every place that copies the rendered Verification text (`pr_template_spec.json`,
   `.github/workflows/pr-body-lint.yml`, `tests/tools/test_parity_index_baseline.py:268`) still
   agrees with the new wording.

## Out of Scope
- Letting `--check` accept a hand-edited Known-gaps line. That would break the rendered-not-written
  contract `--check` exists to enforce (TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS); rejected.
- Fuzzy detection ("except as stated", "not proven", "gap" anywhere). It is unreliable both ways.
- Reading gaps from stored artifacts (e.g. "the record, section 6"). The ticket stays the one source.
- Back-filling `Known gap:` lines into already-closed tickets, including PR #786's (its owner may add
  one before merge if they choose; that is platform's call).
- A new required ticket section (`## Known Gaps`): it would change the ticket format contract and
  `validate_frontmatter`/section checks for one optional field.

## Acceptance Criteria
1. A ticket whose Completion Summary contains `- Known gap: X` renders `- Known gaps:` with a
   `  - <TICKET>: Known gap: X` bullet (or the stripped equivalent); `--check` passes on that body.
2. `FAIL` lines still render exactly as before (existing AC6 tests unchanged in substance).
3. A line containing both `FAIL` and `Known gap:` appears once.
4. A ticket with neither renders the new empty-case wording; the no-tickets path matches.
5. Prose such as "no gaps remain" or "except as stated in the record" does not surface.
6. `delivery_process.md` and the module docstring describe the marker; `make knowledge-index-update`
   run after the docs edit.
7. `pytest tests/tools/test_delivery_pr_render.py tests/tools/test_parity_index_baseline.py
   tests/tools/test_agent_working_paths_guard*.py` passes in full; any pr-body-lint test passes.

## Related Tickets
- TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS (per-ticket gap bullets; `--check` contract)
- TCK-20261002-PR-RENDER-CLOSES-LISTS-FILED-FOLLOWUPS
- TCK-20261021-PROMTAIL-TO-ALLOY-LOG-SHIPPING (PR #786, where it was found; platform-owned)

## Related Docs
- docs/guides/delivery_process.md ("PR Lifecycle", Verification template, `## Known gaps`)
- docs/plans/agent_infrastructure/github_delivery_process/plan.md (original Verification template; historical, no edit needed)

## Related Stored Artifacts
- none

## Related Code Areas
- tools/delivery/pr_render.py (`extract_known_gaps` ~:355, Verification render ~:412-:432, no-tickets body ~:549)
- tools/delivery/pr_template_spec.json
- tests/tools/test_delivery_pr_render.py
- .github/workflows/pr-body-lint.yml

## Assumptions / Open Questions
- Marker spelling `Known gap:` chosen to match the rendered heading; no other convention exists in
  done tickets (7 done tickets have ad-hoc `gap` bullets, none with a consistent prefix).
- Platform-planner also suggested a CLI flag for gaps. Rejected: a flag is text typed at render
  time, which is the hand-written body this tool exists to replace, and `--check` would need the
  same flag to agree.

## Implementation Notes
`tools/delivery/pr_render.py`: `extract_known_gaps` now also collects a line beginning `Known gap:` (optional list marker, case-sensitive), once per line when it also contains `FAIL`; the empty case reads `- Known gaps: none stated (no FAIL or Known gap: line in any ticket's Test/Completion Summary)` from one constant used by both the ticket path and the no-tickets path. `docs/guides/delivery_process.md` describes the marker; the module docstring too. CLAUDE.md was not touched: a pointer there is left for the owner. `pr_template_spec.json`, `pr-body-lint.yml` and `test_parity_index_baseline.py:268` carry no copy of the wording (the last is an unrelated 'Known gaps' heading).

## Test Summary
`tests/tools/test_delivery_pr_render.py` 71 passed, `test_parity_index_baseline.py` and `test_agent_working_paths_guard*.py` passed in the same run (96 + 71 across two runs).

## Files Changed
tools/delivery/pr_render.py; tests/tools/test_delivery_pr_render.py; docs/guides/delivery_process.md.

## Completion Summary
pr_render collects a line beginning with the Known-gap marker, and the empty case names what was checked.
Known gap: a CLAUDE.md pointer to the marker is left for the owner to decide (governing file).
