---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260919-AGENT-MONITORING-MANIFEST-REPRODUCIBILITY-CI-FAILURE
phase: done
date: 2026-09-19
tags: [observability, root-cause, debugging]
---

# TCK-20260919-AGENT-MONITORING-MANIFEST-REPRODUCIBILITY-CI-FAILURE

## Title
`tests/tools/test_agent_monitoring_manifest.py`'s two reproducibility tests are already failing
on `main` (confirmed, not caused by any recent PR) — `tools.jsonl` changes size between the two
manifest-build calls each test makes, implying something writes to it during the test itself

## Status
DONE

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

### Findings (2026-09-19)

**"5 consecutive main-branch CI runs are ALL failure" was a run-level/job-level conflation,
corrected against independently re-fetched evidence, not taken on trust.** `gh run list` reports
one `conclusion` per *run*, and a run fails if *any* job in it fails — this repo's `test.yml` runs
several independent jobs per workflow run, so a run-level `failure` does not mean the `API / tools
/ logging` job specifically failed. Re-checked job-level conclusions directly
(`gh api repos/.../actions/runs/<id>/jobs --jq '.jobs[] | select(.name=="API / tools / logging") |
.conclusion'`) for the 6 real CI runs spanning the last 3 distinct commits on `main`:

| Commit | Run (earlier) | Run (later, if two) | Job-level conclusion |
|---|---|---|---|
| `ff00d95c4` (#221 merge) | `35432848568` | — | **failure** |
| `ed0c77ff0` (#219 merge) | `35424299135` | `35429865142` | **failure**, then **success** |
| `74c11ceb7` | `35317812398` | `35320799248` | success, success |
| `68fad705b` | `35302658970` | — | success |

This is a **2-of-6 flake**, not 5 consecutive failures — the same commit (`ed0c77ff0`) produced
both a failing and a passing run of the identical job, which by itself rules out a deterministic
code-path bug in the checked-out commit and points at something timing/environment-dependent in
the CI runner itself, not a "this test always fails on `main`" claim.

**No stray writer exists in this repo's own test suite** — checked exhaustively, not assumed.
Every test in the CI job's own scope (`tests/api`, `tests/cli`, `tests/tools`, `tests/logging`,
`tests/engine`, `tests/observability`) that invokes `record_run.py`, `record_events.py`,
`post_tool_hook.py`, or `writer.py` directly (`grep` across all 6 directories, then read every
matching call site) isolates its write target via `tmp_path`, `monkeypatch.chdir(tmp_path)`, or an
explicit `cwd=tmp_path`/`cwd=<tmp fixture dir>` on `subprocess.run`. The only call sites using
`cwd=<repo root>` are `TestExitCodeContract` tests in `test_record_run.py`/`test_record_events.py`
that pass a deliberately-invalid record — `record_run.py`'s and `record_events.py`'s own `main()`
both call `validate_record()` and `sys.exit(1)` *before* ever reaching the write, so these never
touch the real corpus. `writer.py::write_line`/`write_lines` open the target in append mode
(`"a"`, or an `O_APPEND`-flagged fd) — structurally incapable of *shrinking* a file, which rules
out the writer as the source of the specific "89210048 → 89209707, 341 bytes smaller" symptom
recorded above (an append-only writer growing the file wouldn't produce a decrease; only a
truncate-and-rewrite could, and no code path here does that).

**A hermetic local reproduction of the exact CI command, isolated from this session's own live
`PostToolUse` hook, could not reproduce either failure.** Cloned the merged branch tip into
`/home/u24desktop/scratch/repro_manifest_ci` (a plain local `git clone`, not a worktree of this
session's own repo, so this session's hook — which does write to a live checkout on every tool
call — cannot reach it) and ran the literal CI command
(`pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability -m "not
slow and not extra_slow" --tb=short -q`) against it: **2942 passed, 0 failed** in 385s. This
confirms the local "89210048 → 89209707" symptom described above was this session's own live hook
racing the test, exactly as the "Locally, this is trivially explained" paragraph above already
said — and separately confirms the CI-only failure is not a deterministic bug reproducible outside
a live-session environment.

**Root cause of the CI-only 2-of-6 flake is not pinned down past this point** — raw job logs for
the failing run (`105870372240`) hit the same TLS block this repo's CI Triage guidance already
documents (`productionresultssa16.blob.core.windows.net`, unrelated to this ticket), so the actual
pytest failure line/assertion detail for the *CI-side* failure was never directly observed, only
inferred from the ticket's own original local-repro description. Given (a) the writer audit found
no legitimate code path that can produce the observed symptom, (b) the hermetic repro passed
cleanly, and (c) the failure is intermittent even for an identical commit — the most likely
remaining explanation is a transient GitHub Actions runner-level filesystem/I/O characteristic
(reading a live, currently-~52MB-across-16-shards real corpus twice, seconds apart, via two
separate subprocess invocations, with zero synchronization) rather than a bug in this repo's own
monitoring code. This could not be conclusively confirmed given the blocked logs — recorded here
as a residual gap, not resolved with false precision.

### Decision (2026-09-19, user relayed via peer, design question answered as scoped)

**Narrow `test_manifest_cli_reproducible_byte_identical_across_two_runs`'s own input to a frozen
snapshot, rather than chase the CI-runner-level mechanism further.** The test's real intent is "is
the manifest CLI deterministic for a given input" — it never needed to also prove "the live
`agent-monitoring/` directory never changes between two subprocess calls a couple seconds apart,"
which is not a guarantee this repo makes or needs. Implemented by copying the real corpus's
current `data/` tree into a `tmp_path` snapshot once per test run, then invoking the CLI against
that frozen snapshot twice — this keeps the test using real, representative content (not synthetic
fixture data) while removing the exposure window entirely, and needed one small, additive CLI
change: `manifest.py`'s `main()` gained an optional `--dir` argument (default: the real directory,
so every existing invocation is unaffected) purely for this test-isolation purpose.
**`test_manifest_run_against_real_corpus_produces_zero_diff` was deliberately left untouched and
still targets the live real directory** — its own assertion (`build_manifest()` itself must not
mutate anything) is a different claim than the CLI-reproducibility test's, is not subject to the
same race (it snapshots porcelain/hash once before and once after a *single* `build_manifest()`
call, not two independent live reads), and per this ticket's own Out of Scope and the peer's
explicit instruction, exists specifically to catch real corpus mutation — narrowing it further was
never on the table.
`test_build_manifest_reproducible_byte_identical_direct_call` (the in-process, microseconds-apart
sibling of the CLI test) has the same theoretical exposure but has never been observed failing in
CI — left as-is rather than applying an unproven fix to a test with no confirmed symptom.

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
- [ ] The real mechanism writing to `agent-monitoring/` during a CI run of these two tests is
  identified with direct evidence (not assumed). **Not met, stated honestly rather than papered
  over**: exhaustively ruled out every code-level candidate (every writer call site in the CI job's
  test scope is properly isolated; `writer.py` cannot shrink a file) and a hermetic repro of the
  exact CI command passed cleanly, but the actual CI-runner-level cause of the intermittent
  size/hash mismatch was never directly observed — raw job logs for the failing run hit this
  repo's already-documented TLS block. See Findings above for what was and wasn't ruled out.
