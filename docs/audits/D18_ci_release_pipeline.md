---
status: active
layer: observability
authority: P1
audience: agent
tags: [audit, ci, release-pipeline, certification, github-actions, gates, local-only]
---

# D18 — CI / Release Pipeline Completeness

## Dimension Profile

| Axis | Value |
|---|---|
| **Group** | C — Developer Tooling |
| **State** | `done` |
| **Impact** | 3 / 5 |
| **Interest** | 2 / 5 |
| **Priority** | 5 |
| **Method** | review |
| **Audit date** | 2026-06-18 |

**What this dimension answers:** Is there a reproducible, automated path from passing code
to certified release — or are all gates developer-opt-in and local-only?

**Related dimensions:** D10 (Test Coverage) — the 121 test failures and 3 determinism breaches
found in D10 are all invisible to CI; D16 (Authoring DX) — ContentUsageMatrix drift (Task 3,
12/15) is already CI-detectable in principle, but CI has no test runner to detect it; D12
(Pattern Consistency) — architecture violations are not caught at merge time.

---

## Review Method

The CI surface is mapped by inventorying all GitHub Actions workflows and cross-referencing
them against the release-readiness conditions defined in `docs/engine/project_lawbook.md`.
Each gap finding is scored on the Pipeline Gate Coverage rubric.

### Pipeline Gate Coverage Scoring

3 dimensions, each 1–5. Maximum: 15. Higher score = more urgent to automate.

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| **Gate Coverage** | CI already gates this check | CI gates a related check, not this one exactly | This check is completely absent from CI; 0% of the surface is guarded |
| **Effort to Wire** | One step added to an existing workflow | New workflow file; some environment setup | Requires new infrastructure (runners, secrets, services) |
| **Risk if Missing** | Purely cosmetic / style issues | Functional regressions that tests would catch | Correctness/safety failures or release-condition violations that ship silently |

---

## CI Workflow Inventory

One workflow exists in `.github/workflows/`:

| File | Trigger | What it does |
|---|---|---|
| `deploy-docs.yml` | `push: main` | `mkdocs gh-deploy` — builds and publishes the documentation site to GitHub Pages |

**No other workflows exist.** No `test.yml`, `ci.yml`, `lint.yml`, or release pipeline file.

`deploy-docs.yml` does not invoke `pytest`, `make test`, any `lane-*` target, or
`gate-expansion`. It runs `pip install mkdocs-material` and deploys the site.

---

## Release-Readiness Conditions vs. Enforcement

`docs/engine/project_lawbook.md §Release-Readiness` defines three conditions:

| Condition | Mechanism | CI-enforced? |
|---|---|---|
| 1. 100% pass rate in CertificationHarness for CLASS_B hardware | `make lane-legacy-regression` / `pytest tests/certification/` | ❌ No |
| 2. Zero documentation drift detected by automated CI checks | Implied: `pytest tests/docs/test_contributor_guardrails.py` | ❌ No |
| 3. All new contributions verified by `test_contributor_guardrails.py` | `pytest tests/docs/` | ❌ No |

All three conditions are **manual** — developers must remember to run them locally.

---

## Makefile Gate Targets (all local-only)

The Makefile provides a complete local release gate:

| Target | What it runs |
|---|---|
| `make test` | Full suite (~3,292 tests) |
| `make test-quick` | Fast subset only |
| `make lane-architecture` | Static architecture guards |
| `make lane-catalog` | Catalog schema + reference graph |
| `make lane-all-fast` | All fast lanes combined |
| `make lane-legacy-regression` | Certification harness + arena + compat |
| `make gate-expansion` | Content expansion readiness gate |
| `make check-resources` | Resource pressure check (exit 1 if DEGRADED) |

None of these targets are invoked by any GitHub Actions workflow. They are developer-opt-in only.

---

## Key Findings

### F1 — No CI test runner: all 3,292 tests are local-only — Priority: 11 / 15

| Dimension | Score | Reason |
|---|---|---|
| Gate Coverage | 5 | Zero tests run in CI; the entire test surface is invisible at merge time |
| Effort to Wire | 1 | A `test.yml` workflow with `make lane-all-fast` is ~25 lines of standard GitHub Actions YAML |
| Risk if Missing | 5 | D10's 121 failures (FallbackRestrictedError teardown contamination, ItemStack.position crash, determinism breach) can merge to `main` undetected; no PR can fail CI on a broken test |
| **Total** | **11** | |

No `test.yml` or equivalent exists. Every push to `main` goes through CI that runs only
`mkdocs gh-deploy`. A change that breaks 121 tests, corrupts determinism, or causes
kernel contract failures will be accepted by CI and merged without any automated signal.

The teardown contamination identified in D10 F1 (34 errors cascading into cognition tests)
is a representative example of what CI would catch immediately.

**Minimum viable CI addition:**
```yaml
# .github/workflows/test.yml
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -e ".[dev]"
      - run: make lane-all-fast
      - run: make gate-expansion
      - run: pytest tests/docs/
```

---

### F2 — Release-readiness conditions are manual (all three unverified in CI) — Priority: 10 / 15

| Dimension | Score | Reason |
|---|---|---|
| Gate Coverage | 4 | All three release conditions from `project_lawbook.md` require local invocation; none are CI-enforced |
| Effort to Wire | 2 | Add `pytest tests/certification/` and `pytest tests/docs/` steps; `make lane-legacy-regression` needs env setup for slow tests |
| Risk if Missing | 4 | A release could go out while the CertificationHarness is failing; contributor guardrails only enforce if the submitter remembers to run them |
| **Total** | **10** | |

