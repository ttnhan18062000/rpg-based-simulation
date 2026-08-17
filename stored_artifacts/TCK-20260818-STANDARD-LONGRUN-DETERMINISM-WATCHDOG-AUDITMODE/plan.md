---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE
artifact_type: plan
tags: [engine, determinism, bug, debugging, root-cause, testing]
---

# Plan — TCK-20260818-STANDARD-LONGRUN-DETERMINISM-WATCHDOG-AUDITMODE

## Scope guard

Fix ONLY the fully-understood, fully-verified root cause (Mechanism A: missing `audit_mode` flag
in a strict hash-equality test). Do NOT touch `src/engine/kernel.py`'s watchdog/throttle logic
(matches the established, explicit F6/`docs/audits/D06_longrun_health.md` precedent — that
mechanism is documented, intentional, corpus-wide engine behavior, not a defect). Do NOT attempt a
speculative fix for Mechanism B (the deeper, audit_mode-immune combat/strategic-cognition
divergence) — report it precisely, open a follow-up ticket, per the parent task's explicit
instruction to prefer honest non-completion over guessing on a P0/P1 architectural bug.

## Steps

1. **`tests/integration/world/test_long_run_stability.py`** — add `flags={"audit_mode": True}` to
   both `Kernel(profile, state, rng)` constructions inside `run_sim()` (used identically for both
   Run 1 and Run 2). This is the minimal, doc-mandated (`docs/engine/deterministic_execution.md`
   Extension Rule 5), precedent-matching (`src/certification/harness.py`,
   `tests/unit/kernel/test_replay_determinism.py`,
   `LongRunStabilityHarness.verify_determinism_parity()`) fix. Do not change any assertions in this
   file — the fix removes the actual source of non-determinism, it does not touch the check.

2. **`docs/audits/D06_longrun_health.md`** — append a new finding, **F7**, documenting Mechanism B
   (the audit_mode-immune divergence in the `metropolis` scenario) in the same evidence-disclosure
   style as F6, so a future ticket does not have to rediscover it from scratch (matches F6's own
   stated ethos: "flagged so a future audit does not have to rediscover the mechanism from
   scratch"). Add a corresponding row to the "Key Findings Summary" table.

3. **`docs/parity_ledger/infrastructure.yaml`** — F6/INFRA-273 already fully covers Mechanism A;
   no edit needed there (this ticket does not change `kernel.py`'s throttle behavior, only a
   test's flag usage — not a production behavior change requiring ledger update). Mechanism B has
   no existing parity ledger entry; given it is reported but not fixed, and no `v2_evidence`/
   `test_path` exists yet to cite (fixing it is out of scope), a new ledger entry is deferred to
   the follow-up ticket rather than added here half-formed — recorded instead in this ticket's
   Related Docs / Completion Summary for traceability.

4. Create the follow-up ticket stub is NOT created here (per repo convention, follow-up tickets
   are scoped and created when picked up, not pre-created as empty placeholders) — instead,
   Mechanism B's full findings are preserved in this ticket's `investigation.md` (moved to
   `stored_artifacts/` on close) and cross-referenced from `docs/audits/D06_longrun_health.md`'s
   new F7 entry, so the next ticket has a concrete starting point.

## Acceptance-criteria map

| AC | Step |
|---|---|
| Root cause identified with file:line evidence, confirmed by real bisection | Step 1-3 of investigation.md (worktree bisection + log evidence) |
| Spawn-collision RNG fix ruled out with real evidence, not assumed | Step 1 of investigation.md |
| `test_long_run_stability` passes deterministically (3+ repeated identical hashes) | Plan Step 1, verified in investigation.md Step 5 |
| TimeoutError classified (related or not) with evidence | Plan step N/A — investigation.md Step 4 (cross-validated by sibling ticket) |
| Mechanism B honestly reported, not guessed at / not silently fixed | investigation.md Step 3; plan Step 2 |
| No test assertion edited to force a pass | Confirmed — only the `Kernel(...)` flags argument changes, not any `assert` |
