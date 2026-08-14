---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260802-CODEX-POSTTOOL-HOOK-COMMAND
phase: done
date: 2026-08-02
tags: [ai, security, workflows, hooks, agent-monitoring, rollback, testing]
---

# TCK-20260802-CODEX-POSTTOOL-HOOK-COMMAND

## Title

Build the non-live Codex PostToolUse adapter command and identity-bound transport environment

## Status

DONE

## Tier

standard

## Type

feature

## Priority

P1

## Request Summary

Provide the missing runnable command capability behind the already-reviewed Codex `PostToolUse`
adapter, and thread only the fixed controlled-pilot identity context into a future Codex child
process. The work must remain capability-only: it must neither register/enable a hook nor invoke
Codex against the real repository.

## Scope

- Add a fixed, fail-open adapter command boundary that consumes the evidenced JSON stdin shape,
  derives no identity from untrusted hook payload fields, and delegates once to the existing
  redacting adapter.
- Extend the reviewed fixed-argv live transport only to pass an explicit, allowlisted environment
  needed by that command; inherit the existing environment without accepting caller-provided
  environment overrides.
- Define and test the exact monitoring record/policy-suffix contract for a future controlled
  pilot, including how every provider-attributed `tools.jsonl` record is identity-bound.
- Reconcile the adapter's existing independent append gate
  (`CODEX_POSTTOOL_ADAPTER_LIVE_APPEND=1`) with the two transport consent gates in an explicit,
  reviewed design; do not weaken or silently remove any gate.
- Test only with synthetic hook payloads, injected scratch roots, and mocked subprocesses.

## Out of Scope

- Editing `.codex/config.toml`, changing the approved no-op hook fragment, registering or enabling
  any hook, or running `codex exec`.
- Writing `provider="codex"` data to real monitoring files, changing the reserved stale-status
  candidate, or modifying either blocked activation ticket.
- Treating code completion as satisfaction of the human/process prerequisites in
  `agent-orchestration/hook-surface-policy.yaml`.
- Removing the adapter's live-append gate or adding arbitrary environment/prompt/config surfaces.

## Acceptance Criteria

- [ ] A runnable, fixed command boundary reads one JSON object from stdin, accepts identity only
      from an explicit allowlisted environment, calls the existing adapter, and exits successfully
      for malformed input, missing identity, append refusal, or writer failure.
- [ ] Live transport passes only the fixed execution identity fields and the explicitly reviewed
      adapter append grant to its child environment; it accepts no caller-selected environment,
      prompt, hook command, target path, candidate, or ticket.
- [ ] The exact expected `tools.jsonl` suffix schema is captured in the just-in-time candidate
      policy and is proven using a new, bounded live-hook proof: every known identity field matches
      exactly; sequences are gap-free and monotonic; the reviewed count cap and transport time
      window are enforced; altered, omitted, reordered, or extra rows are rejected. Existing exact
      suffix proof remains unchanged for all pre-declarable rows.
- [ ] Tests prove payload fields cannot override identity, no real config/repository/Codex/monitoring
      mutation occurs, malformed or missing inputs fail open, and the command is injectable only
      through the reviewed fixed path.
- [ ] The ticket explicitly maps its completed code-level safeguards and the remaining human-only
      activation prerequisites; it does not claim a pilot is authorized or ready to run.

## Related Tickets

- TCK-20260730-CODEX-POSTTOOL-ADAPTER (DONE; adapter implementation)
- TCK-20260801-CODEX-LIVE-TRANSPORT (DONE; fixed invocation boundary)
- TCK-20260802-CODEX-PILOT-ENTRYPOINT (DONE; just-in-time policy/context preparation)
- TCK-20260801-MONITORING-WRITER-STATUS-STALE (reserved pilot candidate; untouched)
- TCK-20260730-CODEX-CONTROLLED-PILOT (BLOCKED; untouched)
- TCK-20260730-CODEX-RUNTIME-ACTIVATION-EPIC (BLOCKED; untouched)

## Related Docs

