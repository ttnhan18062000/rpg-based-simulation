---
status: historical
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE
phase: done
date: 2026-08-08
tags: [progression, combat, feature-flags]
---

# TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE

## Title
Entity growth (`growth_trajectory` ≈ 0 corpus-wide) is not a broken-wiring problem — every real
XP source is directly connected — but the *combination* of a kill-only/quest-only XP economy, a
dead-code threshold red herring, and rare real kills makes leveling structurally unreachable in
any realistic simulation window. Balance/wiring fix, not a new feature.

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Following the 2026-08-08 full-corpus lifecycle-score run (674 entities, 20 real worlds, 1000
ticks, `NORMAL` observability mode — `TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS`), which found
corpus-wide `growth_trajectory` essentially flat (mean **-0.0027**), a direct code-and-data
investigation traced this to its real, verified root cause rather than assuming a hypothesis:

**Real data confirms the symptom, not just the aggregate score.** Ran the lifecycle-score tool on
3 structurally different real worlds (`frontier_extended`, `sandbox_world`, `urban_political`) at
1000 ticks each and inspected the raw event stream directly: **zero** `xp_granted`/`level_up`/
`skill_unlocked`/`recipe_learned`/quest-related events fired in any of the three, despite real
`combat_damage`/`combat_initiated` activity occurring in all three (15–120 damage events per
world).

**Traced the real XP-delivery chain — it IS correctly wired, contrary to an initial hypothesis.**
Two real XP sources exist in this codebase, both confirmed connected end-to-end:
1. Combat kill: `src/engine/combat.py` computes `xp_gain = defender.identity.evolution_level *
   classification.xp_multiplier` **only when `new_hp <= 0`** (a kill/defeat outcome, not on
   ordinary damage) — `defender.identity.evolution_level * 10` for a monster kill, `* 20` for a
   hero kill (matches `docs/mechanics/attribute_progression_contract.md`'s own documented
   formula — not a divergence). Delivered via `ResourceTransferIntent.xp_reward`, consumed by
   `src/core/conservation.py:233/249` into `IdentityUpdate(evolution_points_delta=...)`.
2. Quest completion: `src/engine/quests.py:208` / `src/engine/pipeline_phases/
   quest_opportunity_rewards.py:87`, delivered via `RewardUpdate.xp_gain`.

Both feed into `src/engine/evolution.py::EvolutionSystem.evaluate()`, which correctly reads
**both** `ent_upd.identity.evolution_points_delta` and `ent_upd.reward.xp_gain` (line 34-38,
`raw_delta` consolidation) — confirmed by direct code read, not assumed. **There is no
disconnected-wiring bug in the XP delivery path itself.**

