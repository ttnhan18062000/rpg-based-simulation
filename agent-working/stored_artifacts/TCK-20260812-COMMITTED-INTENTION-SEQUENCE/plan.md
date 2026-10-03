---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260812-COMMITTED-INTENTION-SEQUENCE
artifact_type: plan
tags: [cognition, strategy, progression]
---

# Implementation Plan — TCK-20260812-COMMITTED-INTENTION-SEQUENCE

## Summary

This plan lands the `CommittedIntention` durable multi-step planning model exactly as designed in
`docs/architecture/2026-08-12-multi-step-persistent-planning-design.md`: a new frozen dataclass and
`StrategicComponent.committed_intentions: Tuple[CommittedIntention, ...]` field, materialized one
step at a time as an ordinary tier-5 `GoalScore` candidate injected immediately after
`GoalRegistry.get_all_scores()` (`intelligence.py:1394`), competing through the completely
unmodified `evaluate_project_switch()` arbiter. The approach threads the new state through every
layer the Durable State Rule requires — `StrategicUpdate`/`StrategicPatch.apply()` (authoritative
merge), `StateFingerprinter._strategic_identity()` (replay fidelity), `CapacityEnforcementPhase`
(bandwidth cap), `EntityInspector` (debug visibility), and `V2EntityBuilder` (test construction) —
none of which are named in the ticket's own Related Code Areas but are all confirmed, by direct
read, load-bearing for the feature to persist through the authoritative apply path. Retry-on-loss
semantics require **zero new code**: because nothing writes `committed_intentions` on the losing
path, the entry is left untouched automatically — this is stated explicitly as a design decision,
not silently assumed. `GoalKind` is restricted to the 10 pre-epic "generic" values (all of which
already have live registered scorers, per direct read of `src/ai/goals/__init__.py`), enforced at
the materialization hook (not dataclass construction), consistent with the existing
`RouteToProjectMapper` `(None, None)` no-op precedent. All 5 of the ticket's open implementation
questions are resolved below with cited reasoning, not deferred. This plan also corrects one
inaccurate assumption in `test_plan.md`'s proposed New Test 4 (see Design Decision 6).

## Design Decisions

### Decision 1 — The 4+1 "missing" files are IN scope (necessary consequence of AC1)

The ticket's Scope names only `src/core/strategic.py` and
`src/systems/strategic_systems/intelligence.py`. Investigate found four additional files with **no
`committed_intentions` handling** whose absence would make the feature non-durable:
`src/core/updates.py` (`StrategicUpdate`, read at `:473-528`), `src/engine/patches.py`
(`StrategicPatch.apply()`, read at `:402-466`), `src/replay/fingerprint.py`
(`_strategic_identity()`, read at `:151-226`), and `src/engine/pipeline_phases/
capacity_enforcement.py` (`CapacityEnforcementPhase.enforce()`, read in full, 186 lines) — plus
`src/core/builder.py` (`V2EntityBuilder.strategic()`, read at `:445-491`), a hard test-fixture
prerequisite. **Decision: all five are in scope.** CLAUDE.md's Durable State Rule requires "a typed
model, a stable location in entity/world/registry state, a defined lifecycle, inspection/debug
visibility, and tests" for anything surviving beyond one tick — AC1's literal text ("field on
`StrategicComponent`") is silent on *how* that field persists through a tick boundary, but the only
CLAUDE.md-compliant answer, confirmed by how every one of `StrategicComponent`'s 11 existing
collection fields is threaded (`blockers`, `leads`, `directives`, `projects`, `concerns`,
`candidate_zones`, `hypotheses`, `contracts`, `beliefs`, `turning_points`, `source_trust` — all have
`_add_or_update`/`_remove` pairs on `StrategicUpdate`, consumed by `StrategicPatch.apply()`), is to
follow the same pattern. Skipping these files would mean `committed_intentions` could only be
mutated via `dataclasses.replace()` outside the authoritative apply path — an explicit CLAUDE.md
violation ("Authoritative application is the only place durable state should be committed"). These
five files are added to this plan's own touch list; Implement must not treat them as "extra" scope.

### Decision 2 — GoalKind restricted to the 10 pre-epic generic kinds (adopts Investigate's MVP recommendation)

Confirmed by direct read of `src/core/strategic.py:121-147`: `GoalKind` has 13 members — 10
pre-epic "generic" ones (`HARVESTING, FATIGUE, HUNGER, SOCIAL, TOWN_RETURN, COMBAT_ENGAGE,
COMBAT_RETREAT, RECOVER, RESOLVE_BLOCKER, GUILD`) plus 3 epic-added ones
(`ADVENTURE_ROUTE, SOCIAL_CONTRACT, REGION_STABILIZATION`) that materialize through dedicated
per-kind branches (`intelligence.py:1440-1539`) requiring synthetic `metadata` keys
(`route_family`, `contract_id`, `proj_kind`, `obj_kind`, `region_id`, `raw_score`, ...) a committed
intention has no legitimate way to populate without inventing fake route/contract/region data.
**Decision: `CommittedIntention.goal_kind` is enforced at the materialization hook (Step 7) to be
one of the 10 generic values; the 3 epic kinds are silently treated as not-due (no-op this tick),
never crash.** This is the lower-risk MVP choice Investigate recommended, directly required by the
ticket's own Scope line "no branching, no conditional sequences (MVP scope)" — supporting the 3
epic kinds would require branching logic this ticket explicitly excludes. Enforcement lives in the
hook, not a `CommittedIntention.__post_init__` validator: confirmed by grep, no frozen dataclass in
`strategic.py` performs constructor-time validation (`grep -n "__post_init__" src/core/strategic.py`
returns nothing) — adding one would be a new pattern, not a reuse of an existing one. The
no-op-not-crash treatment mirrors the existing `RouteToProjectMapper` `(None, None)` defensive
pattern already documented at `intelligence.py:1458-1467`.

### Decision 3 — `CommittedIntention` has NO field defaults (matches Design §2's sketch literally, avoids a real ordering bug)

