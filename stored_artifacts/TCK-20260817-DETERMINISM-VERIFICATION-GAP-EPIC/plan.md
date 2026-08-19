---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC
artifact_type: plan
tags: [engine, determinism]
---

# Implementation Plan — TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC

## Summary

This plan implements **path (b)** only (per investigation.md §4/§5 and the ticket's Out of Scope
section): DEGRADED/SURVIVAL run outputs get an explicit, truthful `verification_level` label
("FULL" / "REDUCED") instead of an always-on Tier-2 fingerprint. The cumulative-tracking gap
identified in investigation.md §5 (nothing today tracks "was reduced verification active at any
point during the run," only the instantaneous `current_mode`) is closed by adding one new field,
`max_mode_reached`, to the existing non-authoritative `RuntimeStatus` dataclass
(`src/engine/runtime_status.py`), updated inside `RuntimeStatus.reset_dwell()` — the single
existing method that mutates `current_mode`, called from exactly three sites, all inside
`ResourceGovernor` (`src/engine/governor.py:45,51,68`). This is a **refinement of
investigation.md's suggested hook site**: investigation.md §5 suggested hooking the
`GovernorModeChanged` event-emission block (`kernel.py:960-976`), but that block sits inside
`_phase_observability()`, which returns early and never runs when
`ObservabilityConfig.get_mode() == ObservabilityMode.OFF` (`kernel.py:902-904`) — an
observability-OFF run would silently fail to track reduced verification if hooked there. Hooking
`reset_dwell()` instead is unconditional, and as a bonus already covers the mid-tick emergency
`force_mode()` throttling path (`kernel.py:594-595` → `governor.py:65-68`), which the
event-emission site also happens to cover but only as an indirect side effect.

The new field is deliberately non-authoritative: `RuntimeStatus` is documented in its own
docstring as "M5 Law: This state is isolated from AuthoritativeState and does not contaminate
simulation hashes" (`src/engine/runtime_status.py:15-16`). This resolves investigation.md's second
open question — the new tracking field is presentation/reporting information about *how* the run
was governed, not simulation-meaningful state that affects entity or world outcomes, so it
belongs alongside `current_mode` in `RuntimeStatus`, not on `AuthoritativeState`.

At shutdown, `Kernel.shutdown()` derives `verification_level = "REDUCED" if
self._status.max_mode_reached >= RuntimeMode.DEGRADED else "FULL"` and threads it through the
three existing "truthful run outcome" surfaces investigation.md §5 identified: `ShutdownResult`
(new field, defaulted for backward compat), `RunManifest` (new `Optional` field, populated at the
same `update_manifest()` call site that already sets `state_hash`), and
`RunReportGenerator.generate()`'s `metadata` dict (read defensively via `getattr` because a
second, duck-typed `shutdown_result` producer exists — `SyntheticShutdownResult` in
`src/observability/anomaly/pipeline.py:373-379` — which does not have this attribute). No file
inside `_tick_once_inner()`'s guard logic (`_guard_stability`, `_guard_gross_isolation`) or
`_phase_persistence()`'s hash-computation logic is touched by any step in this plan — Steps 6
add explicit regression tests proving that.

## Steps

### Step 1 — Add cumulative mode-tracking field to `RuntimeStatus`
**Files:** `src/engine/runtime_status.py`
**Change:** Add a new field `max_mode_reached: RuntimeMode = RuntimeMode.NORMAL` to the
`RuntimeStatus` dataclass, immediately after `last_transition_tick: int = 0`
(`src/engine/runtime_status.py:32`). Update `reset_dwell()`
(`src/engine/runtime_status.py:79-83`) to also update it:
```python
def reset_dwell(self, new_mode: RuntimeMode, current_tick: int) -> None:
    """Reset counters when a transition occurs."""
    self.current_mode = new_mode
    self.mode_dwell_ticks = 0
    self.last_transition_tick = current_tick
    self.max_mode_reached = RuntimeMode(max(self.max_mode_reached, new_mode))
```
`RuntimeMode` is an `IntEnum` (`src/core/governance.py:8-16`, NORMAL=0 < CONSTRAINED=1 <
DEGRADED=2 < SURVIVAL=3), so `max()` correctly tracks the worst (most-reduced-verification) mode
ever reached, regardless of later recovery.

