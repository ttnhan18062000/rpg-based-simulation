---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG
artifact_type: investigation
tags: [cognition, strategy]
---

# Investigation — TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG

## Current Behavior

### `StrategicIntelligenceSystem.evaluate_project_switch()` — `src/systems/strategic_systems/intelligence.py:929-1006`

Static method. Given `entity`, a `candidate_project`, and `current_tick`:

- Lines 958-971: if there's no current project, or the current project isn't `ACTIVE`, the
  candidate wins unconditionally (untouched by this ticket).
- Line 974: `retention_margin = profile.interruption_resistance * profile.resistance_multiplier`
  (STRAT-005). Defaults (`CognitionProfile`, `src/core/strategic.py:309-321`):
  `interruption_resistance=0.3` (line 320), `resistance_multiplier=30.0` (line 321) →
  default `retention_margin = 9.0`.
- Line 976: `effective_current_score = current.score + retention_margin` — **raw, unnormalized**
  (STRAT-006).
- Lines 978-994 — the **locked-gate branch**, only entered when `current.lock_until_tick >
  current_tick`:
  - Line 985-986: `candidate_project.kind == "detour"` is the sole unconditional structural
    bypass (skips the rest of the branch).
  - Lines 988-994 — the confirmed-buggy normalized comparison:
    ```python
    candidate_max = _score_scale_max(candidate_project.kind)          # line 988
    current_max = _score_scale_max(current.kind)                      # line 989
    candidate_pct = candidate_project.score / candidate_max           # line 990
    normalized_effective_current_pct = (current.score / current_max) + (retention_margin / current_max)  # line 991
    if not (candidate_pct > normalized_effective_current_pct
            and candidate_pct > _INTERRUPTION_URGENCY_FLOOR_PCT):     # lines 992-993
        return None                                                   # line 994
    ```
- Lines 996-1004 — the **unlocked path** (also reached after a successful lock-bypass): raw,
  unnormalized `if candidate_project.score > effective_current_score:` → switch. Line 1006:
  `return None` otherwise.

### `_score_scale_max(kind)` — `src/systems/strategic_systems/intelligence.py:89-107`

Classifies by **enum class identity** (`isinstance(kind, ProjectKind)`), not string value —
`ProjectKind.HARVESTING`/`GoalKind.HARVESTING` share a string value but are different classes
(`src/core/strategic.py:121-148`). Returns `_ADVENTURE_ROUTE_SCORE_MAX` (2.9, line 32) for real
`ProjectKind` members (System A / `AdventureRouteScorer`), else `_GOAL_UTILITY_SCORE_MAX` (100.0,
line 47) — including raw strings (`"crafting"`, `"detour"`, test fixtures) and real `GoalKind`
members (System B / `GoalRegistry`).

Module constants (`intelligence.py:29-53`):
- `_ADVENTURE_ROUTE_SCORE_MAX: float = 2.9` (line 32) — System A declared ceiling, anchored to
  `docs/mechanics/04_strategic_cognition.md` §6.6 "Total non-blocked: 0.0 to ~2.9".
- `_GOAL_UTILITY_SCORE_MAX: float = 100.0` (line 47) — System B declared ceiling / universal
  baseline scale (comment at lines 34-46 explicitly documents this is a *calibration anchor*, not
  a hard ceiling — some System B scorers, e.g. `TownScorer` (~200), `SleepScorer` (~130), exceed
  it, and `candidate_pct > 1.0` for those is intentional).
- `_INTERRUPTION_URGENCY_FLOOR_PCT: float = 0.8` (line 53) — the old `score > 80` special case
  expressed as a percentage of `_GOAL_UTILITY_SCORE_MAX`.

### Confirmed root cause (established fact per ticket — re-derived here only to source exact line numbers)

Both `current.score` and `retention_margin` are divided by the **same** `current_max` at line 991.
When `current` is System-A-typed (`current_max = 2.9`), `retention_margin(9.0) / 2.9 ≈ 3.1034`
**alone** — before adding `current.score/current_max` — already exceeds any `candidate_pct` a
real System-B scorer can produce (`CombatEngageScorer` tops out at exactly 1.0, occasionally
1.1-1.33 with routine/leadership biasing per the live trace). Direct trace evidence
(`stored_artifacts/TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION/investigation.md`
lines 258-276, 1365 real calls, SEED=42/400 ticks): 0 of 24 locked-branch calls ever switched, in
either direction, anywhere in the run. Two concrete rows used below as realistic (not synthetic)
arithmetic inputs:

| tick | hero | candidate.score (raw, `GoalKind.COMBAT_ENGAGE`) | current.score (raw, `ProjectKind.SOCIAL`) |
|---|---|---|---|
| 2 | 8 | 132.58 | 0.8207 |
| 6 | 4 | 114.45 | 0.6857 |

## Mechanics / Engine Constraints

`docs/mechanics/04_strategic_cognition.md` §2 "Interruption Resistance" is the authoritative law
text and **currently documents the buggy formula verbatim** (added by C3,
`TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS`):

> "...its normalized score must exceed both (a) the current project's normalized effective score
> (`current.score/current_max + retention_margin/current_max`), and (b) a fixed urgency floor of
> `0.8`."

This is the exact formula this ticket must fix — landing a code fix without updating this doc
sentence would immediately break Authoritative Mechanics Rule parity (doc would describe the
pre-fix formula). §6.6's added note (same C3 ticket) — "This `~2.9` 'Total non-blocked' ceiling is
also the normalization anchor... that System A candidate scores are divided by when evaluated
against §2's Generalized Bypass gate" — stays accurate under the chosen fix (candidate/current raw
scores are still each divided by their own declared max; only the *margin* denominator changes),
so §6.6 itself does not need a correction, only §2's formula sentence.

STRAT-185/186/187 (docstring at `intelligence.py:948-950`) are the three governing Logic IDs:
STRAT-185 (retention bounded by interruption resistance), STRAT-186 (switching requires margin
**or** explicit emergency — the "or explicit emergency" clause is exactly what the bug violates:
today there is no value either scoring system can produce that qualifies as an "explicit
emergency" against a locked System-A current), STRAT-187 (current project has reservation
priority — the bug makes this *absolute* for the System-A-current direction, not merely
"favored," which the doc's "or explicit emergency" phrasing does not support).

## Chosen Fix — worked arithmetic

**Change** (single line, `intelligence.py:991`): normalize `retention_margin`'s contribution
against the **fixed universal baseline** `_GOAL_UTILITY_SCORE_MAX` (100.0) always, instead of the
variable `current_max`. `current.score` and `candidate_project.score` keep normalizing against
their own respective system's declared max exactly as today — only the margin term's denominator
changes:

```python
normalized_effective_current_pct = (current.score / current_max) + (retention_margin / _GOAL_UTILITY_SCORE_MAX)
```

This is a refined version of the ticket's option (c) — replacing the flawed `current_max`
denominator with a fixed one — but using the **already-declared, already-calibrated**
`_GOAL_UTILITY_SCORE_MAX` constant rather than inventing a new literal "absolute floor" number.

### Why this denominator, not a new constant

`retention_margin`'s own raw range (`interruption_resistance` 0.0-1.0 × `resistance_multiplier`,
default 30.0 → 0-30 raw units) predates System A/`ProjectKind` entirely — `effective_current_score
= current.score + retention_margin` (line 976, STRAT-006) is the original, still-unnormalized
formula that only ever made sense against System B's 0-100 range (a max margin of 30 is a
sensible ~30% swing on a 100-point scale; it is not a sensible 10x-the-ceiling swing on a
2.9-point scale). `_GOAL_UTILITY_SCORE_MAX` is the existing, already-declared name for exactly
that scale. Reusing it means the fix requires zero new named constants and is self-documenting.

### Worked arithmetic — all four directions, real constants (`_ADVENTURE_ROUTE_SCORE_MAX=2.9`,
`_GOAL_UTILITY_SCORE_MAX=100.0`, `_INTERRUPTION_URGENCY_FLOOR_PCT=0.8`, default
`retention_margin=9.0` unless noted)

