---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP
phase: open
date: 2026-07-13
tags: [simulation-quality, cognition, stasis]
---

# TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP

## Title
No entity, anywhere in the corpus, ever generates a harvest/craft/trade intent — ECONOMY's
`resource_harvested`/`item_crafted`/`trade_executed`/`shop_transaction` events have never fired

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Discovered during `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH`'s Step 4 calibration. That ticket
authored a `trading_company_hub` module (merchant NPCs, crafting-capable population) into 3
candidate worlds (`frontier_living_world`, `frontier_extended`, `swamp_border_world`), verified
clean compilation with correct entity/faction counts, and recalibrated all 9 anchors (3 worlds × 3
seeds) at both the default `merchant_count: 3` and an escalated `merchant_count: 6`, including a
diagnostic 1000t run — ECONOMY graded **C with 0 events** in every single case.

A corpus-wide grep of every `data/calibration/*/quality_scores.jsonl` file (all ~18 worlds, all
committed anchor runs) found that **`resource_harvested`, `item_crafted`, `trade_executed`, and
`shop_transaction` have never fired for any entity, in any world, at any point in this corpus's
history** — including `urban_political`'s own reference runs, which `TCK-20260713-SIMQ-SCORE-CEILING-FIX`
had cited as "genuinely rich activity" (69 events) and used to derive ECONOMY's weight multiplier.
Direct inspection of that 69-event run showed it is **100% `gold_sink_fired`** — the generic,
Gini-threshold-driven baseline event that fires regardless of authored content — not real
harvest/craft/trade activity as previously assumed.

This means ECONOMY's C-heavy grade distribution was never a content-authoring gap (worlds lacking
merchant NPCs) — it is a **strategy/cognition-layer gap**: no entity's goal-generation pipeline
ever produces an accepted harvest, craft, or trade intent, regardless of whether the world has a
merchant population available to interact with. Authoring more content into any world cannot move
this pillar until this gap is closed.

## Scope
- Investigate the strategy/cognition goal-generation pipeline (wherever entity intents/goals are
  formed — likely `src/domains/strategy/` or `src/strategy/`, not yet pinned down) to find why no
  entity, including ones in worlds with an available merchant/crafting population
  (`trading_company_hub`, `urban_political`'s own economy module), ever forms or executes a
  harvest/craft/trade goal.
- Determine whether this is: (a) a missing goal-type registration (harvest/craft/trade goals never
  added to any entity's goal hierarchy), (b) a gating condition that's never satisfied, (c) a
  scoring/utility function that always ranks these goals below threshold, or (d) an execution-path
  bug where the goal is selected but never actually fires the corresponding event.
- Fix the root cause so a real, in-fiction economic transaction (harvest, craft, or trade) can
  occur and produce a `resource_harvested`/`item_crafted`/`trade_executed`/`shop_transaction` event
  under realistic conditions.

## Out of Scope
- `src/simulation_quality/scorers/economy.py` — confirmed correct, purely event-driven, listens for
  the right event types; not touched by this ticket.
- `src/economy/health_monitor.py`'s `INFLATION_SPIRAL_GINI_THRESHOLD` — unrelated mechanism,
  confirmed not to be the cause (the Gini/gold-sink baseline fires independently of this gap).
- Any further world-content authoring — `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH` already confirmed
  3 worlds have adequate merchant/crafting population; the gap is not content, it's goal-generation.
- Re-scoring or re-anchoring ECONOMY once the fix lands — that would be new follow-on work once
  real economic activity becomes observable, not decided here.

## Acceptance Criteria
- [ ] Root cause of the missing harvest/craft/trade goal-generation identified with file:line
      evidence.
- [ ] At least one real calibration run (using `trading_company_hub`-composed worlds already
      authored by `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH`, or `urban_political`) produces a real
      `resource_harvested`, `item_crafted`, `trade_executed`, or `shop_transaction` event under
      realistic play, not the generic `gold_sink_fired` baseline.
- [ ] No regression in existing goal-generation/strategic-cognition test suites.

## Related Tickets
- `TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH` (done) — where this gap was discovered; that ticket's
  content authoring (3 worlds, `trading_company_hub` composed) remains in the corpus, ready to be
  exercised once this gap closes.
- `TCK-20260713-SIMQ-SCORE-CEILING-FIX` (done) — its ECONOMY weight-derivation cited
  `urban_political`'s 69-event run as "genuinely rich activity"; that characterization is now known
  to be inaccurate (it's 100% `gold_sink_fired`, not harvest/craft/trade) — the weight *mechanism*
  itself is unaffected (still correctly derived from real observed data), only the narrative
  framing of what that data represented was wrong.

## Related Docs
- `docs/simulation_quality/current_state.md` — ECONOMY per-pillar read, will need a further update
  once this gap's real scope is understood.
- `docs/mechanics/04_strategic_cognition.md` — goal hierarchy and interruption resistance, the
  likely authoritative chapter for wherever this gap lives.
- `docs/mechanics/03_economic_laws.md` §5 (Industry: Crafting & Conversion) — the economic
  mechanics these missing goals should ultimately resolve through.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260713-SIMQ-ECONOMY-CONTENT-DEPTH/` — the investigation/plan/test_plan
  documenting the corpus-wide event-log grep that found this gap.

## Related Code Areas
- Strategy/cognition goal-generation pipeline (exact file:line not yet pinned down — first
  investigation task; likely under `src/domains/strategy/` or `src/strategy/`).
- `src/simulation_quality/scorers/economy.py` (confirmed correct, not the cause — reference only).
- `data/worlds/urban_political/`, `data/worlds/frontier_living_world/`,
  `data/worlds/frontier_extended/`, `data/worlds/swamp_border_world/` (worlds with merchant
  populations already available for real-world verification once the fix lands).

## Assumptions / Open Questions
- Whether the gap is a missing goal-type registration, an always-failing gate condition, a
  utility-scoring issue, or an execution-path bug is not yet known — first investigation task.
- Whether this affects only ECONOMY-family goals or is a broader symptom of a wider
  goal-generation issue is not yet known.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
