---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261005-PERCEPTION-CONTRACT-DESCRIBES-PARKED-CHAIN-AS-LIVE
phase: done
date: 2026-10-05
tags: [cognition, documentation]
---

# TCK-20261005-PERCEPTION-CONTRACT-DESCRIBES-PARKED-CHAIN-AS-LIVE

## Title
Two places in `perception_contract.md` still describe `PerceptionGate` as the upstream filter of a
pipeline stage that never runs, contradicting the same document's own "designed, not in effect"
relabel sixteen lines earlier

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found by `world-rule-catalog-design` while registering `PerceptionGate` as its own mechanism
(`sense_gated_detection`) for Child B of `TCK-20261002-EPIC-SEMANTIC-FOUNDATION-COMPLETION`, and
filed here because it is a doc/code parity defect in a contract, not registry content.

`docs/simulation/domains/perception_contract.md:17` already carries the correct relabel:

> **Designed, not in effect:** this contract describes a designed attention-based perception model
> that is not in effect at runtime. Distance governs perception today (the `PerceptionGate` call
> site in `src/engine/tactical.py`), not the attention/capacity model described below.

Line 15 is equally explicit that `PerceptionUpdatePhase` has zero call sites in
`AuthoritativeApplyPipeline.refine()`.

**But two later passages were not updated with it, and still assert the parked chain as a live
pipeline:**

1. **`:50`** — "**World-side prerequisite:** `PerceptionGate` (at `src/world/perception/gate.py`)
   runs **before** the Perception Update stage. The gate performs catalog-driven binary
   sense-channel gating — only signals that pass the gate reach `world_signals` for the Perception
   Update stage to score."
2. **`:194`** — the Domain Interactions table row: "**PerceptionGate** … | Upstream prerequisite |
   Gate runs before the Perception Update stage; filters which signals reach the salience
   evaluator".

Both describe a relationship that does not exist at runtime. There is no stage for the gate to run
before, and the gate does not populate `world_signals`. Its only production consumer is
`TacticalDecisionSystem`'s hostile-target loop (`src/engine/tactical.py:199` at `898c6f35a`, through
the singleton in `src/engine/behavior_consumers.py`), which skips any neighbour the gate reports
unperceived — a per-neighbour targeting check, not a signal filter.

This is the shape the Authoritative Mechanics Rule exists to prevent: a reader who lands on `:50` or
on the interactions table without reading `:17` first comes away believing a dormant chain is wired.

## Scope
1. Correct `:50` and `:194` so each states what the gate actually does today — gate one specific
   neighbour's detectability for tactical targeting — and states that the Perception Update stage it
   is described as feeding does not run.
2. Keep the designed relationship on record rather than deleting it. `:17`'s own wording is the
   precedent: the design is deferred to a future perception-foundation epic and nothing is being
   decided here. A "designed:" / "today:" split in both places is the cheapest shape that does not
   lose the design.
3. Sweep the rest of the same document for any third passage with the same defect, and say in the
   ticket whether one exists. Two were found by someone who was not looking for them; the file has
   not been read end-to-end against the relabel.
4. Cross-reference `sense_gated_detection` in `registries/mechanisms.yaml` as the mechanism entry
   for the gate, once Child B's registry content has landed. If it has not landed, leave the
   cross-reference out and note it here — do not block on it.

## Out of Scope
- Deciding between the distance and attention perception models. `:17` explicitly defers that to a
  future perception-foundation epic, and owner decision 7 freezes feature work. This ticket makes the
  document match today's code; it does not choose a mechanism.
- Wiring `PerceptionUpdatePhase` into the pipeline — `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`.
- `registries/mechanisms.yaml` content, which `world-rule-catalog-design` owns.
- Measuring whether the gate ever returns `perceived=False`. That is the value-differential question
  and belongs to `TCK-20260920-VALUE-DIFFERENTIAL-VERIFICATION-INSTRUMENT-GAP`.

## Acceptance Criteria
- [x] `:50` and `:194` each describe the gate's real present-day consumer and no longer assert that
      it filters `world_signals` or precedes a running stage.
