---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC
artifact_type: investigation
tags: [engine, determinism]
---

# Investigation — TCK-20260817-DETERMINISM-VERIFICATION-GAP-EPIC

## Current Behavior

### 1. Tier-2 SHA-256 fingerprint check (`_guard_stability`) — `audit_mode`-gated

`src/engine/kernel.py`, inside `_tick_once_inner()`:

- Line 368-370: `start_fingerprint = self._state.fingerprint()` is only captured **if
  `self._audit_mode`** is true.
- Lines 383-386 (after `_phase_scheduling()`) and 392-395 (after `_phase_collection()`):
  ```python
  if self._audit_mode and start_fingerprint:
      self._guard_stability("Scheduling", start_fingerprint)
  if not self._audit_mode:
      self._guard_gross_isolation("Scheduling", _gross_entity_count, _gross_tick)
  ```
  The full mutation-detecting comparison (`_guard_stability`, lines 1026-1033) runs **only**
  when `audit_mode=True`. In standard runs the fallback is `_guard_gross_isolation` (lines
  1035-1057), which checks only `len(state.entities)` and `state.tick` — two O(1) reads. It
  explicitly does **not** detect field-level mutation of an existing entity
  (`known_limitations.md` §2.3 confirms this via a violation-type table).
- `audit_mode` is set from `flags.get("audit_mode", False)` at kernel construction
  (`kernel.py:81`) and is used in production only by `src/certification/harness.py` /
  certification scenarios — invisible in default production runs, exactly as the ticket states.

### 2. Canonical hash comparison — DEGRADED/SURVIVAL gated

`_phase_persistence()`, `src/engine/kernel.py:1059-1073`:

```python
def _phase_persistence(self) -> None:
    tick_hash = "SKIPPED"
    if self._current_policy.replay_allowed and (self._audit_mode or self._current_policy.replay_richness == "FULL"):
        from src.engine.checkpoint import CanonicalStateHasher
        tick_hash = CanonicalStateHasher.get_hash(self._state)

    if self._current_policy.replay_allowed:
        self._replay.emit(TraceEvent(
            tick=self._state.tick, system="KERNEL", event_type="TICK_END",
            payload={"hash": tick_hash}
        ), self._current_policy)

    self._replay.on_tick_end(self._state.tick)
```

`replay_allowed` / `replay_richness` come from `GovernorPolicy.from_mode()`
(`src/engine/policy.py`), keyed by `RuntimeMode`:

| RuntimeMode | `replay_allowed` | `replay_richness` | `TICK_END.hash` |
|---|---|---|---|
| NORMAL | True | "FULL" | real SHA-256 |
| CONSTRAINED | True | "FULL" | real SHA-256 |
| DEGRADED | True | "MINIMAL" | literal `"SKIPPED"` |
| SURVIVAL | False | "OFF" | **no TICK_END event at all** |

The final shutdown hash (`CanonicalStateHasher.get_hash()` inside `Kernel.shutdown()`,
`kernel.py:1176-1178`, feeding `ShutdownResult.final_hash`) is always computed regardless of
mode — only the **per-tick** hash is conditional.

### 3. Is `TCK-20260627-P2F-CANON-HASH-DOC` the same finding, already resolved?

**No — it is a documentation-only precursor, not a behavior fix.** Read in full
(`stored_artifacts/TCK-20260627-P2F-CANON-HASH-DOC/investigation.md`): that ticket traced the
exact same `_phase_persistence()` gate and concluded the gap was a *documentation* gap — the
conditional "SKIPPED" behavior existed but was undocumented and its framing in the source audit
was partly wrong ("Standard runs record SKIPPED" was corrected to "only DEGRADED does"). Its own
"Existing documentation gaps" section (lines 128-134) lists exactly the three docs it then
updated: `docs/engine/known_limitations.md` §2.4 (now present, verified above),
`docs/engine/kernel.md` (Phase 7 section, now present), and `docs/engine/deterministic_execution.md`.
No code in `src/engine/kernel.py`, `src/engine/checkpoint.py`, or `src/replay/fingerprint.py`
was changed by that ticket — the parity ledger entry it produced, INFRA-223, describes the gate
as `status: verified` (i.e., verified-as-correctly-documented, not verified-as-closed-gap).
**Confirmed still open**: the underlying conditional behavior (Tier-2 fingerprint gated on
`audit_mode`; canonical hash gated on DEGRADED/SURVIVAL) is unchanged today. This ticket's scope
(a cheap always-on partial check, or explicit reduced-verification labeling) is a genuine,
unaddressed increment on top of that prior documentation work — not a duplicate.

