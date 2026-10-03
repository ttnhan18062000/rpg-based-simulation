---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260923-STATUS-VOCABULARY-RECONCILIATION
phase: done
date: 2026-09-23
tags: [architecture, schema, taxonomy, registry, documentation]
---

# TCK-20260923-STATUS-VOCABULARY-RECONCILIATION

## Title

Reconcile the four overlapping mechanism/rule status vocabularies into one declared axis model

## Status

DONE

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

Implemented exactly per `staging_artifacts/TCK-20260923-STATUS-VOCABULARY-RECONCILIATION/plan.md`
Steps 1-9, with the architecture-review advisory folded into Steps 1 and 8:

- **Step 1** — authored `docs/plans/status_axis_model.md` (new doc): four-axis table (A/B enforced
  with 93 real rows, D enforced but empty, C aspirational/unenforced — explicitly ranked, not
  co-equal), a 7-row binding table covering all AC-2-required pairs (`MISSING`×2, `OFF`/`INERT-OFF`,
  `partial`×`PARTIAL`, `gated`×`OFF`, `orphan`×`DORMANT`, `skeleton`'s non-relationship), a closing
  "all other cross-axis value pairs not listed above have no defined relationship" line (the
  architecture-review advisory #2, so AC 2 is satisfied without enumerating the full combinatorial
  cross product), both homograph decisions (§3: keep both words in both cases), and the
  STARVED/REACH-LIMITED decision (§4: no new registry field — §11 admission test fails Q4/Q12 against
  `tactical_decision`; a documented `verified.note` prose convention instead, explicitly not
  validator-enforced, AC 6 not triggered). Used the plan's corrected citations
  (`docs/world_rules/README.md:172`, `roadmap.md:581`,
  `simulation_semantic_control_plane/architecture.md:189-190`), verified by direct grep before
  writing, not investigation.md's original mis-cited `roadmap.md:171-177`.
- **Steps 2-6** — one-line cross-reference pointers added at all four AC-5-required homes
  (`registries/mechanisms.yaml` header after line 99, `tools/mechanism_registry/registry.py`
  docstring before `Usage:`, `core_rpg_design_direction.md` §10 after the REACH-LIMITED bullet,
  `simulation_semantic_control_plane/architecture.md` end of §4) plus the optional fifth pointer
  (`tools/semantic_control_plane/registry.py` docstring). All are prose-only pointer lines, no
  vocabulary content duplicated, no enum/frozenset touched.
- **Step 7** — new permanent test `tests/unit/tools/test_status_axis_model_cross_references.py`
  proving the doc exists/is non-empty and all four required homes contain the literal string
  `status_axis_model.md`. 2/2 passed.
- **Step 8 (AC 7)** — per the architecture-review advisory #1, built a real deterministic check
  instead of eyeballed prose: a small script that parses `git diff registries/mechanisms.yaml`'s
  hunk headers and fails loudly if any changed line falls at/after the pre-edit `layers:` boundary
  (original line 109). Run once (scratchpad-only, not committed — this is a one-time/CI-adjacent
  verification per the plan's own Step 8 reasoning, not a permanent 93-row baseline test that would
  false-positive on every legitimate future `state`/`verdict` correction): output confirmed
  "AC-7 OK: zero changed lines at/after the layers: boundary." Cross-checked by reading the full
  `git diff registries/mechanisms.yaml` directly — the only hunk is 3 added header-comment lines
  between the existing "instrument finding..." line and "Validate with:", entirely inside the
  header block.
- **Step 9** — ran the three scoped pytest commands (all green: 83 passed
  `test_mechanism_registry.py`, 25 passed `test_semantic_control_plane_schema.py`, 2 passed the new
  cross-reference test). Confirmed AC 8: `git diff --stat` on
  `registries/rule_classifications.yaml`, `registries/rule_mechanism_edges.yaml`,
  `registries/mechanism_causal_edges.yaml` shows no output (untouched); `git diff
  tools/semantic_control_plane/registry.py` shows a docstring-only 3-line addition, with
  `VALID_RULE_CLASSIFICATIONS`/`VALID_RULE_MECHANISM_EDGE_TYPES` unchanged, confirmed both by the
  diff itself and by the full unchanged pass of `test_semantic_control_plane_schema.py` (which
  directly asserts those frozensets' exact value sets).

No deviations from the plan's approved shape. Ran `graphify update .` after adding the new test
file under `tests/`.

Sequencing note (retained from Scope): the registry vocabularies (1) and (2) were the only ones with
real data behind them (93 mechanism rows) going in. Treated them as the load-bearing reference per
the plan, rather than reshaping them to fit two vocabularies that have never been applied to a row.

## Test Summary

AC 4 resolved to "no new registry field," so no validator accept/reject fixture pair was needed
(AC 6 not triggered — recorded explicitly as a decision, not silently skipped).

Ran, all green:
- `python3 -m pytest tests/unit/tools/test_mechanism_registry.py -q` — 83 passed
- `python3 -m pytest tests/unit/tools/test_semantic_control_plane_schema.py -q` — 25 passed
- `python3 -m pytest tests/unit/tools/test_status_axis_model_cross_references.py -q` — 2 passed (new)

AC 7's zero-row-reclassification requirement was verified by a deterministic script (parses
`git diff registries/mechanisms.yaml`'s hunk headers, fails if any changed line falls at/after the
pre-edit `layers:` boundary) plus manual confirmation of the actual diff — both show the only change
is 3 added header-comment lines, no row content touched. Not run as a permanent pytest test per the
plan's own reasoning (a hardcoded 93-row baseline would break on every legitimate future
`state`/`verdict` correction, an unrelated maintenance tax).