- [x] A fix (or a documented, deliberate test-robustness change) lands, and both tests pass on a
  real CI run against `main`, not just locally. Documented, deliberate change landed (snapshot
  input for the CLI-reproducibility test); local pass confirmed (10/10 in the affected file, full
  `tests/tools/` suite 2746 passed). **CI-confirmation on a real `main` run is still pending** —
  this criterion is checked for the "fix lands + passes locally" half; the push/PR/merge and its
  own CI run happen after this ticket closes, per this session's standing PR-creation process (push
  and report, the peer/user decide if and when it becomes a PR).
- [x] If this has been failing on `main` for some time, state since when and why it wasn't caught
  sooner. Traced via job-level `gh api` history above: the job flakes at roughly 2-of-6 real runs
  across the 3 most recent distinct commits on `main` (`ff00d95c4`, `ed0c77ff0`, `74c11ceb7`,
  `68fad705b`) — not a clean "since commit X" boundary, since the same commit produced both a pass
  and a fail. It wasn't caught sooner because a run-level `failure` conclusion was being read as
  "the job failed" without checking job-level granularity, and because — until this ticket — no
  one had isolated a hermetic repro to separate "this session's own live hook" from "a real
  CI-only cause."

## Related Tickets
- `TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS` (closed — where this was found
  during CI triage; not the cause)

