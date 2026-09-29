# Plan — TCK-20260929-TOOLS-ORPHAN-FILE-CHECK

1. Write `tools/gate_checks/tools_orphan_check.py`: `IDENT_RE`, `CODEX_SUBTREE_PREFIXES`,
   `IGNORED_REFERENCE_PREFIXES`, `git_ls_tracked_files`, `build_token_index`, `_classify`,
   `check_tools_orphans`, `__main__` (always exit 0).
2. Verify against the real corpus directly (timing + spot-check the 4 buckets) before writing
   tests, to catch design issues early (caught the codex-content-exclusion gap this way).
3. Add the Makefile target (`tools-orphan-check`, help text ending
   `(on-demand only — not CI)`) + `.PHONY` entry.
4. Write `tests/tools/test_tools_orphan_check.py`: the 5 tmp_path cases (a-e) plus determinism,
   `__init__.py`/`__pycache__`/codex-exclusion, Makefile-wiring (pure text), no-`.github/workflows`
   reference, and a real-corpus structure-only test with a 60s timeout guard.
5. Re-run the module standalone to confirm no working-tree side effects from a real invocation.

## Scope guards
- No CI wiring, no ratchet/baseline, no non-zero exit on findings (explicit ticket requirement).
- Does not delete/move any flagged file — dispositions stay a separate human decision.
- Does not import `tools/audit_unreachable_code.py` or reuse `tools/code_test_index.py`.
- Does not scan Codex subtree file *contents* (only lists them in the `excluded` bucket).
- Does not regroup the flat top-level `tools/*.py` files.
- No CLAUDE.md edit.

## Acceptance-criteria map
Every AC maps 1:1 to a test in `test_tools_orphan_check.py` or a direct manual verification
(MARKER: line format + exit 0, checked via direct invocation and `make tools-orphan-check`).
