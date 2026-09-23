# Test Plan — TCK-20260923-CD-PREFIX-ADVISORY-HOOK

## New tests (`tests/tools/test_cd_prefix_advisory_hook.py`)
1. `test_flags_cd_into_the_exact_current_directory` — normal flow, the core detection.
2. `test_flags_cd_with_trailing_slash_normalized` — edge case (path normalization).
3. `test_flags_quoted_cd_target` — edge case (quoted path argument).
4. `test_flags_relative_dot_target_matching_current_dir` — edge case (`cd .`).
5. `test_does_not_flag_cd_into_a_different_directory` — failure-mode guard: must not over-fire.
6. `test_does_not_flag_cd_into_a_subdirectory` — failure-mode guard.
7. `test_does_not_flag_cd_into_a_worktree` — failure-mode guard, the specific legitimate case this
   repo's own worktree-per-ticket convention relies on.
8. `test_does_not_flag_command_with_no_cd_prefix` — normal flow, no match.
9. `test_does_not_flag_bare_cd_with_no_chained_command` — edge case (no `&&`).
10. `test_does_not_flag_cd_that_is_not_the_leading_token` — edge case (cd mid-chain).
11. `test_empty_command_does_not_crash` — edge case.
12. `test_handles_tilde_expansion` — normal flow, `~` expansion.
13. `test_cli_emits_hook_specific_output_for_redundant_cd` — CLI integration, output shape.
14. `test_cli_prints_nothing_for_non_matching_command` — CLI integration, silent path.
15. `test_cli_fails_open_on_malformed_stdin` — failure mode: malformed input must never crash or
    block the tool call the hook is advising on.

## Regression scope
- `pytest tests/tools/test_cd_prefix_advisory_hook.py -v` (new, 15 tests).
- `python3 -c "import json; json.load(open('.claude/settings.json'))"` — settings.json remains
  valid JSON after the new hook entry.
- Manual end-to-end: pipe a realistic PreToolUse stdin payload through the wired module directly
  (not just the pure function in isolation), confirming the full path (stdin parse → detection →
  hookSpecificOutput print) works as the harness will actually invoke it.
- Not the full suite — scoped per CLAUDE.md's Testing Rule; this ticket touches no `src/` code.

## Coverage check
Normal flow: the core redundant-cd detection, quoted/tilde/dot path variants. Edge cases: no `cd`
prefix, bare `cd` with no chain, `cd` mid-chain, empty command. Failure modes: three explicit
must-not-flag cases (the real risk for an advisory hook is false positives eroding trust), fail-open
on malformed stdin. Regression-prone paths: none introduced (no existing code modified besides the
additive `.claude/settings.json` hook-list entry).