Design §2's sketch lists fields in the order `intention_id, goal_kind, target_hint, sequence_index,
status` with **no `=` defaults shown on any field**. This matters mechanically, not just
stylistically: if `target_hint` defaulted to `None` while `sequence_index` (which comes after it in
AC1's literal field order) had no default, Python would reject the dataclass at class-definition
time (`TypeError: non-default argument 'sequence_index' follows default argument`). **Decision: no
field gets a default value** — this is simultaneously the literal reading of the design sketch and
the only way to honor AC1's stated field order without hitting that error. Every caller (test
fixtures now; any future write-path ticket) must pass all 5 fields explicitly, including
`target_hint=None` and `status="pending"` when applicable. `status` stays a bare `str` (not a new
enum), per Design §2's own literal type (`status: str`) — CLAUDE.md's ban on new `GoalKind`s does
not extend to typing `status` as an enum, but the ticket's Out of Scope forbids new `GoalScorer`
machinery generally, and Design §2 did not sketch a new status enum, so this plan does not add one.

### Decision 4 — Materialization hook location and mechanism (verified against current code, not assumed)

Direct read of `evaluate_strategic_intent()` (`intelligence.py:1172-1594`) confirms: unlike Design
§4's framing ("current project absent, abandoned, or completed... triggers tier-5 fallthrough"),
the function reaches `all_scores = GoalRegistry.get_all_scores(entity, state)` (`:1394`)
**unconditionally every eligible tick** unless one of the earlier tier 1/2/3 branches returns early
(worker fast-path `:1193-1204`, detour resume `:1235-1260`, abandonment-threshold / harvesting /
hunger / fatigue / shop-closed early returns `:1281-1360`). The actual protection for a healthy,
locked current project happens **inside** `evaluate_project_switch()`'s own lock/margin logic
(STRAT-186/187), not before tier 5 is reached. This means "when due" for a committed intention
reduces to a single check — `committed_intentions and committed_intentions[0].status == "pending"`
— with no extra gating needed; the arbiter's own existing lock check does the rest, exactly as it
already does for every other tier-5 candidate.

**Injection point** (before `:1397`'s routine/role-boost comprehension, so the synthesized
candidate is boosted like a live one):
```python
if strat.committed_intentions:
    head = strat.committed_intentions[0]
    if head.status == "pending":
        try:
            head_kind = GoalKind(head.goal_kind)
        except ValueError:
            head_kind = None
        if head_kind in _COMMITTED_INTENTION_ELIGIBLE_KINDS:
            all_scores = all_scores + [GoalScore(
                kind=head_kind,
                utility=_COMMITTED_INTENTION_BASE_UTILITY,
                target_id=head.target_hint,
                target_pos=None,
                metadata={"committed_intention_id": head.intention_id},
            )]
```
New imports required: `from src.ai.goals.base import GoalScore` (confirmed `GoalScore` is defined at
`src/ai/goals/base.py:9` but **not** re-exported from `src/ai/goals/__init__.py:1-10`, which
`intelligence.py:78` currently imports `GoalRegistry` from — a direct `base` import is required, not
an addition to the existing `from src.ai.goals import GoalRegistry` line). Two new module-level
constants, placed beside `_GOAL_UTILITY_SCORE_MAX`/`_INTERRUPTION_URGENCY_FLOOR_PCT`
(`intelligence.py:32-53`):
```python
_COMMITTED_INTENTION_BASE_UTILITY: float = 50.0  # fixed, mid-scale (20.0 floor < 50.0 < 100.0 ceiling)
_COMMITTED_INTENTION_ELIGIBLE_KINDS = frozenset({
    GoalKind.HARVESTING, GoalKind.FATIGUE, GoalKind.HUNGER, GoalKind.SOCIAL,
    GoalKind.TOWN_RETURN, GoalKind.COMBAT_ENGAGE, GoalKind.COMBAT_RETREAT,
    GoalKind.RECOVER, GoalKind.RESOLVE_BLOCKER, GoalKind.GUILD,
})
```
The `metadata={"committed_intention_id": ...}` tag is required, not decorative: since all 10
eligible kinds already have live registered scorers (confirmed —
`src/ai/goals/__init__.py:12-21` registers a scorer for every one of the 10), a committed
intention's synthesized candidate and a live scorer's candidate for the *same* `GoalKind` can both
be `best_candidate` on different ticks. The metadata tag is the only reliable way to detect,
downstream, that *this specific* win came from the committed intention (not a coincidental
same-kind live scorer) — needed for the win-transition bookkeeping in Decision 5.

**Materialization branch reuse — no new branch added.** Because the 10 eligible kinds never equal
`ADVENTURE_ROUTE`/`SOCIAL_CONTRACT`/`REGION_STABILIZATION`, a committed intention's synthesized
candidate that wins `best_candidate` selection always falls into the existing **generic `else`
branch** (`intelligence.py:1540-1558`), completely unmodified. No new `elif best_candidate.kind ==
...` branch is added to this dispatch chain — the materialization hook only ever appends to
`all_scores`.

### Decision 5 — Win-transition bookkeeping (the only new code on the "win" path)

Direct read of `_score_scale_max()` (`intelligence.py:91-109`) resolves a scale question the
anti-drift hazard in `investigation.md` raises but does not fully settle: `_score_scale_max`
classifies by `isinstance(kind, ProjectKind)` — the three special branches build a real `ProjectKind`
member (a *different* enum class than `GoalKind`) for `ProjectState.kind`, triggering the
2.9-ceiling `_ADVENTURE_ROUTE_SCORE_MAX` scale, which is why they must use `metadata["raw_score"]`
instead of `utility`. The **generic branch** (`:1549-1558`) sets `kind=best_candidate.kind` — for a
tier-5 `GoalRegistry` candidate this is a `GoalKind` instance, so `_score_scale_max` returns
`_GOAL_UTILITY_SCORE_MAX` (100.0), the *same* scale `utility` already lives on, and the generic
branch's own existing code already does `score=best_candidate.utility` (`:1557`) — scale-correct,
not a bug. A committed intention restricted to the 10 generic kinds always lands in this branch, so
**`ProjectState.score == best_candidate.utility` (== `_COMMITTED_INTENTION_BASE_UTILITY`) is
correct, expected behavior for this feature, not the
`TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG` defect class recurring.** See Decision
6 for the resulting test-plan correction.

The only new code on the win path lives inside the existing `if switch_up:` block
(`intelligence.py:1566-1572`), which already returns early — this is inside
`evaluate_strategic_intent()`, never inside `evaluate_project_switch()`'s own body (`:954-1049`), so
AC3's byte-identical requirement is untouched:
```python
if switch_up:
    extra_ci = {}
    if strat.committed_intentions and best_candidate.metadata.get("committed_intention_id") == strat.committed_intentions[0].intention_id:
        extra_ci["committed_intentions_add_or_update"] = [replace(strat.committed_intentions[0], status="active")]
    return replace(switch_up,
        boredom_delta=boredom_upd,
        leads_add_or_update=memory_upd.leads_add_or_update,
        leads_remove=memory_upd.leads_remove,
        **extra_ci
    )
