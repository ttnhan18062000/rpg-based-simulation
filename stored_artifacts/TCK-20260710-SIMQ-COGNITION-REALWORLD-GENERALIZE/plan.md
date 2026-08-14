---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE
artifact_type: plan
tags: [cognition, self-model, simulation-quality, calibration, investigation]
---

# Implementation Plan — TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE

## Summary

This ticket is investigation-only: no engine code changes. The plan's job is to durably record the
investigation's split-verdict finding (materialization half generalizes cleanly to `urban_political`;
query-routing half does not), reconcile the parity ledger against that finding, resolve three
process/scope questions the investigator explicitly left open (AC7's unsatisfiable-as-written
regression count, the probe-profile fixture's fate, and whether to file the recommended follow-up
engine-fix ticket now), and close out the ticket's own required sections. One new problem was found
during planning that the investigator did not have: the actual on-disk probe-profile file's content
did not match investigation.md's description of it, a genuine evidentiary gap. This was flagged as
an Unresolved Question at drafting time; it was resolved by the orchestrator per Decision 3 below
before Implement began (probe file rebuilt correctly, calibration re-run, exact original numbers
reproduced) — no unresolved question remains in this plan.

## Decisions (stated up front)

**Decision 1 — File the follow-up engine-fix ticket now, tier `standard`, filed to
`tickets/todos/simq-roadmap-phase4-depth-cognition/` (not `tickets/inprogress/`).**
Rationale: the user explicitly authorized extending this epic with new tickets, and the investigation
already did the root-causing work (4 exact file:line points) so there is no reason to leave it as a
bare name-only reference — filing it now prevents the finding from going stale or being re-derived
later. Tier is `standard`, not `hotfix`: the fix is not "self-evident intent" — it touches 4 files
across 2 subsystems (`src/domains/information/router.py`, `phase.py`, `resolver.py`,
`src/engine/intent/action_intent.py`, `src/observability/event_extractor.py`), requires 5 new tests
per `test_plan.md`, and investigation.md's own anti-drift note warns against a "partial-fix trap"
where fixing one of the 3 root causes without the others still leaves the routing half unscoreable —
that compound-fix shape is exactly what `standard`'s "substantive repair" tier routing is for, not
`hotfix`'s "minimal targeted change." It is filed to `tickets/todos/simq-roadmap-phase4-depth-cognition/`
(extending the existing epic folder, alongside this ticket) rather than picked up immediately in
`tickets/inprogress/` — the user asked to *file* it, not implement it in this session, and Phase 4's
own roadmap framing already anticipates it as a "2-4 contingent" ticket, not a required same-session
follow-on.

**Decision 2 — AC7 reconciliation: re-scope to "0 new regressions attributable to this ticket."**
The literal AC7 ("`make evaluate --dry-run` exits 0 with 0 regressions") is unsatisfiable as written
— 3 pre-existing regressions (`dungeon_crawl_seed42_200t` COMBAT/PROGRESSION,
`urban_political_seed42_200t` PROGRESSION) exist on the corpus independent of this investigation,
confirmed via `git status`/`git diff --stat` showing zero tracked files changed before the dry-run
ran. Re-scoping (rather than blocking this ticket on a separate pre-existing-drift fix ticket) is the
correct call because: this ticket made zero code/content changes, so "0 regressions attributable to
this ticket" is trivially and verifiably true, and blocking an investigation-only ticket on unrelated
corpus drift would conflate two independent problems. The pre-existing drift is noted as a candidate
for its own future ticket in the Completion Summary — **not filed here**, since filing it was not
part of this session's authorization and it is unrelated to Branch B/COGNITION.

**Decision 3 — Probe profile fate: RESOLVED (orchestrator re-verification, post-planning) — keep as
permanent test fixture.**
Investigation.md recommended keeping vs. deleting
`config/simulation_quality/profiles/_investigation_probe_urban_political_selfmodel_only.yaml` as a
permanent test fixture. Direct inspection during planning found the file's on-disk content at that
time did not match investigation.md's description (see former UQ-A, now resolved, in Unresolved
Questions below and in investigation.md's Risks and Open Questions section). The orchestrator rebuilt
the file correctly and re-ran the isolated-materialization-only calibration
(`--profile _investigation_probe_urban_political_selfmodel_only`), reproducing investigation.md's
exact claimed numbers (COGNITION grade=S events=5610, INFORMATION grade=C events=0). With the
evidence now independently re-confirmed, keep the file as a permanent test fixture — it is cheap to
retain, it is the only real-world evidence isolating materialization from routing, and the follow-up
ticket's optional grade-anchor regression test (Step 7 below) can now be included unconditionally
rather than skipped.

