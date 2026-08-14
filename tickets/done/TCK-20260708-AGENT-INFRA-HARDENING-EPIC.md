---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260708-AGENT-INFRA-HARDENING-EPIC
phase: done
date: 2026-07-08
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20260708-AGENT-INFRA-HARDENING-EPIC

## Title
Agent Infrastructure Hardening Phase 2 — close the audit's remaining gaps: monitoring schema drift, gate enforcement (hook hard-block + lane-architecture coverage), and spend observability

## Status
DONE

## Tier
epic

## Type
chore

## Priority
P1

## Request Summary
`docs/ai/agent_infrastructure_audit.md` (2026-07-03, scored 8.0/10) raised 3 unscheduled follow-up ideas plus 2 outstanding recommendations. One idea (`idea_agent_gate_determinism.md`) was already 80% implemented by `gate-determinism-followups` (4 static verifiers + `verified_by` field, done 2026-07-05) — but its own "Enforcement: nudge vs. block" section (hook hard-block escalation for the two cases the audit flagged as silently unenforced) was never built, and the idea doc itself is stale (still says "Not scheduled"). The other two ideas — `idea_agent_monitoring_schema_enforcement.md` (2026-07-04) and `idea_agent_cost_observability.md` (2026-07-03) — remain fully unscheduled. This epic tracks closing all three, in the dependency order the ideas themselves specify: schema enforcement first (its own docs call it a near-prerequisite for the cost breakdown), gate enforcement hardening second (independent), cost observability last (consumes both).

## Scope
Track and sequence the three child tickets. No direct implementation.

## Out of Scope
- Re-litigating or re-scoring the 4 already-shipped gate-determinism static verifiers (done-checker/parity-updater/mechanics-auditor/architecture-reviewer) — this epic only closes the *remaining* half of that idea (hook hard-block escalation + lane-architecture coverage documentation)
- Real token/cost telemetry (Tier 3 of the cost-observability idea) — platform-blocked, no action possible until Anthropic forwards usage data
- Model-routing policy — explicitly a longer-term follow-on to Tier 1/2 cost data landing, not this epic
- Backfilling the 98 historical schema-drifted monitoring records — `idea_agent_monitoring_schema_enforcement.md` explicitly scopes this out; only future-drift prevention is in scope

## Acceptance Criteria
- All three child tickets DONE
- `idea_agent_gate_determinism.md` and this epic's other two source idea docs are updated to reflect final disposition (done/superseded/tracked-elsewhere), not left as stale "IDEA — Not scheduled"
- `docs/ai/agent_infrastructure_audit.md`'s Recommendations 1 and 3 can be marked closed with a pointer to the child ticket that closed them
- `make agent-monitoring-retro` output includes a spend-by-phase/spend-by-agent breakdown (Tier 1 proxy)
- At least one hook in `.claude/settings.json` escalates from advisory (`additionalContext`) to a hard block for the two cases the audit named: finalizing a ticket with no matching `agent-monitoring` write, and a `src/` commit in a parity-tracked subsystem with no matching ledger touch

## Related Tickets
TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT, TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING, TCK-20260708-AGENT-COST-OBSERVABILITY. Prior art: TCK-20260705-GATE-DET-DONE-CHECKER, TCK-20260705-GATE-DET-PARITY-UPDATER, TCK-20260705-GATE-DET-MECHANICS-AUDITOR, TCK-20260705-GATE-DET-ARCHITECTURE-REVIEWER (all done, `tickets/done/gate-determinism-followups/`), TCK-20260704-CREATE-TICKETS-MONITORING, TCK-20260704-RETRO-LOOP-ENFORCEMENT.

## Related Docs
docs/ai/agent_infrastructure_audit.md, docs/ai/system_overview.md, docs/plans/agent_infrastructure/idea_agent_gate_determinism.md, docs/plans/agent_infrastructure/idea_agent_cost_observability.md, docs/plans/agent_infrastructure/idea_agent_monitoring_schema_enforcement.md, docs/agent-monitoring/schema.md, docs/agent-monitoring/README.md, docs/guides/agent_monitoring.md, docs/ai/workflows.md, docs/ai/agents.md

