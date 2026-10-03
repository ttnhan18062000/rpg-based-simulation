---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5
artifact_type: investigation
tags: [adventure, agency, strategy, cognition]
---

# Investigation — TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5

## Current Behavior

### The normalization chain, re-verified against current HEAD

`AdventureGoalScorer.score()` (`src/ai/goals/adventure_scorer.py:210`, current line confirmed by
direct read):

```python
utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) * _GOAL_UTILITY_SCORE_MAX
```

where `_ADVENTURE_ROUTE_SCORE_MAX: float = 2.9` and `_GOAL_UTILITY_SCORE_MAX: float = 100.0`
(`src/systems/strategic_systems/intelligence.py:32,47`). `raw_score` is `selected.score`, the
output of `AdventureRouteScorer.score()` (`src/domains/adventure/scoring.py:39-381`), an additive
formula:

```
score = urgency + benefit + personality_bias + plan_advance_bonus + memory_adjustment
        + confidence_bonus − risk_penalty − blocker_penalty
score = max(0.0, score)
```

### `_ADVENTURE_ROUTE_SCORE_MAX`'s real provenance (git history, not assumed)

```
git log -p --follow -S "_ADVENTURE_ROUTE_SCORE_MAX: float = 2.9" -- src/systems/strategic_systems/intelligence.py
```
shows the constant was introduced in commit `3d992dd0` (2026-08-11,
`TCK-20260810-COGNITION-PROFILE-ADVENTURE-ELIGIBILITY, TCK-20260810-PROJECT-SWITCH-BYPASS-
GENERALIZATION, TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS, TCK-20260810-D22-DORMANT-WIRING-
AUDIT`), for `_score_scale_max()`'s **Generalized Bypass gate** purpose — normalizing an
already-committed `ProjectState.score` as a percentage of its own system's declared max, for the
`evaluate_project_switch()` lock-bypass/retention-margin comparison (`intelligence.py:1062-1069`,
`tests/unit/strategic/test_score_normalization.py`, STRAT-186). At this commit, **no tier-5
`GoalScore.utility` computation existed for adventure routing at all** — `AdventureDecisionPhase`
still ran as the unconditional standalone phase (pre-`TCK-20260811-DELETE-ADVENTURE-DECISION-
PHASE`), never competing against other `GoalKind`s.

`git log --oneline -S "_score_scale_max"` shows the very next relevant commits, same day/period:
```
846d53de TCK-20260811-ADVENTURE-GOAL-SCORER: add AdventureGoalScorer as a new tier-5 strategic candidate
2bc3ea26 TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER: generalize GoalScorer-wrapper pattern to social-contract acceptance
3e69174b TCK-20260811-REGION-STABILIZATION-GOAL-SCORER: generalize GoalScorer-wrapper pattern to region stabilization
```
`846d53de` (`TCK-20260811-ADVENTURE-GOAL-SCORER`) is the commit that **first** introduces
`utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) * _GOAL_UTILITY_SCORE_MAX` — it **reuses** the
already-declared constant from `3d992dd0` for a new, different purpose (tier-5 competitive
normalization against `COMBAT_ENGAGE` and every other `GoalKind` scorer) rather than deriving a
fresh denominator calibrated for that specific purpose. `2bc3ea26` and `3e69174b` then each
independently, deliberately reuse the same constant a second and third time (confirmed by their own
code comments, see below).