**Decision 4 — Parity ledger updates:**
- `INFRA-259`: no status/evidence change (investigator's "no change needed" independently confirmed
  by reading the current entry — it already states the materialization claim accurately). One
  cross-reference clause added pointing to the new `INFRA-266` entry, for traceability only.
- `INFRA-260`: append a new paragraph to its existing `support_boundary` field distinguishing the
  hand-built-test claim (still true, unchanged) from the new real-world routing-failure finding.
- New entry `INFRA-266` (next available ID after `INFRA-265`): captures the split verdict —
  materialization verified-generalizing, routing verified-not-generalizing — with the 4 file:line
  root-cause citations.
- `STRAT-245`: no change (investigator's "not directly contradicted" independently confirmed —
  entry is scoped to `unit_selfmodel_pilot`'s shipped-profile hash churn, unaffected by this
  investigation's env-var-override-only runs against `urban_political`).
- `SUB-374`: no change (investigator's "not affected" independently confirmed — entry is about
  unconditional canonical-hash participation, orthogonal to reachability).

## Steps

### Step 1 — Document the split-verdict finding in `eval_matrix_results.md`

**Files:** `docs/simulation_quality/eval_matrix_results.md`

**Change:** Append a new top-level `##` section at the end of the file (after the existing
`## INFORMATION Coverage Closure — Phase 3` section, which is currently the last section), titled
`## COGNITION Real-World Generalization — Phase 4 (TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE)`.
Mirror the structure of the existing `### unit_selfmodel_pilot` and `### hero_guild_routing`
subsections (prose framing paragraph, then evidence, no pillar grade table needed here since this
isn't a new calibration anchor — cite the existing `urban_political_seed{42,123,456}_200t` anchors
instead). Content to include, drawn directly from investigation.md:
1. Candidate-world resolution recap (one paragraph): `urban_political` confirmed correct,
   `hero_guild_routing` independently re-verified as the wrong target because its COGNITION grade is
   driven by `strategic_intelligence`/AGENCY signal (PP-30), not self-model.
2. Materialization-half result (solid evidence, not dependent on the probe file — cite the *combined*
   run using the shipped `urban_political` profile + env-var `ENABLE_SELF_MODEL_COGNITION=ON`
   override): entity 23 (`pop_1`)'s `self_model.knowledge.unknowns` populated from tick 1, seed-
   invariant across 42/123/456; 200-tick calibration shows COGNITION moving `B`→`S`
   (5610–5611 `self_model_updated` events/run). State plainly: **(a) clean generalization.**
3. Query-routing-half result (solid evidence — direct reproduction against real compiled state, not
   dependent on the probe file either): reproduce the 4-point root-cause chain from investigation.md
   verbatim, with exact file:line citations (`router.py:102-103`, `phase.py:92-105`,
   `resolver.py:65-69`, `event_extractor.py:276-299`), seed-invariant across 42/123/456, entity 23's
   `inventory.gold == 0` on all 3 seeds. State plainly: **(c) does not generalize.**
4. The isolated-probe-run's specific numbers (COGNITION grade=S events=5610, INFORMATION grade=C
   events=0) are now independently re-confirmed per Decision 3 above (orchestrator re-ran the
   corrected probe file and reproduced these exact figures) — cite them as confirmed evidence, not
   as pending. The core split verdict does not depend on that specific run alone regardless — it is
   corroborated independently by items 2 and 3 above — but the isolated-probe numbers themselves are
   no longer provisional and should be written into `eval_matrix_results.md` as such.
5. Outcome classification and pointer to the follow-up ticket (name it explicitly once filed in
   Step 4: `TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`).

**Do NOT touch:** any existing section of `eval_matrix_results.md` (all prior `### <world>` write-ups,
grade tables, and the FACTION/INFORMATION Coverage Closure tables) — this is an append-only addition.
Do not add a new `hero_guild_routing` or `urban_political` grade-anchor row/table — no new calibration
anchor is being committed by this ticket.

**Verify:** Manual read-through confirming the new section accurately restates investigation.md's
findings with correct file:line citations (no test executes markdown content; this is a documentation
step). Cross-check against `tests/simulation_quality/test_grade_regression.py`'s existing
`urban_political_seed{42,123,456}_200t` anchor values to confirm the cited `B` baseline/`S` (flag-ON)
contrast doesn't contradict the anchor file's committed data.

### Step 2 — Update `INFRA-260`'s `support_boundary` with the new routing-failure paragraph

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Locate the `INFRA-260` entry (currently lines ~3362-3402). Append a new paragraph to the
end of its existing `support_boundary:` field (do not replace the existing paragraph — it remains
true, scoped to the hand-built `test_fused_loop.py` state). New paragraph text:

