---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION
artifact_type: investigation
tags: [combat, simulation-quality]
---

# Investigation: TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION

## Question
Why does the COMBAT pillar sit at the B/C grade boundary on `dungeon_crawl_seed42_2000t` even
after this session's 5 prior real combat fixes (hostile-pair detection, pursuit tracking, stuck
attack task, combat_resolved/tactical_variety scorer gaps)?

## Method
Direct pipeline instrumentation: a monkeypatched `AuthoritativeApplyPipeline.refine()` wrapper
recording every `CombatUpdate` produced per tick, run against a real, non-mocked
`Kernel.tick_once()` loop (not the calibration tool's own JSONL replay, to avoid the
methodological gap found earlier this session in `TCK-20260809-SIMQ-CALIBRATE-JSONL-MISSING-
PUSH-SHAPER-EVENTS`). Cross-checked against a fresh `tools/calibrate_simq.py` run on the same
world/seed/tick-count for the real, scored `combat_kill` event count.

## Finding
All 25 of `dungeon_crawl_seed42_2000t`'s real, calibrate_simq-scored `combat_kill` events traced
to either:
- A `CombatUpdate` with `outcome_kind=="HAZARD"` on the tick immediately preceding the
  `lifecycle.active` flip (22/25) — `world_dynamics.py`'s environmental hazard drain, a mechanic
  already excluded from `_real_combat_update()`'s own combat classification elsewhere in the same
  file, but NOT excluded from the separate "Kill events" fallback branch that fires on any
  `lifecycle.active` transition.
- No `CombatUpdate` in the lookback window at all (3/25) — a mass despawn/old-age cluster
  (`lifecycle.age_ticks == max_age_ticks` confirmed via direct entity-state inspection at ticks
  999 and 1550).

Zero of the 25 had `death_reason=="COMBAT"` — the durable, typed field
`LifecycleSystem.resolve_lifecycle()` sets in the same `EntityUpdate` as the `active=False` flip,
and the ONLY runtime site (confirmed via exhaustive `grep -rn "active=False" src/`) that performs
that flip for an already-live entity.

Cross-checked `urban_political_seed42_2000t` (same seed/ticks, different world content):
identical pattern (norm -0.00197 → 0.0 after the fix).

Meanwhile, the corpus's genuine `combat_engagement_ended` activity (10 real pursuit sequences on
`dungeon_crawl`) produced zero positive COMBAT credit, because every one resolved as
`PURSUIT_ABANDONED` — the one outcome `CombatShaper` deliberately excludes from `combat_resolved`.

## Root Cause
`src/observability/event_extractor.py`'s "Kill events" fallback (the old diffing extractor's
broad path, kept live specifically to cover non-shaper-owned kill causes per
`TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION`/COMB-295) fired on ANY `lifecycle.active`
transition not already shaper-owned, with no check on the transition's real cause. This meant
every non-combat death in this corpus (hazard, old-age) was counted as `combat_kill`/
`entity_killed` and penalized under COMBAT's attrition scoring (`attrition: -1`,
`early_extinction: -10`), while the pillar's entire positive-scoring surface stayed
structurally unreachable — a false-negative-credit problem, not an under-crediting problem (which
is what the earlier, now-corrected `TCK-20260808-COMBAT-PILLAR-OPPORTUNITY-ATTACK-CREDIT-GAP`
investigated and ruled out, based on an inaccurate causal claim about the same branch — see that
ticket's own added Correction section).

## Secondary/Dormant Finding (disclosed, not chased)
`LifecycleSystem.resolve_lifecycle()` only flips `lifecycle.active=False` for `OLD_AGE` or
`outcome_kind=="KILL"` — never `DEFEAT` (`is_lethal=False`, the value `movement.py`'s
opportunity-attack path hardcodes). `LegalityServiceV2.verify_attack_legality()` separately
rejects any further attack on an already-`combat.alive=False` target
(`ReasonCode.TARGET_INCAPACITATED`). Combined, a DEFEAT-outcome entity is theoretically capable of
becoming a permanent "zombie": incapacitated forever but never formally dead. Directly measured
across all 3 corpus worlds (seed 42, 2000 ticks): zero DEFEAT outcomes occurred and zero such
zombie entities exist at run end in any of them. This is a real, currently-dormant code-path gap
— not an active bug in the shipped corpus — disclosed here and left as a candidate for its own
future investigation if the user wants it chased, rather than assumed to need a fix.

## Fix
Narrowed the fallback to additionally require `entity.lifecycle.death_reason == "COMBAT"`.
`hero_death_unrecorded` (a broader "hero death went unrecorded elsewhere" narrative signal, not
combat-specific) deliberately left un-gated on the new condition. Old-age/despawn deaths keep
their own unaffected credit path: `demographic_mortality` (WORLD pillar) on `entities_remove`.

## Verification
Post-fix, both `dungeon_crawl` and `urban_political` COMBAT norm moved from a small negative
(false attrition credit) to exactly `0.0` — an honest "zero real combat activity credited"
reading. Grade stayed C for both (0 events is the scoring contract's own documented "no signal"
default, not a boundary artifact caused by this fix). This stops a false penalty; it does not add
new positive credit, so it was not expected to move the grade upward on its own.

## Recommendation
The real remaining path to a higher COMBAT grade on this corpus is unblocking
`combat_engagement_ended`'s own resolution rate — why real engagements in this corpus always end
in `PURSUIT_ABANDONED` rather than `KILL`/`ESCAPED`. That is a separate, real, out-of-scope
question for this ticket; left for the user's next explicit direction rather than assumed to be
in scope here.
