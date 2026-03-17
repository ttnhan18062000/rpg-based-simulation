# Bug 02: Hero Keeps Looting When Bag Is Full

## Summary

Heroes continue to pursue loot goals even when their inventory is full. They walk to loot, attempt to pick it up, fail (bag full), and repeat — wasting ticks instead of moving on to sell/store items or pursue other goals.

## Steps to Reproduce

1. Hero inventory reaches max capacity
2. Ground loot exists nearby
3. Hero evaluates LOOT goal — still scores high despite full bag
4. Hero walks to loot, can't pick up → stuck in loop

## Expected Behavior

When bag is full, the hero should:

1. **Abandon loot goal** — LOOT goal scorer returns 0 (or near-zero) when inventory is full
2. **Prioritize selling** — VISIT_SHOP goal scorer gets a bonus when inventory is full
3. **Drop low-value items** — if new loot is significantly better, drop worst item to make room (optional, advanced)

## Affected Code

- `src/ai/goals/scorers.py` — `LootScorer` should check inventory capacity
- `src/ai/states.py` — LOOT state handler should abort if bag is full
- `src/core/models.py` — `Entity` needs exposed `is_bag_full` or inventory capacity check

## Notes

> **Decision required from developer:** Should heroes just skip loot, or should they also prioritize going to town to sell? Should dropping low-value items be supported?

## Labels

`bug`, `ai`, `goal-evaluation`, `needs-decision`
