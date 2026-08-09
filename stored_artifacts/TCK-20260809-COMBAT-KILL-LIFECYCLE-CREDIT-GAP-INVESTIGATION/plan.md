---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION
artifact_type: plan
tags: [combat, simulation-quality]
---

# Plan: TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION

## Approach
1. Instrument the real pipeline (not calibration-tool replay) to classify every real kill's
   actual cause via the durable `death_reason` field, on `dungeon_crawl_seed42_2000t`.
2. Cross-check the pattern against `urban_political_seed42_2000t`.
3. If a genuine, narrow mis-crediting bug is confirmed (not a design tradeoff): fix minimally by
   gating the existing fallback branch on the durable `death_reason` field already computed by
   `LifecycleSystem`, rather than inferring cause from `outcome_kind`/timing heuristics.
4. Verify via a real regression test (bisection-confirmed) plus real corpus re-verification on
   both worlds.
5. Disclose but do not chase any adjacent findings surfaced along the way (the DEFEAT/zombie
   dormant code path; the `PURSUIT_ABANDONED`-only engagement resolution pattern).

## Rejected Alternatives
- **Infer combat-vs-non-combat from `outcome_kind`/`attacker_id` heuristics at the fallback site
  itself** (mirroring `_real_combat_update()`'s own defense-in-depth pattern) — rejected because
  the fallback fires on the CURRENT tick's `lifecycle.active` transition, not necessarily the
  same tick as the causing `CombatUpdate` (the delayed-hazard-transition case already documented
  in `event_shapers.py`'s own comments) — the `death_reason` field is durable and set at the
  exact moment of the authoritative death decision, making it the only reliable, non-timing-
  dependent signal.
- **Gate `hero_death_unrecorded` on the same new condition** — rejected: it's a broader
  narrative-gap signal ("a hero died and nothing else recorded it"), not combat-specific;
  narrowing it would have been an unrelated scope change, confirmed by 2 existing regression
  tests that would have broken.

## Verification Plan
- New regression test confirmed to genuinely fail pre-fix via `git stash` bisection.
- Full scoped test sweep (`tests/unit/observability/`, `tests/simulation_quality/`,
  `tests/observability/`).
- Real corpus re-verification via `tools/calibrate_simq.py` on both `dungeon_crawl` and
  `urban_political`, same seed/tick-count as the investigation.
