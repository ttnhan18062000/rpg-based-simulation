# Bug 01: Diagonal Adjacent HUNT Move Conflict

## Summary

When two entities both in HUNT state are diagonally adjacent and each decides to move toward the other (one moves down, the other moves up), they end up at the same distance from each other — neither closes the gap. The conflict resolver doesn't handle this case properly.

## Steps to Reproduce

1. Entity A at `(5, 5)` hunting Entity B at `(6, 6)` (diagonal adjacent)
2. Entity A proposes move to `(5, 6)` (down toward B)
3. Entity B proposes move to `(6, 5)` (up toward A)
4. After both moves resolve, Manhattan distance is still 2 — no progress made
5. This can repeat indefinitely, creating a deadlock

## Expected Behavior

At least one entity should close the gap. Possible solutions (requires decision):

1. **Tie-breaking by entity ID** — lower ID entity gets priority to move first; second entity recalculates
2. **Engagement detection** — if two entities are hunting each other within range 2, skip movement and initiate combat directly
3. **Asymmetric resolution** — one entity moves diagonally while the other waits

## Affected Code

- `src/engine/conflict_resolver.py` — move conflict resolution
- `src/ai/states.py` — HUNT state handler movement logic
- `src/actions/move.py` — move validation

## Notes

> **Decision required from developer** on which resolution strategy to use.

## Labels

`bug`, `ai`, `conflict-resolution`, `needs-decision`
