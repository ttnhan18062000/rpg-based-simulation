# Investigation — TCK-20260911-OBSERVABILITY-CONFIG-UNUSED-FEATURE-FLAG-GATES-INVESTIGATION

## Re-verifying the ticket's own premise first

Re-checked the ticket's own claim ("10 unused, 3 genuinely-similar siblings ARE real, live-called
methods, ruling out 'naming artifact'") before trusting it. First pass (narrow grep, method calls
in `src/` only) found zero real callers for the 3 claimed-live siblings too
(`is_live_stream_enabled`, `is_behavior_normalization_enabled`, `is_dashboard_export_enabled`) —
which would have overturned the ticket's own premise. A broader re-check (including `tests/`)
initially showed non-zero hits and nearly caused a false "actually the ticket was wrong"
conclusion — but those hits were all inside one test file
(`tests/unit/config/test_phase19_observability_feature_flags.py`) asserting the *flag's own value*
across modes, not real consumer usage. Re-narrowed to `src/`-only, confirmed **zero real production
callers for all 3 "live" siblings too**, same as the 10 under investigation. The ticket's own "3
live siblings" framing does not hold as literally stated — but see the structural finding below,
which explains why and matters more than the literal call count.

## The real gating pattern in this codebase (found while investigating flag #1)

`src/observability/cognition/recorder.py:31-58` (`should_capture()`) checks
`ObservabilityConfig.get_mode()` directly — the coarse `ObservabilityMode` enum
(OFF/LIGHT/NORMAL/FULL/RESEARCH/DEBUG/CERTIFICATION/LONG_RUN) — via explicit mode-comparison
branches, not any of the fine-grained `is_X_enabled()` convenience methods. Its own comment
(lines 46-50) already documents exactly this mismatch as a known, ticketed gap for its own case:
*"NORMAL/FULL/RESEARCH were previously excluded here despite ObservabilityConfig's flag table
marking them progressively richer than LIGHT (OBS_BEHAVIOR_NORMALIZATION/OBS_BEHAVIOR_SCORECARDS
etc.) — a real mismatch between the mode table's documented intent and this policy's actual
behavior (`TCK-20260805-COGNITION-GRAPH-CAPTURE-CORPUS-GAP`)."*

`src/engine/kernel.py:270-273` confirms the same pattern for `EventRecorder`: `enabled=(obs_mode !=
ObservabilityMode.OFF)` — gated by the coarse mode directly, not `is_event_recorder_enabled()`.
Same for `EntityTimelineStore(mode=obs_mode)` immediately below it.

**This is the structural reason the flags are unused, generalized past this one ticket's own
scope**: `ObservabilityConfig`'s 17-flag `OBS_*` preset table was designed to let subsystems opt in
at fine granularity per mode. In practice, real consumers check the coarse `get_mode()` directly
and branch on `ObservabilityMode` themselves — the fine-grained per-flag distinctions the preset
table encodes are largely decorative, since almost nothing actually reads them to make that
distinction. Only 2 of the 17 `is_X_enabled()` methods are called by name anywhere in real code
(`is_decision_trace_enabled()` in `decision_trace_writer.py:103`, `is_runtime_profiling_enabled()`
in `profiler.py:96`) — confirmed via a full sweep of all 17, not just the 10+3 the ticket names.

## Per-flag determination (the 10 in scope)

**Bucket 1 — subsystem runs based on the coarse mode directly, this specific flag is genuinely
unused scaffolding, subsystem itself is fine:**
- `is_event_recorder_enabled` (`OBS_EVENT_RECORDER`): `EventRecorder` gated by
  `obs_mode != ObservabilityMode.OFF` in `kernel.py:272`, confirmed live and load-bearing
  throughout this whole audit arc's own instrumentation. This flag itself is never consulted.
- `is_entity_timeline_enabled` (`OBS_ENTITY_TIMELINE`): `EntityTimelineStore(mode=obs_mode)`,
  same pattern, `kernel.py:277`.
