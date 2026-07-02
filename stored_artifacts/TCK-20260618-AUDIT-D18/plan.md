# D18 Audit Plan

## Approach
Review method. Map the CI surface, cross-reference against release-readiness conditions
defined in `project_lawbook.md`, and score each gap by Pipeline Gate Coverage.

## Data Sources
- `.github/workflows/` — all CI workflows (one found: deploy-docs.yml)
- `Makefile` — test/gate targets
- `docs/engine/project_lawbook.md §Release-Readiness` — 3 release conditions
- `tests/certification/` — certification harness files
- `tests/docs/test_contributor_guardrails.py` — guardrails test

## Output
- `docs/audits/D18_ci_release_pipeline.md`
- Ticket moved to done
- `docs/audits/audit_dimensions.md` D18 row updated
