---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP
phase: open
date: 2026-09-30
tags: [testing, economy, resource]
---

# TCK-20260930-CONSERVATION-REJECTION-PATH-ASSERTION-GAP

## Title
No test asserts `accepted=False` on any rejection path in `ResourceTransactionResolver.resolve()`,
including the reservation guards whose acceptance burns a durable transaction id

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

A mutation baseline over `src/core/conservation.py` — the atomic conservation law — killed 60 of 177
mutants and left **117 survivors**. Seven of those survivors are one family: the literal
`accepted=False` on a rejection path flipped to `accepted=True`, surviving at
`conservation.py:108, 125, 169, 240, 277` and two sibling lines, across the **GROUND_ITEM, CORPSE,
building, QUEST and RECRUIT/CHEST** source kinds. Six source kinds, the same missing assertion in
every one. No test in the 165 selected asserts that a rejected transfer reports rejection.

**This is a coverage gap, not a live defect.** Production code has `accepted=False` correctly on
every one of those paths, verified by reading them. What the survivors prove is that nothing would
catch it if it regressed. Any artifact produced under this ticket must preserve that distinction —
"conservation has a bug" is the sentence this finding decays into, and it would be false.

**What makes it P1 rather than a routine coverage gap is where an `accepted=True` leads.** Traced
through the authoritative apply path:

- `src/engine/economy.py:103` — `if result.accepted:` is entered. The mutant carries **no**
  `inventory_update` and no `ground_item_remove`/`corpse_remove`, so nothing moves.
- `src/engine/economy.py:142` — `in_tick_processed_ids.add(intent.transaction_id)` sits **inside**
  that accepted block.
- `src/engine/economy.py:289` → `src/engine/apply.py:307-308,487` — those ids land in **durable**
  `AuthoritativeState.processed_transaction_ids`.
- `src/engine/economy.py:89` and `conservation.py`'s own idempotency check then reject every retry of
  that id as `IDEMPOTENCY_VIOLATION`, permanently.

So the regression's runtime signature is: the entity is told **accepted**, receives nothing, and can
never retry that transaction for the remainder of the run. It also emits `TRANSACTION ACCEPT` to the
trace and `IntentResult(accepted=True)`, so `src/systems/strategic_systems/work_queue.py:55` and
`src/systems/strategic_systems/intelligence.py:225` — both of which detect intent failure via
`not r.accepted` — never observe a failure and never retry. A silent permanent loss, with a durable
state write behind it, on the guards whose entire purpose is preventing two entities claiming one
ground item or corpse in the same tick.

That combination — an untested guard protecting a durable-state write — is what the Durable State
Rule exists for, and it is why this is not deferred behind the other 110 survivors.

## Scope

- Add assertions that **every** rejection path in `ResourceTransactionResolver.resolve()` returns
  `accepted=False`, with its correct `ReasonCode`. One case per rejection path per source kind, not
  one representative case.
- Add the idempotency-burn assertion specifically: a **rejected** transfer must leave
  `intent.transaction_id` absent from `processed_transaction_ids` after the apply path runs. This is
  the assertion that would have caught the sharp version of the regression, and it belongs at the
  apply-path level (`src/engine/economy.py` / `src/engine/apply.py`), not only at resolver level.
- Add an architecture-test-shaped assertion that a rejected transfer produced **no** durable state
  change at all — no inventory delta, no node charge delta, no ground-item/corpse removal, no
  `processed_transaction_ids` growth. Per this repo's Testing Rule, "verify read-only logic did not
  mutate live state."
- Re-run the mutation baseline afterwards over `src/core/conservation.py` and record the new
  survivor count, so the ticket's effect is measured rather than asserted.

## Out of Scope

- **Any change to `src/` behavior.** Production code is already correct on these paths. This ticket
  adds tests only. A test that requires a production change to pass is a signal to stop and report,
  not to change production.
- **The other 110 survivors.** They are unreviewed and unsampled, and some are genuinely trivial
  (e.g. `frozen=True` → `frozen=False` on the `TransactionResult` dataclass). Killing the remainder
  is not this ticket's job; a follow-up may scope it from the same baseline record.
- Classifying equivalent mutants. The baseline explicitly records
  `"equivalent": "not-classified"`; do not retro-fit a kill-rate target onto a number that has never
  been equivalence-adjusted.
- Any change to `src/core/inventory.py`'s `ItemRegistry` consumption — owned by the open P1
  `TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS`.
- Adding `mutmut` as a project dependency. It is not one, and the baseline was produced from a
  private install in a scratch copy on purpose.

## Acceptance Criteria

1. Every rejection path in `ResourceTransactionResolver.resolve()` has a test asserting
   `accepted is False` **and** the specific expected `ReasonCode`. Asserting only `not accepted`
   does not satisfy this — a wrong reason code is its own defect class.
