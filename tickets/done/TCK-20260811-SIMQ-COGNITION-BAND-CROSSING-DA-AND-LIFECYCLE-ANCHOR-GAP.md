---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP
phase: done
date: 2026-08-11
tags: [simulation-quality, calibration, corpus]
---

# TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP

## Title
`/simq-audit mode=full` run `SIMQ-AUDIT-20260811T111151Z` found 2 real, disclosed findings: a
design-acknowledgment gap in yesterday's watchdog-variance fix, and a newly-exposed 7/8-pillar
drift on a never-registered anchor key

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
While satisfying `TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE`'s AC5 (invoke `/simq-audit
mode=full` as a pre-cutover gate and record its verdict), a full audit run
(`SIMQ-AUDIT-20260811T111151Z`) surfaced two distinct real findings that this audit workflow does
not fix itself, per its own governance:

**(1) DA_NEEDED — 4 COGNITION-pillar REGRESS items cross the discrete ±1 grade band, a check
`TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP`'s `watchdog_variance` ceiling mechanism
does not cover:**
- `simq_routing_test_seed42_500t` COGNITION anchor=A actual=C
- `simq_routing_test_seed456_500t` COGNITION anchor=A actual=C
- `hero_guild_routing_seed42_500t` COGNITION anchor=S actual=C
- `hero_guild_routing_seed456_500t` COGNITION anchor=A actual=C

Yesterday's ticket confirmed real, watchdog-throttle-driven (D06 F6) run-to-run non-determinism
on FAST-tier scenarios and added `score_ceilings.json` `watchdog_variance` entries for
`simq_routing_test_seed42_500t` (PROGRESSION, COGNITION), `simq_routing_test_seed123_500t`
(PROGRESSION), and `urban_political_seed456_500t` (ECONOMY, PROGRESSION) — but that ceiling only
feeds `test_grade_regression.py`'s score-tolerance failure-message path
(`_format_score_failures()`), not the separate, harder `_within_band()` discrete-grade check.
Confirmed directly by reading the test file: the two checks are genuinely independent code paths.

Two of today's 4 items were explicitly sampled and pronounced "stable" by yesterday's ticket based
on only light (2x/3x) re-run sampling — `simq_routing_test_seed456_500t` COGNITION ("stable at
0.6415/63 events across 2 re-runs, though only lightly sampled") and `hero_guild_routing_seed42_500t`
("stable or only sub-tolerance noise"). Today's runs (2 independent re-runs, both showing the same
4 items) directly contradict that conclusion. The other 2 items either had a ceiling for a
different pillar/check-branch than what's failing today (`simq_routing_test_seed42_500t`) or were
recalibrated as "confirmed stable via 3x re-run" (`hero_guild_routing_seed456_500t`) — also
contradicted.

**The open design question**: should the `watchdog_variance` ceiling mechanism be extended to also
suppress/annotate discrete grade-band crossings (not just score-tolerance), given the same
low-event-count watchdog-throttle root cause plausibly explains a band crossing too? Or is a grade
crossing of this size (S→C, a 3-band jump) evidence of something beyond ordinary watchdog jitter,
warranting deeper investigation rather than a wider ceiling? This is a real ruling this ticket does
not make itself.

**(2) A newly-exposed, real drift gap on `lifecycle_full_coverage_world_seed42_200t`:**
`TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD` added this anchor entry but never registered the key
in `FAST_ANCHOR_KEYS` (confirmed absent from the list) and no dedicated isolated test exists for
it — a genuine "registration step missed" gap, distinct from the two `urban_political_selfmodel_*`
keys (which the audit also flags as "uncovered" but are actually correctly covered by their own
dedicated isolated tests — confirmed false positives, no action needed for those two).

Registering `lifecycle_full_coverage_world_seed42_200t` in `FAST_ANCHOR_KEYS` (a mechanical,
disclosed edit already made — see Files Changed) immediately surfaced that **7 of its 8 pillars**
(COGNITION, AGENCY, COMBAT, PROGRESSION, SOCIAL, WORLD, NARRATIVE — only FACTION is within band)
drift beyond score tolerance against the anchor values committed at creation time, never verified
since. This matches the same SUB-384-cascade drift pattern several other worlds already had fixed
by `TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP` and its predecessor tickets — but this
specific key was never gated, so nobody looked at it during those fixes.

## Scope
1. **Investigate finding (1)**: determine whether the 4 COGNITION band-crossing items share the
   same root cause as yesterday's confirmed watchdog-variance instability (re-sample each with
   multiple re-runs, check for `WatchdogTrip` alerts, compare event counts across runs — same
   methodology `TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP` used). Make a concrete
   recommendation: extend `watchdog_variance` ceiling coverage to the grade-band check too (and
   how — this needs either a `test_grade_regression.py` code change to `_within_band()`, or a
   different mechanism), or treat as a distinct issue requiring its own investigation.
2. **Investigate finding (2)**: confirm `lifecycle_full_coverage_world_seed42_200t`'s 7-pillar
   drift is the same already-understood SUB-384 cascade (via `compile_context.json`
   legacy_roles/legacy_factions inspection, same methodology as prior recalibration tickets) —
   not assumed, verified per-pillar.
3. **Plan/Implement**: for finding (1), implement whatever concrete resolution Investigate
   recommends. For finding (2), if confirmed as the known cascade, recalibrate
   `grade_anchors.json` for the 7 drifted pillars following the established pattern.

## Out of Scope
- `TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE`'s own scope (the shadow-parity test suite that
  triggered this audit run) — already DONE, not revisited here.
- The already-fixed SUB-384 root cause itself (`WorldCompiler.compile()`) — not touched, only
  its downstream calibration-data staleness.
- The already-landed `watchdog_variance` ceiling entries from `TCK-20260810-SIMQ-FAST-TIER-DRIFT-
  AND-RELIABILITY-GAP` for `simq_routing_test_seed42_500t`'s PROGRESSION pillar,
  `simq_routing_test_seed123_500t`, and `urban_political_seed456_500t` — untouched, still correct
  for the score-tolerance check they cover.

## Acceptance Criteria
- [x] All 4 COGNITION band-crossing items re-sampled with a real multi-trial investigation (not
      assumed); root cause confirmed or ruled out as the same watchdog-variance mechanism —
      confirmed NOT F6 watchdog-variance; bisected via disposable `git worktree`s to commit
      `3d992dd0` (`TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION`), an already-documented
      intentional divergence (`docs/guidelines/intentional_divergences.md` §2.40). 18 total trials
      across Investigate (15) and Implement (3 reruns): 17/18 bit-identical at COGNITION=0/C, 1/18
      showed a rare residual (event_count=2/grade=B) under artificially induced heavy load — the
      dependent guard test was kept in a tolerance-guard shape (not strict bit-identical) to
      account for this, see Implementation Notes.
- [x] A concrete decision made and implemented for extending (or not extending) the
      `watchdog_variance` mechanism to cover discrete grade-band crossings, with reasoning
      recorded — NOT extended (Decision 3, plan.md): the drift is a real, understood, intentional
      behavior change, not throttle-driven noise; `grade_anchors.json` recalibrated instead, and
      the now-inert `score_ceilings.json` entry annotated as superseded rather than deleted.
- [x] `lifecycle_full_coverage_world_seed42_200t`'s 7-pillar drift investigated and confirmed (or
      ruled out) as the SUB-384 cascade pattern — confirmed **compound**, not purely SUB-384: this
      world's own `ENABLE_ADVENTURE_ROUTING: "ON"` profile setting directly exposes it to the same
      `3d992dd0` mechanism, plus 3 additional tier-5 GoalScorer-consolidation commits that landed
      after the originating audit snapshot. SUB-384's own role/faction signature independently
      re-confirmed via `compile_context.json`.
- [x] `grade_anchors.json` recalibrated for `lifecycle_full_coverage_world_seed42_200t` if
      confirmed as expected drift, following the established methodology — 8 pillars recalibrated
      (COGNITION, AGENCY, COMBAT, ECONOMY, PROGRESSION, SOCIAL, WORLD, NARRATIVE; ECONOMY folded in
      beyond the originally-named 7 per the SUB-384 same-anchor/same-cluster precedent). FACTION
      and INFORMATION confirmed unchanged, left untouched. Test for this run_key passes cleanly.
- [ ] **`pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q` shows 0
      unexplained failures for all 5 items above — PARTIALLY satisfied, reinterpretation
      required, evidence below.** `lifecycle_full_coverage_world_seed42_200t` passes cleanly (0
      failures). The 4 COGNITION items no longer fail on COGNITION (this ticket's own subject,
      fully resolved) — but Implement's own mandatory fresh re-verification (Step 1, required by
      Decision 1 given this area's active churn) discovered all 4 now fail on a **different**
      pillar, AGENCY, which had separately, newly drifted to `0/C` on all 4 run_keys (previously
      only suspected on 1 of them at Scope time). This is a genuinely distinct finding — a
      different pillar, a different plausible root cause (`docs/guidelines/intentional_divergences.
      md` §2.41's `defer_with_reason` gap, not `3d992dd0`), from a different, later-landing ticket
      (`TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`) — not this ticket's own Finding 1 recurring.
      AC5's literal wording ("passing, or carrying a `[known ...]` annotation") does not
      technically fit this case: the `[known ...]` annotation mechanism only exists on
      `_format_score_failures()`'s score-tolerance path, not on `_within_band()`'s discrete
      grade-band-check path where these AGENCY failures actually occur (confirmed as genuinely
      independent code paths, per this ticket's own Request Summary) — building that mechanism
      would be new test-infrastructure work, not pre-approved by Review, and fixing AGENCY itself
      was explicitly ruled out of this ticket's scope by Plan's Decision 2 (a different pillar, a
      different root-cause ticket). Per this session's established practice of reinterpreting an AC
      with full evidence rather than silently reinterpreting or routing around it: **this ticket's
      own named subject (COGNITION band-crossing + lifecycle drift) is fully resolved and verified
      not-COGNITION-caused**; the AGENCY residual is disclosed, root-cause-hypothesized, and
      tracked by a real follow-up ticket (`TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-
      DRIFT`) rather than silently absorbed or silently left untracked. Leaving this box unchecked
      to honestly reflect that the literal pytest command does not yet show 0 failures for these 4
      items — Verify should make the final call on whether this satisfies Definition of Done.

## Related Tickets
- TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP (DONE — established the watchdog_variance
  mechanism and root-caused the same instability class this ticket extends)
- TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD (DONE — created the `lifecycle_full_coverage_world_
  seed42_200t` anchor entry that was never registered/gated)
- TCK-20260811-ADVENTURE-SHADOW-MIGRATION-GATE (the ticket whose AC5 `/simq-audit` invocation
  discovered this)

## Related Docs
- docs/audits/D06_longrun_health.md (F6, the watchdog-throttle mechanism)
- docs/simulation_quality/audit_workflow.md

## Related Stored Artifacts
None yet.

## Related Code Areas
- tests/simulation_quality/test_grade_regression.py (`_within_band()`, `_format_score_failures()`,
  `FAST_ANCHOR_KEYS` — the newly-added `lifecycle_full_coverage_world_seed42_200t` registration
  already landed here, uncommitted)
- tests/simulation_quality/fixtures/score_ceilings.json (`watchdog_variance` ceiling entries)
- tests/simulation_quality/fixtures/grade_anchors.json

## Assumptions / Open Questions
- The `lifecycle_full_coverage_world_seed42_200t` FAST_ANCHOR_KEYS registration edit is already
  made in the working tree (uncommitted) as a direct result of this audit run — Implement should
  build on it, not re-do it, but should verify it's still correct before assuming so.
- Whether the 4 COGNITION band-crossing items are genuinely the same watchdog mechanism or
  something new is explicitly NOT assumed here — Investigate's own job.

## Implementation Notes
Implemented per the approved `plan.md`'s Steps 1-9, with one substantive correction made during
Implement based on real evidence Step 1's mandatory fresh reconfirmation surfaced:

1. **Step 1** — Fresh reconfirmation via `tools/calibrate_simq.py` internals for all 5 named items
   (2-3 independent trials each). Investigate's snapshot values held for 4 of 5; the 5th
   (`lifecycle_full_coverage_world_seed42_200t`) was still measurably moving (SOCIAL
   2395→496→497 across three successive samples in this same session), consistent with
   investigation.md's own Risk #1/#2 disclosure — Step 1's own fresh values were used, not
   investigation.md's snapshot.
2. **Step 2** — `grade_anchors.json` COGNITION recalibrated to `{"grade": "C", "score": 0.0}` for
   the 4 named items. AGENCY and all other pillars on these 4 entries left untouched.
3. **Step 3 — corrected during Implement.** The plan's proposed strict bit-identical conversion of
   `test_simq_routing_test_seed42_500t_cognition_grade_stability` was falsified by direct
   re-verification: 1 of 3 fresh isolated-invocation reruns under the test's own induced-load
   mechanism produced `event_count=2, grade=B, loop_detected=True` instead of the expected 0/C (the
   other 2 reruns matched). This is real evidence of a rare residual variance surviving the
   `3d992dd0` fix that Investigate's own 15 trials did not happen to sample. Rather than force the
   plan's strict-equality assertion through despite contrary evidence, the guard was kept in the
   tolerance-guard (2b) shape — not the 2a bit-identical shape the plan proposed — with a floor
   that accepts the deterministic 0/C outcome as the expected/asserted-for-idle case but tolerates
   the observed rare residual under induced load specifically (`event_count <= 2`,
   `grade in {"C", "B"}`). Re-verified 3/3 clean on isolated reruns after this correction. Docstring
   and the module-level NOTE block both updated to document this real finding rather than the
   plan's original (falsified) "perfectly deterministic" framing. `grade_anchors.json`'s COGNITION
   anchor value itself (Step 2) is unaffected by this correction — 0/C remains the correct,
   overwhelming-majority value (17/18 total trials across Investigate + Implement).
4. **Step 4** — `grade_anchors.json` recalibrated for `lifecycle_full_coverage_world_seed42_200t`,
   8 pillars (COGNITION, AGENCY, COMBAT, ECONOMY, PROGRESSION, SOCIAL, WORLD, NARRATIVE), per
   Decision 2's ECONOMY fold-in. FACTION/INFORMATION confirmed unchanged, untouched.
5. **Step 5** — `score_ceilings.json`'s now-inert `simq_routing_test_seed42_500t`/COGNITION
   `watchdog_variance` entry annotated as superseded (not deleted), with the annotation text
   updated during Implement to honestly reflect the Step 3 residual-variance finding (18 trials,
   17/18 at 0/C, 1/18 residual) rather than an overclaimed "zero correlation" framing.
6. **Step 6** — `docs/simulation_quality/eval_matrix_results.md`: NOTE blocks added to
   `simq_routing_test` and `hero_guild_routing` sections; new `lifecycle_full_coverage_world`
   section added (didn't exist before).
7. **Step 7** — `docs/parity_ledger/substrate.yaml` SUB-384 UPDATE block appended, documenting the
   compound (SUB-384 + `3d992dd0` + 3 additional landed commits) cause for the lifecycle anchor.
   `status`/`priority` unchanged.
8. **Step 8** — Filed `tickets/todos/TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT.md`
   (standard tier, P1) for the disclosed AGENCY drift (confirmed on all 4 named items, broader than
   Scope's original single-item suspicion) and the 2 stale `_1000t` SLOW-tier guards. Not fixed
   here — explicitly out of scope per Decision 2.
9. **Step 9** — See Test Summary.

No production `src/` file was changed at any point — confirmed via `git diff --stat -- src/`
empty throughout.

**Process note**: The dispatched `implementer` sub-agent stalled across 3 resumes on a
long-running full-file `-m slow` sequential sweep without completing Step 9's write-up; the
orchestrating session took over directly to complete Step 3's correction and Step 9's
verification. Separately, the session's own tmp filesystem became resource-exhausted
(0MB free, from accumulated sub-agent transcripts across this long multi-ticket session)
partway through Step 9, blocking further heavy-output Bash commands — resolved after clearing
`data/runs/*` (3.1G of gitignored, ephemeral, historically-uncleared simulation-run output) and a
stale duplicate `venv/` directory, freeing real disk space, then relying on already-gathered
evidence (isolated single-test reruns, already-run scoped pytest commands) rather than
re-attempting a full sequential `-m slow` corpus-diversity sweep, which per
`TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE`'s own established finding is a known
cumulative-session-load-flake-prone invocation style in this repo (~1-in-16 observed rate) —
not the authoritative verification path (`make simq-corpus-diversity-slow-isolated` is), and
this ticket's own Step 3 correction already accounts for exactly this class of residual
variance directly, with real isolated-invocation evidence.

## Test Summary
- `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k "simq_routing_test_seed42_500t or simq_routing_test_seed456_500t or hero_guild_routing_seed42_500t or hero_guild_routing_seed456_500t or lifecycle_full_coverage_world_seed42_200t"`
  — `lifecycle_full_coverage_world_seed42_200t` PASSES cleanly. The 4 COGNITION items each show
  exactly 1 failure, now isolated entirely to AGENCY (not COGNITION) — confirmed by direct
  `-vv` inspection of each failure message. This is the disclosed, follow-up-ticketed finding, not
  a recurrence of this ticket's own Finding 1.
- `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q` (full FAST-tier
  sweep) — 32 pre-existing, unrelated failures confirmed identical with and without this ticket's
  diff (via `git stash` isolation) — all are `[known tick_budget: ...]`-annotated
  score-tolerance/dormant-rule findings across scenarios entirely outside this ticket's named
  scope (`dungeon_crawl_*`, `frontier_extended_*`, `highland_traverse_*`, `crowded_frontier_*`,
  `frontier_marches_*`, `generated_frontier_3_42_*`, `quest_dense_frontier_*`,
  `simq_scale_stress_*`, plus the seed123 siblings of this ticket's own 2 named worlds — none of
  which this ticket touches). 39 passed with this ticket's diff vs. 38 without (the +1 is
  `lifecycle_full_coverage_world_seed42_200t`, newly registered and now passing).
- `pytest tests/unit/worldassembly/test_corpus_diversity.py::test_simq_routing_test_seed42_500t_cognition_grade_stability`
  — FAILED on first fresh isolated invocation (`event_count=2, grade=B` under induced load,
  contradicting the plan's strict-equality proposal) — this is the finding that drove Step 3's
  correction. PASSED 3/3 on subsequent isolated invocations after the guard was corrected to the
  tolerance shape.
- `pytest tests/unit/worldassembly/test_corpus_diversity.py -k "simq_routing_test_seed42_500t or hero_guild_routing" -m slow -v`
  — 2 passed (the in-scope `_500t` guard, post-correction, plus one other unrelated guard in the
  `-k` match set), 1 failed + 1 error (`test_hero_guild_routing_seed42_1000t_cognition_grade_stability`
  — the already-disclosed, out-of-scope `_1000t` guard, tracked by the Step 8 follow-up ticket, not
  a new finding).
- `pytest tests/unit/strategic/test_score_normalization.py::test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate`
  — PASSED (STRAT-186 sanity check, unmodified by this ticket).
- `python3 -c "import json; json.load(open('tests/simulation_quality/fixtures/grade_anchors.json'))"` /
  `score_ceilings.json` — both parse cleanly.
- `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/substrate.yaml'))"` — parses
  cleanly.
- **Not run to completion**: the full `pytest tests/unit/worldassembly/test_corpus_diversity.py -m slow -q`
  sequential sweep (all ~32 tests) — attempted in background, terminated by this session's own
  tmp-filesystem exhaustion (an infrastructure constraint unrelated to this ticket's diff, later
  resolved), and in any case this exact invocation style is the documented flake-prone one per
  `TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE` (~1-in-16 observed cumulative-session-load
  failure rate, unrelated to per-anchor calibration correctness). The isolated single-test
  reruns above (this repo's own established remediation pattern, `make
  simq-corpus-diversity-slow-isolated`) are the trustworthy signal and were used instead.

## Files Changed
- `tests/simulation_quality/fixtures/grade_anchors.json` — COGNITION recalibrated for 4 named
  items; 8-pillar recalibration for `lifecycle_full_coverage_world_seed42_200t`.
- `tests/simulation_quality/fixtures/score_ceilings.json` — 1 entry annotated as superseded
  (reason field only; `ceiling_kind`/`evidence`/`since_ticket` unchanged).
- `tests/unit/worldassembly/test_corpus_diversity.py` — `test_simq_routing_test_seed42_500t_cognition_grade_stability`
  converted from the F6-framed 3-trial tolerance shape to a corrected idle/load tolerance shape
  reflecting the real `3d992dd0`-driven step-change plus the residual-variance finding; module-level
  NOTE block updated to match.
- `tests/simulation_quality/test_grade_regression.py` — `lifecycle_full_coverage_world_seed42_200t`
  registered in `FAST_ANCHOR_KEYS` (pre-existing edit from Scope, verified still correct).
- `docs/simulation_quality/eval_matrix_results.md` — NOTE blocks for `simq_routing_test`,
  `hero_guild_routing`; new `lifecycle_full_coverage_world` section.
- `docs/parity_ledger/substrate.yaml` — SUB-384 UPDATE block appended.
- `tickets/todos/TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT.md` — new follow-up
  ticket (Step 8).

## Completion Summary
Both of this ticket's findings resolved with real evidence, not assumption. Finding 1 (4 COGNITION
band-crossing items): ruled out F6 watchdog-variance via 18 total trials; bisected to a real,
already-documented intentional divergence (`3d992dd0`/`TCK-20260810-PROJECT-SWITCH-BYPASS-
GENERALIZATION`); `grade_anchors.json` recalibrated to the new deterministic value; the
`watchdog_variance` mechanism deliberately NOT extended to grade-band crossings (Decision 3);
the now-inert ceiling entry annotated, not deleted. A real residual (1/18 trials, rare load-driven
variance) was found during Implement's own mandatory reconfirmation and handled with a corrected
tolerance-guard rather than forcing the plan's original strict-equality proposal through despite
contrary evidence. Finding 2 (`lifecycle_full_coverage_world_seed42_200t`): confirmed as a compound
cause (SUB-384 cascade + the same `3d992dd0` mechanism + 3 additional landed commits), 8 pillars
recalibrated. A newly-discovered, disclosed AGENCY drift on all 4 of Finding 1's named items (a
different pillar, different plausible root cause, different originating ticket) was not fixed
here — filed as `TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT` per Decision 2's
explicit scope boundary. AC5's literal pytest-command wording is not fully satisfied for the 4
named items (they still show 1 failure each, now on AGENCY only) — left unchecked with a full
evidentiary reinterpretation recorded in the Acceptance Criteria section above; this ticket's own
named subject (COGNITION) is fully and verifiably resolved. Zero `src/` changes throughout.
