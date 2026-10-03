# Intentional Divergences — agent-orchestration/ Claude Adapter Conformance

Distinct from `docs/guidelines/intentional_divergences.md` (the mechanics-bible/Mechanics Bible
divergence log — a different subsystem, different field format, out of scope for this file). This
log records divergences between the `agent-orchestration/` contract (phases, terminal statuses,
gate policy, artifact requirements) and the LIVE `.claude/workflows/implement-ticket.js` behavior,
as surfaced by `tests/agent_orchestration_claude_adapter/`'s conformance tests
(TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER).

Any mismatch a conformance test finds fails the test UNLESS a matching entry below carries a
complete human-approval marker (`Approved-by` + valid `Approved-date` + `Status: RATIFIED`). A
`DEFERRED` or incomplete entry does not suppress a conformance failure.

## Entry Format

```markdown
## <axis>:<value-or-id>
Axis: terminal_status | phase_order | gate_policy | artifact_requirements
Contract-value: <what the contract says>
Live-value: <what implement-ticket.js actually does>
Rationale: <free text explaining why this is intentional>
Approved-by: <reviewer name>
Approved-date: YYYY-MM-DD
Status: RATIFIED
```

`<value-or-id>` is the specific phase name or terminal-status value the divergence concerns (or a
short slug for `gate_policy`/`artifact_requirements` divergences, once those axes gain conformance
tests). `Status` is `RATIFIED` (approved, suppresses the failure) or `DEFERRED` (acknowledged but
not yet approved — does not suppress).

## Entries

None. This ticket's own contract data
(`agent-orchestration/terminal-statuses.yaml`) was authored directly from the same live extraction
its conformance tests check against, and the phase-order conformance test found no divergence — so
this log ships with the format defined and zero divergence entries.

## Known Configuration Gaps (Not Conformance-Test Axes)

This section is distinct from the structured `## Entries` log above — nothing here suppresses a
conformance test, since neither gap is on the `terminal_status | phase_order | gate_policy |
artifact_requirements` axes that log covers. Recorded here (2026-07-27, post-closure configuration-
parity audit) so these gaps are explicit and discoverable rather than silently absent, per Claude's
`final_configuration_parity_verification_claude.md` and Codex's confirming
`final_configuration_parity_verification_response_codex.md`, both under
`docs/plans/agent_infrastructure/provider_agnostic_orchestration/`.

**Hook-surface policy.** `agent-orchestration/hook-events.yaml` normalizes only `PreToolUse` and
`PostToolUse` — the two hooks actually wired in `.claude/settings.json`. `docs/ai/codex_capability_matrix.md`
verifies Codex has 10 real lifecycle hooks available (`PermissionRequest`, `PreCompact`, `PostCompact`,
`UserPromptSubmit`, `SubagentStop`, `Stop`, `SessionStart`, `SubagentStart` are the 8 not in the
contract). This is a deliberate scoping choice, not an oversight: adding capability-only entries for
hooks no real provider workflow currently uses would make the contract falsely imply support. Expand
`hook-events.yaml` only when a real workflow needs one of the 8 missing entries — do not add them
speculatively.

**Execution-identity activation.** `tools/agent-monitoring/post_tool_hook.py` and the unified writer
support `provider`/`execution_id` fields (per `TCK-20260721-MONITORING-WRITER-UNIFICATION`). As of
`TCK-20260730-CLAUDE-EXECUTION-IDENTITY`, `.claude/workflows/implement-ticket.js` now constructs
`provider="claude"` and a validated `execution_id` once per execution (immediately after `tid` is
confirmed real) and threads both — plus `ticket_id` — into the `.claude/current_run` sidecar
(`writeSidecar`'s body) and into new `runs.jsonl`/`events.jsonl` records (`writeMonitoring`'s
prompt). The no-ticket Scope and scope-failure paths remain identity-less by design (identity is
only synthesized after a ticket is confirmed real). The concurrent-provider guard in
`tools/agent_codex_pilot_guardrails/ticket_selection.py::assert_no_concurrent_claim` can now be
exercised against real Claude-attributed traffic in addition to synthetic fixtures; Codex still has
no active writer, so no real Codex-attributed traffic exists yet — Codex-side activation remains a
separate, unstarted follow-up.
