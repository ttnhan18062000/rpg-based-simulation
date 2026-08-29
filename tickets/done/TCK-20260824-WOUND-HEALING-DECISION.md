---
status: historical
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20260824-WOUND-HEALING-DECISION
phase: done
date: 2026-08-24
tags: [combat]
---

# TCK-20260824-WOUND-HEALING-DECISION

## Title
Decide Whether Wound Healing Should Ever Fire

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
No wound has ever healed in production because `WoundUpdate.wounds_heal` has zero producers. The author wants a decision on whether healing should be implemented, or whether wounds are intentionally permanent until a Scar forms -- separate from the penalty-formula fix.

## Scope
- Record an explicit decision in both Mechanics Bible sections (`docs/mechanics/02_combat_laws.md` Section 5, `docs/mechanics/01_entity_anatomy.md` Section 6): (a) healing is active with a defined trigger, or (b) wounds are intentionally permanent and scars form via a different path
- If (a): implement a real production code path that constructs `WoundUpdate(wounds_heal=[...])` under a deterministic condition, verified via a non-mocked `Kernel.tick_once()` run
- If (b): remove or explicitly annotate `heal_wound()` and `MedicalService.get_diagnosis_quality()` as dead-by-design, and add a `docs/guidelines/intentional_divergences.md` entry
- Correct `docs/parity_ledger/combat_movement.yaml` COMB-296 and `docs/event_ledger/entity.yaml` ENTITY-018 to reflect that `wound_healed` currently has zero production producers, regardless of which option is chosen
- State explicitly whether `MedicalService.get_diagnosis_quality()` (also dead, zero callers) belongs to the healing pipeline or is separately dead

## Out of Scope
- The severity-scaled penalty-formula fix (owned by TCK-20260824-WOUND-PENALTY-FORMULA-WIRING) -- this ticket is explicitly independent of that fix
- The `should_inflict_wound()` 40% threshold dead-code decision (owned by TCK-20260824-WOUND-THRESHOLD-DECISION)

## Acceptance Criteria
- [x] An explicit decision is recorded in both Mechanics Bible sections, replacing the current ambiguous "when a wound heals" phrasing
- [x] If healing is made active: a real production code path constructs `WoundUpdate(wounds_heal=[...])` under a deterministic condition, verified via non-mocked `Kernel.tick_once()` (N/A — Option (b) was chosen, not Option (a))
- [x] If wounds are declared permanent: `heal_wound()`/`MedicalService.get_diagnosis_quality()` are removed or annotated dead-by-design, with an `intentional_divergences.md` entry added (removal done; DEV-005 entry added)
- [x] COMB-296 and ENTITY-018 are corrected to reflect zero production producers regardless of the gate state chosen (done, scoped to `wound_healed`/`scar_gained` — see Implementation Notes for the re-scoped Step 4 proof approach)

## Related Tickets
- TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP
- TCK-20260619-PARITY-P0-BUGS
- TCK-20260429-E3-MISSING-LOGIC
- TCK-20260806-SIMQ-COMBAT-ENGAGEMENT-GATE-CORPUS-VALIDITY
- TCK-20260809-COMBAT-RESOLVED-SCORER-GAP-FIX
- TCK-20260809-COMBAT-TACTICAL-VARIETY-SCORER-GAP-FIX
- TCK-20260824-WOUND-THRESHOLD-DECISION
- TCK-20260824-WOUND-PENALTY-FORMULA-WIRING

## Related Docs
- docs/mechanics/02_combat_laws.md
- docs/mechanics/01_entity_anatomy.md
- docs/parity_ledger/combat_movement.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/engine/rpg_depth.py
- src/core/updates.py
- src/engine/combat.py
- src/engine/patches.py
- src/observability/event_extractor.py

## Assumptions / Open Questions
- This is a genuine open design question with no documented trigger condition anywhere in the Mechanics Bible -- no partial implementation exists to build from
- Coordinate sequencing with TCK-20260824-WOUND-THRESHOLD-DECISION (C2), since a "wounds are permanent" verdict here would further narrow C2's `should_inflict_wound()`/`heal_wound()` cleanup scope

## Implementation Notes