```
    Real-world reachability beyond the hand-built test (TCK-20260710-SIMQ-COGNITION-REALWORLD-
    GENERALIZE): reproduced directly against urban_political's real compiled state (actor_id 23,
    seeds 42/123/456, seed-invariant). The routing half does NOT reach a scoreable outcome there —
    InformationQueryRouter.route() (router.py:102-103) ranks the paid traveling_merchant_rumors
    candidate ahead of the free town_notice_board by certainty; InformationBeliefPhase.apply()
    (phase.py:92-105) never falls back past candidates[0]; InformationIntentResolver.resolve()
    (resolver.py:65-69) silently returns None on the affordability gate (entity 23 has 0 gold, all 3
    seeds); and even a hypothetically successful resolution would not score, since
    event_extractor.py:276-299 has no mapping for last_routed_query_subject/last_routed_query_tick.
    This does not reopen INFRA-260's own claim (accurate for the hand-built single-profile test,
    which only ever seeds one candidate source and therefore never exercises the ranking/
    affordability gap) -- it narrows the claim's scope explicitly to that narrower case. See
    docs/parity_ledger/infrastructure.yaml::INFRA-266 for the split-verdict entry and
    TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE for the scoped follow-up fix.
```

**Do NOT touch:** `INFRA-260`'s `status`, `priority`, `v2_evidence`, `test_path`, or `divergence_note`
fields — the entry's underlying claim (the merge-wiring bug fix) is unchanged and still verified;
only `support_boundary` gets the new paragraph.

**Verify:** `python3 -c "import yaml; yaml.safe_load(open('docs/parity_ledger/infrastructure.yaml'))"`
parses cleanly (YAML syntax check — multi-line block scalar indentation must match the existing
`support_boundary` block's style exactly, matching `INFRA-265`'s block-scalar formatting as the most
recent precedent).

### Step 3 — Add new parity entry `INFRA-266` capturing the split verdict

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** Append a new entry after `INFRA-265` (the current last entry, ending at line 3824):

```yaml
- id: INFRA-266
  text: >
    Branch B real-world generalization split verdict (TCK-20260710-SIMQ-COGNITION-REALWORLD-
    GENERALIZE): the self-model materialization half (SelfModelUpdatePhase -> SelfModelPatch ->
    self_model.knowledge.unknowns) generalizes cleanly to urban_political's real compiled state --
    entity 23 (pop_1)'s unknowns populate from tick 1, seed-invariant across 42/123/456, and a
    200-tick calibration (ENABLE_SELF_MODEL_COGNITION scoped ON via env-var override atop the
    shipped urban_political profile) shows COGNITION moving from baseline B to S (5610-5611
    self_model_updated events/run). The query-routing half (InformationBeliefPhase's route-new-
    query branch, phase.py:83-105) does NOT generalize -- reproducible, seed-invariant intent=None
    result, root-caused to 3 independent points plus a 4th observability gap: router.py:102-103
    ranks a paid candidate ahead of a free one by certainty; phase.py:92-105 has no fallback past
    candidates[0]; resolver.py:65-69 silently returns None on the affordability gate (entity 23 has
    0 gold, all 3 seeds); and even a hypothetically successful resolution would not score, since
    event_extractor.py:276-299 has no mapping for last_routed_query_subject/last_routed_query_tick.
    Real-world reachability beyond unit_selfmodel_pilot is therefore no longer "unverified" in
    either direction -- it is verified-generalizing for materialization and verified-NOT-
    generalizing for routing. See INFRA-260's support_boundary for the companion narrative and
    TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE for the scoped follow-up fix covering the 4
    routing-half points.
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: >
    src/domains/information/router.py:102-103 (candidate ranking by (-expected_certainty,
    cost_gold)); src/domains/information/phase.py:92-105 (Branch B, no fallback past
    candidates[0]); src/domains/information/resolver.py:65-69 (affordability gate returns None);
    src/observability/event_extractor.py:276-299 (last_assimilated_subject/tick mapped,
    last_routed_query_subject/tick absent); src/cognition/knowledge_model.py:67-70
    ("insufficient_gold" answer_kind branch has no producer today)
  proof_type: null
  test_path: >
    tests/simulation_quality/test_grade_regression.py (urban_political_seed{42,123,456}_200t
    anchors -- materialization-half evidence only; the query-routing-half failure has no dedicated
    regression test yet, this is exactly TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE's test 1,
    test_branch_b_query_routing_fails_silently_on_real_urban_political_state)
  divergence_note: null
  support_boundary: >
    Scoped strictly to urban_political's real compiled state at 200 ticks, seeds 42/123/456 --
    not re-verified at other worlds, tick counts, or seeds. Does not supersede or duplicate
    INFRA-259 (materialization sourcing fix) or INFRA-260 (pipeline-wiring merge fix); this entry
    is the real-world-reachability finding that sits on top of both.
```

