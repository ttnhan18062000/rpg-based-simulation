---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-DEV-SKILL
artifact_type: test_plan
tags: [skills, simulation-quality]
---

# Test Plan — TCK-20260805-SIMQ-DEV-SKILL

## Normal Flow
- New skill parses as valid frontmatter + Markdown, `source: project`.
- All 3 core data-model class names and the 9-step pillar-addition protocol markers present.

## Edge Cases
- The disclosed `EconomyScorer`/`paid_info_transaction` divergence is present, not omitted — a
  dev-side skill that hides a known real-vs-documented-design gap would mislead future debugging.

## Failure Modes
N/A — pure content-authoring ticket.

## Regression-Prone Paths
- No-duplication guard: `simq-audit`'s own audit-workflow-specific vocabulary
  (`Recalibrate`, `grade anchors`) does not appear in the new skill.
- `.agents/` mirror body matches `.claude/` source; `agent-orchestration/skills.yaml` contract
  entry present; Codex-adapter regression suite passes.
