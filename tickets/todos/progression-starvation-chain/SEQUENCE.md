# Implementation Sequence — progression-starvation-chain

`TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` is the epic-tier parent and is not implemented
directly — it groups and sequences the five tickets below, each of which keeps its own scope and
acceptance criteria unchanged.

## Order

1. `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` (P0, open, no deps in this batch) —
   the sharpest, most actionable open question in the chain: why the decision-driven `ATTACK` path
   fires 0-2 times per 1000-2000 ticks while the incidental opportunity-attack mechanic fires
   181-2177. Investigate and report only; four candidate causes to confirm or rule out by
   measurement.
2. `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` (P1, paused — resume with (1)'s
   findings) — the older, broader investigation that first found combat to be incidental rather than
   decisional, and whose own 2026-09-17 addendum reframed its remaining open question into exactly
   what (1) investigates. Its own one unresolved lead (a static region-overlap comparison between
   `crowded_frontier` and `frontier_living_world`, not yet verified live) may or may not still need
   checking once (1) lands — that is for whoever picks this up to determine, not assumed here.
3. `TCK-20260915-COMBAT-GATE-DOWNSTREAM-STARVATION-FACTION-AND-BOSS-GATE` (P2, open — boss-gate half
   only; the faction-chain half is already resolved, citing (2)'s own 2026-09-17 addendum). Can run
   independently of (1)/(2) if convenient, but sequenced after them since it is lower priority and
   partially informed by their findings.
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

## Why This Order Matters

**The root of the chain is a mechanism question, not a tuning question, and mechanism questions come
first.** (1) is the most sharply scoped, most actionable, and highest-priority (P0) open link — it
asks a single, well-instrumented question (why does the decision path never fire) with four
concrete candidates already identified and a clear measurement plan. Resolving it is likely to
directly inform, and possibly close, (2)'s own long-paused broader investigation, since (2)'s own
final addendum already reframed its remaining question into (1)'s exact scope.

**(3)'s boss-gate half is real but lower-stakes and less coupled to the rest of the chain** — it
checks whether an already-confirmed-correct gate further starves a different, unrelated downstream
system (the world-boss maturity trigger), not whether the gate is wrong. It can run in parallel with
(1)/(2) without blocking or being blocked by them, but is sequenced after because P2 is genuinely
lower priority than P0/P1.

**(4) needs no further sequencing — it is done.** It stays in `tickets/done/` root rather than
moving into this epic's own folder, matching this repo's own established epic-folder precedent (see
`tickets/done/mechanism-registry/`, where a closed epic's own folder holds only the epic ticket and
`SEQUENCE.md`, and every real child closes individually to `tickets/done/` root, never nested inside
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
