---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION
artifact_type: plan
tags: [cognition, strategy]
---

# Implementation Plan — TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION

## Summary

Replace the hardcoded `kind=='danger'`/`kind=='detour'` allowlist in
`StrategicIntelligenceSystem.evaluate_project_switch()` (`src/systems/strategic_systems/intelligence.py:881-935`)
with a generic rule: `"detour"` stays the sole unconditional structural bypass; any other candidate,
regardless of `kind`, may bypass an active lock only when its score both exceeds the current project's
`effective_current_score` and clears a named urgency floor — both comparisons evaluated on a
**percentage-of-own-system-max** basis, computed fresh only inside the lock-bypass branch. The
pre-existing raw `effective_current_score` formula and the unlocked-path final comparison
(STRAT-005/006, `intelligence.py:920-925`) are left byte-identical, because `test_interruption_resistance_margin`
(`tests/unit/strategic/test_project_continuity.py`) exercises exactly that raw arithmetic on an unlocked
project and is a protected anti-drift guard. System origin (System A/`AdventureRouteScorer` vs System
B/`GoalRegistry`) is detected via `isinstance(kind, ProjectKind)` — the actual Python enum class identity,
not string value — because `ProjectKind.HARVESTING`/`ProjectKind.SOCIAL` and `GoalKind.HARVESTING`/
`GoalKind.SOCIAL` share identical string values (`src/core/strategic.py:121-148`) and a value-based
classifier would silently misclassify System B candidates as System A. Before any of this can be tested
meaningfully, the pre-existing `RouteToProjectMapper.map_to_states()` hardcoded `score=1.0`
(`src/domains/adventure/mapper.py:100`) must be fixed to carry the real `AdventureRouteOption.score`
through, and `AdventureDecisionPhase.apply()` (`src/domains/adventure/phase.py:189-195`) must be
rewired to call `evaluate_project_switch()` instead of unconditionally overwriting
`current_project_id_set`. The plan closes with the two required existing-test updates, seven new
tests, the STRAT-185/186/187 parity-ledger `v2_evidence`/`test_path` population, and one new
`intentional_divergences.md` entry (rationale class `Enforced`). **`docs/mechanics/04_strategic_cognition.md`
itself is NOT touched by this ticket** — per this ticket's own Out of Scope section ("this ticket is
limited to the intentional_divergences.md entry and parity-ledger entries tied directly to its own code
change") and confirmed correct by architecture review: `TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS`
(C3)'s own ticket Scope explicitly owns "§1-2, including the stale L39 line ... matching the ACTUAL
landed code, not a paraphrase" and is sequenced to run immediately after this ticket for exactly that
reason. An earlier draft of this plan (Step 11) proposed editing §2/§6.6 directly, citing the design
doc's own §4 as authority for a section-based ownership split between this ticket and C3 — that citation
does not exist in the design doc (§4 is a flat deliverable list, not scoped per-ticket) and the claim was
wrong; removed after architecture review flagged it as a real duplicate-work risk with C3.

## Steps

### Step 1 — Read Mechanics Bible sections for law consistency (guard step, no code)
**Files:** `docs/mechanics/04_strategic_cognition.md` (read-only this step)
**Change:** Before touching any code, confirm these two passages, already read and verified during
planning, are the exact baseline Implement is generalizing:
- §2 Interruption Resistance (`docs/mechanics/04_strategic_cognition.md:27-39`): `Switch_Allowed =
  New_Goal_Score > (Current_Goal_Score + Interruption_Margin)`, and the line to be replaced —
  "**Emergency Bypass**: High-urgency 'Danger' concerns (score > 80) ignore the interruption margin."
  (line 39).
- §6.6 Score Range Summary (`docs/mechanics/04_strategic_cognition.md:244-256`): "Total non-blocked:
  0.0 to ~2.9" (line 253) — the authoritative System A ceiling, explicitly labeled "Estimated, No
  Blockers" (not a hard-enforced clamp), which Step 3's `_ADVENTURE_ROUTE_SCORE_MAX` constant must
  match exactly.
This step is read-only law-consistency confirmation — **this ticket does not edit this file at all**
(see Step 11's removal note and Scope Guards; the actual §2/§6.6 doc prose update is C3's own scope,
written against this ticket's final landed code).
**Do NOT touch:** Any section of this file, for any reason — not even the §2/§6.6 content this step
reads for consistency-checking.
**Verify:** No test — this step's output is Implement's own confirmation (in Implementation Notes)
that the two cited line ranges match what Step 3's constants/docstring assume.

### Step 2 — Thread the real route score into `ProjectState.score` (mapper score fidelity)
**Files:** `src/domains/adventure/mapper.py`, `src/domains/adventure/service.py`
**Change:** `RouteToProjectMapper.map_to_states()` currently hardcodes `score=1.0` unconditionally
(`src/domains/adventure/mapper.py:96-105`, confirmed by direct read this session). Its only caller is
`AdventureDecisionService.decide()` (`src/domains/adventure/service.py:141-147`), which already has the
real `selected.score` (an `AdventureRouteOption.score`, ~0-2.9 range per §6.6) in scope at the call site
but currently discards it.
1. In `mapper.py`, add a `score: float = 1.0` parameter to `map_to_states()`'s signature (line 67-74,
   after `tick: int = 0`), and change line 100 from `score=1.0,` to `score=score,`. The default of
   `1.0` preserves today's behavior for any future caller that doesn't pass a score explicitly — grep
   confirmed `map_to_states` has exactly one call site in `src/` today
   (`grep -rn "map_to_states" src/` → only `mapper.py:67` def and `service.py:141` call), so no other
   caller needs updating.
2. In `service.py:141-147`, add `score=selected.score,` to the `RouteToProjectMapper.map_to_states(...)`
   call (between `tick=tick,` and the closing paren).
