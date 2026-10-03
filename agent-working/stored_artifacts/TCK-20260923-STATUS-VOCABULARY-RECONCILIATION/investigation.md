---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260923-STATUS-VOCABULARY-RECONCILIATION
artifact_type: investigation
tags: [architecture, schema, taxonomy, registry, documentation]
---

# Investigation — TCK-20260923-STATUS-VOCABULARY-RECONCILIATION

## Current Behavior

Four real, independently-maintained status vocabularies exist today. Confirmed by direct read of
each definition site, not by re-trusting the ticket's own table:

**(1) Registry `state`** — `registries/mechanisms.yaml` header lines 70-71 (six classes:
`done | partial | gap | orphan | gated | skeleton`), enforced by
`tools/mechanism_registry/registry.py::VALID_STATES` (L139) and Invariant 4 of `validate()`
(L300-307). 93 real mechanism rows carry a value (`grep -c "  - id:" registries/mechanisms.yaml`
= 93). Answers: is the mechanism built/reachable.

**(2) Registry `verified.verdict`** — same file, header lines 73-98, `VALID_VERDICTS` (L149:
`observed | contradicted | inconclusive`), `_REQUIRED_VERIFIED_FIELDS` (L150), enforced by
Invariants 5/6 (L348-373). Paired with `instrument` (`STATIC_INSTRUMENTS = {code_trace}`,
`RUNTIME_INSTRUMENTS = {census, scenario, corpus_run}`, L146-148). Answers: what did an instrument
actually find, and how strong is that evidence (static vs. runtime, explicitly never conflated —
header lines 83-91). `state_counts` (`_rollup_stats()`, L793-846) rolls up `state` per system/group;
it does **not** roll up `verdict` at all — verdict has no aggregate view today, only the per-row
value and the verification view render (`mechanism_verification_view.md`).

