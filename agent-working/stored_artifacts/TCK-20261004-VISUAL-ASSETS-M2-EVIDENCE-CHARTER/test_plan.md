---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-M2-EVIDENCE-CHARTER
artifact_type: test_plan
tags: [architecture, documentation, testing]
---

# Test Plan — TCK-20261004-VISUAL-ASSETS-M2-EVIDENCE-CHARTER

Docs-only; nothing was run for record (the charter forbids it). Checks:

1. Every backticked path and every named test or symbol in `m2_evidence_charter.md` exists on the branch (path existence; names found in the cited file, or by `def` search under `tests/`).
2. The register regenerates and all its evidence entries resolve (scratch `check_register.py`, not committed), including the new doc's headings.
3. `tools/validate_frontmatter.py`; `pytest tests/docs tests/static`; `make knowledge-index-update`.
4. `git diff --name-only 2a2dbc78e HEAD` touches only `docs/` and `agent-working/`.

## Results

See the ticket's Test Summary.

## Proof Plan

- **Level:** docs-only, resolver script.
- **Proof kind:** reference resolution plus the existing docs and static suites.
- **Oracle source:** the branch tree (paths, test names, headings).
- **Expected effect:** every citation resolves; a broken one is reported.
- **Selected commands:** scratch `check_register.py`; `pytest tests/docs tests/static`; `tools/validate_frontmatter.py`.
