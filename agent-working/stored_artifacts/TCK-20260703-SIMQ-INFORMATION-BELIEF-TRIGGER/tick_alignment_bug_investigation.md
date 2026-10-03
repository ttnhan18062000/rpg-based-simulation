# Sub-Investigation: `_phase_observability` Tick-Alignment Bug (Size & Risk)

**Date:** 2026-07-03T11:34:38Z
**Scope:** Narrow. Assesses size/risk of fixing the pre-existing tick-alignment bug in
`Kernel._phase_advancement()` / `EventExtractor.extract()` as a candidate scope-expansion
of TCK-20260703-SIMQ-INFORMATION-BELIEF-TRIGGER (that ticket's own work is already done and
is NOT re-litigated here). No code was modified.

---

## Affected Event Types

Complete inventory of every tick-comparison in `src/observability/event_extractor.py`, plus
one sibling instance found in `src/engine/kernel.py` (same phase, same bug shape, not in
event_extractor.py — see note below).

| Line | Expression | Pattern | Verdict |
|---|---|---|---|
| `event_extractor.py:286` | `prop.get("last_assimilated_tick") == tick` | stamped-value equality | **AFFECTED** (already confirmed). Stamped in `src/domains/information/phase.py:77` with `state.tick` = pre-advance tick during Resolution. Compared against `tick = current_state.tick` = post-advance. Never matches → `belief_assimilated`/`belief_updated` never fire. |
| `event_extractor.py:899` | `getattr(update, "last_calamity_tick_set", None) == tick` | stamped-value equality | **NEWLY CONFIRMED AFFECTED.** `src/world/calamity.py:56` sets `last_calamity_tick_set=state.tick` where `state` is the pre-advance state seen by `WorldDynamicsSystem`/`CalamityService.process_world_dynamics` during Resolution. Compared against post-advance `tick` in extract(). Never matches → `calamity_spawned` **never fires in real runs**, ever. |
| `kernel.py:836` (inside `_phase_observability`, not in event_extractor.py) | `getattr(self._status, "last_transition_tick", -1) == tick` | stamped-value equality | **NEWLY CONFIRMED AFFECTED — same bug shape, different file.** `last_transition_tick` is set via `RuntimeStatus.reset_dwell()`, called from `ResourceGovernor.evaluate()` inside `_phase_init()` (kernel.py:535-539) using `self._state.tick` **before** advancement. Compared in `_phase_observability` against `tick = self._state.tick` **after** advancement. Never matches → `GovernorModeChanged` **never fires**, ever. |
| `event_extractor.py:434` | `_age = tick - int(_discovered)` then `_age > _BELIEF_STALE_TICKS` | diff/threshold, not equality | NOT affected in the "never fires" sense. `discovered_tick` is stamped in various places (`belief.py`, `normalizer.py`, `guild.py`) with mixed conventions (`current_tick`, `state.tick`); the systematic +1 offset from this bug shifts `belief_stale`'s firing window by up to 1 tick, not a total failure. Cosmetic skew only. |
| `event_extractor.py:626-629` | `elapsed = tick - created`, `progress = elapsed / (expiry - created)` | diff/ratio, not equality | NOT affected (same reasoning — threshold/ratio tolerant of 1-tick skew). |
| `event_extractor.py:736-747` | `_last_xp_tick[eid] = tick` (stamp) then later `_since = tick - _last_xp_tick.get(eid, 0)` (read) | self-referential diff, both sides always use the *same* module-level `tick` convention | **NOT AFFECTED.** Both stamp and later comparison use `current_state.tick` consistently across ticks, so the constant +1 offset cancels out in the delta. `progression_plateau_detected` is correct today. |
| `event_extractor.py:814` | `tick % 200 == 0` (`ecology_cycle_completed`) | modulo on the label var itself | NOT "never fires," but **phase-shifted by 1**: fires at real-ticks 199/399/599/… instead of 200/400/600/…. Cosmetic, not a functional break. |
| `event_extractor.py:826` | `tick % _SPAWN_INTERVAL == 0` (`spawn_cadence_fired`) | modulo | Same as above — periodic, shifted by 1 tick. Not broken. |
| `event_extractor.py:841` | `tick % 50 == 0` (`conservation_law_verified`) | modulo | Same — shifted, not broken. |
| `event_extractor.py:945-981` (`diplomatic_transition`, faction/territory/contract events, etc.) | pure state-diff / dict comparisons (`prior_state` vs `current_state`, `update` deltas) | diff-based | Confirmed immune, consistent with the ticket's prior finding. |

