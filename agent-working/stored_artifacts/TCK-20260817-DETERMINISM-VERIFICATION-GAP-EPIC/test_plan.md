---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC
artifact_type: test_plan
tags: [engine, determinism]
---

# Test Plan — TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC

This plan assumes the recommended resolution (investigation.md §5): **path (b)** — label
`DEGRADED`/`SURVIVAL` run outputs as reduced-verification via `ShutdownResult` and
`RunManifest`, with a new cumulative mode-tracking mechanism on `Kernel`. If Plan instead
chooses path (a), the "New Tests Required" section below should be replaced with tests asserting
the new always-on comparison fires correctly and stays within the measured perf budget from
investigation.md §4 (a benchmark-style test, not covered here since path (a) is not recommended).

## Regression Surface

Existing tests that must keep passing — grouped by domain, since the change touches
kernel persistence, guards, shutdown, and run-artifact output.

**Unit — kernel guards / hashing:**
- `tests/unit/core/test_engine_integrity.py` — `test_bit_identical_determinism`,
  `test_isolation_guard_trigger`, `test_gross_isolation_guard_triggers_on_tick_change`,
  `test_gross_isolation_guard_triggers_on_entity_count_change`,
  `test_gross_isolation_guard_silent_on_clean_state` (Tier 1/Tier 2 guard behavior must be
  unchanged — this ticket does not touch `_guard_stability`/`_guard_gross_isolation` under
  path (b)).
- `tests/unit/engine/test_hash_scheduler.py` — full `CanonicalHashScheduler`/
  `BudgetedCanonicalHasher` suite, including `TestArchitectureNoDirectHashInNormalTickPath`
  (lines 180-209), which guards the exact `replay_allowed and (audit_mode or
  replay_richness=="FULL")` condition this ticket's docs describe.
- `tests/unit/engine/test_resource_budget_gate.py` — `BudgetedCanonicalHasher` pressure-report
  behavior must be unaffected.
- `tests/unit/core/test_operational_flags.py` — `audit_mode` flag plumbing.
- `tests/unit/core/test_degradation_order.py` — `RuntimeMode`/`GovernorPolicy.from_mode`
  ordering must be unaffected.

**Integration — kernel / replay / determinism:**
- `tests/integration/kernel/test_determinism_suite.py` — canonical hash reproducibility
  (NORMAL-mode path must be bit-identical to before).
- `tests/integration/kernel/test_checkpoint_reproducibility.py`
- `tests/integration/kernel/test_replay_fidelity.py`
- `tests/integration/kernel/test_long_run_determinism.py`
- `tests/integration/kernel/test_snapshot_integrity.py`
- `tests/integration/kernel/test_kernel_boundaries.py`
- `tests/integration/pipeline/test_no_hidden_mutation.py`,
  `tests/integration/pipeline/test_phase_order.py`,
  `tests/integration/pipeline/test_governance_isolation.py`
- `tests/unit/kernel/test_replay_overflow.py` — exercises all four `GovernorPolicy` instances
  (NORMAL/CONSTRAINED/DEGRADED/SURVIVAL replay_richness values) directly; must keep passing
  unchanged since path (b) does not alter `GovernorPolicy`.
- `tests/unit/kernel/test_worker_equivalence.py`

**Observability / run-artifact:**
- `tests/integration/observability/test_run_artifact_flow.py` —
  `test_kernel_run_produces_manifest_and_events`, `test_kernel_state_parity_invariants`.
  This is the file `RunManifest` schema changes are most likely to break; must be updated
  (not just re-run) if `RunManifest` gains a new field, and re-verified for backward
  compatibility (`Optional[...]` field, default `None`/`"FULL"` so existing manifest JSON
  consumers don't break).
- `tests/integration/observability/test_cognition_snapshot_artifact.py`

**Certification:**
- `tests/certification/test_evidence_levels.py`
- `tests/certification/test_event_observability_parity.py`
- `tests/certification/test_resilience_recovery.py`

## New Tests Required

Per acceptance criteria ("DEGRADED/SURVIVAL run outputs are explicitly labeled as
reduced-verification" and "the full Tier-2 fingerprint / canonical hash remains conditional"):

1. **`test_shutdown_result_flags_reduced_verification_after_degraded_run`**
   - Category: unit
   - Verifies: a `Kernel` run that transitions into `DEGRADED` mode at some point before
     `shutdown()` produces a `ShutdownResult` (or equivalent new field) whose
     verification-level field indicates reduced verification, even if the mode had since
     recovered to `NORMAL` by the time `shutdown()` is called (this is the cumulative-tracking
     gap identified in investigation.md §5 — must be tested explicitly, not just the
     current-mode-at-shutdown case, since that's the easy path a naive implementation might
     miss).
   - Location: `tests/unit/core/test_engine_integrity.py` or a new
     `tests/unit/kernel/test_verification_level.py` (Plan/Implement to decide based on final
     field location).

2. **`test_shutdown_result_full_verification_on_normal_run`**
   - Category: unit
   - Verifies: a run that stays in NORMAL/CONSTRAINED the entire time produces a
     verification-level field indicating full verification (regression guard against the new
     field defaulting to "reduced" incorrectly).
   - Location: same file as test 1.

3. **`test_shutdown_result_flags_reduced_verification_after_survival_run`**
   - Category: unit
   - Verifies: a run that enters `SURVIVAL` mode (where `replay_allowed=False` and no
     `TICK_END` event is emitted at all) still produces a correctly-flagged
     verification-level field — this is the mode with the least existing observability
     surface (no TICK_END trail to infer from), so the cumulative tracker must not silently
     rely on scanning TICK_END events alone.
   - Location: same file as test 1.

4. **`test_run_manifest_includes_verification_level_field`**
   - Category: integration
   - Verifies: `RunManifest` written to `data/runs/{run_id}/manifest.json` (via
     `RunArtifactRepository.update_manifest`) includes the new field with the correct value
     for a DEGRADED-touching run, end-to-end through a real (non-mocked) `Kernel` run.
   - Location: `tests/integration/observability/test_run_artifact_flow.py`.

5. **`test_run_report_metadata_surfaces_verification_level`**
   - Category: integration
   - Verifies: `RunReportGenerator.generate()`'s `metadata` dict (and therefore
     `run_report.json`) includes the new field, sourced from `ShutdownResult`, alongside the
     existing `final_hash`/`overall_outcome` fields — this is the primary "consumer of run
     results" surface the ticket's acceptance criteria refers to.
   - Location: a new test in `tests/integration/observability/` alongside
     `test_run_artifact_flow.py`, or a new `tests/unit/observability/test_run_report_metadata.py`
     if `RunReportGenerator.generate()` can be exercised with a fake `shutdown_result` without a
     full kernel run.

6. **`test_tier2_fingerprint_guard_still_audit_mode_gated`**
   - Category: architecture guard
   - Verifies: `_guard_stability()` is still only invoked when `audit_mode=True` (i.e., lines
     368-370 and 383-393 of `kernel.py` are unchanged) — an explicit regression guard against
     accidentally making the Tier-2 check always-on while implementing the reduced-verification
     label, protecting the ticket's own Out-of-Scope boundary.
   - Location: `tests/unit/core/test_engine_integrity.py` (extend near
     `test_isolation_guard_trigger`).

7. **`test_canonical_hash_still_conditional_on_replay_richness`**
   - Category: architecture guard
   - Verifies: `_phase_persistence()` still returns/emits `"SKIPPED"` in DEGRADED mode and no
     `TICK_END` event in SURVIVAL mode — i.e. the underlying hash computation itself is
     unchanged; only a new reporting field is added. Protects against accidentally "fixing" the
     conditional behavior itself, which is explicitly Out of Scope.
   - Location: extend `tests/unit/engine/test_hash_scheduler.py` or add to
     `tests/integration/kernel/test_determinism_suite.py`.

## Scoped Pytest Commands

```bash
# Kernel guards, hashing, and shutdown/lifecycle unit coverage
pytest tests/unit/core/test_engine_integrity.py tests/unit/core/test_degradation_order.py \
       tests/unit/core/test_operational_flags.py tests/unit/engine/test_hash_scheduler.py \
       tests/unit/engine/test_resource_budget_gate.py tests/unit/kernel/ -v

# Integration determinism / replay / pipeline regression surface
pytest tests/integration/kernel/ tests/integration/pipeline/ -v

# Run-artifact / observability output regression surface
pytest tests/integration/observability/ -v

# Certification harness (audit_mode / evidence levels) — must remain unaffected
pytest tests/certification/ -v
```

Do not run `pytest tests/` in full. If time-constrained, the minimum required scoped set for
this ticket's own acceptance criteria is:

```bash
pytest tests/unit/core/test_engine_integrity.py tests/unit/engine/test_hash_scheduler.py \
       tests/integration/kernel/test_determinism_suite.py \
       tests/integration/observability/test_run_artifact_flow.py -v
```

## Anti-Drift Test Guards

- **New test 6 and 7 above are the primary anti-drift guards**: they exist specifically to
  catch an implementation that accidentally widens the Tier-2 guard or the canonical-hash gate
  itself while trying to add labeling — the single most likely scope-creep failure mode
  identified in investigation.md §4.
- `tests/unit/kernel/test_replay_overflow.py`'s direct construction of all four
  `GovernorPolicy` variants (NORMAL/CONSTRAINED/DEGRADED/SURVIVAL) should keep passing
  unmodified — if this ticket's implementation needs to change `GovernorPolicy` itself to add
  the new field, that is a signal the change has grown beyond path (b)'s intended scope
  (labeling run *outputs*, not changing the *policy* that drives per-tick hashing).
- `tests/unit/engine/test_hash_scheduler.py::TestArchitectureNoDirectHashInNormalTickPath::test_no_casual_get_hash_call_when_replay_disabled`
  should keep passing unmodified — it guards that `CanonicalStateHasher.get_hash` is never
  called when `replay_allowed=False`; this must remain true even after the new
  reduced-verification field is added (the field is derived from tracked mode, not from
  triggering an extra hash call in SURVIVAL mode).
- If `RunManifest` gains a new field, verify existing manifest-consuming code
  (`RunArtifactRepository`, dashboard/tooling readers) tolerates a missing/default value for
  manifests written by an older engine version — the field must be `Optional` with a safe
  default, not a required field that breaks deserialization of pre-existing `data/runs/`
  artifacts or fixture JSON used by other tests (e.g.
  `tests/tools/fixtures/kgmcp_phase5_working_log_snapshot.json` if it embeds manifest-shaped
  data).
