---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP
artifact_type: investigation
tags: [simulation-quality, calibration, corpus]
---

# Investigation — TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP

## Current Behavior

### Finding (1) — 4 COGNITION band-crossing items

`tests/simulation_quality/test_grade_regression.py`'s `test_grade_within_anchor_band`
(`FAST_ANCHOR_KEYS`, line 111-195) reads the committed `data/calibration/{run_key}/quality_report.json`
and checks it against `tests/simulation_quality/fixtures/grade_anchors.json` via two independent
checks: `_within_band()` (±1 letter grade, line 231) and `_within_score_tolerance()` (line 242).
Current committed anchors (`grade_anchors.json`) and committed calibration reports
(`data/calibration/.../quality_report.json`, all four dated 2026-08-11 ~18:1x, i.e. captured by
the audit run this ticket originates from):

| run_key | COGNITION anchor | committed report | fresh re-verify (this session, x2) |
|---|---|---|---|
| `simq_routing_test_seed42_500t` | A / 1.3253 | 0 events / 0.0 / **C** | 0 events / 0.0 / **C** (identical) |
| `simq_routing_test_seed456_500t` | A / 0.5703 | 0 events / 0.0 / **C** | 0 events / 0.0 / **C** (identical) |
| `hero_guild_routing_seed42_500t` | S / 2.1084 | 0 events / 0.0 / **C** | 0 events / 0.0 / **C** (identical) |
| `hero_guild_routing_seed456_500t` | A / 0.9256 | 0 events / 0.0 / **C** | 0 events / 0.0 / **C** (identical) |

