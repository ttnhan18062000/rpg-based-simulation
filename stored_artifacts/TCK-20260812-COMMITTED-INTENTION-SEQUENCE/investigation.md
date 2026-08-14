---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260812-COMMITTED-INTENTION-SEQUENCE
artifact_type: investigation
tags: [cognition, strategy, progression]
---

# Investigation — TCK-20260812-COMMITTED-INTENTION-SEQUENCE

## Current Behavior

### `StrategicComponent` / `CognitionProfile` (`src/core/strategic.py`)

`StrategicComponent` is a frozen, `slots=True` dataclass (`strategic.py:345-378`). It currently has
no field resembling an ordered, durable intention sequence. `projects: Dict[str, ProjectState]`
(`:356`) is multi-entry but unordered — dict iteration order is insertion order in CPython but
nothing in the code relies on or preserves a "commitment order"; the one place a `SUSPENDED`
project gets resumed is first-found unordered iteration (`intelligence.py:1248`,
`next((p for p in strat.projects.values() if p.status == ProjectStatus.SUSPENDED), None)`).

`CognitionProfile` (`strategic.py:327-342`) has `max_active_projects: int = 3` (`:333`) as the
direct analogy Design §2 cites for `max_committed_intentions`, and `reserved_detour_depth: int = 2`
(`:342`, comment: "Max nesting depth for detour chains (reserved for future recursive planning)")
which Design §5 confirms is unrelated.

`GoalKind` (`strategic.py:121-147`) has 10 members today: `HARVESTING, FATIGUE, HUNGER, SOCIAL,
TOWN_RETURN, COMBAT_ENGAGE, COMBAT_RETREAT, RECOVER, RESOLVE_BLOCKER, GUILD`, plus 3 added by the
`adventure-cognition-merge` epic: `ADVENTURE_ROUTE = "z_adventure_route"`, `SOCIAL_CONTRACT =
"social_contract"`, `REGION_STABILIZATION = "region_stabilization"` — each with a deliberate
sort-order comment governing `intelligence.py:1408`'s tie-break. No new `GoalKind` is in this
ticket's scope; `CommittedIntention.goal_kind` reuses this vocabulary (Design §2, confirmed against
current code — the enum has not changed since the design doc was written).

### `evaluate_strategic_intent()` (`src/systems/strategic_systems/intelligence.py:1172-1594`)

Five-tier fallthrough, re-verified against current code (matches the design doc's own trace
exactly, same line numbers):

1. **Tier 1** early-exit guards (`:1183-1204`) — inactive/dead/frozen/stunned, worker fast-path.
2. **Tier 2** detour completion → project resumption (`:1225-1260`).
3. **Tier 3** project abandonment / absent check (`:1262-1391`) — nested inside this branch is
   **Tier 4**, unresolved-blocker detour dispatch (`:1363-1391`).
4. **Tier 5** `GoalRegistry.get_all_scores()` (`:1394`) → routine/role utility boost
   (`:1397-1402`, `s.kind.lower()` on each `GoalScore`) → leadership influence (`:1405`) →
   `ScoreModifierSystem.apply_modifiers()` (`:1407`) → `modified_scores.sort(key=lambda x:
   (-x.utility, x.kind))` (`:1408`) → winner-selection loop (`:1410-1415`, first entry with
   `utility >= 20.0` and a resolvable `target_id`/`target_pos`).

**This is the exact tier-5 candidate list AC3 requires touching.** The concrete injection point is
immediately after line 1394 (`all_scores = GoalRegistry.get_all_scores(entity, state)`) and before
line 1397's routine/role-boost comprehension, so a synthesized `GoalScore` for
`committed_intentions[0]` participates in routine/role boosting exactly like a live-scorer
candidate, per the design's own claim that both downstream `.kind` consumers are duplicate-tolerant
(re-verified below).

