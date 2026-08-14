---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260805-COGNITION-STRATEGY-SKILL
artifact_type: test_plan
tags: [skills, strategy]
---

# Test Plan — TCK-20260805-COGNITION-STRATEGY-SKILL

## Normal Flow
- Skill parses as valid frontmatter + Markdown, `source: project`.
- All real formulas/constants/phase names present verbatim.

## Edge Cases
- The boundary section is structurally first (not just present somewhere in the file) — the
  ticket's own explicit "foregrounded, not buried" requirement, tested by position not just
  substring presence.

## Failure Modes
N/A — pure content-authoring ticket.

## Regression-Prone Paths
- `.agents/` mirror body matches `.claude/` source; contract registration present; Codex-adapter
  regression suite passes.
