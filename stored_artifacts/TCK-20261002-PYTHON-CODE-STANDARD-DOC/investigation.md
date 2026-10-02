---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20261002-PYTHON-CODE-STANDARD-DOC
artifact_type: investigation
tags: [documentation, investigation]
---

# Investigation — TCK-20261002-PYTHON-CODE-STANDARD-DOC

## Context scan

- `search_docs` ("Python code standard: function length, complexity thresholds, naming, typing,
  docstrings, error handling"): top hit is `docs/engine/architecture_reference.md` section 9. No
  existing Python code standard, lint guide or size-threshold doc. `docs/audits/D13_type_safety.md`
  holds the typing measurements. No duplicate work.
- `graphify query` (run in the main checkout; this worktree has no `graphify-out/`): only
  code nodes citing `docs/guidelines/design_patterns.md` Pattern 6. Nothing relevant to a code
  standard.

## Findings

1. **No standard exists.** `docs/guidelines/` has `design_patterns.md` (extension points) and
   `repo_tooling_layout.md`, nothing on function/class craft.
2. **`architecture_reference.md` section 9** has three subsections: 9.1 name by domain meaning,
   9.2 small explicit data transformations, 9.3 architectural comments. It has no Python identifier
   conventions (case, private prefix, module names). The ticket leaves open which naming rules are
   new versus cited. Decision: the standard cites section 9 for domain naming and comment style,
   and adds PEP 8 identifier case as new rules, since nothing else in the repo states them.
3. **`design_patterns.md`** defines Patterns 1 to 6 plus legacy V1 patterns. The standard cites it
   by path for extension points and reproduces none of it.
   `tests/docs/test_design_patterns_currency.py` pins that file; it is not edited.
4. **Tooling that exists today:** only mypy. `[tool.mypy]` in `pyproject.toml` is non-strict,
   targets 3.11 and excludes five packages; `make typecheck-py` and the CI `typecheck` job both run
   it with `|| true`, so it never fails. No ruff, complexipy, jscpd or line-count script is
   configured. Every tool marker in the standard is therefore "planned", and the mypy marker says
   "advisory today".
5. **Ownership doc.** `tests/docs/test_subsystem_ownership_lifecycle_doc.py` requires every data
   row's role cell to be one of three hardcoded roles and every role used to appear in the
   vocabulary section. The new row uses `Documentation Governance Maintainer`. The test does not
   count rows, so adding one row is safe. The row must sit between the `## Ownership & Lifecycle
   Table` and `## Excluded Subsystems` headings.
6. **Plans tracking.** The Scope paragraph says "97 Markdown files as 37 plan records". The
   inventory table already has 38 rows, so the stated record count was off by one before this
   ticket. A full re-audit is out of scope; the counts are incremented by what this row adds
   (2 files, 1 record) to 99 and 38, and the Date line says they were incremented, not re-audited.
7. **Threshold-to-tool mapping** (roadmap 6.1 and 6.2). Ruff rule codes are named as the intended
   enforcement but have never been run on this repo; `TCK-20261002-CODE-HEALTH-TOOL-CONFIG`
   confirms or replaces them. The nesting-depth rule (`PLR1702`) is a ruff preview rule.

## Conflicts

None. No mechanics, engine contract or parity ledger entry is touched; this is docs only.
