---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260915-SENTIMENT-HOSTILE-THRESHOLD-REACHABILITY
phase: done
date: 2026-09-15
tags: [world, faction]
---

# TCK-20260915-SENTIMENT-HOSTILE-THRESHOLD-REACHABILITY

## Title
Post-fix, faction sentiment reliably reaches `TENSE` but has not been shown to reach `HOSTILE`
organically — a real 9000-tick run plateaus well short of the threshold; same reachability shape
as the maturity-gate and D-05 findings this week

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION` built `FactionSentimentService`, proved it
end-to-end, and in the process found and fixed a real defect: `DiplomaticStateMachine.compute_transitions()`
was reading `FactionState.tension_level` (an ambient, per-faction scalar) as a stand-in for
pairwise tension, so one faction's real fight with a single rival cascaded into blanket `HOSTILE`
with every faction in the world. That was fixed by introducing `FactionState.pairwise_tension`
(directed, per-rival) and re-scoping `compute_transitions()` to read it.

**Re-running the same acceptance scenario after the fix surfaced a new, honest finding**: the one
real interacting pair in a real 9000-tick `frontier_living_world` run (`bandit_company` <->
`wild_beast_pack`) reached `TENSE` and then **plateaued at `pairwise_tension = 0.418`**, never
approaching the `0.7` `HOSTILE` threshold, across the full run. A pre-fix run had reached `HOSTILE`
for this same pair, but that observation depended on the now-removed cascade (the aggregate scalar
being fed by more than just this one relationship) and is not representative of current, correct
behaviour. As of this ticket, **`HOSTILE` has not been demonstrated to be reachable through
ordinary play with the cascade fixed.**

This is explicitly the same shape as `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY`
and the original D-05 finding in this ticket's own parent: a mechanism that is real, wired, and
documented as working, but that real play does not actually reach.

## Scope
- **Investigation first — do not assume the answer.** Determine, with real evidence (not
  extrapolation from the one 9000-tick run already done), whether the sentiment -> pairwise_tension
  escalation curve genuinely plateaus below `0.7` by design, or whether it is blocked by a further,
  as-yet-unidentified reachability gate (the same "not one big number, several small compounding
  gaps" shape found in the parent ticket's original investigation).
- Concretely check at minimum:
  1. Whether the plateau at `0.418` reflects the real rival pair's combat simply stopping (e.g. one
     side dispersing, moving apart, or being reduced in number) rather than a mechanical ceiling —
     i.e. is this an interaction-volume problem, not a formula problem?
  2. Whether `FACTION_SCALE_FACTOR` (`0.1`, provisional per the spec's own §3.2.3 note) is simply
     too small for realistic interaction volumes to cross `0.7` within a normal simulation horizon,
     and if so, what scale factor (or decay interval) would make `HOSTILE` reachable without making
     it trivial.
  3. Whether `decay_stale_sentiments()`'s periodic decay (`DECAY_FACTOR=0.9` every `DECAY_INTERVAL=500`
     ticks once stale) is actively working against sustained escalation for pairs whose combat comes
     in bursts rather than continuously — i.e. does the mechanism's own decay undercut its own
     escalation before a threshold can be crossed.
  4. Run across more than one corpus world/seed before concluding a general answer — this ticket's
     parent found world-specific behavior (`urban_political` vs `frontier_living_world`) earlier in
     the same investigation; don't generalize from a single world again.
- Out of scope: re-opening the cascade fix itself, re-litigating the additive-field-vs-rename
  decision, or building loop #1 (`military_strength`) / `WAR` reachability — those remain separately
  scoped.

## Out of Scope
- The `military_strength` / `WAR`-reachability gap (loop #1) — already explicitly deferred by the
  parent ticket's own acceptance bar; not this ticket's concern.
- Re-deriving or redesigning the sentiment formula from scratch — this is a reachability
  investigation into the *existing* built mechanism, not a request to re-propose it.
- The importance-weighting cut (`TCK-20260915-FACTION-IMPORTANCE-SIGNAL-INITIATIVE`) — separate,
  already filed.

## Acceptance Criteria
- A real, evidence-backed answer (not assumption) to: is `HOSTILE` reachable through ordinary play
  post-fix, and if not yet observed, what specifically blocks it (interaction volume, scale factor,
  decay working against escalation, or something else)?
- If a genuine gap is found and a fix is proposed, it must be reviewed before being built — same
  sequencing discipline as the parent ticket (design/tuning changes go to peer first).
- If the honest answer is "the mechanism is correct and `HOSTILE` requires sustained real conflict
  this world's content doesn't produce, and that's fine" — that is an acceptable, valid outcome,
  as long as it's stated plainly rather than left ambiguous.

## Related Tickets
- `TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION` (parent — built sentiment, found and fixed
  the tension_level cascade defect, surfaced this finding)
- `TCK-20260914-LAIR-WORLD-BOSS-MATURITY-GATE-REACHABILITY` (same reachability-gap shape, done)
- `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` (sibling reachability gap in the same faction
  subsystem, still open)
- `TCK-20260915-FACTION-IMPORTANCE-SIGNAL-INITIATIVE` (separate, scoping-only)
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` (filed at close — this ticket's own
  investigation found the real blocker is one level down: cross-faction hostile interaction is
  itself rare and seed-fragile, not a tunable threshold/decay problem)

