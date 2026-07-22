"""Claude-adapter conformance tooling for the agent-orchestration/ contract.

Kept as a fresh package, structurally separate from tools/agent_orchestration/ (owned by
TCK-20260721-ORCHESTRATION-CONTRACT-CORE): this package only reads that package's
`load_contract()` output read-only, never edits `tools/agent_orchestration/{loader.py,generator.py}`
or any of agent-orchestration/'s original six contract files.

Built by TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER. Renders a read-only Claude-shaped projection of
the contract and cross-checks it against the live Claude workflow source file under
`.claude/workflows/` — never opens that file in write mode, never subprocesses it. This package's
own source deliberately never spells out that file's name as a literal string constant anywhere
(including comments/docstrings) — see
tests/agent_orchestration_claude_adapter/test_no_forbidden_calls_against_implement_ticket_js.py's
whole-file string-constant scan, which enforces this; callers always pass the path in explicitly.
"""
