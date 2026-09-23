---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC
phase: open
date: 2026-09-23
tags: [architecture, documentation, schema]
---

# TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC

## Title
Simulation Semantic Control Plane — connect the World Rule Catalog to the Mechanism Registry (M0–M4)

## Status
OPEN

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
The World Rule Catalog (`docs/world_rules/`, frozen 2026-09-22, 172 Rule IDs) and the Mechanism
Registry (`registries/mechanisms.yaml`, 93 mechanisms) have zero cross-references today —
confirmed by direct grep, not assumed. No Rule cites a `mechanism_id`; no mechanism cites a Rule.
The design and staged rollout for closing this gap is fully written and merged to `main`
(`docs/plans/simulation_semantic_control_plane/{README,architecture,agent_operating_model,
rollout_plan,roadmap}.md`, landed via PR #223, commit `a4333bcef`). No ticket exists yet for any
of it. This epic tracks scoping the child tickets only, milestone by milestone, per
`roadmap.md`'s own bounded M0→M4 sequencing — it does not implement anything itself.

## Scope
- Scope-only epic: full design lives in `docs/plans/simulation_semantic_control_plane/roadmap.md`
  (M0–M4, each with its own goal/deliverables/exit-criteria) and its four sibling design docs.
  Detailed, investigated child tickets are created separately via the `create-tickets` skill and
  linked here.
- This pass authorizes creating tickets for **M0 only** — "Schema and validator," explicitly
  "gated on nothing" per `roadmap.md`'s own dependency chain. M0's three deliverables (Rule↔
  Mechanism mapping schema, Mechanism→Mechanism causal-edge schema, Rule-level realization-
  classification schema) plus their validator and its proof-on-broken-input are the only unit of
  work this pass creates tickets for.
- M1 (Territory/Control first slice) is gated on M0 and is explicitly NOT created by this pass.
- M2 (drift detection) is gated on M1 and is explicitly NOT created by this pass.
- M3 (existing-finding ingestion) starts after M0 but is described in `roadmap.md` as a permanent,
  ongoing stream with no bounded exit criterion of its own — not a ticket to create now; it is
  triaged organically as later tickets touch mapped domains, per Stage D discipline.
- M4 (second slice, cross-domain view) is gated on M1, M2, and M3's Territory+Combat-scoped triage
  and is explicitly NOT created by this pass.

## Out of Scope
- Any actual mapping entries (real Rule↔Mechanism rows) — M0 is infrastructure only, the same
  sequencing `registries/mechanisms.yaml` itself followed (schema and validator before real rows).
- `rollout_plan.md`'s perpetual Stage D/E/F — these never finish and are not milestones.
- Naming or resolving `tactical_decision`'s `contradicted` verdict or the paused
  `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP` ticket — both are named in `roadmap.md`
  M4 as live state to re-check at that milestone, not something this scoping pass touches.

## Acceptance Criteria
- [ ] A real, investigated `TCK-*.md` M0 ticket (or tickets, if `create-tickets`' Investigate
      phase finds the three schemas warrant separate tickets) exists and is linked in this epic's
      Related Tickets section.
- [ ] The M0 ticket(s) do not include any M1–M4 deliverable and do not populate real mapping data.
- [ ] This epic ticket is not moved to `tickets/done/` until M0–M4 each have a disposition (done,
      blocked, or explicitly deferred) — per `roadmap.md`'s own milestone gating.

## Related Tickets
- TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION

## Related Docs
- `docs/plans/simulation_semantic_control_plane/README.md`
- `docs/plans/simulation_semantic_control_plane/roadmap.md`
- `docs/plans/simulation_semantic_control_plane/architecture.md`
- `docs/plans/simulation_semantic_control_plane/agent_operating_model.md`
- `docs/plans/simulation_semantic_control_plane/rollout_plan.md`
- `docs/world_rules/README.md` (the frozen Catalog this epic connects to the Mechanism Registry)
- `docs/brainstorm/simulation_semantic_control_plane_external_draft.md` (historical, provenance
  only)

## Related Stored Artifacts
None.

## Related Code Areas
- `registries/mechanisms.yaml` (the Mechanism Registry side of the mapping)
- `docs/world_rules/` (the Rule Catalog side of the mapping)
- `tools/mechanism_registry/registry.py::validate()` (the validator pattern M0's own validator
  mirrors)

## Assumptions / Open Questions
- M0's exact mapping file path(s), field names, and serialization format are deliberately
  undecided in `architecture.md` §3 and `roadmap.md` — the M0 child ticket's own investigation is
  expected to resolve this, not this epic.
- Assumes `create-tickets`' Investigate phase, run against `roadmap.md`'s M0 section, will derive
  real file paths and concrete ACs the way it did for the PERF-M0-ARCHITECTURE-GOVERNANCE epic
  (`TCK-20260913-PERF-M0-ARCHITECTURE-GOVERNANCE-EPIC`) — not yet confirmed for this run.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary
