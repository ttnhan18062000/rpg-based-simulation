# Implementation Sequence — progression-starvation-chain

`TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` is the epic-tier parent and is not implemented
directly — it groups and sequences the five tickets below, each of which keeps its own scope and
acceptance criteria unchanged.

## Order

1. `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` (P0, **done** — closed to
   `agent-working/tickets/done/`; status corrected here 2026-09-29, this file previously said "open") — asked why
   the decision-driven `ATTACK` path fires 0-2 times per 1000-2000 ticks while the incidental
   opportunity-attack mechanic fires 181-2177. All four candidates confirmed or ruled out by direct
   per-world measurement through a real `Kernel.tick_once()` loop.
   **Verdict, from its own 2026-09-19 addendum: the decision layer does not fail to choose combat —
   it chooses combat and the choice is discarded at dispatch.** `GoalKind.COMBAT_ENGAGE` wins the
   goal competition, then `intelligence.py`'s winner-consumption code falls into a generic branch
   that hardcodes the objective kind to `"reach_location"`, never derived from the winning goal.
   `ObjectiveKind.DEFEAT_ENEMY` is created only through an unrelated scorer. A dead branch by
   construction. Re-verified still live in `src/` on 2026-09-29
   (`src/systems/strategic_systems/intelligence.py:1711`; scorer now at `src/ai/goals/scorers.py:101`,
   which the closed ticket cites as `:108` — that citation has drifted 7 lines).
2. `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` (P1, **still blocked in practice —
   correction, 2026-10-03**) — the older, broader investigation that first found combat to be incidental rather than
   decisional, and whose own 2026-09-17 addendum reframed its remaining open question into exactly
   what (1) investigates. Its own one unresolved lead (a static region-overlap comparison between
   `crowded_frontier` and `frontier_living_world`, not yet verified live) may or may not still need
   checking once (1) lands — that is for whoever picks this up to determine, not assumed here.
