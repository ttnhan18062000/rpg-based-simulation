---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE
artifact_type: investigation
tags: [engine, bug, websocket]
---

# Investigation — TCK-20260825-FORCE-FULL-SCAN-DEAD-CODE

## Context-Scan Gap (report before findings)

This worktree has no `graphify-out/` directory and no built knowledge-search index
(`mcp__knowledge-search__search_docs` returned `{"error": "index not found", "action": "run make
knowledge-index"}`; `graphify query` returned `error: graph file not found:
.../graphify-out/graph.json`; the `tools/knowledge_search.py` fallback returned `knowledge index
not found — run make knowledge-index`). This is a worktree-provisioning gap, not a decision to
skip the mandatory Step 1/Step 2 calls — both were attempted first, per CLAUDE.md's hard rule, and
both errored out before any grep was run. Investigation proceeded via the documented fallback
(`tickets/`, `docs/`, `docs/REGISTRY.yaml`, `docs/parity_ledger/`, direct source reads) per Context
Scan step 4. This gap should be flagged to the user/orchestrator independently of this ticket's own
scope — it blocks the mandatory tools for every ticket worked in this worktree, not just this one.

## Current Behavior

### `AuthoritativeApplyPipeline.refine()` — `src/engine/pipeline.py:41-361`

- Lines 48-51: `force_full_scan` (the `refine()` kwarg, defaulting `False`) and
  `state._force_full_scan` (set on `AuthoritativeState` by `Kernel.__init__`/`Kernel.state` —
  `src/engine/kernel.py:91,741,1233`, `src/engine/apply.py:410`) both set `update.force_full_scan =
  True` on the `StateUpdate` that flows through the rest of `refine()`.
- Lines 56-59: a `DirtySetBuilder` is constructed from `update.dirty_set` (usually `None` on the raw
  incoming update from `Kernel._phase_resolution`); `mark_from_update` seeds it if `dirty_set is
  None`.
- Five more `dirty_builder.mark_from_update(state, update)` + `.build()` calls thread through
  `refine()` at lines 261-263, 296-297, 314-315, 329-330, and 352-353 (the last one, "Final dirty
  set for result application", is the one whose output becomes `refine()`'s returned
  `StateUpdate.dirty_set`).
- `_refresh_dirty_set` (lines 362-388) is a `@staticmethod` with the docstring "Hardening Phase:
  Ensure DirtySet is always current" / "Phase 17 Law: If force_full_scan is True, the dirty set
  must include ALL entities." **It is not called anywhere in `refine()`, nor anywhere else in the
  repo.** Confirmed by `grep -rn "_refresh_dirty_set" --include="*.py" .` from the repo root: the
  only hit is its own `def` line (`pipeline.py:363`); the sole other reference anywhere in the
  repository is a comment in `tools/perf/live_map_ws_payload_measure.py:32-33`, itself documenting
  the same zero-call-sites finding from the origin ticket. This matches the ticket's own claim and
  needs no re-litigation.

### `Kernel` — `src/engine/kernel.py`

- `Kernel.__init__` (line 84): `self._force_full_scan = flags.get("force_full_scan", False) if
  flags else False` — a boot-time-fixed flag, never mutated per tick.
- Line 91 and line 741 (`_phase_advancement`) and line 1233 (`state` property getter):
  `object.__setattr__(self._state, "_force_full_scan", self._force_full_scan)` — mirrors the
  boot flag onto the (frozen) `AuthoritativeState._force_full_scan` field
  (`src/core/state.py:1146`, `compare=False, repr=False`, so it never affects the state hash).
- `_phase_resolution` (line 648-653) calls `AuthoritativeApplyPipeline.refine(..., cadence=...,
  force_full_scan=self._force_full_scan)` every tick, unconditionally passing the boot flag.
- `_run_hard_law_checks(dirty_set)` (lines 834-847), called from `_phase_advancement` with
  `update.dirty_set` (the `refine()`-produced final dirty set): **only if `ObservabilityConfig
  .get_mode() != ObservabilityMode.OFF`** does it set `self._status.dirty_set = dirty_set`
  (line 843-844) — this is the exact attribute `V2EngineManager._update_latest_state` reads
  (`engine_manager.py:155`). Default mode is `ObservabilityMode.LIGHT`
  (`src/observability/config.py:296-310`, `get_mode()`'s final fallback), not `OFF`, so in the
  default/production configuration this attribute genuinely IS populated every tick — the ticket's
  central claim ("no live mechanism can make the WS-bound DirtySet full") holds under the default
  config, not only in some edge-case observability setting. Worth flagging: if a caller explicitly
  sets `SIM_OBS_MODE=OFF`/`RPG_OBS_MODE=OFF`, `self._status.dirty_set` is **never assigned**, so
  `getattr(self._kernel.status, "dirty_set", None)` in `engine_manager.py:155` returns `None`,
  which `ReadModelInvalidationPolicy.get_dirty_entity_ids` treats as "invalidate everything"
  (`read_model_cache.py:26-28`) — i.e., under `OBS_MODE=OFF` the WS delta is *already* effectively
  full-scan today, for a reason unrelated to `force_full_scan` at all. Not in scope to change, but
  the regression test added by this ticket must pin observability mode explicitly (not rely on the
  ambient default) so it actually exercises the `force_full_scan` path rather than accidentally
  passing via the `dirty_set is None` fallback.
- `RuntimeStatus` (`src/engine/runtime_status.py`) has **no declared `force_full_scan` field**.
  `V2EngineManager._update_latest_state`'s `getattr(self._kernel.status, "force_full_scan", False)`
  (`engine_manager.py:156`) always returns the `False` default today, confirmed by reading
  `RuntimeStatus`'s full dataclass field list (lines 18-33: `current_mode`, `mode_dwell_ticks`,
  `signal_history`, `total_dropped_work`, `dropped_work_delta`, `last_transition_tick`,
  `max_mode_reached` — no `force_full_scan`, no `dirty_set` either, despite `dirty_set` being read
  the same way one line above). `RuntimeStatus` is a **plain, non-frozen, non-slotted**
  `@dataclass` (unlike `Kernel`, which uses `__slots__`), and `Kernel` already bolts several
  undeclared attributes onto `self._status` at runtime as an established pattern: `dirty_set`
  (kernel.py:843-844), `current_tick_violations` (850), `cumulative_violations` (854-855, 863),
  `hard_law_violations` (856-857, 859), `last_hard_law_violation_tick` (860, 775),
  `previous_mode` (554). None of these six are declared `RuntimeStatus` fields either — this is a
  repeated, pre-existing pattern in this exact class, not something introduced by this ticket.

### `src/core/dirty.py` — the incremental-marking mechanism

- `get_relevant_entity_ids(state, update, domain)` (14-39) and `CandidateSelector.entities(state,
  update, domains, ...)` (460-506) — the two entry points pipeline phases use for candidate
  selection — **both check `update.force_full_scan` (or `update.dirty_set is None`) FIRST**, before
  ever consulting `update.dirty_set`'s contents (lines 20, 474). When `force_full_scan=True`, both
  return every entity in `state.entities` directly, bypassing the `DirtySet` entirely for routing
  purposes. This means `force_full_scan`'s phase-widening effect is **structurally independent** of
  whatever `update.dirty_set` currently contains — the dirty set's content plays no role in whether
  a phase sees all entities.
- `DirtySetBuilder.mark_from_update(state, update)` (112-180) only adds an entity ID to any of its
  domain sets when that entity has a **real, non-empty field on its `EntityUpdate`** this tick
  (`e_upd.new_position`, `e_upd.combat`, `e_upd.inventory`, etc. — lines 144-180). It does not
  consult `force_full_scan` at all, and has no path that adds an entity ID merely because that
  entity was a routing *candidate* this tick.

**This is the crux finding.** `force_full_scan` widening phase-routing (via
`get_relevant_entity_ids`/`CandidateSelector`) does **not** imply that every widened-in entity
produces an `EntityUpdate` this tick — an entity can be fully evaluated by a phase and produce *no*
change (e.g., an idle NPC whose strategic re-evaluation concludes "keep doing the same thing," which
under the strategic domain's `is_noop()` contract produces nothing worth compacting in). Only
entities that genuinely mutated get marked into `dirty_builder`'s sets. So **`mark_from_update` does
NOT naturally produce a full `DirtySet` as a side effect of `force_full_scan` widening routing** —
the origin ticket's own "Root-cause hypothesis" (`stored_artifacts/TCK-20260821-LIVE-MAP-PERF-
VALIDATION/report.md` lines 201-204: "`_refresh_dirty_set`... its logic was superseded by the
incremental `DirtySetBuilder.mark_from_update` calls") is **not supported by the code** and this
investigation contradicts it with the evidence above. `_refresh_dirty_set`'s full-scan branch is
**not redundant** — it is the only code in the repository that would force the *downstream*,
post-`refine()` `DirtySet` (the one `Kernel._run_hard_law_checks` copies onto `self._status
.dirty_set`, and that `V2EngineManager._update_latest_state`/`ReadModelCache.compute_tick_delta`
consume) to actually contain every entity, independent of what individually mutated that tick.

### `_refresh_dirty_set`'s two branches are NOT equally safe to wire in

`_refresh_dirty_set` (pipeline.py:362-388) has two branches:

1. **`if update.force_full_scan:`** (372-385) — builds a fresh `DirtySet` with all nine
   entity-domain sets (`movement_entities` through `attribute_entities`, plus `town_entities=
   state.town_entity_ids`) set to `set(state.entities.keys())`. This branch is the genuinely useful
   "Phase 17 Law" logic and is **not redundant** with anything else in the pipeline (see above).
2. **`else:`** (387-388) — `DirtySet.from_update(state, update, base_dirty=update.dirty_set)`. This
   recomputes the dirty set from scratch via the **stateless** `DirtySet.from_update` path rather
   than reusing the already-correct, already-computed `dirty_builder`-based final dirty set from
   `refine()`'s own line 352-353. Per `docs/core/dirty_state_and_dependency.md`'s own "Edge cases"
   section ("`e_upd.task` discrepancy — known risk", lines 164-180): `DirtySetBuilder
   .mark_from_update()` treats `e_upd.task` as a `strategic`-dirty trigger (dirty.py:162:
   `if e_upd.strategic or e_upd.task or e_upd.interaction or e_upd.quest:`), but `DirtySet
   .from_update()` **omits `e_upd.task` from the same check** (dirty.py:329: `if e_upd.strategic or
   e_upd.interaction or e_upd.quest:` — no `e_upd.task`). The doc explicitly says: "Callers that use
   `DirtySet.from_update()` directly ... will not mark an entity `strategic`-dirty when only `task`
   changes... Do not fix it in this ticket — raise a dedicated bugfix ticket if task-only changes
   are observed to slip through strategic routing."

   **Consequence for this ticket**: if `_refresh_dirty_set` were wired in verbatim and
   unconditionally (e.g., `update = AuthoritativeApplyPipeline._refresh_dirty_set(state, update)`
   appended after line 353, called on every tick regardless of `force_full_scan`), every ordinary
   (non-force-full-scan) tick would have its correctly-computed, builder-based final dirty set
   silently **replaced** by a `from_update()`-derived one — reintroducing the documented `e_upd.task`
   discrepancy into the live, default pipeline path for every tick, not just force-full-scan ones.
   This would be a real regression, not a neutral no-op, and the dirty_state_and_dependency.md doc
   explicitly warns against conflating this fix with that pre-existing, deliberately-deferred
   inconsistency.

## Recommended Fix Direction: **wire in, but narrowly** — not verbatim, not removal

The ticket's own open question ("wired back in... or genuinely superseded... removed instead") is a
false dichotomy given the evidence: the full-scan branch is real, needed, non-redundant logic that
must be wired in; the non-full-scan branch is unsafe dead weight that must **not** be wired in as-is.
The correct fix is a **third option**: extract only the full-scan branch's logic into `refine()`,
gated on `update.force_full_scan`, and delete `_refresh_dirty_set` as a standalone method (its
"Phase 17 Law" comment included) rather than calling it.

**Exact insertion point**: immediately after the existing "Final dirty set for result application"
block (pipeline.py:351-353 — `dirty_builder.mark_from_update(state, update)` /
`update = update.replace(dirty_set=dirty_builder.build())`), add a conditional block that, only when
`update.force_full_scan` is true, replaces `update.dirty_set` with the all-entities `DirtySet`
construction currently inside `_refresh_dirty_set`'s `if update.force_full_scan:` branch (lines
372-385, verbatim field-for-field). Do not touch `update.dirty_set` at all when `force_full_scan` is
false — the existing builder-based final dirty set is already correct for that case and must be left
alone.

This location is correct because:
- It runs **after** every phase in `refine()` has already executed with correct `force_full_scan`-
  driven candidate widening (verified: routing checks `update.force_full_scan` directly at each
  `CandidateSelector`/`get_relevant_entity_ids` call site, never through `update.dirty_set`'s
  content — see above). Overriding the dirty set only at the very end cannot change what any phase
  processed this tick.
- It runs **before** `return update.replace(sub_phase_costs=costs, metric_counters=final_metrics)`
  — the returned `StateUpdate` is exactly what `Kernel._phase_resolution` stores as
  `self._current_update` and later feeds to `_run_hard_law_checks(update.dirty_set)` /
  `ApplyPath.apply_generation()`.

**Determinism / state-hash risk: none identified.** `StateUpdate.dirty_set` is advisory routing
metadata, not part of `AuthoritativeState`; the fingerprint/hash machinery
(`CanonicalStateHasher.get_hash`, `StateFingerprinter`) operates over `AuthoritativeState` fields
(entities, world, etc.), not over `StateUpdate.dirty_set`. `tests/perf/test_dirty_parity.py
::test_dirty_set_vs_full_scan_parity` (already passing, unaffected by this fix) compares
`final_state_opt`/`final_state_ref` fingerprints — neither test ever inspects `dirty_set` content —
so widening the final dirty set for `force_full_scan=True` runs has no interaction with that test's
assertions. `AuthoritativeState.validate_dirty_set()`'s leak-detection (audit mode) treats a
too-broad `DirtySet` as safe by design (`dirty_state_and_dependency.md`: "false positives... are
safe"), so a full-entities override cannot trigger `DirtySetLeakError` — it can only ever mask a
genuine leak during a force-full-scan tick specifically (a minor, acceptable audit-blind-spot risk,
not a correctness risk; force_full_scan ticks are diagnostic/rare by design per
`optimization_invariants.md` §3's own framing — "Under chaos testing, diagnostic auditing, or
DEBUG_REFERENCE profiling").

**Performance cost: negligible.** For a 2500-entity world (the ticket's own CLASS_B reference
scale), the override does 9 set copies of `state.entities.keys()` (~2500 elements each, ~22,500 int
insertions total) — microseconds, not milliseconds, against a tick compute budget in the tens of
milliseconds (`Kernel._tick_once_inner`'s watchdog compares against `max(20.0, avg_ms * 2.0)`).
`force_full_scan` is not a hot-path/every-tick flag in production profiles (it is opt-in via
`Kernel(flags={"force_full_scan": True})`, used today only by `src/perf/profile_governance.py`'s
profiling harness and `tests/perf/test_dirty_parity.py`'s reference kernel) — even if it were on
every tick, this cost would not meaningfully move the needle relative to the ~17-phase pipeline's
own per-tick cost (phase costs already logged at `pipeline.py:356-357` in the hundreds of
microseconds-to-milliseconds range per phase group for 500+-entity worlds).

## The Second Gap: `RuntimeStatus`/`Kernel.status` surfacing

**Recommendation: add a declared `force_full_scan: bool = False` field to `RuntimeStatus`
(`src/engine/runtime_status.py`), populated once in `Kernel.__init__`** — e.g. immediately after
`self._status = status or DefaultStatus()` (kernel.py:109): `self._status.force_full_scan =
self._force_full_scan`. Rationale for this option over the two alternatives the ticket poses:

- **Why not "read `Kernel._force_full_scan` directly instead of through `.status`"**: `Kernel`
  uses `__slots__` (kernel.py:40-51) and does not expose `_force_full_scan` through any public
  property today (only `.status`, `.state`, `.run_id`, etc. are public). `V2EngineManager` already
  treats `.status` as the sanctioned read surface for kernel-internal signals (`dirty_set`,
  `dropped_work_delta`, `current_mode`, etc. all flow through `.status`, never through a private
  `_`-prefixed attribute read from outside `Kernel`) — reaching into `self._kernel._force_full_scan`
  from `V2EngineManager` would cross that established encapsulation boundary for no benefit over the
  `.status` route.
- **Why a declared field, not a dynamically-bolted one (matching the `dirty_set` precedent
  exactly)**: `RuntimeStatus` is a plain, non-frozen, non-slotted `@dataclass`, so a declared field
  costs nothing and is trivially backward-compatible (default `False`). Unlike `dirty_set` (which is
  genuinely per-tick and only meaningfully set when `_run_hard_law_checks` runs, i.e. conditionally
  on observability mode), `force_full_scan` is a **boot-time-fixed** value — it never changes across
  the life of a `Kernel`. Setting it once in `__init__`, unconditionally (not gated on observability
  mode the way `dirty_set` is), means `getattr(self._kernel.status, "force_full_scan", False)` works
  correctly in every observability mode, including `OFF` — closing exactly the gap
  `engine_manager.py:156` has today. A declared field is also self-documenting or at minimum
  greppable/type-checkable in a way the existing six ad-hoc `self._status.X = ...` attributes are
  not; it does not, however, retroactively fix those six existing violations of this same principle
  — that is out of scope for this ticket and not requested by it.
- Setting the field in `__init__` rather than per-tick avoids depending on `_run_hard_law_checks`'s
  observability-mode gate at all, so the fix is strictly simpler than mirroring `dirty_set`'s
  per-tick/mode-conditional assignment site.

## Docs Requiring Update

- `docs/core/dirty_state_and_dependency.md`: the "`force_full_scan` fallback" edge-case subsection
  (lines 186-188) currently states, as a general and still partly-true description: "The dirty set
  is still computed and attached — it is just not used for filtering." After this fix, that sentence
  becomes only true for `force_full_scan=False` ticks; for `force_full_scan=True` ticks the final
  attached dirty set is *replaced* with an all-entities set specifically so downstream consumers
  outside `refine()` (ReadModelCache, WS broadcast) see full coverage too. This section must be
  updated to describe both halves of the post-fix behavior (routing bypass — unchanged — vs. the new
  downstream-dirty-set forcing), and the "Regression tests" table (lines 237-243) should gain the new
  test(s) added by this ticket (see test_plan.md).
- `docs/performance/optimization_invariants.md`: OPT-INV-002 ("Force Full Scan Compliance", lines
  59-72) currently only asserts phase-routing/state-hash compliance ("Invariant Rules" 1-3, lines
  64-67) — nothing about the *downstream* `DirtySet` consumed by read-model/API/WS layers. This is a
  genuinely new guarantee this ticket introduces (the dirty set reaching consumers outside `refine()`
  is now also guaranteed complete under `force_full_scan`), not a rewording of an existing rule, so a
  new numbered invariant rule (or a 4th bullet under the existing "Invariant Rules" list) citing the
  new test from test_plan.md is required.
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-388`): the entry's `text` describes
  `ReadModelCache.compute_tick_delta` classifying `DirtySet.all_dirty_entities` into changed/removed,
  but never mentions `force_full_scan` at all — a real omission given `V2EngineManager
  ._update_latest_state` explicitly threads a `force_full` value into `compute_tick_delta`
  (`engine_manager.py:159-161`) that, before this fix, is always `False`. `v2_evidence` and
  `test_path` need the new regression test(s) appended once written (see test_plan.md), and `text`
  needs a clause describing that `force_full_scan=True` now genuinely produces an all-entities
  `changed` list end-to-end. `status: verified` can remain `verified` post-fix (it was already
  "verified" for the non-force-full-scan path, which this fix does not change); it should not be
  marked `divergent` retroactively for a gap this ticket is closing in the same session.

