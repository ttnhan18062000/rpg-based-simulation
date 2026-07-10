---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT
phase: open
date: 2026-07-10
tags: []
---

# TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT

## Title
Add orchestrator-side enforcement for verified_by provenance Step 0 compliance, starting with mechanics-auditor

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
The `verified_by` field should stop relying purely on an agent honestly self-reporting that it ran its Step 0 static check before rendering a verdict. This ticket implements the concern raised in `docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md`, which names mechanics-auditor as the weakest instance of this problem: `docs/ai/agents.md` explicitly admits it "has no orchestrator-side enforcement... compliance depends entirely on the agent actually running the script and citing it honestly." This concern asks for orchestrator-side enforcement of `verified_by` provenance, starting with mechanics-auditor, mirroring the `bash()`-runs-static-check-before-`agent()` pattern already used for Architecture-Verify.

## Scope
- Resolve, explicitly and in writing (not implicitly), whether mechanics-auditor gets a new orchestrator call site (e.g. a standalone wrapper script, since it has no JS workflow host today — it is invoked ad hoc via `Agent(subagent_type: "mechanics-auditor")` outside any pipeline), or whether enforcement takes a different form (e.g. a post-hoc audit of past `verified_by` claims against the static check's own output).
- This must directly address that TCK-20260705-GATE-DET-MECHANICS-AUDITOR's own Implementation Notes explicitly ruled out adding an `Agent(subagent_type: mechanics-auditor)` call site to `implement-ticket.js` as "out of scope per the plan and ticket" — this ticket must either justify overturning that prior explicit scope decision (with Architecture-Review sign-off) or design a non-call-site enforcement mechanism instead.
- If a call site/wrapper is added, the static check result (`tools/gate_checks/mechanics_auditor_static.py`) must be computed before the agent renders its verdict and injected as context, mirroring `implement-ticket.js`'s Architecture-Verify phase pattern (lines 560-613).
- The agent's `verified_by` self-report must then be cross-checked post-hoc against the orchestrator-computed static result.

## Out of Scope
- C1 (tool_call_count/cost_proxy_score sidecar registration) — separate ticket TCK-20260710-CURRENT-RUN-SIDECAR-BASH, different field, different files.
- C2 (per-phase ts capture) — separate ticket TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH, different field.
- Extending this same enforcement mechanism to the other three verified_by-producing gates (done-checker, architecture-reviewer, parity-updater) beyond what's needed to design a reusable pattern — mechanics-auditor is the explicit starting instance; broader rollout is a follow-up.
- The 4 "related, smaller ideas" from `docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md`: (1) asymmetric gate coverage beyond the security tag, (2) cross-retro trend detection, (3) duplicated tag-to-skill mapping logic consolidation, (4) working_log.csv malformed-row normalization backfill.
- Reopening or modifying the scope of TCK-20260705-GATE-DET-MECHANICS-AUDITOR itself — this ticket supersedes/extends its explicit "out of scope" ruling for a new call site, it does not amend that ticket's own closed record.

## Acceptance Criteria
- [ ] The ticket explicitly resolves whether mechanics-auditor gets a new orchestrator call site (e.g. a standalone wrapper script) or whether enforcement takes a different form (e.g. post-hoc audit of past verified_by claims) — documented, not left implicit, given TCK-20260705-GATE-DET-MECHANICS-AUDITOR's prior explicit "out of scope" ruling.
- [ ] If a call site/wrapper is added, the static check result is computed before the agent renders its verdict and injected as context.
- [ ] The agent's verified_by self-report is cross-checked post-hoc against the orchestrator-computed static result.
- [ ] A new test demonstrates the enforcement mechanism actually detects a case where Step 0 was skipped or falsely cited.

## Related Tickets
- TCK-20260710-AGENT-BOOKKEEPING-DETERMINISM-EPIC
- TCK-20260705-GATE-DET-MECHANICS-AUDITOR
- TCK-20260705-GATE-DET-DONE-CHECKER
- TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER
- TCK-20260705-GATE-DET-PARITY-UPDATER
- TCK-20260710-CURRENT-RUN-SIDECAR-BASH (sibling)
- TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH (sibling)

## Related Docs
- docs/plans/agent_infrastructure/idea_agent_bookkeeping_determinism.md
- docs/ai/agents.md
- docs/ai/ticket-lifecycle.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/agents/mechanics-auditor.md
- tools/gate_checks/mechanics_auditor_static.py
- tools/gate_checks/done_checker_static.py
- tools/gate_checks/parity_updater_static.py
- tools/gate_checks/architecture_reviewer_static.py
- .claude/workflows/implement-ticket.js
- docs/ai/agents.md
- docs/ai/skills.md
- docs/ai/workflows.md
- docs/ai/system_overview.md
- docs/ai/ticket-lifecycle.md
- tests/tools/test_mechanics_auditor_static.py

## Assumptions / Open Questions
- mechanics-auditor has zero pipeline call sites anywhere (confirmed across 4 docs) — it's invoked ad hoc via `Agent(subagent_type: "mechanics-auditor")` directly, so the standard `bash()`-before-`agent()` pattern used elsewhere has no natural host location; this must be designed, not assumed to be a direct port.
- Adding a new call site would reverse TCK-20260705-GATE-DET-MECHANICS-AUDITOR's explicit prior scope decision — requires Architecture-Review sign-off before implementation, not just implementer discretion.
- Open question left to Scope/Plan phase: whether the eventual mechanism generalizes cleanly to the other three verified_by-producing gates or is mechanics-auditor-specific due to its lack of a JS workflow host.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