**Direct answer to the ticket's Question #4**: `2.9` was **not** primarily `RegionStabilization`'s
or `SocialContract`'s constant retrofitted onto adventure — chronologically and textually the
opposite is true. The constant's declared value traces to `AdventureRouteScorer.score()`'s own
formula, per `docs/mechanics/04_strategic_cognition.md` §6.6 ("Total non-blocked: 0.0 to ~2.9"),
cited directly in the constant's own code comment (`intelligence.py:28-31`: "Source:
docs/mechanics/04_strategic_cognition.md §6.6"). `RegionStabilizationGoalScorer`
(`src/ai/goals/region_stabilization_scorer.py:60`, comment: "Recalibrated to the SAME 0-2.9 ceiling
ADVENTURE_ROUTE/SOCIAL_CONTRACT already share") and `SocialContractGoalScorer`
(`src/ai/goals/social_contract_scorer.py:84`, comment: "Calibrated to the SAME 0-2.9 ceiling
`_ADVENTURE_ROUTE_SCORE_MAX` already declares") are both the **later** retrofits — both landed
after `846d53de`, both explicitly cite reusing adventure's pre-existing ceiling. This is also
recorded in `docs/parity_ledger/strategic_cognition.yaml` STRAT-254/STRAT-255.

However — and this is the actual defect — **`2.9`'s own basis (§6.6) is itself an untested
theoretical estimate that was never re-validated against the constant's new tier-5-competition use
when `846d53de` reused it**, and that estimate silently assumed a live input
(`faction_directives`) that was severed by a closely-timed sibling change. See next section.

### §6.6's own theoretical estimate depends on an input that is hardcoded to `None` in the live tier-5 path

`docs/mechanics/04_strategic_cognition.md` §6.6 "Score Range Summary (Estimated, No Blockers)"
sums `urgency(~2.0) + benefit(~0.5) + personality_bias(0.25) + confidence_bonus(0.15) −
risk_penalty(0) ≈ 2.9`. The `~2.0` urgency figure is only reachable via §6.10's faction-directive
urgency boosts (`scoring.py:136-153`: `+2.0` GUARD/DEFEND_BORDER, `+1.5` SHOPKEEPER/allied-trade,
`+3.0` HERO/COMMISSION_QUEST), since the needs-based baseline (`InterpretedNeed.urgency`,
`src/core/self_model.py:33`: `"0.0 (low) … 1.0 (critical)"`, and
`src/cognition/need_interpretation.py:31-34`: `_URGENCY_CRITICAL=0.95`, `_URGENCY_HIGH=0.75`,
`_URGENCY_MEDIUM=0.50`, `_URGENCY_LOW=0.25`) never exceeds `0.95` on its own.

Doc §6.10 itself already discloses (re-confirmed by direct read this session, unchanged) that
`faction_directives` is **not threaded into the live path**: `AdventureGoalScorer.score()`
(`adventure_scorer.py:127-134`) calls `AdventureDecisionService.decide(..., faction_directives=None,
...)` unconditionally — "a disclosed simplification, not implemented parity" — because
`GoalScorer.score(entity, state)`'s signature carries no `state.faction_directives` attribute, unlike
the deleted phase's `apply(state, context, trace_writer, faction_directives, factions)` signature,
which received it as a real per-tick pipeline artifact from `FactionDecisionPhase.execute()`
(confirmed via `git show 1825f914^:src/domains/adventure/phase.py`, which passed a live
`faction_directives` argument through to `decide()`). **What §6.10 discloses as a call-signature
simplification, no one previously connected to its downstream effect on `_ADVENTURE_ROUTE_SCORE_MAX`'s
own validity as a normalization denominator** — this investigation is the first to trace that
connection end-to-end.

Also confirmed by direct read: neither the deleted `AdventureDecisionPhase.apply()` (pre-deletion
source) nor the live `AdventureGoalScorer.score()` ever passes `group`/`progression_plan` into
`decide()`/`score()` — `plan_advance_bonus` (max 1.5), the SOC-229 class-synergy multipliers
(`×1.15`/`×1.10`), and the SOC-230 escort bonus (`+3.0`) have **never** been live in production,
in either architecture. This is unrelated to the `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE`
migration and not a new finding caused by it — noted here only so Plan does not mistake these terms
as part of the regression.

### The real, live-reachable ceiling, computed term-by-term from actual opportunity-generation code

With `faction_directives=None`/`group=None`/`progression_plan=None` (the only configuration this
scorer has ever run under in production), the achievable per-route ceiling is measurably lower than
2.9. Concrete opportunity data, read directly from the two live providers:

- `src/world/providers/resources.py:74-75`: `reward = 50.0 if is_needed else 10.0`, scaled by
  `(0.5 + 0.5 × depletion_mult) ∈ [0.5, 1.0]` → `expected_benefit` (`= reward/100.0`,
  `generator.py:84`) tops out at **0.5** for `GATHER_RESOURCE`, `estimated_risk` fixed at `0.1`.
- `src/world/providers/services.py`: `estimated_reward` values of `90.0` (CRAFT_UPGRADE with an
  active material blocker), `80.0` (RECOVER/repair_gear), `70.0` (ASK_INFORMATION with a material
  blocker), `10.0`/`40.0` (BUY_UPGRADE), `sleep_debt` (RECOVER/rest_inn) — all with
  `estimated_risk=0.0`. Highest live `expected_benefit` is **0.9** (CRAFT_UPGRADE, material blocker
  case) → `risk_penalty = 0`.
- `generator.py:105,119`: structural-default routes cap `expected_benefit` at **0.8** (forced
  RECOVER) / **0.6** (forced ASK_INFORMATION), both with `expected_risk` at `0.0`/`0.1`.

Taking the single most favorable live-reachable route (CRAFT_UPGRADE, material blocker,
`gear_quality < 0.25`): `urgency(0.75, _URGENCY_HIGH) + benefit(0.9) + personality_bias(0.25,
industry=1.0 max) + confidence_bonus(0.15) − risk_penalty(0) − blocker_penalty(0) = 2.05`. RECOVER
(repair_gear): `urgency(≤0.95) + benefit(0.8) + personality_bias(0.25, caution max) +
confidence_bonus(0.15) − 0 = up to ~2.15`. **No live-reachable route configuration reaches
`_ADVENTURE_ROUTE_SCORE_MAX = 2.9`** — the honest live ceiling sits around **2.0–2.2**, roughly
25–30% below the declared normalization denominator, before even accounting for typical (not
maximal) conditions.

This is consistent with, and now mechanistically explains, the sibling ticket's DEBUG-trace
observation (`stored_artifacts/TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE/plan.md`
Deviations §2): `ADVENTURE_ROUTE` utility observed **~20-26/100** across full 500-tick runs of
`simq_routing_test`/`hero_guild_routing` — i.e. `raw_score ≈ 0.58–0.75`, well inside a realistic
(non-maximal) band under the corrected ~2.0-2.2 ceiling, not an anomalous or contradictory reading.

### Are `COMBAT_ENGAGE`/`REGION_STABILIZATION` themselves the anomaly? — checked directly, answer: no

- `CombatEngageScorer.score()` (`src/ai/goals/scorers.py:100-131`): `utility = 40.0 +
  bravery×40.0 + stamina_ratio×20.0` — computed **directly on the 0-100 scale**, no division, no
  shared constant. It floors at 40 whenever any hostile is in sensory range (`SensoryFilter.
  filter_saliency`), independent of `_ADVENTURE_ROUTE_SCORE_MAX` entirely. Nothing about its
  formula or the observed ~100-144 range implicates it in this scale-mismatch defect class.
- `RegionStabilizationGoalScorer.score()` (`region_stabilization_scorer.py:60-61`):
  `raw_score = urgency × _ADVENTURE_ROUTE_SCORE_MAX`; `utility = (raw_score /
  _ADVENTURE_ROUTE_SCORE_MAX) × _GOAL_UTILITY_SCORE_MAX`. Algebraically, `_ADVENTURE_ROUTE_SCORE_MAX`
  **cancels out**: `utility = urgency × 100`, mathematically independent of the constant's declared
  value. Its observed flat `100.0` in both calibration worlds simply means `EventInterpreter.
  compute_danger_urgency()` returns `urgency ≈ 1.0` on effectively every evaluated tick in these two
  worlds — a fact about `simq_routing_test`/`hero_guild_routing`'s own danger density (both are
  danger-heavy, adventure-routing calibration worlds by design), not evidence of a REGION_STABILIZATION
  formula defect. **Changing `_ADVENTURE_ROUTE_SCORE_MAX` would have zero effect on
  `RegionStabilizationGoalScorer`'s output** — this is a provable, not assumed, conclusion.
- `SocialContractGoalScorer._raw_score()` (`social_contract_scorer.py:80-126`) clamps its own
  `raw_score` to `max(0.0, min(2.9, raw))` — a **hardcoded literal `2.9`**, not a reference to
  `_ADVENTURE_ROUTE_SCORE_MAX`. Its `utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) × 100`
  (line 63) **does** reference the shared constant. This is a **latent, pre-existing, separate risk**
  flagged for Plan/Implement: if `_ADVENTURE_ROUTE_SCORE_MAX` is ever lowered globally, `raw_score`
  stays clamped at up to `2.9` (the hardcoded literal) while the denominator shrinks, which would
  push `SocialContractGoalScorer`'s `utility` **above** 100 (up to `2.9/new_max × 100`) — silently
  breaking the implicit 0-100 `GoalScore.utility` contract for a scorer this ticket's own Scope
  explicitly says must not be touched. This is a strong, independent argument against a global
  rescale of the shared constant (see Recommended Direction below) and is not observed in production
  today only because `_ADVENTURE_ROUTE_SCORE_MAX` has never been changed.
- `ResolveBlockerScorer.score()` (`scorers.py:189-222`): flat `utility = 80.0` whenever any
  unresolved blocker exists — independent of `_ADVENTURE_ROUTE_SCORE_MAX`. The sibling ticket's own
  DEBUG trace shows this wins 57/371 and 86/335 tier-5 decisions in the two worlds — a real,
  structurally correct competitor unrelated to this defect, but relevant to whether a corrected
  `ADVENTURE_ROUTE` ceiling would flip the outcome on the ticks it currently wins (see Risks below).

**Conclusion on Scope's second bullet**: `COMBAT_ENGAGE` and `REGION_STABILIZATION` are not the
anomaly. `REGION_STABILIZATION`'s formula is provably invariant to the shared constant;
`COMBAT_ENGAGE` never touches it. The mismatch is real, adventure-side, and specifically located in
`AdventureGoalScorer.score()`'s reuse of a denominator calibrated for a different purpose against an
input configuration (`faction_directives` live) that no longer holds.

## Mechanics / Engine Constraints

- `docs/mechanics/04_strategic_cognition.md` §6.6 "Score Range Summary (Estimated, No Blockers)" —
  the authoritative source cited by `_ADVENTURE_ROUTE_SCORE_MAX`'s own code comment
  (`intelligence.py:28-31`). Its `~2.0` urgency-term estimate implicitly assumes faction-directive
  urgency boosts are live (§6.10's own table), which is no longer true in the tier-5 competitive
  path (§6.10's own disclosure). §6.6's own text already states "This `~2.9` 'Total non-blocked'
  ceiling is also the normalization anchor... that System A candidate scores are divided by when
  evaluated against §2's Generalized Bypass gate" and separately documents the second/third/fourth
  "consumer" reuse by `AdventureGoalScorer`/`SocialContractGoalScorer`/`RegionStabilizationGoalScorer`
  — but does **not** state that the tier-5-competition consumer's own live input configuration
  differs from the Generalized Bypass gate's, or that 2.9 was never re-validated for that narrower
  configuration. This doc needs a correction regardless of which fix direction Plan chooses (see
  Docs Requiring Update).
- `docs/mechanics/04_strategic_cognition.md` §6.10 "Faction Directive Urgency Scoring (E53Ac)" —
  already discloses `faction_directives=None` in the live path as "a disclosed simplification, not
  implemented parity," but frames it only as a call-signature gap, not as a factor invalidating
  §6.6's own range estimate for the tier-5-competition consumer specifically. This connection is a
  genuine gap this investigation closes.
- `docs/guidelines/intentional_divergences.md` §2.43 "Regional-Danger Stabilization No Longer
  Unconditionally Wins the Project Slot" — the `Enforced` divergence documenting
  `RegionStabilizationGoalScorer`'s introduction and its `raw_score = urgency × 2.9` design. Confirms
  (does not contradict) this investigation's finding that `RegionStabilization`'s formula is
  deliberately designed to reach the shared ceiling — consistent with, not evidence against, this
  investigation's conclusion that Adventure's own formula is the one that was never actually
  validated to reach it.
- `docs/parity_ledger/strategic_cognition.yaml` STRAT-254 (SocialContract), STRAT-255
  (RegionStabilization) — both `status: verified`, `priority: P2`. Neither entry's `v2_evidence`
  makes a claim this investigation contradicts; both entries explicitly, correctly describe reusing
  the pre-existing `_ADVENTURE_ROUTE_SCORE_MAX` ceiling as "a deliberate, disclosed design choice
  (reusing the existing scale rather than extending the classifier), not an oversight" — true and
  unaffected by this investigation's findings about Adventure's own side of the shared constant.
- Strategic/Tactical Rule (CLAUDE.md) — a rescale that reflects `AdventureRouteScorer.score()`'s
  real, live-reachable output range is a legitimate strategic-layer calibration correction, not
  tactical goal-stacking; it does not touch `evaluate_project_switch()`'s decision logic
  (ticket's Out of Scope, confirmed untouched by every fix direction considered below).

## Docs Requiring Update

- `docs/mechanics/04_strategic_cognition.md`: §6.6 "Score Range Summary" needs a correction —
  either (a) an explicit "live tier-5-competition ceiling" sub-row/footnote distinguishing the
  Generalized-Bypass-gate range (2.9, faction_directives-inclusive, theoretical) from the tier-5
  `AdventureGoalScorer.score()` range (measured ~2.0-2.2 under current wiring, faction_directives
  excluded), or (b) if Plan chooses to correct the normalization denominator itself, an updated
  ~2.9 → new-value figure with the term-by-term derivation this investigation performed. Either way
  the current text is now known-stale for the tier-5-competition consumer and must not be left as-is.
- `docs/mechanics/04_strategic_cognition.md` §6.10: add a cross-reference noting that
  `faction_directives=None`'s effect is not just a disclosed simplification but the specific reason
  `_ADVENTURE_ROUTE_SCORE_MAX`'s own §6.6 basis over-estimates the tier-5-competition-reachable
  ceiling — closing the gap this investigation found between the two already-disclosed facts.
- `docs/parity_ledger/infrastructure.yaml` INFRA-237: add a fourth addendum (following the existing
  three) recording this investigation's findings and whichever fix direction Plan adopts, since this
  ticket is the direct, named follow-up INFRA-237's third addendum already points to.
- `docs/simulation_quality/eval_matrix_results.md`: the AGENCY Cross-World Design Note and its two
  dated NOTE blocks (already flagged stale by the ticket's own Scope) need updating once a fix lands
  and is measured via a fresh `calibrate_simq.py` run — same file the originating ticket already
  identified, not a new doc gap.
- `docs/guidelines/intentional_divergences.md` §2.41: add a further dated addendum recording this
  ticket's root-cause finding (distinct from, but building on, the two prior addenda already there)
  and whichever fix/DA-ruling outcome Plan adopts.

## Parity Ledger Overlap

- `docs/parity_ledger/infrastructure.yaml` INFRA-237 — `status: verified`, `priority: P1`. Directly
  overlaps; not P0, so no `test_path`-blocking gate, but `support_boundary` needs the fourth
  addendum per Docs Requiring Update.
- `docs/parity_ledger/strategic_cognition.yaml` STRAT-254 (SocialContract) — `status: verified`,
  `priority: P2`. Not contradicted, but its `v2_evidence`'s implicit assumption ("lands on the same
  `_ADVENTURE_ROUTE_SCORE_MAX = 2.9` scale... via `_score_scale_max()`'s `isinstance(kind,
  ProjectKind)` classification") is the exact mechanism this investigation flags as fragile against
  a naive global rescale (the hardcoded-`2.9`-literal-vs-shared-constant mismatch in
  `_raw_score()`'s own clamp). No edit required unless Plan chooses the global-rescale direction, in
  which case this entry's correctness becomes directly at risk and must be re-verified.
- `docs/parity_ledger/strategic_cognition.yaml` STRAT-255 (RegionStabilization) — `status: verified`,
  `priority: P2`. Confirmed provably unaffected by any value `_ADVENTURE_ROUTE_SCORE_MAX` might take
  (algebraic cancellation, shown above). No edit required under any fix direction.
- No P0 parity entry is implicated by this investigation; no `test_path`-passing gate is triggered.

## Prior Work

- `stored_artifacts/TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE/` — the direct parent.
  Its `plan.md` Deviations §2 is the evidentiary origin of this ticket (DEBUG-trace observation of
  `ADVENTURE_ROUTE` utility ~20-26 never beating `COMBAT_ENGAGE`/`REGION_STABILIZATION`). This
  investigation independently re-derives the same observation from first principles (formula
  analysis + live opportunity-generation data) and finds it fully consistent, then goes one level
  deeper to the normalization constant's own provenance and validity, which the parent ticket
  correctly flagged as out of its own scope.
- `stored_artifacts/TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT/investigation.md` Finding 1 —
  independently confirms the identical tier-5-starvation phenomenon for `GoalKind.HARVESTING`
  (`HarvestScorer.score()`, distance-decayed `50.0/dist`, wins 1/371 and 1/335 evaluations in the
  same two worlds) — a mechanistically distinct cause (no `_ADVENTURE_ROUTE_SCORE_MAX` involvement;
  `HarvestScorer` computes directly on the 0-100 scale) but the same downstream competitive
  dominance by `COMBAT_ENGAGE`/`REGION_STABILIZATION`. Its Risk #5 explicitly recommends any future
  tier-5 utility-scale/competition rebalancing consider `HARVESTING` alongside `ADVENTURE_ROUTE` —
  **out of this ticket's own Scope** (ticket's Related Code Areas name only the adventure-side
  files), noted here only as context for why a fix here may not, by itself, be expected to flip
  `HARVESTING`'s starvation too.
- `tests/unit/strategic/test_score_normalization.py` — confirmed by direct read to test **only**
  `evaluate_project_switch()`'s lock-bypass gate via hand-built `ProjectState` objects; it never
  calls `AdventureGoalScorer.score()` or `AdventureRouteScorer.score()`. A fix scoped to the
  tier-5-competition normalization specifically (see Recommended Direction) would not need to touch
  this file — a real, positive finding for scoping Plan's blast radius.
- `tests/unit/ai/goals/test_adventure_goal_scorer.py::test_adventure_goal_scorer_normalizes_raw_score_
  to_utility_exact` (lines 96-113) — the live regression guard that currently pins
  `raw_score==2.9 → utility==100.0` exactly (and `1.45→50.0`, `0.0→0.0`). This test **will** need to
  change if Plan adopts a dedicated, smaller tier-5-specific denominator — flagged for Plan/Implement,
  not touched here.

## Risks and Open Questions

1. **A global rescale of `_ADVENTURE_ROUTE_SCORE_MAX` is unsafe and should not be the fix.**
   Confirmed above: it is mathematically inert for `RegionStabilizationGoalScorer` (self-canceling),
   and would silently push `SocialContractGoalScorer.utility` above 100 (its own `raw_score` clamp is
   a hardcoded `2.9` literal, not tied to the shared constant) — a real regression in a scorer this
   ticket's own Scope/Out-of-Scope explicitly protects. **Recommended direction (for Plan to adopt
   or reject with its own reasoning): give `AdventureGoalScorer.score()`'s tier-5-competition
   normalization its own dedicated denominator**, decoupled from `_ADVENTURE_ROUTE_SCORE_MAX` (which
   should remain unchanged and continue to serve `_score_scale_max()`'s Generalized Bypass gate
   purpose, where it is still a defensible percentage-of-own-system-max comparison independent of
   this defect), calibrated to the real, measured, live-reachable range this investigation computed
   (~2.0-2.2, term-by-term from real opportunity data) rather than to §6.6's faction-directive-
   inclusive theoretical estimate. This is a genuine "let it compete on its actual merits" rescale,
   not a forced win-boost — it does not touch `evaluate_project_switch()`, does not touch
   `RegionStabilization`/`SocialContract`/`COMBAT_ENGAGE`, and reflects a formula range this
   investigation directly verified from source, not assumed.
2. **Whether this rescale is *sufficient* to produce nonzero `route_selected`/`action_executed`
   events in the two named calibration worlds is a genuinely open empirical question, not resolved
   by this investigation.** `ResolveBlockerScorer` floors at a flat `utility=80.0` whenever any
   unresolved blocker exists (57/371 and 86/335 tier-5 wins in the sibling trace) — well above even
   a fully corrected Adventure ceiling's typical output (a proportional rescale from ~2.0-2.2 to
   raw_score's own ~0.58-0.75 typical band would raise utility from ~20-26 to roughly ~26-35,
   *still* below `ResolveBlockerScorer`'s flat 80 and far below `CombatEngageScorer`'s floor of 40).
   A rescale is likely to help specifically on the `29/371` and comparable `chosen=None` ticks (no
   candidate cleared the 20.0 floor, per the sibling investigation's own trace) and possibly against
   `harvesting`'s own weak (1-30) typical range, but is **not** provably sufficient to flip outcomes
   on ticks where `COMBAT_ENGAGE`/`REGION_STABILIZATION`/`RESOLVE_BLOCKER` are active — which the
   sibling trace shows is the overwhelming majority of ticks in both worlds. Plan/Implement must
   verify the real effect via a fresh `tools/calibrate_simq.py` run after implementing, per the
   ticket's own AC3 — do not assume a fix that corrects the calibration error will also flip the
   measured `AGENCY` grade; these are separate claims requiring separate verification.
3. **If, after a legitimate, evidence-grounded rescale, `route_selected` events are still zero,**
   that outcome would be meaningfully different from today's — today's zero rate is confounded by a
   *known, provable calibration defect* (this investigation's own finding), so it cannot yet be used
   as evidence for an archetype-correct-losing verdict (mirroring
   `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`). A future determination of "archetype-correct losing" would
   only be defensible **after** the calibration defect is corrected and still-zero events are
   re-measured — this investigation does not have that post-fix data and does not pre-decide the
   question, per the ticket's own explicit instruction.
4. **The exact new denominator value should be derived empirically, not guessed from this
   investigation's manual term-by-term estimate.** The ~2.0-2.2 figure here is a reasoned
   per-route-family maximum computed from real opportunity-generation constants, but Plan/Implement
   should consider instrumenting a real corpus sample (mirroring the sibling tickets' own DEBUG-trace
   methodology) to measure the actual observed `raw_score` distribution across a representative
   window of ticks/worlds before hardcoding a specific new constant, rather than trusting this
   investigation's hand-derived ceiling as the final number.
5. **`docs/mechanics/04_strategic_cognition.md` §6.2's own table already has an internal
   inconsistency this investigation surfaced but which is not this ticket's concern to fix**: §6.2
   lists `personality_bias` max as `0.50` (correct, per `scoring.py:214-223` and §6.4's own text),
   but §6.6's "Score Range Summary" table lists `personality_bias` max as `0.25` — the doc's own
   `~2.9` total is only reachable using the `0.25` figure (`2.0+0.5+0.25+0.15=2.9`), not the `0.50`
   §6.4 documents as the real code maximum. This is a pre-existing doc-internal inconsistency,
   independent of this ticket's live-wiring finding — flagged for whoever corrects §6.6 (see Docs
   Requiring Update) so the correction does not propagate the same inconsistency forward.

## Anti-Drift Hazards

- **Do not change `RegionStabilizationGoalScorer`'s or `SocialContractGoalScorer`'s own formulas** —
  ticket's Out of Scope, and this investigation confirms neither is the anomaly (RegionStabilization
  is provably invariant to the shared constant; SocialContract's own formula was never in question,
  only its fragile dependency on the shared constant's value if that constant were changed globally).
- **Do not change `evaluate_project_switch()`'s own body or `_score_scale_max()`'s
  `isinstance(kind, ProjectKind)` classification logic** — ticket's Out of Scope; this investigation's
  recommended direction (a dedicated tier-5-competition denominator for `AdventureGoalScorer`
  specifically) does not require touching either.
- **Do not globally lower `_ADVENTURE_ROUTE_SCORE_MAX`** — would silently break
  `SocialContractGoalScorer`'s implicit 0-100 utility bound (hardcoded-`2.9`-literal-vs-shared-
  constant mismatch, confirmed above) and have zero effect on `RegionStabilizationGoalScorer`
  (self-canceling) — a real regression risk for two scorers this ticket does not intend to touch.
- **Do not "fix" `COMBAT_ENGAGE` or `ResolveBlockerScorer`** — both are correctly, independently
  calibrated directly on the 0-100 scale and are not implicated in this defect; touching either would
  be exactly the kind of unscoped competing-scorer change the ticket's own Out of Scope forbids
  absent explicit re-scoping.
- **`tests/unit/strategic/test_score_normalization.py` must stay green unmodified** — it tests only
  the Generalized Bypass gate, a different, still-correct use of `_ADVENTURE_ROUTE_SCORE_MAX` this
  ticket's recommended direction does not touch.
- **`tests/unit/ai/goals/test_adventure_goal_scorer.py::test_adventure_goal_scorer_normalizes_raw_
  score_to_utility_exact` is expected to need updating** if Plan adopts a dedicated denominator — this
  is an anticipated, in-scope test change, not drift, since AC2 of the parent
  `TCK-20260811-ADVENTURE-GOAL-SCORER` ticket is precisely the behavior this ticket's own Scope asks
  to recalibrate.
- **Do not port `plan_advance_bonus`/class-synergy/escort-bonus wiring (`group`/`progression_plan`)
  into the live tier-5 path as part of "fixing" this ticket** — confirmed neither has ever been live
  in either the old phase-based or new scorer-based architecture; wiring them in would be a
  materially larger, differently-scoped change (new call-site plumbing through
  `GoalScorer.score(entity, state)`'s signature) than a normalization-denominator correction, and is
  not what the ticket's Scope asks for.
