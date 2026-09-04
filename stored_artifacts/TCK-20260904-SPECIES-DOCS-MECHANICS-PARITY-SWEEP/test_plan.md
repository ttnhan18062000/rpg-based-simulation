---
status: active
layer: mechanics
authority: P1
audience: agent
ticket_id: TCK-20260904-SPECIES-DOCS-MECHANICS-PARITY-SWEEP
artifact_type: test_plan
tags: [content, schema]
---

# Test Plan — TCK-20260904-SPECIES-DOCS-MECHANICS-PARITY-SWEEP

This is a docs-only ticket — no `src/`/`tests/` code changed. Verification is validator/citation
based, not pytest-sweep based.

## `validate_frontmatter.py`
`tools/validate_frontmatter.py docs/` → 355 pre-existing violations across 858 files. Cross-
referenced all 25 files this ticket touched against the violation list: **zero matches** — this
ticket introduced no new frontmatter violations. (Full pre-existing violation list is unrelated
repo-wide debt: archive status mismatches, missing frontmatter in `docs/brainstorm/codex/`,
`docs/guides/` missing `status`, `docs/plans/idea_*.md`'s invalid `status: idea` — none touched
here.)

## Parity index build/health
`tools/parity_index.py build` → `{"status": "ok", "shard_count": 9, "entry_count": 2144}`.
`tools/parity_index.py health` → runs clean, findings are the same pre-existing baseline
population.

## Parity ledger test_path citations verified real and passing
Every `test_path` written or changed by this ticket's `write_entry()` calls was directly run and
confirmed passing, not assumed:
- `tests/unit/content_semantics/test_relation_species_projection.py::
  test_species_relations_hostility_changes_projected_label` (COMB-317, STRAT-263, SOC-257's
  associated evidence tests) — passed.
- `tests/unit/content/test_catalog.py::test_all_13_species_have_documented_intelligence_tier`
  (INFRA-400) — passed.
- `tests/unit/entities/test_entity_identity_resolver.py::
  test_clean_archetype_contract_resolves_clean_identity` (spot-check for the wider content-schema
  citation chain) — passed.

## Entries updated (10, via `write_entry()`)
PROG-120, COMB-317, STRAT-263, STRAT-251, INFRA-329, INFRA-400, SOC-257, SUB-380, SUB-381,
SUB-382.

## Entries found but deliberately left unchanged (10, documented reason)
STRAT-169, SOC-034, SOC-035, SOC-036, SOC-041, SOC-065, SUB-164, SUB-240, SUB-241, WORLD-019,
WORLD-047 — all blocked by the same pre-existing `priority: P0` + `test_path: null` schema
violation (see investigation.md); `write_entry()` correctly refuses these without a real test_path
authored, which is out of this ticket's scope.

## Docs files fixed (16)
`docs/architecture/2026-08-10-cognition-driven-adventure-eligibility-design.md`,
`docs/audits/{D01_rpg_feature_impact,D21_entity_lifecycle_foundation_layers,
D22_dormant_content_wiring}.md`, `docs/content/pipeline_contract.md`,
`docs/core/{attributes_and_classes,items_and_inventory}.md`,
`docs/guidelines/{fallback_retirement_criteria,intentional_divergences}.md`,
`docs/simulation/quest_contract.md`,
`docs/simulation_quality/{entity_lifecycle_score,event_type_coverage}.md`,
`docs/world/assembly_contract.md`,
`docs/plans/rpg_design_roadmap/{rpg_design_roadmap,rpg_m9_corpus_test_coverage_epic,
rpg_m2_foundational_systems_epic}.md`.
