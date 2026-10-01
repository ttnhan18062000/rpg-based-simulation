---
status: historical
layer: architecture
authority: P2
audience: agent
tags: [architecture, documentation, roadmap, lifecycle]
---

> Dated evidence snapshot supporting `docs/plans/systemic_world/roadmap.md` §8. Measured 2026-10-01 for
> PR #276. Where the roadmap has since corrected a claim, the roadmap is authoritative. Point-in-time
> evidence: not rewritten retroactively.

# PR #276 mortality measurement — base vs head, 3 corpus worlds

**Why this exists.** PR #276 (death/lifecycle batch + hero `REBIRTH` retirement) prompted two competing
readings of its behavioural effect. `rpg-feature-planning` reported that the PR "made death total and
irreversible"; `world-rule-catalog-design` corrected that to "it made already-total death **recorded**,
and the consequence layer is what moves", and predicted deactivation counts would be roughly unchanged.
This measurement was run to settle it, at the rule owner's request, before a roadmap claim was written.
**Both readings turned out to be partly wrong.**

## Conditions

- **Base:** `origin/main` @ `fe6a2f564`
- **Head:** `origin/entity-death-cause-at-writer` @ `76f21b8a6` (PR #276)
- Two detached worktrees, 300 ticks, seed 42, `PROD_SMALL`, `flags={"no_frame_pacing": True}`, real
  `Kernel.tick_once()` loop, no world edits.
- Measured by `rpg-feature-planning`. Single run per arm per world — **flakiness was not re-tested**, and
  the kernel logs tick-budget overruns in these worlds, so treat magnitudes as order-of-magnitude and
  the direction as the finding.

## Result

| world | deactivated / `hp_zero` | recorded deaths | heirs assigned | corpses | alive + active |
|---|---|---|---|---|---|
| `frontier_marches` | **21 → 31 (+48%)** | 0 → 31 (`DEFEAT` 24, `HAZARD` 7) | 0 → **13** | 3 → 8 | 42 → 32 |
| `frontier_living_world` | **13 → 18 (+38%)** | 0 → 18 (`DEFEAT` 12, `HAZARD` 6) | 0 → **6** | 0 → 3 | 38 → 33 |
| `lifecycle_full_coverage_world` | **12 → 12 (unchanged)** | 0 → 12 (`DEFEAT` 6, `HAZARD` 6) | 0 → **2** | 3 → 3 | 31 → 31 |

**The mortality increase scales with succession volume, near-linearly: 13 heirs → +10 deaths; 6 heirs →
+5; 2 heirs → 0.** `hp_zero` rose in lockstep with `deactivated`, so this is not a recording artifact or
a one-tick-lag counting difference — genuinely more entities reach 0 HP on head.

## Two facts that settle the other half

1. **`unrecorded_zombies` = 0 on BOTH arms, in all three worlds.** Base had no zombie population at 300
   ticks: its HP-0 entities were all already deactivated, silently and without a `death_reason`. This
   directly confirms the rule owner's central correction — **death was already total; it was merely
   silent** — and refutes the planner's "this PR made death final" framing. (The 8 zombies measured by
   `rpg-implementer` were on the *R1-only intermediate* tree, not on base. Consistent, not contradictory.)
2. **Zero `COMBAT` deaths in all three worlds — no `KILL` outcome fired in 900 tick-world-runs.**
   Consistent with the known-starved tactical-attack path (`registries/mechanisms.yaml`'s
   `tactical_decision`: 0–2 real `resolve_attack()` calls per 1000–2000 ticks). **So removing
   `combat.py:136` had no measurable effect in these runs**, and the architecture review's concern that
   former-`HERO` entities become "lethally killable for the first time" did not materialise — it
   requires `resolve_attack` to actually fire. The planner relayed that as a corpus-wide mortality fact
   without checking it; this is the evidence against that relay.

## Readings (hypotheses, not conclusions)

The mechanism behind the extra deaths is **not established**. Three data points cannot discriminate.

