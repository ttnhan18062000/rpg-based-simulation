---
status: historical
layer: simulation
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260817-STANDARD-BEHAVIORAL-5K-BASELINE-REFRESH
tags: [simulation-quality, testing, bug]
---

# Plan — TCK-20260817-STANDARD-BEHAVIORAL-5K-BASELINE-REFRESH

## Action
Run `make regression-baseline` to regenerate `tests/regression/baseline_5k.json`, only after
confirming the drift is causally explained by real, intentional, already-reviewed changes (not a
bug the refresh would mask) — per this repo's hard rule against editing an artifact just to make a
gate pass instead of fixing/understanding the underlying substance.

## Why this is not "editing an artifact to force a gate to pass"
The gate here (`test_behavioral_5k_regression`) exists to catch *unintentional* behavioral drift.
The drift found is the intentional, expected, already-documented consequence of two closed tickets
that fixed real goal-arbitration bugs (previously-starved HARVESTING/ADVENTURE_ROUTE goal kinds).
Refreshing the baseline here is the correct response to intentional behavior change, exactly as
the test's own docstring instructs: "If the baseline is intentionally outdated (e.g., after a
deliberate design change), refresh it with `make regression-baseline` and commit the result."

## Out of scope
- Any change to `src/ai/goals/` or the goal-arbitration logic itself — already correctly fixed by
  the two cited tickets; this ticket only refreshes the stale baseline that predates those fixes.
- An exhaustive commit-by-commit audit of every change in the squashed `29d78798` commit — the
  working_log.csv cross-reference is judged sufficient given the exact directional/causal match.
