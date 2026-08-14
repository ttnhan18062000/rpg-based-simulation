---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-MULTI-STEP-PLANNING-DESIGN
artifact_type: plan
tags: [cognition, strategy, progression]
---

# Implementation Plan — TCK-20260811-MULTI-STEP-PLANNING-DESIGN

## Summary

This ticket's deliverable is a design document, not code (Out of Scope is explicit: "No production
code merged under this ticket"). Accordingly this plan does not contain code-editing steps — it
contains the design doc's required outline, with the five open questions Investigate flagged
**already resolved here** with code-grounded reasoning, so Implement can write
`docs/architecture/2026-08-12-multi-step-persistent-planning-design.md` largely by transcribing this
plan's decisions into prose, not re-deriving them. Filename date is **2026-08-12** (today, per repo
convention of dating docs at authoring/landing time — the ticket's own `2026-08-11` is its filing
date, not the doc's).

**Go/No-Go: GO**, scoped narrowly. The recommendation is to accept the underlying idea as a genuinely
new, third durable model — not an extension of `ProgressionPlan.goal_queue` — living as a new field
on `StrategicComponent`, executed by feeding its head entry into the existing, **unmodified**
`evaluate_project_switch()` arbiter as one more ordinary tier-5 candidate. A follow-up standard-tier
implementation ticket should be opened; this plan specifies its proposed ID, scope, and constraints
so Implement can draft it directly. Full reasoning for all five questions is worked out inline,
question by question, across this plan (Q1 in Steps 1-2, Q2 in Step 4, Q3 in Step 5, Q4 in Step 3,
Q5 -- "is go/no-go a legitimate design-doc outcome" -- in this Summary's own GO declaration and
Step 8's Go/No-Go Decision section); it must be transcribed into the design doc's own `## Design`
section, not just referenced.

## Design Doc Outline (mirrors `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`'s structure, verified by direct read)

Frontmatter:
```
---
status: active
layer: strategy
authority: P1
audience: developer
last_verified: 2026-08-12
---
```

1. `# Multi-Step Persistent Planning for Adventure-Eligible Entities — Design & Go/No-Go` (H1)
2. `## Context` — restate the proposal (train → craft → quest committed sequence), cite this
   ticket's origin (`docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`
   "Future Extension Patterns" §"Multi-step planning", lines 449-453, read directly and confirmed to
   say exactly: *"A genuinely deeper version would let an entity commit to a short sequence of
   intentions (e.g. train → craft → quest) rather than only ever picking the single next action —
   this implies a new persistent planning concept, not a scorer tweak, and deserves its own design
   conversation rather than folding into this one."*), and state the two prerequisite tickets
   (`TCK-20260811-ADVENTURE-GOAL-SCORER`, `TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION`) are DONE
   and stabilized (per `tickets/todos/adventure-cognition-merge/SEQUENCE.md:17`'s own recommendation
   to wait for exactly this).
3. `## Goals` — (a) define a durable, typed model for committing to 2-4 near-term intentions; (b)
   keep `evaluate_project_switch()` byte-identical — no special-cased bypass for committed
   intentions; (c) keep `ProgressionPlan.goal_queue` untouched, coexisting with clearly separated
   responsibility; (d) stay within the Strategic/Tactical Rule's "strategy" side, not add a 6th
   `GoalScorer`-shaped tactical hack.
4. `## Non-Goals` — no code lands under this ticket; no change to `_threat_resolved()`,
   `RouteToProjectMapper`, `AdventureGoalScorer`, `SocialContractGoalScorer`, or
   `RegionStabilizationGoalScorer` (all DONE, out of this ticket's reach per test_plan.md's
   Anti-Drift Test Guards); no unification of `GoalKind`/`ProjectKind` (tracked separately under D22,
   per the sibling doc's own Non-goals); no resolution of `CognitionProfile.reserved_detour_depth`'s
   fate beyond stating it is unrelated (see Q3 below — do not silently repurpose it).
5. `## Design` (numbered subsections — see "Design Doc Section-by-Section Content Plan" below)
6. `## Future Extension Patterns` — one short forward-pointer: if the follow-up ticket lands, note
   that `ProgressionPlan.goal_queue`'s head-goal bias term could *optionally* seed the initial
   `committed_intentions` ordering at plan-creation time — explicitly flagged as a nice-to-have for a
   later ticket, not part of this design's own scope.
7. `## Diagrams` — one mermaid diagram showing the three coexisting planning concepts and their
   cadence/responsibility split (episode-cadence advisory vs. tick-cadence one-shot vs. the new
   tick-cadence durable-sequence model), and one flowchart showing where the committed-intention head
   is injected into `evaluate_strategic_intent()`'s existing 5-tier fallthrough without adding a new
   tier.
8. `## Go/No-Go Decision` — the accept decision, rationale, and the follow-up ticket stub (see
   "Follow-Up Ticket Stub" below).
9. `## Open Questions For Implementation` — the genuine unresolved details deferred to the follow-up
   ticket (see "Open Questions For Implementation" section below, added at Review round 1 — 5 items:
   the `max_committed_intentions=3` cap's empirical basis, mid-sequence-skip abandonment semantics,
   `target_hint` re-resolution-failure handling, whether `goal_queue` should auto-seed
   `committed_intentions`, and the observability-surface shape).

## Design Doc Section-by-Section Content Plan

### Step 1 — Recap the two existing planning concepts, precisely (no embellishment)
**Files:** `docs/architecture/2026-08-12-multi-step-persistent-planning-design.md` (new)
**Change:** Write `## Design` §1, "The Two Existing Planning Concepts," stating exactly:
- `ProgressionPlan.goal_queue` (`src/domains/campaigns/progression_plan.py:123-141`, read directly —
  frozen dataclass, `goal_queue: Tuple[BuildGoal, ...]` at line 137) is **episode-cadence**: wired
  only from `CampaignOrchestrator._build_initial_state()`/`_advance_state()`
  (per investigation.md, re-confirmed via `docs/simulation/domains/progression_planner_contract.md:69-96`'s
  own "Episode Boundary Hooks" section, read directly). Only `goal_queue[0]` is ever consulted
  (`progression_planner_contract.md:123`, verbatim: *"Only `goal_queue[0]` (the head goal) is
  considered. Multi-goal lookahead is deferred (post-E61)."*), as a **+1.5 additive scoring bias**
  inside `AdventureRouteScorer.score()` (`progression_planner_contract.md:97-119`) — it never writes
  `current_project_id` and never commits a project itself.
- `GoalRegistry`/tier-5 scoring (`src/ai/goals/`) is **tick-cadence**: re-run every eligible tick,
  memoryless — each `GoalScorer.score()` call has no notion of what it decided last tick. This is the
  layer `evaluate_strategic_intent()`'s tier 5 consults
  (`src/systems/strategic_systems/intelligence.py`, confirmed by direct read: tiers 1-5 exist exactly
  as investigation.md describes, cross-checked against the sibling design doc's own §2 "Hierarchy
  compliance," which independently cites the same 5-tier structure).
**Do NOT touch:** Do not describe `StrategicComponent.projects` as a queue (it is a `Dict[str,
ProjectState]`, `src/core/strategic.py:356`, confirmed by direct read — multi-entry, but with no
ordering field; resumption of a `SUSPENDED` entry uses unordered dict iteration,
`next((p for p in strat.projects.values() if p.status == ProjectStatus.SUSPENDED), None)` at
`intelligence.py:1248`, confirmed by direct read — first-found, not first-committed).
**Verify:** test_plan.md check 3 (accurate `goal_queue` boundary quote) and check 6 (template
conformance).

### Step 2 — Propose the new model: `CommittedIntention` on `StrategicComponent`
**Files:** design doc `## Design` §2, "The Proposed Model"
**Change:** Write the concrete typed sketch (illustrative pseudocode — this ticket forbids landing it
as real `src/` code, per investigation.md's Anti-Drift Hazards):

```python
@dataclass(frozen=True)
class CommittedIntention:
    """One step in a short, ordered, durable sequence of future intentions."""
    intention_id: str
    goal_kind: str          # a GoalKind value (src/core/strategic.py:121-147) — reuses the existing
                             # vocabulary; does NOT introduce a third kind-enum
    target_hint: Optional[str]   # optional pre-resolved target; re-resolved at materialization
                                  # time if absent
    sequence_index: int      # explicit ordering — the one thing StrategicComponent.projects's
                              # existing SUSPENDED dict lacks today (see Step 1's citation)
    status: str               # "pending" | "active" | "completed" | "abandoned" | "skipped"
```

New field on `StrategicComponent` (`src/core/strategic.py:346-370`, read directly — frozen,
`slots=True` dataclass with existing `Dict`/`List`/`Tuple` fields following the same
frozen-immutable-with-`field(default_factory=...)` pattern this ticket's model must match):
`committed_intentions: Tuple[CommittedIntention, ...] = field(default_factory=tuple)`. New cap field
on `CognitionProfile` (`src/core/strategic.py:328-342`, read directly — mirrors the existing
`max_active_projects: int = 3` pattern at line 333): `max_committed_intentions: int = 3`.

State explicitly **why this is a new model, not an extension of `ProgressionPlan.goal_queue`**
(resolves the ticket's AC3 together with Step 4): `ProgressionPlan` is a frozen dataclass whose
entire lifecycle is episode-boundary export/import (`ProgressionPlanExporter`/`ProgressionPlanImporter`,
confirmed by direct read of `progression_plan.py:169-` and the contract doc's "Episode Boundary
Hooks" section) — there is no existing mechanism for intra-episode, tick-level mutation of a
`ProgressionPlan`, and building one would either (a) violate its established episode-cadence
lifecycle (a Durable State Rule violation — CLAUDE.md requires "a defined lifecycle" and this would
give it two incompatible ones), or (b) require a *parallel* tick-level tracking structure anyway,
which is just this new model with extra indirection. Placing `committed_intentions` on
`StrategicComponent` instead keeps it co-located with the tick-cadence state it actually interacts
with (`current_project_id`, `projects`), consistent with the Durable State Rule's "stable location in
entity/world/registry state."
**Do NOT touch:** `ProgressionPlan`'s dataclass fields, `PlanRevisionService`, or
`ProgressionPlanExporter`/`Importer` — none of this ticket's model requires changing them.
**Verify:** test_plan.md check 1 (concrete typed structure named, not just prose).

### Step 3 — State the `ProgressionPlan.goal_queue` relationship explicitly: **coexist**
**Files:** design doc `## Design` §3, "Relationship to `ProgressionPlan.goal_queue`"
**Change:** State explicitly: **coexist**, not supersede or extend (resolves AC3). Quote
`progression_planner_contract.md:123` verbatim (already done in Step 1). Give each concept's
non-overlapping responsibility, matching this plan's Go/No-Go framing:
1. `ProgressionPlan.goal_queue` — long-horizon (18+ months / multi-episode), advisory-only,
   episode-cadence scoring nudge. Answers: "which route family should I be nudged toward this
   episode."
2. `GoalRegistry`/tier-5 scoring — short-horizon, memoryless, tick-cadence, competitive utility
   comparison. Answers: "what's the single best immediate action right now."
3. **New**: `StrategicComponent.committed_intentions` — medium-horizon (a handful of ticks to a
   fraction of an episode), durable, ordered, tick-cadence-consulted-but-not-re-decided-each-tick.
   Answers: "given I already decided to do X then Y then Z, hold that commitment across several
   ticks without re-litigating it from scratch every eligible tick."
No overlap: (1) never touches `current_project_id` directly; (2) has no memory of past decisions;
(3) is memory-carrying but does not touch episode boundaries or `CampaignOrchestrator`. This directly
resolves the ticket's own flagged "third overlapping concept" risk (Assumptions line 2,
investigation.md Risks item 4) by naming the third concept's distinct responsibility rather than
merely acknowledging the risk.
**Do NOT touch:** Do not propose migrating `goal_queue`'s head-goal-bonus scoring term
(`AdventureRouteScorer`'s `plan_advance_bonus`, `progression_planner_contract.md:97-119`) into the
new model — it stays exactly where it is.
**Verify:** test_plan.md check 3 in full (quote accuracy + explicit supersede/extend/coexist
statement + third-concept risk engagement).

### Step 4 — Resolve arbiter interaction: intentions go through `evaluate_project_switch()` unmodified
**Files:** design doc `## Design` §4, "Interaction with `current_project_id` and the Arbiter"
**Change:** State explicitly (resolves AC2): when `committed_intentions[0]` becomes due (current
project absent, abandoned, or completed — the same tier-3 condition that already triggers generic
tier-5 fallthrough, `intelligence.py:1262-1391` per investigation.md, read and confirmed to match the
sibling design doc's own §2 tier list), it is materialized into an ordinary `ProjectState` using the
same per-`goal_kind` mapping pattern tier-5 winners already use (the sibling design's own §4
`RouteToProjectMapper` pattern is the precedent, not something this design invents), and injected as
**one additional candidate in tier 5's competitive field** — not a new 6th tier, not a bypass. It
must win `evaluate_project_switch()`'s normal comparison (`intelligence.py:954-1049`, read directly
and confirmed: no `kind`-based special case exists today besides the single unconditional `"detour"`
bypass at line 1024-1025) exactly like any fresh `CombatEngageScorer`/`AdventureGoalScorer` candidate.
This is deliberately option (a) from the ticket's own framing, not (b): giving committed intentions
special priority would reproduce the exact hardcoded kind-string-special-case pattern
`TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION` already replaced once (per the sibling design
doc's own §5 reasoning about `_threat_resolved()`, read directly, lines 234-239: *"treating it as a
new bypass mechanic... would reproduce the exact hardcoded, kind-string-special-case pattern...
already replaced once with a generic rule"* — the same logic applies here).

**Consequence — must be stated explicitly, this is the one real deviation from tier-5's existing
semantics**: today, a losing tier-5 candidate is simply discarded
(`evaluate_project_switch()` returns `None` at lines 1037/1049, and the caller does not requeue it —
confirmed by direct read, matches investigation.md's claim). A committed intention that loses one
tick's arbitration must **not** be discarded — it must remain at `sequence_index` 0 and re-compete
next eligible tick until it wins, is explicitly abandoned, or is skipped by revision logic. State
plainly that this "retry" bookkeeping lives entirely in the new `committed_intentions` tracking, not
inside `evaluate_project_switch()` itself — the arbiter function's own code is untouched, so
**STRAT-185/186/187 need no re-verification against a new path, because there is no new path at the
arbiter** (`docs/parity_ledger/strategic_cognition.yaml:1991-2033`, all three entries read directly
and confirmed: STRAT-185 "Strategic project retention is bounded by interruption resistance",
STRAT-186 "switching requires margin or explicit emergency", STRAT-187 "current project has
reservation priority" — all describe `evaluate_project_switch()`'s existing lock/margin logic at
`intelligence.py:1005-1049`, which this design proposes to call, not modify).

**Other writers to `current_project_id` this step must account for** (the shared resource): per the
sibling design doc's own diagram (lines 508-561, read directly), the *only* legitimate write path
today is `evaluate_project_switch()` itself (`EPS -->|"the ONLY legitimate write path"| RES`); the
two remaining unguarded bypass writers are `engine/tactical.py:194` and
`pipeline_phases/guild_visit.py:88`, both confirmed clear-only (`current_project_id_set=""`), never
steal-on-write. A committed intention materializing into a candidate and losing to a concurrent clear
from either of those two sites behaves exactly as any other tier-5 candidate would today — no new
interaction, since this design adds a candidate *source*, not a new writer to the field itself. State
this explicitly so the design doc doesn't read as silently ignoring the other writers.
**Duplicate-`GoalKind` coexistence (Review round 1 finding — must be disclosed, not silently left
implicit)**: since Step 2 deliberately reuses an existing `GoalKind` value rather than introducing a
third kind-enum, and the injection happens by appending to the tier-5 candidate list *after*
`GoalRegistry.get_all_scores(entity, state)` already ran (`intelligence.py:1394`), a committed
intention's materialized candidate and that same tick's own live-registered scorer's candidate for
the identical `GoalKind` can coexist as two separate entries in `modified_scores` simultaneously.
`GoalRegistry`'s own one-scorer-per-kind invariant (`src/ai/goals/base.py:21-50`, `register()`
raises `ValueError` on a kind conflict) governs *registration*, not this list's post-hoc contents —
it is never violated, but it also does not prevent this coexistence, since the committed-intention
candidate never goes through `register()`/`get_all_scores()` at all.

This is safe by direct trace, not by assumption: read `intelligence.py:1393-1408` yourself.
`all_scores`'s only two consumers of `.kind` before the winner is picked are (a) the routine/role
utility-boost lookups (`s.kind.lower()`, lines 1399-1400) — independently boosts each entry, no
uniqueness requirement, correct even with duplicates; and (b) `modified_scores.sort(key=lambda x:
(-x.utility, x.kind))` (line 1408) — an ordinary stable-sort tie-break key, which tolerates
duplicate values with no special-casing needed. The winner-selection loop (`intelligence.py:1409-`)
then just iterates the sorted list and picks the first entry clearing the utility floor with a
resolvable target — with a same-kind duplicate present, whichever of the two sorts first is
evaluated first, and the other remains a live fallback candidate if the first is skipped (no target,
below floor). No crash, no silent data loss, no special-case code required.

State this explicitly in the design doc: duplicate-`GoalKind` coexistence in the tier-5 candidate
list is an accepted, disclosed consequence of appending outside the registry's own enforcement path,
confirmed structurally harmless by the same trace above — not a constraint requiring committed
intentions to avoid kinds with a currently-registered scorer, and not a suppression/merge of the
real scorer's own candidate. Both entries compete on equal footing through the normal sort/floor/
target-resolution pipeline.

**Do NOT touch:** `evaluate_project_switch()`'s own code, signature, the STRAT-236
`_threat_resolved()` lock-expiry check (`intelligence.py:1005-1017`), or `GoalRegistry`'s
`register()`/`get_all_scores()` implementation — none of it changes; the injection point is strictly
downstream of `get_all_scores()`'s own return.
**Verify:** test_plan.md check 2 in full, plus the parity-ledger citation-accuracy pass (check 5) for
the STRAT-185/186/187 citations above, plus confirmation the design doc's §4 explicitly states the
duplicate-`GoalKind` coexistence finding above (Review round 1 requirement).

### Step 5 — Dispose of `CognitionProfile.reserved_detour_depth`: unrelated, do not repurpose
**Files:** design doc `## Design` §5, "`reserved_detour_depth` — Not the Intended Seam"
**Change:** State explicitly (resolves the investigation's Q3): `reserved_detour_depth: int = 2`
(`src/core/strategic.py:342`, read directly, comment verbatim: *"Max nesting depth for detour chains
(reserved for future recursive planning)"*) sits alongside `detour_breadth: int = 3  # Max detour
suggestions per tick` (line 341) — both are scoped to **detours**, tier 4's
`DetourSuggestionSystem.suggest_detours()` (blocker-driven, *reactive* interruption chains,
`intelligence.py:1363-1391`). A committed-intention sequence is **proactive** — planned ahead of any
blocker — a structurally different concept from bounding how deep a reactive detour-of-a-detour
chain may nest. Conclusion: **not the intended seam; unrelated field.** Do not repurpose it. The new
model's own cap is the separately-introduced `max_committed_intentions` field from Step 2, not this
one. Flag as a one-line forward-pointer only (not designed here): a future ticket could examine
whether a detour occurring *while* a committed sequence is active should count against
`reserved_detour_depth` or be tracked independently — explicitly out of scope for this design.
**Do NOT touch:** Do not remove or rename `reserved_detour_depth` — it is unrelated but still
plausibly reserved for genuine detour-recursion work; removing it is a separate, unrelated cleanup
this ticket has no mandate for.
**Verify:** test_plan.md's general citation-accuracy pass (check 5) — the field must exist at the
cited line with the cited comment text (confirmed above by direct read).

### Step 6 — Strategic/Tactical Rule review
**Files:** design doc `## Design` §6, "Strategic/Tactical Rule Review"
**Change:** Quote CLAUDE.md's Strategic/Tactical Rule verbatim: *"Strategy owns enduring direction.
Tactics own immediate execution. Do not solve strategic problems by stacking more tactical goal
scoring."* State the classification and why: tier-5 `GoalScorer`s (including the new
`AdventureGoalScorer`/`SocialContractGoalScorer`/`RegionStabilizationGoalScorer`, all landed this
epic) are **tactical** — one-shot utility comparison, re-run every eligible tick, no memory beyond
the current `ProjectState`. `committed_intentions` is a durable, ordered, multi-tick commitment that
survives across ticks with its own typed lifecycle (Durable State Rule) — by the rule's own
plain-language test ("enduring direction" vs. "immediate execution"), this sits on the **strategy**
side. Explicitly state why the design avoids the rule's own named anti-pattern: it does **not** add a
new `GoalKind`/`GoalScorer` as its primary mechanism (Step 2's model is a new field + a materialization
hook feeding an *existing* candidate into tier 5's *existing* competition, not a new scorer class),
satisfying test_plan.md check 1's fail condition explicitly.
**Do NOT touch:** N/A — prose-only section.
**Verify:** test_plan.md check 1 in full.

### Step 7 — Mechanics Bible / parity ledger impact statement (deferred, not performed here)
**Files:** design doc `## Design` §7, "Mechanics Bible and Parity Ledger Impact (Follow-Up Scope)"
**Change:** State explicitly that `docs/mechanics/04_strategic_cognition.md` §4 ("The Project
Lifecycle", lines 107-113, read directly — *"Directive → Project → Objective → Action"*, confirmed a
single active chain today, decomposition of one goal not a queue of goals) will need an update
describing the new committed-sequence concept if/when the follow-up ticket lands, and that a new
`docs/parity_ledger/strategic_cognition.yaml` entry (not yet assigned an ID) will be required for
whatever mechanism materializes `committed_intentions[0]` into a candidate. State plainly this is
**not performed by this ticket** (no code, no behavior change yet) and belongs to the follow-up
ticket's own Implement phase, per CLAUDE.md's Authoritative Mechanics Rule (doc/code parity is
required only when logic actually changes).
**Do NOT touch:** Do not edit `docs/mechanics/04_strategic_cognition.md` or any
`docs/parity_ledger/*.yaml` file under this ticket — no entry's `status`/`v2_evidence` changes because
no code changed (matches investigation.md's Parity Ledger Overlap conclusion).
**Verify:** test_plan.md's `git diff --stat -- src/` empty-check (Anti-Drift Test Guards) — confirms
this section's own "not performed here" claim is true in practice, not just asserted.

### Step 8 — Go/No-Go Decision section + Future Extension Patterns update
**Files:** design doc `## Go/No-Go Decision`; separately,
`docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`'s "Future
Extension Patterns" section (lines 449-453, read directly)
**Change:**
- In the new design doc: record **GO**, with the one-paragraph rationale from this plan's Summary,
  and the Follow-Up Ticket Stub (below) as the accepted next step. This satisfies AC4's "(a) accepted
  follow-up implementation ticket opened" branch — Implement should actually create the ticket file
  using this plan's stub content, following `create-tickets`/ticket-scoper conventions, as part of
  closing this ticket's AC4 (ticket creation is not "production code" and is not barred by this
  ticket's Out of Scope).
- In the sibling doc's "Future Extension Patterns" section: add one new `> **Post-landing note**`
  block, following the exact precedent already established there twice (lines 390-400, 402-416, both
  read directly) for `TCK-20260811-SOCIAL-CONTRACT-GOAL-SCORER` and
  `TCK-20260811-REGION-STABILIZATION-GOAL-SCORER`. New note text (paraphrase, Implement should match
  the established voice): *"the 'Multi-step planning' item above has since been design-reviewed —
  see TCK-20260811-MULTI-STEP-PLANNING-DESIGN, decision: GO, design doc at
  docs/architecture/2026-08-12-multi-step-persistent-planning-design.md. A follow-up implementation
  ticket ([stub ID from below]) has been opened to build the `committed_intentions` model described
  there; not yet landed as of this note."* This mirrors the "post-landing note" pattern the ticket's
  own Investigation flagged as required (investigation.md "Docs Requiring Update").
**Do NOT touch:** Any other part of the sibling doc — its `## Design`, `## Diagrams`, or the other two
already-landed Future Extension Patterns notes. Do not mark the multi-step-planning bullet itself
"Status: done" — it is design-reviewed, not implemented.
**Verify:** test_plan.md check 4 (closure record) and the Docs Requiring Update item in
investigation.md.

## Follow-Up Ticket Stub (for Implement to file under AC4's "accept" branch)

- **Proposed ID**: `TCK-20260812-COMMITTED-INTENTION-SEQUENCE` (Implement should use the actual
  filing date if different)
- **Tier**: standard
- **Type**: feature
- **Priority**: P3 (matches parent)
- **Layer**: strategy
- **Scope** (narrow, MVP — not the full generality of the design doc's illustrative sketch): add
  `CommittedIntention` dataclass + `committed_intentions` field to `StrategicComponent`; add
  `max_committed_intentions` to `CognitionProfile`; add the materialization hook that feeds
  `committed_intentions[0]` into tier 5's existing candidate field when due; implement the
  "losing candidate stays queued, doesn't get discarded" retry semantics from Step 4; add the
  Mechanics Bible §4 update and a new parity ledger entry (Step 7). Cap sequences at
  `max_committed_intentions=3` entries — no branching, no conditional sequences.
- **Out of Scope for the follow-up**: no changes to `evaluate_project_switch()`'s own code; no
  `ProgressionPlan.goal_queue` changes; no new `GoalKind`/`GoalScorer`; no UI/observability surface
  beyond standard inspection/debug visibility (Durable State Rule minimum).
- **Related Docs**: this ticket's design doc, `docs/mechanics/04_strategic_cognition.md`,
  `docs/parity_ledger/strategic_cognition.yaml`.

## Open Questions For Implementation (Review round 1 addition — genuinely unresolved, deferred to the follow-up ticket, NOT decided by this design)

These are real open questions this design doc deliberately leaves for the follow-up
implementation ticket to resolve with empirical/implementation-time judgment, not gaps in this
plan's own reasoning:

1. **Is `max_committed_intentions=3` the right cap?** Chosen only by analogy to
   `CognitionProfile.max_active_projects: int = 3` (`src/core/strategic.py:333`) — not empirically
   validated for this genuinely different use case (a durable sequence vs. a set of concurrently
   trackable projects). The follow-up ticket should treat this as a starting point, not a settled
   constant.
2. **Exact abandonment semantics when a mid-sequence intention is skipped.** `CommittedIntention
   .status` includes `"skipped"` (Step 2's sketch), but this design does not specify the trigger
   (explicit player/AI decision? automatic timeout? external world-state invalidation?) or whether
   skipping index N auto-advances to N+1 or halts the whole sequence. Left for the follow-up
   ticket's own implementation-time design.
3. **`target_hint` re-resolution failure handling.** Step 2 specifies `target_hint` is "re-resolved
   at materialization time if absent" but does not specify what happens if resolution fails (the
   hinted target no longer exists) — abandon the intention, skip to the next `sequence_index`, or
   retry next tick with a fresh resolution attempt. Follow-up ticket's call.
4. **Whether `ProgressionPlan.goal_queue`'s head-goal bias should auto-seed `committed_intentions`
   at plan-creation time** — flagged only as a "nice-to-have, explicitly not part of this design's
   own scope" in the Future Extension Patterns outline item above; whether and how to wire this is
   fully open.
5. **Observability/debug surface shape** — the Durable State Rule's minimum ("inspection/debug
   visibility") is a hard requirement, but this design does not specify the exact surface (a new
   `EntityInspector` field, a decision-trace entry, a dedicated debug endpoint) — implementation
   detail for the follow-up ticket, not a design-level decision.

## Scope Guards

- No file under `src/` may be modified by this ticket. `git diff --stat -- src/` must be empty at
  Verify (test_plan.md's own Anti-Drift Test Guards).
- No `docs/mechanics/*.md` or `docs/parity_ledger/*.yaml` file may be modified by this ticket (Step
  7) — those belong to the follow-up ticket, if and when it lands.
- No edit to any file belonging to the 9 already-DONE sibling tickets in the
  `adventure-cognition-merge` epic, except the one explicitly-anticipated post-landing note in the
  sibling design doc's "Future Extension Patterns" section (Step 8) — matching the precedent already
  set twice in that same section.
- Do not resolve `CognitionProfile.reserved_detour_depth`'s fate by repurposing or removing it (Step
  5) — state it is unrelated and stop there.
- Do not silently pick "extend" or "supersede" for the `ProgressionPlan.goal_queue` relationship by
  omission — Step 3 requires the explicit "coexist" statement with rationale.
- Do not give committed intentions special priority inside `evaluate_project_switch()` — Step 4
  requires the "unmodified, ordinary candidate" answer; any design draft proposing a bypass must be
  rejected and rewritten before this ticket closes.
- This ticket may create a new ticket file (the follow-up stub) — that is ticket-authoring, not
  production code, and is explicitly anticipated by AC4's "(a)" branch.

## Dependency Map

Steps 1-2 must be written before Steps 3-6 (they establish the vocabulary/model those sections
reference). Steps 3, 4, 5, 6, 7 are otherwise independent of each other and can be drafted in any
order once Steps 1-2 exist. Step 8 (Go/No-Go + sibling doc update) depends on all of Steps 1-7 being
complete, since its rationale paragraph summarizes them and the follow-up ticket stub's scope is
drawn from Steps 2/4/7.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test_plan.md check |
|---|---|---|
| AC1 — durable typed model, reviewed against Strategic/Tactical Rule | Step 2 (model), Step 6 (rule review) | check 1 |
| AC2 — interaction with `current_project_id`/`current_objective_id` and lock-bypass arbiter | Step 4 | check 2 |
| AC3 — relationship to `ProgressionPlan.goal_queue` (`supersede`/`extend`/`coexist`) | Step 1 (recap), Step 3 (explicit coexist decision) | check 3 |
| AC4 — closure record (accepted follow-up ticket or reject/defer rationale) | Step 8 + Follow-Up Ticket Stub | check 4 |
| (cross-cutting) citation accuracy | Steps 1-8, every `file:line` cited must be re-opened and confirmed | check 5 |
| (cross-cutting) template conformance | Overall doc structure ("Design Doc Outline" above) | check 6 |

## Anti-Drift Notes

- **Do not let Step 2's illustrative pseudocode become real `src/` code under this ticket.** It is
  prose/illustration in the design doc only — the same caveat investigation.md's own Anti-Drift
  Hazards raised, re-stated here as a hard constraint on Implement.
- **Do not describe `evaluate_project_switch()` using pre-epic behavior.** It already carries the
  STRAT-236 threat-resolved early release (`intelligence.py:1005-1017`) and the normalized
  dual-condition lock-bypass gate (`intelligence.py:1017-1037`), both confirmed present by this
  plan's own direct read. A design doc citing the old "kind==danger and score>80 / kind==detour"
  allowlist as current would be factually wrong and must be corrected.
- **Do not let Step 8's sibling-doc update touch anything beyond the one new post-landing note.** The
  sibling doc's own two existing post-landing notes are the precedent for scope and voice — match
  them, don't exceed them.
- **The "losing candidate stays queued" behavior (Step 4) is this design's one genuine deviation from
  today's tier-5 semantics.** It must be stated as an explicit, disclosed design choice in the doc,
  not glossed over — a reviewer re-reading `evaluate_project_switch()`'s code will correctly observe
  it discards losers today, and the doc must explain why `committed_intentions`' own bookkeeping
  layer (not the arbiter) is where that changes.
- **`StrategicComponent.projects` is a dict, not a queue — do not conflate it with the new
  `committed_intentions` tuple.** The design doc must keep these two containers distinct in its own
  prose: `projects` holds materialized `ProjectState`s (including `SUSPENDED` ones with no ordering
  guarantee); `committed_intentions` holds not-yet-materialized, explicitly-ordered future intent.
