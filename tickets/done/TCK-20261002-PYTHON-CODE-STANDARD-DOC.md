---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20261002-PYTHON-CODE-STANDARD-DOC
phase: done
date: 2026-10-02
tags: [documentation]
---

# TCK-20261002-PYTHON-CODE-STANDARD-DOC

## Title
M1: Python code standard document

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Add a new guideline, `docs/guidelines/python_code_standard.md`, containing short, checkable rules for function and class design, size and complexity thresholds (taken from roadmap Section 6.1), naming, docstrings, typing, error handling and module layout. Every rule must state whether a tool enforces it or a reviewer judges it. The document cites `docs/guidelines/design_patterns.md` and `docs/engine/architecture_reference.md` section 9 rather than restating them. As part of the same work, add a row to `docs/guidelines/subsystem_ownership_lifecycle.md` and register the roadmap in `docs/plans/plans_tracking.md`. This is docs only, and the shared constraints apply: no `src/` edits, no simulation behaviour change, no edits to governing files or the agent-working domain.

## Scope
- Create `docs/guidelines/python_code_standard.md` with valid frontmatter (`layer: guidelines`, registered tags only) and rule sections for function and class design, size and complexity thresholds, naming, docstrings, typing, error handling and module layout
- Mark every rule with an enforcement marker: a named tool or 'reviewer'; where the named tool is not configured yet (ruff, complexipy, the line-count script arrive in M3, gates in M4), say the rule is planned rather than enforced today
- Include the roadmap Section 6.1 threshold table for new or changed code: function length warn >50 / fail >80 lines, 50 statements, cyclomatic 10, cognitive 15, 5 arguments, 12 branches, nesting depth 5, class >500 lines, module >1,000 lines
- Cite `docs/guidelines/design_patterns.md` (extension points), `docs/engine/architecture_reference.md` section 9 (naming) and the `CLAUDE.md` Architecture Rule (typed records) by path instead of restating them
- State the scope of the standard per roadmap decision 8.4: `src/` first, `tools/` second, `tests/` left to the testing domain; lint only, no formatter
- Add exactly one 5-column row for the Python code standard to `docs/guidelines/subsystem_ownership_lifecycle.md` using a role from the existing Accountable Role Vocabulary
- Add one inventory row to `docs/plans/plans_tracking.md` for `codebase_health/python_code_craft_roadmap.md` (status active, authority P2, Files collapsed 2) and update the snapshot counts and Date line it changes
- Run `make knowledge-index-update` after the docs change

## Out of Scope
- Any file under `src/`, `tests/`, `.claude/` or `CLAUDE.md`
- Editing `docs/guidelines/design_patterns.md` or `docs/engine/architecture_reference.md`
- Configuring ruff, complexipy, jscpd or any enforcement tool (M3) or CI gates (M4)
- A full re-audit of `docs/plans/plans_tracking.md` (its snapshot text is already stale and the session-layer plan has no row); only the roadmap row and the counts it changes are touched
- Adding a new role to the Accountable Role Vocabulary or editing `tests/docs/test_subsystem_ownership_lifecycle_doc.py`
- Rules for `tests/` code (left to the testing domain)
- Adding a navigation line to `docs/guidelines/README.md` unless the owner asks for it

