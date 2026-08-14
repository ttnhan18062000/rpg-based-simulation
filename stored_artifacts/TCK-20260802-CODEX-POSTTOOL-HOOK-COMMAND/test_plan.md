---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260802-CODEX-POSTTOOL-HOOK-COMMAND
artifact_type: test_plan
tags: [ai, security, workflows, hooks, agent-monitoring, rollback, testing]
---

# Test Plan

## Regression Surface

- `tests/agent_codex_posttool_adapter/` — payload validation, redaction, strict append gate,
  fail-open behavior, writer bridge, and evidenced surface.
- `tests/agent_codex_live_transport/` — fixed argv, fresh consent ordering, real-root refusal,
  and no unreviewed runner surface.
- `tests/agent_codex_pilot_orchestration/` and
  `tests/agent_codex_realrepo_pilot_harness/` — policy and exact suffix proof behavior.

## New Tests Required

- CLI/entrypoint test with JSON stdin and a scratch `tools.jsonl`: valid fixture invokes the
  adapter once and exits zero; invalid JSON, non-object JSON, absent or malformed environment
  identity, append-gate refusal, and writer exception also exit zero and append nothing.
- Identity precedence test: every identity-like hook payload field is ignored; output identity
  comes solely from the reviewed environment values.
- Static command boundary test: no shell interpolation, no arbitrary target path, no caller
  selected provider/candidate, and only the approved adapter composition point is called.
- Transport test: subprocess receives copied environment plus a fixed allowlisted identity bundle;
  conflicting ambient identity values are overwritten only by internally derived values; all three
  ambient consent values are inherited byte-for-byte; and callers cannot provide arbitrary
  environment entries.
- Bounded tools-only proof tests: zero rows; valid rows with matching identity/gap-free seq/window;
  wrong known field; seq starting above one/gap/repeat; count above policy cap; timestamp before or
  after transport bounds; and prefix alteration/reordering/extra unbound rows. Existing
  `assert_post_run_proof` exact-suffix tests remain untouched and must still pass.
- Static config-command rendering test: proposed bytes use absolute `.venv/bin/python3` and
  absolute `hook_entry.py`, never bare `python3`, `PATH`, shell interpolation, or untrusted args.
- Static containment scan proving production config, candidate, blocked tickets, and real
  monitoring paths remain absent from test writes and that no `codex` executable is run.

## Scoped Pytest Commands

```bash
.venv/bin/python -m pytest tests/agent_codex_posttool_adapter tests/agent_codex_live_transport tests/agent_codex_pilot_orchestration tests/agent_codex_realrepo_pilot_harness --import-mode=importlib -q
```

## Anti-Drift Test Guards

- Tests use `tmp_path`, synthetic environment maps, `monkeypatch`, and mocked `subprocess.run`.
- No test supplies real consent environment variables to a real subprocess or writes a provider
  record outside scratch storage.
- Tests preserve the adapter's fail-open exit behavior and strict equality for every gate.
- Tests do not set any consent variable through transport code; values are injected only as test
  fixtures to prove inherited-independent-gate behavior.
