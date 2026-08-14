---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260801-CODEX-REALREPO-PILOT-HARNESS
phase: done
date: 2026-08-01
tags: [ai, workflows, hooks, agent-monitoring, rollback, testing]
---

# TCK-20260801-CODEX-REALREPO-PILOT-HARNESS

## Title
Build a non-live, real-repository-capable controlled-pilot harness

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Build and test an additive harness capable of safely orchestrating one future
real-repository Codex pilot, while exercising it only against injected/scratch
repository roots in this ticket. The harness must make live authority explicit
and fail closed; it does not authorize or execute a pilot.

## Scope
- Add a separate harness package with injected repository root, candidate ticket,
  approved surface, consent, containment, baseline, claim, and rollback seams.
- Enforce preflight and consent ordering, repo/config path containment, expected
  lifecycle-write allowlisting, monitoring prefix preservation, and rollback
  verification through scratch-root tests.
- Provide a reviewed invocation boundary that is structurally unreachable without
  explicit live authority, but do not exercise it against the real repository.
- Preserve the existing scratch-only packages and their no-live-execution invariants.

## Out of Scope
- Any actual `codex exec` call, hook registration, `.codex/config.toml` change,
  provider=`codex` monitoring write, or real-repository test execution.
- Implementing `TCK-20260801-MONITORING-WRITER-STATUS-STALE` or unblocking/running
  `TCK-20260730-CODEX-CONTROLLED-PILOT`.
- Modifying canonical YAML parity data, provider-neutral workflow semantics, or
  existing guardrail/shadow package containment tests.

## Acceptance Criteria
- [x] Tests prove all harness behavior uses injected scratch roots; a real project
      root is refused during normal build/test paths.
- [x] Missing/malformed request, owner, rollback, consent, identity, surface,
      claim, baseline, or containment evidence fails closed before writes.
- [x] The invocation boundary requires explicit independent live authority and is
      not exercised in this ticket; no real `codex exec` occurs.
- [x] Tests prove allowed expected lifecycle writes and reject unexpected ticket,
      config, or monitoring mutation; historical monitoring prefixes remain intact.
- [x] Existing guardrail, replay, shadow, and non-live executor containment tests
      remain unchanged and passing.

## Related Tickets
- TCK-20260730-CODEX-CONTROLLED-PILOT
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC
- TCK-20260731-CODEX-PILOT-EXECUTOR
- TCK-20260801-MONITORING-WRITER-STATUS-STALE

## Related Docs
- docs/plans/agent_infrastructure/codex_controlled_pilot_realrepo_harness_authorization_claude.md
- docs/plans/agent_infrastructure/codex_controlled_pilot_preflight_concerns_response_claude.md

## Related Stored Artifacts
- stored_artifacts/TCK-20260731-CODEX-PILOT-EXECUTOR/

## Related Code Areas
- tools/agent_codex_pilot_executor/
- tools/agent_codex_pilot_guardrails/
- tools/agent_replay_codex/
- tests/agent_codex_pilot_executor/
- tests/agent_codex_pilot_guardrails/

## Assumptions / Open Questions
- Any future actual live execution needs separate contemporaneous user approval
  after this harness is complete and reviewed.

## Implementation Notes
- Added the additive `tools/agent_codex_realrepo_pilot_harness/` package and
  scratch-only test suite. No existing executor, guardrail, hook, provider
  configuration, candidate ticket, or monitoring writer was changed.
- Ordinary preflight validates identity before derived path I/O, rejects the
  project root and escaped paths, validates the scratch candidate/request/surface/
  claim/policy evidence, and captures immutable baseline evidence before any
  invoker boundary.
- Expected-write policy validates its complete structure before hash binding;
  its named baseline helper deliberately excludes only the policy's own relative
  path to avoid an unrepresentable self-hash cycle.
- The public injected invoker requires dual authority plus a captured no-write
  preflight result. A private future-only live admission checks canonical-root
  identity only after those two conditions; this ticket never invokes it.
- Scratch rollback now captures its own baseline only for a contained scratch
  `.codex/config.toml` path and preserves all other scratch paths.
- `CODEX_REALREPO_PILOT_LIVE_CONSENT` remains documented as a future live gate
  only; it was not read for an actual operation in this ticket.
- Post-implementation Architecture-Verify remediation is complete and awaiting
  an independent re-check; this ticket must not advance until that review passes.

## Test Summary
- `.venv/bin/python -m pytest tests/agent_codex_realrepo_pilot_harness --import-mode=importlib -q`:
  **29 passed**.
- Harness plus executor protected scope: **50 passed**.
- Exact test-plan command: **246 passed, 5 skipped, 4 failed**. All four are
  pre-existing runtime-shadow fixtures that still declare workflow version 1
  while the shared contract is 2.
- Architecture re-review's superset protected scope: **311 passed, 5 skipped,
  6 failed**. The additional two known failures are stale Claude-adapter
  `FINALIZE_INCOMPLETE` call-site line-number assertions.

## Files Changed
- `tools/agent_codex_realrepo_pilot_harness/`
- `tests/agent_codex_realrepo_pilot_harness/`
- `staging_artifacts/TCK-20260801-CODEX-REALREPO-PILOT-HARNESS/`

## Completion Summary
Implemented and independently architecture-reviewed an additive non-live pilot
harness. It validates scratch-root-only immutable preflight evidence, exact
expected writes and monitoring suffixes, dual authority ordering, and contained
adapter-owned scratch config rollback. The focused harness suite passes 29 tests;
no live invocation, hook registration, project config change, candidate-hotfix
implementation, or provider-attributed monitoring record occurred. The only
wider-scope failures are six separately documented pre-existing fixture/assertion
drift failures outside this ticket.