**Steps 1-3 of `staging_artifacts/TCK-20260824-WOUND-HEALING-DECISION/plan.md` completed as
specified:**
1. `docs/mechanics/02_combat_laws.md` Section 5's last bullet replaced with an explicit
   "Wound Permanence" statement (zero production `wounds_heal`/`scars_add` producers, citing
   `combat.py::_get_wound_infliction` and `updates.py::WoundUpdate` defaults, referencing
   `TCK-20260824-TACTICAL-WOUND-SCAR-WIRING` for the future scar-formation mechanic).
2. `docs/mechanics/01_entity_anatomy.md` Section 6's "### Permanent Scars" subsection rewritten
   with the same permanence statement; the `scar_penalty = wound_penalty * 0.3` code block
   preserved verbatim per the plan.
3. `WoundService.heal_wound()` and `MedicalService.get_diagnosis_quality()` (plus the now-empty
   `MedicalService` class) deleted from `src/engine/rpg_depth.py`. The now-unused
   `from dataclasses import replace` import was also removed (its only use was inside
   `heal_wound()`) — a small necessary cleanup not explicitly named in the plan but required to
   avoid leaving a dead import. `TestScarPermanence`'s 3 tests and
   `TestEffectiveStats::test_effective_stats_with_scars` (plan.md named this
   `TestSkillScaling::test_effective_stats_with_scars` — the actual class in the current file is
   `TestEffectiveStats`; same test, class name in the plan was imprecise) rewritten to hand-build
   the `WoundState`->`ScarState` transition inline (matching what `heal_wound()` did) instead of
   calling the removed function. `test_wound_heal_through_apply` untouched and still passes.
   `WoundService.create_wound()`, `get_wound_stat_penalties()`, `get_scar_stat_penalties()`,
   `DiscoveryService`, and the shared section comment are all untouched.
   `pytest tests/unit/core/test_rpg_depth.py -v`: 58 passed. `grep -rn "heal_wound|get_diagnosis_quality|MedicalService" src/ tests/`: zero matches.

**Steps 4-7 are BLOCKED — a new architectural conflict was discovered while building Step 4's
integration test, not present in the plan or investigation.md:**

