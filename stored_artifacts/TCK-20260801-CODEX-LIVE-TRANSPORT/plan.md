---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260801-CODEX-LIVE-TRANSPORT
artifact_type: plan
tags: [ai, security, testing]
---

# Plan — TCK-20260801-CODEX-LIVE-TRANSPORT

## Safety invariant

Build a capability, not an operation. No implementation/test/review path may run
Codex, enable a hook, modify `.codex/config.toml`, alter the reserved candidate or
blocked parent tickets, or append a `provider="codex"` project monitoring record.
Only a future, independently authorized controlled-pilot operation may exercise the
completed capability.

## Proposed design

Create an additive `tools/agent_codex_live_transport/` package with a narrow typed
transport API. It owns the fixed `codex exec` argument-vector construction and the
subprocess seam, but has no public raw-root, raw-shell, arbitrary-options, prompt
text, or hook/config/mutation API.

Extend the harness through a minimal, explicitly named live-preflight bridge rather
than changing `ordinary_preflight`:

1. A private/typed live-preflight result carries canonical-project-root identity plus
   the same immutable request/policy/baseline evidence required by the existing
   harness. Its sole sanctioned construction path is a private module-level factory
   that performs genuine real-root validation; no public dataclass construction is
   accepted. The factory is separate from ordinary scratch admission, and no test
   invokes successful real-root admission.
2. The boundary accepts only dual authority plus that live-preflight result before
   delegating to the injected transport. It never accepts a raw root. An AST
   containment test proves no source path outside the private factory constructs the
   live-preflight capability.
3. The transport constructs a fixed argv form (`codex`, `exec`, constrained working
   directory/sandbox flags, and a fixed template derived only from validated
   ticket/candidate/policy fields on the live-preflight result). It accepts no
   caller-supplied prompt/text. The subprocess entry re-checks both established
   exact-value consent gates as its literal first authorization operation, then
   validates authority/preflight before construction. It disables shell execution,
   rejects bypass flags structurally, returns a typed outcome, and exposes no
   automatic retry or broad rollout behavior.
4. A future pilot caller—not this ticket—will be responsible for wrapping that
   invocation with the existing policy post-run proof and separately reviewed
   rollback operation. The transport must require those preflight capabilities at
   entry but must not duplicate proof/rollback logic.

## Implementation steps

1. Add tests first for the typed live-preflight/authority ordering, command vector
   safety, rejection-before-subprocess construction, no raw-root/prompt API, fresh
   re-check of both consent values at the subprocess entry, and default skip-not-fail
   real-invocation fixture behavior.
2. Add the minimal live-preflight capability/bridge in the existing harness package,
   preserving `ordinary_preflight` refusal of the project root and its scratch-only
   public behavior. Implement the sole private factory that genuinely validates the
   real root and immutable evidence. Add an AST containment test proving no source
   path outside that factory constructs `LivePreflightResult`.
3. Add the additive transport package with a fixed argv builder and one injected
   subprocess runner seam. Reuse `issue_live_authority`, live-preflight evidence,
   and existing proof primitives; do not import replay's mutating/zero-diff flow as
   an implementation dependency.
4. Add static source tests for bypass flags, shell execution, hook/config/monitoring
   writers, candidate-ticket paths, prompt/raw-root API exposure, and duplication of
   harness proof/rollback logic.
5. Add the opt-in skip fixture and a test that verifies skip behavior without
   requesting or executing a real Codex call. Do not create a live test invocation.
6. Run focused and protected regression suites. Record any pre-existing failures
   separately. Produce post-implementation evidence for Claude's actual-diff review
   and stop there until approval.

## Scope guards

- Do not modify `tools/agent_replay_codex/invoker.py`; it is a read-only precedent.
- Do not make `_invoke_live_after_authority` publicly callable by arbitrary code;
  expose only the smallest reviewed integration path required by the transport.
- Reuse the existing dual authority gate names. The transport must re-check both
  values fresh at the literal subprocess-invocation entry; an earlier authority
  object is additive evidence, never a substitute for that re-check.
- Do not invoke `subprocess.run` in tests except through an explicitly opted-in
  fixture, which this ticket does not request or enable.

## Acceptance map

| Acceptance criterion | Planned proof |
| --- | --- |
| constrained transport only after authority/preflight | private factory, AST construction scan, and ordering tests |
| refuse before construction / no bypass | unit tests plus AST source scan |
| default no-live tests | non-autouse skip fixture and no-consent test run |
| reuse existing harness | imports/delegation and anti-duplication static tests |
| no forbidden activation mutations | worktree snapshot/AST tests and scoped diff review |
| independent reviews | Claude plan review before Implement; actual-diff review after Implement |

## Open review questions

All Architecture Review design questions are resolved above. Any newly discovered
question that changes these safety boundaries must return to Architecture Review
before implementation continues.
