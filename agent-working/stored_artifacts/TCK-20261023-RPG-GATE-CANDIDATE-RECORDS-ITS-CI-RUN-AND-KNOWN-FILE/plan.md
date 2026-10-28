---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261023-RPG-GATE-CANDIDATE-RECORDS-ITS-CI-RUN-AND-KNOWN-FILE
phase: done
date: 2026-10-26
tags: [testing, regression, simulation-quality]
---

# TCK-20261023-RPG-GATE-CANDIDATE-RECORDS-ITS-CI-RUN-AND-KNOWN-FILE: plan

Files: tools/test_architecture/rpg_gate_candidate.py, tools/test_architecture/rpg_gate_baseline.py, docs/plans/test_architecture/reference/rpg_gate_baseline_format.md, tests/unit/tools/test_rpg_gate_candidate.py, tests/unit/tools/test_rpg_gate_baseline.py. No workflow change.

1. Candidate: add `ci_record(env)` (null unless the four GITHUB_* variables are all non-empty), `file_sha256(path)`, and keyword-only `known_file_sha256` (required) and `env` (default os.environ) on `build_candidate`; provenance gains `known_file_sha256` and `ci`; the CLI hashes the `--known` bytes. Docstring updated.
2. Baseline: `MAIN_REF`, `CI_FIELDS`; `rebaseline()` runs the candidate's provenance through `_lint_ci_provenance` (after the evidence_only check, the one rule shared with the lint; testing-planner's review tweak) and refuses on any problem (null/missing/empty ci, ci.ref other than refs/heads/main, missing or malformed known_file_sha256), telling the caller to re-dispatch the gate on main; `_lint_provenance(prov, version)` calls `_lint_ci_provenance` for int version >= 2. Docstring and module text updated.
3. Doc: "Candidate and recording" states both fields, the refusal, the v1 exemption, and that a local rebuild is for inspection only.
4. Tests (see test_plan.md). Existing fixtures gain a main CI run and a known hash; no assertion removed.
5. Scope guards: v1 json untouched; no GitHub API call; no override flag; no workflow edit.

AC map: AC1 candidate tests; AC2 rebaseline tests (null, missing, empty run id, feature branch, PR ref, empty ref; accepted main; evidence_only still refused); AC3 lint tests + committed v1 lint; AC4 doc + docstrings; AC5 the two test files pass, nothing weakened.
