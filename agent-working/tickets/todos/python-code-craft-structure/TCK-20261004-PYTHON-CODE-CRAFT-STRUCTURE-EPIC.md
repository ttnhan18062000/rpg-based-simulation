---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-PYTHON-CODE-CRAFT-STRUCTURE-EPIC
phase: open
date: 2026-10-04
tags: [architecture, planning]
---

# TCK-20261004-PYTHON-CODE-CRAFT-STRUCTURE-EPIC

## Title
M5: Python Code Craft structure — package audit, package registry, ast-grep rule pack, import-linter evaluation

## Status
EPIC_SCOPED

## Tier
epic

## Type
chore

## Priority
P2

## Request Summary
Roadmap milestone M5 (python_code_craft_roadmap.md Section 7). Owner decisions 2026-10-04: layout codebase/structure/ and codebase/rules/; ast-grep gets its own 14-day soak (M4 flip excludes tool ast_grep); parity proof_type remapped, not extended (recorded in the remediation epic). Scope-only epic; children in SEQUENCE.md.

## Scope
- Track the four children in SEQUENCE.md order (1 audit, 2 package registry, 4 import-linter evaluation; 3 ast-grep independent)
- Follow-ups the children produce (import-linter adoption, blocking flips for the registry validator and the ast-grep rules, package merges for rpg) are filed, not done, by this epic

## Out of Scope
- Any direct implementation (tracks children only)
- M6 agent integration requests and M7 refactor lane
- Any file under src/ (roadmap decision 8.7): no move, merge, delete, autofix, reformat or inline suppression
- CLAUDE.md, .claude/settings.json, Claude Code hooks, .claude/agents/, .claude/workflows/, .claude/skills/
- Making any check blocking (each flip gets its own ticket after its own two-week soak, decision 8.10)
- Changing M4 soak thresholds, ruff/complexipy versions or existing rows in codebase/baselines/code_health_exceptions.jsonl

## Acceptance Criteria
- [ ] Children 1 to 4 in agent-working/tickets/done/
- [ ] Roadmap Section 7 marks M5 done or names what carries forward

## Related Tickets
- TCK-20261004-SRC-PACKAGE-STRUCTURE-AUDIT
- TCK-20261004-PACKAGE-REGISTRY-VALIDATOR
- TCK-20261004-AST-GREP-RULE-PACK-ADVISORY
- TCK-20261004-IMPORT-LINTER-EVALUATION
- TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING

## Related Docs
- docs/plans/codebase_health/python_code_craft_m5_structure_ticket_brief.md
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/guidelines/python_code_standard.md

## Related Stored Artifacts
None.

## Related Code Areas
- codebase/structure/
- codebase/rules/
- codebase/health/

## Assumptions / Open Questions
- Epic closes when all four children are done
- Hand-written by codebase-planner brief (owner decisions 2026-10-04); filed by codebase-implementer 2026-10-04. Facts in the brief were measured on main b9251cf5; each ticket's Investigate phase re-verifies the ones it relies on

## Implementation Notes


## Test Summary

## Files Changed

## Completion Summary
