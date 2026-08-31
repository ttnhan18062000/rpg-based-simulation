---
status: historical
layer: systems
authority: P2
audience: agent
ticket_id: TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS
artifact_type: plan
tags: [social, testing]
---

# Implementation Plan — TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS

## Summary

This is a test-only chore: add one new file, `tests/unit/social/test_social_memory_service.py`,
containing 12 required branch-condition tests (6 per target function) plus 1 optional architecture
guard test, covering `SocialMemoryService.tick_place_attachment()` and
`.check_nemesis_promotion()` (`src/systems/social_systems/memory.py:12-52`). No `src/` file is
touched — both functions are confirmed dead code in production today (unreachable except via direct
unit-test invocation), so this plan changes zero runtime behavior. Tests are grouped into two
narrow, independently-verifiable steps (one per function) plus a third optional step for the
architecture guard, followed by a documentation-closure step that updates only the ticket's own
Implementation Notes / Test Summary / Files Changed / Completion Summary sections. The plan makes an
explicit call not to touch `docs/parity_ledger/social_narrative.yaml` (SOC-050/SOC-066): see Step 4
and Scope Guards for the reasoning.

## Steps

### Step 1 — `tick_place_attachment()` branch coverage
**Files:** `tests/unit/social/test_social_memory_service.py` (new file — create in this step with
module header, imports, and this function's 6 test cases)

**Change:** Create the new test module. Imports required:
`from src.systems.social_systems.memory import SocialMemoryService` (confirmed class/module path,
read at `src/systems/social_systems/memory.py:1-10` — `SocialMemoryService` is the only class in
the file, both target methods are `@staticmethod`s on it, lines 12-17 and 37-38), plus
`from src.core.state import RegionState` (confirmed fields `id: str`, `name: str`,
`bounds: tuple[int,int,int,int]`, `kind: str = "FOREST"` with several other defaulted fields, read
at `src/core/state.py:236-251` — construct with `RegionState(id=..., name=..., bounds=(xmin, ymin,
xmax, ymax))`, matching the convention documentation the investigation found in
`tests/unit/progression/test_progression_quests.py` and `tests/unit/world/*`), and
`from tests.helpers.entities import make_entity, make_state, with_navigation` (confirmed present at
`tests/helpers/entities.py:474-475` for `with_navigation`, `:384-406` for `make_state` which accepts
arbitrary `AuthoritativeState` field overrides via `dataclasses.replace`, e.g.
`make_state(regions={...})`).

Add 6 tests, each calling `SocialMemoryService.tick_place_attachment(entity, state, region_id=...)`
directly and asserting on the returned `SocialUpdate` (or `None`):

1. `test_tick_place_attachment_uses_explicit_region_id` — build an entity at a position (e.g.
   `pos=(0.0, 0.0)`) that does NOT fall inside any region in `state.regions` (or pass a `region_id`
   string with no matching key in `state.regions` at all — per test_plan.md's explicit anti-drift
   guard, this is required, not optional, to actually prove the branch skips validation). Call with
   `region_id="explicit_region"` where `state.regions` is empty or contains only unrelated regions.
   Assert result `== SocialUpdate(place_attachment_delta={"explicit_region": 0.001})`
   (`memory.py:23,31,35` — branch: `region_id` truthy skips the `if not region_id` scan entirely).
2. `test_tick_place_attachment_auto_detects_containing_region` — `region_id=None`, one region in
   `state.regions` whose `bounds` contains the entity's `navigation.position`
   (`entity.navigation.position` checked via `with_navigation(entity, position=(x, y))`, per
   `tests/helpers/entities.py:474-475`; bounds check is `xmin <= ex <= xmax and ymin <= ey <= ymax`,
   `memory.py:27`). Assert result keyed on that region's `id`.
3. `test_tick_place_attachment_returns_none_when_no_region_contains_position` — `region_id=None`,
   one or more regions in `state.regions`, entity position outside all of their bounds. Assert
   result `is None` (`memory.py:31-32`).
4. `test_tick_place_attachment_returns_none_when_no_regions_exist` — `region_id=None`,
   `state.regions == {}`. Assert result `is None` — distinct input path from case 3 (loop body never
   executes vs. loop executes and never matches), both reach the same `memory.py:31-32` guard.
5. `test_tick_place_attachment_boundary_position_matches_region_edge` — entity position placed
   exactly on `xmax` (or another edge) of a region's `bounds`. Assert the region IS matched
   (pins the inclusive `<=`/`>=` comparison at `memory.py:27`).
6. `test_tick_place_attachment_empty_string_region_id_falls_back_to_auto_detect` — call with
   `region_id=""` and a region that DOES contain the entity's position. Assert the result is keyed
   on the auto-detected region's `id`, identical to what `region_id=None` would produce — this pins
   the pre-existing truthy-falsy quirk flagged in investigation.md (Risks and Open Questions) as
   current behavior, not a defect being fixed.

**Do NOT touch:** `src/systems/social_systems/memory.py` itself (no source change — do not add
`region_id` validation against `state.regions`, do not change the `if not region_id:` guard to
`is None`, do not change the `0.001` constant). Do not add anything to the existing
`tests/unit/social/test_social_memory.py` file (unrelated module,
`src.domains.campaigns.social_memory` — see Scope Guards).

**Verify:** All 6 tests pass under
`pytest tests/unit/social/test_social_memory_service.py -v` (subset: the 6
`test_tick_place_attachment_*` tests specifically).

### Step 2 — `check_nemesis_promotion()` branch coverage
**Files:** `tests/unit/social/test_social_memory_service.py` (same file — append this function's 6
test cases after Step 1's)

**Change:** Add 6 tests calling `SocialMemoryService.check_nemesis_promotion(entity)` directly.
Entities are built via `make_entity(grudge_history={...})` (confirmed `grudge_history` is a native
keyword param of `make_entity`, `tests/helpers/entities.py:108`, routed into `builder.social(...)`
at `:297-309`) combined with `with_social(entity, nemesis_ids={...})` for cases needing a
pre-populated `nemesis_ids` set — confirmed `with_social` exists at
`tests/helpers/entities.py:482-483` (`replace(entity, social=replace(entity.social,
**changes))`), and confirmed `V2EntityBuilder.social()` independently accepts both
`grudge_history: Optional[Dict[int, float]]` and `nemesis_ids: Optional[Set[int]]` as sibling
params (`src/core/builder.py:496-516`), so either construction path is valid; use
`make_entity(grudge_history=...)` + `with_social(entity, nemesis_ids=...)` for readability
consistency with Step 1's helper usage.

1. `test_check_nemesis_promotion_empty_grudge_history_returns_none` —
   `grudge_history={}`. Assert `is None` (`memory.py:49-50`).
2. `test_check_nemesis_promotion_below_threshold_not_promoted` — `grudge_history={99: 2.9}`
   (single entry below the hardcoded `3.0` threshold, `memory.py:46`). Assert `is None`.
3. `test_check_nemesis_promotion_already_nemesis_not_repromoted` — `grudge_history={99: 5.0}`,
   `nemesis_ids={99}` (already promoted). Assert `is None` (excluded by the `eid not in
   entity.social.nemesis_ids` guard, `memory.py:46`).
4. `test_check_nemesis_promotion_qualifying_entry_promoted` — `grudge_history={99: 5.0}`,
   `nemesis_ids=set()`. Assert result `== SocialUpdate(nemesis_promotion=[99])`
   (`SocialUpdate.nemesis_promotion: List[int]`, confirmed field at `src/core/updates.py:298`).
5. `test_check_nemesis_promotion_exact_threshold_boundary_promoted` — `grudge_history={99: 3.0}`
   exactly. Assert promoted (pins the inclusive `>=` at `memory.py:46`).
6. `test_check_nemesis_promotion_mixed_entries_only_new_qualifying_promoted` — construct
   `grudge_history` with three entries in a known insertion order, e.g.
   `{101: 2.0, 102: 4.0, 103: 6.0}` where `102` is already in `nemesis_ids` and `103` is the only
   new qualifying entry (`101` below threshold, `102` above threshold but already-nemesis, `103`
   above threshold and new). Assert the exact list `result.nemesis_promotion == [103]` (not set
   membership — per test_plan.md's explicit anti-drift guard, this pins both per-entry filtering and
   `grudge_history` dict/insertion-order determinism, `memory.py:45-47`).

**Do NOT touch:** `src/systems/social_systems/memory.py` (no source change — do not change the
`3.0` threshold constant, do not change the `not in`/`>=` compound condition). Do not add anything
to `tests/unit/social/test_social_memory.py` or `tests/integration/scenarios/test_social_memory.py`
(both test the unrelated `src.domains.campaigns.social_memory` module).

**Verify:** All 6 tests pass under
`pytest tests/unit/social/test_social_memory_service.py -v` (subset: the 6
`test_check_nemesis_promotion_*` tests specifically).

### Step 3 — Architecture guard test (optional, per test_plan.md)
**Files:** `tests/unit/social/test_social_memory_service.py` (same file — append after Step 2's
tests)

**Change:** Add `test_social_memory_service_functions_are_pure_and_do_not_mutate_entity`: build one
entity/state pair with both `grudge_history` and a region under `state.regions` set up so both
functions have real work to do, snapshot the entity (and state, for `tick_place_attachment`) before
calling each function, call `SocialMemoryService.tick_place_attachment(...)` and
`SocialMemoryService.check_nemesis_promotion(...)`, then assert the entity/state objects passed in
are unchanged (e.g. `entity == entity_before`, or field-level equality on `entity.social` /
`entity.navigation`). This is a machine-verified check of the project's "Decision logic reads state,
does not mutate it" architecture rule (`CLAUDE.md` Architecture Rule) for this file specifically —
both `EntityState`/`AuthoritativeState` are frozen dataclasses per `docs/core/state.md`'s
immutability law, so this test is expected to pass structurally without requiring any code change;
it exists to make that guarantee explicit and regression-checked for this file.

This step is optional per test_plan.md's own framing ("cheap add-on") — implement it, since it is
zero-risk (pure addition, asserts an already-true invariant) and directly serves the project's
"Architecture tests" testing-rule requirement (`CLAUDE.md` Testing Rule: "verify read-only logic did
not mutate live state"). If time-constrained, this step may be dropped without affecting either
Acceptance Criterion — see Acceptance Criteria Map.

**Do NOT touch:** Any `src/` file. Do not add mutation-prevention code (e.g. `copy.deepcopy`) to
`memory.py` — the frozen-dataclass immutability already structurally prevents mutation; this test
only observes that fact, it does not enforce it via new source code.

**Verify:**
`pytest tests/unit/social/test_social_memory_service.py::test_social_memory_service_functions_are_pure_and_do_not_mutate_entity -v`

### Step 4 — Parity ledger and documentation closure
**Files:** `tickets/inprogress/TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS.md` (Implementation Notes,
Test Summary, Files Changed, Completion Summary sections only)

**Change:** Explicit decision on `docs/parity_ledger/social_narrative.yaml` SOC-050/SOC-066 (both
P0, `test_path: null`, read/confirmed in investigation.md's Parity Ledger Overlap section): **leave
both entries untouched in this ticket.** Rationale, made explicitly here rather than deferred
further: SOC-050's text ("Verify PlaceAttachment can be instantiated and supports sentiment") names
a `sentiment` concept that does not exist anywhere in the current V2 implementation
(`SocialComponent.place_attachment: Dict[str, float]` is a plain region→score dict — no
`PlaceAttachment` object, no `sentiment` field, confirmed absent from
`src/core/state.py`/`src/core/updates.py` reads in this session and in investigation.md). SOC-066's
text ("Nemesis milestone creation") uses "milestone" terminology absent from `memory.py`,
`updates.py`, and `models/social.py`. Pointing `test_path` at
`tests/unit/social/test_social_memory_service.py` for either entry would assert the new tests are
confirmed evidence for those specific legacy-checklist claims, when they are only directionally
related, not a confirmed 1:1 semantic match — this would misrepresent parity evidence per the
project's Authoritative Mechanics Rule ("Documentation and source code must remain in 100% semantic
parity"). The correct action for the P0/`test_path: null` gap on SOC-050/SOC-066 is a separate,
future ticket scoped to resolving the ambiguous legacy-to-V2 mapping (confirming or correcting the
ledger `text` itself against the actual V2 shape) — not a backfill riding on this ticket's
test-only chore. Record this decision in the ticket's Implementation Notes so it is traceable and
not silently dropped.

Fill in the ticket's `## Implementation Notes` (state: no `src/` changes; one new test file; parity
ledger SOC-050/SOC-066 left untouched with the reasoning above; recommend a follow-up ticket for the
P0/test_path gap), `## Test Summary` (list the 12-13 tests added and the scoped pytest command run),
`## Files Changed` (`tests/unit/social/test_social_memory_service.py` — new file only), and
`## Completion Summary` (both ACs met via the new file's branch coverage; no source, docs, or parity
ledger changes; sibling ticket TCK-20260824-GRIEF-NEMESIS-REACHABILITY confirmed unrelated).

**Do NOT touch:** `docs/parity_ledger/social_narrative.yaml` (explicit decision above — no edit, not
even an evidence-annotation edit). `docs/mechanics/04_strategic_cognition.md` or any other
`docs/mechanics/`/`docs/engine/` file (investigation.md's Docs Requiring Update: None — the two
"PH4 Law" mechanics are pre-existing undocumented magic numbers, not something this ticket
implements or changes; documenting them is separate follow-up work, not this ticket's scope).

**Verify:** `python3 tools/validate_frontmatter.py` (or equivalent project frontmatter check) passes
on the ticket file; ticket's required sections are all filled per the Ticket Format in `CLAUDE.md`.

## Scope Guards

- No `src/` file is modified in this plan, anywhere, for any reason — this is a test-only ticket.
  In particular: do not touch `src/systems/social_systems/memory.py` (the `if not region_id:`
  truthy-falsy guard, the `3.0` threshold, the `0.001` increment, or the unvalidated `region_id`
  trust contract all stay exactly as they are).
- Do not touch `src/domains/campaigns/*` (`CampaignOrchestrator`, `GriefUrgencyImporter`,
  `NemesisRelationImporter`, `src/domains/campaigns/social_memory.py`) — confirmed unrelated by both
  this ticket's Out of Scope and the sibling ticket TCK-20260824-GRIEF-NEMESIS-REACHABILITY's
  Completion Summary "Not changed" list. Any accidental import from `src.domains.campaigns.*` in the
  new test file is scope creep and must not happen.
- Do not add test cases to the existing, unrelated `tests/unit/social/test_social_memory.py` or
  `tests/integration/scenarios/test_social_memory.py` — both test
  `src.domains.campaigns.social_memory`, a different module from this ticket's target
  (`src.systems.social_systems.memory`). The new file's name,
  `test_social_memory_service.py`, is deliberately distinct.
- Do not touch `docs/parity_ledger/social_narrative.yaml` (SOC-050/SOC-066) — decided explicitly in
  Step 4, not deferred.
- Do not touch any `docs/mechanics/` or `docs/engine/` file.
- Do not attempt to make `tick_place_attachment`/`check_nemesis_promotion` reachable from
  `src/engine/apply.py` or any other production call site — that is
  TCK-20260824-GRIEF-NEMESIS-REACHABILITY's explicitly separate scope, not this ticket's.
- Do not change the reachability/dead-code status of either function — no wiring, no new caller,
  no `AuthoritativeApplyPipeline`/`ApplyPath` changes.

## Dependency Map

- Step 1 and Step 2 both write to the same new file (`test_social_memory_service.py`) but are
  content-independent (different functions under test, no shared fixtures beyond the common
  imports declared in Step 1). Step 2 should be applied after Step 1 creates the file (so the module
  header/imports exist), but Step 2's test logic does not depend on Step 1's test outcomes.
- Step 3 (optional architecture guard) depends on Step 1 and Step 2 only in the sense that it is
  appended to the same file after both — it is otherwise self-contained and could be skipped without
  affecting Steps 1/2 or either AC.
- Step 4 (ticket documentation closure) depends on Steps 1-2 (and 3, if implemented) being complete,
  since it summarizes the actual tests added and files changed.
- No step depends on any other ticket's work (TCK-20260824-GRIEF-NEMESIS-REACHABILITY is confirmed
  fully independent per investigation.md's Prior Work section).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| `check_nemesis_promotion()` has unit tests covering each of its branch conditions | Step 2 | `pytest tests/unit/social/test_social_memory_service.py -k check_nemesis_promotion -v` (6 tests: empty history, below threshold, already-nemesis, qualifying, exact-threshold boundary, mixed-entries) |
| `tick_place_attachment()` has unit tests covering each of its branch conditions | Step 1 | `pytest tests/unit/social/test_social_memory_service.py -k tick_place_attachment -v` (6 tests: explicit region_id, auto-detect, no-match returns None, empty-regions returns None, boundary edge, empty-string region_id pin) |

Step 3 (architecture guard) and Step 4 (documentation closure) support the Definition of Done but do
not map to either AC directly — both ACs are fully satisfied by Steps 1 and 2 alone.

## Anti-Drift Notes

- **Test 1 for `tick_place_attachment` must place the entity outside the named region's bounds (or
  use a `region_id` with no matching `state.regions` key at all)** — test_plan.md is explicit that
  this is required to prove the explicit-`region_id` branch actually skips validation, not merely
  happens to agree with what auto-detection would have found anyway.
- **Test 6 for `check_nemesis_promotion` (mixed entries) must assert the exact returned list**
  (`result.nemesis_promotion == [103]`), not `set(result.nemesis_promotion) == {103}` — the looser
  assertion would still pass even if a future refactor leaked duplicate/invalid entries or made
  ordering nondeterministic, defeating the point of the pin.
- **The `region_id=""` test (Step 1, test 6) is a pinning/regression test, not a bug report or a
  request to change behavior.** Do not "fix" the `if not region_id:` truthy-falsy guard to an
  `is None` check as part of this ticket — that would be an unrequested logic change on a ticket
  scoped as test-only, and would contradict the Out of Scope framing in the ticket itself.
- **`SocialUpdate` equality**: `SocialUpdate` is a plain `@dataclass` (confirmed at
  `src/core/updates.py:277`), so direct `==` comparison against a freshly-constructed
  `SocialUpdate(...)` with only the relevant field set (e.g. `SocialUpdate(nemesis_promotion=[99])`)
  works correctly — all other fields default via `field(default_factory=...)` /
  literal defaults and will compare equal between the actual and expected instances as long as no
  other field is populated by either function (confirmed neither target function sets any field
  other than `nemesis_promotion` or `place_attachment_delta` respectively, `memory.py:35,52`).
- **`make_entity()` has no `nemesis_ids` keyword param** (confirmed absent from the parameter list
  at `tests/helpers/entities.py:40-116`) — tests needing a pre-populated `nemesis_ids` must layer
  `with_social(entity, nemesis_ids={...})` on top of `make_entity(grudge_history=...)`, per Step 2's
  Change text. Do not attempt to pass `nemesis_ids=` directly to `make_entity()` — it will raise
  `TypeError: unexpected keyword argument`.
- **Region containment uses `entity.navigation.position`**, set via `with_navigation(entity,
  position=(x, y))` (confirmed helper at `tests/helpers/entities.py:474-475`) — `make_entity()`'s
  own `pos` parameter (line 44) also sets this via `V2EntityBuilder(...).location(*pos)` at
  construction time, so either `make_entity(pos=(x, y))` or a post-hoc `with_navigation(...)` call
  is valid; prefer `make_entity(pos=...)` at construction for the simple cases (most of Step 1's
  tests) and reserve `with_navigation` only if a test needs to vary position independent of other
  `make_entity` params already set.

## Deviations

Implementation followed all 4 steps as written; no scope, test-count, or file-touch deviation.
One minor factual correction to this plan's own Anti-Drift Notes: `SocialUpdate` is declared
`@dataclass(frozen=True, slots=True)` at `src/core/updates.py:276-277`, not the "plain `@dataclass`"
this plan's Anti-Drift Notes stated. This does not change any test-writing consequence described
there — `==` comparison against a freshly-constructed `SocialUpdate(...)` still works identically
whether or not the dataclass is frozen/slotted, and all 13 tests (including the equality-based
assertions) pass as written. Confirmed via direct read of `src/core/updates.py` before writing any
test; not a branch-logic or behavioral inaccuracy in `memory.py` itself (that file's description was
verified byte-for-byte accurate against the plan/investigation, so no `src/` change or scope
escalation was warranted).
