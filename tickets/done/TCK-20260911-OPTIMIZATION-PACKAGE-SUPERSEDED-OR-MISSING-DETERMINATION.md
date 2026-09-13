---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION
phase: done
date: 2026-09-11
tags: [performance, architecture]
---

# TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION

## Title
`src/domains/optimization/`'s 8 unwired modules — determine per-module whether each is a
superseded duplicate of a live mechanism or a genuinely missing one, before deciding anything

## Status
DONE

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
- [x] Each of the 8 modules has an explicit, evidence-backed determination: superseded (name the
      live equivalent, with direct comparison) or genuinely missing (confirm no live equivalent
      exists, not just "none found yet"). Done — but the real finding refines the framing: none of
      the 8 is cleanly one or the other. Every module is *partially* superseded (a live mechanism
      does the core job) *with orphaned unique capability* (something the dead module alone did was
      never carried forward). Only `diagnostics.py` is a clean, fully-superseded case.
- [x] For every module determined superseded: confirmed that no unique behavior would be silently
      lost by deleting it, or that behavior is named as a real gap to preserve during deletion. Done
      for all 8 — this check is what surfaced the "partially superseded" finding above; 6 of the 8
      unique-capability behaviors are named and routed to
      `TCK-20260912-OPTIMIZATION-ORPHANED-CAPABILITY-DETERMINATION` for their own decision.
- [x] For any module determined genuinely missing: a wire/delete/document decision is obtained via
      peer review before implementation. Routed, not resolved here, per this ticket's own Scope
      ("determine, don't fix") — `budget_manager.py` and `provider_enforcement.py` each filed as
      their own standard-tier determination ticket.
- [x] `admission_control.py`'s own `cache_strategy.py`-referencing comments are corrected to match
      whatever `cache_strategy.py`'s own real disposition turns out to be. Confirmed the comments
      are misdirecting (imply a dependency that doesn't exist — `admission_control.py` never
      imports `cache_strategy.py`, it only borrowed the LRU-eviction *shape* as a pattern reference
      for an unrelated domain). Correction folded into
      `TCK-20260912-OPTIMIZATION-ORPHANED-CAPABILITY-DETERMINATION`'s own scope, to land alongside
      `cache_strategy.py`'s eventual real disposition rather than as a disconnected doc fix here.

## Related Tickets
- `TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT` (origin — Cluster C1)
- `TCK-20260909-LEAD-CAPACITY-ENFORCEMENT-DUAL-MECHANISM-PREEMPTION` (the same failure shape —
  two competing mechanisms for the same job — already confirmed real at a smaller scale; the
  qualification, not full-match, found here for `degradation.py`)
- `TCK-20260911-WORKER-UTILIZATION-ZERO-WORKERS-DEGRADED-MISTRIGGER` (the ticket that confirmed
  `ResourceGovernor` is live and load-bearing, the evidence base for the degradation.py comparison)
