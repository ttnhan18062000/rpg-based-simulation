---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5
artifact_type: plan
tags: [adventure, agency, strategy, cognition]
---

# Implementation Plan — TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5

## Summary

This plan adopts investigation.md's recommended direction: give `AdventureGoalScorer.score()`'s
tier-5-competition normalization its own dedicated denominator, decoupled from
`_ADVENTURE_ROUTE_SCORE_MAX` (which stays exactly `2.9` and continues, untouched, to serve
`_score_scale_max()`'s Generalized Bypass gate purpose in `evaluate_project_switch()`). The
investigation's explicitly-flagged UNSAFE option — globally rescaling the shared constant — is
rejected for the reasons investigation.md already proves: it is a no-op for
`RegionStabilizationGoalScorer` (algebraic self-cancellation, `region_stabilization_scorer.py:60-61`)
and would silently push `SocialContractGoalScorer.utility` above the implicit 0-100 bound
(`social_contract_scorer.py:63` divides by the shared constant while `_raw_score()`'s own clamp at
line 126 is the hardcoded literal `2.9`, not a reference to the constant).

The new denominator is named `_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX` and is declared **locally in
`src/ai/goals/adventure_scorer.py`**, not in `src/systems/strategic_systems/intelligence.py`. This
is a deliberate architectural choice beyond what investigation.md specified: investigation.md's own
git-history section shows the root defect pattern is a shared constant declared in one module
(`intelligence.py`) getting silently reused for a third and fourth unrelated purpose
(`RegionStabilizationGoalScorer`, `SocialContractGoalScorer`) without revalidation. Declaring the new
constant inside the one module that owns its meaning (the tier-5 adventure-competition consumer)
removes the "convenient shared constant sitting in `intelligence.py`" attractive nuisance that caused
this defect class in the first place.

Its exact numeric value is not guessed or hand-picked in this plan. Step 1 defines a concrete,
executable derivation procedure — reusing the already-wired, hot-path-safe `decision_trace.jsonl`
observability mechanism (not new DEBUG instrumentation, avoiding investigation.md Risk #4's/the
sibling ticket's own timing-perturbation caution) to measure the real `raw_score` distribution
`AdventureRouteScorer.score()` actually produces across the two named calibration worlds, combined
with a re-derived theoretical safety floor of `2.4` (this plan's own term-by-term recomputation
from source — see Step 1 for the full citation trail, including two corrections made during
Architecture-Verify's pre-Implement review, across two review rounds: (1) the dominant
live-reachable family is `RECOVER`, not `CRAFT_UPGRADE`, since `equipment_improvement`'s need key
never exceeds `_URGENCY_MEDIUM=0.50` per `src/cognition/need_interpretation.py:126-137`, while
`healing`'s need key genuinely reaches `_URGENCY_CRITICAL=0.95`, confirmed at
`need_interpretation.py:70-77`; (2) RECOVER's own benefit ceiling is `1.0` via the `rest_inn`
opportunity kind, not `0.8` via `repair_gear` alone — both map to `RouteFamily.RECOVER` via
`generator.py:38-45`'s `kind_map` (a third, non-`kind_map` structural-default RECOVER source also
exists at `generator.py:98-109`, triggered by `"low_health" in weaknesses`, but computes to a lower
`2.135` ceiling — confirmed by Architecture-Verify's Round 3 pass, does not change the dominant
figure), and the urgency term is keyed by route family, not by which specific
opportunity backs the candidate, so a `rest_inn` candidate can still inherit an independently
critical `healing` urgency). Whichever of the two
(empirical max, theoretical floor) is larger becomes the final constant, so the fix can never
produce an `AdventureGoalScorer.utility` above `100.0` for any input this plan has evidence could
occur. As additional defense-in-depth (Architecture-Verify's recommendation, adopted here), Step 2
also adds a runtime `min(100.0, utility)` clamp, so a future change to opportunity-generation or
need-interpretation logic that raises the true ceiling above this frozen constant cannot silently
push `AdventureGoalScorer.utility` past its documented 0-100 bound.

This plan does not assume the fix flips `route_selected`/`action_executed`/`route_family_first_use`
to nonzero in the two calibration worlds — investigation.md Risk #2 is explicit that
`ResolveBlockerScorer`'s flat `utility=80.0` floor and `CombatEngageScorer`'s floor of `40.0` may
still structurally dominate even a corrected Adventure ceiling's typical output. Step 6 requires a
real, fresh, clean `calibrate_simq.py` measurement and Step 8 defines two distinct, honest closing
outcomes depending on what that measurement actually shows, mirroring the rescoping pattern already
used by the sibling `TCK-20260813-ADVENTURE-ROUTE-LAST-ROUTING-FAMILY-RESTORE` ticket.

## Steps

### Step 1 — Derive the new denominator: empirical measurement + theoretical safety floor

**Files:** None (measurement/analysis only; produces the constant value used by Step 2). Uses
`tools/calibrate_simq.py` (read-only invocation) and `data/calibration/*/decision_trace.jsonl`
(read-only parse).

**Change:**
This is a decision-making step, not a code-writing step. Execute both sub-procedures and take the
larger resulting value, rounded up to 1 decimal place, as the final constant.

**(a) Empirical measurement, using already-wired observability (not new instrumentation).**
`DecisionTraceWriter` (`src/observability/cognition/decision_trace_writer.py:1-20`, confirmed by
direct read: "Writes per-entity scored adventure route traces to decision_trace.jsonl in LIGHT and
above observability modes... write_trace() is a bounded in-memory enqueue only (hot-path safety
contract §3). The actual decision_trace.jsonl write... happen[s] off-path on a private
QueueDrainWorker") is already wired into `AdventureGoalScorer.score()`
(`adventure_scorer.py:142-146`, confirmed by direct read) and writes `result.trace["scored_candidates"]`
— which `AdventureDecisionService.decide()` populates from **every** generated candidate's own
`AdventureRouteOption.score` (`src/domains/adventure/service.py:71-83`, confirmed by direct read:
`scored_candidates: List[AdventureRouteOption] = []` accumulated in a loop over all candidates,
before the valid/blocked split), not just the winner. This is a materially richer and safer corpus
source than the sibling ticket's own ad-hoc `logging.DEBUG` print-tracing of
`evaluate_strategic_intent()`'s selection log (investigation.md Risk #4's caution about
timing-perturbation applies to that ad-hoc mechanism, not to this already-production-wired,
bounded-async one).

Run `tools/calibrate_simq.py` at LIGHT+ observability for the same 6 run_keys named in test_plan.md
New Test 6 (`simq_routing_test` × seeds {42,123,456} `_500t`, `hero_guild_routing` × seeds
{42,123,456} `_500t`) **before making the Step 2 code change** (raw_score computation itself is
untouched by this fix, so a pre-fix measurement is valid evidence for the post-fix denominator).
Parse each run's `decision_trace.jsonl`, extract every scored-candidate `score` value across the
full corpus (all entities, all ticks, all route families — not filtered to the winner), and take the
maximum observed value across all 6 run_keys combined.

**(b) Theoretical safety floor, re-derived directly from source, per matched need key's real
reachable urgency tier (corrected during Architecture-Verify's pre-Implement review — the plan's
first draft incorrectly assumed `equipment_improvement` could reach `_URGENCY_CRITICAL`; it cannot,
per direct read of `src/cognition/need_interpretation.py`).** `AdventureRouteScorer.score()`
(`src/domains/adventure/scoring.py:116-132`) maps each `RouteFamily` to a fixed set of
`InterpretedNeed` keys (`family_needs` dict) and takes the max urgency among whichever of those keys
are present in the entity's active needs. Each need key's own maximum reachable urgency tier is
fixed by `src/cognition/need_interpretation.py`'s own branching (confirmed by direct read, not
assumed):

| Need key | Max urgency tier reachable | Source line |
|---|---|---|
| `healing` | `_URGENCY_CRITICAL` (0.95), when `health < 0.20` | `need_interpretation.py:70-77` |
| `food` | `_URGENCY_CRITICAL` (0.95), when `hunger > 85.0` | `need_interpretation.py:80-90` |
| `rest` | `_URGENCY_HIGH` (0.75) only, never CRITICAL | `need_interpretation.py:92-101` |
| `stamina_recovery` | `_URGENCY_MEDIUM` (0.50) flat | `need_interpretation.py:103-112` |
| `equipment_repair` | `_URGENCY_HIGH` (0.75) only, never CRITICAL | `need_interpretation.py:114-123` |
| `equipment_improvement` | `_URGENCY_MEDIUM` (0.50) only — **never HIGH/CRITICAL** | `need_interpretation.py:125-137` |
| `inventory_space` | `_URGENCY_HIGH` (0.75) only, never CRITICAL | `need_interpretation.py:139-148` |
| `gold` | `_URGENCY_HIGH` (0.75) only, never CRITICAL | `need_interpretation.py:150-159` |
| `information` | `_URGENCY_LOW` (0.25) flat | `need_interpretation.py:161-169` |
| `social` | never populated anywhere in the codebase — always absent, urgency term contributes `0.0` | confirmed via full-repo grep for `needs\["social"\]`/`key="social"`, zero hits |

Recomputing every live-reachable route family (`AdventureRouteGenerator.generate()` only ever
produces `GATHER_RESOURCE`, `BUY_UPGRADE`, `CRAFT_UPGRADE`, `RECOVER`, `ASK_INFORMATION`,
`FORM_PARTY` — confirmed by direct read of `generator.py`; `QUEST_OPPORTUNITY`/
`SELL_LOOT_FOR_GOLD`/`TAKE_EASY_QUEST`/`SCOUT_LOCATION`/`HUNT_WEAK_ENEMY` exist in the scoring
formula but are never generated in the live path) at each family's own real max-urgency ceiling:

| Family | Matched need key(s) | Max urgency | Max benefit | Max personality_bias | Confidence | Ceiling |
|---|---|---|---|---|---|---|
| RECOVER | healing/rest/stamina_recovery/equipment_repair | 0.95 (healing) | **1.0 (`rest_inn`, not 0.8 — see correction below)** | 0.25 (caution) | 0.15 | **2.35** |
| GATHER_RESOURCE | gold/inventory_space | 0.75 (HIGH only) | 0.5 | 0.50 (greed — matches the earlier `elif` branch, `scoring.py:214`, before the later `industry×0.25` branch can ever be reached, a pre-existing dead-branch condition noted but not touched) | 0.15 | 1.90 |
| CRAFT_UPGRADE | equipment_improvement | **0.50 (MEDIUM only)** | 0.9 (material-blocker case) | 0.25 (industry) | 0.15 | **1.80** (not 2.25 — the plan's original, now-corrected figure) |
| FORM_PARTY | social | 0.0 (never populated) | 1.0 | 0.40 (sociability) | 0.15 | 1.55 |
| ASK_INFORMATION | information | 0.25 (LOW only, flat) | 0.7 | 0.25 (curiosity) | 0.15 | 1.35 |
| BUY_UPGRADE | equipment_improvement | 0.50 | 0.4 | 0 (no personality_bias branch matches BUY_UPGRADE) | 0.15 | 1.05 |

All figures use `risk_penalty=0` (each family's best-case route has `estimated_risk=0.0`, per direct
read of `resources.py`/`services.py`/`generator.py`) and `confidence_bonus=0.15` (the flat
`route.confidence × 0.15` term — the `CRAFT_UPGRADE`/`GATHER_RESOURCE` capability-estimate override
path, `scoring.py:264-325`, can push this term higher for some inputs, but 0.15 is the safe baseline
figure this plan uses; Step 1(a)'s empirical measurement independently catches any real case where
the override path produces a higher combined score than this table's static analysis assumes).

**Second correction (Architecture-Verify Round 2, pre-Implement): RECOVER's own benefit ceiling was
also understated.** `generator.py:38-45`'s `kind_map` maps **two** opportunity kinds to
`RouteFamily.RECOVER` — `repair_gear` (`estimated_reward=80.0` fixed, `services.py:78`, capping
`expected_benefit=0.8`) **and** `rest_inn` (`estimated_reward=sleep_debt`, `services.py:120`, a raw
per-entity state value clamped to `[0.0, 100.0]` — confirmed at `src/core/state.py:118`,
`src/engine/apply.py:90,153`, `src/engine/patches.py:110` — so `expected_benefit =
estimated_reward/100.0` reaches `1.0`, not `0.8`, whenever `sleep_debt` reaches its own ceiling).
`AdventureRouteScorer.score()`'s urgency term (`scoring.py:129-132`) is computed from
`family_needs.get(route.family, [])` — keyed by the candidate's `RouteFamily`, not filtered to
which specific opportunity kind backs it — so a `rest_inn`-backed RECOVER candidate still inherits
the entity's own `healing` urgency if that need is independently `CRITICAL` (health<0.20), even
though the candidate route is about resting, not healing; these are two unrelated state dimensions
with no structural exclusion preventing simultaneous occurrence (a low-health, sleep-deprived
entity is a realistic combined state, not a contrived edge case). Corrected RECOVER ceiling:
`urgency(0.95, healing CRITICAL) + benefit(1.0, rest_inn at sleep_debt=100) +
personality_bias(0.25, caution) + confidence_bonus(0.15, rest_inn's confidence=1.0 fixed) −
risk_penalty(0, rest_inn's estimated_risk=0.0) = 2.35`.

**The dominant live-reachable family is `RECOVER` at `2.35`, not `CRAFT_UPGRADE`** — the plan's
first-draft claim that `equipment_improvement` reaches `_URGENCY_CRITICAL` was wrong;
`need_interpretation.py:125-137`'s own branching caps it at `_URGENCY_MEDIUM=0.50` unconditionally
(and downgrades it further to `_URGENCY_LOW` when healing is simultaneously critical — survival
outranks growth, per the module's own docstring). `2.35` rounded up to 1 decimal place is `2.4` —
this, not `2.2` (this plan's own first-round correction, also too low) and not `2.3` (the original
draft's figure), is the theoretical safety floor.

**Decision rule:** `_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX = ROUND_UP_1DP(max(empirical_max_from_1a, 2.4))`.
Using the empirical maximum (not a percentile) as the lower bound of the comparison, together with
the theoretical floor, guarantees the constant is never set below any raw_score this plan has actual
or theoretical evidence could occur — setting it too low would itself introduce a *new*,
self-inflicted regression (an `AdventureGoalScorer.utility` exceeding `100.0`, breaking the same
implicit 0-100 `GoalScore.utility` contract investigation.md flags for `SocialContractGoalScorer`).
Record the measured empirical max and the final chosen constant value in Implementation Notes.

**Do NOT touch:** No code changes in this step. Do not modify `_ADVENTURE_ROUTE_SCORE_MAX` or any
scorer file yet.

**Verify:** N/A (measurement step) — the chosen value is verified indirectly by Step 4's boundary
tests and Step 6's calibration run.

---

### Step 2 — Implement the dedicated denominator in `AdventureGoalScorer.score()`

**Files:** `src/ai/goals/adventure_scorer.py`

**Change:** At module level (near the top of the file, alongside the existing module-level
`_PROFILE_ELIGIBILITY_CACHE`, `adventure_scorer.py:21`), declare:
```python
# Dedicated tier-5-competition normalization ceiling for AdventureGoalScorer.score(), decoupled
# from src.systems.strategic_systems.intelligence._ADVENTURE_ROUTE_SCORE_MAX (TCK-20260813-
# ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5). _ADVENTURE_ROUTE_SCORE_MAX stays 2.9 and
# continues to serve only _score_scale_max()'s Generalized Bypass gate purpose in
# evaluate_project_switch() -- do not reuse it here, and do not let a future scorer reuse THIS
# constant for an unrelated purpose either (that reuse pattern is what caused this ticket).
# Value derived in plan.md Step 1: max(empirical raw_score corpus maximum across
# simq_routing_test/hero_guild_routing x seeds{42,123,456}_500t, 2.4 theoretical safety floor
# derived from RECOVER's own real max-urgency ceiling (healing=CRITICAL + rest_inn benefit=1.0)
# -- see plan.md Step 1b for the full per-need-key urgency-tier table).
_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX: float = <VALUE_FROM_STEP_1>
```
Change the import at `adventure_scorer.py:96-99` from importing both
`_ADVENTURE_ROUTE_SCORE_MAX, _GOAL_UTILITY_SCORE_MAX` from `intelligence.py` to importing only
`_GOAL_UTILITY_SCORE_MAX` (the shared 0-100 scale is still correct and unchanged — only the
System-A-side denominator is decoupled). Change line 210 from
`utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) * _GOAL_UTILITY_SCORE_MAX` to
```python
utility = min(
    _GOAL_UTILITY_SCORE_MAX,
    (raw_score / _ADVENTURE_ROUTE_TIER5_COMPETITION_MAX) * _GOAL_UTILITY_SCORE_MAX,
)
```
The `min(100.0, ...)` clamp is defense-in-depth (Architecture-Verify's recommendation, adopted
here): `_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX` is a frozen constant derived from today's
opportunity-generation/need-interpretation logic; if a future, unrelated change to either raises
the true achievable `raw_score` ceiling above this constant, the clamp prevents
`AdventureGoalScorer.utility` from silently exceeding the documented 0-100 `GoalScore.utility`
contract, without requiring every future change elsewhere in the codebase to remember to
re-validate this constant.

Every other writer to `_ADVENTURE_ROUTE_SCORE_MAX`/consumer of the intelligence.py constants is
enumerated and confirmed unaffected by this change, since none of them are touched:
- `RegionStabilizationGoalScorer.score()` (`region_stabilization_scorer.py:45-61`) imports and uses
  `_ADVENTURE_ROUTE_SCORE_MAX` for both its own `raw_score = urgency * _ADVENTURE_ROUTE_SCORE_MAX`
  and `utility = (raw_score / _ADVENTURE_ROUTE_SCORE_MAX) * _GOAL_UTILITY_SCORE_MAX` — an import
  from `intelligence.py`, not from `adventure_scorer.py`. Untouched by this step; algebraically
  self-cancels regardless (investigation.md).
- `SocialContractGoalScorer.score()` (`social_contract_scorer.py:50-63`) imports the same pair from
  `intelligence.py`, independently. Untouched by this step.
- `_score_scale_max()`/`evaluate_project_switch()` (`intelligence.py`, `_ADVENTURE_ROUTE_SCORE_MAX`
  declared at `intelligence.py:32`) — the module-level declaration itself is not edited by this
  step. Untouched.
- No other file imports `_ADVENTURE_ROUTE_SCORE_MAX` (confirmed: it is a leading-underscore
  module-private name; the only 3 consumers are the ones enumerated above, all read directly this
  session).

**Do NOT touch:** `_ADVENTURE_ROUTE_SCORE_MAX`'s declaration or value (`intelligence.py:32`),
`_GOAL_UTILITY_SCORE_MAX` (`intelligence.py:47`), `region_stabilization_scorer.py`,
`social_contract_scorer.py`, `evaluate_project_switch()`, `_score_scale_max()`,
`AdventureRouteScorer.score()`'s own formula (`scoring.py`) — `raw_score`'s computation is
completely unchanged; only its tier-5-competition consumer's normalization changes.

**Verify:** New Test 1 (Step 4a) and the updated existing test (Step 3).

---

### Step 3 — Update the existing pinned normalization test

**Files:** `tests/unit/ai/goals/test_adventure_goal_scorer.py`

**Change:** `test_adventure_goal_scorer_normalizes_raw_score_to_utility_exact`
(`test_adventure_goal_scorer.py:96-113`, confirmed by direct read) currently parametrizes
`(2.9, 100.0), (1.45, 50.0), (0.0, 0.0)` — i.e. it pins the *old* `_ADVENTURE_ROUTE_SCORE_MAX=2.9`
boundary. Rename to
`test_adventure_goal_scorer_normalizes_raw_score_to_utility_exact_dedicated_denominator` (satisfies
test_plan.md New Test 1 in place, per its own "extend/replace the existing parametrized test"
guidance) and re-parametrize using the Step 1 value `V = _ADVENTURE_ROUTE_TIER5_COMPETITION_MAX`:
`(V, 100.0), (V/2, 50.0), (0.0, 0.0)`. Keep the test's docstring/comment noting this now asserts the
new, dedicated denominator's own boundary, not the old shared-constant boundary — so a future reader
does not mistake `raw_score==2.9` as still meaningful here (it structurally cannot equal `100.0`
utility anymore unless `V` happens to equal `2.9`, which Step 1's derivation makes unlikely).

**Do NOT touch:** The other tests in this file that do not depend on the exact denominator value
(`test_goal_kind_adventure_route_is_registered_member`,
`test_adventure_goal_scorer_metadata_carries_route_family_and_raw_score` — this one asserts
`score.metadata["raw_score"] == 1.8`, a `metadata` field, not `.utility`, so it is unaffected — the
Risk #1 target_pos tests, the AC5 ineligible/defer tests, the AC6 tie-break tests).

**Verify:** `pytest tests/unit/ai/goals/test_adventure_goal_scorer.py -m "not slow" -q`.

---

### Step 4 — Add the regression-guard and behavioral tests

**Files:** `tests/unit/ai/goals/test_adventure_goal_scorer.py`,
`tests/unit/ai/goals/test_region_stabilization_goal_scorer.py`,
`tests/unit/ai/goals/test_social_contract_goal_scorer.py`, and one new file under
`tests/architecture/` (exact path TBD by Implement — see 4d).

**Change (4a — typical-score utility increase, test_plan.md New Test 4):** Add
`test_adventure_route_typical_score_produces_meaningfully_higher_utility_than_before_fix` to
`test_adventure_goal_scorer.py`. Using `_fake_decide_factory` (already in this file, confirmed by
direct read at lines 41-63) with a mid-range `raw_score` drawn from the RECOVER
critical-healing-plus-rest_inn example in the corrected Step 1b table (`raw_score = 2.35`:
`_URGENCY_CRITICAL=0.95` for `healing`, `rest_inn`'s `expected_benefit=1.0` (at `sleep_debt=100`),
`caution×0.25` personality_bias, `confidence_bonus=0.15` (`rest_inn`'s `confidence=1.0` fixed) — a
real, live-reachable value, not a synthetic one), assert the resulting `utility` is measurably
higher than `(2.35 / 2.9) * 100 = 81.03` would have produced pre-fix (using the *actual* post-fix
`_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX` from Step 1, not a hardcoded literal, so this test does not
itself pin an unjustified number). Also add a second parametrized case using the sibling ticket's own
observed typical band (`raw_score ≈ 0.58-0.75`, cited investigation.md "consistent with... the
sibling ticket's DEBUG-trace observation") confirming the post-fix utility in that band is higher
than the pre-fix `(raw_score/2.9)*100` value would have been, quantifying the real-world magnitude
of the fix's effect (not just its boundary values).

**Change (4b — RegionStabilization unaffected, test_plan.md New Test 2):** Add
`test_region_stabilization_goal_scorer_utility_unchanged_by_adventure_denominator_decoupling` to the
**already-existing** `tests/unit/ai/goals/test_region_stabilization_goal_scorer.py` (confirmed
present and already covering AC1/AC3/target_pos/the-2.9-not-100-calibration — do not create a new
file). Assert, at `hazard_level=1.0` (matching the file's existing
`test_region_stabilization_goal_scorer_raw_score_calibrated_to_2_9_not_100` fixture exactly), that
`score.utility == 100.0` and `score.metadata["raw_score"] == pytest.approx(2.9)` — i.e. explicitly
pin the utility value too (the existing test only pins `raw_score`, not `.utility`), proving
`RegionStabilizationGoalScorer` still computes its own `raw_score * 100 / raw_score = 100`-at-max
result unaffected by anything in `adventure_scorer.py`, since `RegionStabilizationGoalScorer` never
imports from `adventure_scorer.py` (Step 2's enumeration).

**Change (4c — SocialContract stays bounded, test_plan.md New Test 3):** Add
`test_social_contract_goal_scorer_utility_stays_bounded_by_100_after_adventure_fix` to the
**already-existing** `tests/unit/ai/goals/test_social_contract_goal_scorer.py` (confirmed present —
test_plan.md's "create if it does not already exist" caveat does not apply; correct this in
Implementation Notes as a test_plan.md correction). Reuse the file's existing
`test_social_contract_goal_scorer_raw_score_clamped_to_2_9_ceiling` fixture (LOAN, trust=1.0 via
bond sentiment=1.0, `terms={"amount": 1000, "duration": 100}`, `current_tick=100`) but assert on
`SocialContractGoalScorer().score(ent, state).utility == 100.0` (not just the `_raw_score()` helper
return value the existing test checks) — proving the full `score()` call path still bounds utility
at exactly `100.0` at the raw-score clamp ceiling, unaffected by Step 2 (SocialContract imports
`_ADVENTURE_ROUTE_SCORE_MAX`/`_GOAL_UTILITY_SCORE_MAX` from `intelligence.py`, never from
`adventure_scorer.py`).

**Change (4d — Generalized Bypass gate still uses 2.9, test_plan.md New Test 5):** Do **not** edit
`tests/unit/strategic/test_score_normalization.py` (investigation.md's own Anti-Drift Hazards and
test_plan.md's Regression Surface both say it "must stay green **unmodified**"). Instead, grep
`tests/architecture/` at Implement time for the existing `test_evaluate_project_switch_source_hash_
unchanged`-style precedent test_plan.md references, and add a new test in that style (or a new file
`tests/architecture/test_adventure_route_score_max_unchanged.py` if no matching file exists) that
asserts, by direct import, `src.systems.strategic_systems.intelligence._ADVENTURE_ROUTE_SCORE_MAX ==
2.9` — a source-level pin that fails loudly if a future change (accidentally or otherwise) alters the
Generalized Bypass gate's own denominator, which this ticket's fix must never touch.

**Do NOT touch:** `tests/unit/strategic/test_score_normalization.py` itself, in any way — it is the
existing proof this ticket's fix does not touch the Generalized Bypass gate; 4d's new test
supplements it, per test_plan.md's own explicit alternative, rather than modifying it.

**Verify:** All 5 scoped pytest files/commands listed in Step 5, run together.

---

### Step 5 — Run the full scoped regression suite

**Files:** None (verification only).

**Change:** Run every command from test_plan.md's "Scoped Pytest Commands" section, in order,
capturing pass/fail counts for each:
```
pytest tests/unit/ai/goals/test_adventure_goal_scorer.py -m "not slow" -q
pytest tests/unit/ai/goals/test_region_stabilization_goal_scorer.py -m "not slow" -q
pytest tests/unit/strategic/test_score_normalization.py -m "not slow" -q
pytest tests/unit/strategic/test_adventure_route_materialization.py tests/unit/strategic/test_region_stabilization_materialization.py tests/unit/strategic/test_social_contract_materialization.py -m "not slow" -q
pytest tests/unit/domains/adventure/ -m "not slow" -q
pytest tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py -m "not slow" -q
pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k "simq_routing_test or hero_guild_routing"
```
Plus the new/moved 4d architecture test file explicitly. Also add
`pytest tests/unit/ai/goals/test_social_contract_goal_scorer.py -m "not slow" -q` (not in
test_plan.md's list verbatim, but the file this plan's Step 4c edits — must be run). Record every
result in Implementation Notes, including the `test_grade_regression.py` baseline (currently AGENCY
`C/0.0` on all 6 named run_keys, per the parent ticket's confirmed-unchanged state) — this file is
expected to still pass at this point (code-level unit change only; `grade_anchors.json` is not yet
touched, and must not need to be until Step 6/8 determine whether it should be).

**Do NOT touch:** `pytest tests/` (unscoped) — never run the full suite, per CLAUDE.md Testing Rule.

**Verify:** All listed commands exit 0 (or, for `test_grade_regression.py`, produce the same
pre-change AGENCY band it already produces, since no `grade_anchors.json` edit has happened yet).

---

### Step 6 — Fresh, clean post-fix `calibrate_simq.py` verification (ticket AC3)

**Files:** None (verification only; produces the evidence Step 7/8 depend on).

**Change:** After Step 2's code change lands and Step 5 is green, run `tools/calibrate_simq.py`
**clean** (no ad-hoc DEBUG print-tracing added — the sibling ticket's own Risk #4 caution; using
LIGHT+ observability's already-wired `decision_trace.jsonl`, exactly as Step 1a did, is fine since
it is the same off-hot-path mechanism, not new instrumentation) against all 6 named run_keys:
`simq_routing_test` × seeds {42,123,456} `_500t`, `hero_guild_routing` × seeds {42,123,456} `_500t`.

For each run_key, record whether `route_selected`, `action_executed`, `route_family_first_use` fire
(nonzero event counts) and what AGENCY grade/`normalized_score` results. **Do not assume a result** —
investigation.md Risk #2 is explicit this is not provably determined by the Step 2 fix alone
(`ResolveBlockerScorer` floors at flat `utility=80.0`; even a realistic post-fix Adventure utility in
the ~26-35 range, per investigation.md's own proportional-rescale estimate, stays below that floor
and below `CombatEngageScorer`'s floor of `40.0`). Report the actual measured numbers.

**Do NOT touch:** `grade_anchors.json`, `eval_matrix_results.md`, or any parity/divergence doc in
this step — Step 6 is measurement only. Do not edit any doc based on an assumed outcome.

**Verify:** This step's own output (the measured event counts/grades) is the evidence Step 7 and
Step 8 consume — there is no separate pass/fail here beyond "the run completed and was captured
faithfully."

---

### Step 7 — Update docs, conditioned on Step 6's actual measured outcome

**Files:** `docs/mechanics/04_strategic_cognition.md` (§6.6, §6.10),
`docs/parity_ledger/infrastructure.yaml` (INFRA-237), `docs/guidelines/intentional_divergences.md`
(§2.41), `docs/simulation_quality/eval_matrix_results.md` (AGENCY Cross-World Design Note, lines
~624-704, and the two `> NOTE (2026-08-13 ...)` blocks in `simq_routing_test`'s own section and
`hero_guild_routing`'s own section — grep `"2026-08-13.*NOTE"` for both at Implement time; the
`hero_guild_routing` one is confirmed at `eval_matrix_results.md:692-704`).

**Change:**
- `04_strategic_cognition.md` §6.6 "Score Range Summary" (confirmed containing the `~2.9` estimate
  and the personality_bias `0.25`-vs-`0.50` table inconsistency, investigation.md Risk #5, itself
  confirmed by direct read at `04_strategic_cognition.md:192` (§6.2 lists max `0.50`, correct per
  `scoring.py:212-223`) vs. the `~2.9` total only being reachable using `0.25`): add an explicit
  "live tier-5-competition ceiling" sub-row/footnote stating `AdventureGoalScorer.score()` now
  normalizes against its own dedicated `_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX` (Step 1's derived
  value), distinct from the `2.9` Generalized-Bypass-gate figure this section otherwise describes.
  While here, also correct the `0.25`-vs-`0.50` personality_bias inconsistency Risk #5 flagged (state
  the real per-family max is `0.50` for greed/GATHER_RESOURCE-family and QUEST_OPPORTUNITY, `0.40`
  for sociability/FORM_PARTY, `0.25` for caution/RECOVER, curiosity/ASK_INFORMATION-family, and
  industry/CRAFT_UPGRADE — not a flat `0.25` — matching `scoring.py:212-223` exactly, confirmed by
  direct read this session). Also fold in Step 1(b)'s corrected per-need-key urgency-tier table
  (Architecture-Verify findings, both review rounds): §6.6's `~2.0` urgency-term estimate is not
  uniformly reachable — only `healing`/`food` ever reach `_URGENCY_CRITICAL`;
  `equipment_improvement`/`information` are hardcoded to `_URGENCY_MEDIUM`/`_URGENCY_LOW`
  respectively and can never reach HIGH/CRITICAL regardless of entity state. State this
  per-need-key ceiling explicitly rather than the single flat `~2.0` figure the doc currently
  implies applies to every route family equally. Additionally note that `RouteFamily.RECOVER`
  itself maps to two distinct opportunity kinds (`repair_gear`, benefit capped at `0.8`;
  `rest_inn`, benefit reaching `1.0`) sharing one urgency-lookup key set — the doc's own §6.6/§6.10
  text does not currently distinguish this, and should, since it is the source of this ticket's
  own corrected `2.35` RECOVER ceiling. This is a pre-existing doc bug unrelated to this ticket's
  live-wiring finding, but investigation.md flagged it explicitly as something "whoever corrects
  §6.6" should not propagate forward — this plan chooses to fix it now since Step 7 is already
  touching this exact table.
- §6.10: add the cross-reference investigation.md's Docs Requiring Update section specifies — that
  `faction_directives=None`'s effect is not just a disclosed call-signature simplification but the
  specific reason §6.6's old `~2.9` figure over-estimated the tier-5-competition-reachable ceiling,
  now corrected by this ticket's dedicated denominator.
- `infrastructure.yaml` INFRA-237: add a fourth `support_boundary`/`divergence_note` addendum
  (following the existing three, confirmed present at `infrastructure.yaml:2937-2965`), dated
  2026-08-13, recording: the root-cause finding (a normalization denominator calibrated for a
  different, faction-directive-inclusive input configuration), the fix (dedicated
  `_ADVENTURE_ROUTE_TIER5_COMPETITION_MAX`, value = Step 1's derived constant), and Step 6's actual
  measured outcome.
- `intentional_divergences.md` §2.41 (confirmed at line 998, "Adventure-Route Defer-Reason
  Observability Gap"): add a further dated bullet addendum, matching the existing addendum style at
  lines ~1090-1120 ("Restoration addendum" / "Related finding — HARVESTING..." bullets already
  there), recording this ticket's root-cause finding and fix, **conditioned on Step 6's outcome**:
  - If Step 6 shows nonzero events: state the fix restored real AGENCY event emission for the
    affected run_keys, with the actual measured counts/grades.
  - If Step 6 still shows zero events: state explicitly that the calibration defect (denominator
    miscalibration) is corrected and confirmed via the unit-level tests (Step 4a/Step 3), but
    `route_selected`/`action_executed` still measure zero for a structurally distinct reason
    (`ResolveBlockerScorer`/`CombatEngageScorer` floor dominance, per investigation.md Risk #2/#3) —
    do not claim a restoration that Step 6's fresh measurement does not support, mirroring the
    existing "Restoration addendum" bullet's own honest-disclosure precedent at lines ~1090-1113.
- `eval_matrix_results.md`: update the AGENCY Cross-World Design Note (`:624-704`) and both
  2026-08-13 NOTE blocks the same way, strictly matching whichever of the two Step 6 outcomes
  actually occurred — do not pre-write either version before Step 6's data exists.

**Do NOT touch:** Any other section of these 4 docs; `docs/parity_ledger/strategic_cognition.yaml`
STRAT-254/STRAT-255 (investigation.md confirms neither entry is contradicted or requires an edit
under the recommended, decoupled-denominator direction).

**Verify:** `make knowledge-index-update` after these doc edits (CLAUDE.md "After Work" rule — docs
under `docs/` were modified).

---

### Step 8 — Close the ticket with an outcome-conditioned framing

**Files:** `tickets/inprogress/TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5.md`
(→ `tickets/done/`), plus a new follow-up ticket file if Step 6's outcome requires one.

**Change:** Two possible closing framings, chosen strictly by Step 6's actual measured result — do
not pick one in advance:

- **Outcome A — Step 6 shows nonzero `route_selected`/`action_executed`/`route_family_first_use`
  for one or more of the 6 run_keys.** Clean win. Recalibrate
  `tests/simulation_quality/fixtures/grade_anchors.json` AGENCY for exactly the run_keys where
  events actually fired, to the actual measured grade (ticket AC4, conditioned on "if the fix
  restores real emission" — confirmed by Step 6's data, not assumed). Close the ticket with all 5
  ACs marked done, citing Step 6's real numbers.

- **Outcome B — Step 6 still shows zero events for all 6 run_keys.** This is a legitimate, evidence-
  grounded close, **not** a failure to satisfy the ticket. Per investigation.md Risk #3 (explicitly
  anticipated, not discovered post-hoc): this outcome is *meaningfully different* from the ticket's
  original starting state, because today's zero rate is confounded by a known, provable calibration
  defect (the denominator mismatch this ticket's own investigation traced end-to-end), which is now
  corrected and verified at the unit level (Step 3/4a). A still-zero post-fix measurement is new,
  uncofounded evidence, not a repeat of the old unexplained zero. Close this ticket with: AC1
  (root cause) done: cited above; AC2 (real, non-forced fix) done: the dedicated-denominator
  rescale, not a win-boost hack; AC3's core clause (fresh `calibrate_simq.py` verification) done:
  Step 6's actual measured zero result is itself the required verification, documented rather than
  assumed — AC3's own parenthetical DA-ruling sub-clause ("if 0 is the correct/expected post-fix
  finding, that is what's verified and documented") is explicitly **deferred to the new follow-up
  ticket below**, not self-adjudicated here (Architecture-Verify's precision note: a DA ruling on
  archetype-correctness is a design/product decision for a separately-scoped ticket, not something
  this ticket's own close can determine); AC4
  (grade_anchors.json recalibration) explicitly **not applicable** — do not touch
  `grade_anchors.json`, since no real emission change occurred to recalibrate against (the 6 run_keys'
  `C`/`0.0` AGENCY anchors remain correct); AC5 (eval_matrix_results.md updated) done: reflects the
  real, now-uncofounded zero outcome per Step 7. File a new follow-up ticket (standard tier, layer
  `strategy`) proposing a DA ruling on whether `COMBAT_ENGAGE`/`REGION_STABILIZATION`/
  `RESOLVE_BLOCKER`'s structural dominance over `ADVENTURE_ROUTE` in these two specific
  danger-heavy calibration worlds is itself archetype-correct (mirroring
  `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`'s precedent) — explicitly out of *this* ticket's own scope
  (a DA ruling is a design/product decision, not a code-correctness fix), matching the sibling
  ticket's own established rescoping pattern (`stored_artifacts/TCK-20260813-ADVENTURE-ROUTE-LAST-
  ROUTING-FAMILY-RESTORE/`).

Either way: append to `tickets/working_log.csv`, move staging artifacts to `stored_artifacts/`, run
`rm -rf data/runs/* reports/release_proof/*` cleanup, stage `agent-monitoring/` and
`docs/REGISTRY.yaml` per CLAUDE.md's After-Work checklist.

**Do NOT touch:** Do not force a route to win by adjusting anything other than the Step 2
denominator (no touching `ResolveBlockerScorer`, `CombatEngageScorer`, `RegionStabilizationGoalScorer`
to manufacture a nonzero result in Outcome B — this project's own explicit guidance against forcing
an unrealistic route to fix a low pillar score, cited directly in the ticket's own Scope).

**Verify:** `done-checker` agent's 13 Definition-of-Done conditions, run independently (per this
session's own memory note: implementer must not self-execute Finalize/self-report done).

## Scope Guards

Restated directly from investigation.md's Anti-Drift Hazards — none of these are touched by any
step above:

- Do not change `RegionStabilizationGoalScorer`'s or `SocialContractGoalScorer`'s own formulas
  (`region_stabilization_scorer.py`, `social_contract_scorer.py`) — confirmed untouched by Step 2's
  enumeration; only extended with new assertions in already-existing test files (Step 4b/4c).
- Do not change `evaluate_project_switch()`'s own body or `_score_scale_max()`'s
  `isinstance(kind, ProjectKind)` classification logic (`intelligence.py`).
- Do not globally lower or otherwise edit `_ADVENTURE_ROUTE_SCORE_MAX` (`intelligence.py:32`) — it
  stays exactly `2.9`, pinned by Step 4d's new source-level guard test.
- Do not "fix" `COMBAT_ENGAGE` (`src/ai/goals/scorers.py:100-131`) or `ResolveBlockerScorer`
  (`scorers.py:189-222`) — both are correctly, independently calibrated directly on the 0-100 scale.
- `tests/unit/strategic/test_score_normalization.py` must stay green **unmodified** — Step 4d
  deliberately avoids editing it, adding a new architecture-guard test elsewhere instead.
- Do not port `plan_advance_bonus`/class-synergy/escort-bonus wiring (`group`/`progression_plan`)
  into the live tier-5 path as part of this fix — confirmed never live in either architecture;
  wiring them in is a materially larger, differently-scoped change than a normalization-denominator
  correction.
- Do not touch `AdventureRouteScorer.score()`'s own formula (`src/domains/adventure/scoring.py`) —
  only its tier-5-competition *consumer*'s normalization changes; `raw_score` computation is
  unchanged end to end.
- Do not touch `docs/parity_ledger/strategic_cognition.yaml` STRAT-254/STRAT-255 — investigation.md
  confirms neither is contradicted by the recommended direction.
- Do not manufacture a nonzero `route_selected`/`action_executed` result in Outcome B by touching any
  competing scorer — per the ticket's own explicit anti-thumb-on-the-scale guidance.
- `hero_guild_routing_seed456_500t`'s ECONOMY/PROGRESSION drift is tracked separately by
  `TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT` — do not fold that ticket's HARVESTING-side
  finding into this plan's scope, even though investigation.md's Prior Work section notes the same
  downstream competitive-dominance phenomenon.

## Dependency Map

- Step 1 → Step 2 (Step 2 needs Step 1's derived constant value).
- Step 2 → Step 3, Step 4a-4c (all reference the new constant/its formula).
- Step 2, Step 3, Step 4 → Step 5 (regression suite needs the code+test changes landed first).
- Step 5 (green) → Step 6 (do not run the expensive calibration pass against code that hasn't passed
  unit tests yet).
- Step 6 → Step 7 (doc content is conditioned on Step 6's actual measured outcome).
- Step 6 → Step 8 (closing framing is conditioned on Step 6's actual measured outcome).
- Step 7 and Step 8 can proceed in parallel once Step 6's data exists (both consume the same
  evidence, neither depends on the other's output).
- Step 4d (architecture guard test) has no dependency on Step 1's specific value — it pins
  `_ADVENTURE_ROUTE_SCORE_MAX == 2.9`, unrelated to whatever Step 1 derives — and could technically
  run before Step 1, but is grouped into Step 4 for review-locality.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Root cause of the utility-scale mismatch determined with real evidence (not assumed) | Already satisfied by investigation.md; restated in this plan's Summary and Step 7's doc updates | N/A (documentary) |
| A real, non-forced fix implemented (rescale, not a win-boost hack) — or an explicit DA-style determination if no fix is warranted | Step 1 (derivation), Step 2 (implementation) | `pytest tests/unit/ai/goals/test_adventure_goal_scorer.py -m "not slow" -q` (Step 3/4a tests) |
| `route_selected`/`action_executed`/`route_family_first_use` verified via a fresh `calibrate_simq.py` run to fire (or, if 0 is the correct/expected post-fix finding, that is what's verified and documented) | Step 6 | Step 6's own measured output; `pytest tests/simulation_quality/test_grade_regression.py -m "not slow" -q -k "simq_routing_test or hero_guild_routing"` |
| `grade_anchors.json` AGENCY recalibrated for the 6 run_keys if the fix restores real emission | Step 8, Outcome A only (explicitly skipped in Outcome B, per Step 8's own reasoning) | `test_grade_regression.py`'s anchor-band assertions for the 6 named keys |
| `docs/simulation_quality/eval_matrix_results.md` updated to reflect the real, verified outcome | Step 7 | N/A (documentary; `make knowledge-index-update` per Step 7's Verify) |

## Anti-Drift Notes

- **Do not let Step 1's empirical measurement leak into a code change before Step 2.** Step 1 is
  read-only analysis; running `calibrate_simq.py` for measurement purposes must not be mistaken for
  the "fresh calibrate_simq.py verification" AC3 requires — that is Step 6, run only *after* Step 2's
  code change lands, and must be reported separately from Step 1's pre-fix numbers.
- **The new denominator must never be set lower than the larger of the two Step 1 sub-results.**
  Setting it too low is a *new*, self-inflicted regression this ticket would introduce (an
  `AdventureGoalScorer.utility` exceeding the implicit 0-100 `GoalScore.utility` contract) — the
  exact same class of bug investigation.md flags as a real risk for `SocialContractGoalScorer` under
  a global rescale, just self-inflicted on `AdventureGoalScorer` itself instead if Step 1 is done
  carelessly.
- **`test_social_contract_goal_scorer.py` and `test_region_stabilization_goal_scorer.py` already
  exist** (confirmed by direct read this session) — test_plan.md's New Test 3 description hedges
  with "create if it does not already exist"; that hedge does not apply. Step 4b/4c extend the
  existing files; do not create duplicate new files.
- **Do not treat Outcome B (Step 6 still zero) as this ticket having failed.** Per investigation.md
  Risk #2/#3 and this plan's own Step 8, a still-zero, evidence-grounded, uncofounded measurement is
  an explicitly anticipated and acceptable close condition — the ticket's own AC2 already
  contemplates "if Investigate concludes no fix is warranted... that determination is made
  explicitly with cited evidence, not silently defaulted either way," and Step 8 Outcome B is exactly
  that pattern applied post-fix rather than pre-fix.
- **`scoring.py:214-219`'s dead `elif` branch for `GATHER_RESOURCE`'s `industry×0.25` term** (never
  reachable — the earlier `greed×0.50` branch always matches first) is noted in Step 1b as an
  unrelated, pre-existing observation. Do not "fix" it as part of this ticket; it is out of scope.
- **Plan-defect correction record (pre-Implement, two Architecture-Verify rounds, both
  NEEDS_CHANGES on the first pass):**
  - **Round 1:** this plan's first draft of Step 1(b) incorrectly claimed `CRAFT_UPGRADE`'s
    `equipment_improvement` need key could reach `_URGENCY_CRITICAL=0.95`, computing a theoretical
    floor of `2.25→2.3` from that false premise. Architecture-Verify traced
    `src/cognition/need_interpretation.py:125-137` directly and found `equipment_improvement` is
    hardcoded to `_URGENCY_MEDIUM=0.50` only (further downgraded to `_URGENCY_LOW` when healing is
    simultaneously critical) — it can never reach HIGH/CRITICAL. The corrected dominant family
    became `RECOVER` (via `healing`, which genuinely reaches `_URGENCY_CRITICAL`) at a
    then-computed ceiling of `2.15` (using only the `repair_gear` opportunity kind's
    `expected_benefit=0.8`), rounding up to a theoretical floor of `2.2`.
  - **Round 2:** re-review of the Round-1-corrected plan found a second, more subtle defect in the
    same Step 1(b) derivation: `RouteFamily.RECOVER` maps to **two** opportunity kinds
    (`generator.py:38-45`) — `repair_gear` (`expected_benefit` capped at `0.8`, the only one Round
    1's correction used) and `rest_inn` (`expected_benefit = sleep_debt/100.0`, reaching `1.0` at
    `sleep_debt=100`, clamped in `src/core/state.py`/`apply.py`/`patches.py`). Because
    `AdventureRouteScorer.score()`'s urgency term (`scoring.py:129-132`) is keyed by `route.family`
    — not filtered to which specific opportunity kind backs the candidate — a `rest_inn`-backed
    RECOVER candidate can still inherit an independently-critical `healing` urgency. The true
    RECOVER ceiling is `0.95 + 1.0 + 0.25 + 0.15 = 2.35`, rounding up to a theoretical floor of
    `2.4`, not `2.2`.
  - This plan (Step 1b, Step 2's code comment, Step 4a's test rationale, Step 7's doc-fix scope) was
    corrected in place after each round, before Implement began. The Round-1-corrected `2.2` figure
    was itself still too low, by the plan's own stated methodology — Round 2's correction was not
    optional polish, it changes the actual final constant value Implement must use. The original
    draft's `2.3` figure happened to be numerically safe purely by coincidence of Round 1's error
    direction, not because the original derivation method was sound, and would still have been
    unsafe relative to Round 2's `2.4` finding had it been used. Implement must use the
    **doubly-corrected `2.4` figure** and the corrected per-need-key/per-opportunity-kind table
    (both corrections), not either of the two earlier draft figures.

## Deviations (recorded during Implement)

- **Step 1's cited `decision_trace.jsonl` location was inaccurate; corrected in place, same
  mechanism/intent.** Step 1(a)'s Files note says `data/calibration/*/decision_trace.jsonl`
  (read-only parse). Direct trace during Implement found `DecisionTraceWriter` is actually
  instantiated by the Kernel with `run_dir` pointing at the engine's own raw run directory,
  `data/runs/{run_id}/` — `decision_trace.jsonl` lands there, not inside
  `data/calibration/{run_tag}/` (which `calibrate_simq.py` only ever populates with
  `quality_report.json`/`quality_scores.jsonl`/`quality_report.run_health.json`). This does not
  change Step 1's derivation method, its "already-wired, hot-path-safe, off-path async write"
  safety argument, or the resulting empirical corpus — `calibrate_simq.py` prints the real
  `engine_run_dir` to stdout, which is what was actually parsed. Empirical result unaffected:
  measured max `raw_score = 0.7439` (well below the `2.4` theoretical floor, which governs the
  final constant either way).
- **One of the 6 run_keys (`simq_routing_test_seed456_500t`) produced no `decision_trace.jsonl` at
  all** during Step 1's pre-fix measurement pass — no eligible entity had any scored adventure
  candidate write a trace entry in that particular 500-tick run (the writer opens the file lazily
  only on a non-empty `write_trace()` call). This contributes nothing to the empirical corpus for
  that run_key, which is expected/consistent (not an error) — the theoretical floor of `2.4`
  already exceeds anything a nonzero corpus from this run_key could plausibly have produced, per
  the other 5 run_keys' own observed maxima (0.59–0.74).
- **Step 4d's new architecture-guard test file was created fresh, not extended from
  `test_committed_intention_arbiter_byte_identical_guard.py`.** That file is a whole-function-body
  SHA-256 pin (a different guard *style* — byte-identical function source, not a single constant's
  literal value); extending it would have conflated two different guard shapes in one file. Step
  4d's own text explicitly allows this fallback ("or a new file under `tests/architecture/`... if
  no matching file exists"). New file: `tests/architecture/test_adventure_route_score_max_unchanged.py`.
- **Step 6's actual measured outcome is Outcome A, but a mixed/partial one (1 of 6 run_keys), not
  the "or more" phrasing's more typical all-or-nothing framing.** Plan Step 8's Outcome A text
  ("nonzero... for one or more of the 6 run_keys") already anticipates and covers this exact shape
  — no plan text conflicts with the actual measured result. `grade_anchors.json` was recalibrated
  for `hero_guild_routing_seed42_500t` only, per Outcome A's own "exactly the run_keys where events
  actually fired" instruction.
