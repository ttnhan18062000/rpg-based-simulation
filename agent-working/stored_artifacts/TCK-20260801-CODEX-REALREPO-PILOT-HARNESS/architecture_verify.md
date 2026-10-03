---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260801-CODEX-REALREPO-PILOT-HARNESS
artifact_type: plan
verdict: NEEDS_CHANGES
---

# Architecture Verify — TCK-20260801-CODEX-REALREPO-PILOT-HARNESS

## Verdict

**NEEDS_CHANGES.** The implementation is safely non-live, and its isolated new
suite passes, but it does not implement the approved preflight/proof architecture
or several ticket acceptance criteria. It must not advance to Test, Parity, or
Finalize.

## Independent evidence

- Ran `.venv/bin/python -m pytest -q tests/agent_codex_realrepo_pilot_harness`:
  **14 passed**. This verifies the claimed 14 focused parametrized cases.
- Ran the exact combined scoped command from `test_plan.md`: collection fails before
  execution because both the new suite and `tests/agent_codex_pilot_executor/` expose
  a top-level `test_preflight.py`. Pytest imports the new module as `test_preflight`,
  then refuses the executor module as an import mismatch. Rename the new module or
  make test-module package identity unambiguous; do not weaken collection safeguards.
- Ran the protected suites excluding the colliding new suite: **217 passed, 5 skipped,
  4 failed**. The four failures are the known pre-existing runtime-shadow fixture
  version brittleness: its fixtures/tests still assert workflow version `1`, whereas
  the previously approved continuation-policy change set the shared workflow to `2`.
  They are unrelated to this harness diff, but the test record must report all four,
  not call the protected scope clean.
- Static inspection of `tools/agent_codex_realrepo_pilot_harness/` found no `codex
  exec`, `subprocess`, CLI, hook registration, project config write, or monitoring
  writer. That correctly preserves the non-live boundary, but is insufficient for
  the required future-capable, fail-closed harness.

## Required corrections

1. **Implement the actual preflight context and gates.** `ordinary_preflight()` only
   rejects the project root and then calls a `NotImplementedError` placeholder. It
   neither loads/validates the candidate or pilot request nor validates owner,
   rollback text, execution identity, approved surface, claim, baseline, or path
   containment evidence. Reuse the approved *public* guardrail/executor APIs named
   in the plan; each failure must be proven before a write or invoker creation.

2. **Restore the approved live-boundary ordering.** `invoke_after_authority()` accepts
   any string as `scratch_root` and directly calls any injected callable after a
   type check. No private live-only root admission, no no-write preflight, and no
   root identity validation precedes it. Preserve the ticket's non-live test rule,
   but implement a structurally separate boundary whose real-root path is reachable
   only after both exact authority values *and* successful immutable preflight.
   The authority object alone is not the required containment proof.

3. **Complete immutable expected-write-policy binding and post-run proof.** The
   current JSON model binds only a candidate ID, one relative target string, and free
   form transition strings. It omits request and baseline hashes, exact three-field
   target-edit validation, declared lifecycle/evidence path classes, and monitoring
   suffix identity/sequence rows. `assert_expected_changes()` is merely a caller
   supplied path-set comparison; `assert_monitoring_prefixes()` permits arbitrary
   appended lines. Capture and verify the validated policy rather than accepting
   caller-provided allowlists or rereading mutable policy at post-run time.

4. **Contain the rollback adapter to the injected scratch root.** `ScratchConfigAdapter`
   rejects only the one canonical project-config path. It can write any other caller
   supplied absolute path, has no root containment proof, and receives a caller
   supplied baseline rather than capturing it through the bounded adapter seam.
   Add scratch-root containment, capture/enable/restore/hook-free verification, and
   post-rollback proof that unintended paths did not change while expected lifecycle
   and append-only evidence remain. Retain the existing cross-identity negative case
   and add claim terminalization ownership coverage.

5. **Add the missing test-plan coverage.** The 14 focused tests do not cover the
   required malformed request/owner/rollback/identity/surface/claim/baseline matrix,
   traversal-shaped ticket IDs, root child/symlink refusal, static boundary scan,
   policy request/baseline/mutation mismatch, multiprocessing claim races,
   exact three-field historical-ticket proof, rejected monitoring suffixes, or
   rollback non-config path preservation. Write these tests first, using only
   tmp-path roots. The session worktree snapshot guard is good and must remain.

## What is approved to retain

- The package remains library-only and has no process/CLI/hook/config/monitoring
  activation code.
- The exact-value dual-consent checks and fake-invoker-only test style are directionally
  correct, provided they become part of the complete gated preflight/boundary flow.
- Project-root refusal before the placeholder loader, policy escaped-path refusal, the
  project-config refusal, monitoring-prefix preservation primitive, and
  cross-identity config restore test are useful partial building blocks.

## Scope guard

Fix only this additive harness and its tests/artifacts. Do not run a live invocation,
register a hook, change `.codex/config.toml`, write provider-attributed project
monitoring data, implement the standing candidate ticket, or repair the unrelated
runtime-shadow version fixtures in this ticket.
