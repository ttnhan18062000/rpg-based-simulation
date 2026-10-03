---
status: historical
layer: economy
authority: P2
audience: agent
ticket_id: TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION
artifact_type: investigation
tags: [economy, adventure]
---

# Investigation — TCK-20260811-HARVEST-CRAFT-EVENT-DERIVATION-REGRESSION

## Central Finding

**The ticket's own Scope-phase hypothesis is CONFIRMED with full rigor: this is a stale-test gap
from an intentional, disclosed architecture migration (`TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-
FACTION`), not a source-code regression.** Production `resource_harvested`/`item_crafted` event
derivation is intact and correct today — it lives in `EconomyShaper.shape()`
(`src/observability/event_shapers.py:377-469`), delivered live by `Kernel._phase_observability()`
(`src/engine/kernel.py:916-943`). `tests/integration/domains/adventure/test_harvest_to_event.py`'s
2 tests call only `EventExtractor.extract()`, never `run_shadow_shapers()`, so they exercise a code
path (`event_extractor.py`'s legacy `intent_results` loop) that has been the *rollback* path, not
the live path, since 2026-08-08 (commit `11b83f37`) — with `ENABLE_PUSH_EVENT_SHAPERS` defaulting
`"ON"`, that loop's guard `[] if _push_shapers_active else (...)` makes it permanently empty
(`event_extractor.py:684`) under real state. The test file itself has never been edited since its
creation at `90794a76` (confirmed: `git log --oneline 90794a76..HEAD --
tests/integration/domains/adventure/test_harvest_to_event.py` returns nothing) — it was simply
never updated to route through the shaper when the cutover landed.

## Current Behavior

### `src/observability/event_extractor.py`

- Line 133-134: `_push_shapers_active = (getattr(prior_state, "feature_flags", None) or {}).get(
  "ENABLE_PUSH_EVENT_SHAPERS", "ON") == "ON"`. With a real `AuthoritativeState` (the dataclass used
  by both failing tests, `src/core/state.py`), `feature_flags` is absent/empty, so the `or {}`
  fallback + `.get(..., "ON")` default resolves `_push_shapers_active = True`.
- Line 678-684: the ECONOMY `intent_results` loop (`resource_harvested`, `item_crafted`,
  `shop_transaction`, `trade_executed`, `quest_reward_dispensed`, `gold_sink_fired`,
  `paid_information_transaction`, `paid_info_transaction`, `paid_info_changed_goal`) is guarded:
  `for ir in ([] if _push_shapers_active else (getattr(e_upd_ext, "intent_results", None) or [])):`
  — when `_push_shapers_active` is `True` (the default), this iterates an empty list. **Confirmed
  genuinely unreachable** under default config with real state — this is not a partial-condition
  branch, the entire ECONOMY block is dead code by default, exactly as `docs/parity_ledger/
  town_resource.yaml::TOWN-190`'s own text states ("the entire loop could be guarded as one unit").
- The code comment at lines 678-683 explicitly documents this: "Flag-gated
  (TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION): live behind EconomyShaper when
  ENABLE_PUSH_EVENT_SHAPERS is 'ON' (default); this loop is the rollback path when it isn't."

### `src/observability/event_shapers.py`

- `EconomyShaper.shape()` (line 359-469, class starts 359, method 377): reads
  `update.entity_updates[eid].intent_results` (same typed records the legacy loop read), filters
  `accepted=True`, and switches on `source_kind`. Confirmed both branches this ticket's 2 tests
  need:
  - `source_kind == "NODE"` → `resource_harvested` (line 400-406), payload `node_id`.
  - `source_kind == "CRAFTING"` → `item_crafted` (line 407-413), payload `source_id`.
  - Also handles `SHOP_BUY`/`SHOP_SELL` → `shop_transaction`+`trade_executed`, `QUEST` →
    `quest_reward_dispensed`, `REPAIR_FEE`/`SERVICE_FEE`/`TAX` → `gold_sink_fired`,
    `INFORMATION_PURCHASE` → `paid_information_transaction`+`paid_info_transaction`(+
    `paid_info_changed_goal` when `prior_state` shows a project switch) — a 1:1 branch mapping to
    the legacy loop, confirmed by direct comparison of both code blocks.
- `SHAPER_REGISTRY` (line 944-948): `"economy": [EconomyShaper()]`.
- `run_shadow_shapers()` (line 1886-1912+): iterates `SHAPER_REGISTRY` (Phase 1, unconditionally
  constructed — economy is Phase 1, not gated by any secondary flag inside this function) plus
  Phase2/Quest/Agency registries gated by their own flags. Called by `Kernel._phase_observability()`
  only when the outer `ENABLE_PUSH_EVENT_SHAPERS` mode is `"ON"` or `"SHADOW"`
  (`kernel.py:929-931`).

**Two independent scratch verifications performed** (real, non-mocked `AuthoritativeState`/
`StateUpdate`/`IntentResult` objects, not the ticket's original hand-built scenario alone):
1. CRAFTING case (mirrors the exact `resolved_update` `test_crafting_project_produces_item_crafted
   _event_through_full_pipeline` builds): `EconomyShaper().shape(state, resolved_update, tick=10)`
   → `item_crafted` present. (Re-confirmed this session, matches the Scope-phase finding.)
2. **NODE/harvest case (independently verified this session, was NOT previously checked)**: built a
   real hero + `ResourceNodeState`, ran `ActionIntentAdapter.execute(HARVEST_RESOURCE)` →
   `InteractionSystem.enforce()` → `ResourceTransactionSystem.resolve_all()` → confirmed
   `intent_results = [IntentResult(accepted=True, source_kind='NODE', source_id=501)]` →
   `EconomyShaper().shape(state, resolved_update, tick=10)` → `resource_harvested` present. Both
   ECONOMY branches this ticket's failing tests need are proven correct in the live shaper.
3. **Full fix-pattern sketch verified**: calling `EventExtractor.extract(...) +
   run_shadow_shapers(state, resolved_update, tick=10, mode=ObservabilityMode.LIGHT)` (mirroring
   `Kernel._phase_observability()`'s own call sequence, `kernel.py:914,933-936`) on the crafting
   scenario yields `{'item_crafted'}` — the exact assertion the test needs, with the exact call
   pattern production itself uses.

### `src/engine/kernel.py` — `_phase_observability()` (line 902-943+)

- Line 914: `generated_events = EventExtractor.extract(prior_state, self._state, update, obs_mode)`.
- Line 929-936: reads `ENABLE_PUSH_EVENT_SHAPERS` (default `"ON"`) directly off
  `prior_state.feature_flags`; when `"ON"` or `"SHADOW"`, calls `run_shadow_shapers(prior_state,
  update, tick, obs_mode)`; when mode is `"ON"`, `generated_events.extend(shaper_events)` —
  i.e. **both** `EventExtractor.extract()` and `run_shadow_shapers()` are called, and their outputs
  are merged, on every real tick. **Confirmed this is the only call site in the real pipeline that
  invokes both together** — `EventExtractor.extract()` alone (as both failing tests do) is never
  how the real kernel loop derives events.

### Bisection (AC1)

`git log --oneline -S "_push_shapers_active" -- src/observability/event_extractor.py` and
`git log --oneline 90794a76..HEAD -- src/observability/event_extractor.py
src/observability/event_shapers.py` both resolve to the same single commit:
**`11b83f37` — "Batch commit: 43-ticket push-based observability migration epic + linked SimQ/Quest/
Entity-observability/Corpus work"** (2026-08-08 19:58:54 +0700). This commit's own message states
it is a **backlog reconciliation commit**: all 43 tickets (each already independently completed,
tested, and gate-passed earlier in the same session) had their working_log rows committed but their
substantive diffs were never actually committed until this one aggregate commit, "discovered during
`TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION`'s own Finalize step; committed now,
correctly attributed, per explicit user instruction to reconcile the backlog." This is **not** a bug
commit — it is the disclosed, intentional `TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION`
migration (one of the 43), whose own `docs/parity_ledger/town_resource.yaml::TOWN-190` entry
documents the exact cutover this ticket investigates. Only 4 other commits touch either file between
`90794a76` and HEAD, none of which introduce or alter the `_push_shapers_active` gate (`ed76d925`,
`55799620`, `54e8e1a9`, `981ef13b` — all `TCK-20260809-COMBAT-*` combat-lifecycle work, unrelated to
ECONOMY). **AC1's bisect requirement is satisfied**: the regression-introducing commit is real and
identified, but it is a disclosed architecture migration, not a bug — this changes what "root cause
fixed" means for Plan (fix the 2 stale tests' call pattern, not revert or patch source logic).

## Mechanics / Engine Constraints

- `docs/engine/kernel.md` — the 6-phase deterministic loop; observability (Phase 6/Persistence-
  adjacent) must not affect the authoritative tick (Zero Simulation Impact,
  `quality_scoring_contract.md §3.1`, cited directly in `kernel.py:925-928`'s own comment). The
  shaper path is wrapped in `try/except` for this reason — irrelevant to this ticket's fix (test
  changes only) but constrains any future source change to this area.
- No Mechanics Bible chapter governs event *derivation* mechanics directly (observability is
  infrastructure, not simulation law); the authoritative source for this specific migration's
  correctness is the parity ledger entries below, not a Mechanics Bible chapter.

## Docs Requiring Update

- `docs/parity_ledger/strategic_cognition.yaml`: `STRAT-189` and `STRAT-246` (both **P0**) list
  `tests/integration/domains/adventure/test_harvest_to_event.py` in their `test_path` — these are
  currently failing, so both P0 entries currently have a **broken test_path**, a live parity-ledger
  violation per CLAUDE.md's own rule ("P0 entries require a passing test_path"). `STRAT-246`'s
  `v2_evidence` also textually describes the pipeline as terminating in `event_extractor.py`
  ("ActionIntentAdapter.execute() -> ResourceTransactionSystem.resolve_all() -> event_extractor.py,
  no mocks") — written `2026-07-14`, before the `2026-08-06` push-shaper cutover, now stale: in
  production the pipeline terminates in `event_shapers.py`'s `EconomyShaper`, not
  `event_extractor.py`. Once the 2 tests are fixed to route through `run_shadow_shapers()`, both
  entries' `test_path` will pass again, but `STRAT-246`'s `v2_evidence` text should be corrected to
  reflect the real live path (or explicitly note event_extractor.py is now the rollback/dormant
  path) to restore doc/code parity, not just test-green status.
- `docs/simulation_quality/event_type_coverage.md`: the `resource_harvested`/`item_crafted` rows
  (lines 109-110) list `source: event_extractor` — stale post-cutover (real source is now
  `event_shapers`/`EconomyShaper`). This staleness pre-dates this ticket (already flagged, not
  fixed, by `TCK-20260807-QUEST-EVENT-PUSH-MIGRATION`'s own investigation: "its own 'source' column
  is stale for most rows post-Phase-1/2 — flagged, not corrected wholesale here"). Not newly
  introduced by this ticket; Plan should decide whether to fold this correction in (small, low-risk,
  same file already touched by this ticket's own parity work) or leave it for a dedicated doc-sweep
  ticket, matching the precedent set twice already.

## Parity Ledger Overlap

- `docs/parity_ledger/town_resource.yaml::TOWN-190` (**P0**, `status: verified`) — the entry that
  documents the exact cutover (`TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION`) this ticket
  investigates. Its own `test_path` is `tests/unit/observability/test_event_shapers_economy_faction.
  py` (20 tests, currently passing, unaffected by this ticket) — **not**
  `test_harvest_to_event.py`, so this entry is not directly broken, but it is the authoritative
  record of *why* `event_extractor.py`'s loop is dead code by default. No status change needed.
- `docs/parity_ledger/strategic_cognition.yaml::STRAT-189` (**P0**, `status: verified`) — text
  "Objective derivation can create executable objectives." `test_path` includes
  `tests/integration/domains/adventure/test_harvest_to_event.py::test_reach_resource_arrival_produces
  _resource_harvested_event_through_full_pipeline` — **currently broken/failing**, a live P0
  test_path violation.
- `docs/parity_ledger/strategic_cognition.yaml::STRAT-246` (**P0**, `status: verified`) — text
  "Every ObjectiveKind System A ... or System B ... can produce reaches real execution via
  ActionIntentAdapter.execute()." `test_path` includes the whole
  `tests/integration/domains/adventure/test_harvest_to_event.py` file (both tests) —
  **currently broken/failing**, a live P0 test_path violation, and its `v2_evidence` narrative is
  independently stale (see Docs Requiring Update above).
- No `docs/parity_ledger/*.yaml` entry needs a `status` change (nothing is newly `divergent` — the
  underlying mechanics this ledger tracks, "objective reaches real execution," remain true; only the
  *proof test* is broken by a stale call pattern). Once the tests are fixed, `STRAT-189`/`STRAT-246`
  should be re-verified (test_path passes again) rather than re-authored.

## Prior Work

Directly on-point precedent from the same migration family (all found via `search_docs` before any
grep, per CLAUDE.md's hard rule):

- `TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION` (DONE) — the actual migration commit this
  investigation traces to. `stored_artifacts/TCK-20260806-PUSH-CUTOVER-COMBAT-ECONOMY-FACTION/`
  exists for deeper reference if Plan needs it.
- `TCK-20260806-PUSH-SHAPER-ECONOMY-FACTION` (DONE, `INFRA-325`) — built `EconomyShaper`/
  `FactionShaper` themselves (the shader logic this ticket verified is correct).
- `TCK-20260807-QUEST-EVENT-PUSH-MIGRATION` (DONE) — **exact precedent for this ticket's own
  situation**: found `quest_event` still diffing-based/ungated after the same migration wave, due to
  a stale claim in an epic's own closed record, and did a **systematic sweep** of
  `event_extractor.py` for other unmigrated/ungated events per explicit user request — a template
  for this investigation's own Step 4 sweep (see below). Its own "Implementation Notes" set the
  precedent of filing narrow follow-up tickets for other gaps found rather than scope-creeping the
  fix.
- `TCK-20260807-REJECTION-CASCADE-TICK-PUSH-MIGRATION-GAP` (DONE) — one of the follow-ups from the
  above sweep; confirms the sweep methodology (grep `event_extractor.py` for scored events not
  gated by any push-shaper flag) is an established, repeatable pattern in this codebase's history.
- `stored_artifacts/TCK-20260714-SIMQ-HARVEST-RESOURCE-ARRIVAL-TRANSITION/` — the original ticket
  whose own proof-test (`test_harvest_to_event.py`) now fails. Its fix (call-site gating in
  `TacticalDecisionSystem`'s Pillar 5.1, `tactical.py:260-295`) is untouched by this regression —
  confirmed via the same test's own passage of steps 1-3 (only step 4, event derivation, fails).

## Risks and Open Questions

- **Open question for Plan (not decided here)**: should the fix update only the 2 failing tests'
  call pattern (minimal, matches ticket's own "Out of Scope" line), or should it also correct
  `STRAT-246`'s stale `v2_evidence` text and/or `event_type_coverage.md`'s stale `source` column in
  the same session? CLAUDE.md's Authoritative Mechanics Rule requires doc/parity updates "in the
  same session" when logic changes — but no logic is changing here, only a test's call pattern. The
  narrowest reading is: fix the 2 P0 test_path violations (which the test fix alone resolves) and
  leave the `v2_evidence` prose / coverage-doc staleness as optional, precedented-as-deferred
  cleanup. Flagging for Plan to decide explicitly rather than assuming.
- **Confirmed, not open**: whether this is a source regression or test-gap (CONFIRMED test-gap, see
  Central Finding) — Plan should not re-litigate this with a redundant source-side investigation.
- No open question blocks implementation of the test fix itself — the fix pattern was verified
  working (see Current Behavior, bullet 3) before writing this investigation.

## Anti-Drift Hazards

- **Do not "fix" this by re-adding an unconditional/legacy-path economy loop to
  `EventExtractor.extract()`** — that would resurrect the double-fire risk the whole shaper-registry
  pattern was built to avoid (see every migration ticket's own "no double-fire" verification step).
  The correct fix is on the test side: call `run_shadow_shapers()` too, exactly as
  `Kernel._phase_observability()` does.
- **Do not change `EconomyShaper.shape()` or `event_extractor.py`'s gate logic** — both are already
  correct and covered by their own passing unit tests
  (`tests/unit/observability/test_event_shapers_economy_faction.py`,
  `tests/unit/observability/test_event_extractor_economy.py`). This ticket's root cause is in the
  *test*, not the source.
- **`tests/unit/observability/test_event_extractor_economy.py` and 12 sibling
  `test_event_extractor_*.py` files use `MagicMock()` for `prior_state`/`update`** — `getattr(
  MagicMock(), "feature_flags", None)` returns a truthy `MagicMock`, so `.get("ENABLE_PUSH_EVENT_
  SHAPERS", "ON")` returns another `MagicMock` (not the string `"ON"`), and `MagicMock() == "ON"`
  is `False` by default — meaning **`_push_shapers_active` evaluates `False` in every one of these
  MagicMock-based tests**, so they accidentally exercise the *rollback* path (still legitimate code,
  still correct), never the real production shaper path. These tests are not broken (do not touch
  them under this ticket's scope) but they provide **zero real coverage of the production delivery
  path** — a latent, pre-existing test-quality gap, out of scope here but worth a note for whoever
  next touches `event_extractor.py`'s test suite (see Test Plan's Anti-Drift Test Guards).
- Do not conflate `_push_shapers_active` (ECONOMY/COMBAT/FACTION, Phase 1, default `ON`, no
  secondary shadow gate inside `run_shadow_shapers()`) with `_push_shapers_phase2_active`/
  `_push_shapers_quest_active`/`_push_shapers_agency_active` — 4 independently-gated flags exist in
  this file, each with its own history and its own rollback branch; a fix touching one must not
  assume it generalizes to the others.
