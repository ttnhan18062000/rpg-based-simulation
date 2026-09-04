---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260904-TEST-SCOPER-HANG-GUARD
phase: open
date: 2026-09-04
tags: [testing, ai, hooks, debugging]
---

# TCK-20260904-TEST-SCOPER-HANG-GUARD

## Title
Test-scoper background-hang deterministic enforcement

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P0

## Request Summary
CLAUDE.md has carried a prose Hard Rule since 2026-08-17/18 ("never end your turn while your own run_in_background command is still running") specifically because of a recurring test-scoper failure mode. RETRO-2026-W36 reports it recurring 3 more times regardless, including after a prior hotfix propagated the same prose warning to 14 more agent role files — direct proof prose alone doesn't prevent the failure. The target is a real Stop/PostToolUse/turn-end deterministic hook or equivalent state check, not a prompt-only assertion. A turn-end prompt assertion is acceptable only as a documented fallback if deterministic detection is proven infeasible during implementation, in the format: "deterministic enforcement not feasible because <reason>; fallback: prompt guidance only; residual risk: <named>" — never as an equally-weighted default. Gated on nothing.

## Scope
- Spike/verify whether a deterministic Stop/SubagentStop (or equivalent turn-end) hook is feasible in this repo's actual Claude Code harness — no such hook event key exists in .claude/settings.json today, and prior investigation (TCK-20260730-PROVIDER-HOOK-POLICY) found no in-repo evidenced payload shape for these events
- If feasible: wire a new hook under a hook event key that did not previously exist in this repo's settings.json hooks block, detecting/blocking a synthetic reproduction of a test-scoper-shaped subagent ending its turn with a still-running run_in_background pytest
- New/extended test in tests/tools/ exercising the hook script directly (stdin JSON in, exit code/structured output out), following the shell-wrapper pattern of pre_tool_hook.py/post_tool_hook.py
- If infeasible: produce the documented fallback in the required literal format in the ticket/epic doc
- Decide explicitly whether test-scoper.md's existing prose section is kept as defense-in-depth alongside any new control, or superseded with documented rationale — never silently deleted

## Out of Scope
- Modifying the existing PreToolUse/PostToolUse hook writers (pre_tool_hook.py, post_tool_hook.py) beyond what's needed to establish the pattern for the new hook
- Resolving the .claude/settings.json hooks-block collision risk with this batch's TCK-20260904-BASH-SECRET-SCAN-HOOK beyond flagging it as a coordination point (additive merge expected, not a sequencing dependency)
- Silently deleting test-scoper.md's existing prose Background Commands section without documented rationale

## Acceptance Criteria
- [ ] A committed artifact exists that either (a) fires/blocks a synthetic reproduction of a test-scoper-shaped subagent ending its turn with a still-running run_in_background pytest, verified by a test simulating the stdin payload and asserting the hook's exit code/output signals the violation, or (b) if proven infeasible, the literal fallback format ("deterministic enforcement not feasible because <reason>; fallback: prompt guidance only; residual risk: <named>") appears in the ticket/epic doc
- [ ] If a hook is implemented, it's wired under a hook event key that did not previously exist in this repo's settings.json hooks block, proving a new deterministic surface rather than a restatement of existing PreToolUse/PostToolUse writers
- [ ] New/extended test in tests/tools/ exercises the hook script directly (stdin JSON in, exit code/structured output out), not merely re-asserting that prose text exists
- [ ] test-scoper.md's existing prose section is either kept as defense-in-depth alongside the new control or explicitly superseded with documented rationale, never silently deleted

## Related Tickets
- TCK-20260902-AGENT-BACKGROUND-TASK-TURN-END-DEFENSE-IN-DEPTH (prior hotfix, propagated the same prose warning to 14 more agent role files; its own closing note states this did NOT prevent a 4th real recurrence and speculates the failure mode may need a product-level fix — directly motivates this ticket, confirms prose-only is exhausted)
- TCK-20260730-PROVIDER-HOOK-POLICY (source of the evidence that Claude's Stop event is unwired/unevidenced in this repo)

## Related Docs
- docs/plans/agent_infrastructure/ai_first_hardening_epics/guardrail_enforcement_epic.md
- docs/ai/codex_capability_matrix.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/agents/test-scoper.md
- .claude/settings.json
- tools/agent-monitoring/pre_tool_hook.py
- tools/agent-monitoring/post_tool_hook.py
- docs/ai/codex_capability_matrix.md
- stored_artifacts/TCK-20260730-PROVIDER-HOOK-POLICY/investigation.md
- tests/tools/test_post_tool_hook.py
- tests/tools/test_retro_nudge_hook.py
- tests/agent_orchestration/test_contract_structure.py

## Assumptions / Open Questions
- Core feasibility is unproven: no Claude Code Stop/SubagentStop hook is wired anywhere in this repo, and the one prior investigation that looked closely (TCK-20260730-PROVIDER-HOOK-POLICY) found no in-repo evidenced payload shape for those events — implementation must spike/verify this before committing to the deterministic path
- A negative result (documented fallback) is a legitimate, epic-sanctioned outcome, not a failure to route around
- Detection state may only be knowable from harness-internal bookkeeping not exposed via documented stdin payload fields, which would push toward the documented-fallback path
- .claude/settings.json's hooks block is a probable multi-ticket edit collision point with this batch's TCK-20260904-BASH-SECRET-SCAN-HOOK (not a sequencing dependency — additive merge expected, flagged as risk not blocker)
- The existing prose warning already represents a "strengthen the words" attempt per the epic's own framing — this ticket must not regress into another prose-only edit dressed up as compliance

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
