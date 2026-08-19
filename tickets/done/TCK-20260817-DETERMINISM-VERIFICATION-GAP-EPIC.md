---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC
phase: done
date: 2026-08-17
tags: [engine, determinism, observability]
---

# TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC

## Title
Close (or explicitly label) the audit-mode-only determinism/mutation-guard verification gap

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P3

## Request Summary
The kernel's strongest correctness proofs are mode-dependent: the Tier-2 SHA-256 fingerprint
check that would catch a subtle off-path field mutation during a read-only phase is gated behind
`audit_mode=True`, invisible in default production runs; the canonical hash comparison is skipped
in DEGRADED mode and absent in SURVIVAL mode — unavailable exactly when the system is under the
load most likely to produce a subtle bug. The source audit explicitly frames this as the
lowest-urgency item in the whole roadmap: only worth pursuing if off-path mutation bugs have
actually occurred or are a live concern.

## Scope
Full findings are in `docs/plans/determinism_verification_gap_epic.md`. Per the source audit's
own framing, this is the lowest-urgency item in the whole roadmap — only worth picking up if
off-path mutation bugs have actually occurred or are a live concern. Concrete scope when picked up:
- Consider a cheap, always-on partial/sampled fingerprint as an alternative to the current
  all-or-nothing `audit_mode` gating in `src/engine/kernel.py`.
- At minimum, if a cheaper always-on check isn't pursued: flag `DEGRADED`/`SURVIVAL` run outputs
  as "reduced verification" so a consumer of that run's results knows the strongest proof wasn't
  applied.

## Out of Scope
- Making the full Tier-2 fingerprint or canonical hash always-on unconditionally — a genuine
  cost/coverage tradeoff per the source audit, not a bug to eliminate outright.

## Acceptance Criteria
- [x] Either a cheap always-on partial fingerprint exists and narrows the current
      audit-mode-only gap, or `DEGRADED`/`SURVIVAL` run outputs are explicitly labeled as
      reduced-verification.
- [x] The full Tier-2 fingerprint / canonical hash remains conditional (not made unconditionally
      always-on) — this is a deliberate cost/coverage tradeoff, not a bug to eliminate.

## Related Tickets
- TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC (parent tracking epic)

## Related Docs
- docs/plans/determinism_verification_gap_epic.md
- docs/plans/architecture_resilience_remediation_roadmap.md
- docs/audits/D23_architecture_resilience.md
- docs/engine/kernel.md

## Related Stored Artifacts
- `stored_artifacts/TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC/` (plan.md, investigation.md,
  test_plan.md) — migrated from `staging_artifacts/` at ticket close (Finalize phase).

## Related Code Areas
- src/engine/kernel.py (audit_mode-gated fingerprint/hash checks)

## Assumptions / Open Questions
- Whether off-path mutation bugs have actually occurred or are a live concern is unknown to this
  ticket — that's the deciding factor for whether this ticket should be picked up at all.
- **Downgraded from epic to standard tier (2026-08-18):** one of 10 sub-epics under
  `TCK-20260817-CODEBASE-HEALTH-RESILIENCE-EPIC`; a single contained fix to one file
  (`src/engine/kernel.py`) with two concrete alternative resolutions — one standard ticket, not a
  multi-ticket initiative. `staging_artifacts/TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC/`
  not yet created. Still gated on the "is this a live concern" question above before pickup.

## Implementation Notes
Implemented path (b) from `staging_artifacts/TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC/plan.md`
exactly as approved, all 7 steps:

1. Added `max_mode_reached: RuntimeMode = RuntimeMode.NORMAL` to `RuntimeStatus`
   (`src/engine/runtime_status.py`), immediately after `last_transition_tick`. Updated
   `reset_dwell()` to also do `self.max_mode_reached = RuntimeMode(max(self.max_mode_reached,
   new_mode))` — an `IntEnum` max, so it tracks the worst mode ever reached regardless of later
   recovery. All three existing `reset_dwell()` call sites in `ResourceGovernor`
   (`src/engine/governor.py:45,51,68`) get correct cumulative tracking automatically, no
   call-site changes needed.
2. Added `verification_level: str = "FULL"` to `ShutdownResult` (`src/core/lifecycle.py`),
   appended after `failure_reason`. In `Kernel.shutdown()` (`src/engine/kernel.py`), computed
   `verification_level = "REDUCED" if self._status.max_mode_reached >= RuntimeMode.DEGRADED
   else "FULL"` immediately before the `return ShutdownResult(...)` and threaded it into the
   constructor call.
3. Added `verification_level: Optional[str] = None` to the `RunManifest` pydantic model
   (`src/observability/reporting/artifact_repository.py`), appended after `state_hash`. Passed
   `verification_level=verification_level` into the existing `update_manifest()` call in
   `Kernel.shutdown()` (same call site that already passes `state_hash=final_hash`).
4. Added `"verification_level": getattr(shutdown_result, "verification_level", "FULL")` to
   `RunReportGenerator.generate()`'s metadata dict (`src/observability/reporting/run_report.py`),
   using `getattr` with a `"FULL"` default because `SyntheticShutdownResult`
   (`src/observability/anomaly/pipeline.py`) is a second, duck-typed producer without this
   attribute — left untouched per plan.
5. Added `tests/unit/kernel/test_verification_level.py` with the 3 specified tests, driving
   `kernel._status.reset_dwell(...)` directly (DEGRADED→NORMAL recovery, CONSTRAINED→NORMAL,
   and SURVIVAL) then calling `kernel.shutdown()` and asserting `verification_level`.
