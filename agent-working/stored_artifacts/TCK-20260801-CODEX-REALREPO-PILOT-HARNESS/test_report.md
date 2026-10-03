---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260801-CODEX-REALREPO-PILOT-HARNESS
artifact_type: test_plan
---

# Test report — TCK-20260801-CODEX-REALREPO-PILOT-HARNESS

## Focused harness

`.venv/bin/python -m pytest tests/agent_codex_realrepo_pilot_harness --import-mode=importlib -q`

Result: **29 passed**.

This includes the real-worktree session snapshot guard. All mutable fixtures use
pytest `tmp_path` scratch roots; no test invokes Codex, constructs a subprocess,
registers a hook, changes project config, or writes provider-attributed project
monitoring.

## Regression scopes

Harness plus executor:

`.venv/bin/python -m pytest tests/agent_codex_realrepo_pilot_harness tests/agent_codex_pilot_executor --import-mode=importlib -q`

Result: **50 passed**.

Exact command from `test_plan.md`:

`.venv/bin/python -m pytest tests/agent_codex_realrepo_pilot_harness tests/agent_codex_pilot_guardrails tests/agent_codex_pilot_executor tests/agent_replay_codex tests/agent_codex_runtime_shadow tests/agent_codex_posttool_adapter tests/tools/test_monitoring_writer.py tests/tools/test_agent_monitoring_manifest.py tests/tools/test_agent_ops_dashboard_ingest.py --import-mode=importlib -q`

Result: **246 passed, 5 skipped, 4 failed**.

The four failures are known pre-existing `agent_codex_runtime_shadow` fixture
expectations for `workflow_version: 1`; the shared workflow contract is already
version 2 due to the previously approved continuation-policy ticket. They are
outside this ticket's scope and do not involve the harness package.

Claude's Architecture-Verify re-review separately ran a superset that included
both orchestration adapters: **311 passed, 5 skipped, 6 failed**. Its two
additional known failures are stale hard-coded line numbers in Claude-adapter
terminal-status extraction tests. No harness regression was found.

## Required test cleanup

The Architecture re-review identified a stale positional invocation in
`test_invoker_is_not_constructed_until_dual_authority_exists`. It was corrected
to the current `(authority, preflight, invoker)` signature, then the focused
suite was re-run with the 29-pass result above.
