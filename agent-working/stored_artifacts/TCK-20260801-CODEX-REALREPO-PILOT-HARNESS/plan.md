---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260801-CODEX-REALREPO-PILOT-HARNESS
artifact_type: plan
tags: [ai, workflows, hooks, agent-monitoring, rollback, testing]
---

# Plan — TCK-20260801-CODEX-REALREPO-PILOT-HARNESS

## Safety boundary

Create a new additive library package only. Ordinary and test entry points
always reject the canonical project root; its tests construct minimal tmp-path
repositories and never exercise the separate live-only root admission. Do not modify existing guardrail/executor/shadow/replay packages,
`.codex/config.toml`, hook registration, candidate ticket, canonical workflow,
or real monitoring data. No test invokes Codex or a real subprocess.

## Steps

1. Add `tools/agent_codex_realrepo_pilot_harness/` with immutable context,
   expected-write-policy, result, and named-refusal models. Validate ticket IDs
   and resolve/contain every path before derived-path I/O. Refuse the canonical
   project root, descendants, symlink escapes, and unsafe target/config/request
   paths from every ordinary/test entry. A separate private live-boundary
   admission performs reviewed root-identity validation only after dual authority
   gates and no-write preflight; this ticket never exercises that admission.

2. Build a pure preflight/proof layer that reuses public guardrail request,
   surface, sign-off, monitoring-prefix, and executor claim APIs. Require
   candidate/request match, genuine owner/rollback text, valid Codex execution
   identity, approved surface, no active competing claim, baseline evidence,
   and a trusted versioned policy artifact before any write/invoker creation.
   The contained policy is bound to candidate/request and baseline by hash and
   declares exact target field transitions, lifecycle/evidence path classes,
   and monitoring suffix identity/sequence rows. Post-run proof uses the
   captured policy, never a mutable re-read.

3. Implement a narrow future-live boundary as the package's sole subprocess
   seam, injectable in tests and with no CLI entry point. It accepts a private
   authority token issued only in normal public flow after exact, independent pilot sign-off and a distinct
   real-repository consent gate. It checks authority before command construction.
   Tests prove refusal before construction and one scratch-only fake-invoker
   success after both gates; they never invoke a process. The future hook/config transport is injected and
   must be separately reviewed before a real pilot.

4. Add snapshot/proof logic: preserve all monitoring prefixes, validate a
   declared suffix identity/sequence, permit only declared candidate lifecycle,
   artifact, registry, working-log, and pilot-evidence writes, and require the
   historical target ticket to match exactly its declared three-field edit. Reject
   unrelated ticket/source/request/config paths and monitoring rewrites/deletions.

5. Define a narrow injected scratch-config adapter with capture, enable, restore,
   and hook-free-verification operations only; it receives no arbitrary command
   or repository-wide writer. Add a one-action rollback proof for scratch config only. It restores
   exact baseline bytes, verifies post-rollback hook-free state, retains expected
   lifecycle/append evidence, rejects any unintended path changes, and refuses
   rollback/terminalization by a different execution identity.

6. Write tests first in `tests/agent_codex_realrepo_pilot_harness/`, including a
   session guard asserting actual project config/tickets/pilot requests/monitoring
   bytes are unchanged. Exercise root containment, all gate failures, authority
   ordering, multiprocessing claims, allowlisted diffs, prefix/suffix evidence,
   rollback, and static subprocess isolation. Run all protected package suites.

## Acceptance map

| AC | Proof |
| --- | --- |
| scratch only | root-refusal matrix and actual-worktree teardown guard |
| fail closed | independent no-write gate matrix |
| future authority only | exact dual-gate/capability tests with fake invoker |
| expected writes/prefix | scratch before/after allowlist and suffix tests |
| existing invariants | unchanged protected regression suites |
