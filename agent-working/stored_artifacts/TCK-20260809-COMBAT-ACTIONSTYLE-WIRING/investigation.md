---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260809-COMBAT-ACTIONSTYLE-WIRING
artifact_type: investigation
tags: [combat, simulation-quality]
---

# Investigation — TCK-20260809-COMBAT-ACTIONSTYLE-WIRING

## Context
Direct follow-up to `TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION` (same session, same
`compiler.py` personality-seeding call site) and to `TCK-20260809-COMBAT-OUTCOME-FLEE-VS-FIGHT-
PERSONALITY`'s own Finding 3, which confirmed `ActionStyle` (`BALANCED`/`AGGRESSIVE`/`EVASIVE`,
`src/core/enums.py`) has real, already-wired code hooks but is never assigned anything but the
class default anywhere in real entity generation.

## Real `ActionStyle` consumers traced (`src/engine/tactical.py`, `src/engine/movement.py`)
1. **Kiting distance, `SKIRMISHER`-role entities** (`tactical.py:549-594`): `kite_dist = 2 if
   AGGRESSIVE else 6 if EVASIVE else 4` — real, consumed, changes real movement targets.
2. **Opportunity-attack suppression on deliberate retreat** (`movement.py:185-186`): `skip_oa =
   True` only when `MovementMode.RETREAT and action_style == EVASIVE` — real, consumed, changes
   whether a real `resolve_multi_attack()` call happens.
3. **Effective attack-range bonus for `AGGRESSIVE`** (`tactical.py:598-600`) and **`EVASIVE`
   "reposition instead of attacking" stub** (`tactical.py:601-603`, a bare `pass`) — traced in
   full: `is_attack_legal` (the value these would need to influence) is computed at
   `tactical.py:401`, **before** this block runs, and the local `attack_range` variable this block
   mutates is never read again by anything after it (confirmed via direct read of lines 605-670).
   **Both are dead code**, independent of whether `action_style` is ever set — disclosed, not
   fixed here (a real but separate bug in `tactical.py`'s own control flow, out of this ticket's
   scope, which is specifically about *wiring* `ActionStyle`, not auditing every one of its own
   downstream consumers for correctness).

## Real fix: derive `ActionStyle` from the entity's own final bravery value
Wired into the same `compiler.py` call site `TCK-20260809-COMBAT-PERSONALITY-RACE-CORRELATION`
already touched, immediately after `bravery`'s own bias-applied value is computed:
`action_style = get_action_style_for_bravery(personality.bravery)`, using the same
data-driven `personality_bias.yaml` file that ticket already introduced (extended with
`action_style_thresholds`, per the user's own mid-session correction that this whole mechanism
should be data-driven, not hardcoded per-race in Python — see that ticket's own investigation.md
for the full data-vs-code design history).

## Real, direct verification (live compiled worlds, not assumed)
`dungeon_crawl`'s real `wild_beast_pack` population (avg bravery ≈0.89, the highest-biased real
faction): 5/5 entities now `AGGRESSIVE`. `urban_political`'s `merchant_league` (no bias, raw RNG):
a real, roughly even 3/3/3 split across `BALANCED`/`AGGRESSIVE`/`EVASIVE`. This is the real
mechanism that activates the previously-dormant kiting and OA-escape hooks above — a
`SKIRMISHER`-role predator will now genuinely kite less (`AGGRESSIVE`, distance 2) than a
`SKIRMISHER`-role citizen might (potentially `EVASIVE`, distance 6), and an `EVASIVE`-styled
entity choosing a deliberate retreat now genuinely skips the opportunity attack it would otherwise
trigger — real, race/personality-correlated diversity in combat outcomes.

## Docs Requiring Update
- `docs/mechanics/04_strategic_cognition.md`: extended the same cross-reference section this
  session's sibling tickets already built, documenting the real `ActionStyle` wiring and the 2
  confirmed-dead sub-branches.
