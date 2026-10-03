---
status: historical
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP
artifact_type: investigation
tags: [simulation-quality, calibration, determinism]
---

# Investigation — TCK-20260715-SIMQ-ANCHOR-LOAD-SENSITIVITY-SWEEP

## Current Behavior

### The 14 anchors, their tier, and the confirmed second-run split

Cross-referencing the ticket's 14-anchor list against `tests/simulation_quality/test_grade_regression.py`'s
`FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` (lines 54-152) and the standalone probe tests:

| Anchor | Drifted pillar(s) | Tier / test | 2nd (isolated) run result |
|---|---|---|---|
| `simq_routing_test_seed42_500t` | COGNITION | FAST (`test_grade_within_anchor_band`) | **FAIL** |
| `simq_routing_test_seed42_1000t` | COGNITION | SLOW (`test_grade_within_anchor_band_long_run`, `@pytest.mark.slow`) | **FAIL** |
| `hero_guild_routing_seed42_1000t` | COGNITION | SLOW | **FAIL** |
| `unit_selfmodel_pilot_seed42_1000t` | COGNITION | SLOW | **FAIL** |
| `urban_political_seed42_200t` | SOCIAL | FAST | pass |
| `urban_political_seed42_1000t` | SOCIAL | SLOW | **FAIL** |
| `urban_political_seed123_1000t` | ECONOMY, SOCIAL | SLOW | **FAIL** |
| `frontier_extended_seed42_200t` | NARRATIVE | FAST | pass |
| `frontier_extended_seed123_200t` | COMBAT, PROGRESSION, NARRATIVE | FAST | pass |
| `frontier_living_world_seed42_200t` | SOCIAL | FAST | pass |
| `frontier_living_world_seed123_200t` | COMBAT, NARRATIVE | FAST | pass |
| `urban_political_selfmodel_probe_seed42_200t` | SOCIAL | standalone (`test_urban_political_selfmodel_cognition_isolated_grade_anchor`, `test_grade_regression.py:334-378`, no `slow` marker, not in `FAST_ANCHOR_KEYS`) | **FAIL** |
| `frontier_marches_seed42_200t` | NARRATIVE | FAST | pass |
| `generated_frontier_3_42_seed123_200t` | COMBAT | FAST | **FAIL** |

