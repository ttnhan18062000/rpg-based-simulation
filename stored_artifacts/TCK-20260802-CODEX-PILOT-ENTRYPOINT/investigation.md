---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260802-CODEX-PILOT-ENTRYPOINT
artifact_type: investigation
tags: [ai, security, workflows, hooks, agent-monitoring, rollback, testing]
---

# Investigation

`execute_controlled_pilot()` is not referenced outside its module/tests; no CLI or
script builds a real `PilotHarnessContext`. The candidate and its request exist at
the authorized in-progress paths. The request's rollback text still says “scratch
configuration,” so a future real attempt needs a reviewed correction before use.

`ExpectedWritePolicy` binds request bytes, a baseline tree hash, exact lifecycle
transitions, allowlisted paths, and monitoring suffix rows. A static policy becomes
stale whenever any unrelated tracked file changes. A safe just-in-time sequence is:

1. Generate one execution identity and choose a contained policy-evidence path.
2. Write a provisional policy; capture the baseline excluding that policy file.
3. Rewrite only the excluded policy with the resulting baseline digest and re-read
   it to bind the typed context. The same execution identity supplies exact suffix rows.

This preserves fail-closed whole-tree semantics while avoiding advance-policy drift.

## Blocking architecture issue

The approved `PostToolUse` fragment is deliberately `command = "true"`. It cannot
call the existing redacting adapter and therefore cannot generate the provider-attributed
monitoring evidence required by the controlled-pilot ticket. Replacing it with a real
adapter command is a materially different hook activation surface and is not authorized
by this handoff. Architecture Review must decide whether a separately reviewed hook
command/config-diff mechanism is needed before this ticket can implement a runnable live path.

## Architecture resolution

The entrypoint is approved only as preparation/output-only. A real adapter-invoking
shell command, project/hook trust review, and exact enabling config-diff review are
a separate future ticket and decision. This ticket must never claim the pilot is
ready to emit genuine `provider="codex"` monitoring evidence.
