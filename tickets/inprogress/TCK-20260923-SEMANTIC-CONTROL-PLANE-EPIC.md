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

Milestone dispositions (this epic closes only when every row below has one):

| Milestone | Ticket | Disposition |
|---|---|---|
| M0 — schema + validator | `TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION` | **DONE** 2026-09-23, branch `semantic-control-plane-m0`, unpushed. Full standard pipeline, 0 blocking gate failures. |
| M1 — Territory/Control slice | not yet created | **UNBLOCKED** by M0. Gated behind `TCK-20260923-STATUS-VOCABULARY-RECONCILIATION` by owner decision (see below). |
| M2 — drift detection | not yet created | Gated on M1. |
| M3 — finding ingestion | not yet created | Permanent stream, startable after M0. Only hard bar: Territory+Combat triage before M4. |
| M4 — Combat slice + cross-domain view | not yet created | Gated on M1, M2, and M3's narrow triage only. |

Cross-cutting, not a milestone:
- `TCK-20260923-STATUS-VOCABULARY-RECONCILIATION` (OPEN, standard, P1) — reconciles the four
  overlapping status vocabularies. **Must land between M0 and M1**: M1 populates the first real
  rows against the control plane's realization vocabulary, so reconciling afterwards costs a data
  migration plus a validator change instead of one ticket.

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
  (`TCK-20260913-PERF-M0-ARCHITECTURE-GOVERNANCE-EPIC`) — **confirmed for this run**: M0's own
  investigation resolved both deliberately-open decisions (see M0 disposition below).

### M0 disposition (recorded 2026-09-23, by the epic owner)

Both decisions `architecture.md`/`roadmap.md` deliberately left open are now **closed**:
- **Serialization/location:** three sibling YAML registries — `registries/rule_mechanism_edges.yaml`,
  `registries/mechanism_causal_edges.yaml`, `registries/rule_classifications.yaml` — kept physically
  separate, matching `roadmap.md`'s explicit warning against merging a Rule→Mechanism edge and a
  Mechanism→Mechanism edge into one row shape.
- **Self-edges:** `producer_mechanism_id == consumer_mechanism_id` is **rejected** by the validator.
- Validator lives in its own sibling package `tools/semantic_control_plane/`, not inside
  `tools/mechanism_registry/`, mirroring the latter's `validate()`/`check_duplicate_keys()` split.
- `rule_id` resolves against a **live scan** of `docs/world_rules/**/*.md`
  (`rule_catalog.py::scan_rule_ids()`), never a hardcoded list — so the 172-Rule foreign key cannot
  silently rot.

Verified by the epic owner against the branch, not taken on report: all three registries ship
genuinely empty (`edges: []`), so M0 populated zero mapping rows as scoped; `architecture.md` is the
only design doc touched. Each registry header additionally warns against generating the
172×93 Cartesian product, holding `architecture.md` §7's "an absent edge means UNKNOWN, not
MISSING" — a durable guard M1 inherits.

One real defect surfaced and fixed mid-pipeline: the documented CLI invocation threw
`ModuleNotFoundError` (no repo-root `sys.path` bootstrap before its `tools.*` imports). Caught by
the shadow architecture-reviewer that PR #240 had just defaulted on, **independently reproduced
before being acted on** (that path is advisory-only and never gates), fixed with a subprocess-based
regression test. Production Architecture-Verify had already APPROVED beforehand — this was added
substance, not gate-routing.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary
