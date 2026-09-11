---
status: active
layer: architecture
authority: P1
audience: agent
tags: [audit, dead-code, architecture]
---

# Unreachable Implemented Code — Audit

`TCK-20260909-UNREACHABLE-IMPLEMENTED-CODE-AUDIT`. Produced by `tools/audit_unreachable_code.py`
(committed, re-runnable — see that file's own docstring for full method detail). Raw structured
data: `docs/audits/unreachable_code_inventory.{json,csv}`.

**Distinct from `D11_dead_code.md`** (directory-level orphan-cluster analysis, later found to have
a 100% false-positive rate from grep-based import counting — see that doc's own "Post-Audit
Correction"). This audit works at function/method granularity via AST-based definition collection
and whole-corpus identifier occurrence counting, specifically designed to avoid D11's own confirmed
failure mode (missing lazy/deferred imports, which this codebase uses heavily).

## Method summary

1. Collect every module-level function/class and class method defined in `src/` via `ast`.
2. Tokenize every file in `src/`, `tests/`, `tools/` once; count occurrences of every identifier.
3. A definition is a candidate if it has **zero occurrences in `src/` outside its own definition
   line** — checked including the same file (a private helper called by a sibling function in the
   same module is alive, not a false positive of "used elsewhere").
4. Test/tool-only usage is tracked **separately**, not folded into the reachability verdict — per
   this ticket's own definition ("no live call site outside their own definition **and their own
   tests**"), a function called only by its own unit test is still not reachable at runtime.
5. Two false-positive categories are excluded automatically, by decorator, with the excluding
   decorator recorded per entry (not silently filtered): FastAPI route/websocket handlers, Pydantic
   validators. Both are real "framework-invoked hooks" (the exclusion category named in this
   ticket's own Scope) — never called by their Python name, only dispatched by their framework.

**Two real methodology bugs were found and fixed while building this tool** (full detail in the
tool's own docstring) — both caught by checking the tool's output against known ground truth
(the original 7-8 known instances), not by trusting the tool blind:
- An early version only checked "referenced outside its own file", missing same-file callers.
- An early version counted test-only usage as "reachable", which silently hid `effective_certainty()`
  — one of the original known instances — until fixed. This second bug mattered more: without the
  fix, the audit would have reported a smaller, falsely-reassuring number with full confidence.

## Headline numbers

| | Count |
|---|---|
| Raw candidates (zero `src/` call sites outside own definition) | 428 |
| Excluded — FastAPI route/websocket handlers (framework-invoked) | 42 |
| Excluded — Pydantic validators (framework-invoked) | 24 |
| **Real candidates** | **362** |
| — zero references anywhere, not even own tests | 102 |
| — test-only (unit-tested, zero production callers) | 260 |
| Real candidates falling into a same-file cluster (2+ per file) | 263 (79 files) |
| Real candidates as singletons (1 per file) | 99 |

362 of ~4305 total definitions in `src/` (~8.4%) have no real call site from live production code.

**Known limitation, confirmed in practice, not just theorized:** generic/common method names
defeat pure text-token matching. `BiologicalSystem.update()` (a known, already-confirmed dead
method from this ticket's own original seed list) can never register here, because the bare
identifier `update` appears thousands of times across the codebase. `src/domains/optimization/
cache_strategy.py`'s `CacheStrategy.get()`/`.put()`/`.invalidate()` were similarly invisible to
this tool — confirmed dead only by the direct production-import check in the Optimization Package
finding below, not by this tool's own method-name matching. A collision can only produce a false
negative (missing a real instance), never a false positive — the safer failure direction, but real
coverage is incomplete for generically-named code. This is a structural limit of text-token
matching, not a bug; a real fix needs type-aware call-graph analysis, out of this audit's own scope.

## Organizing axis: mechanism vs. surface, not zero-anywhere vs. test-only

Per peer review: raw reachability status (zero-anywhere vs. test-only) is a column in the
structured data, not the organizing principle for what follows. The distinction that actually
determines significance and response is **mechanism vs. surface**:

- **Surface** — accessors, convenience wrappers, symmetric API methods kept for completeness.
  Unreferenced is close to normal for a broad public API surface; nobody necessarily expected every
  accessor to be called yet. Lower urgency, usually a `document` or `delete` disposition.
- **Mechanism** — code built to execute per-tick, per-event, or as a gating check, as a real part
  of the live system's own control flow. Unreferenced here means something was built, tested,
  believed to work, and never actually runs. This is the significant, "wire or delete" category —
  matching the shape of `decay_stale_leads()` and `effective_certainty()`, the two most consequential
  findings from the original seven.

## Cluster findings (deep writeups)

### C1 — The `src/domains/optimization/` package: 8 of 9 modules never reached from production

**The single most significant finding of this audit — bigger than the original seven combined.**
An entire budget/degradation/diagnostics/dirty-tracking layer was built, unit-tested, and never
wired into the live `Kernel` pipeline.

Verified directly (not inferred from this tool's own per-symbol output, which missed some of this
cluster to the generic-naming limitation above): a repo-wide grep for `from src.domains.optimization`
outside the directory itself finds exactly **one** real production import —
`src/engine/pipeline.py:69` imports `FeatureFlagManager`/`FeatureMode` from `feature_flags.py`, and
that class is genuinely load-bearing (it gates every pipeline phase via `run_phase()`'s own
`ff_manager.get_flag_mode(feature_flag)` check). Even within that one live module, 3 of its own
convenience methods (`get_all_flags`, `is_enabled`, `is_shadow`) are themselves unused — real
callers use `get_flag_mode()`/`set_flag_mode()` directly instead.

The other 8 modules have **zero** real production imports anywhere:

| Module | Class(es) | Shape |
|---|---|---|
| `budget_manager.py` | `PhaseBudgetManager` | per-phase budget check-and-consume |
| `cache_strategy.py` | `CacheKey`, `CacheStrategy` | LRU-style cache with get/put/invalidate — not caught by this tool (generic method names), confirmed dead by direct import grep |
| `degradation.py` | `GracefulDegradationManager` | pressure-based feature degradation levels |
| `diagnostics.py` | `DeveloperDiagnostics` | issue recording for dev-facing diagnostics |
| `dirty_scheduler.py` | `DirtyWorkScheduler` | dirty-region/entity tracking for incremental work scheduling |
| `memory_limits.py` | `MemoryCapacityLimits` | bounded memory eviction for facts/opponents/rewards/cooperation memory |
| `provider_enforcement.py` | `ProviderBudgetEnforcement` | provider call budget enforcement |
| `trace_governor.py` | `TraceVolumeGovernor` | trace volume governance |

**A comment actively misdirects, not just silently omits.** `src/api/admission_control.py:60,97`
describes its own eviction logic as `evict-oldest-on-overflow (src/domains/optimization/
cache_strategy.py:25-34)` — a comment, not an import, pointing at `cache_strategy.py` as though it
were the live implementation admission_control.py's own local logic mirrors. A reader following
that comment would land on dead code believing it was reading the real mechanism.

**`DirtyWorkScheduler` itself splits cleanly into the two categories this audit distinguishes**,
worth noting as a microcosm of the whole package: its `*_entity*` methods (`mark_entity_dirty`,
`is_entity_dirty`, `get_dirty_entities`, `next_entities`, `clear_processed_entities`) are
unit-tested (`tests/unit/perf/test_phase10_dirty_work_scheduler.py`) but have zero production
callers (test-only); its `*_region*` methods have zero references anywhere, including tests — a
parallel tracking dimension built alongside the entity half and never exercised even once.

**Recommendation:** its own standard-tier ticket, separate from this audit (per peer review) —
determine per-module whether each was superseded by a different live mechanism (e.g. does
`GracefulDegradationManager`'s intended pressure-response role already happen some other way?) or
was simply never finished being wired in, then wire or delete accordingly. Given the package's own
apparent design (a coherent "optimization layer" cross-cutting budget/cache/degradation/tracing),
the disposition decision likely needs to be made once for the whole package, not module-by-module
in isolation.

### C2 — `ObservabilityConfig`: 10 of 17 feature-flag convenience methods unused, and their own underlying flags too

`src/observability/config.py` declares 17 `is_X_enabled()`/`set_flag_override()`-family classmethods,
each a thin wrapper (`return cls.get_flag("OBS_X")`) around a named observability feature flag.
10 are entirely unreferenced (`is_event_recorder_enabled`, `is_entity_timeline_enabled`,
`is_behavior_timeline_enabled`, `is_behavior_episodes_enabled`, `is_behavior_metrics_enabled`,
`is_behavior_patterns_enabled`, `is_behavior_scorecards_enabled`, `is_cohort_analysis_enabled`,
`is_run_comparison_enabled`, `is_insight_generation_enabled`, `is_warehouse_ingest_enabled`), while
3 genuinely-similar siblings (`is_live_stream_enabled`, `is_behavior_normalization_enabled`,
`is_dashboard_export_enabled`) are real, live-called methods — ruling out "the whole cluster is a
naming artifact my tool got wrong."

Checked further, not assumed: the underlying flag strings (`OBS_EVENT_RECORDER`,
`OBS_ENTITY_TIMELINE`, `OBS_COHORT_ANALYSIS`, `OBS_WAREHOUSE_INGEST`, spot-checked) are not read
directly anywhere else either — the convenience method isn't a redundant wrapper around a check that
exists elsewhere; the underlying feature-flag gate is genuinely never consulted by anything.

**Mechanism or surface is not yet determined** — needs its own Investigate: does the observability
subsystem each flag names (entity timeline, cohort analysis, warehouse ingest, etc.) run
unconditionally (making the flag dead-but-harmless scaffolding for a future kill-switch), or does it
never run at all (making the missing gate check moot), or is there a real gap where the subsystem
should be checking this flag and isn't? That distinguishes a `document` disposition from a real
`wire` bug.

### C3 — `CatalogRepository`: 5 accessor methods, `V2EntityBuilder`: 11 `replace_*` methods — surface, not mechanism

Both are large, genuinely-live classes (many other methods/fields on each are real and load-bearing)
with a subset of accessor/builder methods never called. `CatalogRepository.get_terrain`,
`.get_spawn_table`, `.get_class_table`, `.get_default_profile`, `.get_deprecated_ids` — likely
content types whose catalog accessor was added ahead of (or after) real consumer wiring.
`V2EntityBuilder`'s 11 `replace_*` methods (of which `.replace_cognition`/`.replace_strategic`/
`.replace_biological`/`.replace_equipment`/`.replace_interaction`/`.replace_stamina`/
`.replace_self_model` are test-only and `.replace_social`/`.replace_attributes`/`.replace_aptitude`/
`.replace_task` are entirely unreferenced) — a builder-pattern method-per-field surface where only
some fields' own replace method ever gets called from real construction code. Classified **surface**:
neither cluster represents a per-tick mechanism failing to run; both are broad API surfaces where
partial usage is closer to normal than alarming. Lower priority than C1/C2.

### C4 — `unregister_campaign`/`unregister_chronicle`: a real, narrow, confirmed bug

`src/api/routes/campaigns.py`/`chronicle.py` each declare a `register_X`/`unregister_X` pair over an
in-memory dict registry. `register_X` is genuinely called (from tests, injecting state for API
tests). `unregister_X` has zero call sites anywhere, including its own tests — the test file's own
docstring says cleanup uses a separate `_clear_registry()` instead. A real, narrow, already-fully-
verified instance: the cleanup half of a register/unregister pair was written but never wired to
any real teardown path.

## Structured inventory

Full data: `docs/audits/unreachable_code_inventory.json` / `.csv` (428 rows: 362 real candidates +
66 excluded, one row per definition, with `tier`, `kind`, `class`, `name`, `file`, `line`,
`decorators`, `exclusion`, `has_test_coverage` columns).

**Cluster/singleton split**: 263 of the 362 real candidates fall into a same-file cluster of 2+
(79 files); 99 are singletons (the only real candidate in their own file). The four clusters above
were selected for deep writeup because they were independently, individually verified beyond the
automated tool output (direct import greps, comment-vs-import distinction, sibling-method
comparison) — not because they are necessarily the largest by raw count. The remaining 75 file
clusters and 99 singletons are real per this audit's own methodology (same zero-occurrence
criterion, same false-positive exclusions applied) but have **not** individually received this
depth of manual verification — recorded in the structured data with full location detail so a
future pass (this audit's own, or a fresh run of the committed tool) can pick any of them up with a
precise starting point, rather than re-deriving the candidate list from scratch.

## Limitations, stated plainly (per this ticket's own AC)

- **Cannot detect dynamic dispatch** via computed attribute names (`getattr(obj, some_variable)`
  where the string is not a literal) or registry/plugin lookup by a string that doesn't match the
  method's own identifier text elsewhere in the corpus.
- **Cannot distinguish same-named methods on different classes** — a zero-hit result is still a
  strong signal (the literal text appears nowhere else in ~2470 files, regardless of what class it
  would belong to if it did), but a non-zero hit for a generic name is not proof the *specific*
  class's method is what's being called. Demonstrated concretely: `BiologicalSystem.update()` and
  `CacheStrategy.get/put/invalidate()` are confirmed-dead but invisible to this tool.
- **`tools/` is currently grouped with `tests/`** (not counted as "live production" for the
  reachability verdict) — a real script under `tools/` that calls something is, in practice, a
  legitimate entry point, not a test. Spot-checked for the clusters covered by deep writeup above
  (no material effect on those specific findings), but not corrected repo-wide; a future revision of
  the tool should split `tools/` into its own bucket.
- **No cross-language / frontend detection** — a Python function referenced only from
  `frontend/src/` (e.g. via an API route already excluded above) would not be separately verified
  by this pass.
