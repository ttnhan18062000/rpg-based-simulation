---
status: active
layer: ai
authority: P1
audience: developer
tags: [ai, workflows, agent-monitoring, process-improvement]
---

# Replay Fixture Envelope Specification — TCK-20260721-CODEX-REPLAY-PROOF

Defines the versioned data shape a `tools/agent_replay/` fixture file must satisfy to
deterministically replay the `implement-ticket` workflow's Scope → Investigate → Plan → Review
phase slice, and the loader (`tools/agent_replay/fixture_envelope.py`) that validates it.

## Envelope shape

A fixture file is a single YAML document with this top-level shape:

```yaml
version: 1                       # int, currently always 1
source:
  ticket_id: TCK-...              # the real ticket this fixture was derived from
  ticket_path: tickets/done/TCK-....md
  stored_artifacts_dir: stored_artifacts/TCK-.../
  events_run_id: TCK-...          # run_id key in agent-monitoring/events.jsonl
  events_seq_range: [1, 4]        # inclusive seq range covered by this fixture
phases:
  - phase: Scope                  # one of: Scope, Investigate, Plan, Review
    agent: ticket-scoper          # matches docs/agent-monitoring/schema.md's agent vocabulary
    input: {...}                  # real, structured data the deterministic orchestrator logic needs
    output: {...}                 # recorded stand-in for the phase's agent() JSON return
    transition: ok                # ok | CONFLICTS_DETECTED | TAGS_NOT_REGISTERED | NEEDS_HUMAN_INPUT | <Review verdict>
  - phase: Investigate
    ...
  - phase: Plan
    ...
  - phase: Review
    ...
```

Every phase entry requires all five keys (`phase`, `agent`, `input`, `output`, `transition`)
present and non-null. `input`/`output` may be an empty dict (`{}`) for a phase with no
deterministic branch logic (e.g. `Investigate`) — an empty dict is a valid recorded value, distinct
from the key being absent or `null`.

## Why telemetry alone is insufficient

`docs/agent-monitoring/schema.md` caps `events.jsonl`'s `summary` field at 200 chars (silently
re-truncated by `record_events.py`) and `tools.jsonl`'s `input_summary` field at 120 chars. Neither
field carries the full `agent()` prompt, the full structured JSON return value (e.g. `TICKET_SCHEMA`'s
`tags`/`conflicts`, or `REVIEW_SCHEMA`'s `verdict`/`violations`), or which specific branch was taken
and why. A fixture built only from `runs.jsonl`/`events.jsonl`/`tools.jsonl` rows cannot drive a
genuine replay of the orchestrator's branch logic — it can only replay the fact that a phase happened
and its truncated summary. This is the reason AC #1 requires the envelope to carry the actual
recorded phase `input`/`output`/`transition` data, not merely a reformatting of the telemetry
projection.

## Phase-slice scope statement

This fixture format, and the runner that consumes it, cover only the **Scope → Investigate → Plan →
Review** slice — the four `implement-ticket` phases before Implement. Implement,
Architecture-Verify, Test, Parity, Security-Review, Verify, and Finalize are out of scope: those
phases require a `files_changed`/diff payload this fixture format does not define, and replaying them
is a materially larger and different proof. See `staging_artifacts/TCK-20260721-CODEX-REPLAY-PROOF/plan.md`
(now `stored_artifacts/`) for the full reasoning.

## Contract-representation evaluation (AC #5)

`docs/architecture/agent_orchestration_contract.md`'s "Contract Representation and Format" decision
(Status: Decided) states: "The shared orchestration contract is YAML, for human-reviewable
definitions, with generated Python validation models."

This fixture envelope follows the **YAML-for-data** half of that decision — fixture files are plain
YAML, chosen for the same human-reviewability reason the ADR cites, and because YAML tolerates
multi-line prose fields (e.g. a recorded `summary` string) without JSON-escaping. It follows a
**hand-written**, not generated, Python validator (`tools/agent_replay/fixture_envelope.py`'s
`load_fixture`) — no codegen tooling exists in this repository yet, so the "generated" half of the
ADR's decision is not yet buildable. `load_fixture` is the practical analogue of what the ADR's
"generated Python validation models" aspires to, adapted to what is actually implementable today.

This fixture envelope is explicitly **not** the same artifact as the ADR's own future
`agent-orchestration/contract.yaml`. The ADR's Source Ownership decision places that file under a new
`agent-orchestration/` directory this ticket does not create — that directory is Out of Scope per the
ADR's own ticket. The fixture envelope defined here is a separate, replay-specific data shape (test
fixture data for one workflow's Scope→Review slice) that merely follows the same YAML-for-data format
preference; it is not a draft, partial, or alternate implementation of the shared orchestration
contract.

## Unconditional containment law

The replay runner must never subprocess or import `tools/agent-monitoring/pre_tool_hook.py`,
`post_tool_hook.py`, `record_run.py`, or `record_events.py`, under any condition — including from an
isolated or sandboxed working directory. This holds with zero exceptions; there is no conditional or
"safe mode" form of this rule. Fake/no-op stand-ins (`_fake_write_monitoring`, `_fake_hook_boundary`
in `tools/agent_replay/runner.py`) are injected in place of every call site the real orchestrator
would use to write monitoring records or touch a hook sidecar.

## Fail-closed law

`load_fixture` raises `FixtureValidationError`, naming the exact missing field and phase index, on
any missing or null required envelope field. It never substitutes a default and never logs a warning
and continues. This is a deliberate inversion of this repository's dominant fail-open
monitoring-write convention (CLAUDE.md: "Monitoring write failure must never fail the workflow") —
that convention governs the *real* orchestrator's monitoring writes, not this replay proof's fixture
validation, which must fail loudly so a malformed or incomplete fixture can never masquerade as a
successful replay.