- docs/ai/codex_posttool_adapter_real_command_proposal.md
- docs/ai/codex_posttool_adapter_activation_fragment.md
- agent-orchestration/hook-surface-policy.yaml
- docs/ai/monitoring_writer_decision.md

## Related Stored Artifacts

- stored_artifacts/TCK-20260730-CODEX-POSTTOOL-ADAPTER/
- stored_artifacts/TCK-20260801-CODEX-LIVE-TRANSPORT/
- stored_artifacts/TCK-20260802-CODEX-PILOT-ENTRYPOINT/

## Related Code Areas

- tools/agent_codex_posttool_adapter/{adapter.py,live_gate.py,record_builder.py,writer_bridge.py}
- tools/agent_codex_live_transport/invoker.py
- tools/agent_codex_pilot_entrypoint/preparation.py
- tools/agent_codex_realrepo_pilot_harness/{policy.py,proofs.py}
- tests/agent_codex_posttool_adapter/
- tests/agent_codex_live_transport/

## Assumptions / Open Questions

- No approved configuration can invoke the proposed command yet: the sole reviewed fragment remains
  `command = "true"`. Replacing that exact text requires a later human-reviewed config-diff and
  must not occur in this ticket.
- Architecture Review resolved the transport-to-hook contract: transport passes fixed identity
  metadata only. The existing three consent gates stay independent, human-set shell variables and
  are never derived or set by project code.
- Architecture Review resolved monitoring proof: a new bounded tool-only proof is additive to the
  existing exact-suffix proof. It verifies known fields exactly, a reviewed policy cap, gap-free
  sequence, and actual transport time window; it cannot wildcard or fabricate rows.
- A future reviewed configuration must invoke this repository's absolute `.venv/bin/python3` and
  absolute `hook_entry.py` path. Moving that venv requires another config-diff review.
- Completing this capability still leaves `human_approval`, `scratch_first_verification`,
  `project_trust_review`, `hook_trust_review`, `reviewed_config_diff`, and `one_action_rollback`
  as per-run/activation decisions, not ticket-generated evidence.

## Implementation Notes

- Added a fail-open `hook_entry.py` runnable by the reviewed absolute script path. It derives the
  repository-local monitoring target, reads JSON only from stdin, accepts only environment-provided
  identity metadata, and delegates to the existing adapter. It has no command arguments and never
  invokes Codex.
- Added review-only absolute command rendering, identity-only child environment construction, and
  a narrow bounded tools suffix proof. The exact static suffix proof remains unchanged for policies
  without an explicit bounded tools contract. The adapter append gate remains an inherited,
  human-set environment value; no project code sets consent.
- The entrypoint policy now transparently declares an initial `max_tool_calls: 200` proposal for
  fresh human review with the generated policy; it is not a standing authorization to run a pilot.

## Test Summary

- Focused new capability tests: **12 passed**
  (`tests/agent_codex_posttool_adapter/test_hook_entry.py`, review-command and transport-env tests,
  and bounded-proof tests).
- Protected package suite: **114 passed**
  (`tests/agent_codex_posttool_adapter tests/agent_codex_live_transport
  tests/agent_codex_pilot_orchestration tests/agent_codex_realrepo_pilot_harness
  --import-mode=importlib -q`). A final full protected run is required after actual-diff review.

## Files Changed

- tools/agent_codex_posttool_adapter/{hook_entry.py,command.py}
- tools/agent_codex_live_transport/invoker.py
- tools/agent_codex_realrepo_pilot_harness/{policy.py,proofs.py}
- tools/agent_codex_pilot_entrypoint/preparation.py
- tests/agent_codex_{posttool_adapter,live_transport,realrepo_pilot_harness}/
- tests/agent_codex_pilot_orchestration/test_entrypoint.py

## Completion Summary

Implemented the final non-live hook-command capability: bounded tools-only proof,
identity-only transport threading, fail-open absolute-script adapter entrypoint, and
review-only absolute command rendering. Human trust/config/consent prerequisites remain open.
