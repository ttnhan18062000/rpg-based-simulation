---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE
phase: open
date: 2026-09-23
tags: [architecture, schema, registry, world]
---

# TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE

## Title

M1 — first operational slice: map Territory/Control Rules to real mechanisms and render the first
domain management view

## Status

OPEN

## Tier

standard

## Type

feature

## Priority

P1

## Request Summary

M0 built the semantic control plane's three schemas and validator, all shipping genuinely empty.
This ticket puts the **first real data** through them: map the Territory/Control Rules in
`docs/world_rules/places-culture/territory-control.md` to their actual mechanisms in
`registries/mechanisms.yaml`, with evidence, and render the first single-domain management view.

This is `rollout_plan.md` Stage B executed for real, and the first time M0's validator runs against
anything but empty files.

**Pre-verified against the live registry while scoping** (per `roadmap.md`'s own instruction that
its candidate list is a hint, not an answer). Do not re-derive these; do re-confirm they still hold
at execution time:

| Rule | Exists? |
|---|---|
| `TERR-01` claim/control/jurisdiction/property/occupation/cultural-association/residence are 7 distinct relation types | yes, `territory-control.md:27` |
| `TERR-02` control is real only through a declared causal requirement; a bare ownership-field assignment is never control | yes, `:100` |
| `TERR-03` claim without control and control without claim; contested facts must not collapse to one winner | yes, `:130` |
| `TERR-05` a Place may lie inside/span/be associated with a territory other than its controller | yes, `:170` |
| `TERR-04` | **does not exist** — see Findings |

| Candidate mechanism | Live state | Note for the mapper |
|---|---|---|
| `regional_sovereignty` | `done` / `observed` (`code_trace`, 2026-09-17) | **Binding trap — read this before mapping.** `RegionalSovereigntyService` has *zero real callers* anywhere in `src/`. The real live mechanism is `FactionInfluenceService` (`src/world/influence.py`), already corrected once in the registry. Do not re-introduce the wrong binding. |
| `city` | `partial` / `observed` (`code_trace`, 2026-09-19) | A City is not its own class — a City *is* a `RegionState` (`src/core/state.py::RegionState`). `RegionState.owner_faction_id` is the single ownership slot, which is the crux of the TERR-01/03 conflict below. |
| `regional_trauma` | `done` / **`contradicted`** (`corpus_run`, 2026-09-17) | Wired and real, but the Lair region measurably never accumulates trauma in a real corpus run. Same shape as `camp`. |
| `settlement_capacity_axis` | `gap` / no verdict | Include only if evidence genuinely supports an edge; a `gap` mechanism usually maps to `UNKNOWN`, not to a forced edge. |

## Scope

- Populate `registries/rule_mechanism_edges.yaml` with real `REALIZES` / `PARTIALLY_REALIZES` /
  `CONSTRAINED_BY` edges for TERR-01, TERR-02, TERR-03, TERR-05 against their actual mechanisms.
  Every edge carries a real evidence citation (a code path, a Rule's own repository-evidence prose,
  or both) and a date. No edge without a citation.
- Populate `registries/rule_classifications.yaml` with one aggregate realization verdict per Rule —
  a **human judgment call**, never mechanically derived from the edge list.
- Populate `registries/mechanism_causal_edges.yaml` only where a real producer→consumer fact exists
  among the mapped mechanisms. Zero rows is an acceptable outcome; invented edges are not.
- Generate the **Territory-only** management view across `architecture.md` §8's six axes: DESIGN,
  REALIZATION, IMPLEMENTATION, VERIFICATION, INTEGRATION, OBSERVED OUTCOME. Generated, never
  hand-maintained. Never collapsed into a single score or percentage.
- Apply the axis-model prose convention from `docs/plans/status_axis_model.md` §4 to
  `regional_trauma`: its `verified.note` should name which of STARVED / REACH-LIMITED /
  genuinely-broken applies. Its existing note already describes correct, wired code defeated by real
  conditions — i.e. STARVED — but confirm against the note rather than assuming.
- Record **every schema friction point** hit while mapping. M1 is the one milestone where a bounded
  M0 schema revision is expected and budgeted; it is not expected to recur at M3/M4.

## Out of Scope

- Any domain other than Territory/Control. Combat is M4.
- The drift detector — that is M2.
- **Fixing the TERR-04 dangling reference.** Record it as a finding; it needs its own ticket
  against the frozen Catalog, not a quiet edit inside a mapping slice.
