---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-TEST-ARCH-MAINT-MUTATION-BASELINE-METHOD-DOC
artifact_type: investigation
tags: [testing]
---

# Investigation — TCK-20261003-TEST-ARCH-MAINT-MUTATION-BASELINE-METHOD-DOC

## Context scan

`search_docs` MCP failed to connect this session, `graphify-out/graph.json` is absent in a fresh worktree
(untracked by design) and `tools/knowledge_search.py` needs `sentence-transformers` (not installed). The scan
was targeted reads of the sources below; this is disclosed, not a gate.

## Findings

- A selection tool already exists: `tools/test_architecture/mutation_selection.py` (the social baseline's
  `selection.rule_description` names it). The doc points at it; no new tool is needed.
- `tests/mutation/baselines/` holds `src_core_conservation.json` (v1), `_v2.json`, `_v3.json` and
  `src_systems_social_appraisal_v1.json`. The social v1 record carries `tool` (mutmut 2.5.1, `pip --target`,
  install and reproduction commands), `run` (source SHA `9640ff942877cc7264e83309f35d19022a4a3fe6`, a
  `git archive` scratch copy), `selection` (rule `import-based-one-hop`, 46 files, `resolved_files_sha256`
  `41fc8fd64d2e7ed53d04ae56609c21c02443a74ee55f776891417316374ecb00`, green before mutation: 313 passed),
  `determinism_g3` (kernel ran in 3 selected files, 5 `Kernel.tick_once` calls; as found `audit_mode False`
  and `max_tick_budget_ms 100`; forced `audit_mode=True` and `max_tick_budget_ms=10000000` by an out-of-repo
  plugin; reference `docs/engine/deterministic_execution.md` extension rule 5), `positive_control` (fresh, one
  hand mutant on line 67), `stale_after` (target sha256 change, selection change, 30 days, RELATIONSHIP-VECTOR
  landing) and the separate `catalog_conflicting_*` fields. v3 carries `stale_after` (30 days) and `supersedes`.
- Reach-check case C4: `_appraise_position_swap` 0 of 38 mutants killed under the one-hop selection; three
  other test files (24 tests passed) execute 1 of its 28 statements (lines 234 to 298) at `9640ff942`;
  report §4 of `docs/testing/social_test_report_2026-10-03.md`.
- Reach-check case C2: `guilds.py` reads 0% under every social selection and 92% (39 statements, 3 missed)
  from `tests/unit/world/test_guild_intel.py` (2 tests passed), same coverage command; report §2.2. The C2
  ticket and artifacts do not carry a full SHA for this measurement, so the doc cites the report and states
  that, rather than inventing one (see open item below).
- Pilot doc: `docs/testing/core_rpg_test_pilot_2026-09-30.md`, paragraph "**Update 2026-10-01 (v2
  baseline).**" (reviewer-confirmed). Roadmap §6 (e) is at about line 269.

## Open item

The `guilds.py` measurement's SHA is only "the same branch head" in the report. Resolve by reading the git
history of the C2 commit for the report's §2.2 figure; if it cannot be pinned, the doc says "SHA not recorded
in the report" for that case.