**Summary:** 3 confirmed "never fires" bugs total — 2 in `event_extractor.py` (`belief_assimilated`/`belief_updated` already known, plus **newly found `calamity_spawned`**), and 1 in `kernel.py` proper (**newly found `GovernorModeChanged`**, outside event_extractor.py entirely). A handful of modulo/diff-based checks have a benign 1-tick phase-shift, not a functional break.

---

## Candidate Fixes

### (a) Change `_phase_observability`'s `tick = self._state.tick` → `tick = prior_state.tick`

**Blast radius: large.** This is the module-level label used for *every* `SimulationEvent.tick` emitted through this call — roughly 80 event types across `event_extractor.py`, plus `InvariantViolation` and `GovernorModeChanged` emitted directly in `kernel.py`. Effects:

- Fixes all 3 confirmed bugs (the two `event_extractor.py` stamped comparisons AND the `kernel.py:836` one, since they'd now compare against the same shifted `tick`).
- **Introduces a new correctness problem**: `_run_hard_law_checks` (kernel.py:724) runs `HardLawMonitor.check(self._state, ...)` against the **already-advanced** state, so `InvariantViolation` events legitimately describe the *post-advance* state and are correctly labeled with `self._state.tick` today. Under fix (a) they'd be mislabeled with the stale pre-advance tick — a regression in a currently-correct path.
- Every consumer that has ever relied on "`SimulationEvent.tick` == the new/just-advanced tick" (SimQ scorers, dashboards, replay/report tooling, any per-tick event-count reconciliation) would see all event timestamps shift by −1. This is a systemic semantic change, not a local one.
- Modulo-gated events (`ecology_cycle_completed`, `spawn_cadence_fired`, `conservation_law_verified`) would also shift their firing tick by 1 — currently benign, but changes on-disk artifact tick values for every scenario.

This is the "larger engineering effort" option — it requires re-auditing every downstream consumer of `SimulationEvent.tick`, not just the two/three bugs at hand.

### (b) Fix only the specific `== tick` checks in `EventExtractor.extract()` to compare against `prior_state.tick` explicitly, leaving the module's `tick` label unchanged

**Blast radius: small, surgical.** Two one-line changes in `event_extractor.py`:
- Line 286: `prop.get("last_assimilated_tick") == prior_state.tick`
- Line 899: `getattr(update, "last_calamity_tick_set", None) == prior_state.tick`

`prior_state` is already an extract() parameter and, in production (`kernel.py:725`), is precisely the pre-advance state snapshot — the same state whose `.tick` value was in scope when `phase.py`/`calamity.py` stamped these fields during Resolution. This is a textbook-correct, minimal fix: it does not change the event `tick` label for any event (still `current_state.tick`, consistent with every other event and with `InvariantViolation` labeling), and does not touch modulo-gated or diff-based logic at all.

Does **not** fix the `kernel.py:836` `GovernorModeChanged` bug — that lives outside `event_extractor.py` and needs its own one-line sibling fix.

### (b′) Sibling surgical fix for `kernel.py:836`

`getattr(self._status, "last_transition_tick", -1) == tick` → `== prior_state.tick`. Same reasoning: `last_transition_tick` is stamped in `_phase_init` using the pre-advance `self._state.tick`; `prior_state` is available in `_phase_observability`'s own signature. One-line change, zero blast radius outside this one `if` block — does not touch the `tick=tick` label on the `GovernorModeChanged` event itself (which correctly keeps using the post-advance tick, consistent with everything else in that method).

**Recommendation if this is done at all:** (b) + (b′) together — three total one-line changes, none of which touch the shared `tick` variable's meaning anywhere. This is categorically smaller and safer than (a).

### (c) Other approaches considered

No existing codebase convention passes an explicit "as-of tick" into `extract()` separately from `current_state`/`prior_state` — the function derives `tick` internally. Introducing a new explicit `tick:` parameter to `extract()` was considered but is strictly more invasive than (b) for the same result (touches every call site, including the ~13+ test files that call `extract()` directly) with no additional correctness benefit. Not recommended.

---

## Test Impact

Searched all direct callers of `EventExtractor.extract()` under `tests/unit/observability/`. The dominant pattern (used in `test_event_extractor_cognition.py`, `test_event_extractor_world.py`, and others) is:

```python
state = _state({1: e}, tick=10)
events = EventExtractor.extract(state, state, _update_with_belief(1, tick=10, ...), ObservabilityMode.NORMAL)
```

i.e. **`prior_state is current_state`** (the exact "same state twice" pattern flagged in the ticket as not exercising the real N-vs-N+1 pairing). Concretely:

- `test_event_extractor_cognition.py::test_belief_assimilated_emitted_when_tick_matches` / `test_belief_updated_emitted_with_belief_assimilated` / `test_belief_subject_in_payload` / `test_belief_not_emitted_when_tick_stale` — all pass `state, state, update(tick=10 or 5)`.
- `test_event_extractor_world.py::test_calamity_spawned_emitted` / `test_calamity_not_emitted_when_tick_mismatch` — same pattern, `state, state, upd(tick=10, last_calamity=10 or 5)`.

Because `prior_state` and `current_state` are literally the same object in these tests, `prior_state.tick == current_state.tick` always holds. **Under fix (b)/(b′), none of these tests change behavior** — switching the comparison target from `current_state.tick` to `prior_state.tick` is a no-op when they're the same object, so all existing assertions (both the "fires when tick matches" and "doesn't fire when stale" cases) continue to pass unchanged. **Zero test breakage identified** for fix (b)/(b′).

Under fix (a), these same tests are also unaffected directly (they call `extract()` directly, bypassing `_phase_observability` entirely, and `extract()`'s internal `tick = current_state.tick` line is untouched by fix (a)) — but fix (a) provides **no verification path** through these unit tests either way, since none of them exercise `_phase_observability` or `Kernel` end-to-end. Any regression from fix (a) (e.g. the `InvariantViolation` mislabeling) would only surface in integration/kernel-level tests, of which none currently assert on `SimulationEvent.tick` values for hard-law violations or `GovernorModeChanged` (no test references either in `tests/`).

**No existing test currently would catch a correct fix for calamity_spawned/GovernorModeChanged firing "for real"** (all use the collapsed same-state pattern) — new regression tests exercising genuine `prior_state.tick != current_state.tick` pairs would be needed regardless of which fix direction is chosen, to actually prove the bug is closed.

---

## Calibration Regression Risk

`event_extractor.py` is shared infrastructure invoked every tick of every scenario, so any change here is in scope for calibration concern — but the *practical* risk differs sharply by fix:

- **Fix (b)/(b′) (surgical, `prior_state.tick` substitution):** Changes only *whether* `belief_assimilated`/`belief_updated`, `calamity_spawned`, and `GovernorModeChanged` fire — not any other event's tick label, volume, or shape. However, this is not "risk-free noise": these events currently **never fire** in real runs today (confirmed via source trace, not just unit-test inspection), so fixing them is a genuine **behavior change**, not just a bugfix with no observable effect:
  - `belief_assimilated`/`belief_updated` feed `InformationScorer` (SQ-15/16 per `test_scenario_coverage.py`) — currently zero-signal in every calibration run; fixing this will newly populate INFORMATION pillar scoring wherever belief assimilation actually happens.
  - `calamity_spawned` feeds `WorldDynamicsScorer` (SQ-17), which has an explicit `calamity_active` vs `calamity_dormant` gate (`zero_emergence_by_tick` param, see `test_world_dynamics_scorer.py::TestCalamity`). Since `calamity_spawned` never fires today, every run currently scores as if no calamity ever occurred — likely tripping the `calamity_dormant` penalty path in every long-enough scenario. Fixing this could **swing WORLD-pillar scores** in any scenario long enough to cross `CalamityService.CALAMITY_MIN_INTERVAL` (2000 ticks) / `CALAMITY_FORCE_INTERVAL` (5000 ticks) — worth noting per `docs/audits/D06_longrun_health.md`, existing long-run audits reference "1,000-tick runs," which is **below** the calamity min-interval, so short calibration scenarios may see no change at all; only longer-duration scenarios would be affected. This needs an actual run to know, not just static analysis.
  - `GovernorModeChanged` is infrastructure telemetry, not scored by SimQ pillars (no reference found in `simulation_quality/`), so its fix is low-risk for calibration scoring specifically, but still changes observability/telemetry output.
- **Fix (a) (global tick relabel):** Same behavior changes as above, **plus** shifts every event's `tick` field by one across every scenario's event log (a much larger diff footprint against any stored artifacts/snapshots that pin exact tick values) and mislabels `InvariantViolation` tick going forward — this would need re-validation across the full calibration corpus, not just the 3 event types.

**Honest estimate:** A full 30-scenario calibration re-run is not strictly *required* for fix (b)/(b′) to be safe from a determinism/correctness standpoint (the change is narrowly scoped and doesn't touch RNG, state mutation, or unrelated event paths), but it **is warranted** to characterize the scoring-impact magnitude of newly-firing `belief_assimilated`/`calamity_spawned` events on SimQ pillar scores, since those pillars have never seen non-zero signal from these event types in any existing calibration baseline. At minimum, the scenarios with the longest tick counts (those most likely to cross the calamity interval, and any INFORMATION-heavy scenario) should be spot-checked before/after. A blanket "not needed" claim would be dishonest given the confirmed always-zero-today baseline for both scorers.

---

## Contract/Documentation Answer

Searched `docs/engine/kernel.md`, `docs/engine/architecture.md`, `docs/engine/known_limitations.md`, `docs/engine/project_lawbook_m10.md` for explicit tick-labeling semantics for `_phase_observability` / `EventExtractor.extract()`. None exists. `kernel.md`'s 7-phase table documents *phase order* (Advancement=phase 6 "Update world clock and commit the new state," Persistence=phase 7) but does not specify what tick value telemetry emitted *during* Advancement should carry.

One informative precedent: `_phase_persistence` (Phase 7, kernel.py:942-944) emits the replay `TICK_END` event using `self._state.tick` — i.e., the **post-advance** tick — establishing an implicit codebase convention that telemetry emitted after Advancement labels itself with the new/post-advance tick, not the tick that just finished executing. This is consistent with current `event_extractor.py` behavior (`tick = current_state.tick`) and is *evidence against* fix (a) (which would make `_phase_observability` the one place using the opposite convention from `_phase_persistence`, one phase later in the same tick).

**Conclusion: there is no authoritative contract answer — this is genuinely ambiguous engineering judgment**, but the codebase's own existing convention (`TICK_END` using post-advance tick) leans toward preserving the current label semantics (i.e., favoring fix (b)/(b′) over fix (a)). No `docs/parity_ledger/` entry references this either; `infrastructure.yaml` (replay/telemetry/observability) would be the natural home for a parity entry if this is fixed, and none currently exists mentioning tick-alignment in event extraction.

---

## Recommendation

**This is a small, contained, surgical fix (b + b′) — not a large engineering effort — provided it is scoped exactly as fix (b)/(b′), not fix (a).**

Reasoning:
1. The correct fix is 3 one-line changes across 2 files (`event_extractor.py:286`, `event_extractor.py:899`, `kernel.py:836`), all following the identical, low-risk pattern of comparing a Resolution-phase-stamped value against `prior_state.tick` (already an available parameter) instead of the post-advance `tick` variable.
2. Zero existing tests break under this fix — verified by tracing the exact "same state twice" test pattern used throughout `tests/unit/observability/`.
3. The one real risk is **not code risk, it's calibration-baseline risk**: `belief_assimilated`, `belief_updated`, and `calamity_spawned` have never fired in any real run to date, so fixing them is a genuine, previously-invisible behavior change to SimQ INFORMATION and WORLD pillar scoring. This warrants targeted before/after spot-checks on a few long-running/INFORMATION-heavy scenarios — not a mandatory full 30-scenario re-run, but budget for at least reviewing scoring deltas is honest and appropriate.
4. No documented contract dictates the answer, but the codebase's own `TICK_END` convention supports fix (b)/(b′)'s direction (preserve current post-advance event-tick labeling; fix only the specific stamped-value comparisons) over fix (a)'s riskier global relabeling, which would additionally regress `InvariantViolation` tick-correctness with no compensating benefit.

**Decision framing for the human:** if the goal is "close this specific, cheap, well-understood bug," expanding INFORMATION-BELIEF-TRIGGER's scope by fix (b)/(b′) is proportionate and low-risk to implement in the same session. If the goal is "prove SimQ scoring baselines are stable after this change," that calls for a separate follow-up ticket to do the targeted calibration spot-check — this should not block the code fix but also should not be silently skipped, since the change measurably alters INFORMATION and WORLD pillar signal for the first time.