3. `TCK-20260915-COMBAT-GATE-DOWNSTREAM-STARVATION-FACTION-AND-BOSS-GATE` (P2, open — boss-gate half
   only; the faction-chain half is already resolved, citing (2)'s own 2026-09-17 addendum).
   **PARKED, 2026-10-05, by owner deferral — do not pick it up.** The owner was asked directly whether
   the world-boss deferral covers the lair world boss (the `BossService` maturity gate, live and proven)
   or only the calamity boss, and ruled **both**. The boss-gate half's entire downstream is therefore
   deferred, so there is nothing for it to starve that anyone is measuring. It is **not** independently
   runnable, which earlier revisions of this file claimed. Nothing is removed: the live lair-boss path
   stays as it is, and boss spawns remain not evidence for anything (memo row 10).
4. `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS` (done — not reopened).
   Already root-caused: the combat-XP-to-level-up-to-`stats_dirty` chain is confirmed correctly
   wired via a real Kernel-tick positive control. Referenced here for the chain's own narrative
   completeness, not because there is remaining work.
5. `TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME` (P1, **blocked** — must run last).
   Already self-declared blocked on (2) landing, per that ticket's own Status field: retuning the XP
   threshold or per-kill values against today's starved combat volume would silence the signal
   (entities barely fight) rather than fix what the signal reports on — the same failure shape as
   lowering an attribution ratchet to fit a low score. This epic restates that constraint at the
   sequence level so it is visible without opening the individual ticket.

## Correction, 2026-10-03 — why this epic is idle, and why that is correct

**The epic-staleness check will keep flagging this folder. The idleness is a recorded dependency, not
neglect.** Recorded here so the next reader does not have to re-derive it, and does not "unstick" the
epic by dispatching a child whose prerequisite has not landed.

**What landed is item (1)'s *investigation*, not its *fix*.** The distinction was blurred in the
line above, which this correction replaces. The investigation closed with the verdict — `COMBAT_ENGAGE`
wins the goal competition and the win is discarded at dispatch. The **fix** for that verdict is
`TCK-20261002-GOAL-WINNER-CONSUMPTION-DISCARDS-DECIDED-OBJECTIVE-KIND`, PR **#291**.

> **UPDATE 2026-10-04: #291 IS NOW MERGED.** `mergedAt` 2026-10-04T10:33:12Z, merge commit
> `f4146ddbb`, confirmed as the tip of `origin/main`. **The hold is lifted and the fix has landed**, so
> the "held pending #291" half of this correction is spent. `rpg-feature-planning` withdrew its hold
> before the merge on the ground below: the nondeterminism is **pre-existing** and #291 did not cause it,
> so gating the fix on a bug it did not introduce was the wrong shape of caution. **What has NOT changed
> is the determinism caveat** — read the next paragraph as a live constraint on *measurement*, not as a
> reason the fix is still blocked.

`rpg-feature-planning` originally **recommended holding** #291 on determinism grounds, and the
underlying fact is unchanged by the merge: its AC6 landed **contradicted**, not merely undemonstrated —
**780 vs 1609 opportunity attacks on identical runs**, a divergence recorded as
`TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE` and one that **survives
`audit_mode=True` and a raised `max_tick_budget_ms`**, unlike the `INFRA-273` throttle.

**Why that blocks item (2) specifically.** Item (2) is a corpus *measurement* ticket — it counts
cross-faction hostile interaction. It runs on the same combat/tactical path the nondeterminism was
measured on. **Any count it takes before that divergence is settled is unreliable at the precision the
ticket needs**, and dispatching it would produce numbers that look authoritative and are not. This is
the same failure shape the epic's own closing section warns about for item (5).

**So the real sequence head is now** (revised 2026-10-04, #291 having merged): **#291 has landed**, so
item (2) is no longer waiting on a fix. What remains ahead of it is
`TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE` — **settled, or a different
instrument established** — because item (2) is a corpus *measurement* ticket and runs on exactly the path
that divergence was measured on.

**The distinction that matters for whoever picks item (2) up:** it is **not blocked from running**; it is
blocked from producing numbers it can *claim precision for*. If item (2)'s question can be answered at
order-of-magnitude — e.g. "is cross-faction hostile interaction zero or non-zero" — it can run **now**
against a post-#291 corpus and that is a genuine result. If it needs exact counts, the nondeterminism
ticket comes first. **Decide which before dispatching**, and record the choice, rather than taking counts
and discovering afterwards that they were not reproducible.

Item (5) is unaffected by this correction and remains last. **Item (3) is no longer independently
runnable**: it is parked by the owner's world-boss deferral (2026-10-05, covering both the calamity boss
and the lair world boss). An earlier revision of this line said otherwise; that claim is withdrawn.

~~Whether #291 lands as-is is **its own user's decision, not this epic's.**~~ **It landed, 2026-10-04,
with AC6 unmet.** The one thing asked of its ticket still stands and is **outstanding**: that it record
AC6 as *failed and knowingly accepted*, with the 780-vs-1609 numbers and a pointer to
`TCK-20261003-COMBAT-TACTICAL-PATH-NONDETERMINISM-SURVIVES-AUDIT-MODE`. **This is not this epic's to
enforce** — it belongs to #291's own ticket and user — but it is noted here because a reader arriving at
this chain later will see an AC that *looks* met on a merged PR, and the measurement says otherwise.

## Why This Order Matters

**The root of the chain is a mechanism question, not a tuning question, and mechanism questions come
first.** (1) was the most sharply scoped, most actionable, and highest-priority (P0) link — it asked
a single, well-instrumented question (why does the decision path never fire) with four concrete
candidates and a clear measurement plan. **It has now landed, and it answered the chain's root
question**: the dispatch discard, not perception, scoring or tuning. (2)'s own final addendum had
already reframed its remaining question into (1)'s exact scope, so (2) should be re-read against
(1)'s verdict before any fresh measurement — a good part of it may already be answered.

**Note the chain's centre of gravity has moved.** The root cause now sits in the goal-dispatch path
(`src/ai/goals/`, `src/systems/strategic_systems/`), not in progression or combat resolution. Any
fix routed from this chain lands there, which is worth knowing before picking up (2) or (3).

**(3)'s boss-gate half is real but lower-stakes and less coupled to the rest of the chain** — it
checks whether an already-confirmed-correct gate further starves a different, unrelated downstream
system (the world-boss maturity trigger), not whether the gate is wrong. **It is parked (2026-10-05):
the owner's deferral covers both the calamity boss and the lair world boss, so its downstream is
deferred too.** The earlier statement that it "can run in parallel with (1)/(2)" no longer applies.
Revisit only if the boss deferral is lifted.

**(4) needs no further sequencing — it is done.** It stays in `agent-working/tickets/done/` root rather than
moving into this epic's own folder, matching this repo's own established epic-folder precedent (see
`agent-working/tickets/done/mechanism-registry/`, where a closed epic's own folder holds only the epic ticket and
`SEQUENCE.md`, and every real child closes individually to `agent-working/tickets/done/` root, never nested inside
the epic's folder). It is listed in this sequence purely so the chain's own narrative is complete
without having to open a separate epic-closure record to find it.

**(5) is last by explicit, pre-existing constraint, not by this epic's own invention.**
`TCK-20260917-XP-LEVEL-UP-THRESHOLD-VS-CORPUS-COMBAT-VOLUME`'s own Status field already recorded
this blocking relationship before this epic existed — this sequence file states it again at the
group level so it is visible to whoever opens the epic without having to read into any one child's
own Status field first.

## One thing this epic explicitly does not do

**It does not re-derive or re-litigate `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION`'s
own priority.** That investigation was originally selected because `tactical_decision` (the
mechanism it investigates) ranked at or near the top of `registries/mechanisms.yaml`'s own derived
"which mechanism to verify next" priority — a ranking that `TCK-20260917-MECHANISM-DEPENDS-ON-EDGE-SEMANTICS-AUDIT`
has since re-derived, dropping `tactical_decision` to zero transitive dependents. **The investigation's
own real corpus measurement (the 181-2177-vs-0-2 call-count split, independently corroborated by two
other unrelated investigations across a month) does not depend on why the mechanism was originally
selected, and this chain's own priority (P0 for item 1 above) is unaffected by that ranking's own
collapse.** Recorded here explicitly, per direct instruction, so this real and substantial
investigation does not read as retracted or deprioritized by an unrelated registry-tooling finding.
