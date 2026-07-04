---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE
artifact_type: plan
tags: [simulation_quality, agency, cognition, stasis, calibration, bug]
---

# Plan — TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE

## Decisions Pinned By Direct Evidence (not re-litigated)

- Root cause is `AgencyScorer`'s stasis-penalty formula (`src/simulation_quality/scorers/agency.py:87-112`),
  not adventure decision logic. `AdventureDecisionPhase`/`Generator`/`Service` behave exactly per
  their own contract for entity 23/seed456 (investigation §3). **Not touched by this plan.**
- Two independent defects, both must be fixed together (investigation §2.3, §2.4):
  1. **Attribution**: `defer_count` (`agency.py:90`) is a population-wide `context.window_tag_counts`
     lookup, not the per-entity consecutive counter the contract's own prose/pseudocode describe
     (`docs/simulation_quality/quality_scoring_contract.md:451,556`).
  2. **Magnitude**: `stasis_per_tick * extra_ticks` (`agency.py:109-110`) has no ceiling — the only
     unbounded-growth negative weight across all 10 pillars in `scoring_weights.yaml`.
- Not in scope: `src/domains/adventure/` decision logic; the `hometown` resource-tag content gap
  (filed as a new standalone follow-up, see Step 7); re-litigating STONE-GAP.

## Numeric grounding used throughout this plan (re-derived, not assumed)

Confirmed live from `data/calibration/simq_routing_test_seed456_500t/quality_scores.jsonl`
(AGENCY records only):

```
entity 23: 491 events, sum delta = -172,751.0  (all defer_with_reason / defer_idle / stasis_N)
entity 24: 101 events, sum delta = +105.0      (route_selected / action_executed / route_family_first_use)
entity 25: 101 events, sum delta = +105.0      (same as 24)
total raw = -172,541.0  → normalized = raw / 500 = -345.082  (matches investigation exactly)
```

`quality_report.py:99-104`: `normalized_score = raw_score / effective_denominator`, where
`effective_denominator = max(floor_tick, last_event_tick)`, `floor_tick = max(1, tick//4)`. For this
500-tick run, `effective_denominator = 500`. Grade thresholds (`grade_thresholds.yaml`):
`S>2.0, A>0.5, B>0.0, C>-0.5, D>-1.0, else F` — i.e. in **raw-score terms** (×500): `S>1000, A>250,
B>0, C>-250, D>-500`.

Entities 24+25 contribute a fixed **+210** raw, unaffected by this fix (they never emit
`defer_with_reason` in any of the 3 seeds — confirmed, see Step 6). So the AGENCY grade for this
run is entirely determined by `entity23_total + 210`.

**Load-bearing fact used below**: `defer_idle = -1.0` (`scoring_weights.yaml:19`) is a *flat, fixed
per-event weight applied to literally every `defer_with_reason` event*, independent of any streak
tracking or cap — it is not part of the two defects above and is out of this ticket's DECIDED scope
(it is the same flat-per-event convention as `action_taken=+1.0`, not a bug). Entity 23 emits 491
such events regardless of how the escalation term is fixed. Therefore, **even with the escalation
term capped all the way down to a no-op (delta=0 added)**, `entity23_total >= -491` and
`total >= -491 + 210 = -281`, i.e. `normalized >= -0.562`. This is inside the **D** bracket
(`-1.0 < -0.562 <= -0.5`... actually `-0.562` fails `> -0.5` so it is **D**, not C) and specifically
**cannot reach C** (needs `entity23_total > -460`; base alone is already `-491`, i.e. 31 raw units
short) **let alone B** (needs `entity23_total > -210`, 281 raw units short) **purely from the base
per-event weight, before any escalation is even added.**

**This is a hard mathematical ceiling, not a cap-design choice**: no value or shape of the escalation
term can push this specific run above D, because the escalation term can only subtract further, never
add back. See the "Governance Decision — AC6 Per-Seed Exception" section below and Step 8 — this is
resolved by governance decision (not re-litigated by this ticket), not left open.

## Step 1 — Per-entity streak attribution (`src/simulation_quality/scorers/agency.py`)

Mirror the existing per-entity instance-state pattern already used for `project_abandoned`/
`project_started` cycling (`self._last_abandoned: dict[int, str]`, `agency.py:28,72,81-84`) — this
is the "existing per-entity instance-state pattern" the investigation pointed at, confirmed by
reading the file. Add two new dicts in `__init__` (`agency.py:26-29`):

```python
self._entity_defer_streak: dict[int, int] = {}
self._entity_stasis_fired: dict[int, bool] = {}
```

Add a private helper:

```python
def _reset_entity_stasis(self, entity_id: Optional[int]) -> None:
    if entity_id is not None:
        self._entity_defer_streak.pop(entity_id, None)
        self._entity_stasis_fired.pop(entity_id, None)
```