### 4. Feasibility of resolution path (a): cheap always-on partial/sampled fingerprint

Three hashing mechanisms already exist in the codebase, at three different cost points:

1. **`CanonicalStateHasher.get_hash()`** (`src/engine/checkpoint.py:38-107`) — full SHA-256 over
   *all* authoritative state: every entity via `to_canonical_dict()`, plus regions, local_scars,
   resource_nodes, buildings, corpses, ground_items, chests, groups, home_storage, camps, derived
   indices, and the RNG checkpoint. This is the expensive check the ticket explicitly says must
   stay conditional (Out of Scope). It is already wrapped by `BudgetedCanonicalHasher` (rate
   limit per 100-tick window) and gated by `CanonicalHashScheduler` (`checkpoint.py:200-253`,
   INFRA-196/197), which raises `HashScheduleViolation` for any FULL hash outside tick=0,
   run-end, or `reason in {"certification","audit","replay"}` — strong existing evidence the
   project treats the full hash as *deliberately* expensive and rate-limited, not a check to
   casually widen.
2. **`StateFingerprinter.get_fingerprint()`** (`src/replay/fingerprint.py`) — MD5 over a
   *partial* domain (entity identity/position/HP/gold/project/readiness/skills-count/items-
   identity/bonds-count/reputation, plus strategic state, global resources, resource nodes,
   regions, local scars, groups, macro state). This is already the "cheap partial fingerprint"
   concept the ticket's path (a) asks for — but it is **not free**: it is O(N) in entity count
   (builds a formatted string per entity), and it is what `_guard_stability` already uses
   internally. It already runs once per tick unconditionally whenever `replay_allowed=True`
   (`kernel.py:675`, inside the `REFINED_UPDATE` payload) — but the *guard comparison* itself
   (before Scheduling / after Collection) only calls it 2 more times when `audit_mode=True`
   (`kernel.py:368-370, 383-393`). Making the Tier-2 comparison always-on (even using the cheaper
   MD5 fingerprint instead of the full SHA-256) would roughly **triple** the fingerprint-related
   O(N) cost on every tick in every run mode, not just certification runs.
3. **`CanonicalHashScheduler.compute_hash(mode=HashMode.LIGHT)`** (`checkpoint.py:228-252`) — a
   genuinely O(1) MD5 over `f"{tick}:{seed}:{len(entities)}:{len(regions)}"`. This is the only
   truly "cheap" hash in the codebase, but the class's own docstring says it is "NOT a
   determinism proof" — and structurally it **cannot** catch a field-level mutation (an HP or
   position change on an existing entity does not change entity_count or region_count), so it
   would not narrow the coverage gap this ticket cares about at all. Also: `CanonicalHashScheduler`
   is currently only wired into `src/certification/harness.py` (two call sites), never into
   `Kernel._tick_once_inner()` / `_phase_persistence()` — it is not reachable from the standard
   tick loop today.

`docs/engine/performance_contract.md` has no explicit per-hardware-class ms table, but
`src/config/profiles.py`'s `RuntimeProfile` instances give the real numbers: `PROD_SMALL`
(Class C / legacy-edge) has `max_tick_budget_ms=100.0` and `max_observability_budget_percent=2.0`
— a 2ms total observability budget per tick. `PROD_DEFAULT` (Class B) has `max_tick_budget_ms=50.0`
at 5% (2.5ms). `PROD_LARGE` (Class A, 5,000-entity target) has `max_tick_budget_ms=100.0` at 10%
(10ms). Tripling an O(N) fingerprint cost inside those budgets, at scale, is a real and
measurable risk, not a rounding error — and doing so would functionally make the Tier-2 mutation
guard "always run its comparison logic every tick," which risks drifting into the explicitly
out-of-scope territory ("making the full Tier-2 fingerprint... always-on unconditionally") even
though the hash algorithm itself (MD5 vs SHA-256) would differ.