**Materialization is per-`kind`-branched, not literally "call `RouteToProjectMapper`."** Once
`best_candidate` is selected (`:1410-1415`), `evaluate_strategic_intent()` branches on
`best_candidate.kind` (`:1440-1558`):
- `GoalKind.ADVENTURE_ROUTE` (`:1440-1467`) → `RouteToProjectMapper.map_to_states()`, needs
  `metadata["route_family"]` and `metadata["raw_score"]`.
- `GoalKind.SOCIAL_CONTRACT` (`:1468-1504`) → needs `metadata["contract_id"]`,
  `metadata["proj_kind"]`, `metadata["obj_kind"]`, `metadata["obj_id_prefix"]`,
  `metadata["raw_score"]`.
- `GoalKind.REGION_STABILIZATION` (`:1505-1539`) → needs `metadata["region_id"]`,
  `metadata["proj_kind"]`, `metadata["obj_kind"]`, `metadata["raw_score"]`.
- **Generic else branch** (`:1540-1558`) → the only branch a committed intention can safely use
  without inventing synthetic metadata: builds `ObjectiveState(kind="reach_location", ...)` and
  `ProjectState(kind=best_candidate.kind, score=best_candidate.utility, lock_until_tick=min(tick+10,
  tick+50), ...)` directly from the `GoalScore`'s own fields.

**Risk, not previously called out in the ticket/design doc:** if a `CommittedIntention.goal_kind`
value happens to equal `ADVENTURE_ROUTE`, `SOCIAL_CONTRACT`, or `REGION_STABILIZATION`, the
synthesized `GoalScore` must carry the exact metadata keys that branch's materialization code reads,
or the winner-selection either crashes (`.get()` on missing keys returns `None`, which
`RouteToProjectMapper.get_kinds()`/`ProjectState(kind=None, ...)` will not handle gracefully in all
paths) or produces a malformed project. See Risks below.

Then `evaluate_project_switch()` is called (`:1566`) and, if it returns a `StrategicUpdate` (won),
that's returned; if it returns `None` (lost), execution falls through to bandwidth enforcement
(`:1574-1586`) and the function eventually returns without any record that the committed intention
lost — **today, a losing candidate leaves zero trace**, confirming Design §4's "losing candidate is
simply discarded" claim.

### `evaluate_project_switch()` (`intelligence.py:954-1049`)

