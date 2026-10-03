---
status: historical
layer: systems
authority: P2
audience: agent
ticket_id: TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS
artifact_type: investigation
tags: [social, testing]
---

# Investigation — TCK-20260824-NEMESIS-MEMORY-UNIT-TESTS

## Current Behavior

Both target functions live in `src/systems/social_systems/memory.py`, inside
`SocialMemoryService` — a stateless `@staticmethod`-only class ("Domain 4 Hardening"). The class
is re-exported unchanged by the facade `src/systems/social_memory.py`
(`from src.systems.social_systems.memory import SocialMemoryService`), which is itself imported by
`src/engine/apply.py:46`. Neither the facade nor `memory.py` are imported anywhere else in `src/`.

**Both target functions are currently dead code in production**: a repo-wide grep for
`tick_place_attachment\|check_nemesis_promotion` across `src/` finds only their two definitions in
`memory.py` — `SocialMemoryService` is imported into `src/engine/apply.py:46` but neither static
method is actually *called* anywhere in that file or anywhere else in `src/`. This means these
functions are reachable today only via direct unit-test invocation, not via any live tick/pipeline
path — consistent with the ticket's framing of them as "orphaned" and explains why zero coverage
went unnoticed. This is informational context for scoping the test plan (no engine-pipeline
regression surface exists for these two functions specifically), not a defect to fix — reachability
is explicitly Out of Scope per this ticket's own text and the sibling ticket's boundary.

### `tick_place_attachment(entity, state, region_id=None) -> Optional[SocialUpdate]` (`memory.py:12-35`)

Purpose: passively grows an entity's attachment to whatever region it currently occupies (PH4:
"Long-term presence creates 'Home' attachment"). Returns a `SocialUpdate` carrying
`place_attachment_delta`, or `None` if no region can be resolved.

Branch-by-branch (`memory.py:22-35`):
1. `if not region_id:` (line 23) — when the caller does not pass a `region_id` (or passes a falsy
   one — see Risk below), the function scans `state.regions.items()` (line 25) and, for each
   region, tests `entity.navigation.position` against `region.bounds` (`xmin, ymin, xmax, ymax`)
   with **inclusive** bounds (`xmin <= ex <= xmax and ymin <= ey <= ymax`, line 27). On the first
   match it sets `region_id = rid` and `break`s (lines 28-29) — dict iteration order decides the
   winner if regions overlap.
2. `if not region_id:` (line 31) — after the optional lookup, if `region_id` is still falsy (no
   `region_id` was passed AND no region's bounds contained the entity's position), returns `None`.
3. Otherwise (a `region_id` was passed truthy, OR the loop found a containing region): returns
   `SocialUpdate(place_attachment_delta={region_id: 0.001})` (line 35) — a fixed per-tick increment,
   not scaled by tick delta or any other state.

Distinct branch conditions needing coverage:
- (A) `region_id` passed explicitly (non-empty string) → skips the scan entirely, returns the
  update keyed on the passed `region_id` regardless of whether that region exists in `state.regions`
  or the entity's actual position (the function does not validate the passed `region_id` against
  `state.regions` at all).
- (B) `region_id=None`, entity position falls inside exactly one region's bounds → returns the
  update keyed on the discovered region.
- (C) `region_id=None`, entity position falls inside no region's bounds → returns `None`.
- (D) Boundary condition: entity position exactly on a region's edge (`ex == xmax` etc.) → must
  still match, since the comparison is inclusive on both ends.
- (E) `region_id=None`, `state.regions` is empty → same code path as (C), returns `None`.

### `check_nemesis_promotion(entity) -> Optional[SocialUpdate]` (`memory.py:37-52`)

Purpose: promotes entities from `entity.social.grudge_history` (`Dict[int, float]`) into
`entity.social.nemesis_ids` (`Set[int]`) once grudge reaches a hardcoded 3.0 threshold (PH4:
"Significant history of harm creates a 'Nemesis'"). Returns a `SocialUpdate` carrying
`nemesis_promotion: List[int]`, or `None` if nothing to promote.

