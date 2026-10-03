---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-TEST-ARCH-MAINT-MUTATION-BASELINE-METHOD-DOC
artifact_type: test_plan
tags: [testing]
---

# Test Plan — TCK-20261003-TEST-ARCH-MAINT-MUTATION-BASELINE-METHOD-DOC

Docs only; no behavior changes, so no new pytest case (and `tests/` must not change). Verification:

1. `python3 tools/validate_frontmatter.py --content-type doc docs/testing/mutation_baseline_method.md` passes.
2. Every SHA, count and path quoted in the doc is re-read against its source file (baseline JSON, report,
   `git cat-file -e` for each full SHA).
3. Existing doc/registry tests that cover `docs/` stay green (docs registry, frontmatter corpus, link checks
   where they exist), scoped by the test-scoper to the changed files.
4. `make knowledge-index-update` runs; `docs/REGISTRY.yaml` regenerated and staged.
5. Gate: `git diff --name-only origin/main...HEAD` lists no `tests/`, `src/` or `docs/parity_ledger/` path.
