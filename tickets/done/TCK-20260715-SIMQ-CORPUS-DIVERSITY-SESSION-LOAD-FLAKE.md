---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE
phase: done
date: 2026-07-15
tags: [simulation-quality, calibration, determinism, corpus]
---

# TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE

## Title
Investigate the disclosed residual F6-class flake risk in
`tests/unit/worldassembly/test_corpus_diversity.py`'s `-m slow` grade-stability guards and
`test_grade_regression.py`'s fixed-width score tolerance, both left explicitly unresolved by
`TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP`

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
`TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP` (closing this session) added 14
tolerance-based grade-stability guards to `tests/unit/worldassembly/test_corpus_diversity.py`
after confirming all 14 re-anchored `grade_anchors.json` pillars are genuinely F6-class
load/timing-sensitive (`docs/audits/D06_longrun_health.md` §F6). Its own Implementation Notes
and `staging_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/repro_sweep.md` disclose,
but explicitly do not resolve, two related residual risks:

1. Three named pillars (`urban_political_seed123_1000t` SOCIAL and ECONOMY;
   `frontier_marches_seed42_200t` NARRATIVE) showed real-world score variance, across
   4-7 independent samples each, close to or exceeding `test_grade_regression.py`'s
   `test_grade_within_anchor_band`/`_long_run` fixed-width tolerance formula
   (`max(SCORE_TOLERANCE_ABS_FLOOR, SCORE_TOLERANCE_REL_PCT * |anchor_score|)`, i.e.
   `max(0.05, 0.20 * |anchor|)`), which that ticket was forbidden from widening. A single
   unlucky future draw for these pillars could still fail the fast anchor-band check even with
   a correctly re-anchored value and a correct multi-trial guard in place.
2. Two independent, full, sequential `pytest tests/unit/worldassembly/test_corpus_diversity.py
   -m slow --resource-budget large -v` runs of the whole 32-test file (18 pre-existing + 14 new)
   each showed exactly one guard failing — a different anchor each time
   (`test_frontier_marches_seed42_200t_narrative_grade_stability` in Run 1,
   `test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability` in Run 2) —
   under cumulative session-load pressure from everything that ran earlier in the same
   ~13-minute sequential session. This is roughly a 1-in-16-tests observed failure rate across
   the 32-test file, and the mechanism (cumulative wall-clock compute pressure across a long
   sequential in-process session, not a per-anchor calibration defect) could in principle also
   affect the 2 pre-existing precedent guards
   (`test_urban_political_seed123_500t_cognition_bit_identical_under_load` and
   `test_generated_frontier_3_42_extended_population_stability`), not just the 14 new ones —
   though neither of those two failed in either of the parent ticket's 2 full runs.

