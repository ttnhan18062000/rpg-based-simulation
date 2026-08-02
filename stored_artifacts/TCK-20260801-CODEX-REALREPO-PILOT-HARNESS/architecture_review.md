---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260801-CODEX-REALREPO-PILOT-HARNESS
artifact_type: plan
verdict: APPROVED
---

# Architecture Review — TCK-20260801-CODEX-REALREPO-PILOT-HARNESS

## Verdict

**APPROVED.** The revised plan resolves every required architecture finding and
remains within the owner's non-live authorization.

## Resolution verification

1. **Live-only admission vs. ordinary/test refusal — resolved.** Ordinary and
   test entry points reject the canonical root, descendants, and escapes before
   derived-path I/O.  A separate private live-boundary admission is the only
   future path that may perform reviewed root-identity validation, and it is
   behind both exact consent gates plus no-write preflight.  The plan explicitly
   forbids exercising that admission in this ticket; the test plan covers only
   its refusal path against the actual project root.

2. **Trusted immutable expected-write policy — resolved.** The policy is now a
   contained, versioned artifact bound to candidate/request/baseline by hash.
   It declares exact historical field transitions, lifecycle/evidence path
   classes, and monitoring suffix identity/sequence rows.  Preflight validates
   it before claim/write/invoker construction and post-run proof uses the
   captured policy, rather than a mutable re-read.  Required tests now reject
   caller-supplied, mismatched, and post-baseline-mutated policy.

3. **Authority and fake-invoker semantics — resolved.** The plan no longer
   makes an indefensible cryptographic claim for Python.  It uses a private
   token issued only by the dual exact-value gate in the normal public flow.
   Tests prove refusals occur before construction and one scratch-root fake
   invoker records a call without starting a process.  Both gates are necessary
   value checks; contemporaneous human authorization remains an external future
   pilot requirement, not something a passing test establishes.

4. **Deferred hook transport and rollback — resolved.** The adapter is bounded
   to scratch-config capture/enable/restore/hook-free verification and receives
   neither arbitrary command nor repository-wide write capability.  Exact
   rollback restoration is kept distinct from retained lifecycle and append-only
   evidence; cross-identity restore/terminalization is now a required negative
   test.  A real hook/config adapter remains a separately reviewed prerequisite.

## Required implementation boundaries

- Reuse public guardrail loaders/surface checks, monitoring prefix helpers, and
  the executor's ownership-verified `fcntl.flock` protocol; do not import
  private writer internals or replay invocation code.
- Keep the new package library-only.  Its sole subprocess seam must be static
  and structurally isolated; no test starts a real process or calls `codex`.
- Preserve the complete historical monitoring prefix and validate a declared
  suffix rather than accepting arbitrary append-only rows.
- Do not register a hook, change `.codex/config.toml`, run against the actual
  repository, emit a project `provider=\"codex\"` record, or alter the standing
  candidate ticket during this ticket.
- A future hook transport remains an explicit preflight dependency and must be
  separately reviewed before any actual pilot; this ticket must not invent one.

## Implementation note

Keep the documented ordering literal in code: ordinary/test root refusal before
any derived-path I/O; future live-only root admission only after authority and
no-write validation; policy validation before claim/write/invoker creation.
Any need to select a real hook/config transport, invoke Codex, target the real
repository in tests, or relax a protected scratch-only package is outside this
approval and requires a new review.
