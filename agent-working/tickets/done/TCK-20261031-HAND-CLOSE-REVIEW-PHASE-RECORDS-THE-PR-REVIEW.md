---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-HAND-CLOSE-REVIEW-PHASE-RECORDS-THE-PR-REVIEW
phase: done
date: 2026-10-31
tags: [agent-monitoring, governance]
---

# TCK-20261031-HAND-CLOSE-REVIEW-PHASE-RECORDS-THE-PR-REVIEW

## Title
A standard-tier hand close's Review phase is the planner's PR review: record it, rather than `skipped`/`no_hand_tool` in every run

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
This is proposal 1 of the W44 retro (PR #804). The owner said "Yes, triage them" (#715 issuecomment-6545824938 item 2), and
agent-working-planner-u24 triaged it to this ticket. The W44 lead note (#715 6492223703) raised the same open question.

In W44, all 37 standard-tier hand closes recorded Review and Architecture-Verify as `skipped`/`no_hand_tool`.
`tools/agent-monitoring/record_hand_orchestrated_closure.py` (l.~255-268) writes that by default. Yet every one of those
tickets reached main through a PR that its domain planner reviewed by comment, and the delivery process requires that
review (one PR per batch, planner reviews, owner merges). So the retro reports a review gap that doesn't exist, and it
can't tell the one that does: a standard close whose PR had no review comment.

## Scope
Pending the owner's choice in Open Questions:
- (a, proposed) `record_hand_orchestrated_closure.py` accepts the review evidence, e.g. `--review-ref <PR#>#<comment id>`,
  and records Review as `ok` with that ref. Architecture-Verify stays `skipped` unless a reviewer recorded an architecture
  verdict. A standard-tier close without the ref keeps today's `skipped`/`no_hand_tool`, so the retro still shows it.
- (b) Doc-only: state in `docs/guides/delivery_process.md` and `docs/agent-monitoring/README.md` that a hand close's Review
  is the PR review. Have the retro's Phase Status table label `no_hand_tool` Review skips as "reviewed on the PR (not
  recorded)".
- In either case, update the retro proposal text so the routing-candidate note no longer fires on the documented
  case. Add tests in `tests/tools/`.

## Out of Scope
- Making any review blocking, or changing a tier or the pipeline (`implement-ticket.js`).
- Backfilling W44 or earlier rows.
- CLAUDE.md (the closure example there is the owner's). Name any wording it would need in the PR body.

## Acceptance Criteria
1. Under (a): a closure called with the review ref writes Review `ok` with the ref, and one called without it writes
   exactly today's event. Tests cover both. Under (b): the docs state the rule, and the retro labels the skips as stated.
2. `pytest tests/tools -k "hand_orchestrated or retro or closure" -p no:randomly` passes.
3. The PR body shows a W44-shaped sample of the Phase Status table before and after.

## Related Tickets
- TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE
- TCK-20261006-HAND-CLOSURE-RETRO-PROVENANCE

## Related Docs
- docs/guides/delivery_process.md (PR Lifecycle)
- docs/agent-monitoring/README.md ("Recording coverage for a hand-orchestrated closure")

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261031-HAND-CLOSE-REVIEW-PHASE-RECORDS-THE-PR-REVIEW/ (plan, investigation, test_plan)

## Related Code Areas
- tools/agent-monitoring/record_hand_orchestrated_closure.py
- tools/agent-monitoring/generate_retro.py, tools/agent-monitoring/path_report.py (routing-candidate text)

## Assumptions / Open Questions
- **Decided: (a)** (owner, #715 issuecomment-6545962757: "(a) + dispatch"). `--review-ref <PR#>#<comment id>` records
  Review `ok` with the ref. A close with no ref stays `skipped`/`no_hand_tool`, so a review that really is missing still
  shows. Option (b) is out of scope.
- Dispatched to agent-working-implementer-u24 under that same go.

## Implementation Notes
- Dispatched by agent-working-planner-u24 (owner go and option (a): #715 6545962757). Based on origin/main b0cb9402b (#804 not merged yet).
- `record_hand_orchestrated_closure.py`: new `--review-ref <PR#>#<comment id>` and `review_ref_event()`. With a ref, Review is recorded `ok` with a summary naming the PR and the comment; the event is inserted before `folded_phase_events`, which then leaves Review alone. Without a ref the events are exactly today's (a test compares them). Architecture-Verify is unchanged. The flag is refused, with nothing written, when the ref is malformed, when the tier plan has no `full` Review (hotfix), or when the closer narrated a Review event.
- `path_report.py`: no counting change was needed, since a phase with any non-skipped event already counts as `ran`, so a ref'd Review leaves the skipped count and stops being a routing candidate by itself. The Paths footer now says so.
- Docs: the tool's docstring and the README paragraph on folded phases. CLAUDE.md is out of scope; its closure example needs no change to keep working. If the owner wants the flag shown there, the wording would be: add `[--review-ref <PR#>#<comment id>]` to the example command's flag list and one sentence "give it only once the planner's PR review comment exists".
- Own closes: no `--review-ref`, because no PR review exists yet.

## Test Summary
- `pytest tests/tools -k "hand_orchestrated or retro or closure or path_report" -p no:randomly` (serial): 416 passed. New tests: 17 in `test_closure_recorder_folded_phases.py` (ref event shape and plan order, Architecture-Verify unchanged, no ref == today's events, validation, 12 malformed refs, hotfix / narrated Review / bad ref refused through `main`), 1 in `test_path_report.py`.

## Files Changed
- tools/agent-monitoring/record_hand_orchestrated_closure.py, tools/agent-monitoring/path_report.py
- docs/agent-monitoring/README.md
- tests/tools/test_closure_recorder_folded_phases.py, tests/tools/test_path_report.py
- agent-working/stored_artifacts/TCK-20261031-HAND-CLOSE-REVIEW-PHASE-RECORDS-THE-PR-REVIEW/ (plan, investigation, test_plan)

## Completion Summary
AC1 met under (a): a ref writes Review `ok` with the link and no ref writes exactly today's event; both are tested. AC2: the scoped pytest passes. AC3: the PR body shows the W44-shaped Phase Status sample before and after.
