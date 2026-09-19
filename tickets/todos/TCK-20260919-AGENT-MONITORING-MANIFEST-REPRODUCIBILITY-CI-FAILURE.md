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

**The design question, per peer review — lead with this, not the environment-mechanism
question.** Both tests assert *determinism* over a value — `tools.jsonl`'s own recorded `size` —
that comes from a file the monitoring hook legitimately mutates on every tool call. Those two
facts cannot coexist stably, in CI or anywhere: a reproducibility assertion that includes a
live-mutating input is fragile by design, not environment-flaky. "What writes to it in a clean CI
runner" could burn real time chasing a writer that turns out to be the test's own harness (a
concurrent test, a fixture setup step, or `pytest`'s own collection touching the directory) rather
than anything actually wrong. **Answer the design question first** — should either test's own
comparison exclude `tools.jsonl`'s size (or any other field that's expected to change under normal
operation) before asking why it changed in this specific environment. The environment-mechanism
question (Scope's own first bullet) is still worth answering, but only after the design question
rules out "the test itself asks an unanswerable question."

**A red `main` is a problem in its own right, independent of this ticket's own fix size.** Five
consecutive main-branch CI failures means every PR lands with a failing check nobody caused,
whether or not the underlying test bug is small. This is the same failure shape (in effect, not in
cause) that killed the attribution ratchet: a red signal that's always red teaches people to stop
reading it, and then it stops catching anything real. This one is a genuine test defect rather
than an inverted metric, but the consequence of leaving it red is the same. This ticket's own
priority should reflect that blast radius, not just the size of the eventual fix.

## Scope
1. **Answer the design question first, per peer review**: should either test's own comparison
   include `tools.jsonl`'s `size` (or any field derived from a file the monitoring hook is
   expected to mutate during normal operation) at all? If the answer is no — the likely
   outcome — the fix is narrowing what the two tests compare (e.g. asserting the *structure*/
   schema of the manifest is reproducible, not every byte-for-byte field of a file that
   legitimately changes), not chasing a writer.
2. Only if (1) concludes the comparison is intentionally supposed to be exact and something is
   genuinely misbehaving: determine why `tools.jsonl` changes size *during* a CI job run, when no
   live agent session should be writing to the checkout — check test parallelism (pytest-xdist),
   any other CI step or hook that touches `agent-monitoring/` during the test phase, and whether
   this has been silently failing on `main` longer than the 5 runs checked here.
3. Fix the actual issue found in (1) or (2) — a narrower comparison, a real race fix, or both if
   both turn out to be real. Land it, and confirm both tests pass on a real CI run against `main`,
   not just locally.

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
