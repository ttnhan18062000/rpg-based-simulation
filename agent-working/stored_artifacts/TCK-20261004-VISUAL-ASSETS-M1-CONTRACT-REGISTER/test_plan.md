---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-M1-CONTRACT-REGISTER
artifact_type: test_plan
tags: [architecture, documentation]
---

# Test Plan — TCK-20261004-VISUAL-ASSETS-M1-CONTRACT-REGISTER

Docs-only ticket: no code behaviour changes, so no new tests. Checks:

1. Every evidence entry resolves on the branch (doc headings by GitHub slug, ADR rows, `path::symbol` by definition search, test and file paths by existence). Scratch script `check_register.py` (not committed).
2. Negative control: three deliberately broken entries (a missing heading, a missing symbol) are reported as `UNRESOLVED`, so the check can fail.
3. Every clause of the plan's acceptance cells has exactly one row; summary counts are generated from the rows.
4. `tools/validate_frontmatter.py` on the new page, the ticket and these artifacts; docs and static tests scoped to `tests/docs`, `tests/static`; `make knowledge-index-update` after the docs change.
5. `git diff --name-only origin/main` shows nothing outside `docs/` and `agent-working/` (plus the regenerated `docs/REGISTRY.yaml` and monitoring shards).

## Results

Check 1 (run on the committed page): `checked 179 evidence entries` (178 before the W10 review fix), no `UNRESOLVED` line. Check 2: with a broken heading and a broken symbol the same script printed `UNRESOLVED W02.3 visual_assets/store/identities.py::NOPE_SYMBOL symbol missing` and `UNRESOLVED W12.4 docs/assets/store_contract.md#nope heading missing`, exit 1. Summary: 40 MET, 24 GAP, 4 N/A over 68 rows (W10.2 and W10.4 corrected in a review-fix commit; the first run read 40/23/5). Checks 4 and 5: see the ticket's Test Summary.

## Proof Plan

- **Level:** docs-only; checked by a resolver script, not unit tests.
- **Proof kind:** reference resolution with a negative control, plus the existing docs and static test suites.
- **Oracle source:** the branch tree itself (headings, ADR table rows, symbol definitions, file paths).
- **Expected effect:** every evidence entry in the register resolves; broken entries are reported and exit non-zero.
- **Selected commands:** scratch `check_register.py` (not committed); `pytest tests/docs tests/static tests/visual_assets/store/unit/test_docs_commands.py` under a 2 GB cap; `tools/validate_frontmatter.py`.