2. A test asserts that a rejected transfer leaves `intent.transaction_id` **absent** from
   `processed_transaction_ids` after the authoritative apply path has run.
3. A test asserts a rejected transfer produced zero durable state change across inventory, node
   charges, ground items, corpses, and `processed_transaction_ids`.
4. The reservation-guard paths (`TARGET_LOCKED`) are covered for **each** of the source kinds the
   baseline named: GROUND_ITEM, CORPSE, building, QUEST, RECRUIT/CHEST.
5. `src/` is unchanged. A `git diff --stat origin/main -- src/` over the ticket's commits is empty.
6. The mutation baseline is re-run on `src/core/conservation.py` and the new survivor count recorded
   in `tests/mutation/baselines/src_core_conservation.json` (or a sibling record), with the
   previous count retained for comparison. **The seven named flag-flip survivors must be killed**;
   a drop in total count that leaves any of them alive does not satisfy this.
   **Baseline scope note:** the baseline delta excludes `src/core/conservation.py:82-91`; the
   mutants there were killed by `tests/unit/resource/test_node_charge_accounting.py` from PR #265,
   not by anything under this ticket. Do not count those kills toward this ticket's survivor
   reduction, and do not re-count them as survivors.
7. No artifact produced under this ticket claims or implies that conservation currently has a live
   defect.

## Related Tickets
- `TCK-20260929-EPIC-TEST-BASELINE-RELIABILITY` / test-architecture Epic A (§4.7 mutation baseline)
  — produced the evidence; deliberately did **not** kill the survivors, because writing down expected
  conservation behaviour is RPG logic.
- `TCK-20260914-ITEM-REGISTRY-DUAL-CLASS-DIVERGENT-FAILURE-SEMANTICS` (open, P1) — touches
  `src/core/inventory.py`; excluded from the baseline target for that reason and excluded here.
- `TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION` — unrelated in subject; noted only so
  nobody folds this into that epic's scope-only guard.

## Related Docs
- `docs/mechanics/03_economic_laws.md` — atomic conservation. **Note:** the chapter's framing leads
  readers to `src/systems/`, where the economy files are 2–3 line re-export shims. The law is in
  `src/core/conservation.py`. Consider whether this chapter should say so.
- `docs/core/state.md` — immutability law, authoritative vs non-authoritative partitioning.
- `docs/engine/authoritative_mutation_pipeline_contract.md` — apply-path law.

## Related Stored Artifacts
- `tests/mutation/baselines/src_core_conservation.json` — the baseline record: every survivor's id,
  `file:line` and diff, plus `target.sha256`, `stale_after` (30 days / target sha change), and the
  `target_selection` rationale. Committed on branch `test-baseline-reliability` at `b1ab0c2d5`,
  unpushed at time of filing; readable via
  `git show b1ab0c2d5:tests/mutation/baselines/src_core_conservation.json`.

## Related Code Areas
- `src/core/conservation.py` (`ResourceTransactionResolver.resolve`, `TransactionResult`)
- `src/engine/economy.py` (`:89`, `:103`, `:142`, `:289`)
- `src/engine/apply.py` (`:307-308`, `:487`)
- `src/systems/strategic_systems/work_queue.py:55`,
  `src/systems/strategic_systems/intelligence.py:225` (downstream `not r.accepted` consumers)

## Assumptions / Open Questions

- **Verified, not assumed:** the baseline record was read independently from the shared git object
  store (78,274 bytes, 117 survivor entries, counts `{total 177, killed 60, survived 117, timeout 0,
  suspicious 0}`) and the caller trace above was read from production code, not inferred from the
  mutation diffs.
- **Open:** whether the 7 flag-flip survivors are best killed by 7 focused unit tests or by one
  parametrised test over the source kinds. Prefer whichever makes a future *added* source kind fail
  loudly for missing coverage — a parametrised test that silently skips a new kind is worse than
  seven explicit ones.
- **Open:** whether `src/core/inventory.py` should be added to the baseline target once
  `ITEM-REGISTRY-DUAL-CLASS` closes. Not this ticket's call.
- **Methodology note carried forward:** verify scope guards against `origin/main`, never a local
  `main` ref in a long-lived worktree — a stale local `main` reported a 132-file diff for a 6-file
  branch during this ticket's own filing week.
- **Tooling note:** `mutmut` 3.x cannot run in this repo — its trampoline rejects modules whose
  import path starts with `src.`. The baseline used 2.5.1. Anyone re-running AC-6 will otherwise
  lose the same hour.

## Implementation Notes
_(open)_

## Test Summary
_(open)_

## Files Changed
_(open)_

## Completion Summary
_(open)_
