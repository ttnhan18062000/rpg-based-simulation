---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION
artifact_type: investigation
tags: [simulation-quality, information, social, grade-thresholds, calibration, feature-flags]
---

# Investigation — TCK-20260829-SELFMODEL-PROBE-GRADE-ANCHOR-DRIFT-INVESTIGATION

## Context-Search Note

Per Step 0c: `mcp__knowledge-search__search_docs` was called first with the ticket's exact query
and returned `{"error": "index not found"}` — the same failure mode already documented by
`stored_artifacts/TCK-20260827-SEMANTIC-INDEX-PARTIAL-BUILD/investigation.md` for this worktree.
The fallback `python3 tools/knowledge_search.py query ... --top-k 5` was then tried and returned
`knowledge index not found — run make knowledge-index`, the same documented failure. Per the
orchestrator's explicit instruction, neither is a blocker; the index was not rebuilt (out of
scope), and investigation proceeded to `graphify query` (both required queries ran successfully,
confirmed working in this worktree — `graphify-out/` is built) and then to source reads.
`graphify query "SelfModelUpdatePhase Knowledge Assimilation"` (117 nodes) confirmed
`SelfModelUpdatePhase`/`KnowledgeModelService`/`self_model_phase.py` as the primary cognition-side
targets; `graphify query "CooperationPhase SOCIAL scorer"` (186 nodes) confirmed
`CooperationPhase`/`SocialScorer`/`src/domains/cooperation/*` as the primary SOCIAL-side targets —
both used as the basis for the follow-up file reads below.

## Current Behavior

