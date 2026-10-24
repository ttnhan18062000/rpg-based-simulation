---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261010-PERF-M2-T06-GATE-CONFORMANCE
date: 2026-10-24
tags: [performance, documentation, certification]
---

# Draft: `docs/engine/performance_contract.md` section 5 edit (waits for rpg's lift)

**Not applied.** `docs/engine/performance_contract.md` is rpg-owned P1; the edit is the PR's last commit and is made only after rpg-planner grants the lift (#593 perf issuecomment-6386482656). The text and numbers are the owner's decision (#715 issuecomment-6386636889, option A); nothing is invented here. Evidence write-up: #593 issuecomment-6386482656.

## Edit 1: section 5, first bullet, the sentence beginning "The threshold (provisional, owner-approved 2026-10-10)" through "...detect only changes above about 40%."

**Old** (verbatim, from `performance_contract.md` line 80):

> **The threshold (provisional, owner-approved 2026-10-10):** the tripwire (`tools/perf/tripwire.py`, `TRIPWIRE_THRESHOLDS`) reports `REGRESSION` when the head's average tick latency over 50 sampled ticks exceeds `max(5.0 ms, base x 1.40)`, base and head measured paired on one runner, each in a fresh process. The relative term sits above the noise budget, 0.35, the largest head/base deviation seen with identical code on both sides (44 A/A pairs, 6-vCPU VM, 2026-10-10); the margin is small, which is a further reason to recalibrate. A first non-PASS result is run once more, head first; a disagreeing retry is `INCONCLUSIVE`; the outcome is reported and never blocks. The values are **provisional**: they must be recalibrated with `python3 tools/perf/tripwire.py calibrate` on the CI runner once the CI step lands, and on this host they detect only changes above about 40%.

**New:**

> **The threshold (final, report-only; owner decision 2026-10-24, option A):** the tripwire (`tools/perf/tripwire.py`, `TRIPWIRE_THRESHOLDS`) reports `REGRESSION` when the head's average tick latency over 50 sampled ticks exceeds `max(5.0 ms, base x 1.40)`, base and head measured paired on one runner, each in a fresh process. The relative term sits above the measured noise: the largest head/base deviation with identical code on both sides was 0.35 on the 6-vCPU development VM (44 A/A pairs, 2026-10-10), and on the CI runner 0.206 (idle_100_local) and 0.095 (movement_100_local) in run 40106785877 (main `10422cedd`) and 0.005 and 0.010 in run 40109334529 (main `667552eb9`), 8 trials per scenario in each. A first non-PASS result is run once more, head first; a disagreeing retry is `INCONCLUSIVE`; the outcome is reported and never blocks. **Limit of the evidence:** the CI measurements cover two runner VMs, and the tripwire detects only changes above about 40%; a smaller change is not detected by it.

## Edit 2 (only if the owner's text calls for it): section 3.3, the Tripwire bullet

No numeric change. The bullet already states the claim scope (no capacity claim) and that the tripwire reports and does not block; the ticket's AC "no sentence still says 'The threshold is not yet set'" is already met by the current text (a grep finds no such sentence). Left as is unless rpg-planner asks.

## Points for perf-planner (not edits)

- Section 3.3, Tripwire bullet, last sentence: "The nightly lane is `INCONCLUSIVE` until baseline records are promoted (`PERF-M2-T08`)." T08 is DONE and the records are promoted (`tests/perf/baselines/*.v0001.json`), so this sentence reads stale. Fixing it is outside the owner-fixed text; raised for a decision.
- Section 5 first-bullet last sentence lists retired tolerances including "the retired `tools/perf/check_perf_regression.py`"; the file is gone, which agrees with the sentence, so no edit.
