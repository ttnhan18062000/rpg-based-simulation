---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261027-RPG-MEASURE-CACHE-DEFAULT-HOST-NEUTRAL
phase: open
date: 2026-10-27
tags: [benchmarking]
---

# TCK-20261027-RPG-MEASURE-CACHE-DEFAULT-HOST-NEUTRAL

## Title
The paired run's default cache path is host-neutral, resolved when called, and fails early when unwritable

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
rpg-planner (u24) wrote this spec and filed it on its own seat at 7503b3426. It was never pushed,
and rpg-planner then dropped that copy (seat a5163fcda). rpg-planner-ubuntu re-files it here under
the same ID, using rpg-planner's full text as relayed by lead-planner on 2026-10-27; u24 confirmed
the relay is complete, and the original ticket file is being posted on #593. rpg owns
tools/rpg_measure (TCK-20261022-SESSION-ROLES-RPG-OWNS-RPG-MEASURE).

On origin/main 3b5fab1e9, `tools/rpg_measure/paired.py:48` sets
`DEFAULT_CACHE = Path(os.environ.get("RPG_MEASURE_CACHE", "/mnt/data/scratch-rpg-measure"))` at
import time. Line 295 uses it as the `--cache` default. `/mnt/data` exists only on u24, so on ubuntu
a run without the variable writes to a path that doesn't exist. Ubuntu runs have worked around this
by setting RPG_MEASURE_CACHE by hand.

## Scope
- In `tools/rpg_measure/paired.py`, the cache path is `$RPG_MEASURE_CACHE` if set, else
  `$XDG_CACHE_HOME/rpg-measure`, else `~/.cache/rpg-measure`. Resolve it when called, not at import.
- An unwritable cache fails before any arm runs, with one message that names RPG_MEASURE_CACHE and
  the path tried.
- The module docstring says u24 keeps its cached arms by setting
  `RPG_MEASURE_CACHE=/mnt/data/scratch-rpg-measure`. Say the same in
  `docs/observability/how_to_run_simulation.md` if that doc covers paired runs; on 3b5fab1e9 it
  does not mention paired runs or rpg_measure at all, so no docs change is expected.

## Out of Scope
- `paired_arms.py`: it takes `--cache`, so T2 is unaffected.
- Cache keys, arm layout, report format, and a scheme-aware paired mode.

## Acceptance Criteria
1. No host-specific absolute path is left in `tools/rpg_measure/`.
2. With the variable unset and no `--cache`, paired uses the XDG or home path.
3. An unwritable cache gives a one-line error naming the variable and the path, exits non-zero, and
   starts no child process.
4. Cache keys are unchanged. Once the PR is up, rpg-planner verifies on u24, with the variable set to
   `/mnt/data/scratch-rpg-measure`, that a run hits an arm cached before the change.
5. Unit tests cover the three cases: variable set, XDG/home fallback, and unwritable path. Put them
   beside `tests/unit/tools/test_rpg_measure.py`.

## Related Tickets
- TCK-20261022-SESSION-ROLES-RPG-OWNS-RPG-MEASURE (ownership)
- TCK-20261027-CRAFT-UNKNOWN-RECIPE-RAISES-KEYERROR (#762): its proof had to set RPG_MEASURE_CACHE
  by hand on ubuntu.

## Related Docs
- docs/observability/how_to_run_simulation.md

## Related Stored Artifacts

## Related Code Areas
- tools/rpg_measure/paired.py (line 48 `DEFAULT_CACHE`, line 295 `--cache`)
- tests/unit/tools/test_rpg_measure.py

## Assumptions / Open Questions
- Host note for ubuntu: `~/.cache` resolves to /data/vboxuser/.cache, on the same disk as /data
  (/dev/sdb1). The new default does not take load off /data here, so ubuntu proof runs keep setting
  RPG_MEASURE_CACHE explicitly.
- Timing: don't merge while a u24 paired run is live. rpg-planner announces on #593 when its step A
  R-only run ends.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