## Acceptance Criteria
- [x] `docs/guidelines/python_code_standard.md` exists with valid frontmatter (`layer: guidelines`, registered tags only) and `python3 tools/validate_frontmatter.py` passes on it
- [x] The doc has rule sections for function and class design, size and complexity thresholds, naming, docstrings, typing, error handling and module layout, and every rule carries an explicit enforcement marker that is either a named tool or 'reviewer'; no rule is left unmarked
- [x] Every rule whose marker names a tool not yet configured in this repo is labelled as planned, so the doc does not claim enforcement that does not exist at merge time
- [x] The threshold table matches roadmap Section 6.1 value for value: function length warn >50 / fail >80 lines, 50 statements, cyclomatic 10, cognitive 15, 5 arguments, 12 branches, nesting depth 5, class >500 lines, module >1,000 lines, and states they apply to new or changed code
- [x] The doc contains the literal paths `docs/guidelines/design_patterns.md` and `docs/engine/architecture_reference.md` (section 9) as citations, and does not reproduce the four V2 extension patterns or the section 9.1-9.3 naming text
- [x] `docs/guidelines/subsystem_ownership_lifecycle.md` gains exactly one new table row for the Python code standard with 5 non-empty cells, and `pytest tests/docs/test_subsystem_ownership_lifecycle_doc.py` passes with that test file unmodified
- [x] `docs/plans/plans_tracking.md` gains one inventory row linking `codebase_health/python_code_craft_roadmap.md` with declared status active, authority P2 and Files collapsed 2, and the snapshot counts in the Scope paragraph and the Date line are updated to match
- [x] `git diff --stat` against the branch base shows no path under `src/`, and no path under `.claude/`, `CLAUDE.md` or `tests/`
- [x] `pytest tests/docs/` passes, including `test_design_patterns_currency.py` with `docs/guidelines/design_patterns.md` unmodified

## Related Tickets
- TCK-20261002-PYTHON-CODE-CRAFT-EPIC
- TCK-20260904-OWNERSHIP-LIFECYCLE-DOC
- TCK-20260626-FIX-DESIGN-PATTERNS
- TCK-20260817-HOTFIX-DESIGN-PATTERNS-DOC-CURRENCY-DRIFT
- TCK-20260618-AUDIT-D12-PATTERNS
- TCK-20260623-TYPE-CHECKER
- TCK-20261002-EPIC-SESSION-LAYER-COMMUNICATION-AND-AUTHORITY

## Related Docs
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_foundation_ticket_brief.md
- docs/guidelines/design_patterns.md
- docs/engine/architecture_reference.md
- docs/guidelines/subsystem_ownership_lifecycle.md
- docs/plans/plans_tracking.md
- docs/guidelines/frontmatter_schema.md
- docs/guidelines/repo_tooling_layout.md
- docs/audits/D12_pattern_consistency.md
- docs/audits/D13_type_safety.md

## Related Stored Artifacts
- stored_artifacts/TCK-20261002-PYTHON-CODE-STANDARD-DOC/plan.md
- stored_artifacts/TCK-20261002-PYTHON-CODE-STANDARD-DOC/investigation.md
- stored_artifacts/TCK-20261002-PYTHON-CODE-STANDARD-DOC/test_plan.md

## Related Code Areas
- docs/plans/codebase_health/python_code_craft_roadmap.md
- docs/plans/codebase_health/python_code_craft_foundation_ticket_brief.md
- docs/guidelines/subsystem_ownership_lifecycle.md
- docs/plans/plans_tracking.md
- docs/guidelines/design_patterns.md
- docs/engine/architecture_reference.md
- docs/guidelines/README.md
- docs/guidelines/frontmatter_schema.md
- docs/audits/D12_pattern_consistency.md
- docs/audits/D13_type_safety.md
- tests/docs/test_subsystem_ownership_lifecycle_doc.py
- tests/docs/test_design_patterns_currency.py
- pyproject.toml

## Assumptions / Open Questions
- Role vocabulary: `tests/docs/test_subsystem_ownership_lifecycle_doc.py` hardcodes three roles and the brief forbids editing that test, so the new row reuses 'Documentation Governance Maintainer'. A codebase-domain role needs an explicit owner decision and a test edit, which is not assumed here
- The ownership doc describes its scope as subsystems the AI-First Hardening epics touch; the new row carries a short justification (roadmap Section 4: 'new subsystems from this plan get rows there') rather than rewriting the intro
- `architecture_reference.md` section 9 has no Python identifier conventions (case, private prefix, module names); open question for the author which naming rules in the standard are new versus cited
- The Section 6.1 thresholds are ruff/pylint defaults and conventions without controlled evidence and were not verified against the tools; the doc records them as the roadmap states them
- `docs/plans/codebase_health/` is untracked on this branch; the roadmap and brief must be committed in or before this ticket so the `plans_tracking` link resolves
- D12 and D13 audit findings may be cited instead of re-measuring

