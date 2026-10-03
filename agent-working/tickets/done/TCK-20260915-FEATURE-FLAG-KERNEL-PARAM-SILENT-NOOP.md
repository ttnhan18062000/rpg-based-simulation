---
status: historical
layer: engine
authority: P0
audience: agent
ticket_id: TCK-20260915-FEATURE-FLAG-KERNEL-PARAM-SILENT-NOOP
phase: done
date: 2026-09-15
tags: [feature-flags, observability]
---

# TCK-20260915-FEATURE-FLAG-KERNEL-PARAM-SILENT-NOOP

## Title
`Kernel(flags={"ENABLE_<X>": "ON"/"OFF"})` silently does nothing for any `run_phase()`-gated
feature flag — the real lever is `state.feature_flags`, set on the frozen state before `Kernel`
construction; confirmed to have invalidated at least one prior investigation's own toggle

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P0

## Request Summary
While re-verifying `TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION`'s gate (does
it actually reduce real attacks when `ENABLE_COMBAT_ENGAGEMENT` flips OFF vs ON), a corrected A/B
using `state.feature_flags` directly produced a genuinely different result (1960 OFF -> 837 ON with
the gate active) from every prior A/B in this same investigation, which used
`Kernel(profile=..., state=..., rng=..., flags={"ENABLE_COMBAT_ENGAGEMENT": "ON"/"OFF"})` and
always got identical OFF/ON counts.

**Root cause, confirmed by direct read of both files:**
- `src/engine/pipeline.py::AuthoritativeApplyPipeline.refine()`'s inner `run_phase()` resolves a
  phase's enabled/disabled/shadow mode via `ff_manager.get_flag_mode(feature_flag)`, where
  `ff_manager` is a fresh `FeatureFlagManager()` populated from `state.feature_flags` (lines ~68-92:
  `if getattr(state, "feature_flags", None) is not None: for k, v in state.feature_flags.items():
  ff_manager.set_flag_mode(k, v)`).
- `src/engine/kernel.py::Kernel.__init__`'s `flags: Optional[Dict[str, Any]] = None` parameter is a
  **completely separate namespace** — it only ever reads specific engine-level keys (`audit_mode`,
  `audit_dirty_set`, `perf_tracker`, `force_full_scan`, `no_frame_pacing`, `no_replay`). It has no
  code path that writes into `state.feature_flags` at all. A key like
  `"ENABLE_COMBAT_ENGAGEMENT"` passed there is read by nothing and silently dropped.