## Related Stored Artifacts
none yet

## Related Code Areas
.claude/settings.json (hooks), .claude/workflows/implement-ticket.js (writeMonitoring, pushEvent), tools/agent-monitoring/record_run.py, tools/agent-monitoring/record_events.py, tools/agent-monitoring/validate.py, tools/agent-monitoring/generate_retro.py, tools/gate_checks/*.py

## Assumptions / Open Questions
- Assumes the dependency order specified inside the idea docs (schema enforcement before cost observability) is still correct — child ticket 1's own Investigate phase should confirm rather than re-derive from scratch.
- Open question carried from `idea_agent_gate_determinism.md`: do static-verifier-style hard blocks fail the workflow outright, or downgrade to the existing `NEEDS_CHANGES`/`BLOCKED`/`DOD_BLOCKED` vocabulary? Child ticket 2 must resolve this before implementing, since it changes hook behavior for every future run.
- Open question carried from `idea_agent_cost_observability.md`: is a unitless `cost_proxy_score` actionable without a rough per-model $/call constant? Child ticket 3's Investigate phase should size this before committing to the full Tier 1 formula.

## Implementation Notes
Sequencing: (1) MONITORING-SCHEMA-ENFORCEMENT first — foundational data-quality fix, explicitly named as a near-prerequisite by the cost-observability idea doc itself. (2) GATE-ENFORCEMENT-HARDENING second — independent of (1), but closes the audit's oldest still-open recommendation (#1, hook near-misses) and also absorbs Recommendation #3 (document `lane-architecture` coverage), per `idea_agent_gate_determinism.md`'s own "Natural Integration Points" table which says both are subsumed here. (3) AGENT-COST-OBSERVABILITY last — its retro-report payoff depends on (1)'s clean phase/agent vocabulary, and it can cite (2)'s `verified_by` field split (already landed from gate-determinism-followups) as the evidence base for a future model-routing decision.

## Test Summary
(epic — see children)

## Files Changed
(epic — see children for source/test changes)
- `docs/plans/agent_infrastructure/idea_agent_monitoring_schema_enforcement.md` (maturity banner: SCHEDULED → SHIPPED)
- `docs/plans/agent_infrastructure/idea_agent_cost_observability.md` (maturity banner: SCHEDULED → SHIPPED (Tier 1))
- `docs/ai/agent_infrastructure_audit.md` (Recommendation 2 marked closed with pointer)
- `docs/plans/agent_infrastructure/idea_agent_gate_determinism.md` and Recommendations 1/3 were already closed by TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING prior to this epic-closure pass — verified, not re-touched.

## Completion Summary
All three child tickets are DONE: `TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT`, `TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING`, `TCK-20260708-AGENT-COST-OBSERVABILITY` (all `tickets/done/`). All 5 epic Acceptance Criteria are satisfied:
1. Three child tickets DONE — confirmed.
2. All three source idea docs reflect final disposition — `idea_agent_gate_determinism.md` was already SHIPPED; this closure pass updated `idea_agent_monitoring_schema_enforcement.md` and `idea_agent_cost_observability.md` from SCHEDULED to SHIPPED with pointers to their completed tickets.
3. `docs/ai/agent_infrastructure_audit.md` Recommendations 1 and 3 were already marked closed (by GATE-ENFORCEMENT-HARDENING); this closure pass added the Recommendation 2 pointer to COST-OBSERVABILITY.
4. `make agent-monitoring-retro` output includes a spend-by-phase/spend-by-agent breakdown — shipped by COST-OBSERVABILITY.
5. `.claude/settings.json`-adjacent enforcement escalated from advisory to hard block for the two audit-named cases (parity-ledger cross-reference miss now hard-blocks as `PARITY_INCOMPLETE`; the monitoring-write case was deliberately revised to a non-blocking warning during that ticket's own architecture review, to avoid reversing CLAUDE.md's Hard Rule — see that ticket's plan.md Design Decision 2) — shipped by GATE-ENFORCEMENT-HARDENING.

No `src/` files were touched by this epic-closure pass (docs only). No parity ledger impact.
