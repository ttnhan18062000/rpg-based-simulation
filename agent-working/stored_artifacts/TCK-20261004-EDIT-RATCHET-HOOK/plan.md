---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-EDIT-RATCHET-HOOK
artifact_type: plan
tags: [architecture, hooks]
---

# Plan — TCK-20261004-EDIT-RATCHET-HOOK

## Approach
`staged_ratchet.check(root, files)` already is the shared function (staged file list in, `RatchetResult` or `HookSkipped` out). The hook reuses it; no second comparison is written. The refactor is small and behaviour-preserving:
- `_ruff_json` and `check` gain two keyword-only parameters with defaults that keep today's behaviour: `timeout: float | None = None` (passed to `subprocess.run`; `TimeoutExpired` becomes `HookSkipped`) and `python: str = sys.executable`.
- The `find_spec("ruff")` guard stays for the default interpreter; when `python` is given the guard is skipped and a ruff failure surfaces as `HookSkipped` through the existing exit-code branch.

New `codebase/hooks/edit_ratchet_hook.py` (stdlib plus `codebase.gates.staged_ratchet`):
1. Read stdin JSON; anything malformed, a tool other than Edit/Write/MultiEdit, or no `tool_input.file_path`: print nothing.
2. Resolve the path; require it inside the repo root, ending `.py`, an existing file under `src/`; relativize to `src/...`.
3. Interpreter: `<root>/.venv/bin/python3` if it exists (system `python3` lacks the lint group, so a bare `python3` would skip silently every time), else `sys.executable`.
4. `check(root, [rel], timeout=5, python=...)`. On NEW/WORSE print one JSON object `{"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": <text>}}`; text = `ratchet.format_report` capped at 20 lines plus "... and N more", plus one line pointing at the standard's rule IDs. Pass or any skip: print nothing.
5. `main()` wraps everything in `try/except Exception` and always `return 0`.
Settings entry (after owner confirms the literal diff): one new PostToolUse group `{"matcher": "Edit|Write|MultiEdit", "hooks": [{"type": "command", "command": "python3 -m codebase.hooks.edit_ratchet_hook 2>/dev/null || true"}]}` appended at the end of the PostToolUse list, so no existing index shifts (the wiring test indexes `PreToolUse[3]`; PostToolUse indices are not pinned but appending is safest).

## Steps
1. Parameterize `staged_ratchet` (tests first: existing staged-ratchet tests unchanged).
2. Write the hook and `tests/codebase/test_edit_ratchet_hook.py`.
3. Docs: `codebase/README.md` hooks row, standard Section 2 sentence, `agent_working_environment.md` only if it lists Claude Code hooks (it lists git hooks; will check, likely add one sentence).
4. Wiring: extend `tests/tools/test_settings_json_hooks_wiring.py` with a test for the new entry (matcher, command text, `|| true`, appended last); check `hook-surface-policy.yaml` (it lists events, not commands: PostToolUse is already enabled, so likely no change).
5. AskUserQuestion with the literal settings.json diff; commit only after yes. Until then the code commit excludes settings.json.
6. Capability envelope: record the finding below in the ticket and the planner outbox.

## Capability-envelope finding (already checked, no schema change)
`tools/capability_envelope_baseline.py` audits only `.claude/settings.local.json` and 4 fields (`permissions.allow` plus 3 MCP fields). It does not read `hooks` and does not read `settings.json`. So there is no row to add; this is a finding for agent-working, recorded in the ticket and outbox. Roadmap 5.8's "new hooks must be added there" cannot be met without extending the schema, which is out of scope.

## Scope guards
No `src/`, `tools/`, or other-domain test edits except extending `tests/tools/test_settings_json_hooks_wiring.py` (additive). Nothing blocking; hook exits 0 always.

## Acceptance-criteria map
Exit 0 and silent on pass: step 2 tests. Owner diff: step 5. Wiring test: step 4. Envelope result: step 6. Pre-commit unchanged: step 1. No src diff: `git diff --stat`.

## Open choices (defaults taken)
- Venv interpreter preference (item 3) is my addition to the brief; it is the only way the hook can work in this repo's normal setup.
- Output cap 20 lines.
