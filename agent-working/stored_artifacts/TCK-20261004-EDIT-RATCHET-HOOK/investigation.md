---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-EDIT-RATCHET-HOOK
artifact_type: investigation
tags: [architecture, hooks]
---

# Investigation — TCK-20261004-EDIT-RATCHET-HOOK

- `codebase/gates/staged_ratchet.py::check(root, files, registry_file=None)` already returns a `RatchetResult` or raises `HookSkipped`; `run()` prints the report and exits 1. The hook needs only a non-failing printer.
- `_ruff_json` uses `sys.executable -m ruff` and has no timeout.
- `.claude/settings.json` PostToolUse: `*` post_tool_hook, `Edit|Write|MultiEdit` graphify update, `*` retro nudge, `*` epic staleness. All end `|| true`.
- `tests/tools/test_settings_json_hooks_wiring.py` pins SubagentStop and PreToolUse[3]; it does not pin PostToolUse indices.
- `hook-surface-policy.yaml` lists events per provider (claude enabled: PreToolUse, PostToolUse, SubagentStop), not commands.
- Capability envelope audits `settings.local.json` only, 4 fields; no hooks coverage (see plan).
