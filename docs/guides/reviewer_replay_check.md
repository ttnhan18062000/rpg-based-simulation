---
status: active
layer: testing
authority: P1
audience: agent
tags: [determinism, testing]
---

# Reviewer replay check

One command that shows the determinism claim working: the same seed, run twice, gives the same final state hash.

```bash
make replay-check
```

It runs `python3 -m src cli --seed 42 --ticks 300` twice from the repository root with `RPG_SIGNAL_CONTRACT=canonical`, reads each `Final State Hash:` line and compares them. It takes about a minute (each run is 12-20 s) and removes the `data/runs/` directories its own runs created, and no others. Options: `--seed N`, `--ticks N`, `--timeout SECONDS` (per run), `--live`.

## Expected output

```text
canonical contract (RPG_SIGNAL_CONTRACT=canonical) (seed=42, ticks=300)
  run 1: 43e5263e113907ec0119c9b7124c24ac0c16524fce80cec9559153b03e0e10b3
  run 2: 43e5263e113907ec0119c9b7124c24ac0c16524fce80cec9559153b03e0e10b3
MATCH
```

The hash shown is an example from origin/main `927700be4` and will change as the code changes. What matters is that the two runs print the same value.

| Exit code | Meaning |
|---|---|
| 0 | The two hashes match. |
| 1 | The hashes differ. |
| 2 | A run crashed, timed out, or printed no `Final State Hash:` line. |

`--live` also runs the pair on the default LIVE contract, as a contrast. It is informational: the line is labelled "expected to differ today (known gap, #585)" and its result never changes the exit code. At 100 ticks it printed two different hashes (`ca4c2d1b...`, `17546857...`).

## What it proves

The same seed under the Canonical signal contract gives the same final state hash (the proof digest, `CanonicalStateHasher.get_hash()`), on this machine, for the seed and tick count you ran.

## What it does not prove

- **Default LIVE runs do not reproduce yet.** Without `RPG_SIGNAL_CONTRACT=canonical` two runs of the same seed differ, because a wall-clock input still changes what is computed (#585, PERF-D1 A2). This check does not hide that: it sets the contract on purpose.
- **Canonical here is not the full PERF-M1 Canonical contract.** It is the modelled-cost signal contract (`TCK-20261006-PERF-GOVERNOR-WALL-CLOCK-INPUTS-DETERMINISTIC-PROXY`), which replaces the governor's measured tick cost with a modelled one. Other items on the PERF-M1 list are not built.
- **It is a short-run measurement, not a proof.** Two runs of one seed for a few hundred ticks, on one host, sequential execution. It makes no claim about other seeds, longer runs, other executors or other hardware (the DET-PORT tiers).

The contract and its open items are in [`docs/engine/deterministic_execution.md`](../engine/deterministic_execution.md), section "What runs today".

## Code

`codebase/reports/replay_check.py`; tests in `tests/codebase/test_replay_check.py` (a fake CLI, no real simulation).
