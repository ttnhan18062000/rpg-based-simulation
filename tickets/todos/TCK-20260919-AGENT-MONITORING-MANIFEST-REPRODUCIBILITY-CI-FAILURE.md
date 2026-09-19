---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260919-AGENT-MONITORING-MANIFEST-REPRODUCIBILITY-CI-FAILURE
phase: open
date: 2026-09-19
tags: [observability, root-cause, debugging]
---

# TCK-20260919-AGENT-MONITORING-MANIFEST-REPRODUCIBILITY-CI-FAILURE

## Title
`tests/tools/test_agent_monitoring_manifest.py`'s two reproducibility tests are already failing
on `main` (confirmed, not caused by any recent PR) — `tools.jsonl` changes size between the two
manifest-build calls each test makes, implying something writes to it during the test itself

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found while triaging a real CI failure on `TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-
SEMANTICS`'s own PR (#222) — the "API / tools / logging" job failed. Per this repo's own CI
Triage discipline (never conclude root cause from a job name/guess): reproduced locally with the
exact CI command
(`pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability -m "not
slow and not extra_slow" --tb=short -q`) and got the identical 2 failures.

**Confirmed pre-existing and unrelated to that PR's own changes**, not assumed: `gh run list
--workflow=test.yml --branch=main` shows the last 5 CI runs on `main` itself are **all
`failure`**, including `ff00d95c4` (`#221`'s own merge commit, landed before this ticket's own
PR even started) and `ed0c77ff0` (`#219`'s merge). `gh run view` on the latest confirms the same
single job, "API / tools / logging," is the one failing each time.

**Root cause, traced not guessed**: both failing tests —
`test_manifest_cli_reproducible_byte_identical_across_two_runs` and
`test_manifest_run_against_real_corpus_produces_zero_diff` — call the manifest-building logic
against the real `agent-monitoring/` directory **twice** within the same test and assert the two
results are identical (byte-identical CLI output, or an unchanged content hash). The actual
failure detail: `tools.jsonl`'s recorded `size` field differs between the two calls (e.g.
`89210048` vs. `89209707` in one local repro) — meaning the real `agent-monitoring/data/*/
tools.jsonl` file's own byte size changed **between** the test's two manifest-build calls. Since
`build_manifest()` itself is asserted (and, on its own, appears) to be a pure read, this points to
something else writing to `tools.jsonl` concurrently with the test run itself.

**Locally, this is trivially explained**: an active Claude Code session's own `PostToolUse` hook
writes a new `tools.jsonl` row on every tool call, so running this test suite in a live,
actively-working session will always risk this exact race. **But CI runs are not supposed to have
a live agent session writing to the checkout during `pytest`** — the fact that the identical
failure reproduces on real CI runs (not just this session's own local repro) means either (a)
something in the CI job's own environment/setup writes to `agent-monitoring/` during the test
run (a monitoring hook active in CI that shouldn't be, or a leftover process), or (b) the test's
own real corpus fixture (`_REAL_AGENT_MONITORING_DIR`) is shared/mutated by another test running
concurrently or just before it in the same job (pytest-xdist parallelism, or ordering-dependent
state bleed), or (c) something else not yet identified. **Not yet root-caused past this point —
this ticket investigates which.**

## Scope
- Determine why `tools.jsonl` (or any file `build_manifest()` reads) changes size *during* a CI
  job run, when no live agent session should be writing to the checkout.
- Check whether these two tests run under any parallelism (pytest-xdist, `-n auto`, etc.) in the
  CI job's own configuration that could let another test's own write interleave with these tests'
  two-call comparison.
- Check whether any other CI step in the same job (or a hook wired into the CI environment itself)
  writes to `agent-monitoring/` during the test phase.
- Determine whether this has been silently failing on `main` for longer than the 5 runs checked
  here (check further back), and if so, since when/what changed.
- Fix the actual race, or make the tests robust to legitimate concurrent monitoring writes if the
  underlying behavior (something else writing during the test) turns out to be expected/
  unavoidable in the CI environment — the two are different conclusions, not assumed which applies.

## Out of Scope
- `TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS`'s own PR (#222) — not blocked
  on this; its own failure was traced to this pre-existing, unrelated main-branch issue, not its
  own changes, and reported as such rather than fixed inside that PR.
- Any change to `build_manifest()`'s own manifest-generation logic unless the investigation finds
  it genuinely is the one mutating something (currently believed innocent, per the test's own
  framing, but not yet independently re-verified here).

## Acceptance Criteria
- The real mechanism writing to `agent-monitoring/` during a CI run of these two tests is
  identified with direct evidence (not assumed).
- A fix (or a documented, deliberate test-robustness change) lands, and both tests pass on a real
  CI run against `main`, not just locally.
- If this has been failing on `main` for some time, state since when and why it wasn't caught
  sooner (e.g., was `API / tools / logging` not being checked, or was it failing intermittently
  and not noticed).

## Related Tickets
- `TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS` (closed — where this was found
  during CI triage; not the cause)

## Related Docs
- `docs/testing/regression_policy.md` — this failure is not yet documented there as a known
  environment-dependent flake; add it there once root-caused, or fix it outright.

## Related Stored Artifacts
_(none yet — not yet investigated)_

## Related Code Areas
- `tests/tools/test_agent_monitoring_manifest.py` (`test_manifest_cli_reproducible_byte_identical_across_two_runs`,
  `test_manifest_run_against_real_corpus_produces_zero_diff`)
- `tools/agent-monitoring/` (the manifest-building CLI/logic itself, `_MANIFEST_PATH`)
- `.github/workflows/test.yml` ("API / tools / logging" job definition, line ~329)

## Assumptions / Open Questions
- Whether this is a genuine CI-environment bug (something writes during the test that shouldn't)
  or a test-design gap (the test assumes exclusive access to a directory nothing guarantees is
  exclusive) — not yet determined, a real investigation question for whoever picks this up.

## Implementation Notes
_(none yet — not yet investigated)_

## Test Summary
_(none yet)_

## Files Changed
_(none yet)_

## Completion Summary
_(none yet — filed from real CI triage evidence: reproduced locally, confirmed pre-existing and
identical on 5 consecutive real `main`-branch CI runs, not caused by the PR that surfaced it.)_