6. Added `test_tier2_fingerprint_guard_still_audit_mode_gated` to
   `tests/unit/core/test_engine_integrity.py` (patches `Kernel._guard_stability` /
   `Kernel._guard_gross_isolation` at the class level — `Kernel` uses `__slots__` so
   instance-level `patch.object` fails with `AttributeError: read-only`; patching the class
   works and is the correct pattern here) and `test_canonical_hash_still_conditional_on_replay_richness`
   to `tests/unit/engine/test_hash_scheduler.py` (drives a real `Kernel._phase_persistence()`
   call under DEGRADED and SURVIVAL policies, asserting `CanonicalStateHasher.get_hash` is never
   called and the `"SKIPPED"` sentinel / no-`TICK_END` behavior is unchanged).
7. Updated `docs/engine/known_limitations.md` §2.4 (new "Run-level `verification_level` label"
   subsection), `docs/engine/kernel.md` (itemized `ShutdownResult`'s fields under "Resource
   Snapshot and Lifecycle Supervisor", plus a cross-reference paragraph in "State Hashing in
   Phase 7"), and `docs/parity_ledger/infrastructure.yaml` (appended a note to `INFRA-223`'s
   `v2_evidence`, added new entry `INFRA-363`; re-ran the `grep -oE "INFRA-[0-9]+" ... | tail -1`
   check at implementation time and confirmed `INFRA-362` was still the highest id, so `INFRA-363`
   was correct with no id collision).

No deviations from plan.md — all field names, values (`"FULL"`/`"REDUCED"`), hook site
(`reset_dwell()`), and scope guards were followed exactly as specified. `staging_artifacts/.../plan.md`
does not need a Deviations section.

## Test Summary
Ran the exact scoped commands specified for this ticket, using `.venv/bin/python3` (bare
`python3` lacks pydantic on this machine):

- `tests/unit/kernel/test_verification_level.py tests/unit/core/test_engine_integrity.py
  tests/unit/engine/test_hash_scheduler.py tests/unit/core/test_degradation_order.py
  tests/unit/core/test_operational_flags.py tests/unit/engine/test_resource_budget_gate.py
  tests/unit/kernel/` — **107 passed** (includes all 5 new tests: 3 in
  `test_verification_level.py`, 1 in `test_engine_integrity.py`, 1 in `test_hash_scheduler.py`).
- `tests/integration/kernel/ tests/integration/pipeline/` — **177 passed, 1 failed**
  (`test_long_run_determinism.py::test_1000_tick_determinism`). Confirmed via `git stash`
  that this failure is **pre-existing and identical without this ticket's changes** — a
  1000-real-tick test that exceeds `tests/conftest.py`'s resource-time watchdog on this
  machine's current load, unrelated to `verification_level`.
- `tests/integration/observability/` — **97 passed, 5 skipped** (Redis-stream tests skipped by
  design). `test_run_artifact_flow.py` (the file most likely to break from the `RunManifest`
  schema change) passed unmodified — the new field is `Optional[str] = None`, fully backward
  compatible.
- `tests/certification/` — **71 passed, 1 skipped, 3 failed, 1 error**. Confirmed via `git
  stash` that all 4 failures/errors (`test_cert_long_run_stability.py`'s three tests and
  `test_world_compile_determinism.py::test_compile_report_contents`) are **pre-existing and
  identical without this ticket's changes** — unrelated long-run-timing and world-compile
  issues, not caused by `verification_level`.

`make knowledge-index-update` was run after the `docs/` edits (21 files re-embedded, 2864 from
cache).

## Files Changed
- `src/engine/runtime_status.py`
- `src/core/lifecycle.py`
- `src/engine/kernel.py`
- `src/observability/reporting/artifact_repository.py`
- `src/observability/reporting/run_report.py`
- `tests/unit/kernel/test_verification_level.py` (new)
- `tests/unit/core/test_engine_integrity.py`
- `tests/unit/engine/test_hash_scheduler.py`
- `docs/engine/known_limitations.md`
- `docs/engine/kernel.md`
- `docs/parity_ledger/infrastructure.yaml`
- `staging_artifacts/TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC/investigation.md` (produced
  by the prior Investigate phase of this run, not by this Implement pass)
- `staging_artifacts/TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC/plan.md` (produced by the
  prior Plan phase of this run, not by this Implement pass)
- `staging_artifacts/TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC/test_plan.md` (produced by
  the prior Investigate phase of this run, not by this Implement pass)
- `tickets/inprogress/TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC.md` (this file)
- `agent-monitoring/tools.jsonl` (auto-updated monitoring log)

## Completion Summary
Implemented path (b) (per investigation.md §4/§5): DEGRADED/SURVIVAL run outputs now carry an
explicit, truthful `verification_level` (`"FULL"`/`"REDUCED"`) label instead of an always-on
Tier-2 fingerprint. A new cumulative `RuntimeStatus.max_mode_reached` field (updated inside
`reset_dwell()`) tracks the worst `RuntimeMode` reached across a run, independent of the replay
stream, so it correctly covers both mid-run recovery and SURVIVAL mode (no `TICK_END` trail).
`Kernel.shutdown()` derives `verification_level` from it and surfaces the value on
`ShutdownResult`, `RunManifest`, and `run_report.json`/`.md` metadata. The Tier-2
`audit_mode`-gated fingerprint guard and the DEGRADED/SURVIVAL canonical-hash conditional gate
are unchanged — verified by two new architecture-guard tests (Step 6) — satisfying both
acceptance criteria. Docs (`known_limitations.md`, `kernel.md`) and the parity ledger
(`INFRA-223` note + new `INFRA-363` entry) were updated to match. All 5 new tests pass; the
only test failures encountered are pre-existing, confirmed unrelated via `git stash` comparison.
