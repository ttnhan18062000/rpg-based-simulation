---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261009-RPG-REGRESSION-METRICS-COMPUTED-FROM-TYPED-RECORDS
phase: investigate
date: 2026-10-09
tags: []
---

# TCK-20261009-RPG-REGRESSION-METRICS-COMPUTED-FROM-TYPED-RECORDS

## Title
RPG regression metrics: validity checks V1-V7 and outcome figures O1-O7, computed only from typed run records, each citing its rule.

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The owner asked for durable regression control on rpg behaviour (2026-10-09). Today each batch's measurement is an ad hoc probe that nothing re-runs. The metric set v1 is agreed with rpg-designer (outcome neutrality plus D33: VALIDITY checks can fail; OUTCOME figures are drift-watched, never graded alone) and with testing-planner (the split: rpg owns definitions, oracles, thresholds, baseline content and computation; testing owns the harness, workflow, baseline format, states and ownership registry). This ticket is the rpg half: the computation.

## Scope
- A pure, read-only module that takes one run's typed records (events, transfers, the H6 starvation-death record, FEEDING_KILL, CORPSE_FOOD, MEAT_DECAYED, positions, deaths by cause, kind groups) and returns V1-V7 (pass/fail plus counterexamples) and O1-O7 (per-seed values).
- Each metric declares its class, its oracle citation (a Bible chapter, rule id or memo row) and, for outcome metrics, its practical floor with a fiction reason (never fitted).
- MODULE HOME (agreed with testing-implementer 2026-10-11): src/observability/rpg_gate_metrics.py exposing compute(run_artifacts) -> one doc and pool(docs_for_one_world) -> [metric]; the harness (RPG-GATE-PINNED-FRESH-PROCESS-HARNESS) builds against a stub with that signature and reads worlds/seeds/ticks from tests/simulation_quality/rpg_gate/config.yaml.
- HARNESS CONSTRAINT (testing #503): the harness hash covers ONLY src/observability/rpg_gate_metrics.py, so editing it makes older baselines stale. Keep every metric DEFINITION (compute, pool, the oracles and thresholds they use) in that one file; it may call src/ readers for typed records, but no definition logic lives elsewhere. A split needs testing-planner to add an explicit source list first. k and the per-metric floors live IN the module (testing-planner 2026-10-11); config.yaml holds only worlds/seeds/ticks, stale_after_days and the stop lines (config.yaml is hashed too, so editing a stop line also stales the baseline: safe direction). Contract: compute(RunArtifacts(world, seed, ticks, sha, state, run_dir)) and pool(docs).
- CONFIG WRITTEN (rpg-planner 2026-10-11, on rpg-combined #505): tests/simulation_quality/rpg_gate/config.yaml. The module MUST emit the pooled outcome row `O2.seeds_with_survivors` per world x kind group (the number of seeds with at least one member alive at the last tick); it is the R2 stop line's input (min 1). R1 (meal OFF vs ON, more than 2 SE apart) is not a stop line: it needs a two-arm run R1 stays a PAIRED-REPORT item read by rpg (testing-planner 2026-10-11: no two-arm mode planned; ask for an `arms` ticket if we ever gate it). R2 is a stop line ONLY (an outcome, never a validity metric): it's judged at re-baseline, and on daily runs it shows as drift.
- KNOWN REDS AT LANDING (testing child 6, agreed 2026-10-11): a validity row > 0 with a current owned `state: fail` entry in rpg_gate_known.yaml is OMITTED from the baseline candidate (recorded as omitted_validity); an unowned fail refuses the candidate. So this ticket MUST add rpg_gate_known.yaml entries (owner ticket, expiry) for every validity check expected to fail at M0, at least V3 (owned by the H6 record and the pull fixes), before recording v1.
- RECORDING v1 (testing #508, on main f40ccadff): only a MAIN run of the gate workflow is a baseline source. Download its `rpg-gate-candidate.json`, then `python -m tools.test_architecture.rpg_gate_baseline rebaseline --candidate rpg-gate-candidate.json --config tests/simulation_quality/rpg_gate/config.yaml --known tools/test_architecture/rpg_gate_known.yaml --milestone M0 --cite TCK-20261009-RPG-REGRESSION-METRICS-COMPUTED-FROM-TYPED-RECORDS`. The known-reds file is tools/test_architecture/rpg_gate_known.yaml. Tell testing-planner when the module is on main, and they dispatch.
- IMPLEMENTS THE CONTRACT in testing's epic: per (world, seed), one JSON document `rpg-gate-metrics/v1` {world, seed, ticks, sha, harness_hash, metrics:[validity {id, group, violations, examples<=5} | outcome {id, group, key?, tick?, value}]}, every metric carrying `scope: run|pooled`. Pooled validity (V7 and the hunt instance) carries raw counts, and the module exports `pool(docs_for_one_world)`. It also supplies the rpg-owned config: worlds, seeds, ticks, k, the floor per metric id, each validity oracle citation, and the R1/R2 stop lines.
- KIND GROUPS (designer, 2026-10-09): group O2 and every per-group figure by KIND PROPERTY (people-kind / wildlife / ...) and by settlement or affiliation, NEVER by EntityRole. The old trace grouped camp warriors (role MONSTER) with heroes as "heroes_other", which hid the real victims.
- A paired-comparison function over seeds (mean, SD, paired SE, k; the drift flag) that the testing harness calls.
- V7's liveness check reads the declared ways per kind (SURV-06) and the earning ways (EXCH-02) from content, not from a hardcoded list.
- The first baseline (v1) is computed AFTER Lane C's need-wake PR (designer, 2026-10-10: every earlier population figure is dominated by held moves; the baseline cites that PR), and after the hunting batch and the H6 record land, as a small summary table, with provenance.

- Move-issue counts (e.g. LEASH_RETURN issues, which went 22 -> 1665/run in the frontier under divergence 2.113) are OUTCOME rows only, never validity. If any metric reads them, v1 must be recorded AFTER the 2.113 PR lands so the jump is in the baseline, and any re-baseline that crosses it cites 2.113 (designer, 2026-10-11).

## Out of Scope
- The harness, the scheduled/dispatch workflow, the baseline file format and staleness, the report states and the ownership registry: testing-planner's tickets.
- The SimQ pillar (its own ticket).

## Acceptance Criteria
- Each V check has a test with a constructed counterexample that fails it and a clean run that passes it.
- The computation is deterministic and reads no live state (an architecture test).
- On one pinned run, the per-run metric JSON is reproduced exactly across two runs.

## Related Tickets
TCK-20261009-A-STARVATION-DEATH-RECORDS-THE-WAYS-IN-REACH-AND-THE-WAYS-TRIED-M0-GATE-H6 (V3's input); the hunting batch (FEEDING_KILL, CORPSE_FOOD, MEAT_DECAYED); Lane C's LAW-POSITION-IN-WORLD (V5); testing-planner's epic TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC (#469; children KNOWN-REDS-REGISTRY-SHARED-MODULE, RPG-GATE-BASELINE-FORMAT-AND-STALENESS, RPG-GATE-PINNED-FRESH-PROCESS-HARNESS, RPG-GATE-REPORT-STATES-AND-SAME-SHA-RERUN, RPG-GATE-SCHEDULED-AND-DISPATCH-WORKFLOW).

## Related Docs
.claude/handover/drafts/rpg-regression-metric-set-v1.md (the agreed metric set; copy it into the staging artifacts); docs/brainstorm/simulation-rule-taxonomy-evaluation-direction.md §5 (outcome neutrality) and §10 "Applied first to needs and livelihood" (designer, rpg-designer-next 2ce31a84f, riding the next evidence PR); docs/plans/test_architecture/roadmap.md §4.1-4.5; Bible 03, 06; world rules SURV-06/07, EXCH-02; designer memo rows 52-56.

## Related Stored Artifacts
None yet.

## Related Code Areas
src/simulation_quality/ or tools/ (a new metrics module), src/observability/event_extractor.py.

## Assumptions / Open Questions
- Lane: Lane B, together with the H6 record (which feeds V3). It lands before the M0 gate run; the gate report is this module run by testing's harness.

## Implementation Notes
TBD

## Test Summary
TBD

## Files Changed
TBD

## Completion Summary
TBD