**1. Locked System-A current, System-B candidate (the confirmed bug direction) — real trace row
(tick=2, hero=8):**
`current = ProjectState(kind=ProjectKind.SOCIAL, score=0.8207)`, `current_max=2.9`,
`current_pct = 0.8207/2.9 = 0.28300`.
`candidate = ProjectState(kind=GoalKind.COMBAT_ENGAGE, score=132.58)`, `candidate_max=100`,
`candidate_pct = 1.3258`.
- OLD: `normalized_effective_current_pct = 0.28300 + 9.0/2.9 = 0.28300 + 3.10345 = 3.38645`.
  `1.3258 > 3.38645`? **No** → blocked (matches the trace's observed `switched=False`, confirms
  this read of the code against real captured data).
- NEW: `normalized_effective_current_pct = 0.28300 + 9.0/100 = 0.28300 + 0.09 = 0.37300`.
  `1.3258 > 0.37300` **and** `1.3258 > 0.8` → **True** → bypasses. **Bug fixed.**

**2. Same direction, low-urgency System-B candidate — must still fail (AC2).**
Same `current` as above (`current_pct=0.28300`, `normalized_effective_current_pct=0.37300`).
`candidate = GoalKind.*, score=30.0` → `candidate_pct=0.30`. `0.30 > 0.373`? No → blocked before
even reaching the floor check. Correctly blocked. A candidate at `score=75` (`candidate_pct=0.75`)
clears the margin term (`0.75 > 0.373`) but still fails the `0.8` floor → still blocked. Only a
candidate whose `candidate_pct` clears **both** 0.373 and 0.8 (i.e., roughly `score > 80`) bypasses
— matches the "explicit emergency" framing in STRAT-186's own text.

**3. Locked System-B current, System-A candidate (reverse direction) — unaffected by the fix,
confirmed algebraically.** `current_max` here was already `100` under the old formula (any
`GoalKind`-typed or raw-string current), so `retention_margin / current_max` was already
`9.0/100 = 0.09` **before** this fix — identical to the new fixed-denominator value. Concretely
(matches the existing, currently-passing
`test_weak_adventure_route_candidate_blocked_by_high_urgency_goal_current`): `current =
GoalKind.COMBAT_ENGAGE, score=90` → `current_pct=0.9`, `normalized=0.9+0.09=0.99` (old and new,
identical). A high-urgency `ProjectKind` candidate at its own ceiling (`score=2.9`,
`candidate_pct=1.0`) against a low-score current (`score=10` → `current_pct=0.1`,
`normalized=0.19`): `1.0 > 0.19` and `1.0 > 0.8` → bypasses (old and new, identical). **This
direction was never broken and stays byte-identical under the fix** — no regression risk here.

**4. Same-system vs. same-system.**
- **B-vs-B**: `current_max=candidate_max=100` always → margin term is `9.0/100=0.09` under both
  old and new formulas → **byte-identical, unaffected**. All 6 existing
  `TestGenericInterruptionBypass` tests use `kind="crafting"`/`"scavenge"`/`"danger"` (raw
  strings, not `ProjectKind`/`GoalKind` instances) for `current`, which `_score_scale_max`
  classifies to `_GOAL_UTILITY_SCORE_MAX=100` by the default branch — every one of these tests is
  in this unaffected case. Confirmed pass-through by inspection of each test's kind values
  (`tests/unit/strategic/test_interruption_resistance.py:159-269`).
- **A-vs-A**: `current_max=candidate_max=2.9`. OLD: margin term `9.0/2.9=3.10` — structurally
  broken here too (same defect class, just not the direction the ticket's own trace emphasized).
  NEW: margin term `0.09` fixed. Example: `current.score=0.5` (`current_pct=0.172`),
  `candidate.score=2.8` (`candidate_pct=0.966`): OLD `normalized=0.172+3.10=3.28`, `0.966>3.28`?
  No → blocked (bug, same as direction 1). NEW: `normalized=0.172+0.09=0.262`, `0.966>0.262` and
  `0.966>0.8` → bypasses. **This direction was also silently broken pre-fix and is also fixed by
  the same one-line change** — not required by this ticket's ACs (which only name the
  System-A-current/System-B-candidate direction) but confirmed as a beneficial side effect, not a
  scope-creep risk, since it's the identical line of code.

