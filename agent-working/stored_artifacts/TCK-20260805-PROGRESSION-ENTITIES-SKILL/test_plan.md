---
status: active
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260805-PROGRESSION-ENTITIES-SKILL
artifact_type: test_plan
tags: [skills, progression]
---

# Test Plan — TCK-20260805-PROGRESSION-ENTITIES-SKILL

## Normal Flow
- Skill parses as valid frontmatter + Markdown, `source: project`.
- Real formulas/constants/phase names present verbatim.

## Edge Cases
- The 6-step recalculation order is tested for correct sequence, not just presence — getting the
  order wrong (e.g. applying trait bonuses before equipment bonuses) would silently produce wrong
  derived stats in any real debugging session using this skill.

## Failure Modes
N/A — pure content-authoring ticket.

## Regression-Prone Paths
- `.agents/` mirror body matches `.claude/` source; contract registration present; Codex-adapter
  regression suite passes.
