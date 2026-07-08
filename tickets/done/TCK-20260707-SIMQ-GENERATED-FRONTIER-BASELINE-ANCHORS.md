---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS
phase: done
date: 2026-07-07T16:31:09Z
tags: [simulation-quality, corpus, calibration, world]
---

# TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS

## Title
Establish `generated_frontier_3_42`'s first-ever grade anchors (200t baseline + capped long-run tier)

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` §1.2 found that
`generated_frontier_3_42` has **zero anchors of any kind** in
`tests/simulation_quality/fixtures/grade_anchors.json` — not even a 200t short-run anchor — despite
having its own calibration profile at
`config/simulation_quality/profiles/generated_frontier_3_42.yaml`. This was found incidentally during
the long-run coverage audit and is a distinct, smaller gap from the main long-run-anchor thread: this
world has never been grade-anchored at any tick count, so it currently has zero regression protection
from `test_grade_regression.py` at all.

## Scope
1. Confirm live (do not assume) that `generated_frontier_3_42` compiles and runs cleanly through the
   standard calibration harness (`python3 tools/calibrate_simq.py --name generated_frontier_3_42
   --seed <N> --ticks <T>`) — if it does not, that is itself a genuine finding to document, not paper
   over.
2. Establish the world's first-ever 200t anchor(s), matching the rest of the short-run corpus's
   convention (per investigation.md §1.2's framing of "matching the rest of the short-run corpus
   convention").
3. Establish at least one long-run tier anchor (1000t), capped at 2000t maximum per this epic's
   overall scope cap — do not exceed 2000t.
4. Add each anchor via the same data-only mechanism used elsewhere in this epic (investigation.md
   §4): calibration artifact at `data/calibration/{run_key}/quality_report.json`, entry in
   `grade_anchors.json`, and (for the long-run tier only) an entry in `SLOW_ANCHOR_KEYS` in
   `test_grade_regression.py`.
5. Document the resulting grades in `docs/simulation_quality/eval_matrix_results.md`, noting this is
   the world's first-ever calibration entry.
6. Run `make evaluate --dry-run` to confirm 0 regressions on the rest of the corpus after the new
   entries are added.

## Out of Scope
- Any anchor beyond 2000 ticks.
- Any content/catalog changes to `generated_frontier_3_42` itself — if Scope item 1 reveals the world
  does not compile/run cleanly, document the blocker and escalate rather than fixing world content in
  this ticket (that would be a separate follow-up).
- Adding `generated_frontier_3_42` to `POPULATION_STABILITY_WORLDS` — that is
  `TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP`'s scope; do not duplicate (though this
  ticket's Related Tickets notes the overlap for awareness).
- Work on any other world — this ticket is scoped to `generated_frontier_3_42` only.

## Acceptance Criteria
- [ ] `generated_frontier_3_42` confirmed to compile and run cleanly through the calibration harness
      (or the blocker is documented if it does not)
- [ ] At least one 200t anchor added, matching corpus convention
- [ ] At least one long-run anchor added (1000t), not exceeding 2000t
- [ ] All new anchors added via the data-only mechanism (calibration artifact + `grade_anchors.json`
      + `SLOW_ANCHOR_KEYS` for the long-run entry)
- [ ] `eval_matrix_results.md` documents the new grades as this world's first-ever calibration entry
- [ ] `make evaluate --dry-run` confirms 0 regressions on the rest of the corpus

## Related Tickets
- TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC (parent epic)
- TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP — sibling ticket also touching
  `generated_frontier_3_42` (population-stability test coverage, not grade anchors); no scope
  overlap, but both should be checked against each other's outcome before either closes
- TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS — sibling long-run-anchor ticket for other worlds;
  this ticket is independent of it (different world, no shared dependency) and can run in parallel

## Related Docs
- `staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` §1.2 (the exact finding:
  zero anchors of any kind despite having a calibration profile)
- `docs/simulation_quality/eval_matrix_results.md` — to be updated with this world's first entry

## Related Stored Artifacts
- `staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` (see Related Docs)

## Related Code Areas
- `tests/simulation_quality/fixtures/grade_anchors.json`
- `tests/simulation_quality/test_grade_regression.py` — `SLOW_ANCHOR_KEYS`
- `tools/calibrate_simq.py`
- `config/simulation_quality/profiles/generated_frontier_3_42.yaml`
- `data/worlds/generated_frontier_3_42/`

## Assumptions / Open Questions
- Investigation.md §5 Q4 left open whether this world's total absence from `grade_anchors.json` is
  intentional (used only for corpus-diversity/population-stability tests, not grade calibration) or
  an oversight. This ticket proceeds on the assumption it is an oversight worth closing (per the
  epic's decision to give it its own ticket) — if Scope item 1's live check reveals a structural
  reason the world was never anchored (e.g. it doesn't compile, or its content is intentionally
  minimal/non-representative), that finding overrides this assumption and should be documented
  instead of forcing an anchor.

## Implementation Notes
Implemented exactly per `staging_artifacts/TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS/plan.md`'s
10 steps, with one deviation (Step 9 test fix — see Deviations note below and `plan.md`'s own
Deviations section).

- **Step 1 (live-verify/determinism):** Re-ran `calibrate_simq.py --name generated_frontier_3_42
  --seed 42 --ticks 200` fresh. All 10 pillar grades, raw_scores, normalized_scores, and event_counts
  matched the existing on-disk artifact exactly (only `run_id`/`generated_at`/random `event_id` hashes
  differed) — determinism confirmed, on-disk artifact overwritten with the fresh run. This stands in
  for a seed123/seed456 spot-check per the plan's reasoning (same tooling/world/day-of-origin).
- **Step 2 (200t fast anchors, 3 seeds):** Added `generated_frontier_3_42_seed{42,123,456}_200t` to
  `tests/simulation_quality/fixtures/grade_anchors.json` (values copied directly from the on-disk
  `quality_report.json` files, not hand-typed) and to `FAST_ANCHOR_KEYS` in
  `tests/simulation_quality/test_grade_regression.py`.
- **Step 3 (fresh 1000t run):** Ran `calibrate_simq.py --name generated_frontier_3_42 --seed 42
  --ticks 1000` — completed cleanly, 626 events replayed. Overall grade A(200t)→B(1000t). Only two
  genuine letter-grade shifts: FACTION S→A (raw_score/event_count byte-identical between 200t and
  1000t — pure `effective_denom` dilution, `docs/simulation_quality/quality_scoring_contract.md`
  §4.4, matching the `dungeon_crawl` precedent) and COMBAT A→B (raw_score grew 32→174 but
  `effective_denom` grew faster, plus 6 new `entity_killed` negative events at ticks 982-1000).
  ECONOMY actually improved C→B (0→24 events, genuine new activity). All other pillars held grade.
- **Step 4 (1000t slow anchor):** Added `generated_frontier_3_42_seed42_1000t` to `grade_anchors.json`
  and `SLOW_ANCHOR_KEYS`.
- **Step 5 (population cross-check, ad hoc, non-gating):** Drove `WorldCompiler.compile` →
  `Kernel.tick_once()` for 1000 ticks at seed 42 (mirroring `test_population_stability`'s pattern,
  sampling every 100 ticks against the 60%-alive-of-44 floor = 26.4). **Genuine new finding:**
  population holds through tick 800 (81.8%→79.5%→65.9%→70.5%→63.6%, all above floor) then collapses
  sharply — 15/44 (34.1%) at tick 900, 4/44 (9.1%) at tick 1000, both below the 60% floor. This is a
  previously-unknown late-tick collapse (`generated_frontier_3_42` was not in
  `KNOWN_POPULATION_COLLAPSE_WORLDS` and `test_population_stability` only covers 300 ticks, so this
  was never exercised before). Per Out of Scope, the root cause was **not** investigated or fixed —
  filed as `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE`
  (`tickets/todos/TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE.md`), analogous to
  the existing `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE` tracking for `dungeon_crawl`/
  `urban_political` but a distinct late-cliff failure shape, not assumed to share a root cause. Not
  added to `KNOWN_POPULATION_COLLAPSE_WORLDS` — that dict is keyed to `test_population_stability`'s
  existing 300-tick test, which this world correctly passes; the new ticket's Scope item 3 covers
  creating an extended-window regression guard instead. The 1000t anchor was still landed as-is
  (AC3 requires it; the anchor reflects the world's actual measured behavior).
- **Step 6:** Added a new dated section to `docs/simulation_quality/eval_matrix_results.md`
  superseding (not deleting) the prior "FACTION + INFORMATION, content-only, NO new anchor" section —
  full 10-pillar 200t (3-seed) and 1000t (seed42) tables, grade-shift attribution table, population
  finding, and seed-count rationale.
- **Step 7:** Corrected the stale `docs/simulation_quality/corpus_tier_taxonomy.md:131` Notes text
  (no longer claims the world is "deliberately left outside the anchored calibration corpus").
- **Step 8:** Appended `v2_evidence` notes to `INFRA-240` (COGNITION) and `INFRA-241` (FACTION) citing
  this ticket's data points, and a staleness flag to `INFRA-250`'s `v2_evidence` (live count: 71
  non-metadata `grade_anchors.json` keys = 53 fast + 18 slow, vs. the stale "25 (14/11)" text). No
  `status` fields changed. YAML validity confirmed via `yaml.safe_load`.
- **Step 9 (scoped regression):** All commands from the plan ran; see Test Summary. One genuine
  failure surfaced and was fixed as part of this step (see Deviations).
- **Step 10:** `make evaluate` (dry-run) reported `710 pillars checked — 0 regressions — 0 missing`
  across the full corpus.

**Deviation from plan (documented in `plan.md`'s own Deviations section too):** Step 9's full-suite
run of `tests/unit/worldassembly/test_corpus_diversity.py` surfaced a genuine, foreseeable-but-
undocumented regression in `test_module_family_anchored`: that test derives its "anchored worlds" set
directly from `grade_anchors.json` keys, so anchoring `generated_frontier_3_42` (which is the sole
world composing the `moon_cult_ruins` module) automatically anchors that module too. The test's own
`STILL_UNANCHORED_MODULE = "moon_cult_ruins"` constant (and its assertion that this module must
*not* become anchored) was written by a prior ticket
(`TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS`) under the explicit assumption that `generated_frontier_3_42`
would remain unanchored — an assumption this ticket's entire purpose is to invalidate. The test's own
failure message states verbatim: "this test's exclusion list is stale and should be updated." Fixed by
moving `moon_cult_ruins` into `NEWLY_ANCHORED_MODULES` and removing the now-inapplicable
`STILL_UNANCHORED_MODULE` assertion (confirmed via direct query that zero modules remain unanchored
corpus-wide after this ticket). This is not a scope violation — it is the direct, mechanical
consequence of the Scope-approved anchoring work, and the plan's own Step 9 explicitly called for
running this exact suite to "confirm no cross-world regression from touching shared fixtures."

## Test Summary
- `pytest tests/simulation_quality/ -m "not slow" -v` — 430 passed
- `pytest tests/simulation_quality/test_grade_regression.py -m slow -v` — 18 passed (all existing
  17 slow anchors + this ticket's new `generated_frontier_3_42_seed42_1000t`, zero drift on any
  other world)
- `pytest tests/simulation_quality/test_grade_regression.py -v -k generated_frontier_3_42` +
  `test_grade_anchor_file_exists_and_valid` — 4 passed
- `pytest tests/unit/worldassembly/test_corpus_diversity.py -v -k generated_frontier_3_42` — 3 passed
  (`test_population_stability[generated_frontier_3_42]` still passes at its native 300t scope)
- `pytest tests/unit/worldassembly/test_corpus_diversity.py -v` — 48 passed, 2 xfailed
  (`dungeon_crawl`/`urban_political`, pre-existing documented collapses) — required the
  `test_module_family_anchored` fix described above to pass
- `pytest tests/integration/worldassembly/test_e2e_smoke.py -v -k generated_frontier_3_42` — 1 passed
- `pytest tests/integration/test_world_profile_feature_flag_guardrail.py -v` — 55 passed, zero diff
- `pytest tests/unit/strategic/test_opportunities.py -v -k orc_stronghold` — 1 passed
- `make evaluate` (dry-run) — 710 pillars checked, 0 regressions, 0 missing

## Files Changed
- `tests/simulation_quality/fixtures/grade_anchors.json` — 4 new keys (3× 200t, 1× 1000t)
- `tests/simulation_quality/test_grade_regression.py` — 3 new `FAST_ANCHOR_KEYS`, 1 new
  `SLOW_ANCHOR_KEYS`
- `tests/unit/worldassembly/test_corpus_diversity.py` — `moon_cult_ruins` moved into
  `NEWLY_ANCHORED_MODULES`; `STILL_UNANCHORED_MODULE` constant and its assertion removed (Deviation)
- `docs/simulation_quality/eval_matrix_results.md` — new superseding section for
  `generated_frontier_3_42`
- `docs/simulation_quality/corpus_tier_taxonomy.md` — line 131 anchor-status text corrected
- `docs/parity_ledger/infrastructure.yaml` — `v2_evidence` additions to `INFRA-240`, `INFRA-241`,
  `INFRA-250` (no `status` changes)
- `data/calibration/generated_frontier_3_42_seed42_200t/quality_report.json` (overwritten, gitignored
  disk artifact, not committed)
- `data/calibration/generated_frontier_3_42_seed42_1000t/quality_report.json` (new, gitignored disk
  artifact, not committed)

## Completion Summary
All 6 acceptance criteria met. `generated_frontier_3_42` now has its first-ever grade anchors (3
seeds @ 200t, 1 seed @ 1000t), documented in `eval_matrix_results.md` and `corpus_tier_taxonomy.md`,
with parity-ledger evidence added to `INFRA-240`/`INFRA-241`/`INFRA-250`. The full scoped regression
suite and `make evaluate --dry-run` (710 pillars, 0 regressions) both pass. A genuine new finding — a
late-tick (800→1000) population collapse for this world, previously unexercised — was surfaced by
Step 5's cross-check and documented rather than fixed, per Out of Scope; filed as a real follow-up
ticket, `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE`
(`tickets/todos/TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE.md`), rather than left
as unactioned prose. Ticket finalized and closed with all Definition-of-Done conditions satisfied.