Re-read in full. No `kind`-based special case exists except the unconditional `"detour"` bypass at
`:1024-1025`. Function signature: `evaluate_project_switch(entity, candidate_project, current_tick,
state=None)`. Returns `None` at `:1037` (locked, doesn't clear normalized margin/floor) and `:1049`
(unlocked but doesn't beat `effective_current_score`) — both are the "discard" paths Design §4
refers to. **AC3's requirement that this function stay byte-identical is achievable**: nothing in
this ticket's scope requires touching this function's body — the retry bookkeeping the design
mandates lives entirely in how `committed_intentions` state is read/written by the *caller*
(`evaluate_strategic_intent()`), not inside the arbiter. This is empirically checkable post-
implementation via `git diff --stat -- src/systems/strategic_systems/intelligence.py` and, more
precisely, `git diff -- src/systems/strategic_systems/intelligence.py` scoped to confirm no lines
inside the `evaluate_project_switch` function body (`:954-1049`) changed.

### `RouteToProjectMapper` (`src/domains/adventure/mapper.py`, 109 lines, read in full)

`_MAP: Dict[RouteFamily, Tuple[ProjectKind, ObjectiveKind]]` (`:31-47`) is a static data-driven
dict. `get_kinds(family)` (`:49-64`) validates via `RouteFamily(family)` and returns `(None, None)`
for `DEFER_WITH_REASON`. `map_to_states()` (`:66-108`) builds deterministic IDs
(`f"proj.{family.value}.ent{entity_id}.t{tick}"`), an `ObjectiveState`, and a `ProjectState` with
`lock_until_tick=min(tick+10, tick+50)`.

**Important clarification for Plan**: this mapper keys on `RouteFamily`, not `GoalKind` — it is not
directly reusable for committed intentions (which key on `GoalKind`). The design doc's phrase "the
same per-`goal_kind` mapping pattern tier-5 winners already use (the sibling design's own §4
`RouteToProjectMapper` pattern is the precedent...)" should be read as: *mirror the architectural
pattern* (a static, deterministic, data-driven kind→(ProjectKind, ObjectiveKind) mapping consulted
at materialization time) — not literally invoke `RouteToProjectMapper.get_kinds()` on a
`GoalKind` value (it would raise `ValueError` — `RouteFamily(family)` cannot coerce a `GoalKind`
value). For the 8 plain `GoalKind`s with no special branch, the *existing* generic materialization
branch (`intelligence.py:1540-1558`) already does exactly this "per-kind" mapping implicitly (project
`kind` is set directly to `best_candidate.kind`); no new mapper class is required for MVP scope if
committed intentions are restricted to those 8 kinds (see Risks).

## Mechanics / Engine Constraints

- **Durable State Rule (CLAUDE.md)**: `committed_intentions` must have "a typed model, a stable
  location in entity/world/registry state, a defined lifecycle, inspection/debug visibility, and
  tests." The dataclass + `StrategicComponent` field satisfies the first two; the ticket's own scope
  omits the observability item as a genuinely-open question (#5) but the rule is still a **hard
  requirement**, not optional — Plan must pick a concrete minimal surface, not defer it further.
- **`docs/mechanics/04_strategic_cognition.md` §4 "The Project Lifecycle"** (`:107-113`) states the
  chain as "Directive → Project → Objective → Action," describing decomposition of *one* goal, not a
  queue. This is the exact section the ticket must update (confirmed by direct read — the chapter
  currently has no queue/sequence concept anywhere).
- **STRAT-185/186/187** (`docs/parity_ledger/strategic_cognition.yaml:1991-2038`) describe
  `evaluate_project_switch()`'s existing lock/margin/retention logic. Re-verified against current
  code at `intelligence.py:1005-1049` (design doc's own citation of `:1005-1049` for these three
  laws matches current line numbers exactly — no drift since the design doc was written one day
  prior).
- **Strategic/Tactical Rule**: `committed_intentions` sits on the strategy side (durable, ordered,
  multi-tick) — reused GoalKind, no new `GoalScorer`. Confirmed no new scorer class is needed for
  the materialization hook itself (it produces a synthetic `GoalScore`/`ProjectState` inline, not
  through `GoalRegistry.register()`).

## Docs Requiring Update

- `docs/mechanics/04_strategic_cognition.md`: §4 "The Project Lifecycle" (lines 107-113) needs a new
  subsection describing the `committed_intentions` sequence concept, its cap, and its coexistence
  with the single-slot project model, per Design §7.
- `docs/parity_ledger/strategic_cognition.yaml`: a new entry (next available ID is `STRAT-256` —
  highest existing ID in the file is `STRAT-255` at line 3476) documenting the materialization
  mechanism and its retry semantics, per Design §7. Status should be `verified` only once a passing
  `test_path` exists (P0 candidate, since it governs durable-state committed behavior — see Parity
  Ledger Overlap below for the P0-without-test_path precedent this must NOT repeat).
- `docs/simulation/domains/progression_planner_contract.md`: no change required by this ticket's
  scope (Out of Scope explicitly forbids touching `ProgressionPlan.goal_queue`/exporter/importer),
  but the "Episode Boundary Hooks" section (`:69-96`) and the "Only `goal_queue[0]`... Multi-goal
  lookahead is deferred" line (`:123`, verified present at that exact line) should get a one-line
  cross-reference note pointing at the new `committed_intentions` concept so a future reader does not
  conflate the two — this is a judgment call for Plan, not a hard requirement, since the ticket's Out
  of Scope only forbids *behavior* changes to `goal_queue`, not a documentation cross-reference.

## Parity Ledger Overlap

- **STRAT-185** (`:1991-2000`, P0, "Strategic project retention is bounded by interruption
  resistance"): `test_path: null` — **pre-existing gap, not introduced by this ticket**, but directly
  relevant to AC6 ("STRAT-185/186/187 re-run and confirmed still passing"). Since STRAT-185 has no
  assigned test, "still passing" for it can only be confirmed by inspection/manual reasoning (its
  logic is `evaluate_project_switch()`'s retention_margin/effective_current_score computation, still
  unmodified), not a scoped pytest run. Flag this explicitly in Verify — do not silently treat
  STRAT-185 as "passing" via the same mechanism as 186/187 (which have real `test_path`s).
- **STRAT-186** (`:2001-2021`, P0): `test_path:
  tests/unit/strategic/test_score_normalization.py::test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate`
  — exists and is runnable.
- **STRAT-187** (`:2022-2038`, P0): `test_path:
  tests/unit/strategic/test_score_normalization.py::test_locked_system_a_current_still_blocks_low_urgency_system_b_candidate`
  — exists and is runnable.
- New entry for this ticket's own mechanism: none exists yet (confirmed via `grep -n "^- id:"` —
  highest is STRAT-255). Should be added as **P0** given it governs durable committed-state
  materialization into the authoritative project-switch path, with a real `test_path` from day one
  (do not repeat STRAT-185's gap).

## Prior Work

- `stored_artifacts/TCK-20260811-MULTI-STEP-PLANNING-DESIGN/` — the design-scoping ticket itself;
  its `investigation.md` already surveyed the two existing planning concepts
  (`ProgressionPlan.goal_queue`, `GoalRegistry`/tier-5) in depth. No production code landed there
  (confirmed: ticket's own Non-Goals state this explicitly).
- `TCK-20260811-ADVENTURE-GOAL-SCORER` (done) — landed `AdventureGoalScorer`/
  `GoalKind.ADVENTURE_ROUTE`/`RouteToProjectMapper`, the direct precedent for the per-kind
  materialization branch pattern read above.
- `TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION` (done) — moved `_threat_resolved()` into
  `intelligence.py`, added the STRAT-236 early-release check inside `evaluate_project_switch()`'s
  locked branch. Confirms current line numbers (`:1005-1049`) reflect post-epic state.
- `TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION` — replaced the old hardcoded
  `kind=="danger" and score>80` allowlist with the normalized `_score_scale_max()`/
  `_INTERRUPTION_URGENCY_FLOOR_PCT` mechanism now in place; the design doc explicitly analogizes
  against this to argue committed intentions must NOT get arbiter-level special-case priority.
  Confirmed no such special case exists in current code.
- `TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG` — fixed the retention-margin
  normalization denominator; relevant because `RouteToProjectMapper`/social-contract/
  region-stabilization branches all carry inline comments (`:1447-1449`, `:1498-1502`,
  `:1534-1538`) warning never to pass `best_candidate.utility` as `ProjectState.score` — **this
  exact warning applies to committed-intention materialization too**: whatever GoalKind branch a
  committed intention's synthetic candidate lands in, `ProjectState.score` must come from a raw,
  scale-appropriate value, not the normalized `utility` used for tier-5 competition, or this bug
  class reproduces.
- `TCK-20260527-COG-DETOUR-DEPTH` (done) — confirms `reserved_detour_depth`'s naming history
  (renamed from `detour_depth`); independently corroborates Design §5's "not the intended seam"
  conclusion.
- `TCK-20260518-STRATEGIC-WORK-QUEUE` (done) — `StrategicWorkQueue` narrows *which entities* get
  evaluated per tick across urgency tiers; unrelated to per-entity intention sequencing but worth
  Plan being aware of as a distinct "queue" concept in this codebase so naming doesn't collide
  conceptually.

## Risks and Open Questions

Re-verified per the ticket's own instruction, not assumed:

**Duplicate-`GoalKind` coexistence (design doc's traced claim) — RE-CONFIRMED against current
code.** `intelligence.py:1393-1408`'s two `.kind` consumers before winner selection:
(a) `:1399-1400`, `RoutineService.get_routine_utility_boost(entity, s.kind.lower(), ...)` /
`get_role_utility_boost(entity, s.kind.lower())` — independently boosts each `GoalScore` entry, no
uniqueness assumption; (b) `:1408`, `modified_scores.sort(key=lambda x: (-x.utility, x.kind))` — a
stable-sort tie-break tolerant of duplicate `.kind` values. Both still hold exactly as described,
current line numbers unchanged. **Confirmed safe, not assumed.**

**New risk not previously traced (found during this Investigate pass): the per-kind materialization
metadata gap.** If Plan allows `CommittedIntention.goal_kind` to be any of the 13 `GoalKind` values
(not just the 10 pre-epic ones), a committed intention reusing `ADVENTURE_ROUTE`, `SOCIAL_CONTRACT`,
or `REGION_STABILIZATION` needs synthetic `metadata` matching that branch's exact key contract
(traced above) or materialization breaks. Two resolutions, both legitimate implementation-time
judgment calls for Plan: (a) restrict `CommittedIntention.goal_kind` at construction/validation time
to the 10 pre-epic "generic" kinds (simplest, avoids inventing synthetic route/contract/region
metadata that wouldn't correspond to any real route/contract/region), or (b) support all 13 kinds by
having the materialization hook synthesize kind-appropriate metadata. Given the ticket's Scope says
"no branching, no conditional sequences (MVP scope)," (a) is the lower-risk MVP choice, but this is
not decided by the ticket text — Plan must make and document the call.

**No production write path populates `committed_intentions` under this ticket's scope.** The
ticket's Scope implements the *consume* side (materialize `[0]` into tier 5, retry-on-loss
bookkeeping) but nothing in Scope, Related Code Areas, or the design doc's Follow-Up stub creates an
API/system that ever writes real `CommittedIntention` entries into production `StrategicComponent`
state (Open Question 4 — `goal_queue` auto-seed — is explicitly "nice-to-have," not required). This
appears to be intentional narrow MVP scope (the design's Future Extension Patterns section frames
auto-seeding as a later ticket), but it means: (a) the AC's regression test for retry semantics must
construct `committed_intentions` directly via test fixtures/builder, not through any real production
flow; (b) the feature is inert in production until a follow-up ticket adds a write path — this
should be stated plainly in the ticket's Implementation Notes / Completion Summary so it isn't
mistaken for a completed end-to-end feature.

**Durable-state plumbing gap not mentioned anywhere in the ticket or design doc (found during this
Investigate pass) — this is the single largest scope-completeness risk:**
- `StrategicUpdate` (`src/core/updates.py:473-528`) has **no field** for `committed_intentions`.
  Every other `StrategicComponent` collection (`blockers`, `leads`, `directives`, `projects`,
  `concerns`, `candidate_zones`, `hypotheses`, `contracts`, `beliefs`, `turning_points`,
  `source_trust`) has a corresponding `_add_or_update`/`_remove` (or `_add`) pair on
  `StrategicUpdate`, consumed by `StrategicPatch.apply()` (`src/engine/patches.py:402-466`, the
  authoritative merge path). **Neither of these two files is listed in the ticket's Related Code
  Areas.** Without touching them, there is no CLAUDE.md-compliant ("Authoritative application is the
  only place durable state should be committed") way to actually persist a `committed_intentions`
  change — retrying/advancing `sequence_index`/`status` on loss must go through a typed update field,
  not a direct mutation.
- `CapacityEnforcementPhase` (`src/engine/pipeline_phases/capacity_enforcement.py`, read in full,
  186 lines) is the authoritative, established pattern for enforcing every other
  `CognitionProfile`-declared cap (`max_leads`, `max_concerns`, `max_active_projects`,
  `max_hypotheses`, `max_candidate_zones`, `max_turning_points`) via
  `CapacityService.trim_dict`/`trim_list` (score/salience/confidence/urgency-keyed eviction) inside
  the authoritative pipeline, **not** inline inside `evaluate_project_switch()` or
  `evaluate_strategic_intent()`. This directly informs Open Question 1 (cap validation): the
  established architectural precedent is a pipeline-phase enforcement step, not inline validation at
  the arbiter. However, `committed_intentions` is an **ordered Tuple by `sequence_index`**, not a
  `Dict` keyed by `.id` like every field this phase currently handles — trimming by score (like
  projects/leads/concerns) would violate the sequence's own ordering semantics. Plan must decide
  whether enforcement trims from the *tail* (drop lowest-priority future steps, preserving
  `sequence_index` order) rather than by a score-based eviction, which is a genuine deviation from
  the existing `CapacityService.trim_dict` pattern, not a drop-in reuse.
- `StateFingerprinter._strategic_identity()` (`src/replay/fingerprint.py:151-226`, read in full)
  builds the deterministic replay-fidelity hash by explicitly enumerating every
  `StrategicComponent` dict-keyed collection (`projects`, `blockers`, `leads`, `directives`,
  `concerns`, `contracts`, `boredom`) sorted by key, with an explicit docstring warning: "A project
  with ID p1 and a project with ID p2 are different replay states even if both have the same count."
  `committed_intentions` is exactly this kind of replay-visible planning state (an ID-bearing,
  order-sensitive sequence) and is **not currently included**. `tests/integration/kernel/
  test_p1_replay_fidelity.py` exercises this fingerprinter — omitting the new field risks two
  divergent `committed_intentions` states hashing identically, silently breaking replay-divergence
  detection for this feature. This file is also not in the ticket's Related Code Areas.
- `V2EntityBuilder.strategic()` (`src/core/builder.py:445-484`, read in full) — the test-construction
  helper used by essentially every strategic unit test (`_strategic_to_dict()` pattern,
  `test_interruption_resistance.py::_make_entity` reused by `test_score_normalization.py` and
  likely others) has **no `committed_intentions` parameter**. Tests cannot construct an entity with
  a populated `committed_intentions` tuple without this being added — a hard prerequisite for AC4's
  regression test, not an optional nicety.

These four files (`src/core/updates.py`, `src/engine/patches.py`,
`src/engine/pipeline_phases/capacity_enforcement.py`, `src/replay/fingerprint.py`) plus the test
builder (`src/core/builder.py`) are **not listed in the ticket's Related Code Areas** but are, by
direct trace of how every structurally-identical existing field is threaded through the codebase,
required touch points for a CLAUDE.md-compliant implementation. Plan should either add them to the
implementation's actual file list or explicitly justify why each is skippable (e.g., if Plan decides
`committed_intentions` can be `replace()`d directly on `StrategicComponent` without going through
`StrategicUpdate` for MVP — which would itself violate "Durable changes must be represented through
typed records/updates" and should not be the chosen path).

**Open Question 1 (cap validation)**: informed by the `CapacityEnforcementPhase` precedent above —
real precedent exists, but the ordering-vs-score-trim mismatch (Tuple vs Dict) means this is not a
drop-in reuse; Plan must design the actual trim rule.

**Open Question 2 (mid-sequence-skip abandonment semantics)**: no direct precedent found.
`ProjectStatus` (ACTIVE/SUSPENDED/COMPLETED/ABANDONED) governs materialized `ProjectState`s; the
design's sketch adds a parallel, not-yet-precedented `"skipped"` status specific to
`CommittedIntention`. The closest analogous logic is the project-abandonment section
(`intelligence.py:1262-1362`), which transitions status based on biological/environmental triggers
(hunger/fatigue satisfied, node depleted, consecutive-rejection threshold) — but none of those
triggers map cleanly onto "skip step N of an ordered sequence." Genuinely open; Plan must decide the
trigger and whether skip auto-advances to N+1 or halts.

**Open Question 3 (`target_hint` re-resolution failure)**: real precedent found —
`intelligence.py:1458-1467`'s handling of `RouteToProjectMapper.map_to_states()` returning
`(None, None)` ("defensive no-op... not an assumption the mapper always returns non-None") is the
established pattern in this exact function for "resolution produced nothing usable → no-op this
tick, do not crash." Combined with committed intentions' own required retry-on-loss semantics
(Design §4), the natural, precedent-consistent answer is: re-resolution failure → do not materialize
this tick, leave `status="pending"` at the same `sequence_index`, retry next eligible tick (same code
path as a losing-arbitration retry) — rather than immediately abandoning or auto-skipping. This is a
strong recommendation from precedent, not a certainty Plan is bound to, since retrying forever on a
permanently-invalid target_hint (e.g., a razed building) could wedge a sequence indefinitely with no
stated escape hatch — Plan should still decide explicitly, and may want a bounded retry count.

**Open Question 4 (`goal_queue` auto-seed)**: the ticket's own Out of Scope already answers this for
the current ticket — no `ProgressionPlan.goal_queue`/exporter/importer changes are permitted here.
The only remaining judgment call is whether to state this as "deferred to a follow-up ticket" in the
Mechanics Bible update (recommended) versus leaving it unmentioned.

**Open Question 5 (observability surface)**: real precedent found — `EntityInspector`
(`src/observability/live/entity_inspector.py`, read in full) already has a `strategic_summary: Dict`
populated at `:85-90` with `current_project_id`, `blockers_count`, `contracts_count`,
`leads_count`, `boredom`. The lowest-risk, precedent-consistent minimum surface is adding
`committed_intentions_count` (and optionally the head entry's `goal_kind`/`status`) to this same
dict — satisfying the Durable State Rule's "inspection/debug visibility" minimum without inventing a
new endpoint or `EntityInspectionSnapshot` field. This is a strong recommendation, not a mandate;
Plan may choose a `EntityInspectionSnapshot` top-level field instead if richer detail is wanted.

## Anti-Drift Hazards

- **Do not touch `evaluate_project_switch()`'s body.** AC3 requires byte-identical function code;
  the verification command is `git diff --stat -- src/systems/strategic_systems/intelligence.py`
  plus a manual check that only lines inside `evaluate_strategic_intent()` (and the new
  materialization helper, if factored out) changed.
- **Never pass `best_candidate.utility`/a normalized tier-5 utility value into
  `ProjectState.score`** for a materialized committed intention — this exact defect class
  (`TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG`) is called out three times in the
  current code's own comments (`:1447-1449`, `:1498-1502`, `:1534-1538`) precisely because it's easy
  to get wrong when adding a fourth materialization path.
- **Do not give committed intentions arbiter-level priority** (e.g., a new unconditional bypass
  alongside `"detour"` at `:1024-1025`). The design's entire premise (and Goal b) is that they win or
  lose as an ordinary candidate.
- **Do not silently skip the durable-state plumbing** (`StrategicUpdate`, `StrategicPatch.apply()`,
  `V2EntityBuilder.strategic()`, `StateFingerprinter._strategic_identity()`) — see Risks above. A
  `committed_intentions` implementation that only touches `src/core/strategic.py` and
  `src/systems/strategic_systems/intelligence.py` (the ticket's literal Related Code Areas) cannot
  actually persist retry state through the authoritative apply path.
- **Do not introduce a new `GoalKind`** even implicitly (e.g., a `"committed_"`-prefixed sentinel) —
  Scope and Design §2 are explicit that the existing vocabulary must be reused as-is.
- **Do not let `max_committed_intentions` enforcement silently reorder the sequence.** Whatever trim
  rule Plan picks, it must preserve `sequence_index` ordering for surviving entries — a
  score-based `CapacityService.trim_dict`-style eviction (as used for `projects`/`leads`/`concerns`)
  would violate the "ordered" part of the model if applied naively.
