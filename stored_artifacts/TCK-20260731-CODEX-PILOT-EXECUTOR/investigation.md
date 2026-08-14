---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260731-CODEX-PILOT-EXECUTOR
artifact_type: investigation
---

# Investigation — TCK-20260731-CODEX-PILOT-EXECUTOR

## Decision

Implement a **simulation-only executor boundary**, not a live-pilot executor.  The new package
must accept an injected scratch root and construct a deterministic synthetic lifecycle there.  It
must never receive the repository root as a permitted output root, read a real candidate request,
modify `.codex/config.toml`, invoke a hook, spawn a process, or call `codex`.

The package should orchestrate existing components; it must not become a second monitoring
writer, payload redactor, identity validator, dashboard reader, policy parser, or config toggle.
Its durable technical counterpart is only a scratch fixture corpus used by tests.

## Existing Components and Gaps

| Concern | Existing component | Reuse / boundary |
| --- | --- | --- |
| Candidate ownership and rollback fields | `agent_codex_pilot_guardrails.pilot_manifest` and `ticket_selection` | Load only from an injected scratch `pilot_requests/`; reject absent, malformed, or mismatched ticket IDs. |
| Policy limit | `enabled_surface.assert_enabled_surface_subset` | Require exactly the synthetic declared subset: `PostToolUse` and `write_line`; this proves the candidate surface without enabling it. |
| Monitoring history preservation | `baseline_manifest_gate.capture_pilot_baseline` / `assert_pilot_baseline_preserved` | Take pre/post scratch snapshots.  Prefix, rather than full-file equality, is correct because the synthetic lifecycle deliberately appends declared rows. |
| Tool row | `agent_codex_posttool_adapter.adapter.process_post_tool_use` | Feed the captured fixture payload in-process to a scratch `tools.jsonl` target, with an explicit injected mapping for the adapter's gate.  Do not mutate `os.environ`; this is a test seam, not live authorization. |
| Tool record identity/redaction | adapter's input model, identity validation, record builder, and writer bridge | Reuse unchanged; the executor supplies matching `run_id`, `seq`, `phase`, `agent`, `ticket_id`, and `execution_id`. |
| Run and event validation / append semantics | `tools/agent-monitoring/record_run.py`, `record_events.py`, and shared `writer.py` | Reuse `validate_record` functions and `writer.write_line` / `write_lines` against injected scratch paths.  Do **not** call their CLIs: their module constants target real `agent-monitoring/`. |
| Dashboard proof | `src.api.agent_ops_dashboard.ingest.DashboardCache` | Instantiate it over a disposable repo-shaped scratch root and assert provider/execution/timeline visibility through public reader methods. |

The current `assert_no_concurrent_claim()` is insufficient for this ticket: it only rejects two
different providers and is a pure list inspection.  The executor needs a local scratch-only,
atomic claim protocol which also rejects a second unfinished claim by the *same* provider.

The existing replay invoker is explicitly unsuitable: it runs `codex exec` and asserts that
monitoring and config never change.  It must not be imported by the new package.

## Minimal Architecture

```text
scratch root (injected, validated as outside repository)
  ├─ pilot_requests/<ticket>.yaml       → existing manifest loader
  ├─ claims/<ticket>.json               → executor-owned O_EXCL claim marker
  ├─ agent-monitoring/{runs,events,tools}.jsonl
  │    └─ existing writer + adapter only
  └─ tickets/...                        → minimal copied ticket fixture for DashboardCache

preflight() → acquire_claim() → synthesize_lifecycle() → dashboard_proof()
             ↘ refusal / injected failure → terminalize or remove scratch claim
```

Create `tools/agent_codex_pilot_executor/` as a small library (no CLI).  Its public API should
be named to describe simulation rather than execution, for example `preflight_simulation`,
`acquire_scratch_claim`, `write_synthetic_lifecycle`, and `verify_scratch_dashboard`.  A frozen
context object carries only injected paths, expected identity, fixed timestamps, and an injected
adapter-gate mapping.  It must reject any root that resolves to the repository root, is inside
the real `agent-monitoring/`, or would resolve a monitoring/config/request/claim path outside the
provided scratch root.

### Ordered preflight and claim semantics

