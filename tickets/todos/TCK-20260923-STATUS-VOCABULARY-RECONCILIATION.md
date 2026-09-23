---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260923-STATUS-VOCABULARY-RECONCILIATION
phase: open
date: 2026-09-23
tags: [architecture, schema, taxonomy, registry, documentation]
---

# TCK-20260923-STATUS-VOCABULARY-RECONCILIATION

## Title

Reconcile the four overlapping mechanism/rule status vocabularies into one declared axis model

## Status

OPEN

## Tier

standard

## Type

refactor

## Priority

P1

## Request Summary

This repo now carries **four** separate status vocabularies that describe overlapping facts about
the same mechanisms, with nothing binding them to each other:

| # | Vocabulary | Values | Where it lives | What it actually answers |
|---|---|---|---|---|
| 1 | Registry `state` | `done` · `partial` · `gap` · `orphan` · `gated` · `skeleton` | `registries/mechanisms.yaml`, enforced by `tools/mechanism_registry/registry.py::VALID_STATES` | How complete is the implementation? |
| 2 | Registry `verified.verdict` | `observed` · `contradicted` · `inconclusive` | same file, `VALID_VERDICTS`, paired with `instrument` (`code_trace` static; `census`/`scenario`/`corpus_run` runtime) | What did an instrument actually find? |
| 3 | Compass §10 runtime status | `MISSING` · `DESIGNED` · `EXPERIMENTAL` · `OFF` · `DORMANT` · `STARVED` · `REACH-LIMITED` · `LIVE` · `DEPRECATED` · `REPLACED` | `docs/brainstorm/core_rpg_design_direction.md` §10 | Does it actually run in a real simulation, and how widely? |
| 4 | Control plane Rule realization | `SUPPORTED` · `PARTIAL` · `CONFLICTING` · `MISSING` · `INERT-OFF` · `UNKNOWN` | `docs/plans/simulation_semantic_control_plane/architecture.md` §3/§4; being built now by `TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION` | Does the world Rule hold, given its mapped mechanisms? |

Three overlapping status vocabularies is precisely the drift the Mechanism Registry was created to
end; #4 makes it four, and #4 is being implemented **right now** by M0.

The problem is not that four vocabularies exist. On inspection they sit on **genuinely different
axes** and collapsing them into one enum would destroy real information. The problem is that
nothing states that, so:

- **Values collide across axes with no declared relationship.** `MISSING` is in both (3) and (4).
  `PARTIAL` is in both (1) and (4). `OFF` (3) and `INERT-OFF` (4) are near-homographs. A reader
  cannot tell whether two `MISSING`s mean the same thing, and today they do not.
- **Real overlaps are undeclared.** `DORMANT` (3) and `orphan` (1) describe the same underlying
  situation from different angles. `gated` (1) and `OFF` (3) likewise.
- **One axis has a concept the others cannot express.** `STARVED` and `REACH-LIMITED` (3) have no
  representation in (1) or (2) at all — yet the repo's single most-cited example,
  `tactical_decision` (`state: done`, `verified.verdict: contradicted`), is *exactly* a STARVED
  mechanism. The registry can only say "done but contradicted," which is strictly less informative
  than the word the compass already coined for it.

**Timing is why this is P1 now, not later.** M0 builds schema and validator only, with no rows. M1
populates the first real Territory mapping data against vocabulary (4). Reconciling before M1 costs
one ticket; reconciling after M1 costs a data migration on live mapping entries plus a validator
change. This ticket must land **between M0 and M1**.

## Scope

- Produce one authoritative **axis model**: a short written statement of how many distinct status
  axes actually exist, what question each answers, and which of the four vocabularies is the
  canonical expression of each axis.
- Produce a **binding table** mapping values across axes wherever a real relationship exists,
  stating for each pair whether it is equivalence, implication (one-directional), or merely
  correlation. Explicitly mark pairs with *no* defined relationship as such, rather than leaving
  them unstated.
- **Resolve the two homograph collisions by decision**, not by silence: `MISSING` in (3) vs (4),
  and `OFF` (3) vs `INERT-OFF` (4). Either rename one side, or declare and document that the same
  word means different things on different axes and is never to be compared across them.
- **Decide whether `STARVED` / `REACH-LIMITED` earn representation in the registry.** Two admissible
  outcomes, both acceptable: add a registry field for runtime reach, OR record the decision that
  runtime reach is deliberately not registry-resident and lives only on the compass axis. A decision
  either way is the deliverable; leaving it undecided is not.
- Update each vocabulary's own home to point at the axis model, so no future reader meets one
  vocabulary without learning the other three exist.
- Apply the §11 admission test to any new field this ticket proposes, per the compass's own gate.

## Out of Scope

- **Merging the four vocabularies into a single enum.** Investigation should treat this as the
  likely-wrong answer; they measure different things. If evidence says otherwise, that is a finding
  to report, not a mandate to execute.
- Re-classifying any actual mechanism. This ticket changes the *vocabulary contract*, not any
  mechanism's current value. Zero row-level reclassification.
- Populating any control-plane mapping data (that is M1).
- Changing `depends_on` semantics.
- Resolving the `tactical_decision` design question (whether the strategic dispatch gate should
  derive `DEFEAT_ENEMY`). That is an open user decision, cited here only as evidence that the
  STARVED concept has no registry home.
