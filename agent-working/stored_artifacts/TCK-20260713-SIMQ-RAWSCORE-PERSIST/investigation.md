---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260713-SIMQ-RAWSCORE-PERSIST
artifact_type: investigation
tags: [simulation-quality, calibration, corpus]
---

# Investigation — TCK-20260713-SIMQ-RAWSCORE-PERSIST

## Current Behavior

### `grade_anchors.json` — current schema (re-verified today, post `SCORE-CEILING-FIX`)
`tests/simulation_quality/fixtures/grade_anchors.json` has **78 top-level keys**: 3 metadata keys
(`_note`, `_instructions`, `_grade_order`) + **75 real scenario entries** (confirmed via
`json.load` + key count, not the ticket's own cited 72×10 — that count is stale, superseded by
`TCK-20260713-SIMQ-SCORE-CEILING-FIX`'s same-day re-anchor pass, which added 3 new
`unit_information_density_seed{42,123,456}_200t` entries on top of the pre-existing 72). Each
scenario entry is `{PILLAR: "GRADE"}` — a bare string per pillar, e.g.:
```json
"sandbox_world_seed42_200t": {
  "COGNITION": "B", "AGENCY": "C", "COMBAT": "C", "FACTION": "S", "ECONOMY": "C",
  "PROGRESSION": "C", "SOCIAL": "C", "INFORMATION": "B", "WORLD": "B", "NARRATIVE": "A"
}
```
Confirmed via `stored_artifacts/TCK-20260713-SIMQ-SCORE-CEILING-FIX/plan.md`'s own Scope Guards:
*"Do not extend `grade_anchors.json`'s schema to store raw scores — `TCK-20260713-SIMQ-RAWSCORE-
PERSIST` owns that; this ticket's anchor edits are letter-grade values only, same schema."* — clean
handoff, schema is untouched by the sibling ticket as promised.

### `tests/simulation_quality/test_grade_regression.py` — the primary consumer
- `GRADE_ORDER = ["D","C","B","A","S"]` (line 34).
- `FAST_ANCHOR_KEYS` (41–112) / `SLOW_ANCHOR_KEYS` (114–139) — now 53 fast + 19 slow (including
  the ticket-cited `unit_information_density_seed{42,123,456}_200t` fast keys added at
  lines 104-111 today).
- `_within_band(actual, anchor, tolerance=1)` (line 148) — pure letter-index distance check, no
  magnitude awareness at all.
- `_extract_pillar_grades(report)` (line 159) — `{pillar: data["grade"] for pillar, data in
  report["pillars"].items()}` — reads only `"grade"` from `quality_report.json`'s pillar dict, not
  `"normalized_score"`, even though that field exists in every report (see below).
- `grade_anchors` fixture (line 182) — loads the raw JSON, so `anchors[pillar]` is currently a bare
  string in every call site.
- `test_grade_within_anchor_band` (193), `test_grade_within_anchor_band_long_run` (229),
  `test_urban_political_selfmodel_cognition_isolated_grade_anchor` (263) all do
  `for pillar, anchor_grade in anchors.items(): ... _within_band(actual, anchor_grade)` — this
  breaks the moment `anchor_grade` becomes a dict (`_within_band` returns `False` unconditionally
  since a dict is never `in GRADE_ORDER`), so every one of these tests needs its anchor-read
  updated to `anchor_grade = anchors[pillar]["grade"]` (or equivalent) for the migration.
- `test_grade_anchor_file_exists_and_valid` (301) is the strictest consumer: asserts
  `len(entry) == 10` (still valid — pillar count is unaffected by the schema change) and
  `assert grade in GRADE_ORDER` per pillar (317) — this specific assertion must become
  `assert entry[pillar]["grade"] in GRADE_ORDER`, and a **new** assertion for the score field's
  presence/type belongs here too (this is the natural home for a "every entry has both fields,
  every score is a number" structural check).

### `data/calibration/{run_key}/quality_report.json` — the source of the score to persist
Confirmed via a live sample (`dungeon_crawl_seed42_5200t/quality_report.json`): each pillar object
already carries `raw_score`, `normalized_score`, `grade`, `event_count`, `negative_count`,
`loop_detected`, `loop_flags`, `worst_events`. The ticket's "raw `normalized_score`" language means
the **`normalized_score`** field specifically (the value grades are assigned from, per §4.4) — not
`raw_score` (the unnormalized pre-division accumulator total, a different, larger-magnitude number
that is *not* what feeds grade assignment). The example in the ticket/roadmap,
`{"grade": "S", "score": 2.87}`, is consistent with `normalized_score` magnitudes (S starts at
`>2.0`), confirming `normalized_score` — not `raw_score` — is the field to persist.

### `tools/evaluate_simq.py` — the second known consumer
- `_within_band`/`_extract_pillar_grades` (lines 36-43) — same shape as the test file's helpers,
  operate on bare grade strings; no change needed to these two functions themselves.
- `_compare()` (113-127) — takes `anchor_grades: dict[str, str]` and does
  `for pillar, anchor in anchor_grades.items()` directly — **this is the one real call-site break**.
- `main()` (141-225), line 200: `anchor_grades = all_anchors[run_key]` — passes the raw per-pillar
  dict straight from the JSON file into `_compare()`. Once the schema changes to
  `{"grade":..., "score":...}` objects, this line must be rewritten to extract just the grade
  (e.g. `anchor_grades = {p: v["grade"] for p, v in all_anchors[run_key].items()}`) before calling
  `_compare()`, or `_compare()` itself must be taught the new shape. Confirmed via
  `tests/simulation_quality/test_evaluate_harness.py::TestCompare`/`TestWithinBand` — those tests
  pass bare strings directly and do not need to change, so the fix belongs in `main()`'s call site,
  not in `_compare()`/`_within_band()`.
- **Open design question** (not yet resolved — see Risks below): `evaluate_simq.py`'s own
  docstring and `quality_scoring_contract.md` §11.6 both describe it as using "the same ±1 band
  tolerance as the regression tests" — if this ticket adds a *second* tolerance dimension (score)
  to the pytest suite only, the standing harness and the pytest suite diverge in what they check,
  which is a bar `§11.6`'s own framing (parity between the two) may not anticipate.

### Other candidate consumers checked and ruled out (schema-agnostic, no change needed)
- `tools/simq_audit_gaps.py::load_anchor_keys()` (line 51) — `[k for k in data if k not in
  _META_KEYS]` — only reads top-level keys (run_key strings), never touches a pillar's value.
  Confirmed no per-pillar read anywhere in the file.
- `tests/unit/worldassembly/test_corpus_diversity.py::_anchored_world_ids()` (line 180) — same
  pattern, strips `_seed{N}_{ticks}t` off top-level keys only.
- `.claude/workflows/simq-audit.js` — an LLM-orchestration workflow (not a JSON parser); its prompt
  text tells the `anchor-updater` agent to "edit `tests/simulation_quality/fixtures/grade_anchors.json`
  (new grade for an anchor key)" (line ~219) with no mention of a score field. This is a **prose
  drift risk**, not a code break — flagged under Anti-Drift Hazards below, since a future
  SimQ-audit run following that workflow's literal instructions could update `grade` and silently
  leave `score` stale.
- No other repo file reads a pillar's grade value out of `grade_anchors.json` (verified via
  `grep -rln "grade_anchors"` across `.py`/`.md`/`.yaml`/`.js`, cross-checked against every hit).

## Mechanics / Engine Constraints

- **`docs/simulation_quality/quality_scoring_contract.md` §4.4 Normalized Score** — defines the
  exact formula (`normalized_score = raw_score / effective_denom`) that produces the value this
  ticket persists. Not modified by this ticket; only read and stored, not recomputed.
- **§4.5 Health Grades** — S is unbounded (`>2.0`, no ceiling) — this is the structural reason the
  ticket exists: any two S-graded runs are indistinguishable by grade alone regardless of how far
  apart their `normalized_score` actually is.
- **§11.3 Regression Tests** and **§11.6 Standing Evaluation Harness** — both explicitly describe
  the ±1-letter band as *the* regression mechanism today; this ticket adds a second, independent
  mechanism (score tolerance) alongside it, not a replacement.
- **§14 Non-Goals** — "Historical run comparison (cross-run scoring requires baseline storage
  infrastructure)" is explicitly out of scope. This ticket's one-number-per-anchor-entry addition is
  narrower: it compares *live vs. its own single committed anchor*, the same shape as the existing
  letter-grade check, not a new time-series/dashboard capability. Confirmed consistent with the
  ticket's own framing and the roadmap's Phase 1b note — no drift into the Non-Goal found.

## Parity Ledger Overlap

- **`INFRA-250`** (`docs/parity_ledger/infrastructure.yaml`, status `verified`, priority `P1`) —
  "Full SimQ test suite... Grade regression anchors: ... Parametric band-tolerance tests (±1
  letter) against `data/calibration/` reports." `test_path` includes
  `tests/simulation_quality/test_grade_regression.py::test_grade_within_anchor_band` and
  `::test_grade_anchor_file_exists_and_valid` — **both directly modified by this ticket's schema
  migration and new tolerance assertion**. Text/`v2_evidence` must be updated to describe the new
  two-field schema and the second (score) tolerance dimension. Not P0, but directly touched — should
  be updated in the same session per the Authoritative Mechanics Rule.
- **`INFRA-252`** (`verified`, `P1`) — "`tools/evaluate_simq.py` standing harness: `--dry-run` diffs
  existing `data/calibration/` reports against `grade_anchors.json` (25 entries)..." — entry count
  is already stale (25 vs. today's 75, a pre-existing staleness not caused by this ticket, same
  class of drift `INFRA-250` already flags for itself). `test_path`:
  `tests/simulation_quality/test_evaluate_harness.py::TestResolveWorldName` — does not currently
  cover `_compare()`'s anchor-shape assumption, which is the one real break in this file. Text
  should be updated to note the schema-compatibility fix in `main()`'s call site.
- No P0 entries found overlapping this ticket's scope — both hits are P1. Neither requires a
  passing `test_path` as a hard gate (that's a P0-only rule), but both should still be updated
  since their described behavior changes.
- Searched `docs/parity_ledger/*.yaml` for `grade_anchors.json`/`normalized_score`/`SIMQ` broadly;
  no other entry describes the anchor file's per-pillar value shape specifically.

## Prior Work

- **`TCK-20260630-SIMQ-ANCHORS`** — original anchor-file creation; established the bare-string
  schema this ticket now extends.
- **`TCK-20260713-SIMQ-SCORE-CEILING-FIX`** (done today, same session) — the ticket this one is
  explicitly sequenced after. Its `plan.md` Scope Guards confirm the schema handoff (quoted above)
  and its `investigation.md`/`plan.md` establish the current, authoritative 75-entry anchor state
  this ticket must build on (not the 72-entry figure the ticket text itself cites — already
  corrected in `current_state.md`).
- **`TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE`** — establishes the project's
  precedent for handling documented run-to-run engine nondeterminism with a **tolerance-based**
  assertion rather than a tight one, for a different subsystem (population counts, not SimQ
  scores). Useful precedent shape (tolerance band sized from real multi-trial data), not directly
  reusable code.
- **Empirical variance evidence found this session** (fresher and more precise than
  `D20_simq_integration.md`'s qualitative claim — see Risks below): `data/calibration/` contains 18
  run_keys with genuine same-config repeat trials (`{run_key}_trial2` and `{run_key}_trial3`,
  generated 23–74 seconds apart on 2026-07-11, before today's `SCORE-CEILING-FIX` weight change —
  confirmed via `generated_at` timestamps and identical `raw_score` values between the two trials
  where they match). Comparing `normalized_score` across all 180 pillar-observations in these
  trial2/trial3 pairs:
  - **135/180 (75%) are bit-identical** — most pillars are fully deterministic run-to-run.
  - **45/180 differ**, concentrated in COMBAT, NARRATIVE, ECONOMY, PROGRESSION, WORLD, SOCIAL — the
    pillars whose scoring depends on tick-by-tick event timing, which the kernel's wall-clock
    tick-budget throttle can shift run-to-run past ~tick 300-400 (consistent with
    `D20_simq_integration.md`'s qualitative finding, now with a concrete number attached).
  - Relative differences range from ~0.2% up to a max observed **43.5%**
    (`dungeon_crawl_seed456_2000t` ECONOMY: `0.0533` vs. `0.0342`), with a second-highest cluster
    around 24% (`urban_political_seed123_1000t` ECONOMY, 0.1287 vs. 0.1641) and 16% (`SOCIAL`,
    urban_political variants). All of these outliers occur on pillars/scenarios with **small
    absolute `normalized_score` magnitude** (well below the A threshold of 0.5) — the same absolute
    noise produces an inflated *relative* % purely because the denominator is small.
  - By contrast, every S-band (`normalized_score > 2.0`) pillar observed in these same trial pairs
    (e.g. `hero_guild_routing_seed42_1000t` NARRATIVE: 3.19 vs. 3.195) shows negligible relative
    noise (<0.2%), because the same absolute timing jitter is a much smaller fraction of a larger
    number.
  - This dataset is a stronger empirical basis than `D20_simq_integration.md`'s citation (which
    documents the *existence* of wall-clock-driven variance for entity population counts, not a
    number for `normalized_score` itself) — use it as the primary cited evidence, with D20 as
    corroborating qualitative context for *why* the variance exists (the tick-budget throttle).

## Risks and Open Questions

1. **A flat relative-percentage tolerance does not fit both ends of the observed variance
   distribution — this blocks a specific numeric decision, do not guess it.** The AC's own
   demonstration case ("an S-graded pillar's score cut in half but still >2.0") requires the
   tolerance to be tighter than 50%. But real observed noise on low-magnitude pillars reaches up to
   43.5%. A single flat percentage in between (e.g. the roadmap doc's own suggested "±15%" in
   `current_state.md" line 243) would **false-positive** on the legitimate 16–43.5% noise this
   session's own trial-pair data shows on ECONOMY/SOCIAL/WORLD-class low-magnitude pillars, while a
   wider flat percentage (e.g. ±50%) would fail to reliably catch the AC's synthetic 50%-cut
   demonstration. This is a real design tension, not a made-up one — flagging for the planner
   rather than picking a number: candidate resolutions (not decided here) are (a) a percentage
   tolerance combined with an absolute-delta floor/ceiling so near-zero-magnitude pillars aren't
   penalized by relative-% blowup, (b) an absolute delta instead of a percentage, sized from the
   observed max absolute delta (~0.019, from the ECONOMY outlier) rather than relative, or (c) a
   tighter percentage that accepts the low-magnitude pillars will occasionally need a legitimate
   anchor refresh (same operational pattern as the existing letter-band check already requires).
2. **COGNITION-specific nondeterminism is a live, unresolved, unrelated bug that intersects this
   ticket's design space.** `TCK-20260713-SIMQ-SCORE-CEILING-FIX`'s Step 12 discovered (documented
   in its `plan.md` Deviations section, and filed as the still-open
   `tickets/todos/TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM.md`, P1) that COGNITION's
   self-model loop-detection path can produce a **runaway result under sustained system load**:
   `urban_political_seed123_500t` COGNITION measured `grade=B, raw_score=11.0` in three clean,
   bit-identical reproductions, but `grade=S, raw_score=3521.0` (a >300x jump) in one live sweep run
   under ~30 minutes of concurrent load with `WatchdogTrip` warnings. This is already caught by the
   *existing* ±1-letter check (B→S is 2 letters). A new score-tolerance check built from this
   session's trial-pair evidence should **not** be sized to also tolerate that kind of runaway —
   doing so would defeat the check's purpose. This is a separate, already-tracked bug; the new
   tolerance test may need to explicitly exclude COGNITION-under-load from its "known good variance"
   assumptions, or accept that COGNITION could occasionally trip both checks until the loopdet
   ticket is fixed (consistent with how the letter-band check already can).
3. **Whether `evaluate_simq.py` should gain the score-tolerance check too, or only the schema-
   compatibility fix.** The ticket's scope text lists `evaluate_simq.py` only as needing an update
   "reads grade_anchors.json entries as bare strings" (i.e., don't crash) — but §11.6 of the
   contract describes the standing harness as using "the same ±1 band tolerance as the regression
   tests," implying the two should stay in parity. Left as an open question for the planner: adding
   only the minimal schema-compat fix satisfies the ticket's literal AC, but leaves the harness and
   the pytest suite checking different things, a documentation/consistency gap that may be worth
   closing in the same ticket (small additional surface) or flagging as an explicit, intentional
   scope boundary.
4. **`.claude/workflows/simq-audit.js`'s anchor-update instructions are now stale prose**, telling
   the `anchor-updater` agent to edit "new grade for an anchor key" with no mention of the score
   field. Not a code break (JS orchestration text, not a JSON schema consumer), but a real drift
   risk for the *next* SimQ audit run after this ticket lands — flagged under Anti-Drift Hazards.
5. **`grade_anchors.json`'s `_instructions` metadata key** (currently: "If a pillar grade moves by
   more than one letter from the anchor, the regression test fails...") describes only the letter-
   band mechanism and will be incomplete/misleading once the score-tolerance check exists — should
   be updated alongside the schema migration, though this is house-keeping rather than a hard
   requirement.

## Anti-Drift Hazards

- **Do not use `raw_score` instead of `normalized_score`.** They are different fields at very
  different magnitudes (e.g. `dungeon_crawl_seed42_5200t` COMBAT: `raw_score=215.0` vs.
  `normalized_score=0.0426`) — persisting the wrong one would silently make the tolerance check
  meaningless (it would appear to "work" numerically but never correspond to what the grade
  boundaries in §4.5 are defined against).
- **Do not treat the sibling ticket's re-anchor pass as re-runnable for this ticket's own
  purposes.** `SCORE-CEILING-FIX` already regenerated all 75 entries' calibration reports today
  (2026-07-13); re-running a fresh full-corpus sweep for this migration (rather than reading the
  already-regenerated `data/calibration/{run_key}/quality_report.json` files that are still on
  disk) risks picking up further organic drift and turning a schema-migration ticket into an
  unplanned second re-anchor pass — the ticket's own Scope explicitly says to reuse the sibling's
  pass, not repeat it.
- **Do not silently widen the existing ±1-letter tolerance while adding the score check** — the two
  checks are independent and additive (§ ticket Scope); `_within_band`'s `tolerance=1` default must
  stay as-is.
- **`unit_information_density`'s 3 new entries** (added today by the sibling ticket) must be
  included in this migration's schema conversion — do not scope the migration to "the pre-existing
  72" and leave the 3 newest entries as bare strings by accident.
- **`test_evaluate_harness.py`'s `TestCompare`/`TestWithinBand` classes pass bare grade strings
  directly to `_compare`/`_within_band`** and should *not* need to change — if an implementer finds
  themselves editing those two functions' signatures to accept the new object shape, that is a sign
  the fix is being applied in the wrong place (the fix belongs in `main()`'s call site, which is the
  one place that actually reads `grade_anchors.json`'s raw JSON).
- **Metadata keys** (`_note`, `_instructions`, `_grade_order`) are not scenario entries — any script
  or test that iterates `grade_anchors.json`'s top-level keys must keep excluding keys starting with
  `_` (already handled correctly everywhere checked; do not regress this filter while touching the
  file).
