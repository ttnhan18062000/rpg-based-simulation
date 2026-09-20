# Plan — TCK-20260919-AGENT-MONITORING-MANIFEST-REPRODUCIBILITY-CI-FAILURE

## Decision

Narrow `test_manifest_cli_reproducible_byte_identical_across_two_runs` to a frozen snapshot of the
real corpus, rather than continue chasing a CI-runner-level mechanism that raw logs can't confirm
(see `investigation.md`). Leave `test_manifest_run_against_real_corpus_produces_zero_diff`
untouched — it asserts a different thing (`build_manifest()` itself doesn't mutate anything,
checked once before/after a *single* call) and is explicitly out of scope for narrowing per this
ticket's own text and peer review.

## Steps

1. **`tools/agent-monitoring/manifest.py`**: add an optional `--dir` argument to `main()`,
   defaulting to the real `agent-monitoring/` directory (`_AGENT_MONITORING_DIR`) so every existing
   invocation (with no `--dir`) is byte-for-byte unaffected. This is the minimal change needed to
   let a test point the CLI at an isolated directory — `build_manifest()` itself, the streaming
   logic, and the zero-mutation/streaming-guard contracts are untouched.
2. **`tests/tools/test_agent_monitoring_manifest.py`**:
   - `test_manifest_cli_reproducible_byte_identical_across_two_runs`: copy
     `_REAL_AGENT_MONITORING_DIR / "data"` into a `tmp_path` snapshot once, then invoke the CLI
     with `--dir <snapshot>` twice and compare stdout. Real content, frozen input, zero exposure to
     whatever mutates the live directory during the test's own ~1-2s window.
   - Add direct coverage for the new `--dir` flag itself (a synthetic tiny corpus proving `--dir`
     is actually honored, and a default-behavior test proving omitting `--dir` still scans the real
     corpus) — the fix's own correctness shouldn't rest solely on the reproducibility test passing
     by coincidence.
   - Add a one-line comment at the new test explaining why it diverges from the file's own
     top-of-file "never a tmp_path copy" framing, so a future reader doesn't read this as
     contradicting that rule (it doesn't — that rule protects the mutation/streaming-guard tests
     specifically, which are untouched).
3. Run the affected test file, then the full `tests/tools/` suite, to confirm no regression.
4. Write the corrected job-level CI history and findings into the ticket itself (not left for
   someone else to reconcile against the peer's relayed correction).
5. Close via the standard hand-orchestrated path: `stored_artifacts/`, `record_hand_orchestrated_
   closure.py`, `docs/REGISTRY.yaml` regeneration. No `docs/testing/regression_policy.md` update —
   the ticket's own Related Docs note said to add an entry there "once root-caused, or fix it
   outright"; this was fixed outright with a real code change, not left as an acknowledged ongoing
   flake, so the doc's "known environment-dependent flake" table doesn't apply.
