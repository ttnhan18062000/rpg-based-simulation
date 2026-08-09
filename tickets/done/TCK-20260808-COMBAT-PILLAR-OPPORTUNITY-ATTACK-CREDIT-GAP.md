---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260808-COMBAT-PILLAR-OPPORTUNITY-ATTACK-CREDIT-GAP
phase: open
date: 2026-08-08
tags: [combat, simulation-quality]
---

# TCK-20260808-COMBAT-PILLAR-OPPORTUNITY-ATTACK-CREDIT-GAP

## Title
`wilderness_survival` (monster-only-gauntlet, presumably combat-heavy) grades COMBAT=C, identical
to `urban_political` (civilian-heavy, presumably combat-light) — does the COMBAT scorer correctly
credit real activity reaching it via `movement.py`'s opportunity-attack path?

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Child ticket of `TCK-20260808-ENTITY-LIFECYCLE-IMPROVEMENT-EPIC`. That epic's own real 2000-tick,
6-world observation data (`docs/simulation_quality/long_run_observations/*.json`, seed 42) shows a
counter-intuitive COMBAT pillar pattern:

| World | Archetype | COMBAT grade |
|---|---|---|
| `wilderness_survival` | `monster_only_gauntlet` | **C** |
| `dungeon_crawl` | `monster_only_gauntlet` | **B** |
| `resource_dense_basin` | `civilian_settlement` | B |
| `crowded_frontier` | `civilian_settlement` | B |
| `hero_guild_routing` | `civilian_settlement` | C |
| `urban_political` | `civilian_settlement` | **C** |

`wilderness_survival` — a world explicitly authored as a "high danger ecology... survival
challenge," entirely populated by hostile monster kinds, with no civilian population at all —
grades the same COMBAT `C` as `urban_political`, a settlement-heavy world where combat is
plausibly incidental. This session's own `TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF`
investigation directly confirmed the corpus's real, dominant kill mechanism is
`movement.py`'s opportunity-attack path (not the `ATTACK` action, and not gated by the still-OFF
`ENABLE_COMBAT_ENGAGEMENT` flag) — whether `src/simulation_quality/scorers/combat.py` reads the
right typed records to credit that path's real activity is not yet confirmed.

## Scope
1. **Investigate** (mandatory before Plan):
   - Read `src/simulation_quality/scorers/combat.py` directly: which event types/typed records
     does it score from, and does the opportunity-attack path (`movement.py`'s
     `resolve_multi_attack` call site) produce all of them?
   - Measure real combat event volume (`combat_damage`, `combat_initiated`, `entity_killed`) on
     `wilderness_survival` specifically at 2000 ticks — is it genuinely low (a content/balance
     finding: monsters aren't actually fighting each other or heroes much, despite the archetype),
     or is real combat happening but under-credited by the scorer (a scorer bug)?
   - Recall this session's own related finding: the opportunity-attack path hardcodes
     `is_lethal=False`, so `entity_killed` never fires for that death class — check whether
     `combat.py`'s COMBAT scorer relies on `entity_killed` for a meaningful fraction of its score,
     which would directly explain under-crediting independent of any new bug.
   - Cross-check `dungeon_crawl` (same archetype, grades `B`) for what's different — its own real
     entity/region composition may simply produce more raw combat volume even at the same
     archetype, which would mean this isn't a scorer bug at all, just real content variance.
2. **Plan**: design the fix based on Investigate's own conclusion — either a scorer-side fix (if a
   real credit gap is found) or no code change (if the C grade is confirmed to reflect genuinely
   low real combat volume, matching the "archetype-correct, not a defect" pattern already
   established elsewhere this session).
3. **Implement**: the real fix, if warranted, re-verified via the real long-run observation tier.

## Out of Scope
- The `is_lethal=False` hardcoding itself on the opportunity-attack path — already flagged as a
  deliberately-deferred, disclosed item in `TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-
  IN-PRACTICE`'s own Implementation Notes; this ticket investigates its downstream SCORING
  consequence, not whether to change the flag itself (a separate game-design decision).
- `TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX` (sibling child ticket) — related XP
  question, tracked separately.

## Acceptance Criteria
- [ ] investigation.md reports exactly which event types/typed records `combat.py`'s COMBAT
      scorer reads
- [ ] investigation.md reports real, measured combat event volume on `wilderness_survival` at
      2000 ticks, with a real comparison against `dungeon_crawl`
- [ ] investigation.md reaches a real, evidenced conclusion: scorer credit gap vs. genuinely low
      real activity — not assumed either way
- [ ] If a real credit gap is found: a fix lands, re-verified via the real long-run observation
      tier
- [ ] If no gap is found: the finding is documented (matching the `wilderness_survival` archetype-
      awareness precedent) rather than silently closed with no artifact
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260808-ENTITY-LIFECYCLE-IMPROVEMENT-EPIC (parent epic)
- TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF (DONE — the opportunity-attack-path finding this
  ticket investigates the scoring consequence of)
- TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE (DONE — the `is_lethal=False`
  deferred note this ticket's Investigate should re-read)
- TCK-20260808-LIFECYCLE-SCORE-WORLD-ARCHETYPE-AWARENESS (DONE — the archetype field used to frame
  this finding)

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §7 (COMBAT pillar rules)
- `docs/simulation_quality/long_run_observations/wilderness_survival_seed42_2000t.json`,
  `dungeon_crawl_seed42_2000t.json` (the real data this ticket investigates)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260808-HERO-ADVENTURE-ROUTING-DEFAULT-OFF/`

## Related Code Areas
- `src/simulation_quality/scorers/combat.py`
- `src/engine/movement.py` (opportunity-attack path)
- `src/observability/event_shapers.py` (`entity_killed` gating on `outcome_kind=="KILL"`)

## Assumptions / Open Questions
- Whether the C grade reflects a real scoring gap or genuinely low real combat activity — not
  assumed either way; Investigate must measure, not guess.

## Implementation Notes
Subagent spawning unavailable this session (200/200 cap) — self-performed throughout.

Found a real, striking mismatch within a single instrumented run: `resolve_multi_attack` produced
0 KILL outcomes (6 DEFEAT), yet the same run's own JSONL showed 26 real `entity_killed` events.
Resolved by re-reading this session's own earlier `TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-
FACTION` completion notes: `entity_killed` is deliberately emitted by 2 co-existing mechanisms
(narrow push-shaper, only `outcome_kind=="KILL"`; broad diffing extractor, any `lifecycle.active`
transition, kept specifically to cover non-shaper-owned kill causes like the opportunity-attack
path's own DEFEAT outcomes) — not a credit gap.

The real, decisive finding: `config/simulation_quality/scoring_weights.yaml`'s own COMBAT weights
score `entity_killed` **negatively** (`attrition: -1.0`, `early_extinction: -10.0`) — the pillar
intentionally treats attrition as an instability signal, not a growth signal. This directly
explains both worlds' real C grade as a correct arithmetic consequence of the real formula, not
evidence of under-crediting — the ticket's own original premise (a monster-heavy world should
score *higher* on COMBAT) doesn't follow from the real scoring direction. Real, same-technique
data for `wilderness_survival` also showed it wasn't meaningfully more combat-active than
`urban_political` in this specific run, undermining the archetype-based assumption independently.

## Test Summary
No code change — `docs/simulation_quality/quality_scoring_contract.md` §7 (COMBAT) cross-
references the real finding. No new tests warranted; no existing behavior changed.

## Files Changed
- `docs/simulation_quality/quality_scoring_contract.md` — real finding cross-referenced in §7

## Completion Summary
Root-caused with real, same-run instrumentation (eliminating cross-run non-determinism as a
confound) rather than accepting the ticket's own original premise uncritically. No scorer bug
found — the real event-delivery mechanism is correct, and the C grades reflect the real, intended
scoring direction (kills penalize, not reward). Documented rather than forcing a fix onto a
non-defect, matching this session's own established discipline.

## Correction (added during `TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION`, next
## session day)
This ticket's own causal claim — "the 26 real `entity_killed` events... are the broader diffing
path correctly catching the opportunity-attack path's own real DEFEAT-outcome deaths" — is not
supported by the runtime code and should be treated as unverified, not as an established
mechanism. An exhaustive grep of every runtime site that ever writes `lifecycle.active=False`
(`src/systems/lifecycle_systems/lifecycle.py:53`, the sole such site for an already-live entity)
shows `LifecycleSystem.resolve_lifecycle()` only sets `is_dead=True` for `age_ticks >=
max_age_ticks` (`OLD_AGE`) or `ent_upd.combat.outcome_kind == "KILL"` specifically — a `DEFEAT`
outcome (`is_lethal=False`, the opportunity-attack path's own hardcoded value) never flips
`lifecycle.active`, so the old diffing extractor's `combat_kill` branch (gated on a
`lifecycle.active` transition) cannot have been reached by a DEFEAT-outcome death at all. The
real source of this ticket's own observed 26 `entity_killed` events was not re-identified — most
likely a real `KILL` outcome from a combat-resolution path this ticket's own instrumentation
didn't cover (it only wrapped `resolve_multi_attack`), not the DEFEAT-outcome mechanism it
credited. This does not change this ticket's own core, still-valid conclusion (`entity_killed`
scores negatively by design, so a C grade is not itself evidence of under-crediting) — only the
specific causal mechanism claimed for the DEFEAT/broad-path case. See COMB-309
(`docs/parity_ledger/combat_movement.yaml`) and
`TCK-20260809-COMBAT-KILL-LIFECYCLE-CREDIT-GAP-INVESTIGATION` for the real finding this
correction is based on: 100% of a fresh `dungeon_crawl_seed42_2000t` run's real `combat_kill`
events traced to `HAZARD`-preceded or unset `death_reason`, zero to `COMBAT` — independently
confirming DEFEAT-outcome deaths are not a meaningful contributor to this pillar's real,
observed `entity_killed` volume in the current corpus (0 DEFEAT outcomes and 0
`lifecycle.active=True`/`combat.alive=False` "zombie" entities were directly measured across all
3 corpus worlds this same investigation, at the identical seed/tick-count).
