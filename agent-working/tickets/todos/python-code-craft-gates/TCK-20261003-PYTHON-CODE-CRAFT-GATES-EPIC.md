---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-PYTHON-CODE-CRAFT-GATES-EPIC
phase: open
date: 2026-10-03
tags: [delivery, planning]
---

# TCK-20261003-PYTHON-CODE-CRAFT-GATES-EPIC

## Title
M4: Python Code Craft gates — advisory CI ratchet, SARIF feedback, mypy baseline, prek, type-checker trial

## Status
EPIC_SCOPED

## Tier
epic

## Type
chore

## Priority
P2

## Request Summary
Roadmap milestone M4 (python_code_craft_roadmap.md Section 7). M1 to M3 closed under TCK-20261002-PYTHON-CODE-CRAFT-EPIC (PRs #288, #297, #298). The owner approved the toolchain (decision 8.8), a two-week advisory soak before any gate blocks (8.10), and on 2026-10-03: mypy soaks with the ratchet, changed-line feedback via SARIF code scanning, prek installed opt-in only, jscpd report-only. Scope-only epic; children listed in SEQUENCE.md.

## Scope
- Track the six child tickets in SEQUENCE.md order
- Record the soak start date (merge of the advisory CI job) and end date (start + 14 days) here and in the roadmap

## Out of Scope
- Any file under src/ (roadmap decision 8.7): no autofix, no reformat, no `# noqa` / `# type: ignore`
- CLAUDE.md, .claude/settings.json, Claude Code hooks, .claude/agents/, .claude/workflows/, .claude/skills/
- Roadmap M5, M6, M7

## Acceptance Criteria
- [ ] Children 1 to 5 in agent-working/tickets/done/
- [ ] Child 6 (flip) is filed with the soak end date and either done or explicitly carried forward by the owner
- [ ] Roadmap Section 7 marks M4 done or names what carries forward

## Related Tickets
- TCK-20261002-PYTHON-CODE-CRAFT-EPIC
- the six children in SEQUENCE.md

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_m4_gates_ticket_brief.md
- docs/guidelines/python_code_standard.md

## Related Stored Artifacts
None.

## Related Code Areas
- .github/workflows/test.yml
- tools/code_health/
- registries/code_health_exceptions.jsonl
- pyproject.toml, uv.lock, Makefile

## Assumptions / Open Questions
- Measured 2026-10-03 on main b90c3aa9: mypy 2.1.0 reports 1,569 errors in 236 of 710 files under src/ (48 s, ~400 MB); registry holds 3,617 rows, all reviewed: false
- Hand-written by codebase-planner from the approved brief (not a create-tickets run); each child's Investigate phase must confirm its facts

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