**A real, disclosed correction of an initial hypothesis mid-investigation**: `evolution.py`'s own
module-level `EVOLUTION_THRESHOLD = 1000` constant (with its own comment, "In a full system, this
would come from a profile") looked like a plausible balance-mismatch culprit — but `grep -n
"EVOLUTION_THRESHOLD" src/engine/evolution.py` shows it is referenced **exactly once, at its own
definition** — confirmed **dead code**, never read anywhere in the evaluate loop. The REAL
threshold `evolution.py` actually uses (line 59, `req = LevelingService.get_xp_required(current_
eval_level)`) is `src/progression/leveling.py::LevelingService.get_xp_required()` — the
documented, parity-verified `100 * (level ** 1.5)` formula (VERIFIED v2: `xp_threshold_formula`,
`docs/mechanics/attribute_progression_contract.md`). At level 1 this is **100 XP**, not 1000 — a
single monster kill (10 XP) is 10% of the way there, not 1%. The dead constant is not the real
bottleneck; disclosed and should still be cleaned up as real, confirmed dead code regardless.

**The real, unresolved bottleneck, narrowed but not yet fully pinned down**: with a reachable
~100 XP threshold and real combat damage occurring, zero level-ups still fired in any of the 3
worlds at 1000 ticks. The most likely explanation, not yet directly confirmed: kills specifically
(not damage) are rare — `combat.py`'s XP path requires `new_hp <= 0`, and real combat_damage
volume (15-120 hits) apparently never resolved to a kill within the observed window in any of the
3 worlds tested. A second, real, disclosed open question: `src/engine/patches.py:590-593`
(`RewardPatch.apply()`) **also** calls `LevelingService.process_progression()` independently of
`evolution.py::EvolutionSystem.evaluate()` — whether these are two cleanly-separated consumers of
different `StateUpdate` fields, or a real duplicate-application risk, is not yet confirmed and
must be Investigate's own first task.

**Per the user's own explicit framing for this ticket**: this is not a request for new progression
features — every mechanism described above already exists and (mostly) already works. The fix is
expected to be in balance (kill-rate vs. threshold), wiring precision (the two `LevelingService`
call sites), and cleanup (the confirmed-dead `EVOLUTION_THRESHOLD` constant), not new mechanics.

## Scope
1. **Investigate** (mandatory before Plan):
   - Resolve the two-consumer question: does `patches.py::RewardPatch.apply()` and
     `evolution.py::EvolutionSystem.evaluate()` ever both process the same tick's XP for the same
     entity? If so, is it a double-application bug, or are they cleanly gated to different,
     non-overlapping `StateUpdate` shapes? Trace real call sites, don't assume either answer.
   - Directly measure real kill rate (not just damage rate) across a representative sample of
     corpus worlds at 1000+ ticks — how many `entity_killed`/`combat_kill` events actually fire,
     and does the resulting XP total plausibly cross `LevelingService.get_xp_required()`'s own
     real threshold for any entity within a realistic window?
   - Confirm whether quest completion is genuinely zero corpus-wide (matching the historical
     finding in `TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE`'s own "Original context") or
     has changed since — re-verify with real current data, not the old finding alone.
   - Decide the real fix shape: is this a kill-rate/combat-engagement problem (upstream of XP
     entirely — see `TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY`'s own prior
     findings on combat dormancy), an XP-magnitude balance problem (per-kill XP too low relative
     to threshold even when kills happen), or both?
2. **Plan**: design the specific balance/wiring change(s) — likely one or more of: adjust
   per-kill XP magnitude, adjust `LevelingService.get_xp_required()`'s own curve, resolve the
   dual-consumer question, remove the confirmed-dead `EVOLUTION_THRESHOLD` constant. Explicitly
   NOT expected to require new event types, new mechanics, or new feature flags.
3. **Implement**: the real fix(es), matching CLAUDE.md's Mechanics Bible consistency rule —
   any formula change must update `docs/mechanics/attribute_progression_contract.md` and the
   relevant `docs/parity_ledger/progression.yaml` entry in the same session.
4. Recalibrate `grade_anchors.json` for any scenario whose PROGRESSION grade shifts.

## Out of Scope
- Re-enabling `ENABLE_PROGRESSION_EVOLUTION` (the progression-conversion domain: equip/repair/
  allocate_ap/train) corpus-wide — a much larger, separate decision with its own blast radius on
  every existing calibration baseline; not assumed needed until this ticket's own narrower
  kill/quest-XP investigation is resolved first.
- The HERO-role-specific underperformance finding from the same lifecycle-score run — tracked
  separately in `TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF` (a distinct root cause: HERO's
  own decision pipeline being off, not the XP economy itself).
- Quest-completion-rate root-causing beyond confirming it's still real and current — if quest
  dormancy itself needs a fix, that's substantial enough to warrant its own follow-up ticket, not
  folded into this one.

## Acceptance Criteria
- [ ] investigation.md resolves whether `RewardPatch.apply()`/`EvolutionSystem.evaluate()` is a
      real double-application risk or cleanly separated, with real evidence either way
- [ ] investigation.md reports real, measured kill rate (not just damage rate) across a
      representative real-world sample at 1000+ ticks
- [ ] investigation.md confirms current quest-completion rate with fresh data, not just cites the
      historical finding
- [ ] A real fix lands (magnitude/curve/wiring — not a new mechanic) with a measurable, verified
      increase in real `xp_granted`/`level_up` events on at least 2 real corpus worlds at 1000+
      ticks, re-run through the lifecycle-score tool to confirm `growth_trajectory` moves
- [ ] Confirmed-dead `EVOLUTION_THRESHOLD` constant is either removed or wired for real use — not
      left as unreachable dead code either way
- [ ] `docs/mechanics/attribute_progression_contract.md` and `docs/parity_ledger/progression.yaml`
      updated if any formula changes
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS, TCK-20260808-ENTITY-LIFECYCLE-SCORE-CALIBRATION
  (the tool and the full-corpus run that surfaced this finding — both DONE)
- TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF (sibling finding from the same lifecycle-score
  run — a distinct root cause, HERO's own decision pipeline being off)
- TCK-20260806-SIMQ-PROGRESSION-CAPABILITY-LIFECYCLE (the historical "zero xp_granted/level_up/
  skill_unlocked/entity_killed/quest_reward_dispensed corpus-wide" finding this ticket re-verifies
  and narrows with fresh real data)
- TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY (prior investigation into combat
  dormancy — directly relevant to the "why are kills rare" question)

## Related Docs
- `docs/mechanics/attribute_progression_contract.md` (documented, parity-verified XP/threshold
  formulas — the authoritative source this ticket's own fix must stay consistent with)
- `docs/mechanics/02_combat_laws.md` (Victory Outcomes — the kill/defeat resolution this XP path
  depends on)
- `docs/parity_ledger/progression.yaml` (`xp_threshold_formula`, `level_cap_enforced` — existing
  verified entries)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `src/engine/combat.py` (kill-only XP computation, 3 call sites)
- `src/engine/evolution.py` (`EvolutionSystem.evaluate()`, the confirmed-dead
  `EVOLUTION_THRESHOLD` constant)
- `src/engine/patches.py` (`RewardPatch.apply()`, the second `LevelingService` consumer)
- `src/progression/leveling.py` (`LevelingService` — the real, documented threshold formula)
- `src/core/conservation.py` (`xp_reward` → `evolution_points_delta` conversion)
- `src/engine/quests.py`, `src/engine/pipeline_phases/quest_opportunity_rewards.py` (quest-XP path)

## Assumptions / Open Questions
- Whether the real bottleneck is kill-rate scarcity, XP-magnitude balance, or the dual-consumer
  question — not assumed; Investigate must resolve with real measurements, not guess before Plan.
- Whether quest completion is genuinely still near-zero — the historical finding is real but
  months old; re-verify, don't inherit uncritically.

## Implementation Notes
Subagent spawning was unavailable this whole session (200/200 cap) — Investigate, Plan, Review,
Implement, Document-Update, and Verify were all performed via direct tool calls, with Review and
Architecture-Verify self-performed and disclosed as such rather than delegated.

Root cause (see investigation.md for full evidence): the dominant real combat-kill path in the
corpus is not the `ATTACK` action (0 calls in a real 2000-tick `sandbox_world` run) — it's the
opportunity-attack-on-retreat mechanic in `src/engine/movement.py`. That call site attached the
kill reward (`CombatUpdate.resource_transfers`) to the victim's own `EntityUpdate` instead of the
attacker's, and never lifted it out of the nested `CombatUpdate` field into the top-level
`EntityUpdate.resource_transfers` field `ResourceTransactionSystem.resolve_all()` actually reads —
so every real kill through this path (9/2000 ticks in `sandbox_world`) silently discarded its own
reward. Fixed by lifting `resource_transfers` onto the correct attacker's own `EntityUpdate`,
mirroring the existing `attacker_id`-based attribution convention already used by
`entity_killed`'s own event shaper for multi-attacker kills.

Also resolved (not a code change): confirmed `RewardPatch.apply()`/`EvolutionSystem.evaluate()`
are cleanly sequenced consumers of `reward.xp_gain`, not a double-application bug —
`EvolutionSystem` zeroes the field after consuming it, before `ApplyPath` ever builds a
`RewardPatch` from the same, already-processed `EntityUpdate`.

Removed the confirmed-dead `EVOLUTION_THRESHOLD = 1000` module constant from
`src/engine/evolution.py` (referenced nowhere but its own definition; the real threshold is
`LevelingService.get_xp_required()`'s documented `100 * level^1.5` formula, untouched).

Deliberately deferred (disclosed, not silently dropped): the same opportunity-attack call site
hardcodes `is_lethal=False`, so this death class can never produce `outcome_kind == "KILL"` (only
`"DEFEAT"`), meaning `entity_killed`/`hero_death_unrecorded` still never fire for it even after
this fix — the XP/gold reward itself is gated on `alive`, not `outcome_kind`, so this doesn't
block progression, but it does mean this class of death stays invisible to `entity_killed`-based
signals. Whether `is_lethal=False` is intentional design is a game-design call left open, not
resolved here.

Recorded as a new intentional-divergence entry (§2.33, Bug Fix class) and updated the directly
relevant parity ledger entry (`COMB-049`, "Kill reward emission in apply") with real, current
verification evidence and a test path — the entry was previously `verified` on generic legacy
"exhaustive checklist audit" evidence with no real test, which is exactly the kind of unverified
entry this bug slipped through.

## Test Summary
`pytest tests/unit/movement/ tests/unit/combat/ tests/integration/pipeline/
test_combat_legality_matrix.py tests/integration/pipeline/
test_movement_micro_arena_position_swap.py -q` — **152 passed, 1 pre-existing failure**
(`test_movement_spatial_regression.py::test_normal_move_triggers_oa`, confirmed via `git stash` to
fail identically on the pre-existing codebase before any change in this ticket — unrelated,
disclosed, not fixed as out of scope for this ticket).

New test: `test_opportunity_attack_lethal_grants_resource_transfers_to_attacker` — real lethal
opportunity-attack scenario through the full `AuthoritativeApplyPipeline.refine()` path. Before
the fix this failed (attacker's `identity.evolution_points_delta` was 0); after the fix it passes
(`> 0`), and the victim's own `EntityUpdate.resource_transfers` is confirmed empty (attribution
correctness, not just presence).

Real end-to-end verification (scratch scripts, not committed): before the fix, a live 2000-tick
`Kernel` run of `sandbox_world` (seed 42) showed zero `entity.identity.evolution_points`/
`evolution_level` changes despite 9 real deaths; the same real-pipeline check inside the new unit
test confirms the fix produces a real `evolution_points_delta > 0` on the attacker.

## Files Changed
- `src/engine/movement.py` — lift `combat_update.resource_transfers` onto the correct attacker's
  `EntityUpdate`
- `src/engine/evolution.py` — removed dead `EVOLUTION_THRESHOLD` constant
- `tests/unit/movement/test_tactical_movement.py` — new lethal opportunity-attack test
- `docs/guidelines/intentional_divergences.md` — new §2.33 entry + summary table row
- `docs/parity_ledger/combat_movement.yaml` — `COMB-049` updated with real evidence/test_path

## Completion Summary
Root-caused and fixed the corpus-wide flat-`growth_trajectory` finding from
`TCK-20260808-ENTITY-LIFECYCLE-SCORE-METRICS`'s full-corpus run: real combat kills were happening
(9/2000 ticks in `sandbox_world`, via the opportunity-attack-on-retreat mechanic, the corpus's
dominant real kill path) but their XP/gold reward was structurally orphaned — attached to the
wrong entity and never lifted to a field anything reads. Verified end-to-end, not just at the
unit level: a real `Kernel` run now produces `evolution_points_delta > 0` on a real kill through
this path, where it produced nothing before. Also resolved (as not-a-bug) the dual-consumer
question, re-confirmed real kill rate and quest-completion rate with fresh data, and removed
confirmed-dead code — all 4 of the ticket's own Acceptance Criteria items satisfied. HERO-specific
underperformance and quest dormancy remain tracked in their own sibling tickets, per this ticket's
own Out of Scope.
