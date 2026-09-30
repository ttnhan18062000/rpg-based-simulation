---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260930-CORE-RPG-TEST-REPORT-V0
artifact_type: investigation
tags: [testing]
---

# Investigation: core-RPG test report v0

- Context scan: `search_docs` found no existing report producer; no `tools/test_architecture/` exists. `tools/code_test_index.py`
  is a graphify symbol index (different purpose), not reused.
- CI (`.github/workflows/test.yml`): pytest lanes list directories explicitly; only `api-tools` uploads JUnit (line ~387);
  a certification report artifact is uploaded separately. So execution data is a supplied input in v0.
- Classification rules come from `docs/plans/test_architecture/reference/current_test_system_overview.md` §10 (directory list and import list).
  Neither signal is reliable alone (89 agree, 59 directory-only, 56 import-only in the planner's 2026-09-28 script), hence `uncertain`.
- Mutation records are tracked at `tests/mutation/baselines/` (batch 1); `reports/*` is gitignored.
- Escaped-defect tag registered 2026-09-29 (`registries/tag_registry.jsonl`).