**Other writers of `reset_dwell()` (verified by reading `src/engine/governor.py` directly, not
inferred):** exactly three call sites, all inside `ResourceGovernor`:
- `governor.py:45` — inside `evaluate()`, escalation branch (`indicated_mode > current_mode`).
- `governor.py:51` — inside `evaluate()`, de-escalation branch (dwell-time-gated recovery).
- `governor.py:68` — inside `force_mode()`, the mid-tick emergency throttle override called from
  `kernel.py:594-595` when a tick blows its compute budget during `_phase_resolution`.

All three run synchronously inside the single-threaded tick pipeline (no worker thread ever
mutates `self._status`), so there is no race between them — each tick calls `evaluate()` exactly
once (`kernel.py:520-556`, inside the governance phase), and `force_mode()` is an additional,
also-synchronous call within the same tick's resolution phase. Because the new field is updated
unconditionally inside `reset_dwell()` itself, all three existing writers automatically get
correct cumulative tracking with no per-call-site changes needed.

**Do NOT touch:** `current_mode`, `mode_dwell_ticks`, `previous_mode`,
`last_transition_tick` semantics; do not change `reset_dwell()`'s signature or any of its 3 call
sites in `governor.py`; do not touch `GovernorPolicy.from_mode()` (`src/engine/policy.py`) —
test_plan.md's Anti-Drift Test Guards explicitly flags a `GovernorPolicy` change as a signal of
scope creep beyond path (b).

**Verify:** Underlies tests 1 and 3 (Step 5) — a `RuntimeStatus` that transitions
NORMAL→DEGRADED→NORMAL must show `max_mode_reached == RuntimeMode.DEGRADED` after the sequence
even though `current_mode` ends at `NORMAL`.

---

### Step 2 — Add `verification_level` to `ShutdownResult`, computed in `Kernel.shutdown()`
**Files:** `src/core/lifecycle.py`, `src/engine/kernel.py`
**Change:** Add `verification_level: str = "FULL"` to the frozen `ShutdownResult` dataclass
(`src/core/lifecycle.py:15-24`), appended **after** `failure_reason` (the last existing field) so
field order stays backward compatible for positional construction (verified: all 5 existing
`ShutdownResult(...)` construction call sites —
`tests/integration/observability/test_report_v2.py:87,202`,
`tests/integration/observability/test_cognition_report_section.py:66,104`,
`tests/integration/observability/test_run_report_generator.py:56` — use keyword arguments
exclusively, none positional; confirmed by reading each site directly). Because the new field has
a default, none of these 5 sites need modification.

In `Kernel.shutdown()`, immediately before the existing `return ShutdownResult(...)` statement
(`src/engine/kernel.py:1176-1181`), compute:
```python
verification_level = "REDUCED" if self._status.max_mode_reached >= RuntimeMode.DEGRADED else "FULL"
```
`RuntimeMode` is already imported at module level in `kernel.py:15`
(`from src.core.governance import PressureSignals, RuntimeMode`) — no new import needed. Pass
`verification_level=verification_level` as the new kwarg to `ShutdownResult(...)`.

**Do NOT touch:** `final_tick`, `final_hash`, `replay_outcome`, `overall_outcome`,
`failure_reason` computation — this step only adds the new field and its one-line derivation.

**Verify:** Test 2 (`test_shutdown_result_full_verification_on_normal_run`, Step 5).

---

### Step 3 — Wire `verification_level` into `RunManifest` at shutdown
**Files:** `src/observability/reporting/artifact_repository.py`, `src/engine/kernel.py`
**Change:** Add `verification_level: Optional[str] = None` to the `RunManifest` pydantic model
(`src/observability/reporting/artifact_repository.py:8-35`), appended immediately after
`state_hash: Optional[str] = None` (line 35) — same `Optional[...] = None` pattern as `state_hash`
itself, so existing manifest JSON on disk (missing the key entirely) deserializes with
`verification_level=None` rather than failing validation (pydantic treats a missing key with a
declared default as satisfied). In `Kernel.shutdown()`'s existing `update_manifest()` call
(`kernel.py:1167-1173`, the same call site that already passes `state_hash=final_hash`), add
`verification_level=verification_level` (the value computed in Step 2).

**Other writers of `update_manifest()` (verified via `grep -rn "update_manifest(" src/`):**
- `kernel.py:176` — `update_manifest(self._run_id, status="RUNNING")`, called at run start. Does
  not pass `verification_level`; the field stays at its pydantic default (`None`) until shutdown
  populates it — identical lifecycle to `state_hash`, which is also only set at shutdown.
- `src/lab/orchestrator.py:256`, `src/observability/sweeper.py:220`,
  `src/observability/mining/controller.py:248` — all three call
  `update_manifest(run_id, status="FAILED", failure_reason=str(e))` on a subsystem failure path.
- `src/observability/anomaly/pipeline.py:392` — `update_manifest(run_id, status="ANALYZED")`,
  called by the post-hoc anomaly-analysis pipeline after report generation.

`update_manifest()`'s merge logic (`artifact_repository.py:105-124`) does a read-modify-write that
only overwrites keys present in the passed `**kwargs` (`for k, v in kwargs.items(): if k in
dumped: dumped[k] = v`), so none of these five other call sites reference or clobber
`verification_level` — there is no ordering conflict between them and the shutdown-time write.

**Do NOT touch:** any of the five other `update_manifest()` call sites; `create_run()`'s initial
manifest construction (`artifact_repository.py:41-58`) — `verification_level` correctly defaults
to `None` there, mirroring `state_hash`'s existing behavior.

**Verify:** Test 4 (`test_run_manifest_includes_verification_level_field`, Step 5).

---

### Step 4 — Surface `verification_level` in `run_report.json` / `run_report.md`
**Files:** `src/observability/reporting/run_report.py`
**Change:** In `RunReportGenerator.generate()`'s `metadata` dict construction
(`run_report.py:106-121`), add one entry alongside the existing `final_hash`/`overall_outcome`
keys:
```python
"verification_level": getattr(shutdown_result, "verification_level", "FULL"),
```
Use `getattr(..., "FULL")`, not direct attribute access. `shutdown_result` is typed
`Optional[Any]` (`run_report.py:21`) and has **two producers**, not one:
1. The real `Kernel.shutdown()` → `ShutdownResult` dataclass (Step 2), which will have
   `verification_level` after this plan lands.
2. `SyntheticShutdownResult` (`src/observability/anomaly/pipeline.py:373-379`), a hand-rolled
   duck-typed shim constructed by the post-hoc anomaly-analysis pipeline (no live `Kernel`
   session), which defines only `final_tick`, `final_hash`, `overall_outcome` — confirmed by
   reading its `__init__` directly. Direct attribute access would raise `AttributeError` for
   every `ANALYZED`-status report generated through that path. Defaulting to `"FULL"` there is
   the honest choice (not a false claim of `"REDUCED"`), and matches the existing defensive style
   already used at `run_report.py:102-104` (`shutdown_result.final_tick if shutdown_result else
   -1`, etc.) for the `None` case.

**Do NOT touch:** `SyntheticShutdownResult`'s field set — it is a distinct, unrelated consumer of
a different code path (post-hoc analysis, not live kernel shutdown); do not add a fabricated
`verification_level` attribute to it as part of this ticket.

**Verify:** Test 5 (`test_run_report_metadata_surfaces_verification_level`, Step 5).

---

### Step 5 — New tests 1, 2, 3: cumulative tracking through recovery and SURVIVAL mode
**Files:** `tests/unit/kernel/test_verification_level.py` (new file)
**Change:** Add the three hardest-case tests from test_plan.md's "New Tests Required" section:

- **`test_shutdown_result_flags_reduced_verification_after_degraded_run`** (test 1): drive a
  `Kernel`'s `self._status` through `reset_dwell(RuntimeMode.DEGRADED, tick)` then
  `reset_dwell(RuntimeMode.NORMAL, tick+1)` (directly, as `tests/unit/core/test_engine_integrity.py`
  already does for guard-testing patterns — no need to synthesize real pressure signals through
  `ResourceGovernor.evaluate()`), then call `kernel.shutdown()`; assert
  `result.verification_level == "REDUCED"` even though `self._status.current_mode == NORMAL` at
  the time of the call. This is the cumulative-tracking case Step 1 exists to fix.
- **`test_shutdown_result_full_verification_on_normal_run`** (test 2): a `Kernel` whose
  `self._status` never leaves `NORMAL`/`CONSTRAINED`; assert `result.verification_level == "FULL"`
  — regression guard against the new field defaulting to `"REDUCED"` incorrectly.
