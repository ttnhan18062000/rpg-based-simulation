---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION
artifact_type: plan
tags: [combat, calibration]
---

# Implementation Plan — TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION

## Summary

Fix `test_bravery_quartile_combat_rate_2x` per the user's approved approach — multi-seed averaging
+ larger population per seed — by (1) doubling `_build_differentiation_spec()`'s population from
8 heroes/4 monsters to 16 heroes/8 monsters while scaling the arena from 32×32 to 45×45 to hold
spawn density constant, (2) replacing the single `SEED=42` run with a fixed, unbiased 24-seed loop
(`SEEDS = list(range(1, 25))`), (3) aggregating bottom/top-quartile `combat_engage` rates as the
mean of each seed's own rate (not a single-seed extreme-pair comparison), and (4) recalibrating the
pass threshold from `>= 2.0x` down to `>= 1.5x`, because live empirical measurement at this exact
population/seed methodology (run directly against current HEAD as part of this planning session,
not estimated) converges to a real, reproducible ~1.74x aggregate ratio — genuinely bravery-driven
and directionally consistent, but never approaching 2x. All five of the ticket's required Plan
decisions are resolved below with the concrete evidence that grounds them; no numbers here are
arbitrary — every population/seed-count/threshold value was verified by actually running the
scenario at HEAD before being written into this plan (see per-step evidence). A 6th step adds one
new test to `tests/unit/strategic/test_score_normalization.py` — a documented-limitation regression
guard required by test_plan.md's own AC2 New Test #3, pinning the current (buggy, separately-ticketed)
behavior of C2's normalization gate rather than fixing it here. Two doc/ledger locations that assert
the stale "4.92x, System A" claim must be corrected as part of this ticket's own AC2 (flagged for the
Parity and Docs phases, not implemented directly by this plan's steps, since those are
separately-owned phases in this repo's 10-phase pipeline — see "Required Follow-on" in Anti-Drift
Notes).

## Required Plan Decisions — resolved

