---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260805-COMBAT-SKILL
artifact_type: test_plan
tags: [skills, combat]
---

# Test Plan — TCK-20260805-COMBAT-SKILL

## Normal Flow
- Skill parses as valid frontmatter + Markdown, `source: project`.
- Real formula, modifiers, posture values, Sliding State rule all present verbatim.

## Edge Cases
- "NOT authoritative" framing present — the single most consequential distinction to get right,
  per the ticket's own explicit citation.

## Failure Modes
N/A — pure content-authoring ticket.

## Regression-Prone Paths
- `.agents/` mirror body matches `.claude/` source; contract registration present; Codex-adapter
  regression suite passes.
