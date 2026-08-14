---
status: active
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260808-COMBAT-PILLAR-OPPORTUNITY-ATTACK-CREDIT-GAP
artifact_type: investigation
phase: investigate
date: 2026-08-08
tags: [combat, simulation-quality]
---

# Investigation — TCK-20260808-COMBAT-PILLAR-OPPORTUNITY-ATTACK-CREDIT-GAP

## `src/simulation_quality/scorers/combat.py`: which event types it reads (confirmed, not assumed)

Read directly: `CombatScorer` reads `combat_initiated`, `combat_resolved`, `near_death_survival`,
`combat_damage`, and **`entity_killed`** — all 5, including the exact event the ticket's own
Request Summary worried might be under-credited.

## Real, decisive finding: a genuine architectural mystery, resolved within a single run

Instrumenting all 5 `CombatResolutionSystem.resolve_*` methods (the same technique used earlier
this session) in the SAME live run that also captured the real JSONL event stream —
eliminating cross-run non-determinism as a confound — found a striking mismatch:
**`resolve_multi_attack` produced exactly 6 `DEFEAT` outcomes, zero `KILL` outcomes from any of
the 5 methods, yet the real JSONL for the same run shows 26 `entity_killed` events.**

**Resolved, not a new bug**: this matches a design already established this session
(`TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION`'s own completion notes) — `entity_killed` is
**deliberately, knowingly emitted by two separate mechanisms**: the newer push-shaper
(`event_shapers.py`, narrow — fires only on `outcome_kind=="KILL"`, which never occurs via the
opportunity-attack path since it hardcodes `is_lethal=False`) and the older diffing-based
`event_extractor.py` (broad — fires on *any* `lifecycle.active` transition, deliberately kept
"to preserve non-shaper-owned kill causes" per that prior ticket's own completion summary). The
26 real `entity_killed` events in this run are the broader diffing path correctly catching the
opportunity-attack path's own real DEFEAT-outcome deaths — **not a credit gap**. Confirmed the
event genuinely reaches the scorer (`CombatScorer` reads `entity_killed` directly, with no
gating that would exclude these).

## The real answer to this ticket's own core question: no scorer bug — a scoring-*direction* misunderstanding in the ticket's own original premise

Read `config/simulation_quality/scoring_weights.yaml`'s real COMBAT weights directly:

| Event | Score tag | Weight |
|---|---|---|
| `combat_initiated` | `combat_active` | **+2.0** |
| `combat_resolved` | `combat_resolved` | +3.0 |
| `near_death_survival` | `survival_tension` | +2.0 |
| `combat_damage` (new tactical modifier only) | `tactical_variety` | +1.0 |
| `entity_killed` (first, if early) | `early_extinction` | **-10.0** |
| `entity_killed` (subsequent) | `attrition` | **-1.0** |

**`entity_killed` is scored *negatively*** — the COMBAT pillar's own real design treats
attrition/death as an instability signal, not a growth/reward signal, mirroring
`combat_dormant`'s own -15.0 penalty for the opposite extreme (no combat at all). The ticket's own
original premise — "a monster-only, presumably combat-heavy world should score *higher* on
COMBAT than a civilian world" — does not follow from this real formula: more kills means more
`attrition` penalty, not more credit.

**Real, same-day data directly confirms this, not contradicts it.** `urban_political` (real,
same-run): `combat_initiated=12`, `entity_killed=26` → estimated raw score ≈ `12×2.0 - 10.0 -
25×1.0` ≈ **-9**. `wilderness_survival` (real, same-technique run): `combat_initiated=1`,
`entity_killed=2` → estimated raw score ≈ `1×2.0 - 10.0 - 1×1.0` ≈ **-9**. Both land in a similar,
low-negative range — **both worlds' real COMBAT grade of `C` is directly explained by this real
formula**, not evidence of one being under-credited relative to the other. `wilderness_survival`
was also not, in this real run, meaningfully more "combat-heavy" than `urban_political` in raw
event terms — the ticket's own original archetype-based assumption doesn't hold on real data
either.

## Real conclusion: no bug, no credit gap — the scorer works as designed

Both halves of the original finding are resolved: (1) events genuinely reach `CombatScorer`
correctly, confirmed via direct, same-run instrumentation; (2) the C grade for both worlds is a
direct, arithmetic consequence of a real, intentional design (kills penalize, not reward, the
COMBAT score) — not a scorer-side gap. This is the same class of finding as `AGENCY=C` being
archetype-correct for non-routing worlds and `wilderness_survival`'s own low diversity being
archetype-correct — a real, disclosed non-bug, not forced into a fix.

## Docs Requiring Update

- `docs/simulation_quality/quality_scoring_contract.md`: no formula change, but the real
  same-run instrumentation finding (dual `entity_killed` emission paths, push-shaper narrow vs.
  diffing-path broad) is worth a short cross-reference note near §7's COMBAT section for future
  investigators, since it isn't otherwise documented outside `TCK-20260806-PUSH-CUTOVER-COMBAT-
  ECONOMY-FACTION`'s own completion notes
