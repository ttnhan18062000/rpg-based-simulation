---
status: active
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20261002-PYTHON-CODE-STANDARD-DOC
phase: open
date: 2026-10-02
tags: [documentation]
---

# TCK-20261002-PYTHON-CODE-STANDARD-DOC

## Title
M1: Python code standard document

## Status
OPEN

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
- [ ] `docs/guidelines/python_code_standard.md` exists with valid frontmatter (`layer: guidelines`, registered tags only) and `python3 tools/validate_frontmatter.py` passes on it
- [ ] The doc has rule sections for function and class design, size and complexity thresholds, naming, docstrings, typing, error handling and module layout, and every rule carries an explicit enforcement marker that is either a named tool or 'reviewer'; no rule is left unmarked
- [ ] Every rule whose marker names a tool not yet configured in this repo is labelled as planned, so the doc does not claim enforcement that does not exist at merge time
- [ ] The threshold table matches roadmap Section 6.1 value for value: function length warn >50 / fail >80 lines, 50 statements, cyclomatic 10, cognitive 15, 5 arguments, 12 branches, nesting depth 5, class >500 lines, module >1,000 lines, and states they apply to new or changed code
- [ ] The doc contains the literal paths `docs/guidelines/design_patterns.md` and `docs/engine/architecture_reference.md` (section 9) as citations, and does not reproduce the four V2 extension patterns or the section 9.1-9.3 naming text
- [ ] `docs/guidelines/subsystem_ownership_lifecycle.md` gains exactly one new table row for the Python code standard with 5 non-empty cells, and `pytest tests/docs/test_subsystem_ownership_lifecycle_doc.py` passes with that test file unmodified
- [ ] `docs/plans/plans_tracking.md` gains one inventory row linking `codebase_health/python_code_craft_roadmap.md` with declared status active, authority P2 and Files collapsed 2, and the snapshot counts in the Scope paragraph and the Date line are updated to match
- [ ] `git diff --stat` against the branch base shows no path under `src/`, and no path under `.claude/`, `CLAUDE.md` or `tests/`
- [ ] `pytest tests/docs/` passes, including `test_design_patterns_currency.py` with `docs/guidelines/design_patterns.md` unmodified

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
None.

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

## Test Summary

## Files Changed

## Completion Summary