**Conclusion: path (a) is not a clean "genuinely cheap" win.** The only O(1) cheap primitive
that exists (`HashMode.LIGHT`) doesn't detect the class of bug in question; the primitive that
would detect it (`StateFingerprinter`) is O(N) and would need to run 2-3x more often than today,
which is a real cost-budget risk on Class B/C hardware and blurs the Out-of-Scope line.

### 5. Recommendation: path (b) — label DEGRADED/SURVIVAL outputs as reduced-verification

Given §4's findings, **path (b) is recommended**. It is explicitly framed by the ticket as the
safe "at minimum" floor, requires no perf-budget trade-off judgment call, and the codebase
already has the building blocks needed to implement it minimally:

- `AuthoritativeState.current_mode: RuntimeMode` (`src/core/state.py:1200`) — the *current* mode
  is already durable state.
- A `GovernorModeChanged` `SimulationEvent` is already emitted on every mode transition
  (`kernel.py:960-976`), payload includes `previous_mode`/`current_mode`/`mode_dwell_ticks` —
  this is the existing precedent for "degraded mode is observable, not silent" (parity ledger
  INFRA-173, `status: verified`, text: "Degraded mode is observable, not silent.").
- `ShutdownResult` (`src/core/lifecycle.py:15-24`) is explicitly documented as "M10 Law: Truthful
  representation of the engine's final state" — the natural, already-existing home for a new
  run-level truthfulness field, but currently has no mode/verification field at all (only
  `final_tick`, `final_hash`, `replay_outcome`, `overall_outcome`, `failure_reason`).
- `RunManifest` (`src/observability/reporting/artifact_repository.py:8-35`) already has a
  `state_hash: Optional[str]` field, populated at shutdown via
  `self._artifact_repo.update_manifest(self._run_id, status=..., ticks_completed=...,
  ended_at=..., state_hash=final_hash)` (`kernel.py:1164-1173`) — the same call site is the
  natural place to also pass a new verification-level field.
- `RunReportGenerator.generate()` (`src/observability/reporting/run_report.py:101-121`) already
  builds a `metadata` dict from `shutdown_result` (`final_tick`, `final_hash`, `overall_outcome`,
  `health_score`, ...) that is written to both `run_report.json` and `run_report.md` — the
  natural place to surface the new field to a human/machine consumer of run outputs.

**Genuine gap Plan must scope**: none of the above currently tracks *cumulative* mode history
across a run — only the *current* mode at any instant. A run that dipped into DEGRADED for 50
ticks and recovered to NORMAL by shutdown would show `current_mode=NORMAL` at the end with no
current field indicating reduced verification occurred earlier. Plan must decide how to
accumulate this (e.g., a running "ticks_in_reduced_verification" / "max_mode_reached" counter on
`Kernel`, updated at the same site as the existing `GovernorModeChanged` event emission around
`kernel.py:960-976`, then read at `shutdown()` to populate `ShutdownResult` and the manifest).

## Mechanics / Engine Constraints

This is a pure engine/infrastructure change — no `docs/mechanics/` chapter is implicated (no
gameplay formula or law changes). The relevant engine contracts are:
- `docs/engine/kernel.md` — "🛡️ The Stability Guard Law" (Tier 1/Tier 2 gating) and "State
  Hashing in Phase 7 (Persistence)" sections directly describe the current conditional behavior
  that this ticket either narrows (path a) or labels (path b).
- `docs/engine/known_limitations.md` §2.3 (Phase Isolation Detection) and §2.4 (Canonical State
  Hash Availability by Runtime Mode) are the authoritative descriptions of exactly the two gaps
  in scope.
