---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG
artifact_type: plan
tags: [cognition, strategy]
---

# Implementation Plan — TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG

## Summary

Fix `StrategicIntelligenceSystem.evaluate_project_switch()`'s locked-branch normalization
(`src/systems/strategic_systems/intelligence.py:988-993`) by changing `retention_margin`'s own
denominator from the variable `current_max` to the fixed `_GOAL_UTILITY_SCORE_MAX` (100.0) — a
single-line arithmetic change, fully justified and worked through across all 4 direction
combinations (System-A-current/System-B-candidate, the reverse, and both same-system cases) in
`investigation.md`. `current.score` and `candidate_project.score` keep normalizing against their
own system's declared max exactly as today; only the margin term's own denominator changes. This
closes the confirmed bug (a locked System-A current is structurally un-interruptible by any
System-B candidate, contradicting STRAT-186's own "or explicit emergency" clause) while leaving the
already-correct System-B-current direction and all same-system-vs-same-system cases byte-identical
(both confirmed algebraically in investigation.md, not assumed).

## Steps

### Step 1 — Fix the normalization denominator

**Files:** `src/systems/strategic_systems/intelligence.py`

**Change:** Line 991 (confirmed current text: `normalized_effective_current_pct = (current.score /
current_max) + (retention_margin / current_max)`) becomes:
```python
normalized_effective_current_pct = (current.score / current_max) + (retention_margin / _GOAL_UTILITY_SCORE_MAX)
```
Only the margin term's denominator changes (`current_max` → `_GOAL_UTILITY_SCORE_MAX`). The
`current.score / current_max` term, `candidate_pct`'s own computation (line 990), and the
`_INTERRUPTION_URGENCY_FLOOR_PCT` floor check are all untouched.

Update the function's own docstring/comment context immediately above the locked-branch block
(around lines 978-987) to note the margin term is deliberately normalized against the universal
baseline scale, not the current project's own scale — one sentence, citing this ticket, so a future
reader doesn't "simplify" it back to `current_max` (which is the exact regression this ticket
exists to prevent).

**Do NOT touch:** line 976 (`effective_current_score = current.score + retention_margin`, the raw
unlocked-path formula) or line 996 (`if candidate_project.score > effective_current_score:`) — both
are explicitly out of scope (investigation.md's own "Is the unlocked path affected?" section
confirms neither references `_score_scale_max()` at all, and both are protected by existing tests
that assert their current raw behavior). Do not touch `candidate_max`/`current_max`'s own
computation (lines 988-989) or `_score_scale_max()` itself (lines 89-107) — only the margin term's
denominator at line 991 changes.

**Verify:** Steps 3-4's new/updated tests, plus the full existing regression surface (Step 5).

### Step 2 — Update the Mechanics Bible

**Files:** `docs/mechanics/04_strategic_cognition.md`