- **H1 — consequence-layer feedback (planner's).** Recording a death fires the `if is_dead:` dispatch —
  succession, heirs, feud inheritance, dying-wish seeding — and that seeded hostility drives more
  opportunity attacks, hence more `DEFEAT` deaths. Fits the heirs-scaling: where the consequence layer
  barely fires (2 heirs) mortality is *exactly* unchanged.
- **H2 — one-tick-later deactivation (rule owner's).** R1 moved deactivation to `resolve_lifecycle`, so a
  zero-HP entity now stays `active` for an extra tick. If anything still acts on, moves near, or is
  targeted by an active zero-HP entity during that tick, it could add opportunity-attack `DEFEAT`s.
- **Weighing them:** H2 would scale with *death count*, and `lifecycle_full_coverage_world` had 12 deaths
  with **zero** increase — which argues against a pure per-death effect and favours H1's scaling with
  *succession dispatch* rather than deaths. Both owner and planner lean H1 on that basis, but it is a
  lean, not a result.
- **The discriminating check is cheap and deliberately out of PR #276's scope:** on the head build,
  disable feud inheritance and dying-wish seeding one at a time and see which removes the excess. Owned
  by `TCK-20261001-EPIC-BODY-RECOVERY-AND-SURVIVABLE-DEFEAT-FOUNDATION` child 3, or a small investigation.

**If H1 holds, that is arguably the systemic world working as intended** — deaths cause revenge, revenge
causes conflict. The risk is that the loop is **unbounded**, not that it exists.

## Consequence for Epic K

The population-collapse risk in `TCK-20261001-EPIC-BODY-RECOVERY-AND-SURVIVABLE-DEFEAT-FOUNDATION` is no
longer hypothetical: `alive + active` fell 24% and 13% at only 300 ticks, and under H1 the loop is
self-reinforcing. **Child 3 must measure on a world where succession actually dispatches** (e.g.
`frontier_marches`); `lifecycle_full_coverage_world` would have shown nothing.

## Raw output

```json
{"corpses": 3, "deactivated": 21, "death_reasons": {}, "end_alive_and_active": 42, "end_population_entities": 63, "entities_holding_heirlooms": 0, "heirs_assigned": 0, "hp_zero": 21, "is_permadeath": 0, "recorded_deaths_total": 0, "seed": 42, "start_population": 62, "ticks": 300, "unrecorded_zombies": 0, "world_id": "frontier_marches"}
{"corpses": 8, "deactivated": 31, "death_reasons": {"DEFEAT": 24, "HAZARD": 7}, "end_alive_and_active": 32, "end_population_entities": 63, "entities_holding_heirlooms": 0, "heirs_assigned": 13, "hp_zero": 31, "is_permadeath": 31, "recorded_deaths_total": 31, "seed": 42, "start_population": 62, "ticks": 300, "unrecorded_zombies": 0, "world_id": "frontier_marches"}
{"corpses": 0, "deactivated": 13, "death_reasons": {}, "end_alive_and_active": 38, "end_population_entities": 51, "entities_holding_heirlooms": 0, "heirs_assigned": 0, "hp_zero": 13, "is_permadeath": 0, "recorded_deaths_total": 0, "seed": 42, "start_population": 49, "ticks": 300, "unrecorded_zombies": 0, "world_id": "frontier_living_world"}
{"corpses": 3, "deactivated": 18, "death_reasons": {"DEFEAT": 12, "HAZARD": 6}, "end_alive_and_active": 33, "end_population_entities": 51, "entities_holding_heirlooms": 0, "heirs_assigned": 6, "hp_zero": 18, "is_permadeath": 18, "recorded_deaths_total": 18, "seed": 42, "start_population": 49, "ticks": 300, "unrecorded_zombies": 0, "world_id": "frontier_living_world"}
{"corpses": 3, "deactivated": 12, "death_reasons": {}, "end_alive_and_active": 31, "end_population_entities": 43, "entities_holding_heirlooms": 0, "heirs_assigned": 0, "hp_zero": 12, "is_permadeath": 0, "recorded_deaths_total": 0, "seed": 42, "start_population": 41, "ticks": 300, "unrecorded_zombies": 0, "world_id": "lifecycle_full_coverage_world"}
{"corpses": 3, "deactivated": 12, "death_reasons": {"DEFEAT": 6, "HAZARD": 6}, "end_alive_and_active": 31, "end_population_entities": 43, "entities_holding_heirlooms": 0, "heirs_assigned": 2, "hp_zero": 12, "is_permadeath": 12, "recorded_deaths_total": 12, "seed": 42, "start_population": 41, "ticks": 300, "unrecorded_zombies": 0, "world_id": "lifecycle_full_coverage_world"}
```

Rows are in run order: base, head, per world.
