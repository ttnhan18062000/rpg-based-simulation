---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-PACKAGE-REGISTRY-VALIDATOR
phase: open
date: 2026-10-04
tags: [architecture, planning]
---

# TCK-20261004-PACKAGE-REGISTRY-VALIDATOR

## Title
M5.2: Package registry seeded from the audit, with advisory validator

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
codebase/structure/package_registry.jsonl with one row per tracked top-level src/ package, plus a loader and validator that makes standard rule M5 (new top-level package) checkable. Advisory only.

## Scope
- package_registry.jsonl fields: package, purpose, layer (audit's model), status (active | legacy | frozen), strictness_tier (names defined in this ticket; every row starts at the same tier), exemplar_modules (0 to 3 paths), do_not_imitate (0+ paths each with a reason), system (optional, from registries/system_registry.jsonl), audit_decision, added_date, reviewed
- Loader and validator in codebase/structure/ (python3 -m codebase.structure.packages validate), following codebase/health/registry.py and tools/capability_envelope_baseline.py: reject unknown fields; every row's package exists on disk; every tracked top-level package has exactly one row; cited module paths exist
- Run the validator as an advisory step of the code-health CI job (reports, never fails the PR) and in tests/codebase/
- Docs: roadmap 6.4 path updated to codebase/structure/; codebase/README.md row for structure/; standard rule M5 Enforcement cell names the validator; row in docs/guidelines/subsystem_ownership_lifecycle.md
- File the follow-up ticket to make new-package-without-a-row blocking (after its own two-week soak)

## Out of Scope
- Per-package gates driven by strictness_tier (later)
- Agent guidance pointing at exemplars (M6 request to agent-working)
- Any file under src/ (roadmap decision 8.7): no move, merge, delete, autofix, reformat or inline suppression
- CLAUDE.md, .claude/settings.json, Claude Code hooks, .claude/agents/, .claude/workflows/, .claude/skills/
- Making any check blocking (each flip gets its own ticket after its own two-week soak, decision 8.10)
- Changing M4 soak thresholds, ruff/complexipy versions or existing rows in codebase/baselines/code_health_exceptions.jsonl

## Acceptance Criteria
- [ ] Registry has one row per tracked top-level package; validator passes on main
- [ ] Validator fails on injected: unknown field, missing package row, nonexistent package, nonexistent cited path (tests)
- [ ] CI step is advisory (continue-on-error) and visible in a real PR run
- [ ] Follow-up blocking-flip ticket filed
- [ ] `git diff --stat <base>...HEAD` lists no path under src/

## Related Tickets
- TCK-20261004-PYTHON-CODE-CRAFT-STRUCTURE-EPIC
- TCK-20261004-SRC-PACKAGE-STRUCTURE-AUDIT
- TCK-20261004-IMPORT-LINTER-EVALUATION

## Related Docs
- docs/plans/codebase_health/python_code_craft_m5_structure_ticket_brief.md
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/guidelines/python_code_standard.md
- docs/guidelines/subsystem_ownership_lifecycle.md
- codebase/README.md

## Related Stored Artifacts
None.

## Related Code Areas
- codebase/structure/
- codebase/health/registry.py
- tests/codebase/
- .github/workflows/test.yml

## Assumptions / Open Questions
- Depends on ticket 1 (the audit's layer column and decisions seed the rows)
- Tests pinning CI/Makefile may be edited (decision 8.11); tell the testing planner before the change lands
- Hand-written by codebase-planner brief (owner decisions 2026-10-04); filed by codebase-implementer 2026-10-04. Facts in the brief were measured on main b9251cf5; each ticket's Investigate phase re-verifies the ones it relies on

## Implementation Notes


## Test Summary

## Files Changed

## Completion Summary
