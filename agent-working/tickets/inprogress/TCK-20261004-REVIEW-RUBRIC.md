---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-REVIEW-RUBRIC
phase: inprogress
date: 2026-10-04
tags: [architecture, planning]
---

# TCK-20261004-REVIEW-RUBRIC

## Title
M6b: Review rubric in the Python code standard

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Add a short "Review rubric" section to `docs/guidelines/python_code_standard.md` for whoever reviews Python changes. Docs-only, so no plan.md round trip.

## Scope
- Every finding is Important, Nit or Pre-existing; only Important blocks
- At most 3 Nits per review; the rest are dropped
- Nothing a configured tool already reports is raised by hand (the Enforcement column says which)
- A Pre-existing finding never blocks the change; tool-reported ones are already registry rows; file-wide reviewer rules are proposed as `do_not_imitate`; otherwise mentioned once and dropped
- Each Important finding names the rule ID (F1, T3, E3 ...) or the architecture rule it breaks
- One table plus up to 6 bullets, no examples (examples go in the skill, M6d)
- Doc test pins the three categories and the "only Important blocks" sentence

## Out of Scope
- Any reviewer agent prompt (`.claude/agents/*review*`)
- Examples

## Acceptance Criteria
- [ ] Section present, within the length limit
- [ ] Doc test passes
- [ ] Frontmatter valid; `make knowledge-index-update` run
- [ ] `git diff --stat <base>...HEAD` lists no path under src/

## Related Tickets
None.

## Related Docs
- docs/plans/codebase_health/python_code_craft_m6_agent_integration_ticket_brief.md
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/guidelines/python_code_standard.md

## Related Stored Artifacts
None.

## Related Code Areas
- docs/guidelines/python_code_standard.md
- tests/codebase/

## Assumptions / Open Questions
- Owner decision 8.17 (2026-10-04): codebase implements M6 although `.claude/**` is agent-working's territory; the PR body names agent-working as owner of those paths
- Nothing here blocks a PR or tool call; M4 and M5 soaks are not disturbed

## Implementation Notes
New Section 11 "Review rubric" in the standard (one table, 5 bullets); old Section 11 "Related" became 12 (no inbound references to the number found). Docs-only: no plan.md round trip.

## Test Summary
`tests/codebase/test_review_rubric.py`: 3 passed (three categories, the "Only Important blocks." sentence, length limit). ruff clean.

## Files Changed
docs/guidelines/python_code_standard.md, tests/codebase/test_review_rubric.py (new), ticket

## Completion Summary
