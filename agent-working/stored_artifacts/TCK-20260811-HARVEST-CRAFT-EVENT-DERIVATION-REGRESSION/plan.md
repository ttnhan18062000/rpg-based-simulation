---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION
artifact_type: plan
tags: [economy, adventure]
---

# Implementation Plan — TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION

## Summary

This is a test-gap fix, not a source-code fix. Investigation confirmed (and this plan
independently re-verified against live source, see citations in each step) that
`src/observability/event_extractor.py`'s legacy ECONOMY `intent_results` loop
(`event_extractor.py:684`) is intentionally dead by default since the disclosed
`TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION` migration (commit `11b83f37`), and that live
`resource_harvested`/`item_crafted` derivation now lives in `EconomyShaper.shape()`
(`src/observability/event_shapers.py:377-471`), delivered every real tick by
`Kernel._phase_observability()` (`src/engine/kernel.py:914,929-936`) via `run_shadow_shapers()`
(`event_shapers.py:1886-1912`). `tests/integration/domains/adventure/test_harvest_to_event.py`'s 2
tests call only `EventExtractor.extract()` and were never updated at the cutover to also call
`run_shadow_shapers()`, so they exercise a permanently-empty rollback branch. The fix: add one
import and one call+merge line to each test, mirroring `Kernel._phase_observability()`'s own real
call sequence exactly. No production source file changes. In parallel, correct one stale prose
line in the P0 parity-ledger entry `STRAT-246` that pre-dates the cutover and still claims the live
pipeline terminates in `event_extractor.py`.

## Steps

### Step 1 — Add `run_shadow_shapers` import to the test file
**Files:** `tests/integration/domains/adventure/test_harvest_to_event.py`
**Change:** Add `from src.observability.event_shapers import run_shadow_shapers` to the module-level
import block (alongside the existing `from src.observability.event_extractor import EventExtractor`
and `from src.observability.config import ObservabilityMode`, currently at lines 35-36). Verified
`run_shadow_shapers`'s exact signature at `src/observability/event_shapers.py:1886-1891`:
`run_shadow_shapers(prior_state: AuthoritativeState, update: StateUpdate, tick: int, mode:
ObservabilityMode = ObservabilityMode.LIGHT) -> List[SimulationEvent]` — positional-compatible with
the call this plan adds in Steps 2 and 3.
**Do NOT touch:** Any other import in the file, the module docstring (lines 1-25), or the two
`ActionIntent`/`ObjectiveKind` construction blocks.
**Verify:** File still parses/imports cleanly — implicitly verified by Step 2/3's test runs (an
import error would fail both tests immediately).

