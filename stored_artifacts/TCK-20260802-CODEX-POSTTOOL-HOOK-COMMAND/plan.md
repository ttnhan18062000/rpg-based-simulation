---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260802-CODEX-POSTTOOL-HOOK-COMMAND
artifact_type: plan
tags: [ai, security, workflows, hooks, agent-monitoring, rollback, testing]
---

# Plan

## Scope Guards

No `.codex/config.toml` edit, hook registration, live Codex invocation, production monitoring
append, candidate implementation, or blocked-parent-ticket edit is permitted. All tests are
scratch-only and all subprocess interactions are mocked. This ticket builds a capability, not a
pilot authorization or a substitute for the human prerequisites in hook-surface policy.

## Ordered Steps

1. **Add the bounded, tools-only live-hook proof.**
   - Files: `tools/agent_codex_realrepo_pilot_harness/{policy.py,proofs.py}`, the just-in-time
     entrypoint policy builder, and focused tests.
   - Keep `assert_post_run_proof` and `_assert_suffixes` byte-for-byte semantically unchanged.
     Add a separate proof only for live `tools.jsonl` output: exact known identity fields,
     contiguous sequence starting at one, policy-declared `max_tool_calls`, and timestamps within
     transport-captured start/end bounds. Every violation fails closed.
   - The policy declares the cap for future human review; this ticket must not silently make a
     permanent cap decision. No wildcard expected rows or fabricated records are permitted.

2. **Specify and implement the fixed command/environment contract.**
   - Files: `tools/agent_codex_posttool_adapter/` (new entrypoint module),
     `tools/agent_codex_live_transport/invoker.py`, and tests.
   - Define fixed names for execution identity and bounded metadata, repository-local target
     derivation, JSON-stdin handling, and a no-raise/no-nonzero failure contract. The hook payload
     cannot override any context field. The transport may copy ambient environment only to preserve
     normal process operation, then set solely its internally derived allowlisted identity values.
     It must not set, derive, or change any of the three human consent variables.
   - Render a review-only proposed command with absolute `<repo>/.venv/bin/python3` and absolute
     `<repo>/tools/agent_codex_posttool_adapter/hook_entry.py` paths. Do not change the no-op
     fragment or `.codex/config.toml`; moving the venv requires a new human config-diff review.

3. **Reuse existing adapter and proof primitives.**
   - Reuse `process_post_tool_use`, `identity.validate_identity`, `live_gate.require_live_append`,
     `record_builder`, shared writer bridge, and existing policy/proof primitives. Add only the
     reviewed narrow code needed for the bounded tool path.
   - Keep the activation fragment’s no-op command and config byte identity unchanged.

4. **Add synthetic boundary and proof tests.**
   - Cover valid/invalid stdin, environment identity precedence, inherited independent consent
     gates, writer failure, fixed transport environment, exact bounded-proof violations, and static
     no-shell/no-real-write containment.
   - Extend existing suites additively; do not repair unrelated brittle tests.

5. **Verify documentation and activation boundary.**
   - Update the ticket and review-only proposal to distinguish command capability from activation.
     Map code-level safeguards versus still-human prerequisites exactly.

## Resolved Architecture Decisions

- The exact row proof remains the standard for static suffixes; only live `tools.jsonl` callbacks
  receive the separate, stricter-in-known-fields bounded mechanism described in Step 1.
- All three consent variables are independently human-set in the shell. Transport threads identity
  only and must not grant adapter append permission.
- The future reviewed config command uses absolute repository-local venv and entrypoint paths,
  never ambient `PATH` resolution.

## Dependency Map

`Step 1 (bounded proof) → Step 2 (command and transport) → Step 3 (reuse integration) → Step 4 (tests) → Step 5 (verification)`.

## Acceptance-Criteria Map

- AC 1 → Steps 2–4
- AC 2 → Steps 2–4
- AC 3 → Steps 1 and 4
- AC 4 → Steps 2–4
- AC 5 → Step 5

## Review Gate

The design is ready for Claude's final architecture re-review. No implementation may begin until
that verdict is `APPROVED`.