**Change:** §2's Interruption Resistance section currently states the formula verbatim (added by
C3, `TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS`): "...its normalized score must exceed both
(a) the current project's normalized effective score (`current.score/current_max +
retention_margin/current_max`)..." — this is the confirmed-buggy formula, now stale the moment
Step 1 lands. Replace `retention_margin/current_max` with `retention_margin/100.0` (or spell out
`_GOAL_UTILITY_SCORE_MAX`) in this sentence, and add one clause explaining why: the margin term is
deliberately anchored to the universal baseline scale rather than the current project's own scale,
because `retention_margin`'s own raw range (0-30, from `interruption_resistance × 
resistance_multiplier`) was calibrated against System B's 0-100 range from the start — a sensible
~30% swing on that scale, not a coherent value on System A's ~2.9 scale.

§6.6's own added note ("This `~2.9` ceiling is also the normalization anchor... that System A
candidate scores are divided by...") stays accurate under this fix — candidate/current raw scores
are still each divided by their own declared max; only the margin denominator changes. No edit
needed there (confirmed directly in investigation.md's "Mechanics / Engine Constraints" section).

**Do NOT touch:** Any other section. This ticket's own doc-update scope is limited to §2's formula
sentence.

**Verify:** No automated test — this session's own established fact-verification requirement:
Implement must re-read the final landed code (Step 1) and confirm the doc text matches exactly,
not a paraphrase.

### Step 3 — Update the contradicted test (rename, not delete)

**Files:** `tests/unit/strategic/test_score_normalization.py`

**Change:** `test_locked_system_a_current_unreachable_by_system_b_candidate_documented_limitation`
currently asserts `result is None` specifically because of this bug (its own docstring says so and
explicitly instructs future updaters not to delete it). Rename to
`test_locked_system_a_current_now_reachable_by_system_b_candidate_fix_confirmed`, flip the
assertion to `result is not None` and `result.current_project_id_set == "candidate"`, and rewrite
the docstring to describe this as the confirmed fix for this ticket, citing the old formula's
`3.10`-vs-new formula's `0.09` margin-term arithmetic (using the exact scenario already in the test:
`current.score=0.1`, default profile, `candidate = GoalKind.COMBAT_ENGAGE, score=100.0` —
`current_pct=0.0345`, old `normalized=3.1345` blocks, new `normalized=0.1245` bypasses since
`1.0 > 0.1245` and `1.0 > 0.8`).

**Do NOT touch:** The test's own fixture construction (`current`/`candidate` `ProjectState`
values) — only the assertion and docstring change; the scenario itself is a good, real boundary
case (`current.score` near zero) worth preserving exactly as-is.

**Verify:** The renamed test itself, run directly.

### Step 4 — Add the two new AC-mapped tests

**Files:** `tests/unit/strategic/test_score_normalization.py` (co-locate with the existing
cross-system tests and Step 3's renamed test)

**Change:** Add both tests exactly as specified in `test_plan.md`'s "New Tests Required" section:

1. `test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate` (AC1) — real trace
   values (tick=2, hero=8 from the parent ticket's own live trace): `current =
   ProjectState(kind=ProjectKind.SOCIAL, score=0.8207, lock_until_tick=100)`, default
   `CognitionProfile`, `candidate = ProjectState(kind=GoalKind.COMBAT_ENGAGE, score=132.58)`,
   `current_tick=50` → asserts a non-`None` result with `current_project_id_set == candidate.id`.
   Docstring notes these are real, captured-trace values, not synthetic — directly satisfies AC1's
   "not synthetic" requirement.
2. `test_locked_system_a_current_still_blocks_low_urgency_system_b_candidate` (AC2) — same
   `current` as test 1, two sub-cases: `candidate.score=30.0` (fails the margin term itself) and
   `candidate.score=75.0` (clears the margin term but not the `0.8` floor) — both assert `result is
   None`. The second sub-case specifically pins that the floor still binds even once the margin
   term is fixed, guarding against an overcorrection into "any candidate can always interrupt."

**Do NOT touch:** Any existing test in this file (`test_max_adventure_route_candidate_can_exceed_low_urgency_goal_current`,
`test_weak_adventure_route_candidate_blocked_by_high_urgency_goal_current`) — both use
`GoalKind`-typed currents (`current_max=100` already under both old and new formulas), confirmed
byte-identical and unaffected by this fix in investigation.md's Direction 3.

**Verify:** Both new tests, run directly.

### Step 5 — Update the parity ledger

**Files:** `docs/parity_ledger/strategic_cognition.yaml`

**Change:** `STRAT-186` (id at line 1997) and `STRAT-187` (id at line 2007) — both currently P0,
`status: verified`, but `test_path: null` and carrying generic, pre-C2 `v2_evidence` ("Implementation
proven via exhaustive checklist audit Phase 1-11") that predates and doesn't describe the current
mechanism at all (confirmed in investigation.md's "Docs Requiring Update" section — this is a
first-time real update, not a correction of previously-accurate text). Write real `v2_evidence` for
both describing the fixed formula (margin term normalized against `_GOAL_UTILITY_SCORE_MAX`, not
`current_max`), and set `test_path`:
- `STRAT-186` ("switching requires margin or explicit emergency"): `test_path:
  tests/unit/strategic/test_score_normalization.py::test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate`
  (the "or explicit emergency" clause — this is the test that proves an emergency-equivalent
  candidate can now get through).
- `STRAT-187` ("current project has reservation priority"): `test_path:
  tests/unit/strategic/test_score_normalization.py::test_locked_system_a_current_still_blocks_low_urgency_system_b_candidate`
  (the "favored, not absolute" clause — this is the test that proves retention priority still holds
  for genuinely low-urgency candidates, now that the fix could theoretically have overcorrected).

**Do NOT touch:** `STRAT-185` (line 1987) — investigation.md confirms it's only indirectly touched
(`retention_margin`'s own computation at line 974 is unchanged; only its use in the comparison
changes) and is not required to close by this ticket's own scope, though its own `test_path: null`
gap is flagged for a future ticket's awareness. Do not touch any other entry in this file.

**Verify:** Whatever repo-wide parity-ledger schema/lint check exists (confirm at Implement time),
plus a direct check that both new `test_path` values reference real, currently-existing,
currently-passing test node IDs (matching Steps 3-4's actual final names).

## Scope Guards

- Do not touch `intelligence.py:976` or `:996` (the raw, unnormalized `effective_current_score`
  formula and the final unlocked-path comparison) — both must stay byte-identical; protected by
  `test_retention_when_candidate_below_margin` and siblings in
  `tests/unit/strategic/test_interruption_resistance.py`, and by the code comment/docstring at
  lines 983-984/946 that explicitly requires this.
- Do not touch `candidate_max`/`current_max`'s own computation (lines 988-989) or `_score_scale_max()`
  itself (lines 89-107) — only the margin term's own denominator at line 991 changes. Changing the
  score terms too would re-break the already-correct System-B-current direction and the 6
  `TestGenericInterruptionBypass` tests that depend on it staying byte-identical.
- Do not clamp `candidate_pct` to `[0, 1]` — the existing module comment (`intelligence.py:39-46`)
  explicitly forbids this; `candidate_pct > 1.0` for real System-B scorers (`TownScorer`,
  `SleepScorer`) is intentional, documented behavior, unrelated to this bug.
- Do not touch `docs/mechanics/04_strategic_cognition.md` §6.6 — confirmed accurate under this fix,
  no edit needed there, only §2's formula sentence (Step 2).
- Do not conflate this ticket with `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`
  (the same-day, not-yet-implemented wrapper-design doc) — that document independently corroborates
  the `_GOAL_UTILITY_SCORE_MAX`-as-common-basis pattern as evidence this fix is the right shape, but
  is a much larger, separate, unimplemented redesign. This ticket is a single-line arithmetic fix
  plus its required doc/ledger/test updates only.
- Do not touch `resume_project()`, `process_project_outcome()`, or either of the two
  `evaluate_project_switch()` call sites' own construction logic (`intelligence.py:1341`, `:1422`)
  beyond what Step 1 already requires (none — the call sites themselves don't change, only the
  function they call does).
- `STRAT-185`'s own `test_path: null` gap is real but out of this ticket's required scope (flagged,
  not silently ignored) — do not expand this ticket to close it unless Implement finds doing so is
  trivially free as a byproduct of Steps 3-4's new tests.

## Dependency Map

- Step 1 must land before Steps 3-4 (their assertions depend on the fixed formula).
- Step 2 depends on Step 1 being finalized (doc text must match the final landed code, not a draft).
- Step 5 depends on Steps 1, 3, and 4 (needs the final code behavior and final test names).
- All steps are meant to land together as one coherent diff.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — locked System-A current CAN be interrupted by high-urgency System-B candidate, real values | Step 1 (fix) + Step 4 (new test) | `test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate` |
| AC2 — locked System-A current still NOT interrupted by low-urgency System-B candidate | Step 1 (fix) + Step 4 (new test) | `test_locked_system_a_current_still_blocks_low_urgency_system_b_candidate` |
| AC3 — all existing tests pass, buggy-behavior-encoding test updated not left green by accident | Step 3 (rename/flip) | Full scoped suite (see below) — 0 unexpected failures, 1 deliberately-renamed test |
| AC4 — STRAT-186/187 parity-ledger entries updated to describe the fixed mechanism | Step 5 | `pytest` re-run confirming both new `test_path` values are real and pass; parity schema check |

**Scoped pytest command** (per test_plan.md, reusing the exact command the parent ticket's own
investigation already used for the pre-fix baseline — 19 tests, all passing then):
```
.venv/bin/python3 -m pytest tests/unit/strategic/test_interruption_resistance.py tests/unit/strategic/test_project_continuity.py tests/unit/strategic/test_score_normalization.py -v
```
Never `pytest tests/`.

## Anti-Drift Notes

- The 6 `TestGenericInterruptionBypass` tests and the 2 untouched `test_score_normalization.py`
  tests must all pass with **zero modification** — they are the direct evidence the fix is a no-op
  for every direction except the one confirmed-broken one. If any of these needs a code change to
  pass, the fix touched something outside the single margin-term denominator — stop and re-examine
  rather than adjusting the test.
- The fix's own worked arithmetic (investigation.md) confirms it also silently fixes the
  System-A-vs-System-A direction (both locked at `current_max=candidate_max=2.9`) as a beneficial
  side effect of the identical line change — not required by this ticket's own ACs, not a separate
  scope item, just worth Implement being aware of so a surprising-but-correct test result isn't
  mistaken for a bug.
- `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`'s own §4
  flags a related-but-distinct, more severe version of this same defect class (feeding a normalized
  `utility` into a raw-scale `ProjectState.score`) that would only arise if/when that design is
  implemented — confirmed not present in today's code, purely a documented risk for that other,
  future ticket to avoid. Not this ticket's concern.
