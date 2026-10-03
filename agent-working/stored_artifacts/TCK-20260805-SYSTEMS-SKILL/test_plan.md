---
status: active
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260805-SYSTEMS-SKILL
artifact_type: test_plan
tags: [skills, economy]
---

# Test Plan — TCK-20260805-SYSTEMS-SKILL

## Normal Flow
- Skill parses as valid frontmatter + Markdown, `source: project`.
- Real formulas/constants present verbatim.

## Edge Cases
- The `src/core/quests.py` vs `src/systems/quest_system.py` distinction is stated (a real, easy
  source of confusion this skill must not silently conflate).
- The explicit "what this skill does NOT cover" disclosure is present.

## Failure Modes
N/A — pure content-authoring ticket.

## Regression-Prone Paths
- `.agents/` mirror body matches `.claude/` source; contract registration present; Codex-adapter
  regression suite passes.
