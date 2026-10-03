---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260811-MULTI-STEP-PLANNING-DESIGN
artifact_type: investigation
tags: [cognition, strategy, progression]
---

# Investigation — TCK-20260811-MULTI-STEP-PLANNING-DESIGN

## Current Behavior

This ticket is design-scoping work, not implementation (see ticket Scope/Out-of-Scope). This
investigation's job is to ground the design conversation in the *real, current* state of the three
things the design doc's ACs require it to resolve, post-epic. All three code areas below are the
**stabilized state after both `TCK-20260811-ADVENTURE-GOAL-SCORER` and
`TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION` landed** (both DONE, confirmed via
`tickets/todos/adventure-cognition-merge/SEQUENCE.md:17`, which explicitly recommended this ticket
wait for exactly that stabilization).

### 1. The tick-level single-slot model — `StrategicIntelligenceSystem` (`src/systems/strategic_systems/intelligence.py`)

- `StrategicComponent` (`src/core/strategic.py:346-362`) holds `projects: Dict[str, ProjectState]`
  (line 356) — **already a multi-entry container**, not a single scalar. Only one project is
  *active* at a time, referenced by `entity.strategic.current_project_id`
  (`entity.strategic.current_project_id` / `current_objective_id`, read at
  `intelligence.py:983`, `:1133`, `:1192`, `:1220`, `:1227`, `:1263`). Others can sit as
  `ProjectStatus.SUSPENDED` and be revived later.
- `CognitionProfile.max_active_projects: int = 3` (`src/core/strategic.py:333`) caps
  `len(strat.projects)`, enforced at `intelligence.py:1560` (`at_capacity = len(strat.projects) >=
  strat.profile.max_active_projects`) — a *new* winning candidate is dropped (not queued) when at
  capacity and no existing same-kind project exists.
- **Grounded, load-bearing finding**: `CognitionProfile.reserved_detour_depth: int = 2`
  (`src/core/strategic.py:342`) is annotated in-code as `"Max nesting depth for detour chains
  (reserved for future recursive planning)"`. This is a real, already-declared-but-unused field
  that pre-dates this ticket and signals the original schema author anticipated a future
  multi-step/recursive planning need at the `StrategicComponent` level, not just at
  `ProgressionPlan` level. The design doc should address whether this field is the intended seam,
  a dead placeholder, or should be superseded/removed.
- **Resumption today is not an ordered queue.** `evaluate_strategic_intent()`
  (`intelligence.py:1172-1594`) only resumes a `SUSPENDED` project in one place: when a `detour`
  project completes (`intelligence.py:1225-1260`), it does
  `suspended = next((p for p in strat.projects.values() if p.status == ProjectStatus.SUSPENDED),
  None)` — the **first** suspended project found by dict-iteration order (insertion order in
  practice, but not an explicit priority/sequence field), not a deliberately-ordered "next
  intention." There is no general "resume whatever was suspended, in commitment order" path outside
  the detour-completion branch.
- **`evaluate_strategic_intent()`'s real current 5-tier fallthrough** (re-verified, matches
  `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md:110-123`'s
  own claim byte-for-byte against the live function):
  1. Lead suppression / active-objective short-circuit (`_resolve_active_objective`,
     `intelligence.py:1131-1170`, called at `:1209`)
  2. Detour completion → project resumption (`:1225-1260`)
  3. Project abandonment — rejection-backoff, embedded harvesting/hunger/fatigue/shopping
     completion checks (`:1262-1391`)
  4. Blocker-driven detour suggestion, nested inside tier 3's "has active project" branch
     (`:1363-1391`)
  5. Goal scoring — `GoalRegistry.get_all_scores()` (`:1394`), the generic lowest-priority
     fallback, tier-5 competition across **13 `GoalKind` members** (`src/core/strategic.py:121-152`)
     including the 3 new `GoalKind`s landed this epic (`ADVENTURE_ROUTE` :131,
     `SOCIAL_CONTRACT` :135, `REGION_STABILIZATION` :140) plus the 2 tickets that added scoring
     terms without a new `GoalKind` (`MEMORY-INFORMED-ROUTE-SCORING`,
     `CAPABILITY-CONFIDENCE-ADVENTURE-SCORING`, `RELATIONSHIP-AWARE-FORM-PARTY` — additive terms on
     existing scorers, no new `GoalKind`).