### Why the rejected alternatives are worse

**(a) "Normalize `retention_margin` itself as a percentage of `current_max` at its point of
origin."** Read literally, `retention_margin_as_pct_of_current_max = retention_margin /
current_max` — which is **exactly the existing, already-broken expression** at line 991. This
option is definitionally the bug restated, not a fix, unless "point of origin" means computing it
somewhere `current_max` isn't in scope (`CognitionProfile`, `src/core/strategic.py`), in which
case it cannot reference `current_max` at all and collapses into a fixed-denominator scheme —
i.e., converges to the chosen fix, or to using `_GOAL_UTILITY_SCORE_MAX` specifically, if done
correctly. Rejected as stated; its only coherent form is the chosen fix.

**(b) Cap `retention_margin`'s normalized contribution at some fraction (e.g. `min(retention_margin
/ current_max, 0.3)`).** Requires inventing a new, arbitrary cap constant with no existing
calibration anchor to justify its specific value. Worse, it turns the margin term into a **step
function** for System-A currents: any `interruption_resistance ≳ 0.029` (`0.029*30/2.9 ≈ 0.3`)
already saturates the cap, so profiles with resistance 0.1 and 1.0 would contribute the *identical*
0.3 margin against a System-A current — destroying the whole point of `interruption_resistance` as
a continuously-tunable personality trait, precisely for the direction this ticket cares about. The
chosen fix has no such step: margin term ranges smoothly from `0` (`resistance=0`) to `30/100=0.3`
(`resistance=1.0`) — the "0.3 cap" emerges naturally from existing constants instead of being
hand-picked.

**(c) Literal "fixed absolute floor" (compare `retention_margin` in raw units against a hardcoded
number, decoupled from percentages entirely).** Reintroduces exactly the cross-system raw-unit
mismatch the percentage redesign (`TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION`) was built
to eliminate: a single raw-unit floor cannot be simultaneously meaningful against a 2.9-ceiling
scale and a 100-ceiling scale. The chosen fix is a refinement of this option's *intent*
("stop dividing by the variable, unstable `current_max`") realized as a **fixed percentage**
denominator instead of a fixed raw-unit floor, which stays consistent with the percentage-based
design C2 already established and requires no new constant.

**(d) Something else — none found.** No alternative surfaced during investigation that both fixes
the bug and avoids a new arbitrary constant. The newly-added (same-day, 2026-08-11)
`docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md` (§3, "Score
normalization," line 142) independently proposes `utility = (raw_score /
_ADVENTURE_ROUTE_SCORE_MAX) * _GOAL_UTILITY_SCORE_MAX` for a *different* problem (giving
`AdventureRouteScorer` candidates a fair shot in `GoalRegistry`'s selection) — corroborating
evidence, not this ticket's scope (that doc is a future wrapper-design proposal, no code landed),
that routing values through the `_GOAL_UTILITY_SCORE_MAX` scale as a common basis is the
established pattern in this codebase for exactly this class of cross-system comparison problem.

## Is the unlocked path affected?

**No — confirmed by direct inspection, not assumption.** Line 996, `if candidate_project.score >
effective_current_score:`, uses `effective_current_score` from line 976
(`current.score + retention_margin`, fully raw) and `candidate_project.score` (also fully raw).
Neither operand ever calls `_score_scale_max()` or references `current_max`/`candidate_max` — the
locked-gate normalization (lines 988-993) and the unlocked/final raw comparison (line 996) are two
textually and semantically separate expressions; nothing in the chosen fix touches line 976 or 996
at all. The unlocked path *does* have its own, pre-existing, unrelated cross-scale asymmetry
(documented directly in `test_max_adventure_route_candidate_can_exceed_low_urgency_goal_current`'s
own docstring, `tests/unit/strategic/test_score_normalization.py:27-35`: a maximal System-A
candidate at `score=2.9` cannot clear a System-B current whose raw `score+retention_margin` exceeds
2.9) — but that asymmetry is explicitly out of scope per this ticket's own "Out of Scope" section
(the raw formula is called out as intentionally unchanged in both the code comment at
`intelligence.py:983-984` and the docstring at line 946) and per `TCK-20260810-COMBAT-BRAVERY-
QUARTILE-ENGAGEMENT-INVERSION`'s finding that it does not block real heroes in practice (the raw
check only has to clear ~9.5-9.8, trivially cleared by any real System-B utility once the lock
naturally expires). Flagging it as a candidate for a **future**, separately-ticketed fix if the
System-A-current/System-A-candidate raw-scale case ever becomes practically reachable — not this
ticket's job.

## Docs Requiring Update

- `docs/mechanics/04_strategic_cognition.md`: §2's Interruption Resistance law text currently
  states the buggy formula (`retention_margin/current_max`) verbatim and must be corrected to the
  fixed formula (`retention_margin/_GOAL_UTILITY_SCORE_MAX`), with a one-line rationale note (why
  the margin term uses a fixed denominator while the score terms don't).
- `docs/parity_ledger/strategic_cognition.yaml`: STRAT-186 (id at line 1997) and STRAT-187 (id at
  line 2007) entries — both currently carry generic, stale `v2_evidence` ("Implementation proven
  via exhaustive checklist audit Phase 1-11") that predates and does not describe the C2
  normalized-gate mechanism at all (contrary to the ticket's Scope text, C2 never actually wrote
  bug-specific `v2_evidence` into this file — see Prior Work below), and both have `test_path:
  null` despite `priority: P0`, which is itself a pre-existing gap the project rule ("P0 entries
  require a passing test_path") requires closing. This ticket must write real `v2_evidence`
  describing the fixed formula and set a real `test_path` for both entries — this is a first-time
  real update, not a "correction" of previously-accurate text.

## Parity Ledger Overlap

- **STRAT-185** (line 1987, "Strategic project retention is bounded by interruption resistance"):
  touched indirectly — `retention_margin`'s computation (line 974) is unchanged; only its use in
  the locked-gate comparison changes. `status: verified`, `priority: P0`, `test_path: null`
  (pre-existing gap, not required to close by this ticket's scope but worth flagging to Plan).
- **STRAT-186** (line 1997, "Strategic project switching requires margin or explicit emergency"):
  directly touched — this is the entry whose "or explicit emergency" clause the bug violates.
  `status: verified` (misleading pre-fix — no test ever verified the "or explicit emergency" half
  for the System-A-current direction), `priority: P0`, `test_path: null`. **Must update.**
- **STRAT-187** (line 2007, "Current project has reservation priority"): directly touched — the
  bug makes this absolute/un-interruptible for one direction, contradicting the doc's own
  "favored, not absolute" framing. `priority: P0`, `test_path: null`. **Must update.**
- All three are `P0` — per the Authoritative Mechanics Rule, P0 entries require a passing
  `test_path` after changes. None currently has one; Plan should select the new/updated regression
  test(s) from this ticket's test_plan.md as the `test_path` value(s).

## Prior Work

- `stored_artifacts/TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION/` (C2): landed the
  normalized gate this ticket fixes. Its own `plan.md` (lines 226-310) worked out several
  arithmetic examples for the *other* direction (System-A candidate vs. System-B current, or
  same-system) — none of them exercise a locked System-A current against a System-B candidate,
  which is exactly the gap this ticket closes. Confirms the ticket's claim that "no test in the C2
  batch exercises the locked, cross-system, small-max-current direction at all."
- `stored_artifacts/TCK-20260810-COGNITION-ELIGIBILITY-BYPASS-DOCS/` (C3): wrote the current (now
  confirmed-buggy) §2 formula text into `docs/mechanics/04_strategic_cognition.md` and the §6.6
  normalization-anchor note. The §6.6 note stays accurate under this fix; only §2's formula
  sentence needs correction.
- `stored_artifacts/TCK-20260810-COMBAT-BRAVERY-QUARTILE-ENGAGEMENT-INVERSION/investigation.md`
  "Post-Batch Re-Investigation" section (lines 226-397): the direct evidentiary source for this
  bug — the live 1365-call trace, the exact confirmed constants, and the two real trace rows used
  in this document's worked arithmetic above.
- `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`: a
  same-day, not-yet-implemented design doc for a much larger unification (folding
  `AdventureDecisionPhase` into `GoalRegistry` as a scorer). References this ticket directly (§3,
  its own "Context" section) as a known blocking defect, and independently corroborates the
  `_GOAL_UTILITY_SCORE_MAX`-as-common-basis pattern. Not this ticket's scope — flagged only as
  corroborating evidence and as a heads-up that a *much larger* related change is being designed in
  parallel; Plan should not attempt to anticipate or merge with it.

## Risks and Open Questions

- **None blocking.** The Assumptions/Open Questions section's two questions are resolved by this
  investigation: (1) the fix mechanism is the fixed-`_GOAL_UTILITY_SCORE_MAX`-denominator variant
  of option (c), justified above; (2) tier — recommend `standard` (already the ticket's declared
  tier), not `hotfix`: the fix is a single line, but it requires a parity-ledger update (2 P0
  entries needing real evidence + test_path for the first time), a Mechanics Bible doc correction,
  and an existing test's own assertion flip (`test_locked_system_a_current_unreachable_by_
  system_b_candidate_documented_limitation`) — more than "self-evident intent," and the project's
  own tier table reserves `hotfix` for changes with self-evident intent and no staging-artifact
  requirement, which this ticket already has (staging artifacts exist and are required).
- **Low real-world exposure, does not change urgency of the fix**: per the ticket's own note, only
  2 of 20 corpus worlds currently run with `ENABLE_ADVENTURE_ROUTING=ON`. This affects how much
  regression-suite/corpus-level verification is warranted at Verify time, not whether the fix
  itself is correct.
- **The `docs/architecture/2026-08-11-...` design doc's own §4** flags a *related but distinct*
  and *more severe* version of this same defect class (feeding a normalized `utility` value, not a
  raw score, into a `ProjectKind`-classified `ProjectState.score`) that would arise only if/when
  that design is implemented. Not present in today's code (`RouteToProjectMapper` today always
  receives raw route scores per `mapper.py:96-107`) — confirmed not a live bug today, purely a
  documented risk for a future ticket to avoid reintroducing.

## Anti-Drift Hazards

- **Do not touch line 976 (`effective_current_score = current.score + retention_margin`) or line
  996 (`if candidate_project.score > effective_current_score:`)** — both the code comment
  (`intelligence.py:983-984`) and the docstring (line 946) explicitly require these stay raw and
  byte-identical; `test_max_adventure_route_candidate_can_exceed_low_urgency_goal_current` and
  `test_weak_adventure_route_candidate_blocked_by_high_urgency_goal_current` both encode this raw
  path's current behavior directly and would fail if it changed.
- **Do not change `candidate_pct`'s or `current.score`'s own denominators** (`candidate_max`,
  `current_max` at lines 988-990) — only the margin term's denominator (line 991) changes. Changing
  the score terms too would re-break the already-correct System-B-current direction (Direction 3
  above) and the 6 `TestGenericInterruptionBypass` tests that depend on it staying byte-identical.
- **Do not "fix" this by clamping `candidate_pct` to `[0, 1]`** — the existing module comment
  (`intelligence.py:39-46`) explicitly forbids this; `candidate_pct > 1.0` for real System-B
  scorers (`TownScorer`, `SleepScorer`) is intentional, documented behavior, unrelated to this bug.
- **Do not conflate this ticket with the `docs/architecture/2026-08-11-...` wrapper-design doc** —
  it is a much larger, unimplemented redesign; this ticket is a single-line arithmetic fix plus its
  required doc/ledger/test updates. Resist any temptation to "future-proof" by pre-adopting pieces
  of that design here.
- **The now-contradicted test** (`tests/unit/strategic/test_score_normalization.py::
  test_locked_system_a_current_unreachable_by_system_b_candidate_documented_limitation`) asserts
  `result is None` *specifically because of this bug* — per its own docstring, it is a
  documented-limitation regression guard, not a desired-behavior test, and its own final paragraph
  explicitly instructs: "If this now returns a StrategicUpdate... update this test to assert the
  new, intended behavior instead... Do not just delete this test." Plan/Implement must flip its
  assertion (and rewrite its docstring to describe the fix, not delete/skip it) — see test_plan.md.
