---
status: active
layer: testing
authority: P1
audience: agent
tags: [testing, architecture, planning]
---

# Test Architecture — Ticket Outlines for the Ticket Planner (revision f)

**Status: PROPOSAL, 2026-09-29. No tickets have been created.** Identifiers below (`TA-…`) are
placeholders, not ticket IDs; the ticket planner assigns real `TCK-YYYYMMDD-…` ids. Sources:
[`test_architecture_epic.md`](test_architecture_epic.md) (revision f),
[`milestone_plans.md`](milestone_plans.md), and
[`current_test_system_overview.md`](current_test_system_overview.md) (OV). Suggested tiers follow
CLAUDE.md tier routing. All ticket layers are `testing`.

- **Part 1** outlines tickets that are ready to cut: M0a, R1, and the documentation/metadata portion
  of MT.
- **Part 2** outlines tickets that **require an owner decision first**: R2, MF quarantine, and M2
  oracle review.

---

## Part 1 · Ready for ticket planning

### Dependency graph

```
TA-M0a-1 ──┬──► TA-M0a-2
           ├──► TA-M0a-3
           ├──► TA-M0a-4
           └──► TA-MT-2 ──► TA-MT-3
TA-MT-1 ─────► TA-MT-2
TA-R1-1 ─────► TA-R1-2
```

TA-R1-1 is independent of everything else and can start first. TA-MT-1 is doc-only and can start
immediately.

### M0a · As-is baseline

| Placeholder | Title | Tier | Scope | Out of scope | Acceptance | Depends on |
|---|---|---|---|---|---|---|
| **TA-M0a-1** | Core-RPG test report: schema, producer, inventory and lane layers | standard | Versioned report schema (layers + state vocabulary + denominators + input-artifact manifest, epic §6.2); a producer script; the classification layer (directory/import signals; `uncertain` and `unclassified` preserved; evidence-classification rules for example / characterization / broad-simulation tests); a lane layer derived from `test.yml` rules | coverage ingestion, SimQ/census/parity layers, any metadata markers | Two runs on the **same input artifacts** give identical normalized output. Every layer shows a value with its denominator, or a state. Failing tests present in the inputs are listed with their run id; **no fixed failure count** | — |
| **TA-M0a-2** | Standing coverage job + `make test-cov` repair | standard | Fix `make test-cov` (`Makefile:209-210` points at `tests_v2`/`src_v2`); add a nightly, informational CI job producing line + branch coverage with contexts; the report ingests its artifact with its scope label | making coverage a gate | The job produces an artifact with SHA, tier list and failed-test list; the report shows package coverage and domain coverage `not-derived` | TA-M0a-1 |
| **TA-M0a-3** | Parity evidence-state derivation + committed baseline snapshot | hotfix or standard | Read-only derived evidence state (`test_linked` / `audit_only` / `legacy` / `missing`); a committed snapshot of the categorized schema errors (OV §4.6) | changing ledger entries or priority semantics (D7 is a separate path) | Snapshot reproduces the 2,842 + 25 / 1,561 categorization at its SHA, or explains the difference | TA-M0a-1 |
| **TA-M0a-4** | SimQ and census state ingestion | hotfix | Report states `skipped-no-data` (with the 81-comparison denominator = 79 + 2) and `unstable` | fixing the SimQ skip (R3, SimQ owner) | States appear with provenance; no silent zero | TA-M0a-1 |

### R1 · Test-isolation repair

| Placeholder | Title | Tier | Scope | Acceptance | Depends on |
|---|---|---|---|---|---|
| **TA-R1-1** | Fix progression order-dependent test failures | standard (hotfix if the leak is trivial) | Bisect the polluting test for the 7 nodes (OV §4.2); fix at the source of the leaked state; add a regression guard; record a C5-format evidence record. If the source lies in feature code under rework → route to the feature team (C5) and mark `blocked` | Combined + isolated runs pass at one SHA → R1 `provisional` | — |
| **TA-R1-2** | RNG-contract check + random-order verification | standard | Check that a random-order plugin's reseeding (e.g. `pytest-randomly` resets `random.seed`) does not conflict with `DeterministicRNG` / `tests/unit/core/test_rng_contract.py`; add the plugin (a dev-dependency change) or an equivalent, **scoped to an opt-in job**, not default runs; run the directory in random order | Random-order run passes → R1 `verified` | TA-R1-1 |

### MT · Documentation and metadata portion