Call `self._reset_entity_stasis(entity_id)` at the top of the `action_executed` (`agency.py:54-55`),
`route_selected` (`agency.py:61-62`), `route_family_first_use` (`agency.py:57-59`), and
`project_completed` (`agency.py:64-67`) branches — these are the signals that the entity actually
took/completed a real route this tick, so any prior defer streak is over. `project_started` /
`project_abandoned` / `commitment_abandoned` are **not** reset points (they return `None` today and
are not part of the routing defer/act dichotomy — leave untouched).

Replace the `defer_with_reason` branch's `defer_count` source (`agency.py:87-112`). The
**population-wide `window_tags`/`defer_count` lookup is kept only for the `population_stasis`
one-shot check** (`agency.py:92-104`) — that mechanism is explicitly population-level by design
(investigation §3, "population_stasis... is a separate mechanism... should not be touched") and its
own tests (`test_population_stasis_fires_when_no_actions`, `test_population_stasis_fires_only_once`,
and the `test_timegate_penalties.py` population_stasis tests) must keep passing unmodified. A new,
separate per-entity `streak` variable drives the `stasis_N` path:

```python
if et == "defer_with_reason":
    stasis_gate = self.weights.int_param("stasis_gate_ticks")
    window_tags = context.window_tag_counts.get(PillarId.AGENCY, {})
    pop_defer_count = window_tags.get("defer_idle", 0)  # population_stasis check only, unchanged

    if (
        not self._pop_stasis_fired
        and tick > stasis_gate
        and window_tags.get("action_taken", 0) == 0
        and pop_defer_count > 0
    ):
        self._pop_stasis_fired = True
        return _rec(
            self.weights["population_stasis"],
            "population-wide stasis: zero non-defer actions in window",
            ("population_stasis",),
        )

    streak = self._entity_defer_streak.get(entity_id, 0) + 1
    if entity_id is not None:
        self._entity_defer_streak[entity_id] = streak

    cap = self.weights.int_param("stasis_extra_ticks_cap")
    delta = self.weights["defer_idle"]
    tags = ["defer_idle"]
    if streak > stasis_gate:
        tags.append("stasis_N")
        extra = streak - stasis_gate
        already_fired = self._entity_stasis_fired.get(entity_id, False) if entity_id is not None else False
        # Fire the one-shot escalation only once the streak has ACTUALLY REACHED the
        # full cap threshold (extra >= cap), NOT at the first post-gate tick (extra == 1).
        # Firing at extra == 1 would always add stasis_per_tick * 1 regardless of `cap`,
        # since streak increments by exactly 1 per event -- this was the original defect
        # (architecture review, TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE plan review):
        # `min(streak - stasis_gate, cap)` evaluated to 1 at the very first breach, every
        # time, making the escalation permanently -3.0 instead of the intended -15.0.
        if not already_fired and extra >= cap:
            capped_extra = min(extra, cap)  # defensive; extra == cap at the firing point by construction
            delta += self.weights["stasis_per_tick"] * capped_extra
            if entity_id is not None:
                self._entity_stasis_fired[entity_id] = True
    return _rec(delta, "entity deferred action", tuple(tags))
```

Design note on the `stasis_N` tag continuing to fire on every event past the gate (not just once):
this preserves the documented loop-detection signal (`quality_scoring_contract.md:563`:
"`stasis_N` at >70% of window → `loop_detected:entity_stasis`", implemented in
`pillar_accumulator.py:60-70` via tag-frequency over `window_buffer` — a boolean-presence check, not
a magnitude sum). Only the **numeric delta contribution** is one-shot per continuous streak; the
**tag** (observability signal) keeps firing for as long as the entity is genuinely stuck. This keeps
`loop_detected:entity_stasis` meaningful for the whole duration of a real stasis episode, while
bounding the score contribution.

## Step 2 — Cap mechanism and value (resolved)

**Mechanism: a capped, ONE-SHOT-per-streak escalation**, not a capped-but-repeating per-event
penalty. Both were considered; only one-shot satisfies the test_plan.md failure-mode requirement
("bounded/asymptotic... not just less than before"):

- **Capped-but-repeating** (fire the capped extra every event past the cap point, forever): with
  `stasis_extra_ticks_cap=5` (see below), the per-event floor is `-1.0 + (-3.0*5) = -16.0`, repeated
  for the ~481 remaining events of entity 23's 491-event streak → `-16*481 ≈ -7,696` alone, total
  `≈ -7,541` raw, normalized `≈ -15.08` — **still deep in F territory**. Rejected: a repeating cap's
  cumulative total still grows linearly (unboundedly) with streak length, just at a slower rate; it
  is not actually bounded, only "less bad," and for a genuinely long-lived stuck entity it can still
  blow through every grade band.
- **One-shot** (chosen): the capped magnitude is added exactly once per continuous per-entity
  streak, then subsequent events in the same streak get only the flat `defer_idle` base. This gives
  a magnitude contribution from the escalation term that is **provably independent of streak
  length** — a true asymptotic bound, satisfying test_plan.md's "Formula must not silently
  reintroduce unbounded growth" / "actually bounded/asymptotic" requirement for any streak length
  (500 ticks or 5000).

