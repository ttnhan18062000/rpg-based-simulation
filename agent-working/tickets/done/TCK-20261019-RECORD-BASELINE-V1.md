---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261019-RECORD-BASELINE-V1
phase: done
date: 2026-10-19
tags: []
---

# TCK-20261019-RECORD-BASELINE-V1

## Title
Record baseline v1: paired fingerprints, gate V1-V8 rows and the behavioral_5k rebaseline, all on one commit, with v1_disclosure.md as what v1 does not claim

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Milestone 0 ends with the baseline v1 record, and milestone 1 measures against it. The recipe below is the designer's (rpg-designer, 2026-10-19). The user's merge of the v1 PR is the owner's sign-off.

## Scope
0. Precondition checklist (it goes in the v1 PR body). Every "before v1" ruling must be folded on the v1 commit:
   - D70 camp spawns;
   - D71 stronghold;
   - D72 terrain cost;
   - D74 species;
   - D75 route;
   - the D78 gate path: earning, eating, cover, high ground, chokepoints;
   - the grief fix (TCK-20261016-GRIEF-AS-STATE-…);
   - the event-drop fix (TCK-20261016-EVENT-FILE-KEEPS-EVERY-EVENT-THAT-PASSED-THE-MODE-FILTER, to confirm) and its tests;
   - V8.
   Each one cites a fold sha and a test path. Anything not folded is either listed in v1_disclosure.md or blocks v1.
1. The commit is main after #654 (R2) and the designer's docs batch (v1_disclosure.md must be on main).
2. Paired fingerprints become the new D76 cumulative base, replacing 903239fbe:
   - 3 gate worlds × seeds 42-51 (10) × 5000t;
   - audit_mode, signals zeroed, full self-check.
   Behaviour steps after v1 are still measured on seeds 42-46.
3. Gate V1-V8 rows, recorded as rpg_gate_baseline_format.md "Recording v1" specifies:
   - the candidate comes from a scheduled or dispatched MAIN run, never --evidence-only, on the config's 5 seeds (42-46, D54), governor-pinned NORMAL;
   - then `rebaseline --milestone M0 --cite TCK-20261019-RECORD-BASELINE-V1`, with the JSON in the v1 PR;
   - if any kind group crosses R2 (O2.seeds_with_survivors min 1), the rebaseline needs `--owner-ruling-ref/date` from the OWNER;
   - R1 is not in v1 by construction, because it needs the two-arm free-meal run.
4. Calibration regenerated with make evaluate-full (host-independent sidecar), so testing can re-anchor SimQ (TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1). That is data for the after-v1 rebuild, never called a grade.
5. behavioral_5k is rebaselined on the same commit (T2, TCK-20261007-BEHAVIORAL-5K-REBASELINE-…).
6. The PR body has one line asking the owner to accept v1 with v1_disclosure.md, and names the two edge items:
   - crowded_frontier at the D76 stop edge;
   - the frontier M2 report-only reading, which would have stopped had it been live.

## Out of Scope
- D73 free-meal removal: it comes after v1 and is measured against it, followed by the gate.
- The roadmap §12.3 v1 sha line and the disclosure header (the designer adds them in the next batch).
- Never compare across the gate record (governor-pinned NORMAL) and the paired record (audit_mode).

## Acceptance Criteria
- Every precondition row has a sha and test path, or is named in v1_disclosure.md.
- The paired base is recorded on the v1 commit (10 seeds, self-check spread 0) and the D76 table points at it.
- The gate baseline JSON comes from a main run, is committed in the v1 PR, and is cited to this ticket.
- behavioral_5k is green on the v1 commit after the rebaseline.
- The calibration dirs carry the run_determinism sidecar. Testing-planner is told the v1 sha.

## Related Tickets
- TCK-20261014-SIMQ-SINGLE-REANCHOR-ON-BASELINE-V1 (testing; check date 10-31)
- TCK-20261007-BEHAVIORAL-5K-REBASELINE-… (expires 11-15)
- TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK

## Related Docs
- docs/plans/systemic_world/v1_disclosure.md
- docs/plans/systemic_world/roadmap.md §12.3
- docs/plans/systemic_world/owner_decision_memo.md (D44, D54, D70-D78)
- docs/plans/test_architecture/reference/rpg_gate_baseline_format.md ("Recording v1")

## Related Stored Artifacts
- .claude/handover/drafts/M0-CUMULATIVE-WATCH-TABLE.md

## Related Code Areas
- tools/rpg_measure/paired.py
- the rpg gate rebaseline tool
- tests/regression/test_behavioral_5k.py

