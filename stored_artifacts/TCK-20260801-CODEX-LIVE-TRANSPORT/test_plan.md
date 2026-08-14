---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260801-CODEX-LIVE-TRANSPORT
artifact_type: test_plan
tags: [ai, security, testing]
---

# Test plan — TCK-20260801-CODEX-LIVE-TRANSPORT

## Default-safe unit and structural coverage

1. A missing, malformed, or ordinary/scratch preflight object is refused before
   any subprocess object/command is constructed.
2. Missing, truthy-but-not-`"1"`, or one-of-two authority gates is refused before
   construction; only the existing dual-authority capability can reach the
   transport seam.
3. The transport accepts only a reviewed live-preflight capability and passes only
   its validated canonical root to the internal command builder.
4. Command construction uses a fixed argument vector, has no shell mode, rejects
   caller-provided executable/options/prompt fragments, and never contains
   `--dangerously-bypass-approvals-and-sandbox` or
   `--dangerously-bypass-hook-trust`.
5. Static AST tests prove the transport is the only new subprocess seam and neither
   it nor its tests import/write hook registration, project config, monitoring
   recorders, or candidate-ticket mutators.
6. Existing harness tests remain passing and prove policy/containment/post-run proof
   behavior remains delegated, not duplicated.

## Opt-in real-invocation fixture

Add a non-autouse, session-scoped fixture mirroring
`tests/agent_replay_codex/conftest.py::real_codex_replay`:

- skip if `shutil.which("codex")` is absent;
- skip if the existing `CODEX_REALREPO_PILOT_LIVE_CONSENT` variable is not
  exactly `"1"`; do not introduce a test-only third consent variable;
- skip without constructing a command or reading a real root;
- only a separately marked/explicit test may request it.

Default `pytest` for the new package must pass with zero skips or clean skips and
zero real invocation. This ticket will not set the test-consent variable or request
the fixture in CI/default local verification.

## Regression command candidates

```bash
.venv/bin/python -m pytest \
  tests/agent_codex_live_transport \
  tests/agent_codex_realrepo_pilot_harness \
  tests/agent_replay_codex \
  --import-mode=importlib -q
```

The final scoped command may expand after implementation, but it must distinguish
the known unrelated runtime-shadow fixture-version failures from any new transport
failure.
