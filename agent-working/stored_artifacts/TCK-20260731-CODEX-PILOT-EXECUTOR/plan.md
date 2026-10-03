---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260731-CODEX-PILOT-EXECUTOR
artifact_type: plan
---

# Plan — TCK-20260731-CODEX-PILOT-EXECUTOR

## Implementation Decision

Create a library-only `tools/agent_codex_pilot_executor/` that simulates one
Codex pilot lifecycle exclusively below a caller-injected scratch root.  It is
an integration boundary around the existing guardrails, PostToolUse adapter,
monitoring validators/writer, manifest gate, and dashboard reader; it is not a
second writer, hook implementation, config toggle, or Codex launcher.

The failure-recovery representation is a retained terminal claim marker plus a
Linux advisory per-ticket transition lock. `claims/<ticket_id>.json` has state
`active`, `completed`, or `failed`; an open `claims/<ticket_id>.json.lock` file
descriptor holds `fcntl.flock(LOCK_EX)` across every marker read/replace/
terminalization. Kernel release handles a crashed owner; active claims are
never auto-reclaimed. Malformed content fails closed.

## Ordered Implementation Steps

1. Add the package boundary and containment model.

   - Add `tools/agent_codex_pilot_executor/__init__.py`, `models.py`,
     `errors.py`, and `paths.py`.
   - Define an immutable simulation context containing only injected scratch
     paths, fixed identity/timestamps, the declared synthetic surface, and the
     captured PostToolUse fixture.  Do not accept a config path, command,
     environment mutation capability, or real repository output path.
   - Validate `TICKET_ID_PATTERN` through the existing adapter identity helper
     before constructing any ticket-derived path, with zero I/O. Resolve every
     configured request, claim, and claim-lock path only after this check and
     assert it remains contained by its resolved scratch parent before use.
     Require the scratch root to be
     outside the repository root; reject the repository root, its
     `agent-monitoring/` directory, symlink escapes, and every target that is
     not contained by the resolved scratch root.  Apply this check before
     request parsing, claim creation, adapter invocation, or writer use.
   - Keep the package library-only: no `__main__`, CLI parser, subprocess,
     shell, network, replay-invoker, config-toggle, or `codex` dependency.

2. Implement deterministic preflight by composing the established guardrails.

   - Add `preflight.py` which loads only
     `<scratch>/pilot_requests/<ticket_id>.yaml` through
     `agent_codex_pilot_guardrails.ticket_selection.select_pilot_candidate`.
     Require the loaded `PilotRequest.ticket_id` to equal the requested ID.
   - Reuse `agent_codex_posttool_adapter.identity.validate_identity` for the
     fixed `provider="codex"`, ticket ID, and execution ID; do not duplicate
     its regexes.
   - Reuse
     `agent_codex_pilot_guardrails.enabled_surface.assert_enabled_surface_subset`
     with the exact fixture declaration `{PostToolUse}` and
     `{write_line, write_lines}`.  This validates evidence only; it never
     reads or changes `.codex/config.toml`.
   - Return typed, gate-specific refusal results/errors for containment,
     request, identity, and surface failures.  Preflight failures must occur
     before baseline capture, claim writes, or monitoring writes.

3. Implement scratch-only atomic claims and terminal recovery.

   - Add `claims.py` with executor-owned marker and transition-lock locations.
     Use a fresh, scratch-scoped Linux `fcntl.flock(LOCK_EX)` transition lock
     held by file descriptor for the entire transition; do not import private
     writer internals or use age-based lock-file deletion.
   - Under the transition lock, parse the marker: absent creates active;
     active/malformed/unrecognized refuses; verified completed/failed is
     atomically replaced through a same-directory temporary file and
     `os.replace`. Kernel lock release handles process crash; active-claim
     staleness never is.
   - Terminalization acquires the same lock, verifies active ownership by
     ticket and execution ID, then atomically replaces the marker with
     completed/failed. Ownership mismatch refuses without modifying evidence.

4. Compose the synthetic monitoring lifecycle without broadening any real
   writer surface.

   - Add `simulation.py` and a narrow dependency-loading module, if needed,
     to reuse `record_run.validate_record` / `compute_duration_s`,
     `record_events.validate_record`, the guardrail baseline functions, and
     `agent_codex_posttool_adapter.writer_bridge.write_line`.  Use the shared
     monitoring writer's existing `write_line` / `write_lines` functions for
     all scratch append operations; do not copy append, locking, payload,
     redaction, or identity logic.
   - After preflight and a successful claim, seed all three scratch monitoring
     JSONL files, then capture the scratch monitoring
     baseline.  Build exactly one valid terminal run record for
     `workflow="codex-pilot-simulation"`, at least two increasing-sequence
     event records (including the synthetic PostToolUse event), and one tool
     record by calling
     `agent_codex_posttool_adapter.adapter.process_post_tool_use` in-process.
     Pass a locally injected adapter-gate mapping with the exact required
     value; never set process environment variables.
   - Use one common `run_id`, `ticket_id`, `provider="codex"`, and
     `execution_id` in all rows.  Set the tool row's `seq` to the declared
     PostToolUse event sequence.  Validate run/event records before writing;
     require each shared-writer call and the adapter call to report success.
   - Declare the complete ordered expected suffix for each of runs, events,
     and tools before writing.  On success, use the existing manifest gate to
     prove historical prefixes are byte/line-preserved and independently
     compare each post-baseline suffix exactly to its declared rows.  Then
     use `DashboardCache(repo_root=scratch_root)` and its public readers to
     prove run, provider/execution identity, timeline, and attached tool
     visibility before terminalizing the claim `completed`.
   - Catch an injected or real write/proof failure, terminalize the owned
     claim as `failed`, return a non-success result identifying the failed
     boundary, and never describe a partial physical suffix as a completed
     lifecycle.

