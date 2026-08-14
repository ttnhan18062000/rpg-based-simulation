---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260730-CODEX-CONTROLLED-PILOT
artifact_type: plan
---

# Plan — TCK-20260730-CODEX-CONTROLLED-PILOT

## Plan Status

Safe-stopping plan. It authorizes read-only validation and preparation only. It does not authorize
a live invocation, hook enablement, a hook-bearing config, any live-consent environment variable,
or an executor/activation implementation. Per the ratified pre-pilot monitoring policy, mandatory
lifecycle bookkeeping is permitted and required only through `record_run.py`/`record_events.py`
with `provider` omitted or `null`; it must never claim `provider="codex"` before the authorized
pilot operation.

## Dependency Map

```text
Readiness tickets DONE
  → controlled-pilot evidence/preflight preparation (this ticket)
  → separately reviewed executor/activation ticket
  → named candidate + request + fresh human sign-off
  → all preflight gates pass
  → one named final live operation
```

## Ordered Steps

1. Reconfirm completed predecessor evidence and the controlled baseline: hook-free config, exact
   policy surface, no Codex provider record, no-live structural tests, and isolated unrelated
   working-tree changes. Record facts only; do not repair baseline drift.
2. Run the scoped readiness suite from `test_plan.md` with `.venv`; preserve pass/fail evidence
   and distinguish any unrelated pre-existing failure.
3. Document a future candidate-request checklist, without creating/approving a request: named
   low-risk candidate, owner, one-action rollback, fresh sign-off, real-corpus claim decision,
   baseline manifest, policy subset, expected lifecycle records, and dashboard visibility.
4. Define the future preflight evidence bundle and refusal-before-action ordering. It must validate
   predecessors, request, real corpus, policy, trust reviews, config diff, identity lifecycle,
   baseline/prefix preservation, and rollback evidence before any mutation/invocation.
5. Record the named final-operation stop. This workflow must not set live-consent/sign-off/append
   variables, create hook-bearing config, invoke Codex, or write a `provider="codex"` monitoring
   record. It must write ordinary pre-pilot lifecycle entries identity-less. A future effort may
   cross the final-operation stop only after all separately reviewed/human-owned conditions exist.
6. Architecture-review this plan as a containment plan. Reject any attempt to embed, reinterpret,
   or weaken the missing executor boundary in this ticket.
7. Keep this ticket in progress and BLOCKED at the final-operation gate; do not finalize it or
   simulate a live result.

## Acceptance-Criteria Map

| Ticket criterion | Steps | This ticket's result |
|---|---|---|
| Missing/invalid preflight inputs reject | 3–4 | Requirements and refusal contract documented; executor implementation deferred |
| Exact enabled surface | 1–2, 4 | Read-only verification and policy evidence |
| No approval means no live action | 1, 5, 7 | Preserved and evidenced |
| Live prefix/lifecycle/dashboard/rollback proof | 4 | Deferred to executor plus fresh approval |
| Review before expansion | 6–7 | Handoff gate prepared; no expansion |

## Scope Guards

- Do not change guardrail, adapter, or shadow no-live-execution invariants.
- Do not add an executor/invoker/hook command or production activation config.
- Do not invoke Codex or set `CODEX_REPLAY_PARITY_LIVE_CONSENT`,
  `CODEX_LIVE_PILOT_HUMAN_SIGNOFF`, or `CODEX_POSTTOOL_ADAPTER_LIVE_APPEND`.
- Write mandatory pre-pilot lifecycle records only through `record_run.py`/`record_events.py`, with
  `provider` absent or `null`; do not backfill earlier runs or fabricate a Codex provider identity.
- Do not alter historic prefixes or claim a tool row proves a coherent dashboard-visible run.
- Do not absorb unrelated working-tree changes or touch simulation/parity behavior.

## Required Evidence Before the Final-Operation Gate

- Hook-free config and policy-surface baseline.
- Monitoring corpus prefix baseline and no active conflicting claim under the future policy.
- Identity-less pre-pilot lifecycle records for future workflow activity, per
  `codex_controlled_pilot_monitoring_policy_decision_codex.md`.
- Scoped readiness test evidence, with unrelated failures isolated.
- Predecessor/shadow evidence references and a candidate-request checklist (not a fabricated request).
- Architecture-review approval of this containment plan and an explicit executor handoff.

## Unresolved Questions

1. **Blocking: separate executor/activation boundary.** No reviewed component can safely compose
   trusted config activation, live invocation, real-corpus lifecycle writes, reader proof, and
   rollback. The replay invoker cannot serve this role because it deliberately rejects those effects.
   A new narrowly scoped, independently reviewed ticket is required.
2. **Blocking: fresh human approval.** Before any final operation, the user must supply a named
   low-risk candidate, valid request/owner/rollback plan, and contemporaneous explicit sign-off.
3. The executor design must define single-provider active-claim semantics, coherent run/event/tool
   lifecycle ownership, and a prefix-preservation proof that permits only expected pilot appends.

## Deviations

None. The plan intentionally stops before the live-operation implementation phase.
