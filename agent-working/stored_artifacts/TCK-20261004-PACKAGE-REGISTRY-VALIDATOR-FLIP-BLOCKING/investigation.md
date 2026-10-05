---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-PACKAGE-REGISTRY-VALIDATOR-FLIP-BLOCKING
artifact_type: investigation
tags: [architecture, delivery]
---

# Investigation — TCK-20261004-PACKAGE-REGISTRY-VALIDATOR-FLIP-BLOCKING

- `python3 -m codebase.structure.packages validate` has two problem classes: `schema` and `completeness`. Exit 1 for any problem, 2 if it could not run; `--schema-only` skips completeness.
- Tracked packages come from `git ls-files` (checkout in CI is full), with a directory fallback and a notice outside git; the fallback is why the live test runs the same code path as CI.
- Today the real-repo test asserts schema only, on purpose (module docstring): the module runs in the non-advisory tools lane, so a live completeness assertion would block before the soak ended. At the flip that is intended.
- The `Package registry` step has its own `continue-on-error`; after ticket 1 it and "Paths this PR changed" are the only tolerant steps of `code-health`.
- Check on `origin/main` 053f459e4 before the flip: `validate` exit status to be recorded in the ticket (expected 0).