The `docs/engine/candidate_selection.md` doc (path: `docs/engine/candidate_selection.md`, under
`docs/engine/`) is not required to change for this ticket: Tier 2's "Stage 4: Force-full-scan
bypass" description already accurately describes routing behavior only (it delegates the detailed
force_full_scan fallback description to `dirty_state_and_dependency.md` via a cross-reference,
line 46), and this fix does not change routing/candidate-selection behavior at all — only the final,
post-routing `DirtySet` that downstream (non-pipeline) consumers read. No sentence in this doc
becomes inaccurate.

The `docs/core/update_intents.md` doc (path: `docs/core/update_intents.md`) is not required to
change: its one `force_full_scan` mention (lines 179-181, "Edge cases — `force_full_scan` and
dirty-set bypass") already correctly and narrowly states "`force_full_scan` only affects routing,
not application" — a claim about `ApplyPath.apply_generation()` application behavior, which this fix
does not touch (the fix only changes what `StateUpdate.dirty_set` contains when `refine()` returns,
not how updates are applied).

## Parity Ledger Overlap

- `INFRA-388` (`docs/parity_ledger/infrastructure.yaml`, status `verified`, priority `P1`) — the
  entry this ticket must update (see Docs Requiring Update above). Not `P0`, so a passing
  `test_path` is a strong expectation but not a hard `done-checker` gate the way a `P0` entry would
  be; this ticket should still add real, passing test coverage regardless.
- No other parity ledger entry was found referencing `force_full_scan`, `_refresh_dirty_set`, or
  `DirtySetBuilder` by name (checked via direct `grep` across `docs/parity_ledger/*.yaml` for these
  terms; only `infrastructure.yaml`'s `INFRA-388` and its own text matched, plus the general
  dirty-tracking mentions already covered by `PERF-005`–`PERF-008` Logic IDs cited in
  `dirty_state_and_dependency.md`, which are not tracked in the parity ledger as separate IDs — they
  are Logic IDs referenced from source comments, a different tracking mechanism from the parity
  ledger's `id:` entries).

## Prior Work

- `stored_artifacts/TCK-20260821-LIVE-MAP-PERF-VALIDATION/report.md` (AC4 Finding 1, lines 180-211)
  — the origin finding. Its "Root-cause hypothesis" (lines 201-204, "`_refresh_dirty_set`... its
  logic was superseded by the incremental `DirtySetBuilder.mark_from_update` calls") is **contested
  by this investigation** with concrete evidence (see "This is the crux finding" above) — it is not
  superseded; the full-scan branch is genuinely non-redundant.
- `stored_artifacts/TCK-20260821-LIVE-MAP-PERF-VALIDATION/plan.md` (Deviations section) and
  `tools/perf/live_map_ws_payload_measure.py` (lines 27-59, "Full-scan finding" docstring) — the
  synthetic-estimate workaround that ticket used in place of a live capture, exactly because this gap
  existed. Once this ticket's fix lands, that harness's `full_scan` bucket could, as a future
  improvement (out of scope here — this ticket's own Out of Scope explicitly excludes touching that
  ticket's deliverables), be replaced with a genuine `force_full_scan=True`-booted live capture; not
  proposed as part of this ticket.
- `docs/REGISTRY.yaml` was consulted for related closed tickets tagged `engine`/`websocket`/
  `performance` overlapping `src/engine/pipeline.py`, `src/api/read_model_cache.py`,
  `src/api/engine_manager.py`; `TCK-20260821-WS-ENTITY-DELTA-BROADCAST` (introduced
  `compute_tick_delta`/`INFRA-388`) and `TCK-20260821-DELTA-ENVELOPE-SPATIAL-FIELD` (added
  `region_id`) are the two most relevant, both already reflected in the current `INFRA-388` text
  read above — no additional undiscovered prior-work pattern beyond what the ticket's own "Related
  Stored Artifacts" pointer already surfaced.

## Risks and Open Questions

- **Observability-mode dependency of `dirty_set` on `.status`** (see "Current Behavior" above):
  `self._status.dirty_set` is only ever assigned inside `_run_hard_law_checks`, gated on
  `ObservabilityConfig.get_mode() != OFF`. This ticket's fix does not change that gating — it only
  fixes what `dirty_set` *contains* once assigned, and separately fixes `force_full_scan` surfacing
  (via a `RuntimeStatus` field set once at `__init__`, independent of that gate). Not a blocking
  question, but the new regression test **must** either rely on the default `LIGHT` mode (not
  explicitly force `OFF`) or explicitly assert the mode it runs under, to avoid accidentally testing
  the `dirty_set is None` fallback path instead of the real `force_full_scan` fix.
- **Repo-wide check for other `force_full_scan` consumers** (ticket's own open question): confirmed
  via `grep -rn "force_full_scan" src/` that consumers beyond the WS broadcast path exist:
  `src/engine/phase_graph.py:87` (`PhaseDependencyGraph.should_run_phase`'s "Full scan overrides"
  check — forces every phase to run), `src/engine/candidate_selector.py:113`
  (`MovementCandidateSelector`'s "Stage 4: Force-full-scan bypass"), `src/systems/strategic_systems
  /work_queue.py:36`, `src/core/dirty.py` (`get_relevant_entity_ids`, `get_relevant_group_ids`,
  `CandidateSelector.entities`), `src/core/updates.py:920,951` (`StateUpdate.force_full_scan` field
  and its role in `StateUpdate.is_noop()`), `src/perf/long_run_harness.py:152`. **All of these read
  `update.force_full_scan` or `state._force_full_scan` directly — none of them read the `DirtySet`'s
  contents to decide whether force-full-scan is active.** This confirms the fix (only touching the
  final `dirty_set` value, not `update.force_full_scan` itself) cannot regress any of these other
  consumers — they are unaffected by what this ticket changes. `ReadModelCache.get_entities_paged`
  (the ticket's specifically-named example) does **not** read `dirty_set` or `force_full_scan` at
  all (`read_model_cache.py:176-194` — pages directly over `state.entities`, unconditionally) — it is
  unaffected either way, confirmed by reading its full body.
- **No open question blocks implementation.** The insertion point, the exact logic to relocate, the
  `RuntimeStatus` fix, and the doc/parity-ledger updates are all concretely determined by the
  evidence above.

## Anti-Drift Hazards

- **Do not call `_refresh_dirty_set` verbatim/unconditionally as "the fix."** As shown above, this
  would silently reintroduce the `e_upd.task` strategic-dirty discrepancy into every ordinary tick,
  not just force-full-scan ones — a real regression, not a neutral wiring-in. The fix must extract
  only the `if update.force_full_scan:` branch and gate it explicitly; the method itself should be
  deleted, not called.
- **Do not touch `DirtySetBuilder.mark_from_update` or `DirtySet.from_update`** to "fix" the
  `e_upd.task` discrepancy as a side effect of this ticket — `dirty_state_and_dependency.md`
  explicitly defers that to its own dedicated bugfix ticket; conflating it here would be scope creep
  beyond this ticket's stated Scope/Out of Scope.
- **Do not widen this ticket into building a new full-scan-cadence feature** (e.g., an automatic
  periodic full re-sync) — explicitly excluded by the ticket's own Out of Scope, and nothing in this
  investigation's findings implies such a feature is needed; the existing, already-documented
  `force_full_scan` mechanism just needs its downstream half wired up.
- **Do not change `docs/engine/candidate_selection.md` or `docs/core/update_intents.md`** — both
  were checked and found accurate as-is post-fix (see "Docs Requiring Update," Format 2 entries
  above); editing them anyway would be an unjustified drift.
- **Do not retroactively "clean up" the other five ad-hoc `self._status.X = ...` assignments**
  (`current_tick_violations`, `cumulative_violations`, `hard_law_violations`,
  `last_hard_law_violation_tick`, `previous_mode`) while touching `RuntimeStatus` for
  `force_full_scan` — out of scope, and each has its own established call sites/tests that a
  blanket refactor could destabilize without its own dedicated investigation.
- **Watch the `AuthoritativeState._force_full_scan` vs. `StateUpdate.force_full_scan` naming
  overlap** — they are two different fields on two different objects (state.py:1146 vs.
  updates.py:920) reconciled only inside `refine()`'s lines 48-51. Any new test or doc edit should
  be precise about which one it means; conflating them in prose would be a comprehension hazard for
  the next reader even though the code itself keeps them correctly separate.
