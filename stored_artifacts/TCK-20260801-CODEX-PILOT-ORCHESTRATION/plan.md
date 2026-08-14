---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260801-CODEX-PILOT-ORCHESTRATION
artifact_type: plan
tags: [ai, security, workflows, hooks, agent-monitoring, rollback, testing]
---

# Plan — TCK-20260801-CODEX-PILOT-ORCHESTRATION

## Safety invariant

Build capability only. No code path in implementation or tests may call Codex,
modify the committed `.codex/config.toml`, enable a real hook, append a
provider-attributed monitoring record, implement the reserved candidate, or modify
the blocked parent tickets.

## Proposed design

Create an additive `tools/agent_codex_pilot_orchestration/` package. Keep
`ScratchConfigAdapter` unmodified and refusal-only for the real root.

- `production_config.py` owns a typed, private-factory-created config capability.
  It derives exactly `<canonical live-preflight root>/.codex/config.toml`; no public
  raw-root/path/TOML/command parameter exists. The factory verifies typed live
  preflight, authority, and canonical root. It captures original config bytes
  strictly before `enable()` can write. `enable()` re-checks both existing consent
  values immediately before its write; `restore()` deliberately does not recheck
  consent, so the owning identity can always return the config to hook-free bytes
  in a failure `finally` path. Restore is a safe no-op after a completed restore by
  that same owner, while another identity is refused. Tests use synthetic private
  capability doubles rooted in `tmp_path`; an AST containment test proves no
  production source constructs the capability outside the private factory.
- `orchestrator.py` owns the only integration sequence. It calls the existing live
  preflight factory, issues authority through the existing issuer, creates the
  config capability, delegates invocation to `invoke_live_transport`, captures the
  after tree, delegates to `assert_post_run_proof`, then restores and verifies the
  config in a failure-preserving `finally` path. It requires the immutable policy
  to declare `.codex/config.toml` as its one transient path and confirms that file
  still contains exactly the approved hook bytes before accepting the post-run
  proof; arbitrary transport-time config changes are rejected.
- Use the fixed evidenced PostToolUse fragment from guardrails/adapter precedent;
  no caller can choose hook events, writer functions, executable, arguments, or
  additional environment variables.

## Ordered implementation steps

1. Add failing pure/injected tests for factory admission, exact dual-consent write
   ordering, fixed fragment surface, exact restore, and orchestration failure paths.
2. Implement the typed production-config capability and private factory with strict
   canonical-root derivation, baseline ownership binding, and fresh consent
   rechecks. Preserve every existing scratch adapter behavior unchanged.
3. Implement the minimal orchestration composition. Delegate to live preflight,
   authority, transport, post-run proof, and rollback helpers; do not copy their
   validation algorithms.
4. Add AST/negative-path tests proving the public API cannot receive bypass inputs,
   the production factory is unique, and tests never mutate the committed config.
5. Run focused and protected regression suites; record a bounded infrastructure
   parity disposition; submit the actual diff to Claude for mandatory review before
   Test/Verify/Finalize.

## Dependency map

`live_preflight` + `authority` -> production config capability -> fixed transport
-> post-run proof -> exact rollback verification. The config capability must be
restored in all terminal paths, and any failed proof/rollback makes orchestration
fail rather than report pilot success.

## Scope guards

- Do not add a third consent variable or a free-form hook/prompt/config API.
- Do not weaken real-root refusal in existing scratch-only classes.
- Do not write test doubles under the actual project root or use mocked subprocess
  calls against it.
- Do not touch `.codex/config.toml`, the reserved candidate, blocked parent tickets,
  or provider-attributed monitoring in this ticket.
- Do not treat completion as hook-activation approval: the policy's recorded human
  approval, project/hook trust reviews, exact config-diff review, and reviewed
  real-run rollback evidence remain separate future requirements.

## Acceptance-criteria map

| Acceptance criterion | Implementation/proof |
| --- | --- |
| composed ordering | orchestrator dependency injection and call-order tests |
| canonical config capability | private factory, type/root checks, AST test |
| approved hook + exact rollback | fixed fragment and byte-identity tests |
| refusal/failure coverage | unit tests for each admission and failure path |
| no-live default | static containment/config snapshot tests |
| independent review | Claude plan review and actual-diff review before closure |
