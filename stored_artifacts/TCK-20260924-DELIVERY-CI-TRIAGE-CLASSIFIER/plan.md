---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20260924-DELIVERY-CI-TRIAGE-CLASSIFIER
date: 2026-09-24
tags: [delivery, ai, process-improvement]
---

# Plan — TCK-20260924-DELIVERY-CI-TRIAGE-CLASSIFIER

## Module: `tools/delivery/ci_triage_classifier.py`

Categories: `REAL_REGRESSION` (1), `DOCUMENTED_FLAKE` (2), `BASELINE_DRIFT` (3), `ENVIRONMENT` (4),
`UNCLASSIFIED`. Each classification is `{"category", "remedy", "evidence"}`.

### Functions
- `parse_regression_policy_soft_paths(policy_path) -> set[str]` — backtick-quoted paths from the
  `## 3. Soft Monitors` section only (investigation.md decision).
- `parse_workflow_job_paths(workflow_path) -> dict[str, list[str]]` — job name -> the `pytest`
  argument paths its `run:` step invokes, parsed from `.github/workflows/test.yml`.
- `_is_tls_blocked_reason(reason) -> bool` — reuses `pr_status._TLS_BLOCK_KEYWORDS` directly.
- `classify_absent(reason) -> dict` — category 4, remedy varies on `CONFLICTING` vs. generic.
- `classify_unknown(reason) -> dict` — category 4 if TLS-blocked, else `UNCLASSIFIED`.
- `classify_failing_job(job, job_paths, soft_paths, changed_files, known_baseline_drift_paths,
  known_parked_jobs) -> dict` — per-job classification per investigation.md decisions 1–3, with a
  `parked` flag when the job name matches `known_parked_jobs`.
- `classify(payload, run_command=default_run_command, base_ref="origin/main",
  policy_path=..., workflow_path=..., known_baseline_drift_paths=frozenset({
  "tests/tools/test_parity_index_baseline.py"}), known_parked_jobs=frozenset({"Slow regression"}))
  -> dict` — dispatches on `payload["verdict"]`; for `FAILING`, classifies every job in
  `failing_jobs` and resolves to `UNCLASSIFIED` overall if per-job categories disagree, else that
  shared category with all jobs' evidence combined.

No test file, baseline, gate, or assertion is ever written by any function here — this module reads
`payload`, `policy_path`, `workflow_path`, and `git diff --name-only` only.

### CLI
```
python3 tools/delivery/ci_triage_classifier.py --payload-file <pr_status --json output> [--json]
```
Reads a `pr_status.py`-shaped payload from a file (or stdin), classifies, prints the result. Exit 0
always, matching the tool's own advisory contract.

## Tests: `tests/tools/test_delivery_ci_triage_classifier.py`
1. AC1 — a fixture `FAILING` payload whose job's covered path is listed in a fixture
   `regression_policy.md` -> `DOCUMENTED_FLAKE`, remedy says not to code-fix.
2. AC2 — a fixture `FAILING` payload whose job's covered path is in the (faked) changed-files list
   and not in the soft-monitor or baseline-drift lists -> `REAL_REGRESSION`, remedy says file a
   hotfix ticket.
3. AC3 — a fixture whose job's covered path matches the known baseline-drift pattern ->
   `BASELINE_DRIFT`, remedy explicitly says "never a silent edit."
4. AC4 — an `ABSENT` payload with `reason` containing `CONFLICTING` -> `ENVIRONMENT`, remedy names
   resolving the conflict and states re-trigger/force-push will not help.
5. AC5 — a fixture with no soft-monitor match, no baseline-drift match, and no changed-file overlap
   -> `UNCLASSIFIED`. A second fixture with two failing jobs classifying differently -> also
   `UNCLASSIFIED` overall (investigation.md decision 3).
6. AC6 — a fixture `regression_policy.md` altered to add/remove a path, observed to change the
   classification — proves the module reads it at runtime, not a hardcoded copy.
7. AC7 — a `FAILING` payload is classified, then `git status --short` is asserted unchanged.
8. AC8 — every classification path (all 5 categories) asserted to produce exit code 0 via the CLI.
9. AC9 — recorded once run.

## Out-of-scope guardrails
- No call to `gh`/log-fetching anywhere in this module — it consumes `pr_status.py`'s own output.
- No ticket filing, no test/gate/assertion edits, no job re-run — advisory text only.
