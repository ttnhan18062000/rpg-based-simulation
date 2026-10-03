---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260802-CODEX-PILOT-ENTRYPOINT
artifact_type: test_plan
tags: [ai, security, workflows, hooks, agent-monitoring, rollback, testing]
---

# Test plan

- Build policy/context twice against identical injected roots and prove deterministic bytes.
- Change any baseline/request byte after preparation and prove preflight refusal.
- Reject a wrong candidate, traversal-shaped evidence path, missing config allowlist, widened surface,
  or inconsistent execution identity before an invocation callable is touched.
- Assert the CLI/entrypoint test seam never calls `execute_controlled_pilot`, changes a real root,
  writes config, or invokes subprocess without a separately opted-in live test (which this ticket
  does not contain).
- Re-run orchestration/harness/transport/guardrail/adapter suites.