**Value: `stasis_extra_ticks_cap = 5`**, added to `config/simulation_quality/detection_params.yaml`'s
existing free-form `time_gates: dict[str, int]` (`detection_params.yaml:5-27`, no schema change
needed — `weights.py:66`'s `int_param()` already reads arbitrary keys from this dict, confirmed by
reading `weights.py:35-64`). One-shot ceiling magnitude = `stasis_per_tick * stasis_extra_ticks_cap
= -3.0 * 5 = -15.0` (added once, on top of the ever-present `-1.0` base), for a maximum single-event
delta of **-16.0** at the moment the one-shot fires, and `-1.0` for every other event in the streak.

Reasoning for `-15.0` as the one-shot ceiling, tied to the existing grade-banding/severity scale
(per the instruction to calibrate against real magnitudes, not an arbitrary round number):

- It must be **strictly less severe** than `population_stasis = -25.0`
  (`scoring_weights.yaml:25`) — AGENCY's own largest fixed penalty, reserved for a *population-wide*
  collapse (zero non-defer actions from anyone). A single stuck entity while others act normally is
  a lesser condition and should not out-rank it.
- It matches the established "`*_dormant`/sustained-severity" tier used across the whole config for
  "this subsystem has gone quiet for a while" signals: `AGENCY.rejection_cascade_sustained=-15.0`,
  `COMBAT.combat_dormant=-15.0`, `SOCIAL.cooperation_dormant=-15.0`,
  `COGNITION.belief_system_dormant=-15.0`, `INFORMATION.belief_system_silent=-15.0` (confirmed via
  `config/simulation_quality/scoring_weights.yaml`: `COGNITION` uses the key `belief_system_dormant`,
  `INFORMATION` uses the distinct key `belief_system_silent` — same -15.0 magnitude and semantic
  intent, different key names; citation corrected here to name each pillar's actual key rather than
  conflating them under one name). `-15.0` sits exactly on this existing convention rather than
  inventing a new magnitude class.
- `stasis_extra_ticks_cap=5` (equal to `stasis_gate_ticks=5`) is a deliberately simple, readable
  choice: "wait `gate` ticks before flagging stasis at all, then wait one more `gate`-length window
  before escalating once, permanently, until the entity acts again." This keeps the two related
  constants symmetric and easy to reason about instead of an unrelated magic number.
- Verified not toothless: `-15.0` is 15x the base `defer_idle` penalty and larger than 8 of the other
  9 pillars' non-collapse-tier severe penalties (e.g. larger than `zero_trade=-15.0` ties,
  larger than `progression_frozen=-10.0`, `knowledge_economy_dormant=-10.0`) — it registers as a
  real, distinct severity marker in `worst_events`, not a rounding error.

**Resulting grade for seed456 (recomputed against the corrected Step 1 firing condition —
`extra >= cap`, not `streak > stasis_gate` — with `stasis_gate_ticks=5`, `stasis_extra_ticks_cap=5`;
to be confirmed by live re-run in Step 5)**:

Entity 23's 491-event continuous `defer_with_reason` streak (streak counter increments 1 per event,
no non-defer routing action ever occurs for this entity — investigation §2.1) breaks down as:

| Streak range | # events | Condition | `stasis_N` tag? | Escalation fires? | Delta/event |
|---|---|---|---|---|---|
| 1–5 (`streak <= gate`) | 5 | below/at gate | no | no | `-1.0` |
| 6–9 (`streak > gate`, `extra < cap`) | 4 | `extra = streak-5 ∈ {1,2,3,4}`, `< cap(5)` | yes | no (not yet at cap) | `-1.0` |
| 10 (`streak = gate+cap`) | 1 | `extra = 5 >= cap(5)`, first time | yes | **YES (one-shot)** | `-1.0 + (-3.0*5) = -16.0` |
| 11–491 (already fired) | 481 | `extra > cap`, `already_fired=True` | yes | no (already fired) | `-1.0` |

Event-count check: `5 + 4 + 1 + 481 = 491` ✓ (matches the confirmed live count).

```
entity23_total = (5 + 4 + 481) * -1.0 + 1 * -16.0
               = 490 * -1.0 + -16.0
               = -490.0 - 16.0
               = -506.0
```

**This is the same -506.0 the plan originally stated** — that number was always the *intended*
design target; the defect (architecture review, "Violation 1") was that Step 1's original code fired
the one-shot at the very first post-gate event (`streak = gate+1 = 6`, `extra = 1`), where
`capped_extra = min(1, cap) = 1` **regardless of `cap`'s configured value** (5). That produced a
buggy escalation of `stasis_per_tick * 1 = -3.0`, not `-15.0`, giving a buggy total of
`490 * -1.0 + 1 * -4.0 = -494.0` — matching the architecture review's independently-verified ~-494
figure. The corrected condition above (fire only when `extra >= cap`, i.e. at `streak = gate + cap =
10`) closes this gap: the escalation is genuinely `stasis_per_tick * cap = -3.0 * 5 = -15.0`
(single-event delta `-16.0` including the base `-1.0`), applied exactly once, at the point the streak
actually crosses the full cap threshold — matching Step 1's code as now written above.

```
total = entity23_total + 210 = -506.0 + 210 = -296.0
normalized = -296.0 / 500 = -0.592
```

