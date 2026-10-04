---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-AST-GREP-RULE-PACK-ADVISORY
phase: open
date: 2026-10-04
tags: [architecture, planning]
---

# TCK-20261004-AST-GREP-RULE-PACK-ADVISORY

## Title
M5.3: ast-grep rule pack (N3, N4, E3) advisory through the ratchet

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Add ast-grep as a pinned lint dependency and a rule pack in codebase/rules/ for the reviewer-only standard rules, reporting through the code-health ratchet under its own tool key ast_grep, with its own 14-day soak.

## Scope
- Add ast-grep-cli (exact pin) to the lint group; refresh uv.lock
- Rules in codebase/rules/ (sgconfig.yml, one YAML per rule), each message states the fix (roadmap 6.2), with ast-grep rule tests (valid and invalid snippets) run by `ast-grep test` from tests/codebase/: N3 (import of a _private name from another module), N4 (V2 / _v2 / _new markers in def and class names only), E3 (except whose body is only pass)
- T3 dict[str, Any] rule only if Investigate shows a precise pattern (public functions, signatures only); otherwise it stays a reviewer rule and the ticket records why
- Adapter in codebase/health/adapters.py reading ast-grep JSON into the normalised finding format keyed by file and enclosing symbol, tool key ast_grep. Seed only ast_grep rows on main; rows of other tools untouched
- Report in the advisory code-health job and make code-health; include in SARIF changed-line feedback if codebase/gates/sarif_feedback.py accepts a new tool without structural change, else note a follow-up
- Verify the flip ticket's (TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING) ast_grep exclusion still covers the tool key as implemented; adjust that ticket if the key differs, and file this pack's own flip ticket dated 14 days after merge
- Docs: standard rules N3, N4, E3 Enforcement cells name the rule IDs

## Out of Scope
- Porting existing hand-written AST tests to ast-grep (ticket 4 only lists candidates)
- Rules beyond the standard; autofix
- Any file under src/ (roadmap decision 8.7): no move, merge, delete, autofix, reformat or inline suppression
- CLAUDE.md, .claude/settings.json, Claude Code hooks, .claude/agents/, .claude/workflows/, .claude/skills/
- Making any check blocking (each flip gets its own ticket after its own two-week soak, decision 8.10)
- Changing M4 soak thresholds, ruff/complexipy versions or existing rows in codebase/baselines/code_health_exceptions.jsonl

## Acceptance Criteria
- [ ] Rules fire on invalid snippets and not on valid ones (ast-grep test via tests/codebase/)
- [ ] ast_grep rows seeded; diff to code_health_exceptions.jsonl touches only tool ast_grep rows
- [ ] The flip ticket's ast_grep exclusion verified against the implemented tool key (adjusted if it differs)
- [ ] Own flip ticket filed with the soak end date
- [ ] Real PR run shows the advisory report
- [ ] `git diff --stat <base>...HEAD` lists no path under src/

## Related Tickets
- TCK-20261004-PYTHON-CODE-CRAFT-STRUCTURE-EPIC
- TCK-20261003-CODE-HEALTH-GATES-FLIP-BLOCKING

## Related Docs
- docs/plans/codebase_health/python_code_craft_m5_structure_ticket_brief.md
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/guidelines/python_code_standard.md

## Related Stored Artifacts
None.

## Related Code Areas
- codebase/rules/
- codebase/health/adapters.py
- codebase/gates/sarif_feedback.py
- pyproject.toml, uv.lock

## Assumptions / Open Questions
- Independent of tickets 1 and 2; the flip ticket already carries the ast_grep exclusion (added in the planning commit, whatever order the two land in); this ticket only verifies the tool key
- ~107 except-pass occurrences in src/ by a rough grep: expect a large seeded baseline for E3
- Hand-written by codebase-planner brief (owner decisions 2026-10-04); filed by codebase-implementer 2026-10-04. Facts in the brief were measured on main b9251cf5; each ticket's Investigate phase re-verifies the ones it relies on

## Implementation Notes


## Test Summary

## Files Changed

## Completion Summary
