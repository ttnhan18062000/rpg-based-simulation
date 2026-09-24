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
| M1 — Territory/Control slice | `TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE` | **DONE** 2026-09-24. First real data through M0's schemas; Territory six-axis view wired (`make territory-control-view`). |
| M2 — drift detection | `TCK-20260924-M2-MAPPING-DRIFT-DETECTION` | **DONE** 2026-09-24. `tools/semantic_control_plane/mapping_drift_check.py` + `make semantic-control-plane-drift-check`. Drift classes 1 (cited-code-changed) and 3 (verdict-changed) implemented and fixture-tested; class 2 (split/merge) consciously descoped — no lineage field exists in the schema, written reason in `investigation.md`. Live run against M1's Territory mapping: clean (0 findings). Report-only, exit 0 always, no CI wiring at this milestone. |
| M3 — finding ingestion | not yet created | Permanent stream, startable after M0. Only hard bar: Territory+Combat triage before M4. |
| M4 — Combat slice + cross-domain view | not yet created | Gated on M1, M2, and M3's narrow triage only. |

Cross-cutting, not a milestone:
- `TCK-20260923-STATUS-VOCABULARY-RECONCILIATION` — **DONE** 2026-09-23, landed between M0 and M1 as
  intended. Deliverable: `docs/plans/status_axis_model.md`.

### M1 disposition (recorded 2026-09-24, by the epic owner)

Verified against the branch, not taken on report.

**Classifications produced** (`registries/rule_classifications.yaml`), each citing real code paths:
- **TERR-01 `CONFLICTING`** — on *two structurally distinct* pieces of evidence, not one. The known
  `owner_faction_id` three-concept overload, **plus** an independently-discovered second desync:
  `betrayal_siege_war`/FAC-010 transfers control via `FactionState.territory` on every real siege
  conquest without ever updating `RegionState.owner_faction_id`. Two representations of "who
  controls this region" that diverge in normal play.
- **TERR-03 `CONFLICTING`** — same root cause as TERR-01.
- **TERR-02 `PARTIAL`** — landed on the axis M1's ticket left open (`SUPPORTED` vs `MISSING`), and
  resolved to neither: `FactionInfluenceService` *does* supply a real causal basis (accumulated
  in-region combat-death evidence crossing a threshold), so it isn't a bare assignment — but
  world-generation-time initial ownership (`src/worldbuilding/compiler.py:415,446`) is bare
  declarative assignment with zero causal basis, and the threshold disagreement below is unresolved.
- **TERR-05 `PARTIAL`** — **overrode an initial `MISSING` suggestion on evidence**, correctly.
  `RegionState.places`/`PlaceState.region_id` genuinely realizes the containment half; the
  cultural-association half is *confirmed absent* (`PlaceState` carries no such field, and
  `prior_kind`/`transformed_tick` is a Place-kind trail, not a polity fact) rather than unexamined.
  That is the `MISSING`-vs-`UNKNOWN` distinction `architecture.md` §7 requires, applied correctly.

**Verified by the epic owner:** AC 8 holds — a diff of `registries/mechanisms.yaml` against
`origin/main` shows **zero** `state` or `verdict` changes. The six-axis Territory view is wired as
`make territory-control-view`, mirroring the `mechanism-system-rollup-view` precedent.

**Escalated out of the slice:** a four-way regional-sovereignty threshold disagreement — ±100 in the
Mechanics Bible and `src/engine/world_dynamics.py:82,86`, ±50 in the runtime contract and
`src/world/influence.py:29-30`. Two *live* ownership-transfer paths on different thresholds, so this
is a parity violation and a consistency hazard, not doc drift. Correctly recorded rather than fixed
in a mapping slice. Filed as `TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT` (standard,
P1); every citation independently re-verified before filing.

### Vocabulary reconciliation disposition (recorded 2026-09-23, by the epic owner)

The ticket's central assumption — four genuinely distinct axes, reconcile rather than merge —
**survived falsification**. All four remain separate; `VALID_STATES`, `VALID_VERDICTS` and
`VALID_RULE_CLASSIFICATIONS` stay independently enforced.

Decisions now binding on M1 and everything after:
- **Both homographs keep their words.** `MISSING` (compass §10) × `MISSING` (Rule realization) is
  *correlation, not equivalence* — different granularity and a different evidentiary bar, since the
  control plane's `MISSING` requires investigated, evidenced absence while `UNKNOWN` means "not yet
  looked at." `OFF` × `INERT-OFF` is equivalence in intent; cite `INERT-OFF`'s evidence when both
  apply. Renaming was rejected because it would have widened M0's already-landed schema.
- **No new registry field for `STARVED`/`REACH-LIMITED`.** The compass's own §11 admission test was
  run against a hypothetical `reach` field using `tactical_decision` as the test case, and the field
  **failed** it twice over: no system consumes a structured reach value (Q4), and `verified.note`
  already captures the case in full (Q12). Adopted instead: a prose convention — when
  `verified.verdict: contradicted` pairs with a runtime instrument, the `note` names which of
  STARVED / REACH-LIMITED / genuinely-broken applies. Deliberately not validator-enforced.

**Material finding, wider than this ticket.** Compass §10 is far weaker than its prominence
suggests: **zero** mechanism rows carry a §10 value, no validator checks any §10 term, and only 2 of
its 10 values (`STARVED`, `REACH-LIMITED`) are defined in prose anywhere in the repo. The axis model
therefore ranks §10 as the *least* authoritative of the four axes and explicitly declines to bind
`orphan` × `DORMANT`, recording it as undefined rather than inferring a mapping onto an undefined
word. `skeleton` likewise has no §10 counterpart (zero hits). **This is a live gap in the compass
itself, not a control-plane problem — it needs an owner decision, not a ticket from this epic.**

Verified by the epic owner against the branch: `registries/mechanisms.yaml` changed by exactly one
3-line comment cross-reference (AC 7 holds — no `state` or `verdict` value altered), and M0's three
schema registries are byte-identical, with `tools/semantic_control_plane/registry.py` changed only
by a 3-line docstring pointer (AC 8 holds).

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
