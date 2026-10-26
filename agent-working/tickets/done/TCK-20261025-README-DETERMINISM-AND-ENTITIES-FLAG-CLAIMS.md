---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261025-README-DETERMINISM-AND-ENTITIES-FLAG-CLAIMS
phase: done
date: 2026-10-25
tags: [documentation, determinism]
---

# TCK-20261025-README-DETERMINISM-AND-ENTITIES-FLAG-CLAIMS

## Title
README overclaims determinism ("xxhash generators", "100% replay fidelity", "every run byte-identical") and its run examples pass an --entities flag that serve rejects and cli ignores

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P3

## Request Summary
Issue #617 (lead-planner, from the career-brief fact check, plus codebase-planner's second finding on 2026-10-16):
1. README.md's Architecture table says all randomness comes from "xxhash generators" with "100% replay fidelity". src/ does not use xxhash; `src/platform/rng.py` (`DeterministicRNG`) seeds a fresh `random.Random` per draw from an XOR-composite seed. `docs/engine/deterministic_execution.md` scopes the guarantee to tier DET-PORT-0 under the Canonical signal contract and lists known gaps.
2. The Quick Start runs `--entities 50`, which `sandbox_world` ignores.

## Scope
- Correct the README intro sentence and the Determinism row to match the code and the contract, linking `docs/engine/deterministic_execution.md`.
- Drop `--entities 50` from both README run examples.

## Out of Scope
- Making `--entities` work, warn, or go away in `src/cli/entry.py` (rpg's call; noted on #617).
- Removing `xxhash` from pyproject.toml. No file in src/ or tools/ imports it on origin/main a3c000aa3, so it looks removable. That's a separate dependency ticket, with the tests and scripts checked.
- Any change to docs/engine/ or the parity ledger. The contract is already right; only the README was wrong.

## Acceptance Criteria
- The README makes no claim about xxhash and no unconditional "100%" or "every run byte-identical" claim. Its determinism text matches `src/platform/rng.py` and points to the contract for scope.
- Every README run command parses with `src/cli/entry.py`'s argparse.

## Related Tickets
- TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY (the Canonical signal contract)

## Related Docs
- docs/engine/deterministic_execution.md ("Scope of the guarantee", "Rule 1: Stateless random numbers")
- docs/guides/reviewer_replay_check.md

## Related Stored Artifacts
- none

## Related Code Areas
- README.md; src/platform/rng.py; src/cli/entry.py

## Assumptions / Open Questions
- #617 also asks whether `--entities` should work. That stays open on the issue for rpg.

## Implementation Notes
Verified on origin/main a3c000aa3:
- `DeterministicRNG.get_float/get_int/choice/weighted_choice/sample` each build `random.Random(_composite_seed(...))` per draw (src/platform/rng.py). `git grep xxhash -- src tools` is empty.
- `serve` defines no `--entities` argument (src/cli/entry.py, serve parser), so `python3 -m src serve --seed 42 --entities 50 --workers 4` exits with an argparse error. `cli` defines `--entities`, but nothing reads `args.entities`. Removing the flag from both examples makes them true. This finding goes beyond #617's own wording, which said only that the flag is ignored.
- The intro sentence "Every run is byte-identical replay-faithful" is replaced with the DET-PORT-0 / Canonical statement and the contract link. The default LIVE contract does not reproduce a final hash across two same-seed runs; Canonical does (#617, second comment).

## Test Summary
README only. Ran `tests/docs/` (scoped) and a check that both README run commands parse.

## Files Changed
README.md

## Completion Summary
README's determinism claims and run examples now match the code and docs/engine/deterministic_execution.md. Closes #617's README asks; the `--entities` behaviour question stays with rpg.