**Structural finding not yet stated in the ticket text**: all 5 `SLOW_ANCHOR_KEYS` (1000t)
entries in this list failed in *both* runs (the original sustained sweep and the isolated
per-scenario re-run) — 100% consistency at the 1000t tier. Of the 9 `FAST`/standalone 200t
entries, 6 passed cleanly on isolated re-run and 3 did not
(`simq_routing_test_seed42_500t` is 500t, not 200t — also failed both times).
This is consistent with, but does not yet prove, F6's documented tick-300-320 onset
threshold (`docs/audits/D06_longrun_health.md` §F6): 1000t/500t anchors have far more
tick-runway past the onset threshold than 200t anchors, so higher/consistent failure
there is the expected shape *if* F6 is the mechanism. The three 200t exceptions
(`generated_frontier_3_42_seed123_200t`, `urban_political_selfmodel_probe_seed42_200t`,
and — inconsistently — one of the two `frontier_extended`/`frontier_living_world` 200t
pairs did NOT fail, only their *sibling* anchors in the same world did) are the concrete
evidence this ticket's repro work needs to explain: either F6 can also manifest at 200t
under sufficiently sustained multi-scenario session load (contradicting the "~300-320
onset" framing as an absolute floor, not just a typical one), or these 3 have a distinct,
non-F6 cause and must not be silently folded into an F6 narrative.

### Watchdog / throttle mechanism (read-only reference, current line numbers)

`src/engine/kernel.py::Kernel.tick_once()` (starts line 332) runs two independent
wall-clock-gated degradation paths, unchanged since the prior tickets' investigations
(line numbers have drifted slightly from the previously-cited 420-442/574-601 due to
unrelated commits since; confirmed logic is byte-identical in substance):

- **End-of-tick watchdog** (`kernel.py:415-437`, warning fires at line 424): after all
  phases complete, if `not self._audit_mode and self._state.tick > 5` and
  `self._final_compute_ms > min(hard_cap, limit_ms)` (where `limit_ms = max(20.0,
  avg_ms * 2.0)`), logs `"Tick {N} exceeded budget..."`, calls
  `self._status.record_dropped_work(9999)`, and routes a `watchdog_trip` alert. Does
  **not** roll back or drop any of the current tick's already-applied work — it is a
  post-hoc signal/counter increment for *this* tick, feeding the running average that
  gates *future* ticks' `limit_ms`.
- **Mid-tick emergency throttle** (`_phase_resolution`, `kernel.py:564-602`, warning at
  line 581): iterates `self._final_results` in fixed, deterministic sort order
  (`(class_priority, -local_priority, entity_id)`, line 570) and every 10th item checks
  `elapsed = (time.perf_counter_ns() - self._start_perf_ts) / 1e6` against
  `self._profile.max_tick_budget_ms`. If exceeded, it **drops the remaining
  resolution-queue items for that tick outright** (`break`, no further entities
  processed this tick), forces `RuntimeMode.DEGRADED` via `self._governor.force_mode`,
  and routes a `watchdog_trip` alert. This is the mechanism that actually removes
  entity behavior for a tick, not just a compute-time signal.

Both paths are gated `not self._audit_mode` — `audit_mode=True` runs disable both and
are documented as measuring a materially different, unrealistically optimistic scenario
(confirmed unchanged from prior investigations' findings). `tools/calibrate_simq.py`'s
`_run_engine` never sets `audit_mode` (confirmed by direct read, matches prior tickets'
finding) — every calibration run, including this ticket's repro work, exercises the real
throttled path.

### `decision_divergence_detected`'s missing dedup gate — confirmed still the only
### event type in this shape

`src/observability/event_extractor.py:477-496` (COGNITION-only): fires per-entity-per-tick
whenever `entity.strategic.concerns`'s top concern is `danger` with `urgency > 0.7` **and**
`current_project_id`'s kind is in `_NON_SURVIVAL_PROJECT_KINDS`. This condition is
re-evaluated fresh from live entity state every tick with **no "already-emitted" gating
set** (contrast `_emitted_stale_leads`, `_emitted_social_memory`,
`_emitted_contract_milestones` — all present, all gated). If the mismatch persists across
N ticks because the mid-tick throttle keeps dropping that entity's resolution work before
it can resolve the danger concern, this event refires N times. This exact mechanism was
independently confirmed real by `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM`'s
controlled repro, but that repro also found `urban_political_seed123_500t` specifically
does **not** exercise this mechanism (bit-identical across idle/2x/4x load) — it is real,
but anchor-specific whether any given scenario/seed actually drives an entity into the
`danger`+non-survival-project state at all.

### The SOCIAL/COMBAT/PROGRESSION/NARRATIVE (16 non-COGNITION) event paths do **not**
### share `decision_divergence_detected`'s exact mechanism — this is the ticket's own
### flagged open question, and the investigation resolves it partially

Read all `EVENT_TYPES` for the 4 affected scorers and traced each back to its
`event_extractor.py` construction site:

- `SocialScorer.EVENT_TYPES` (`scorers/social.py:19-31`): `cooperation_event`,
  `group_joined`/`group_expelled`, `contract_offer_created`/`_accepted`/`_completed`/
  `_lapsed`/`_expired_offer`, `reputation_delta`, `social_memory_created`.
- `CombatScorer.EVENT_TYPES` (`scorers/combat.py:16-24`): `combat_initiated`,
  `combat_resolved`, `combat_damage`, `entity_killed`, `near_death_survival`,
  `combat_hard_law_violation`, `attrition_threshold_crossed`.
- `ProgressionScorer.EVENT_TYPES` (`scorers/progression.py:16-25`): `xp_granted`,
  `level_up`, `skill_unlocked`, `trait_expressed`, `pillar_trait_unlocked`,
  `progression_conversion_applied`, `near_death_survival`,
  `progression_plateau_detected`.
- `NarrativeScorer.EVENT_TYPES` (`scorers/narrative.py:22-33`): `quest_started/_completed/
  _failed`, `chronicle_entry_created`, `world_emergence_event`, `narrative_milestone`,
  `scenario_objective_progressed/_completed`, `scenario_stalled`, `hero_death_unrecorded`.

Every one of these that is constructed in `event_extractor.py` (`reputation_delta`,
`group_joined`/`_expelled`, `cooperation_event`, `social_memory_created`,
`contract_offer_created`/etc., `progression_plateau_detected`, `skill_unlocked`,
`xp_granted`, `level_up`, `hero_death_unrecorded`, `narrative_milestone`) is a **state
transition/delta event** — gated on `prior_state` vs. `state` comparison for that
specific tick (e.g. `curr_group != prior_group`, `abs(delta) > 0.05`,
`curr_status != prior_status`), or a "did X happen this tick" flag check (e.g.
`prop.get("last_cooperation_decision") is not None`). None of these re-evaluate a
*persisting condition* every tick the way `decision_divergence_detected` does — they
fire once, at the tick the underlying state actually changed, not once per tick the
changed state remains true. `social_memory_created` (line 538) and the contract
milestone family (line 643) are additionally dedup-gated by explicit `_emitted_*` sets,
same as the already-audited COGNITION-adjacent paths.

`combat_damage` and `entity_killed` are **not constructed in `event_extractor.py` at
all** — `combat_damage` is `SimulationEvent`'s own Pydantic field default
(`src/observability/events.py:84`), meaning these two event types originate from a
different emission path (combat resolution phase, not the tick-boundary diff-based
extractor). This was not traced further in this investigation (out of the ticket's
Related Code Areas, which names only `event_extractor.py`) — **flagged as a gap**: if
`generated_frontier_3_42_seed123_200t`'s COMBAT drift or
`frontier_extended_seed123_200t`'s COMBAT drift trace to `combat_damage`/`entity_killed`
specifically, the repro work needs to locate and read that emission path before it can
conclude anything about mechanism, since it is architecturally distinct from
`decision_divergence_detected`.

**Conclusion on the open question**: the "same-class-but-distinct no-dedup-gate event
type per pillar" hypothesis in the ticket's Assumptions section does **not** hold for
the delta-based SOCIAL/PROGRESSION/NARRATIVE events audited here — they structurally
cannot refire every tick the way `decision_divergence_detected` does, because they are
gated on a transition, not a persisting condition. If F6 is nonetheless implicated for
these anchors, the mechanism must instead be: **the mid-tick throttle drops a resolution
item outright on tick T, so the transition that would have fired the delta event on tick
T either fires on a later tick (T+k, whenever that entity's resolution work is next
processed without being dropped) or never fires that run at all** — a "which tick the
delta lands on, or whether it lands at all" sensitivity, not a "same event refires many
extra times" sensitivity. This is a different failure shape than COGNITION's, consistent
with the ticket's own instruction not to force-fit F6's exact `decision_divergence_detected`
signature onto other pillars, but is still the *same underlying throttle mechanism*
(dropped resolution-queue items) as documented root cause. `combat_damage`/`entity_killed`'s
separate emission path (not audited here) is the concrete residual unknown.

### `tools/calibrate_simq.py` / `tools/evaluate_simq.py` — repro harness confirmed unchanged

`tools/calibrate_simq.py`: `_resolve_profile` (line 32), `_load_profile_feature_flags`
(line 44), `_run_engine` (drives the real `Kernel`, no `audit_mode`), `_build_hub`,
`_replay_jsonl_through_hub` — same internals `TCK-20260713-SIMQ-COGNITION-LOOPDET-
NONDETERMINISM`'s `repro_sweep.md` used and this ticket's Scope explicitly directs reuse
of. `--output` supports redirecting a trial's report to a non-canonical path (confirmed
present, matches `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`'s Anti-Drift Hazard about
not clobbering trial data before comparison).

## Mechanics / Engine Constraints

- `docs/engine/kernel.md` §"Emergency Throttling" (lines 66-70): documents the two-step
  DEGRADED-transition + dropped-resolution-queue-work + logged-warning behavior. Current
  source (`kernel.py:415-437`, `564-602`) matches the doc's description exactly — no
  drift found.
- `docs/engine/performance_contract.md` §7 "Adaptive Phase Budget Governor" (lines
  65-77): documents the broader `PhaseBudgetGovernor` this watchdog/throttle pair is one
  instrument of — corpus-wide, intentional, load-adaptive degradation, not a bug.
- Per the ticket's Out of Scope and the two precedent tickets' Anti-Drift Hazards: this
  mechanism is not to be changed by this ticket under any circumstance. It is the
  measured object, not a target.
- No Mechanics Bible chapter governs SimQ scoring-tool correctness (confirmed, same
  finding as both precedent investigations) — this remains a tooling-reliability
  concern, not a simulation-law concern.

## Parity Ledger Overlap

- **`docs/parity_ledger/infrastructure.yaml::INFRA-272`** (P1, `verified`) — the entry
  that directly names this ticket. Its `text` states the 14-anchor list is
  "intentionally left un-reconciled" pending this ticket's own investigation, and its
  `test_path` explicitly carves out `test_grade_within_anchor_band` /
  `test_grade_within_anchor_band_long_run` parametrized cases for these 14 keys as a
  "known, tracked exception... not expected to pass until that ticket closes." **This
  entry's `status`/`v2_evidence`/`test_path` will need updating once this ticket
  produces a guard for each of the 14 anchors** — specifically, once
  `test_grade_regression.py -v` is fully green again (per this ticket's AC #4), INFRA-272's
  "up to 14 known, separately-tracked failures" caveat becomes stale and should either be
  updated to reference the closed state or a new entry should record the closure. This is
  the primary parity update this ticket owns.
- **`docs/parity_ledger/infrastructure.yaml::INFRA-271`** (P1, `verified`) — the
  underlying pillar-scoped weight-lookup fix. Not directly touched by this ticket (Out of
  Scope explicitly excludes any `weights.py`/`scoring_weights.yaml` change), but
  INFRA-271's `test_path` should remain valid and green throughout — worth a sanity
  check at Implement time that nothing in this ticket's guard additions accidentally
  regresses it.
- No parity entry documents F6's precise per-pillar blast radius beyond COGNITION
  (`decision_divergence_detected`) — this ticket is the first to investigate whether F6
  extends to SOCIAL/COMBAT/PROGRESSION/NARRATIVE, and if confirmed, a **new** parity
  entry (or an extension of the existing F6-adjacent entries, none of which currently
  exist as a dedicated `INFRA-*` entry for F6 itself — confirmed via search, F6 lives
  only in `docs/audits/D06_longrun_health.md`, not the parity ledger) may be warranted at
  Implement/Finalize time. Flag for the planner: whether to originate a new `INFRA-*`
  entry for "F6 confirmed to extend beyond COGNITION to N additional pillars" if the
  repro confirms this.

## Prior Work

- `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM` (done) — established the F6
  root-cause finding for COGNITION specifically, the repro methodology
  (`repro_sweep.md`: idle repeats + escalating `multiprocessing`-busy-loop induced load,
  measured via `budget_warnings`/`watchdog_trips` log-line counts), and the
  bit-identical-vs-tolerance-guard decision fork. **Important nuance this ticket must not
  lose**: that ticket's repro found `urban_political_seed123_500t` (a *different* anchor
  from any of this ticket's 14) does NOT exercise F6's mechanism despite genuine throttle
  activity — proving throttle activity alone does not imply score instability for every
  anchor. Do not assume any of this ticket's 14 anchors are F6-affected without an
  anchor-specific repro; the precedent ticket is proof that assumption can be wrong.
- `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY` (done) — original tolerance-guard
  precedent (grade-band-only, ±1 letter) for the 18 `SLOW_ANCHOR_KEYS`, found all 18/18
  stable. **Important nuance**: that ticket's "stable" classification predates
  `_within_score_tolerance`'s stricter magnitude check (added by a later, same-day
  commit batch per the COGNITION-LOOPDET investigation) — so "stable" there means
  grade-band-stable only, not score-magnitude-stable. None of this ticket's 14 anchors
  were covered by that sweep anyway (that sweep only covers `SLOW_ANCHOR_KEYS`, and only
  5 of this ticket's 14 anchors are `SLOW_ANCHOR_KEYS`; the ANCHOR-RELIABILITY-VERIFY
  "18/18 stable" result says nothing about whether those specific 5 anchors' *individual
  pillar* scores this ticket cares about were part of what was checked — they were, as
  part of the full 10-pillar sweep, but the failures **now** observed post-weight-fix
  postdate that verification and are not covered by its "stable" conclusion).
- `TCK-20260714-SIMQ-WEIGHTS-PILLAR-COLLISION` (done) — the immediate parent ticket.
  Its Step 7 regression scan is the direct source of this ticket's 14-anchor list and the
  `INFRA-272` parity entry. Confirmed (via its own investigation.md) that the 41 already-
  reconciled COGNITION diffs are provably attributable to the weight-collision arithmetic
  (verified per-event); the 14 in this ticket's scope are provably **not** attributable to
  that arithmetic — either a zero-delta reconstruction (weight fix caused no change) or a
  pillar the fix never reads (SOCIAL/COMBAT/PROGRESSION/NARRATIVE). This rules out the
  weight-collision fix itself as a cause for any of the 14, narrowing the causal search to
  F6-class load-sensitivity or a genuinely unrelated stale-anchor cause, matching this
  ticket's own Scope framing.
- `TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE` (done) — originated F6
  and its tolerance-guard test pattern (`test_generated_frontier_3_42_extended_population_
  stability`, `test_corpus_diversity.py:293-373`). Notably, `generated_frontier_3_42` is
  also the world for one of this ticket's 14 anchors
  (`generated_frontier_3_42_seed123_200t`, COMBAT) — but a different seed (123 vs. 42)
  and a much shorter tick count (200t vs. the 1000t+ this world's known-unstable
  population dynamics were measured at). Do not assume this anchor inherits the
  population-collapse finding directly; it needs its own repro.

## Risks and Open Questions

1. **Blocking, must be resolved before guard selection**: whether any of the 3 "200t
   exception" anchors (`generated_frontier_3_42_seed123_200t`,
   `urban_political_selfmodel_probe_seed42_200t`, and whichever one of the
   `frontier_extended`/`frontier_living_world` 200t-seed123 pair failed but its
   seed42 sibling did not) are genuinely F6-class despite being well under F6's
   documented ~tick 300-320 onset threshold. If confirmed F6 at 200t, this is new
   information that should update `docs/audits/D06_longrun_health.md` §F6's stated onset
   boundary (currently framed as roughly categorical: "below that, floor assertions are
   reliably reproducible"). If not F6 at 200t, these 3 anchors need their own
   investigation and likely a different remedy (stale anchor / genuine unrelated
   nondeterminism per the ticket's own Scope fallback). Do not assume either answer —
   the repro step must distinguish.
2. **The `combat_damage`/`entity_killed` emission path was not traced in this
   investigation** (out of the ticket's named Related Code Areas, which cites only
   `event_extractor.py`). If `generated_frontier_3_42_seed123_200t`'s or
   `frontier_extended_seed123_200t`'s/`frontier_living_world_seed123_200t`'s COMBAT
   drift traces to one of these two event types, the repro work will need to locate that
   separate construction site (likely inside combat resolution phase code, not
   `event_extractor.py`) before it can characterize the mechanism. Flagging so the
   Implement phase does not assume `event_extractor.py` is the only relevant file for
   the COMBAT pillar.
3. **`data/calibration/` is gitignored and ephemeral** (confirmed, same as both
   precedent tickets) — the specific reports the ticket's Implementation Notes reference
   ("as generated 2026-07-15 in TCK-20260714's session") will not exist on a fresh
   checkout. The repro work must regenerate them via `tools/calibrate_simq.py`
   per-scenario invocations; this is explicitly anticipated by the ticket's own Scope
   text ("ephemeral, regenerate before use").
4. **Whether a tolerance-guard's schema constraint (no range-valued fields in
   `grade_anchors.json`) still holds** — confirmed unchanged from
   `TCK-20260710-SIMQ-ANCHOR-RELIABILITY-VERIFY`'s finding (every entry remains
   `{PILLAR: {"grade": str, "score": float}}`, no list/range fields). Any
   tolerance-guard conversion must live as a separate test in
   `test_corpus_diversity.py` (or an equivalent dedicated file), not as a schema change
   to the fixture — consistent with both precedents.
