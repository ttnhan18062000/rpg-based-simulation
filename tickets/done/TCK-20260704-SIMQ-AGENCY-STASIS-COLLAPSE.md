---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE
phase: done
date: 2026-07-04
tags: [simulation_quality, agency, cognition, stasis, calibration, bug]
---

# TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE

## Title
Investigate AGENCY=F collapse in simq_routing_test seed456: entity 23 enters a sustained defer/stasis streak from tick 176

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP` fixed a `ResourceRegistry` crash that had, since
2026-05-18, silently prevented `simq_routing_test` (`ENABLE_ADVENTURE_ROUTING=ON`) from ever
completing a full calibration run for any seed. With the crash fixed, `seed456`'s 500-tick
calibration now completes — and reveals a real, previously-invisible defect: `AGENCY` grades `F`
(`normalized_score=-172541.0` raw / `-345.08` normalized), far below the D20 audit's AC6 gate
("AGENCY ≥ B confirmed for all three `simq_routing_test` seeds"). `seed42`/`seed123` are unaffected
(A/A).

Root cause was traced (not just observed) during the STONE-GAP ticket: in
`quality_scores.jsonl` for `run_1783171252_1673`, entity 23 enters a sustained
`defer_with_reason`/`stasis_N`-tagged event streak starting at **tick 176** — provably before
`ResourceEcologyService`'s first seed check (tick 200) can write any node into state, so this is
**not** caused by the STONE-GAP fix, the new `stone_outcrop` resource, or any other content change
in that ticket. It is a pre-existing property of this world's 2026-07-01-recompiled state plus
`AgencyScorer`'s stasis-penalty formula (`config/simulation_quality/scoring_weights.yaml:20`,
`stasis_per_tick = -3.0`, applied per subsequent defer event once a population-wide idle streak
crosses `stasis_gate_ticks`), only now observable because the STONE crash no longer blocks this
world from running to completion.

Because `tests/simulation_quality/fixtures/grade_anchors.json`'s consumer
(`GRADE_ORDER = ["D","C","B","A","S"]`) has no representable slot for `F`, `seed456`'s AGENCY anchor
was recorded as `"D"` (the schema floor, not the true grade) by the STONE-GAP ticket, specifically
so `test_grade_within_anchor_band[simq_routing_test_seed456_500t]` keeps correctly failing on any
future local re-run until this ticket's fix lands and the anchor is re-set to the true, fixed grade.
This test only fails when `data/calibration/simq_routing_test_seed456_500t/` exists locally
(gitignored, not committed) — it skips cleanly in a fresh checkout/CI absent that data, so this is
not currently blocking the wider test suite.

## Scope
1. Re-verify the finding against current `src/` (this ticket may be picked up after other changes
   land) — re-run `ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py --ticks 500 --seed 456
   --name simq_routing_test` and confirm AGENCY still grades `F`.
2. Investigate why entity 23 (and, per the ticket's own finding, only in `seed456` — not `seed42`
   or `seed123`) enters a sustained `defer_with_reason`/`stasis_N` streak starting at tick 176.
   Trace the actual decision-making path that leads to this entity repeatedly deferring rather than
   selecting a route — this likely touches `AdventureDecisionPhase`/`AdventureRouteGenerator`
   (routing is ON in this world) and whatever blocker/precondition is causing routes to be
   perpetually rejected or deferred for this specific entity+seed combination.
3. Determine whether the fix belongs in (a) the entity's decision logic (something is stuck that
   shouldn't be), (b) `AgencyScorer`'s stasis-penalty formula (the penalty escalates without bound
   — `-3.0` per subsequent defer event compounding to `-172541.0` over 693 events seems
   disproportionate even for a genuinely stuck entity; consider whether the formula needs a floor,
   cap, or different scaling), or (c) both. Read `docs/mechanics/04_strategic_cognition.md` and the
   `AgencyScorer` source to determine which is architecturally correct before deciding — do not
   guess.
4. Once fixed, re-run `simq_routing_test` seed456 calibration and update
   `tests/simulation_quality/fixtures/grade_anchors.json`'s `simq_routing_test_seed456_500t` AGENCY
   anchor from the placeholder `"D"` to the true, now-fixed grade.
5. Re-confirm AC6 ("AGENCY ≥ B for all three `simq_routing_test` seeds") is fully satisfied across
   all 3 seeds, not just seed42/123.
6. Add a regression test proving this specific stasis-collapse scenario doesn't recur (if the fix is
   in decision logic) or that the stasis penalty formula behaves reasonably at scale (if the fix is
   in scoring).

## Out of Scope
- Any other `simq_routing_test` content changes (this ticket is scoped to the AGENCY/stasis
  finding only)
- Re-litigating `TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP`'s already-completed work (that
  ticket's fix is confirmed unrelated to this finding — the stasis streak begins before ecology's
  first seed check can even fire)
- Changing `ENABLE_ADVENTURE_ROUTING`'s default or scope

## Acceptance Criteria
- [x] Root cause of entity 23's sustained defer/stasis streak (seed456, tick 176 onward) confirmed
      with file:line evidence
- [x] Explanation for why this occurs in seed456 but not seed42/seed123 (seed-specific RNG draw,
      a specific route-generation edge case, or something else)
- [x] Fix applied (decision logic, scoring formula, or both — per Scope item 3's investigation)
- [x] `simq_routing_test` seed456's AGENCY grade no longer F (binding closure bar for this ticket)
- [x] AC6's "AGENCY >= B for all 3 seeds" gate carries a documented, evidenced per-seed exception
      for seed456 (recorded in `docs/simulation_quality/eval_matrix_results.md`'s AC6 and
      Cross-World Design Note sections) rather than being fully satisfied — governance-decided,
      not re-litigated by this ticket
- [x] `grade_anchors.json`'s `simq_routing_test_seed456_500t` AGENCY anchor updated from the `"D"`
      placeholder (schema floor standing in for `F`) to the true, live-recomputed `"D"` grade — the
      string value is unchanged, but its meaning changes from "floor placeholder for F" to "real,
      post-fix grade, confirmed by live calibration re-run at norm=-0.5920, matching the plan's
      hand-computed prediction of -0.592"
- [x] New regression test prevents recurrence
- [x] `make evaluate --dry-run` exits 0

## Related Tickets
- TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP (todo, filed during this ticket's planning
  phase) — standalone follow-up for the world-content gap (no resource node tagged `hometown`) that
  is the other half of why entity 23 has zero alternative routes; not implemented by this ticket
  (out of scope — see this ticket's Out of Scope), and its own landing would not retroactively
  change this ticket's AC6 per-seed exception record (see eval_matrix_results.md AC6 section)
- TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP (done) — fixed the crash that was blocking this
  world from completing calibration, which is what surfaced this finding; confirmed this finding is
  causally unrelated to that ticket's fix
- TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS (done) — the 2026-07-01 hazard-kind recompile that changed
  this world's dynamics is cited as context for when this stasis property may have been introduced
  or become observable

## Related Docs
- `docs/simulation_quality/eval_matrix_results.md` — STONE-GAP's dated NOTE documents this finding
  in full, including the exact `quality_scores.jsonl` run key (`run_1783171252_1673`) and event
  counts (693 AGENCY events, 491 `defer_idle`/`stasis_N`-tagged)
- `docs/mechanics/04_strategic_cognition.md` — goal/route decision logic, relevant if the fix is in
  decision-making rather than scoring
- `config/simulation_quality/scoring_weights.yaml` — `stasis_per_tick` and related AGENCY scoring
  constants

## Related Stored Artifacts
- `stored_artifacts/TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP/` — investigation/plan documenting
  the original discovery and root-cause tracing of this finding

## Related Code Areas
- `src/domains/adventure/` — `AdventureDecisionPhase`, `AdventureRouteGenerator`
- Wherever `AgencyScorer` is defined (likely `src/simulation_quality/pillars.py` or similar) — the
  stasis-penalty formula
- `data/worlds/simq_routing_test/` — the world whose seed456 run exhibits this behavior

## Assumptions / Open Questions
- UQ-1: Is this a genuine entity-decision bug (something that should not get stuck, does), or a
  scoring-formula issue (the entity is correctly and intentionally idle for valid reasons — e.g. no
  legal route exists — but the penalty formula scales unreasonably)? These require different fixes
  and this ticket's own Scope item 3 defers the decision to investigation with evidence, not a
  guess made here.

## Implementation Notes
Implemented per `staging_artifacts/TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE/plan.md` (APPROVED,
2nd pass) exactly, in order (Steps 1-10). Two independent defects were fixed together in
`AgencyScorer` (`src/simulation_quality/scorers/agency.py`):

1. **Attribution**: `defer_with_reason`'s `stasis_N` path now tracks a true per-entity consecutive
   streak (`self._entity_defer_streak: dict[int, int]`), mirroring the scorer's existing
   `self._last_abandoned` per-entity instance-state pattern, instead of reading the
   population-wide `context.window_tag_counts` window. That population-wide lookup is retained
   only for the separate, untouched `population_stasis` one-shot mechanism.
2. **Magnitude**: the escalation term (`stasis_per_tick * extra_ticks`) is now a capped, ONE-SHOT
   per continuous streak (`self._entity_stasis_fired: dict[int, bool]`), firing exactly once when
   `extra >= stasis_extra_ticks_cap` (streak reaches `gate + cap`, i.e. streak=10 given
   `gate=5`/`cap=5`), not at the first post-gate tick — this exact firing condition was the subject
   of an architecture-review fix-and-reverify cycle (an earlier draft fired at `extra >= 1`, always
   yielding `capped_extra=1` regardless of `cap`'s configured value). The `stasis_N` **tag** still
   fires on every qualifying event (preserving the `loop_detected:entity_stasis` signal for the
   whole duration of a real episode); only the **score delta** is one-shot.

New config: `stasis_extra_ticks_cap: 5` added to `detection_params.yaml`'s `time_gates` dict (no
schema change — `int_param()` already reads arbitrary keys).

Streak reset points: `action_executed`, `route_selected`, `route_family_first_use`,
`project_completed` (the four signals that a real non-defer routing outcome occurred).
`project_started`/`project_abandoned`/`commitment_abandoned` are unchanged no-op-for-stasis paths.

Live re-run confirms the plan's hand-computed arithmetic exactly: `simq_routing_test` seed456
(500t) now grades `AGENCY=D`, `norm=-0.5920` (plan predicted `-0.592`), up from the pre-fix `F`
(`norm=-345.082`). seed42/seed123 are unaffected (`AGENCY=A`/`A`, confirmed live, not assumed) —
entities 24/25 never emit `defer_with_reason` in any seed, so the streak dict never accumulates
for them.

seed456's `AGENCY=D` (not `>=B`) is a governance-decided, documented exception to AC6's blanket
cross-seed gate, not an open gap: entity 23 genuinely, legitimately emits 491 `defer_with_reason`
events over the run (a real personality-roll + world-content-gap combination, confirmed by
investigation, not a bug), and `defer_idle=-1.0`'s flat per-event weight alone puts a hard
mathematical floor of `normalized <= -0.562` on this run regardless of the escalation term's
value — `defer_idle` and the population-tick normalization denominator are both explicitly out of
this ticket's authorized scope. Recorded per plan Step 8 in
`docs/simulation_quality/eval_matrix_results.md` (AC6 section + Cross-World Design Note "Second
exception class" subsection) and `docs/plans/audit_fix_plan.md`'s P0-A row.

Docs contract (`docs/simulation_quality/quality_scoring_contract.md`) pseudocode and AGENCY table
row updated to match the corrected per-entity/capped/one-shot formula. Fixed a citation nit found
during planning: `INFORMATION`'s parallel -15.0 "gone quiet" key is `belief_system_silent`, not
`belief_system_dormant` (that name belongs only to `COGNITION`'s key) — corrected in `plan.md`'s
own Step 2 reasoning (the contract doc's own two occurrences at the COGNITION and INFORMATION
table rows were already correctly named, confirmed via `scoring_weights.yaml`, no doc fix needed
there).

Parity ledger `INFRA-237` (`docs/parity_ledger/infrastructure.yaml`) updated: `text` appended with
the per-entity/capped clause, `divergence_note` records the 2026-07-04 correction (was `null`).
`v2_evidence`/`test_path` unchanged (same file/class, same test files with rewritten assertions).

Decision logic (`src/domains/adventure/`), `defer_idle`'s base -1.0 weight, and the
hometown-resource-tag world-content gap were explicitly NOT touched, per architecture constraints.

## Test Summary
- `pytest tests/simulation_quality/test_agency_scorer.py -v` — 26 passed (rewrote
  `TestDefer::test_stasis_fires_after_gate` to drive the per-entity streak via repeated same-entity
  `score()` calls and assert the corrected fire-at-streak=10 condition; added `TestStasisBounding`
  with 3 new test methods incl. a parametrized [20, 2000]-length long-streak bounding test; the
  other 3 `TestDefer` tests and all other classes unmodified, re-verified passing).
- `pytest tests/simulation_quality/test_timegate_penalties.py -v` — 27 passed (rewrote
  `test_stasis_N_timegate_fires_after_gate`/`test_stasis_N_timegate_not_before_gate` for
  per-entity-driving; renamed `test_stasis_N_timegate_accumulates_linearly` to
  `test_stasis_N_timegate_bounded_one_shot` and rewrote to assert the fixed one-shot escalation
  contribution over a long streak; `population_stasis` tests unmodified, re-verified passing).
- `pytest tests/simulation_quality/test_grade_regression.py -v -m "not slow"` — 82 passed, 1
  skipped (pre-existing, unrelated `urban_political_seed42_200t` skip) — all 3
  `simq_routing_test_seed*` anchor-band checks pass against live-refreshed calibration data.
- `pytest tests/simulation_quality/test_quality_hub_integration.py -v` — 10 passed, no cross-pillar
  leakage (fix is fully contained inside `AgencyScorer`'s own instance state).
- `pytest tests/integration/domains/adventure/ tests/unit/domains/adventure/
  tests/perf/test_phase3_adventure_decision_budget.py -v` — 58 total; 1 pre-existing flaky perf
  test (`test_phase3_adventure_decision_perf_budget`, VM-scheduling-variance sensitive per its own
  in-file comment) failed only when run immediately after other CPU-heavy tests in the same
  session, and passed cleanly (0.50s) when re-run in isolation — confirmed unrelated to this
  change (no adventure decision-logic file touched).
- `pytest tests/unit/observability/test_event_extractor_agency.py
  tests/unit/observability/test_event_extractor_agency2.py tests/unit/social/test_party_agency.py
  -v` — 35 passed.
- Live calibration re-runs (all with `rm -rf` of the stale dir first, per the append-mode
  footgun): seed456 → `AGENCY=D, norm=-0.5920` (was `F, norm=-345.082`); seed42 →
  `AGENCY=A, norm=+1.4207`; seed123 → `AGENCY=A, norm=+0.6415` — both unchanged from pre-fix,
  confirming the fix is inert for entities that never enter a defer streak.
- `make evaluate --dry-run` — exit 0, "390 pillars checked — 0 regressions — 0 missing" (1
  pre-existing scenario with no calibration data, unrelated to this ticket).
- `make knowledge-index-update` — 3 docs files re-embedded (contract doc, eval_matrix_results.md,
  audit_fix_plan.md), 1855 unchanged from cache.

## Files Changed
- `src/simulation_quality/scorers/agency.py` — per-entity streak dicts (`_entity_defer_streak`,
  `_entity_stasis_fired`), `_reset_entity_stasis` helper called from the four non-defer routing
  branches, corrected capped one-shot escalation logic in the `defer_with_reason` branch
- `config/simulation_quality/detection_params.yaml` — new `stasis_extra_ticks_cap: 5` time-gate
- `docs/simulation_quality/quality_scoring_contract.md` — pseudocode block (~441-455) rewritten to
  match corrected logic; AGENCY table `stasis_N` row (~line 556 pre-edit) rewritten; loop-signal
  clarifying note added (tag-vs-delta distinction)
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-237` `text` appended, `divergence_note` filled
- `tests/simulation_quality/test_agency_scorer.py` — `TestDefer::test_stasis_fires_after_gate`
  rewritten; new `TestStasisBounding` class (3 tests, one parametrized over [20, 2000])
