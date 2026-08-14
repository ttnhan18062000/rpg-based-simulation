---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE
artifact_type: investigation
tags: [simulation-quality, calibration, determinism, corpus]
---

# Investigation — TCK-20260716-SIMQ-URBAN-POLITICAL-NARRATIVE-TOLERANCE

## Current Behavior

### `tests/simulation_quality/test_grade_regression.py` — score-tolerance mechanism

- `SCORE_TOLERANCE_ABS_FLOOR = 0.05`, `SCORE_TOLERANCE_REL_PCT = 0.20` (lines 46-47) — global
  defaults for the score-tolerance check.
- `SCORE_TOLERANCE_OVERRIDES: dict[tuple[str, str], float]` (lines 49-68) — currently exactly
  2 entries:
  - `("urban_political_seed123_1000t", "ECONOMY"): 0.2878`
  - `("frontier_marches_seed42_200t", "NARRATIVE"): 0.3351`
- `_score_tolerance_kwargs(run_key, pillar)` (lines 71-75) — returns `{"abs_floor": ...}` if a
  `(run_key, pillar)` pair is in the table, else `{}` (falls through to the module defaults).
- `_within_score_tolerance(actual_score, anchor_score, abs_floor=..., rel_pct=...)`
  (lines 201-214) — `True` iff `abs(actual - anchor) <= max(abs_floor, rel_pct * abs(anchor))`.
- `test_grade_within_anchor_band` (line 259, fast/200-500t) and
  `test_grade_within_anchor_band_long_run` (line 313, `@pytest.mark.slow`, 1000t+) both call
  `_within_score_tolerance(actual_score, anchor_score, **_score_tolerance_kwargs(run_key, pillar))`
  (lines 289-291, 345-347) — this is the exact call site the 3rd override entry must be wired
  into (no code change needed beyond the table itself; the lookup helper and both call sites
  already handle an arbitrary number of entries).
- `test_score_tolerance_override_table_scoped_to_named_pillars` (line 605) — asserts
  `set(SCORE_TOLERANCE_OVERRIDES.keys()) == {("urban_political_seed123_1000t", "ECONOMY"),
  ("frontier_marches_seed42_200t", "NARRATIVE")}` **exactly** (line 610-613) — this hard-coded
  set assertion **must be updated** to a 3-tuple set when a 3rd entry is added, or this test
  will fail immediately (not a soft check).
- `test_score_tolerance_overrides_do_not_affect_unlisted_anchors` (line 626) — iterates every
  `(run_key, pillar)` in `grade_anchors.json` not in the table and asserts
  `_score_tolerance_kwargs(run_key, pillar) == {}` — self-adjusting (no update needed when a
  new entry is added; it dynamically skips whatever is currently in the table via `if (run_key,
  pillar) in SCORE_TOLERANCE_OVERRIDES: continue`).
- `SLOW_ANCHOR_KEYS` includes `"urban_political_seed123_1000t"` (confirmed via grep, line
  ~164) — `test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]` is a real,
  currently-collected parametrized case, not hypothetical.
