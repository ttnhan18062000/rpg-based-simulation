---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260801-CODEX-PILOT-ORCHESTRATION
artifact_type: investigation
tags: [ai, security, workflows, hooks, agent-monitoring, rollback, testing]
---

# Investigation — TCK-20260801-CODEX-PILOT-ORCHESTRATION

## Current behavior

- `live_preflight.py::_create_live_preflight` is the only sanctioned constructor
  for real-root immutable evidence. It reuses the shared no-write evidence capture
  and refuses every non-canonical root.
- `authority.py::issue_live_authority` is the sole dual-consent issuer. Both
  `CODEX_LIVE_PILOT_HUMAN_SIGNOFF` and
  `CODEX_REALREPO_PILOT_LIVE_CONSENT` must equal exactly `"1"`.
- `agent_codex_live_transport.invoker::invoke_live_transport` rechecks that same
  dual consent as its literal first statement and delegates real-root admission to
  `_invoke_live_after_authority`. It does not perform post-run proof or rollback.
- `proofs.py::assert_post_run_proof` already enforces immutable policy binding,
  allowlisted changes, exact historical target transition, and append-only exact
  monitoring suffixes. It must be called, not copied.
- `rollback.py::ScratchConfigAdapter` deliberately refuses the real project root
  and captures/restores a temporary config only. Its refusal is a protected prior
  safety property, so a real-config capability must be additive and separate.
- `config_toggle.py` supplies the empirical `PostToolUse` TOML fragment but is
  likewise scratch-only. The hook policy approves only that event and the shared
  writer functions `write_line`/`write_lines` as a future activation candidate.

## Constraints

No simulation `AuthoritativeState` is involved. The controlling constraints are
operational: default tests never touch the canonical config or call Codex; only the
two existing consent gates may authorize real-root/config capability; ordinary
preflight and scratch rollback refusal remain intact; and the reserved candidate
plus blocked parent tickets must not be changed.

## Prior work and reusable primitives

- `TCK-20260801-CODEX-REALREPO-PILOT-HARNESS` established immutable preflight,
  expected-write proof, root containment, and scratch config rollback.
- `TCK-20260801-CODEX-LIVE-TRANSPORT` created the reviewed fixed-argv subprocess
  seam, source-level constructor containment proof, literal-first fresh-consent
  check, and control-character-safe instruction rendering.
- `TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS` owns request schema, approved enabled
  surface, and the originally captured PostToolUse fragment.

## Architecture proposal for review

Add a separate package with two deliberately narrow objects:

1. A production-config capability created only by a private factory taking typed
   `LivePreflightResult` plus issued authority. Its real target is derived from the
   reviewed canonical root, never a caller path. Production-facing calls re-run
   `issue_live_authority(os.environ)` immediately before a write. Tests exercise
   byte operations with synthetic private capability doubles rooted in `tmp_path`,
   while an AST containment test proves no production source constructs one outside
   the private factory. It snapshots exact bytes and exposes no arbitrary TOML or
   hook-command input.
2. A pilot orchestrator accepting only the typed live preflight and authority. It
   issues/configures, delegates to `invoke_live_transport`, captures the post-run
   tree, calls `assert_post_run_proof`, and restores/verifies in a `finally` path.
   It must not claim an invocation succeeded if post-run proof or rollback fails.

The exact public/private split and whether a single orchestration call should own
the adapter lifecycle require Architecture Review because this is the first
capability intentionally able to write the canonical config when later exercised.

## Risks and anti-drift hazards

- A factory that accepts a raw `Path`, an ordinary preflight, or an arbitrary
  fragment would bypass the reviewed evidence boundary.
- Restoration must occur even when transport/proof raises, but rollback failure
  must remain visible rather than masking the primary failure.
- The expected-write policy must explicitly accommodate the temporary config state
  only within orchestration proof sequencing; a post-rollback final tree must be
  proven hook-free and policy-compliant.
- Tests must use `tmp_path` stand-ins and synthetic typed objects. A mocked process
  against the real root is still prohibited.

## Parity disposition

This is agent-operation infrastructure with no simulation behavior change. If
implementation remains within tooling, parity should add a clearly bounded
`INFRA-*` entry documenting the unexercised capability and no-live condition.

## Governed activation-prerequisite mapping

Completion of this ticket is not approval to activate a hook. The nine
`hook-surface-policy.yaml` prerequisites map as follows:

| Prerequisite | This ticket's contribution | Still required for a real pilot |
| --- | --- | --- |
| `human_approval` | none | A contemporaneous, recorded human decision immediately before the run |
| `scratch_first_verification` | Adds injected-config orchestration tests | Confirm the reviewed scratch evidence remains applicable to the selected run |
| `project_trust_review` | none | Independent human project-trust review |
| `hook_trust_review` | none | Independent human hook-trust review |
| `failure_timeout_fail_open` | Reuses the fail-open adapter | Confirm against the exact approved live fragment |
| `redacted_output` | Reuses the redacting PostToolUse adapter | Confirm the live payload route remains redacted |
| `out_of_band_diagnostics` | Reuses writer health-sidecar behavior | Confirm diagnostics are available for the actual run |
| `reviewed_config_diff` | Produces a deterministic capability/fragment | Review the exact config diff for that one run |
| `one_action_rollback` | Builds and tests exact-byte rollback mechanism | Review real-run rollback evidence after the hook is restored |

Only the mechanism-level contributions can be built here. The human approval,
trust reviews, exact-diff review, and real-run evidence remain future pilot-decision
requirements even if this ticket closes.