Used `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3` — the bare `python3` on PATH
lacks `pydantic` and fails collecting `tests/conftest.py`, a known local-sandbox gap, not a real
test failure.

## Files Changed

- `docs/plans/status_axis_model.md` (new) — the axis-model doc itself: four-axis table, binding
  table, homograph decisions, STARVED/REACH-LIMITED decision, §10 enforcement-status statement.
- `registries/mechanisms.yaml` — two-line cross-reference added to the header comment block
  (lines 100-101), no row content changed.
- `tools/mechanism_registry/registry.py` — three-line cross-reference added to the module docstring
  before `Usage:`, no code/constant changed.
- `docs/brainstorm/core_rpg_design_direction.md` — cross-reference + aspirational-status note added
  after the §10 REACH-LIMITED bullet; the ten-value code block itself unchanged.
- `docs/plans/simulation_semantic_control_plane/architecture.md` — cross-reference added at the end
  of §4; `VALID_RULE_CLASSIFICATIONS`'s code block unchanged.
- `tools/semantic_control_plane/registry.py` — optional docstring-only cross-reference added
  (Step 6); `VALID_RULE_CLASSIFICATIONS`/`VALID_RULE_MECHANISM_EDGE_TYPES` frozensets unchanged.
- `tests/unit/tools/test_status_axis_model_cross_references.py` (new) — permanent test proving the
  axis-model doc exists and all four AC-5-required homes reference it.
- `staging_artifacts/TCK-20260923-STATUS-VOCABULARY-RECONCILIATION/plan.md` — added a "Deviations"
  section documenting the AC-7 verification-shape change (see Implementation Notes).
- `staging_artifacts/TCK-20260923-STATUS-VOCABULARY-RECONCILIATION/investigation.md`,
  `staging_artifacts/TCK-20260923-STATUS-VOCABULARY-RECONCILIATION/test_plan.md` — created during
  this run's own Investigate/Plan phases (untracked prior to this close); listed here per ticket
  hygiene even though not authored by the Implement phase itself.
- `tickets/inprogress/TCK-20260923-STATUS-VOCABULARY-RECONCILIATION.md` — this ticket file (Status,
  Implementation Notes, Test Summary, Files Changed, Completion Summary).
- `agent-monitoring/data/2026-W39/tools.jsonl` — auto-updated per-tool-call shard (pre-existing
  modification from prior session tool calls, not authored by this Implement pass).

No `src/` files were changed.

## Completion Summary

Reconciled the four overlapping mechanism/rule status vocabularies (registry `state`, registry
`verified.verdict`, compass §10 runtime status, control-plane Rule realization) into one declared
axis model at `docs/plans/status_axis_model.md`, without merging any of them and without
reclassifying any existing mechanism row. The doc states which axis is canonical for which question,
binds every cross-axis value pair the ticket named (both homographs, `partial`/`PARTIAL`,
`gated`/`OFF`, `orphan`/`DORMANT`, `skeleton`'s non-relationship) with an explicit
equivalence/implication/correlation/undefined label, and records two decisions: keep both homograph
pairs as separate words (never rename, since renaming Axis D would widen M0's already-landed schema
out of scope), and represent STARVED/REACH-LIMITED as a documented `verified.note` prose convention
rather than a new registry field (§11 admission test fails on no current consumer and duplication of
the existing `note` field). All four AC-5-required vocabulary homes now cross-reference the new doc,
proven by a new permanent test. AC 7 (zero mechanism row reclassification) and AC 8 (M0 schema
byte-identical) were both verified deterministically: the only change to `registries/mechanisms.yaml`
is two header-comment lines, and `tools/semantic_control_plane/registry.py`'s only change is a
docstring addition with both frozensets untouched. All three scoped pytest suites pass (83 + 25 + 2
tests, 110 total).
