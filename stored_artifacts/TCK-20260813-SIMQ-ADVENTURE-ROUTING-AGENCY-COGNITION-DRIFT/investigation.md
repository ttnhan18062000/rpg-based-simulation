---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT
artifact_type: investigation
tags: [simulation-quality, calibration, corpus, agency, cognition, adventure]
---

# Investigation — TCK-20260813-SIMQ-ADVENTURE-ROUTING-AGENCY-COGNITION-DRIFT

## Current Behavior

### Finding (1) — AGENCY drift on 4 named `_500t` run_keys: CONFIRMED, root cause broader than §2.41 discloses

**§2.41's hypothesis is directionally correct but materially incomplete.** Direct code trace (not
assumed):

`src/observability/event_extractor.py:594-630` (rollback path, live when
`ENABLE_PUSH_EVENT_SHAPERS_PHASE2=OFF`) and `src/observability/event_shapers.py:750-783`
(`StrategyShaper.shape()`, the **live** path — `ENABLE_PUSH_EVENT_SHAPERS_PHASE2` defaults `ON`,
`src/domains/optimization/feature_flags.py:45`) both emit **all four** of AGENCY's
adventure-routing event types from exactly two `EntityUpdate.property_updates` keys:
- `route_selected` + `action_executed` + `route_family_first_use` ← `prop.get("last_routing_family")`
- `defer_with_reason` ← `prop.get("last_defer_reason")`

Repo-wide grep (`grep -rn "last_routing_family\|last_defer_reason" src/`) confirms **neither key is
written anywhere in `src/` today**. The only writer of either key, ever, was the deleted
`AdventureDecisionPhase.apply()` — confirmed by reading the pre-deletion source directly
(`git show 1825f914^:src/domains/adventure/phase.py`):
- Line 161-164: writes `last_defer_reason`/`last_defer_tick` on the `DEFER_WITH_REASON` path
  (this is the only half §2.41 documents).
- Line 178-179: writes `last_routing_tick`/`last_routing_family` **unconditionally on every
  successfully-committed route** (`evaluate_project_switch()` returns non-`None`) — i.e. the
  **winning**-route path, not a sub-floor-discarded one.

