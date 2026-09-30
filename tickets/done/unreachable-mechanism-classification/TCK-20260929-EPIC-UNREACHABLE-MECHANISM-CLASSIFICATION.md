---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION
phase: done
date: 2026-09-29
tags: [investigation, root-cause, corpus]
---

# TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION

## Title
Unreachable-mechanism corpus: classify every open never-fires / never-seeded / always-empty ticket
before any more of them are fixed individually

## Status
DONE

## Tier
epic

## Type
chore

## Priority
P1

## Request Summary
Fourteen open tickets in `tickets/todos/` report the same shape of finding: real, wired, correct
code that **does not execute during any run this project actually performs**. They were each filed
independently, by different investigations, over 2026-09-12..2026-09-29, and each is framed as its
own local defect. They are not each their own local defect.

`TCK-20260928-EPIC-SYSTEMIC-WORLD-FIRST-WAVE` (closed, PR #258) assessed three of these mechanisms
under a bounded-reachability question — is this a defect, a condition, or a mislabel? — and the
three answers came out **different in kind**:

- `calamity_intensity` = **DEFECT.** `apply_calamity_consequences` has zero real callers anywhere
  in `src/`.
- `regional_trauma` = **CONDITION.** Code correct and wired; `moon_cave` is spatially isolated from
  every hostile faction, so the input never arrives. Confirmed on a fresh 5,000-tick run.
- aging / succession = **CONDITION.** Correct code reachable at ~20.16M ticks, against a corpus that
  runs 1k–5k ticks — 4,000–20,000× beyond anything we execute.

That result is the whole argument for this epic. Three tickets that read identically on their face
needed three different dispositions, and **only one of the three was a bug**. We have eleven more
sitting behind the same ambiguity, and nothing in the corpus tells them apart. `TCK-20260914-
REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` compounds it: `RegionState.influence` has never moved in this
codebase's history, and `#247` nonetheless unified a sovereignty threshold on it. We are tuning
dials on machinery that does not run, and we cannot currently tell which dials those are.

The shared-root-cause hypothesis was already tested and **disconfirmed** during the wave: J2's cause
is spatial isolation; `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES`'s is a death-outcome-kind
filter missing `DEFEAT`. This epic therefore does **not** assume a common root cause. It assumes
only a common *question*, and its deliverable is the answer per ticket.

## Scope

**This is a scope-only epic.** It produces a classification and a disposition per ticket; it
changes no runtime behavior and fixes nothing directly.

### The classification axis

Every ticket in the corpus below is assigned exactly one verdict:

| Verdict | Means | Disposition |
|---|---|---|
| `DEFECT` | Code is unreachable because of a real wiring/guard/filter bug | Keep open; becomes a fix ticket |
| `CONDITION` | Code is correct and reachable; our world content or run length never supplies the input | Reframe as a corpus/content question, not a code bug |
| `UNDECLARED` | Several competing implementations exist and nothing declares which is authoritative | Needs a design decision before any code change |
| `MISLABEL` | The mechanism's registry/doc claim overstates what the code was ever meant to do | Route to the registry owner; close the reachability framing |

A verdict requires **evidence**, not reading. `CONDITION` in particular must state either the
content fact (as J2 did: spatial isolation) or the tick arithmetic (as J3 did: ~20.16M vs 1k–5k).

### Corpus in scope (14 open tickets)

Grouped by the shape they present, **not** by assumed cause:

*Zero real callers / dead constant*
- `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` — already assessed `DEFECT` by the wave;
  record the verdict, do not re-investigate.
- `TCK-20260914-CALAMITY-RANDOM-CHANCE-UNUSED-CONSTANT` (hotfix, P3)
- `TCK-20260917-REGIONAL-SOVEREIGNTY-SERVICE-ORPHAN-TAXATION-DEBUFFS` (hotfix, P2)
- `TCK-20260929-PROFILE-API-PAYLOAD-DEAD-API-REFS` (hotfix, P2)

*Never-seeded precondition state*
- `TCK-20260920-CAMP-STATE-NEVER-SEEDED-BY-WORLD-COMPOSITION`
- `TCK-20260920-DEMOGRAPHIC-COHORT-CYCLE-POPULATION-COHORTS-NEVER-SEEDED`
- `TCK-20260912-CAPABILITY-CONTEXT-REGION-ENEMY-DATA-ALWAYS-EMPTY`
- `TCK-20260913-NO-MECHANISM-RECORDS-PER-ENEMY-KIND-DANGER`

*Dead guard / filter*
- `TCK-20260914-REGIONAL-INFLUENCE-SHIFT-NEVER-FIRES` (P1)
- `TCK-20260914-REGION-DANGER-SEEN-TWO-DEAD-PRECONDITIONS`
- `TCK-20260921-COGNITION-CAPACITY-ENFORCEMENT-CONDITIONAL-ON-OTHER-UPDATES` (P1)

*Scale / content conditioned*
- `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` — already assessed `CONDITION` by the wave.
- `TCK-20260915-COMBAT-GATE-DOWNSTREAM-STARVATION-FACTION-AND-BOSS-GATE`

*Undeclared design*
- `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` (P1) — three perception-shaped things
  exist and nothing declares which is the entity's real perception. Strongly pre-indicated
  `UNDECLARED`; the epic should confirm, not re-derive.

### Deliverables

1. A classification document under `docs/plans/` carrying the verdict + evidence per ticket.
2. A per-ticket edit recording its verdict in its own body (so a ticket picked up standalone later
   carries the answer with it).
3. A ranked fix order for the `DEFECT` subset only.
4. An explicit statement of which `CONDITION` tickets are conditions **of our corpus run length**
   versus **of our world content** — these have different owners and different fixes.

### Candidate child tickets

Named here for the detail-planner; **not created by this pass**, per this session's planner role.

| ID | Covers | Prereq |
|---|---|---|
| `T01` | Classification pass over the 4 zero-caller / dead-constant tickets | none |
| `T02` | Classification pass over the 4 never-seeded tickets | none |
| `T03` | Classification pass over the 3 dead-guard tickets | none |
| `T04` | Confirm the 2 wave-assessed verdicts + the 2 scale/content tickets | none |
| `T05` | Perception-authority design decision (`UNDECLARED` resolution) | `T03` |
| `T06` | Ranked fix order + corpus-vs-content owner split | `T01`–`T04` |

`T01`–`T04` have no unmet prerequisite and may be created first.

## Out of Scope

- **Fixing anything.** No `DEFECT` is repaired under this epic; each becomes its own fix ticket
  after classification.
- **Changing `registries/mechanisms.yaml`.** The wave's J1 recommendation is already routed to
  `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION`, which owns that entry. That ticket
  scored highest on the open-ticket overlap scan (30.4) and is **adjacent, not duplicate**: it owns
  registry `implemented_by` residue; this epic owns runtime reachability. Do not merge them.
- **Changing corpus run length or world content** to make a `CONDITION` fire. Recording that a
  mechanism needs 20M ticks is the deliverable; deciding to run 20M ticks is not this epic's call.
- `TCK-20260928-ENTITY-DEATH-AUTHORITY-BOUNDARY-CHECK` — held behind
  `TCK-20260925-SOVEREIGNTY-OWNERSHIP-WRITER-CONSOLIDATION`'s determinism sequencing, unchanged by
  this epic.
- Any re-derivation of combat volume. **Those numbers have moved twice** (see Assumptions).

## Acceptance Criteria

1. Every one of the 14 corpus tickets carries exactly one verdict from the four-value axis.
2. Every verdict cites evidence — a named zero-caller grep, a content fact, or tick arithmetic.
   A verdict supported only by reading the code is not accepted.
3. The two wave-assessed tickets (`CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`,
   `LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`) record the wave's existing verdict without
   re-investigation, and the classification doc cites PR #258 as the source.
4. `registries/mechanisms.yaml` is byte-for-byte unchanged across the whole epic (same scope guard
   the wave used and verified).
5. No `src/` behavior change lands under this epic or any of its children.
6. The `CONDITION` set is split into corpus-run-length versus world-content subsets, each with a
   named owner.
7. If any ticket resists all four verdicts, that is recorded as a fifth outcome and reported —
   **not** forced into the nearest bucket.

## Related Tickets
- `TCK-20260928-EPIC-SYSTEMIC-WORLD-FIRST-WAVE` (closed, PR #258) — the three-mechanism assessment
  this epic generalizes.
- `TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION` (open) — adjacent; owns the registry side.
- `TCK-20260915-EPIC-MECHANISM-REGISTRY`, `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` (open,
  both idle past the staleness window) — overlapping subject matter; this epic does not absorb either.
- The 14 corpus tickets enumerated under Scope.

## Related Docs
- `docs/mechanics/05_world_evolution.md` — calamity, regional trauma, tick-to-day arithmetic.
- `docs/mechanics/regional_sovereignty.md` — `RegionState.influence` / `owner_faction_id`.
- `docs/mechanics/04_strategic_cognition.md` — perception and capacity enforcement.
- `docs/plans/world_composition_precondition_gap_finding.md` — the existing never-seeded finding
  shared by `camp` and its siblings.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260928-EPIC-SYSTEMIC-WORLD-FIRST-WAVE/` — Card J's reachability method,
  which this epic reuses as its classification procedure.
- `stored_artifacts/TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION/` — this ticket's own `investigation.md`/`plan.md`/`test_plan.md`, migrated at closure.

## Related Code Areas
- `src/world/calamity.py`, `src/world/regional_sovereignty.py`
- `src/systems/lifecycle_systems/lifecycle.py`
- `src/engine/pipeline_phases/capacity_enforcement.py`
- `src/systems/strategic_systems/intelligence.py`
- `src/worldassembly/`, `src/worldbuilding/` (never-seeded preconditions)

## Assumptions / Open Questions

- **Assumed:** the four-value axis is sufficient. AC-7 exists because it may not be.
- **Assumed:** no shared root cause. This was tested and disconfirmed during the wave; any child
  ticket that thinks it found one must prove it rather than assume it.
- **Open:** whether `CONDITION`-by-run-length is a finding about the code or a finding about the
  SimQ corpus. `TCK-20260915-SIMQ-CORPUS-BLIND-TO-SCALE-DEPENDENT-BEHAVIOR` (open) is arguably
  where that half belongs; the epic should decide, not silently take it.
- **Hard constraint for any child:** combat-volume numbers are **not safe to cite**. They moved
  twice — first `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` found `COMBAT_ENGAGE`
  wins goal competition then is discarded at dispatch
  (`src/systems/strategic_systems/intelligence.py:1711` hardcodes `kind="reach_location"`; re-verified
  live 2026-09-29), then `TCK-20260919-COMBAT-ENGAGED-HOSTILES-UNIFY-CATALOG-SEMANTICS` measured a
  large drop (`crowded_frontier` −84.8%, `hero_guild_routing` −95.9%). Any child reasoning about
  combat volume must re-measure.
- **Environment note:** both semantic search paths are dead in the planning worktree (`search_docs`
  returns "index not found"; `knowledge_search.py` fails on missing `sentence-transformers`). A
  child ticket should say so rather than imply the scan ran.

## Implementation Notes
Scope-only epic; nothing implemented directly. Executed as six children, all in `tickets/done/`: `TCK-20260929-UNREACHABLE-CLASSIFY-ZERO-CALLER`, `TCK-20260929-UNREACHABLE-CLASSIFY-NEVER-SEEDED`, `TCK-20260929-UNREACHABLE-CLASSIFY-DEAD-GUARD`, `TCK-20260929-UNREACHABLE-CLASSIFY-WAVE-CONFIRM`, `TCK-20260930-UNREACHABLE-CLASSIFY-PERCEPTION-AUTHORITY`, `TCK-20260930-UNREACHABLE-CLASSIFY-ROLLUP`. The deliverable is `docs/plans/unreachable_mechanism_classification.md`; each verdict is also recorded in its covered ticket's body.

## Test Summary
No repo test change under the epic. Children recorded their own verification. Epic-level: `registries/mechanisms.yaml` and `src/ tests/ registries/` unchanged against `origin/main`.

## Files Changed
No `src/`/`tests/`/registry change. Files touched: the six children (created and closed), the 14 corpus tickets (each carries its verdict), `docs/plans/unreachable_mechanism_classification.md` (new), this epic ticket and `SEQUENCE.md` (moved to `tickets/done/unreachable-mechanism-classification/`), `stored_artifacts/` for each child and for this epic, and `docs/REGISTRY.yaml` (regenerated by Finalize, not hand-edited).

## Completion Summary
All seven epic acceptance criteria are met (status table in the shared document): every one of the 14 corpus tickets carries one verdict with evidence; the two wave-assessed tickets were recorded from PR #258 without re-investigation; `registries/mechanisms.yaml` and `src/` are unchanged; the `CONDITION` set is split by owner; three resistant cases used AC-7 (`STALE-PREMISE` twice, `NO-MECHANISM` once) and one outcome (perception) is recorded as needing a human decision.

The 14 corpus tickets stay open by design: the epic classified them, it did not fix them. The next actions are decisions for people — the five `UNDECLARED` design calls, the wire-or-delete calls for two `DEFECT`s, follow-ups F1-F6 in the shared document, and the SimQ corpus ticket for the run-length condition. The single-world, single-seed limit on the measurements is stated first in the shared document and applies to this summary.