5. Add focused scratch-only regression coverage.

   - Add `tests/agent_codex_pilot_executor/conftest.py` with an autouse guard
     that snapshots real `agent-monitoring/{runs,events,tools}.jsonl`,
     `.codex/config.toml`, and the real ticket tree; assert byte equality at
     teardown.  Every writable fixture must be under `tmp_path`.
   - Add containment/structure tests that AST-scan the new package for CLI,
     subprocess/system calls, `codex` invocation, replay-invoker/config-toggle
     imports, and config writes; test repository-root, real-monitoring,
     symlink, and outside-root refusal before dependencies are called.
   - Add parametrized preflight tests for traversal-shaped, missing, malformed,
     or mismatched request,
     invalid identity, and widened surface.  Assert a distinct gate outcome
     and no claim or scratch JSONL mutation for each case.
   - Add multiprocessing claim tests using simultaneous attempts, including
     replacement of an existing terminal marker: exactly
     one acquisition for the same ticket, including two `codex` attempts;
     independent ticket acquisition succeeds; active and malformed claims
     refuse.  Add completed/failed replacement and injected lifecycle-failure
     recovery tests plus terminalize-without-ownership refusal, asserting an
     unambiguous terminal marker. Hold one owner past the former stale-lock
     interval and prove a contender cannot enter until release or process exit.
   - Add lifecycle tests proving shared validator/writer/adapter/guardrail
     reuse, identity coherence, event ordering, tool-to-event sequence join,
     adapter redaction, prefix preservation, exact suffix comparison, and
     rejection of altered/deleted/reordered historical lines or unexpected
     suffix rows.  Add dashboard ingestion tests against a minimal scratch
     ticket tree, including rejection of a tool-only corpus as a completed run.

6. Record the durable operational boundary and run the scoped checks.

   - Update `docs/ai/monitoring_writer_decision.md` with the agreed
     identity-less pre-pilot logging policy; scratch-only executor lifecycle,
     claim, prefix, and terminal-recovery semantics; and the invariant that a
     real provider-bearing Codex record still requires separate human
     authorization.  Do not imply the scratch adapter gate authorizes a live
     append.
   - Run the scoped suite from `test_plan.md`, with the executor AST
     containment test last.  Record the known unrelated provider-count
     baseline failure if encountered; do not change that assertion in this
     ticket.
   - Update the relevant `docs/parity_ledger/infrastructure.yaml` entry only
     if the normal Parity phase identifies a concrete agent-tooling behavior
     change needing an INFRA ledger record; do not create simulation-state
     parity entries.

## Dependency Map

```text
paths/models/errors
       ↓
preflight (existing manifest + identity + surface guardrails)
       ↓
atomic claim
       ↓
synthetic lifecycle (existing validators + writer + adapter + manifest gate)
       ↓
exact suffix proof + DashboardCache proof
       ↓
claim terminalization → docs + scoped regression suite
```

## Acceptance-Criteria Map

| Acceptance criterion | Implementation steps | Verification |
| --- | --- | --- |
| Scratch-only, no live/config/subprocess path, component reuse | 1, 4 | Structure/AST and dependency-spy tests |
| Deterministic, gate-specific preflight refusal | 1–2 | Parametrized preflight and zero-mutation tests |
| Atomic exclusive claim and recoverable terminal outcomes | 3 | Real `fcntl.flock` multiprocessing concurrency and injected-failure tests |
| Coherent Codex lifecycle visible in dashboard | 4 | Identity, ordering, adapter, and DashboardCache tests |
| Historical prefix plus declared exact suffix proof | 4 | Drift, reorder, deletion, and extra-row tests |
| Identity-less pre-pilot policy and separate human gate | 6 | Documentation regression test |

## Scope Guards

- Do not modify `.codex/config.toml`, hook registration/policy, activation
  fragments, replay invoker, or dashboard design.
- Do not invoke Codex, subprocesses, hooks, network clients, or real pilot
  requests; do not choose a candidate or collect consent/sign-off.
- Do not write real `agent-monitoring/*.jsonl` data, backfill historic records,
  or emit a real `provider="codex"` record.  Such values exist only in
  disposable test fixtures.
- Do not duplicate shared writer locking/append behavior, adapter parsing or
  redaction, identity validation, manifest-prefix logic, or dashboard ingest.
- If a needed reuse point cannot accept an injected scratch target without
  changing its production contract, stop at Review rather than adding a broad
  production writer/config seam under this ticket.

## Deviations

- The planned regression command initially exposed the real-corpus provider-count assertion
  described in Step 6.  It was not changed in this ticket: the truth-preserving assertion repair
  was recorded and closed separately as `TCK-20260801-PROVIDER-COVERAGE-TEST-STALE`, because the
  Claude identity ticket had already made the earlier exact-zero premise obsolete.
