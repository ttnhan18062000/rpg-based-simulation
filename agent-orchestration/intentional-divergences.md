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