- **`test_shutdown_result_flags_reduced_verification_after_survival_run`** (test 3): drive
  `self._status` into `SURVIVAL` via `reset_dwell(RuntimeMode.SURVIVAL, tick)`; assert
  `result.verification_level == "REDUCED"`. Explicitly assert this does **not** depend on
  scanning replay `TICK_END` events (SURVIVAL has `replay_allowed=False`,
  `src/engine/policy.py:127-146`, so no `TICK_END` trail exists to scan) — the assertion should
  read `max_mode_reached` / `verification_level` directly, proving Step 1's design (tracking on
  `RuntimeStatus`, independent of the replay stream) resolves this hazard.

**Do NOT touch:** `tests/unit/kernel/test_replay_overflow.py`'s four `GovernorPolicy` variant
constructions — must keep passing unmodified (test_plan.md Anti-Drift Test Guards).

**Verify:** Tests 1, 2, 3 pass. Regression: `tests/unit/core/test_degradation_order.py`,
`tests/unit/kernel/test_replay_overflow.py` unaffected (neither touches `RuntimeStatus.reset_dwell`
directly, both construct `GovernorPolicy` independently).

---

### Step 6 — Architecture guard tests 6, 7: Tier-2 fingerprint gate and canonical-hash gate unchanged
**Files:** `tests/unit/core/test_engine_integrity.py` (test 6), `tests/unit/engine/test_hash_scheduler.py` (test 7)
**Change:**
- **`test_tier2_fingerprint_guard_still_audit_mode_gated`** (test 6), added near
  `test_isolation_guard_trigger` (`tests/unit/core/test_engine_integrity.py:150`): assert
  `_guard_stability()` is invoked only when `audit_mode=True` — i.e. exercise a non-audit-mode
  tick and confirm `_guard_stability` is never called (patch/spy), while `_guard_gross_isolation`
  is. This proves `kernel.py:383-395` was not touched by Steps 1-4.
- **`test_canonical_hash_still_conditional_on_replay_richness`** (test 7), added to
  `tests/unit/engine/test_hash_scheduler.py` alongside the existing
  `TestArchitectureNoDirectHashInNormalTickPath` class (`tests/unit/engine/test_hash_scheduler.py:180-209`):
  assert `_phase_persistence()` (`kernel.py:1059-1073`) still returns `"SKIPPED"` for the
  DEGRADED-mode `TraceEvent.payload["hash"]`, and emits no `TICK_END` event at all in SURVIVAL
  mode (`replay_allowed=False`) — i.e. the underlying hash-computation gate itself is
  byte-for-byte unchanged; only new *reporting* fields exist elsewhere (Steps 1-4).

These are the primary anti-scope-creep guards for AC2 and the ticket's Out of Scope line — per
investigation.md §4, accidentally widening `_guard_stability` or the canonical-hash gate while
adding labeling is the single most likely failure mode of this ticket.

**Do NOT touch:** `_guard_stability`, `_guard_gross_isolation`, `_phase_persistence`'s
hash-computation logic (`kernel.py:1059-1073`) — Steps 1-4 never modify these; these new tests
exist to prove that, not to add new behavior to them.

**Verify:** Tests 6, 7 pass. Full existing `tests/unit/engine/test_hash_scheduler.py` and
`tests/unit/core/test_engine_integrity.py` suites (all functions listed in test_plan.md's
Regression Surface) pass unmodified.

---

### Step 7 — Docs and parity ledger updates
**Files:** `docs/engine/known_limitations.md`, `docs/engine/kernel.md`,
`docs/parity_ledger/infrastructure.yaml`
**Change:**
- `docs/engine/known_limitations.md` §2.4 "Canonical State Hash Availability by Runtime Mode"
  (confirmed by reading the file: section spans lines 110-159, ending just before §3 "Tooling /
  Observability" at line 161): add a short subsection describing the new `verification_level`
  field ("FULL" / "REDUCED"), stating explicitly that it is derived from the **cumulative**
  `max_mode_reached` tracked across the whole run (not the instantaneous mode at shutdown), and
  listing where it surfaces: `ShutdownResult.verification_level`,
  `RunManifest.verification_level`, and the `run_report.json`/`.md` `metadata.verification_level`
  key.
- `docs/engine/kernel.md`: "State Hashing in Phase 7 (Persistence)" section (confirmed lines
  100-127) gets one short paragraph cross-referencing the new field and pointing to the updated
  `known_limitations.md` §2.4 subsection. "Resource Snapshot and Lifecycle Supervisor" section
  (confirmed lines 82-97) — its existing `ShutdownResult`/`ShutdownReport` bullet list at lines
  88-94 documents `ShutdownReport` fields only; `ShutdownResult`'s own fields (`final_tick`,
  `final_hash`, `replay_outcome`, `overall_outcome`, `failure_reason`) are not itemized there
  today. Add a short itemized note for `ShutdownResult`'s fields including the new
  `verification_level`, filling a pre-existing documentation gap rather than expanding scope.
