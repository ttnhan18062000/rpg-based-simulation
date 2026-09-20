# Investigation — TCK-20260919-AGENT-MONITORING-MANIFEST-REPRODUCIBILITY-CI-FAILURE

## 1. Correcting the ticket's own "5 consecutive failures" claim

`gh run list --workflow=test.yml --branch=main` reports one `conclusion` per *run*; a run fails if
*any* job in it fails. Re-derived job-level conclusions directly for the `API / tools / logging`
job specifically, across 6 real runs spanning the 4 most recent distinct commits on `main`:

```
gh api repos/ttnhan18062000/rpg-based-simulation/actions/runs/<id>/jobs \
  --jq '.jobs[] | select(.name=="API / tools / logging") | .conclusion'
```

| Run ID | Commit | Conclusion |
|---|---|---|
| 35432848568 | ff00d95c4 (#221 merge) | failure |
| 35429865142 | ed0c77ff0 (#219 merge, later) | success |
| 35424299135 | ed0c77ff0 (#219 merge, earlier) | failure |
| 35320799248 | 74c11ceb7 (later) | success |
| 35317812398 | 74c11ceb7 (earlier) | success |
| 35302658970 | 68fad705b | success |

2-of-6 job-level failures. `ed0c77ff0` itself produced both a failure and a success on separate
runs — this alone rules out "the checked-out commit deterministically fails," since nothing in the
commit's own content changed between those two runs of the same job.

## 2. Auditing every writer call site in the CI job's own test scope

The CI job runs `pytest tests/api tests/cli tests/tools tests/logging tests/engine
tests/observability`. Searched all 6 directories for any reference to `record_run.py`,
`record_events.py`, `post_tool_hook.py`, `writer.py`, or `agent-monitoring` (34 matching files
total across the whole repo; narrowed to the 6 in-scope directories, `tests/cli/test_lab_cli.py`
was the only unrelated hit, a coincidental `"record_events"` config key name).

Every call site that invokes the writer scripts/functions was checked directly (not sampled):
- All `subprocess.run(...)` calls pass `cwd=tmp_path` (or an explicit tmp fixture dir) or
  `monkeypatch.chdir(tmp_path)` before calling `.main()` in-process.
- `post_tool_hook.py`'s own target path (`Path("agent-monitoring/data") / iso_week /
  "tools.jsonl"`) is process-cwd-relative, not `__file__`-relative — so a subprocess launched with
  `cwd=tmp_path` genuinely cannot reach the real repo's `agent-monitoring/`.
- The only calls using `cwd=<repo root>` are `TestExitCodeContract` cases in
  `test_record_run.py`/`test_record_events.py` that pass a record with a `None`/missing required
  field. Both `record_run.py::main()` and `record_events.py::main()` call `validate_record()` and
  `sys.exit(1)` *before* reaching the write — confirmed by reading the exact `main()` source, not
  inferred from the test's own name.
- `writer.py::write_line`/`write_lines` open the target with `"a"` (or an `O_APPEND` fd) —
  structurally append-only. This rules out the writer itself as the source of the specific
  "89210048 → 89209707 (341 bytes smaller)" symptom in the ticket's own original text: an
  append-only writer cannot shrink a file under any of its own code paths.

Conclusion: no stray writer exists in this repo's own test suite that could explain a live mutation
of the real `agent-monitoring/` corpus during this specific CI job.

## 3. Hermetic local reproduction

This session's own live Claude Code hook writes to the checkout on every tool call, which would
make any local repro run *inside* this worktree indistinguishable from the CI-only failure (the
ticket's own text already acknowledges this: "Locally, this is trivially explained"). To rule that
out, cloned the merged branch tip into a plain `git clone` outside any Claude Code worktree
(`/home/u24desktop/scratch/repro_manifest_ci` — a session's own hook cannot write into a directory
it isn't running against) and ran the literal CI command:

```
pytest tests/api tests/cli tests/tools tests/logging tests/engine tests/observability \
  -m "not slow and not extra_slow" --tb=short -q
```

Result: **2942 passed, 0 failed**, 385s. The failure did not reproduce outside a live-session
environment, and no code-level cause was found — this leaves a CI-runner-level, environment-only
cause (untraceable further given the TLS block on raw job logs, see Related Docs' CI Triage
section for that block being a known, pre-existing sandbox/runner limitation, not specific to this
ticket) as the most likely remaining explanation, recorded honestly as unresolved rather than
guessed at.

## 4. Fix direction

Given (1) confirms this is a real but rare CI-runner-level flake, not a deterministic bug, and (2)
found no writer to fix, the actionable fix is exactly what the ticket's own Scope item 1 predicted:
narrow what `test_manifest_cli_reproducible_byte_identical_across_two_runs` depends on, since its
real intent ("the manifest CLI is deterministic for the same input") never required also proving
"the live real corpus never changes between two subprocess calls." See `plan.md` for the exact
change and why `test_manifest_run_against_real_corpus_produces_zero_diff` was deliberately left
untouched.
