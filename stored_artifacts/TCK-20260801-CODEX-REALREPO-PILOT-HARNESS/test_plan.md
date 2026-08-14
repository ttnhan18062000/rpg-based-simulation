---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260801-CODEX-REALREPO-PILOT-HARNESS
artifact_type: test_plan
---

# Test Plan — TCK-20260801-CODEX-REALREPO-PILOT-HARNESS

## Regression Surface

- `tests/agent_codex_pilot_guardrails/`: request loading, enabled-surface evidence,
  sign-off, scratch rollback, and its no-live-execution static guard must stay unchanged
  and pass.
- `tests/agent_codex_pilot_executor/`: injected-root containment, atomic claims,
  prefix/exact-suffix behavior, and synthetic lifecycle proof must stay unchanged and pass.
- `tests/agent_replay_codex/`: replay remains scratch-only and preserves a real repo
  unchanged; no live-consent test is enabled.
- `tests/agent_codex_runtime_shadow/`, `tests/agent_codex_posttool_adapter/`,
  `tests/tools/test_monitoring_writer.py`, `tests/tools/test_agent_monitoring_manifest.py`,
  and `tests/tools/test_agent_ops_dashboard_ingest.py` cover reused components.

The new suite must have a session autouse guard snapshotting the actual project's
`.codex/config.toml`, `agent-monitoring/{runs,events,tools}.jsonl`, `pilot_requests/`,
and all ticket bytes.  It asserts exact equality at teardown.  All mutable fixtures are
tmp-path repository shapes; no test passes the actual root to a successful harness path.

## New Tests Required

1. **Structural boundary test.** AST-scan the new package: exactly the dedicated
   boundary module may import/call `subprocess`; no `os.system`, shell execution,
   `--dangerously-bypass-*`, hook registration, config writing, CLI main guard, or dynamic
   import of replay invoker exists.  The rest of the package has zero subprocess imports.
2. **Root and path containment ordering.** Parameterize the actual project root,
   a child path, symlinked root, traversal ID, absolute/escaped candidate/request/config
   path, and missing target.  Instrument request loader/claim/invoker to prove refusal
   occurs before any derived-path read, write, claim, or subprocess construction.
   Live-root admission is tested only with a refusal double; no test succeeds
   with or reads the project root through a harness path.
3. **Fail-closed preflight matrix.** Independently prove missing/malformed request,
   owner, rollback text, candidate, identity, surface evidence, claim evidence, baseline,
   expected-write policy, and containment evidence each returns a specific refusal with
   no writes.  Verify `"true"`, `"yes"`, and `"0"` never satisfy either authority gate.
4. **Authority ordering.** Unit-test that an otherwise valid scratch context cannot
   obtain `LivePilotAuthority` without *both* exact values; prove command construction
   is not reached on either failure. With both gates, execute one scratch-root
   fake-invoker call that records but never starts a process. Prove callers cannot
   inject a public authority constructor.
5. **Claim concurrency and terminalization.** Reuse/import the executor protocol and
   run real multiprocessing races against a scratch root: exactly one owner wins, active
   claims never expire by age, terminal replacement remains race-safe, and a different
   execution ID cannot terminalize or roll back another owner's claim.
6. **Baseline and allowlist proof.** Create a scratch repository with dirty initial
   ticket/monitoring state.  Verify permitted candidate lifecycle files and declared
   artifacts are accepted; an unrelated ticket, source file, real config, pilot request,
   unexpected artifact, monitoring deletion/reorder/rewrite, or unapproved append is
   rejected.  Include a negative test that a target historical ticket changed outside
   the exact three field edits is rejected.
   Reject caller-supplied, mutable, mismatched, and post-baseline-modified policy;
   prove post-run checks use the captured policy hash and exact transitions.
7. **Monitoring proof.** Seed distinct historical JSONL prefixes.  Verify accepted
   appends retain every prefix and satisfy the required ticket/run/execution/provider
   identity and event/tool sequence contract.  Verify altered, deleted, reordered, or
   extra suffix rows fail.  Use only fixture records, never `provider="codex"` in the
   project corpus.
8. **Rollback proof.** Against scratch configuration bytes, run enable/fake-invocation/
   rollback with an injected adapter.  Verify a single restoration returns exact
   baseline bytes, config is hook-free post-rollback, historical monitoring prefixes
   remain, expected lifecycle evidence remains, and unintended paths are unchanged.
   Verify a different execution identity cannot restore or terminalize the claim.
9. **Existing-invariant regressions.** Run all three existing package suites unchanged
   to prove the new capability neither imports nor relaxes their no-live/scratch-only
   contracts.

## Scoped Pytest Commands

```bash
.venv/bin/python -m pytest -q \
  tests/agent_codex_realrepo_pilot_harness \
  tests/agent_codex_pilot_guardrails \
  tests/agent_codex_pilot_executor \
  tests/agent_replay_codex \
  tests/agent_codex_runtime_shadow \
  tests/agent_codex_posttool_adapter \
  tests/tools/test_monitoring_writer.py \
  tests/tools/test_agent_monitoring_manifest.py \
  tests/tools/test_agent_ops_dashboard_ingest.py
```

Run static containment tests last.  Do not set either live-consent environment variable
or request `real_codex_replay`; any real invocation is outside this ticket.

## Acceptance-Criteria Coverage

| Acceptance criterion | Tests |
| --- | --- |
| Scratch-only test behavior / project-root refusal | 1–4 plus suite guard |
| Missing evidence fails before writes | 2–4 |
| Independent future live authority, never exercised here | 1, 3–4 |
| Allowlisted lifecycle writes and monitoring prefixes | 6–7 |
| Rollback is contained and verified | 5, 8 |
| Existing non-live packages unchanged/passing | 9 |

## Anti-Drift Guards

- A fake invoker may record attempted arguments only; it must not start a process.
- Test helpers must build a minimal tmp-path git repository and never copy or mutate the
  project working tree.
- A green scratch "live-shaped" test is evidence of harness mechanics, not consent to
  run a pilot.  No test may create hooks, alter `.codex/config.toml`, or emit a real
  provider-bearing monitoring record.