- **`evaluate_project_switch()`** (`intelligence.py:954-1049`) is the sole authoritative
  application/arbiter path for changing `current_project_id`:
  - No current project → adopt candidate unconditionally (`:985-990`).
  - Current project not ACTIVE → adopt candidate unconditionally (`:992-998`).
  - Current project locked (`current.lock_until_tick > current_tick`): STRAT-236 threat-resolved
    early release first (`:1005-1015`, landed by `TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION`)
    — if not released, `detour`-kind candidates unconditionally bypass the lock (`:1024-1025`);
    every other kind must clear a normalized dual-condition gate (candidate's own
    percent-of-its-system's-declared-max must exceed both the current project's normalized
    effective score AND a fixed `_INTERRUPTION_URGENCY_FLOOR_PCT`) (`:1026-1037`), fixed under
    `TCK-20260811-INTERRUPTION-BYPASS-RETENTION-MARGIN-SCALE-BUG`.
  - Unlocked path: `candidate_project.score > effective_current_score` (`current.score +
    retention_margin`) (`:1039-1047`).
  - Any candidate that loses replaces nothing — `evaluate_project_switch()` returns `None`
    (`:1037`, `:1049`), and the candidate is simply discarded, not queued for later reconsideration.
  This is the exact arbiter the ticket's AC2 requires the design to reason about, and it is
  **stateless per call** — it has no notion of "the candidate that lost this tick might win in 3
  ticks," which is precisely the gap a committed-intention-sequence model would need to fill.

### 2. The episode-level model — `ProgressionPlan.goal_queue` (`src/domains/campaigns/progression_plan.py`, `docs/simulation/domains/progression_planner_contract.md`)

- `ProgressionPlan` (`progression_plan.py:123-166`, frozen dataclass) holds `goal_queue:
  Tuple[BuildGoal, ...]` (`:137`) — an ordered tuple of `BuildGoal` records
  (`goal_id`/`target_route_family`/`target_item_id`/`target_level`/`status`, `:24-57`).