## Related Docs
- `docs/plans/rpg_design_roadmap/faction_war_drivers_proposal.md` (§3.2, §4 — the sentiment spec
  and its acceptance bar; carries the post-build finding banner this ticket was filed from)

## Related Stored Artifacts
_(none yet — filed as a finding from the parent ticket's own build/verification, not yet
investigated)_

## Related Code Areas
- `src/domains/faction/sentiment.py` (`FactionSentimentService` — `FACTION_SCALE_FACTOR`,
  `DECAY_INTERVAL`, `DECAY_STALENESS_THRESHOLD`, `DECAY_FACTOR`)
- `src/domains/faction/diplomatic_state_machine.py` (`compute_transitions()` — the `0.7` `HOSTILE`
  threshold read against `pairwise_tension`)
- `src/core/state.py` (`FactionState.pairwise_tension`)

## Assumptions / Open Questions
- Not yet known whether this is a tuning problem (raise `FACTION_SCALE_FACTOR` or lower the
  threshold) or a genuine second reachability gate. Do not assume either before measuring.

## Implementation Notes
**2026-09-15, investigation complete.** Three checks run, all real evidence, no code changes (per
Scope's own "do not assume" instruction, and confirmed no fix is safe to apply yet — see
Conclusion below).

**1. `shared_territory` is not a second path to `HOSTILE` — it is completely dead across the
entire corpus.** Checked `FactionState.territory` at world-compile time in all 14 real,
non-unit-test corpus worlds (`frontier_living_world`, `frontier_extended`, `frontier_marches`,
`crowded_frontier`, `urban_political`, `sandbox_world`, `wilderness_survival`,
`highland_traverse`, `quest_dense_frontier`, `resource_dense_basin`, `swamp_border_world`,
`dungeon_crawl`, `hero_guild_routing`, `generated_frontier_3_42`): **0 of 14 have any faction with
nonempty territory; 0 faction pairs ever share territory.** `territory_add`'s only real producer
is siege-won transfer (`src/engine/military_conflict.py`), itself gated on an existing `WAR` —
same circularity the parent ticket's original investigation found for loop #2. This means
`pair_tension > 0.7` via sentiment is the *only* route to `HOSTILE` anywhere in the real corpus
today, confirmed rather than assumed.

**2. The `0.418` plateau is not a decay-vs-escalation race.** Grepped every producer of
`pairwise_tension`/`pairwise_tension_delta` in `src/` — the only writers are
`FactionSentimentService.derive_from_bond_updates()` (real combat) and
`diplomatic_actions.py`'s treaty/trade/betrayal handlers (deliberate peace-making, negative
deltas only on an accepted treaty/trade). **There is no decay producer for `pairwise_tension` at
all** (decay only touches `faction_sentiments`, a different field). So `pairwise_tension` is
purely additive and monotonic outside deliberate diplomacy — a plateau means the contributing
interaction stopped, not that something eroded it. Confirmed check #3 from Scope: decay is not
fighting escalation, because decay doesn't apply to this field.