```

### Decision 6 — Correction to `test_plan.md`'s New Test 4

`test_plan.md`'s New Test 4 (`test_committed_intention_materializes_with_raw_score_not_utility`)
assumes the same "never pass `utility`" invariant that applies to the three special branches also
applies to committed intentions, "mirror[ing] the three existing `test_*_winner_materializes_with_
raw_score_not_utility` tests." **This assumption is incorrect for this feature**, per Decision 5's
scale trace: committed intentions deliberately *do* materialize via the generic branch using
`utility` directly, because `ProjectState.kind` stays a `GoalKind` instance (100-ceiling scale), not
a `ProjectKind` instance (2.9-ceiling scale). Implementing New Test 4 as literally described would
assert a false invariant. **Decision: replace New Test 4 with
`test_committed_intention_materializes_via_generic_branch_with_scale_consistent_score`**, asserting
(a) `candidate_proj.kind` is a `GoalKind` instance (not reclassified into `ProjectKind`), confirming
the committed intention did not accidentally get routed through a special branch, and (b)
`ProjectState.score == best_candidate.utility == _COMMITTED_INTENTION_BASE_UTILITY` (scale-consistent
by construction, not a regression of the retention-margin scale bug). This is corrected, not
silently dropped — the underlying anti-drift concern (never pass a wrongly-scaled value into
`ProjectState.score`) is still tested, just with the scale-correct assertion for this feature's own
materialization path.

### Decision 7 — Open Question 1 (cap validation / `max_committed_intentions` enforcement)

`CapacityEnforcementPhase` (`src/engine/pipeline_phases/capacity_enforcement.py`, read in full) is
the correct precedent — it already enforces every other `CognitionProfile` cap
(`max_leads`, `max_concerns`, `max_active_projects`, `max_hypotheses`, `max_candidate_zones`) via
`CapacityService.trim_dict`/`trim_list` (`src/strategy/capacity.py`, read in full). But
`committed_intentions` is an **ordered `Tuple`, not a `Dict`** — a score-based eviction (as used for
projects/leads/concerns, dropping the *lowest-score* entry) would violate `sequence_index` ordering
if applied naively. **Decision: reuse `CapacityService.trim_list()` (not `trim_dict()`) with a
score function that encodes order-priority instead of a domain score:**
`score_func=lambda ci: -ci.sequence_index`. `trim_list`'s own documented behavior
(`capacity.py:32-52`) is "if `score_func` is provided, drops lowest scores... `sorted(data,
key=score_func, reverse=True)[:max_size]`" — with `score_func=lambda ci: -ci.sequence_index`, this
sorts by *ascending* `sequence_index` and keeps the first `max_size` entries, i.e. it drops the
**highest**-`sequence_index` (furthest-future, lowest-priority) entries first and preserves the
front of the sequence. This is a genuine, cited deviation from the score-based pattern (as
Investigate's Risks section flagged would be needed), implemented by reusing the existing generic
`trim_list` utility with an order-encoding `score_func` — no new method added to
`CapacityService`. `max_committed_intentions=3`'s literal value is **not** re-tuned by this ticket —
Design's own Open Question 1 asks only whether 3 is empirically right; this plan's decision is to
keep the design's stated default and treat further tuning as a future ticket's job if evidence
emerges, consistent with the ticket's own Scope line "Cap sequences at `max_committed_intentions=3`
entries."

### Decision 8 — Open Question 2 (mid-sequence-skip abandonment semantics)

No direct precedent exists for a "skip step N, advance to N+1" trigger (Investigate confirmed).
Combined with Finding #4 (no production write path exists in this ticket's scope — nothing ever
constructs a `CommittedIntention` in production code under this ticket), auto-advance/skip logic
would be genuinely untestable end-to-end and unreachable in production either way. **Decision: this
ticket implements no skip-trigger and no auto-advance mechanism.** The materialization hook (Step 7)
only ever reads `committed_intentions[0]`; if its `status` is anything other than `"pending"`
(including a hypothetical future `"skipped"`), the hook treats the head as not-due and does nothing
— it does **not** look at `committed_intentions[1]`. This is the literal, minimal reading of the
ticket's own "no branching, no conditional sequences (MVP scope)" line: advancing past a
skipped/abandoned head to the next index *is* a form of conditional-sequence logic, and is
explicitly deferred to a future ticket that would also need to add the write path that could ever
produce a non-`"pending"` head in the first place. State this plainly in Implementation Notes.

### Decision 9 — Open Question 3 (`target_hint` re-resolution failure)

Adopts Investigate's precedent-grounded recommendation with one refinement found during this
Plan pass: **no bespoke re-resolution logic is needed at all.** If `target_hint` is `None`, the
synthesized `GoalScore` (Decision 4) has `target_id=None, target_pos=None`. The existing
winner-selection loop's own floor check (`intelligence.py:1412`,
`if g_score.utility < 20.0 or (g_score.target_id is None and g_score.target_pos is None): continue`)
already skips any candidate with no resolvable target — a committed intention with no `target_hint`
can never become `best_candidate` and therefore never materializes, with zero new code. This is a
free, precedent-consistent "no-op this tick, retry next tick" (the candidate is re-synthesized and
re-offered — and re-skipped — every eligible tick until `target_hint` is set by whatever future
write path populates it), reusing the arbiter's own existing filter rather than inventing a resolver
or a bounded-retry counter. **Known limitation, stated explicitly, not silently accepted**: since no
write path exists in this ticket's scope (Finding #4) to ever *set* `target_hint` after construction,
a permanently-`None` `target_hint` would retry forever once a future write path exists — that
follow-up ticket must decide whether to bound the retry count; this ticket does not need to, since it
never produces such an entry itself.

### Decision 10 — Open Question 4 (`goal_queue` auto-seed)

The ticket's own Out of Scope already forbids `ProgressionPlan.goal_queue`/`PlanRevisionService`/
Exporter/Importer changes. **Decision: no auto-seed code, and the Mechanics Bible update (Step 12)
states this is deferred to a future ticket** (per Design's own "Future Extension Patterns" framing),
rather than leaving the relationship unmentioned.

### Decision 11 — Open Question 5 (observability surface)

Adopts Investigate's recommendation: `EntityInspector.strategic_summary`
(`src/observability/live/entity_inspector.py:85-91`, read in full) already holds
`current_project_id`, `blockers_count`, `contracts_count`, `leads_count`, `boredom` as a flat dict
populated inline in `inspect_entity()`. **Decision: add `committed_intentions_count` (int) and
`committed_intention_head` (a small dict with `goal_kind`/`status`/`sequence_index`, or `None` when
empty) to this same dict** — satisfies the Durable State Rule's "inspection/debug visibility"
minimum without a new `EntityInspectionSnapshot` field or a new endpoint.

## Steps

### Step 1 — `CommittedIntention` dataclass + `StrategicComponent.committed_intentions` field
**Files:** `src/core/strategic.py`
**Change:** Add, after `SourceTrustEntry` (currently ending at `:324`) and before `CognitionProfile`
(currently `:327-342`):
```python
@dataclass(frozen=True, slots=True)
class CommittedIntention:
    """One step in a short, ordered, durable sequence of future intentions."""
    intention_id: str
    goal_kind: str
    target_hint: Optional[str]
    sequence_index: int
    status: str
