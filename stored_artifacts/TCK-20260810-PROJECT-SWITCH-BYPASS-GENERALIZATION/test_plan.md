---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION
artifact_type: test_plan
tags: [cognition, strategy]
---

# Test Plan — TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION

## Regression Surface

**Unit — `tests/unit/strategic/`**
- `test_interruption_resistance.py` — full file (contains `test_lock_prevents_switch`, being
  updated in-scope, plus `test_interruption_resistance_resume_suspended`,
  `test_profile_derivation_deterministic` and the rest of `TestCognitionProfile`, which exercise
  unrelated `evaluate_project_switch()` paths — the no-current-project and inactive-current-project
  early-return branches, L898-911 — untouched by this ticket and must keep passing unmodified).
- `test_project_continuity.py` — full file (contains `test_project_lock`, being updated in-scope,
  plus `test_interruption_resistance_margin` (L31+, exercises the untouched
  `retention_margin`/`effective_current_score` formula with an *unlocked* current project — no lock
  branch involved, must be unaffected) and `test_project_continuity_resume_suspended`).
- `test_strategic_hardening.py` — unrelated (STRAT-221-224, interaction-interrupt logic) but lives in
  the same directory; scoped run will include it, must still pass.
- Any other file under `tests/unit/strategic/` that constructs `ProjectState` with `lock_until_tick`
  and calls `evaluate_project_switch()` (grep for call sites before Implement finalizes, to make sure
  none besides the two named tests silently assumed the old allowlist).

**Unit — `tests/unit/domains/adventure/`**
- `test_phase3_adventure_decision_boundary.py`, `test_phase3_adventure_decision_service.py`,
  `test_phase3_route_families.py`, `test_phase3_route_generator.py`, `test_phase3_route_scoring.py`,
  `test_eligibility_cognition_profile.py` — none currently assert on `evaluate_project_switch()`
  interaction (confirmed no match for that name in `tests/unit/domains/adventure/` at investigation
  time), but all touch `RouteToProjectMapper`/`AdventureDecisionService`/scoring, which sit directly
  upstream of the `mapper.py:100` hardcoded-`score=1.0` fix this ticket's Plan will need to make (see
  investigation.md Risks) — must be re-run to confirm no assertion on `ProjectState.score == 1.0`
  breaks if that value changes.

**Integration**
- `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py` — exercises
  `AdventureDecisionPhase.apply()` end-to-end; will need a new test here for AC3 (see below), and all
  existing tests in this file must keep passing once `apply()` routes through
  `evaluate_project_switch()`.
- `tests/integration/scenarios/test_entity_differentiation.py::
  test_bravery_quartile_combat_rate_2x` — named in the design doc's own Testing section as the
  original failing test this whole batch traces back to; not directly owned by this ticket (batch-level
  regression, likely closed out by whichever ticket in the 4-ticket sequence lands last), but must not
  newly break as a result of this ticket's changes — run it as a smoke check.