## Related Docs
- `docs/testing/regression_policy.md` — this failure is not yet documented there as a known
  environment-dependent flake; add it there once root-caused, or fix it outright.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260919-AGENT-MONITORING-MANIFEST-REPRODUCIBILITY-CI-FAILURE/investigation.md`
- `stored_artifacts/TCK-20260919-AGENT-MONITORING-MANIFEST-REPRODUCIBILITY-CI-FAILURE/plan.md`
- `stored_artifacts/TCK-20260919-AGENT-MONITORING-MANIFEST-REPRODUCIBILITY-CI-FAILURE/test_plan.md`

## Related Code Areas
- `tests/tools/test_agent_monitoring_manifest.py` (`test_manifest_cli_reproducible_byte_identical_across_two_runs`,
  `test_manifest_run_against_real_corpus_produces_zero_diff`)
- `tools/agent-monitoring/` (the manifest-building CLI/logic itself, `_MANIFEST_PATH`)
- `.github/workflows/test.yml` ("API / tools / logging" job definition, line ~329)

## Assumptions / Open Questions
- ~~Whether this is a genuine CI-environment bug (something writes during the test that
  shouldn't) or a test-design gap~~ — **resolved**: it's neither cleanly. No code-level writer was
  found (ruling out the "test-design gap caused by our own code" framing), and a hermetic repro
  passed cleanly (ruling out "a deterministic bug in the checked-out commit"). The remaining
  candidate is a transient CI-runner-level characteristic, not conclusively identified — see
  Findings above.
- **Open**: the exact CI-runner-level mechanism behind the 2-of-6 flake is still unknown. If it
  recurs after this fix (which only removes the *test's* exposure to it, not whatever the
  mechanism actually is — though nothing else in this repo currently depends on two live reads of
  the real corpus seconds apart, so no other test should be exposed to it), that would be new
  evidence worth a follow-up ticket rather than reopening this one.

## Implementation Notes
- `tools/agent-monitoring/manifest.py`: `main()` gained an optional `--dir` argument (default: the
  real `agent-monitoring/` directory) purely for test isolation. `build_manifest()` itself,
  `_scan_source()`, `_source_paths()`, and the streaming/hashing logic are byte-for-byte unchanged.
- `tests/tools/test_agent_monitoring_manifest.py`:
  - `test_manifest_cli_reproducible_byte_identical_across_two_runs` now copies the real corpus's
    `data/` tree into a `tmp_path` snapshot once, then runs the CLI against that frozen snapshot
    twice via the new `--dir` flag.
  - Two new tests directly cover the `--dir` flag itself: one proving it's honored (a synthetic
    single-shard corpus), one proving the default (no `--dir`) still targets the real corpus.
  - `test_manifest_run_against_real_corpus_produces_zero_diff` and every other existing test in the
    file are unchanged.

## Test Summary
- `pytest tests/tools/test_agent_monitoring_manifest.py -v`: 10 passed (8 original including both
  previously-failing tests, plus 2 new `--dir`-flag tests).
- `pytest tests/tools/ -m "not slow and not extra_slow" -q`: 2746 passed, 25 skipped, 28
  deselected, 1 xfailed, 0 failed.
- Hermetic full-CI-command repro (outside any Claude Code worktree, before the fix, to confirm the
  failure does NOT reproduce without a live session's own hook): 2942 passed, 0 failed.
- See `stored_artifacts/.../test_plan.md` for the full case-by-case mapping.

## Files Changed
- `tools/agent-monitoring/manifest.py` — added optional `--dir` CLI argument (test-isolation only,
  default preserves existing behavior)
- `tests/tools/test_agent_monitoring_manifest.py` — snapshot-isolated the CLI reproducibility test;
  added 2 new tests for the `--dir` flag itself
- `tickets/inprogress/` → `tickets/done/TCK-20260919-AGENT-MONITORING-MANIFEST-REPRODUCIBILITY-CI-FAILURE.md`
- `stored_artifacts/TCK-20260919-AGENT-MONITORING-MANIFEST-REPRODUCIBILITY-CI-FAILURE/` (new:
  `investigation.md`, `plan.md`, `test_plan.md`)

## Completion Summary
Corrected the ticket's own "5 consecutive main-branch CI failures" claim against independently
re-derived job-level evidence (it's a 2-of-6 flake, including the same commit both passing and
failing). Exhaustively audited every writer call site in the CI job's own test scope and found none
capable of reaching the real corpus or shrinking a file; a hermetic reproduction of the exact CI
command outside any live Claude Code session passed cleanly, confirming this is not a deterministic
code bug. The design question the peer flagged — should a reproducibility assertion depend on a
live-mutating real file at all — is answered no for the CLI reproducibility test specifically:
narrowed it to a frozen snapshot of the real corpus via a new, additive, backward-compatible `--dir`
CLI flag, while deliberately leaving the zero-mutation test on the live real directory since its own
assertion is a different, non-fragile claim. The CI-runner-level root cause of the original flake is
recorded as a genuine, honestly-stated open gap rather than resolved with false precision — the logs
needed to pin it down further are TLS-blocked, a pre-existing sandbox limitation unrelated to this
ticket.