## Assumptions / Open Questions
- Whether main after 6d7bd1509 (the #645 tip) has moved simulation behaviour (deps window, R1, R2, other domains). A hash-identity check answers this before the record.

## Implementation Notes
v1 = e8df8b96d (main after #714 v1 fixes, #718 known file, #720 emitter filter). Order of events: the first 1b (paired.py on e6a6a3e10) was refused (NonAuditRunError: the cached base at 903239fbe predates the determinism fix, so its manifest has audit_mode/signals_zeroed = None; the plan's command had left out --legacy-base). The re-run with --legacy-base --self-check full proved the base audit by a byte-identical 30-run base repeat. The first gate run on main (39710919027) was RED with 5 unowned fails (3 V3, 2 V2) and wrote no candidate; the V2 pair was a one-tick decay-record defect fixed by #720, the V3s were owned by a blanket known entry (#718, expires 2026-11-05). The recorded candidate is from gate run 39799337778 (workflow_dispatch on main, no ref input, commit_sha e8df8b96d, not evidence-only, harness_hash 525fe36f2cbc equal to run 39710919027's). 1b on e6a6a3e10 carries over to v1 because (a1) (#720) was proven identical in every paired result field, 0 of 15 pairs (P1); the known file changes only verdict labels. The diff e6a6a3e10..e8df8b96d under src, content, config, data, registries, tools/rpg_measure and the gate paths is src/engine/economy.py (#720), tools/test_architecture/rpg_gate_known.yaml (#718) and registries/session_roles.yaml (outside the measured paths, session routing only).

## Test Summary
1b (paired, seeds 42-51, 5000t, --legacy-base --self-check full, e6a6a3e10 vs 903239fbe): base repeat spread 0 (30 runs byte-identical); people deaths frontier 255->246 (-9, SE 1.83), urban 91->99 (+8, SE 0.92), crowded 300->312 (+12, SE 0.80), all no drift; the tool's extinction line is STOP none in all three worlds; two-way per-seed extinctions only_in_new 45 / only_in_base 29 (v1b/extinct_two_way.txt), disclosed under owner memo row 86; crowded raider 54->69 per-kind is disclosed with the goblin-spawn confound (not a stop). Gate run 39799337778: GREEN, 90 pass / 18 fail (all owned: 15 V1 free-meal, 3 V3) / 0 drift / 0 unstable / 253 no-data (no baseline existed), V2 pass on all 15; V3 examples exactly urban_political/44 merchant 28 (t3140), frontier_living_world/44 worker 2 (t3736), crowded_frontier/46 raider 38 (t3778). rebaseline --milestone M0 --cite this ticket: wrote rpg_gate_v1.json (no owner-ruling flags); `rpg_gate_baseline lint` exit 0. behavioral_5k (urban_political, seed 42, 5000t, PYTHONHASHSEED=0): two regeneration runs agree; alive_avg 13.30 -> 18.34, gold_avg 584.16 -> 904.2, quest_active_count 0.0 -> 6.16; tests/regression/test_behavioral_5k.py -m extra_slow passes (412 s). Attribution: the harness change (shared world helper with the content context, tick-0 gold guard) accounts for most of the move (that harness measured 18.34 / 909.4 / 7.08 on 66ba2aa39); the remaining gap to v1 (gold 909.4 -> 904.2, quest 7.08 -> 6.16) is simulation changes merged between the harness run and v1, not isolated to a PR.

## Files Changed
tests/simulation_quality/rpg_gate/baselines/rpg_gate_v1.json (new), tests/regression/baseline_5k.json, the merged rpg-baseline-v1 files (tests/helpers/world_build.py, tests/regression/test_behavioral_5k.py, tests/unit/worldassembly/test_world_build_helper_matches_the_gate.py, tickets), the designer's docs commits (docs/plans/systemic_world/owner_decision_memo.md, v1_disclosure.md, roadmap.md), docs/REGISTRY.yaml, monitoring shards.

## Completion Summary
Baseline v1 recorded at e8df8b96d: the gate baseline JSON (M0) from a main run, the behavioral_5k rebaseline, and 1b carried over under owner memo rows 85/86. NOT done in this ticket: scope item 4 (calibration regenerated with make evaluate-full and its run_determinism sidecar, for testing's SimQ re-anchor) and pointing the D76 cumulative table at the new base (the 1b run is the data for it); both are carried by TCK-20261023-V1-CALIBRATION-AND-D76-TABLE-ON-THE-NEW-BASE and are not claimed here. The user's merge of the record PR is the owner's sign-off.
