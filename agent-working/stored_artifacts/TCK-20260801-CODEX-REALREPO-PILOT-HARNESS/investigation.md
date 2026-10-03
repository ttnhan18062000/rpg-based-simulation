---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260801-CODEX-REALREPO-PILOT-HARNESS
artifact_type: investigation
---

# Investigation — TCK-20260801-CODEX-REALREPO-PILOT-HARNESS

## Current Behavior

- `tools/agent_replay_codex/invoker.py:30-73` is the sole current `codex exec`
  boundary.  It always uses a new temporary directory and proves the real repository's
  tickets, monitoring prefix, and `.codex/config.toml` were unchanged.  It cannot run
  a candidate ticket.
- `tools/agent_codex_pilot_executor/simulation.py:72-164` composes an entirely
  disposable, provider-attributed synthetic lifecycle.  Its preflight accepts only an
  injected scratch root (`preflight.py:31-53`); `paths.py` rejects the actual project
  root and symlink escapes.  It deliberately imports no `subprocess`.
- The guardrails package already owns the pilot-request schema and selected reusable
  checks: strict owner/rollback loading (`pilot_manifest.py:35-64`), evidenced surface
  subset (`enabled_surface.py:17-58`), monitoring prefix preservation
  (`baseline_manifest_gate.py:27-34`), fresh pilot sign-off
  (`signoff_gate.py:17-34`), and scratch-only config restoration
  (`config_toggle.py:38-82`).  Its `test_no_live_execution_path.py` is a protected
  no-live invariant and must remain unchanged.
- The selected candidate has a real `pilot_requests/` record naming `tnhan`, but
  `TCK-20260801-MONITORING-WRITER-STATUS-STALE` remains unimplemented.  Its own AC
  permits ordinary lifecycle outputs for the candidate while restricting the historical
  target ticket to its three declared lifecycle-field edits.

## Mechanics/Engine Constraints

This tooling does not mutate `AuthoritativeState`, so the 32-phase engine pipeline is
not an execution path here.  The applicable system constraint is fail-closed
operational containment: no test may target the project root, no hook/config/provider
activation is authorized in this ticket, monitoring history is append-only, and the
existing scratch-only packages must not be weakened or repurposed.

## Safe Additive Architecture

Create a new library-only package, tentatively
`tools/agent_codex_realrepo_pilot_harness/`, separate from all existing packages.
It has two layers:

1. **Pure/injected preflight and proof layer.** A frozen `PilotHarnessContext` takes
   `repo_root`, candidate ticket id/path, request path, a predeclared expected-write
   policy, execution identity, approved hook/writer sets, and an injected environment.
   Every derived path is resolved and checked under the supplied root *before* it is
   opened. Normal preflight rejects the actual project root, a root inside it, symlink
   escapes, malformed/mismatched request, missing owner or rollback text, invalid
   identity, widened surface, absent candidate, invalid claim evidence, and an unsafe
   expected-write policy before any write or subprocess construction.
2. **Narrow future live boundary.** It is the only module allowed to import
   `subprocess`, and exposes no CLI.  It requires a non-forgeable-in-normal-flow
   `LivePilotAuthority` returned only after two independent exact-value checks:
   existing `CODEX_LIVE_PILOT_HUMAN_SIGNOFF=1` plus a new,
   pilot-specific `CODEX_REALREPO_PILOT_LIVE_CONSENT=1`.  The replay consent variable
   must not be reused because it authorizes a scratch replay, not a state-changing
   candidate.  The live boundary checks authority before constructing a command; no
   test calls it against the project root or a real `codex` binary.

The invocation itself is injected as a callable/command builder in tests.  Tests may
exercise a live-shaped *scratch* repository with a fake invoker, but production
execution may only call the one boundary after all preflight evidence and both gates
pass.  This creates future capability without treating test success as a pilot.

## Required Evidence and Ordering

1. Validate ID format and all paths with zero I/O to derived paths; resolve and prove
   containment before reads.
2. Refuse normal/test use of the actual project root.  Load the candidate and request
   only from the injected root; validate `human_owner`, rollback summary, request-ticket
   match, execution identity, and the existing evidenced surface subset.
3. Capture a baseline of the complete relevant tree and per-file monitoring line
   prefixes; take an exclusive per-ticket claim before enabling/invoking anything.
   Reuse the executor's ownership-verified `fcntl.flock` claim protocol rather than
   copying it.  An active claim is never reclaimed by age.
4. Validate an immutable expected-write policy.  It must allow only the candidate's
   declared target file edits, its normal workflow lifecycle paths (candidate ticket,
   its artifacts, working log, registry), declared pilot-evidence paths, and append-only
   monitoring files.  It must reject every other ticket, config, source, request, and
   monitoring rewrite.
5. Only after all non-live checks succeed may the live boundary check both fresh
   authority gates and call the injected production invoker.  This ticket never takes
   that branch.
6. Post-run proof requires (a) every pre-existing monitoring line is unchanged and in
   order, (b) every changed non-monitoring path is allowlisted, (c) changed historical
   target bytes conform exactly to the candidate's declared edit policy, (d) any new
   monitoring suffix satisfies the declared record/identity policy, and (e) the claim
   terminalizes under the original execution identity.  Any partial failure is failure,
   never success.
7. Rollback is a distinct one-action injected operation.  Snapshot the approved
   rollback artifact before enable, restore its exact bytes, then prove that config is
   hook-free and that non-rollback paths did not change.  The normal candidate lifecycle
   and append-only records are retained as evidence, not deleted or rewritten.

## Reuse Boundaries

Reuse guardrail manifest/surface/sign-off/baseline code, executor claim protocol, the
shared monitoring manifest helpers, and `DashboardCache` only through public APIs.
Do not import replay `invoker.py`, private writer internals, or existing package tests.
Do not change `.codex/config.toml`, register a hook, set process environment, or write
real provider-attributed monitoring data in this ticket.

## Parity Ledger Overlap

No simulation behavior changes.  This is AI operational tooling, so no existing
`docs/parity_ledger/` entry maps to it; parity phase should record an explicit
not-applicable disposition, not create an artificial simulation entry.

## Prior Work

- `TCK-20260731-CODEX-PILOT-EXECUTOR` supplies the scratch claim, exact monitoring
  suffix, and dashboard-reader proof patterns.
- `TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS` supplies the request, surface, prefix,
  sign-off, and scratch rollback mechanisms.
- `TCK-20260721-CODEX-REPLAY-PARITY` supplies strict consent ordering and a contained
  subprocess style, but its no-real-repo-mutation goal is intentionally incompatible
  with this new package.

## Risks and Open Questions

There is one real design decision for Architecture Review: **the future hook transport is
not yet specified.** The project config must remain hook-free in this ticket, while a
future pilot desires a minimal PostToolUse evidence surface.  The harness should accept
a reviewed future invocation/config adapter rather than inventing a config strategy now.
This is not a blocker to building the generic non-live harness, but it must remain an
explicit preflight requirement before any future actual pilot.

## Anti-Drift Hazards

- Do not convert the guardrail or executor packages into live-capable code.
- Do not use `CODEX_REPLAY_PARITY_LIVE_CONSENT` for a different operational meaning.
- Do not equate prefix preservation with whole-file equality, nor allow arbitrary
  append rows without an expected-suffix/identity policy.
- Do not make a live authority object constructible from ticket selection, a passing
  test, or a truthy environment value.
- Do not test against the real repository even with a mocked subprocess.
