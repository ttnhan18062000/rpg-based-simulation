---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261019-RECORD-BASELINE-V1
artifact_type: plan
tags: []
---

# Plan — TCK-20261019-RECORD-BASELINE-V1

**v1 sha superseded: gate red, see handover.** The v1 gate run on 864f7b281 had 4 hard-check fails (V2, V3, V4, V1 saw nothing); the designer ruled they are fixed before v1, which changes simulation behaviour, so 864f7b281 is not the v1 sha. The paired 10-seed run on it was stopped (partial cache kept at /mnt/data/scratch-rpg-implementer-2/v1/cache); nothing below is recorded until the new v1 sha exists.

Commit: origin/main 864f7b281 (v1 sha; the gate dispatch run 39212800104 ran on it). Branch rpg-baseline-v1. Full command plan: see `/mnt/data/scratch-rpg-implementer-2/v1_plan.md` (timings measured on df3cb7256).

1. Paired 10-seed base: `python -m tools.rpg_measure.paired --base 864f7b281 --new 864f7b281 --report-only --seeds 42..51 --self-check full --jobs 1 --cache /mnt/data/scratch-rpg-implementer-2/v1/cache` (60 runs, sequential). Digest table per world x seed goes to stored_artifacts at close (not the raw JSONs).
2. behavioral_5k: set audit_mode (and pin the governor as PinnedNormalGovernor does if needed) in the test Kernel; regenerate baseline_5k.json; two repeats must agree; record old -> new values in the ticket.
3. Gate V1-V8 candidate: handled by rpg-planner from CI run 39212800104; rebaseline by rpg-planner.
4. evaluate-full: skipped by decision (testing runs its own producer).