- `data/calibration/` is gitignored and empty on a fresh checkout (confirmed:
  `git ls-files data/calibration | wc -l` = 0) — both anchor-band tests `pytest.skip()` for any
  `run_key` without a locally-regenerated report; they are only actually *exercised* (not just
  structurally present) when a developer runs `tools/calibrate_simq.py` locally first. This is
  a pre-existing, unrelated-to-this-ticket property of the file (documented in the parent
  ticket's Anti-Drift Notes) — not something this ticket changes.

### `tests/unit/worldassembly/test_corpus_diversity.py` — existing guard coverage for this anchor

- `test_urban_political_seed123_1000t_social_economy_grade_stability` (line 933) is the **only**
  `grade_stability`-style guard for `urban_political_seed123_1000t` — it covers exactly
  `{"SOCIAL": abs_floor=2.9568, "ECONOMY": abs_floor=0.2878}` (lines 995-998). **NARRATIVE is
  confirmed NOT covered by any existing guard for this anchor** — grepping the file for
  `urban_political_seed123_1000t` finds only this one guard function; grepping for `NARRATIVE`
  guards elsewhere (`test_frontier_extended_seed42_200t_narrative_grade_stability`,
  `test_frontier_marches_seed42_200t_narrative_grade_stability`, two combined
  COMBAT+NARRATIVE/PROGRESSION+NARRATIVE guards on other anchors) confirms every existing
  NARRATIVE guard is scoped to a *different* anchor. This directly confirms the ticket's
  premise: NARRATIVE was not one of this anchor's originally-scoped pillars in
  `TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP`.
- The guard's own docstring (lines 933-977) documents the exact derivation formula reused
  below: for a pillar whose anchor is **not** re-centered (ECONOMY, kept at its original
  committed value 0.6564), `abs_floor = round(1.3 * max_observed_deviation_from_anchor, 4)`,
  floored at `SCORE_TOLERANCE_ABS_FLOOR = 0.05`. For a pillar whose anchor **is** re-centered
  on the midpoint of the observed range (`frontier_marches_seed42_200t`/NARRATIVE, SOCIAL on
  this same anchor), `abs_floor = round(1.3 * half_range, 4)` where `half_range = (max -
  min)/2` and the anchor `score` field is simultaneously updated to the range's midpoint.
  Verified by direct arithmetic against both existing table entries:
  - ECONOMY: anchor unchanged at 0.6564; repro min sample 0.435; `1.3 * |0.6564-0.435| =
    1.3*0.2214 = 0.28782` → rounds to `0.2878` (matches exactly).
  - `frontier_marches_seed42_200t`/NARRATIVE: anchor re-centered to `0.6186` (midpoint of the
    7-sample range `[0.3608, 0.8763]`); `1.3 * (0.8763-0.3608)/2 = 1.3*0.25775 = 0.335075` →
    rounds to `0.3351` (matches exactly, confirmed against
    `tests/unit/worldassembly/test_corpus_diversity.py:1696`).

### `src/simulation_quality/scorers/narrative.py` — `NarrativeScorer`

- `PILLAR_ID = PillarId.NARRATIVE` (line 20); `EVENT_TYPES` (lines 22-33) includes
  `hero_death_unrecorded` — the exact event type that appears in every fresh draw's
  `worst_events` (see Prior Work below) as the single negative NARRATIVE contribution.
- `score()` (line 41) awards positive deltas for `quest_started`/`quest_completed`/
  `chronicle_entry_created`/`world_emergence_event`/`narrative_milestone`/
  `scenario_objective_progressed`/`scenario_objective_completed`, and negative deltas for
  `quest_failed`, `quest_system_dormant` (a one-shot gate-fired event, line 65-78),
  `history_silent` (one-shot, line 87-101), `scenario_stalled` (one-shot, line 115-123), and
  `hero_death_unrecorded` (line 125-130, unconditional, fires every time a `hero`-kind entity
  deactivates without a corresponding chronicle/narrative event that tick).
- The scorer itself is a pure per-event accumulator with no internal randomness or wall-clock
  dependency — it deterministically maps whatever events arrive in the replayed
  `simulation_events.jsonl` stream to score deltas. **The variance origin is entirely upstream**
  in which events get emitted in the first place (see next section), not in how the scorer
  processes them.

### `src/observability/event_extractor.py` — the delta-gated event-construction mechanism

- **File-path correction**: the ticket's Related Code Areas names `src/engine/
  event_extractor.py`, which does not exist (`ls` confirms `No such file or directory`). The
  actual file is `src/observability/event_extractor.py` (confirmed via `graphify query` and
  direct file read) — a path-naming slip in the ticket, not a missing file. Flagged as a minor
  gap; does not affect the investigation's substance since the correct file was read.
- `hero_death_unrecorded` (lines 165-176) is constructed inside the same per-entity,
  per-tick diff loop as `CombatKillEvent` — it compares `prior_ent.lifecycle.active` (previous
  tick's snapshot) against `entity.lifecycle.active` (this tick's snapshot): `if
  prior_ent.lifecycle.active and not entity.lifecycle.active: ... if getattr(entity, "kind",
  None) == "hero": events.append(SimulationEvent(event_type="hero_death_unrecorded", ...))`.
  This is a **this-tick-vs-prior-tick state comparison**, not a re-evaluated-every-tick signal
  (unlike COGNITION's `decision_divergence_detected`, which INFRA-273 documents as having "no
  dedup gate, re-evaluated every tick"). It fires exactly once per genuine hero-death state
  transition.
- This confirms the exact mechanism INFRA-273 names for NARRATIVE's inclusion in the
  "cascading divergence" pillar list: when `kernel.py`'s tick-budget watchdog drops a
  resolution-queue item on some tick T (real wall-clock timing, not seed-dependent — see
  `docs/audits/D06_longrun_health.md` §F6), an entity that would otherwise have taken different
  action that tick has its state diverge from the counterfactual "what would have happened"
  path. Because this-tick-vs-prior-tick comparisons are stateful across the whole 1000-tick
  run, a single dropped resolution item early in the run can cascade into materially different
  total event counts by tick 1000 — not just one event's tick timestamp shifting by a few
  ticks. `hero_death_unrecorded`'s "unconditional" framing in `narrative.py`'s own comment
  (line 76: "fires even if quest config is empty") underscores it is not gated on scenario
  configuration — its trigger condition is purely this-tick-vs-prior-tick entity state.

## Mechanics / Engine Constraints

- `docs/audits/D06_longrun_health.md` §F6 (lines 211-267, "Wall-Clock-Dependent Non-Determinism
  at Long Tick Counts") — documented, intentional engine behavior, not a bug. Root cause:
  `kernel.py`'s tick-budget watchdog (`kernel.py:420-442`) and mid-tick emergency throttle
  (`kernel.py:574-601`) measure real wall-clock compute time per tick and drop
  resolution-queue work items when a tick exceeds budget — *which* entities get dropped
  depends on real timing (system load, scheduler jitter, GC pauses), not the deterministic
  seed/RNG stream. The "reliably reproducible below ~tick 300-320" hedge is explicitly *not*
  contradicted by this finding (all draws in this investigation are 1000t runs, well past that
  threshold) — consistent with, not new evidence against, the existing hedge.
- `docs/engine/kernel.md` §"Emergency Throttling" and §"State Hashing in Phase 7" — the
  canonical hash is `"SKIPPED"` in `DEGRADED` mode; this throttle behavior is already known to
  be non-determinism-guaranteed at the engine-contract level, not something this ticket's
  finding newly reveals.
- `docs/engine/performance_contract.md` §7 — hardware-class scaling limits this watchdog
  enforces; read-only reference per this ticket's Out of Scope (no code change to
  `src/engine/kernel.py` is in scope or was made).
- `docs/parity_ledger/infrastructure.yaml::INFRA-273` — the specific mechanism confirmation
  this investigation's fresh evidence is consistent with (see below).

## Parity Ledger Overlap

- **`INFRA-272`** (status: `verified`, priority: `P1`) — contains the exact "HONEST
  DISCLOSURE, NOT RESOLVED" block this ticket exists to close
  (`docs/parity_ledger/infrastructure.yaml:4276-4287`): anchor 0.6603, draws
  0.5210/0.4340/0.4144, deltas 0.139-0.246, tracked as this ticket. **This entry needs a
  RESOLVED pointer appended** once the fix lands, following the exact append-only convention
  already used for the ECONOMY/frontier_marches resolution in the same entry
  (lines 4269-4275).
- **`INFRA-273`** (status: `verified`, priority: `P2`) — the "cascading divergence" mechanism
  confirmation for delta-gated SOCIAL/COMBAT/PROGRESSION/NARRATIVE/WORLD pillars
  (`docs/parity_ledger/infrastructure.yaml:4296-4319`). This investigation's fresh evidence
  (6 total NARRATIVE draws, deviations 0.031-0.246, `hero_death_unrecorded`'s confirmed
  this-tick-vs-prior-tick construction in `event_extractor.py`) is **consistent with, not
  contradicting**, this entry's existing text — no update strictly required, but the ticket's
  Related Docs names it for cross-reference; a one-line pointer in `eval_matrix_results.md`
  Part 4 (see below) is sufficient, no `v2_evidence`/`test_path` edit needed since the
  underlying mechanism claim (not a specific test count) is what INFRA-273 documents.
- No `P0` entries are touched by this ticket's scope — `INFRA-272` is `P1`, `INFRA-273` is
  `P2`. Neither requires a newly-passing `test_path` as a hard gate the way a `P0` entry
  would, though `INFRA-272`'s own cited `test_path` (which includes
  `test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]`, implicitly via the
  file-level slow marker) does benefit from this ticket's fix making that parametrized case
  pass rather than fail against fresh real data.

## Prior Work

- `stored_artifacts/TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE/` — direct parent;
  established the `SCORE_TOLERANCE_OVERRIDES` mechanism itself (Step 1-3 of its plan.md) and
  is the exact source of the 3 original NARRATIVE draws (Deviation #1). Its `plan.md`'s
  Anti-Drift Notes explicitly warn: "If a future session's evidence shows this reasoning was
  wrong for either pillar (e.g. a fresh single draw outside the current floor), that is new
  evidence for a future ticket, not a reason to silently pad these values now" — directly
  relevant to a new finding surfaced below (SOCIAL).
- `stored_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/repro_sweep.md` Section 8
  — the exact derivation-methodology precedent (1.3x max-observed-deviation, optionally with
  anchor re-centering) this investigation's own abs_floor recommendation below reuses
  verbatim, not invented fresh.
- `stored_artifacts/TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM/repro_sweep.md` — the
  original repro-methodology precedent (multiple independent same-seed trials, documented
  variance) both parent tickets and this investigation build on.
- `tickets/done/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP.md` — confirms
  `urban_political_seed123_1000t`'s originally-scoped pillars were `ECONOMY, SOCIAL` only
  (line 98, 139 of the ticket) — NARRATIVE was never in scope for that ticket's 14-anchor
  sweep, consistent with this investigation's own grep confirmation above.

## Fresh Evidence Gathered This Session

3 additional independent fresh `urban_political_seed123_1000t` calibration draws were run
(`python3 tools/calibrate_simq.py --name urban_political --seed 123 --ticks 1000`, each to a
distinct `--output` path to avoid clobbering while comparing independent draws; each run took
~35-50s wall-clock, not the 1000t hero-guild-scale drives that take minutes — this scenario's
`urban_political` engine run is comparatively fast). Combined with the 3 draws already on
record from the parent ticket (anchor `NARRATIVE` score = `0.6603206412825652`, per
`grade_anchors.json`):

| Draw | Source | NARRATIVE score | Grade | Delta from anchor |
|---|---|---|---|---|
| 1 | parent ticket | 0.5210 | B | 0.1393 |
| 2 | parent ticket | 0.4340 | B | 0.2263 |
| 3 | parent ticket | 0.4144 | B | **0.2459 (max)** |
| 4 | this investigation | 0.6290 | A | 0.0313 |
| 5 | this investigation | 0.5490 | A | 0.1113 |
| 6 | this investigation | 0.5762 (0.5761523046092184) | A | 0.0841 |

Observations:
- **All 6 draws stay within the ±1 `GRADE_ORDER` band** of the anchor's `B` grade (`A` and `B`
  are both within 1 of `B`) — the band check (`_within_band`, separate from the score-tolerance
  check) has never failed for this pillar/anchor, in this or the parent ticket's evidence. This
  ticket's fix is scoped entirely to the score-tolerance check, consistent with its Scope.
- The 3 newest draws all landed grade `A` (not `B` like the parent's 3), meaning the observed
  grade itself flips between `B` and `A` depending on draw — a wider real-world swing than the
  parent ticket's disclosure alone showed, though still safely inside the existing ±1 band
  tolerance (not a new problem, but strengthens the case that this is genuine, still-live
  variance rather than a fluke of the parent session).
- Every draw's single negative-scoring event was `hero_death_unrecorded` (1 occurrence in
  every draw's `worst_events`), consistent with the `event_extractor.py` mechanism identified
  above — the variance is driven by event *counts* for the positive-scoring event types
  (`quest_started`/`chronicle_entry_created`/etc., ranging 111-127 total NARRATIVE events
  across the 3 new draws), not a change in which negative events fire.
- **Conclusion (a) — F6-class, confirmed, not a distinct root cause.** The evidence is fully
  consistent with `INFRA-273`'s already-confirmed "cascading divergence" mechanism: NARRATIVE
  is explicitly named among the delta-gated pillars in that entry, `hero_death_unrecorded`'s
  construction in `event_extractor.py` is architecturally identical to the other named
  events' this-tick-vs-prior-tick pattern, and the observed variance shape (band-stable,
  score-volatile, single fixed-tolerance-exceeding draws mixed with in-tolerance draws) matches
  the parent tickets' characterization of every other F6-confirmed pillar on this same anchor
  and others. No evidence was found suggesting a distinct bug (no exception, no malformed
  event, no scorer defect — `NarrativeScorer.score()` is a deterministic pure accumulator).

### Derived `abs_floor` for a 3rd `SCORE_TOLERANCE_OVERRIDES` entry

Because no existing `grade_stability` guard exists for this `(anchor, pillar)` pair, there is
no guard `abs_floor` to reuse verbatim (unlike the 2 existing table entries). Applying the same
formula the existing 2 entries were verified to follow (anchor **not** re-centered, since
`grade_anchors.json`'s committed `NARRATIVE` value for this anchor is not being touched by this
ticket — matching the ECONOMY precedent, not the frontier_marches-NARRATIVE precedent):

```
max_deviation = max(0.1393, 0.2263, 0.2459, 0.0313, 0.1113, 0.0841) = 0.2459  (draw 3)
abs_floor = round(1.3 * 0.2459, 4) = 0.3197
default_width = max(0.05, 0.20 * 0.6603206412825652) = 0.1321 (rounded)
0.3197 > 0.1321  →  widens tolerance (satisfies the anti-drift guard's own invariant)
```

Verified directly: `abs(draw - 0.6603206412825652) <= 0.3197` holds for **all 6 draws**,
including the boundary draw (parent draw 3, delta exactly 0.2459, well inside 0.3197 with
margin). **Recommended value: `("urban_political_seed123_1000t", "NARRATIVE"): 0.3197`.**

### New out-of-scope finding surfaced during this session's own fresh draws (SOCIAL)

Copying fresh draw 6's `quality_report.json` into `data/calibration/urban_political_seed123_1000t/`
and running `pytest "tests/simulation_quality/test_grade_regression.py::
test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]" -m slow
--resource-budget large -v` against it produced a **different** failure than expected:

```
AssertionError: urban_political_seed123_1000t — 1 pillar(s) drifted beyond score tolerance:
  SOCIAL: actual_score=21.814 is outside tolerance of anchor_score=17.9655