- `tests/simulation_quality/test_timegate_penalties.py` — `test_stasis_N_timegate_fires_after_gate`
  / `test_stasis_N_timegate_not_before_gate` rewritten for per-entity driving;
  `test_stasis_N_timegate_accumulates_linearly` renamed to
  `test_stasis_N_timegate_bounded_one_shot` and rewritten
- `tests/simulation_quality/fixtures/grade_anchors.json` — no value change (`AGENCY: "D"` for
  `simq_routing_test_seed456_500t` was already `"D"`); confirmed the live-recomputed grade matches
  the existing string exactly, so only its *meaning* changes (floor-placeholder-for-F → real
  post-fix grade) — called out here per plan Step 5's instruction, not a diff in the file itself
- `docs/simulation_quality/eval_matrix_results.md` — new dated status paragraph under `## AC6 —
  AGENCY Confirmation`; new "Second exception class" subsection under `## AGENCY — Cross-World
  Design Note`
- `docs/plans/audit_fix_plan.md` — parenthetical annotation appended to the `P0-A` summary-table
  row (~line 566) noting seed456's documented D-grade exception
- `staging_artifacts/TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE/plan.md` — corrected Step 2's own
  citation nit (`COGNITION.belief_system_dormant` vs. `INFORMATION.belief_system_silent` were
  conflated under one name; now cited separately with the exact keys)