- `docs/parity_ledger/infrastructure.yaml`: append a note to `INFRA-223`'s `text`/`v2_evidence`
  (entry at line 2717, confirmed by reading the file directly) stating that DEGRADED/SURVIVAL
  outputs are now explicitly flagged via `verification_level`, citing this ticket. Do **not**
  change `INFRA-223`'s `status` (stays `verified`) or `priority`/`test_path`. Add a **new** entry
  for the `verification_level` field itself. The highest existing `INFRA-` id in the file as of
  this planning session is `INFRA-362` (confirmed via `grep -oE "INFRA-[0-9]+"
  docs/parity_ledger/infrastructure.yaml | sort -t- -k2 -n -u | tail -1`), so the next available
  id is provisionally `INFRA-363` — **re-run that grep at implementation time** before writing the
  new entry, since concurrent ticket work on this file is a known risk (investigation.md,
  Parity Ledger Overlap section) and the id may have advanced.

**Do NOT touch:** any other parity ledger file (`combat_movement.yaml`, `progression.yaml`,
etc.), `INFRA-222`'s entry, or `INFRA-223`'s `status`/`priority`/`test_path`.

**Verify:** No automated test — manual review that doc field names/values match Steps 1-4's
shipped code exactly (field name `verification_level`, values `"FULL"`/`"REDUCED"`, no
alternate spelling). Run `make knowledge-index-update` after these doc edits per CLAUDE.md's
After Work rule (docs/ was modified).

## Scope Guards

Derived from the ticket's Out of Scope section and investigation.md's Anti-Drift Hazards:

- Do not make `_guard_stability()`'s Tier-2 fingerprint comparison run unconditionally, or run it
  more than the current 2 times per tick under `audit_mode=True` — this is the exact Out of Scope
  boundary the ticket names. No step in this plan touches `_guard_stability`,
  `_guard_gross_isolation`, or the `audit_mode` conditionals at `kernel.py:368-395`.
- Do not make the canonical hash (`CanonicalStateHasher.get_hash()`) always-on in
  `_phase_persistence()` — the DEGRADED `"SKIPPED"` sentinel and SURVIVAL no-`TICK_END` behavior
  must remain byte-for-byte unchanged (Step 6 is the explicit regression guard for this).
- Do not widen `CanonicalStateHasher`'s field coverage — that scope was deliberately hardened by
  `TCK-20260419-MA-TASK4-HARDEN-HASHING`; any additions belong to a separate ticket.
- Do not remove or weaken `CanonicalHashScheduler`'s rate limiting (INFRA-196/197) — untouched by
  every step in this plan.
- Do not conflate `RuntimeMode` (this ticket's subject) with `ObservabilityMode`
  (`src/observability/config.py`) — `verification_level` is derived exclusively from
  `RuntimeStatus.max_mode_reached` (a `RuntimeMode` history), never from
  `ObservabilityConfig.get_mode()`.
- Do not change `GovernorPolicy` (`src/engine/policy.py`) in any way — if implementation finds
  itself needing to, that is a signal the change has grown beyond path (b)'s intended scope
  (labeling run *outputs*, not changing the *policy* that drives per-tick hashing/replay).
- Do not change `INFRA-223`'s `status` away from `verified`.
- Do not add a `verification_level` attribute to `SyntheticShutdownResult`
  (`src/observability/anomaly/pipeline.py:373-379`) — Step 4's `getattr` default handles that
  producer without modifying it.

## Dependency Map

- Step 1 has no dependencies; it is the foundation all other steps read from.
- Step 2 depends on Step 1 (`self._status.max_mode_reached` must exist).
- Step 3 depends on Step 2 (`verification_level` must be computed before it can be passed to
  `update_manifest()`).
- Step 4 depends on Step 2 (`ShutdownResult.verification_level` must exist for `getattr` to find
  it) — independent of Step 3.
- Step 5's tests depend on Steps 1 and 2 being implemented (they exercise `RuntimeStatus` and
  `ShutdownResult` directly).