```
No field defaults — see Design Decision 3. Add to `StrategicComponent` (`:345-378`, verified via
direct read), in the "Core state" group alongside the other collection fields (after `beliefs:
Dict[str, Any]` at `:363`, before "Active tracking" at `:365`):
```python
committed_intentions: Tuple[CommittedIntention, ...] = field(default_factory=tuple)
```
`Tuple` is **not** currently imported in this file — confirmed by direct read of the import block
(`strategic.py:4-6`: `from typing import Dict, Any, Optional, List`, no `Tuple`). Add `Tuple` to this
import line as part of this step (`from typing import Dict, Any, Optional, List, Tuple`).
**Do NOT touch:** `GoalKind` enum (`:121-147`), `ProjectKind`, any other dataclass in this file.
**Verify:** `tests/unit/strategic/test_committed_intention_model.py::test_committed_intention_dataclass_shape`
(new).

### Step 2 — `CognitionProfile.max_committed_intentions`
**Files:** `src/core/strategic.py`
**Change:** Add `max_committed_intentions: int = 3` to `CognitionProfile` (`:327-342`, verified via
direct read), after `reserved_detour_depth: int = 2` (`:342`), mirroring `max_active_projects: int =
3`'s existing pattern (`:333`).
**Do NOT touch:** `reserved_detour_depth` itself — confirmed unrelated by Design §5 and by
`TCK-20260527-COG-DETOUR-DEPTH`'s naming history; do not rename, remove, or repurpose it.
**Verify:** `tests/unit/strategic/test_committed_intention_model.py::test_cognition_profile_max_committed_intentions_default`
(new).

### Step 3 — `V2EntityBuilder.strategic()` test-fixture parameter
**Files:** `src/core/builder.py`
**Change:** `V2EntityBuilder.strategic()` (`:445-491`, read in full) has no `committed_intentions`
parameter today — confirmed by direct read of its full keyword-argument list
(`home_region_id` through `boredom`). `CommittedIntention` is also not yet imported into this file —
confirmed by direct read of the `from src.core.strategic import (...)` block (`:33-46`), which lists
`StrategicComponent, CognitionProfile, ProjectState, BlockerState, LeadState, DirectiveState,
ConcernState, CandidateZone, HypothesisState, SourceTrustEntry, TurningPointState, ContractState` —
no `CommittedIntention`; add it to this import block. `Tuple` is also not imported from `typing`
here (`:6`: `from typing import Any, Dict, Iterable, List, Mapping, Optional, Set`, no `Tuple`) —
add it. Then add `committed_intentions: Optional[Tuple[CommittedIntention, ...]] = None` to the
`.strategic()` signature, and thread it through the existing `updates = {...}` dict /
`current[key] = value` merge loop (`:465-490`) exactly like every other collection parameter (e.g.
`turning_points`, which uses `_copy_list(...)  if turning_points is not None else None` — for a
`Tuple` field, use `tuple(committed_intentions) if committed_intentions is not None else None`,
matching this file's existing `_copy_dict`/`_copy_list` helper pattern rather than inventing a new
one).
**Do NOT touch:** any other `V2EntityBuilder` method (`.cognition()` at `:395+`, `.social()` at
`:493+`, etc.).
**Verify:** `tests/unit/strategic/test_committed_intention_materialization.py::
test_builder_supports_committed_intentions` (new; test_plan.md's New Test 11).

### Step 4 — `StrategicUpdate` fields for `committed_intentions`
**Files:** `src/core/updates.py`
**Change:** `StrategicUpdate` (`:473-528`, read in full) has an `_add_or_update`/`_remove` list pair
for every one of `StrategicComponent`'s 11 collection fields — none exist for
`committed_intentions`. `CommittedIntention` also needs adding to this file's `TYPE_CHECKING`-guarded
import block (`:7-13`: `from src.core.strategic import (ConcernState, CandidateZone,
HypothesisState, SourceTrustEntry, CognitionProfile, BlockerState, LeadState, DirectiveState,
ProjectState, ContractState, TurningPointState)` — confirmed by direct read, no `CommittedIntention`
present; `Tuple` is already imported at `:6`, no action needed there). Add, following the exact
existing pattern (e.g. `contracts_add_or_update`/ `contracts_remove` at `:504-505`):
```python
# Committed Intentions
committed_intentions_add_or_update: list[CommittedIntention] = field(default_factory=list)
committed_intentions_remove: list[str] = field(default_factory=list)  # by intention_id
```
**Other writers to this same dataclass, and how this interacts with them:** `StrategicUpdate` is
returned from many call sites across `intelligence.py`, `detour.py`, `belief.py`, and others — all
of them construct a fresh `StrategicUpdate(...)` with only the fields they care about, relying on
`field(default_factory=list)` defaults for everything else. Adding two new list-typed fields with
`default_factory=list` is additive and backward-compatible: every existing call site continues to
construct `StrategicUpdate()` instances with `committed_intentions_add_or_update=[]` /
`committed_intentions_remove=[]` implicitly, changing nothing about their behavior. Update
`is_noop()` (`:515-528`) to include `and not self.committed_intentions_add_or_update and not
self.committed_intentions_remove` in the boolean chain — every caller that checks `is_noop()`
(e.g. `StrategicPatch.is_noop()` at `patches.py:406-407`) must correctly treat a
committed-intentions-only update as non-noop, or Step 7's win-transition update could be silently
dropped. Update `merge()` (`:530-566`) to concatenate the two new list fields exactly like
`contracts_add_or_update`/`contracts_remove` are concatenated (`:559-560`) — `merge()` is called
whenever two `StrategicUpdate`s from the same tick are combined (e.g.
`intelligence.py:1386-1391`'s `replace(detour_up, ...)` pattern uses `replace`, not `merge`, for
most sites, but `merge()` itself is a public method other subsystems may call; omitting the new
fields from `merge()` would silently drop committed-intention changes whenever it is used).
**Do NOT touch:** any other field or method on `StrategicUpdate`, `RewardUpdate`, `StaminaUpdate`,
or `WoundUpdate` in this same file.
**Verify:** exercised indirectly by
`tests/unit/strategic/test_committed_intention_materialization.py::
test_committed_intention_head_materializes_as_ordinary_tier5_candidate` (new; requires `is_noop()`
to correctly report non-noop and `merge()`/`replace()` to correctly carry the new fields through to
`StrategicPatch.apply()` in Step 5).

### Step 5 — `StrategicPatch.apply()` order-preserving merge
**Files:** `src/engine/patches.py`
**Change:** `StrategicPatch.apply()` (`:415-466`, read in full) is the sole authoritative merge path
for `StrategicComponent` — it builds every dict-shaped collection via the local `merge_dict(
current_dict, add_list, remove_list)` helper (`:421-429`), which is not directly reusable here
because `committed_intentions` is stored as an ordered `Tuple`, not a `Dict`, and needs its
resulting order to reflect `sequence_index`, not dict-insertion order. Add a second local helper,
`merge_committed_intentions`, following `merge_dict`'s own shape but keyed and re-sorted:
```python
def merge_committed_intentions(current_tuple, add_list, remove_list):
    if not add_list and not remove_list:
        return current_tuple
    by_id = {ci.intention_id: ci for ci in current_tuple}
    for item in add_list:
        by_id[item.intention_id] = item
    for item_id in remove_list:
        by_id.pop(item_id, None)
    return tuple(sorted(by_id.values(), key=lambda ci: ci.sequence_index))