**Do NOT touch:** any entry before `INFRA-265` in the file. Do not renumber or reorder existing
entries.

**Verify:** Same YAML parse check as Step 2. Confirm `INFRA-266` is the only new ID introduced (no
collision with an existing ID — confirmed during planning that `INFRA-265` is the current max).

### Step 4 — File the follow-up engine-fix ticket

**Files:** `tickets/todos/simq-roadmap-phase4-depth-cognition/TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE.md`
(new file)

**Change:** Create the new ticket file with the following full content:

```markdown
---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE
phase: open
date: 2026-07-12
tags: [cognition, information, self-model, observability, simulation-quality]
---

# TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE

## Title
Fix Branch B query-routing's real-world dead-end: candidate ranking, no-fallback, silent
affordability gate, and missing event-extractor mapping

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
`TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE` found that `InformationBeliefPhase`'s Branch B
query-routing logic (`src/domains/information/phase.py:83-105`) is mechanically reachable but dead-
ends against `urban_political`'s real compiled state, reproducibly and seed-invariantly (seeds
42/123/456). This ticket fixes the 4 root-caused points so a real entity's information query can
actually resolve, execute, and score under the SimQ pipeline -- closing the gap between
"reachable" (the existing hand-built `test_fused_loop.py` test) and "succeeds against a real
world's actual candidate ranking and actual entity economy" (what this ticket verifies).

## Scope
1. `InformationQueryRouter.route()` (`src/domains/information/router.py:102-103`) currently sorts
   candidates by `(-expected_certainty, cost_gold)` with no regard for affordability -- a paid,
   higher-certainty candidate always outranks a free, lower-certainty one even when the entity
   cannot afford the paid one. Fix point (decide during implementation, per investigation.md's own
   note that this is a 3-way tradeoff, not obviously "the ranking is the bug"): either change the
   ranking to prefer affordable candidates, or leave ranking as-is and rely on fix 2's fallback.
2. `InformationBeliefPhase.apply()` (`src/domains/information/phase.py:92-105`) only ever tries
   `candidates[0]` -- add a fallback to try `candidates[1]`, `candidates[2]`, etc. when resolution
   of the top candidate fails, before giving up for the tick.
3. `InformationIntentResolver.resolve()` (`src/domains/information/resolver.py:65-69`) silently
   returns `None` when `actor_gold < candidate.cost_gold` -- return a structured
   "insufficient_gold"-shaped signal instead, consumable by the fallback in fix 2 and by
   `KnowledgeModelService.assimilate()`'s existing `"insufficient_gold"` `answer_kind` branch
   (`src/cognition/knowledge_model.py:67-70`), which currently has no producer anywhere in `src/`.
4. `src/observability/event_extractor.py:276-299` has no extractor branch for
   `last_routed_query_subject`/`last_routed_query_tick` (Branch B's own property-update keys, set
   at `phase.py:101-104`) -- add one (a `route_new_query`-style event or equivalent) so a
   successful routing action becomes visible and scoreable under the SimQ pipeline at all.
5. Close the `ASK_INFORMATION` intent execution loop (`src/engine/intent/action_intent.py:127-141`)
   -- it currently only deducts gold and appends an internal `IntentTrace`, never producing an
   `InformationResponse`/`pending_information_responses`-equivalent entry that a later tick's
   `InformationBeliefPhase` Branch A could re-assimilate. Without this, even a "successful" routing
   action never resolves the entity's unknown into a known fact.
6. Add the 5 tests scoped in `stored_artifacts/TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE/test_plan.md`'s
   "New Tests Required" section (verbatim -- do not re-derive):
   `test_branch_b_query_routing_fails_silently_on_real_urban_political_state`,
   `test_information_belief_phase_falls_back_to_next_candidate_on_resolution_failure`,
   `test_intent_resolver_insufficient_gold_produces_signal_not_silent_none`,
   `test_event_extractor_emits_route_new_query_event`,
   `test_ask_information_intent_execution_closes_the_loop`.
7. The parent investigation ticket's probe-file question is now resolved (formalized as a permanent
   fixture, per Decision 3 above) — add `test_urban_political_selfmodel_cognition_isolated_grade_anchor`
   (test_plan.md item 6) unconditionally.
8. Update `docs/parity_ledger/infrastructure.yaml::INFRA-266` (added by
   `TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE`) to `status: verified` with the fix's
   `test_path` once these tests pass, replacing its current routing-failure framing with a
   routing-fixed framing (or add a new INFRA-26x entry if the split-verdict framing should be
   preserved historically rather than overwritten -- implementer's call, consistent with how
   INFRA-259/260 were kept as separate, narrowly-scoped entries rather than merged).

## Out of Scope
- Changing `ENABLE_SELF_MODEL_COGNITION`/`ENABLE_BELIEF_ASSIMILATION` defaults in any shipped
  profile -- this ticket fixes the mechanism, it does not activate it anywhere new.
- Widening the fix into "the full belief-assimilation response cycle" beyond the 5 numbered points
  above -- mirrors the existing anti-drift note in
  `docs/plans/idea_information_belief_trigger_wiring.md` and
  `stored_artifacts/TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE/test_plan.md`'s own
  "partial-fix trap" warning: a single-point fix (e.g. only re-sorting the router) would likely
  still leave routing unscoreable even if resolution succeeds -- all 4 root-cause points (5
  including the intent-closure gap) must land together.
- Any change to `SelfAssessmentService`, `NeedInterpretationService`, or `CapabilityEstimateService`.
- Turning `ENABLE_ADVENTURE_ROUTING`/AGENCY on in combination with self-model flags in the same
  test -- `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B`'s Finding 5 blast-radius sweep already flagged this
  three-way combination as out of scope for Branch B work.

## Acceptance Criteria
- [ ] `InformationQueryRouter`/`InformationBeliefPhase`/`InformationIntentResolver` resolve a real
      `ASK_INFORMATION` query end-to-end against `urban_political`'s real compiled state (entity 23,
      0 gold) for at least one of the two available candidates, across all 3 anchor seeds
- [ ] `event_extractor.py` emits a scoreable event for a successful routing action
- [ ] A successfully executed `ASK_INFORMATION` intent eventually produces an answer that a later
      tick's Branch A can re-assimilate
- [ ] All 6 new tests pass (5 from Scope items 1-6 plus the grade-anchor test from Scope item 7,
      now unconditional per the parent investigation ticket's Decision 3);
      `test_branch_b_fires_across_real_tick_boundary_after_self_model_patch_materialization`
      still passes unmodified
- [ ] `INFRA-266` (or a new successor entry) updated to reflect the fixed state with a passing
      `test_path`
- [ ] `make evaluate --dry-run` shows 0 new regressions attributable to this ticket

## Related Tickets
- `TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE` (parent investigation -- source of all 4
  root-cause file:line citations this ticket implements against)
- `TCK-20260703-SIMQ-UPLIFT3-BRANCH-B` (done -- the original 3-bug materialization fix chain)
- `TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT` (done -- established the isolated-
  materialization pilot this ticket's fix extends beyond)

## Related Docs
- `docs/parity_ledger/infrastructure.yaml` (`INFRA-259`, `INFRA-260`, `INFRA-266`)
- `stored_artifacts/TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE/investigation.md` (full root-
  cause evidence chain, file:line citations, seed-invariance confirmation)
- `stored_artifacts/TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE/test_plan.md` ("New Tests
  Required" section -- the 6 tests this ticket must add, already scoped)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE/`

