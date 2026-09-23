---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE
phase: done
date: 2026-09-23
tags: [architecture, schema, registry, world]
---

# TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE

## Title

M1 — first operational slice: map Territory/Control Rules to real mechanisms and render the first
domain management view

## Status

DONE

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

Implemented per `staging_artifacts/TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE/plan.md`'s 13
ordered steps, edges laid down and validator-clean before the separate classification pass (Step 5
run only after Steps 1-2 were on disk), exactly per the sequencing hint below.

1. **AC 7 schema-friction disposition (resolved: deferred with reason, no schema revision).**
   `registries/mechanism_causal_edges.yaml`'s `producer_mechanism_id`/`consumer_mechanism_id` row
   shape models "A produces input for B." The one candidate relation found during mapping —
   `regional_sovereignty` (`FactionInfluenceService`, `src/world/influence.py`) and
   `betrayal_siege_war` (`MilitaryConflictPhase`, `src/engine/military_conflict.py`)
   independently and inconsistently writing the same durable field
   (`RegionState.owner_faction_id`) — is a conflict/duplication relation, not a producer→consumer
   one, and does not fit this schema's shape (no `edge_type` field exists here; the relation is
   also not a `producer == consumer` self-edge, the schema's only other special case). Disposition:
   the file stays at zero rows (a correct, documented outcome, not a gap); an inline header comment
   now records this reasoning for a future mapper, and the same fact is cited as evidence on the
   `TERR-01`/`TERR-03` → `betrayal_siege_war` edges in `rule_mechanism_edges.yaml`. No schema field
   was added or changed.
2. **Threshold-mismatch finding — now confirmed three-way, not just two code paths.** The
   already-known `FactionInfluenceService` (`src/world/influence.py`, `±50.0`) vs.
   `WorldDynamicsSystem` (`src/engine/world_dynamics.py`, `±100.0`) inconsistency was cross-checked
   against the two governing docs during this implementation pass:
   `docs/mechanics/regional_sovereignty.md:22-24` states `±100.0` as canonical ("Hero Guild
   Control: Influence > 100.0", "Monster Horde Control: Influence < -100.0", "Contested: Between
   -50.0 and 50.0"), matching `world_dynamics.py`; but
   `docs/world/regional_sovereignty_runtime_contract.md:24,109` states `±50.0` as canonical ("one
   faction's influence >= +50... or <= -50", "The influence threshold (±50) is configurable
   per-region"), matching `influence.py`. So the Mechanics Bible chapter and the runtime contract
   doc disagree with **each other**, independent of either code path. Recorded as evidence on the
   `TERR-02` / `regional_sovereignty` edge; explicitly not fixed here (Out of Scope — no `src/` or
   `docs/` edit made). The doc-vs-doc disagreement itself (as distinct from the already-known
   code-vs-code one) is worth a separate follow-up ticket — not filed by this ticket.
3. Pointer to the fuller record: `staging_artifacts/TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE/investigation.md`'s
   "Risks and Open Questions" section covers both findings' original discovery context.

One implementation-time correction from the plan's own draft text (recorded in `plan.md`'s
Deviations section): the plan's own suggested header-comment wording for
`rule_mechanism_edges.yaml` (Step 1) would have spelled out the literal string `TERR-04`, which
conflicts with Step 6's own `test_terr04_never_appears_in_populated_registries` guard (a
literal-string check over the whole file, comments included). Reworded to describe the stale
citation without spelling out the ID it points at; no change to the guard's own intent or
strictness.

Sequencing hint (already followed): classify the Rules **after** laying down the edges, not while
doing it. The classification is deliberately a separate judgment (`architecture.md` §3/§4), and
doing both in one pass is how it silently becomes a mechanical roll-up — the exact mistake the
three-schema split exists to prevent.

## Test Summary

Scoped regression run (117 tests, all passing):
```
pytest tests/unit/tools/test_semantic_control_plane_schema.py \
       tests/unit/tools/test_mechanism_registry.py \
       tests/unit/tools/test_territory_control_view.py \
       tests/unit/tools/test_terr_mapping_mechanism_state_stability.py -v
```
- `test_semantic_control_plane_schema.py` (28 tests, 3 new: `test_all_four_terr_rules_have_a_classification_record`,
  `test_terr04_never_appears_in_populated_registries`,
  `test_real_rule_mechanism_edges_have_nonempty_evidence_and_date`) — all pass, including
  `test_all_three_schemas_pass_on_real_seed_data` and `test_documented_cli_invocation_actually_runs`
  (real subprocess run of `tools/semantic_control_plane/registry.py`, confirms AC 4's zero-manual-
  override requirement against the real populated files).
- `test_mechanism_registry.py` (regression surface, zero code changes to
  `tools/mechanism_registry/` this ticket makes) — all 83 tests pass unmodified.
- `test_territory_control_view.py` (5 new tests) — six-axis rendering, `UNKNOWN` positive control,
  mapped/unmapped + verified/unverified counts, no-collapsed-badge guard, `--check` staleness
  detection, and committed-output-matches-fresh-render regression — all pass.
- `test_terr_mapping_mechanism_state_stability.py` (1 new test, AC 8 guard) — run once against the
  real `registries/mechanisms.yaml` *before* the Step 4 note edit (baseline) and once *after*
  (regression) — passes both times.

Manual `git diff registries/mechanisms.yaml` confirms the only change is inside
`regional_trauma`'s `note: >-` block (STARVED-convention prose); no `state`/`verified.instrument`/
`verified.verdict`/`verified.date` line changed anywhere in the file, on this or any other
mechanism.