`-0.592` → **D** bracket (`-1.0 < -0.592 <= -0.5`; same bracket as the escalation-disabled floor
computed above, `-0.562` — the one-shot adds real severity, visible in `worst_events` and the
`stasis_N` loop flag, without being catastrophic). This is a genuine, large improvement over `F`
(`-345.08`), but is **not** `>= B` — this is now a governance-decided, documented exception (Step 8),
not an open question.

## Step 3 — Update `docs/simulation_quality/quality_scoring_contract.md`

**Pseudocode block (lines 441-455)**: replace the `consecutive = context.window_tag_counts[...]`
line (line 451, which the investigation confirmed encodes the same population-wide bug under a
misleading name) with the corrected per-entity, capped, one-shot logic:

```python
class AgencyScorer(PillarScorer):
    def __init__(self, weights):
        ...
        self._entity_defer_streak: dict[int, int] = {}
        self._entity_stasis_fired: dict[int, bool] = {}

    def score(self, envelope, context):
        w = self.weights
        entity_id = envelope.entity_id

        if envelope.event_type == "defer_with_reason":
            gate = w.int("stasis_gate_ticks")
            cap = w.int("stasis_extra_ticks_cap")
            streak = self._entity_defer_streak.get(entity_id, 0) + 1
            self._entity_defer_streak[entity_id] = streak

            delta = w["defer_idle"]
            tags = ["defer_idle"]
            if streak > gate:
                tags.append("stasis_N")
                extra = streak - gate
                # Fire only once the streak has actually reached the full cap threshold
                # (extra >= cap) -- NOT at the first post-gate tick (extra == 1), which
                # would always yield capped_extra=1 regardless of `cap`.
                if not self._entity_stasis_fired.get(entity_id, False) and extra >= cap:
                    delta += w["stasis_per_tick"] * min(extra, cap)
                    self._entity_stasis_fired[entity_id] = True
            return ScoreRecord(delta=delta, tags=tuple(tags), ...)

        # non-defer routing outcomes reset this entity's streak:
        if envelope.event_type in ("action_executed", "route_selected", "route_family_first_use", "project_completed"):
            self._entity_defer_streak.pop(entity_id, None)
            self._entity_stasis_fired.pop(entity_id, None)
            ...
```

**AGENCY table row (line 556)**: change

> `Entity receives DEFER for N>5 consecutive ticks | −3 per additional tick | stasis_N`

to:

> `Entity receives DEFER for N>5 consecutive ticks (per-entity streak, tracked via instance state — not the shared scoring window) | −3 × cap (max −15, capped), applied exactly once per continuous streak — at the tick the streak first reaches `gate + cap` (streak=10), not at the first post-gate tick (streak=6); no further escalation for the rest of the streak; resets when the entity next takes a non-DEFER routing action | stasis_N`

