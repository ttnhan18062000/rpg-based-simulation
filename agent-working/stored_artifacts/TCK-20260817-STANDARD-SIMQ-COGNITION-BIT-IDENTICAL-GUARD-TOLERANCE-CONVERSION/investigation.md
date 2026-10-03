---
status: historical
layer: simulation
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260817-STANDARD-SIMQ-COGNITION-BIT-IDENTICAL-GUARD-TOLERANCE-CONVERSION
tags: [simulation-quality, calibration, testing, bug]
---

# Investigation — TCK-20260817-STANDARD-SIMQ-COGNITION-BIT-IDENTICAL-GUARD-TOLERANCE-CONVERSION

## Failing test
`test_urban_political_seed123_500t_cognition_bit_identical_under_load`
(`tests/unit/worldassembly/test_corpus_diversity.py`), one of 10 failures in the
`-m slow` suite's first-ever real CI run today.

## Real evidence gathered (10 independent fresh trials, this session)
1. Two isolated single-trial runs (idle-vs-load structure, original test as-committed):
   run 1 PASSED (idle=load, `event_count=2/B`), run 2 PASSED (same), run 3 FAILED, run 4 FAILED
   — with the failing runs' idle leg ALONE (captured before any load workers spawn) already
   showing `event_count=355, raw_score=1768.0, normalized_score=3.536, grade=S`.
2. A separate parallel sub-agent's own reproduction independently confirmed the same divergence:
   `idle={'event_count': 355, 'raw_score': 1768.0, 'grade': 'S', 'loop_detected': True}
   load={'event_count': 357, 'raw_score': 1778.0, 'grade': 'S', 'loop_detected': True}` (load
   leg slightly different from idle, both landing grade S).
3. A clean 5-trial isolated batch (no induced load, no concurrent test contention) run directly
   via `tools.calibrate_simq`'s internals: **5/5 identical**, all
   `{'event_count': 355, 'raw_score': 1768.0, 'normalized_score': 3.536, 'grade': 'S'}`.

Total across all 10 real observations this session: 8 landed on grade S (`355/1768.0/3.536`,
internally bit-identical across every S-observation), 2 landed on the original grade B
(`2/11.0/0.088`, matching the committed anchor exactly). This is genuinely bimodal, not scattered
noise around a single center — and notably, the induced-load busy-loop machinery in the original
test is not even necessary to trigger the S state (plain idle reruns hit it too), meaning "under
load" in the old test's name was never the precise trigger condition; ordinary wall-clock/
scheduling jitter is sufficient.

## Root cause
Same mechanism the establishing ticket (`TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM`)
already characterized: `decision_divergence_detected`
(`src/observability/event_extractor.py:844-863`) has no "already-emitted" dedup gate — it
re-fires every tick an entity's `danger` concern (`urgency > 0.7`) persists alongside a
non-survival active project (`_NON_SURVIVAL_PROJECT_KINDS`). F6's wall-clock watchdog/throttle
(`src/engine/kernel.py:420-442`, `574-601`) can, under real timing variance, drop resolution-queue
work and stall that resolution across many consecutive ticks.

That establishing ticket's own repro (4 trials: 2 idle, 2 induced-load, 2x/4x oversubscription)
found this scenario did NOT enter the stuck state at the time — "does not appear to place any
entity into the danger-concern-stuck state F6's mechanism requires" — and selected the
bit-identical guard shape specifically on that evidence. That premise is now empirically false:
the same mechanism is now recurring reliably.

## Why not fix the source (dedup gate) instead of the test?
Investigated as the more architecturally correct option (CLAUDE.md's rule against papering over
gate failures instead of fixing substance). Found:
- The fix itself would be small and idiomatically consistent: `event_extractor.py` already
  diffs prior-vs-current entity state for other event types nearby (e.g. `curr_group !=
  prior_group`, group_joined/group_expelled, a few hundred lines above this block) — adding an
  edge-trigger (only emit on the tick the mismatch newly becomes true, not every tick it persists)
  would follow the same established pattern.
