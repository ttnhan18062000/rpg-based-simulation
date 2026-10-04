---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-PACKAGE-REGISTRY-VALIDATOR
phase: done
date: 2026-10-04
tags: [architecture, planning]
---

# TCK-20261004-PACKAGE-REGISTRY-VALIDATOR

## Title
M5.2: Package registry seeded from the audit, with advisory validator

## Status
DONE

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
- [x] Registry has one row per tracked top-level package; validator passes on main
- [x] Validator fails on injected: unknown field, missing package row, nonexistent package, nonexistent cited path (tests)
- [x] CI step is advisory (continue-on-error) and visible in a real PR run
- [x] Follow-up blocking-flip ticket filed
- [x] `git diff --stat <base>...HEAD` lists no path under src/

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
- Planner review (2026-10-04) changed the plan: the real-repo test asserts schema validity only, never completeness against the live tree, because `tests/codebase/` runs in the non-advisory tools-a-e job and a completeness assertion would fail any domain's PR that adds a package, skipping the soak. Completeness is tested only in scratch-repo fixtures. Problems carry a `kind` (`schema` or `completeness`) so the flip ticket promotes completeness without a rewrite. The advisory CI step runs both classes.
- Seeded 36 rows from the audit table by a one-off script (not committed). `do_not_imitate` carries the four roadmap Section 2 worst cases with sizes re-measured with `ast` on 2026-10-04 (`EventExtractor.extract` is 1,588 lines now, the roadmap says 1,585). `exemplar_modules` is empty and `system` null on every row: choosing exemplars is judgement the audit did not make. **Open follow-up for M6 or the owner: pick exemplar modules.**
- The registry is the source of truth after seeding; the audit table carries a dated-snapshot note, and the README and standard rows say so.
- Flip ticket filed: `TCK-20261004-PACKAGE-REGISTRY-VALIDATOR-FLIP-BLOCKING` (BLOCKED, dates written at merge). The namespace-package assumption was added to `TCK-20261004-IMPORT-LINTER-EVALUATION` as the planner asked.
- No CI-pinning test needed editing (adding a step to an existing job changed no job set); no outbox note to the testing planner was needed.


## Test Summary
`tests/codebase/test_package_registry.py`: 26 passed (real-repo schema check, 13 schema-defect cases, missing field, duplicate and bad JSON, both completeness checks, untracked directory, kinds filter, non-git fallback, `load_rows`, CLI exit codes, CI step advisory). CI-pinning static and tools tests (126 with the new file) pass. `ruff check codebase/structure` clean. `python3 -m codebase.structure.packages validate` on main: 0 problems.

## Files Changed
- codebase/structure/__init__.py, packages.py, package_registry.jsonl (new)
- tests/codebase/test_package_registry.py (new)
- .github/workflows/test.yml (advisory step)
- docs: roadmap 6.4, python_code_standard.md (M5), codebase/README.md, subsystem_ownership_lifecycle.md, audit snapshot note
- agent-working: this ticket, the flip ticket, the import-linter ticket assumption, SEQUENCE.md

## Completion Summary
Package registry (36 rows) and an advisory validator with `schema` and `completeness` problem classes, wired as an advisory step of the code-health job. Open follow-ups: exemplar modules (M6 or owner); the blocking flip after its soak. No `src/` change.