- `docs/engine/performance_contract.md` §4.1 "Parity Invariant" and §4.2 "Bounded Overhead"
  constrain any change to hashing cost — any new always-on check must not alter tick-to-tick
  semantic outcomes (parity invariant) and per §5, must not increase `avg_tick_compute_ms` by
  more than 5% on a stable scenario without a recorded "Divergence Reason."

## Docs Requiring Update

- `docs/engine/known_limitations.md`: §2.4 (lines 110-159) must be updated once the chosen
  resolution lands — either to describe the new lightweight always-on check (path a) or to
  document the new reduced-verification flag/field and where it appears in run outputs (path b).
- `docs/engine/kernel.md`: the "State Hashing in Phase 7 (Persistence)" section (lines 100-126)
  must be updated to describe the new labeling/field once implemented; if path (b) also touches
  `ShutdownResult`/`RunManifest`, the "Resource Snapshot and Lifecycle Supervisor" section (lines
  82-97, which already documents `ShutdownResult`/`shutdown_report()`) should note the new field.
- `docs/parity_ledger/infrastructure.yaml`: INFRA-223 (lines 2717-2738) describes the current
  gate accurately and does not need its `status` changed for path (b) alone (the gate itself is
  unchanged), but its `text`/`v2_evidence` should gain a note that DEGRADED/SURVIVAL outputs are
  now explicitly flagged, once implemented. A **new** entry should be added for the new
  reduced-verification field itself (id TBD by Plan, e.g. next available `INFRA-2xx`), citing
  this ticket.

## Parity Ledger Overlap

- `docs/parity_ledger/infrastructure.yaml::INFRA-222` (line 2702) — Tier 1 gross isolation guard,
  `status: verified`, `test_path`: `tests/unit/core/test_engine_integrity.py::test_gross_isolation_guard_triggers_on_tick_change,...`.
  Its own `text` already notes "Field-level mutations within existing entities require
  audit_mode=True for detection" — i.e. it documents the Tier-2 gap as a known limitation of
  Tier 1, not a bug in Tier 1 itself. No change needed unless Plan adds a new always-on Tier
  1.5 check.
