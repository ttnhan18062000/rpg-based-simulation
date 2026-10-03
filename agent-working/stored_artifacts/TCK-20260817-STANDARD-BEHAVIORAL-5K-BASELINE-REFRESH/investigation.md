---
status: historical
layer: simulation
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260817-STANDARD-BEHAVIORAL-5K-BASELINE-REFRESH
tags: [simulation-quality, testing, bug]
---

# Investigation — TCK-20260817-STANDARD-BEHAVIORAL-5K-BASELINE-REFRESH

## Failing test
`tests/regression/test_behavioral_5k.py::test_behavioral_5k_regression` — one of the 439 tests
never run by any CI job (in one of the 16 orphaned test directories added by commit `29d78798`).
A plain local run also spuriously fails with a `TimeoutError` under the default 60s resource
budget — this test is `@pytest.mark.extra_slow` (documented as needing ~100-170s) and was never
run with `--resource-budget large` locally before now, since it was never run at all.

## Real drift confirmed
Under `--resource-budget large` (matching CI's dedicated `slow` job), the test completes in
~105-115s and fails for real:
```
alive_avg: actual=13.3000 baseline=11.3400 drift=17.3% > allowed=10%
gold_avg: actual=584.1600 baseline=457.3200 drift=27.7% > allowed=20%
```
Both numbers are exactly deterministic (seed=42) and reproduced identically across 2 separate
runs.

## Root cause
The committed baseline (`tests/regression/baseline_5k.json`) was generated 2026-06-28. The only
`src/` changes since then (per `git log --oneline --since=2026-06-28 -- src/`, which shows this
repo's history is consolidated into a small number of large squashed commits) are `00c603c3`
(docs-only, confirmed irrelevant) and `29d78798` ("Simulation quality #20", 2026-08-14). Cross-
referencing `29d78798`'s working_log.csv entries for goal-arbitration/scoring changes surfaces two
directly relevant, real, documented, already-reviewed tickets:

- `TCK-20260813-HERO-GUILD-SEED456-ECON-PROG-DRIFT`: fixed HARVESTING being starved by
  COMBAT_ENGAGE/REGION_STABILIZATION in tier-5 goal competition (root-caused via DEBUG-trace to a
  1/371 win rate before the fix).
- `TCK-20260813-ADVENTURE-ROUTE-UTILITY-SCALE-NEVER-WINS-TIER5`: fixed ADVENTURE_ROUTE being
  "structurally dead" in goal scoring (a miscalibrated denominator).

Both directly explain higher survival (`alive_avg`) and economic activity (`gold_avg`): entities
that previously lost the tier-5 goal-arbitration to combat/stabilization now actually harvest and
route to adventures, engaging in more economic activity and presumably surviving better via
improved resource access. The direction (both metrics increasing) and rough magnitude are
consistent with "previously-starved goal kinds now winning some competitions," not a
regression.

## Verification performed
- Confirmed the exact drift numbers via direct reproduction (2 runs, byte-identical results —
  fully deterministic under seed=42).
- Confirmed the causal tickets are real, closed, and describe exactly the class of change that
  explains this direction of drift (not merely plausible-sounding — read their own working_log.csv
  entries and root-cause descriptions directly).
- This is not an exhaustive per-commit audit of every change in the large squashed `29d78798`
  commit — the working_log.csv cross-reference for goal-scoring/arbitration-tagged tickets is the
  verification method, consistent with how this class of drift was already investigated and
  resolved for SimQ grade-anchor calibration in the same commit (see the two cited tickets' own
  stored_artifacts).
