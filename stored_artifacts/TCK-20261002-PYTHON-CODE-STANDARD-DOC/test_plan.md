---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20261002-PYTHON-CODE-STANDARD-DOC
artifact_type: test_plan
tags: [documentation, testing]
---

# Test Plan — TCK-20261002-PYTHON-CODE-STANDARD-DOC

Docs only; no behaviour changes, so no new test is added. Existing checks are run.

| Check | Command | Expected |
|---|---|---|
| Frontmatter | `python3 tools/validate_frontmatter.py` on the new doc, the ticket and the staging artifacts | pass |
| Ownership doc structure | `pytest tests/docs/test_subsystem_ownership_lifecycle_doc.py` (file unmodified) | pass |
| Docs suite, including `test_design_patterns_currency.py` | `pytest tests/docs/` | pass |
| Every rule marked | script: every data row in the standard's rule tables has a non-empty Enforcement cell that names a tool or `reviewer` | no unmarked row |
| Planned labelling | script: every Enforcement cell naming ruff, complexipy, jscpd or the line-count script contains "planned" | no unlabelled cell |
| Diff scope | `git diff --stat 7dfd1349` | no `src/`, `tests/`, `.claude/`, `CLAUDE.md` path |
| Plans link resolves | the linked roadmap path exists relative to `docs/plans/` | exists |

Failure mode covered: a role outside the vocabulary or a row with an empty cell fails the
ownership test. Regression-prone path: `test_three_existing_ownership_docs_unmodified` uses
`git diff HEAD`, so it is run before and after commit.