- `docs/parity_ledger/infrastructure.yaml::INFRA-223` (line 2717) — the exact
  `_phase_persistence()` conditional-hash entry this ticket's path (b) touches. `status:
  verified`, `priority: P2`, `test_path: tests/integration/kernel/test_determinism_suite.py`.
  **Note**: that test file (`tests/integration/kernel/test_determinism_suite.py`) does NOT
  currently exercise the DEGRADED/SURVIVAL "SKIPPED"/no-event branches (verified by reading its
  test names: `test_reproducibility`, `test_seed_divergence`, `test_canonical_sorting_stability`,
  `test_local_vs_concurrent_equivalence` — all NORMAL-mode determinism checks). The listed
  `test_path` is therefore a loose/representative reference, not a precise regression guard for
  the conditional gate itself; `tests/unit/engine/test_hash_scheduler.py` (class
  `TestArchitectureNoDirectHashInNormalTickPath`, lines 180-209) is the closer existing guard,
  though it re-implements the gate condition inline rather than calling
  `Kernel._phase_persistence()` directly.
- **No P0 entries found** touching this behavior — INFRA-222 and INFRA-223 are both P1/P2, so
  the "P0 requires passing test_path" rule does not block this ticket.
- No entry currently exists for the Tier-2 `_guard_stability()` `audit_mode` gate as its own
  parity item (only referenced inside INFRA-222's text). If Plan pursues path (a) after all, a
  new entry would be needed; for path (b) this is not required since Tier-2 itself is untouched.

## Prior Work

- `TCK-20260627-P2F-CANON-HASH-DOC` (`stored_artifacts/TCK-20260627-P2F-CANON-HASH-DOC/`) — see
  §3 above. Documentation-only; produced `docs/engine/known_limitations.md` §2.4 and INFRA-223.
  This ticket builds directly on top of it rather than duplicating it.
- `TCK-20260627-P1G-STABILITY-GUARD` (cited in `known_limitations.md` §2.3, source D09 Finding 5)
  — appears to be the ticket that documented (or hardened) the Tier 1/Tier 2 guard split. Not
  re-read in full for this investigation since §2.3's content already gives an accurate, current
  description of the guard split cross-checked directly against `kernel.py`; no indication this
  ticket changed the `audit_mode` gating itself (only documented/hardened `_guard_gross_isolation`
  as the Tier 1 always-on fallback).
- `TCK-20260419-MA-TASK4-HARDEN-HASHING` (`tickets/done/`) — hardened `CanonicalStateHasher` to
  include only authoritative fields and be fully deterministic. Establishes that the canonical
  hasher's scope (what fields it covers) has been a deliberately curated, previously-hardened
  surface — relevant context for anyone tempted to casually add fields to a new partial check.
- `TCK-20260614-HASH-SCHEDULER` — introduced `CanonicalHashScheduler`/`BudgetedCanonicalHasher`
  (INFRA-196/197), i.e. the existing cost-control machinery around the full hash referenced in
  §4 above.

## Risks and Open Questions

- **Is this ticket worth picking up at all?** The ticket's own "Assumptions / Open Questions"
  section flags that pickup is gated on "off-path mutation bugs have actually occurred or are a
  live concern" — this investigation found no evidence in the codebase (no open bug reports, no
  failing test, no divergence-note) that such a bug has actually occurred. This is a scope
  decision for Plan/the ticket owner, not something this investigation can resolve — flagging
  per the "vague leads stay vague" rule rather than assuming an answer.
- **Cumulative mode tracking does not exist yet** (see §5) — Plan must decide the exact
  accumulation mechanism (counter on `Kernel`, or derive from scanning `GovernorModeChanged`
  events in the replay stream) before Implement can proceed. This is a design decision, not
  ambiguous scope, so it does not block Investigate, but Plan must make an explicit choice here.
  Non-authoritative telemetry should be favored over adding a new field to `AuthoritativeState`
  itself, since a coarse cumulative "was verification reduced" flag is presentation/reporting
  information rather than durable simulation state (Durable State Rule in CLAUDE.md concerns
  simulation-meaningful state, not run-report metadata — Plan should still confirm this framing
  since `AuthoritativeState.current_mode` already exists as durable state as a counter-example).
- Choosing path (a) instead is not prohibited by this investigation, but would need Plan to pick
  a specific "cheap" definition (e.g. sampling 1-in-K entities, or restricting the always-on
  comparison to a small fixed subset of high-risk fields) and to explicitly justify why it does
  not amount to "making Tier 2 always-on" against the Out-of-Scope boundary — this investigation
  found no such design already implemented or clearly cheap enough to lift as-is.

## Anti-Drift Hazards

- **Do not widen `CanonicalStateHasher`'s field coverage** as a side effect of this ticket —
  that hasher's scope was deliberately hardened by `TCK-20260419-MA-TASK4-HARDEN-HASHING` and
  any additions belong to a separate, explicitly-scoped ticket.
- **Do not remove or weaken `CanonicalHashScheduler`'s rate limiting/sanctioned-boundary
  enforcement** (INFRA-196/197) while touching this area — it is a distinct, already-verified
  cost-control mechanism, not part of this ticket's scope.
- **Do not make `_guard_stability()`'s comparison run unconditionally** without an explicit,
  measured cost justification — per §4, this is the single easiest way to accidentally violate
  the ticket's own Out-of-Scope boundary while technically "just adding a cheap check."
  Reasonable per-tick perf-cost measurement is the burden of proof.
- **Do not conflate `RuntimeMode` (governance/kernel mode: NORMAL/CONSTRAINED/DEGRADED/SURVIVAL)
  with `ObservabilityMode`** (`src/observability/config.py`, used for `RunManifest.observability_mode`)
  — these are two separate enums governing two separate subsystems. A "reduced verification"
  field belongs to `RuntimeMode`'s history, not `ObservabilityMode`.
- **Do not change `INFRA-223`'s `status` away from `verified`** — the gate it documents remains
  exactly as documented; only add new text/entries for the new labeling behavior, don't imply
  the previously-documented gate was wrong.
