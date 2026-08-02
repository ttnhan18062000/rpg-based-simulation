---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260801-CODEX-LIVE-TRANSPORT
phase: done
date: 2026-08-01
tags: [ai, security, testing]
---

# TCK-20260801-CODEX-LIVE-TRANSPORT

## Title
Build the reviewed non-exercised Codex live-transport capability

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Build the first narrowly bounded transport capable of constructing a real
`codex exec` invocation only through the existing real-repository harness's
dual-authority and immutable-preflight boundary. The capability must be fully
testable without live Codex access and remain unexercised in this ticket. It is
not authorization to run a pilot, enable a hook, alter project configuration,
or write provider-attributed monitoring data.

## Scope
- Design and add a contained real-repository Codex transport/invoker that is
  reachable only through the harness's reviewed authority/preflight boundary.
- Reuse the harness's preflight, expected-write proof, containment, and rollback
  primitives rather than duplicate their logic.
- Add default-safe tests, including an explicitly requested real-invocation
  fixture that skips—not fails—when the Codex CLI or fresh test consent is absent.
- Add static tests proving no forbidden bypass flags, hook registration, or
  unguarded real invocation path.

## Out of Scope
- Exercising any real Codex invocation during implementation, tests, review, or
  this ticket's closure.
- Hook registration, `.codex/config.toml` changes, or a `provider="codex"`
  monitoring write.
- Implementing or modifying `TCK-20260801-MONITORING-WRITER-STATUS-STALE`.
- Changing either blocked activation ticket or authorizing the controlled pilot.
- Reimplementing harness authority, containment, baseline, policy, expected-write,
  monitoring-suffix, or rollback logic in the new transport.

## Acceptance Criteria
- [x] The transport can construct a constrained `codex exec` request only after
      a separately reviewed real-root preflight result and dual authority; no
      caller-supplied raw root bypass exists.
- [x] Tests prove refusal before subprocess construction for missing/invalid
      authority or preflight evidence, re-check both exact consent values at the
      invocation seam, and reject dangerous bypass flags.
- [x] A private real-root live-preflight factory is the only sanctioned constructor
      for the live capability; AST coverage proves no other source path constructs
      it, and the transport accepts no caller-supplied root or prompt text.
- [x] Default test runs make zero real Codex calls. Any test that would exercise
      a real call is opt-in and skips cleanly when the CLI or fresh test consent
      is unavailable.
- [x] The implementation reuses the harness proof/containment primitives and
      introduces no duplicate expected-write or rollback implementation.
- [x] No hook/config/candidate/blocked-ticket/provider-monitoring mutation occurs.
- [x] Architecture Review approves the plan and independently approves the actual
      diff before the ticket can proceed to Verify/Finalize.

## Related Tickets
- TCK-20260801-CODEX-REALREPO-HARNESS-PARITY-ADDENDUM (DONE)
- TCK-20260801-CODEX-REALREPO-PILOT-HARNESS (DONE; reuse boundary/primitives)
- TCK-20260730-CODEX-CONTROLLED-PILOT (BLOCKED; not modified here)
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC (BLOCKED; not modified here)

## Related Docs
- docs/plans/agent_infrastructure/codex_live_transport_ticket_authorization_claude.md
- docs/plans/agent_infrastructure/codex_blocked_activation_next_steps_answer_claude.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260801-CODEX-REALREPO-PILOT-HARNESS/

## Related Code Areas
- tools/agent_codex_realrepo_pilot_harness/boundary.py
- tools/agent_codex_realrepo_pilot_harness/preflight.py
- tools/agent_codex_realrepo_pilot_harness/proofs.py
- tools/agent_codex_realrepo_pilot_harness/rollback.py
- tools/agent_replay_codex/invoker.py
- tests/agent_replay_codex/conftest.py

## Assumptions / Open Questions
- The transport's consent naming and how a separately reviewed live preflight
  produces real-root-bound evidence are architecture decisions for this ticket.
- The fresh live pilot decision remains outside this ticket even after the
  capability is complete.

## Implementation Notes
- Added `tools/agent_codex_live_transport/` as the sole new fixed-argv subprocess
  seam and `live_preflight.py` as the private real-root capability factory.
- `ordinary_preflight` remains scratch-only and continues to refuse the project
  root. Shared evidence capture was factored into a private helper; the live factory
  uses it only after canonical-root admission.
- The transport has no root/prompt/options parameters. Its first invocation
  operation re-checks both existing exact consent gates, then it requires the
  earlier authority object and typed live-preflight capability.
- The non-autouse opt-in fixture reuses `CODEX_REALREPO_PILOT_LIVE_CONSENT` and is
  intentionally unrequested; it cannot trigger a real call in this ticket.
- Claude independently approved the actual diff and subsequent direct
  `_admit_live_root` negative-path coverage. Instruction evidence strings are
  JSON-escaped so control characters cannot forge additional fixed-template lines.

## Test Summary
- `.venv/bin/python -m pytest tests/agent_codex_live_transport
  tests/agent_codex_realrepo_pilot_harness tests/agent_replay_codex
  --import-mode=importlib -q`: **63 passed, 5 skipped**. Skips are existing opt-in
  replay tests; no test requested the new live fixture or invoked Codex.
- Wider protected scope: **258 passed, 5 skipped, 4 failed**. The four failures are
  the known unrelated runtime-shadow workflow-version-1 fixture mismatch; no new
  transport/harness/replay/guardrail/executor/posttool/monitoring failure occurred.

## Files Changed
- tools/agent_codex_realrepo_pilot_harness/preflight.py
- tools/agent_codex_realrepo_pilot_harness/live_preflight.py
- tools/agent_codex_realrepo_pilot_harness/boundary.py
- tools/agent_codex_live_transport/__init__.py
- tools/agent_codex_live_transport/invoker.py
- tests/agent_codex_live_transport/

## Completion Summary

Implemented and verified the non-exercised fixed-argv live-transport capability.
The future controlled pilot remains separately blocked: this ticket neither ran
Codex nor activated hooks/configuration, consumed the reserved candidate, changed
blocked activation tickets, or wrote provider-attributed monitoring.
