# agent-infra-hardening — Implementation Sequence

Epic: `TCK-20260708-AGENT-INFRA-HARDENING-EPIC`. Closes the 3 remaining follow-ups from
`docs/ai/agent_infrastructure_audit.md` (2026-07-03): one half-finished idea
(`idea_agent_gate_determinism.md` — static verifiers shipped 2026-07-05, enforcement-escalation
half never built) and two fully-unscheduled ideas (`idea_agent_monitoring_schema_enforcement.md`,
`idea_agent_cost_observability.md`).

| Order | Ticket | Idea source | Why this order |
|---|---|---|---|
| 1 | TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT | idea_agent_monitoring_schema_enforcement.md | Foundational data-quality fix; the cost-observability idea doc names this as a near-prerequisite for its own retro-report payoff to mean anything |
| 2 | TCK-20260708-AGENT-GATE-ENFORCEMENT-HARDENING | idea_agent_gate_determinism.md (remaining half) | Independent of ticket 1; closes the audit's oldest open recommendations (#1 hook near-misses, #3 lane-architecture coverage docs) |
| 3 | TCK-20260708-AGENT-COST-OBSERVABILITY | idea_agent_cost_observability.md | Consumes ticket 1's clean phase/agent vocabulary for a meaningful spend-by-phase breakdown, and cites ticket 2 / prior gate-determinism-followups' `verified_by` split as evidence for any future model-routing discussion |

## Dependency Notes
- Ticket 2 has no hard dependency on 1 or 3 — could run in parallel with ticket 1 if bandwidth allows.
- Ticket 3's phase-breakdown payoff is only as good as ticket 1's vocabulary cleanup — land 1 first even if 2 slips.
- None of these three tickets touch simulation/gameplay code (`src/domains/`, `src/engine/` mechanics) — all changes are confined to `.claude/`, `tools/agent-monitoring/`, `tools/gate_checks/`, and `docs/ai/`+`docs/agent-monitoring/`. No parity ledger entry is expected from any of the three.
- Grade/SimQ anchors are unaffected — this epic is pure agent-tooling, not simulation-mechanics.