- Separately, `Kernel.__init__` *does* seed `state.feature_flags` from `FeatureFlagManager()`'s own
  registered defaults (`_manager_defaults = FeatureFlagManager().serialize(); ...
  object.__setattr__(self._state, "feature_flags", {**_manager_defaults, **_existing_flags})`) —
  but only fills gaps the caller never set (`_existing_flags` wins), it does not accept overrides
  through the `Kernel(flags=...)` argument itself. This defaulting behavior is
  `TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS`'s own fix for a
  *different* problem (a flag's default not applying when nothing overrides it) and is not itself
  the bug — it's the reason the silent no-op above is easy to miss: `Kernel(flags={"ENABLE_X":
  "OFF"})` looks like it should work, does nothing, and the flag then falls back to its registered
  default (`ON` for `ENABLE_COMBAT_ENGAGEMENT`), which is indistinguishable from "the OFF override
  worked and the default happens to also be ON" unless you check both conditions.

**Confirmed real-world impact**: every prior probe in this session's combat_engagement
investigation (including the four-condition A/B published in
`TCK-20260915-COMBAT-ENGAGEMENT-4X-MEASUREMENT-NO-LONGER-REPRODUCES` and
`docs/plans/design_enhancement/performance_optimization/performance_m4_baseline_gate_a_epic.md`'s
2026-09-15 correction) used this exact pattern. Every condition in that A/B was actually running
with `ENABLE_COMBAT_ENGAGEMENT` genuinely ON regardless of the value passed — the "OFF" condition
was never really OFF. **The underlying conclusion (no measurable causal effect on real combat
volume) was independently re-verified with the corrected toggle and still holds** — see that
ticket's Implementation Notes — so no downstream conclusion needs retracting. But this was luck,
not a property of the methodology: a different phase, or a different question, could have produced
a confidently wrong answer via this exact same broken-toggle pattern.

## Scope
- Document the correct way to toggle a `run_phase()`-gated feature flag for a real A/B: set it
  directly on the (frozen) `AuthoritativeState.feature_flags` dict via `object.__setattr__` before
  constructing the `Kernel`, not via `Kernel(flags=...)`.
- ~~Audit other probe scripts / investigation tickets in this repo's history that used
  `Kernel(flags={"ENABLE_...": ...})`~~ — **done, see Implementation Notes below** (peer flagged
  this as the first task before closing rather than leaving it as a named-but-unchecked risk).
- Consider (not decided here) whether `Kernel.__init__`'s `flags` parameter should reject or warn
  on an unrecognized `ENABLE_*`-shaped key, to make this failure mode loud instead of silent — this
  is a design decision for whoever picks this up, not assumed here.

## Out of Scope
- Any code change to `Kernel.__init__` itself (e.g. adding a warning/rejection for unrecognized
  flag-shaped keys) — a real design decision left to a future ticket if picked up.

## Acceptance Criteria
- Root cause identified and confirmed via direct code read (done, see Request Summary).
- The specific investigation this bug was found in (`TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-
  WIRED-TO-EXECUTION` / `TCK-20260915-COMBAT-ENGAGEMENT-4X-MEASUREMENT-NO-LONGER-REPRODUCES`)
  re-verified with the corrected toggle, and the corrected methodology documented in both tickets.
- This ticket exists as a discoverable, standalone record of the pattern for future investigators,
  independent of the specific combat_engagement work that surfaced it.

## Related Tickets
- `TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION` (the gate build whose
  verification surfaced this)
- `TCK-20260915-COMBAT-ENGAGEMENT-4X-MEASUREMENT-NO-LONGER-REPRODUCES` (the sibling measurement
  ticket whose own four-condition A/B used the broken toggle)
- `TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS` (a related but
  distinct prior fix — that ticket made a flag's *default* apply consistently; it did not address,
  and does not fix, `Kernel(flags=...)` being unable to *override* a flag)

## Related Docs
- `docs/plans/design_enhancement/performance_optimization/performance_m4_baseline_gate_a_epic.md`

## Related Stored Artifacts
_(none — hotfix-tier finding, no staging artifacts required)_

## Related Code Areas
- `src/engine/kernel.py::Kernel.__init__`
- `src/engine/pipeline.py::AuthoritativeApplyPipeline.refine()` (the `run_phase()` closure and its
  `ff_manager` construction)
- `src/domains/optimization/feature_flags.py::FeatureFlagManager`

## Assumptions / Open Questions
- Whether to make this failure mode loud (reject/warn on `Kernel(flags=...)` receiving an
  `ENABLE_*`-shaped key) is left as an open design question for whoever next touches
  `Kernel.__init__`'s `flags` parameter — not decided or implemented here.

## Implementation Notes
No source code changed by this ticket — it is a documentation/discoverability fix for a
measurement-methodology bug, not a code defect in the flag system itself (the two mechanisms
*correctly* do different things; the bug is that this looks like one mechanism from the call site).
The corrected toggle used in the sibling tickets:
```python
existing = dict(getattr(state, "feature_flags", None) or {})
existing["ENABLE_COMBAT_ENGAGEMENT"] = "OFF"  # or "ON"
object.__setattr__(state, "feature_flags", existing)
kernel = Kernel(profile=..., state=state, rng=..., flags={"no_frame_pacing": True})
```

**Audit of historical usage (per peer's explicit request, done before closing rather than left as
a named-but-unchecked risk).** Searched `stored_artifacts/`, `tickets/`, `tests/`, and every real
`Kernel(...)` construction site in `src/` and `tools/` for the broken pattern
(`Kernel(flags={"ENABLE_...": ...})`). **Result: no other instance found.**
- Every real production/tooling `Kernel(...)` call site (`src/certification/harness.py`,
  `src/perf/bench_harness.py`, `src/perf/long_run_harness.py`, `src/domains/campaigns/runner.py`,
  `src/engine/scenario_runtime.py`, `tools/calibrate_simq.py`, `tools/personality_audit.py`, etc.)
  passes only genuine engine-level knobs through `flags=` (`audit_mode`, `no_replay`,
  `no_frame_pacing`, `force_full_scan`, `perf_tracker`) — never an `ENABLE_*` key.
  `src/perf/bench_harness.py`/`long_run_harness.py`'s own `flags` parameter (forwarded from their
  own `run(...)` callers into `Kernel(flags=effective_flags)`) was checked specifically, since
  peer named the perf A/Bs as at-risk — no caller in `tests/perf/` or elsewhere passes an
  `ENABLE_*` key through that path either; every perf test that touches a feature flag does so via
  `state.feature_flags=` directly, the correct mechanism.
- Every test fixture and stored-artifact plan that sets a feature flag (dozens of call sites
  across `tests/unit/`, `tests/integration/`, `tests/simulation_quality/`) uses
  `feature_flags={...}` on the state object directly — including the one helper with a
  confusingly-named `flags` parameter (`tests/unit/ai/test_guild_need_scorer.py::
  _state_with_town_hall`), which correctly forwards it to `AuthoritativeState(feature_flags=flags)`
  rather than to `Kernel`.
- **The original 2026-09-14 measurement this whole investigation traces back to
  (`TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER`) used a third, also-correct methodology**:
  flipping the literal registered default in `src/domains/optimization/feature_flags.py` itself
  (`"ENABLE_COMBAT_ENGAGEMENT": FeatureMode.OFF -> ON`) and measuring before/after that source
  change, per its own `plan.md`/`test_plan.md`. This is not affected by the `Kernel(flags=...)`
  bug either, since it never goes through that parameter at all — **this rules out "the original
  4.1x measurement itself used the broken toggle" as an explanation for why it doesn't reproduce**,
  narrowing `TCK-20260915-COMBAT-ENGAGEMENT-4X-MEASUREMENT-NO-LONGER-REPRODUCES`'s own still-open
  historical question toward its other candidates (a differing original metric, or a real
  behavior change from the spatial-index/cognition-merge fixes that landed the same day).
- **Conclusion: the broken pattern appears to be contained to this investigation's own throwaway
  probe scripts** (never committed to the repo), not to any historical, committed measurement.
  The residual risk named in the original version of this ticket is now closed out rather than
  left open-ended.

## Test Summary
No test changes — this is a probe-methodology finding, not a behavior change.

## Files Changed
_(none)_

## Completion Summary
Closed as a documented, standalone finding. Root cause confirmed via direct code read; the specific
investigation it was found in was re-verified with the corrected toggle and its conclusions held.
The historical audit peer requested was completed (not left as a named-but-unchecked risk): no
other instance of the broken pattern was found in any real production `Kernel(...)` call site, test
fixture, or stored-artifact plan, and the original 2026-09-14 measurement this investigation traces
back to used a third, unaffected methodology (flipping the literal registered default). The broken
pattern appears contained to this investigation's own throwaway probes.
