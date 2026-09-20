# Test Plan — TCK-20260919-AGENT-MONITORING-MANIFEST-REPRODUCIBILITY-CI-FAILURE

| Case | Verification |
|---|---|
| Corrected job-level CI history matches independently re-derived data | 6 direct `gh api .../jobs` calls, one per run ID, cross-checked against the peer's relayed correction — exact match on all 6 |
| No writer call site in the CI job's own test scope reaches the real corpus | Read every matching call site in `tests/api`, `tests/cli`, `tests/tools`, `tests/logging`, `tests/engine`, `tests/observability`; confirmed `tmp_path`/`monkeypatch.chdir`/explicit `cwd` isolation on every subprocess/`.main()` call, and validate-before-write ordering on the two `cwd=repo_root` exceptions |
| `writer.py` cannot shrink a file | Read `write_line`/`write_lines` source directly — both append-only (`"a"` mode / `O_APPEND` fd), no `truncate`/`seek`/`"w"` anywhere in the module |
| The failure does not reproduce hermetically (outside a live Claude Code session) | Cloned the merged branch tip outside any worktree, ran the exact CI command: 2942 passed, 0 failed |
| Fixed test passes in isolation | `pytest tests/tools/test_agent_monitoring_manifest.py -v`: 10 passed (8 original + 2 new `--dir`-flag tests) |
| Fix does not regress the surrounding suite | `pytest tests/tools/ -m "not slow and not extra_slow" -q`: 2746 passed, 25 skipped, 28 deselected, 1 xfailed, 0 failed |
| `--dir` flag defaults preserve existing behavior when omitted | `test_manifest_cli_no_dir_flag_still_defaults_to_the_real_corpus` — CLI output with no `--dir` matches `build_manifest(_REAL_AGENT_MONITORING_DIR)` directly |
| `--dir` flag is actually honored, not a no-op | `test_manifest_cli_dir_flag_scans_the_given_directory_not_the_real_one` — a synthetic single-shard corpus in `tmp_path`, CLI output reflects only that shard's line count and byte size |
| `test_manifest_run_against_real_corpus_produces_zero_diff` unaffected | Left untouched; still passes as part of the 10/10 file run and the 2746-pass suite run — its own assertion (zero mutation across a single `build_manifest()` call) was never the fragile one |

Executed: `pytest tests/tools/test_agent_monitoring_manifest.py -v` (10 passed) and
`pytest tests/tools/ -m "not slow and not extra_slow" -q` (2746 passed, 0 failed), both against
`.venv313` (Python 3.13.14, CI-matching).
