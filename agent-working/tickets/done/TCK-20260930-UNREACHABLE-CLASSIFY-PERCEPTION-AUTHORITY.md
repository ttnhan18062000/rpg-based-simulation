---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260930-UNREACHABLE-CLASSIFY-PERCEPTION-AUTHORITY
phase: done
date: 2026-09-30
tags: [investigation, root-cause, corpus, cognition]
---

# TCK-20260930-UNREACHABLE-CLASSIFY-PERCEPTION-AUTHORITY

## Title
Perception-authority classification: confirm `UNDECLARED` for `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`
and specify what the missing declaration would have to say, without making the decision

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Child `T05` of `TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION` (see its `SEQUENCE.md`). The 14th and last
corpus ticket, `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` (P1), reports three real perception-shaped
things and says nothing declares which is the entity's actual perception: (1) `PerceptionUpdatePhase` /
`PerceptionFilterService` (a `PerceptionModel` nothing instantiates or reads), (2) strategic cognition's direct
`SpatialQueryService.nearby_entities()` radius query, (3) the live `PerceptionGate` used by tactical targeting. The epic
pre-indicated `UNDECLARED`. This pass **confirms** that verdict against the current tree, spends its effort on *what the
declaration would have to say*, and records — under AC-7 — that choosing among the options is a human design decision
this pass does not make. Its prerequisite `T03` is met, and it feeds `T06`.

## Scope
- Confirm the covered ticket's factual claims still hold at branch tip (instantiation, readers, call sites) rather than
  re-proving the phase is uninstantiated from scratch.
- Inventory every existing *declaration* of what perception is (Mechanics Bible, domain contracts, parity ledger,
  registry) and state where they agree and where they conflict — the covered ticket's "nothing declares" is tested, not
  assumed.
- Specify the questions a declaration must answer and the facts a decider needs, **without selecting an option**.
- Record the verdict in the covered ticket's own body (epic Deliverable 2).

## Out of Scope
- Deciding which perception model is canonical, wiring, deleting or repurposing anything.
- Editing `docs/mechanics/04_strategic_cognition.md`, `docs/simulation/domains/perception_contract.md`, the parity ledger
  or `registries/mechanisms.yaml` (byte-for-byte unchanged across the epic).
- Re-litigating other epic tickets; the shared classification doc (that is `T06`).

## Acceptance Criteria
1. The covered ticket carries exactly one verdict from the axis (or an AC-7 fifth outcome) with named evidence. (Epic AC 1-2.)
2. Every existing declaration of perception is listed with its authority and date, and every conflict between them is named.
3. The pass states what the declaration must say and what a decider needs to know, and does **not** choose an option; it
   says explicitly that the decision needs a human. (Epic AC 7.)
4. `registries/mechanisms.yaml` byte-for-byte unchanged against `origin/main`; no `src/`/`tests/` change. (Epic AC 4-5.)

## Related Tickets
- `TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION` — parent epic; this is its `T05`.
- `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` — the covered ticket.
- `TCK-20260929-UNREACHABLE-CLASSIFY-DEAD-GUARD` (done) — prerequisite `T03`.
- `TCK-20260920-MECHANISM-COGNITION-DIFFERENTIAL-RUNTIME-VERIFICATION` — found the original contradiction.
- `TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION` — the earlier partial decision the contract header cites.

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` §5 (Perception & Salience).
- `docs/simulation/domains/perception_contract.md`; `docs/world/opportunity_providers_contract.md` (gate section).
- `docs/parity_ledger/strategic_cognition.yaml` — `STRAT-238`, `STRAT-261`.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260928-EPIC-SYSTEMIC-WORLD-FIRST-WAVE/` — method precedent.
- `stored_artifacts/TCK-20260930-UNREACHABLE-CLASSIFY-PERCEPTION-AUTHORITY/` — this ticket's own `investigation.md`/`plan.md`/`test_plan.md`, migrated at closure.

## Related Code Areas
- `src/domains/perception/` (`phase.py`, `filter.py`, `salience.py`, `service.py`), `src/core/cognition.py` (`PerceptionModel`)
- `src/systems/strategic_systems/intelligence.py` (`nearby_entities`), `src/world/perception/gate.py`, `src/engine/tactical.py`
- `src/domains/fame/legend.py` (`to_world_signal`)

## Assumptions / Open Questions
- `search_docs` and `graphify` are live in this worktree (tested).
- Open, and deliberately left open: which reading is canonical. That is a human decision.

## Implementation Notes

Verdict on the covered ticket (`TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`): **`UNDECLARED`, confirmed — and the decision needs a human, so none is made here (AC-7 discipline).** Full evidence lives in that ticket's Implementation Notes and `stored_artifacts/TCK-20260930-UNREACHABLE-CLASSIFY-PERCEPTION-AUTHORITY/investigation.md`.

What this pass adds beyond confirming the verdict:
- The covered ticket's "nothing declares which is canonical" is partly wrong. Two authoritative descriptions exist and conflict: Mechanics Bible §5 (+ parity `STRAT-238`, verified) describes a `10.0`-unit radius view — what strategy actually uses; `perception_contract.md` (+ `STRAT-261`, registry `perception`) describes a `PerceptionModel` pipeline that does not run. The gap is a reconciliation, not a first declaration.
- The phase would not work if simply wired in: its input `world_signals` has no production producer (`LegendFactService.to_world_signal`, tests only) and nothing reads its output. That is three missing pieces, not one.
- Bible-wins precedence was deliberately not applied: it settles legacy-vs-Bible ambiguity, and using it here would silently make the design decision.
- Five questions a declaration must answer, and the facts a decider needs, are written into the covered ticket. No option is recommended.

## Test Summary

Classification only; no repo test suite authored. Re-ran `tests/mechanic_scenarios/test_perception_pipeline_wiring.py` (2 passed); full-tree greps for instantiation, readers and signal producers; a `git log --since` drift check (no change since filing).

## Files Changed

No `src/`/`tests/`/content/doc/parity change; `registries/mechanisms.yaml` unchanged against `origin/main`. Files touched are ticket/artifact bookkeeping only:
- this ticket: created in and closed from `tickets/inprogress/` to `tickets/done/`; `stored_artifacts/TCK-20260930-UNREACHABLE-CLASSIFY-PERCEPTION-AUTHORITY/` migrated from `staging_artifacts/`.
- the covered ticket `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` carries its verdict.
- `docs/REGISTRY.yaml` — regenerated by Finalize's self-check, not hand-edited.

## Completion Summary
The last of the epic's 14 corpus tickets now carries a verdict: `UNDECLARED`, confirmed. The pass's value is the correction and the decision aid, not the label: the ticket's premise ("nothing declares") is replaced by "two authoritative descriptions disagree", the phase's missing signal producer is a second unbuilt piece, and the five questions plus decider facts are recorded. Deliberately not done: choosing among the three perception readings (needs the user or the roadmap owner), any doc/parity/registry edit, and the shared classification document (`T06`). Not checked: whether `PerceptionModel` would enter the state-hash surface if wired. No push, PR or merge.