**Do NOT touch:** Any other field of the `ProjectState`/`ObjectiveState` construction in `mapper.py`
(`id`, `kind`, `lock_until_tick`, `objectives`, `active_objective_id`, `created_tick` all stay as-is —
test_plan.md's anti-drift guard explicitly requires these fields be unaffected by the score fix).
**Verify:** Step 10's new mapper-fidelity test.

### Step 3 — Generalize `evaluate_project_switch()`'s lock-bypass gate (intelligence.py)
**Files:** `src/systems/strategic_systems/intelligence.py`
**Change:** This is the ticket's core logic change, touching lines 881-935 (function body) and the
import block at lines 38-42.

1. Add `ProjectKind` to the existing `from src.core.strategic import (...)` block at lines 38-42 (it
   currently imports `BlockerState, LeadState, LeadCertainty, ProjectState, ProjectStatus,
   ObjectiveState, ObjectiveStatus, CognitionProfile` — `ProjectKind` is not yet imported here,
   confirmed by direct read). `ProjectKind` is defined at `src/core/strategic.py:135-148`; `GoalKind`
   at `src/core/strategic.py:121-132`. Do not import `GoalKind` — it is not needed (see step 3 below).

2. Add three module-level constants near `_MAX_CONSECUTIVE_REJECTIONS` (line 27), following that exact
   precedent style (named constant + comment citing the rationale and the Logic/STRAT ID it serves):
   ```python
   # Declared score ceiling for System A (AdventureRouteScorer) candidates/currents, used only to
   # normalize the lock-bypass comparison below — not a hard clamp on AdventureRouteScorer's own
   # output. Source: docs/mechanics/04_strategic_cognition.md §6.6 "Total non-blocked: 0.0 to ~2.9".
   _ADVENTURE_ROUTE_SCORE_MAX: float = 2.9

   # Declared score ceiling for System B (GoalRegistry) candidates/currents and for any kind not
   # recognized as a real ProjectKind member (synthetic/test kinds default here — GoalRegistry is the
   # universal per-entity baseline, the closer analogue for an unclassified score). Matches the scale
   # the pre-existing "danger" bypass (score > 80) was already implicitly calibrated against.
   #
   # NOT a true hard ceiling: TownScorer (src/ai/goals/scorers.py) can reach ~200 and SleepScorer ~130
   # (confirmed in investigation.md's own scorer survey). This constant is a calibration anchor
   # continuing the pre-existing score>80 threshold, not a claim that no System B scorer exceeds it —
   # a candidate from one of those two scorers can legitimately produce candidate_pct > 1.0, which is
   # intentional (their real-world urgency is genuinely higher, so clearing the floor more easily is
   # correct, not a bug) and does not break the comparison (no clamp exists; percentages simply aren't
   # bounded to [0, 1] for these two scorers). Do not "fix" this by clamping or by raising the constant
   # to 200 — that would only shift which System B scorers under-clear the floor instead.
   _GOAL_UTILITY_SCORE_MAX: float = 100.0

   # Generalized urgency floor for the lock-bypass gate, replacing the old `kind=='danger' and
   # score > 80` special case. 0.8 == 80/100, the exact threshold the code already used before this
   # ticket, expressed as a percentage of _GOAL_UTILITY_SCORE_MAX so it generalizes across kinds and
   # both score systems. STRAT-186.
   _INTERRUPTION_URGENCY_FLOOR_PCT: float = 0.8
   ```

3. Add a module-level helper directly above `evaluate_project_switch` (or as a private staticmethod
   on the class, matching whichever style dominates the file — `_MAX_CONSECUTIVE_REJECTIONS` usage
   at line 1167 is a bare module function call, so a bare function is consistent):
   ```python
   def _score_scale_max(kind) -> float:
       """Return the declared score ceiling for the system that produced `kind`.

       Classification is by the *actual Python enum class* of `kind`, not its string value:
       ProjectKind.HARVESTING and GoalKind.HARVESTING (and ProjectKind.SOCIAL / GoalKind.SOCIAL)
       share identical string values (src/core/strategic.py:121-148) but are different enum classes.
       A value-based check (e.g. `kind in {v.value for v in ProjectKind}`) would silently misclassify
       System B candidates as System A for those two overlapping kinds — do not do that.

       Does not unify or alter the ProjectKind/GoalKind vocabulary split (out of scope, tracked under
       D22/C4) — it only reads the enum identity already present at each ProjectState construction
       site: mapper.py:96-107 always emits real ProjectKind members; intelligence.py's own
       GoalRegistry-sourced candidate (line ~1334) always emits real GoalKind members. Anything else
       (raw strings — "detour", test fixtures, any future third system) defaults to the
       GoalRegistry/universal-baseline scale.
       """
       if isinstance(kind, ProjectKind):
           return _ADVENTURE_ROUTE_SCORE_MAX
       return _GOAL_UTILITY_SCORE_MAX
   ```

4. Replace lines 913-935 (from the `if current.lock_until_tick > current_tick:` line through the
   function's final `return None`) with:
   ```python
   # Logic ID: STRAT-005 (Project switching uses interruption resistance)
   retention_margin = profile.interruption_resistance * profile.resistance_multiplier
   # Logic ID: STRAT-006 (Current project gets retention priority)
   effective_current_score = current.score + retention_margin

   if current.lock_until_tick > current_tick:
       # STRAT-186 (generalized): the lock may be bypassed only for the unconditional "detour"
       # structural override, or when the candidate's score — expressed as a percentage of its own
       # system's declared max — both exceeds the current project's own normalized effective score
       # AND clears the urgency floor. This comparison is intentionally normalized and kept separate
       # from the raw `effective_current_score` comparison below: the raw formula and the unlocked
       # path must stay byte-identical (test_interruption_resistance_margin depends on this).
       if candidate_project.kind == "detour":
           pass
       else:
           candidate_max = _score_scale_max(candidate_project.kind)
           current_max = _score_scale_max(current.kind)
           candidate_pct = candidate_project.score / candidate_max
           normalized_effective_current_pct = (current.score / current_max) + (retention_margin / current_max)
           if not (candidate_pct > normalized_effective_current_pct
                   and candidate_pct > _INTERRUPTION_URGENCY_FLOOR_PCT):
               return None

   if candidate_project.score > effective_current_score:
       return StrategicUpdate(
           projects_add_or_update=[
               replace(current, status=ProjectStatus.SUSPENDED),
               candidate_project
           ],
           current_project_id_set=candidate_project.id,
           current_objective_id_set=candidate_project.active_objective_id
       )

   return None
   ```
   Note the `retention_margin`/`effective_current_score` computation is *relocated* (not rewritten) to
   above the lock check, because the new bypass gate needs `retention_margin` too — this is a pure
   reordering; the two-line formula itself is untouched, and the final `if candidate_project.score >
   effective_current_score:` block below is byte-identical to the pre-existing lines 925-933.

5. Update the function's own docstring (lines 886-892) to describe the new dual-condition rule instead
   of "high-urgency danger/safety projects" — this docstring is the direct source Step 12 (parity
   ledger) draws from, and the source C3 will read when it writes the real §2/§6.6 doc prose against
   this ticket's landed code, so keep it accurate to what was actually built.

**Do NOT touch:** `resume_project()` (line 938+) or `process_project_outcome()` (line 954+) — neither
calls the lock-bypass gate and both are explicitly out of scope. Do not touch the two call sites at
lines 1270 and 1351 — they pass `entity` and a freshly-built `candidate_project` into the *same*
3-argument signature, which is unchanged by this step, so neither call site needs edits. Do not
introduce a `ProjectKind`/`GoalKind` common base or rename either enum's members.
**Other writers to this function's call surface:** `evaluate_project_switch()` has exactly three call
sites today — `intelligence.py:1270` (detour candidate, always `kind="detour"`, unaffected by the new
non-detour branch), `intelligence.py:1351` (System B `GoalRegistry` candidate, `kind=best_candidate.kind`
— a real `GoalKind` member, so `_score_scale_max` correctly resolves it to
`_GOAL_UTILITY_SCORE_MAX`), and — after Step 7 — `phase.py`'s new call (System A candidate, `kind` a
real `ProjectKind` member from Step 2's fixed mapper, resolving to `_ADVENTURE_ROUTE_SCORE_MAX`). No
other production code path constructs a `ProjectState` and calls this function; the two `events.py`
direct-overwrite sites do not call `evaluate_project_switch()` at all and are unaffected (see Scope
Guards).
**Verify:** Step 4 (updated existing tests) and Step 5 (new unit tests).

### Step 4 — Update the two existing tests for the intentional loosening
**Files:** `tests/unit/strategic/test_interruption_resistance.py`,
`tests/unit/strategic/test_project_continuity.py`
**Change:**
- `test_lock_prevents_switch` (`test_interruption_resistance.py:103-115`): current build has
  `candidate = ProjectState(id="rival", kind="quest", status=ProjectStatus.ACTIVE, score=999)` against
  `current` with `score=10, lock_until_tick=100`, `interruption_resistance=0.0`, evaluated at
  `current_tick=50`. Under Step 3's new gate: `candidate.kind="quest"` is a raw string (not a
  `ProjectKind`/`GoalKind` instance) → `_score_scale_max` returns `_GOAL_UTILITY_SCORE_MAX=100.0` →
  `candidate_pct = 999/100 = 9.99`; `current_max=100.0` (current.kind is also a raw string) →
  `normalized_effective_current_pct = 10/100 + 0/100 = 0.1`; `9.99 > 0.1` and `9.99 > 0.8` → bypasses.
  Update the test's docstring/assertion: rename to reflect "lock prevents switch for scores that don't
  clear the urgency floor" and change the assertion to `assert result is not None` +
  `assert result.current_project_id_set == "rival"`, OR (preferred, to still assert something is
  blocked by a lock) lower `candidate.score` to a value below the floor (e.g. `score=50`, giving
  `candidate_pct=0.5 < 0.8`) so the test still demonstrates a lock blocking a low-urgency candidate,
  while adding a second assertion/case with `score=999` proving the loosening. Implement should choose
  whichever reads clearest; the important part is the test must no longer claim "regardless of score."
- `test_project_lock` (`test_project_continuity.py:59-80`): same shape — `candidate` has `score=100.0,
  kind="combat"` (raw string → `_GOAL_UTILITY_SCORE_MAX`), `current` has `score=10.0,
  lock_until_tick=200, resistance=0.1`. At `current_tick=100`: `candidate_pct=1.0`,
  `normalized_effective_current_pct = 10/100 + 3/100 = 0.13` → `1.0 > 0.13` and `1.0 > 0.8` → bypasses.
  Update the first assertion (currently `assert up is None`) to reflect the new bypass, or lower the
  candidate score below the 80% floor (e.g. `score=50.0` → `candidate_pct=0.5`) to keep demonstrating a
  genuinely-blocked case, with a second higher-score case proving the loosening — same choice as above,
  apply consistently across both files.
**Do NOT touch:** `test_switch_when_no_current_project`, `test_retention_when_candidate_below_margin`,
`test_switch_when_candidate_exceeds_margin`, `test_higher_resistance_prevents_more_switches`,
`test_interruption_resistance_resume_suspended` (all exercise the unlocked path or `resume_project()`,
untouched by Step 3). Do NOT touch `test_interruption_resistance_margin` or
`test_project_continuity_resume_suspended` in `test_project_continuity.py` — both are explicit
anti-drift guards per test_plan.md.
**Verify:** Both updated tests pass; `pytest tests/unit/strategic/test_interruption_resistance.py
tests/unit/strategic/test_project_continuity.py -v`.

### Step 5 — Add new unit tests for the generalized bypass rule
**Files:** `tests/unit/strategic/test_interruption_resistance.py` (new `TestGenericInterruptionBypass`
class, placed after `TestInterruptionResistance`)
**Change:** Add these tests, matching test_plan.md items 1-3:
- `test_generic_kind_bypasses_when_score_and_floor_clear`: candidate with a novel kind never seen by
  the old allowlist (e.g. `kind="scavenge"`), score chosen so `candidate_pct > 0.8` (e.g. `score=90`
  against `_GOAL_UTILITY_SCORE_MAX=100` → `0.9`) and clearly above the current's normalized effective
  score (e.g. `current.score=5`, low resistance). Assert bypass succeeds
  (`result.current_project_id_set == candidate.id`).
- `test_generic_kind_blocked_when_floor_not_cleared`: same synthetic kind, score high enough to exceed
  `current`'s normalized effective score but below 0.8 of `_GOAL_UTILITY_SCORE_MAX` (e.g. `score=60` →
  `0.6 < 0.8`). Assert `result is None`.
- `test_generic_kind_blocked_when_effective_current_not_cleared`: same synthetic kind, score above the
  0.8 floor but `current` has a high enough score/resistance that
  `normalized_effective_current_pct` still exceeds `candidate_pct` (e.g. `candidate.score=85`,
  `current.score=90`, `resistance=0.5`). Assert `result is None`.
- `test_detour_bypasses_lock_unconditionally`: `candidate = ProjectState(..., kind="detour", score=1.0)`
  — deliberately below both the floor and `current`'s effective score — against a locked, high-score
  `current`. Assert bypass still succeeds, proving `"detour"` was not folded into the generic
  score/floor gate.
- `test_danger_bypass_still_works_when_effective_current_clears`: `candidate` with `kind="danger",
  score=85` (i.e. `>80`, matching the old special-cased threshold), `current.score` low enough that
  `effective_current_score` (raw) and `normalized_effective_current_pct` both clear — e.g.
  `current.score=10`, default resistance. Assert bypass succeeds — this is AC4's "resolves identically"
  half.
- `test_danger_bypass_blocked_when_effective_current_not_cleared`: same `candidate` (`kind="danger",
  score=85`), but `current.score`/resistance raised so `current`'s normalized effective score exceeds
  `candidate_pct` (e.g. `current.score=90, resistance=0.8` → `normalized_effective_current_pct =
  0.9 + 24/100 = 1.14 > 0.85`). Assert `result is None` — this is AC4's "intentional tightening" half,
  and must not have existed as a passing scenario under the old code (old code bypassed unconditionally
  whenever `kind=="danger" and score>80`, ignoring `current` entirely).
**Do NOT touch:** Do not add any test using `kind="danger"` sourced from a live production code path —
per investigation.md, no production `ProjectState(` construction site ever sets `kind="danger"`; these
are deliberately hand-constructed per AC4's own framing ("a specified contract, not observed live
behavior" — reflected in Step 13's divergence note wording, not asserted here as a corpus scenario).
**Verify:** `pytest tests/unit/strategic/test_interruption_resistance.py -v` — all six new tests pass,
all pre-existing tests in the file still pass unmodified except the two touched in Step 4.

### Step 6 — Add cross-system normalization tests
**Files:** `tests/unit/strategic/test_score_normalization.py` (new file)
**Change:** Two tests matching test_plan.md items 4-5, both requiring Step 2's mapper fix to be
meaningful (using real System-A-shaped data, not the `1.0` placeholder):
- `test_max_adventure_route_candidate_can_exceed_low_urgency_goal_current`: candidate `ProjectState`
  with `kind=ProjectKind.QUEST` (a real `ProjectKind` member — must use the actual enum member, not a
  string, so `_score_scale_max` classifies it as System A) and `score=2.9` (100% of
  `_ADVENTURE_ROUTE_SCORE_MAX`), locked. `current` with `kind=GoalKind.SOCIAL` (a real `GoalKind`
  member — System B), `score=5.0`, low `interruption_resistance` (e.g. `0.1`). Compute expected:
  `candidate_pct = 2.9/2.9 = 1.0`; `normalized_effective_current_pct = 5/100 + 3/100 = 0.08`; `1.0 >
  0.08` and `1.0 > 0.8` → bypass succeeds. Assert `result is not None`. This is the direct proof that
  Step 2's fix landed — with the old hardcoded `score=1.0`, a real System-A candidate could never reach
  this test's `score=2.9` at all.
- `test_weak_adventure_route_candidate_blocked_by_high_urgency_goal_current`: candidate
  `kind=ProjectKind.QUEST`, `score=0.5` (weak, `candidate_pct ≈ 0.17`), locked. `current`
  `kind=GoalKind.COMBAT_ENGAGE`, `score=90.0`, `interruption_resistance=0.3` (→ margin 9.0):
  `normalized_effective_current_pct = 0.9 + 0.09 = 0.99`; `0.17 < 0.99` → blocked regardless of the
  raw ~2.9-vs-100 scale gap. Assert `result is None`.
Import `ProjectKind` and `GoalKind` from `src.core.strategic` at the top of the new file.
**Do NOT touch:** Do not add a test asserting a specific numeric value for `_ADVENTURE_ROUTE_SCORE_MAX`
or `_GOAL_UTILITY_SCORE_MAX` beyond what's needed to compute the expected pass/fail outcome above —
these are internal constants, not part of any public contract this ticket is establishing.
**Verify:** `pytest tests/unit/strategic/test_score_normalization.py -v`.

### Step 7 — Route `AdventureDecisionPhase.apply()` through `evaluate_project_switch()`
**Files:** `src/domains/adventure/phase.py`
**Change:** Replace lines 189-195:
```python
if result.proposed_project and result.proposed_objective:
    strat_upd = StrategicUpdate(
        projects_add_or_update=[result.proposed_project],
        current_project_id_set=result.proposed_project.id,
        current_objective_id_set=result.proposed_objective.id,
    )
```
with:
```python
if result.proposed_project and result.proposed_objective:
    strat_upd = StrategicIntelligenceSystem.evaluate_project_switch(
        hero, result.proposed_project, tick
    )
    if strat_upd is None:
        continue
```
`evaluate_project_switch(entity, candidate_project, current_tick)` (`intelligence.py:881-885`) already
reads `entity.strategic.current_project_id` and `entity.strategic.projects` internally to resolve
"current" — no separate lookup or `current` argument needs to be constructed in `phase.py`; passing
`hero` and `result.proposed_project` is sufficient. When there is no current project, or the current
project isn't `ProjectStatus.ACTIVE`, `evaluate_project_switch()` already unconditionally accepts the
candidate (lines 898-911, unchanged by Step 3) — so this rewiring is behavior-preserving for the
"hero had no active project" case, and only changes behavior when a hero has an active, locked project
whose retained/normalized score the new candidate doesn't clear.
Add the import: `from src.systems.strategic import StrategicIntelligenceSystem` at the top of
`phase.py` (alongside the existing imports at lines 13-23). Confirmed no circular import risk:
`src/systems/strategic.py` is a compatibility wrapper re-exporting
`src.systems.strategic_systems.intelligence.StrategicIntelligenceSystem`, and `intelligence.py` has no
import of `src.domains.adventure` anywhere (grepped, zero matches).
The `continue` on `strat_upd is None` means this hero's `entity_updates` entry is skipped entirely for
the tick — matching AC3's "must NOT overwrite" requirement and the existing `continue` pattern used
just above for the `DEFER_WITH_REASON` case (line 187). This intentionally also skips recording
`last_routing_tick`/`last_routing_family` for a rejected switch (Implement should not add a separate
"partial" property update path for this — that would be new, unrequested behavior).
**Do NOT touch:** The per-hero own-lock gate at lines 141-150 (`if tick < active_proj.lock_until_tick
and not _threat_resolved(...)`) — this is a separate, pre-existing early-release mechanism this ticket
doesn't change. Per investigation.md, once this gate is passed (lock expired, or `_threat_resolved()`
true while lock is still nominally active), `evaluate_project_switch()`'s own `lock_until_tick >
current_tick` check inside the new Step 3 gate independently re-blocks the switch if the candidate
doesn't clear the bar — this is the intended, not accidental, interaction between the two gates; do not
try to "fix" or short-circuit this by also checking `lock_until_tick` in `phase.py` itself. Do not touch
the eligibility filter at lines 126-130 (`_supports_adventure_routing`, C1's already-DONE work). Do not
touch `_threat_resolved()` itself.
**Other writers to `current_project_id`:** `AdventureDecisionPhase.apply()` is one of several writers
to `entity.strategic.current_project_id` — the others are `evaluate_project_switch()`'s own two
internal call sites in `intelligence.py` (lines 1270, 1351, both go through the same now-generalized
gate this ticket touches) and `resume_project()` (line 938, untouched, only reachable via its own
explicit call sites, not via `apply()`). After this step, `apply()` no longer writes
`current_project_id_set` directly at all — it only does so via the return value of
`evaluate_project_switch()`, closing the asymmetry investigation.md flagged (`phase.py` was the only
writer that bypassed the shared gate). The two `events.py` direct-overwrite sites
(`stabilize_project` etc.) are NOT touched — they remain a separate, out-of-scope instance of the same
historical pattern (see Scope Guards).
**Verify:** Step 8's integration tests; Step 9's architecture guard test.

### Step 8 — Add integration tests for `apply()`'s lock-respecting behavior
**Files:** `tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py`
**Change:** Two tests matching test_plan.md items 6-7. Both need a hero with HP > 80% and no hostile
nearby (so `_threat_resolved()` returns `True` and the per-hero own-lock gate at `phase.py:150` does
NOT skip the entity — see the existing `test_filters_out_locked_projects` in this file, lines 49-80,
for the entity-construction pattern to follow: `V2EntityBuilder`, manual `strategic` replace with a
locked `ProjectState`), and a route-generation setup that produces at least one candidate (reuse
existing fixture patterns from this file/its siblings for opportunity/candidate generation — confirm
the exact generator/provider mocking pattern already used elsewhere in this file before duplicating it).
- `test_apply_respects_active_system_b_lock`: hero's `current_project_id` points at an ACTIVE
  `ProjectState` with `kind=GoalKind.COMBAT_ENGAGE` (or similar), high score, `lock_until_tick` in the
  future relative to `state.tick`. Route generation/scoring must produce a candidate whose (real,
  post-Step-2) score does not clear the new normalized bypass gate. Call `AdventureDecisionPhase.apply()`
  and assert the returned `StateUpdate` either has no entry for this hero's id in `entity_updates`, or
  has an entry whose `strategic` is `None`/carries no `current_project_id_set` change — i.e. the
  System-B project's `current_project_id` is preserved.
- `test_apply_switches_when_candidate_clears_bar`: same setup, but tune the current project's score/
  resistance low enough (and/or the generated route's expected score high enough) that the normalized
  bypass gate clears. Assert `apply()`'s resulting update DOES set `current_project_id_set` to the new
  route's project id — this is the "don't over-correct into never switching while any lock exists"
  guard test_plan.md calls for.
**Do NOT touch:** `test_filters_out_locked_projects` and any other existing test in this file — all
must keep passing unmodified (they exercise the per-hero own-lock gate at line 150, a different,
untouched mechanism).
**Verify:** `pytest tests/integration/domains/adventure/test_phase3_adventure_decision_phase.py -v`.

### Step 9 — Add architecture guard test for the routing path
**Files:** `tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py` (new file)
**Change:** A guard test (matching test_plan.md item 8 and CLAUDE.md's "authoritative application path
was used" architecture-test pattern) that fails if `phase.py`'s project-commit branch ever again
constructs `StrategicUpdate(current_project_id_set=...)` directly instead of going through
`StrategicIntelligenceSystem.evaluate_project_switch()`. Implement should pick one concrete mechanism:
either (a) an AST-level check reading `src/domains/adventure/phase.py`'s source and asserting no
`StrategicUpdate(` call site outside of module-level test fixtures directly sets
`current_project_id_set=` as a literal/attribute-derived-not-from-evaluate_project_switch value, or
(b) a call-tracing/monkeypatch check (e.g. wrap `StrategicIntelligenceSystem.evaluate_project_switch`
and assert it was called at least once when `apply()` produces any `current_project_id_set` change in
its result, mirroring the "authoritative application path was used" pattern from existing architecture
tests elsewhere in the repo — check `tests/unit/domains/adventure/test_phase3_adventure_decision_boundary.py`
for whether it already does boundary/architecture-style assertions before deciding whether this belongs
in a new file or as an addition there, per test_plan.md's own note).
**Do NOT touch:** Do not make this guard so strict it forbids `StrategicUpdate(...)` construction
generally (Step 3's `evaluate_project_switch()` itself legitimately constructs one) — it must only
guard `phase.py`'s own commit path.
**Verify:** The new guard test itself, run against the Step 7 code; also confirm it would have failed
against the pre-Step-7 code (Implement should sanity-check this by temporarily reverting Step 7 locally
if unsure — do not leave that revert in place).

### Step 10 — Add mapper score-fidelity regression test
**Files:** `tests/unit/domains/adventure/test_phase3_route_families.py` (or wherever
`RouteToProjectMapper`/`AdventureDecisionService` is already under test in this directory — confirm
exact existing file before adding; `test_phase3_adventure_decision_service.py` is the other candidate
since it exercises `AdventureDecisionService.decide()` end-to-end)
**Change:** A direct test that `RouteToProjectMapper.map_to_states(family=..., entity_id=..., tick=...,
score=2.3)` produces a `ProjectState.score == 2.3`, not `1.0` — and a second assertion (or separate
test) that `AdventureDecisionService.decide()`'s `proposed_project.score` matches `selected.score`
exactly for a scored candidate, proving the Step 2 wiring end-to-end through the real caller, not just
the mapper in isolation.
**Do NOT touch:** Do not assert on `id`, `kind`, `lock_until_tick`, `objectives`, or `active_objective_id`
in a way that would break if those fields' *values* change for unrelated reasons — this test's sole
purpose is score fidelity (test_plan.md's own anti-drift guard already covers the "other fields
unaffected" case as a separate assertion, not this test's main point).
**Verify:** `pytest tests/unit/domains/adventure/ -v` (whichever file Step 10 lands in, plus the whole
directory to confirm no collateral breakage from the mapper signature change).

### Step 11 — (removed after architecture review)
**This step was removed.** An earlier draft proposed editing `docs/mechanics/04_strategic_cognition.md`
§2/§6.6 directly in this ticket, citing the design doc's §4 as authority for a section-based ownership
split with C3. That citation doesn't exist in the design doc, and this ticket's own Out of Scope section
already assigns the entire narrative-doc rewrite (including §2's stale "Emergency Bypass" line and any
§6.6-adjacent normalization note) to `TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS` (C3) — confirmed
by reading C3's own ticket Scope, which explicitly claims "§1-2, including the stale L39 line ...
matching the ACTUAL landed code, not a paraphrase," sequenced immediately after this ticket for exactly
that reason (`SEQUENCE.md`: C3 depends on C2). Editing it here would either be silently redone/overwritten
by C3 or create a merge conflict — see CLAUDE.md's Workflow Rule on detecting duplicate work. Implement
must leave `docs/mechanics/04_strategic_cognition.md` completely untouched; the accurate final rule text
(Step 3's actual landed code) is available to C3 via this ticket's own updated docstring (Step 3.5),
Step 12's parity-ledger `v2_evidence`, and Step 13's divergence-note prose — all three exist specifically
so C3 can write accurate doc prose without re-deriving the logic from source.

### Step 12 — Update `docs/parity_ledger/strategic_cognition.yaml` STRAT-185/186/187
**Files:** `docs/parity_ledger/strategic_cognition.yaml`
**Change:** All three entries currently have `status: verified`, `priority: P0`, `v2_evidence:
"Implementation proven via exhaustive checklist audit Phase 1-11"`, `test_path: null` (confirmed by
direct read: STRAT-185 at lines 1987-1996, STRAT-186 at 1997-2006, STRAT-187 at 2007-2016). Per the
schema (`docs/parity_ledger/schema.json`), `status: "verified"` requires both `v2_evidence` and
`test_path` to be non-null — update, do not merely add:
- **STRAT-185** ("Strategic project retention is bounded by interruption resistance"): `v2_evidence` →
  describe the new normalized lock-bypass gate (Step 3) as the enforcement mechanism. `test_path` →
  `tests/unit/strategic/test_interruption_resistance.py::TestGenericInterruptionBypass::test_generic_kind_blocked_when_effective_current_not_cleared`
  (the test that most directly proves retention still holds when the candidate doesn't clear).
- **STRAT-186** ("Strategic project switching requires margin or explicit emergency"): `v2_evidence` →
  describe the generalization from the kind-allowlist to the score/urgency-floor rule. `test_path` →
  `tests/unit/strategic/test_interruption_resistance.py::TestGenericInterruptionBypass::test_generic_kind_bypasses_when_score_and_floor_clear`.
- **STRAT-187** ("Current project has reservation priority"): `v2_evidence` → note the
  `retention_margin`/`effective_current_score` formula is unchanged (Step 3 preserves it exactly) and
  point at the still-passing `test_switch_when_candidate_exceeds_margin`
  (`tests/unit/strategic/test_interruption_resistance.py`) as evidence retention priority still holds.
  `test_path` → `tests/unit/strategic/test_interruption_resistance.py::TestInterruptionResistance::test_switch_when_candidate_exceeds_margin`.
Use exact test node IDs matching whatever class/function names Step 4/5 actually land with — if
Implement names the new class/tests differently than suggested in Step 5, update these `test_path`
values to match the real names, not the suggested ones.
**Do NOT touch:** Any other entry in this file. Do not touch `docs/compliance/checklist.md`'s stale
STRAT-185/186/187 `TEST:` cross-reference (pointing at `test_strategic_hardening.py`, confirmed to
contain no matching tests) — pre-existing staleness, out of this ticket's Related Docs/Scope per
investigation.md; do not "fix" it while in the area.
**Verify:** Whatever repo-wide parity-ledger schema/lint check exists (confirm at implement time
whether one is wired into the test suite or a standalone script) passes against the edited YAML.

### Step 13 — Add `intentional_divergences.md` entry
**Files:** `docs/guidelines/intentional_divergences.md`
**Change:** Add one row to the Divergence Summary Table (after the existing rows, matching the existing
four-column format `| Subsystem | Feature | Rationale Class | Status |`):
```
| **RPG-CORE** | Interruption-Bypass Generalization | **Enforced** | RATIFIED |
```
And a corresponding numbered entry in §2 Detailed Records (next sequential number after the existing
entries), following the exact 4-field format seen at every existing entry (Subsystem / Old Behavior /
New Behavior / Rationale / Verification):
- **Subsystem**: Strategic Cognition / Project Interruption
- **Old Behavior**: `evaluate_project_switch()`'s lock-bypass gate allowed exactly two hardcoded
  cases: `kind == "detour"` (unconditional), or `kind == "danger" and score > 80` (unconditional,
  ignoring the current project's own score/retention entirely). Per investigation.md, no production
  `ProjectState(` construction site in `src/` ever sets `kind="danger"` — this branch was reachable
  only via directly hand-constructed test fixtures, not any live corpus scenario.
- **New Behavior**: `"detour"` remains the sole unconditional structural bypass. Any other candidate,
  regardless of `kind`, may bypass an active lock only when its score — normalized to a percentage of
  its own system's declared max (`~2.9` for `AdventureRouteScorer`, `100.0` for `GoalRegistry`) —
  both exceeds the current project's own normalized effective score and clears an 80%-of-max urgency
  floor. This is a real, deliberate tightening of the (previously unreachable-in-production) danger-kind
  case, not a change to any observed live behavior: a `kind=="danger", score>80` candidate that would
  have bypassed unconditionally before now additionally requires the current project's own score not
  dominate it.
- **Rationale**: **Enforced**. Generalizes a hardcoded kind-string special case into the score/urgency
  rule it was already implicitly modeling, closing the gap where any future project `kind` (present or
  not-yet-invented) had no path to legitimately interrupt a locked project regardless of how urgent it
  actually was.
- **Verification**: `tests/unit/strategic/test_interruption_resistance.py::TestGenericInterruptionBypass::test_danger_bypass_blocked_when_effective_current_not_cleared`
  (use the actual final test name from Step 5).
**Do NOT touch:** Any other row/entry in this file, including the existing "RPG-CORE | Project Margin |
Stabilized | RATIFIED" row — that is a different, pre-existing divergence, not this ticket's.
**Verify:** No automated test; manual cross-check that the "Old Behavior"/"New Behavior" text matches
Step 3's actual final code, not this plan's draft, if Implement's final code differs in any material
way from what Step 3 specifies.

## Scope Guards

- Do not touch `GoalKind`/`ProjectKind` vocabulary unification. The overlapping string values
  (`HARVESTING`, `SOCIAL`) between the two enums are a confirmed, real, pre-existing gap — Step 3's
  `_score_scale_max()` works around it via `isinstance()` against the enum class, not by merging or
  renaming either enum. Tracked separately under D22/C4.
- Do not touch `CognitionProfileDefinition.supports_adventure_routing` or the `src/domains/adventure/scoring.py`
  HERO checks (C1's eligibility gate, already DONE) — this ticket's phase.py edits are confined to
  lines 189-195 (Step 7); the eligibility filter at lines 126-130 is untouched.
- Do not touch `docs/mechanics/04_strategic_cognition.md` at all — not §2, not §6.6, not any other
  section. The entire file is owned by C3 (`TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS`), per this
  ticket's own Out of Scope section and confirmed by architecture review (see Step 11's removal note).
  Do not touch `docs/simulation/domains/adventure_contract.md`'s eligibility table either — also C3's.
  This ticket's own doc-update scope is limited to Step 12 (parity ledger) and Step 13
  (intentional_divergences.md) only.
- Do not touch `docs/audits/D22_dormant_content_wiring.md` — owned by C4.
- Do not touch `resume_project()` (`intelligence.py:938+`) or `process_project_outcome()`
  (`intelligence.py:954+`) — neither calls the lock-bypass gate.
- Do not touch the two `events.py` direct-overwrite sites (`stabilize_project` and similar
  region-danger-driven pivots) — a third, independent instance of the same "direct overwrite, no
  `evaluate_project_switch()` call" pattern, explicitly not named in this ticket's Scope/Related Code
  Areas. Flag for a future ticket if desired; do not expand this one.
- Do not touch `docs/compliance/checklist.md`'s stale STRAT-185/186/187 `TEST:` pointer — pre-existing
  staleness, unrelated to this ticket's own parity-ledger `test_path` population (Step 12).
- Do not change the raw `retention_margin`/`effective_current_score` formula (STRAT-005/006) or the
  unlocked-path final comparison (`if candidate_project.score > effective_current_score:`) — both must
  remain byte-identical to today, since `test_interruption_resistance_margin` depends on the raw
  arithmetic and is a protected anti-drift guard. Normalization is confined entirely to the new
  lock-bypass gate inside the `if current.lock_until_tick > current_tick:` branch.
- Do not classify System A vs System B by `kind`'s string value (e.g. `kind in {v.value for v in
  ProjectKind}`) — use `isinstance(kind, ProjectKind)` only, per Step 3's documented rationale.
- Do not revive `RouteFamily.HUNT_WEAK_ENEMY`'s dead route generator, and do not attempt any
  scoring-coefficient/personality-bias customization — both explicitly out of scope per the design doc's
  Non-goals.

## Dependency Map

- Step 1 has no code dependency but should be done first (confirms the doc baseline Step 3 builds on).
- Step 2 (mapper fix) is independent of Step 3.
- Step 3 (gate logic) is independent of Step 2, but Step 1 should precede it.
- Step 4 and Step 5 depend on Step 3 (need the final gate logic to know what to assert).
- Step 6 depends on both Step 2 (needs real System-A-scale test data) and Step 3 (needs the classifier/
  constants).
- Step 7 depends on Step 2 (candidate scores must be real, not the `1.0` placeholder, for the
  normalized comparison to be meaningful) and Step 3 (the gate it now calls into must be finalized).
- Step 8 and Step 9 depend on Step 7.
- Step 10 depends on Step 2.
- Step 11 is removed (see its entry above) — no dependency.
- Step 12 depends on Steps 3, 4, 5 (needs final test names) and Step 3's final docstring.
- Step 13 depends on Step 3 (needs final rule description) and ideally follows Step 5 (needs the final
  regression test name for its Verification field).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: generic gate replaces allowlist (detour unconditional OR score+floor regardless of kind) | Step 3 | Step 5's `test_generic_kind_bypasses_when_score_and_floor_clear`, `test_generic_kind_blocked_when_floor_not_cleared`, `test_generic_kind_blocked_when_effective_current_not_cleared`, `test_detour_bypasses_lock_unconditionally` |
| AC2: cross-system score scale normalized before comparison (percentage-of-declared-max) | Step 2, Step 3 | Step 6's `test_max_adventure_route_candidate_can_exceed_low_urgency_goal_current`, `test_weak_adventure_route_candidate_blocked_by_high_urgency_goal_current` |
| AC3: `AdventureDecisionPhase.apply()` routes through `evaluate_project_switch()` instead of unconditional overwrite | Step 7 | Step 8's `test_apply_respects_active_system_b_lock`, `test_apply_switches_when_candidate_clears_bar`; Step 9's routing guard test |
| AC4: existing danger-bypass scenarios resolve identically only when effective_current_score also clears | Step 3 | Step 5's `test_danger_bypass_still_works_when_effective_current_clears`, `test_danger_bypass_blocked_when_effective_current_not_cleared` |
| AC5: `test_lock_prevents_switch` and `test_project_lock` explicitly updated | Step 4 | Step 4's own updated assertions (run via `pytest tests/unit/strategic/ -v`) |

## Anti-Drift Notes

- `ProjectKind.HARVESTING`/`ProjectKind.SOCIAL` and `GoalKind.HARVESTING`/`GoalKind.SOCIAL` have
  identical string values (confirmed by direct read, `src/core/strategic.py:121-148`). Any temptation
  to simplify `_score_scale_max()` into a string/value-based lookup must be resisted — it would
  silently misclassify System B candidates of those two kinds as System A, inflating their normalized
  percentage by ~34x (100/2.9) and defeating AC2's own "low-urgency System A candidate cannot
  spuriously bypass" guarantee in the opposite direction (a System B candidate would spuriously look
  like a maxed-out System A one).
- The `"danger"` bypass branch is unreachable via any live production code path today (confirmed by
  grepping every `ProjectState(` construction site in `src/`) — Step 13's divergence note must describe
  this as tightening a *specified* contract, not a change to observed live behavior, per
  investigation.md's own explicit framing.
- Normalization applies **only** inside the lock-bypass branch (Step 3's new code). The raw
  `effective_current_score` formula and the final unconditional comparison at the bottom of
  `evaluate_project_switch()` are untouched — `test_interruption_resistance_margin` in
  `test_project_continuity.py` exercises exactly that raw path on an *unlocked* current project and
  must keep passing with zero assertion changes. If Implement finds itself needing to touch that test,
  that is a signal the normalization boundary has leaked into the wrong branch.
- `evaluate_project_switch(entity, candidate_project, current_tick)`'s signature is unchanged by this
  ticket — it already resolves "current" internally from `entity.strategic.current_project_id` /
  `entity.strategic.projects`. `phase.py` (Step 7) must not construct a separate "current"
  `ProjectState` to pass in; there is no such parameter.
- Step 2's mapper fix is a genuine prerequisite for AC2/AC3 to mean anything real — a reviewer should
  check that Step 6's and Step 8's tests actually exercise the real, non-`1.0` score path (e.g. via
  `AdventureDecisionService.decide()` or `RouteToProjectMapper.map_to_states(..., score=...)` directly),
  not a hand-constructed `ProjectState` that bypasses the mapper entirely and could pass even if Step 2
  were silently reverted.
- `_GOAL_UTILITY_SCORE_MAX=100.0` is a calibration anchor (continuing the pre-existing `score > 80`
  threshold), not a true observed ceiling — `TownScorer` (~200) and `SleepScorer` (~130) can both
  legitimately exceed it, per investigation.md's own scorer survey (architecture review Finding 2). This
  is intentional and must not be "fixed" by clamping percentages or raising the constant — see Step 3's
  own constant docstring for the full rationale.
- `docs/mechanics/04_strategic_cognition.md` is NOT touched by this ticket at all (Step 11 removed after
  architecture review — see that step's entry and Scope Guards). Implement must not add a doc edit here
  under any rationale, including "just documenting what I built" — that is C3's scope.

## Deviations (added during Implement)

All deviations below are test-fixture-value corrections or test-location choices — the actual
production code (`intelligence.py`, `mapper.py`, `service.py`, `phase.py`) was implemented exactly
per Step 3/2/7's literal specification, byte-for-byte, and was re-verified against the plan's own
line-range claims before editing (no code-vs-plan discrepancy found anywhere).

1. **Step 5 (`test_detour_bypasses_lock_unconditionally`) and Step 6
   (`test_max_adventure_route_candidate_can_exceed_low_urgency_goal_current`) numeric examples
   needed correction.** Both tests as sketched in the plan chose a candidate score "deliberately
   below" the current's effective score, with `current` described as "high-score" (Step 5) or a
   `score=5.0` mid current (Step 6), and asserted `result is not None`. Running the tests as
   literally sketched failed both times with `result is None`. Root cause: `evaluate_project_switch()`'s
   final `if candidate_project.score > effective_current_score:` check (STRAT-005/006, explicitly
   preserved byte-identical by Step 3.4 itself) applies *unconditionally after* the lock-bypass gate
   on every path, including a detour-bypassed one or one that clears the normalized gate — it is not
   skipped just because the lock-bypass gate was cleared or bypassed. A candidate whose raw score is
   below the current's raw `effective_current_score` can therefore never produce a non-None result,
   regardless of what happens at the lock-bypass gate. This is not a code bug — the code matches
   Step 3.4's own text exactly, and Anti-Drift Notes explicitly required this final raw check stay
   untouched. It is a gap in the plan's own worked-example arithmetic for these two specific tests
   (it accounted for the lock-bypass gate's normalized math but not the downstream raw check).
   **Fix applied**: lowered `current`'s raw `score`/`interruption_resistance` in both tests so the
   raw `effective_current_score` is also small enough for the final check to clear alongside the
   lock-bypass gate, while keeping the candidate's *normalized percentage* far below what a
   non-detour/non-maximal candidate would need — preserving each test's original intent (proving the
   lock-bypass gate specifically, not the whole function, behaves as designed). Both tests now pass;
   full rationale is documented inline in each test's docstring.
2. **Step 8 integration tests use a monkeypatched `AdventureRouteGenerator.generate`, not a fully
   wired `ResourceOpportunityProvider`/`ResourceRegistry` opportunity pipeline.** Standing up a real
   region-tagged resource node so `ResourceOpportunityProvider.get_opportunities()` would yield a
   non-empty candidate list was a materially larger, unrelated setup surface (region tags, tool
   requirements, depletion state) than this ticket's scope. Instead,
   `AdventureRouteGenerator.generate` is monkeypatched to return one hand-built
   `AdventureRouteOption` with controlled `expected_benefit`/`confidence`/`expected_risk` fields; the
   real (unmodified) `AdventureRouteScorer.score()` and `RouteToProjectMapper.map_to_states()` still
   run unmocked, so the real Step 2 score-fidelity fix and Step 3 gate are genuinely exercised
   end-to-end through `AdventureDecisionService.decide()` and `AdventureDecisionPhase.apply()` — only
   candidate *generation* is stubbed, not scoring or mapping.
3. **Step 9's guard test uses option (a) (AST-level check)**, landed in a new file
   `tests/unit/domains/adventure/test_phase3_project_switch_routing_guard.py` (the plan's own
   default suggestion) — `test_phase3_adventure_decision_boundary.py` was checked first and confirmed
   to do domain-isolation boundary checks only (not authoritative-path/architecture-guard-style
   assertions), so a new file was the correct choice per the plan's own decision criterion.
4. **Step 10's mapper regression test landed in `tests/unit/domains/adventure/test_phase3_route_families.py`**
   (the plan's first-listed candidate) since that file already imports and directly tests
   `RouteToProjectMapper`. Both the isolated mapper test and the `AdventureDecisionService.decide()`
   end-to-end test (plan's "second assertion... proving the Step 2 wiring end-to-end through the real
   caller") were added to this same file rather than split into
   `test_phase3_adventure_decision_service.py`, for locality with the existing mapper tests.
5. **Removed the now-dead `StrategicUpdate` import from `phase.py`.** Step 7's rewiring means
   `phase.py` no longer constructs `StrategicUpdate(...)` directly anywhere (that's the point of the
   guard test in Step 9) — the import became unused. Not explicitly called out by Step 7's text, but
   is a direct, mechanical consequence of it, not a new design decision.
