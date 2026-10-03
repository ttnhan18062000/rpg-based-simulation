---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260713-SIMQ-RAWSCORE-PERSIST
artifact_type: plan
tags: [simulation-quality, calibration, corpus]
---

# Implementation Plan — TCK-20260713-SIMQ-RAWSCORE-PERSIST

## Summary

Extend `grade_anchors.json`'s per-pillar schema from a bare grade string (`"S"`) to an object
carrying both `grade` and `normalized_score` (e.g. `{"grade": "S", "score": 2.87}`), migrating all
75 existing entries by reading the already-regenerated `data/calibration/{run_key}/quality_report.json`
files left on disk by the same-day sibling ticket `SCORE-CEILING-FIX` (no fresh corpus sweep). Update
the two real code consumers of the per-pillar shape — `test_grade_regression.py`'s three anchor-read
call sites plus its strict-validation test, and `tools/evaluate_simq.py::main()`'s one call site — to
read `["grade"]` explicitly. Add a new, independent score-tolerance assertion using a combined
absolute-floor-or-relative-percentage tolerance (`abs_delta <= 0.05` OR `relative_delta <= 20%`,
whichever is wider), derived directly from this session's 18-run_key/180-observation trial-pair
dataset in `investigation.md`. Add the AC-mandated before/after demonstration test proving the new
check catches what the old letter-only check misses. `evaluate_simq.py` gets only the minimal
schema-compat fix, not a mirrored tolerance check (deferred, see Anti-Drift Notes). Update the two
touched parity ledger entries (`INFRA-250`, `INFRA-252`).

## Steps

### Step 1 — Migrate `grade_anchors.json` schema (bare string → `{grade, score}` object)
**Files:** `tests/simulation_quality/fixtures/grade_anchors.json`
**Change:** Write a one-time migration script (throwaway, does not need to be committed to the repo
— e.g. run from an interactive Python shell or a scratch script) that:
1. Loads `grade_anchors.json`, iterating only non-metadata keys (skip `_note`, `_instructions`,
   `_grade_order`) — 75 scenario entries, including the 3 `unit_information_density_seed{42,123,456}_200t`
   entries added today by `SCORE-CEILING-FIX`.
2. For each `run_key`, reads `data/calibration/{run_key}/quality_report.json` (already on disk,
   regenerated today by the sibling ticket — do not re-run the corpus sweep).
3. For each pillar, replaces the bare grade string with `{"grade": existing_grade, "score":
   report["pillars"][pillar]["normalized_score"]}`. Use `normalized_score`, **not** `raw_score`
   (they differ by an order of magnitude — e.g. `dungeon_crawl_seed42_5200t` COMBAT: `raw_score=215.0`
   vs `normalized_score=0.0426`; only `normalized_score` is what grade bands are defined against
   per §4.5).