`project_lawbook.md` defines its release-readiness conditions with the assumption that
"automated CI checks" will detect doc drift and certification failures. In practice,
these are run by developers before releasing — not by the infrastructure.

The certification harness (`tests/certification/`) contains ~10 test files covering:
determinism parity, resource envelopes, rollout gates, event observability, manifest
integrity, and long-run stability. These are the highest-value automated checks in the
project and they never run automatically.

---

### F3 — Static architecture gate not in CI — Priority: 7 / 15

| Dimension | Score | Reason |
|---|---|---|
| Gate Coverage | 3 | `make lane-architecture` exists with good static guards; not connected to CI |
| Effort to Wire | 1 | One step: `make lane-architecture` in the `test.yml` job |
| Risk if Missing | 3 | D14's prohibited cross-domain import (core→engine lazy import) and D12's architecture violations could merge without triggering any gate |
| **Total** | **7** | |

`make lane-architecture` provides static architecture enforcement — the same category of
check that caught D14 F2 (hard_law_monitor→WorldIndexService coupling) and that would
have caught D12 F1 (unstable sorts). Not connected to CI means these guards are
effectively advisory.

---

### F4 — Content expansion gate not in CI — Priority: 5 / 15

| Dimension | Score | Reason |
|---|---|---|
| Gate Coverage | 2 | `make gate-expansion` exists; not in CI |
| Effort to Wire | 1 | One step added to test workflow |
| Risk if Missing | 2 | ContentUsageMatrix drift (D16 F3) could accumulate across multiple PRs before being noticed locally |
| **Total** | **5** | |

`make gate-expansion` is the content expansion readiness gate. D16 identified
ContentUsageMatrix drift as the highest-friction authoring trap (DX gap 12/15): new
YAML files in `data/content/` fail the matrix test silently until a developer runs it.
Wiring this gate into CI would make the D16 drift failure immediate on PR open.

---

### F5 — Release reports are ephemeral with no CI artifact upload — Priority: 5 / 15

| Dimension | Score | Reason |
|---|---|---|
| Gate Coverage | 2 | `reports/certification/` and `reports/release_proof/` exist locally; no CI artifact upload step |
| Effort to Wire | 2 | Add `actions/upload-artifact` step to a release workflow |
| Risk if Missing | 1 | Loss of artifact trail is an audit/traceability concern, not a correctness risk |
| **Total** | **5** | |

CLAUDE.md §After Work requires `rm -rf reports/release_proof/*` as a cleanup step —
confirming reports are treated as ephemeral local output. For a project with formal
release conditions, reports should be archived as CI artifacts tied to the commit SHA.

---

### Pipeline Gate Coverage Summary

| Finding | Description | Priority Score |
|---|---|---|
| F1 | No CI test runner — entire test suite is local-only | **11 / 15** |
| F2 | All 3 release-readiness conditions are manually enforced | **10 / 15** |
| F3 | Static architecture gate (`lane-architecture`) not in CI | **7 / 15** |
| F4 | Content expansion gate (`gate-expansion`) not in CI | **5 / 15** |
| F5 | Release reports are ephemeral; no CI artifact upload | **5 / 15** |

---

## What Exists (Positives)

| Area | Assessment |
|---|---|
| Makefile lane structure | Excellent — `lane-catalog`, `lane-architecture`, `lane-legacy-regression`, `lane-all-fast`, `gate-expansion` provide well-scoped, targeted gates |
| Certification harness | Rich — 10+ test files covering all major release conditions |
| `test_contributor_guardrails.py` | Complete — enforces doc terminology, extension templates, and CONTRIBUTING rules |
| `deploy-docs.yml` | Well-configured with `concurrency` controls to prevent overlapping deploys |
| `check-resources` | Useful local health check; `exit 1` on DEGRADED state |

The local gate infrastructure is mature. The only gap is the absence of a CI wrapper that calls it.

---

## Recommended Follow-Up Tickets

| Priority | Action | Finding |
|---|---|---|
| **P0** | Add `.github/workflows/test.yml` to run `make lane-all-fast`, `make gate-expansion`, and `pytest tests/docs/` on every push/PR | F1 + F4 — immediate test gate; unblocks all other findings |
| **P1** | Add release workflow step for `make lane-legacy-regression` (certification harness) — can be on `main` push only (slow) | F2 |
| **P1** | Add `make lane-architecture` as a step in the test workflow | F3 |
| P2 | Upload `reports/certification/` as a CI artifact in the release workflow via `actions/upload-artifact` | F5 |
| P2 | Cache pip dependencies and Python environment in `test.yml` to keep PR CI under 3 min | F1 (latency) |

---

## Related Dimensions

- **D10 (Test Coverage)** — F1 here is the CI-level mirror of D10's findings: the 121 test failures and 3 determinism breaches exist locally but are unenforceable at the PR boundary. Adding CI would make D10's top findings catch-on-merge.
- **D16 (Authoring DX)** — ContentUsageMatrix drift (D16 Task 3, 12/15) is already detected by an existing test; F4 here closes the final gap by wiring it into CI so authors get instant PR feedback.
- **D12 (Pattern Consistency)** — F3 here (`lane-architecture` not in CI) means D12 F1 (unstable sorts, determinism) and D14 F2 (cross-domain import) have no PR-level enforcement.
- **D13 (Type Safety)** — a CI lint/type-check step (e.g. `mypy src/`) would extend CI coverage to type annotation gaps; not yet assessed in D13.
