---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260919-COMBAT-HOSTILITY-SOURCE-DIVERGENCE-UNIFICATION
phase: open
date: 2026-09-19
tags: [combat, faction, root-cause]
---

# TCK-20260919-COMBAT-HOSTILITY-SOURCE-DIVERGENCE-UNIFICATION

## Title
The mechanic that produces nearly all real combat (`resolve_multi_attack()`, via
`LegalityServiceV2.get_engaged_hostiles_at_pos()`) determines "hostile" from a raw 4-value legacy
enum, never the real per-pair content catalog `is_hostile_compat()` uses — measured to be wrong on
34%-97% of every pair either source flags as hostile; investigate the blast radius before fixing

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION`'s 2026-09-19 addendum found and measured,
directly, that this codebase has two independent, unreconciled implementations of "is this pair
hostile":

- `FactionSemanticsService.is_hostile_compat()` (`src/content_semantics/faction.py:159-206`) —
  reads real per-pair authored data (`faction_relationships.yaml`/`perspectives.yaml`, falling
  back to `alignment_bucket`). Used by `TacticalDecisionSystem.evaluate_entity_intent`'s
  decision-driven `hostiles`-loop (`src/engine/tactical.py:182-226`).
- `LegalityServiceV2.get_engaged_hostiles_at_pos()` (`src/engine/legality.py:517-559`) — compares
  `entity.identity.faction`, the raw 4-value legacy `Faction` enum (`HERO_GUILD`/`MONSTER_HORDE`/
  `TOWN_COUNCIL`/`NEUTRAL`), never touching the catalog at all. Used by `movement.py`'s
  opportunity-attack trigger (`src/engine/movement.py:232-242`, `resolve_multi_attack()`) — the
  mechanic that produces the overwhelming majority of real combat resolution in the corpus worlds
  sampled (181-2177 calls per 1000-2000 ticks, vs. 0-2 for the decision-driven `ATTACK` path).

**Measured directly** (instrumenting both sources side-by-side over real 2000-tick runs,
`WorldCompiler.compile()`, `LocalSequentialExecutor`, seed 42), comparing every real adjacent-pair
check either source evaluates:

| World | Total pair-checks | Both agree hostile | Both agree not-hostile | Legacy says hostile, catalog says NOT (false-positive engagement) | Catalog says hostile, legacy says NOT (blocked real rivalry) |
|---|---|---|---|---|---|
| `crowded_frontier` | 21366 | 982 | 19787 | 506 (34% of legacy-triggered pairs) | 91 |
| `hero_guild_routing` | 20254 | 78 | 17556 | **2620 (97% of legacy-triggered pairs)** | 0 |
| `quest_dense_frontier` | 1022 | 0 | 1022 | 0 | 0 |

**In `hero_guild_routing`, 97% of the "engaged hostile" determinations that actually produce real
combat are not the game's authored hostility model at all** — entities fight because a legacy
4-value enum happens to put them in different buckets (e.g. `hero_guild` vs `merchant_league`,
`hero_guild` vs `town_council`, both real, catalog-neutral pairs), not because the content catalog
says they're enemies. The reverse also happens: `bandit_company`/`goblin_warband`, a real,
specifically authored rivalry, can never engage via this path because both share
`legacy_engine_bucket: "MONSTER_HORDE"`.

## Scope
**Investigation-first, per the source ticket's own explicit scope cap** ("this affects
combat/targeting broadly, not just the faction subsystem — propose for peer review before
building"). `get_engaged_hostiles_at_pos()` is a shared legality primitive with call sites beyond
the opportunity-attack trigger:
- `movement.py:240` — the opportunity-attack trigger itself (`resolve_multi_attack()`), the
  primary subject of the measurement above.
- `movement.py:181` (`engaged_hostiles`, used for the `skip_oa`/escape-tag logic and the
  `combat_escape: "EVASIVE_SUCCESS"` observability tag) — same function, different consumer;
  changing what "hostile" means here changes what counts as a real escape.
- `movement.py:100` (`get_engaged_hostiles_at_pos` at a hypothetical position, used during
  pathing/movement-mode decisions) — changing the hostility test here could change pathing
  behavior around perceived threats, not just combat outcomes.
- Determine whether there are other real callers not yet found — a repo-wide grep for
  `get_engaged_hostiles` and `get_engaged_hostiles_at_pos` before scoping a fix.
- For each call site, determine what actually changes if the hostility test is swapped for
  (or made to consult) `is_hostile_compat()`'s real catalog data — in particular whether it is
  *safe* everywhere (e.g. does any call site rely on the current same-legacy-bucket "friendly"
  assumption in a way a catalog-aware swap would break?).
- Determine the real combat-volume impact: given `hero_guild_routing`'s 97% false-positive rate,
  a correct fix would likely make real opportunity-attack volume in these worlds drop sharply —
  is that a desirable outcome (accurate to the authored hostility model) or does it starve combat
  even further in a corpus that's already progression-starved
  (`TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN`)? This is a design question for the user, not
  resolved by this investigation alone — surface it plainly rather than deciding it here.
- Propose a scoped fix (or fixes, if call sites need different treatment) for peer review. Do not
  build without review, per the source ticket's own explicit instruction.

## Out of Scope
- Building the fix itself in this ticket — investigation and a reviewed proposal only, unless the
  investigation finds the fix is trivially safe and narrow (unlikely given 3+ call sites with
  different consumers) and peer explicitly signs off on folding implementation in.
- `TacticalDecisionSystem`'s own near-zero decision-driven `ATTACK` rate — already root-caused and
  closed (`TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION`); not revisited here.
- `FactionSentimentService`/`pairwise_tension`'s own mechanism — flagged as a related open
  question below, not investigated in this ticket's own scope.
- `EntityIdentityResolver.resolve()`'s identity-resolution correctness — already fixed for a
  different reason (see Related Tickets); not revisited, and confirmed structurally unrelated
  since `get_engaged_hostiles_at_pos()` never calls the resolver at all.

## Acceptance Criteria
- A complete list of every real call site of `get_engaged_hostiles`/`get_engaged_hostiles_at_pos`,
  with what each one's caller does with the result and what would change if the hostility test
  were made catalog-aware.
- A determination of whether a single unified fix is safe across all call sites, or whether
  different call sites need different treatment (e.g. opportunity-attack triggering vs.
  pathing/escape-tag observability).
- A real, measured before/after estimate of combat-volume impact on at least the two worlds
  measured above (`crowded_frontier`, `hero_guild_routing`), not just a qualitative claim.
- The design question (does correcting this help or hurt an already progression-starved corpus)
  surfaced explicitly for the user, not silently decided.
- A scoped fix proposal, reviewed by peer, before any implementation.

## Related Tickets
- `TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION` (source — where this finding was
  discovered and measured; see its 2026-09-19 addendum for the full trace and numbers this
  ticket's own Request Summary is drawn from)
- `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` (closed — sibling finding: the
  decision-driven path that *does* use `is_hostile_compat()` correctly essentially never fires at
  all; this ticket is about the mechanic that fires constantly but reads a different, cruder
  source)
- `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` (the broader causal chain this feeds into —
  combat volume/accuracy here upstream of XP/level-up starvation)
- **Checked and confirmed distinct, not a recurrence, despite similar names/area**:
  `TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE` (closed, 2026-08-09) — fixed
  `EntityIdentityResolver.resolve()`'s Path 1 gate collapsing real `faction_id` to `"neutral"`
  when `role_id` was absent, which fed into `is_hostile_compat()`'s own upstream identity
  resolution for the decision-driven path. This ticket's finding is structurally unrelated:
  `get_engaged_hostiles_at_pos()` never calls `EntityIdentityResolver` or `is_hostile_compat()` at
  all — it reads the raw legacy enum directly. That August fix could not have touched this defect,
  and this defect would not have masked that one's own symptom.
- **Also checked and confirmed distinct**: `TCK-20260809-COMBAT-ATTACK-LEGALITY-ALWAYS-FALSE-INVESTIGATION`
  (closed, 2026-08-09) — root-caused `LegalityServiceV2.verify_attack_legality()`'s
  `FRIENDLY_FIRE_ILLEGAL`/`INSUFFICIENT_READINESS` split for the decision-driven `ATTACK` path's
  own legality gate. A different function (`verify_attack_legality`, not
  `get_engaged_hostiles_at_pos`) answering a different question (is this specific attack legal
  right now, not what counts as "engaged/hostile" for opportunity-attack triggering).

**A better explanation than "not a recurrence," stated on its own**: all three prior
investigations in this area (the two above, plus this ticket's own source ticket's earlier
2026-09-15/17 candidates) examined the *decision* path's hostility handling —
`EntityIdentityResolver` feeding `is_hostile_compat()`, and `verify_attack_legality()`'s own gate.
None of them examined `get_engaged_hostiles_at_pos()`, the *movement* path — the one producing
essentially all of the real combat (181-2177 calls/2000 ticks vs. 0-2). That is not "nobody
noticed" — people looked at this area repeatedly and carefully. It is that attention consistently
followed the half that decides, not the half that acts. That asymmetry, not oversight, is the
better account of why this survived three separate investigations in the same area.

## Related Docs
- `docs/engine/contracts/combat_contract.md` §4 (Opportunity Attacks — `resolve_multi_attack`'s
  own documented scope)

## Related Stored Artifacts
_(none yet — filed as a measured finding with a proposed investigation scope, not yet
investigated further)_

## Related Code Areas
- `src/engine/legality.py` (`LegalityServiceV2.get_engaged_hostiles`,
  `get_engaged_hostiles_at_pos`, lines 512-559 — the defect)
- `src/engine/movement.py` (lines ~100, ~181, ~232-242 — the three known call sites)
- `src/content_semantics/faction.py` (`FactionSemanticsService.is_hostile_compat`,
  `get_legacy_faction_bucket` — the correct, catalog-aware reference implementation)
- `src/core/enums.py` (`Faction` — the raw 4-value legacy enum at the center of the divergence)
- `data/content/social/factions.yaml` (`legacy_engine_bucket` per faction — where the collapsing
  happens for real content factions)

## Assumptions / Open Questions
- **Not this ticket's scope, but worth a sentence for whoever picks it up**: if attention in this
  area has systematically followed the decision path rather than the movement path (see the
  "asymmetry of attention" note under Related Tickets above), other movement-side primitives may
  carry the same never-examined status this one did. Not investigated here — a pattern to watch
  for, not a lead to chase inside this ticket.
- **Flagged, not asserted, per peer review of the source ticket's addendum**: this arc built
  `FactionSentimentService`/`pairwise_tension` specifically so hostility could accumulate from
  real cross-faction interaction. If the dominant real-combat path never reads catalog/sentiment
  data at all (this ticket's own finding), sentiment accumulation may have no effect on who
  actually fights, even though diplomacy/war decisions built on top of it elsewhere might still
  respond correctly to the sentiment value itself. Not checked here — whether anything else reads
  sentiment into engagement decisions is an open question for whoever picks this up, or a
  candidate for its own separate ticket if it turns out to be real and consequential.
- Not yet known whether the fix, once scoped, is small (a single shared helper both callers use)
  or requires per-call-site treatment — left for the Investigate phase to determine with real
  evidence, not assumed here.

## Implementation Notes
_(none yet — not yet investigated)_

## Test Summary
_(none yet)_

## Files Changed
_(none yet)_

## Completion Summary
_(none yet — filed per peer's explicit direction that this is "the highest-value repair in the
queue" and needs its own ticket rather than living only as a citation inside the source
investigation's addendum)_
