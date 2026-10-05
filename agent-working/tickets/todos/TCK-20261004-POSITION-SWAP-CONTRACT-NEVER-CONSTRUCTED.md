---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261004-POSITION-SWAP-CONTRACT-NEVER-CONSTRUCTED
phase: open
date: 2026-10-04
tags: [strategy, social, root-cause]
---

# TCK-20261004-POSITION-SWAP-CONTRACT-NEVER-CONSTRUCTED

## Title

`ContractKind.POSITION_SWAP` is never constructed anywhere in production, leaving two consumers
(`_appraise_position_swap` and `MovementPhase.resolve_position_swaps`, 147 lines with a code-health
exception) unreachable in every real run

## Status

OPEN

## Tier

standard

## Type

repair

## Priority

P2

## Request Summary

**`ContractKind.POSITION_SWAP` has no creation site.** Two separate consumers exist and act on it, and
neither can ever fire in a real run because nothing ever builds one.

**Attribution — this is not my measurement.** Found and verified by
`test-architecture-implementer` and independently re-verified by `test-architecture-reviewer`, both
**statically only**, at `origin/main` `3eae2e25058b36cdd6013d0491b155d7b6dad154`. I accepted it without
re-measuring; the reasoning for that is below. Their sessions are the citation of record, not this
ticket.

**Why the absence argument is conclusive rather than suggestive.** An "X never happens" finding is
usually weak, and this one is not, because four independent facts together close the entire construction
surface:

1. All **14** `ContractState(...)` constructions in `src/` pass a **fixed literal** kind, and none is
   `POSITION_SWAP`. The kinds actually constructed are `PROTECTION`, `RECRUITMENT`, `TEAM_UP`,
   `MERCHANT`, `TEACH`, `MARRIAGE`, `CLAN`, `PAID_INFORMATION`, `LOAN` — in
   `certification/scenarios.py`, `engine/domain/core_actions.py`, `pipeline_phases/paid_information.py`,
   `social_systems/contracts.py`.
2. **Nothing builds a kind dynamically** — no `ContractKind(...)` call, no `ContractKind[...]` lookup, no
   `getattr`. So no construction can arrive by indirection.
3. **`core/state.py` serialises contracts out and never deserialises them back**, so no construction can
   arrive from persisted state.
4. **`data/` and `registries/` hold no contract-kind entries.** The only registry hits are
   `code_health_exceptions` rows.

With literal-only construction, no dynamic path, no deserialisation and no data-driven path, there is no
route left for a `POSITION_SWAP` contract to appear. That is a real absence, not an unobserved one.

**Both consumers are therefore dead in production:**

| consumer | size | status |
|---|---|---|
| `_appraise_position_swap` (`social_systems/appraisal.py:91` dispatches, `:234` defines) | — | unreachable |
| `MovementPhase.resolve_position_swaps` (`movement.py:31-178`) | **147 lines, carries a code-health exception** | unreachable |

Other references only *consume*: `pipeline_phases/movement.py:407` filters for the kind.

**No test pins the appraisal side either**, which is consistent with dormancy rather than with a
feature that merely lacks a creation site. At the mutation baseline's source SHA `9640ff942`,
`_appraise_position_swap` scored **0 of 38 mutants killed**.
`test_shared_gate_no_fallthrough_for_gated_kinds` does iterate a literal kind→terms dict, so the
`POSITION_SWAP` iteration genuinely runs — but it passes **empty terms** and asserts only
`reason != UNKNOWN`, which **every mutant still satisfies**. The movement-side `POSITION_SWAP` tests do
not import appraisal, so an import-based one-hop selection left them out. Reported by
`test-architecture-reviewer`; the measurement is theirs and they consider it sound.

**Two name-collision traps, both already caught — do not re-fall into them:**

- **`"run_position_swaps": 1`** in `data/runs/*/chunk_*.json` is a **phase cadence flag**, not a
  contract. A shared identifier is not a shared path. This nearly produced a wrong reading once already.
- **`ReasonCode.POSITION_SWAP*`** (`enums.py:97-99`) are **reason codes**, not contract kinds.

## Scope

- **Decide the direction, which is the whole point of this ticket:** is `POSITION_SWAP` an *unfinished
  feature* missing its creation site, or *dead code* to remove? Both consumers stand or fall together.
- Put the design question to `world-rule-catalog-design` and the user **before** either implementing a
  creation site or deleting anything. Whether position-swap was ever an intended world mechanic is a
  design/world-rules question, not an implementation detail.
- If **dead code**: remove both consumers, the enum member if nothing else needs it, the
  `code_health_exceptions` row for `resolve_position_swaps`, and the tests that construct
  `POSITION_SWAP` only to exercise dead paths.