```
Call it alongside the existing `merge_dict(...)` calls (`:431-439`):
```python
nci = merge_committed_intentions(new_strat.committed_intentions, u_strat.committed_intentions_add_or_update, u_strat.committed_intentions_remove)
```
and add `committed_intentions=nci` to the final `replace(new_strat, ...)` call (`:458-465`). No
`shallow_freeze()` call is needed for this field — `committed_intentions` is already an immutable
`Tuple` of frozen dataclasses, unlike the `Dict`-typed fields that need `shallow_freeze()` to become
`ReadOnlyDict`s.
**Other writers to `entity.strategic` via this same `apply()` method:** this is the single
authoritative merge point for every `StrategicUpdate` field (Step 4's list). No other code path
mutates `StrategicComponent` outside this function (confirmed by the design doc's own trace: "the
only legitimate write path today is `evaluate_project_switch()`" for `current_project_id`
specifically, and this `apply()` method for every other field) — the two unguarded
`current_project_id_set=""` clear-only writers (`engine/tactical.py:194`,
`pipeline_phases/guild_visit.py:88`, per the design doc's own citation) never touch
`committed_intentions`, so there is no additional writer to reconcile here.
**Do NOT touch:** `merge_dict()` itself (used by 9 other collections — do not generalize it to
handle ordering, since none of its other callers need that, and doing so risks regressing an
unrelated collection's behavior), `EquipmentPatch.apply()`, `QuestPatch`.
**Verify:** `tests/unit/strategic/test_committed_intention_materialization.py::
test_committed_intention_head_materializes_as_ordinary_tier5_candidate` (new) — this test's
assertion that a win is durably reflected in `StrategicComponent.committed_intentions` after
applying the returned `StrategicUpdate` exercises this exact merge path end-to-end.

### Step 6 — `StateFingerprinter._strategic_identity()` fingerprint inclusion
**Files:** `src/replay/fingerprint.py`
**Change:** `_strategic_identity()` (`:151-226`, read in full) explicitly enumerates every
`StrategicComponent` dict-keyed collection sorted by key (`projects`, `blockers`, `leads`,
`directives`, `concerns`, `contracts`, `boredom`), with a docstring warning that count-only
comparison is insufficient — `committed_intentions` is not present. Add, following the existing
`project_ident`-style pattern (`:163-170`), sorted by `sequence_index` (not insertion order, for
determinism regardless of construction order):
```python
committed_intention_ident = "|".join(
    f"{ci.intention_id}:"
    f"{ci.goal_kind}:"
    f"{ci.sequence_index}:"
    f"{ci.status}:"
    f"{ci.target_hint}"
    for ci in sorted(strategic.committed_intentions, key=lambda c: c.sequence_index)
)
```
and add `f"committed_intentions=[{committed_intention_ident}];"` to the final returned f-string
(`:218-226`), placed after `projects=[...]` (grouping it with the other planning-state fields, ahead
of the more peripheral `blockers`/`leads`/`directives`/`concerns`/`contracts`/`boredom` entries — a
readability choice, not a functional requirement, since every segment is delimited and order within
the joined string does not affect hash-collision safety as long as it is deterministic).
**Other writers/readers of this fingerprint:** `_strategic_identity()` is called from
`StateFingerprinter`'s top-level `fingerprint()` method (not modified by this step) alongside
`_group_identity()` and other component identities — this step only adds one more input string to
an already-concatenated whole; no other caller needs to change. `tests/integration/kernel/
test_p1_replay_fidelity.py` is the sole consumer that exercises this method's output for
divergence-detection assertions.
**Do NOT touch:** `_group_identity()` or any other `_*_identity()` static method in this class.
**Verify:** `tests/integration/kernel/test_p1_replay_fidelity.py::
test_committed_intentions_included_in_replay_fingerprint` (new; test_plan.md's New Test 10) —
constructs two otherwise-identical `AuthoritativeState`s differing only in `committed_intentions`
and asserts different `state_hash` values.

### Step 7 — Materialization hook in `evaluate_strategic_intent()`
**Files:** `src/systems/strategic_systems/intelligence.py`
**Change:** Per Design Decisions 4 and 5 above (full code and citations there). Summary: (a) two new
module-level constants (`_COMMITTED_INTENTION_BASE_UTILITY`,
`_COMMITTED_INTENTION_ELIGIBLE_KINDS`) near `:32-53`; (b) one new import,
`from src.ai.goals.base import GoalScore`; (c) the injection block immediately after `:1394`
(`all_scores = GoalRegistry.get_all_scores(...)`), before `:1397`'s comprehension; (d) the
win-transition block inside the existing `if switch_up:` branch (`:1566-1572`). **No new `elif
best_candidate.kind == ...` branch is added** — the existing generic branch (`:1540-1558`) handles
materialization unmodified, confirmed scale-safe by Decision 5.
**Do NOT touch:** `evaluate_project_switch()`'s own body (`:954-1049`) — zero lines inside this
function's line range may change. This is the ticket's single most important guard; see Step 11.
Also do not touch the three special `elif` branches (`:1440-1539`), the winner-selection loop's
floor check (`:1410-1415`), or `modified_scores.sort(...)` (`:1408`) — the duplicate-`GoalKind`
tolerance these depend on is re-verified, not re-implemented (see `test_duplicate_goal_kind_...`
below).
**Verify:** `tests/unit/strategic/test_committed_intention_materialization.py::
test_committed_intention_head_materializes_as_ordinary_tier5_candidate`,
`::test_committed_intention_materializes_via_generic_branch_with_scale_consistent_score` (Decision
6's corrected New Test 4), `::test_committed_intentions_participate_in_routine_role_boosting`
(test_plan.md New Test 7), `::test_duplicate_goal_kind_committed_intention_and_live_scorer_coexist`
(test_plan.md New Test 8).

### Step 8 — Retry-on-loss semantics (documentation + regression test only, no new code)
**Files:** none (documentation in `Implementation Notes`; test only)
**Change:** As established in Design Decision 4/5, a committed intention that loses tier-5
arbitration — either because a different candidate wins, or because it wins `best_candidate`
selection but loses inside `evaluate_project_switch()` (`switch_up is None`, falling through to
`:1574-1594`) — triggers **no code path that touches `committed_intentions`**, because the
win-transition block (Step 7d) only executes `if switch_up:`. The entry is therefore left exactly as
it was: `sequence_index 0`, `status "pending"`. This must be stated explicitly in the ticket's
Implementation Notes as the mechanism (not a "TODO: implement retry"), since it is easy to mistake a
structural absence-of-code for an unimplemented requirement.
**Do NOT touch:** nothing to touch — this step exists to make the absence-of-change traceable and
tested, not to add code.
**Verify:** `tests/unit/strategic/test_committed_intention_materialization.py::
test_losing_committed_intention_retries_next_eligible_tick` (new; test_plan.md's New Test 5 — the
ticket's own explicitly required AC4 regression test). Must assert across two simulated ticks per
test_plan.md's spec: tick N loses arbitration, tick N+1 (unchanged world state) the same entry is
still present at `sequence_index 0` with unchanged `status` and is still eligible to compete.

### Step 9 — `CapacityEnforcementPhase` cap enforcement
**Files:** `src/engine/pipeline_phases/capacity_enforcement.py`
**Change:** Per Design Decision 7. Add a 7th enforcement block (after "6. Enforce Candidate Zones",
`:117-130`), following the file's own established shape but using `trim_list` instead of
`trim_dict` (since `committed_intentions` is list/tuple-shaped, not dict-shaped):
```python
# 7. Enforce Committed Intentions (ordered by sequence_index -- NOT score-based, unlike 1-6 above)
ci_removals = []
if len(entity.strategic.committed_intentions) + len(strat_upd.committed_intentions_add_or_update) > profile.max_committed_intentions:
    by_id = {ci.intention_id: ci for ci in entity.strategic.committed_intentions}
    for ci in strat_upd.committed_intentions_add_or_update:
        by_id[ci.intention_id] = ci
    for ci_id in strat_upd.committed_intentions_remove:
        by_id.pop(ci_id, None)
    combined = list(by_id.values())
    survivors = CapacityService.trim_list(combined, profile.max_committed_intentions, score_func=lambda ci: -ci.sequence_index)
    survivor_ids = {ci.intention_id for ci in survivors}
    ci_removals = [ci.intention_id for ci in combined if ci.intention_id not in survivor_ids]
