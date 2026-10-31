---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261031-SDLC-PLAN-REVIEW-FIXES-AND-EVIDENCE
phase: open
date: 2026-10-31
tags: [planning, documentation]
---

# TCK-20261031-SDLC-PLAN-REVIEW-FIXES-AND-EVIDENCE

## Title
Apply lead-planner's review fixes to the AI-first SDLC plan and add an evidence section to its summary

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
The designer asked for its before/after draft to land in the next agent-working PR, with no plan-only PR. Lead-planner agreed the scope. The text is at main-checkout `.claude/handover/drafts/sdlc_plan_review_fixes.md`, which is gitignored, so the plan's own diff is the durable record. Nothing here is an owner decision and no decision changes.

## Scope
Docs only, in `docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md` and `AI_FIRST_SDLC_DECISION_SUMMARY.md`:
- A: the summary's trust statement and "What the proposal rests on" table.
- B: review findings 1-4, including outcome movement in section 28a.
- C: wording findings 5-7.
- D: alignment to the logged decisions and the R0 differences, and the governing-file fact.

Count at landing, with the commit named: test files naming the workflows (`~57` becomes that figure), and Codex lines with the glob stated.

## Out of Scope
- Writing any undecided decision as decided: OD-4 to OD-9, OD-11 to OD-13, OD-16 to OD-21.
- Credential detail of any kind, and u24 specifics.
- Mermaid diagram text.
- Plan sections other than those the draft names.

## Acceptance Criteria
1. Every draft edit is applied at the stated text, except any the planner has marked in Implementation Notes. If a Before string is not found on that line, stop and report; do not approximate.
2. Both counts are recorded with their commit and, for Codex, the glob.
3. The sweep figures cite the path on main if the evidence branch has merged, or that branch at d2ed6c8c2 if it still stands. If it has been deleted, the sentence stays and the figures go.
4. The CI-lane sentence for the Codex row is checked against the workflow first.
5. `tests/docs` passes and `docs/REGISTRY.yaml` is regenerated.
6. The PR body says which plan sections lead-planner reviewed and that the rest remain unreviewed, and states the summary's growth of about 350 words.

## Related Tickets
TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION, TCK-20261031-GOVERNING-FILE-EDITS-VISIBLE-TO-OWNER

## Related Docs
docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md, docs/plans/agent_infrastructure/AI_FIRST_SDLC_DECISION_SUMMARY.md

## Related Stored Artifacts
None.

## Related Code Areas
None.

## Assumptions / Open Questions
Line numbers in the draft are from origin/main b110ee4c2. `Un-require` and `5k LOC` each appear twice in the plan, so those two edits go by the draft's line number, 1361 and 1042.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