- If **unfinished feature**: specify what creates a position-swap contract, under what conditions, and
  strengthen `test_shared_gate_no_fallthrough_for_gated_kinds` so it actually pins behaviour (non-empty
  terms, an assertion a mutant can fail).

## Out of Scope

- **Any balance or tuning question** about how often position-swap *should* occur if it is completed.
  Parked by `owner_decision_memo.md` row 7.
- The mutation-measurement methodology question (why the one-hop import selection missed the
  movement-side tests). That is test-architecture's own, explicitly retained by
  `test-architecture-reviewer`.
- Other dormant mechanisms. This ticket is one contract kind, not a dormant-path sweep.
- `ReasonCode.POSITION_SWAP*` and the `run_position_swaps` cadence flag — different things that merely
  share a name.

## Acceptance Criteria

1. A recorded decision — unfinished feature or dead code — with the design question put to
   `world-rule-catalog-design` and the user **before** implementation, and their answer cited.
2. The static absence is re-verified at the then-current `origin/main` before acting. It is accepted here
   at `3eae2e250`, and a creation site could legitimately have been added in between; do not delete code
   on the strength of a measurement that has gone stale.
3. Whichever direction is chosen, **no consumer of `POSITION_SWAP` is left reachable-but-unpinned**: if
   completed, a test fails on the unfixed code; if removed, no dead consumer and no code-health
   exception for one remains.
4. If removed, `docs/guidelines/intentional_divergences.md` records it with a rationale class, and the
   relevant `docs/parity_ledger/` entry is updated. Removing a mechanic is a behaviour change even when
   the mechanic never ran.

## Related Tickets

- `TCK-20260920-VALUE-DIFFERENTIAL-VERIFICATION-INSTRUMENT-GAP` — child B2 of the foundation epic. Same
  family of problem one level out: this contract does not even execute, where that ticket is about
  mechanisms that execute without effect. A worked example for its instrument.
- `TCK-20261002-EPIC-SEMANTIC-FOUNDATION-COMPLETION` — **this ticket is sequenced behind it**, see Status
  note below.

## Related Docs

- `docs/mechanics/04_strategic_cognition.md` — appraisal and contract evaluation
- `docs/combat/combat_movement_overhaul_spec.md` — the movement side
- `docs/plans/systemic_world/owner_decision_memo.md` — row 7, why this waits

## Related Stored Artifacts

None. The evidence lives in `test-architecture-implementer`'s and `test-architecture-reviewer`'s own
sessions and should be cited from there rather than restated as this ticket's own measurement.

## Related Code Areas

All paths and line numbers below **re-verified in this worktree** before filing, because the relayed
report cited `src/cognition/appraisal.py`, which does not exist. Corrected:

- `src/core/strategic.py:82` (`ContractKind.POSITION_SWAP`), `:218` (`ContractState`) — both confirmed
  exact
- **`src/systems/social_systems/appraisal.py`** (NOT `src/cognition/appraisal.py`) — kind dispatch at
  **`:91`**, `_appraise_position_swap` defined at **`:234`**
- `src/engine/pipeline_phases/movement.py` — `MovementPhase.resolve_position_swaps` at **`:31-178`**,
  which is **exactly 147 lines**, confirming the relayed figure. The kind filter is at `:407` (confirmed
  exact). `:152`/`:158` emit `ReasonCode.POSITION_SWAP`; `:490` is the string
  `"movement_resolution": "POSITION_SWAP"`. The relayed description of `:490`/`:495` as "fulfils an
  existing contract" is **not** something I verified — read those lines before relying on it.
- `src/core/enums.py:97-99` — `ReasonCode.POSITION_SWAP*`, **not** contract kinds
- `tests/.../test_movement_micro_arena_position_swap.py`, `test_position_swap.py`,
  `test_social_contract_goal_scorer.py`, `test_appraisal_logic.py` — the only constructors

## Assumptions / Open Questions

- **Whether position-swap was ever an intended mechanic is genuinely unknown** and is the question this
  ticket exists to answer. Not pre-judged in either direction.
- Unverified: whether `resolve_position_swaps`' code-health exception was granted *because* the function
  is dormant or for an unrelated reason. Worth reading before citing the exception as evidence.
- Unverified: whether any frontend/API surface displays a position-swap contract. A read model over a
  kind that never exists would be a third dead consumer.

## Implementation Notes

**Status note, stated up front so nobody expects movement:** this is **feature work, not a hard bug**,
under `owner_decision_memo.md` row 7's definitions — nothing in a running world is broken by code that
never executes. It is therefore **filed and expected to sit** behind the foundation programme. It is
recorded now because the evidence is complete and would otherwise be lost in a session transcript, not
because it is scheduled.

## Test Summary

_(not started)_

## Files Changed

_(not started)_

## Completion Summary

_(not started)_