- BUT: `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION` (filed by the establishing ticket's own
  investigation) documents that `decision_divergence_detected`'s current repeat-count already
  feeds into scoring for multiple pillars via a cross-pillar weight-key collision (at minimum
  INFORMATION's `subjective_divergence`). Deduping this event would silently shift scores across
  every anchor in the corpus that currently relies on its repeat-firing behavior — not just this
  one test — requiring a full corpus-wide recalibration pass to verify no other anchor silently
  broke.
- The establishing ticket's own Scope/Out-of-Scope already settled this exact decision rule for
  this exact finding class: "If [root cause] traces to the same wall-clock-driven watchdog/
  throttle mechanism already recorded as F6 ... apply the same tolerance-based multi-trial
  regression-guard pattern ... do not silently leave the anchor unguarded either way," and
  explicitly protects "reopening docs/guidelines/intentional_divergences.md's F6 entry" and any
  change to `src/engine/kernel.py`'s throttle from being revisited for this class of finding.

Given this, implementing the source fix now would be a larger, riskier undertaking than this
ticket's scope, and would go against an already-settled repo precedent for exactly this
situation. Recommended as separate future work, not implemented here.

## `3d992dd0` compounding-factor investigation (inconclusive)
A prior parallel investigation flagged `TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION`
(commit `3d992dd0`) as a plausible compounding factor: it generalized
`StrategicIntelligenceSystem.evaluate_project_switch()`'s interruption-bypass gate so it can now
return `None` (skip a switch) where the adventure decision path previously always unconditionally
overwrote `current_project_id`. Mechanistically, this could newly create the "stuck on a stale
non-survival project while a danger concern is active" precondition `decision_divergence_detected`
requires, where none existed before.

Attempted a real empirical bisect via an isolated `git worktree` (to avoid disturbing the shared
working tree, which has another concurrent session's uncommitted work in it):
- `git worktree add /tmp/.../bisect 3d992dd0~1` — resolved to `d671c53b`, a commit whose message
  ("Stage trailing agent-monitoring/tools.jsonl update from this session's commit") shows it
  belongs to a different, more fine-grained commit history than `agent-working`'s current HEAD.
  `git merge-base --is-ancestor 3d992dd0 HEAD` confirmed **`3d992dd0` is NOT an ancestor of
  `agent-working`'s current HEAD** — this repo squash-merges feature work from a more granular
  history (likely `main`) into `agent-working` via large PR commits, so `3d992dd0`'s content
  landed on this branch under a different hash.
- Traced the real landing commit via `git log --oneline -- src/systems/strategic_systems/
  intelligence.py src/domains/adventure/`: both files were touched by `6e25d4f2` ("Engine audit
  documentation, simulation quality (in-progress), test refactor and fixing (#19)"). Confirmed
  `evaluate_project_switch` calls exist in `intelligence.py` as of that commit's diff.
- Re-attempted the worktree bisect at `6e25d4f2~1` (`7a41beb5`, "Update documentation (#18)",
  a legitimate pre-epic ancestor). Blocked: `tools/calibrate_simq.py` does not exist at that
  commit (`ModuleNotFoundError`) — the SimQ calibration harness this guard's own methodology
  depends on was introduced later, in the same squash-commit era as the epic itself. There is no
  equivalent old-commit tool to reproduce a directly comparable score without building one from
  scratch.
- Also could not confirm the specific class name `AdventureDecisionPhase` (cited by the earlier
  parallel investigation) exists anywhere in the current codebase — `grep -rn "class
  AdventureDecisionPhase" src/` returns nothing; `src/domains/adventure/` currently has
  `AdventureDecisionService`, `AdventureRouteGenerator`, `AdventureRouteScorer`, etc. This class
  name may have been refactored/renamed since, or was imprecisely recalled — could not verify the
  exact original call-site cited.

Given this, the compounding-factor lead is **not empirically confirmed**. The mechanistic
argument (unconditional-overwrite-always-switches structurally prevents the stuck-state
precondition; gated-switch-can-skip creates it) remains plausible but unverified. Left as an
explicit open question rather than asserted either way, per this repo's Uncertainty Rule.

## Verification performed
- Converted test re-run individually, isolated: `1 passed in 37.59s`.
- Confirmed no stale cross-references to the removed test name remain in the file.
- Confirmed `_within_band`'s function-level default (1) is untouched — only this call site passes
  an explicit `tolerance=2`.
