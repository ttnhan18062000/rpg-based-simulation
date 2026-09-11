---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION
phase: open
date: 2026-09-11
tags: [performance, architecture]
---

# TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION

## Title
`src/domains/optimization/`'s 8 unwired modules — determine per-module whether each is a
superseded duplicate of a live mechanism or a genuinely missing one, before deciding anything

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
**Do not treat this as "wire these modules in."** That was the first hypothesis and it is likely
wrong for at least part of the package — this ticket exists to make the real determination, not
to execute a pre-judged fix.

Found during `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (`docs/audits/
unreachable_code_inventory.md`, Cluster C1): of `src/domains/optimization/`'s 9 modules, 8 have
**zero real production imports anywhere in the codebase** — confirmed directly
(`grep -rn "from src.domains.optimization" src/ tools/ | grep -v "src/domains/optimization/"`
finds exactly one hit, `src/engine/pipeline.py:69`, importing `FeatureFlagManager`/`FeatureMode`
from the 9th module, `feature_flags.py`). `src/api/admission_control.py:60,97` even references
`cache_strategy.py` in its own comments as though describing the live implementation, when it is
one of the 8 unreferenced modules — a comment pointing at dead code as if it were live, not merely
silent.

**The worked example that changes the framing.** `optimization/degradation.py`'s
`GracefulDegradationManager` (`DegradationLevel.NORMAL/CONSTRAINED/DEGRADED/CRITICAL`,
`update_pressure(tick_time_ms, limit_ms)` computing a ratio against a time budget,
`get_provider_cap()`, `should_skip_phase()`) and `src/engine/governor.py`'s `ResourceGovernor`
(`RuntimeMode`, `_get_indicated_mode()` computing ratio thresholds against
`signals.tick_compute_ms`/`profile.max_tick_budget_ms`, confirmed live and load-bearing during
Batch A — it's what the `worker_utilization` sentinel feeds and what drives
`ScanPolicy.EXACT_DIRTY`) do **the same job** — react to compute pressure by degrading behavior —
with different implementations, different specific thresholds, and only one of them wired in. The
same pattern plausibly holds for `budget_manager.py`'s `PhaseBudgetManager.check_and_consume()`
(time/entity/provider-call/trace-event budget enforcement) against the live `GovernorPolicy`/
`PhaseBudgets` system (`src/engine/policy.py`, `src/engine/phase_governor.py`,
`src/config/optimization_profiles.py` — `policy.movement_budget`, `policy.scan_policy`, per prior
investigation from the same Batch A arc that traced `ResourceGovernor`).

**If this pattern holds, wiring the unwired module in would be actively harmful** — two competing
degradation/budget systems running simultaneously is the `lead_capacity` dual-mechanism-
preemption problem (`TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION`) at
subsystem scale. The correct disposition for a genuinely-superseded module is **delete**, not
wire — but this must be established per-module with real evidence, not assumed uniformly across
all 8 just because two of them match the pattern.

The 8 unwired modules, grouped by apparent shape (not yet individually determined):

| Module | Class(es) | Apparent shape | Live candidate equivalent (unconfirmed) |
|---|---|---|---|
| `degradation.py` | `GracefulDegradationManager` | pressure-ratio degradation levels | `src/engine/governor.py::ResourceGovernor` — strong structural match, confirmed |
| `budget_manager.py` | `PhaseBudgetManager` | per-phase time/entity/provider/trace budget enforcement | `GovernorPolicy`/`PhaseBudgets` (`src/engine/policy.py`, `phase_governor.py`) — plausible match per prior Batch A investigation, not yet directly compared |
| `cache_strategy.py` | `CacheKey`, `CacheStrategy` | LRU-style cache with get/put/invalidate | `admission_control.py`'s own local eviction logic (its comments describe `cache_strategy.py`'s behavior as if implementing it) — plausible match, not yet directly compared |
| `dirty_scheduler.py` | `DirtyWorkScheduler` | dirty-region/entity tracking for incremental scheduling | unknown — check for a live dirty-tracking mechanism elsewhere in the engine |
| `memory_limits.py` | `MemoryCapacityLimits` | bounded memory eviction (facts/opponents/rewards/cooperation) | unknown |
| `diagnostics.py` | `DeveloperDiagnostics` | issue recording for dev-facing diagnostics | unknown |
| `provider_enforcement.py` | `ProviderBudgetEnforcement` | provider call budget enforcement | unknown — may overlap with `PhaseBudgetManager`'s own `provider_calls` tracking, or with a live rate-limiter elsewhere |
| `trace_governor.py` | `TraceVolumeGovernor` | trace volume governance | unknown |

## Scope
- For each of the 8 modules: determine whether a live equivalent mechanism already exists
  elsewhere in the engine (superseded — real disposition: delete, after confirming no unique
  behavior would be lost) or whether the module represents a genuinely missing wiring gap with no
  live equivalent (real disposition: wire, or document as deliberately deferred).
- Start with `degradation.py` vs. `ResourceGovernor` and `budget_manager.py` vs. `GovernorPolicy`/
  `PhaseBudgets` — the two pairs with the strongest prior evidence — before the other 6, which have
  no live-equivalent candidate identified yet.
- For any module confirmed superseded: confirm no unique behavior in the dead module is absent
  from its live replacement before recommending deletion (e.g. `GracefulDegradationManager.
  resolve_content_source()`'s catalog-preference-under-pressure behavior — does `ResourceGovernor`
  or anything else provide this, or would deleting `degradation.py` silently drop it?).
- For any module confirmed genuinely missing (no live equivalent found): route the wire-vs-delete-
  vs-document decision through peer review before implementing, per this ticket's own priority and
  the precedent this whole follow-up arc has established for findings with real design stakes.
- `src/api/admission_control.py`'s own misdirecting comment (references `cache_strategy.py` as if
  describing live behavior) should be corrected once `cache_strategy.py`'s own disposition is
  settled — either point at the real live implementation, or state plainly that the referenced
  code is dead and the comment is illustrative only.

## Out of Scope
- The 9th module, `feature_flags.py` — confirmed live and load-bearing (gates every pipeline phase
  via `FeatureFlagManager.get_flag_mode()`/`set_flag_mode()`, called from `src/engine/pipeline.py`).
  Its own 3 unused convenience methods (`get_all_flags`, `is_enabled`, `is_shadow`) are a much
  smaller, separate finding — not part of this ticket's own scope (file separately if worth it;
  low priority, surface-level per the audit's own classification).
- Any other cluster from the same audit (`docs/audits/unreachable_code_inventory.md`'s C2/C3/C4) —
  each has, or will have, its own ticket.
- Full execution of whatever disposition is determined per module — this ticket is the
  determination; implementing "delete" or "wire" for any specific module is its own follow-up once
  decided, per the audit's own Out of Scope precedent (determine, don't fix, in the same pass).

## Acceptance Criteria
- [ ] Each of the 8 modules has an explicit, evidence-backed determination: superseded (name the
      live equivalent, with direct comparison) or genuinely missing (confirm no live equivalent
      exists, not just "none found yet").
- [ ] For every module determined superseded: confirmed that no unique behavior would be silently
      lost by deleting it, or that behavior is named as a real gap to preserve during deletion.
- [ ] For any module determined genuinely missing: a wire/delete/document decision is obtained via
      peer review before implementation.
- [ ] `admission_control.py`'s own `cache_strategy.py`-referencing comments are corrected to match
      whatever `cache_strategy.py`'s own real disposition turns out to be.

## Related Tickets
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (origin — Cluster C1)
- `TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION` (the same failure shape —
  two competing mechanisms for the same job — already confirmed real at a smaller scale; this
  ticket checks whether the same pattern exists at subsystem scale)
- `TCK-20260911-WORKER-UTILIZATION-ZERO-WORKERS-DEGRADED-MISTRIGGER` (the ticket that confirmed
  `ResourceGovernor` is live and load-bearing, the evidence base for the degradation.py comparison)

## Related Docs
- `docs/audits/unreachable_code_inventory.md` (Cluster C1's own full writeup)
- `docs/engine/governance_logic.md` (if it exists — the live governor/policy system's own
  documented contract, check during Investigate)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `src/domains/optimization/` (all 9 modules)
- `src/engine/governor.py` (`ResourceGovernor` — the confirmed live equivalent for `degradation.py`)
- `src/engine/policy.py`, `src/engine/phase_governor.py`, `src/config/optimization_profiles.py`
  (`GovernorPolicy`/`PhaseBudgets` — the plausible live equivalent for `budget_manager.py`)
- `src/api/admission_control.py` (the misdirecting comment referencing `cache_strategy.py`)

## Assumptions / Open Questions
- Whether `dirty_scheduler.py`, `memory_limits.py`, `diagnostics.py`, `provider_enforcement.py`,
  `trace_governor.py` each have a live equivalent is genuinely unknown — not investigated beyond
  confirming they have zero production imports. Do not assume the superseded-pattern holds
  uniformly across all 8 just because it holds for 2; each needs its own real check.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
