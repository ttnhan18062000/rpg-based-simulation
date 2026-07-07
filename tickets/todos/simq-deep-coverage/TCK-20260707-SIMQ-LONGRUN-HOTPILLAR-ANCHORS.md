---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS
phase: open
date: 2026-07-07T16:31:09Z
tags: [simulation-quality, corpus, calibration, agency, faction, cognition, stasis]
---

# TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS

## Title
Add long-run (1000t/2000t, capped at ≤2000t) anchors for the worlds already known to drive
AGENCY/COGNITION/FACTION/NARRATIVE to their peak short-run grades

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` §1.3 found that across all 11
existing `SLOW_ANCHOR_KEYS` (≥1000t) anchors, AGENCY/COMBAT/PROGRESSION/WORLD grades are literally
invariant (AGENCY = C×11, COMBAT = B×11, PROGRESSION = B×11, WORLD = B×11) while the short-run corpus
shows AGENCY reaching A (`simq_routing_test`, `hero_guild_routing`, 500t), COGNITION reaching S
(`unit_selfmodel_pilot`, 200t), FACTION reaching S (`unit_faction_tension` and 6 other 200t worlds),
and NARRATIVE reaching S (`hero_guild_routing`, `simq_routing_test`, 500t) — none of which has ever
been run past 500t. The mechanism (§1.3): the only 3 worlds carrying any ≥1000t anchor
(`dungeon_crawl`, `sandbox_world`, `urban_political`) predate the unit-tier/hero-tier specialization
work and are not content-tuned to drive those pillars hot. This ticket closes that blind spot for the
specific hypotheses investigation.md §1.4 identifies as evidence-backed and worth testing:

- **AGENCY** (`hero_guild_routing`, `simq_routing_test`): does a "hot" (A-grade, actively routing)
  AGENCY pillar hold, drift toward stasis (`stasis_N`/`population_stasis` per the pillar contract
  §5), or oscillate over 1000-2000 ticks? Zero evidence exists today.
- **FACTION** (`unit_faction_tension`): the one existing long-run FACTION data point
  (`dungeon_crawl` 1000t→2000t) shows FACTION decaying from grade A to B as tick count grows — raw
  score unchanged, but `effective_denom` in the normalized-score formula (contract §4.4) grows with
  `last_event_tick`/`floor_tick`. If that decay dynamic generalizes, `unit_faction_tension`'s S-grade
  could plausibly decay to A/B by 1000-2000t purely from normalization mechanics, independent of any
  real regression — or it could be a genuine drift signal. These two explanations are currently
  indistinguishable because no S-tier FACTION world has ever run long.
- **COGNITION** (`unit_selfmodel_pilot`): same untested-peak pattern — the S-grade peak is completely
  dark beyond 200t.
- **SOCIAL persistence** (`urban_political` extended to 2000t): `urban_political` already shows
  SOCIAL holding at S through 1000t but has no 2000t anchor, so persistence beyond 1000t is
  unconfirmed for the weakest-pillar's one carrying world.

## Scope
1. Confirm (per this epic's `SEQUENCE.md`) that the 4 relocated resource/coverage-gap tickets
   (`TCK-20260707-HERO-GUILD-ROUTING-RESOURCE-TAG-GAP`,
   `TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP`,
   `TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT`,
   `TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP`) have landed in `tickets/done/` before
   starting work that touches `hero_guild_routing` or `urban_political`.
2. In this ticket's own Plan phase, decide the exact seed count per world/tier (1, 2, or 3 seeds) for
   each of the following, with explicit cost/coverage reasoning (calibration run cost vs. evidence
   value) — the epic sets only the floor (at least 1 seed per world/tier) and the ≤2000t cap, not the
   exact grid:
   - `unit_selfmodel_pilot` — new 1000t anchor(s)
   - `unit_faction_tension` — new 1000t anchor(s)
   - `hero_guild_routing` — new 1000t anchor(s)
   - `simq_routing_test` — new 1000t anchor(s)
   - `unit_faction_tension` — new 2000t anchor(s) (in addition to 1000t)
   - `urban_political` — new 2000t anchor(s) (in addition to its existing 1000t anchors)
3. Before anchoring `unit_faction_tension`, verify live (per investigation.md §4 point 4) whether it
   needs its own `config/simulation_quality/profiles/unit_faction_tension.yaml` or whether
   `default.yaml` is confirmed sufficient — its FACTION=S grade already fires at 200t without a
   dedicated profile, which is suggestive but not proof for a 1000t+ run.
4. Add each new anchor via the exact data-only mechanism investigation.md §4 documents — no test
   infrastructure code changes required:
   - Generate and commit the calibration artifact via
     `python3 tools/calibrate_simq.py --name <world> --seed <N> --ticks <T>` at
     `data/calibration/{run_key}/quality_report.json`
   - Add the resulting grade dict to `tests/simulation_quality/fixtures/grade_anchors.json`
     (key format `{world}_seed{N}_{ticks}t`)
   - Add the same key string to `SLOW_ANCHOR_KEYS` in `test_grade_regression.py`
5. Document the resulting grades honestly in `docs/simulation_quality/eval_matrix_results.md` for
   each of the 4 hypotheses above — whether AGENCY/COGNITION/FACTION hold, decay, or reveal a
   genuine drift bug, and whether SOCIAL persists at S through 2000t for `urban_political`. If a
   genuine bug is found (e.g. a real degenerate loop, not just normalization-driven grade decay),
   file a follow-up ticket rather than fixing it in this ticket — mirror the pattern established in
   `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT`'s Scope item 4c.
6. Run `make evaluate` and `make evaluate-full` and confirm 0 regressions on the rest of the corpus.

## Out of Scope
- Any anchor beyond 2000 ticks — explicitly capped per the epic's scope; a 5000t+ tier is a future,
  separately-scoped decision, not part of this ticket.
- Fixing any genuine drift bug discovered by this ticket's data — file a follow-up ticket instead
  (per Scope item 5).
- Re-fixing `hero_guild_routing`'s resource-tag gap or `urban_political`'s hometown gap — handled by
  the 4 prerequisite tickets this one depends on; do not duplicate.
- Adding anchors for any world not named in Scope item 2 (e.g. no new anchors for `dungeon_crawl`,
  `sandbox_world`, or the flat PROGRESSION/WORLD/ECONOMY/INFORMATION pillars, which investigation.md
  §1.3 found flat corpus-wide, not specifically long-run-blind — that is corpus-breadth work covered
  by the prior tiers epic's remit, not this ticket).
- Creating or modifying `unit_faction_tension.yaml`'s profile unless Scope item 3's live verification
  determines it is actually needed.

## Acceptance Criteria
- [ ] All 4 prerequisite tickets are in `tickets/done/` before any calibration run touching
      `hero_guild_routing` or `urban_political` is performed
- [ ] New anchors added for `unit_selfmodel_pilot`, `unit_faction_tension` (both 1000t and 2000t),
      `hero_guild_routing`, and `simq_routing_test` at 1000t, plus `urban_political` at 2000t — each
      via the exact 3-step data-only mechanism (calibration artifact + `grade_anchors.json` entry +
      `SLOW_ANCHOR_KEYS` entry), with no anchor exceeding 2000t
- [ ] `eval_matrix_results.md` documents, honestly, whether AGENCY/COGNITION/FACTION hold, decay, or
      reveal a genuine bug at long run, and whether `urban_political`'s SOCIAL=S persists to 2000t —
      if a genuine bug is found, a follow-up ticket is filed (not fixed here) and referenced
- [ ] Whether `unit_faction_tension` needs a dedicated profile YAML is explicitly confirmed live
      (not assumed) and the outcome documented
- [ ] `make evaluate` and `make evaluate-full` both confirm 0 regressions on the rest of the corpus

## Related Tickets
- TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC (parent epic)
- TCK-20260707-HERO-GUILD-ROUTING-RESOURCE-TAG-GAP (hard dependency — must land first)
- TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP (hard dependency — must land first)
- TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT (hard dependency — must land first)
- TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP (hard dependency — must land first)
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT — source of the "file a follow-up, don't fix
  in-ticket" pattern this ticket's Scope item 5 mirrors
- TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE — established the per-world `feature_flags:`
  profile mechanism relevant to `hero_guild_routing`/`simq_routing_test`'s existing ON state

## Related Docs
- `staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` §1.2-1.4 (the exact
  invariant-grade evidence table and per-pillar hypotheses this ticket tests), §4 (the data-only
  anchor-extension mechanism and the `unit_faction_tension` profile question)
- `docs/simulation_quality/quality_scoring_contract.md` §4.4 (`effective_denom` normalization
  formula — the mechanism that could explain FACTION grade decay independent of a real regression)
- `docs/simulation_quality/eval_matrix_results.md` — to be updated with this ticket's findings

## Related Stored Artifacts
- `staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` (see Related Docs)

## Related Code Areas
- `tests/simulation_quality/fixtures/grade_anchors.json`
- `tests/simulation_quality/test_grade_regression.py` — `SLOW_ANCHOR_KEYS`
- `tools/calibrate_simq.py`
- `data/calibration/` — new artifact directories per anchor
- `config/simulation_quality/profiles/` — `unit_faction_tension.yaml` (conditionally, per Scope
  item 3)
- `src/simulation_quality/scorers/agency.py`, `cognition.py`, `faction.py`, `social.py` — not
  modified, only exercised

## Assumptions / Open Questions
- Exact seed count per world/tier is intentionally left to this ticket's own Plan phase (per epic
  scope) — if the eventual choice is fewer seeds than the existing 3-seed convention
  (`dungeon_crawl`/`urban_political` use seed42/123/456), the Plan phase must state the coverage
  trade-off explicitly, not silently under-sample.
- Assumes `unit_faction_tension`'s FACTION=S grade generalizes to a live-runnable 1000t/2000t
  simulation without hitting an unrelated blocker (e.g. missing content for long-run population
  stability) — if Scope item 1's prerequisite tickets surface such a blocker, this ticket's Plan
  phase must account for it before committing to the anchor matrix.
- If Scope item 5 uncovers a genuine drift bug in any of the 4 hot pillars, this ticket's scope is
  explicitly to document and file a follow-up, not fix — if that boundary turns out to be
  impractical (e.g. the bug blocks getting a stable anchor grade at all), escalate rather than
  silently expanding scope.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