`make territory-control-view` run twice in a row (before and after committing) produces byte-
identical output — the generator is deterministic against the committed registry state.

## Files Changed

- `registries/rule_mechanism_edges.yaml` — 6 real edges (TERR-01/02/03/05 against
  `regional_sovereignty`, `betrayal_siege_war`, `city`), each with evidence + date.
- `registries/rule_classifications.yaml` — 4 real classifications (TERR-01: CONFLICTING, TERR-02:
  PARTIAL, TERR-03: CONFLICTING, TERR-05: PARTIAL), each with evidence + review_date.
- `registries/mechanism_causal_edges.yaml` — unchanged row count (still zero rows); added an
  inline header comment recording the AC 7 schema-friction disposition.
- `registries/mechanisms.yaml` — `regional_trauma`'s `verified.note` prose only (STARVED-convention
  naming per `docs/plans/status_axis_model.md` §4); no `state`/`verified.verdict` change anywhere
  in the file.
- `tools/semantic_control_plane/generate_territory_control_view.py` (new) — Territory-only
  six-axis management view generator, mirroring
  `tools/mechanism_registry/generate_mechanism_system_rollup_view.py`'s conventions.
- `Makefile` — new `territory-control-view` target.
- `docs/brainstorm/territory_control_management_view.md` (new, generated) — the real Territory
  management view output.
- `docs/brainstorm/mechanism_verification_view.md` (generated, regenerated as a side effect of
  running `test_mechanism_registry.py`'s own `test_make_target_generates_verification_view`,
  which calls `make mechanism-verification-view` for real) — the only content change is
  `regional_trauma`'s own row picking up the same STARVED-convention note prose edited in
  `registries/mechanisms.yaml`; never hand-edited.
- `tests/unit/tools/test_terr_mapping_mechanism_state_stability.py` (new) — AC 8 state/verdict
  stability guard for the five TERR-implicated mechanisms.
- `tests/unit/tools/test_semantic_control_plane_schema.py` — 3 new cross-schema data-integrity
  tests.
- `tests/unit/tools/test_territory_control_view.py` (new) — Territory view rendering tests.
- `tickets/inprogress/TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE.md` — Implementation Notes,
  Test Summary, Files Changed, Completion Summary, Status filled in.
- `staging_artifacts/TCK-20260923-M1-TERRITORY-CONTROL-MAPPING-SLICE/plan.md` — Deviations section
  added (one wording-only correction, no decision change).

## Completion Summary

Populated the Simulation Semantic Control Plane's three M0 schemas with their first real data: 6
Rule→Mechanism edges and 4 Rule classifications covering all four real Territory/Control Rules
(TERR-01, TERR-02, TERR-03, TERR-05), with `mechanism_causal_edges.yaml` correctly staying at zero
rows (a documented, evidenced outcome, not a gap). Applied the STARVED-naming convention to
`regional_trauma`'s note only, with zero `state`/`verified.verdict` changes anywhere in
`registries/mechanisms.yaml` (confirmed by both a dedicated regression test and a manual diff).
Built and wired a new Territory-only management-view generator rendering all four Rules across
`architecture.md` §8's six axes (DESIGN, REALIZATION, IMPLEMENTATION, VERIFICATION, INTEGRATION,
OBSERVED OUTCOME), with explicit `UNKNOWN` values, mapped/unmapped and verified/unverified counts,
and no collapsed score — generated via `make territory-control-view` into
`docs/brainstorm/territory_control_management_view.md`. M0's validator passes with zero manual
overrides. All 8 acceptance criteria are satisfied: AC 1-3 by the populated edges/classifications
(TERR-04 never written, confirmed by a dedicated guard test), AC 4 by the clean validator run, AC
5-6 by the generated view and its own test coverage, AC 7 by the documented schema-friction
disposition (Implementation Notes above), and AC 8 by the note-only `mechanisms.yaml` diff. No
`src/` file was touched anywhere in this ticket.

Two fixes were applied during Verify before Finalize: (1) a stale duplicate of this ticket's own
source file under `tickets/todos/` was deleted as part of Verify-phase cleanup — the ticket
originated directly in `tickets/todos/` (no subfolder), so its removal is the full required
cleanup step, confirmed gone at Finalize time; (2) the TERR-04 follow-up cross-reference in
"Findings Recorded During Scoping" (finding 1) was corrected to point at the actual closed
implementing ticket, `TCK-20260923-TERR01-CITATION-FIX` (hotfix, DONE, confirmed present in
`tickets/done/`), rather than the earlier tracking ID `TCK-20260923-TERR01-STALE-JURISDICTION-CITATION`
under which the work was originally filed.

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
   traceability. Tracked as `TCK-20260923-TERR01-STALE-JURISDICTION-CITATION`, implemented and
   closed under the ID `TCK-20260923-TERR01-CITATION-FIX` (hotfix, DONE — see
   `tickets/done/TCK-20260923-TERR01-CITATION-FIX.md`).
2. **`regional_sovereignty`'s binding was already wrong once.** `RegionalSovereigntyService` has
   zero real callers; the live mechanism is `FactionInfluenceService`. Recorded here so M1 does not
   re-introduce the plausible-but-dead binding.
3. The frozen Catalog's own §"Implementation Candidates — Non-Binding" prose for this domain is M3
   ingestion input. Per `roadmap.md`, re-verify any such claim against current code rather than
   promoting it as already-current fact.
