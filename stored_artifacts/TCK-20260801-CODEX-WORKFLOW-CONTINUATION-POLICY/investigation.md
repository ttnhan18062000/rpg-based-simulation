---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260801-CODEX-WORKFLOW-CONTINUATION-POLICY
artifact_type: investigation
---

# Investigation — TCK-20260801-CODEX-WORKFLOW-CONTINUATION-POLICY

## Question

Can the proposed `continuation_policy` in the shared `implement-ticket` workflow contract be
made explicit, validated, and safe without weakening any existing workflow stop condition or
authorizing live/provider activation?

## Retrieval and evidence limits

The local semantic search fallback could not run because the project venv lacks the optional
`sentence-transformers` dependency. `graphify query` returned unrelated retention-policy nodes.
Investigation therefore used the ticket/Claude review documents and direct follow-up reads of the
contract, loader, renderer, terminal-status vocabulary, workflow source, and their tests.

## Current implementation and gap

The uncommitted proposal is limited to:

- `agent-orchestration/workflows/implement-ticket.yaml`: optional `continuation_policy` mapping;
- `tools/agent_orchestration_codex_adapter/generator.py`: emits the mapping's prose and
  `non_gates` into `AGENTS.md`; and
- generated `AGENTS.md`.

`tools/agent_orchestration/loader.py::_load_workflow_yaml` currently validates only required
workflow keys, non-empty phases, and non-empty agents. It neither recognizes nor validates
`continuation_policy`; `ContractBundle` has no dedicated continuation-policy field. Any mapping
shape (including missing mode/instruction or unsafe non-gate wording) is accepted and rendered.
The previously reported 39 passing tests cover the unrelated hook-surface-policy work and provide
only additive-compatibility evidence, not continuation-policy safety proof.

The direct precedent is `loader.py::_load_hook_surface_policy_yaml`: required-key/type/invariant
checks raise `ContractValidationError`, and `load_contract()` passes the validated value through a
dedicated `ContractBundle` field. `tests/agent_orchestration/test_validator_errors.py` uses a
temporary copied contract and table-like mutation helpers to prove named failures. The Codex
renderer test surface is `tests/agent_orchestration_codex_adapter/test_generator_traceability.py`;
it currently does not assert `AGENTS.md` continuation content.

## Existing terminal outcomes

`agent-orchestration/terminal-statuses.yaml` is the declared normalized vocabulary, sourced from
`.claude/workflows/implement-ticket.js`. The workflow returns immediately after each of these
non-success/finalization outcomes:

| Terminal status | Phase | Continuation consequence |
| --- | --- | --- |
| `CONFLICTS_DETECTED`, `TAGS_NOT_REGISTERED` | Scope | Stop; scoped run cannot continue. |
| `SCOPE_AGENT_FAILED` | Scope | Stop; malformed/no ticket scope. |
| `NEEDS_HUMAN_INPUT` | Investigate | Stop; unresolved question requires user decision. |
| `NEEDS_CHANGES`, `BLOCKED` | Review, Architecture-Verify | Stop; review gate failed. |
| `DOC_STALENESS_BLOCKED` | Architecture-Verify | Stop; implementation documentation gate failed. |
| `TESTS_FAILED`, `DATA_RUNS_CLEAN_FAILED` | Test | Stop; verification or cleanliness gate failed. |
| `PARITY_INCOMPLETE` | Parity | Stop; parity gate failed. |
| `SECURITY_BLOCKED` | Security-Review | Stop; security gate failed. |
| `DOD_BLOCKED` | Verify | Stop; Definition-of-Done failed. |
| `FINALIZE_INCOMPLETE` | Finalize | Stop; post-migration self-check failed. |

`DONE` is the sole normal terminal outcome. `EPIC_SCOPED` is an intentional scope-only terminal
outcome, not permission to select or begin another ticket. Claude specifically requires explicit
coverage of `NEEDS_HUMAN_INPUT`, `NEEDS_CHANGES`, `BLOCKED`, `DOD_BLOCKED`,
`CONFLICTS_DETECTED`, `TAGS_NOT_REGISTERED`, `SECURITY_BLOCKED`, `TESTS_FAILED`, and
`DOC_STALENESS_BLOCKED`; the remaining declared stop outcomes must also be reserved to avoid a
weaker policy by omission.

The concrete behavioral precedent is this session: the executor workflow stopped at
`NEEDS_HUMAN_INPUT` for unresolved plan questions and stopped at architecture-review
`NEEDS_CHANGES`, rather than resolving or retrying those gates silently.

## Design constraints

1. The shared workflow's existing return/gate semantics remain authoritative. A continuation
   instruction only prevents unnecessary conversational pauses while the current run is healthy;
   it cannot alter a declared terminal status.
2. Policy validation must be structural. A prose instruction alone cannot prevent someone adding
   `NEEDS_HUMAN_INPUT` or another reserved terminal value to `non_gates`.
3. The policy applies only to an already selected, in-scope ticket invocation. It cannot select a
   next ticket, broaden scope, edit gate evidence to pass, authorize a live/destructive action,
   or override separate consent/sign-off requirements.
4. This is agent-orchestration/developer tooling, not simulation behavior. No Mechanics Bible or
   authoritative mutation pipeline changes apply; an INFRA parity disposition may be appropriate
   if the behavior contract itself changes.
5. The existing three-file diff remains quarantined. It must be treated as an implementation
   candidate, not accepted evidence, until architecture review and explicit user sign-off of the
   final rendered text.

## Recommended implementation shape

- Add a typed `ContinuationPolicy` dataclass (or an equally explicit validated mapping) to
  `ContractBundle`; validate `mode == "continue_until_terminal_or_hard_gate"`, non-empty string
  `instruction`, and non-empty list of non-empty string `non_gates`.
- Derive reserved stop-status values from `terminal-statuses.yaml` during loading, or centrally
  define and cross-check the same vocabulary; reject case-insensitive/normalized overlap between
  any `non_gates` entry and every reserved terminal status. Do not duplicate a partial hard-gate
  list in the renderer.
- Have `build_agents_md()` consume the validated bundle field rather than a free-form
  `workflow.get()` mapping.
- Add exact rendered-text coverage and validation mutations for missing/invalid fields,
  malformed lists, and every reserved status. Add an invariant test that the required Claude-named
  statuses are members of the reserved set and that every non-DONE terminal return is treated as a
  stop outcome.
- The final operational wording must state that `DONE`/`EPIC_SCOPED` end the invocation, all
  non-success terminal statuses stop it, and human authority remains required for the separately
  governed live/destructive actions.

## Risks and controls

| Risk | Control |
| --- | --- |
| Prose accidentally treats a gate as ordinary progress | Loader rejects normalized reserved status names in `non_gates`; tests enumerate the vocabulary. |
| Terminal-status list drifts | Derive/cross-check against `terminal-statuses.yaml` and test all non-DONE entries. |
| Continuation is misread as broad autonomy | Render explicit non-authorizations; require user approval of final rendered text. |
| Existing providers change behavior accidentally | Keep the change Codex-renderer scoped; do not modify `.claude/workflows/implement-ticket.js`. |
| Monitoring falsely claims a live Codex run | Use provider-omitted lifecycle monitoring only; do not alter hooks/config/corpus identity. |

## Scope recommendation

Proceed with a standard plan and architecture review. The ticket is not ready for closure without
the final explicit user approval of the exact `AGENTS.md` policy text, after Claude's review.
