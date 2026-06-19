# D18 Investigation — CI / Release Pipeline Completeness

## CI Workflow Inventory

`ls .github/workflows/` returns exactly one file:

- `deploy-docs.yml` — Builds MkDocs site, deploys to GitHub Pages on push to `main`.
  Triggered by: `push: branches: [main]`. Steps: `actions/checkout`, `actions/setup-python`,
  `pip install mkdocs-material`, `mkdocs gh-deploy`.
  **Does NOT run pytest, make test, or any quality gate.**

No `test.yml`, `ci.yml`, `lint.yml`, or any other workflow exists.

## Makefile Test / Gate Targets (all local-only)

| Target | What it runs | Slow? |
|---|---|---|
| `make test` | Full test suite | Yes |
| `make test-quick` | Fast tests only | No |
| `make lane-catalog` | Catalog schema + reference graph | No |
| `make lane-architecture` | Static architecture guards | No |
| `make lane-all-fast` | All fast lanes combined | No |
| `make lane-legacy-regression` | Arena + certification + legacy compat | Yes |
| `make gate-expansion` | Content expansion readiness gate | No |
| `make check-resources` | Resource pressure check (exit 1 if DEGRADED) | No |

None of these targets are invoked by any GitHub Actions workflow.

## Release-Readiness Conditions (project_lawbook.md §Release-Readiness)

Three conditions must be met before a certified release:

1. **CLASS_B Certification** — 100% pass rate in `tests/certification/` for CLASS_B hardware profile.
2. **Zero documentation drift** — No drift detected by automated CI checks.
3. **Contributor guardrails** — All new contributions pass `tests/docs/test_contributor_guardrails.py`.

Enforcement status: **Manual only.** Developers must run `make lane-legacy-regression` and `pytest tests/docs/` locally. Neither runs in CI.

## Certification Harness (tests/certification/)

~10 certification test files found:
- `test_final_gate.py` — production-readiness gate
- `test_harness_contract.py` — CertificationHarness contracts
- `test_cert_long_run_stability.py` — long-run stability across seeds
- `test_manifest_snapshot.py` — manifest integrity
- `test_envelope_violations.py` — resource envelope violations
- `test_event_observability_parity.py` — observability parity
- `test_phase10_enhanced_determinism_parity.py` — determinism
- `test_phase10_enhanced_rollout_gate.py` — rollout gate
- `test_artifact_budget.py` — artifact budgets
- `test_evidence_levels.py` — evidence levels

**None of these run in CI.** The certification harness is the most thorough release gate — and it is 100% local.

## Reports Directory

`reports/` exists with `perf/`, `certification/`, `arena/` subdirectories.
Reports are generated locally by test runs. No CI workflow uploads them as build artifacts.
CLAUDE.md §After Work specifies `rm -rf reports/release_proof/*` — confirming reports are ephemeral.

## What Would Need to Change to Add CI

Minimum viable CI for this project (a `test.yml` GitHub Actions workflow):
```yaml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -e ".[dev]"
      - run: make lane-all-fast          # fast lanes: catalog + architecture + others
      - run: make gate-expansion         # content expansion gate
      - run: pytest tests/docs/          # contributor guardrails (release condition 3)
```

For a full release gate, also add:
```yaml
      - run: make lane-legacy-regression  # certification harness + arena + compat
      - uses: actions/upload-artifact@v4
        with:
          name: certification-report
          path: reports/certification/
```