- **Operates at episode granularity, not tick granularity.** Wired exclusively from
  `CampaignOrchestrator._build_initial_state()`/`_advance_state()`
  (`src/domains/campaigns/orchestrator.py:582-612`, `:448-460`) — i.e. once per episode boundary
  (episodes are the "18+ months" long-horizon unit per `tickets/working_log.csv`'s E61 entry), never
  from the per-tick strategic loop. `PlanRevisionService.generate_initial_plan()`
  (`plan_revision.py:57`) and `.detect_and_revise()` (`plan_revision.py:120`) are both called only
  from that same episode-boundary orchestrator method.
- **Only the head goal (`goal_queue[0]`) is ever consulted**, and only as a scoring *nudge*, not a
  commitment: `AdventureRouteScorer.score()`'s `plan_advance_bonus` term adds a flat **+1.5** to a
  route's score when `route.family.value == head_goal.target_route_family` and the head goal is
  pending/in-progress (`docs/simulation/domains/progression_planner_contract.md:97-119`,
  formula cross-checked against `docs/mechanics/04_strategic_cognition.md:145`). This is one
  additive term among ~8 in `AdventureRouteScorer`'s formula (§6.1) — it never forces route
  selection, and it never touches `current_project_id`/`evaluate_project_switch()` directly; it only
  biases which `AdventureRouteOption` wins *inside* `AdventureDecisionService.decide()`, whose
  single winner then becomes one `GoalScore` candidate for tier-5 (via `AdventureGoalScorer`,
  landed this epic).
- **The contract doc's own words, verbatim** (`progression_planner_contract.md:123`): *"Only
  `goal_queue[0]` (the head goal) is considered. Multi-goal lookahead is deferred (post-E61)."* This
  is the exact boundary the ticket's AC3 requires the design doc to address
  (supersede/extend/coexist).
- Revision only rotates the queue on two trigger kinds (`mentor_dead`, `item_unavailable`), and only
  the first firing trigger per episode is processed (`progression_planner_contract.md:163-181`) —
  again, an episode-cadence mechanism, not a tick-cadence one.

### 3. The gap between them

`ProgressionPlan.goal_queue` is a **long-horizon, episode-cadence, advisory bias list** consumed
only by one scoring term. `StrategicComponent`/`evaluate_strategic_intent()` is a **tick-cadence,
freshly-re-decided-every-eligible-tick, single-active-slot arbiter**. Neither today implements "an
entity commits to a short, ordered sequence of near-term intentions and executes them in order,
tick over tick, without re-litigating the whole tier-1-through-5 competition each time." The
proposal's own worked example (train → craft → quest) operates at *tick-to-episode-fraction*
granularity — much finer-grained than `ProgressionPlan`'s episode cadence, and much more durable
than a single `ProjectState` (which is discarded, not queued, the moment it loses an
`evaluate_project_switch()` comparison).

## Mechanics / Engine Constraints

- **`docs/mechanics/04_strategic_cognition.md` §2 (Interruption Resistance, lines 27-42)** and **§2a
  (Regional Danger materialization pattern, lines 46-83)** are the authoritative, Certified Level 1
  description of the *current* single-slot arbiter, including STRAT-236's threat-resolved early
  release. Any committed-intention model that changes how/whether a locked project can be
  interrupted, or that pre-empts the tier-5 competition for a future tick, must be reconciled with
  this chapter or explicitly recorded as an intentional divergence
  (`docs/guidelines/intentional_divergences.md`, per CLAUDE.md's Authoritative Mechanics Rule).
- **§4 (Project Lifecycle, lines 107-113)**: `Directive → Project → Objective → Action` is
  explicitly a single active chain today ("Strategic goals are broken down into a multi-step
  hierarchy" refers to *decomposition* of one goal, not a *queue* of goals — there is no fifth tier
  for "next project after this one"). A durable multi-step-intention model is a structural addition
  to this hierarchy, not a parameter tweak.
- **CLAUDE.md Strategic/Tactical Rule** (verbatim, from this session's own system context): *"Strategy
  owns enduring direction. Tactics own immediate execution. Do not solve strategic problems by
  stacking more tactical goal scoring."* The ticket's own Scope requires the design to be
  "explicitly reviewed against" this rule. Grounded reading: `GoalRegistry`/tier-5 scoring
  (`src/ai/goals/`) is the **tactical** layer — one-shot utility comparison, re-run every eligible
  tick, no memory of intent beyond the current `ProjectState`. A durable "committed sequence of
  future intentions" is, by this rule's own definition, a **strategic** concern and must not be
  implemented by adding more `GoalScorer`s or more `GoalKind` branches to tier-5 — doing so would
  reproduce exactly the anti-pattern this rule warns against, and would also collide with the
  ticket's own flagged risk of "a third overlapping planning concept."
- **Durable State Rule** (CLAUDE.md, Architecture Rule): if a committed-but-not-yet-executed
  intention "survives beyond the current tick," it must have a typed model, a stable location in
  `EntityState`/`StrategicComponent`, a defined lifecycle, inspection/debug visibility, and tests —
  this directly matches the ticket's AC1 requirement for "a durable typed model."

## Docs Requiring Update

- `docs/architecture/<date>-multi-step-persistent-planning-design.md`: this ticket's primary
  deliverable — new design doc proposing the durable typed model, reviewed against the
  Strategic/Tactical Rule, resolving both interaction questions in the ACs. Does not exist yet;
  filename/date is Implement's choice.
- `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md`: its own
  "Future Extension Patterns" section (lines 449-453) explicitly named this exact proposal
  ("Multi-step planning... deserves its own design conversation") and already carries a
  "Post-landing note" pattern for the other two items in that section
  (`SOCIAL-CONTRACT-GOAL-SCORER`, `REGION-STABILIZATION-GOAL-SCORER`, lines 390-416). Following that
  established precedent, this section should get an equivalent post-landing note once this ticket's
  design doc/decision exists, pointing to the outcome (design doc path, and accept/reject/defer
  status).

Conditionally, **not** required by this ticket itself (per its own Out-of-Scope: no production
code): `docs/simulation/domains/progression_planner_contract.md` and
`docs/mechanics/04_strategic_cognition.md` would need updates *if and when* a follow-up
implementation ticket lands the actual model — that update belongs to that future ticket, not this
design-scoping one. The design doc itself should say so explicitly so the follow-up ticket's own
investigation phase does not have to re-derive it.

## Parity Ledger Overlap

No parity ledger entry should change *status* as a result of this ticket (no code changes). But the
design doc must be written with full awareness of the P0 entries whose `v2_evidence` describes
exactly the mechanism a committed-intention model would need to alter or extend:

- `docs/parity_ledger/strategic_cognition.yaml` — `STRAT-185` ("Strategic project retention is
  bounded by interruption resistance", P0, verified, no `test_path` recorded), `STRAT-186`
  ("Strategic project switching requires margin or explicit emergency", P0, verified, `test_path:
  tests/unit/strategic/test_score_normalization.py::test_locked_system_a_current_interrupted_by_high_urgency_system_b_candidate`),
  `STRAT-187` ("Current project has reservation priority", P0, verified, `test_path:
  tests/unit/strategic/test_score_normalization.py::test_locked_system_a_current_still_blocks_low_urgency_system_b_candidate`).
  Any future implementation that lets a *committed* future intention bypass or pre-empt
  `evaluate_project_switch()`'s comparison would directly touch these three P0 entries and their
  passing tests — the design doc should flag this explicitly as a downstream implementation
  concern, even though it is out of scope to resolve here.
- `docs/parity_ledger/progression.yaml` — `PROG-110`–`PROG-113` (all verified): `ProgressionPlan`
  serialization, export/import, plan-advance bonus, and revision rules. If the design's conclusion
  is "extend `ProgressionPlan.goal_queue`" rather than "new model," these four entries are the ones
  a follow-up ticket would need to touch.

No P0 entry is broken or made to fail by this ticket, since no code changes.

## Prior Work

- This is ticket 10/10 of the `adventure-cognition-merge` epic
  (`tickets/todos/adventure-cognition-merge/SEQUENCE.md`); the other 9 are all DONE. The two this
  ticket's own Assumptions flagged as blocking prerequisites — `TCK-20260811-ADVENTURE-GOAL-SCORER`
  and `TCK-20260811-THREAT-RESOLVED-ARBITER-RELOCATION` — are both DONE and their changes are
  reflected in the "Current Behavior" section above (re-verified directly against the live
  `intelligence.py`, not assumed from the ticket text).
- `docs/architecture/2026-08-11-adventure-as-cognition-strategy-subcomponent-design.md` is the
  direct originating document (cited in this ticket's Assumptions) and doubles as the structural
  template to follow: frontmatter (`status/layer/authority/audience/last_verified`) → H1 title →
  `## Context` → a Non-Goals-style list (its own lines 74-78 are exactly where this proposal was
  first scoped out) → `## Design` (numbered subsections) → `## Future Extension Patterns` →
  `## Diagrams` (mermaid). No other `docs/architecture/*.md` file diverges from this shape among
  the files checked (`2026-08-10-cognition-driven-adventure-eligibility-design.md` follows the same
  pattern).
- `TCK-20260619-E61-PROGRESSION` and its 4 children (`E61A` model, `E61B` exporter/importer, `E61C`
  scorer integration, `E61D` plan revision) are the origin of `ProgressionPlan`/`goal_queue` and the
  authoritative source for its "deferred" boundary — `docs/simulation/domains/progression_planner_contract.md`
  is their consolidated contract doc, read in full above.
- No prior stored artifact directly investigates "committing to a sequence of future
  `ProjectState`s" — this is a genuinely new question, not a re-litigation of settled work.

## Risks and Open Questions

These are handed to Plan, not answered here (per CLAUDE.md's Uncertainty Rule — "vague leads stay
vague until evidence narrows them"; this ticket's own Out-of-Scope forbids resolving them with code):

1. **Does a genuinely new durable model make sense, or is this better framed as extending
   `ProgressionPlan.goal_queue`?** Arguments found for *extend*: the queue/ordering/rotation
   machinery already exists and is tested (`test_plan_revision.py`, `test_progression_plan*.py`,
   `test_progression_planner_three_episode.py`); extending it to tick-cadence consultation (not just
   episode-cadence revision) would reuse a durable, already-typed, already-serialized model.
   Arguments found for *new*: `ProgressionPlan` is architecturally episode-scoped throughout (its
   own docstring, its exporter/importer contract, its revision-trigger cadence) — repurposing it for
   tick-level commitment execution would blur that boundary and could make episode-boundary
   revision logic (`detect_and_revise()`) interact unpredictably with mid-episode tick-level
   execution state. This tension is not resolved by this investigation; it is the design doc's job.
2. **What does "committed but not yet executed" mean for `evaluate_project_switch()`'s arbiter?**
   Concretely: when intention #2 in a committed sequence becomes "next," does it (a) go through
   `evaluate_project_switch()` exactly like any fresh tier-5 candidate (meaning commitment carries
   no special weight, and STRAT-185/186/187 are untouched), or (b) get some form of priority/bypass
   (meaning STRAT-185/186/187's `v2_evidence`/tests need re-verification against the new path)? The
   `StrategicComponent.projects` dict and `resume_project()` already provide a *partial* answer
   pattern (suspend now, resume later) but with no ordering guarantee today (see "Current Behavior"
   §1) — the design should state explicitly whether it reuses/extends this or replaces it.
3. **`CognitionProfile.reserved_detour_depth`** (`src/core/strategic.py:342`) already exists,
   labeled for "future recursive planning" — is this the intended seam for a committed-sequence
   depth limit, a coincidentally-similar but unrelated field (it's specifically about detour
   *nesting*, not intention *sequencing*), or dead weight to be removed? Not resolved here; flagged
   for the design doc to address explicitly rather than silently ignore.
4. **Third overlapping concept risk** (the ticket's own flagged risk, Assumptions line 2): with
   `ProgressionPlan.goal_queue` (episode-cadence, advisory) and `GoalRegistry`/tier-5 scoring
   (tick-cadence, one-shot) already coexisting, a new committed-intention-sequence model that is
   neither would be a third structurally distinct planning concept in the same codebase. The design
   doc must make an explicit case for why a third concept is warranted if that's its conclusion,
   not merely note the risk and proceed.
5. **Go/no-go is a legitimate design-doc outcome.** The ticket's AC4 explicitly allows "reject/defer
   decision recorded with rationale" as a valid closure — this investigation found no code-level
   blocker that forces either an accept or a reject; the decision is a genuine architectural
   judgment call, not something derivable from the current code state alone.

## Anti-Drift Hazards

- **Do not let this ticket produce implementation code.** Out-of-Scope is explicit and the ticket's
  own Request Summary already documents why ("no implementation ACs can be honestly derived"). Any
  Plan/Implement work that starts sketching `dataclass` fields for a new committed-intention model
  in `src/` rather than in the design doc's own prose/pseudocode is scope creep.
  A design doc *may* include illustrative pseudocode/dataclass sketches (the pattern doc it's
  modeled on does not, but nothing forbids it) — the hazard is landing that sketch as real, wired-in
  `src/` code under this ticket.
- **Do not silently resolve the `ProgressionPlan.goal_queue` relationship by omission.** The AC
  requires an *explicit* supersede/extend/coexist statement with rationale — a design doc that
  proposes a new model without directly addressing why `goal_queue` doesn't already solve this would
  fail AC3 even if otherwise well-written.
- **Do not describe `evaluate_project_switch()`/`current_project_id` as simpler than it now is.**
  Post-epic, it already carries STRAT-236 threat-resolved early release and the normalized
  dual-condition lock-bypass gate (both landed same-epic, this week) — a design doc citing the
  pre-epic "kind==danger and score>80 / kind==detour" allowlist behavior (superseded by
  `TCK-20260810-PROJECT-SWITCH-BYPASS-GENERALIZATION`, itself further generalized this epic) would
  be citing stale, already-replaced behavior.
- **Do not conflate `StrategicComponent.projects`'s existing multi-entry dict with a "queue."** It
  already holds more than one `ProjectState`, which could read as "multi-step planning already
  exists" at a glance — but there is no ordering field, no commitment semantics, and resumption is
  narrowly gated to the detour-completion branch only (see "Current Behavior" §1). The design doc
  should be precise about this distinction rather than either overstating or understating what
  already exists.
