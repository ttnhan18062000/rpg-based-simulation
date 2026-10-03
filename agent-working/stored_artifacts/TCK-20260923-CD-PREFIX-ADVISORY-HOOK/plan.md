# Plan — TCK-20260923-CD-PREFIX-ADVISORY-HOOK

## Steps
1. `tools/agent-monitoring/cd_prefix_advisory_hook.py`: pure `detect_redundant_cd_prefix(command,
   current_dir) -> str | None` (exact normalized-path equality only, per investigation.md's design
   decision), plus a thin `main()` CLI wrapper reading `{"tool_input": {"command": ...}, "cwd":
   ...}` from stdin, wrapped in try/except so a hook failure never blocks the Bash call it advises
   on, printing a `hookSpecificOutput.additionalContext` line (never a `decision`/block field) only
   when triggered.
2. Wire into `.claude/settings.json`'s `PreToolUse` → `Bash` matcher list (new entry, alongside
   the existing graphify/secret-scan Bash-matcher hooks), invoking the module directly (mirrors
   `pre_tool_hook.py`/`post_tool_hook.py`'s own `python3 tools/agent-monitoring/*.py 2>/dev/null
   || true` shape, not an inline one-liner, since the detection logic needed a real function to be
   independently testable).
3. Tests: `tests/tools/test_cd_prefix_advisory_hook.py` — unit tests for the pure detector (both
   "must flag" and "must NOT flag a genuine directory switch" groups), CLI subprocess tests
   (hookSpecificOutput shape, silent on non-match, fail-open on malformed stdin).
4. Manual end-to-end verification: pipe a realistic stdin payload through the wired module,
   confirm it fires only for the exact redundant case; validate `.claude/settings.json` remains
   parseable JSON after the edit.

## Explicitly not doing
- **Not** flagging every `cd` call, or any heuristic broader than exact-path-match — the 21.5%
  figure is a call-count share, not a waste count; most `cd` calls (worktree switches, subproject
  entry) are legitimate and must never be second-guessed. See investigation.md's design decision.
- **Not** blocking or modifying the Bash call in any way — advisory-only per this batch's explicit,
  non-negotiable constraint (`[[feedback_agent_tooling_checks_proportionate]]`); no hook here may
  fail or gate a tool call.
- **Not** measuring the hook's own effect within this ticket — ticket 1's `bash_command_mix.py`
  (with `--ref` pinning from the follow-up hotfix) is the standing before/after instrument; this
  ticket ships the nudge, not a self-contained before/after study.

## Acceptance-criteria map
- "Advisory (never blocking) PreToolUse hook... to kill the `cd <path> &&` prefix habit" →
  `cd_prefix_advisory_hook.py` + `.claude/settings.json` wiring.
- "Follow the existing sidecar-check hook's advisory shape" → same `hookSpecificOutput.
  additionalContext`-only shape, no `decision` field, wrapped fail-open.
- Tested, no false positives on legitimate directory switches → 15 tests, including 3 explicit
  "must NOT flag" cases (different directory, subdirectory, sibling worktree).