- [x] The designed relationship is still readable in the document, not deleted.
- [x] The Scope 3 sweep result is recorded either way — "no third passage" is a valid, wanted answer.
- [x] No claim in the edited passages is unverifiable against `src/` at a named commit; cite the
      commit.
- [x] `make knowledge-index-update`: satisfied after merge. The index is per-worktree and not committed, so lead-planner runs it in the main checkout after every merge (lead-planner, 2026-10-27); it was not run in this worktree.

## Related Tickets
- `TCK-20260918-MOTIVATION-DOCTRINE-STALE-AGAINST-RETIRED-DOCTRINE-VALUES-CHAIN` — the registry work
  that surfaced this; not a parent.
- `TCK-20261002-EPIC-SEMANTIC-FOUNDATION-COMPLETION` — Child B registers the gate as
  `sense_gated_detection`. This ticket is **not** a child of that epic; it is an independent doc fix.
- `TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED` — the phase's own dormancy.
- `TCK-20260831-DEAD-COGNITION-SCHEMA-DECISION` — cited at `:15`.
- `TCK-20260920-VALUE-DIFFERENTIAL-VERIFICATION-INSTRUMENT-GAP` — the effect question, out of scope.

## Related Docs
- `docs/simulation/domains/perception_contract.md` — the file to fix
- `docs/mechanics/04_strategic_cognition.md` — perception and knowledge management

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION/runtime_probe/`
  — the positive-controlled call counter that established the gate's reach (1839 / 528 / 33
  `can_perceive` calls per 1000 ticks on `crowded_frontier` / `frontier_living_world` /
  `quest_dense_frontier`, seed 42, `PROD_SMALL`)

## Related Code Areas
- `src/world/perception/gate.py::PerceptionGate`
- `src/engine/tactical.py:199` — the sole production call site
- `src/engine/behavior_consumers.py` — the singleton it is reached through

## Assumptions / Open Questions
- The gate's reach is measured; its **effect** is not. The call sits inside a bare
  `except Exception: pass` permissive fallback, so a gate that always raises cannot be distinguished
  from one that always perceives. The corrected text must not imply the gate is known to change any
  targeting outcome — only that it is called and can skip a neighbour.
- `:199` is the call site at `898c6f35a`. Lane A's dispatched batch edits `src/engine/tactical.py`
  in three tickets, so **re-derive the line number at the commit being cited** rather than copying it
  from here.

## Implementation Notes
`docs/simulation/domains/perception_contract.md`, every passage that asserted the parked chain as live now carries a "Designed:" / "Today:" split; nothing was deleted. Call sites re-derived at main 3533fde71 (the ticket's `tactical.py:199` is stale): `src/engine/appraisal.py::perceives` (line 50) and `src/engine/tactical.py::_target_still_perceived` (line 90), both through the singleton in `src/engine/behavior_consumers.py`, both catching `(AttributeError, KeyError, TypeError, ValueError, RuntimeError)` and treating a gate failure as perceived. The text says reach is measured and effect is not. `sense_gated_detection` had landed in the previous commit of this batch, so the cross-reference is included.
**Scope 3 sweep result: there were more than the two found.** Edited: `:50` (World-side prerequisite), `:194` (Domain Interactions row), plus four more passages with the same defect: `:36` (the domain "consumes the post-gate signal list"), `:128` ("runs before the Perception Update stage in the engine loop"), `:141` ("The Perception Update stage never sees signals that the gate blocked") and `:149` (the What It Reads row "post-gate `Sequence[WorldSignal]`"). The header lines `:11`-`:17` were already correct, and the `:188` catalog-immutability row and the test and extension sections make no claim about the pipeline.

## Test Summary
Docs only; no code or test touched. `make knowledge-index-update` is not run in this worktree (the index is per-worktree and uncommitted); lead-planner runs it in the main checkout after merge.

## Files Changed
- docs/simulation/domains/perception_contract.md

## Completion Summary
Six passages in `perception_contract.md` now state the designed relationship and what the gate actually does today, cited at main 3533fde71. No code changed.
