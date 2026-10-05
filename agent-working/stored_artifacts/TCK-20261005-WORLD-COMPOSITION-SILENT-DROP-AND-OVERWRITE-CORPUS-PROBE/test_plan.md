---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261005-WORLD-COMPOSITION-SILENT-DROP-AND-OVERWRITE-CORPUS-PROBE
phase: done
date: 2026-10-05
tags: [world]
---

# test_plan — TCK-20261005-WORLD-COMPOSITION-SILENT-DROP-AND-OVERWRITE-CORPUS-PROBE

| Case | Test |
|---|---|
| duplicate place id detected, and the compiler loses one | `test_duplicate_place_ids_fires_and_compile_loses_the_place`, `..._end_to_end_through_the_resolver` |
| distinct place ids quiet | `test_duplicate_place_ids_quiet_for_distinct_ids` |
| dangling population / resource / building detected; resolving spec quiet | `test_dropped_placements_fires_for_each_kind_of_dangling_reference`, `..._quiet_for_resolving_references` |
| faction id not pre-seeded; disagreeing definitions; matching definitions quiet | `test_faction_merge_fires_for_an_id_the_resolver_did_not_pre_seed`, `..._two_modules_disagree...`, `..._quiet_when_every_contribution_matches_the_seed` |
| why the faction count is structurally zero | `test_a_module_naming_a_faction_outside_the_catalog_cannot_reach_the_merge` |
| biome mismatch for an underscore namespace; quiet for a one-word or absent namespace | `test_biome_provenance_fires_...`, `..._quiet_for_a_single_word_namespace`, `..._quiet_without_a_namespace` |
| validator residue counts per rule without raising; `.jsonl` output enforced; zero counts reported | `test_validator_residue_counts_issues_per_rule_without_raising`, `test_main_rejects_a_non_jsonl_output_path`, `test_summarize_reports_zero_counts_per_check` |
Result: 15 passed. The corpus run uses the same detectors, so a zero there is a zero from a detector shown able to fire.

## Proof Plan
- level: unit and end-to-end through the real `WorldAssemblyResolver` / `WorldCompiler` with synthetic modules, plus a corpus-wide run of 24 compositions
- proof kind: positive control (deliberately introduced instance must be detected) and negative control (clean input stays quiet), per check
- oracle source: the resolver and compiler source lines cited in `investigation.md`; the catalog's own region definitions for the expected biome
- expected effect: each detector fires on its deliberate instance and stays quiet otherwise; the corpus run reports a count per world and check, including zeros
- selected commands: `pytest tests/tools/test_world_composition_corpus_probe.py`; `python3 tools/world_composition_corpus_probe.py --out <path>.jsonl`