- Any CI wiring. Report-only.

## Acceptance Criteria

1. A single document states the axis model: how many axes exist, the question each answers, and the
   canonical vocabulary for each.
2. A binding table covers every cross-axis value pair that has a real relationship, each labelled
   equivalence / implication / correlation; pairs with no defined relationship are explicitly listed
   as undefined rather than omitted.
3. Both homograph collisions (`MISSING`×2, `OFF`/`INERT-OFF`) have a recorded decision and a
   rationale.
4. The `STARVED`/`REACH-LIMITED` registry-representation question has a recorded decision, with the
   §11 admission test applied if the decision adds a field.
5. All four homes cross-reference the axis model: `registries/mechanisms.yaml`'s schema docs,
   `core_rpg_design_direction.md` §10, `simulation_semantic_control_plane/architecture.md` §3/§4,
   and the registry validator's own docstring.
6. If a registry field is added, `tools/mechanism_registry/registry.py::validate()` enforces it and
   is proven to reject a deliberately-invalid fixture — matching the discipline set by
   `TCK-20260920-MECHANISM-REGISTRY-CI-WIRING` and required of M0's own validator.
7. Zero mechanism rows change classification as a result of this ticket; a diff of
   `registries/mechanisms.yaml` shows no `state` or `verdict` value changed.
8. The M0 schema is unchanged, or if this ticket requires a change to it, that change is recorded
   against M1's already-budgeted "one bounded schema revision" allowance rather than silently
   widening M0.

## Related Tickets

- `TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC` — parent context; this is a cross-cutting prerequisite
  sitting between M0 and M1, not one of the M0–M4 milestones.
- `TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION` — builds vocabulary (4). Must land first; this
  ticket must land before M1 populates data against it.
- `TCK-20260915-MECHANISM-REGISTRY-FOUNDATION` — established vocabularies (1) and (2).
- `TCK-20260920-MECHANISM-REGISTRY-CI-WIRING` — the broken-fixture proof discipline AC 6 inherits.
- `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` (DONE) — evidence that STARVED has
  no registry representation. Closed as investigation; behavior deliberately not fixed.
- `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION` — adjacent registry-hygiene tail.

## Related Docs

- `docs/brainstorm/core_rpg_design_direction.md` §10 (vocabulary 3), §11 (admission test)
- `docs/plans/simulation_semantic_control_plane/architecture.md` §3, §4, §8
- `docs/plans/simulation_semantic_control_plane/roadmap.md` (M0/M1 boundary this ticket sits in)
- `docs/plans/simulation_semantic_control_plane/rollout_plan.md` (Stage A "don't design the final
  ontology up front" — the counter-pressure this ticket must respect)
- `docs/guidelines/tag_taxonomy.md` — precedent for a repo vocabulary split into declared categories

## Related Stored Artifacts

- `stored_artifacts/TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC/{plan,investigation,test_plan}.md`

## Related Code Areas

- `registries/mechanisms.yaml`
- `tools/mechanism_registry/registry.py` (`VALID_STATES` ~L139, `VALID_VERDICTS` ~L149,
  `_REQUIRED_VERIFIED_FIELDS` ~L150, `validate()`, `state_counts` ~L802)
- Whatever M0 lands as the control-plane schema + validator (path undecided by design)

## Assumptions / Open Questions

- **Assumption:** the four vocabularies are genuinely different axes and must stay separate. Stated
  as the expected conclusion so the investigation can *falsify* it rather than rediscover it; if the
  evidence contradicts this, report that rather than forcing the assumed shape.
- **Open:** does the axis model live in a new doc, or as a section inside an existing one? Prefer
  extending an existing doc over creating a new one, per the one-fact-one-home rule. Investigation
  picks the home and justifies it.
- **Open:** the compass §10 list is aspirational prose ("worth carrying eventually"), not an
  enforced enum — no validator checks it and no mechanism currently carries a §10 value. Confirm
  this before binding to it; binding an enforced vocabulary to an unenforced one is itself a
  decision needing a rationale.
- **Open:** whether `skeleton` (1) has any §10 counterpart, or is purely an implementation-completeness
  notion with no runtime meaning.
- **Not assumed:** that the compass's §10 vocabulary is correct merely because it is newer. It has
  never been applied to real data; M0's vocabulary has at least been designed against the Rule
  Catalog. Neither has field-tested precedence over the registry's, which is the only one with 93
  real rows behind it.

## Implementation Notes

_To be completed by the implementer._

Sequencing note for whoever picks this up: the registry vocabularies (1) and (2) are the only ones
with real data behind them (93 mechanism rows). Treat them as the load-bearing reference and bind
the others to them, rather than reshaping them to fit two vocabularies that have never been applied
to a row.

## Test Summary

_To be completed by the implementer._

Expected shape: a validator test only if AC 4 adds a field (normal accept + deliberately-broken
fixture reject per AC 6), plus a regression assertion for AC 7 that no existing `state`/`verdict`
value changed. Mostly a documentation-contract ticket; do not manufacture coverage beyond this.

## Files Changed

_To be completed by the implementer._

## Completion Summary

_To be completed by the implementer._
