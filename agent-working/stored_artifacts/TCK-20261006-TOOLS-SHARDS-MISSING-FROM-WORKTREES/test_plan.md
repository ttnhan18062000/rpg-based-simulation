# Test Plan — TCK-20261006-TOOLS-SHARDS-MISSING-FROM-WORKTREES

`tests/tools/test_monitoring_hook_subdirectory_cwd.py`: the five settings.json commands resolve the top level and `cd` into it;
the real post_tool_hook command, run in a throwaway detached worktree from the root, `docs/` and `tools/agent-monitoring/`,
writes exactly one tools row and leaves no stray `agent-working/` or `.claude/` under the subdirectory.
`tests/tools/test_settings_permission_rules.py` and every other test that reads settings.json still pass.
