---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261028-RE-RECORD-BASELINE-V1-UNDER-FLAT-SHA256-V3
artifact_type: investigation
tags: [benchmarking]
---

# Investigation

## Diff e8df8b96d..957caf8f6, measured paths (src, content, config, data, registries, tools/rpg_measure, gate paths)
| PR | commit | class | evidence |
|---|---|---|---|
| #753 step B | 3533fde71 | behaviour, measured | divergence 2.138, own paired run (base 341f700d0), merchant extinction STOP accepted (#715 6411018314) |
| #751 H1 | 35e80fb56 | neutral, measured | paired identical (RelationLookup) |
| #757 | 6e3ffea3f | dead-path deletions plus CLI | Deleted economy_systems/chests.ChestSystem, world_systems/quest_generator.QuestGenerator, appraisal.RecruitmentAppraiser and the shims chest_system.py and quest_generator.py. At 6e3ffea3f^1 their only importers were the shims, and nothing imported the shims. cli/entry.py is --entities (2.140, CLI only). The live QuestGenerator is a different class (src/quests/generator.py). |
| #760 | 2afdba653 | dead classes deleted | own `paired --neutral` IDENTICAL x3 (6e3ffea3f vs 99e2cf394) |
| #762 | 792a6b439 | docstring plus a never-taken error path | scorers.py docstring only. action_intent: an unknown or missing recipe used to raise KeyError (no catch at either call site), so no completed run took it. Own `--neutral` IDENTICAL x3 (2afdba653 vs ac0d2301f). history_query is observability only. |
| #758 F1 | 957caf8f6 | digest only | checkpoint.py scheme v3; benchmark_record.py |
| #735, #529 | 002bc317c, 10422cedd | perf records | src/perf/benchmark_record.py only |
| #731 | ab184acfc | API split | src/api only, not on the run path |
| #727, #747 | 0a3df6159, cb4f95015 | labels and grades | gate known file, SimQ anchors |
| #759, #752, #750, #737, #729, #722 | | tooling and sessions | no simulation path |

## Digest-bearing records
- `rpg_gate_v1.json`: provenance has `harness_hash` only. Its inputs (rpg_gate_harness.py, rpg_gate_run.py, tests/helpers/kernel_pinning.py, config, metrics module) are unchanged since v1; it is stale after 2026-11-21.
- `tests/regression/baseline_5k.json`: metrics only, no hash.
- Paired results: `start_hash` and `final_hash`.