4. Writes the result back preserving key order and the 3 metadata keys unchanged.
5. Sanity-check before committing: total scenario-entry count is still 75; every pillar value is now
   a dict with exactly `{"grade", "score"}`; the existing grade strings are byte-identical to what
   they were before migration (only the value's *type* changes, not its grade content).
**Do NOT touch:** `_note`, `_instructions`, `_grade_order` metadata keys' structure (content of
`_instructions` is updated in Step 2, separately); do not regenerate any `data/calibration/` report
(read-only source for this step); do not add, remove, or rename any scenario entry.
**Verify:** `tests/simulation_quality/test_grade_regression.py::test_grade_anchor_file_exists_and_valid`
(after Step 3's edits land) confirms structural validity; manual `json.load` + key-count check
(75 entries, `len(entry) == 10` per entry, each value a dict) before moving to Step 3.

### Step 2 — Update `_instructions` metadata text
**Files:** `tests/simulation_quality/fixtures/grade_anchors.json`
**Change:** Update the `_instructions` key's text (currently describes only the ±1-letter mechanism)
to also describe the new score-tolerance check: both fields are checked independently, per pillar —
letter-grade band (±1, unchanged) and score tolerance (absolute-floor-or-relative-percentage,
documented with its values from Step 4).
**Do NOT touch:** `_note`, `_grade_order` — only `_instructions` text changes.
**Verify:** No dedicated test (this is fixture housekeeping); confirmed by visual diff review during
implementation and by `test_grade_anchor_file_exists_and_valid` not asserting on `_instructions`
content (only structure), so this step cannot break that test.

### Step 3 — Fix anchor-read call sites in `test_grade_regression.py` for the new schema
**Files:** `tests/simulation_quality/test_grade_regression.py`
**Change:**
1. In `test_grade_within_anchor_band` (~line 193), `test_grade_within_anchor_band_long_run`
   (~line 229), and `test_urban_political_selfmodel_cognition_isolated_grade_anchor` (~line 263):
   change `anchor_grade = anchors[pillar]` to `anchor_grade = anchors[pillar]["grade"]` before the
   existing `_within_band(actual, anchor_grade)` call. Do not change `_within_band`'s signature or
   default (`tolerance=1` stays exactly as-is).
2. In `test_grade_anchor_file_exists_and_valid` (~line 301): change the per-pillar assertion from
   `assert grade in GRADE_ORDER` to `assert entry[pillar]["grade"] in GRADE_ORDER`. Add a new
   structural assertion in the same guarded iteration (do not add a second raw `for key in
   grade_anchors` loop — reuse the existing metadata-key-excluding iteration) checking: each pillar
   value is a `dict` with exactly the keys `{"grade", "score"}`; `score` is `isinstance(score, (int,
   float))` and not `None`/`str`. Also add the field-confusion guard: for at least one known
   S-graded entry (e.g. `hero_guild_routing_seed42_1000t` NARRATIVE, or whichever S-band entry
   survived migration), assert `entry[pillar]["score"] > 2.0` and that it is *not* equal to that
   run's `raw_score` from the calibration report (catches an implementer wiring the wrong field).
   Keep the existing `len(entry) == 10` pillar-count assertion unchanged.
**Do NOT touch:** `_within_band()` function body or signature; `GRADE_ORDER` constant;
`FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` lists; `_extract_pillar_grades()` (still reads `"grade"` from
the *live* `quality_report.json`, an unrelated, already-correct shape — do not confuse this with the
anchor-file read).
**Verify:** `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v` — all fast
tests pass on the new schema.

### Step 4 — Add score-tolerance assertion (new, independent check)
**Files:** `tests/simulation_quality/test_grade_regression.py`
**Change:** Define two module-level constants near `GRADE_ORDER` (~line 34):
```python
SCORE_TOLERANCE_ABS_FLOOR = 0.05
SCORE_TOLERANCE_REL_PCT = 0.20
```
Add a helper `_within_score_tolerance(actual_score, anchor_score, abs_floor=SCORE_TOLERANCE_ABS_FLOOR,
rel_pct=SCORE_TOLERANCE_REL_PCT) -> bool` that returns `True` if
`abs(actual_score - anchor_score) <= max(abs_floor, rel_pct * abs(anchor_score))` — i.e. the check
passes if the delta is within *either* the absolute floor *or* the relative percentage, whichever
tolerance is wider at that magnitude. Fold a call to this helper into
`test_grade_within_anchor_band` and `test_grade_within_anchor_band_long_run` as an **additional**
assertion block per pillar (not a new parametrized test function — reuses the existing per-run_key
parametrization, per the ticket's "one additional tolerance assertion" framing). Failures from this
new check must be collected into a separate failure list/message from the existing letter-band
failures, so a CI reader can tell "letter moved" apart from "same letter, magnitude drifted" (per
test_plan.md New Test #3). Do the same for
`test_urban_political_selfmodel_cognition_isolated_grade_anchor` — this pillar (COGNITION) may
occasionally trip this new check due to the separate, already-tracked
`TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM` bug; this is acceptable (the existing ±1-letter
check already can trip on that bug too) and must **not** be special-cased with a wider tolerance for
COGNITION specifically.
**Do NOT touch:** `_within_band`'s `tolerance=1` default (assert this is unchanged, e.g. via a quick
`assert _within_band.__defaults__ == (1,)` sanity check during review); do not add any
pillar-specific tolerance override (COGNITION included) — the tolerance constants apply uniformly to
all 10 pillars.
**Verify:** `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -v` (fast tier)
and, once before Finalize, `pytest tests/simulation_quality/test_grade_regression.py -m slow -v`
(long-run tier) — both pass with the new assertion active against the migrated fixture.

### Step 5 — Before/after demonstration test (AC-mandated proof)
**Files:** `tests/simulation_quality/test_grade_regression.py`
**Change:** Add a new, dedicated test function `test_score_tolerance_catches_within_band_regression()`.
Construct an in-memory synthetic anchor value `{"grade": "S", "score": 4.5}` and a synthetic "live"
value of `2.25` (exactly half, still `> 2.0` so still grade `S` — same letter band). Assert, in the
same test:
1. The OLD mechanism — `_within_band("S", "S")` — returns `True` (PASS), demonstrating the gap this
   ticket closes.
2. The NEW mechanism — `_within_score_tolerance(2.25, 4.5)` — returns `False` (FAIL), since
   `abs(2.25 - 4.5) = 2.25` exceeds `max(0.05, 0.20 * 4.5) = 0.9`.
Do not use a committed calibration scenario for this — it is a synthetic in-memory demonstration, not
a new anchor entry.
**Do NOT touch:** No committed fixture or scenario changes in this step; this test is self-contained.
**Verify:** The new test itself, run via `pytest tests/simulation_quality/test_grade_regression.py::test_score_tolerance_catches_within_band_regression -v`.

### Step 6 — Fix `tools/evaluate_simq.py`'s schema-compat break (minimal fix only)
**Files:** `tools/evaluate_simq.py`, `tests/simulation_quality/test_evaluate_harness.py`
**Change:** In `main()` (~line 200), change `anchor_grades = all_anchors[run_key]` to
`anchor_grades = {p: v["grade"] for p, v in all_anchors[run_key].items()}` before it is passed into
`_compare()`. This is the one real call-site break identified in investigation.md — `_compare()`
itself keeps taking `dict[str, str]` and does not change. Add a test in
`test_evaluate_harness.py` that loads a small in-memory or `tmp_path`-fixtured anchor dict in the new
`{"grade":..., "score":...}` object schema and confirms `main()`'s read path produces the same
`_compare()` inputs it would have produced under the old bare-string schema; include a dry-run smoke
test against the post-migration real fixture (using an existing `data/calibration/` report) to catch
key-ordering/typing issues a synthetic dict might miss.
**Do NOT touch:** `_compare()` or `_within_band()` function bodies/signatures in
`tools/evaluate_simq.py` (they stay on bare grade strings — confirmed by
`test_evaluate_harness.py::TestCompare`/`TestWithinBand` which must keep passing unmodified). Do
**not** add a score-tolerance check to `evaluate_simq.py`/`_compare()` in this step — that is
explicitly deferred, see Anti-Drift Notes below.
**Verify:** `pytest tests/simulation_quality/test_evaluate_harness.py -v` — all existing tests
unchanged and green, plus the new schema-compat test passing.

### Step 7 — Update `quality_scoring_contract.md` §11.3 (architecture-review finding, 2026-07-13)
**Files:** `docs/simulation_quality/quality_scoring_contract.md`
**Change:** §11.3 ("Regression Tests (grade stability)") currently describes only the single,
letter-band-only comparison mechanism ("a code change that moves a pillar grade by more than one
letter ... must be explicitly justified and the anchor updated"). Update this section to describe
the anchor-comparison mechanism as now having **two independent dimensions**: (1) the existing
letter-grade ±1-band check (unchanged), and (2) the new score-tolerance check (raw `normalized_score`
must stay within `max(0.05, 0.20 * |anchored_score|)` of the anchored value, independent of whether
the letter grade moved — catches within-band magnitude regressions the letter-only check cannot
see). State plainly that either check failing independently blocks the anchor as a regression. Do
not touch §11.6 (evaluate_simq.py's own harness description) — its "±1-band parity" claim remains
accurate and unchanged, since Step 6 deliberately does not add the tolerance check there.
**Do NOT touch:** §4.4 (`normalized_score` formula — unchanged), §4.5 (grade bands — unchanged),
§14 (Non-Goals — unchanged, this ticket stays inside the existing regression-detection goal). Do
not touch any chapter/section beyond §11.3.
**Verify:** No pytest coverage (doc-only) — manual review that §11.3's updated text accurately
matches the tolerance formula implemented in Steps 3-4. Since `docs/` is modified, run
`make knowledge-index-update` per the project's After Work rule (can be combined with Step 8's doc
change into a single index-update run).

### Step 8 — Update parity ledger entries
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:**
- `INFRA-250`: update `text`/`v2_evidence` to describe the new two-field
  (`grade`+`score`) anchor schema and the second, independent score-tolerance dimension (absolute
  floor 0.05 / relative 20%, whichever wider) alongside the existing ±1-letter check. Keep
  `test_path` entries (`test_grade_within_anchor_band`, `test_grade_anchor_file_exists_and_valid`)
  and add `test_score_tolerance_catches_within_band_regression`.
- `INFRA-252`: update `text` to note the schema-compatibility fix in `main()`'s call site (do not
  fix the pre-existing stale "25 entries" count unless trivial — that staleness predates this
  ticket and is not in scope; if corrected in passing, note it as incidental, not as ticket work).
**Do NOT touch:** Any other parity ledger file/entry; do not touch P0 entries (none overlap this
ticket per investigation.md).
**Verify:** No test gate (both entries are P1, not P0) — verified by visual review that `status`,
`v2_evidence`, and `test_path` accurately reflect the new code state, and that the ledger's
description is consistent with Step 7's contract-doc update.

### Step 9 (optional housekeeping, low-cost, not tied to any AC) — Align `simq-audit.js` prompt text
**Files:** `.claude/workflows/simq-audit.js`
**Change:** Update the `anchor-updater` agent's prompt text (~line 219, currently "edit
`grade_anchors.json` (new grade for an anchor key)") to also mention updating the `score` field,
preventing a future SimQ-audit run from updating `grade` while silently leaving `score` stale (flagged
as a prose drift risk in investigation.md Risk #4).
**Do NOT touch:** Any other part of the workflow file; this is a prose-only edit, not a logic change.
**Verify:** No automated test (this is LLM-orchestration prompt text, not parsed JSON/code); verified
by manual review only. Skip this step entirely if it risks scope creep beyond a one-line prose edit —
it is explicitly not required by any acceptance criterion.

## Scope Guards

- Do not touch the weight/threshold recalibration itself (`TCK-20260713-SIMQ-SCORE-CEILING-FIX`'s
  domain) — this ticket only adds visibility into score magnitude, it does not change what the
  scores are.
- Do not re-run a fresh full corpus sweep for the migration — reuse the sibling ticket's
  already-regenerated `data/calibration/{run_key}/quality_report.json` files on disk.
- Do not persist scores anywhere beyond `grade_anchors.json` (no new long-term storage of
  `data/calibration/`'s per-run reports — those remain transient/gitignored as today).
- Do not build any dashboard, trend chart, or cross-run comparison UI/tooling (§14 Non-Goal,
  explicitly reaffirmed out of scope by the ticket).
- Do not change `_compare()`'s or `_within_band()`'s signatures in either
  `tools/evaluate_simq.py` or `test_grade_regression.py` — both operate on bare grade strings by
  design; the fix belongs at the call site that reads the raw JSON, not inside these helpers.
- Do not add a score-tolerance check to `tools/evaluate_simq.py` in this ticket (deferred — see
  Anti-Drift Notes).
- Do not widen `_within_band`'s existing `tolerance=1` default while adding the new score check —
  the two checks are independent and additive, not a replacement of one for a looser other.
- Do not special-case or widen the tolerance for COGNITION specifically to accommodate the known
  `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM` bug — that bug is tracked and fixed
  elsewhere; this ticket's tolerance applies uniformly across all 10 pillars.
- Do not use `raw_score` anywhere in this ticket's persisted field or tolerance math — only
  `normalized_score` is the correct field.
- Do not scope the migration to "the pre-existing 72" — the 3 newest
  `unit_information_density_seed{42,123,456}_200t` entries (added today by the sibling ticket) must
  be migrated too, for a total of 75.

## Dependency Map

- **Step 1** (schema migration) must complete and be structurally valid before **Steps 3, 4, 5, 6**
  can pass their tests (they read/assert against the new schema). Step 1 itself has no dependencies.
- **Step 2** (instructions text) depends only on Step 1's schema existing (so the description is
  accurate) — otherwise independent of Steps 3–6, can be done in parallel/either order.
- **Step 3** (call-site fixes) should land before **Step 4** (new tolerance assertion) in the same
  file, since Step 4's assertions are added into the same test functions Step 3 is repairing — doing
  them as one coherent edit to `test_grade_regression.py` is fine, but Step 3's fixes are the
  prerequisite for the file to even import/collect without errors.
- **Step 5** (demonstration test) depends on Step 4's `_within_score_tolerance` helper existing.
- **Step 6** (`evaluate_simq.py` fix) is independent of Steps 2–5 (different file), but depends on
  Step 1 (needs the migrated schema to test against).
- **Step 7** (`quality_scoring_contract.md` §11.3 update) depends on Steps 3-4's tolerance formula
  being finalized (the doc text must match the actual constants), but is otherwise independent of
  Step 6.
- **Step 8** (parity ledger) should be done last among the required steps, after Steps 1–7 land, so
  the ledger accurately describes the final code AND doc state (its `v2_evidence` should be
  consistent with Step 7's contract text, not just the code).
- **Step 9** (optional) is independent of everything except Step 1 (needs the schema to exist to
  describe it correctly); can be skipped without blocking any other step.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `grade_anchors.json` stores both grade and raw score per pillar per anchor entry | Step 1 | `test_grade_anchor_file_exists_and_valid` (Step 3's new structural assertions) |
| `test_grade_regression.py` asserts the raw score stays within a documented tolerance, in addition to the existing letter-grade band check | Steps 3, 4 | `test_grade_within_anchor_band`, `test_grade_within_anchor_band_long_run`, `test_urban_political_selfmodel_cognition_isolated_grade_anchor` |
| A deliberately-injected synthetic score regression within the same letter-grade band is caught by the new check, and demonstrated NOT caught by the old check | Step 5 | `test_score_tolerance_catches_within_band_regression` |
| The tolerance width is justified against real run-to-run variance data | Step 4 (constants derivation) | No standalone test — justified in this plan's Summary/Anti-Drift Notes citing investigation.md's 18-run_key/180-observation dataset; reviewable via `SCORE_TOLERANCE_ABS_FLOOR`/`SCORE_TOLERANCE_REL_PCT` constants, Step 2's updated `_instructions` text, and Step 7's `quality_scoring_contract.md` §11.3 update |
| Update any other code reading `grade_anchors.json` as bare strings (`tools/evaluate_simq.py`) | Step 6 | `test_evaluate_harness.py` new schema-compat test |

## Anti-Drift Notes

- **`normalized_score` vs `raw_score`**: the two fields differ by an order of magnitude (e.g.
  COMBAT `raw_score=215.0` vs `normalized_score=0.0426`); only `normalized_score` is what grade
  bands are defined against (§4.5). Step 1's migration script and Step 3's field-confusion guard
  assertion both exist specifically to prevent wiring the wrong one.
- **Tolerance derivation, made explicit here**: investigation.md's 18-run_key trial2/trial3 dataset
  (135/180 bit-identical, 45/180 differing) shows all observed noise concentrates at *low absolute
  magnitude* — max observed absolute delta ~0.0191 (ECONOMY, `dungeon_crawl_seed456_2000t`), with
  relative deltas up to 43.5% purely because the denominator is small. S-band (`>2.0`) pillars show
  <0.2% relative noise in the same data. A flat percentage tolerance cannot satisfy both ends (a
  tight enough % to catch the AC's 50%-cut synthetic case would false-positive on the 43.5%
  low-magnitude noise; a wide enough % to tolerate that noise would fail to catch a 50% cut). The
  chosen design — `abs_delta <= 0.05 OR relative_delta <= 20%` (pass if *either* holds) — resolves
  this: the 0.05 absolute floor is >2.5x the largest observed legitimate absolute delta, so all of
  this session's real noise (including the 43.5%, 24%, and 16% relative outliers, all under ~0.035
  absolute) passes via the floor regardless of its relative %. The 20% relative threshold, which
  only binds at higher magnitudes where the absolute floor is already exceeded, still catches any
  regression of 20%+ — comfortably below the AC's 50%-cut demonstration case, giving a 2.5x safety
  margin on that side too.
- **COGNITION-under-load exclusion**: the `>300x` runaway observed in `SCORE-CEILING-FIX`'s Step 12
  (`grade=B, raw_score=11.0` clean vs `grade=S, raw_score=3521.0` under load) is a separate,
  already-tracked bug (`TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM`), not organic run-to-run
  variance — it is not part of the 18-run_key clean trial-pair dataset used to derive the tolerance
  constants above, and must not be used to justify widening them. The new score check may
  legitimately trip on COGNITION until that separate bug is fixed; this mirrors how the existing
  ±1-letter check already can trip on the same bug, and is explicitly not a regression introduced by
  this ticket.
- **`evaluate_simq.py` score-tolerance parity deferred, not omitted by oversight**: §11.6 of the
  quality scoring contract frames the standing harness as using "the same ±1 band tolerance as the
  regression tests," and this ticket's new score check creates a parity gap between the harness and
  the pytest suite. Resolved as: fix only the mandatory schema-compat break (the real crash/misbehavior
  at `main()`'s call site) in this ticket; do not mirror the new score-tolerance check into
  `_compare()`/`main()`. Rationale: the tolerance check is not required by any AC, and adding it would
  require plumbing `score` data through `_compare()`'s output-row shape and duplicating Step 4's
  tolerance logic — a larger surface than this ticket's "one additional number, one additional
  assertion" framing justifies. This gap should be filed as a follow-up ticket if the standing-harness
  parity is later judged worth closing; it is not silently dropped, it is explicitly deferred here
  with rationale (per investigation.md Risk #3).
- **`.claude/workflows/simq-audit.js` prose drift** (Step 9): low-cost, optional, not required by any
  AC — do not let this step expand into anything beyond a one-line prompt text edit.
- **Metadata-key exclusion**: `_note`, `_instructions`, `_grade_order` must keep being excluded from
  every iteration touching `grade_anchors.json` — do not regress this filter while editing the file
  in Steps 1–2.

## Unresolved Questions

None. All three flagged design questions (tolerance width/shape, `evaluate_simq.py` scope, COGNITION
exclusion) are resolved above using investigation.md's own empirical numbers — see Anti-Drift Notes
for the full justification of each.

## Deviations

- **Step 3 (implementation addition, not a scope change)**: added a new
  `_extract_pillar_scores(report) -> dict[str, float]` helper in `test_grade_regression.py`,
  mirroring the existing `_extract_pillar_grades()`, to read each pillar's live
  `normalized_score` out of `quality_report.json`. The plan's Step 4 requires comparing the
  live score against the anchored score but did not name a helper for extracting the live
  side; this is the minimal, directly-analogous addition needed to do so (same shape as the
  pre-existing grade-extraction helper) and does not touch `_within_band`, `_compare`, or
  any other function the plan explicitly scoped.
- All other steps (1, 2, 4, 5, 6, 7, 8, 9) implemented exactly as specified, with no
  scope changes. Step 9 was completed (not skipped) since the one-line prose edit stayed
  within the "low-cost, optional" bound the plan set for it.
