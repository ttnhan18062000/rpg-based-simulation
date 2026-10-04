---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261004-PACKAGE-REGISTRY-VALIDATOR
artifact_type: investigation
tags: [architecture, planning]
---

# Investigation — TCK-20261004-PACKAGE-REGISTRY-VALIDATOR

- Pattern: `codebase/health/registry.py` (JSONL, `validate_file`/`load_rows`/`RegistryError`, required-field table, existence checks) and `tests/codebase/test_code_health_ratchet_registry.py` (scratch repos, `--root`).
- `code-health` job (`.github/workflows/test.yml` ~L926): steps are checkout, setup-uv, `uv sync --locked --no-install-project`, node, changed paths, ratchet (`continue-on-error: true`). The validator needs only Python and git, so one more step there.
- `registries/system_registry.jsonl` has a `system` field with 7 names (combat, progression, cognition, social, faction, economy, world); the registry references it and does not copy it.
- Audit (`docs/plans/codebase_health/src_package_structure_audit.md`, approved 1c443a957): 36 packages with layer and decision; layer slugs map from L0 to L5.
- Standard rule M5 (python_code_standard.md L154) Enforcement is `reviewer`; `subsystem_ownership_lifecycle.md` has a code-health registry row to copy the shape of.
- Tests pinning the CI job list: `tests/static/test_ci_step_summary_reporting.py`, `tests/static/test_ci_uv_install.py` (`_LINT_JOBS`); adding a step to an existing job should not change job sets, to be confirmed by running them.