**3. Multi-world AND multi-seed sampling — this is the decisive finding, and it overturns an
early, wrong hypothesis.** Sampled 3 more real worlds (`crowded_frontier`, `quest_dense_frontier`,
`urban_political`) at 4000 ticks each: **`pairwise_tension` stayed at exactly `0.0` for every
faction pair, the entire run, in all three.** Only `frontier_living_world` showed any nonzero
tension among the 4 worlds sampled. This alone looked like a "one world is fine, three aren't"
story, and the natural next question was whether `frontier_living_world`'s real interaction
volume (~42 hostile hits, back-of-envelope from `0.418 / ~0.01 per hit`) was simply short of
crossing `0.7`, tunable by raising `FACTION_SCALE_FACTOR`.

**Ran `frontier_living_world` itself across 5 seeds (42, 7, 123, 999, 2026) at 6000 ticks each to
check whether that volume is typical before leaning on it for a tuning fix — the exact "measure
spread before leaning on a field" rule this arc has now needed twice before.** Result:
```
seed=42:   max_pairwise_tension=0.4180
seed=7:    max_pairwise_tension=0.4180
seed=123:  max_pairwise_tension=0.6500
seed=999:  max_pairwise_tension=0.0000
seed=2026: max_pairwise_tension=0.0100
```
**The interaction volume is not typical or stable — it is a lottery, even within the single world
that "works."** Two of five seeds produce essentially nothing (`0.0`, `0.01`); the other three
range from `0.418` to `0.65`, none crossing `0.7`. A scale-factor bump calibrated to seed 42's
`0.418` would do nothing useful for seed 999 (there is no interaction to scale up) and might
overshoot for seed 123. **This is not a formula/threshold tuning problem — it is the same
underlying problem as finding #3 above, just visible within one world instead of only across
worlds**: cross-faction hostile interaction itself is fragile and inconsistent, and no single
`FACTION_SCALE_FACTOR` value reliably converts "whatever interaction happens to occur" into a
real `HOSTILE` crossing across the corpus.

## Conclusion (Acceptance Criteria's third option, taken honestly)
**`HOSTILE` is not reachable through ordinary play today, and the reason is not the sentiment
mechanism itself — sentiment correctly reflects real interaction whenever real interaction
happens. The actual blocker is one level down: cross-faction hostile interaction is itself rare
and seed-fragile, in `frontier_living_world` and near-absent in the other 3 worlds sampled.**
`FACTION_SCALE_FACTOR` tuning was the tempting fix and is explicitly **not** proposed here,
because the multi-seed check shows it would not reliably work — this is the "measure before you
lean on it" discipline paying for itself with a negative result instead of a shipped-but-fragile
tuning value.

Filed the real root-cause question as its own ticket, not folded into a tuning change here:
`TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`. It is now a **prerequisite** for both
(a) any further `HOSTILE`-reachability work on this ticket's own scope, and (b) the
military-strength/`WAR` driver work the user asked for next — building `WAR` reachability on top
of a `HOSTILE` gate that mostly isn't reached would repeat this week's own core pattern with full
knowledge of the risk.

## Test Summary
No code changed; no new tests. Evidence gathered via direct instrumentation probes (multi-world
territory-overlap check, multi-world tension sampling, multi-seed tension sampling against
`frontier_living_world`), consistent with this ticket's own investigation-first scope.

## Files Changed
_(none — investigation only, per this ticket's own scope)_

## Completion Summary
Investigation complete. `HOSTILE` reachability is confirmed blocked, and the blocker is
root-caused to cross-faction hostile interaction itself being rare and seed-fragile — not a
tunable threshold/decay problem, and not something this ticket should patch with a scale-factor
change the evidence shows wouldn't reliably work. Real root cause filed as
`TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`, explicitly sequenced as a prerequisite
before the military-strength driver. No implementation in this ticket; none was safe to make.