- This ticket file — AC bullet split (Step 8), Related Tickets cross-reference to
  `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP`, Implementation
  Notes/Test Summary/Files Changed
- `tickets/todos/TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP.md` — already existed
  (filed during planning), confirmed cross-referenced, not otherwise modified by this ticket

## Completion Summary
Fixed `AgencyScorer`'s stasis-penalty formula: replaced the population-wide, unbounded
`window_tag_counts`-based escalation with true per-entity consecutive-streak tracking and a
capped one-shot escalation (new `stasis_extra_ticks_cap=5`), correcting a premature-firing bug
found during architecture review (the original design fired the cap at the very first post-gate
event, always yielding `-3.0` regardless of the configured cap, instead of the intended `-15.0`
ceiling). Live-recalibrated `simq_routing_test` seed456 from `AGENCY=F` (`norm=-345.082`) to
`AGENCY=D` (`norm=-0.5920`), matching the plan's hand-computed prediction to 4 decimal places.
Confirmed via fresh live re-runs (not assumed) that seed42/seed123 are fully unaffected
(`A`/`A`, unchanged) since entities 24/25 never emit `defer_with_reason` in either seed. 0
regressions across the rest of the calibration corpus (`make evaluate --dry-run`).

Entity 23's stasis is legitimate, not a decision-logic bug: its sociability (0.18816) rolls just
under the `FORM_PARTY` gate (0.2) in seed456 specifically, and no resource node in this world has
`hometown` in its `source_region_tags`, so no alternative opportunity exists either — confirmed via
direct `WorldCompiler.compile()` inspection across all 3 seeds. Filed
`TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP` as a separate follow-up for that content gap
(out of scope here).

`AGENCY grade no longer F` (this ticket's binding bar) is satisfied. AC6's literal `AGENCY >= B for
all 3 seeds` is **not** fully satisfiable within this ticket's authorized scope — even a perfect
fix caps out at `D` because `defer_idle`'s flat `-1.0` base weight (an out-of-scope, corpus-wide
constant) applied to 491 genuinely-legitimate defer events already exceeds the grade band on its
own, before any escalation term. Per explicit governance decision, this is recorded as a documented
per-seed exception (mirroring the existing `AGENCY=C` archetype-exception precedent) in
`docs/simulation_quality/eval_matrix_results.md`'s AC6 section and Cross-World Design Note, rather
than expanding this ticket's scope into the base weight — a broader, corpus-wide scoring change was
explicitly declined as out of scope for this bug fix.
