---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION
phase: done
date: 2026-08-09
tags: [combat, simulation-quality]
---

# TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION

## Title
COMBAT pillar sits at the B/C grade boundary on `dungeon_crawl` because zero of its
credit-bearing signals (`combat_damage`, `combat_initiated`, `combat_resolved`,
`tactical_variety`) fire for any of the run's real kills — determine whether the deaths
themselves are misclassified (hazard/old-age vs. genuine combat) or whether a real
attacker-attribution gap exists in the lifecycle-death path.

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Follow-up from `TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS` and
`TCK-20260809-SIMQ-COMBAT-PILLAR-RECALIBRATION-CHECK`: after confirming this session's 5 real
combat fixes and a corrected (flag-off) calibration methodology, COMBAT still grades C on
`dungeon_crawl_seed42_2000t` (norm -0.0251, right at the B/C boundary, score=0.0). The user asked
whether combat is "good enough" to move past, or needs more work first, and agreed to investigate
why the grade is stuck rather than accept it at face value.

A fresh `tools/calibrate_simq.py` run (`dungeon_crawl_seed42_2000t`, corpus-default flags) shows:
- 25 real kills (`combat_kill` → aliased to `entity_killed`, -1 attrition each = -25 raw), all
  with `killer_id=None`.
- 10 `combat_engagement_ended` events, **all** `outcome=PURSUIT_ABANDONED` — the one outcome
  `event_shapers.py`'s `CombatShaper` deliberately does not credit (`combat_resolved` only fires
  on `KILL`/`ESCAPED` outcomes).