- Changing any mechanism's `state` or `verified.verdict`. If mapping produces evidence that a
  mechanism's registry state is wrong, that is a finding to report, not an edit to make here.
- Resolving the TERR-01/TERR-03 vs. `owner_faction_id` conflict in code. M1 *records* the conflict;
  fixing the simulation's territory model is a separate design decision the user has not made.
- Any CI wiring.

## Acceptance Criteria

1. All four real TERR Rules have at least one mapping entry, or an explicitly recorded reason for
   having none. TERR-04 is not mapped and not invented.
2. Every edge in `rule_mechanism_edges.yaml` carries a real evidence citation and a date. Zero
   uncited edges.
3. `rule_classifications.yaml` carries one aggregate verdict per mapped Rule, each with evidence and
   a review date, and each visibly a judgment rather than a mechanical roll-up of its edges.
4. M0's validator passes on the populated files with **zero manual overrides of a reported
   violation**. If the validator reports a violation, either the data or the schema changes — never
   the check.
5. The Territory management view exists and gives an **explicit state for every one of the six
   axes**. `UNKNOWN` is a legitimate, complete answer where no suitable evidence exists (e.g.
   "OBSERVED OUTCOME: UNKNOWN — no runtime evidence currently exists"). A silently unrendered axis is
   the actual failure condition; the presence of `UNKNOWN` is not.
6. The view shows `mapped`/`unmapped` and `verified`/`unverified` counts alongside any
   classification breakdown, per the pre-filtered-sample lesson in
   `TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN`. No single collapsed completion number
   or badge anywhere.
7. Schema friction points are written down, each either resolved within M1's budgeted bounded schema
   revision or explicitly deferred with a reason.
8. No mechanism's `state` or `verified.verdict` value changes; a diff of `registries/mechanisms.yaml`
   shows only `verified.note` prose edits, if any.

## Related Tickets

- `TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC` — parent; this is milestone M1.
- `TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION` (DONE) — built the schemas/validator this populates.
- `TCK-20260923-STATUS-VOCABULARY-RECONCILIATION` (DONE) — fixed the vocabulary before real data
  landed. Its `docs/plans/status_axis_model.md` governs every status word used here.
- `TCK-20260920-MECHANISM-BOUND-UNVERIFIED-INSTRUMENT-RUN` — source of AC 6's counts requirement.
- `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` (DONE) — precedent for recording a
  measured-but-deliberately-unfixed behavior.

## Related Docs

- `docs/world_rules/places-culture/territory-control.md` — the four Rules
- `docs/plans/simulation_semantic_control_plane/roadmap.md` — M1 goal/deliverables/exit criteria
- `docs/plans/simulation_semantic_control_plane/architecture.md` §3 (schema), §7 (UNKNOWN is
  permanent), §8 (the six axes)
- `docs/plans/simulation_semantic_control_plane/rollout_plan.md` — Stage B
- `docs/plans/status_axis_model.md` — the four-axis binding; governs status vocabulary here

## Related Stored Artifacts

- `stored_artifacts/TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION/{investigation,plan,test_plan}.md`
- `stored_artifacts/TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC/{plan,investigation,test_plan}.md`

## Related Code Areas

- `registries/{rule_mechanism_edges,rule_classifications,mechanism_causal_edges}.yaml`
- `tools/semantic_control_plane/{registry.py,rule_catalog.py}`
- `src/world/influence.py::FactionInfluenceService` (the real sovereignty binding)
- `src/core/state.py::RegionState` (`owner_faction_id` — the single ownership slot)
- `src/world/consequences.py::RegionalConsequenceService` (`regional_trauma`)

## Assumptions / Open Questions

- **TERR-01 `CONFLICTING` is settled design, not a prediction to test.** *Confirmed 2026-09-23 by
  the Catalog's author; verified in the doc.* `architecture.md:132` uses TERR-01 as its own worked
  example: "`TERR-01` is `CONFLICTING` (a shared field actively serves three incompatible concepts)
  even though the mechanisms reading `owner_faction_id` are all `state: done` — the code works
  exactly as written; the semantics it expresses are wrong." TERR-03 follows the same shape.
  Still record the evidence rather than copying the verdict across — but this is a documented
  precedent to apply, not an open question.

