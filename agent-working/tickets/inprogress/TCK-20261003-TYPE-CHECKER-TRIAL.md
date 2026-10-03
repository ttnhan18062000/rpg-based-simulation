---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261003-TYPE-CHECKER-TRIAL
phase: open
date: 2026-10-03
tags: [benchmarking]
---

# TCK-20261003-TYPE-CHECKER-TRIAL

## Title
M4e: Type-checker trial — basedpyright and Pyrefly against mypy on src/ (report only)

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Roadmap 6.2 keeps mypy + mypy-baseline as primary and names basedpyright (native baseline) and Pyrefly as trials; `ty` is excluded because its only suppression path edits source. Produce a measured comparison and a recommendation. No CI or dependency change.

## Scope
- Run basedpyright and Pyrefly over src/ on one commit, each in a scratch environment, one at a time under a memory cap
- Record per checker: version, wall time, peak memory, error count, baseline support (no source edits), error overlap with mypy 2.1.0 on the same commit
- Decision record in docs/plans/codebase_health/ recommending keep mypy, replace, or add a second checker

## Out of Scope
- Any file under src/ (roadmap decision 8.7): no autofix, no reformat, no `# noqa` / `# type: ignore`
- CLAUDE.md, .claude/settings.json, Claude Code hooks, .claude/agents/, .claude/workflows/, .claude/skills/
- Any change to pyproject.toml, uv.lock, CI or Makefile

## Acceptance Criteria
- [ ] Decision record exists with the measurements above for all three checkers on the same commit, and the commit SHA
- [ ] Measurements reproducible from commands written in the record
- [ ] `git diff --stat <base>...HEAD` lists no path under src/, none under .claude/, and not CLAUDE.md

## Related Tickets
- TCK-20261003-PYTHON-CODE-CRAFT-GATES-EPIC
- TCK-20261003-MYPY-BASELINE-ADVISORY

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_m4_gates_ticket_brief.md

## Related Stored Artifacts
None.

## Related Code Areas
- pyproject.toml ([tool.mypy], read only)
- src/ (read only)

## Assumptions / Open Questions
- Independent of the other tickets; may run any time

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