**(3) Compass §10 runtime status** — `docs/brainstorm/core_rpg_design_direction.md` lines 467-482.
The full list appears exactly once (line 472):
`MISSING · DESIGNED · EXPERIMENTAL · OFF · DORMANT · STARVED · REACH-LIMITED · LIVE · DEPRECATED ·
REPLACED`. Only two of the ten values get a real one-line definition anywhere in the document —
**STARVED** (line 475: "a live path whose conditions almost never occur in real simulation") and
**REACH-LIMITED** (line 476, added 2026-09-20: "live and reached, but only inside a narrow slice of
reality"). The other eight (`MISSING`, `DESIGNED`, `EXPERIMENTAL`, `OFF`, `DORMANT`, `LIVE`,
`DEPRECATED`, `REPLACED`) are never defined anywhere in this file or elsewhere in `docs/` — confirmed
by `grep -n` for each term across `core_rpg_design_direction.md`: none produces a second hit beyond
the bare list itself. Line 480 ("Mechanism metadata worth carrying eventually... runtime status,
validation scenario") is explicitly future-tense/aspirational, not a present commitment.

**(4) Control-plane Rule realization classification** — `docs/plans/simulation_semantic_control_plane/
architecture.md` §4 (lines 119-143): `SUPPORTED | PARTIAL | CONFLICTING | MISSING | INERT-OFF |
UNKNOWN`. §4 explicitly states this is "reused, not reinvented" — it is the same vocabulary the
World Rule Catalog's own review-export batches already use (confirmed live in
`docs/world_rules/roadmap.md` lines 171-177, 581, and
`docs/world_rules/review-exports/culture-belief-batch-11b-review.md` line 252: "Classified per the
CONFLICTING/INERT-OFF/MISSING distinction established in prior batches"). Enforced today by
`tools/semantic_control_plane/registry.py::VALID_RULE_CLASSIFICATIONS` (L58-59) and
`validate_all()`. This is the vocabulary M0 (`TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION`, already
merged into this worktree) just built schema+validator for, with **zero populated rows** — M1 is
what populates real Territory mapping data against it (per `roadmap.md` M0/M1 split, lines 34-108).
Answers: does the world Rule's semantic requirement hold, given its mapped mechanisms — a judgment
call, not mechanically derived from mechanism `state` (architecture.md §4, lines 128-136: `TERR-01`
is `CONFLICTING` even though every mechanism reading `owner_faction_id` is `state: done` — the code
works exactly as written, the semantics it expresses are wrong).

**The `tactical_decision` STARVED evidence, read directly** —
`registries/mechanisms.yaml` lines 186-225: `state: done`, `verified.verdict: contradicted`,
`instrument: corpus_run`. The note (lines 196-204) states explicitly: "state stays `done` — no
evidence the decision logic itself is wrong, only that it essentially never selects ATTACK in these
worlds' real play" — 0-2 real `resolve_attack()` calls per 1000-2000 ticks, independently
corroborated three times over six weeks and root-caused by
`TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` (DONE, confirmed read: two compounding
causes — strategic layer essentially never assigns `DEFEAT_ENEMY`, and even when the brain runs,
`hostiles` was non-empty 0 of 1130 real calls). This is a textbook STARVED case by §10's own
one-line definition ("a live path whose conditions almost never occur in real simulation") and the
registry today can only express it as `done` + `contradicted`, which loses the specific
"conditions-almost-never-occur" shape (a `contradicted` verdict could equally mean "the code is
outright broken," a materially different diagnosis requiring a materially different fix).

## Mechanics / Engine Constraints

This ticket is a documentation/vocabulary-contract ticket, not a simulation-behavior change — no
Mechanics Bible chapter or Engine Contract formula constrains it directly. The relevant constraint
is architectural/process, not mechanical: `docs/plans/simulation_semantic_control_plane/
rollout_plan.md` Stage A (lines 18-32) — "Do not design the final schema up front... Stage B is
where real data pressure-tests the shape before it is locked in." This ticket must respect that
counter-pressure: it is reconciling *existing, already-enforced* vocabularies (1)/(2)/(4), not
inventing new ontology ahead of data. Binding §10 (aspirational, unenforced) risks exactly the
premature-lock-in Stage A warns against, which is why the investigation below treats §10's binding
status as an open decision rather than assuming it.

`architecture.md` §7 ("Unknown is permanent, not a bug to eliminate," lines 178-196) and §9's
non-goals (lines 221-243, esp. "No single collapsed completion percentage") are direct precedent
for this ticket's own instruction not to merge the vocabularies into one enum — the control-plane
design already independently arrived at "keep axes declared and separate, never collapse," which is
strong internal-consistency evidence for this ticket's central assumption.

## Docs Requiring Update

- `docs/plans/status_axis_model.md`: new doc (chosen home — see Risks/Open Questions below for the
  extending-vs-new-doc tradeoff) stating the axis model, binding table, and both homograph decisions
  required by AC 1-4.
- `registries/mechanisms.yaml`: header comment (near lines 70-98) needs one added cross-reference
  line pointing at the new axis-model doc, per AC 5 ("all four homes cross-reference the axis
  model").
- `docs/brainstorm/core_rpg_design_direction.md`: §10 needs a cross-reference to the axis-model doc,
  per AC 5, plus (pending the recommendation below) an explicit note that none of its ten values
  beyond STARVED/REACH-LIMITED are currently enforced or registry-bound.
- `docs/plans/simulation_semantic_control_plane/architecture.md`: §3/§4 need a cross-reference to
  the axis-model doc, per AC 5.
- `tools/mechanism_registry/registry.py`: the module/`VALID_STATES`/`VALID_VERDICTS` docstring area
  needs a one-line cross-reference to the axis-model doc, per AC 5's explicit "the registry
  validator's own docstring" requirement.

The `docs/parity_ledger/*.yaml` files are not required to change for this ticket: no entry in any
subsystem file (`substrate.yaml`, `combat_movement.yaml`, `strategic_cognition.yaml`,
`town_resource.yaml`, `progression.yaml`, `social_narrative.yaml`, `world_dynamics.yaml`,
`infrastructure.yaml`) references `mechanism_registry`, `VALID_STATES`, `VALID_VERDICTS`,
`rule_classification`, or `realization` (confirmed by `grep -rl` across the directory, zero hits) —
this ticket changes a documentation/vocabulary contract, not a verified simulation behavior, and AC
7 explicitly forbids any row-level reclassification that would create new parity evidence.

`docs/guidelines/tag_taxonomy.md` (path: `docs/guidelines/tag_taxonomy.md`, under `docs/`) is not
required to change for this ticket: it is cited in Related Docs as a structural precedent for
"a vocabulary split into declared categories" (its own Subsystem/Topic / Phase/Milestone /
Process-Skill-signal / Quality-attribute four-way split), useful as a pattern to imitate for the
axis-model doc's own structure, but this ticket does not touch the tag system itself and has no
reason to modify that file's content.

`tools/semantic_control_plane/registry.py` (path: `tools/semantic_control_plane/registry.py`, under
`tools/`, not `docs/` so not machine-checked by the coverage regex regardless, listed here for
completeness) may get a one-line docstring cross-reference alongside `VALID_RULE_CLASSIFICATIONS`
mirroring the `mechanism_registry/registry.py` change above, satisfying AC 5's "architecture.md §3/§4"
requirement without a separate docs/ bullet since the AC explicitly names the doc, not the code file,
as the cross-reference target.

## Parity Ledger Overlap

None. Grepped all eight `docs/parity_ledger/*.yaml` files for `mechanism_registry`,
`VALID_STATES`/`VALID_VERDICTS`, `rule_classification`, and `realization` — zero hits. This ticket
does not touch verified simulation behavior (AC 7 explicitly forbids any row reclassification), so
no P0/P1/P2 parity entry requires a status or evidence update as a result of this work.

## Prior Work

- `TCK-20260915-MECHANISM-REGISTRY-FOUNDATION` (DONE) — established vocabularies (1) `state` and
  (2) `verified.verdict`, and the STATIC-vs-RUNTIME evidence distinction that (2) still carries.
  Confirms the "registry vocabularies are the only ones with real data behind them (93 rows)"
  framing in the ticket's own Implementation Notes.
- `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` (DONE) — the real corpus-run
  evidence behind `tactical_decision`'s `state: done` / `verdict: contradicted` combination; closed
  as investigation-only, behavior deliberately not fixed. This is the concrete case AC 4 must
  resolve against.
- `TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION` (its stored artifacts exist at
  `stored_artifacts/TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION/`) — built vocabulary (4)'s schema
  and validator with zero populated rows, already merged into this worktree
  (`tools/semantic_control_plane/registry.py`, `tests/unit/tools/test_semantic_control_plane_schema.py`
  both present and passing). This ticket must land before M1 populates real data against that
  schema.
- `stored_artifacts/TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC/{plan,investigation,test_plan}.md` —
  **does not exist** on disk (confirmed: `stored_artifacts/` has no
  `TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC` directory, only
  `TCK-20260923-M0-SCHEMA-VALIDATOR-FOUNDATION`). This is a gap in the current ticket's own "Related
  Stored Artifacts" pointer, not something this investigation can resolve — flagged rather than
  silently worked around. It does not block this ticket's own investigation since the epic ticket
  file itself (`tickets/inprogress/` or `tickets/done/TCK-20260923-SEMANTIC-CONTROL-PLANE-EPIC.md`,
  not directly read in this pass but referenced consistently across M0's and this ticket's own text)
  and `architecture.md`/`roadmap.md`/`rollout_plan.md` carry the same design content directly.
- World Rule Catalog review-export precedent (`docs/world_rules/roadmap.md`,
  `docs/world_rules/review-exports/*.md`) — real, already-in-production usage of vocabulary (4)'s
  `MISSING`/`INERT-OFF`/`CONFLICTING` distinction across 12+ batches, which is the strongest evidence
  available for what those two specific words mean in that axis (see Anti-Drift Hazards).

## Risks and Open Questions

- **Central assumption (four axes, genuinely distinct) — investigated, holds.** Each vocabulary
  answers a different, non-substitutable question (built? evidenced-how? runs-in-practice-how-widely?
  Rule-semantics-satisfied?), confirmed by re-deriving each definition from its own source rather than
  trusting the ticket's paraphrase. `architecture.md` §4 (lines 128-136) independently makes the same
  argument for why (4) must not be equated with (1) even though both are five/six-value enums with a
  shared shape — this is direct, already-written precedent for the "same shape, different axis, do
  not conflate" conclusion this ticket needs, not just supporting color. No evidence found that
  collapsing would preserve information; recommend the assumption stands, per the ticket's own
  Out-of-Scope framing.
- **Where the axis-model doc lives — open, needs a decision, no single obviously-correct existing
  home found.** Candidates considered: (a) `registries/mechanisms.yaml`'s own header comment — ruled
  out, it is already very long (108 lines of comment before the first mechanism) and the axis model
  is about a relationship *among* four vocabularies, not solely registry-internal content; (b)
  `docs/brainstorm/core_rpg_design_direction.md` — ruled out as primary home, since binding an
  enforced 3-axis relationship inside a "brainstorm" doc whose own §10 vocabulary is unenforced
  prose inverts the intended authority direction (the enforced things should not live inside the
  aspirational doc); (c) `docs/plans/simulation_semantic_control_plane/architecture.md` — a plausible
  extension point (it already documents axis (4) and explicitly disclaims equivalence with (1) in
  §4), but it is scoped to the control-plane initiative specifically and a reader investigating only
  the Mechanism Registry (vocabularies 1/2) would not think to look inside a semantic-control-plane
  plan doc; (d) a new doc under `docs/plans/` (e.g. `docs/plans/status_axis_model.md`) sibling to
  `mechanism_registry_initiative.md` and `simulation_semantic_control_plane/`. **Recommendation: (d),
  a new doc**, specifically because none of the three existing candidates is a fact-neutral home all
  four vocabularies' own maintainers would independently think to check — the one-fact-one-home rule
  argues against duplicating the axis model into an existing doc that already has a narrower primary
  subject, not against giving a genuinely new fact (the cross-axis relationship itself, which has no
  existing home at all) its own doc. All four existing vocabulary homes get a short cross-reference
  pointer instead of the model's full content, avoiding the duplication the rule actually forbids.
- **§10 enforcement status — investigated, confirmed unenforced.** Grepped `tools/` and `src/` for
  every §10 term (`STARVED`, `REACH-LIMITED`/`REACH_LIMITED`, `DORMANT`, etc.); the only hits were an
  unrelated constant name (`EXACT_DIRTY_STARVED_CADENCE_MODULO` in
  `src/engine/candidate_selector.py`) and an unrelated ticket-ID substring
  (`TCK-20260817-STANDARD-HUNGER-STARVED-BY-RESOLVE-BLOCKER...`). Grepped `registries/mechanisms.yaml`
  for every §10 term — zero mechanism row carries a §10 value in any field. Confirms the ticket's own
  suspicion exactly: §10 is aspirational prose, not an enforced vocabulary, and only 2 of its 10
  values (`STARVED`, `REACH-LIMITED`) are even defined in prose. **This is itself a decision input**:
  binding a fully-enforced vocabulary ((1)/(2), or the newly-built (4)) to an unenforced one changes
  the enforced side's own reliability story if done carelessly — recommend the axis model record §10
  as "aspirational / not yet data-bearing" explicitly, rather than presenting it with equal footing
  to (1)/(2)/(4).
- **`skeleton` §10 counterpart — investigated, no counterpart exists.** `skeleton` is not mentioned
  anywhere in `core_rpg_design_direction.md` (confirmed by grep); it is purely a registry
  implementation-completeness notion (state before `gap`/`partial`/`done` — a scaffold with no real
  logic yet). Recommend the binding table record this pair as "no defined relationship" (explicitly
  undefined, per AC 2's own requirement), not attempt to force a mapping to `MISSING`/`DESIGNED`.
- **Homograph 1 — `MISSING` (§10) vs `MISSING` (control-plane, vocabulary 4) — investigated,
  recommend: same word, compatible-but-not-identical meaning, keep the word, document the scope
  difference rather than rename.** §10's `MISSING` (never itself defined in prose, but positioned
  first in a list that runs MISSING → DESIGNED → EXPERIMENTAL → ... → LIVE, i.e. "not designed yet")
  answers "does this *mechanism* exist at all in the compass's per-mechanism runtime-status sense."
  Vocabulary (4)'s `MISSING` is explicitly defined by direct precedent in `docs/world_rules/
  roadmap.md` (lines 171-177) as "no in-simulation mechanism realizes this Rule at all" — an
  investigated, evidenced absence at the *Rule* level, contrasted explicitly against `UNKNOWN`
  ("not yet looked at," never coerced into `MISSING` per `architecture.md` §7). The two are close in
  spirit (both mean "nothing real exists yet for X") but operate at different granularity (mechanism
  vs. Rule) and different evidentiary bar (§10's is undefined/no bar stated; (4)'s has an explicit
  "investigated" requirement). Recommend: keep both words as `MISSING`, record in the binding table
  as **correlation, not equivalence** — a Rule classified `MISSING` (4) very likely has every mapped
  mechanism at `MISSING`-if-it-existed on axis (3), but the converse does not hold (a mechanism can
  be §10-`MISSING` while its owning Rule is `PARTIAL` via other mechanisms), and axis (3) has no
  enforcement to check the correlation against today anyway.
- **Homograph 2 — `OFF` (§10) vs `INERT-OFF` (control-plane, vocabulary 4) — investigated, recommend:
  compatible concepts, `INERT-OFF` is the more evidenced/precise term, §10's `OFF` should defer to it
  rather than the two independently drifting.** `INERT-OFF` has a real, repeatedly-applied definition
  from direct precedent (`docs/world_rules/roadmap.md` lines 172-173: "`knowledge_model` has no
  decision consumer, INERT/OFF; `PerceptionUpdatePhase` has zero production call sites, INERT/OFF" —
  i.e., code exists, is wired in some sense, but has zero real production effect) and line 581
  ("PARTIAL/INERT-OFF... `ItemInstance`'s own real, feature-gated, untriggered-in-production
  history/provenance machinery" — i.e., a feature flag or gating condition keeps it from firing).
  §10's `OFF` is never itself defined in prose beyond its position in the MISSING→...→LIVE ordering,
  but its plain-English reading ("built but switched off") is a closer match to `INERT-OFF`'s
  feature-gated sense than to any other value. Recommend the binding table record these as
  **equivalence in intent, non-identical in evidentiary rigor** — `INERT-OFF` (4) carries an
  explicit "investigated and found zero call sites / feature-gated" evidentiary bar that §10's `OFF`
  does not, so the axis model should say "§10 `OFF` and control-plane `INERT-OFF` describe the same
  underlying situation; when both apply to the same mechanism/Rule pair, prefer citing `INERT-OFF`'s
  evidence," not silently rename either value (renaming (4)'s enforced enum would touch M0's already-
  landed schema, explicitly out of scope per AC 8 unless charged against M1's one bounded revision).
- **STARVED/REACH-LIMITED registry representation (AC 4) — investigated concretely against
  `tactical_decision`, recommend: do NOT add a registry field; record the decision that runtime reach
  is deliberately not registry-resident.** Applying the §11 admission test (12 questions,
  `core_rpg_design_direction.md` lines 490-501) to a hypothetical new `reach` field: (1) What concept
  — how narrowly a live path's trigger conditions occur in real corpus play. (2) World rule /
  abstraction / derived state — derived state, computed from runtime observation, not authored.
  (3) Who perceives it — no in-world entity; tooling/agents only. (4) Which system consumes it — none
  today; would need a new consumer to justify the field (§11 Q4 fails: no current consumer). (5) What
  future decision changes — potentially triage priority, but this is already served today by
  `verified.verdict: contradicted` plus the free-text `note` (the `tactical_decision` row already
  carries the full STARVED story in its `note`, unabbreviated, per lines 196-225). (6) What it
  connects to — the existing `verified` block, which already has a `note` field designed exactly for
  this ("one line, what was actually seen," header line 81). (8) Numeric precision vs. coarse
  category — a `reach` field would need a real runtime-measured threshold (what fraction of ticks
  counts as STARVED vs. REACH-LIMITED vs. LIVE?) that has never been calibrated against real data —
  §10's own two example definitions ("almost never occur" / "narrow slice") are themselves
  qualitative, not thresholded. (12) Duplicates existing mechanism — **yes**: `verdict: contradicted`
  + `instrument: corpus_run` + a free-text `note` already fully captures this exact case today (see
  Current Behavior above); a new field would encode information the `note` field already expresses,
  just in structured form the registry has explicitly avoided doing prematurely elsewhere (per
  `architecture.md` §6's own "capability first, registry maybe later" precedent for a very similar
  judgment call). The admission test's own closing line ("State with no interaction, no consumer, no
  behavioural effect... should be treated with suspicion") applies directly: no consumer exists for a
  structured `reach` value today. Recommend recording the decision as: STARVED/REACH-LIMITED stay
  compass-axis-only, qualitative, and expressed on the registry side via the existing `verified.note`
  free-text field plus (optionally, as a lighter-weight alternative this ticket could still propose)
  a documented convention that a `contradicted` verdict's `note` should state which of
  STARVED/REACH-LIMITED/genuinely-broken applies, in prose, without a new enum field.
- **Open risk not resolvable by this investigation alone:** whether the "prose convention" half of
  the STARVED/REACH-LIMITED recommendation above (documenting that `note` should name which §10
  category applies) counts as "a registry field" for AC 6's "if a registry field is added, validate()
  enforces it" trigger. It does not add a new YAML key, so AC 6 should not apply — but this is a
  judgment call for the planner/implementer to confirm explicitly rather than silently assume, since
  getting it wrong either way (skipping a required validator change, or building an unneeded one)
  costs a round trip either direction.

## Anti-Drift Hazards

- **Do not let "reconcile" drift into "merge."** The ticket's own Out of Scope and this
  investigation's own finding both point the same direction: collapsing (1)/(2)/(3)/(4) into one enum
  would destroy real information current tooling depends on (`VALID_STATES`/`VALID_VERDICTS`/
  `VALID_RULE_CLASSIFICATIONS` are all independently enforced today; merging breaks all three
  validators simultaneously for no evidenced gain).
- **Do not let "cross-reference the axis model" become "duplicate the axis model."** AC 5 requires
  each of the four homes to point at the model, not restate it — restating risks the exact
  one-fact-one-home violation `tag_taxonomy.md` and this repo's own conventions already guard
  against elsewhere.
- **Do not silently reclassify `tactical_decision` (or any other row) while investigating the STARVED
  question.** AC 7 requires zero `state`/`verdict` changes; the concrete-example analysis above reads
  the row as evidence only, never as a trigger to "fix" its classification.
- **Do not widen M0's already-landed schema without explicitly charging it to M1's one bounded
  revision (AC 8).** `tools/semantic_control_plane/registry.py`'s `VALID_RULE_CLASSIFICATIONS` is
  live and tested (`tests/unit/tools/test_semantic_control_plane_schema.py`); any homograph-driven
  rename temptation (e.g. renaming (4)'s `MISSING` to disambiguate from (3)'s) must not be executed
  under this ticket's plain "docs cross-reference" scope — the recommendation above explicitly avoids
  renaming for this reason.
- **Do not treat §10 as load-bearing just because it is newer.** The ticket's own "Not assumed"
  clause and this investigation's confirmed-unenforced finding both argue the same way: only
  (1)/(2)/(4) have real enforcement and real data behind them; §10 should be positioned in the axis
  model as the least authoritative of the four, not co-equal.