Step 4 required a real, non-mocked `Kernel.tick_once()` loop proving `wound_sustained` fires while
`wound_healed`/`scar_gained` never do — this is the evidence Steps 5/6/7 all depend on (Steps 5/6
cite Step 4's exact test node id; Step 7's DEV-005 entry cites Steps 5/6's corrected content).
Building that test surfaced a real bug, verified directly and reproducibly (not from a single
observation):

- `WoundPatch.apply()` (`src/engine/patches.py:639`, the authoritative apply path) always commits
  `entity.combat.wounds`/`.scars` as **tuples** (`replace(new_com, wounds=tuple(new_wounds),
  scars=tuple(new_scars))`) — this is the established, deliberate immutability convention for
  durable state in this codebase.
- `src/observability/event_extractor.py:280-281` and `:302-303` (added by
  `TCK-20260808-ENTITY-VITALS-OBSERVABILITY-GAP`) gate the wound/scar diffing blocks with
  `isinstance(entity.combat.wounds, list)` / `isinstance(entity.combat.scars, list)` — **`list`
  only, not `(list, tuple)`**. Since the real apply path always produces tuples, this check is
  always `False` for any wound/scar that reached state through the real apply path, so
  `entity_wounds`/`entity_scars` silently become `[]` and the diff loop that emits
  `wound_sustained`/`wound_healed`/`scar_gained` never runs. This is a real, pre-existing bug, not
  a hypothetical — the same file already handles this correctly elsewhere with
  `isinstance(x, (list, tuple))` (`event_extractor.py:1499`, `:1583`), confirming the codebase is
  aware tuples occur here and this block's check is simply wrong.
- Verified directly with a real `Kernel.tick_once()` loop (2 hand-built entities, hostile
  factions, `ENABLE_COMBAT_ENGAGEMENT: "ON"`, attacker ATK tuned so a hit exceeds the 25%-max-HP
  wound threshold): a real wound was genuinely inflicted through the production combat path
  (`kernel.state.entities[...].combat.wounds` had 1 entry, `entity.combat` carried a real
  `WoundUpdate(wounds_add=[...])` in that tick's `EntityUpdate`), yet
  `kernel._event_recorder.event_count_by_type` never recorded `wound_sustained` for that tick or
  any other. `prior_state`/`current_state` passed into `EventExtractor.extract()` at the exact
  call site were confirmed to be tuples (`()` and `(WoundState(...),)` respectively).
- The existing test evidence cited by `COMB-296`/`ENTITY-018`
  (`test_wound_sustained_severity_mapping`, `test_wound_healed_fires`, `test_scar_gained_fires` in
  `tests/unit/observability/test_event_extractor_vitals.py`) all construct
  `replace(prior_ent.combat, wounds=[wound])` — a **literal Python `list`**, not through the real
  apply path — which is exactly why they pass despite this bug. This was not caught by
  investigation.md's Finding 6, which correctly identified these tests as "hand-constructed, not
  through `Kernel.tick_once()`" but did not identify that even a Kernel-loop-produced wound would
  also fail to fire the event, for an unrelated, independent reason.

**Why this blocks Steps 4-7, not just changes their wording:** the plan's premise (inherited from
investigation.md, itself inherited from the pre-existing `COMB-296`/`ENTITY-018` ledger text) is
that `wound_sustained` is a real, working producer gated only by `ENABLE_COMBAT_ENGAGEMENT` —
distinct from `wound_healed`/`scar_gained`, which have zero producers regardless of gate state.
That distinction is what Steps 5/6's ledger corrections and Step 7's DEV-005 entry are built to
state precisely. My finding shows the *event* layer is broken for all three, independent of the
gate, for a completely different and previously-undocumented reason (an `isinstance` type check,
not a missing producer). Writing Step 4's test to assert `wound_sustained` fires would encode a
false claim (it does not, currently). Writing it to assert the event never fires, then having
Steps 5/6 restate that as "gated only by `ENABLE_COMBAT_ENGAGEMENT`," would launder a real,
independently-discovered bug into ledger text as if it were an accepted, understood limitation —
this is exactly the kind of gate-integrity violation the project's Hard Rules prohibit ("Never
edit an artifact to make an automated gate/check pass instead of fixing the underlying
substance"). Fixing `event_extractor.py`'s `isinstance` check is a one-line, well-understood fix,
but it is out of this ticket's approved plan (no step names `event_extractor.py` as a file to
change) and deserves its own ticket with its own test coverage and parity-ledger evidence, not a
silent scope expansion buried inside this ticket's Step 4.