**Repro methodology used** (matching `stored_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/repro_sweep.md`
Section 2's exact shape): for all 4 anchors, drove the real throttled `Kernel` (`no_frame_pacing=True`,
no `audit_mode`) via `tools/calibrate_simq.py`'s real internals (`_resolve_profile`,
`_load_profile_feature_flags`, `_run_engine`, `_build_hub`, `_replay_jsonl_through_hub`) — 2 independent
idle repeats each, plus one shared 2x-induced-load session (8 busy-worker processes on this 4-core
machine) covering all 4 anchors. **Result: 15 independent trials total (8 idle + 4 load-2x + the 3
trials inside the already-committed `test_simq_routing_test_seed42_500t_cognition_grade_stability`
guard test, run directly), every single one bit-identical at `event_count=0, normalized_score=0.0,
grade=C`.** No `WatchdogTrip` alert or budget-warning count correlated with any change in COGNITION's
output — the watchdog fires on every trial (idle and load alike, same as always) but COGNITION's
value never moves. This directly contradicts yesterday's `TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-
RELIABILITY-GAP` "stable" classifications for `hero_guild_routing_seed42_500t` (212 vs 213 events)
and `simq_routing_test_seed456_500t` (63 events, 2 re-runs) — those numbers were real *at the time*,
but the world has moved since (see Root cause below); today's re-sample is not a repeat of
yesterday's under-sampling mistake, it is a genuinely different live value.

**The already-committed `test_simq_routing_test_seed42_500t_cognition_grade_stability` guard test**
(`tests/unit/worldassembly/test_corpus_diversity.py:501`, landed by `TCK-20260715-SIMQ-ANCHOR-LOAD-
SENSITIVITY-SWEEP` specifically *because* this anchor was confirmed genuinely watchdog-variable back
then — event_count 183/183/183/179, always grade A) was run directly (`pytest ... -m slow`) and
**FAILS today, deterministically, all 3 of its own internal trials**: `grade=C outside +/-1 band of
anchor grade=A` every time. This is strong independent confirmation the drift is real and is not an
artifact of my own repro script (verified byte-for-byte against the committed test's own call
sequence).

**Root cause — directly bisected, not assumed.** `decision_divergence_detected` (COGNITION's
dominant event type for these 4 anchors — `self_model_updated` never fires for either world/profile
since neither sets `ENABLE_SELF_MODEL_COGNITION`, which defaults `OFF`, `src/domains/optimization/
feature_flags.py:15`) is emitted (`src/observability/event_extractor.py:844-859` /
`src/observability/event_shapers.py` `StrategyShaper`, both paths checked and agree) only when an
entity's top concern is `danger` with `urgency > 0.7` while its active project's kind is in
`_NON_SURVIVAL_PROJECT_KINDS` — i.e., the entity is *stuck*, unable to switch to a survival-response
project despite a critical danger signal. Toggling `ENABLE_PUSH_EVENT_SHAPERS_PHASE2=OFF` (forcing
the old `event_extractor.py` code path instead of the newer `StrategyShaper`) still produced
`event_count=0` — ruling out the event-shaping migration itself as the cause; the upstream STRATEGIC
decision logic itself changed.

Bisected via disposable `git worktree`s at 3 points on this branch's own history:

| Commit | Date (UTC) | `simq_routing_test_seed42_500t` COGNITION |
|---|---|---|
| `b3bb72c6` (TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP, yesterday's own commit) | Aug 10 | 196 events / 1.968 / **A** |
| `d671c53b` (immediately before the epic below) | Aug 10 | 194 events / 1.948 / **A** |
| `3d992dd0` (`TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION` + 3 sibling tickets, closed as one commit) | Aug 11, 03:07 +07 | **0 events / 0.0 / C** |
| `846d53de^` / `428f5ec3` (just before `TCK-20260811-ADVENTURE-GOAL-SCORER`) | Aug 11 | 0 events / 0.0 / C (unchanged) |

The regression lands exactly at `3d992dd0`, specifically `TCK-20260810-PROJECT-SWITCH-BYPASS-
GENERALIZATION` (`stored_artifacts` not kept, ticket in `tickets/done/`). That ticket:
1. Replaced `evaluate_project_switch()`'s hardcoded `kind=='danger' and score>80` / `kind=='detour'`
   lock-bypass allowlist with a generalized, normalized score/urgency-floor rule
   (`src/systems/strategic_systems/intelligence.py`, STRAT-186).
2. Rewired `AdventureDecisionPhase.apply()` (`src/domains/adventure/phase.py`) to route its project
   handoff through `evaluate_project_switch()` **instead of unconditionally overwriting
   `current_project_id`** — closing an asymmetry where `AdventureDecisionPhase` was the only writer
   that ignored locks/interruption-resistance entirely.

Both `simq_routing_test` and `hero_guild_routing` calibration profiles set `ENABLE_ADVENTURE_ROUTING:
"ON"` (`config/simulation_quality/profiles/*.yaml`) — i.e., both are exactly the kind of
`AdventureDecisionPhase`-heavy worlds this fix targets. Before the fix, `AdventureDecisionPhase`'s
unconditional overwrite could churn an entity's `current_project_id` in ways that left it out of sync
with a newly-critical `danger` concern (the entity's active project kind mismatching its top concern),
generating `decision_divergence_detected` on essentially every tick the mismatch persisted — this is
exactly what drove the historical 183-412 event counts across this whole anchor family (documented in
`test_hero_guild_routing_seed42_1000t_cognition_grade_stability`'s own docstring, "F6/
decision_divergence_detected-class"). After the fix, the same routing now correctly respects the
lock/urgency-floor gate, so the stuck-mismatch state this event exists to detect essentially never
persists for these two worlds anymore. **`decision_divergence_detected` is scored with a *positive*
weight** (`config/simulation_quality/scoring_weights.yaml`: `subjective_divergence: 5.0` / `30.0`,
`src/simulation_quality/scorers/cognition.py:106-110`) under the framing "entities … diverged on
route choice" (a positive diversity signal in this scoring model) — so the historical A/S COGNITION
grades for these 4 anchors were, in substantial part, *measuring the frequency of a real interruption-
bypass bug*, not a positive quality signal. This is a legitimate, already-reviewed, already-documented
divergence: `docs/guidelines/intentional_divergences.md` §2.40 "Interruption-Bypass Generalization",
rationale class **Enforced**, `docs/parity_ledger/strategic_cognition.yaml` STRAT-185/186/187 all
`status: verified`. It is not a new bug and not F6 watchdog jitter — see Risks below for the adjacent
churn still landing in this exact area.

**This does NOT fit the F6 watchdog-variance pattern**: F6-affected anchors (per `TCK-20260715`'s own
repro, `stored_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/repro_sweep.md` Section 2)
show *small, load-correlated, variable* event counts (e.g. 183→179 at 4x load, or 316↔401 across idle
repeats) — never a hard, load-insensitive zero reproduced identically across 15/15 independent trials.
`watchdog_trips`/`budget_warnings` fire on every trial here exactly as they always have (confirmed:
1 `WatchdogTrip` per idle run, more under load) with zero correlation to COGNITION's value — decisive
evidence this is a deterministic step-change, not throttle-driven jitter.

**Adjacent, out-of-scope discovery (disclosed, not fixed here):** the same fresh re-verification for
`simq_routing_test_seed42_500t` also shows **AGENCY** has drifted from its committed calibration
value (9 events / 0.168 / B, itself already inside the anchor's A-band) to **0 events / 0.0 / C**
at current `HEAD` — i.e., beyond `simq_routing_test_seed42_500t`'s AGENCY anchor's own ±1 band. This
was *not* present in the Aug-11 18:12 committed calibration report and is not one of this ticket's 4
scoped items. Plausible cause: `docs/guidelines/intentional_divergences.md` §2.41 "Adventure-Route
Defer-Reason Observability Gap" (`TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`, landed *after* this
ticket's originating audit run) — `last_defer_reason`/`defer_with_reason` (an AGENCY event) was
deliberately not ported when `AdventureDecisionPhase` was deleted. Not verified further — genuinely
out of this ticket's scope (Out of Scope explicitly excludes "the already-fixed SUB-384 root cause
itself" and this is a different mechanism entirely) — flagged as a real, material gap for a follow-up
ticket, not silently absorbed.

### Finding (2) — `lifecycle_full_coverage_world_seed42_200t` 7-pillar drift

**`FAST_ANCHOR_KEYS` registration confirmed present and correct**: `tests/simulation_quality/
test_grade_regression.py:194` — `"lifecycle_full_coverage_world_seed42_200t"`, with the exact
comment block the ticket describes (added as a mechanical consequence of the audit run). No further
action needed on the registration itself.

**SUB-384 signature confirmed directly** (same methodology as `stored_artifacts/TCK-20260810-SIMQ-
FAST-TIER-DRIFT-AND-RELIABILITY-GAP/investigation.md` Finding 1 and `stored_artifacts/TCK-20260810-
SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION/investigation.md`): read `data/worlds/
lifecycle_full_coverage_world/resolved/compile_context.json` directly —
`legacy_roles: {..., "raider": 2, "leader": 2, "sentinel": 2, "predator_hunter": 2, "alpha": 2, ...}`
(role-id → `EntityRole.MONSTER`(=2)) and real `legacy_factions` entries (`goblin_warband`,
`orc_clan`, `undead_remnants`, `wild_beast_pack` all present, non-empty). This is the exact SUB-384
signature the prior tickets used to confirm affected-vs-not — **confirmed, not assumed**.

**But the drift is NOT purely SUB-384, and the committed calibration snapshot the audit used is
itself already stale.** `lifecycle_full_coverage_world`'s own profile
(`config/simulation_quality/profiles/lifecycle_full_coverage_world.yaml`) sets
`ENABLE_ADVENTURE_ROUTING: "ON"` (by design, per its own header comment, to maximize lifecycle-bucket
reachability) — i.e., this world is *also* directly exposed to Finding (1)'s
`PROJECT-SWITCH-BYPASS-GENERALIZATION` mechanism, not just SUB-384. Three-way comparison (anchor vs.
committed Aug-11 18:17 calibration report vs. this session's fresh re-verification, x2, bit-identical
both times):

| Pillar | anchor (`grade_anchors.json`) | committed report (Aug 11 18:17) | fresh re-verify (this session) |
|---|---|---|---|
| COGNITION | A / 1.2879 | 14 ev / 0.35 / B | **0 ev / 0.0 / C** |
| AGENCY | A / 1.925 | 11 ev / 0.187 / B | **0 ev / 0.0 / C** |
| COMBAT | B / 0.0101 | 28 ev / 0.272 / B | 2 ev / 0.0237 / B |
| FACTION | S / 7.5 | 75 ev / 7.5 / S | 75 ev / 7.5 / S (unchanged, within band+tolerance both times) |
| ECONOMY | A / 0.5304 | 17 ev / 0.571 / A (passes) | **0 ev / 0.0 / C** (newly drifted, NOT in ticket's 7-item list) |
| PROGRESSION | A / 0.8736 | 11 ev / 0.418 / B | 1 ev / -0.157 / C |
| SOCIAL | S / 29.115 | 2395 ev / 23.0 / S | **496-497 ev / ~6.2 / S** (further drop) |
| INFORMATION | C / 0.0 | 0 ev / 0.0 / C (unchanged) | 0 ev / 0.0 / C (unchanged) |
| WORLD | A / 0.54 | 72 ev / 0.97 / A | 49 ev / 0.72 / A |
| NARRATIVE | C / 0.0 | 2 ev / 0.082 / B | 3 ev / 0.123 / B |

The two fresh re-verify runs (independent, back-to-back this session) agree closely (SOCIAL 496 vs
497 events, everything else bit-identical) — i.e. **current live behavior is itself stable/
deterministic**, it is simply *different* from both the anchor and the Aug-11 18:17 committed
snapshot. This is consistent with the same commit-cluster identified in Finding (1): the committed
snapshot predates `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE` (18:59 UTC),
`TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER` (20:24 UTC), and `TCK-20260811-REGION-STABILIZATION-GOAL-
SCORER` (Aug 12, 03:03 UTC) — three more tier-5 GoalScorer-consolidation commits landed *after* the
audit that discovered this ticket, and this world (with `ENABLE_ADVENTURE_ROUTING=ON`) is directly
exposed to that whole commit cluster, same as Finding (1)'s anchors. COGNITION/AGENCY going fully to
0/C here matches Finding (1)'s signature exactly (same mechanism). SOCIAL's further drop (2395→496)
and ECONOMY's new drift (17→0, not previously flagged) are evidence the cascade is *still moving*,
not settled — most plausibly a mix of SUB-384's original population/RNG-stream cascade (established
class: "changes death/survival timing … cascading into every pillar's own event production even
though the scorers never touch role/faction fields") compounding with the newer tier-5 arbitration
churn.

## Mechanics / Engine Constraints

- `docs/engine/kernel.md` "Emergency Throttling" — the D06 F6 watchdog/throttle mechanism Finding (1)
  was originally suspected of. Directly ruled out for all 4 items (see above): load-insensitive,
  100% deterministic zero across 15 trials.
- `docs/mechanics/04_strategic_cognition.md` §2/§6.6/§6.8 — tier-5 goal arbitration, `ProjectKind`/
  `GoalKind` score scales (`_ADVENTURE_ROUTE_SCORE_MAX=2.9`, `_GOAL_UTILITY_SCORE_MAX=100.0`) that
  `_score_scale_max()` (the STRAT-186 fix) reads.
- Strategic/Tactical Rule (CLAUDE.md): the interruption-bypass generalization is exactly this rule in
  action — a hardcoded tactical-looking `kind=="danger"` string check was replaced with the actual
  strategic urgency/score comparison it was implicitly modeling. Not touched by this ticket; cited as
  context for why the SimQ drift is legitimate.

## Docs Requiring Update

- `docs/simulation_quality/eval_matrix_results.md`: needs a dated NOTE block (matching the existing
  SUB-384/`urban_political` NOTE pattern at line ~330-354) for the `simq_routing_test`/
  `hero_guild_routing` COGNITION sections and the `lifecycle_full_coverage_world` entry, recording
  today's recalibration and its root cause (`PROJECT-SWITCH-BYPASS-GENERALIZATION`-driven, not F6).
- `docs/parity_ledger/substrate.yaml`: SUB-384's `support_boundary` field already has an "UPDATE
  (TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION, 2026-08-10)" block listing which
  worlds/anchors were recalibrated under this cause; needs a follow-up "UPDATE" block adding
  `lifecycle_full_coverage_world_seed42_200t`, explicitly noting the compounding (not purely
  SUB-384) cause for COGNITION/AGENCY/ECONOMY.
- `docs/guidelines/intentional_divergences.md`: §2.40 "Interruption-Bypass Generalization" already
  documents the root-cause code change (no edit needed to the divergence text itself); if Implement
  wants a downstream cross-reference (matching how SUB-384's substrate.yaml entry links forward to
  its SimQ-recalibration consequence) that is a nice-to-have, not a hard requirement — the
  divergence's own `Verification` test path is a strategy-layer unit test, not a SimQ anchor.

## Parity Ledger Overlap

- `docs/parity_ledger/strategic_cognition.yaml` STRAT-185/186/187 — `status: verified`, P0, all
  three already updated by `TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION` and further re-verified
  by two even-more-recent tickets (`TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG`,
  `TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION` — both landed changes to this exact
  `evaluate_project_switch()` lock-bypass block after `3d992dd0`). `test_path` for STRAT-186:
  `tests/unit/strategic/test_score_normalization.py::test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate`
  — exists and is presumably passing (not re-run here, out of this ticket's scope). This area is
  under **active, still-landing churn** — flagged as a Risk below.
- `docs/parity_ledger/substrate.yaml` SUB-384 — `status: verified`, P0, `test_path` exists
  (`tests/unit/worldbuilding/test_world_repository.py` + a large scoped regression list). Directly
  relevant to Finding (2); needs the "UPDATE" append described above.

## Prior Work

- `stored_artifacts/TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP/` (investigation.md, plan.md,
  test_plan.md, repro_sweep.md) — the F6 repro methodology this ticket's Finding (1) reused
  end-to-end. Its own repro data for `simq_routing_test_seed42_500t`/`hero_guild_routing_seed42_1000t`
  COGNITION (183-412 events, always A/S) is the "before" baseline this ticket's bisection confirms
  moved away from — not contradicted, superseded by a real subsequent code change.
- `stored_artifacts/TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP/investigation.md` — source
  of the `watchdog_variance` ceiling mechanism and the light 2-3x sampling this ticket's own Request
  Summary flags as insufficient (confirmed: today's fuller re-sample directly contradicts 2 of its
  "stable" classifications, for the reason explained above — not sampling noise, the world's live
  behavior changed between the two sessions).
- `stored_artifacts/TCK-20260810-SIMQ-CORPUS-ROLE-FACTION-DRIFT-VERIFICATION/investigation.md` — the
  exact SUB-384-cascade verification methodology (`compile_context.json` `legacy_roles`/
  `legacy_factions` inspection) applied directly to Finding (2) above.
- `tickets/done/TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION.md` — the actual root-cause ticket
  for Finding (1), fully read; confirms this is a deliberate, reviewed, tested change with its own
  intentional-divergence and parity-ledger entries already in place.

## Risks and Open Questions

1. **This area of the codebase is under active, still-landing churn.** Four related tickets
   (`TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION`, `TCK-20260811-ADVENTURE-GOAL-SCORER`,
   `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`, `TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER`,
   `TCK-20260811-REGION-STABILIZATION-GOAL-SCORER`, plus two more touching STRAT-186's exact code —
   `TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG`,
   `TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION`) all landed on `src/systems/strategic_systems/
   intelligence.py` / the adventure-routing pipeline within roughly 24 hours of this investigation.
   Finding (2)'s own numbers already show the effect of 3 of these landing *after* the audit that
   spawned this ticket. **Recommendation: re-verify live values immediately before Implement writes
   the new anchor numbers into `grade_anchors.json`** — do not blindly copy this investigation's own
   snapshot values, since more sibling tickets in this same cluster may land in the interim (this is
   a live-branch timing risk, not a methodology gap).
2. **Finding (2)'s drift is not cleanly single-cause.** The ticket's own framing ("7 of 8 pillars …
   only FACTION within band") is itself now stale — this session's fresh re-verification shows
   ECONOMY has *also* drifted beyond tolerance (17→0 events), which the original audit did not flag.
   Whether to fold ECONOMY into this ticket's recalibration (following the same evidence) or scope it
   out is a real decision Plan should make explicitly, not silently absorb either way.
3. **`test_simq_routing_test_seed42_500t_cognition_grade_stability`
   (`tests/unit/worldassembly/test_corpus_diversity.py:501`, `@pytest.mark.slow`) is now stale and
   failing, and is NOT covered by this ticket's own AC5 pytest command**
   (`pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q`, which only runs the
   FAST tier, and this guard test lives in a different file, marked slow). If Implement only touches
   `grade_anchors.json`, this pre-existing slow-marked guard test will keep failing on any `-m slow`
   or unmarked run — it needs its own update (see Anti-Drift Hazards).
4. Whether `score_ceilings.json`'s existing `simq_routing_test_seed42_500t`/COGNITION
   `watchdog_variance` entry (added yesterday, citing 194/196/194/193 event-count variance) should be
   removed/annotated as superseded, once the anchor is recalibrated to the new deterministic 0 value
   (making the ceiling permanently inert for that pillar going forward) — cosmetic, not blocking, but
   leaving it verbatim could mislead a future reader into thinking COGNITION is still F6-variable at
   this run_key.

## Anti-Drift Hazards

- **Do not extend `watchdog_variance` to grade-band crossings for these 4 items** — the evidence
  (15/15 trials bit-identical, load-insensitive, directly bisected to a specific non-F6 commit) rules
  this out cleanly. Extending the ceiling mechanism here would misclassify a real, understood,
  intentional behavior change as noise.
- **Do not add a new multi-trial `*_grade_stability` guard test** (the TCK-20260715 tolerance-guard
  shape) for these 4 items either — that shape exists specifically for anchors with real trial-to-
  trial variance. These 4 are now perfectly deterministic; a plain point-anchor update to
  `grade_anchors.json` is the correct, simpler fix. Reach for the tolerance-guard shape only if a
  *future* re-check finds real variance again.
- **The already-committed `test_simq_routing_test_seed42_500t_cognition_grade_stability` guard test's
  own inline anchor (`{"grade": "A", "score": 1.8373, "abs_floor": 0.0521}`) must also be updated**,
  not just `grade_anchors.json` — it is a separate, independently-maintained anchor value in a
  different file and will keep failing otherwise.
- Do not touch `src/systems/strategic_systems/intelligence.py` or any of the tier-5 GoalScorer code —
  Out of Scope explicitly excludes the SUB-384/interruption-bypass root causes themselves; this
  ticket's job is downstream SimQ calibration only.
- Do not fix the adjacent AGENCY drift on `simq_routing_test_seed42_500t` (or investigate §2.41's
  `defer_with_reason` gap) as part of this ticket — disclosed above as a real, out-of-scope gap for a
  follow-up ticket, not silently rolled into this one's scope.