### Fresh pytest re-run (this exact HEAD, `.venv/bin/python3 -m pytest
tests/simulation_quality/test_grade_regression.py::test_urban_political_selfmodel_cognition_isolated_grade_anchor
tests/simulation_quality/test_grade_regression.py::test_urban_political_selfmodel_execution_isolated_grade_anchor -v`)

Both tests still **FAIL**, but the fresh numbers differ materially from both the filing ticket's
and `TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION`'s prior figures — this is reported
honestly below, not assumed unchanged.

**`test_urban_political_selfmodel_cognition_isolated_grade_anchor`** (run_key
`urban_political_selfmodel_probe_seed42_200t`) fails on the test's own hard-coded structural
assert, before it ever reaches the band/score-tolerance checks:
```
assert pillars["INFORMATION"]["grade"] == "C"
AssertionError: assert 'B' == 'C'
```
Reading `data/calibration/urban_political_selfmodel_probe_seed42_200t/quality_report.json`
directly (report mtime 2026-08-30 01:55, gitignored/transient — see "Report freshness" below):
- `INFORMATION`: `grade=B`, `normalized_score=0.2`, `event_count=1` (anchor: `C`/`0.0`/`0`) — same
  drift direction as previously reported.
- `SOCIAL`: `grade=S`, `normalized_score=12.625`, `event_count=970`, `negative_count=271` (anchor:
  `S`/`17.895`). `|12.625-17.895|=5.27` > `max(0.05, 0.2×17.895)=3.579` — **also outside score
  tolerance**, confirmed by direct calculation, but the test never reaches this check because the
  earlier `INFORMATION` hard assert raises first. This is a real gap in this test's own structure
  (see Anti-Drift Hazards) — SOCIAL's drift on this run key is real but currently invisible to
  pytest's output.

**`test_urban_political_selfmodel_execution_isolated_grade_anchor`** (run_key
`urban_political_selfmodel_execution_probe_seed42_200t`) fails on `score_failures`, band check
passes:
```
COMBAT: actual_score=1.67 outside tolerance of anchor_score=0.7839... [known tick_budget ceiling]
ECONOMY: actual_score=0.1644 outside tolerance of anchor_score=0.0 [known tick_budget ceiling]
PROGRESSION: actual_score=0.399 outside tolerance of anchor_score=-0.1569 [known tick_budget ceiling]
```
`SOCIAL` and `INFORMATION` are **not** in this fresh run's `score_failures` list. Direct read of
`data/calibration/urban_political_selfmodel_execution_probe_seed42_200t/quality_report.json`
(mtime 2026-08-30 01:57): `INFORMATION` grade=B/0.2/event_count=1 — **exact match** to anchor
(`B`/`0.2`). `SOCIAL`: grade=S, `normalized_score=13.87`, `event_count=1061`,
`negative_count=294` — anchor `S`/`16.815`; `|13.87-16.815|=2.945` ≤ `max(0.05, 0.2×16.815)=3.363`
— **within tolerance**, by a margin of only 0.42.

**This is the ticket's first required finding and it is a real, material correction to the
premise**: on this exact HEAD, right now, `SOCIAL` drift on the `_execution_probe` run key does
**not** reproduce beyond tolerance — contrary to both the filing ticket's trial (`13.35` vs
`16.815`, outside tolerance by 0.087) and `TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION`'s
independent re-confirmation (also `13.35`, both citing this as "confirmed... deterministic, not
stale-data noise"). My fresh run gives `13.87`, not `13.35`, and the two probe legs — which
historically gave *byte-identical* `SOCIAL=13.35` on both runs — now disagree with each other
(`12.625` vs `13.87`). See "Report freshness" and Risks/Open Questions for why this number is not
stable and should not be over-trusted on its own.

### Report freshness — why these numbers moved

`data/calibration/` is gitignored (transient, regenerated by `calibrate_simq.py`/`evaluate_simq.py`
— see `.gitignore:240`). Both quality_report.json files used above have today's mtime
(2026-08-30 01:55/01:57), i.e. they were regenerated very recently in this same worktree — most
likely a side effect of the concurrent `TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE`
session's own broad corpus re-run (its own commits are the immediately-preceding history on this
branch). `grade_anchors.json`'s committed values for both `urban_political_selfmodel*_probe`
run keys are unchanged from the filing ticket's figures (confirmed by direct read) — only the
*calibration reports* being compared against them are fresher than the 2026-08-26 trial evidence.

Between the 2026-08-26 trial (`SOCIAL=13.35`, both legs identical) and this fresh run
(`SOCIAL=12.625`/`13.87`, legs now diverge), 5 commits landed touching shared/upstream code paths
(`git log --since=2026-08-26 --oneline -- src/`):
`446d4226` (`TCK-20260829-HOTFIX-WOUND-SCAR-EVENT-EXTRACTOR-TUPLE-BLIND`, fixes `event_extractor.py`
wound/scar diffing so `wound_sustained` now actually reaches the event layer for the first time
through any real Kernel run), `9e05c3c6` (occupation-change trigger), `704c14a6` (lead
contradiction wiring), `6eba9931` (grief/nemesis reachability), `fa1dc125` (causal memory route
scoring). None of these touch `src/domains/cooperation/` or `src/simulation_quality/scorers/social.py`
directly, but several touch entity self-assessment/decision inputs
(`SelfAssessmentService`/`HelpNeedEvaluator` read `entity.combat.wounds`/needs) that
`SelfModelUpdatePhase`'s own dirty-check (`self_model_phase.py:148-154`) and
`CooperationPhase.execute()`'s help-need evaluation both consume — a plausible, not fully isolated,
mechanism for why identical-seed runs now diverge deterministically between the two probe legs
(the two legs enable different upstream flags — `ENABLE_BELIEF_ASSIMILATION`,
`ENABLE_INFORMATION_INTENT_EXECUTION` — so any wound/need-input change that alters even one
early-tick decision cascades differently once the two legs' downstream state has already diverged
for other reasons). This causal chain was not isolated further within this ticket's scope; see
Risks and Open Questions.

### INFORMATION drift — code path (unchanged conclusion from the filing ticket, re-confirmed)

`src/cognition/self_model_phase.py:32-74` (`SelfModelUpdatePhase.apply()`) groups
`state.pending_self_model_information_events` by `actor_id` (line 46) and calls
`SelfModelUpdatePhase.run()` (line 57) for every active/alive entity. `apply()` itself is gated
only by `ENABLE_SELF_MODEL_COGNITION` — the sole gate is `src/engine/pipeline.py:164`:
```
update = run_phase("self_model", update, lambda u: SelfModelUpdatePhase.apply(state, u), "ENABLE_SELF_MODEL_COGNITION")
```
Inside `run()`, Step 1 "Knowledge Assimilation" (`self_model_phase.py:103-141`) iterates `events`
and, for any event with an `answer_kind` attribute, calls `KnowledgeModelService.assimilate()`
(`src/cognition/knowledge_model.py:42-130`) unconditionally — there is **no** reference to
`ENABLE_BELIEF_ASSIMILATION` anywhere in `self_model_phase.py` or `knowledge_model.py`
(`grep -rn "ENABLE_BELIEF_ASSIMILATION" src/` returns exactly one call site,
`src/engine/pipeline.py:173`, gating the wholly separate `InformationBeliefPhase`
(`src/domains/information/phase.py`), not `SelfModelUpdatePhase`). Both
`urban_political_selfmodel_probe`/`urban_political.yaml`-derived worlds seed exactly one
`pending_self_model_information_events` entry (`data/worlds/urban_political/world.yaml`, the
`bandit_road_danger` fact for actor 22, tick 1) — this is the sole source of the drift, and it
fires whenever `ENABLE_SELF_MODEL_COGNITION` is ON, regardless of `ENABLE_BELIEF_ASSIMILATION`.

### SOCIAL drift — code path (new finding, this ticket's own mission #2)

`SOCIAL`'s drift is **not** produced by `SelfModelUpdatePhase`/`ENABLE_BELIEF_ASSIMILATION` at
all — a structurally different mechanism from `INFORMATION`. Trace:

1. `src/simulation_quality/scorers/social.py:19-33` — `SocialScorer.EVENT_TYPES` includes
   `cooperation_event` and `contract_expired_offer` among others.
2. `src/domains/cooperation/phase.py:34-141` (`CooperationPhase.execute()`) is gated by
   `ENABLE_SOCIAL_COOPERATION` (`src/engine/pipeline.py:189`) — both probe profiles
   (`config/simulation_quality/profiles/urban_political_selfmodel_probe.yaml:24`,
   `.../urban_political_selfmodel_execution_probe.yaml:20`) set `ENABLE_SOCIAL_COOPERATION: "ON"`
   explicitly and have done so since each profile's original authorship (TCK-20260712/
   TCK-20260713) — this predates the `TCK-20260824-ROLLOUT-FLAG-DECISIONS` global default flip, so
   (unlike the 61 `FAST_ANCHOR_KEYS` combos documented in `docs/testing/regression_policy.md`
   §9-10) the "dormant → live" flag-flip narrative does **not** directly explain these 2 run keys'
   drift — cooperation was already live when their anchors (`S/17.895`, `S/16.815`) were set.
3. `CooperationPhase.execute()` sets `entity.timeline`/`property_updates["last_cooperation_decision"]`
   every evaluated tick (`phase.py:138-139`); `src/observability/event_extractor.py:668-676` and
   `src/observability/event_shapers.py:820-827` both emit `cooperation_event` whenever that
   property `is not None` — any truthy posture value qualifies, so this fires broadly whenever
   `CooperationPhase` evaluates an entity.
4. `SocialScorer.score()` weights `cooperation_active` at **+4.0** and `offer_dead`
   (`contract_expired_offer`) at **-1.0** (`config/simulation_quality/scoring_weights.yaml:108,116`).
   Both fresh reports show large negative-event fractions: cognition-isolated run
   `event_count=970`/`negative_count=271` (28%), execution-isolated run
   `event_count=1061`/`negative_count=294` (28%) — `worst_events` in both reports is dominated by
   repeated `contract_expired_offer`/`offer_dead` entries for the same handful of entity IDs across
   consecutive ticks (e.g. entities 9/14/17/23/24 repeating at ticks 142/143/144 in the
   execution-probe report).
5. This exact pattern — the same entity re-proposing and expiring a cooperation offer on
   immediately-consecutive ticks with no cooldown — is **already independently discovered and
   ticketed**: `tickets/todos/TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING.md`, filed
   today by the sibling `TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE` ticket for
   `highland_traverse_seed42_200t` ("the same entity fires `contract_expired_offer` on 20-23
   literally consecutive ticks... `src/domains/cooperation/phase.py`/`services.py` has no cooldown
   or backoff after a cooperation offer expires unaccepted"). The root code gap it names —
   `src/domains/cooperation/phase.py`/`services.py` lacking a retry cooldown — is the same
   mechanism dragging `SOCIAL` down on both `urban_political_selfmodel*_probe` run keys; it is not
   specific to `highland_traverse`.

## Mechanics / Engine Constraints

- `docs/mechanics/04_strategic_cognition.md` covers goal hierarchy, interruption resistance,
  knowledge management, and perception — the Mechanics Bible chapter that would need to state (if
  it does not already) that self-model knowledge assimilation is gated solely by
  `ENABLE_SELF_MODEL_COGNITION` and is independent of `ENABLE_BELIEF_ASSIMILATION`/
  `InformationBeliefPhase`. Not checked line-by-line against this specific claim in this
  investigation (out of the code-level tracing this ticket scoped) — flagged as an open question
  in Risks below rather than asserted as covered or uncovered.
- Party/group cooperation being "purpose-driven, not just proximity clustering" is `SOC-007`
  (`docs/parity_ledger/social_narrative.yaml:79-90`, status `verified`) — unaffected by this
  investigation's findings; the retry-cooldown gap is a tuning/throttling absence, not a violation
  of SOC-007's purpose-driven-cooperation law.
- No engine contract in `docs/engine/` explicitly governs offer-retry cadence/cooldown for
  cooperation proposals — `docs/engine/known_limitations.md` was not found to reference this gap
  (checked via `grep`; if it should, that is `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING`'s
  scope, not this ticket's).

## Docs Requiring Update

- `docs/architecture/rollout_flag_decisions_m1.md`: the "ENABLE_SELF_MODEL_COGNITION — Validation
  Trial Result" section's Honest Gap language should be updated once this ticket's root-cause
  determination (below) is accepted and acted on — currently it says `SOCIAL`'s drift "was not
  traced further"; that is no longer true after this investigation.

The following were considered and explicitly excluded from Format 1 (nothing to add there beyond
the one bullet above):

`docs/mechanics/04_strategic_cognition.md` was considered (self-model knowledge assimilation
gating is arguably a mechanics-bible-level fact) but is not listed as required here: this
investigation traces the *code* gating precisely but did not cross-check whether the chapter
already documents the `ENABLE_SELF_MODEL_COGNITION`/`ENABLE_BELIEF_ASSIMILATION` independence
claim or is silent on it — that check belongs to whichever ticket actually implements the fix/
re-anchor decision (this ticket is investigation-only per its Tier/Scope), not asserted here
without having read the chapter against this specific claim.

`docs/parity_ledger/strategic_cognition.yaml`'s `INFRA-259` entry (`pending_self_model_information_events`
compile-time plumbing) already documents the mechanism accurately as-is (confirmed by direct read,
see Parity Ledger Overlap below) — no update needed from this investigation's findings; it does not
claim `ENABLE_BELIEF_ASSIMILATION` gates this path, so there is nothing in it to correct.

`docs/testing/regression_policy.md` already carries a directly-analogous worked example (§9-10,
the M1 batch `FAST_ANCHOR_KEYS` re-baseline) covering the same class of drift and the same
retry-cooldown anti-pattern discovery method — it does not need a *new* pattern added by this
ticket, only (if the implementing ticket re-anchors) a short cross-reference addition, which is an
implementation-time judgment call, not asserted as required here.

## Parity Ledger Overlap

- `INFRA-259` (`docs/parity_ledger/strategic_cognition.yaml:3579-3608`, status `verified`,
  priority `P1`): documents the `pending_self_model_information_events` compile-time-seed
  mechanism and `SelfModelUpdatePhase.apply()`'s events grouping exactly as this investigation
  traced it. Text is accurate as-is; not implicated by the drift (the mechanism works as
  documented — the anchors, not the mechanism, are stale).
- No `docs/parity_ledger/social_narrative.yaml` entry documents `cooperation_event`/
  `contract_expired_offer` scoring or a retry-cooldown expectation specifically — `SOC-007`
  (purpose-driven cooperation) and the contract-related entries found (`SOC-062`, `SOC-143`) are
  adjacent but do not cover offer-retry cadence. No entry needs a status change from this
  investigation; a parity ledger addition, if warranted, belongs to
  `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING`'s own scope (its Related Code Areas
  already include `src/simulation_quality/scorers/social.py`).
- No P0 entries are implicated by either drift.

## Prior Work

- `stored_artifacts/TCK-20260826-SELF-MODEL-COGNITION-FLAG-VALIDATION/trial_evidence.md`: filed
  this ticket; traced INFORMATION's cause, left SOCIAL untraced, both legs' `SOCIAL` were
  byte-identical at `13.35` in that trial.
- `tickets/done/TCK-20260826-INFORMATION-INTENT-EXECUTION-FLAG-VALIDATION.md`: independently
  reproduced `SOCIAL=13.35` on the `_execution_probe` run key the same day (2026-08-26), called it
  "confirmed as real and deterministic, not stale-data noise" — this investigation's fresh run
  (`13.87`, 4 days later) shows that characterization does not hold under a later re-run; see
  Report Freshness above. That ticket's own INFORMATION cross-check (exact match to anchor B/0.2)
  matches what this investigation also finds unchanged.
- `docs/testing/regression_policy.md` §9-10: directly analogous precedent — the M1 batch flag-flip
  rebaseline, including the exact retry-cooldown anti-pattern discovery method this investigation
  reused (reading `worst_events` for a same-entity-repeating-on-consecutive-ticks signature).
- `tickets/todos/TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING.md`: independently
  discovered, today, the exact code-level root cause this investigation traces for `SOCIAL` —
  scoped to `highland_traverse_seed42_200t` only; this investigation's Blast Radius section below
  extends that finding to the 2 run keys in this ticket's own scope.
- `stored_artifacts/TCK-20260830-M1-BATCH-CORPUS-GRADE-ANCHOR-REBASELINE/`: the sibling rebaseline
  ticket that most likely regenerated the fresh `data/calibration/` reports this investigation read
  (see Report Freshness) and established the re-anchor-vs-fix methodology this investigation's Root
  Cause Determination follows.

## Risks and Open Questions

1. **SOCIAL's exact magnitude is not currently stable enough to re-anchor with confidence from a
   single draw.** Three independent measurements at the same nominal seed/config
   (`urban_political_selfmodel_execution_probe_seed42_200t`, `SOCIAL`) gave `13.35`, `13.35`, then
   `13.87` across three sessions four days apart, and the two probe legs (which previously matched
   exactly) now disagree with each other. This project's own memory record
   (`project_slow_regression_determinism_root_cause`) already documents a **confirmed, unfixed**
   Kernel wall-clock mid-tick throttle nondeterminism bug (`kernel.py:585-596`, fires when
   `audit_mode=False`) as a standing, deliberately-unaddressed risk ("user said let it sit"). This
   investigation did not confirm `calibrate_simq.py` runs with `audit_mode=False`, but if it does,
   that mechanism — not intervening feature commits — could fully explain the run-to-run SOCIAL
   score variance observed here. **This is a blocking open question for any re-anchor decision**:
   re-anchoring to a single fresh draw when the true score is nondeterministic risks committing
   another anchor that immediately drifts again. A multi-draw sweep (the same methodology
   `SCORE_TOLERANCE_OVERRIDES`' existing entries used, per this file's own module docstring) is
   recommended before committing new SOCIAL anchor values, not a single re-run.
2. **INFORMATION's coupling determination (see Root Cause Determination) is confident**, but the
   SOCIAL magnitude question above means this ticket cannot respond with a single clean
   re-anchor-both-pillars verdict for both run keys without either (a) accepting single-draw risk,
   or (b) running the multi-draw sweep this ticket's own time budget did not include.
3. Whether `docs/mechanics/04_strategic_cognition.md` already documents the
   `ENABLE_SELF_MODEL_COGNITION`/`ENABLE_BELIEF_ASSIMILATION` independence is unresolved — flagged
   under Docs Requiring Update rather than assumed either way.
4. Fixing `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING` (separately ticketed, not this
   ticket's scope) will itself move `SOCIAL`'s real score for both `urban_political_selfmodel*_probe`
   run keys once implemented — any re-anchor decided by this ticket's own implementation phase
   should account for whether that fix lands first (re-anchoring now risks a second drift the
   moment that fix ships) or is deliberately deferred (in which case the anchor should say so
   explicitly, matching the `highland_traverse` precedent of "deliberately left un-rebaselined and
   disclosed").

## Anti-Drift Hazards

- `test_urban_political_selfmodel_cognition_isolated_grade_anchor`'s hard-coded
  `assert pillars["INFORMATION"]["grade"] == "C"` (line 446) masks `SOCIAL`'s score-tolerance
  failure on the same run key — anyone fixing only the `INFORMATION` assert without also checking
  `SOCIAL`'s band/score tolerance will get a false "fixed" signal the moment the `INFORMATION`
  assert passes, because the function will then proceed into the band/score checks for the first
  time and may newly fail there. Any implementation ticket must re-run the full test after any
  `INFORMATION`-only fix, not just check the first assert.
- Do not conflate the `SOCIAL` root cause with `INFORMATION`'s — they are two structurally
  independent mechanisms (`SelfModelUpdatePhase`/no-flag-gate vs `CooperationPhase`/
  `ENABLE_SOCIAL_COOPERATION`-gated retry-spam). A fix or re-anchor for one says nothing about the
  other; do not assume a shared cause or a shared fix.
- Do not silently re-anchor `SOCIAL` to a single fresh draw given the nondeterminism risk in Risks
  item 1 — that is exactly the kind of "loosened without evidence" re-anchor the ticket's own
  Acceptance Criteria forbid.
- The `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING` ticket is explicitly scoped to
  `highland_traverse_seed42_200t` only ("Out of Scope: Re-litigating any other run_key's anchor
  value"). If that ticket's fix lands first, whoever re-anchors `SOCIAL` for these two
  `urban_political_selfmodel*_probe` run keys should re-verify against the *post-fix* behavior, not
  the pre-fix numbers this investigation recorded — otherwise the new anchor will itself already be
  stale on arrival.

## Root Cause Determination

**INFORMATION (confidence: high).** `SelfModelUpdatePhase.run()`'s Step 1 Knowledge Assimilation
(`self_model_phase.py:103-141`) has never, in its entire git history, referenced
`ENABLE_BELIEF_ASSIMILATION` — `git log --oneline -- src/cognition/self_model_phase.py` shows only
2 commits total (`6fe08820`, original authorship 2026-05-30; `29d78798`, a later simulation-quality
pass that did not touch lines 100-145 per `git blame`). `ENABLE_BELIEF_ASSIMILATION`'s sole live
call site (`pipeline.py:173`) has always gated a structurally separate phase
(`InformationBeliefPhase`). There is no evidence anywhere in history that these two flags were ever
wired together and later un-wired — the coupling the `INFORMATION=C/0.0` anchor assumed simply
never existed in the code. This is **(a) intended coupling** — or more precisely, the anchor's own
assumption was wrong from the start, not a regression from a later code change. Recommendation:
**re-anchor `INFORMATION` for `urban_political_selfmodel_probe_seed42_200t`** to `B/0.2` (matches
both this fresh run and the 2026-08-26 trial, byte-identical twice) with `event_count=1` — this
number has been stable across every measurement this investigation and its predecessors took,
unlike `SOCIAL`. `urban_political_selfmodel_execution_probe_seed42_200t`'s `INFORMATION` anchor
(`B/0.2`) already matches and needs no change.

**SOCIAL (confidence: moderate — root mechanism is high-confidence, exact re-anchor value is not
yet trustworthy).** SOCIAL's drift is driven by `CooperationPhase`'s cooperation-offer
retry-without-cooldown gap (`src/domains/cooperation/phase.py`/`services.py`), the same mechanism
`TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING` already ticketed for `highland_traverse`,
compounded by the fact that this drift is **not gated by any single flag flip this ticket can
point to** — `ENABLE_SOCIAL_COOPERATION` was already ON in both probe profiles at anchor-setting
time, unlike the 61 `FAST_ANCHOR_KEYS` combos in `regression_policy.md` §9-10 whose drift traces
cleanly to the 2026-08-24 global default flip. This makes SOCIAL's classification genuinely mixed,
not cleanly "(a) re-anchor" or "(b) fix a regression" in the ticket's own binary framing: it is
**neither** an unintended regression in `self_model_phase.py`'s gating (that code is unrelated to
SOCIAL entirely) **nor** a clean flag-flip-caused magnitude shift ready to re-anchor as-is — it is
a real, already-disclosed tuning gap in a different subsystem (`CooperationPhase`) whose fix is
already ticketed separately. Recommendation: **do not re-anchor `SOCIAL` for either run key in this
ticket** until either (a) `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING` lands and SOCIAL
is re-measured post-fix, or (b) a deliberate decision is made to re-anchor pre-fix with an explicit
disclosure note (matching the `highland_traverse` precedent's "deliberately left un-rebaselined and
disclosed" language) — and even then, only after a multi-draw sweep addresses Risks item 1's
nondeterminism concern, not a single fresh draw.

## Blast Radius

- **INFORMATION mechanism**: only 2 source `data/worlds/*/world.yaml` specs seed a non-empty
  `pending_self_model_information_events` entry: `unit_selfmodel_pilot/world.yaml` and
  `urban_political/world.yaml` (confirmed by iterating every `data/worlds/*/world.yaml` and
  counting entries — all other `pending_self_model_information_events` matches found by grep were
  either `resolved/world.resolved.yaml` derivatives carrying through the schema's empty default,
  or unrelated code/doc/test references). `unit_selfmodel_pilot`'s calibration profile
  (`config/simulation_quality/profiles/unit_selfmodel_pilot.yaml`) also sets
  `ENABLE_SELF_MODEL_COGNITION: "ON"`, so it shares the structural precondition — but its own
  existing on-disk calibration reports (`unit_selfmodel_pilot_seed{42,123,456}_200t/quality_report.json`)
  currently show `INFORMATION` grade `C`/score `0.0`/`event_count=0`, matching their committed
  anchors exactly, **not** drifted. (These reports' freshness was not independently re-verified —
  re-running `unit_selfmodel_pilot`'s calibration is explicitly Out of Scope for this ticket per
  the filing ticket's own scope guard.) **Conclusion: INFORMATION's drift is isolated to the 2
  `urban_political_selfmodel*_probe` run keys in this ticket's scope; it does not currently extend
  to `unit_selfmodel_pilot`'s 3 anchored run keys**, based on existing evidence.
- **SOCIAL/cooperation-retry-cooldown mechanism**: structurally much wider. Any world/profile with
  `ENABLE_SOCIAL_COOPERATION: "ON"` and cooperation offers actually occurring is exposed to the
  same missing-cooldown gap — this includes, at minimum, every profile grepped with that flag ON
  (`frontier_living_world`, `highland_traverse`, `lifecycle_full_coverage_world`, `urban_political`,
  and both `urban_political_selfmodel*_probe` profiles investigated here) plus any world inheriting
  the now-ON global default. `TCK-20260830-COOPERATION-OFFER-RETRY-COOLDOWN-MISSING` already
  disclosed one instance (`highland_traverse_seed42_200t`) and is explicitly scoped to that one run
  key only; this investigation adds two more known-affected run keys
  (`urban_political_selfmodel_probe_seed42_200t`, `urban_political_selfmodel_execution_probe_seed42_200t`)
  to the same underlying bug's blast radius, though neither is in that ticket's own stated scope.
  Whether other `FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` run keys are also silently affected (i.e.
  passing their score-tolerance check today only because their retry-spam volume happens to still
  fall inside the tolerance band) was not swept in this investigation — out of this ticket's time
  budget; flagged as a residual unknown, not asserted clear.