The parent ticket's Step 14 explicitly states "a third live-widening round was deliberately not
attempted" for reason (2) above — this was a scope/time-bounded stopping point, not an
abandoned or dismissed finding, and the parent ticket's own text calls for exactly this kind of
follow-up ("A CI/verification process that runs this file's tests with appropriate parallelism
or isolation ... would not be expected to see this effect"). This ticket files that follow-up.

## Scope
- Investigate whether `test_grade_within_anchor_band`/`_long_run`
  (`tests/simulation_quality/test_grade_regression.py`, `_within_score_tolerance()`,
  `SCORE_TOLERANCE_ABS_FLOOR`/`SCORE_TOLERANCE_REL_PCT`) needs an evidence-derived-width option
  for pillars with confirmed high real-world variance, informed by
  `staging_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/repro_sweep.md`'s actual
  measured per-anchor variance (Sections 2-8), specifically for the 3 named pillars above.
- Investigate whether `tests/unit/worldassembly/test_corpus_diversity.py`'s `-m slow` guards
  (all 32: the 18 pre-existing plus the 14 new from the parent ticket) should run with test
  isolation or parallelism in CI (`.github/workflows/test.yml`'s `slow` job, which currently
  invokes `pytest tests/ -m "slow or extra_slow" --resource-budget large --tb=short -q` as one
  long sequential in-process run) to eliminate cross-test cumulative-load contamination as the
  root mechanism of the observed ~1-in-16 flake rate.
- Determine, with evidence, whether remedy (a), remedy (b), both, or neither is the right
  path — this is investigation-tier work. Do not pre-decide the remedy in this ticket; that
  determination belongs to this ticket's own future investigation/plan phase.
- If a remedy is adopted, assess its impact against the existing accepted-tolerance behavior for
  every other pillar/anchor (not just the 3 named ones), so a fix for these 3 does not silently
  loosen or tighten checks elsewhere.
- Update `docs/parity_ledger/infrastructure.yaml` (extend INFRA-273, or add a new entry) and
  `docs/simulation_quality/eval_matrix_results.md` if the investigation results in a behavior or
  process change.

## Out of Scope
- Re-opening `TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP`'s own 14 grade-stability guards
  or their re-anchored `grade_anchors.json` values — those are done and correct as-is; this
  ticket investigates the residual risk they disclosed, it does not re-litigate their content.
- Re-opening `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM`'s original
  `test_urban_political_seed123_500t_cognition_bit_identical_under_load` guard — stays as-is
  unless this investigation's own evidence specifically implicates it (not assumed).
- Any change to `src/engine/kernel.py`'s tick-budget watchdog / mid-tick emergency throttle
  mechanism — same hard constraint as both parent tickets; F6 is documented, intentional engine
  behavior (`docs/audits/D06_longrun_health.md`, `docs/engine/kernel.md`,
  `docs/engine/performance_contract.md` §7). Only test-side / CI-process-side remedies are in
  scope.
- Re-tuning any `scoring_weights.yaml` value or any `simulation_quality` scoring formula outside
  the tolerance-comparison logic named above.
- Adding coverage for anchors/pillars not already named in this ticket's Scope (the 3 named
  score-tolerance-risk pillars, and the 32-test `-m slow` file's flake mechanism as a whole) —
  a broader corpus-wide sweep is not this ticket's job.

## Acceptance Criteria
- [ ] Investigation determines, with cited evidence from `repro_sweep.md` and this ticket's own
      analysis, whether remedy (a) (evidence-derived tolerance width), remedy (b) (CI test
      isolation/parallelism for the `-m slow` guard file), both, or neither is warranted, and
      records the rationale in this ticket's Implementation Notes.
- [ ] If remedy (a) is adopted: a concrete evidence-derived-width mechanism is designed for
      `test_grade_within_anchor_band`/`_long_run` and verified to not change pass/fail outcome
      for any pillar/anchor other than the 3 named ones, with a passing test proving
      `test_within_band_default_tolerance_unchanged`-equivalent protection still holds for the
      unaffected pillars.
- [ ] If remedy (b) is adopted: a concrete CI isolation/parallelism proposal for
      `.github/workflows/test.yml`'s `slow` job (or an equivalent scoped invocation) is designed
      and at least one controlled comparison run (isolated/parallel vs. sequential) is executed
      and its result recorded, testing whether it measurably reduces or eliminates the
      cumulative-load-driven flake.
- [ ] Whichever remedy(ies) are adopted, `docs/parity_ledger/infrastructure.yaml` and
      `docs/simulation_quality/eval_matrix_results.md` are updated to reflect the decision.
- [ ] If neither remedy is adopted, that determination is documented with explicit reasoning
      (not silently dropped), and the residual risk remains disclosed rather than papered over.
- [ ] No change is made to any of the 14 guards' anchors, the 2 pre-existing precedent guards,
      any `grade_anchors.json` value from `TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP`, or
      `src/engine/kernel.py`'s watchdog/throttle mechanism, unless this investigation's own
      evidence specifically requires it and that requirement is called out explicitly.

## Related Tickets
- `TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP` (closing this session) — parent ticket;
  its Implementation Notes' "Net honest state" paragraph and Test Summary are the direct source
  of this ticket's residual-risk disclosure.
- `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM` (done) — established the F6 root-cause
  finding, the repro methodology (`repro_sweep.md` precedent), and the original
  bit-identical-guard pattern (`test_urban_political_seed123_500t_cognition_bit_identical_under_load`)
  this ticket's flake-rate concern extends to.
- `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY` (done) — original precedent for the
  tolerance-based multi-trial guard pattern (`test_generated_frontier_3_42_extended_population_stability`)
- `TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE` (open, filed at close of this
  ticket) — named follow-up tracking a 4th, previously-unnamed pillar
  (`urban_political_seed123_1000t`/NARRATIVE) found during this ticket's own calibration
  regen to show the same F6-class variance, deterministically failing across all 3 fresh
  draws taken this session (0.5210/0.4340/0.4144 vs anchor 0.6603) — outside this ticket's
  authorized 2-entry override scope, disclosed not fixed.
  used by all 14 of the parent ticket's new guards.

## Related Docs
- `docs/audits/D06_longrun_health.md` §F6 — the documented load-sensitive divergence finding
  both parent tickets trace to; this ticket's investigation must stay consistent with its
  "reliably reproducible below ~tick 300-320" hedge, which `TCK-20260715` already sharpened.
- `docs/engine/kernel.md`, `docs/engine/performance_contract.md` §7 — watchdog/throttle
  mechanism F6 attributes the variance to (read-only reference; not to be modified).
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-273` (F6 blast-radius confirmation,
  documents the `test_path` this ticket's `-m slow` flake concerns) and `INFRA-272` (14-anchor
  carve-out closure); this ticket updates or extends these as its own findings land.
- `docs/simulation_quality/eval_matrix_results.md` — "Anchor Reliability Verification, Part 2"
  subsection, the 14-entry record this ticket's findings may extend.

## Related Stored Artifacts
- `staging_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/repro_sweep.md` — source of
  the measured per-anchor variance data (Sections 2-8) this ticket's remedy (a) investigation
  must use. At time of filing this parent ticket is still open in `tickets/inprogress/`; expect
  this artifact to move to `stored_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/`
  once that ticket closes — check both locations.
- `stored_artifacts/TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM/repro_sweep.md` — the
  original repro methodology template both parent tickets and this investigation build on.

## Related Code Areas
- `tests/simulation_quality/test_grade_regression.py` — `_within_score_tolerance()`,
  `SCORE_TOLERANCE_ABS_FLOOR`/`SCORE_TOLERANCE_REL_PCT` (lines 46-47),
  `test_grade_within_anchor_band`/`_long_run`, `test_within_band_default_tolerance_unchanged`
  (the existing guard any remedy-(a) change must not silently break for unaffected pillars).
- `tests/unit/worldassembly/test_corpus_diversity.py` — the 32 `-m slow` grade-stability /
  population-stability guards (18 pre-existing + 14 from `TCK-20260715`), including the 2 named
  precedent guards.
- `.github/workflows/test.yml` — the `slow` job (`pytest tests/ -m "slow or extra_slow"
  --resource-budget large --tb=short -q`, currently one sequential in-process run with no
  isolation/parallelism flag), the CI surface remedy (b) would change.
- `tests/simulation_quality/fixtures/grade_anchors.json` — read-only reference for this
  investigation; not to be modified except as an explicit, called-out consequence of the
  adopted remedy.

## Assumptions / Open Questions
- Whether `pytest-xdist` or an equivalent parallelism/isolation tool is already available or
  acceptable in this repo's CI/test environment is unconfirmed — it is not currently listed as
  a dependency (checked `requirements.txt`, `pyproject.toml` at filing time). Investigation must
  establish this before proposing remedy (b) concretely.
- Whether an evidence-derived-width mechanism for `_within_score_tolerance()` can be scoped as
  a per-pillar/per-anchor override (touching only the 3 named pillars) rather than a global
  formula change is assumed but unverified — if it turns out to require a global formula change,
  that would directly interact with `test_within_band_default_tolerance_unchanged`'s existing
  guard and needs its own explicit resolution, not a silent widening.
- Whether the 2 pre-existing precedent guards genuinely share the new 14's flake exposure, or
  are meaningfully more robust for reasons not yet identified (e.g. narrower trial variance,
  different pillar characteristics), is open — the parent ticket observed zero failures for
  either across 2 full sequential runs, which is suggestive but not proof of either guard's own
  reliability.
- The ~1-in-16 observed rate is based on exactly 2 full-sequential-session samples (2 failures
  across 2 runs of 32 tests) — a small sample. This ticket's own investigation may need
  additional sequential-session runs (or the isolation/parallelism comparison from remedy (b))
  to firm up this estimate before concluding on a remedy.
- `layer: simulation` was inferred from the parent tickets' identical layer value and this
  ticket's SimQ-calibration-and-test-infrastructure scope; not flagged as uncertain.

## Implementation Notes

**AC #1 — remedy determination (both adopted)**: Per investigation.md and plan.md's
Summary, both remedy (a) and remedy (b) were adopted with cited evidence; AC #5 ("if
neither adopted") does not apply.

**Remedy (a) — evidence-derived score-tolerance overrides**
(`tests/simulation_quality/test_grade_regression.py`): added
`SCORE_TOLERANCE_OVERRIDES` (2 entries: `urban_political_seed123_1000t`/ECONOMY
`abs_floor=0.2878`, `frontier_marches_seed42_200t`/NARRATIVE `abs_floor=0.3351`, reused
verbatim from the corresponding `grade_stability` guard's own evidence-derived floor)
and `_score_tolerance_kwargs(run_key, pillar)`, wired into both
`test_grade_within_anchor_band` (line ~289) and `test_grade_within_anchor_band_long_run`
(line ~345). `urban_political_seed123_1000t`/SOCIAL deliberately excluded — its existing
20%-relative default (3.5931) already exceeds the guard's own floor (2.9568), confirmed
by direct arithmetic. Two anti-drift guard tests added
(`test_score_tolerance_override_table_scoped_to_named_pillars`,
`test_score_tolerance_overrides_do_not_affect_unlisted_anchors`), both passing.
`SCORE_TOLERANCE_ABS_FLOOR`/`SCORE_TOLERANCE_REL_PCT` (the global constants) were not
touched; no other call site (`test_urban_political_selfmodel_cognition_isolated_grade_anchor`,
`_execution_isolated_grade_anchor`, `test_information_intent_execution_fires_through_kernel_tick_once`,
`test_score_tolerance_catches_within_band_regression`) was modified.

Calibration data for the 2 affected run_keys was regenerated locally
(`tools/calibrate_simq.py --name urban_political --seed 123 --ticks 1000`;
`--name frontier_marches --seed 42 --ticks 200`) to prove real (non-skip) pass behavior,
per Step 3. `frontier_marches_seed42_200t` passed cleanly on its one fresh draw.
`urban_political_seed123_1000t`'s ECONOMY override was verified across 3 independent
fresh draws (deltas 0.0286, 0, 0.1237 — all comfortably under the 0.2878 floor).

**New out-of-scope finding (disclosed, not fixed)**: those same 3
`urban_political_seed123_1000t` draws all showed NARRATIVE — a pillar with no existing
`grade_stability` guard, not named in this ticket's investigation — landing 0.139-0.246
outside the default ±0.05/20% tolerance (anchor 0.6603; draws
0.5210/0.4340/0.4144; band check unaffected, grade B every time). This ticket's Out of
Scope explicitly forbids adding coverage for anchors/pillars not already named, so no
override was added and `grade_anchors.json` was not touched. Consequence: the specific
command `pytest "tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]" -m slow --resource-budget large -v`
FAILS against the currently-regenerated calibration data on this checkout, on NARRATIVE
only — not because the override mechanism is broken (proven correct via ECONOMY passing
3/3 and the two anti-drift guard tests), but because a 4th, previously-unidentified
pillar exhibits the same F6-class single-draw variance this whole ticket investigates.
Disclosed in `docs/parity_ledger/infrastructure.yaml::INFRA-272`'s new NOTE block and
`eval_matrix_results.md` Part 3, tracked in a named follow-up:
`TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE`.

**Remedy (b) — CI test isolation** (`Makefile`, `.github/workflows/test.yml`,
`tests/static/test_corpus_diversity_ci_isolation.py`): added
`simq-corpus-diversity-slow-isolated` Makefile target — dynamically collects
`test_corpus_diversity.py`'s 32 `-m slow` node IDs via `--collect-only`, asserts the
count is `>=32` (aborting loudly, before the per-nodeid loop, on a short/empty
collection), then runs each node ID as its own `pytest` subprocess. Wired into CI's
`slow` job ahead of the existing sequential invocation, which now carries
`--ignore=tests/unit/worldassembly/test_corpus_diversity.py`. No `pytest-xdist` or other
parallelism plugin was added (confirmed not a dependency; sequential subprocess-splitting
never holds more than one 8 GB `RLIMIT_AS` ceiling at a time, sidestepping the
CI-runner memory-pressure risk `xdist` would introduce). Static architecture guard
(`tests/static/test_corpus_diversity_ci_isolation.py`, 3 tests, all passing) proves the
CI YAML/Makefile wiring shape (dynamic collection, no hardcoded node-ID list, `--ignore`
flag present, correct step ordering) — it does not execute live pytest collection; that
runtime protection is the Makefile target's own `nodeid_count -lt 32` assertion.

**Step 4's count-assertion smoke check (performed for real, not just asserted)**:
temporarily edited the Makefile target to point `--collect-only` at a nonexistent test
file, ran `make simq-corpus-diversity-slow-isolated`, and confirmed it printed
`ERROR: expected >=32 tests from test_corpus_diversity.py -m slow, collected 0 --
aborting...` and exited non-zero (`make: *** [Makefile:317: ...] Error 1`) — with no
`[isolated]` subprocess line printed, proving the guard trips before the per-nodeid loop
starts. Reverted the Makefile to its real form immediately after; confirmed
`git diff --stat -- Makefile` shows only the intended additive target.

**Step 7 — controlled comparison** (`isolation_comparison.md`): ran the isolated
Makefile target twice (32/32 passed both times, 16m50s and 14m48s wall-clock) and one
fresh sequential-baseline run (32/32 passed, 18m23s). Honest result: **all 3 of this
session's own fresh runs came back completely clean** — the sequential-baseline sample
that the original ~1-in-16 estimate predicted had roughly even odds of failing did not
fail this time. The isolated-vs-sequential contrast recorded in the comparison artifact
therefore rests on pooling this session's clean isolated samples against the *parent*
ticket's 2 older failing sequential samples (cited from `repro_sweep.md` Section 8), not
on a live within-session A/B difference. This is stated plainly, not overclaimed — the
remedy's justification is architectural (subprocess isolation structurally removes the
cross-test session-load-carryover mechanism the parent ticket characterized), not
statistically proven by 5 sequential-style + 2 isolated total observations. An
unexpected, honestly-disclosed finding: both isolated samples were *faster* in wall-clock
than the sequential sample on this machine, contradicting the plan's Anti-Drift Notes'
prediction that isolation would cost more wall-clock — recorded as one-machine evidence,
not a general claim.

**AC #3 assessment**: at the moment this ticket's implementation work concluded, both
`make simq-corpus-diversity-slow-isolated` (×2) and a fresh sequential
`pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow --resource-budget
large -v` were fully green (32/32 each), satisfying the AC's literal requirement. This
is not a guarantee of permanent flake-freedom — the underlying F6 watchdog/throttle
variance was not disabled or changed (out of scope, confirmed byte-identical
`src/engine/kernel.py`) — only the cumulative-session-load *mechanism* the isolated lane
targets was structurally removed from the CI path.

**AC #4**: `docs/parity_ledger/infrastructure.yaml` — INFRA-272's NOTE extended with a
RESOLVED pointer (remedy a) plus a new "HONEST DISCLOSURE, NOT RESOLVED" block (the
NARRATIVE finding above); INFRA-273 extended with an UPDATE block in `v2_evidence` and
`test_path` citing the isolation remedy and `isolation_comparison.md`. Original text of
both entries left intact (append-only, per project convention).
`docs/simulation_quality/eval_matrix_results.md` — new "Anchor Reliability
Verification, Part 3" subsection appended after Part 2 (untouched); summarizes both
remedies and cross-references `isolation_comparison.md` and the parity ledger updates.

**AC #6 — scope guards held**: `git diff --stat` confirmed empty for `src/engine/kernel.py`,
`tests/unit/worldassembly/test_corpus_diversity.py` (the 14 guards + 2 precedent guards),
and `tests/simulation_quality/fixtures/grade_anchors.json`.

## Test Summary

- `tests/simulation_quality/test_grade_regression.py::test_score_tolerance_override_table_scoped_to_named_pillars` — PASS (new)
- `tests/simulation_quality/test_grade_regression.py::test_score_tolerance_overrides_do_not_affect_unlisted_anchors` — PASS (new)
- `tests/simulation_quality/test_grade_regression.py::test_within_band_default_tolerance_unchanged` — PASS (unaffected, regression check)
- `tests/simulation_quality/test_grade_regression.py::test_grade_anchors_entry_count_unchanged` — PASS (unaffected, regression check)
- `tests/simulation_quality/test_grade_regression.py::test_score_tolerance_catches_within_band_regression` — PASS (unaffected, regression check)
- `tests/simulation_quality/test_grade_regression.py -m "not slow"` (deselecting the
  pre-existing, unrelated `test_grade_anchor_file_exists_and_valid` failure — confirmed
  via `git stash` to fail identically with and without this ticket's diff, caused by a
  missing `hero_guild_routing_seed42_1000t` calibration fixture on this fresh checkout,
  not by this ticket's changes) — 7 passed, 57 skipped, 19 deselected.
- `test_grade_within_anchor_band[frontier_marches_seed42_200t]` — PASS (real calibration
  data, not skip)
- `test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]` -m slow
  --resource-budget large — FAIL, on NARRATIVE only (out-of-scope finding, see
  Implementation Notes; ECONOMY and SOCIAL both pass against the same calibration data)
- `tests/static/test_corpus_diversity_ci_isolation.py` (3 new tests) — PASS
- `tests/static/` (full directory, 6 tests) — PASS, no regression
- `make simq-corpus-diversity-slow-isolated` ×2 — PASS, 32/32 both times (16m50s, 14m48s)
- `pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow --resource-budget
  large -v` (fresh sequential baseline) — PASS, 32/32 (18m23s)
- Step 4 count-assertion smoke check (manual, one-time) — CONFIRMED: aborts non-zero,
  before the subprocess loop, on short/empty collection.
- `python3 -c "import yaml; yaml.safe_load(...)"` — both `.github/workflows/test.yml`
  and `docs/parity_ledger/infrastructure.yaml` parse cleanly after edits.

## Files Changed

- `tests/simulation_quality/test_grade_regression.py` — Steps 1-3 (override table,
  helper, wiring, 2 new anti-drift tests)
- `Makefile` — Step 4 (new `simq-corpus-diversity-slow-isolated` target + `.PHONY` entry)
- `.github/workflows/test.yml` — Step 5 (new isolated-lane step + `--ignore` flag on the
  existing sequential step)
- `tests/static/test_corpus_diversity_ci_isolation.py` — Step 6 (new file, 3 static
  guard tests)
- `staging_artifacts/TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE/isolation_comparison.md` — Step 7 (new file)
- `docs/parity_ledger/infrastructure.yaml` — Step 8 (INFRA-272 NOTE extended, INFRA-273
  UPDATE block appended)
- `docs/simulation_quality/eval_matrix_results.md` — Step 9 (new Part 3 subsection)
- `staging_artifacts/TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE/plan.md` —
  Deviations section added
- `tickets/inprogress/TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE.md` — this
  file (Implementation Notes/Test Summary/Files Changed/Completion Summary)
- `data/calibration/urban_political_seed123_1000t/`,
  `data/calibration/frontier_marches_seed42_200t/` — regenerated locally (gitignored,
  not part of the commit diff)
- `agent-monitoring/tools.jsonl` — auto-updated by tooling, staged per project convention

## Completion Summary

Both remedies named in this ticket's Scope were investigated and adopted with cited
evidence. Remedy (a) (evidence-derived score-tolerance overrides for the 2 named
pillars) is fully implemented, wired, and verified against real regenerated calibration
data — proven correct via 3/3 clean draws for the ECONOMY override and the two new
anti-drift guard tests. Remedy (b) (CI isolation for `test_corpus_diversity.py`'s 32
`-m slow` guards via per-test subprocesses) is fully implemented and wired into CI ahead
of the now-`--ignore`-flagged sequential step, with a static guard test protecting the
wiring shape and a manually-verified, load-bearing count assertion protecting the
runtime collection step. At the point this implementation concluded, both the isolated
lane (×2) and a fresh sequential run of `test_corpus_diversity.py -m slow
--resource-budget large` were fully green (32/32), meeting this ticket's own stated
deliverable. Two findings are disclosed rather than force-fit into a clean narrative:
(1) a 4th, previously-unnamed pillar (`urban_political_seed123_1000t`/NARRATIVE) showed
the same F6-class single-draw variance during calibration regen but is out of this
ticket's authorized override scope, tracked in a named follow-up
(`TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE`); (2) the controlled
comparison's apparent isolated-vs-sequential improvement rests on pooling with the
parent ticket's older failing samples rather than a live within-session difference, since
all of this session's own fresh runs (isolated and sequential alike) happened to come
back clean — reported honestly as a thin-sample-size caveat rather than overclaimed as
a proven fix. No change was made to `src/engine/kernel.py`, the 14 `grade_stability`
guards, the 2 precedent guards, or `grade_anchors.json` — confirmed via empty
`git diff --stat` for all three.