**Arena-combat**
- None directly — this ticket does not touch combat resolution. If `CombatEngageScorer`-sourced
  `ProjectState.score` values (System B, used as `candidate_project` in `evaluate_project_switch()`)
  interact with any arena-combat scenario fixture that depends on today's kind-allowlist bypass timing
  (e.g. a scenario relying on a `"danger"`-kind bypass that no longer applies because
  `effective_current_score` isn't cleared), that would surface as a scenario-level regression — no such
  scenario found at investigation time (the `"danger"` kind is confirmed unreachable in production
  code paths), so none identified as regression surface, but flag if Implement discovers one.

## New Tests Required

1. **Generic bypass with a synthetic/novel kind**
   - Category: unit
   - Verifies: a candidate `ProjectState` with a `kind` never seen by the old allowlist (e.g.
     `kind="scavenge"` or similar synthetic string) bypasses an active lock when
     `score > effective_current_score` AND clears the named urgency-floor constant; and is blocked
     when either condition fails (two sub-cases, or two separate tests: "bypasses when both conditions
     met" / "blocked when score clears floor but not effective_current_score" / "blocked when score
     clears effective_current_score but not floor").
   - Location: `tests/unit/strategic/test_interruption_resistance.py` (near `test_lock_prevents_switch`)
     or a new `TestGenericInterruptionBypass` class in the same file — matches AC1 exactly.

2. **`"detour"` remains unconditional structural bypass**
   - Category: unit
   - Verifies: a `kind="detour"` candidate with a low score (below `effective_current_score` and
     below the urgency floor) still bypasses the lock — proves detour truly stays unconditional and
     wasn't accidentally folded into the generic score/floor gate.
   - Location: same file as above.

3. **`"danger"` bypass scenario, tightened**
   - Category: unit (regression per AC4)
   - Verifies: `kind="danger"`, `score > 80` bypasses the lock **only when** `score >
     effective_current_score` also holds (e.g. `current.score` low enough, per AC4's own wording, that
     `effective_current_score` still clears) — must resolve identically to today's behavior in that
     case. A second case (score > 80 but `current.score` high enough that
     `effective_current_score` does NOT clear) must now return `None` where the old code would have
     bypassed unconditionally — this is the explicit, intentional tightening and must be asserted, not
     just the identical-behavior case.
   - Location: same file — this is the direct regression test named in AC4.

4. **Cross-system score normalization — System A candidate vs System B current**
   - Category: unit
   - Verifies (AC2, first half): a maximal System A candidate (score at 100% of its own declared max,
     ~2.9 per `docs/mechanics/04_strategic_cognition.md` §6.6) is not structurally incapable of
     exceeding a low-urgency System B current project, once both are expressed as a percentage of
     their own system's max. Must use the corrected (post-mapper-fix) real score, not the
     `mapper.py:100` placeholder `1.0` — this test is what proves the mapper fix (flagged in
     investigation.md Risks) actually landed.
   - Location: `tests/unit/strategic/test_interruption_resistance.py` or a new
     `tests/unit/strategic/test_score_normalization.py` if Implement introduces a standalone
     normalization helper function worth testing in isolation.

5. **Cross-system score normalization — System B candidate vs System A current, low-urgency guard**
   - Category: unit
   - Verifies (AC2, second half): a low-urgency System A candidate cannot spuriously bypass a
     high-urgency System B current project purely because of the raw ~2.9-vs-100 scale gap — i.e. the
     normalization doesn't just help System A, it also correctly still blocks weak System A candidates
     against strong System B incumbents.
   - Location: same as #4.

6. **`AdventureDecisionPhase.apply()` respects an active System-B lock**
   - Category: integration
   - Verifies (AC3): a hero entity with `current_project_id` pointing at an ACTIVE System-B project
     (e.g. `kind="combat_engage"`, high score, `lock_until_tick` in the future, HP > 80% and no
     hostile nearby so `_threat_resolved()` returns True and the per-hero own-lock gate at
     `phase.py:150` does NOT skip the entity) — `AdventureDecisionPhase.apply()` independently
     proposes a new route the same tick, and the resulting `EntityUpdate` must NOT set
     `current_project_id_set` to the new route's project id while the System-B lock is active and the
     new route's score doesn't clear `effective_current_score`/urgency floor.
   - Location: `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`.

7. **`AdventureDecisionPhase.apply()` still switches when the candidate genuinely clears the bar**
   - Category: integration
   - Verifies: the inverse of #6 — same setup, but the new route's (corrected, real) score clears
     both `effective_current_score` and the urgency floor after normalization; `apply()` must still
     commit the switch. Prevents Implement from over-correcting AC3 into "never switch while any lock
     exists."
   - Location: same file as #6.

8. **Architecture guard — `AdventureDecisionPhase.apply()` never bypasses `evaluate_project_switch()`**
   - Category: architecture guard
   - Verifies: a structural/AST-level or call-tracing check (mirroring the project's existing
     "authoritative application path was used" guard pattern from CLAUDE.md's Architecture Rule) that
     `phase.py`'s project-commit path actually calls `StrategicIntelligenceSystem.
     evaluate_project_switch()` (or an equivalent shared helper) rather than constructing
     `current_project_id_set` directly, so a future edit can't silently reintroduce the unconditional
     overwrite this ticket is fixing.
   - Location: `tests/unit/domains/adventure/` (new file, e.g.
     `test_phase3_project_switch_routing_guard.py`) or added to
     `test_phase3_adventure_decision_boundary.py` if that file already does boundary/architecture-style
     assertions (confirm at Implement time).

9. **Mapper score fidelity**
   - Category: unit
   - Verifies: `RouteToProjectMapper.map_to_states()` (or its caller) produces a `ProjectState.score`
     that reflects the real `AdventureRouteOption.score`, not the hardcoded `1.0` — a direct regression
     test for the mapper fix identified in investigation.md, since none of tests #1-8 would fail loudly
     if this fix were silently reverted (they construct `ProjectState` directly in most cases rather
     than going through the real mapper).
   - Location: `tests/unit/domains/adventure/test_phase3_route_families.py` (or wherever
     `RouteToProjectMapper` is currently tested — confirm exact file at Implement time) or
     `tests/unit/domains/adventure/test_phase3_adventure_decision_service.py`.

## Scoped Pytest Commands

```
pytest tests/unit/strategic/ -v
pytest tests/unit/domains/adventure/ -v
pytest tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py -v
pytest tests/integration/scenarios/test_entity_differentiation.py::test_bravery_quartile_combat_rate_2x -v
```
Do not run `pytest tests/` — scope is limited to the strategic/cognition and adventure domains per
this ticket's Related Code Areas.

## Anti-Drift Test Guards

- **`test_interruption_resistance_margin`** (`test_project_continuity.py`) exercises the
  `retention_margin`/`effective_current_score` formula on an *unlocked* current project — this ticket
  must not touch that formula. If this test's assertions change, that's a signal the formula itself
  was touched, which is out of scope.
- **`test_interruption_resistance_resume_suspended`** and **`test_project_continuity_resume_suspended`**
  exercise `resume_project()`, a function explicitly untouched by this ticket per investigation.md's
  Anti-Drift Hazards — must keep passing byte-for-byte with no assertion changes.
- **A test asserting `RouteToProjectMapper.map_to_states()`'s other fields** (`id`, `kind`,
  `lock_until_tick`, `objectives`) **are unaffected by the score fix** — guards against the mapper fix
  (test #9) accidentally touching unrelated fields while threading the real score through.
- **A test confirming `GoalKind`/`ProjectKind` are NOT unified/merged by this change** — the generic
  bypass rule must work with `kind` as an unenforced string; if Implement is tempted to "clean up" the
  vocabulary split while generalizing the allowlist, a guard test asserting both enums still diverge
  (or at minimum that `evaluate_project_switch()` doesn't newly require `kind` to be a `ProjectKind`
  enum member) would catch an accidental scope-creep fix of the D22/C4-owned issue.
- **A test confirming the eligibility gate (`supports_adventure_routing`, C1's own change, already
  DONE) is untouched** — e.g. re-run `test_eligibility_cognition_profile.py` unmodified and confirm no
  diff is needed, guarding against this ticket accidentally touching ticket 1's landed work while in
  the same file (`phase.py`).
- **A test on `docs/parity_ledger/strategic_cognition.yaml`'s schema validity** (existing repo-wide
  parity-ledger schema check, if one exists — confirm via `docs/parity_ledger/schema.json` at Implement
  time) to guard against the STRAT-185/186/187 `test_path` update introducing a malformed entry.