## Related Code Areas
- `src/domains/information/router.py:102-103`
- `src/domains/information/phase.py:83-105`
- `src/domains/information/resolver.py:65-69`
- `src/cognition/knowledge_model.py:67-70`
- `src/observability/event_extractor.py:276-299`
- `src/engine/intent/action_intent.py:127-141`

## Assumptions / Open Questions
- Whether to fix the router's ranking heuristic itself or rely solely on the phase-level fallback
  (Scope item 1) is left to the implementer, per investigation.md's own note that the ranking
  heuristic is plausibly intentional design (favor accuracy over price) and only becomes a hard
  failure combined with zero starting gold and no fallback -- decide based on which combination of
  fixes 1-3 produces the cleanest, most minimal diff satisfying the Acceptance Criteria.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
```

**Do NOT touch:** do not begin implementing any of this new ticket's Scope items as part of the
current ticket's work -- filing it is the full extent of this step. Do not move it to
`tickets/inprogress/`.

**Verify:** `python3 tools/validate_frontmatter.py tickets/todos/simq-roadmap-phase4-depth-cognition/TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE.md`
(or the repo's equivalent frontmatter/tag validator) passes -- all 5 tags
(`cognition`, `information`, `self-model`, `observability`, `simulation-quality`) are confirmed
pre-registered in `docs/guidelines/tag_registry.jsonl` as of this planning session, so no new tag
registration step is required.

### Step 5 — Fill in this ticket's own Completion Summary, Implementation Notes, Test Summary, Files Changed

**Files:** `tickets/inprogress/TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE.md`

**Change:**
- `## Implementation Notes`: record the candidate-world re-confirmation (matches investigation.md
  Part A, already independently re-derived not just accepted), and explicitly record the AC7
  reconciliation decision (Decision 2 above) and the probe-profile resolution (Decision 3 above --
  RESOLVED, kept as permanent fixture, numbers independently re-confirmed) inline so a future reader
  does not have to open `plan.md` to find them.