- Step 6 is independent of Steps 1-5 — it can be written and run at any point, but should be run
  last as the final anti-drift confirmation that Steps 1-4 didn't touch guard/hash logic.
- Step 7 (docs) depends on Steps 1-4 being finalized, since it documents the exact field names and
  values they ship.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| "Either a cheap always-on partial fingerprint exists... or DEGRADED/SURVIVAL run outputs are explicitly labeled as reduced-verification" | Steps 1-4 (cumulative tracking + `verification_level` on `ShutdownResult`/`RunManifest`/`run_report`) | Tests 1-5 (Step 5: tests 1,2,3; Step 3: test 4; Step 4: test 5) |
| "The full Tier-2 fingerprint / canonical hash remains conditional (not made unconditionally always-on)" | Step 6 (explicit regression guards); also satisfied by Steps 1-4 never modifying `_guard_stability`/`_guard_gross_isolation`/`_phase_persistence` | Tests 6, 7 (Step 6) |

## Anti-Drift Notes

- **Hook site correction from investigation.md**: investigation.md §5 suggested hooking the
  `GovernorModeChanged` event-emission block at `kernel.py:960-976`. This plan instead hooks
  `RuntimeStatus.reset_dwell()` (`runtime_status.py:79-83`), because the event-emission block
  lives inside `_phase_observability()`, which returns early whenever
  `ObservabilityConfig.get_mode() == ObservabilityMode.OFF` (`kernel.py:902-904`) — an
  observability-OFF production run would silently fail to track reduced verification under the
  investigation's suggested hook. `reset_dwell()` is unconditional and is also the exact site
  `force_mode()`'s mid-tick emergency throttle path uses, so no separate wiring is needed for
  that path either.
- **`SyntheticShutdownResult` is a second, real writer to the `RunReportGenerator.generate()`
  consumption surface** that neither the ticket nor investigation.md names explicitly (found by
  reading `src/observability/anomaly/pipeline.py:373-379` directly during planning). Step 4's
  `getattr(..., "FULL")` default is required, not optional stylistic defensiveness — direct
  attribute access breaks the `ANALYZED`-status report path today.
- **Fixture concern resolved, not just noted**: test_plan.md's Anti-Drift Test Guards section
  flags `tests/tools/fixtures/kgmcp_phase5_working_log_snapshot.json` as a fixture to check for
  embedded manifest-shaped data. Verified directly by reading the file: it is a list of ticket
  `{summary, ticket_id, title}` objects (a working-log snapshot), not `RunManifest`-shaped JSON.
  The one occurrence of the substring "state_hash" in the file (line 4843) is inside a prose
  `summary` string describing an unrelated ticket, not a JSON key. **No action needed on this
  fixture** — confirmed false positive, do not modify it.
- `RuntimeMode` comparison (`>= RuntimeMode.DEGRADED`) relies on `RuntimeMode` being an `IntEnum`
  with the exact ordering NORMAL=0 < CONSTRAINED=1 < DEGRADED=2 < SURVIVAL=3
  (`src/core/governance.py:8-16`, confirmed by reading the file). If a future ticket ever
  reorders or renames these values, `verification_level`'s derivation in Step 2 must be revisited
  — flag this coupling in code comments when implementing.
- Confirm the `INFRA-` id for Step 7's new parity ledger entry by re-running
  `grep -oE "INFRA-[0-9]+" docs/parity_ledger/infrastructure.yaml | sort -t- -k2 -n -u | tail -1`
  immediately before writing the entry (was `INFRA-362` → next `INFRA-363` at planning time;
  concurrent writers are a known risk per investigation.md).

## Unresolved Questions

None. Both design decisions investigation.md flagged as needing Plan's explicit resolution have
been made:
1. **Cumulative-tracking mechanism**: a `max_mode_reached` field on `RuntimeStatus`, updated
   inside `reset_dwell()` (Step 1) — chosen over scanning replay-stream `GovernorModeChanged`
   events because SURVIVAL mode has `replay_allowed=False` (no replay stream to scan at all), and
   because it is strictly cheaper (one `IntEnum` comparison per transition vs. a shutdown-time
   scan).
2. **Field location (durable `AuthoritativeState` vs. non-authoritative telemetry)**:
   non-authoritative — placed on `RuntimeStatus`, which is explicitly documented as isolated from
   `AuthoritativeState` and simulation hashes (`runtime_status.py:15-16`). This is presentation/
   reporting information about how the run was governed, not simulation-meaningful state.