Branch-by-branch (`memory.py:43-52`):
1. Loop over `entity.social.grudge_history.items()` (line 45). For each `(eid, grudge)`: `if eid
   not in entity.social.nemesis_ids and grudge >= 3.0:` (line 46) — a compound AND condition with
   two independently-testable sub-conditions — append `eid` to `nemesis_to_add`.
2. `if not nemesis_to_add:` (line 49) — if nothing qualified, return `None`.
3. Otherwise, return `SocialUpdate(nemesis_promotion=nemesis_to_add)` (line 52) — a list, order
   following `grudge_history` dict iteration (insertion) order.

Distinct branch conditions needing coverage:
- (A) `grudge_history` empty → `nemesis_to_add` stays empty → `None`.
- (B) An entry with `grudge < 3.0` (below threshold, not already nemesis) → excluded → (if it's the
  only entry) `None`.
- (C) An entry with `grudge >= 3.0` but `eid` already in `nemesis_ids` → excluded by the `not in`
  guard → (if it's the only entry) `None`.
- (D) An entry with `grudge >= 3.0` and `eid` not in `nemesis_ids` → included → returns
  `SocialUpdate(nemesis_promotion=[eid])`.
- (E) Boundary: `grudge == 3.0` exactly → included, since the comparison is `>=`.
- (F) Mixed multi-entry case: one entry below threshold, one already-nemesis, one new qualifying
  entry, in the same call → only the new qualifying entry appears in the result list, proving the
  filter is applied per-entry rather than short-circuiting the whole call.

## Mechanics / Engine Constraints

Both functions are labelled "Domain 4 Hardening" / "PH4 Law" in their docstrings, but a repo-wide
search (`grep -rn "PH4\|place_attachment\|Home.*attachment\|Domain 4 Hard" docs/mechanics/*.md
docs/engine/*.md`) finds **no** chapter or contract that documents these two mechanics by name.
`docs/mechanics/04_strategic_cognition.md:22` only lists `social`/`grudge`/`bond` as Tier-3 Social
concern keywords in the goal-hierarchy table — it does not describe place-attachment accrual or the
3.0 nemesis-promotion threshold as a formula. This is a **pre-existing documentation gap**,
independent of this ticket (this ticket adds tests only, no logic change, so it does not newly
create the gap — see Docs Requiring Update below for why it is not fixed here).

`SocialUpdate.merge()` (`src/core/updates.py:315+`) and `.is_noop()` (`:305-313`) both already
enumerate `nemesis_promotion`/`place_attachment_delta` as first-class fields — the return-value
shape these two functions produce is consistent with the rest of the authoritative-update pipeline
(`AuthoritativeApplyPipeline`/`ApplyPath`), which is out of scope to touch here (see Out of Scope).

## Docs Requiring Update

None.

The two "PH4 Law" docstring mechanics (place attachment accrual, 3.0 nemesis-promotion threshold)
are not documented in any `docs/mechanics/` chapter today (verified by grep, see Mechanics/Engine
Constraints above), but this ticket is a test-only chore with an explicit, narrow AC set ("has unit
tests covering each of its branch conditions") and a ticket-level `Related Docs: None.` declaration
— it does not implement, change, or newly introduce either mechanic, so writing the doc chapter is
not implied work here. `docs/mechanics/04_strategic_cognition.md` (path:
`docs/mechanics/04_strategic_cognition.md`) is not required to change for this ticket: it already
covers Tier-3 Social goal-hierarchy concerns at a category level, and adding a full formula
subsection for place-attachment/nemesis-promotion would be new-mechanic documentation work, not a
byproduct of adding tests to existing, unchanged code — flagged instead as a follow-up opportunity
in Risks and Open Questions below.

## Parity Ledger Overlap

`docs/parity_ledger/social_narrative.yaml` has two entries that are plausibly, but not certainly,
related to this code:

- **SOC-050** (`test_place_attachment_instantiation`, status `verified`, priority `P0`,
  `v2_evidence: "Implementation proven via exhaustive checklist audit Phase 1-11"`, `test_path:
  null`) — text says "Verify PlaceAttachment can be instantiated and supports sentiment." This
  legacy-checklist wording implies a `PlaceAttachment` *object* with a `sentiment` field; the actual
  V2 shape is `SocialComponent.place_attachment: Dict[str, float]` (`src/core/models/social.py:37`)
  — a plain region→score dict with no `sentiment` concept. The mapping from this ledger entry to
  `tick_place_attachment()` is therefore uncertain, not a confirmed 1:1 match.
- **SOC-066** (`test_nemesis_milestone_creation`, status `verified`, priority `P0`, same generic
  `v2_evidence`, `test_path: null`) — text says "Nemesis milestone creation," which is directionally
  consistent with `check_nemesis_promotion()`'s grudge→nemesis promotion, but "milestone" is not a
  term used anywhere in `memory.py`, `updates.py`, or `models/social.py`, so this is also not a
  confirmed 1:1 match.

Both are **P0 with `test_path: null`** — an existing gap (P0 entries are supposed to require a
passing `test_path`) that predates this ticket and is not caused by it. Per the Authoritative
Mechanics Rule, a parity ledger update is required "if logic changes" — this ticket changes no
logic, only adds tests, so no ledger edit is strictly required by this ticket's scope. Whether to
opportunistically backfill `test_path` on SOC-050/SOC-066 once new tests exist is flagged as an open
question for the Plan/Parity phase (see Risks and Open Questions) rather than decided here, given
the text-to-code mapping uncertainty above.

`docs/parity_ledger/social_narrative.yaml:3413-3443` (the `TCK-20260824-GRIEF-NEMESIS-REACHABILITY`
entry block) explicitly documents that ticket's own `Not changed` list, which names
`src/systems/social_systems/memory.py` — confirming this file's functions are established as a
separate, unrelated code path (matches this ticket's own Related Tickets note).

## Prior Work

- `TCK-20260824-GRIEF-NEMESIS-REACHABILITY` (`tickets/done/`, `stored_artifacts/`) is the sibling
  ticket that split this scope out. Its own ticket body states, twice, that
  `check_nemesis_promotion()`/`tick_place_attachment()` are "completely unrelated" to its Campaign
  Orchestrator reachability/event-wiring work, and its Completion Summary's "Not changed" list
  explicitly names `src/systems/social_systems/memory.py`. Confirms this ticket's functions have no
  shared caller, data model, or test dependency with that work — safe to treat as fully independent.
- `tests/refactor/test_public_facades.py::test_system_public_facades` and
  `tests/refactor/test_import_compatibility.py` both import `SocialMemoryService` from the
  `src.systems.social_memory` facade and assert only `is not None` — an import-existence smoke test,
  not a behavioral test of either target function. This confirms the ticket's "zero test coverage"
  claim: no existing test constructs an `EntityState`/`AuthoritativeState` and calls
  `tick_place_attachment()` or `check_nemesis_promotion()` directly anywhere in `tests/`.
  `tests/unit/social/test_social_memory.py` and `tests/integration/scenarios/test_social_memory.py`
  are both **misleadingly named look-alikes** — they test `src.domains.campaigns.social_memory`
  (a different, unrelated module: campaign-mode `SocialMemoryRecord`/`SocialMemoryImporter`), not
  `src/systems/social_systems/memory.py`. Do not confuse the two when picking a test file name.
- `tests/unit/combat/test_combat_ecology.py:35-45` documents (via a scope-note comment and
  `hasattr`/`isinstance` assertions) that "Grudge state (`grudge_history`, `nemesis_ids`,
  `combat_loss_counts`) lives on `SocialComponent`" and is "run-scoped only" — useful confirming
  context for how `grudge_history`/`nemesis_ids` are populated by other systems, though that file
  does not test `check_nemesis_promotion()` itself.
- `tests/helpers/entities.py` provides `make_entity(...)` (supports `grudge_history` but *not*
  `nemesis_ids` or `place_attachment` as keyword params) and `make_state(...)` (supports arbitrary
  `AuthoritativeState` field overrides, e.g. `regions={...}`, via `dataclasses.replace`). Since
  `make_entity()` has no `nemesis_ids`/`place_attachment` params, tests needing those fields should
  either construct entities directly via `V2EntityBuilder(id).kind(...).location(...).social(
  grudge_history=..., nemesis_ids=...).build()` (which does expose both, per
  `src/core/builder.py:496-528`) or use `dataclasses.replace(entity, social=dataclasses.replace(
  entity.social, nemesis_ids={...}))` after `make_entity()`. `tests/unit/progression/
  test_progression_quests.py` and several `tests/unit/world/*` files show the convention for
  constructing `RegionState(id=..., name=..., bounds=(xmin,ymin,xmax,ymax), ...)` directly.

## Risks and Open Questions

- **No genuine bug found in either function during branch analysis, but one real edge-case
  ambiguity worth flagging (not fixing, per ticket scope):** `tick_place_attachment`'s guard is `if
  not region_id:` (line 23), which is truthy-falsy, not an explicit `is None` check. Calling the
  function with `region_id=""` (empty string, as opposed to omitting the argument / passing `None`)
  falls into the **same** auto-detection branch as `region_id=None`, silently ignoring an explicit
  (if degenerate) caller-supplied value rather than treating "" as an explicit-but-invalid `region_id`.
  This is a pre-existing behavior, not something introduced or fixed by this ticket; a test case
  covering `region_id=""` is recommended purely to **pin the current behavior** (belt-and-suspenders
  regression guard), not because it is being changed. Flagged here per this ticket's instruction to
  surface — not silently plan around — anything found while analyzing branches for testability.
- **Parity ledger SOC-050/SOC-066 test_path backfill is an open scope question, not decided here**
  (see Parity Ledger Overlap): both are P0 entries with `test_path: null`, and this ticket's new
  tests are directionally related but not a confirmed 1:1 semantic match to their legacy-checklist
  wording ("PlaceAttachment... supports sentiment" / "Nemesis milestone creation" — neither term
  appears in the current V2 implementation). Recommend the Plan phase decide explicitly whether to
  point `test_path` at the new test file as incidental evidence, or leave the ledger untouched and
  file the P0/test_path gap as its own separate follow-up — do not assume either answer.
  auto-picking one without a decision could misrepresent parity evidence for a mechanic the new
  tests do not actually claim to cover (e.g. "sentiment").
- **Undocumented mechanics**: the 0.001-per-tick place-attachment increment and the 3.0
  grudge-to-nemesis threshold are both hardcoded magic numbers with no `docs/mechanics/` citation.
  Out of scope to document here (test-only chore ticket), but worth a follow-up ticket if these
  values are ever meant to be tunable/formalized as Mechanics Bible law.

## Anti-Drift Hazards

- **Do not implicate `src.domains.campaigns.social_memory`** — `tests/unit/social/
  test_social_memory.py` and `tests/integration/scenarios/test_social_memory.py` are same-named but
  test a completely different module (`SocialMemoryRecord`/`SocialMemoryImporter` in
  `src/domains/campaigns/social_memory.py`, Campaign-mode narrative memory). New tests for this
  ticket must import from `src.systems.social_systems.memory` (or the
  `src.systems.social_memory` facade) and must not be added to either of those existing files, to
  avoid conflating two unrelated "social memory" concepts under one filename.
- **Do not touch the Campaign-mode grief/nemesis reachability path** (`CampaignOrchestrator`,
  `GriefUrgencyImporter`, `NemesisRelationImporter`, `src/domains/campaigns/*`) — confirmed
  unrelated by both this ticket's Out of Scope and the sibling ticket's Completion Summary. Any test
  that ends up importing from `src.domains.campaigns.*` is scope creep.
- **Do not change the threshold constants** (`3.0` grudge threshold, `0.001` place-attachment
  increment) to make a test's assertions rounder/easier — these are production values; tests must
  assert against the real hardcoded constants, not adjust the source to fit a convenient test value.
- **Do not validate `region_id` against `state.regions` inside `tick_place_attachment`** as a
  "fix" — the function's current contract is to trust an explicitly-passed `region_id` without
  cross-checking it exists in `state.regions`; a test asserting otherwise would be asserting
  behavior that does not exist and is out of this ticket's scope to add.
- **`SocialUpdate.nemesis_promotion` order determinism**: `check_nemesis_promotion()`'s output list
  order follows `grudge_history` dict (insertion) order — a multi-entry test must construct
  `grudge_history` with values inserted in a known order and assert the exact list, not just set
  membership, to actually pin this behavior rather than accidentally passing regardless of order.
