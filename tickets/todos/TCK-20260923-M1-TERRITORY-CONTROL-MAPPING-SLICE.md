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

- **Expected outcome, stated so it can be falsified rather than manufactured:** TERR-01 and TERR-03
  are expected to classify `CONFLICTING`. TERR-01 requires seven independently-representable
  relation types and TERR-03 forbids collapsing contested cases to one winner, while the
  implementation carries a single `RegionState.owner_faction_id` slot;
  `territory-control.md:76` already states that slot "is itself incompatible with the divergence
  TERR-01/TERR-03 require." **If the evidence does not support `CONFLICTING`, record what it does
  support.** Do not reach for `CONFLICTING` because this ticket predicted it.
- **Open:** TERR-02 says a bare ownership-field assignment never constitutes control, and the
  implementation's control signal is largely that assignment. Whether this is `CONFLICTING` or
  `PARTIAL` depends on whether `FactionInfluenceService` supplies a real causal requirement. Decide
  on evidence.
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

1. **`TERR-04` is a dangling cross-reference.** `territory-control.md:30` cites "jurisdiction
   (legal/institutional applicability, see TERR-04)" but no `TERR-04` heading exists anywhere in
   `docs/world_rules/` — the file's own numbering runs 01, 02, 03, 05. Either the Rule was removed
   or renamed without updating the reference, or it was never written. This matters beyond
   cosmetics: M0's validator resolves `rule_id` against a **live scan** of `docs/world_rules/`
   headings, so any attempt to map `TERR-04` fails validation correctly. Needs its own ticket
   against the frozen Catalog — deliberately not fixed here.
2. **`regional_sovereignty`'s binding was already wrong once.** `RegionalSovereigntyService` has
   zero real callers; the live mechanism is `FactionInfluenceService`. Recorded here so M1 does not
   re-introduce the plausible-but-dead binding.
3. The frozen Catalog's own §"Implementation Candidates — Non-Binding" prose for this domain is M3
   ingestion input. Per `roadmap.md`, re-verify any such claim against current code rather than
   promoting it as already-current fact.