1. Validate scratch-root containment before every filesystem operation; reject real-corpus or
   escaped paths first.
2. Load the scratch request using the existing loader; require its `ticket_id` to equal the
   requested ticket.  Validate ticket ID / Codex execution ID with the adapter's identity helper.
3. Validate the declared surface with `assert_enabled_surface_subset`; the accepted set is the
   already evidenced `PostToolUse` plus `write_line`, not a configuration change.
4. Capture the scratch baseline, then atomically acquire `claims/<ticket>.json` with
   `os.open(..., O_CREAT | O_EXCL | O_WRONLY)`.  A pre-existing unfinished claim is a refusal,
   regardless of provider.  Claim content records only synthetic ticket/execution/provider/state.
5. Write the declared ordered lifecycle: one terminal synthetic run row, ordered events, and one
   redacted adapter-produced tool row.  The tool row's `seq` must point to a declared event; all
   identity fields must agree.
6. Check the prefix invariant and dashboard reader result.  Mark the claim terminal only after
   all proof succeeds.  On an injected write/proof failure, remove the just-acquired unfinished
   claim (or replace it atomically with a terminal `failed` record); never leave an ambiguous
   active claim.  The chosen recovery representation must be deterministic and tested.

Use a terminal run record from the outset only after all preflight checks pass; it represents a
synthetic completed test transaction, not a live run.  The claim marker, rather than a real
`runs.jsonl` in-progress record, provides the atomic exclusion property.  This avoids falsely
claiming a real Codex provider record in the repository corpus.

## Required Synthetic Record Contract

- One `runs.jsonl` record: `workflow="codex-pilot-simulation"`, terminal status, and matching
  `run_id`, `ticket_id`, `provider="codex"`, `execution_id`, fixed start/end timestamps.
- At least two event rows in increasing `seq` order (preflight and synthetic PostToolUse); each
  repeats the same identity triplet.  Their phase/agent labels should be fixture-local labels and
  may produce the current writer's warn-only vocabulary warning; do not change the global
  vocabulary merely to suppress it.
- Exactly one tools row, built only by the adapter from the captured PostToolUse fixture, joined
  to the PostToolUse event by `(run_id, seq)`.  Tests assert its redacted summary and absence of
  envelope secrets/paths.
- The executor declares the complete expected append sequence per file and compares it with the
  post-baseline suffix.  `assert_prefix_preserved` alone catches historical drift but does not
  prove that no unexpected new row was appended.

## Risks, Constraints, and Open Questions

1. `record_run.py` / `record_events.py` expose validation functions but hard-code real output
   paths in their command entry points.  The implementation must reuse their validators and the
   single shared writer directly, with no refactor that broadens production write surfaces.
2. The adapter's gate name includes `LIVE_APPEND`; a **locally passed mapping** with exact value
   `"1"` is acceptable only for an isolated scratch test.  It must not set process environment,
   appear in config, or be described as authorization.  If that naming is judged too misleading
   in review, add a pure injected adapter seam in the adapter ticket rather than weakening the
   gate here.
3. The ticket must decide whether recovery deletes a failed scratch claim or retains a terminal
   failed marker.  Recommended: retain a terminal marker with `state="failed"` and allow a fresh
   acquisition only after verifying its terminal state; this gives failure evidence without an
   ambiguous active lock.  Stale unfinished claims must refuse, not be auto-reclaimed.
4. Dashboard cache rebuilds depend on mtimes and expects a ticket tree.  Tests need a minimal
   ticket fixture, not a copy of the real tree; do not write under real `tickets/`.
5. The historical `test_provider_field_coverage_against_real_corpus_is_currently_zero` is known
   stale because a real Claude identity record now exists.  It is unrelated baseline drift and
   must be reported, not changed as part of this ticket.

## Out-of-Scope Guards

- No `.codex/config.toml`, hook policy, activation fragment, config toggle, or pilot request in
  the real repository changes.
- No `subprocess`, `os.system`, `codex`, replay invoker import, hook command, CLI, or network.
- No real `agent-monitoring/*.jsonl` write and no provider-bearing non-fixture record.
- No human sign-off, consent, candidate selection, or live execution.  The documentation update
  records that the separate human-approval gate remains required.