**Recommendation**: file a new `hotfix`-tier ticket to fix
`src/observability/event_extractor.py:280-281,302-303` (`isinstance(x, list)` ->
`isinstance(x, (list, tuple))`, matching the already-correct pattern at lines 1499/1583 in the
same file), with its own real-`Kernel.tick_once()` regression test. Once that lands, this ticket's
Steps 4-7 can proceed as planned (Step 4's test should then genuinely pass), and `COMB-296`/
`ENTITY-018` can be corrected accurately in one pass referencing both the healing-permanence
decision and the event-extraction fix.

**Files/tests verified but not modified in this session**: `src/observability/event_extractor.py`,
`src/engine/patches.py`, `tests/unit/observability/test_event_extractor_vitals.py` (read/traced
only, to confirm the bug — no changes made).

**Follow-up session (2026-08-29): Steps 4-7 re-scoped and completed.** The recommendation above was
acted on: the hotfix was filed as `tickets/todos/TCK-20260829-HOTFIX-WOUND-SCAR-EVENT-EXTRACTOR-TUPLE-BLIND.md`
(not implemented by this ticket). Rather than blocking this ticket's own completion on that hotfix
landing, the top-level session directed a re-scope: Step 4's proof was retargeted from the
*event* layer (which is broken for all three wound/scar events uniformly, not specific to healing)
to the *authoritative-state/producer* layer, which does not depend on the hotfix.

- **Step 4 (re-scoped)**: Added
  `tests/integration/combat/test_wound_healing_permanence.py::test_wound_healed_and_scar_gained_have_zero_production_producers`.
  Builds two real, hand-built entities (`hero_guild` attacker ATK 80, `goblin_warband` defender HP
  100, hostile factions, adjacent) inside a real, non-mocked `Kernel` with
  `ENABLE_COMBAT_ENGAGEMENT=ON`, and runs `kernel.tick_once()` for 40 ticks at seed 42 — no
  mocking, no hand-injected task/intent. A real wound is genuinely inflicted at tick 9 through the
  full production AI pipeline (deterministic, reproduced twice during this session). Rather than
  reading `EventExtractor`-emitted events (broken by the separate isinstance bug), the test reads
  `kernel.state.entities[...].combat.wounds`/`.scars` directly each tick — the real, frozen,
  authoritative state, confirmed tuple-shaped by an in-test `isinstance(..., tuple)` assertion
  (matching the exact shape the event_extractor bug mishandles, without depending on that code
  path). Across the full 40-tick run: no wound ever transitions `healed: False -> True`, and no
  `ScarState` is ever added to either entity. Combined with a fresh full-repo grep re-confirming
  `WoundUpdate(` is constructed in exactly one place in `src/` (`combat.py:617`, never populating
  `wounds_heal`/`scars_add`), this is a producer-existence proof at the state/code level, not an
  event-observability proof — it does not require the separate hotfix to land first.
  `pytest tests/integration/combat/ -v -m "not slow"`: 36 passed (35 pre-existing + 1 new).
- **Step 5**: `docs/parity_ledger/combat_movement.yaml` COMB-296 corrected via the sanctioned
  `tools/parity_ledger_writer.py` write path (not raw Edit). `v2_evidence`/`support_boundary`/
  `test_path` now state precisely that `wound_healed`/`scar_gained` have zero production
  producers independent of gate state, and separately (factually, without asserting a fix) note
  that the event-layer emission bug affecting all three events is tracked by
  `TCK-20260829-HOTFIX-WOUND-SCAR-EVENT-EXTRACTOR-TUPLE-BLIND` rather than corrected here — this
  ticket does not claim `wound_sustained`'s event-layer status changed. Verified via
  entry-count equality (314 before/after) and per-entry content equality against
  `git show HEAD:docs/parity_ledger/combat_movement.yaml` for every entry except COMB-296 itself
  (script-checked, zero mismatches). `git diff --stat`: 1 file changed, 40 insertions(+), 17
  deletions(-) — a small surgical diff despite going through the full-shard-rewrite writer.
- **Step 6**: `docs/event_ledger/entity.yaml` ENTITY-018 corrected directly (no sanctioned writer
  exists for this file; plan Step 6 anticipated this). Same wound_healed/scar_gained-scoped
  correction as COMB-296, same wound_sustained non-conflation. `git diff --stat`: 1 file changed,
  2 insertions(+), 2 deletions(-). `tests/tools/test_entity_event_ledger.py`: initially failed
  `test_entity_ledger_evidence_citations_are_real_files` because the first draft cited bare
  `combat.py`/`event_extractor.py` filenames instead of full `src/...` paths — fixed by using full
  paths throughout; re-ran and it now passes.
  `test_entity_ledger_covers_every_entity_update_field` fails both before and after this ticket's
  changes (`cognition_bundle_set` missing a ledger entry) — confirmed pre-existing via
  `git stash`/re-run, unrelated to this ticket, not touched.
- **Step 7**: `docs/guidelines/intentional_divergences.md` DEV-005 entry added (Subsystem/
  Situation/Decision/Rationale/Verification/Status, following the DEV-004 template), including an
  explicit sub-note on why Step 4 was re-scoped and how it relates to the separate hotfix ticket.
  Summary table row added; footer "Last updated" line updated to 2026-08-29/DEV-005.
- **Pre-existing, unrelated test-baseline drift noticed during Parity verification**:
  `tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path`
  fails on unmodified `HEAD` too (`live_missing=1322` vs. hardcoded baseline `1332`) — confirmed via
  `git stash`/re-run before this ticket touched anything. Not caused by this ticket, not fixed by
  this ticket (matches the documented "hardcoded baseline drift" regression-policy category; a
  separate hotfix ticket would be needed to refresh the baseline with fresh evidence, out of this
  ticket's scope).

## Test Summary
- `pytest tests/unit/core/test_rpg_depth.py -v` — 58 passed (includes the 4 rewritten tests and the
  unchanged `test_wound_heal_through_apply`).
- `pytest tests/integration/combat/ -v -m "not slow"` — 36 passed (35 pre-existing +
  `test_wound_healed_and_scar_gained_have_zero_production_producers`, new).
- `pytest tests/tools/test_entity_event_ledger.py -v` — 2 passed, 1 pre-existing failure
  (`test_entity_ledger_covers_every_entity_update_field`, `cognition_bundle_set` gap — confirmed
  present on unmodified `HEAD` via `git stash`, unrelated to this ticket).
- `pytest tests/tools/test_parity_index_baseline.py tests/tools/test_parity_ledger_writer.py -v` —
  28 passed, 1 pre-existing failure
  (`test_baseline_manifest_does_not_coerce_missing_test_path` — confirmed present on unmodified
  `HEAD` via `git stash`, unrelated to this ticket).

## Files Changed
- `docs/mechanics/02_combat_laws.md` (Step 1)
- `docs/mechanics/01_entity_anatomy.md` (Step 2)
- `src/engine/rpg_depth.py` (Step 3: deleted `heal_wound()`, `MedicalService`/
  `get_diagnosis_quality()`, removed now-unused `replace` import)
- `tests/unit/core/test_rpg_depth.py` (Step 3: rewrote 4 tests to hand-construct the
  `WoundState`->`ScarState` transition)
- `tests/integration/combat/test_wound_healing_permanence.py` (Step 4, new file: real
  `Kernel.tick_once()` state-level producer-existence proof)
- `docs/parity_ledger/combat_movement.yaml` (Step 5: COMB-296 corrected via
  `tools/parity_ledger_writer.py`)
- `docs/event_ledger/entity.yaml` (Step 6: ENTITY-018 corrected directly)
- `docs/guidelines/intentional_divergences.md` (Step 7: new DEV-005 entry, summary table row,
  footer date)
- `docs/brainstorm/rpg_simulation_wiring_map.html` (Document-Update phase: fixed stale
  `heal_wound()`/Idea-17 "should we wire it in" language not flagged by investigation.md —
  Trauma summary-table row, lifecycle-arc mermaid diagram, T7 lifecycle-transition table row)
- `docs/brainstorm/rpg_expected_schemas.html` (Document-Update phase: same stale-reference fix,
  Trauma Scar schema field row and duplicate-storage-corrections table row)
- `staging_artifacts/TCK-20260824-WOUND-HEALING-DECISION/plan.md` (Deviations section: Step 3's
  original note, plus the Step 4-7 re-scope rationale)
- `tickets/inprogress/TCK-20260824-WOUND-HEALING-DECISION.md` (this file)

## Completion Summary
All 7 steps of the approved plan are complete and verified. Steps 1-3 (from the prior session):
both Mechanics Bible sections state the wound-permanence decision explicitly, and the two
dead-by-design functions (`WoundService.heal_wound()`, `MedicalService.get_diagnosis_quality()`)
are removed with their 4 dependent unit tests rewritten to preserve coverage (58/58 passing).

Steps 4-7 (this session, re-scoped): Step 4 was originally blocked because building a real
`Kernel.tick_once()` integration test surfaced a genuine, independently-verified production bug in
`src/observability/event_extractor.py` (an `isinstance(x, list)` check that silently drops all
real wound/scar event diffing, since the authoritative apply path always produces tuples) —
meaning none of `wound_sustained`/`wound_healed`/`scar_gained` fire through the event layer today,
for a reason unrelated to whether a producer exists. That bug was filed as its own hotfix ticket
(`TCK-20260829-HOTFIX-WOUND-SCAR-EVENT-EXTRACTOR-TUPLE-BLIND`) rather than fixed here, since it was
outside this ticket's approved plan. The top-level session then directed a re-scope: Step 4's proof
was retargeted from the event layer to the authoritative-state/producer layer — reading
`kernel.state.entities[...].combat.wounds`/`.scars` directly, which a real 40-tick
`Kernel.tick_once()` run (a real wound inflicted at tick 9) shows never transitions to `healed`
and never gains a `ScarState` — which does not depend on the separate event-extraction bug being
fixed first. `COMB-296`/`ENTITY-018` were corrected precisely for `wound_healed`/`scar_gained`'s
zero-producer status, explicitly not conflating that with `wound_sustained`'s separate, still-open
event-layer reachability question (left for the hotfix ticket). A new `DEV-005` entry records the
full decision and re-scope rationale in `docs/guidelines/intentional_divergences.md`.