- **Use this litmus test for every `CONFLICTING` vs `PARTIAL` call in this slice** (the Catalog's
  own consistent rule across precedents):
  - **`CONFLICTING`** — the current representation *actively, structurally forecloses* representing
    the Rule's required distinction. Usually one overloaded field or slot serving 2+ incompatible
    concepts at once, so the missing piece cannot be added without restructuring.
    `RegionState.owner_faction_id` is the textbook overloaded-slot case.
  - **`PARTIAL`** — a real, valid, non-contradictory *narrower slice*. It doesn't claim
    completeness, but nothing blocks eventually adding the rest. Precedent:
    `docs/world_rules/README.md:725`, Batch 11B's culture reassessment — "PARTIAL, not CONFLICTING…
    nothing treats its four axes as culture's complete definition."

- **Open — genuinely undecided, decide on evidence:** TERR-02 says a bare ownership-field assignment
  never by itself constitutes real control. Per the Catalog author, this sits on a *different axis*
  than the one above: the question is `SUPPORTED` vs `MISSING` (does a real causal-basis mechanism
  exist at all?), not `PARTIAL` vs `CONFLICTING`. It turns on whether `FactionInfluenceService`
  supplies a genuine causal requirement — presence, administrative reach, enforcement, connectivity
  — or merely writes the ownership field. Nothing is pre-loaded here deliberately.
- **Open:** where the generated Territory view lives (path and format) is undecided — M0
  deliberately left rendering out. Follow the existing generated-view precedent
  (`mechanism_system_rollup_view.md` and siblings are regenerated, never hand-edited) and state the
  choice.
- **Open:** whether TERR-05 has any implementing mechanism at all. A `MISSING` or `UNKNOWN` verdict
  is a complete, acceptable answer — resist inventing an edge to avoid an empty row.
- **Note:** `regional_trauma` is `contradicted` on a runtime instrument. Under the axis model this
  is a real signal about runtime reach, not a reason to exclude it from the mapping.

## Implementation Notes

_To be completed by the implementer._

Sequencing hint: classify the Rules **after** laying down the edges, not while doing it. The
classification is deliberately a separate judgment (`architecture.md` §3/§4), and doing both in one
pass is how it silently becomes a mechanical roll-up — the exact mistake the three-schema split
exists to prevent.

## Test Summary

_To be completed by the implementer._

Expected shape: validator passes on the populated files; a regression assertion for AC 8 that no
`state`/`verdict` changed; a test that the generated view renders all six axes including any
`UNKNOWN`. Do not manufacture coverage beyond the data's own invariants.

## Files Changed

_To be completed by the implementer._

## Completion Summary

_To be completed by the implementer._

## Findings Recorded During Scoping

1. **`TERR-04` is a stale citation, NOT a coverage gap.** *Resolved 2026-09-23 by the Catalog's
   author (`world-rule-catalog-design`); verified against the file before recording here.*
   `territory-control.md:30` cites "jurisdiction (legal/institutional applicability, see TERR-04)",
   but jurisdiction was admitted as an **Inherited entry**, not a new Domain Rule — a direct reuse of
   Batch 10's `LAW-03` with no new semantics (`territory-control.md:217`, the heading
   "Jurisdiction's territorial basis is one declared scope among several", which carries **no
   TERR-0N ID**, and `:324`, "Inherited jurisdiction entry → Law/Enforcement (LAW-03, Batch 10)").
   Under the Catalog's own admission discipline, Inherited entries never receive a local ID, so a
   `TERR-04` heading was never going to exist *by design*. Corroborating: none of TERR-01's other
   six relation types carries a self-referential `TERR-0N` pointer either — "one ID per relation
   type" was never the pattern.

   So the numbering gap is correct and nothing is missing from the Catalog. Only TERR-01's inline
   citation is wrong — a leftover from a drafting guess made before the admission pass concluded
   Inherited. **M0's validator rejecting `TERR-04` is correct behavior, not evidence against the
   Catalog.** Still deliberately not fixed here: a one-line edit to a frozen doc wants its own
   traceability. Tracked as `TCK-20260923-TERR01-STALE-JURISDICTION-CITATION` (hotfix).
2. **`regional_sovereignty`'s binding was already wrong once.** `RegionalSovereigntyService` has
   zero real callers; the live mechanism is `FactionInfluenceService`. Recorded here so M1 does not
   re-introduce the plausible-but-dead binding.
3. The frozen Catalog's own §"Implementation Candidates — Non-Binding" prose for this domain is M3
   ingestion input. Per `roadmap.md`, re-verify any such claim against current code rather than
   promoting it as already-current fact.