- `## Test Summary`: cite the verification already performed (per `test_plan.md`'s "Verification
  Already Performed" section) -- `make evaluate --dry-run` (710 pillars, 3 pre-existing/unrelated
  regressions), direct `WorldCompiler.compile()` calls (seeds 42/123/456), the combined-flags
  200-tick calibration run, the direct router/resolver reproduction, and the orchestrator's
  isolated-probe re-verification (Decision 3). Cite the isolated-probe-only run's specific numbers
  (COGNITION grade=S events=5610, INFORMATION grade=C events=0) as independently re-confirmed, not
  pending.
- `## Files Changed`: `docs/simulation_quality/eval_matrix_results.md` (new section),
  `docs/parity_ledger/infrastructure.yaml` (`INFRA-260` support_boundary addition, new `INFRA-266`
  entry), `config/simulation_quality/profiles/_investigation_probe_urban_political_selfmodel_only.yaml`
  (new file, permanent test fixture per Decision 3),
  `tickets/todos/simq-roadmap-phase4-depth-cognition/TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE.md`
  (new file). Explicitly note zero `src/` files changed.
- `## Completion Summary`: state the split verdict in one paragraph (materialization: clean
  generalization; routing: does not generalize, 4 root causes, follow-up filed as
  `TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`), the AC7 reconciliation ("0 new regressions
  attributable to this ticket" -- true, literal "0 regressions" AC not satisfiable due to unrelated
  pre-existing corpus drift, not blocking closure), and the probe-profile fixture's fate as resolved
  (Decision 3: content re-verified by re-running the isolated-materialization-only calibration,
  exact number match to originally-claimed evidence, kept as a permanent test fixture).

**Do NOT touch:** `## Scope`, `## Out of Scope`, `## Acceptance Criteria`, `## Related Tickets/Docs/
Stored Artifacts/Code Areas`, or the frontmatter -- those sections are already correct as filed and
this step only fills in the trailing, previously-empty sections.

**Verify:** `python3 tools/done_checker_static.py tickets/inprogress/TCK-20260710-SIMQ-COGNITION-REALWORLD-GENERALIZE.md`
(or equivalent done-checker script) reports all script-checkable Definition-of-Done conditions
satisfied, given the AC7 reconciliation is explicitly documented rather than silently glossed over.

## Scope Guards

- Do not fix any of the 4 routing root-causes (`router.py`, `phase.py`, `resolver.py`,
  `event_extractor.py`, `action_intent.py`) in this ticket -- filing
  `TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE` is the only permitted action regarding those
  files; this ticket's own Out of Scope explicitly forbids in-place fixing.
- Do not turn `ENABLE_SELF_MODEL_COGNITION` (or `ENABLE_BELIEF_ASSIMILATION`, already ON) on in
  `urban_political.yaml`'s shipped profile, or any other shipped profile. All evidence stays
  env-var-override-scoped, per Scope item 6 of the parent ticket and `INFRA-262`'s guardrail test.
- Do not touch `SelfAssessmentService`, `NeedInterpretationService`, or `CapabilityEstimateService`.
- Do not modify `data/worlds/urban_political/world.yaml` or its `resolved/world.resolved.yaml` --
  the existing `pending_self_model_information_events` seed is already valid (UQ-2 resolved,
  confirmed by direct `WorldCompiler.compile()` call), no re-seeding is needed or permitted.
- Do not re-decide `hero_guild_routing`'s or `unit_selfmodel_pilot`'s tier classification in
  `corpus_tier_taxonomy.md`.
