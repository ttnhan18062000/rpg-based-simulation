---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260805-OBSERVABILITY-SKILL
artifact_type: test_plan
tags: [skills, observability]
---

# Test Plan — TCK-20260805-OBSERVABILITY-SKILL

## Normal Flow
- New skill file parses as valid frontmatter + Markdown.
- All 7 real Law IDs, all 4 `ObservabilityMode` values, all 4 backpressure modes present verbatim.

## Edge Cases
- The disclosed `LONG_RUN` fall-through gap is present, not silently omitted (a skill that hides
  a known gotcha would actively mislead a debugging session).

## Failure Modes
N/A — pure content-authoring ticket, no executable logic beyond the skill's own presence/content
checks and the mirror-regeneration correctness check.

## Regression-Prone Paths
- `.agents/` mirror body matches `.claude/` source exactly.
- `docs/ai/skills.md` genuinely lists the new skill (not just a claim in the ticket).
