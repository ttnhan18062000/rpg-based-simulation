---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261021-PYREFLY-ADVISORY-REPORT
artifact_type: investigation
tags: [delivery]
---

# Investigation — TCK-20261021-PYREFLY-ADVISORY-REPORT

- The decision record is `docs/plans/codebase_health/python_code_craft_type_checker_trial.md` (commit e6b3f97f). Pyrefly 1.3.2 found 817 errors in 151 files and took about 2 s and 207 MB. It has a native baseline that needs no source edits, and it flagged 100 lines that neither mypy nor basedpyright reported. The record recommends it as an advisory second opinion, not as a gate.
- The owner's decision of 2026-10-20 (relayed by lead-planner): report-only, never a gate. M7 (`src/api/server.py`) waits until this batch merges (roadmap decision 7 amendment).
- PyPI release dates as of 2026-10-21: 1.3.2 on 2026-09-28, 1.4.0 on 2026-10-15. Only 1.3.2 meets the two-week age rule.
- `Type check` job (`test.yml`): it is required and deliberately has no continue-on-error (see its own comment). So Pyrefly cannot go inside it; it needs its own, non-required job.
- `tests/static/test_ci_uv_install.py` pins the `lint` group to exactly {ruff, complexipy, ast-grep-cli, import-linter}, and pins `_LINT_JOBS`. Both pins change with this ticket. They belong to testing, so the 8.11 notice applies.
- `tests/codebase/test_typecheck_gate_configured.py` pins the mypy gate. Pyrefly must leave it unchanged.
- `INFRA-TYPE-001` in `docs/parity_ledger/infrastructure.yaml` covers mypy. Pyrefly gets its own `INFRA-TYPE-002` entry.