| Placeholder | Title | Tier | Scope | Out of scope | Acceptance | Depends on |
|---|---|---|---|---|---|---|
| **TA-MT-1** | Replace `docs/testing/test_taxonomy.md` with the level-contract taxonomy | standard (doc-only) | Level contracts, technique criteria, placement, ownership map, the evidence-classification table and proof kinds from epic §3 / §6; reconcile or retire the legacy-parity marker text; mark the old legacy markers as deprecated (not removed) | shared helpers, pattern examples | The doc covers every level in epic §3.2; `docs/testing/*` cross-links are updated; `make knowledge-index-update` run | — |
| **TA-MT-2** | Register test-metadata markers + advisory consistency check | standard | Register `domain(s)` / `level` / `proof_kind` / `behaviour_id` markers in `pyproject.toml`; an **advisory** check comparing declared domain vs imports/directory, reporting disagreements; S1 rule documented (required for new/modified core-RPG tests, advisory first) | bulk classification of existing tests; blocking enforcement | A synthetic marked test is located and classified by the report; a deliberately mismatched test is flagged; `uncertain`/`unclassified` counts unchanged for unmarked files | TA-MT-1, TA-M0a-1 |
| **TA-MT-3** | S2 label-proposal tooling (report-only) | hotfix or standard | Generate *proposed* labels for candidates where the directory and import signals agree (about 89 by the OV §10 scan); output a review list; **never writes markers** | applying labels; S3 uncertain files | The proposal list reproduces at the same SHA; nothing is changed in `tests/` | TA-MT-2 |

*(The shared helpers, pattern examples and replay-diff helper in MT are not outlined here; they
follow after TA-MT-2, per milestone_plans MT.)*

---

## Part 2 · Draft outlines that need an owner decision first

### R2 · Scenario lane selection

- **Decision required [D-R2]:**
  - (a) accept the three-outcome relevant-PR rule, including the **`tools/` mapping** (producers
    relevant, listed subdirectories not relevant, unmapped → impact-unknown → the lane runs);
  - (b) confirm that this roadmap owns the CI lane change;
  - (c) choose a dedicated scenario job (recommended) or a widened `PERF_RE`.
- **Draft TA-R2-1: Scenario lane selection rule + mapping honesty check** (standard).
  - Scope: the classifier over changed paths; the `tools/` mapping file with a justification per
    line; the dedicated job; the fixture test; the mapping-honesty static check; per-PR recording
    of outcome, trigger, execution and wall time.
  - Acceptance: see milestone_plans R2 item 7.
  - Depends on: D-R2 only.
- **Draft TA-R2-2: Lane cost observation** (hotfix). Record the median/p90 lane time and the
  fallback-triggered count over the first 10 relevant PRs, and revisit the split if the median
  exceeds 5 min. Depends on: TA-R2-1.

### MF · Quarantine mechanism

- **Decision required [D-MF]:**
  - (a) replace `docs/testing/regression_policy.md` §6's `xfail(strict=False)` rule with the bounded
    quarantine;
  - (b) the maximum expiry window N (proposed 14 days) and the renewal rule (proposed: one renewal,
    a second needs the owner);
  - (c) which always-on job hosts the required `quarantine_check` (proposed: `arch-docs`).
- **Draft TA-MF-Q1: Quarantine marker, collection hook and required check** (standard).
  - Scope: register the marker; a conftest hook that enforces node-level scope, required fields
    and an open ticket, and adds `xfail(strict=True, raises=…)` while active (behaviour observed
    with pytest 9.0.2, epic §7.3); JUnit `user_properties`; a static `quarantine_check` with a
    `QUARANTINE_TODAY` override for its own tests; report states `quarantined` /
    `quarantine-expired`.
  - Acceptance: see milestone_plans MF item 7.
  - Depends on: D-MF, TA-M0a-1 (report state).
- **Draft TA-MF-Q2: Update `regression_policy.md` §6 and link the unified triage workflow**
  (standard, doc). Depends on: D-MF (a).

### M2 · Oracle / spec review step

- **Decision required [D-M2]:**
  - (a) who approves oracles and expectation changes per core-RPG domain while the features are
    being reworked (the user, or a named feature-team lead per domain);
  - (b) whether oracle approval **blocks** Implement for ACs that add or change an expectation, or
    is advisory during the pilot (recommended: advisory in the pilot, blocking after the MP
    keep decision);
  - (c) the interim storage location for review records until the registry epic's link exists.
- **Draft TA-M2-O1: Review-record format + mechanical validator** (standard).
  - Scope: record fields (epic §6.3); the **two-part freshness** computation (rerun triggers →
    `unverified-at-sha`; approval triggers 1–5 → `stale-approval`; a behaviour-path-only change →
    rerun only); a validator used by the report.
  - Acceptance: a behaviour-path-only change yields `unverified-at-sha` and no re-approval; a spec
    section edit yields `stale-approval`; an assertion-literal edit yields `stale-approval`.
  - Depends on: D-M2 (c), TA-MT-2.
- **Draft TA-M2-O2: Oracle-review step in the ticket workflow** (standard; agent prompt change).
  - Scope: `investigator` `test_plan.md` mandatory fields (proof kind, oracle source, expected
    effect); a recorded approval by the D-M2 (a) approver when an AC adds or changes an
    expectation; the `done-checker` presence check.
  - Depends on: D-M2 (a, b), TA-M2-O1.