5. **14 separate repro+guard decisions is a large unit of work for one ticket.** The
   Scope explicitly requires a controlled idle-vs-load repro *per anchor* (not a single
   corpus-wide conclusion), and a guard *per anchor*. Given 5 are 1000t/500t (each
   calibration run costs tens of seconds per trial per prior tickets' timing data,
   scaled up for induced-load trials), and induced-load repro trials add further
   overhead, this is plausibly the largest single-ticket repro workload in the SimQ
   reliability lineage so far (14 anchors vs. 18 anchors at grade-band-only tolerance in
   the largest precedent, but this ticket also requires idle-vs-load *and*
   score-tolerance-level* scrutiny per anchor, not just grade-band). The Plan phase
   should budget accordingly and consider whether anchors sharing a world/mechanism
   (e.g. the 5 COGNITION-drifted anchors, all seed42, all matching
   `decision_divergence_detected`'s signature) can share one representative repro rather
   than requiring 5 fully independent repro sweeps — this is a planning judgment call,
   not assumed here.
6. **Whether `urban_political_selfmodel_probe_seed42_200t`'s standalone test function
   (not parametrized under `FAST_ANCHOR_KEYS`) is included in the ticket's AC #4
   "`pytest tests/simulation_quality/test_grade_regression.py -v` is fully green"
   requirement.** It is: `-v` with no `-k`/`-m` filter runs every test function in the
   file, including standalone ones. Flagging only because it is easy to overlook this
   anchor when scanning for anchors "in `FAST_ANCHOR_KEYS`" — it is not in that list, but
   it is still exercised by the full-file pytest invocation the AC specifies.

## Anti-Drift Hazards

- **Do not touch `src/engine/kernel.py`'s watchdog/throttle logic** — hard Out of Scope,
  litigated identically by both precedent tickets, restated here because the natural
  instinct on finding a "which tick a delta event lands on" sensitivity for the
  non-COGNITION pillars might be to think about smoothing or debouncing the throttle
  itself. That is a much larger, corpus-wide behavior change belonging to its own ticket
  with its own blast-radius review, not this one.
- **Do not add a per-entity "already-emitted" dedup gate to
  `decision_divergence_detected`** as a side effect of investigating the other 4
  COGNITION anchors in this ticket's list — same hazard as
  `TCK-20260713-SIMQ-COGNITION-LOOPDET-NONDETERMINISM`'s Anti-Drift Hazards, restated
  because this ticket revisits the same code path. If a per-entity cooldown is later
  proposed, it needs its own ticket and its own blast-radius review.
- **Do not silently force-fit F6 onto the 3 "200t exception" anchors** (Risk #1) without
  confirming it via a real idle-vs-load repro for each — the ticket's own Scope
  explicitly forbids this ("do not silently force-fit F6's explanation onto a different
  cause").
- **Do not widen `_within_band`'s default ±1-letter tolerance or `_within_score_tolerance`'s
  `abs_floor`/`rel_pct` constants** as a shortcut to make any of the 14 anchors "pass" —
  same hazard both precedent tickets flag; `test_within_band_default_tolerance_unchanged`
  (`test_grade_regression.py:547-553`) exists specifically to catch this.
- **Do not silently re-anchor any of the 14 anchors' `grade_anchors.json` values without
  a guard already in place** — the ticket's own AC #2 explicitly requires this ordering
  ("`grade_anchors.json` is updated only after the guard is in place, not as a bare
  re-anchor without a guard"), matching both precedents' "not left as an unstyled
  unguarded single-run point comparison" standard.
- **Do not conflate this ticket's `generated_frontier_3_42_seed123_200t` (seed 123,
  200t, COMBAT) with the already-closed `generated_frontier_3_42` population-collapse
  finding** (`TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE`, seed 42,
  extended to 1000t, population metric not grade/score) — different seed, different
  tick count, different metric entirely. That prior ticket's guard
  (`test_generated_frontier_3_42_extended_population_stability`) is a template for
  *pattern*, not evidence this specific anchor's COMBAT drift shares its cause.
- **Do not expand this ticket's scope to trace `combat_damage`/`entity_killed`'s full
  emission architecture** unless the repro specifically implicates one of them (Risk
  #2) — read only as much of that path as needed to characterize the specific anchor's
  drift; a full audit of that separate event-emission mechanism is its own potential
  follow-up, not assumed in-scope here.