### Step 2 — Fix `test_crafting_project_produces_item_crafted_event_through_full_pipeline`
**Files:** `tests/integration/domains/adventure/test_harvest_to_event.py` (lines 75-82, current line
numbers per this plan's read of the file)
**Change:** Between the existing `events = EventExtractor.extract(state, state, resolved_update,
mode=ObservabilityMode.LIGHT)` call and the `event_types = {e.event_type for e in events}` line,
insert:
```python
events += run_shadow_shapers(state, resolved_update, tick=state.tick, mode=ObservabilityMode.LIGHT)
```
This mirrors `Kernel._phase_observability()`'s own real call sequence
(`src/engine/kernel.py:914` `generated_events = EventExtractor.extract(prior_state, self._state,
update, obs_mode)`, then `kernel.py:934` `shaper_events = run_shadow_shapers(prior_state, update,
tick, obs_mode)`, then `kernel.py:936` `generated_events.extend(shaper_events)` when the push-shaper
mode is `"ON"`) — same two calls, same merge, same source (`prior_state`/`update` = this test's own
`state`/`resolved_update`), same `tick` derivation (`kernel.py:911` `tick = self._state.tick`, this
test's `state.tick == 10`). No `reset_run_state()` call is needed for `EconomyShaper` before or
after this call: read the full class body at `event_shapers.py:359-471` and confirmed via `grep -n
"def reset_run_state" src/observability/event_shapers.py` that `reset_run_state` is defined only at
lines 507, 724, 973, and 1467 — all outside `EconomyShaper`'s own 359-471 range (those belong to
other shaper classes further down the file, e.g. `FactionShaper` at line 474+). `EconomyShaper.shape()`
(`event_shapers.py:377-383`) reads only its own `prior_state`/`update` arguments per call, no class-
or instance-level accumulator — confirmed stateless directly from the method body, not inferred from
its docstring. The existing `EventExtractor.reset_run_state()` call earlier in the test (unchanged,
still needed for `EventExtractor`'s own stateful KILL-event tracking) is untouched.
**Other writers to this shared call path:** `run_shadow_shapers()` is also invoked, with the same
signature, from `Kernel._phase_observability()` on every real tick (`kernel.py:934`) and from no
other test in the sweep this ticket's investigation performed (16 `EventExtractor.extract()` call
sites checked, none of the other 15 call `run_shadow_shapers()` today). Adding this call in this one
test does not create any double-delivery or ordering conflict: this test never touches durable world
state or the real kernel loop, `run_shadow_shapers()` only *constructs* a list of `SimulationEvent`
objects from the same `resolved_update` already in scope, and the merge (`events += ...`) is
append-only into a local list that ceases to exist at test-function exit — no shared registry,
counter, or file is written.
**Do NOT touch:** The construction of `hero`, `recipe`, `intent`, `adapter_updates`, or
`resolved_update` above this point (all confirmed correct — the test's own assertion on
`resolved_update.entity_updates[hero.id].intent_results` already passes today, only the derived-event
assertion fails). Do not change the `assert "item_crafted" in event_types` line's expected string or
add any new assertion.
**Verify:** `.venv/bin/python3 -m pytest
tests/integration/domains/adventure/test_harvest_to_event.py::test_crafting_project_produces_item_crafted_event_through_full_pipeline
-v` passes.

### Step 3 — Fix `test_reach_resource_arrival_produces_resource_harvested_event_through_full_pipeline`
**Files:** `tests/integration/domains/adventure/test_harvest_to_event.py` (lines 130-137, current
line numbers per this plan's read of the file)
**Change:** Identical pattern to Step 2, applied to this test's own `state`/`resolved_update`
(the NODE/harvest scenario, built from `ResourceNodeState(id=501, ...)` and a `HARVEST_RESOURCE`
`ActionIntent`, resolved through `InteractionSystem.enforce()` then
`ResourceTransactionSystem.resolve_all()`). Insert, between the existing `EventExtractor.extract(...)`
call and `event_types = {...}`:
```python
events += run_shadow_shapers(state, resolved_update, tick=state.tick, mode=ObservabilityMode.LIGHT)
```
Same signature/verification/statelessness citations as Step 2 apply (same `run_shadow_shapers`
function, same `EconomyShaper.shape()` NODE branch at `event_shapers.py:400-406`, independently
verified during investigation against a real, non-`MagicMock` `ActionIntentAdapter.execute()` →
`InteractionSystem.enforce()` → `ResourceTransactionSystem.resolve_all()` chain, not just the
crafting scenario).
**Other writers to this shared call path:** Same analysis as Step 2 — no additional writer, no
double-delivery risk, purely local list construction.
**Do NOT touch:** The `hero`/`node`/`state`/`intent` construction, the `InteractionSystem.enforce()`
call, or the `resolved_update.entity_updates[hero.id].intent_results` assertion above the event-
derivation block. Do not change the `assert "resource_harvested" in event_types` line.
**Verify:** `.venv/bin/python3 -m pytest
tests/integration/domains/adventure/test_harvest_to_event.py::test_reach_resource_arrival_produces_resource_harvested_event_through_full_pipeline
-v` passes.

### Step 4 — Correct stale `support_boundary` prose on `STRAT-246`
**Files:** `docs/parity_ledger/strategic_cognition.yaml`
**Change:** Investigation's Docs-Requiring-Update section attributed this staleness to the entry's
`v2_evidence` field; re-reading the entry directly (`strategic_cognition.yaml:2955-3033`) shows the
stale sentence is actually in the **`support_boundary`** field, not `v2_evidence` — `v2_evidence`
(lines 2963-2988) describes the `TCK-20260713-SIMQ-ECONOMY-INTENT-GENERATION-GAP` and
`TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION` fixes accurately and does not claim a
pipeline terminus. The stale claim is in `support_boundary` (line ~3009-3010): "...reachability
itself (this entry's text) is proven at the unit/integration level (test_path above) via direct,
real-pipeline-component construction (ActionIntentAdapter.execute() ->
ResourceTransactionSystem.resolve_all() -> event_extractor.py, no mocks)." This pre-dates the
2026-08-06 push-shaper cutover and no longer reflects the live derivation terminus. Correct it to:
"...via direct, real-pipeline-component construction (ActionIntentAdapter.execute() ->
ResourceTransactionSystem.resolve_all() -> EventExtractor.extract() + run_shadow_shapers()'s
EconomyShaper, no mocks; event_extractor.py's own legacy ECONOMY loop is the flag-gated rollback
path as of TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION, not the live terminus)." Keep every
other sentence in `support_boundary` (the three empirically-isolated out-of-scope factors) unchanged
— they remain accurate and unaffected by this ticket.
**Other writers to this shared resource:** `docs/parity_ledger/strategic_cognition.yaml` is a shared,
actively-edited registry file — `git log --oneline -3` on it shows 3 other tickets
(`TCK-20260811-CAPABILITY-CONFIDENCE-ADVENTURE-SCORING`, `TCK-20260811-MEMORY-INFORMED-ROUTE-SCORING`,
`TCK-20260811-REGION-STABILIZATION-GOAL-SCORER`) committed edits to it within the last 3 commits
touching the file, each adding/editing their own unrelated entries. No ticket currently in
`tickets/inprogress/` references `strategic_cognition.yaml` (checked via
`grep -rl "strategic_cognition.yaml" tickets/inprogress/`), so there is no live concurrent-edit
conflict at plan time, but the implementer must edit **only** the `STRAT-246` entry's
`support_boundary` field — do not reformat, reflow, or touch any other entry's block-scalar
indentation in the same file (a YAML block-scalar reflow of an unrelated entry would show as a
spurious diff in an unrelated ticket's history).
**Do NOT touch:** `STRAT-246`'s `status` (`verified`, stays `verified` — the underlying mechanics
this ledger entry tracks did not become divergent), `priority` (`P0`, unchanged), `test_path`
(already correct — both cited tests will pass once Steps 2-3 land, no edit needed), `proof_type`, or
`divergence_note`. Do NOT edit `STRAT-189` at all — its own `support_boundary` (lines 2085-2096) does
not contain the stale pipeline-terminus claim (confirmed by direct read); it only cross-references
"See STRAT-246 for full detail," which remains correct.
**Verify:** `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/strategic_cognition.yaml'))"`
parses without error (confirms no YAML block-scalar indentation break from the edit); manual diff
review confirms only `STRAT-246`'s `support_boundary` block changed.

### Step 5 — Verify (test fix + parity-ledger P0 restoration)
**Files:** None changed; verification only.
**Change:** N/A.
**Do NOT touch:** N/A.
**Verify:** Run, in order:
1. `.venv/bin/python3 -m pytest tests/integration/domains/adventure/test_harvest_to_event.py -v`
   — both tests pass (this ticket's direct AC3 target).
2. `.venv/bin/python3 -m pytest tests/unit/observability/ -q` — full observability regression
   surface stays green, including `test_event_shapers_economy_faction.py::test_resource_harvested`
   and `::test_item_crafted` (the shaper ground truth, confirmed present at
   `tests/unit/observability/test_event_shapers_economy_faction.py:49,55`) and the 13 `MagicMock`-
   based `test_event_extractor_*.py` files (must stay passing **unmodified** — they are out of
   scope, see Scope Guards).
3. `.venv/bin/python3 -m pytest tests/unit/domains/adventure/
   tests/unit/tactical/test_objective_pursuit_coverage.py tests/integrity/test_logic_guards.py -q`
   — the full `STRAT-189`/`STRAT-246` `test_path` set (per both entries' own `test_path` fields,
   re-read at `strategic_cognition.yaml:2077-2081` and `:2996-3003`) passes, which is the direct
   verification that both P0 parity-ledger violations identified in investigation.md are resolved,
   not just that the 2 harvest/craft tests are green in isolation.
4. `.venv/bin/python3 -m pytest tests/simulation_quality/test_economy_scorer.py
   tests/simulation_quality/test_timegate_penalties.py
   tests/simulation_quality/test_scenario_coverage.py -q` — SimQ scorer-level contract sanity check
   (unaffected; these test scorers against synthetic fixtures, never through `EventExtractor`/
   shapers).
5. `.venv/bin/python3 -m pytest tests/integration/scenarios/test_phase5_information_belief_scenarios.py -q`
   — adjacent sanity check (asserts only `belief_assimilated`, never gated by
   `_push_shapers_active`).
Record the AC4 (SimQ/corpus blast-radius) finding in the ticket's own Implementation Notes at
Finalize: `docs/simulation_quality/event_type_coverage.md` (lines 109-110, re-read this session)
already shows `resource_harvested`/`item_crafted` at `0` corpus-wide hits, and `STRAT-246`'s own
`support_boundary` independently attributes that `0` to three empirically-isolated, already-tracked,
out-of-scope routing/calibration factors (`ENABLE_ADVENTURE_ROUTING` default-off,
`AdventureRouteScorer` route competition, closed by `TCK-20260714-...`) — not to this test's dead
call pattern, since `EconomyShaper.shape()` was never broken and was always reachable via the real
kernel loop. **This ticket's regression therefore has zero additional corpus/SimQ blast radius
beyond the 2 broken P0 test_path guarantees fixed in Steps 2-4** — direct evidence, not assumed.

## Design Decisions

**AC1 ("real regression-introducing commit identified via git bisect... not assumed") — satisfied
as written, no reinterpretation needed.** Investigation performed a real bisection
(`git log --oneline -S "_push_shapers_active" -- src/observability/event_extractor.py` and
`git log --oneline 90794a76..HEAD -- src/observability/event_extractor.py
src/observability/event_shapers.py`, both independently resolving to the same single commit,
`11b83f37`) and this plan did not re-derive that finding from scratch, only re-verified the source
citations it depends on (`event_extractor.py:133-134,678-684`, `event_shapers.py:377-471,1886-1912`,
`kernel.py:911-943`) directly against current HEAD. `11b83f37` is real and identified — AC1 does not
require the commit to be a "bug commit," only that it be the real, bisected origin, which it is.

**AC2 ("root cause fixed in the actual pipeline stage responsible, not routed around") —
reinterpreted, evidence cited.** The ticket's own wording anticipates a source-code fix, but the
confirmed root cause (investigation.md Central Finding, re-verified in Steps 1-3 above) is that the
2 tests never invoke the actual pipeline stage responsible for derivation post-cutover
(`EconomyShaper.shape()` via `run_shadow_shapers()`) — they invoke only the now-dormant rollback
stage. "Routing around" the root cause would mean either (a) resurrecting the dead
`event_extractor.py` legacy loop (explicitly forbidden, investigation.md Anti-Drift Hazards — this
would reintroduce the double-fire risk the shaper-registry pattern was built to prevent), or (b)
weakening the test assertion to pass without exercising real derivation. This plan does neither: it
makes the tests invoke the actual, currently-live pipeline stage, with the exact call pattern
production itself uses (`Kernel._phase_observability()`, `kernel.py:914,933-936`). This satisfies
AC2's intent — fixing the root cause at the stage genuinely responsible — without a source change,
because the pipeline stage itself was never broken; only the tests' visibility into it was.

**Tier note (for the record, not acted on).** Given the confirmed root cause is a 2-line test-call-
pattern fix plus one parity-ledger prose correction — no source-code change, no architecture
question — a `hotfix`-tier pipeline (Scope → Implement → Test → Parity → Verify → Finalize) would
likely have sufficed had the ticket been scoped this way from the start. The ticket is already
mid-pipeline as `standard` tier; this plan does not unilaterally downgrade it. Continue as `standard`
tier through Review/Architecture-Verify as already scoped.

**Doc/parity update scope decision.** Fix `STRAT-246`'s stale `support_boundary` prose (Step 4) in
this same session: it is small, low-risk, and the same file this ticket must already touch to
confirm the P0 `test_path` restoration — deferring it would leave doc/code parity broken even after
the tests pass. Do **not** fold in `docs/simulation_quality/event_type_coverage.md`'s stale `source`
column (lines 109-110, listing `event_extractor` for all ECONOMY rows) into this ticket: that
staleness pre-dates this ticket, was already flagged-not-fixed twice by prior tickets in the same
migration family (`TCK-20260807-QUEST-EVENT-PUSH-MIGRATION`'s own investigation, per
investigation.md's Prior Work section), and fixing it here would require touching every migrated
event row (COMBAT/FACTION/QUEST/AGENCY, not just the 2 ECONOMY rows this ticket cares about) —
out of this ticket's narrow scope. Leave as a candidate future doc-sweep ticket, matching precedent.
Do **not** add the optional `test_event_extractor_alone_does_not_prove_production_event_delivery`
architecture-guard test test_plan.md flagged as a possibility: it is explicitly optional, and adding
new test mechanism exceeds the ticket's own Out-of-Scope line ("any change to
`test_harvest_to_event.py` itself beyond what's needed to keep it passing post-fix").

## Scope Guards

- **No change to `src/observability/event_extractor.py`** — confirmed correct as-is; its legacy
  ECONOMY loop and `_push_shapers_active` gate are the intentional rollback path, not a bug.
- **No change to `src/observability/event_shapers.py`** — `EconomyShaper.shape()`, `SHAPER_REGISTRY`,
  and `run_shadow_shapers()` are confirmed correct as-is; do not add a `reset_run_state()` method to
  `EconomyShaper` (confirmed genuinely stateless, no state to reset).
- **No change to `src/engine/kernel.py`** — `_phase_observability()`'s own call sequence is the
  pattern this plan's test fix mirrors, not a file this ticket touches.
- **No change to any of the 13 `MagicMock`-based `test_event_extractor_*.py` files** — they
  accidentally exercise the rollback path (still legitimate, still correct) and are a separate,
  pre-existing test-quality gap (zero real coverage of the production shaper path), explicitly
  out of scope for this ticket per investigation.md's Anti-Drift Hazards.
- **No change to any other real-state (`non-MagicMock`) test asserting on a shaper-migrated ECONOMY
  event type beyond the 2 named in this ticket** — investigation's sweep of all 16
  `EventExtractor.extract()` call sites in `tests/` found no other real-state caller of any
  ECONOMY-domain event type (`resource_harvested`, `item_crafted`, `shop_transaction`,
  `trade_executed`, `quest_reward_dispensed`, `gold_sink_fired`, `paid_information_transaction`,
  `paid_info_transaction`, `paid_info_changed_goal`). This scope boundary is confirmed, not
  reopened by this plan — if Implement independently discovers a 17th call site during this
  ticket's work that was missed by the sweep, treat it as a second instance of the same gap class
  (test_plan.md's own Anti-Drift Test Guards) and flag it rather than silently expanding this
  ticket's diff.
- **No `status`, `priority`, `proof_type`, `divergence_note`, or `test_path` field changes** in
  `STRAT-189` or `STRAT-246` — only `STRAT-246`'s `support_boundary` prose changes (Step 4). No edit
  to `STRAT-189` at all.
- **No edit to `docs/parity_ledger/town_resource.yaml::TOWN-190`** — its own `test_path`
  (`test_event_shapers_economy_faction.py`) is unaffected by this ticket and requires no change.
- **No edit to `docs/simulation_quality/event_type_coverage.md`** — deferred, see Design Decisions.
- **No new test files, no new test functions, no new architecture-guard mechanism** — only the 2
  existing test bodies' derivation-assertion block changes (Steps 2-3), nothing else in the file.
- **No change to `test_harvest_to_event.py`'s module docstring, entity/state construction code, or
  the first three pipeline-stage calls/assertions in either test** (`ActionIntentAdapter.execute()`,
  `InteractionSystem.enforce()`, `ResourceTransactionSystem.resolve_all()`, and the
  `intent_results` truthiness assertion) — all confirmed already passing and correct.

## Dependency Map

- Step 1 (import) must land before Step 2 and Step 3 (both reference `run_shadow_shapers`), but Step
  1 is a single-line addition with no independent test of its own — verify it together with Step 2
  or Step 3's first run (an import error surfaces immediately).
- Step 2 and Step 3 are independent of each other (different test functions, same file, non-
  overlapping line ranges) — either can be implemented and verified first.
- Step 4 (parity-ledger doc edit) is fully independent of Steps 1-3 — different file, no code
  dependency — but its own Verify step (re-running the `STRAT-189`/`STRAT-246` `test_path` test
  set) is only meaningful once Steps 2-3 have landed, since those tests are what the parity claim
  depends on.
- Step 5 (Verify) depends on all of Steps 1-4 being complete.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: Real regression-introducing commit identified via `git bisect`, not assumed | Already satisfied by investigation.md (commit `11b83f37`); this plan re-verified the source citations it rests on, no new step required | N/A — evidentiary, not test-verified; see investigation.md Bisection section |
| AC2: Root cause fixed in the actual pipeline stage responsible, not routed around | Steps 1-3 (reinterpreted per Design Decisions: the fix routes the tests through the actual live derivation stage, `EconomyShaper` via `run_shadow_shapers()`, matching production's own call pattern) | `test_harvest_to_event.py` both tests (Step 5.1) |
| AC3: Both `test_harvest_to_event.py` tests pass | Steps 1, 2, 3 | `.venv/bin/python3 -m pytest tests/integration/domains/adventure/test_harvest_to_event.py -v` (Step 5.1) |
| AC4: SimQ/corpus blast-radius question answered with direct evidence, not assumed | Answered directly in Step 5's Verify text, citing `event_type_coverage.md:109-110` and `STRAT-246`'s `support_boundary` — zero additional blast radius beyond the 2 P0 `test_path` violations | No test — evidentiary; recorded in ticket's Implementation Notes at Finalize per Step 5 |

## Anti-Drift Notes

- **Never resurrect `event_extractor.py`'s legacy ECONOMY loop or flip `_push_shapers_active`'s
  default.** The correct fix is exclusively on the test side (Steps 1-3); doing anything to
  `event_extractor.py` or `event_shapers.py` reintroduces the double-fire risk the shaper-registry
  pattern was built to prevent — this is the single highest-consequence mistake this plan guards
  against, called out identically in investigation.md's Anti-Drift Hazards and test_plan.md's
  Anti-Drift Test Guards.
- **`EconomyShaper` is one of 4 independently-gated shaper families** (`_push_shapers_active` for
  ECONOMY/COMBAT/FACTION Phase 1; `_push_shapers_phase2_active`, `_push_shapers_quest_active`,
  `_push_shapers_agency_active` for the others) — this ticket's fix pattern (call
  `run_shadow_shapers()` alongside `EventExtractor.extract()`) is specific to Phase 1's
  unconditional construction inside `run_shadow_shapers()` (`event_shapers.py:1910-1912`, iterates
  `SHAPER_REGISTRY` with no secondary gate). Do not assume this generalizes automatically to a
  Phase 2/Quest/Agency-domain test without re-checking that domain's own gating.
  `run_shadow_shapers()` itself already handles the Phase 2/Quest/Agency gating internally
  (`event_shapers.py:1914-1925`+), so the same one-line call in Steps 2-3 is sufficient for this
  ticket's ECONOMY-only scope — but a future ticket fixing a different domain's stale test must
  re-verify its own flag's default and gating location rather than copy this pattern blindly.
- **The 13 `MagicMock`-based `test_event_extractor_*.py` files are a real, separate, pre-existing
  test-quality gap** (zero coverage of the production shaper delivery path — they accidentally
  exercise only the rollback branch because `MagicMock() == "ON"` is `False`). This ticket does not
  fix that gap; it is explicitly out of scope. Whoever next touches `event_extractor.py`'s test
  suite should be pointed at this finding.
- **`STRAT-189`'s `support_boundary` is correct as-is and must not be edited** — only `STRAT-246`'s
  is stale. Conflating the two (e.g. applying Step 4's edit to both entries) would introduce an
  incorrect duplicate edit; re-read both entries' current text before editing, do not pattern-match
  off one to infer the other needs the same change.
- **`docs/parity_ledger/strategic_cognition.yaml` is a large, actively-shared file other tickets
  append entries to in parallel sessions** (3 other `TCK-20260811-*` tickets touched it in the last
  3 commits alone) — Step 4's diff must be scoped to exactly the `support_boundary` sentence being
  corrected, nothing else in the file, to avoid an unrelated-looking diff blocking or confusing a
  concurrent ticket's own review.
