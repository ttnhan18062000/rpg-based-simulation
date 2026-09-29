# Test Plan — TCK-20260929-TOOLS-ORPHAN-FILE-CHECK

Derived directly from the ticket's Acceptance Criteria; all implemented in
`tests/tools/test_tools_orphan_check.py`.

1. Direct invocation (`python3 tools/gate_checks/tools_orphan_check.py`): exactly one stdout
   line starting with `MARKER:` followed by valid JSON; exit code 0.
2. Real-corpus structure test: every result has exactly the keys `{file, status, evidence}`,
   `status` in the 5 valid values, `file` under `tools/`, never `__init__.py`/`__pycache__`;
   `excluded` results are exactly the Codex-subtree files with empty evidence; no duplicate
   files. Never asserts specific counts (they shift over time, per the ticket's own Assumptions).
3. tmp_path (a): a `tools/` file referenced only by a bare-stem sibling import in another
   `tools/` file -> `LIVE`.
4. tmp_path (b): a `tools/` file referenced only from `tests/` -> `TEST_ONLY`.
5. tmp_path (c): `tools/test_docker.py` is NOT matched by a longer identifier containing
   "test_docker" as a substring (word-boundary tokens, not substring search).
6. tmp_path (d): references located only in `tickets/done/`, `docs/archive/`, or
   `stored_artifacts/` are ignored -> `NO_REFERENCES`.
7. tmp_path (e): a reference from the Makefile, or from `.claude/settings.json`, makes the file
   `LIVE` (two separate cases, one per entrypoint kind).
8. `__init__.py` and `__pycache__/` files never appear in results; Codex subtree files appear
   only in `excluded`, and `is_codex_subtree` is exact-prefix (not a loose substring match —
   `tools/agent_replay/` itself is NOT excluded, only `tools/agent_replay_<x>/`).
9. Two consecutive runs against the same tree produce byte-identical JSON, and the tree's files
   are unmodified byte-for-byte afterwards.
10. Makefile wiring: `tools-orphan-check:` target exists, references `tools_orphan_check.py`,
    its help text contains `(on-demand only — not CI)`, and it's listed on the `.PHONY` line
    (pure-text assertions, no subprocess).
11. No `.github/workflows/*.yml` file references `tools_orphan_check`.
12. Real-corpus run completes in well under the test's 60s guard (measured: ~2s, vs. the
    documented >300s per-tool-regex-scan failure mode this design avoids).