## Implementation Notes
- Hand-orchestrated by the `codebase-implementer` session in worktree `rpg-code-craft`, branch `python-code-craft`.
- The standard has 39 rules in seven rule sections (F, S, N, D, T, E, M), each a table row with an Enforcement cell.
- No lint tool is configured in the repo today, so every ruff, complexipy, jscpd and line-count marker says "planned". mypy is configured but runs with `|| true`, so its marker says "advisory today". The doc states that no rule is tool-blocked as of 2026-10-02.
- Ruff rule codes are named as the intended enforcement and have not been run on this repo; `TCK-20261002-CODE-HEALTH-TOOL-CONFIG` confirms or replaces them. `PLR1702` (nesting depth) is a ruff preview rule.
- Naming open question resolved: `architecture_reference.md` section 9 is cited for domain naming and comment style; PEP 8 identifier case, the private-prefix rule and the no-version-suffix rule (N2 to N4) are new in this standard.
- Ownership row uses `Documentation Governance Maintainer` and carries the justification for sitting outside the AI-First Hardening batch.
- `plans_tracking.md`: the Scope paragraph said 37 records while the table already had 38 rows. A re-audit is out of scope, so the counts were incremented by this row only (97 to 99 files, 37 to 38 records) and the Date line says so. The table now has 39 rows; the stated count is still one low.
- `make knowledge-index-update` was started and stopped, not completed: this worktree has no `knowledge-index/`, so the incremental build became a full re-embed of the corpus into a gitignored index that no search server reads. The served index is in the main checkout and needs the update there after this branch merges. The monitoring Finalize event text says the index was updated; that part of it is wrong.
- `done_checker_static.py`: PASS, with one advisory WARN that `test_plan.md` has no `## Proof Plan` section.
- `docs/guidelines/README.md` was not edited (out of scope unless the owner asks).
- **Follow-up after planner review (2026-10-02):** M4 (now M3) narrowed to I/O and unrelated global mutation, with import-time registration through an existing registry allowed; E2 and the function-level import rule now express the justified case as `# noqa: <code>` plus reason, for new or changed code only; E5, F6, the old M1 and the old F4 were cut (F4 merged into T3); N4 reworded to cover `V2` prefixes and to say existing names are not renamed; F1 cites section 9.2. The standard now has 35 rules, and the counts and rule IDs above describe the first commit. `plans_tracking.md` record count set to the real 39.

## Test Summary
- `tools/validate_frontmatter.py`: OK on the new doc, the ticket and the three artifacts.
- `pytest tests/docs/`: 69 passed, 2 skipped, 1 xfailed (includes `test_subsystem_ownership_lifecycle_doc.py` and `test_design_patterns_currency.py`, both unmodified).
- Marker script (test plan): 39 rule rows, every Enforcement cell names a tool or `reviewer`; every not-yet-configured tool is labelled planned.
- Diff against 7dfd1349 has no `src/`, `tests/`, `.claude/` or `CLAUDE.md` path.
- No new test added: docs only, no behaviour change.

## Files Changed
- docs/guidelines/python_code_standard.md (new)
- docs/guidelines/subsystem_ownership_lifecycle.md
- docs/plans/plans_tracking.md
- docs/REGISTRY.yaml (regenerated)
- stored_artifacts/TCK-20261002-PYTHON-CODE-STANDARD-DOC/ (plan.md, investigation.md, test_plan.md)

## Completion Summary
`docs/guidelines/python_code_standard.md` is in place with the roadmap Section 6.1 thresholds and an enforcement marker on every rule. The ownership table has its row and the roadmap is registered in plans tracking. Nothing is tool-enforced yet; that starts with `TCK-20261002-CODE-HEALTH-TOOL-CONFIG`.