Add one clarifying sentence directly under the table (near line 563's "Loop signal" line) noting
that the `stasis_N` **tag** continues to be applied on every qualifying event (for loop-detection
purposes), while the **score delta** it carries is the one-shot cap after the first occurrence —
so readers don't assume tag-presence implies a repeating penalty.

## Step 4 — Rewrite existing tests

`tests/simulation_quality/test_agency_scorer.py::TestDefer`:
- `test_stasis_fires_after_gate` (105-113): the `_ctx(window_tags=...)` injection pattern no longer
  drives `stasis_N` (that path is now population_stasis-only). Rewrite to call `scorer.score()`
  repeatedly for the **same `entity_id`** across `gate + cap` consecutive `defer_with_reason`
  calls (driving the new per-entity streak via repeated calls, matching how a real run would
  produce it), then assert: `stasis_N` present on every call once `streak > gate` (i.e. from call
  `gate+1` onward); calls `gate+1` through `gate+cap-1` (the "not yet at cap" window) carry
  `delta == defer_idle` only, despite carrying the `stasis_N` tag — **the escalation must NOT fire
  at the first post-gate call** (this is the exact defect the architecture review caught: firing at
  `streak = gate+1` always yields `capped_extra = min(1, cap) = 1` regardless of `cap`'s configured
  value); the call at `streak == gate + cap` (the `cap`-th post-gate call) carries
  `delta = defer_idle + stasis_per_tick * cap`; **all subsequent** post-gate calls (further into the
  same streak) carry `delta == defer_idle` only (one-shot already fired). Also assert `"stasis_N"`
  is still present in `tags` on those later calls (tag keeps firing, magnitude does not).
- `test_stasis_no_fire_before_gate` (98-103): no behavioral change needed (streak below gate never
  triggers `stasis_N` in either the old or new model) — re-verify passes unmodified, note in Test
  Summary.
- `test_population_stasis_fires_when_no_actions` / `test_population_stasis_fires_only_once`
  (115-129): unchanged code path — re-run to confirm no regression, do not modify assertions.
- Add a new `TestStasisBounding` class (or extend `TestDefer`) per the ticket's own AC ("regression
  test proving this specific stasis-collapse scenario doesn't recur"):
  - `test_stasis_one_shot_bounded_for_long_streak`: drive 500+ consecutive `defer_with_reason` calls
    for one `entity_id`; assert the **cumulative** delta contribution from `stasis_N`-tagged escalation
    (i.e. total delta minus `defer_idle * event_count`) equals exactly `stasis_per_tick *
    stasis_extra_ticks_cap` (a single fixed constant), regardless of how many events beyond the cap
    point occur — i.e. assert this sum is **identical** whether the streak is 20 or 2000 events long
    (parametrize over both lengths, assert equal escalation contribution).
  - `test_streak_resets_on_non_defer_action`: defer past the gate (one-shot fires), then feed one
    `action_executed`/`route_selected` for the same entity, then defer past the gate again — assert
    the one-shot **fires a second time** (streak counter genuinely reset, not stuck at "already
    fired forever").
  - `test_two_entities_streaks_independent`: interleave `defer_with_reason` calls for two different
    `entity_id`s past the gate; assert each accrues its own one-shot independently (entity A's
    one-shot firing does not suppress or double-count entity B's).

`tests/simulation_quality/test_timegate_penalties.py`:
- `test_stasis_N_timegate_fires_after_gate` / `test_stasis_N_timegate_not_before_gate`: same
  per-entity-driving rewrite as above (repeated same-entity calls instead of `window_tags`
  injection).
- `test_stasis_N_timegate_accumulates_linearly`: **rename** to
  `test_stasis_N_timegate_bounded_one_shot` (the name itself asserted the bug's behavior) and
  rewrite to assert the capped one-shot magnitude instead of linear accumulation, plus a long-streak
  case proving no further growth (mirrors the new `test_stasis_one_shot_bounded_for_long_streak`).
- `test_population_stasis_timegate_*` (484-535): unchanged code path, re-run only.

Both files' `_ctx()` helper (which still accepts `window_tags` for `action_taken`/`population_stasis`
gating) stays as-is; new tests additionally track/pass a consistent `entity_id` across multiple
`scorer.score()` calls to build up the per-entity streak, since that state now lives in the scorer
instance, not the injected context.

## Step 5 — Re-run seed456, update `grade_anchors.json`

```
rm -rf data/calibration/simq_routing_test_seed456_500t/
ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py --ticks 500 --seed 456 --name simq_routing_test
```

Confirm the resulting AGENCY grade matches (or is close to) the Step 2 prediction (D). Update
`tests/simulation_quality/fixtures/grade_anchors.json`'s `simq_routing_test_seed456_500t.AGENCY`
from `"D"` (placeholder-for-F) to whatever the **real recomputed grade** is (predicted `D`, but this
is a placeholder-for-real-D now, not a floor-for-F — this distinction matters and should be called
out in the Files Changed / Completion Summary so a future reader doesn't confuse "D" the honest
grade with "D" the old schema-floor stand-in). Do NOT hand-adjust weights further just to force a
`B` — the gap to `B` is a documented, governance-decided AC6 exception (Step 8), not a tuning target.

## Step 6 — Re-run seed42/seed123, confirm no regression

Per investigation §2.2/§2.1, entities 24/25 in **all three seeds** never emit a single
`defer_with_reason` event (their 101 events/run are exclusively `route_selected`/`action_executed`/
`route_family_first_use`) — confirmed via the `quality_scores.jsonl` entity/event-type breakdown
above and the investigation's `decision_trace.jsonl` citations. The per-entity streak dict therefore
never accumulates for entities 24/25 in any seed; the attribution change is fully inert for them.
Re-run both anyway as a live confirmation (not just an assumption, per the task's explicit
instruction):

```
rm -rf data/calibration/simq_routing_test_seed{42,123}_500t/
ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py --ticks 500 --seed 42  --name simq_routing_test
ENABLE_ADVENTURE_ROUTING=ON python3 tools/calibrate_simq.py --ticks 500 --seed 123 --name simq_routing_test
```

Confirm `AGENCY` grade stays `A` for both (matching `grade_anchors.json`'s existing entries — no
anchor change expected for these two).

## Step 7 — File standalone follow-up ticket (content gap, out of scope here)

Create `tickets/todos/TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP.md` (standalone file, not
inside a subfolder — matching the flat-file convention seen throughout `tickets/done/`), tier
`standard`, type `bug`. Scope citing investigation §2.1's evidence: none of `simq_routing_test`'s 5
resource nodes (`herb_patch`, `wood_node`, `iron_vein`, `silver_vein`, `crystal_outcrop`) list
`hometown` in `source_region_tags`, and all heroes spawn in `hometown`
(`ResourceOpportunityProvider.get_opportunities`, `src/world/providers/resources.py:69`) — so any
hero whose personality roll lands `sociability < 0.2` (the `FORM_PARTY` gate,
`src/domains/adventure/generator.py:124`) has **zero** possible non-defer route for its entire life
in this world, seed-independently. This is a world-content authoring gap, not a decision-logic or
scoring bug. (Created as part of this ticket's Step 7 deliverable — see the actual ticket file for
full required sections.)

## Step 8 — Record AC6 per-seed exception (governance decision, not re-litigated)

**This decision is already made and is not re-opened by this plan**: "`AGENCY` grade no longer `F`"
is the binding closure bar for this ticket. AC6's blanket "`>= B` for all 3 `simq_routing_test`
seeds" gate now carries a documented, evidenced **per-seed exception** for `seed456`, mirroring the
existing AGENCY=C archetype-exception precedent already recorded for this pillar
(`TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA`, documented in
`docs/simulation_quality/eval_matrix_results.md`'s `## AC6 — AGENCY Confirmation` and
`## AGENCY — Cross-World Design Note` sections). Run this step **after** Step 5 (live-recomputed
grade exists) and Step 7 (follow-up ticket ID exists), since both are cited below.

1. **`docs/simulation_quality/eval_matrix_results.md` — `## AC6 — AGENCY Confirmation` section**:
   append a new dated status paragraph directly after the existing "Historical text (pre-recompile,
   superseded...)" paragraph (after current line ~378), matching that section's existing
   dated-status-paragraph format/style exactly:

   ```
   **Status as of 2026-07-04 (TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE): DOCUMENTED EXCEPTION.**
   seed456's AGENCY grade is fixed at [live-recomputed grade from Step 5, predicted **D**] (up from
   `F`), and this is accepted as a permanent, evidenced exception to AC6's "≥ B for all 3 seeds" gate
   — not a further remediation target. Root cause: entity 23's `sociability` roll lands just under
   the `FORM_PARTY` gate (`src/domains/adventure/generator.py:124`), and no resource node in
   `simq_routing_test`'s world content lists `hometown` in `source_region_tags`
   (`src/world/providers/resources.py:69`), while all heroes spawn in `hometown` — so this entity has
   zero legal non-defer route for its entire 500-tick life, seed-independently, once its personality
   roll lands this way. This is a genuine, provable, legitimate-stasis case (confirmed by
   `TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE`'s investigation), not a decision-logic or scoring bug —
   the scoring fix in that ticket (per-entity streak attribution + one-shot capped escalation)
   corrects the *magnitude* of the penalty (`F` → `D`) but cannot and should not force the grade to
   `B`, since the underlying behavior (491 legitimate consecutive defers) is real, and the
   `defer_idle` per-event weight is explicitly out of that ticket's authorized scope. The
   world-content gap producing the zero-route condition is tracked separately as
   `TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP` (a `hometown` resource-tag authoring fix,
   not a scoring or decision-logic change); even if that lands, this per-seed exception record is
   retained as historical evidence for this run — a future re-anchor would be a new anchor update,
   not a retroactive edit here.
   ```

2. **`docs/simulation_quality/eval_matrix_results.md` — `## AGENCY — Cross-World Design Note`
   section**: append a new subsection directly after the existing "Anti-drift" paragraph (after
   current line ~413), introducing this as a second, distinct exception class alongside the
   archetype-C exception already documented there:

   ```
   **Second exception class — per-seed legitimate-stasis (TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE):**
   unlike the archetype-C exception above (a *pillar-inactive-by-flag* exception, applying uniformly
   whenever `ENABLE_ADVENTURE_ROUTING=OFF`), this is a *pillar-active-but-content-constrained*
   exception: routing is genuinely ON and the scorer is scoring correctly for
   `simq_routing_test_seed456`, but one entity's personality roll combined with a resource-tagging
   gap in this specific world's content leaves it with zero legal routes for its whole life, capping
   the achievable grade at D regardless of scoring-formula correctness. See AC6 above for the full
   evidence chain.
   ```

3. **`tickets/inprogress/TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE.md`** — implementer to-do: update
   the Acceptance Criteria list, replacing the single bullet

   > `- [ ] simq_routing_test seed456's AGENCY grade no longer F; AC6 fully re-confirmed for all 3 seeds`

   with two bullets:

   > `- [ ] simq_routing_test seed456's AGENCY grade no longer F (binding closure bar for this ticket)`
   > `- [ ] AC6's "AGENCY >= B for all 3 seeds" gate carries a documented, evidenced per-seed exception for seed456 (recorded in docs/simulation_quality/eval_matrix_results.md's AC6 and Cross-World Design Note sections) rather than being fully satisfied — governance-decided, not re-litigated by this ticket`

4. **`docs/plans/audit_fix_plan.md`** — line 566's `P0-A ENABLE_ADVENTURE_ROUTING` summary-table row
   currently reads "...AGENCY=B achievable via env-var inject (confirmed by simq_routing_test)." with
   no per-seed qualification; this is now stale for `seed456` specifically (P0-A's flag-default
   decision itself remains correctly `RESOLVED` — do not change that status). Append a parenthetical
   to that row's text:

   ```
   (seed456 specifically now carries a documented D-grade exception post-TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE — see eval_matrix_results.md AC6 section; seed42/seed123 remain unaffected, A/A)
   ```

## Step 9 — Parity ledger check

`docs/parity_ledger/strategic_cognition.yaml` has **no** AGENCY/stasis-specific entry (confirmed via
full-file grep — its one `stasis`/`defer`-adjacent hit at line 2618 is an unrelated economy
"deferred to next evaluation" phrase). The relevant entry is
**`docs/parity_ledger/infrastructure.yaml` id `INFRA-237`** (`AgencyScorer covers all contract §5
AGENCY & ACTION rules... stasis_N (time-gated)...`, `v2_evidence: agency.py::AgencyScorer.score;
scoring_weights.yaml AGENCY section`, `test_path: test_agency_scorer.py;
test_timegate_penalties.py::TestAgencyTimegate`).

Update `INFRA-237`:
- `text`: keep as-is (still true — the scorer still covers all these rules), but append a clause
  noting `stasis_N` is now per-entity-attributed and capped/one-shot (was population-wide and
  unbounded).
- `v2_evidence`: unchanged (same file/class), no new file added.
- `test_path`: unchanged (same test files, just rewritten assertions inside them).
- `divergence_note`: add — this field exists precisely for "intentional differs from documented
  contract" cases. Record: "2026-07-04 (TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE): stasis_N
  attribution corrected from population-wide windowed count to true per-entity consecutive streak,
  matching the contract's own documented intent (quality_scoring_contract.md:556); escalation term
  capped to a one-shot magnitude (`stasis_per_tick * stasis_extra_ticks_cap`, new
  `detection_params.yaml` time-gate) to prevent unbounded growth. Corrects a real doc/code mismatch
  where the contract's own worked pseudocode (line 451, variable `consecutive`) encoded the same
  population-wide bug as the implementation."

No `strategic_cognition.yaml` entry needs creation — this is squarely an `infrastructure.yaml`
(observability/scoring plumbing) concern per that file's existing AGENCY entry, not a strategic
cognition/goal-hierarchy concern (confirmed in investigation §3: `docs/mechanics/
04_strategic_cognition.md` has zero mentions of stasis/defer/AGENCY scoring at all).

No new entry in `docs/guidelines/intentional_divergences.md` (the actual filename — CLAUDE.md's
reference to `v2_intentional_divergences.md` is stale; confirmed via `find`) — that document tracks
Legacy-V1-vs-V2 behavior divergences per its own structure (`## 3. Unsupported/Retired Behavior`,
numbered `DEV-00N` economy divergences, etc.); this fix is a SimQ-scoring-contract-internal
correction with no legacy analog, so it belongs in the parity ledger's `divergence_note` (as above)
and the contract doc itself (Step 3), not this file.

## Step 10 — `make evaluate --dry-run`

Run after Steps 5-6's calibration data is refreshed and `grade_anchors.json` is updated. This
diffs current `data/calibration/` against anchors with no engine re-run
(`tools/evaluate_simq.py --dry-run`, `Makefile:286-287`). Must exit 0 (no regressions across the
rest of the corpus — dungeon_crawl, sandbox_world, urban_political, frontier_*, highland_traverse,
swamp_border_world, wilderness_survival — none of which touch `AgencyScorer`'s defer path in a way
this fix changes, since `ENABLE_ADVENTURE_ROUTING` is OFF by default everywhere except
`simq_routing_test`, per `INFRA-237`'s own `support_boundary` note).

## Test execution order (scoped, per project Testing Rule — no full-suite run)

```
pytest tests/simulation_quality/test_agency_scorer.py -v
pytest tests/simulation_quality/test_timegate_penalties.py -v
pytest tests/simulation_quality/test_grade_regression.py -v -m "not slow"
pytest tests/simulation_quality/test_quality_hub_integration.py -v
pytest tests/integration/domains/adventure/ tests/unit/domains/adventure/ tests/perf/test_phase3_adventure_decision_budget.py -v
pytest tests/unit/observability/test_event_extractor_agency.py tests/unit/observability/test_event_extractor_agency2.py tests/unit/social/test_party_agency.py -v
make evaluate --dry-run
```

## Governance Decision — AC6 Per-Seed Exception (Resolved, Recorded in Step 8)

**This was originally raised as an open question in an earlier draft of this plan. It is now
resolved by explicit governance decision (not re-litigated by this ticket) and implemented via
Step 8 above.** The reasoning below is retained as the evidentiary basis for that decision.

**AC6's literal target ("AGENCY ≥ B confirmed for all three `simq_routing_test` seeds") cannot be
met for seed456 within this ticket's authorized scope, and this is a mathematical consequence of
fixed data, not a cap-tuning failure.**

Evidence: entity 23 genuinely, legitimately emits 491 `defer_with_reason` events over the 500-tick
run (investigation §2.1 — confirmed not a bug). `defer_idle = -1.0` is a flat per-event weight
applied to **every** such event regardless of streak state, and is explicitly **not** one of the two
defects this ticket is authorized to fix (DECIDED items 1-2 name only the attribution and the
escalation-term cap). Entities 24+25 contribute a fixed `+210` raw budget. Therefore
`entity23_total >= -491` unconditionally (the escalation term can only subtract further, never add
back), giving `total <= -281` at best-case-zero-escalation, `normalized <= -0.562` — inside the
**D** bracket and **31 raw points short of even C** (`C` needs `> -460`; base alone is `-491`),
**before any escalation penalty is added at all.** No choice of cap value or shape changes this
ceiling; only reducing `defer_idle` itself, or changing the population-tick-based normalization
denominator to something per-entity, could reach `C`/`B` — both of which are explicitly outside
DECIDED items 1-2 and would be new scope, not a Plan-phase cap-calibration decision.

This is not a new discovery invented here — `docs/simulation_quality/eval_matrix_results.md:369`
already anticipated exactly this possibility in its own AC6 note: "...underlying stasis dynamic
**or revisit this gate's definition**." This plan implements the "fix the underlying stasis dynamic"
half fully (attribution + bounded magnitude, landing at a real, honest, no-longer-F grade of `D`);
it does **not** unilaterally revisit AC6's gate definition, since that is a product/quality-bar
decision (does a single seed's single legitimately-unlucky entity get to define the whole world's
minimum acceptable grade band, or should AC6 be scoped per-entity / amended / given a documented
exception for this specific seed+world combination?) — genuinely requiring a human call, not
something inferable from the investigation's evidence alone.

**Decision adopted (governance-decided, implemented in Step 8)**: "`AGENCY` grade no longer `F`" (an
explicit, separately-listed AC bullet, fully satisfiable and satisfied by this plan) is the binding
acceptance bar for this ticket. AC6's cross-seed `>= B` gate is amended/annotated with an explicit,
evidenced exception for `simq_routing_test_seed456` (analogous to how `INFRA-237`/the Cross-World
Design Note already document an "archetype-correct" exception for `AGENCY=C` in non-routing worlds)
rather than chasing a numeric target that the fixed input data make structurally unreachable without
touching `defer_idle` or the normalization denominator — see Step 8 for the concrete doc/ticket edits
that record this.

## Files Changed (anticipated)

- `src/simulation_quality/scorers/agency.py` — per-entity streak dicts, reset calls, capped
  one-shot escalation
- `config/simulation_quality/detection_params.yaml` — new `stasis_extra_ticks_cap: 5` time-gate
- `docs/simulation_quality/quality_scoring_contract.md` — pseudocode (441-455) + AGENCY table row
  (556) + loop-signal clarifying note
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-237` text/divergence_note update
- `tests/simulation_quality/test_agency_scorer.py` — `TestDefer` rewrites + new bounding tests
- `tests/simulation_quality/test_timegate_penalties.py` — stasis test rewrites + rename
- `tests/simulation_quality/fixtures/grade_anchors.json` — `simq_routing_test_seed456_500t.AGENCY`
  `"D"` (placeholder) → `"D"` (real, post-fix) or whatever the live re-run confirms
- `tickets/todos/TCK-20260704-SIMQ-ROUTING-TEST-HOMETOWN-RESOURCE-GAP.md` — new standalone follow-up
- `docs/simulation_quality/eval_matrix_results.md` — Step 8: new dated status paragraph under
  `## AC6 — AGENCY Confirmation`; new "Second exception class" subsection under
  `## AGENCY — Cross-World Design Note`
- `tickets/inprogress/TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE.md` — Step 8: Acceptance Criteria
  bullet split (AGENCY-no-longer-F vs. documented AC6 exception)
- `docs/plans/audit_fix_plan.md` — Step 8: parenthetical annotation on the `P0-A` summary-table row
  (line 566) noting seed456's documented D-grade exception

## Deviations (filled during implementation)

None material. The live re-run of `simq_routing_test` seed456 (500t) matched the plan's
hand-computed prediction exactly: `AGENCY grade=D, norm=-0.5920` against the predicted `-0.592`
(the tiny 0.0000 delta is float display rounding, not a computational discrepancy — entities
24/25's exact event timing did not shift the entity23-dominated total in any observable way for
this run). seed42 (`AGENCY=A, norm=+1.4207`) and seed123 (`AGENCY=A, norm=+0.6415`) were confirmed
live, unaffected, per Step 6.

`tests/simulation_quality/fixtures/grade_anchors.json`'s `simq_routing_test_seed456_500t.AGENCY`
value required no edit — it already read `"D"` (recorded as the schema-floor placeholder for `F`
by the prior STONE-GAP ticket), and the live-recomputed real grade is also `"D"`, so the string is
unchanged; only its documented *meaning* changes (floor-placeholder-for-F → real post-fix grade).
This is called out explicitly in the ticket's Files Changed / Completion Summary per this section's
own instruction, so a future reader does not confuse the two "D"s.

One citation nit was found and fixed during implementation (not a plan defect requiring
re-architecture-review, just a factual correction): Step 2's reasoning bullet cited
"`COGNITION/INFORMATION.belief_system_dormant=-15.0`" as if both pillars shared one key name.
Confirmed via `config/simulation_quality/scoring_weights.yaml`: `COGNITION` uses
`belief_system_dormant`, `INFORMATION` uses the distinct key `belief_system_silent` (both -15.0,
same "gone quiet" severity tier, different names). Corrected in Step 2's bullet above; no other
plan content depended on the wrong name (the AGENCY table row edit in Step 3 does not cite either
key).