- **Zero** `combat_damage`, `combat_initiated`, `combat_resolved`, `combat_engagement_started`,
  `near_death_survival`, or `entity_killed` (the push-shaper's own version) events anywhere in the
  entire 2000-tick run.

Root cause traced to `src/observability/event_extractor.py:468-481`: the old, broad
`CombatKillEvent` fires unconditionally on any `lifecycle.active → False` transition whenever the
shaper's own narrower `outcome_kind=="KILL"` condition isn't met (`_real_combat_update()` returns
`None` when the death's own same-tick `CombatUpdate.attacker_id` is unset). All 25 real deaths in
this run hit that fallback path — meaning every one of them lacks a same-tick,
attacker-attributed `CombatUpdate`, so **none** of `CombatShaper`'s credit-bearing event types
(`combat_damage`, `combat_initiated`, `combat_resolved`) had anything to key off. The pillar's
entire positive-scoring surface (`combat_active` +2, `combat_resolved` +3, `tactical_variety`
+1/modifier, `survival_tension` +2) is structurally unreachable for this run's real kill
population, while the only realized signal is attrition (-1 × 25).

A partial correlation check (13/25 kills within 5 ticks of a `hazard_drain_applied` for the same
entity) suggests some fraction may be legitimately non-combat (environmental/hazard) deaths that
the old extractor's broad "any lifecycle transition" net still tags `combat_kill` and scores under
COMBAT — but 12/25 have no nearby hazard signal, so this is not a single, clean explanation.
**Not yet determined**: whether the un-correlated 12/25 are (a) genuine PvP kills whose causing
`CombatUpdate` simply isn't visible at the same tick as the lifecycle transition (a real
attacker-attribution/timing gap, matching the delayed-hazard-transition case already documented in
`event_shapers.py`'s own comments), (b) old-age deaths incorrectly counted under COMBAT, or (c)
something else. This ticket is scoped to answering that question — not to forcing a fix.

## Scope
1. For a sample of the 25 real kills in a fresh `dungeon_crawl_seed42_2000t` run (both the 13
   hazard-correlated and a sample of the 12 non-correlated), trace each victim's own
   `EntityState`/`CombatComponent`/`LifecycleComponent` history across the preceding ~10 ticks to
   classify the real cause of death: opportunity-attack (OA) combat, standard `ATTACK` intent
   combat, hazard/environmental, old-age, starvation/biological, or other.
2. Determine whether any of the non-hazard-correlated kills are genuine PvP deaths whose
   `CombatUpdate` (with `attacker_id`) exists on an earlier tick than the `lifecycle.active`
   transition itself becomes visible (the "delayed transition" case `event_shapers.py` already
   names but says must be "quantified... before cutover" — quantify it here).
3. If a real, fixable attacker-attribution or timing gap is found (not old-age/hazard
   misclassification, which would be expected/correct behavior): scope a minimal, precedent-
   matching fix recommendation — do not implement speculatively; report the finding first.
4. If the dominant cause turns out to be old-age or hazard deaths legitimately outside COMBAT's
   own scope (per the Mechanics Bible's own definition of combat) being over-broadly captured by
   the old extractor's "any lifecycle transition" net: determine whether that's a scoring-taxonomy
   issue (COMBAT pillar penalized for non-combat deaths) worth its own follow-up, or intentional/
   acceptable given `docs/simulation_quality/quality_scoring_contract.md`'s own design.
5. Document the real, honest finding — no forced conclusion, no forced fix, per this session's own
   established pattern (`[[feedback_simq_no_forced_routes]]`-equivalent discipline).

## Out of Scope
- Any code fix beyond a disclosed, minimal, precedent-matching change if a genuine, narrow bug is
  confirmed (not a design tradeoff).
- Recalibrating `grade_anchors.json` — a separate ticket if this investigation concludes the
  anchor itself needs revisiting.
- The `PURSUIT_ABANDONED`-only `combat_engagement_ended` outcome distribution (why engagements
  never resolve via `KILL`/`ESCAPED` when the engagement lifecycle itself runs) — a related but
  separate question from the lifecycle-death-attribution gap this ticket investigates; may be
  filed as its own follow-up if this investigation's findings warrant it.

## Acceptance Criteria
- [x] Real cause of death classified for a representative sample of the run's 25 kills
- [x] The delayed-transition/attacker-attribution question is answered with evidence, not assumed
- [x] A concrete, honest recommendation is produced (fix scoped, or leave-as-is with reasoning)
- [x] Finding is documented in this ticket and, if code-relevant, in `docs/audits/` or the COMBAT
      pillar contract section

## Related Tickets
- TCK-20260809-COMBAT-ENGAGEMENT-FLAG-SUPPRESSES-PUSH-SHAPER-EVENTS (prior, same session — fixed
  the `combat_engagement` merge bug this investigation's own calibration baseline builds on)
- TCK-20260809-SIMQ-COMBAT-PILLAR-RECALIBRATION-CHECK (prior, same session — established the
  corrected, flag-off calibration methodology and first flagged the C-grade finding)
- TCK-20260808-COMBAT-PILLAR-OPPORTUNITY-ATTACK-CREDIT-GAP (prior session — established that
  `entity_killed` IS correctly credited via the broad old-extractor path for OA-caused deaths;
  this ticket asks the next question: are these particular deaths even OA-caused at all, and why
  do none of the OTHER credit-bearing events (`combat_damage`, `combat_resolved`) ever fire)
- TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX, TCK-20260809-COMBAT-TACTICAL-VARIETY-SCORER-GAP-FIX
  (prior, same session — added real producers for `combat_resolved`/`tactical_variety`, but this
  investigation found their own trigger conditions are never reached by this corpus's real kill
  population)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §5 COMBAT
- `docs/observability/` event shaping docs (`event_shapers.py`, `event_extractor.py` provenance)

## Related Stored Artifacts
- `staging_artifacts/TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION/`

## Related Code Areas
- `src/observability/event_shapers.py` (`CombatShaper.shape()`, lines ~108-350)
- `src/observability/event_extractor.py` (`_real_combat_update()`, `CombatKillEvent`/
  `CombatDamageEvent` fallback branches, lines ~27-42, ~437-490)
- `src/engine/combat.py` (`CombatResolutionSystem.resolve_multi_attack()`/`resolve_attack()`,
  `is_lethal`/`outcome_kind` construction)
- `src/engine/movement.py` (opportunity-attack trigger, line ~213-216)

## Assumptions / Open Questions
- Whether a single 2000-tick run's 25 kills is a representative sample, or whether run-to-run
  variance (already observed repeatedly this session for combat volume) means this needs
  cross-checking against `urban_political` and/or multiple seeds before concluding. **Resolved**:
  cross-checked against `urban_political_seed42_2000t` (same seed, same corpus-default flags) —
  identical signature (norm -0.00197, same fix moves it to 0.0), plus a direct classification
  pass on `dungeon_crawl`'s full 35-death population (not just the 25 scored kills) confirmed the
  same pattern held for every real death this run produced.
- **New, disclosed, out-of-scope finding** (not chased further, matching this session's own
  established scope discipline): `LifecycleSystem.resolve_lifecycle()` only ever flips
  `lifecycle.active=False` for `OLD_AGE` or `outcome_kind=="KILL"` — a `DEFEAT` outcome
  (`is_lethal=False`, the hardcoded value on `movement.py`'s opportunity-attack path) never
  triggers this, and `LegalityServiceV2.verify_attack_legality()` rejects any further attack on
  an already-`combat.alive=False` target (`TARGET_INCAPACITATED`), meaning a DEFEAT-outcome
  entity is theoretically capable of becoming a permanent "zombie": incapacitated forever
  (`combat.alive=False`) but never formally dead (`lifecycle.active` stays `True`), un-actable
  and un-attackable. Directly measured across all 3 corpus worlds
  (`dungeon_crawl`/`wilderness_survival`/`urban_political`, seed 42, 2000 ticks): **zero** DEFEAT
  outcomes and **zero** such zombie entities exist at run end in any of them — this is a real,
  currently-dormant code-path gap, not an active, currently-manifesting bug in the shipped
  corpus. Also directly contradicts a causal claim in the now-corrected
  `TCK-20260808-COMBAT-PILLAR-OPPORTUNITY-ATTACK-CREDIT-GAP` (see that ticket's own added
  Correction section and this doc's `quality_scoring_contract.md` update).

## Implementation Notes
Root cause traced via direct pipeline instrumentation (a monkeypatched
`AuthoritativeApplyPipeline.refine()` wrapper recording every `CombatUpdate` produced per tick,
run against a real, non-mocked `Kernel.tick_once()` loop): all 25 of `dungeon_crawl_seed42_2000t`'s
real, calibrate_simq-scored `combat_kill` events had a `CombatUpdate` with
`outcome_kind=="HAZARD"` on the tick immediately preceding their `lifecycle.active` flip
(world_dynamics.py's environmental drain — 22/25) or no `CombatUpdate` at all in the lookback
window (a mass despawn/old-age cluster at ticks 999/1550 — 3/25, confirmed via
`lifecycle.age_ticks` inspection: all at exactly `age_ticks==max_age_ticks` or a shared batch
despawn). Zero had `death_reason=="COMBAT"`. Cross-checked `urban_political_seed42_2000t`:
identical pattern (norm -0.00197 → 0.0 post-fix).

Fixed `src/observability/event_extractor.py`'s "Kill events" fallback branch to additionally
require `entity.lifecycle.death_reason == "COMBAT"` — the durable, typed field
`LifecycleSystem.resolve_lifecycle()` sets in the same `EntityUpdate` as the `active=False` flip,
and the only runtime site (confirmed via exhaustive grep of every `active=False` write) that
performs that flip. `hero_death_unrecorded` (a broader "hero death went unrecorded elsewhere"
narrative signal, not combat-specific) deliberately left un-gated on the new condition — a real
regression against 2 existing tests (`TestHeroDeathUnrecorded`) caught this during Test and was
corrected by keeping that block outside the new `if is_genuine_combat_death:` guard.

Also investigated (but did not chase, per Out of Scope) why the corpus's real
`combat_engagement_ended` activity never resolves as `KILL`/`ESCAPED` (always
`PURSUIT_ABANDONED`) — this remains the reason COMBAT's positive-scoring surface stays
unreachable even after this fix; the fix here only stops a false *negative* penalty, it doesn't
add real positive credit.

Corrected two now-inaccurate prior records (visible addenda, not silent rewrites, per this
session's own established discipline): `tickets/done/TCK-20260808-COMBAT-PILLAR-OPPORTUNITY-
ATTACK-CREDIT-GAP.md` (its DEFEAT-outcome causal claim) and
`docs/simulation_quality/quality_scoring_contract.md` §5 COMBAT (same correction, plus this
ticket's own new finding).

## Test Summary
2 new tests in `tests/unit/observability/test_event_extractor_world.py`
(`test_combat_kill_not_emitted_for_hazard_caused_death`, confirmed via git-stash bisection to
genuinely fail against the pre-fix code; `test_combat_kill_emitted_for_genuine_combat_death`,
regression guard confirming real combat deaths still fire). Full scoped re-run:
`tests/unit/observability/`, `tests/simulation_quality/`, `tests/observability/` — 1477 passed,
89 skipped; 3 failures, all confirmed pre-existing/unrelated via git-stash bisection
(`test_grade_anchor_file_exists_and_valid` — missing local calibration-report fixture;
`test_metrics_endpoint_integration`/`test_ws_events_stream` — refused localhost connections in
this sandbox). Real corpus re-verification: fresh `tools/calibrate_simq.py` runs against both
`dungeon_crawl_seed42_2000t` and `urban_political_seed42_2000t` confirm COMBAT norm moved from a
small negative to exactly `0.0` in both, with `combat_kill` event count dropping from 25/unknown
to 0 in the replayed JSONL.

## Files Changed
- `src/observability/event_extractor.py` — narrowed the Kill-events fallback to require
  `death_reason=="COMBAT"`
- `tests/unit/observability/test_event_extractor_world.py` — 2 new tests
- `docs/simulation_quality/quality_scoring_contract.md` — corrected the TCK-20260808 causal claim,
  documented this ticket's own real finding
- `docs/parity_ledger/combat_movement.yaml` — added COMB-309 (P0, per the real P0 intersection
  from `event_extractor.py`'s own file-to-ledger mapping)
- `tickets/done/TCK-20260808-COMBAT-PILLAR-OPPORTUNITY-ATTACK-CREDIT-GAP.md` — added a visible
  Correction section

## Completion Summary
Investigated why the COMBAT pillar sat at the B/C grade boundary on `dungeon_crawl` even after
this session's 5 prior real combat fixes. Found the real, structural cause: the old diffing
extractor's `combat_kill` fallback fired on ANY `lifecycle.active` transition regardless of real
cause, so 100% of this corpus's real "combat" deaths were actually HAZARD/old-age deaths
mis-credited as combat attrition — while genuine combat engagements produced zero positive credit
because they never resolved as `KILL`/`ESCAPED`. Fixed the mis-crediting (narrowed the fallback to
require the durable, authoritative `death_reason=="COMBAT"` field) — this stops a false penalty,
it does not add new positive credit, so the grade stayed C for both worlds (an honest "zero real
combat activity credited" reading, correct per the scoring contract's own conventions, not a
forced improvement). Along the way, found and corrected an inaccurate causal claim in a prior,
already-closed ticket (TCK-20260808) via a visible addendum, and disclosed — but explicitly did
not chase — a real, currently-dormant "zombie entity" code-path gap (DEFEAT-outcome deaths could
theoretically never resolve) that was directly measured to have zero manifestation in the current
corpus. The remaining, real path to a higher COMBAT grade is unblocking `combat_engagement_ended`'s
own resolution rate (why engagements always end in `PURSUIT_ABANDONED` rather than `KILL`/
`ESCAPED`) — out of this ticket's scope, left as a candidate follow-up for the user's next
direction rather than assumed.