```
Fold `ci_removals` into the existing `new_*_remove` reconciliation (`:138-142`) as
`new_committed_intentions_remove = list(set(strat_upd.committed_intentions_remove) |
set(ci_removals))`, add it to the `any_removals` check (`:133`) and to the `replace(strat_upd, ...)`
call (`:144-154`), matching how `leads_remove`/`concerns_remove`/etc. are already folded in.
**Other writers to this same phase's output (`StateUpdate.entity_updates`):** `CapacityEnforcementPhase.enforce()`
is itself the sole writer of capacity-trim removals — it is one phase in the authoritative pipeline,
reading `update.entity_updates` (produced by upstream phases, including Step 7's materialization
hook) and returning a refined copy. No other phase enforces `max_committed_intentions`; this is the
single, correct enforcement point, matching how the other 5 caps are enforced nowhere else in the
codebase (confirmed: `grep -rn "max_active_projects\|max_leads\|max_concerns" src/` for enforcement,
not just reads, surfaces only this file). The dirty-set gating (`get_relevant_entity_ids(state,
update, "capacity")` at `:26`, mapping to `ds.strategic_entities` per `src/core/dirty.py:32-33`) is
already generic to "any strategic update," not field-specific — confirmed by direct read — so no
change to `src/core/dirty.py` is needed for `committed_intentions`-only updates to be picked up.
**Do NOT touch:** enforcement blocks 1-6 (`:44-130`), `_score_lead()` (`:176-185`), or
`CapacityService.trim_dict`/`trim_list` themselves in `src/strategy/capacity.py` — `trim_list`'s
existing `score_func` parameter already supports this use case without modification.
**Verify:** `tests/unit/strategic/test_committed_intention_model.py::
test_max_committed_intentions_cap_enforced` (new; test_plan.md New Test 9) — place in
`tests/unit/strategic/test_capacity_enforcement.py` instead if Implement judges that file (confirmed
to exist, read in part, covers `enforce_bandwidth`/leads/concerns/hypotheses/projects trimming for
this exact phase) a better fit than a new model-test file; either location is acceptable as long as
the test exists and is wired into the scoped pytest command.

### Step 10 — `EntityInspector.strategic_summary` observability surface
**Files:** `src/observability/live/entity_inspector.py`
**Change:** Per Design Decision 11. Add to the `strategic_sum` dict (`:85-91`, read in full):
```python
"committed_intentions_count": len(entity.strategic.committed_intentions),
"committed_intention_head": (
    {
        "goal_kind": entity.strategic.committed_intentions[0].goal_kind,
        "status": entity.strategic.committed_intentions[0].status,
        "sequence_index": entity.strategic.committed_intentions[0].sequence_index,
    }
    if entity.strategic.committed_intentions else None
),
```
**Do NOT touch:** `combat_sum`, `inventory_sum`, the `quests` list, the timeline-events section
(`:93+`), or `EntityInspectionSnapshot`'s pydantic model (`entity_inspector.py:8-36`) — the surface
lives inside the existing `strategic_summary: Dict[str, Any]` field, no new pydantic field needed.
**Verify:** `tests/unit/strategic/test_committed_intention_materialization.py::
test_committed_intention_observability_surface` (new; test_plan.md New Test 12) — locate or create
the appropriate `EntityInspector` test file at Implement time (test_plan.md notes none was found
already covering `strategic_summary` during Investigate).

### Step 11 — Architecture guard: `evaluate_project_switch()` byte-identical
**Files:** new test file, `tests/architecture/test_committed_intention_arbiter_byte_identical_guard.py`
(directory confirmed to exist and already hold architecture-guard-style tests, e.g.
`test_phase18_import_boundaries.py`, `test_no_new_hardcoded_gameplay_truth.py`)
**Change:** Add a source-hash guard test using the golden value captured **before** any
implementation work in this ticket began (computed directly against the current repo state during
this Plan phase, `.venv/bin/python3 -c "import hashlib, inspect; from
src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem; print(hashlib.sha256(
inspect.getsource(StrategicIntelligenceSystem.evaluate_project_switch).encode()).hexdigest())"`):
```python
import hashlib
import inspect

from src.systems.strategic_systems.intelligence import StrategicIntelligenceSystem

_GOLDEN_SHA256 = "635bc4f274f3110c8bd0c130a85bc548e517b4247df33cf426bcec81e6eb80f3"  # 96 lines, captured pre-TCK-20260812-COMMITTED-INTENTION-SEQUENCE


def test_evaluate_project_switch_source_hash_unchanged():
    src = inspect.getsource(StrategicIntelligenceSystem.evaluate_project_switch)
    assert hashlib.sha256(src.encode()).hexdigest() == _GOLDEN_SHA256, (
        "evaluate_project_switch() body changed -- this ticket (TCK-20260812-COMMITTED-INTENTION-SEQUENCE) "
        "requires it to stay byte-identical (AC3). If a change here is genuinely intended for other reasons, "
        "update _GOLDEN_SHA256 deliberately and note why in the commit, not as a silent side effect of this ticket."
    )
```
Recommended to add this step **first**, before Step 7's edits begin, so Implement has a continuously
running tripwire while writing the materialization hook.
**Do NOT touch:** the golden hash value itself, unless a change to `evaluate_project_switch()` is
independently and deliberately intended (which this ticket's Out of Scope forbids).
**Verify:** the test itself, run both before and after Step 7's edits — must pass in both runs.

### Step 12 — Mechanics Bible update
**Files:** `docs/mechanics/04_strategic_cognition.md`
**Change:** Add a new subsection "### Committed Intentions (Multi-Step Planning)" to `## 4. The
Project Lifecycle` (currently `:107-113`, a 4-item list describing single-goal decomposition,
followed by a `---` separator at `:115`), inserted between the list and the separator. Content
(condensed from Design Decisions 4/5/7/8/9/10 above): describes the `committed_intentions` field,
its cap and 10-kind restriction, the materialization-as-ordinary-tier-5-candidate mechanism, the
"retry is structural absence-of-write" semantics, the order-preserving capacity trim, and an
explicit "Scope note" stating no production write path exists yet (per Decision 10, cross-reference
`ProgressionPlan.goal_queue`'s deferred auto-seed idea rather than leaving it unmentioned).
**Do NOT touch:** `## 6. Adventure Route Scoring Constants` or any other chapter section; do not
alter the existing 4-item Directive→Project→Objective→Action list itself, only add alongside it.
**Verify:** no automated test; verified by `mechanics-auditor` agent or manual doc/code parity check
per CLAUDE.md's Authoritative Mechanics Rule, in the same session as the code change (AC5).

### Step 13 — Parity ledger entry `STRAT-256`
**Files:** `docs/parity_ledger/strategic_cognition.yaml`
**Change:** Append a new entry after `STRAT-255` (confirmed the highest existing ID, ending at
`:3513`, `priority: P2`). **Decision: `STRAT-256` is `priority: P0`** (not mirroring STRAT-255's P2)
— per Investigate's recommendation, since this entry governs durable committed-state materialization
into the authoritative project-switch path, a materially different risk class than STRAT-255's
concern-generation scorer. Unlike STRAT-185's pre-existing gap (P0 with `test_path: null`), this
entry must have a real, populated `test_path` from the start — list every new test from Steps 1-11
(see this plan's own Acceptance Criteria Map for the full list). `status: verified` (not
`legacy_verified` — no legacy behavior exists to compare against; this is new-in-V2 functionality),
`proof_type: parity`. `divergence_note` must state this is additive-only (not a Mechanics Bible
divergence) and must disclose the duplicate-`GoalKind` coexistence consequence (all 10 eligible
kinds already have live scorers registered, per `src/ai/goals/__init__.py:12-21`). `support_boundary`
must state the "consume-side only, no production writer" scope limitation from Finding #4 verbatim,
so a future reader does not mistake this for an end-to-end-reachable production feature.
**Do NOT touch:** `STRAT-185`, `STRAT-186`, `STRAT-187`, `STRAT-255`, or any other existing entry in
this file.
**Verify:** the entry's own `test_path` list, all of which must be real and passing (verified in
Step 14 alongside the STRAT-185/186/187 re-run).

### Step 14 — STRAT-185/186/187 regression re-verification (AC6)
**Files:** none (verification-only step; run, do not edit)
**Change:** Run `pytest tests/unit/strategic/test_score_normalization.py -v` and confirm
`test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate` (STRAT-186's
`test_path`) and `test_locked_system_a_current_still_blocks_low_urgency_system_b_candidate`
(STRAT-187's `test_path`) both pass **after** Steps 1-11 land, not merely cite that Investigate found
them unchanged pre-implementation. **STRAT-185 has no `test_path` (`docs/parity_ledger/
strategic_cognition.yaml:1991-2000`, a pre-existing gap not introduced by this ticket)** — its
"still passing" claim can only be confirmed by inspection: re-read `evaluate_project_switch()`'s
retention-margin/`effective_current_score` computation (`:1005-1049`) and confirm, by the Step 11
byte-hash guard already passing, that this logic is unmodified. Record both the pytest pass/fail
result and the STRAT-185 inspection confirmation explicitly in the ticket's Implementation Notes —
do not silently conflate STRAT-185's inspection-based confirmation with STRAT-186/187's
test-based confirmation; they are different evidence types and AC6 requires both be stated, not
just one blanket "confirmed."
**Do NOT touch:** the STRAT-185/186/187 parity ledger entries themselves (no code changed under
them, so no `v2_evidence`/`test_path` update is warranted — only re-run and record).
**Verify:** the scoped pytest command above; zero code changes expected as a result of this step.

## Scope Guards

- **No change to `evaluate_project_switch()`'s own code, signature, or the STRAT-236
  `_threat_resolved()` lock-expiry check.** Enforced by Step 11's source-hash guard test, run both
  before Step 7 begins and after all steps land; additionally verify via `git diff --stat --
  src/systems/strategic_systems/intelligence.py` at the end of Implement, manually confirming every
  changed line falls outside the `:954-1049` range.
- **No new `GoalKind`.** `_COMMITTED_INTENTION_ELIGIBLE_KINDS` (Step 7) is a `frozenset` of existing
  `GoalKind` members, not a new enum value.
- **No change to `ProgressionPlan.goal_queue`, `PlanRevisionService`, or
  `ProgressionPlanExporter`/`Importer`.** Step 12's Mechanics Bible update may add a one-line
  cross-reference note to `docs/simulation/domains/progression_planner_contract.md` (per
  Investigate's judgment-call suggestion) but must not touch any `src/domains/campaigns/
  progression_plan.py` code.
- **No repurposing of `CognitionProfile.reserved_detour_depth`.** Step 2 adds
  `max_committed_intentions` as a wholly separate field.
- **No production write path for `CommittedIntention` creation.** This ticket implements the
  consume side only (Steps 1-11 read/materialize/retry an existing `committed_intentions` tuple).
  Implement must resist the temptation to add a convenience constructor call, an API endpoint, or a
  `goal_queue`-seeding hook "while touching this code" — that is explicitly a future ticket's scope
  (Design's own "Future Extension Patterns" section, and Decision 10 above).
- **No `CommittedIntention.__post_init__` validation.** Per Decision 2, `GoalKind` restriction is
  enforced only at the materialization hook (Step 7), matching the codebase's existing pattern of
  zero constructor-time validation on every other frozen dataclass in `strategic.py`.
- **No new `GoalScorer` class or `GoalRegistry.register()` call.** The materialization hook
  synthesizes a `GoalScore` inline; it is never registered.
- **No auto-advance-to-next-`sequence_index`/skip-trigger logic.** Per Decision 8, only
  `committed_intentions[0]` is ever read by the materialization hook in this ticket's scope.
- **No new `EntityInspectionSnapshot` pydantic field or new observability endpoint.** Per Decision
  11, the surface lives inside the existing `strategic_summary: Dict[str, Any]`.
- **No modification to `CapacityService.trim_dict`/`trim_list`, `merge_dict()` in `patches.py`, or
  `_score_scale_max()`** — all three are reused as-is via their existing parameters (`score_func`),
  not generalized or altered.

## Dependency Map

- Step 1 — no dependencies (foundational).
- Step 2 — no dependencies (same file as Step 1, independent field).
- Step 3 — depends on Step 1 (needs `CommittedIntention` importable).
- Step 4 — depends on Step 1.
- Step 5 — depends on Step 4.
- Step 6 — depends on Step 1.
- Step 7 — depends on Steps 1, 2, 4 (needs the field, the cap constant, and
  `committed_intentions_add_or_update` to exist).
- Step 8 — depends on Step 7 (the emergent behavior it documents/tests) and Step 5 (the apply path
  the 2-tick regression test exercises).
- Step 9 — depends on Steps 1, 2, 4.
- Step 10 — depends on Step 1.
- Step 11 — no dependencies; recommended to land *before* Step 7 for continuous verification, but
  independently completable at any point.
- Step 12 — depends on Step 7 (describes the landed mechanism accurately).
- Step 13 — depends on Step 7 and on all New Tests existing and passing (needs a real `test_path`).
- Step 14 — depends on Step 7 (re-verifies no regression after the arbiter's *caller* changed).

Steps 1, 2, 6, 10, 11 can be implemented in parallel by construction (no shared file conflicts
except Steps 1/2 both touching `strategic.py`, which is safe since they add disjoint fields).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — `CommittedIntention` dataclass + `committed_intentions` field on `StrategicComponent` | Step 1 | `test_committed_intention_dataclass_shape` |
| AC2 — `max_committed_intentions` on `CognitionProfile`, default 3 | Step 2 | `test_cognition_profile_max_committed_intentions_default` |
| AC3 — materializes as ordinary tier-5 candidate, `evaluate_project_switch()` byte-identical | Steps 7, 11 | `test_committed_intention_head_materializes_as_ordinary_tier5_candidate`, `test_evaluate_project_switch_source_hash_unchanged` |
| AC4 — losing committed intentions retried next eligible tick, not discarded | Steps 7, 8 | `test_losing_committed_intention_retries_next_eligible_tick` |
| AC5 — Mechanics Bible + parity ledger updated same session | Steps 12, 13 | manual/mechanics-auditor review; new `STRAT-256` entry with real `test_path` |
| AC6 — STRAT-185/186/187 re-run and confirmed still passing (empirically, not just cited) | Step 14 | `pytest tests/unit/strategic/test_score_normalization.py -v` + STRAT-185 inspection note |
| AC7 — 5 open implementation questions resolved with explicit, documented decisions | Design Decisions 2, 7, 8, 9, 10, 11 (this document) | N/A — decisions are the artifact; downstream behavior tested by each decision's cited step/test |

## Anti-Drift Notes

- **`evaluate_project_switch()`'s body is the single highest-risk touch point.** Step 11's hash
  guard must be added and passing before Step 7's edits are considered complete, not just checked
  once at the very end.
- **`test_plan.md`'s New Test 4 is corrected, not implemented as literally written** — see Design
  Decision 6. Implement must build
  `test_committed_intention_materializes_via_generic_branch_with_scale_consistent_score` (asserting
  `score == utility`, scale-consistent), not a test asserting `score != utility` (which would be
  asserting a false invariant for this feature's own materialization path, even though it is the
  correct invariant for the three special branches).
- **All 10 eligible `GoalKind`s already have live registered scorers** (`src/ai/goals/
  __init__.py:12-21`) — duplicate-`GoalKind` coexistence (Design's disclosed consequence) is the
  **normal case**, not an edge case, for this feature. `test_duplicate_goal_kind_committed_intention_
  and_live_scorer_coexist` is not optional defensive coverage; it tests the common path.
  Do not "fix" the apparent duplicate by de-duping `all_scores` — that would silently break the
  routine/role-boost and sort-tie-break duplicate-tolerance this design explicitly relies on
  (re-verified against `intelligence.py:1393-1408` during Investigate).
- **`ProjectState.kind` ends up holding a `GoalKind` instance despite its type hint reading
  `ProjectKind`** in the generic branch (`:1549-1558`) — this is pre-existing behavior in the
  current codebase, not introduced by this ticket, and is exactly what keeps `_score_scale_max()`
  classifying it onto the 100-ceiling scale (Decision 5). Do not "fix" this by coercing `kind` to a
  real `ProjectKind` as part of this ticket — that would change the scale classification and
  reproduce the retention-margin scale-bug defect class in the opposite direction.
- **The `_COMMITTED_INTENTION_BASE_UTILITY = 50.0` constant is a judgment call**, not derived from
  any cited source (no existing precedent specifies a "default committed-intention utility"). It is
  chosen to sit meaningfully above the `20.0` winner floor and meaningfully below the `100.0` scale
  ceiling so the committed intention competes as a genuinely ordinary mid-strength candidate — not a
  guaranteed winner, not a guaranteed loser. This value is tunable in a future ticket if empirical
  simulation behavior suggests otherwise; it is not treated as load-bearing precision by this plan.
- **No production write path exists for `CommittedIntention` after this ticket lands** (Finding #4,
  reconfirmed by Decision 10's Scope Guard). The feature is inert in production until a follow-up
  ticket adds one. State this in the ticket's Completion Summary in plain language so it is not
  mistaken for an end-to-end-complete feature.
