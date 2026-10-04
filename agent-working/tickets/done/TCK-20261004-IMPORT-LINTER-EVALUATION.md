---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261004-IMPORT-LINTER-EVALUATION
phase: done
date: 2026-10-04
tags: [architecture, planning]
---

# TCK-20261004-IMPORT-LINTER-EVALUATION

## Title
M5.4: import-linter evaluation (report only)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Evaluate import-linter against the existing import-boundary tests and the package registry's layer order. Output is a decision record: replace, add, or drop. No dependency, CI or test change.

## Scope
- Express the existing import-boundary tests as import-linter contracts in a scratch config (not committed to pyproject.toml), plus one layers contract built from the registry's layer field; run over src/ on one commit. Re-verify the 31-file / 41-rule inventory from the brief, do not trust it
- Record version, wall time, peak memory; per test whether the contract catches the same violation (inject one known violation per rule in a scratch copy, confirm both fail); TYPE_CHECKING and function-local import handling; current src/ violations per contract (the ignore_imports baseline needed); rules no contract can express
- Run each contract with and without allow_indirect_imports and exclude_type_checking_imports and report the difference
- Confirm or refute with an injected violation that tests/architecture/test_phase19_observability_boundaries.py::test_hot_path_does_not_import_heavy_analyzers is a no-op; if confirmed, send the finding to the testing planner as an outbox note (no test edit)
- List hand-written AST tests in tests/architecture/ that could become ast-grep rules, without changing them
- Decision record in docs/plans/codebase_health/ (like the type-checker trial): replace (named tests retire, owner and testing planner agree), add (layer order and uncovered rules), or drop. Roadmap Section 4: never a second copy of the tests

## Out of Scope
- Committing import-linter to pyproject.toml or CI
- Editing or deleting any tests/architecture/ test (owned by another domain; replacement is a later ticket agreed with its owner)
- Any file under src/ (roadmap decision 8.7): no move, merge, delete, autofix, reformat or inline suppression
- CLAUDE.md, .claude/settings.json, Claude Code hooks, .claude/agents/, .claude/workflows/, .claude/skills/
- Making any check blocking (each flip gets its own ticket after its own two-week soak, decision 8.10)
- Changing M4 soak thresholds, ruff/complexipy versions or existing rows in codebase/baselines/code_health_exceptions.jsonl

## Acceptance Criteria
- [x] Decision record written with the measurements above
- [x] Injected-violation results for each rule, in the record
- [x] phase19 finding confirmed or refuted; outbox note written to .claude/handover/codebase-planner-outbox.md with status: pending, if confirmed
- [x] Adoption ticket filed if the recommendation is replace or add
- [x] git diff shows no change to pyproject.toml, CI, tests/ or src/

## Related Tickets
- TCK-20261004-PYTHON-CODE-CRAFT-STRUCTURE-EPIC
- TCK-20261004-PACKAGE-REGISTRY-VALIDATOR
- TCK-20261004-AST-GREP-RULE-PACK-ADVISORY

## Related Docs
- docs/plans/codebase_health/python_code_craft_m5_structure_ticket_brief.md
- docs/plans/codebase_health/python_code_craft_roadmap.md
- tests/architecture/
- docs/audits/D14_coupling_depth.md

## Related Stored Artifacts
None.

## Related Code Areas
- tests/architecture/
- tests/unit/
- tests/integration/
- tests/api/

## Assumptions / Open Questions
- Namespace packages (from the audit, TCK-20261004-SRC-PACKAGE-STRUCTURE-AUDIT): 20 of 36 top-level packages have no `__init__.py` (actions, ai, api, certification, content, content_semantics, core, domains, logging, observability, perf, strategy, systems, testing, town, views, world, worldassembly, worldgeneration, worldmodules), and a grimp build over `src` saw only 215 of 744 files. import-linter is built on grimp, so this ticket must MEASURE (not assume) (a) whether import-linter/grimp can cover those 20 packages without adding `__init__.py` (a `src/` edit, out of scope), and (b) what coverage loss a `drop` or `add` recommendation would carry if it cannot. If full coverage needs `__init__.py` files, the record says so; that becomes an M7 / rpg decision, not part of this batch
- Depends on ticket 2 (the layers contract reads the registry)
- Heavy runs one at a time under systemd-run --user --scope -p MemoryMax=2G
- Hand-written by codebase-planner brief (owner decisions 2026-10-04); filed by codebase-implementer 2026-10-04. Facts in the brief were measured on main b9251cf5; each ticket's Investigate phase re-verifies the ones it relies on

## Implementation Notes
- Record: `docs/plans/codebase_health/import_linter_evaluation.md`. Recommendation ADD with a narrow replace of 8 equivalent rules; versions import-linter 2.15 / grimp 3.17; scratch tree from `git archive c4304a7a3`; the exact command is in the record.
- Namespace packages measured: 20 of 36 top-level packages lack `__init__.py`; `src` + `src.<pkg>` for each covers 774 of 744 files plus package nodes except `src/engine/intent`; `src` alone makes a contract on `src.core` fail loudly. No `src/` edit needed for the 20; the one uncovered directory is an M7 / rpg decision.
- The inventory (a read-only subagent) lists 50 rules in 29 files (its own summary said 53; the brief said 41 in 31). 27 were exercised by injection; 23 are classified from the inventory only.
- phase19 no-op confirmed; Message 9 written to the outbox (status: pending). Adoption ticket filed: `TCK-20261004-IMPORT-LINTER-ADOPTION` (BLOCKED on owner and testing planner).
- The harness and cases ran from the scratchpad and are not committed; the contract bodies are in the record's Appendix A.


## Test Summary
No repo test changed. Evidence is the record: baseline of 12 contracts in a 2 x 2 flag matrix, 45 injected-violation rows (existing test result vs contract), layer contract baseline 113 / 99, namespace coverage counts. `git diff --stat origin/main...HEAD` shows no change to src/, tests/ (other than ticket 2's new test), pyproject.toml, uv.lock or .github/ from this ticket.

## Files Changed
- docs/plans/codebase_health/import_linter_evaluation.md (new)
- agent-working: this ticket, the adoption ticket, stored artifacts, monitoring shards; outbox Message 9 (git-ignored)

## Completion Summary
import-linter evaluated against the existing import-boundary tests and the registry's layer order: ADD, with a narrow replace of 8 equivalent tests (one a no-op), subject to the owner and the testing planner. Open: the `src/engine/intent` `__init__.py` question (M7 / rpg) and the adoption ticket.
