---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260929-UNREACHABLE-CLASSIFY-DEAD-GUARD
phase: done
date: 2026-09-29
tags: [simulation-quality, world, strategy, cognition, root-cause]
---

# TCK-20260929-UNREACHABLE-CLASSIFY-DEAD-GUARD

## Title
Classification pass over the 3 dead-guard/filter tickets — assign each a verdict on the
DEFECT/CONDITION/UNDECLARED/MISLABEL axis from `TCK-20260929-EPIC-UNREACHABLE-MECHANISM-
CLASSIFICATION`, with evidence, no fixes

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Child `T03` of `TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION`. The epic groups 14 open
"never fires / never seeded / always empty" tickets by the *shape* their finding presents, not by
assumed cause, and requires each to be assigned exactly one verdict off a four-value axis (DEFECT /
CONDITION / UNDECLARED / MISLABEL) with real evidence — a named zero-caller grep, a content fact, or
tick arithmetic; reading the code alone does not count. `T03` covers the epic's "dead guard / filter"
group: three tickets whose own investigations already found a real precondition or filter that
never fires, but which have not yet had the epic's own four-value verdict formally recorded against
them.

Two of the three (`REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`, `COGNITION-CAPACITY-ENFORCEMENT-
CONDITIONAL-ON-OTHER-UPDATES`) are `P1`; the third (`REGION-DANGER-SEEN-TWO-DEAD-PRECONDITIONS`) is
`P2` — this ticket classifies all three as one pass regardless of their individual priorities,
matching the epic's own per-shape grouping.

`REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` already carries an unusually complete root-cause writeup in
its own Implementation Notes: `resolve_lifecycle()`'s death filter checks
`outcome_kind in ("KILL", "PERMADEATH")` while `world_dynamics.py`'s independent trauma block checks
`alive_set is False` directly, and an instrumented 3000-tick run found 20/20 real deaths classified
`"DEFEAT"` — a value neither of `resolve_lifecycle()`'s two accepted values. That writeup is
cited here as already-known context (per the epic's own Request Summary, which surfaces it), but it
is **not** itself a recorded verdict on the epic's four-value axis — this ticket's own job is the
formal verdict-recording (confirming the cited grep/instrumentation still holds and writing the
verdict into the ticket body), not re-deriving root cause from scratch.

## Scope
- For each of the 3 tickets below, assign exactly one verdict from {`DEFECT`, `CONDITION`,
  `UNDECLARED`, `MISLABEL`} and record it directly in that ticket's own body (a new dated
  Implementation Notes entry plus a verdict line), per the epic's Deliverable 2:
  - `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` (P1) — confirm the existing
    `outcome_kind`/`alive_set` divergence finding still holds (re-run or re-grep the cited evidence,
    do not just restate the ticket's prose) and record the formal verdict. This ticket's own
    Completion Summary already argues the shape of a `DEFECT` (a real classification-divergence bug
    between two independent readers of one combat-outcome event); this pass turns that argument into
    an axis-conformant verdict with re-confirmed evidence, it does not invent a new investigation.
  - `TCK-20260914-REGION-DANGER-SEEN-TWO-DEAD-PRECONDITIONS` (P2) — two independent dead
    preconditions (`state.local_scars` never populated; no real blocker ever carries a
    lead-matching material subject) already confirmed via exhaustive grep and a 2000-tick empirical
    run in the linked stored artifact. Confirm both grep results still hold in the current tree and
    record the verdict(s) — note in Scope of the epic's own axis whether one verdict covers both
    dead preconditions or whether they need two independent verdicts (they are named as two
    independent root causes with no shared fix shape).
  - `TCK-20260921-COGNITION-CAPACITY-ENFORCEMENT-CONDITIONAL-ON-OTHER-UPDATES` (P1) — this ticket is
    explicitly framed as an undecided design question ("is opportunistic enforcement intended or a
    gap?"), not a confirmed defect. Determine whether that framing itself maps to `UNDECLARED` on
    the epic's axis, or whether the `if not ent_upd or not ent_upd.strategic: continue` guard is
    better classified `DEFECT` (a real gap, unconditionally reachable code that silently skips
    over-cap entities) or `CONDITION` (bounded by how often "over cap with nothing else proposed"
    actually occurs in real corpus play, per that ticket's own unmeasured Scope item 4) — do not
    assume the answer from the ticket's own framing language alone; the axis assignment is this
    ticket's job, using the evidence bar (a grep confirming the guard's real reachability shape, or
    a corpus measurement of Scope item 4 if one is cheap enough to run within this ticket's own
    investment cap — not required if it is not).
- Produce evidence per verdict meeting the epic's evidence bar: a named zero-caller grep, a content
  fact, or tick arithmetic. Re-run or re-confirm any evidence cited from the source tickets rather
  than copying it uncritically — the epic's own AC-2 requires evidence, and evidence copied from a
  ticket filed 2-3 weeks earlier is not automatically still true of the current tree.
- If any of the 3 tickets resists all four verdicts, record that explicitly as a fifth outcome per
  the epic's AC-7 — do not force it into the nearest bucket.
- Contribute this pass's classified tickets into whichever corpus-run-length-vs-world-content split
  and DEFECT-subset ranking the epic's `T06` (not this ticket) ultimately produces — this ticket
  records verdicts and evidence only; it does not rank or split.

## Out of Scope
- **Fixing anything.** No code change lands under this ticket for any of the 3 covered tickets,
  regardless of verdict (including not adding `DEFEAT` to `resolve_lifecycle()`'s filter, not wiring
  `create_battlefield_scar()`/`create_raid_scar()` to a real trigger, not changing
  `CapacityEnforcementPhase.enforce()`'s guard). A `DEFECT` verdict becomes its own future fix
  ticket, per the epic's disposition table — that ticket is not created here either.
- **`registries/mechanisms.yaml`.** Must stay byte-for-byte unchanged across this ticket's work,
  same scope guard the wave (PR #258) used and verified.
- **Re-deriving combat volume.** Those numbers moved twice already (see the epic's own Assumptions)
  and are not safe to cite; nothing in this ticket's evidence gathering should depend on a fresh
  combat-volume measurement.
- **The design decision itself for `COGNITION-CAPACITY-ENFORCEMENT-CONDITIONAL-ON-OTHER-UPDATES`.**
  That ticket's own Scope explicitly reserves "is opportunistic enforcement intended or a gap" for
  the roadmap/planning session, not for whoever classifies it here. This ticket's job is to place
  the *current, undecided* state of that question onto the epic's four-value axis (most likely
  `UNDECLARED`, but not assumed — see Scope above), not to resolve the underlying design question.
- **Re-investigating `REGION-DANGER-SEEN-TWO-DEAD-PRECONDITIONS`'s own conjunction reachability.**
  Its own Out of Scope already marks this "already conclusively answered... not to be re-litigated
  here"; this ticket only re-confirms the cited evidence still holds and records the axis verdict.
- **`T05`'s perception-authority decision** (`TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-
  INSTANTIATED`) — a separate epic child, not covered by this ticket's corpus, even though it shares
  the strategic-cognition code area and depends on this ticket completing first (see Related
  Tickets).

## Acceptance Criteria
- [ ] All 3 corpus tickets (`REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`, `REGION-DANGER-SEEN-TWO-DEAD-
      PRECONDITIONS`, `COGNITION-CAPACITY-ENFORCEMENT-CONDITIONAL-ON-OTHER-UPDATES`) carry exactly
      one verdict each from {`DEFECT`, `CONDITION`, `UNDECLARED`, `MISLABEL`}, recorded in that
      ticket's own body — maps to the epic's AC-1 and Deliverable 2.
- [ ] Every verdict cites evidence meeting the epic's bar (a named zero-caller grep, a content fact,
      or tick arithmetic) — reading the code alone is not accepted. For
      `REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` specifically, the verdict must be backed by a grep/
      instrumentation confirmation performed under this ticket, not a bare restatement of the
      epic's own Request Summary prose — maps to the epic's AC-2 and AC-3's "not re-investigation
      but also not a bare restatement" distinction (this ticket is not one of the two wave-assessed
      tickets AC-3 covers, so its evidence bar is the full AC-2 bar, not the lighter AC-3 citation
      path).
- [ ] If any of the 3 tickets resists all four verdicts, that is recorded explicitly as a fifth
      outcome with a stated reason, not forced into the nearest bucket — maps to the epic's AC-7.
- [ ] `registries/mechanisms.yaml` is byte-for-byte unchanged (verified via `git diff` before this
      ticket closes) — maps to the epic's AC-4.
- [ ] No `src/` behavior change lands under this ticket — maps to the epic's AC-5.

## Related Tickets
- `TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION` (open) — parent epic; this is its `T03`
  child per `tickets/todos/unreachable-mechanism-classification/SEQUENCE.md`.
- `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` (open, P1) — corpus ticket 1.
- `TCK-20260914-REGION-DANGER-SEEN-TWO-DEAD-PRECONDITIONS` (open, P2) — corpus ticket 2.
- `TCK-20260921-COGNITION-CAPACITY-ENFORCEMENT-CONDITIONAL-ON-OTHER-UPDATES` (open, P1) — corpus
  ticket 3.
- `TCK-20260928-EPIC-SYSTEMIC-WORLD-FIRST-WAVE` (done, PR #258) — the method precedent this ticket
  and the wider epic reuse: bounded reachability assessment ending in one of four verdicts per
  mechanism, with evidence required per verdict.
- **`T05` (not yet created — `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`'s eventual
  classification child) has this ticket as its prerequisite**, per `SEQUENCE.md`: T05 is scoped as
  an `UNDECLARED`-resolution decision only after this ticket's dead-guard pass has run, because two
  of this ticket's three tickets (`REGION-DANGER-SEEN-TWO-DEAD-PRECONDITIONS`,
  `COGNITION-CAPACITY-ENFORCEMENT-CONDITIONAL-ON-OTHER-UPDATES`) share the strategic-cognition code
  area T05's own perception-authority decision touches. Whoever creates T05 should wait on this
  ticket closing.

## Related Docs
- `docs/mechanics/regional_sovereignty.md` — `RegionState.owner_faction_id`/`.influence`, the
  mechanism `REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` investigates.
- `docs/mechanics/04_strategic_cognition.md` § "Leads (Knowledge)" — `region_danger_seen`'s belief
  synthesis and capacity enforcement, cited by both `REGION-DANGER-SEEN-TWO-DEAD-PRECONDITIONS` and
  `COGNITION-CAPACITY-ENFORCEMENT-CONDITIONAL-ON-OTHER-UPDATES`.
- `docs/plans/rpg_design_roadmap/faction_war_drivers_proposal.md` §2.1, §5 — the investigation that
  originally surfaced `REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`, per that ticket's own Related Docs.
- `docs/parity_ledger/strategic_cognition.yaml` `STRAT-230` — per
  `REGION-DANGER-SEEN-TWO-DEAD-PRECONDITIONS`'s own Related Docs.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260914-REGION-DANGER-SEEN-COLOCATION-SCAR-CONJUNCTION-UNPROVEN/
  investigation.md` — the full investigation naming both `REGION-DANGER-SEEN-TWO-DEAD-PRECONDITIONS`
  defects, with the 2000-tick empirical confirmation; this ticket's own evidence re-check starts
  from here.
- `stored_artifacts/TCK-20260928-EPIC-SYSTEMIC-WORLD-FIRST-WAVE/` — Card J's reachability method,
  reused as this ticket's classification procedure (per the epic's own citation).
- `stored_artifacts/TCK-20260929-UNREACHABLE-CLASSIFY-DEAD-GUARD/` — this ticket's own `investigation.md`/`plan.md`/`test_plan.md`, migrated at closure.

## Related Code Areas
- `src/world/influence.py` (`FactionInfluenceService.process_influence_shift()`)
- `src/systems/lifecycle_systems/lifecycle.py` (`resolve_lifecycle()`)
- `src/content_semantics/faction.py` (`FactionSemanticsService.get_faction_id_str()`)
- `src/engine/world_dynamics.py` (independent trauma-block death detection, used as the comparison
  point for `REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`)
- `src/world/consequences.py` (`RegionalConsequenceService.create_battlefield_scar()`/
  `.create_raid_scar()`)
- `src/systems/strategic_systems/intelligence.py` (real blocker-inference logic)
- `src/ai/goals/scorers.py` (`ResolveBlockerScorer`)
- `src/domains/information/phase.py` (`InformationBeliefPhase.apply()`'s `region_danger_seen`
  branch)
- `src/perf/scenarios.py:248` (synthetic `iron_ore` material-blocker fixture, cited as evidence not
  a real production site)
- `src/engine/pipeline_phases/capacity_enforcement.py` (`CapacityEnforcementPhase.enforce()`)
- `src/strategy/capacity.py` (`CapacityService`)

## Assumptions / Open Questions
- **Environment note (tested, not assumed):** the epic's own Assumptions section reports both
  semantic-search paths as dead in the *planning* worktree (`m2-idea43-temporal-note`) —
  `search_docs` returning "index not found" and `knowledge_search.py` failing on missing
  `sentence-transformers`. That is a different worktree from this one. This ticket's own scoping
  pass tested `mcp__knowledge-search__search_docs` directly in *this* worktree
  (`m2-foundational-systems-tickets`) with a query relevant to this ticket's corpus and it returned
  real ranked results (8 hits, real doc/ticket paths, nonzero semantic/keyword scores) — it is
  **not** dead here. Whoever picks up this ticket should re-verify at pickup time rather than assume
  either this finding or the epic's own planning-worktree finding still holds, since worktree-local
  index state can drift.
- **Open, deferred to the classification pass itself, not decided here:** whether
  `REGION-DANGER-SEEN-TWO-DEAD-PRECONDITIONS`'s two independent dead preconditions (`local_scars`
  never populated; no real material-name-subject blocker) need one shared verdict or two
  independent verdicts. That ticket's own Scope already flags they may be worth splitting into two
  implementation tickets later since they share no fix shape; the same question applies to whether
  they share one axis verdict now.
- **Open, deferred to the classification pass itself:** whether
  `COGNITION-CAPACITY-ENFORCEMENT-CONDITIONAL-ON-OTHER-UPDATES`'s own "design decision needed"
  framing maps directly to `UNDECLARED`, or whether closer evidence-gathering (a grep on the guard's
  real reachability shape, or a cheap corpus check of that ticket's own Scope item 4) surfaces a
  `DEFECT` or `CONDITION` verdict instead. Not pre-decided by this scoping pass.
- **Assumed, per the epic:** no shared root cause across this ticket's three tickets. The epic's own
  method already disconfirmed a shared-cause hypothesis across its first wave; if this pass's own
  classification work believes it has found a shared cause across these three, it must prove it with
  the same evidence bar rather than assume it from the corpus grouping alone.
- **`layer: simulation`** was chosen to match the epic and the wave precedent
  (`TCK-20260928-MECHANISM-REACHABILITY-CALAMITY-TRAUMA-AGING`, also `layer: simulation`), even
  though two of the three covered tickets are individually tagged `layer: strategy` and one
  `layer: world`. Classification-pass tickets in this corpus track as `simulation` regardless of the
  domain area of the tickets they classify, consistent with how the wave's own cross-mechanism
  assessment was tagged.

## Implementation Notes
| Covered ticket | Verdict | Evidence in one line |
|---|---|---|
| `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` | `DEFECT` | known cause (death-outcome-kind filter) re-confirmed in code at HEAD; 1,500-tick run: 59 deaths, 0 `process_influence_shift` calls, influence never moved |
| `TCK-20260914-REGION-DANGER-SEEN-TWO-DEAD-PRECONDITIONS` | `DEFECT` | scar creators have no callers (re-verified); Defect 2 stale as written (production `generate_crafting_blockers` emits real-material blockers, `blacksmith.py:190,207`) but Defect 1 alone blocks the conjunction |
| `TCK-20260921-COGNITION-CAPACITY-ENFORCEMENT-CONDITIONAL-ON-OTHER-UPDATES` | `UNDECLARED` | not a never-fires mechanism; opportunistic behaviour declared as PERF-007 in code but its consequence unadjudicated; 10,916 entity-checks, 0 over-cap |

Calibration, as directed: all three are self-derived (no `registries/mechanisms.yaml` verdict cited), so no registry-dating and no `STALE-PREMISE` hunt; each claim was re-run at HEAD and the cited code dated against filing. `STALE-PREMISE` was not the outcome for any of them, though the capacity ticket's "undocumented as a design choice" and the region-danger ticket's Defect 2 were each partly wrong — narrower, different findings.

The influence ticket answers the CONDITION-vs-DEFECT question it was flagged for: `DEFECT`. `RegionState.influence` has never moved in this codebase's history, so the sovereignty-threshold unification in `TCK-20260924-REGIONAL-SOVEREIGNTY-THRESHOLD-DISAGREEMENT` tuned constants on a path this defect keeps from firing. Evidence lives in each covered ticket's body and `stored_artifacts/TCK-20260929-UNREACHABLE-CLASSIFY-DEAD-GUARD/investigation.md`.

`T05` (perception-authority decision) had this ticket as its prerequisite; that prerequisite is now met.

## Test Summary
Classification only; no repo test suite authored. Re-ran `tests/mechanic_scenarios/test_cognition_capacity_fatigue_lead_trim.py` (3 passed) and two uncommitted scratchpad kernel probes (`frontier_living_world`, seed 42, 1,500 ticks each): an over-cap scan and an influence-shift call counter. Greps and code reads at HEAD for the rest.

## Files Changed
No `src/`/`tests/`/content change; `registries/mechanisms.yaml` unchanged against `origin/main`. Files touched are ticket/artifact bookkeeping only:
- this ticket: `tickets/todos/` -> `tickets/inprogress/` -> `tickets/done/`; `stored_artifacts/TCK-20260929-UNREACHABLE-CLASSIFY-DEAD-GUARD/` migrated from `staging_artifacts/`.
- the three covered tickets (`REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`, `REGION-DANGER-SEEN-TWO-DEAD-PRECONDITIONS`, `COGNITION-CAPACITY-ENFORCEMENT-CONDITIONAL-ON-OTHER-UPDATES`) — each carries its verdict.
- `docs/REGISTRY.yaml` — regenerated by Finalize's self-check, not hand-edited.

## Completion Summary
All three covered tickets carry a verdict: `DEFECT`, `DEFECT`, `UNDECLARED`. No `CONDITION`, so the AC-6 split does not apply. Two ticket premises were partly wrong and are corrected in their bodies (the capacity behaviour is declared as PERF-007; the region-danger ticket's Defect 2 no longer holds as written). Not measured: whether the blacksmith crafting-blocker path is reached in corpus runs alongside a matching location lead. Deferred, not dropped: the shared classification document (`T06`); the influence fix's open design question (does a non-lethal `DEFEAT` count as a sovereignty-relevant death); the capacity ticket's `P1` priority given 0 over-cap observations. `T05` is unblocked. No push, PR or merge.