- `is_warehouse_ingest_enabled` (`OBS_WAREHOUSE_INGEST`): the warehouse subsystem
  (`src/observability/warehouse/`) is real and reachable via `src/cli/entry.py`'s own `warehouse`
  subcommand (`ingest-run`/`ingest-sweep`/`query`) and read by `src/api/routes/{search,behavior}.py`
  — but it's an operator-invoked CLI tool, not a per-tick kernel mechanism, and no code checks this
  or any flag before allowing the CLI command to run. Unconditional-when-invoked, different flavor
  of Bucket 1 than the two above (on-demand tool vs. always-running kernel component), but the same
  disposition: the flag itself is vestigial.

**Bucket 2/3 — a real, previously-undiscovered "inert end to end" finding, bigger than this
ticket's own framing anticipated:**
- `is_behavior_timeline_enabled`, `is_behavior_episodes_enabled`, `is_behavior_metrics_enabled`,
  `is_behavior_patterns_enabled`, `is_behavior_scorecards_enabled`, `is_cohort_analysis_enabled`,
  `is_run_comparison_enabled`, `is_insight_generation_enabled` (8 of the 10) all map to
  `src/observability/behavior/`'s own analysis pipeline — a real, substantial, individually
  *tested* subsystem (`BehaviorWorker`, `EpisodeDetector`, `CohortAnalyzer`,
  `RunBehaviorComparison`, `BehaviorMetricsAggregator`, `PatternDetector`, each with its own
  dedicated test file: `tests/unit/observability/behavior/test_phase{22,23,24,26}_*.py`,
  `tests/integration/observability/test_phase22_behavior_worker_from_{stream,jsonl}.py`).
  **None of these classes has a single real construction site anywhere in production code.**
  `BehaviorWorker(` — the intended top-level entry point — is never constructed outside its own
  file and its own tests, despite `kernel.py:1221`'s own comment ("Wire BehaviorWorker into
  shutdown: join any running behavior-normalization threads") implying it IS wired — confirmed
  false, the same "confident comment describing behavior that doesn't happen" class as three other
  instances already found this batch (`invalidate_read_model`, the survivor-branch placement claim,
  `campaigns.py`'s `register_campaign()` claim).
  - This is **not** "genuinely missing" (nothing built) — it's built, real, and tested in isolation,
    just never wired into the real Kernel/CLI/API startup path. The exact "designed, built, tested,
    disconnected" shape this whole audit arc found for `CooperationPosture.JOIN_PARTY` before the
    party-formation fix.
  - **Same shape as the already-closed `TCK-20260911-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-
    POPULATED-IN-PRODUCTION` finding, at larger scale**: `src/api/routes/behavior.py` has **7** live
    `@router.get` read endpoints (`get_behavior_events`, `get_entity_behavior_timeline`,
    `get_entity_behavior_episodes`, `get_run_behavior_scorecard`, `get_run_behavior_insights`,
    `get_run_cohorts`, `compare_run_behavior`) that read from `LocalWarehouseAdapter` — the same
    warehouse store `BehaviorWorker`'s own analysis pipeline would write to, if it ran. Since
    nothing populates it, every real request against all 7 endpoints returns empty/404, always, by
    construction — a public API surface backed by a store nothing writes to.
  - The 8 `is_X_enabled()` flags being unused is a symptom of this, not an independent cause: even
    if every one were wired to a real gate check, there's no live call site that would consult it,
    since `BehaviorWorker` itself is never started.

## A pattern spanning two tickets, not a coincidence

This is the **second** case this batch of live API endpoints backed by a store nothing populates:
- Campaigns/chronicle (`TCK-20260911-CAMPAIGN-CHRONICLE-API-REGISTRY-NEVER-POPULATED-IN-
  PRODUCTION`): 2 endpoints, registry never populated in production.
- Behavior (this ticket): 7 endpoints, warehouse never populated because its own pipeline is never
  started.

**That's 9 public endpoints across two subsystems returning empty or 404 in production, always, by
construction.** Two instances of the same shape in one batch isn't coincidence — it suggests the
API surface in this codebase was built ahead of the data sources meant to feed it, systematically,
not as a one-off. Cross-referenced in both tickets. Whoever picks up either should treat them as
possibly one problem with two faces, and should check whether any *other* route module reads a
store with no production writer before assuming these are the only two.

## Two generalizable lessons, worth recording for whoever does this kind of pass next

1. **Grep scope can produce a confidently wrong answer in both directions, not just the narrow
   one.** `TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION` (this batch's
   prior ticket) caught a narrow-grep false negative (`trace_governor.py` — missing a real live
   equivalent because the keyword search didn't share vocabulary with it). This investigation
   caught the opposite: a *broad* grep (including `tests/`) nearly produced a false "the ticket's
   own premise is wrong" conclusion, because it counted test-file assertions on a flag's own value
   as if they were real consumer usage. Both were caught before finalizing by re-checking against a
   known case rather than trusting the search's own output. The transferable lesson: verify a
   grep's scope against a case you can reason about independently before trusting its answer, in
   either direction — narrow searches miss real matches, broad searches manufacture fake ones.
2. **The coarse-vs-fine gating mismatch generalizes past the 10 flags this ticket named.** Only 2
   of all 17 `is_X_enabled()` convenience methods on `ObservabilityConfig` are called by name
   anywhere in real code (`is_decision_trace_enabled`, `is_runtime_profiling_enabled`) — confirmed
   via a full sweep of all 17, not just the 10+3 the ticket's own Request Summary named. The real
   scope of "is this convenience-method layer used" is larger than what was asked; not resolved
   here, since the ticket's own AC is the 10 named flags, but worth recording so a future pass
   knows the remaining 5 (`is_raw_events_enabled` and 4 not otherwise covered) haven't been checked
   either.

## Summary table

| Flag | Real subsystem | Bucket | Disposition |
|---|---|---|---|
| `is_event_recorder_enabled` | `EventRecorder` (live, mode-gated directly) | 1 | Delete convenience method |
| `is_entity_timeline_enabled` | `EntityTimelineStore` (live, mode-gated directly) | 1 | Delete convenience method |
| `is_warehouse_ingest_enabled` | warehouse CLI/API (live, unconditional-when-invoked) | 1 | Delete convenience method |
| `is_behavior_timeline_enabled` | `BehaviorWorker` pipeline (built, tested, never wired) | 2/3 | See disposition below — do not decide in isolation from the other 7 |
| `is_behavior_episodes_enabled` | `EpisodeDetector` (built, tested, never wired) | 2/3 | ” |
| `is_behavior_metrics_enabled` | `BehaviorMetricsAggregator` (built, tested, never wired) | 2/3 | ” |
| `is_behavior_patterns_enabled` | `PatternDetector` (built, tested, never wired) | 2/3 | ” |
| `is_behavior_scorecards_enabled` | (same pipeline, scorecard output) | 2/3 | ” |
| `is_cohort_analysis_enabled` | `CohortAnalyzer` (built, tested, never wired) | 2/3 | ” |
| `is_run_comparison_enabled` | `RunBehaviorComparison` (built, tested, never wired) | 2/3 | ” |
| `is_insight_generation_enabled` | (same pipeline, insight output) | 2/3 | ” |

## Disposition

**Bucket 1 (3 flags)**: safe to delete as vestigial scaffolding — real, confirmed, this ticket's
own disposition, no design question. `EventRecorder`/`EntityTimelineStore`/warehouse CLI all work
correctly today via the coarse `obs_mode` gate; nothing is lost by removing these 3 unused
convenience methods.

**Bucket 2/3 (8 flags, one underlying subsystem)**: **not decided here** — this is a real design
question bigger than "delete 8 unused methods." Whether to wire `BehaviorWorker`'s pipeline into
the real Kernel/CLI startup path (a real feature that's fully built and tested, just disconnected)
or to leave it as deliberately-deferred/formally document it as such is a genuine product decision,
not a cleanup — the same class of decision this whole audit arc has routed to peer/user rather than
resolved unilaterally. The 5-6 empty/404 API endpoints in `behavior.py` are the concrete,
observable, public-facing consequence either way. Filed as its own finding, cross-referenced to the
already-closed sibling finding for campaigns/chronicle, rather than resolved as part of this
ticket's own "delete unused flags" framing.