§2.41's own text ("Old Behavior... New Behavior... Rationale: Bounded") describes only the
`last_defer_reason` loss, and its stated rationale (DEFER_WITH_REASON candidates are discarded by
the tier-5 utility-floor check before any `StrategicUpdate`-returning site is reached,
`intelligence.py:1409`) does **not** apply to the `last_routing_family` loss at all — a winning
`ADVENTURE_ROUTE` candidate *does* reach a commit site
(`RouteToProjectMapper.map_to_states()` → real `ProjectState`/`ObjectiveState`,
`intelligence.py:1478-1495`, confirmed by direct read), it just never writes `property_updates`
there. `AdventureGoalScorer.score()` (`src/ai/goals/adventure_scorer.py`) returns a `GoalScore`
with `metadata={"route_family": ..., "raw_score": ...}` for both the winning and deferred cases,
but nothing downstream (neither the scorer itself nor `intelligence.py`'s materialization branch)
ever converts that metadata back into an `EntityUpdate.property_updates` write. This means **all
three** `last_routing_family`-derived event types (not just `defer_with_reason`) are silently dead
for every routing-capable world, a strictly larger blast radius than §2.41 discloses.

This is corroborated by an existing, independent guard test:
`tests/unit/domains/adventure/test_delete_adventure_decision_phase_guards.py`'s "Guard 1"
(`test_defer_property_name_constant_matches_phase_and_extractor`) only pins the
`last_defer_reason` absence/presence contract — **no equivalent guard exists for
`last_routing_family`**, meaning the broader loss was never asserted or noticed by the deletion
ticket's own test suite.

Also corroborated by `docs/parity_ledger/infrastructure.yaml` INFRA-237's own `support_boundary`
field, which already carries an "Addendum (TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE)" stating
the old `ENABLE_ADVENTURE_ROUTING`-gating claim for `route_selected`/`action_executed`/
`route_family_first_use` is "UNVERIFIED against the current codebase" and explicitly asks for "a
follow-up ticket [to] re-run the AGENCY calibration sweep... against current HEAD before this
support_boundary's grading claims are relied upon again" — **this ticket is that follow-up.**

**Fresh live re-verification (this session, current HEAD)** confirms all 4 named run_keys are
`AGENCY: 0 events / 0.0 / C` (matching the parent ticket's already-established COGNITION pattern
exactly), and this is the sole cause — no other mechanism found:

| run_key | AGENCY anchor | fresh AGENCY (this session) |
|---|---|---|
| `simq_routing_test_seed42_500t` | A / 0.918 | 0 ev / 0.0 / C |
| `simq_routing_test_seed456_500t` | A / 0.6415 | 0 ev / 0.0 / C |
| `hero_guild_routing_seed42_500t` | A / 0.9777 | 0 ev / 0.0 / C |
| `hero_guild_routing_seed456_500t` | A / 0.6727 | 0 ev / 0.0 / C |

(`data/calibration/{run_key}/quality_report.json`, all dated 2026-08-13 05:30-05:32, i.e. produced
by this ticket's own parent's Implement-time re-verification session, re-confirmed by direct read
this session — `data/calibration/` is gitignored working-cache data, not durable/tracked truth;
the durable anchor is `grade_anchors.json`.)

`pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k "..."` (all 6 named
run_keys) run fresh this session: **6/6 fail**, all on AGENCY band-crossing (`actual='C'` vs
`anchor='A'`); the seed123 pair additionally fails on COGNITION band-crossing (see Finding 2).

**hero_guild_routing_seed456_500t also shows ECONOMY (B, was passing) and PROGRESSION (C, event
count/negative-count changed) drift beyond this ticket's own named scope** — confirmed present in
the fresh committed report, matching the parent ticket's own Request Summary disclosure. Not
investigated further here (Out of Scope names only AGENCY + the seed123 COGNITION/AGENCY pair) —
flagged in Risks below, not silently absorbed.

### Finding (2) — seed123 pair: SAME mechanism, SAME magnitude, NOT milder — the ticket's own framing is stale

**The Request Summary's "milder... a different magnitude" characterization is refuted by direct
evidence.** The numbers it cites (`simq_routing_test_seed123_500t` COGNITION 0.04/AGENCY 0.168;
`hero_guild_routing_seed123_500t` COGNITION 0.0467/AGENCY 0.1963) come from
`data/calibration/{run_key}/quality_report.json` files timestamped **2026-08-11 18:12/18:15** —
confirmed by direct `stat` read this session. `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`
(the mechanism identified in Finding 1) landed at **2026-08-11 18:59**, i.e. **after** that
snapshot was captured. The cited "milder" numbers are real, but they are the *pre-deletion* state
(post-`3d992dd0`/`PROJECT-SWITCH-BYPASS-GENERALIZATION`, which had already reduced routing
churn/AGENCY activity from A/0.6415 down to 9 events/0.168/B by that point — a different,
already-understood mechanism), not the *current* state.

**Fresh calibration run at current HEAD (this session, 2 independent trials each, bit-identical
both times):**

| run_key | pillar | fresh live value |
|---|---|---|
| `simq_routing_test_seed123_500t` | AGENCY | 0 ev / 0.0 / C |
| `simq_routing_test_seed123_500t` | COGNITION | 0 ev / 0.0 / C |
| `hero_guild_routing_seed123_500t` | AGENCY | 0 ev / 0.0 / C |
| `hero_guild_routing_seed123_500t` | COGNITION | 0 ev / 0.0 / C |

(Ran via `tools/calibrate_simq.py --ticks 500 --seed 123 --name {simq_routing_test,
hero_guild_routing}`, 2 trials each, identical results both times.)

`pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k "seed123"` confirms
this is now a **band-crossing** failure (`actual='C'` vs `anchor='A'`) for both COGNITION and
AGENCY on both run_keys — not a score-tolerance-only failure as the ticket text describes. This is
the **identical full-zero signature** as Finding 1's 4 named items, produced by the **identical
mechanism** (§2.41's true, broader scope — Finding 1). It is not a distinct, milder cause; it is
the same regression, just first captured under this ticket's own filing before the confirming
Implement-time re-run happened.

**The `score_ceilings.json` contradiction the ticket names is independently confirmed.** The
`simq_routing_test_seed123_500t`/`PROGRESSION`/`watchdog_variance` entry (added by
`TCK-20260810-SIMQ-FAST-TIER-DRIFT-AND-RELIABILITY-GAP`) has a `reason` field asserting COGNITION
was "stable at 0.5295/52 events across both re-runs" — this session's fresh run shows COGNITION at
`0 events/0.0`, directly contradicting that aside. The entry's own `PROGRESSION`/`watchdog_variance`
classification is not necessarily wrong (this session's `simq_routing_test_seed123_500t`
PROGRESSION showed 24 events / -0.6432, roughly consistent with the entry's originally-cited
24-28 event range) — only the incidental "COGNITION stable" claim inside its `reason` text is now
false and should be annotated (not deleted), matching the precedent the parent ticket set for its
own now-superseded ceiling annotation (`stored_artifacts/TCK-20260811-.../plan.md` Step 5).

### Finding (3) — 2 stale SLOW-tier `_1000t` guard tests: CONFIRMED same root cause, line numbers corrected

**Current line numbers** (re-verified by direct grep this session — the ticket's cited `~600`/
`~684` are stale, shifted by the parent ticket's own Step 3 edit which expanded the sibling
`_500t` test's body):
- `test_simq_routing_test_seed42_1000t_cognition_grade_stability` — now at
  `tests/unit/worldassembly/test_corpus_diversity.py:633` (was ~585 pre-parent-ticket, ~600 per
  this ticket's stale citation).
- `test_hero_guild_routing_seed42_1000t_cognition_grade_stability` — now at
  `tests/unit/worldassembly/test_corpus_diversity.py:717` (was ~669, ~684 per this ticket's stale
  citation).

Both still carry the old TCK-20260715 3-trial tolerance-guard shape (`n_trials=3`, `_within_band`
+ mean-`_within_score_tolerance` against a stale COGNITION-only anchor: A/1.7961 and S/2.0641
respectively) and a docstring still framed as "F6/decision_divergence_detected-class... genuinely
unstable" — the same stale framing the parent ticket already corrected for the `_500t` sibling.

**Fresh isolated repro this session** (per the flake-avoidance guidance: single-nodeid isolated
`pytest` invocations, not a raw sequential `-m slow` sweep —
`TCK-20260715-SIMQ-CORPUS-DIVERSITY-SESSION-LOAD-FLAKE` precedent), each test's own internal
3-trial loop:

- `test_simq_routing_test_seed42_1000t_cognition_grade_stability`: **FAILED**, all 3/3 internal
  trials `COGNITION grade=C` (anchor `A`) — `AssertionError: ... 3 trial/pillar grade(s) drifted
  beyond anchor band`.
- `test_hero_guild_routing_seed42_1000t_cognition_grade_stability`: **FAILED**, all 3/3 internal
  trials `COGNITION grade=C` (anchor `S`) — same assertion shape.

6/6 total trials across both tests deterministically `grade=C` — this is the identical signature
Finding 1/parent-ticket's investigation established for the `_500t` siblings (bisected to `3d992dd0`
/ `TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION`, `docs/guidelines/intentional_divergences.md`
§2.40), now **confirmed, not assumed**, to also hold at the `_1000t` tick count for both worlds.
No evidence of the residual load-variance signature the `_500t` sibling's own guard now tolerates
(`event_count <= 2, grade in {"C","B"}`) — both `_1000t` tests came back grade=C on 3/3 trials with
no variance observed in this session's sampling, consistent with (not proof of) the deterministic-
zero classification, matching the `_500t` sibling's own majority behavior (17/18 trials there were
also clean 0/C).

## Mechanics / Engine Constraints

- `docs/guidelines/intentional_divergences.md` §2.40 "Interruption-Bypass Generalization" —
  already-reviewed, `Enforced`-class divergence that is the underlying cause of COGNITION's
  drop (unrelated fix mechanism from Finding 1's AGENCY loss, but the same commit cluster/same
  worlds).
- `docs/guidelines/intentional_divergences.md` §2.41 "Adventure-Route Defer-Reason Observability
  Gap" — the divergence record this ticket's own Scope §1 asks to confirm/refute. **Confirmed as
  real but incomplete**: only documents `last_defer_reason`; this investigation found the
  `last_routing_family` loss (unaffected by §2.41's stated "sub-floor discard" rationale, since it
  covers the *winning*-route case) is the dominant contributor to AGENCY's full zero, and was
  never disclosed in this or any other divergence entry.
- `docs/parity_ledger/infrastructure.yaml` INFRA-237 — `support_boundary` field already has an
  addendum from `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE` explicitly requesting the
  re-verification this ticket performs; not yet updated with the result.
- `docs/simulation_quality/eval_matrix_results.md` "AGENCY — Cross-World Design Note" (line
  579-609) — this section's own "Root cause" prose still states "All three AGENCY key events...
  are emitted only from `AdventureDecisionPhase` (`src/domains/adventure/phase.py`)" and that
  `simq_routing_test`'s AGENCY "activates... as designed" — both now **factually false**
  (the file is deleted; AGENCY no longer activates for this world at all). This is a genuine,
  material doc-staleness gap this ticket's own scope should close, beyond the dated-NOTE-block
  pattern the parent ticket used — this section needs a correcting edit, not just an added NOTE.
- Strategic/Tactical Rule (CLAUDE.md) — not directly implicated; this is a pure observability-wiring
  gap (an emitted-signal loss), not a strategy/tactics boundary violation.

## Docs Requiring Update

- `docs/guidelines/intentional_divergences.md`: §2.41's "Old Behavior"/"New Behavior" text
  currently describes only the `last_defer_reason` loss; if Plan/Implement decides the
  `last_routing_family` loss is also an intentional, accepted divergence (rather than a code bug
  to fix), §2.41 needs to be broadened to disclose it honestly — the current text would otherwise
  actively mislead a reader into thinking only `defer_with_reason` was affected.
- `docs/parity_ledger/infrastructure.yaml`: INFRA-237's `support_boundary` field explicitly asks
  for this exact re-verification ("a follow-up ticket should re-run the AGENCY calibration sweep
  referenced above against current HEAD") — needs an addendum recording this ticket's confirmed
  result (AGENCY now zero for all measured routing-capable worlds/seeds, root-caused to the
  `last_routing_family`/`last_defer_reason` property-write loss).
- `docs/simulation_quality/eval_matrix_results.md`: (a) the "AGENCY — Cross-World Design Note"
  section (line ~579-609) needs a correcting edit — its "Root cause" prose cites the deleted
  `AdventureDecisionPhase`/`phase.py` as the still-live emission mechanism and claims
  `simq_routing_test`'s AGENCY "activates... as designed", both false at current HEAD; (b) a dated
  NOTE block (matching the existing 2026-08-13 COGNITION NOTE already present in the
  `simq_routing_test` section) recording this ticket's AGENCY findings for both the
  `simq_routing_test` and `hero_guild_routing` sections.
- `tests/simulation_quality/fixtures/grade_anchors.json`: AGENCY field for the 4 Finding-1 items,
  plus COGNITION+AGENCY for the 2 seed123 items (per Finding 2's confirmation this is the same
  mechanism/magnitude, not a distinct milder one) — not a docs/ path but flagged here since it is
  the primary durable-truth artifact this ticket recalibrates.
- `tests/simulation_quality/fixtures/score_ceilings.json`: the existing
  `simq_routing_test_seed123_500t`/`PROGRESSION`/`watchdog_variance` entry's `reason` field
  contains a now-false "COGNITION stable at 0.5295/52 events" aside — needs an annotation (not
  deletion), matching the precedent the parent ticket set for its own now-superseded entry.

## Parity Ledger Overlap

- `docs/parity_ledger/infrastructure.yaml` INFRA-237 (AgencyScorer coverage) — `status: verified`,
  P1, `support_boundary` field directly overlaps this ticket's scope and explicitly requests this
  re-verification (see above). Not P0, so no `test_path`-passing requirement is triggered by this
  ledger entry itself, but its own text asks for a factual update.
- `docs/parity_ledger/strategic_cognition.yaml` STRAT-185/186/187 (interruption-bypass
  generalization, `3d992dd0`) — `status: verified`, P0, already fully handled by the parent
  ticket; this ticket's own AGENCY finding does not change these entries' correctness, only
  confirms the same commit cluster is the shared context. No action needed here.
- No `docs/parity_ledger/*.yaml` entry currently documents the `last_routing_family`/
  `last_defer_reason` property-write loss itself as a parity concern (AGENCY is scored correctly
  given its inputs — `AgencyScorer`'s own unit tests, `tests/simulation_quality/
  test_agency_scorer.py`, construct synthetic envelopes directly and pass regardless of the
  emission-side gap). This is an emission/observability gap, not a scorer-logic parity divergence
  — INFRA-237 is the correct ledger entry to carry the addendum, not a new entry.

## Prior Work

- `stored_artifacts/TCK-20260811-SIMQ-COGNITION-BAND-CROSSING-DA-AND-LIFECYCLE-ANCHOR-GAP/` —
  the originating ticket; its investigation.md's "Adjacent, out-of-scope discovery" section is
  where the AGENCY drift and the `_1000t` guard staleness were first flagged (on exactly 1
  run_key at the time — this ticket's own Implement-time fresh re-verification found the same
  0/C outcome on all 4 named items, per this ticket's own Request Summary). Its plan.md's
  Decision 2 explicitly scoped both out, directing this follow-up.
- `tickets/done/TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE.md` — the actual root-cause ticket.
  Its own Deviations §5 independently found (and disclosed, not fixed) the seed123 pair's
  score-tolerance drift as "pre-existing... confirmed unrelated to this ticket's diff" via
  calibration-file mtime comparison — consistent with this investigation's own finding that the
  Aug-11 18:12 seed123 snapshot predates this ticket's Aug-11 18:59 landing.
- `docs/guidelines/intentional_divergences.md` §2.40/§2.41 — both fully read this session; §2.40
  is accurate as written, §2.41 is real but incomplete (see Mechanics/Engine Constraints above).
- `tests/unit/domains/adventure/test_delete_adventure_decision_phase_guards.py` — read in full;
  its "Guard 1" pins only the `last_defer_reason` absence, corroborating that
  `last_routing_family`'s loss was never asserted/noticed.

## Risks and Open Questions

1. **Real code gap vs. stale anchor — Plan must decide, not assume.** Unlike the parent ticket's
   COGNITION finding (where the old `decision_divergence_detected`-heavy behavior was itself a
   confirmed bug being fixed by `3d992dd0`, so the drop to 0/C is the *correct* new baseline),
   AGENCY's zero does not represent a behavior improvement — the underlying adventure-routing
   activity (route selection, deferral, action execution) still happens every tick
   (`AdventureGoalScorer.score()` is reached unconditionally, `RouteToProjectMapper` still
   materializes real projects) — only the *observability* of it was silently dropped by the
   `AdventureDecisionPhase` deletion. This ticket's own Out of Scope explicitly reserves the
   "real code gap" question for Plan/Implement to decide ("Investigate first; only Plan/Implement
   touches source if a real code gap... is confirmed"). This investigation's recommendation:
   the `last_defer_reason` loss is an already-reviewed, deliberately-`Bounded` divergence (§2.41)
   and should stay a stale-anchor recalibration; the `last_routing_family` loss (feeding 3 of 4
   AGENCY event types, covering the *winning*-route case which §2.41's own stated rationale does
   not cover) looks like an unreviewed regression, not a reviewed divergence — Plan should weigh
   whether porting a `last_routing_family`-equivalent write (e.g., threading `GoalScore.metadata`
   through `intelligence.py`'s `ADVENTURE_ROUTE` materialization branch into a
   `StrategicUpdate`/`EntityUpdate.property_updates` field) is warranted, versus recalibrating and
   deferring the fix. Either decision is defensible; this investigation does not assume which.
2. **Finding 2's "milder" framing in the ticket's own Request Summary is stale and should not be
   propagated into Plan/Implement's own artifacts.** Fresh evidence shows seed123 is the identical
   mechanism/magnitude as the 4 named items — Plan should fold seed123's COGNITION+AGENCY
   recalibration in alongside Finding 1's 4 items as one recalibration pass (all 6 run_keys, same
   cause, same evidence standard), not treat it as a separate, smaller-scope item.
3. **`hero_guild_routing_seed456_500t`'s ECONOMY/PROGRESSION drift (also beyond band/tolerance in
   the fresh committed report) is outside this ticket's own named Scope** (only AGENCY + seed123
   COGNITION/AGENCY are named). Flagged, not investigated further — Plan should explicitly decide
   whether to fold it in (same run_key already being touched, same commit-cluster timeframe,
   matching the parent ticket's own precedent for folding in same-cause discoveries) or file
   another follow-up, rather than silently leaving it untracked.
4. **This area is still under active churn.** The same 7-sibling-ticket cluster the parent
   ticket's Risk #1 named is the direct cause of both Finding 1 and Finding 2. Any
   `grade_anchors.json` write must be preceded by a fresh Implement-time confirming run, per the
   parent ticket's own Decision 1 precedent — do not copy this investigation's own snapshot values
   verbatim without a final re-check immediately before commit.
5. Whether `docs/simulation_quality/eval_matrix_results.md`'s "AGENCY — Cross-World Design Note"
   section's claims for `dungeon_crawl`/`urban_political`/`sandbox_world` (all currently
   "archetype-blocked C" because their entities are not adventure-routing-eligible, independent of
   `last_routing_family`) remain accurate is NOT re-verified here — those worlds' AGENCY=C is a
   different, still-valid mechanism (ineligibility, not emission-loss) and out of this ticket's
   own named scope. Only the section's factual claim about *how* `simq_routing_test`/
   `hero_guild_routing`'s AGENCY currently activates is stale and needs correction.

## Anti-Drift Hazards

- **Do not extend `watchdog_variance` to any of these 6 `(run_key, {AGENCY, COGNITION})` pairs** —
  same reasoning as the parent ticket's Decision 3: this is a deterministic, directly-bisected
  step-change (0/0/0 event counts across every trial sampled, no load sensitivity observed), not
  F6 jitter.
- **Do not fix `src/domains/adventure/`, `src/ai/goals/adventure_scorer.py`, or
  `src/systems/strategic_systems/intelligence.py` during Investigate** (already respected — no
  source edits made this session) — and Plan should treat "port `last_routing_family` emission" as
  a deliberate, reviewed decision requiring its own explicit sign-off, not a reflexive fix, given
  the area's active-churn history and this ticket's own Out of Scope guardrail.
- `tests/simulation_quality/test_agency_scorer.py`'s unit tests (including
  `TestDefer`/`test_scorer_handles_defer_with_reason_event`, `TestNewEventTypes`) construct
  synthetic `ObservabilityEventEnvelope`s directly and bypass `event_extractor.py`/
  `event_shapers.py` entirely — they will keep passing regardless of whether the emission-side gap
  is fixed or recalibrated-around. They are **not** a regression signal for this ticket's change
  and must not be mistaken for coverage of the actual emission wiring.
- Do not touch `SCORE_TOLERANCE_OVERRIDES` (`tests/simulation_quality/test_grade_regression.py:90`)
  — none of the 6 named run_keys/pillars appear there (confirmed by direct read); a
  `grade_anchors.json`-only point-edit is the correct shape, following the parent ticket's own
  established pattern.
- Do not widen this ticket to re-verify every other `SLOW_ANCHOR_KEYS`/`FAST_ANCHOR_KEYS` entry for
  the same root cause — only the 6 named `_500t` run_keys and the 2 named `_1000t` guard tests are
  in scope; `hero_guild_routing_seed456_500t`'s ECONOMY/PROGRESSION drift (Risk #3) is a real,
  flagged, but out-of-named-scope discovery requiring its own explicit Plan decision, not silent
  scope creep in either direction.
- The `_1000t` guard tests' correct target shape (per the `_500t` sibling's own precedent) is
  **not necessarily** a strict bit-identical (2a) conversion — the `_500t` sibling itself was
  *reverted* from a proposed 2a conversion back to a tolerance-guard (2b) shape after a rare
  residual (1/18 trials, `event_count=2, grade=B`) was found under induced load. This session's
  6/6-trial 1000t repro found no such residual, but sampled fewer trials under less load stress
  than the `_500t` sibling's own bisection did — Plan/Implement should weigh doing an
  induced-load trial (matching the `_500t` sibling's own `_busy_loop` mechanism) before committing
  to a strict 2a shape for the `_1000t` tests, rather than assuming the `_500t` sibling's own
  residual-variance finding doesn't apply here too.
