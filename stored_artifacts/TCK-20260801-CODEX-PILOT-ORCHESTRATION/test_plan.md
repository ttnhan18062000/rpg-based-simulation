---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260801-CODEX-PILOT-ORCHESTRATION
artifact_type: test_plan
tags: [ai, security, workflows, hooks, agent-monitoring, rollback, testing]
---

# Test plan — TCK-20260801-CODEX-PILOT-ORCHESTRATION

## New tests required

1. Private production-adapter factory rejects raw roots, scratch/ordinary
   preflight, mismatched context/baseline evidence, non-canonical config paths,
   missing config, and symlinked escape paths before any file write.
2. Enable accepts only the fixed approved PostToolUse block, captures original
   bytes once, and refuses wider events, writer names, duplicate/unrecognized
   fragments, or a mismatched execution identity.
3. `enable()` rechecks both exact consent gates immediately before I/O; missing,
   stale, or truthy-but-not-`"1"` values leave the injected config bytes unchanged.
   `restore()` deliberately does not recheck consent: it remains available to the
   owning identity when consent has been cleared or changed, so failure cleanup
   cannot strand an enabled hook.
4. Restore is ownership-bound and exact-byte. A second restore by the same owner is
   a safe no-op after successful restoration; a different identity is refused.
   Verification detects a one-byte mismatch or any changed non-config file in its
   injected rollback scope.
5. Orchestration uses the exact sequence: live preflight -> authority -> config
   enable -> transport -> captured post-run proof -> restore/verify. Fake injected
   transport/proof functions prove no duplication and verify rollback after every
   transport/proof failure path. The captured policy must explicitly allow only the
   transient config path, and an altered config is rejected before proof/rollback.
6. Static AST/source tests prove no caller-controlled root/prompt/options/fragment,
   no extra consent variable, no dangerous bypass flag, no direct monitoring writer,
   and no source/test path targets the real `.codex/config.toml` for mutation.
7. Regression tests retain scratch adapter project-root refusal, live transport
   fixed-argv behavior, and hook-surface policy validation.

## Commands

```bash
.venv/bin/python -m pytest \
  tests/agent_codex_pilot_orchestration \
  tests/agent_codex_realrepo_pilot_harness \
  tests/agent_codex_live_transport \
  tests/agent_codex_pilot_guardrails \
  tests/agent_codex_posttool_adapter \
  --import-mode=importlib -q
```

The final protected scope may include monitoring writer and runtime-shadow tests.
Known runtime-shadow fixture-version failures, if still present, must be reported
separately and never normalized as a new orchestration failure.