**1. Seeds and population.** Methodology used (reproducible by Implement if re-verification is
ever needed): ran the exact tick-loop/quartile logic from
`tests/integration/scenarios/test_entity_differentiation.py:169-258` against HEAD, unmodified except
for population and seed, across 32 sequential seeds (`1..32`, chosen unbiased — not cherry-picked)
at the current 8-hero/4-monster population, then again at a doubled 16-hero/8-monster population
with the arena scaled from 32×32 to 45×45 (density-matched, see Step 1). Findings:
- At 8 heroes (today's population), `q_size = max(1, n//4)` stayed at 1 for **all 16** sampled
  seeds (`n_alive` ranged 3–7), confirming the statistical collapse is not a SEED=42-specific fluke
  — it is structural at this population size.
- At 16 heroes/45×45 arena, across all 32 sampled seeds, `q_size` was **always >= 2** (range 2–3,
  `n_alive` range 8–15) — the collapse is fixed at this population size.
- Density matters: a control run of 16 heroes/8 monsters in the *original* 32×32 arena (denser
  packing, not scaled) still collapsed `q_size` to 1 in 2 of 8 sampled seeds (higher lethality from
  denser combat) — confirms the arena must scale with population, not just the entity count.
- Runtime: 24 seeds at 16-hero population measured **128.8s wall-clock** total (tick-loop only,
  `no_frame_pacing=True`, ~5.4s/seed) — see decision on CI tier below.
- **Decision: 24 seeds (`SEEDS = list(range(1, 25))`), 16 heroes + 8 monsters, arena scaled to
  45×45.** 24 was chosen (not 32) because the aggregate ratio stabilizes by seed-count 24
  (cumulative ratio-of-means: n=20 → 1.75, n=24 → 1.74, n=28 → 1.74, n=32 → 1.71 — flat within
  ~0.04 from 20 seeds onward), so 24 captures the stable value without paying for 8 more seeds of
  runtime for no material precision gain.

**2. Statistic and threshold.** Chosen: **(a) — average each seed's own `top_rate`/`bottom_rate`
across all 24 seeds, then apply the ratio comparison to the two averaged values** (not per-seed
majority-vote, not a full-population correlation coefficient). Rationale: each seed is one
independent trial of the same experiment; averaging trial-level rates (rather than pooling raw tick
counts unevenly weighted by each seed's differing `q_size`) treats every seed as one equally-weighted
sample, which is the simplest defensible aggregation and matches this ticket's own required-decision
wording verbatim. Measured at HEAD with this exact methodology: mean `bottom_rate` = 0.4576, mean
`top_rate` = 0.7972, ratio = **1.7421** across `SEEDS = 1..24`. This is a real, reproducible,
positive signal (not noise): it held stable across four different seed-count cuts (20/24/28/32, all
within 1.71–1.75) and is corroborated by a pooled per-hero Pearson correlation between bravery and
individual `combat_engage` rate of **r = 0.316** (n=371 hero-seed observations, positive, moderate)
computed across all 32 sampled seeds at the 16-hero population — up from a population that, at
8 heroes, showed **no consistent correlation at all** (2 of 16 sampled seeds even showed negative
per-seed correlation; see investigation.md's own "no bravery correlation across the full alive
population" finding, now explained: undersized population, not absence of signal).
**Threshold: recalibrated from `>= 2.0x` to `>= 1.5x`.** This exercises AC2's explicit
recalibration allowance rather than defaulting to keeping 2x. Rationale: the measured 1.7421
converged value has ~0.24 of margin above 1.5x (14% headroom) — enough to avoid the test being a
coin-flip on ordinary determinism, while 1.5x is still a real, meaningful, bravery-predictive bar
(not "any ratio above 1.0," which would validate noise). 2x was never achievable at this or any
tested population/seed combination without cherry-picking a favorable seed subset, which the
investigation's own "do not curve-fit" instruction (test_plan.md, New Tests Required §AC2)
explicitly rules out.

**3. Population size.** Resolved above in (1): 16 heroes + 8 monsters (2x today's 8+4), arena
scaled 32×32 → 45×45. Density check: original 1024 sq units / 12 entities = 85.3 sq units/entity;
new 2025 sq units / 24 entities = 84.4 sq units/entity (within 1.1% of original density — arena
scaling is not arbitrary, it is the side length that preserves original per-entity spawn density
for double the entity count: `sqrt(12 × (32²/12) × 2) ≈ 45.25`, rounded to 45).

**4. `RESOLVE_BLOCKER` / same-system confound.** No dedicated mitigation — out of scope, expected
to average out. This was already implicitly present, un-mitigated, in every seed of the calibration
data above (the calibration script measures `combat_engage` rate exactly as the production test
does — any tick a hero spends in `resolve_blocker`, `social`, or any other competing goal is
correctly counted as "not combat_engage," with no special-casing), and the resulting 24-seed
aggregate still produced a stable, real, positive 1.74x signal. If this confound were dominant
enough to erase the bravery signal, the measured ratio would not have stabilized as tightly as it
did (1.71–1.75 across four different seed-count cuts). No further investigation needed for this
ticket's own scope.

**5. Loop structure.** Inline `for seed in SEEDS:` loop inside the single test function (matching
this repo's own precedent in `tests/integration/observability/test_sweep_execution_flow.py:34`,
`for seed in [1, 2, 3]:`), with the per-seed heavy lifting factored into a new module-level helper
`_run_quartile_ticks_for_seed(spec, seed)` — matching this exact file's existing helper-function
convention (`_build_differentiation_spec()`, `_test_profile()`, lines 37–111). **Not**
`@pytest.mark.parametrize` — parametrize would produce 24 independent per-seed test nodes each
asserting pass/fail individually, which is wrong here since the decision in (2) is to assert on the
*aggregate*, not on any individual seed (individual seeds are noisy and not expected to
individually clear the threshold — confirmed: only 11 of 30 individually-sampled seeds at the
16-hero population cleared 2x, and per-seed ratios ranged from 0.49 to 74.0 in the wider 32-seed
scan).

## Steps

### Step 1 — Scale `_build_differentiation_spec()` population and arena

**Files:** `tests/integration/scenarios/test_entity_differentiation.py`

**Change:** Modify `_build_differentiation_spec()` (currently lines 37–93, read and verified this
session) in place:
- `topology.width` / `topology.height`: `64` → `90`
- `regions[0]` ("arena"): `bounds: [0, 0, 32, 32]` → `bounds: [0, 0, 45, 45]`
- `regions[1]` ("village"): `bounds: [33, 33, 63, 63]` → `bounds: [46, 46, 89, 89]`
- `entities[0]` ("heroes_group"): `count: 8` → `count: 16`
- `entities[1]` ("monsters_group"): `count: 4` → `count: 8`
- Update the function's own docstring (currently lines 38–45) to state the new counts/bounds and
  cite this ticket for the density-preservation rationale (45×45 chosen to hold ~85 sq
  units/entity constant when population doubles from 12 to 24 entities — see Plan decision 3).

This is the ONLY spec change needed — `WorldSpec.model_validate()` (imported at line 22, used at
line 128/171) accepts these values with no schema changes required; verified this session by
constructing and validating a `WorldSpec` with these exact values and running it through
`WorldCompiler.compile()` across 32 different seeds with no validation or compile errors.

**Do NOT touch:** `factions`, `resources`, `buildings`, `quests` keys (all stay empty/unchanged);
`world_id`/`name`/`schema_version` (unchanged); do not add a third region or change `terrain`.

**Verify:** `tests/integration/scenarios/test_entity_differentiation.py::test_no_identical_personality_vectors_at_spawn`
must still pass unmodified against the new spec — verified this session directly: ran
`WorldCompiler.compile(spec, seed=X)` for X in {42, 1, 7} against the new 16h/8m/45×45 spec and
confirmed 24/24 unique personality vectors at every seed, zero duplicates.

---

### Step 2 — Add the `SEEDS` module constant, keep `SEED` for Test 1

**Files:** `tests/integration/scenarios/test_entity_differentiation.py`

**Change:** At the module-level constants block (currently lines 29–30):
```python
TICKS = 400
SEED = 42                    # used by test_no_identical_personality_vectors_at_spawn only
SEEDS = list(range(1, 25))   # 24 seeds, used by test_bravery_quartile_combat_rate_2x's aggregate
```
`SEED = 42` is kept, unchanged, and continues to be the only seed
`test_no_identical_personality_vectors_at_spawn` (lines 118–144) uses — that test is unaffected by
this ticket except that it now compiles the larger (16h/8m) spec from Step 1, which Step 1's own
Verify already confirmed still passes. `TICKS = 400` is unchanged — kept for continuity with the
calibration data above (all measurements in this plan used `TICKS=400`; shrinking it was
considered and rejected, see Anti-Drift Notes).

**Do NOT touch:** `test_no_identical_personality_vectors_at_spawn`'s own body (lines 119–144) — it
already reads module-level `SEED`, needs no code change, only benefits from Step 1's spec change
and this step's untouched `SEED` constant.

**Verify:** No new test — this step is a prerequisite for Steps 3–4. Confirmed by Step 1's own
Verify (uses `SEED` implicitly via `_build_differentiation_spec()`'s consumers).

---

### Step 3 — Extract the per-seed run into a helper function

**Files:** `tests/integration/scenarios/test_entity_differentiation.py`

**Change:** Add a new module-level helper, placed after `_test_profile()` (after line 111, before
the Test 1 section comment at line 114):

```python
def _run_quartile_ticks_for_seed(spec: WorldSpec, seed: int) -> dict:
    """
    Compile `spec` at `seed`, run TICKS ticks with combat/adventure flags ON, and return
    per-seed quartile tick-counts (not rates — rates are computed by the caller after
    aggregating across all seeds in SEEDS).

    Returns a dict with keys: n_alive, q_size, bottom_combat_ticks, bottom_total_ticks,
    top_combat_ticks, top_total_ticks.
    """
    initial_state, _report = WorldCompiler.compile(spec, seed=seed)
    initial_state = replace(
        initial_state,
        feature_flags={
            "ENABLE_COMBAT_ENGAGEMENT": "ON",
            "ENABLE_ADVENTURE_ROUTING": "ON",
        },
    )
    project_kind_history: dict[int, list[str | None]] = defaultdict(list)
    rng = DeterministicRNG(seed)
    kernel = Kernel(_test_profile(), initial_state, rng, flags={"no_replay": True, "no_frame_pacing": True})
    try:
        for _ in range(TICKS):
            kernel.tick_once()
            for eid, ent in kernel.state.entities.items():
                cur_proj_id = ent.strategic.current_project_id
                if cur_proj_id and cur_proj_id in ent.strategic.projects:
                    kind = ent.strategic.projects[cur_proj_id].kind
                    project_kind_history[eid].append(
                        kind.value if hasattr(kind, "value") else str(kind)
                    )
                else:
                    project_kind_history[eid].append(None)
        final_state = kernel.state
    finally:
        kernel.shutdown()

    hero_entities = [
        ent for ent in final_state.entities.values()
        if ent.kind.lower() == "hero" and ent.combat.alive
    ]
    hero_entities.sort(key=lambda e: e.identity.personality.bravery)
    n = len(hero_entities)
    q_size = max(1, n // 4)
    bottom_quartile = hero_entities[:q_size]
    top_quartile = hero_entities[n - q_size:]
    combat_engage_value = GoalKind.COMBAT_ENGAGE.value

    def _ticks(entity_list):
        total = sum(len(project_kind_history[e.id]) for e in entity_list)
        combat = sum(
            1 for e in entity_list for k in project_kind_history[e.id]
            if k == combat_engage_value
        )
        return combat, total

    bottom_combat_ticks, bottom_total_ticks = _ticks(bottom_quartile)
    top_combat_ticks, top_total_ticks = _ticks(top_quartile)

    return {
        "n_alive": n,
        "q_size": q_size,
        "bottom_combat_ticks": bottom_combat_ticks,
        "bottom_total_ticks": bottom_total_ticks,
        "top_combat_ticks": top_combat_ticks,
        "top_total_ticks": top_total_ticks,
    }
```

This is a direct extraction of the existing per-seed logic currently inline at lines 169–246 (compile
→ set flags → tick loop → sample `current_project_id` → sort by bravery → slice quartiles → compute
tick counts) — no behavioral change to any single seed's own computation, only a change in *how many
times* it runs and *what* the caller does with the result (Step 4).

**Do NOT touch:** the tick-sampling logic itself (must stay identical to today's lines 193–205 —
`current_project_id` → `projects[id].kind`, not `transaction_trace` or `entity_timeline_store`, per
the existing anti-drift notes in the file's own docstring, lines 162–165).

**Verify:** No standalone test for the helper — verified indirectly by Step 4's test passing with
the same aggregate numbers measured in this planning session (mean bottom_rate ≈0.4576, mean
top_rate ≈0.7972 at `SEEDS=1..24`).

---

### Step 4 — Rewrite the test body: multi-seed loop, aggregation, population guard, recalibrated assertion

**Files:** `tests/integration/scenarios/test_entity_differentiation.py`

**Change:** Replace `test_bravery_quartile_combat_rate_2x`'s body (currently lines 169–258) with:

```python
def test_bravery_quartile_combat_rate_2x():
    spec = _build_differentiation_spec()

    bottom_rates: list[float] = []
    top_rates: list[float] = []

    for seed in SEEDS:
        result = _run_quartile_ticks_for_seed(spec, seed)

        assert result["q_size"] >= 2, (
            f"seed={seed}: quartile size collapsed to {result['q_size']} "
            f"(n_alive={result['n_alive']}) -- population guard failed. "
            f"See TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION Plan decision 1: "
            f"16 heroes/8 monsters at a 45x45 arena should keep n_alive >= 8 (q_size >= 2) "
            f"in every one of the 24 calibrated seeds. A collapse here means either the spec "
            f"or the seed list drifted from what was calibrated."
        )

        bottom_rates.append(
            result["bottom_combat_ticks"] / max(1, result["bottom_total_ticks"])
        )
        top_rates.append(
            result["top_combat_ticks"] / max(1, result["top_total_ticks"])
        )

    bottom_rate = sum(bottom_rates) / len(bottom_rates)
    top_rate = sum(top_rates) / len(top_rates)

    # Diagnostic gate: if the AGGREGATE bottom_rate is 0, the flags or proximity setup is broken.
    # (Individual seeds occasionally show bottom_rate == 0 -- e.g. seed 22 in the 24-seed
    # calibration set -- that is expected per-seed noise, not a broken setup; only an
    # all-zero aggregate indicates a structural problem.)
    assert bottom_rate > 0, (
        f"Aggregate bottom-quartile combat_engage rate is 0 across all {len(SEEDS)} seeds "
        f"after {TICKS} ticks each. Check ENABLE_COMBAT_ENGAGEMENT flag and entity proximity "
        f"in the arena region."
    )

    assert top_rate >= 1.5 * bottom_rate, (
        f"Top-quartile combat_engage rate ({top_rate:.4f}, averaged across {len(SEEDS)} seeds) "
        f"is less than 1.5x bottom-quartile rate ({bottom_rate:.4f}). "
        f"Recalibrated threshold per TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION "
        f"(measured ~1.74x at this population/seed methodology; see that ticket's stored plan.md "
        f"for the calibration evidence -- this is no longer TCK-20260619-E11D-SCORING-CAL's "
        f"stale 4.92x/System-A baseline)."
    )
```

This directly implements decisions (2) (mean-of-per-seed-rates aggregation, 1.5x threshold) and (5)
(inline loop + helper). The population guard (`q_size >= 2`) implements test_plan.md's New Test #2
("population guard") as an inline assertion inside the existing test rather than a separate test
function — test_plan.md itself said this is "likely" the cheaper, acceptable form ("Category: unit
or integration (whichever is cheaper — likely a lightweight assertion inside the existing test
rather than a separate one)").

**Do NOT touch:** `CombatEngageScorer`/`CombatRetreatScorer` (`src/ai/goals/scorers.py`) — no diff to
this file is part of this plan, per investigation.md's confirmed-correct sign finding and
test_plan.md's explicit anti-drift guard. Do NOT touch
`StrategicIntelligenceSystem.evaluate_project_switch()` / `_score_scale_max()`
(`src/systems/strategic_systems/intelligence.py`) — that is
`TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG`'s own scope, filed separately. Do NOT
revive `RouteFamily.HUNT_WEAK_ENEMY` in `src/domains/adventure/generator.py`.

**Verify:** `pytest tests/integration/scenarios/test_entity_differentiation.py::test_bravery_quartile_combat_rate_2x -v`
passes. Expected real values at `SEEDS=1..24`: `bottom_rate ≈ 0.4576`, `top_rate ≈ 0.7972`, ratio
`≈ 1.74` (`>= 1.5` holds with ~0.24 margin). Exact floats may shift in the low decimal places
between this calibration run and the final landed code (this plan's calibration script computed
rates slightly differently — via a standalone `run_one()` helper, not byte-for-byte the same code
as Step 3's `_run_quartile_ticks_for_seed()` — the two are logically equivalent but Implement should
not treat 0.4576/0.7972 as an exact-match assertion target, only as the expected order of magnitude
confirming the 1.5x threshold has real margin).

---

### Step 5 — Update marker and docstring

**Files:** `tests/integration/scenarios/test_entity_differentiation.py`

**Change:** At lines 151–152, change `@pytest.mark.slow` → `@pytest.mark.extra_slow` (keep
`@pytest.mark.integration`). Rationale: `pyproject.toml:69` defines `extra_slow` as "marks tests as
extremely slow (>60s...)" — the new 24-seed loop measured 128.8s wall-clock for the tick loops alone
this session, definitively over the 60s line the marker taxonomy draws. This does not change which
CI job runs the test: `.github/workflows/test.yml`'s "Integration" job already filters
`-m "not slow and not extra_slow"` (line 109) so this test is excluded from that job either way; both
markers are only ever included together by the "Slow regression" job (line 232:
`pytest tests/ -m "slow or extra_slow" --resource-budget large ...`), which already grants a 600s
per-test limit (`tests/conftest.py:83-85`, `large` budget = 600s). 128.8s fits comfortably (21% of
budget) with no CI-tier change needed — this test already lives in the slow/nightly-equivalent tier,
not the PR-blocking fast tier, confirmed by reading `.github/workflows/test.yml` directly this
session (not assumed).

Also rewrite the docstring (currently lines 154–168): remove the stale "E11D confirmed 4.92× ratio"
claim (investigation.md's post-batch section confirms this number is not reproducible under any
current code path — `RouteFamily.HUNT_WEAK_ENEMY` is dead, so E11D's original measurement, if it
used that route family, cannot be what's being measured today). Replace with a description of the
24-seed/16-hero methodology, cite `TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION` as the
authority for the 1.5x threshold and the measured ~1.74x aggregate, and update the runtime-budget
note (60s conftest medium-budget framing no longer applies at the `extra_slow`/large-budget tier —
replace with the 128.8s measured total and the 600s large-budget ceiling).

**Do NOT touch:** `@pytest.mark.integration` (line 152, unchanged) — the test still belongs to the
integration taxonomy category, only its speed-tier marker changes.

**Verify:** `pytest --collect-only -m "extra_slow and integration" tests/integration/scenarios/test_entity_differentiation.py`
collects the test; `pytest --collect-only -m "not slow and not extra_slow" tests/integration/scenarios/test_entity_differentiation.py`
does NOT collect it (confirms it's excluded from the fast/PR-blocking tier, same as before).

---

### Step 6 — Add the documented-limitation regression guard test (required by test_plan.md's AC2 New Test #3)

**Files:** `tests/unit/strategic/test_score_normalization.py`

**Change:** `test_plan.md`'s own New Test #3 (its AC2 section) requires this test regardless of
which direction Plan takes on the normalization defect: since this ticket does NOT fix
`retention_margin`/`current_max` normalization (filed separately as
`TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG`, per Scope Guards below), test_plan.md
specifies the **documented-limitation regression guard** form — assert the gate is currently
unreachable in the [locked System-A `current`, System-B `candidate`] direction, so a future silent
behavior change (in either direction — the bug getting fixed, or getting worse) is caught, not
missed. An earlier draft of this plan omitted this test entirely; added after architecture review
flagged the omission against test_plan.md's own explicit "required" framing.

Add, co-located with C2's existing cross-system tests in the same file (matching the file's own
docstring/import/`_make_entity` helper conventions):

```python
def test_locked_system_a_current_unreachable_by_system_b_candidate_documented_limitation():
    """Documented-limitation regression guard, not a desired-behavior test.

    TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION's post-batch re-investigation
    confirmed, via a live 1365-call trace, that 0 of 24 real evaluate_project_switch() calls
    made while current.lock_until_tick > current_tick ever passed -- retention_margin(9.0) /
    _ADVENTURE_ROUTE_SCORE_MAX(2.9) ~ 3.10 alone exceeds any realistic System-B candidate_pct,
    so a locked System-A current can never be interrupted by a System-B candidate today,
    regardless of urgency. This is a real, confirmed, independently-ticketed defect
    (TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG), not fixed by this ticket.
    This test pins the CURRENT (buggy) behavior so a future change to either direction --
    the bug getting silently fixed, or a regression making it worse -- is caught and requires
    an explicit decision, not missed by accident.
    """
    current = ProjectState(
        id="current", kind=ProjectKind.SOCIAL, status=ProjectStatus.ACTIVE,
        score=0.1, lock_until_tick=100  # minimal-score, freshly-locked System-A current
    )
    entity = _make_entity(
        profile=CognitionProfile(interruption_resistance=0.3, resistance_multiplier=30.0),
        current_project=current
    )
    # Maximal-urgency System-B candidate: CombatEngageScorer's own real ceiling is
    # 40 + bravery(1.0)*40 + stamina_ratio(1.0)*20 = 100 -- the highest realistic value.
    candidate = ProjectState(
        id="candidate", kind=GoalKind.COMBAT_ENGAGE, status=ProjectStatus.ACTIVE, score=100.0
    )
    result = StrategicIntelligenceSystem.evaluate_project_switch(entity, candidate, current_tick=50)
    assert result is None, (
        "If this now returns a StrategicUpdate, TCK-20260811-INTERRUPTION-BYPASS-RETENTION-"
        "MARGIN-SCALE-BUG's normalization defect has been fixed (or the formula changed) -- "
        "update this test to assert the new, intended behavior instead of the documented "
        "limitation, and close/update that ticket accordingly. Do not just delete this test."
    )
```

**Do NOT touch:** Any other test in this file (`test_max_adventure_route_candidate_can_exceed_low_urgency_goal_current`,
`test_weak_adventure_route_candidate_blocked_by_high_urgency_goal_current`) — both stay exactly as
C2 landed them.

**Verify:** `pytest tests/unit/strategic/test_score_normalization.py -v` — all 3 tests (2 existing + 1
new) pass.

## Scope Guards

Explicit list of things this plan must not touch:

- `src/ai/goals/scorers.py` (`CombatEngageScorer`, `CombatRetreatScorer`) — bravery sign/coefficients
  already confirmed correct by investigation.md; any diff here is scope creep, not a fix.
- `src/systems/strategic_systems/intelligence.py` (`evaluate_project_switch()`, `_score_scale_max()`,
  the `retention_margin`/`current_max` normalization constants) — this is
  `TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG`'s own scope, filed separately by
  this ticket's own investigation as a real, confirmed, independent defect. Not touched here.
- `src/domains/adventure/generator.py` (`AdventureRouteGenerator.generate()`) — do not revive
  `RouteFamily.HUNT_WEAK_ENEMY`; investigation.md already determined this would build a second,
  redundant combat-decision path duplicating `GoalRegistry`'s legitimate ownership.
- `src/domains/adventure/phase.py`, `src/domains/adventure/mapper.py` — C2's own landed files, not
  touched by this ticket.
- `tests/unit/strategic/test_interruption_resistance.py`,
  `tests/unit/strategic/test_project_continuity.py` (especially
  `test_interruption_resistance_margin`, C2's explicit anti-drift guard) — C2-owned regression
  surface, must keep passing unmodified, not edited by this plan.
- `tests/unit/strategic/test_score_normalization.py`'s two EXISTING tests
  (`test_max_adventure_route_candidate_can_exceed_low_urgency_goal_current`,
  `test_weak_adventure_route_candidate_blocked_by_high_urgency_goal_current`) — C2-owned, must keep
  passing unmodified. **This file itself is not fully off-limits**: Step 6 adds one new test to it
  (required by test_plan.md's own AC2 New Test #3), co-located with these two, not touching either
  of them.
- `tests/unit/domains/adventure/test_phase3_route_families.py`,
  `test_phase3_project_switch_routing_guard.py`, `test_phase3_adventure_decision_boundary.py`,
  `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py` — C2-owned, not
  touched.
- `test_no_identical_personality_vectors_at_spawn` (Test 1 in the same file) — no assertion-logic
  change, only benefits from Step 1's spec change; do not add new assertions to it.
- `TICKS` module constant — stays `400`; do not shrink it to save runtime (see Anti-Drift Notes).
- The CI workflow file (`.github/workflows/test.yml`) and `pyproject.toml`'s marker definitions —
  this plan only changes which existing marker is applied to one test, not the marker taxonomy or
  job structure itself.

## Dependency Map

- Step 1 (spec change) must land before Steps 3–4 (they consume the new spec's population/arena
  shape for their calibration-derived expected values).
- Step 2 (constants) must land before Step 4 (the test body references `SEEDS`).
- Step 3 (helper extraction) must land before Step 4 (the test body calls the helper).
- Step 5 (marker + docstring) is independent of Steps 1–4's code logic but should land in the same
  commit since it documents the same change — order it last for review clarity.
- Step 6 (test_score_normalization.py guard test) is independent of Steps 1–5 — different file,
  different subsystem, added to satisfy test_plan.md's own AC2 requirement rather than this ticket's
  own test_entity_differentiation.py fix. Can land in any order relative to Steps 1–5.
- All of Steps 1–5 are within one file (`test_entity_differentiation.py`) and are meant to land
  together as one coherent diff; they are listed as separate steps for review granularity, not for
  staged landing across multiple commits. Step 6 touches a second file
  (`test_score_normalization.py`) but lands in the same overall change.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — "Real root cause ... confirmed with direct evidence" | Already satisfied by investigation.md's post-batch section (1365 real `evaluate_project_switch()` calls captured, per-hero trace data) — no plan step needed, this is an investigation-phase deliverable. | N/A (investigation.md itself is the evidence) |
| AC2 — "Fix implemented and the test passes at >= 2x ratio (or the test's own threshold is recalibrated with real evidence...)" | Steps 1–5 (spec scaling, seed loop, aggregation, recalibrated 1.5x threshold, marker/docstring update) + Step 6 (test_plan.md's own required documented-limitation regression guard) | `tests/integration/scenarios/test_entity_differentiation.py::test_bravery_quartile_combat_rate_2x`, `tests/unit/strategic/test_score_normalization.py::test_locked_system_a_current_unreachable_by_system_b_candidate_documented_limitation` |
| AC3 — "Scoped pytest passes (combat, strategic, goals test directories)" | No code change needed in those directories beyond Step 6's addition (Scope Guards above) — verified by re-running the scoped command unchanged | `.venv/bin/python3 -m pytest tests/integration/scenarios/test_entity_differentiation.py tests/unit/strategic/ tests/unit/domains/adventure/ tests/integration/domains/adventure/ tests/unit/ai/goals/ -v` (per test_plan.md's Scoped Pytest Commands; confirm exact goals-scorer test path at Implement time if `tests/unit/ai/goals/` does not exist, per test_plan.md's own caveat) |

## Anti-Drift Notes

- **Do not chase 2x by searching for a more favorable seed subset.** The 1.7421 measured ratio at
  `SEEDS=1..24` was obtained from an unbiased, sequential seed range chosen before looking at
  results (not cherry-picked). If Implement's own run of the final landed code produces a
  meaningfully different ratio (e.g., outside roughly 1.5–2.0), that is a signal something in Step 3's
  extraction diverged from the calibration script's logic — re-diff against this plan's Step 3 code
  block, do not "fix" it by swapping in a different seed range to hit a target number.
- **`TICKS=400` must not be shrunk.** Considered and rejected: all calibration numbers in this plan
  (population collapse fix, 1.74x ratio, 128.8s runtime) were measured at `TICKS=400`. Shrinking
  ticks would invalidate every number in this plan and require re-calibration from scratch — not
  worth it given the 128.8s runtime already fits the `extra_slow`/large-budget CI tier with 79%
  headroom (128.8s of 600s).
- **This ticket does not need a `docs/guidelines/intentional_divergences.md` entry.** Checked
  `docs/mechanics/04_strategic_cognition.md` directly this session (grepped for "quartile",
  "calibrat", "4.92", "combat_engage", "bravery") — the Mechanics Bible documents the risk-multiplier
  *coefficients* (bravery=0.6, caution=0.8) but never codifies the 4.92x/2x quartile-ratio number as
  a Bible-level law. That number lives only in the test's own docstring and two other
  non-Bible-authoritative locations (see Required Follow-on below). Recalibrating it is a test/doc
  correction, not a divergence from an authoritative mechanics law — do not add an
  intentional_divergences.md entry for this.
- **Required Follow-on (not implemented by this plan's own steps — flagged for the Parity and Docs
  phases of this ticket's pipeline run, must land in the same session per this repo's Authoritative
  Mechanics Rule):**
  - `docs/parity_ledger/strategic_cognition.yaml:2472-2488` (entry `STRAT-226`, priority P1, status
    `verified`) currently claims the 2x/4.92x differential is produced by "AdventureRouteScorer['s]
    ... bravery/caution risk multiplier" (System A). Investigation.md's post-batch section directly
    disproves this attribution: `RouteFamily.HUNT_WEAK_ENEMY` (the only combat-tagged System-A route)
    is dead code (`grep -n "HUNT_WEAK_ENEMY" src/domains/adventure/generator.py` returns zero
    matches, confirmed this session and in investigation.md) — the real, live mechanism is System B
    (`GoalRegistry`/`CombatEngageScorer`, `src/ai/goals/scorers.py`), unrelated to
    `AdventureRouteScorer`'s risk multiplier. The Parity phase must correct `STRAT-226`'s `text` and
    `v2_evidence` to name the real mechanism and update the measured ratio to ~1.74x / threshold to
    1.5x, matching this plan's Step 4.
  - `docs/simulation/domains/adventure_contract.md:145-149` ("Calibration Note (E11D, 2026-06-19)")
    makes the same stale claim ("The bravery coefficient (0.6) and caution coefficient (0.8) are
    calibration-tested. Measured baseline: ... 4.92× combat_engage rate ratio"). **Correction to
    investigation.md's own citation**: this doc's real frontmatter is `status: active`, not
    `status: authoritative` (verified directly via `git blame` this session — has been `active`
    since the doc's creation, 2026-06-13; investigation.md's original pre-batch section misstated
    this). This doesn't change what needs fixing — the stale 4.92×/System-A claim is real and still
    needs correcting — but it does mean this doc doesn't carry the same "100% semantic parity,
    same-session update" force CLAUDE.md's Authoritative Mechanics Rule reserves for
    `status: authoritative` docs specifically. The Docs phase should still correct this note (a
    correct, current doc is better than a stale one regardless of authority tier), same real
    mechanism, same recalibrated numbers — just without over-citing an authority level the doc
    doesn't actually have.
  - Both corrections cite this ticket (`TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION`)
    as the source of the corrected measurement, replacing the `TCK-20260619-E11D-SCORING-CAL`
    citation (E11D's own ticket becomes historical-context-only, not the live source of truth for
    this number).
- **The `RouteFamily.HUNT_WEAK_ENEMY` dead-code finding itself is not this ticket's to fix.**
  Investigation.md already concluded reviving it would be the wrong fix (duplicates `GoalRegistry`'s
  legitimate ownership of the combat decision). This plan does not touch `generator.py`; if a future
  ticket wants a guard test asserting `AdventureRouteGenerator.generate()` never yields
  `HUNT_WEAK_ENEMY`, that is new/separate scope, not part of this plan (test_plan.md itself frames
  this as optional and only relevant "if Implement's fix touches `generator.py`" — it does not).
