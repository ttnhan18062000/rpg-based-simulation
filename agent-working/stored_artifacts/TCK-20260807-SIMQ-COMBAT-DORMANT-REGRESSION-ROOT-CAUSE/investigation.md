---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260807-SIMQ-COMBAT-DORMANT-REGRESSION-ROOT-CAUSE
artifact_type: investigation
tags: [simulation-quality, combat]
---

# Investigation — TCK-20260807-SIMQ-COMBAT-DORMANT-REGRESSION-ROOT-CAUSE

## Docs Requiring Update

- `docs/simulation_quality/current_state.md`: close out the investigation (Implement phase)
- `docs/simulation_quality/eval_matrix_results.md`: append disposition (Implement phase)

## Root cause: confirmed, not a live regression — a stale-anchor consequence of 2 already-landed, already-disclosed 2026-08-06 changes

`mcp__knowledge-search__search_docs` (Context Scan Step 1) immediately surfaced
`TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY` (DONE) and its child hotfix
`TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-MISCLASSIFICATION-FIX` (DONE) — both dated exactly one
day before the 2026-08-07 full-corpus run that first surfaced this ticket's own 26-pair drift.

1. **`ENABLE_COMBAT_ENGAGEMENT` is corpus-wide OFF, deliberately** (confirmed still true:
   `src/domains/optimization/feature_flags.py:17` default `FeatureMode.OFF`, zero of the 17
   `config/simulation_quality/profiles/*.yaml` files set it ON). `TCK-20260806-SIMQ-COMBAT-
   ENGAGEMENT-GATE-CORPUS-VALIDITY` confirmed this is a deliberate ruling (DEV-002), not an
   unexamined gap — `CombatEngagementPhase` (PP-16, the phase that applies the damage formula) has
   never fired anywhere in the SimQ corpus.
2. **Before 2026-08-06, `event_extractor.py`'s combat-damage branch had no `outcome_kind` check**,
   so hazard-drain damage (honestly tagged `outcome_kind="HAZARD"` by `world_dynamics.py`) was
   double-classified as combat — this is what gave many scenarios their previously-nonzero COMBAT
   signal, despite PP-16 itself never running. `TCK-20260806-SIMQ-EXTRACTOR-HAZARD-COMBAT-
   MISCLASSIFICATION-FIX` (hotfix) fixed this: confirmed still live in current code
   (`src/observability/event_extractor.py:22-24,42`, `_NON_COMBAT_OUTCOME_KINDS = ("HAZARD",
   "REJECTED")`, `_real_combat_update()` requiring `attacker_id is not None`).
3. **That hotfix ticket's own Acceptance Criteria explicitly deferred `grade_anchors.json`
   recalibration** ("grade_anchors.json/parity ledger updated if any scenario's COMBAT grade
   shifts" — left unchecked, `Files Changed` lists no `grade_anchors.json` edit) — the parent
   investigation ticket's own Out of Scope confirms why: "recalibrating grade_anchors.json — that
   is follow-up implementation work once this investigation's recommendation is in hand, likely a
   separate ticket." **The 2026-08-07 full-corpus run that surfaced this ticket's own 26-pair
   drift was the first live re-run against the fixed extractor — it correctly, honestly reports
   the new reality (no real combat, formerly-inflated hazard-drain no longer counted), and the
   anchors were simply never refreshed to match.**

This fully and precisely explains the predecessor ticket's own most striking finding — **zero
trial-to-trial variance across all 26 COMBAT pairs**: since PP-16 is corpus-wide disabled and
hazard-drain no longer counts, the only path to a nonzero COMBAT score requires a real
`attacker_id`-bearing `CombatUpdate`, which structurally cannot occur while the phase that
produces one is gated off — there is no wall-clock-dependent code path left to produce variance.
This is not a bug to fix in `src/` — it is the intended, correct post-fix behavior; the anchors
were stale.

## Fix: recalibrate all 26 COMBAT anchors (mechanical, not a code change)

Reused the predecessor ticket's own already-captured 3-trial data (bit-identical across all 3
trials per pair, confirmed) — no new engine runs needed. Every one of the 26
`grade_anchors.json` COMBAT entries updated to its confirmed-stable post-fix value. Examples:
`sandbox_world_seed999_200t`: B/0.08 → C/0.0; `urban_political_seed456_500t`: A/0.03 →
C/-0.0236; `quest_dense_frontier_seed42_200t`: unchanged direction (already negative), refreshed
to the exact confirmed value.

`tests/simulation_quality/test_grade_regression.py -m "not slow"` re-run after recalibration: all
26 previously-flagged COMBAT failures resolved.

## One additional, disclosed, NOT fixed: a newly-surfaced COGNITION anchor issue

Re-running the fast-tier suite after the COMBAT recalibration surfaced 1 new, unrelated failure:
`hero_guild_routing_seed42_500t`/COGNITION (anchor=1.016, my own 3 trials: 1.827, 1.837, 1.837 —
close to each other but far from the anchor, and NOT perfectly bit-identical like the COMBAT
pairs, showing small genuine trial-to-trial jitter). This is NOT the same failure mode as the
COMBAT pairs (no stale-anchor cause identified yet, and it shows real variance, unlike COMBAT's
zero-variance signature) and NOT part of this ticket's own COMBAT-only scope. **Deliberately left
untouched** — recommend a small follow-up investigation (same 3-trial methodology) if this is
worth pursuing; not chased further here to avoid scope creep on a finding with no diagnosed cause
yet, consistent with this session's own established discipline of not blindly recalibrating
without evidence.