- Do not add a new committed calibration anchor (new `grade_anchors.json` key, new
  `data/runs/` fixture) for the isolated-probe run in this ticket -- that formalization
  (test_plan.md's optional test 6, `test_urban_political_selfmodel_cognition_isolated_grade_anchor`)
  is deferred to the follow-up ticket (Step 7 of its own scope), which lands alongside the routing
  fix rather than in this investigation-only ticket.
- `config/simulation_quality/profiles/_investigation_probe_urban_political_selfmodel_only.yaml` IS
  git-added and committed by this ticket (Decision 3 above: resolved, kept as a permanent test
  fixture, content independently re-verified) -- this reverses the plan's original blocked stance;
  do not delete or rename it.
- Do not fix the 3 pre-existing, unrelated `make evaluate --dry-run` regressions
  (`dungeon_crawl_seed42_200t` COMBAT/PROGRESSION, `urban_political_seed42_200t` PROGRESSION) --
  out of scope, confirmed pre-existing and unrelated, not this ticket's job.

## Dependency Map

- Step 1 (eval_matrix_results.md) is independent of Steps 2-3 (parity ledger) -- both read from the
  same investigation.md source but write to different files. Can be done in either order.
- Step 2 and Step 3 both edit `docs/parity_ledger/infrastructure.yaml` -- do Step 2 before Step 3 to
  avoid a diff/line-number collision (Step 2 edits an existing entry mid-file; Step 3 appends at
  end). Not a hard architectural dependency, just a mechanical ordering to keep the diff clean.
- Step 4 (file follow-up ticket) is independent of Steps 1-3 -- it can be drafted in parallel, but
  should reference the exact same file:line citations, so do it after Step 1/3 are drafted (even if
  not yet saved) to guarantee the citations match verbatim. Sequence as written (Step 4 after 1-3)
  for citation consistency, not a strict technical dependency.
- Step 5 (this ticket's own Completion Summary) depends on Steps 1-4 all being complete, since it
  summarizes and cross-references all of them (including the follow-up ticket's ID, which must
  exist before Step 5 can cite it).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Candidate-world choice confirmed and recorded in Implementation Notes | Already done by investigation.md (Part A); Step 5 records it in the ticket itself | Manual read-through; cross-checked against `corpus_tier_taxonomy.md`/`grade_anchors.json` during investigation |
| `self_model.knowledge.unknowns` seeding attempted, 200+ tick real calibration run | Already performed by investigation.md; Step 1 documents it durably | `tests/simulation_quality/test_grade_regression.py` (`urban_political_seed{42,123,456}_200t` anchors, unaffected) |
| Both flags ON together for at least one run (materialization + routing) | Already performed by investigation.md (combined shipped-profile + env-override run); Step 1 documents it | Direct calibration run evidence in investigation.md; re-derivable via `calibrate_simq.py` with the same env override |
| Documented, evidence-based generalization answer recorded | Step 1 (eval_matrix_results.md), Step 3 (INFRA-266) | Manual read-through against investigation.md's citations |
| Gap documented with file:line detail sufficient for a follow-up ticket; follow-up named/referenced | Step 4 (ticket filed, not just named) | Ticket file exists at the stated path with all 4 root-cause points |
| Parity ledger entries updated (`strategic_cognition.yaml`, `infrastructure.yaml` INFRA-259/260) | Step 2 (INFRA-260), Step 3 (INFRA-266); STRAT-245/INFRA-259/SUB-374 explicitly verified as needing no change | YAML parse check; manual diff review |
| `make evaluate --dry-run` exits 0 with 0 regressions | **Re-scoped (Decision 2): 0 new regressions attributable to this ticket** -- already true, confirmed via `git diff --stat` showing zero tracked `src/`/`data/`/`config/` files changed before the dry-run ran; Step 5 records this reconciliation explicitly | `python3 tools/evaluate_simq.py --dry-run` (already run during investigation: 710 pillars, 3 pre-existing/unrelated regressions, 0 attributable to this ticket) |

## Unresolved Questions

None remain — UQ-A below was resolved by the orchestrator after this plan was drafted, before
Implement began. Preserved here as a record of the finding and its resolution.

**UQ-A — RESOLVED (orchestrator re-verification, 2026-07-12, post-planning).** Original finding:
the probe-profile file's actual content did not match investigation.md's description of it.

`config/simulation_quality/profiles/_investigation_probe_urban_political_selfmodel_only.yaml`
currently on disk contains:

```yaml
pillar_weights:
  FACTION: 1.5
  ECONOMY: 1.5
  SOCIAL: 1.5
  COMBAT: 0.3
feature_flags:
  ENABLE_SOCIAL_COOPERATION: "ON"
```

Investigation.md describes this exact file as containing `ENABLE_SELF_MODEL_COGNITION=ON only, no
belief-assimilation flag`. These do not match at all -- the on-disk file has no
`ENABLE_SELF_MODEL_COGNITION` key anywhere, and its `feature_flags` block turns on
`ENABLE_SOCIAL_COOPERATION` instead, a completely unrelated SimQ pillar (SOCIAL, not COGNITION).
Cross-referencing `tickets/working_log.csv`, the same-day, same-branch
`TCK-20260710-SIMQ-DEPTH-SOCIAL` ticket (closed 2026-07-12T07:05:00Z, several hours before this
session) activated `ENABLE_SOCIAL_COOPERATION` in two other worlds -- this probe file's actual
content (pillar weights favoring FACTION/ECONOMY/SOCIAL, `ENABLE_SOCIAL_COOPERATION: "ON"`) is far
more consistent with being stray, uncommitted scratch contamination from that unrelated ticket's
session than with anything this investigation describes producing.

**What this does and does not put at risk:** the core split verdict (materialization generalizes,
routing does not) does **not** depend on this file -- the materialization evidence comes from the
*combined* run (shipped `urban_political` profile + env-var override, no probe file involved), and
the routing evidence comes from direct function-call reproduction against real compiled state (also
no probe file involved). What **is** at risk is the specific "isolated materialization-only" run
investigation.md reports (COGNITION=S, 5610 events; INFORMATION=C, 0 events; "delta of exactly 1
event between the two runs") -- if that run actually used this file's real content
(`ENABLE_SOCIAL_COOPERATION` instead of `ENABLE_SELF_MODEL_COGNITION`), the reported numbers
describe a different experiment than the one investigation.md claims to have run.

**Why this is flagged rather than decided:** deciding "keep as permanent fixture" (as investigation.md
suggested as one option) would risk enshrining mismatched content as verified evidence. Deciding
"delete" unilaterally would destroy the artifact before a human/investigator can determine whether
this is genuinely contamination (most likely) or whether investigation.md's description is simply
wrong about a file whose real content is still valid evidence of *something* (less likely, but not
ruled out without asking). Neither branch is safe for the planner to pick alone.

**Resolution (orchestrator, 2026-07-12):** re-ran the recommended path directly. Rebuilt the file as
`urban_political.yaml`'s shipped content + `ENABLE_SELF_MODEL_COGNITION: "ON"`, minus
`ENABLE_BELIEF_ASSIMILATION`, and re-ran `tools/calibrate_simq.py --ticks 200 --seed 42 --name
urban_political --profile _investigation_probe_urban_political_selfmodel_only`. Result: exact match
to investigation.md's originally claimed numbers (COGNITION grade=S events=5610, INFORMATION
grade=C events=0). This confirms the original measurement was captured correctly and the file's
on-disk drift happened afterward (most plausibly an incomplete edit mid-session, not contamination
from the unrelated SOCIAL ticket after all, since that ticket's own profile edits were scoped to
`frontier_living_world.yaml`/`highland_traverse.yaml`, never `urban_political.yaml`). File restored
to correct content; see investigation.md's Risks and Open Questions section for the full resolution
note. Decision 3 above (keep as permanent fixture) is now made on this confirmed evidence.

## Anti-Drift Notes

- Do not conflate the materialization half's "(a) clean generalization" verdict with the routing
  half's "(c) does not generalize" verdict in any of the writing produced by Steps 1/3/5 -- they are
  two structurally separate code paths (`SelfModelUpdatePhase` vs. `InformationBeliefPhase`'s Branch
  B) and collapsing them into a single "Branch B generalizes"/"doesn't generalize" statement would
  misrepresent both. `INFRA-259` (materialization) and `INFRA-260`/`INFRA-266` (routing) already
  maintain this split in the ledger -- preserve it in every new sentence written.
- The follow-up ticket (`TCK-20260712-SIMQ-INFORMATION-ROUTING-CLOSURE`) must stay narrow to the 4
  file:line points (plus the intent-closure gap) -- do not let its Scope drift into "the full
  belief-assimilation response cycle" when it is eventually implemented.
- `tests/integration/test_world_profile_feature_flag_guardrail.py` (`INFRA-262`) will fail if any
  step in this plan accidentally leaves a shipped profile's feature flags changed -- none of the
  steps above touch any `config/simulation_quality/profiles/<shipped-world>.yaml` file, but this is
  the guard to re-run if anything unexpected shows up in `git status` after Steps 1-5.
- `urban_political` is Regression/baseline tier, explicitly "do not touch" per
  `corpus_tier_taxonomy.md` -- none of this plan's steps modify `data/worlds/urban_political/` or
  `config/simulation_quality/profiles/urban_political.yaml`; if any step is later found to require
  touching either, stop and re-flag rather than proceeding.
- The `_investigation_probe_urban_political_selfmodel_only.yaml` naming's leading underscore is
  deliberate (visually distinct from shipped profiles) -- per investigation.md's own anti-drift note,
  do not rename it. This naming-preservation rule stands on its own regardless of UQ-A's status,
  which is in any case already resolved (Decision 3, Unresolved Questions section): the file is kept
  as a permanent test fixture under this exact name.