```

NARRATIVE itself **passed** on this specific draw (delta 0.0841, well inside the recommended
0.3197 floor and even inside the *default* 0.1321 width) — but SOCIAL failed the *default*
tolerance (`|21.814 - 17.9655| = 3.8485 > max(0.05, 0.20*17.9655) = 3.5931`, exceeding by
0.2554). Checking SOCIAL across all 3 of this session's fresh draws: draw 4 delta 1.8805
(pass), draw 5 delta 1.0275 (pass), draw 6 delta 3.8485 (**fail**) — 1 of 3 fresh draws
exceeds even the current *unmodified* default tolerance for SOCIAL on this same anchor.

This directly contradicts the parent ticket's Out-of-Scope assumption ("its existing
20%-relative default (3.5931) already exceeds the guard's own evidence-derived floor (2.9568)
— the single-draw check is not actually under-tolerant for that pillar," per
`test_grade_regression.py`'s own module comment, lines 60-64) with **new evidence specifically
implicating it**, per this ticket's own Out-of-Scope carve-out language ("do not re-derive or
second-guess that finding *without new evidence specifically implicating it*"). See Risks and
Open Questions below — **this is disclosed, not fixed, in this investigation**; flagged as a
decision point for the planner, not resolved unilaterally here.

## Risks and Open Questions

1. **[DECISION NEEDED] SOCIAL now has contradicting evidence.** One of this session's 3 fresh
   draws shows SOCIAL exceeding the *existing, untouched* default tolerance (delta 3.8485 vs.
   width 3.5931) — new evidence the parent ticket's Out-of-Scope explicitly anticipated might
   surface ("if a future session's evidence shows this reasoning was wrong... that is new
   evidence for a future ticket, not a reason to silently pad these values now"). This
   ticket's own Acceptance Criteria (`git diff --stat` bullet) permits touching
   `urban_political_seed123_1000t`/SOCIAL "if explicitly justified by new evidence and called
   out in Implementation Notes" — but this ticket's Scope is titled and scoped around
   NARRATIVE specifically, and its Related Tickets/Out-of-Scope framing (one disclosed, named
   finding per ticket, mirroring how this ticket itself was spawned from the parent's single
   NARRATIVE disclosure) suggests the cleaner path is: **do not silently fold a SOCIAL fix
   into this ticket; disclose it in `INFRA-272`/`Implementation Notes` and file a named
   follow-up ticket, matching this ticket's own genesis pattern.** This is a judgment call for
   planning, not decided here — flagged explicitly so it is not silently absorbed or silently
   dropped.
2. **Whether a dedicated `grade_stability` guard should also be added.** The ticket's Scope
   authorizes either path. Given (a) 6 independent real draws already provide a solid
   evidence base without needing a 3-trial-mean guard to derive the floor, (b) the existing
   precedent shows even a dedicated guard is *not* immune to the same F6 mechanism when run at
   the tail of a long sequential `-m slow` session (`frontier_marches_seed42_200t`'s own guard
   intermittently failed in exactly this way per `repro_sweep.md` Section 8 — a guard is not a
   strictly stronger protection, just a differently-shaped one), and (c) the ticket's Out of
   Scope defaults to *not* adding one "unless this ticket's own investigation evidence
   specifically requires it" — **this investigation's recommendation is: tolerance-override
   alone is sufficient; do not add a new `grade_stability` guard.** No evidence surfaced that
   the override alone is inadequate — all 6 draws pass under the recommended 0.3197 floor.
3. **Sample size remains modest (6 draws, 3 from a different session/machine-state).** Per the
   project's own established honesty convention (`isolation_comparison.md`'s explicit
   "Honesty on sample size" section), 6 draws is a reasonable, evidence-based basis for a
   `1.3x`-safety-margin floor (consistent with how the 2 existing entries were derived from
   comparably-sized samples) but should not be oversold as exhaustive — a future draw
   exceeding 0.3197 would not be shocking given the underlying mechanism is genuinely
   wall-clock/timing-dependent, not a fixed distribution.
4. **`src/engine/event_extractor.py` (as named in the ticket's Related Code Areas) does not
   exist** — the real path is `src/observability/event_extractor.py`. Flagged as a minor
   ticket-text gap, already worked around by reading the correct file; no action needed beyond
   this note.

## Anti-Drift Hazards

- **Do not touch `grade_anchors.json`'s NARRATIVE anchor value for this run_key.** Unlike
  `frontier_marches_seed42_200t`/NARRATIVE (which was re-centered), this recommendation keeps
  the anchor at its original committed `0.6603206412825652` — matching the ECONOMY precedent
  on this same anchor, not the frontier_marches precedent. Re-centering was not evidence-driven
  here (the original anchor is not itself an outlier relative to the 6-draw spread) and touching
  `grade_anchors.json` would trip `test_grade_anchors_entry_count_unchanged` review scrutiny
  unnecessarily.
- **`test_score_tolerance_override_table_scoped_to_named_pillars`'s hard-coded `set(...) ==
  {...}` assertion (line 610) will fail the moment a 3rd entry is added to the table** unless
  that assertion is updated in the same change — this is intentional (anti-drift by design),
  not a bug to work around; the implementer must update both in the same commit.
- **Do not silently widen `SCORE_TOLERANCE_ABS_FLOOR`/`SCORE_TOLERANCE_REL_PCT`** (the module
  defaults) — same hard constraint as the parent ticket; any fix stays scoped to the
  per-`(run_key, pillar)` override table.
- **Do not fold the SOCIAL finding into this ticket's diff without an explicit, separately
  documented justification** — see Risks item 1. The default posture (absent a planning
  decision to the contrary) should be: disclose only, file separately, exactly mirroring how
  this ticket itself was spawned rather than silently expanding
  `TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE`'s own scope when the same class of
  finding first appeared there.
- **`data/calibration/` and `data/runs/` are gitignored scratch space** — the 3 fresh draws
  gathered in this investigation were written to non-colliding `--output` paths, inspected,
  and then deleted (`rm -rf`) before finalizing this investigation to avoid leaving stale
  local-only calibration data that could confuse a future session's own fresh-draw gathering.
  The implementer will need to regenerate real calibration data locally
  (`python3 tools/calibrate_simq.py --name urban_political --seed 123 --ticks 1000`, writing
  to the *default* `data/calibration/urban_political_seed123_1000t/` path this time, not a
  custom `--output`) before `test_grade_within_anchor_band_long_run[urban_political_seed123_1000t]`
  can actually run (not skip) to prove the fix.
- **`hero_death_unrecorded`'s "unconditional" framing** (`narrative.py` line 76's comment,
  which actually documents `quest_system_dormant`, a different event — do not conflate the two
  when reading the scorer; `hero_death_unrecorded`'s own unconditional nature is stated at line
  125-130 with no gate/one-shot-fired guard, unlike the other three special-cased events in this
  scorer) means every hero death without a same-tick chronicle/narrative event is scored, every
  time — this is not itself the source of variance; the variance is in whether/when a hero dies
  and whether other positive-scoring events (`quest_started` etc.) fire, both of which are
  downstream of the F6 throttle's cascading effects on entity behavior, not the scorer's own
  logic.
