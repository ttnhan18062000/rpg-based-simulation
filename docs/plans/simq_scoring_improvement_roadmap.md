---
status: active
layer: simulation
authority: P1
audience: agent
tags: [roadmap, simulation-quality, calibration, corpus, determinism, planning]
date: 2026-07-13
source: docs/simulation_quality/current_state.md
---

# SimQ Scoring Calibration & Coverage — Improvement Roadmap

## Source & Method

`docs/plans/archive/simq_development_roadmap.md` (archived 2026-07-13, all 6 phases complete)
closed out the question of *corpus coverage depth* — how many worlds exercise each pillar. This
document picks up a different, narrower question raised immediately after that roadmap closed:
does the **scoring formula itself** have enough discriminative power to be useful, independent of
how much of the corpus is covered? `docs/simulation_quality/current_state.md`'s "Recommended next
features" section (added 2026-07-13, prompted by a direct question about whether scoring
multipliers need adjustment) is the evidence base this roadmap sequences into phases — read that
doc first for the full data and reasoning; this doc is *what to do about it, in what order*.

**The core finding this roadmap responds to:** 4 of SimQ's 10 pillars (WORLD, ECONOMY, PROGRESSION,
INFORMATION) structurally cannot reach grade A or S under the current weight/normalization scale,
regardless of how good the underlying world is — confirmed by cross-referencing raw
`normalized_score` values against the grade-band thresholds across all 72 committed anchor
scenarios (WORLD's entire real-world range, 0.0-0.3, fits inside the B band alone; ECONOMY tops
out at 1/3 of the way to A even at its single richest observed run, 69 scored events). Separately,
the anchor system stores only the discretized letter grade, never the raw score, which — combined
with S being an unbounded top band — makes the regression-detection goal blind to real
improvement *or* regression that doesn't cross a full grade-letter boundary. A third, unrelated but
concretely diagnosed issue (a tooling bug in `evaluate_simq.py`'s live-run mode) was found along
the way and is folded into this roadmap as a small, independent prerequisite fix.

---

## The Bar This Roadmap Targets

SimQ's own three goals (`quality_scoring_contract.md` §1) are automated quality visibility,
regression detection, and balance/tuning support. All three implicitly assume the scoring scale
itself is trustworthy — that a grade actually reflects world quality, and that a grade change
actually reflects a real behavior change. Corpus-depth work (the archived roadmap) grows *how much*
of the corpus the goals apply to; this roadmap fixes *whether the measurement itself is sound* for
the pillars and grade-band edges where that's currently in question.

---

## Phase Summary

| Phase | Goal | Depends on | Effort |
|---|---|---|---|
| **0 — Tooling Reliability** | Fix the `evaluate_simq.py` live-mode profile/world-name bug | Nothing | S |
| **1 — Scoring Discriminative-Power & Regression-Fidelity** | Make WORLD/ECONOMY/PROGRESSION/INFORMATION's grade bands actually reachable; make the anchor system sensitive to within-band movement | Phase 0 (uses the fixed tool for verification) | M (two tickets, sequenced to share one re-anchor pass) |
| **2 — ECONOMY Content Depth** | Author real economic activity into 2-3 more archetype worlds | Phase 1 (a capped formula makes new content invisible in the grades) | M |
| **3 — COGNITION Pipeline Wiring** | Give self-model query-routing a real production call site | Nothing (independent of 0-2) | M-L |

**Critical path:** Phase 0 → Phase 1 → Phase 2. Phase 3 runs independently and can be picked up in
parallel with any of the others.

---

## Phase 0 — Tooling Reliability: `evaluate_simq.py` profile/world-name bug

**Problem:** `tools/evaluate_simq.py`'s `_run_calibration()` (line 59) never forwards `--profile`
to `calibrate_simq.py`; `_parse_run_key()` (line 45) derives the calibration `--name` purely from
the run_key's regex-matched prefix (`^(.+)_seed(\d+)_(\d+)t$`). For any run_key where the profile
name differs from the world name — currently `urban_political_selfmodel_probe_seed42_200t`, the
probe fixture added by `TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE` — this passes the *profile*
name where the *world* name is expected. `calibrate_simq.py`'s world-loading then silently falls
back to a generic synthetic scenario (`world_id: "unknown"`, `scenario_name: "PROD_SMALL"`,
confirmed via that run's `run_manifest.json`) instead of erroring, producing a near-empty,
meaningless result compared against the real anchor. Verified via a standalone re-run of the exact
same scenario, which reproduces the correct, anchor-matching result — confirming this is a tooling
bug, not a quality regression. Full evidence in `tmp/evaluate_simq_bug_evidence/` (session-local,
not committed) and `docs/simulation_quality/current_state.md`'s "Known issue" note.

**Why first:** Phase 1's implementation ticket will need to run the live (non-`--dry-run`) full
corpus sweep repeatedly while tuning weights — doing that against a tool with a known silent-
corruption bug risks mistaking a tooling artifact for a real calibration result, exactly as almost
happened when this bug was first found.

**Work:** fix `_run_calibration()` to forward `--profile` explicitly (needs access to the anchor's
originating profile name, not just the run_key-derived world name — may require extending
`grade_anchors.json`'s schema with a `_profile` metadata hint per entry, or deriving profile from
a new explicit mapping, implementer's call after investigating). Additionally, `calibrate_simq.py`'s
world-loading should fail loudly (raise, not silently fall back to a synthetic scenario) when the
requested world name doesn't resolve to a real `data/worlds/{name}/` directory — the silent
fallback is what let this bug produce a plausible-looking (if empty) result instead of an obvious
crash.

**Acceptance signal:** `evaluate_simq.py` (live mode, not `--dry-run`) run against the full corpus
reproduces the same grades as the standalone per-scenario `calibrate_simq.py` invocations, including
for `urban_political_selfmodel_probe_seed42_200t`; a deliberately-broken world name in a future
anchor entry raises an error instead of silently succeeding with corrupted data.

---

## Phase 1 — Scoring Discriminative-Power & Regression-Fidelity

Two tickets, explicitly sequenced (not parallel) because both require a full corpus re-anchor pass
and that pass should only happen once.

### 1a. Recalibrate the weight/normalization scale for WORLD, ECONOMY, PROGRESSION, INFORMATION

**Problem:** see the Source & Method section above and `current_state.md`'s discriminative-power
table. These 4 pillars cannot reach A/S under current weights regardless of world quality — a real
gap against the balance/tuning-support goal (§1), which needs the top of the scale to be reachable
to mean anything.

**Work:** investigation-tier first — deliberately construct or identify one genuinely best-case and
one genuinely worst-case scenario per affected pillar, run them through the current formula, and
determine whether raising per-event weights (`config/simulation_quality/scoring_weights.yaml`) or
lowering grade thresholds (`quality_scoring_contract.md` §4.5, `S >2.0` / `A 0.5-2.0` / `B 0.0-0.5`)
— or both — restores real discrimination without destabilizing the many already-passing anchors for
these same 4 pillars in worlds where they're legitimately supposed to stay low (structural C's for
gated/inactive content must not accidentally become reachable A's from a blanket weight increase).
Changing shared weight constants risks moving grades corpus-wide — full regression sweep required,
almost certainly a wholesale `grade_anchors.json` re-anchor for at least these 4 pillars' entries.

**Acceptance signal:** for each of the 4 pillars, at least one real corpus scenario (not a synthetic
edge case) reaches A or S under the recalibrated formula, while the structurally-inert C entries
(e.g. INFORMATION in worlds with no information content) remain C — i.e. the fix must move the
ceiling, not just inflate every score uniformly.

### 1b. Persist raw `normalized_score` alongside the letter grade, with its own tolerance check

**Problem:** `grade_anchors.json` stores only the discretized letter grade, never the raw score
that produced it. Combined with S being an unbounded top band, this makes the regression-detection
goal blind in both directions for any pillar already at S — a real improvement (norm-score
2.1→10.0) and a real regression (10.0→2.1) both show as "S → S" as long as neither crosses a full
grade-letter boundary.

**Not the excluded Non-Goal:** SimQ's §14 rules out "historical run comparison" (dashboards, trend
charts over time) — that stays out of scope. This is narrower: one additional number stored per
anchor entry, checked with one additional tolerance assertion, inside the existing regression-
detection goal, not a new comparison/analytics capability.

**Work:** extend `grade_anchors.json`'s schema to carry `{"grade": "S", "score": 2.87}` per pillar
instead of a bare string (migration needed for all 72×10 existing entries — **reuse 1a's re-anchor
pass, do not run a second full corpus sweep**); extend `test_grade_regression.py`'s comparison to
assert the raw score stays within a tolerance band (empirically determined, not guessed — needs
investigation against known run-to-run variance, see
`docs/audits/D20_simq_integration.md`'s wall-clock-throttle findings, so the tolerance doesn't
false-positive on legitimate variance) of the anchored value, independent of whether the letter
grade moved.

**Acceptance signal:** a deliberately-injected synthetic score regression that stays within the same
letter-grade band is caught by the new tolerance check and would not have been caught by the old
letter-only comparison.

---

## Phase 2 — ECONOMY Content Depth Wave

**Problem:** `EconomyScorer` (`src/simulation_quality/scorers/economy.py`) listens for 10 distinct
event types (harvesting, crafting, trading, gold flow, scarcity, inflation control, conservation
checks, paid-info transactions, quest rewards) — not a thin, single-signal pillar. The corpus-wide
C-heavy distribution (60/72 anchors) is partly a genuine content gap: most worlds simply don't have
sustained harvest/craft/trade content authored into them. This pillar was never addressed by the
archived roadmap (explicitly out of scope there — a Gini-threshold/archetype-composition question,
not the `FeatureMode`-gating question that roadmap's 4 pillars shared).

**Why after Phase 1, not before or in parallel:** authoring more content into a formula that caps
at 1/3-of-A regardless of volume (confirmed empirically — the single richest observed ECONOMY run,
69 events, only reached 0.16 against a 0.5 A-threshold) risks spending real content-authoring effort
for a result that still reads as C/B corpus-wide, exactly the kind of wasted-effort trap Phase 1
exists to prevent.

**Work:** same playbook as the archived roadmap's Phase 2 (SOCIAL) — an investigation-tier ticket
first, to confirm which worlds have a merchant NPC or crafting-capable population already (per
`data/worlds/*/world.yaml`) before any content authoring, mirroring how that roadmap's Phase 3
investigation found FACTION/INFORMATION already more covered than assumed. Then author harvest/
craft/trade content into 2-3 confirmed candidate worlds, recalibrate against Phase 1's corrected
formula, full regression sweep.

**Acceptance signal:** ECONOMY grade moves measurably off C in ≥2 additional worlds, with
calibration evidence in `eval_matrix_results.md`, and 0 regressions on `evaluate_simq.py`.

---

## Phase 3 — COGNITION Pipeline Wiring: `ActionIntentAdapter.execute()`

**Problem:** self-model query-routing (Branch B — "what don't I know, who might know it") is
verified mechanically correct (`TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`, direct test-harness
invocation) but has zero live-gameplay reach. Confirmed directly (`grep -rn "ActionIntentAdapter"
src/`): the execution entry point (`src/engine/intent/action_intent.py:32`) has no production call
site anywhere — it exists only as a class definition and a docstring mention. Every other gated
phase in `src/engine/pipeline.py` (`cooperation`, `information_belief`, `adventure_decision`) is
wired via a `run_phase(...)` call; no equivalent line exists for intent execution. This is the
specific, named blocker the archived roadmap's Phase 5 gate identified and explicitly deferred as
"a distinct future initiative if gameplay ever actually needs live self-model query-routing" — this
phase picks up exactly that thread, not a re-opening of any closed question.

**Work:** investigation-tier ticket first — the exact merge point, ordering relative to the two
existing information/cooperation phases, and whether a new feature flag is needed (almost certainly
yes, to keep this off by default in shipped profiles) all need scoping before implementation. Then
add a new gated phase to `src/engine/pipeline.py` matching the existing `run_phase(...)` pattern,
taking the `ActionIntent` routed by `InformationBeliefPhase` Branch B and calling
`ActionIntentAdapter.execute()` on it, merging the resulting `EntityUpdate` back into the tick's
update set.

**Acceptance signal:** a real, shipped-profile-adjacent calibration run (flag deliberately turned
on for a test/probe profile, mirroring `urban_political_selfmodel_probe`'s existing pattern) shows
at least one `ActionIntentAdapter.execute()` call actually firing through the real tick pipeline,
not just via direct test-harness invocation.

---

## Explicitly Out of Scope

- Corpus coverage depth for FACTION/INFORMATION/SOCIAL/AGENCY — all declared complete by the
  archived roadmap's Phase 5 gate; not reopened by this roadmap.
- Any of `quality_scoring_contract.md` §14's Non-Goals (per-entity profiles, historical run
  comparison, real-time push alerts, ML-based anomaly detection, automated config suggestion) —
  reaffirmed out of scope by explicit user decision 2026-07-10. Phase 1b is deliberately scoped
  narrower than "historical run comparison" — see that phase's own note.
- ECONOMY's Gini-threshold mechanism itself, or COMBAT/NARRATIVE's formulas — the discriminative-
  power check found these are not exhibiting the same ceiling pattern as the 4 pillars in Phase 1;
  not touched by this roadmap unless a future check finds otherwise.
- Touching `src/engine/kernel.py`'s tick-budget throttle/watchdog logic — same standing scope guard
  as the archived roadmap; documented, intentional engine behavior.

---

## Related

- `docs/simulation_quality/current_state.md` — the evidence base and original recommendation
  ordering this roadmap sequences into phases; refreshed in place, treat as more current than this
  doc's prose wherever the two disagree on data.
- `docs/plans/archive/simq_development_roadmap.md` — the archived predecessor roadmap (corpus
  coverage depth, distinct question from this one).
- `docs/simulation_quality/quality_scoring_contract.md` — §1 (goals), §4.4-4.5 (normalized score
  and grade bands, target of Phase 1a), §14 (Non-Goals, reaffirmed Out of Scope, relevant to 1b).
- `docs/simulation_quality/eval_matrix_results.md` — full historical calibration batch log.
- `tmp/evaluate_simq_bug_evidence/` — session-local diagnostic evidence for Phase 0 (not committed;
  re-derive from source if this has been cleaned up by the time Phase 0 is picked up).

---

*Raised: 2026-07-13, following a direct question about whether SimQ's scoring multipliers need
adjustment — not just corpus coverage. Supersedes no prior doc; sequences findings from
`current_state.md` the same way the archived roadmap sequenced `idea_simq_near_perfect_roadmap.md`'s
threads. Ticketing pass to follow immediately via the `create-tickets` workflow.*
