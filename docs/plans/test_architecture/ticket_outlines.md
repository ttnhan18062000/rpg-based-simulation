---
status: active
layer: testing
authority: P1
audience: agent
tags: [testing, architecture, planning]
---

# Test Architecture — Ticket Outlines for the Ticket Planner (revision f)

**Status: PROPOSAL, 2026-09-29 (revision h; decisions PENDING). No tickets have been created.** Full drafts of TA-R1-1, TA-MT-1 and TA-M0a-1 are in the review package; baselines were re-checked at `origin/main` `5d4e4a237`. Identifiers below (`TA-…`) are
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
| **TA-M0a-1** | Core-RPG test report v0: schema, producer, classification and lane layers | standard | Versioned schema (layers, states, denominators, input manifest); producer; classification layer (signals only; `uncertain`/`unclassified` kept); lane layer from `test.yml`; an execution layer from **supplied** JUnit that distinguishes **`no-junit-artifact`** (no JUnit supplied for that lane or run) from **`not-run`** (the lane or node was absent from a supplied run: skipped lane, deselected, not collected) from **`pass`/`fail`/`skipped`** (the node's recorded outcome) | coverage, SimQ/census/parity layers, markers, CI changes | Two runs on the same input artifacts are identical after normalization; every count has a denominator; the three execution states never collapse into each other; failing nodes are listed with their run id; **no failure-count target**. v0 limits stated in the report header | — |
| **TA-M0a-2** | Standing coverage job + `make test-cov` repair | standard | Fix `make test-cov` (`Makefile:209-210` points at `tests_v2`/`src_v2`); add a nightly, informational CI job producing line + branch coverage (**no per-test contexts**; those are in Part 3); the report ingests its artifact with its scope label | making coverage a gate | The job produces an artifact with SHA, tier list and failed-test list; the report shows package coverage and domain coverage `not-derived` | TA-M0a-1 |
| **TA-M0a-3** | Parity evidence-state derivation + committed baseline snapshot | hotfix or standard | Read-only derived evidence state (`test_linked` / `audit_only` / `legacy` / `missing`); a committed snapshot of the categorized schema errors (OV §4.6) | changing ledger entries or priority semantics (D7 is a separate path) | Snapshot reproduces the 2,842 + 25 / 1,561 categorization at its SHA, or explains the difference | TA-M0a-1 |
| **TA-M0a-4** | SimQ and census state ingestion | hotfix | Report states `skipped-no-data` (with the 81-comparison denominator = 79 + 2) and `unstable` | fixing the SimQ skip (R3, SimQ owner) | States appear with provenance; no silent zero | TA-M0a-1 |

### R1 · Test-isolation repair

| Placeholder | Title | Tier | Scope | Acceptance | Depends on |
|---|---|---|---|---|---|
| **TA-R1-1** | Fix the registry/content-mode state leak behind 7 progression failures | standard | Reproduce against the 8 identified polluter files; fix the leaked state at its source; add a regression guard; record a C5 evidence record. If the source is feature code under rework → route to the feature team, `blocked` | **Bounded verification at one SHA:** each polluter + 3-file reproducer passes; `tests/unit` and the combined fast-tier command show 0 failures in the 7 nodes; `tests/unit/domains` alone still passes → R1 `provisional` (random order in TA-R1-2) | — |
| **TA-R1-2** | RNG-contract check + random-order verification at the same SHA as TA-R1-1's final runs | standard | Check that a random-order plugin's reseeding (e.g. `pytest-randomly` resets `random.seed`) does not conflict with `DeterministicRNG` / `tests/unit/core/test_rng_contract.py`; add the plugin (a dev-dependency change) or an equivalent, **scoped to an opt-in job**, not default runs; run the directory in random order | Random-order run passes → R1 `verified` | TA-R1-1 |

### MT · Documentation and metadata portion

| Placeholder | Title | Tier | Scope | Out of scope | Acceptance | Depends on |
|---|---|---|---|---|---|---|
| **TA-MT-1** | Replace `docs/testing/test_taxonomy.md` with the level-contract taxonomy | standard (doc-only) | Level contracts, technique criteria, placement, ownership map, the evidence-classification table and proof kinds from epic §3 / §6; reconcile or retire the legacy-parity marker text; mark the old legacy markers as deprecated (not removed) | shared helpers, pattern examples | The doc covers every level in epic §3.2; `docs/testing/*` cross-links are updated; `make knowledge-index-update` run | — |
| **TA-MT-2** | Register test-metadata markers + advisory consistency check | standard | Register `domain(s)` / `level` / `proof_kind` / `behaviour_id` markers in `pyproject.toml`; an **advisory** check comparing declared domain vs imports/directory, reporting disagreements; S1 rule documented (required for new/modified core-RPG tests, advisory first) | bulk classification of existing tests; blocking enforcement | A synthetic marked test is located and classified by the report; a deliberately mismatched test is flagged; `uncertain`/`unclassified` counts unchanged for unmarked files | TA-MT-1, TA-M0a-1 |
| **TA-MT-3** | S2 label-proposal tooling (report-only) | hotfix or standard | Generate *proposed* labels for candidates where the directory and import signals agree (about 89 by the OV §10 scan); output a review list; **never writes markers** | applying labels; S3 uncertain files | The proposal list reproduces at the same SHA; nothing is changed in `tests/` | TA-MT-2 |

*(The shared helpers, pattern examples and replay-diff helper in MT are not outlined here; they
follow after TA-MT-2, per milestone_plans MT.)*

---

## Part 2 · Decision-gated drafts

### R2 · Scenario lane selection (draft for D-R2)

**Rule (phase 1, minimal):**

| Outcome | Paths |
|---|---|
| **Trigger the scenario lane** | `src/**`; known scenario dependencies: `tests/mechanic_scenarios/**`, `tests/helpers/**`, `tests/conftest.py`, `data/worlds/**`, `config/**`, `requirements*.txt`, `pyproject.toml`, `.github/workflows/test.yml`, and the known input-generator scripts (`tools/generate_corpus_registry.py`, `tools/evaluate_simq.py`, `tools/calibrate_simq.py`; the list is kept in the rule file) |
| **Known irrelevant** | `docs/**`, `tickets/**`, `agent-monitoring/**`, `tmp/**`, `frontend/**`, `dashboard-frontend/**` |
| **Unknown → conservative fallback: the lane runs** | everything else, including other `tools/**` and any newly added top-level path. **Listed by name in the job summary** as "fallback-triggered by: …" |

- **Draft TA-R2-1: Dedicated scenario lane + phase-1 rule** (standard).
  - Scope: the classifier; a dedicated job running `tests/mechanic_scenarios`; the job summary
    listing matched and fallback paths; a fixture test for the classifier; per-run recording of
    outcome, trigger and wall time (JUnit + summary).
  - Acceptance: fixture cases pass (`src/progression/x.py` → trigger; `docs/x.md` → skip;
    `tools/new_thing.py` → trigger via fallback, and named in the summary).
  - Cost: one extra parallel job per relevant PR.
- **Draft TA-R2-2: Measure actual lane cost** (hotfix). Record lane wall time and the
  fallback-triggered count over the first 10 relevant PRs. **The rule is not expanded or narrowed
  (e.g. by mapping `tools/` subdirectories as irrelevant) until this measurement exists.**
- **Requires [D-R2]:** approval of the phase-1 rule table and fallback, the dedicated job, and this
  roadmap as owner of the CI change.

### MF · Bounded quarantine (policy now, tooling later)

- **Draft TA-MF-Q2: Publish the bounded-quarantine policy** (standard, doc).
  - Scope: update `docs/testing/regression_policy.md` §6 from unbounded `xfail(strict=False)` to
    bounded quarantine (nondeterminism class only; node-level `xfail(strict=True, raises=…)`; owner,
    ticket and expiry recorded; existing failures never quarantined to make a suite green). Add the
    interim manual rule and the triage-class table (epic §7.2).
  - Acceptance: the doc is updated, cross-links from `delivery_process.md` CI triage are added, and
    no test changes.
- **Enforcement tooling (TA-MF-Q1)** → Part 3, trigger: the first real quarantine need.
- **Requires [D-MF]:** approval of the policy text replacing §6, and of the maximum expiry
  (proposed 14 days) and renewal rule (proposed: one renewal, then the owner decides).

### M2 · Oracle / spec review

- **Draft TA-M2-O2: Oracle-review step in the ticket workflow** (standard; agent-prompt change).
  - Scope: add mandatory `test_plan.md` fields to the `investigator` (proof kind, oracle source,
    expected effect, **oracle document section + parity-ledger id**). The oracle is the
    Bible/contract document. When an AC adds or changes an expectation, the plan requires the
    document and parity-ledger change first (plus a divergence entry if intentional), per CLAUDE.md's
    Authoritative Mechanics Rule; **no new status store**. A silent document (e.g. party), missing
    ownership, a cross-domain dispute or an intra-Bible conflict → escalate to the user.
    `done-checker` checks the fields are present.
  - Mode: advisory during the pilot.
  - Depends on: TA-MT-1. `rpg-feature-planning` answered on 2026-09-29: the oracle is a document;
    escalation goes to the user; no change to ledger/registry authority.
- **Requires [D-M2]:** approval of the oracle model (Bible/contract document + parity ledger, with
  the user as escalation point for silence, disputes and intra-Bible conflicts); advisory mode
  during the pilot; and **a decision on party**, which has no oracle document.

---

## Part 3 · Deferred, evidence-triggered tickets (not to be cut until the trigger fires)

| Placeholder | What | Trigger |
|---|---|---|
| TA-M2-O1 | Review-record format + mechanical validator (two-part freshness) | A feature team first asks to register a proof, **or** the registry epic ships its mechanism → test link |
| TA-M1-SF | Seeded-fault evaluation harness (fault-revealing recall) | Before the impact model is used to **skip** any test or lane, **or** the first recorded "CI selection failure" triage case |
| TA-M0a-CTX | Per-test coverage contexts (who-tests-what) | A recorded CI selection failure where the static inputs missed a dynamic dependency |
| TA-MF-Q1 | Quarantine marker, collection hook, required expiry check, report states | The first real case that needs quarantine (the nondeterminism class) |
| TA-M0a-ART | Upload JUnit artifacts from every CI job (today only `api-tools` uploads), for automatic report ingestion | When M0a-1's manual input step becomes the recurring bottleneck (today only `api-tools` uploads JUnit) |

## Part 4 · Test-hygiene finding (separate from R1)

**Finding [O], 2026-09-29.** Running the fast test tiers in a clean detached checkout of
`5d4e4a237` modified the tracked file `docs/brainstorm/mechanism_verification_view.md` (2 lines).
Its generator is `tools/mechanism_registry/generate_mechanism_verification_view.py` (default
output: that file). The two tests that invoke it (`tests/unit/tools/test_mechanism_registry.py:1024,
1039`) use `--check` or a `tmp_path` output, so **the actual writer is not yet identified**.

**Determination: it needs its own ticket.** A test that rewrites a tracked file breaks run
reproducibility and can put unrelated diffs into PRs. It is a different defect from R1's state
leak (environment/fixture class, epic §7.2).

| Placeholder | Title | Tier | Scope | Acceptance |
|---|---|---|---|---|
| **TA-HYG-1** | Find and stop the test run that rewrites `docs/brainstorm/mechanism_verification_view.md` | hotfix | Identify the writer (bisect the fast tiers with `git status` after each directory); redirect its output to `tmp_path` or make it `--check`-only; add a guard that fails if a test run leaves tracked files modified (e.g. `git status --porcelain` check in the test job, advisory first) | A clean checkout shows no tracked-file changes after the fast tiers; the guard catches a seeded write |