- `TCK-20260912-OPTIMIZATION-DIAGNOSTICS-DEAD-CODE-DELETION` (follow-up A — clean deletion)
- `TCK-20260912-OPTIMIZATION-MEMORY-LIMITS-ABANDONED-DESIGN-DELETION` (follow-up B —
  `memory_limits.py`'s own disposition)
- `TCK-20260912-OPTIMIZATION-ORPHANED-CAPABILITY-DETERMINATION` (follow-up C — the 6-capability
  "is this wanted" determination)
- `TCK-20260912-OPTIMIZATION-BUDGET-MANAGER-MISSING-DETERMINATION` (follow-up D)
- `TCK-20260912-OPTIMIZATION-PROVIDER-ENFORCEMENT-MISSING-DETERMINATION` (follow-up E)

## Related Docs
- `docs/audits/unreachable_code_inventory.md` (Cluster C1's own full writeup)
- `docs/engine/governance_logic.md` (if it exists — the live governor/policy system's own
  documented contract, check during Investigate)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION/`
  (`investigation.md`, `plan.md`, `test_plan.md`)

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
Manual, module-by-module pass, per standing instruction — not another automated sweep, since the
origin audit's own tool has a confirmed generic-name blind spot (`cache_strategy.py`'s `CacheKey`/
`CacheStrategy` never appeared in its output at all). Each of the 8 modules was compared against the
real live mechanism doing its job today, verified by reading that mechanism directly.

Peer review's own `degradation.py`/`governor.py` lead was treated as exactly that — a lead, not a
conclusion — and re-verified independently. It held for the core pressure-level computation
(confirmed structural match to `ResourceGovernor._get_indicated_mode()`), but not fully: acting on
"superseded, delete" as originally framed would have deleted `should_skip_phase()`'s and
`resolve_content_source()`'s real, undocumented-elsewhere capability. This is the second time this
audit arc a lead would have caused real loss if inherited rather than verified.

**Headline finding, a genuine refinement of the parent audit's own conclusion**: the audit's
"superseded, not missing" pattern held cleanly for `BiologicalSystem`/`spawn_calamity()`/
`effective_certainty()` — a live replacement fully covers the dead code's job, safe to delete. It
does not hold cleanly here. Every one of these 8 modules is *partially* superseded, with *orphaned
unique capability* — a live mechanism took over the core job, but something the dead module alone
did was never carried forward, and no one built a replacement for it. "Superseded" here is not
automatically "safe to delete." Every disposition was written at method/behavior granularity, not
file granularity, specifically so a future reader can't misread "superseded" as "delete the file."

Caught and corrected one instance of the same blind-spot risk in manual form, mid-investigation:
`trace_governor.py`'s initial narrow keyword grep (`max_trace_events`, `trace_volume`,
`TraceVolumeGovernor`) found nothing and would have wrongly concluded "genuinely missing." Checking
the real, broader live event-volume-management system (`EventRecorder`, which shares no vocabulary
with `trace_governor.py` at all) directly found a real, confirmed-live, functionally-overlapping
mechanism instead. Recorded explicitly in investigation.md as a generalizable lesson: a keyword
search, automated or manual, only finds what already uses the same words.

Filed 5 follow-up tickets, grouped by decision type per peer review's explicit direction (8
per-module tickets would have fragmented one question into eight): a clean deletion
(`diagnostics.py`), `memory_limits.py`'s own standalone disposition (one half superseded, one half
abandoned design — distinct reasoning from the clean-deletion case, kept separate), one
orphaned-capability determination covering all 6 genuinely-unique behaviors found across 4 modules
(one decision session), and two separate genuinely-missing determinations
(`budget_manager.py`, `provider_enforcement.py` — different "should we build this" questions each,
flagged for possible overlap on provider-call budgeting but not resolved here).

No code changed in this ticket — determination and follow-up tickets only, per this ticket's own
explicit Scope.

## Test Summary
Determination-only — no `src/`/`tests/` code changed, so no new automated tests. Verification is
the investigation's own evidence trail: each of the 8 modules read and compared directly against
its real live counterpart (not grepped-and-assumed), with one explicit self-correction recorded to
demonstrate the check held under its own stated method. `tests/integrity/
test_no_duplicate_content_blocks.py` and `validate_frontmatter.py --content-type ticket` passed on
this ticket and all 5 newly-filed follow-ups.

## Files Changed
- `stored_artifacts/TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION/{investigation.md,plan.md,test_plan.md}`
  — full evidence trail and disposition.
- `tickets/todos/TCK-20260912-OPTIMIZATION-DIAGNOSTICS-DEAD-CODE-DELETION.md` — new (follow-up A).
- `tickets/todos/TCK-20260912-OPTIMIZATION-MEMORY-LIMITS-ABANDONED-DESIGN-DELETION.md` — new
  (follow-up B).
- `tickets/todos/TCK-20260912-OPTIMIZATION-ORPHANED-CAPABILITY-DETERMINATION.md` — new (follow-up
  C).
- `tickets/todos/TCK-20260912-OPTIMIZATION-BUDGET-MANAGER-MISSING-DETERMINATION.md` — new
  (follow-up D).
- `tickets/todos/TCK-20260912-OPTIMIZATION-PROVIDER-ENFORCEMENT-MISSING-DETERMINATION.md` — new
  (follow-up E).
- `tickets/done/TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION.md` — this
  file, closed.
- No `src/` or `tests/` files changed.

## Completion Summary
Determined all 8 `src/domains/optimization/` modules manually, module-by-module, per this ticket's
own explicit "determine, don't fix" scope. The real finding refines the parent audit's own
conclusion: this package is not cleanly "superseded" or "missing" — every module is *partially*
superseded, carrying at least one genuinely distinct capability the live replacement never carried
forward (`diagnostics.py` is the sole clean exception). Peer review's own `degradation.py`/
`governor.py` lead held for the core job but would have caused real capability loss if acted on
as-framed — confirmed, not assumed, per standing discipline. One self-correction recorded
(`trace_governor.py`) as a demonstration of the same keyword-blind-spot risk in manual form.

Filed 5 follow-up tickets grouped by decision type, each written at method/behavior granularity to
prevent a future reader from collapsing "partially superseded" into "delete the file": one clean
deletion, one module with its own distinct abandoned-design reasoning, one combined
orphaned-capability determination covering 6 real behaviors across 4 modules, and two separate
genuinely-missing build/don't-build determinations. No code deleted or wired in this ticket itself.
