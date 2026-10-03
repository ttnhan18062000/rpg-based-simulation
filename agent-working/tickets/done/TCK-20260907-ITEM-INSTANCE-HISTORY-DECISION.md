---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260907-ITEM-INSTANCE-HISTORY-DECISION
phase: done
date: 2026-09-07
tags: [content, architecture]
---

# TCK-20260907-ITEM-INSTANCE-HISTORY-DECISION

## Title
Idea 30 (Possessions With Personal History) — activate ENABLE_ITEM_INSTANCE_HISTORY or confirm deliberate deferral

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Dormant Mechanism Closure epic (`TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE`) child 4 of 6.
`ENABLE_ITEM_INSTANCE_HISTORY` defaults `OFF` (`src/domains/optimization/feature_flags.py:134`);
`ItemInstanceService.maybe_create_instance()` (`src/core/inventory.py:221`) is real, confirmed
2026-09-07, but has zero real (non-test, non-definition) call sites anywhere in `src/` — the flag has
never been exercised in a live run. Unlike the other tickets in this epic, this is a real product
decision (activate and verify, or leave deliberately dormant), not a wiring bug to fix.

## Scope
- Confirm the real current state of `ItemInstanceService`'s implementation (is it feature-complete
  behind the flag, or a partial scaffold?) during Investigate.
- Present the roadmap owner (the user, via `AskUserQuestion` or equivalent) with a real decision:
  activate the flag and verify the mechanism works end-to-end in at least one real corpus run, or
  record an explicit, evidenced reason to leave it dormant for now.
- If activated: confirm no regression in existing item/inventory tests, and add real test coverage
  proving ownership-history actually accumulates across a real gameplay sequence (LOOT→CRAFTED→
  GIFT→INHERITED, matching M9's own idea-30 corpus-test spec from `CORPUS-TEST-ZERO-NEW-WORLD-
  ASSERTIONS`, if that ticket's own idea-30 work didn't already cover this).
- If deferred: record the reason clearly in this ticket and in the plan doc, not silently left open.

## Out of Scope
- Building any new item-history mechanic beyond what `ItemInstanceService` already implements.
- Any other item from the Dormant Mechanism Closure epic's scope.

## Acceptance Criteria
- [ ] A real decision (activate or defer) is made and recorded with an evidenced reason.
- [ ] If activated: real test coverage confirms the mechanism works end-to-end with no regression.

## Related Tickets
- `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` (parent epic)
- `TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS` (M9's own idea-30 corpus-test work, check for
  overlap during Investigate)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_dormant_mechanism_closure_plan.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `src/core/inventory.py`
- `src/domains/optimization/feature_flags.py`

## Assumptions / Open Questions
- Whether to activate or defer is a real product decision, not resolved here.

## Implementation Notes

### Investigation, 2026-09-07 (orchestrator-directed fork, decision NOT made here)

**Is the primitive feature-complete or a scaffold?** Feature-complete at the *primitive* level,
confirmed via direct code read plus a real `ApplyPath.apply_partial()` round-trip test
(`tests/simulation_quality/test_item_owner_history_corpus.py`, added by M9's own
`TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS`): `ItemInstanceService.maybe_create_instance()`
(`src/core/inventory.py:238`) correctly mints, the per-tick id-allocator discipline is real and
documented, `StateUpdate.merge_many` correctly extends `item_instance_updates`, and
`ApplyPath.apply_generation`/`apply_partial` (`src/engine/apply.py:252-261`) correctly applies
`owner_history_append` onto the immutable `ItemInstance.owner_history` list across multiple
transfers. `acquired_method` is set once at mint time and is correctly immutable thereafter (M9's own
test docstring flags and corrects the original ticket's mistaken framing that it "accumulates all 4
values" — it doesn't; only `owner_history` accumulates, `acquired_method` never changes after mint).

**Zero real call sites, confirmed still true.** `grep -rn "maybe_create_instance" src/` outside
`src/core/inventory.py` itself and the docstring/comment in `feature_flags.py` returns nothing — the
only two callers anywhere in the repo are the two test files
(`tests/unit/resource/test_item_instance_history.py`,
`tests/simulation_quality/test_item_owner_history_corpus.py`). No loot/craft/gift/inherit domain
phase calls it.

**New finding, strengthens the case for deferral, not in the ticket's original text:** there is also
**zero real consumer** of `state.item_instances`/`ItemInstance.owner_history` anywhere in `src/`
(`grep -rn "item_instances\[|item_instances\.get" src/` outside the writer files themselves returns
nothing). Unlike this epic's other dormant-mechanism tickets (idea 56/57's `region_culture_states`/
`entity_legend_facts`, `SocialBond.role`), which each had a real, already-shipped *consumer* silently
starved of a producer, idea 30 has **neither a producer nor a consumer wired** — activating the flag
today would mint typed records that nothing reads, narrative or scoring-wise.

**The `significant=True` trigger criteria was deliberately left undecided, not merely unwired** —
confirmed via the feature flag's own registration comment (`src/domains/optimization/
feature_flags.py:127-133`, from the original `TCK-20260831-ITEM-INSTANCE-HISTORY`): *"no production
call site passes significant=True yet (significance_flag trigger criteria is an explicit open design
decision, not invented by this ticket — see ticket AC #5)."* This is direct evidence the original
ticket's own author already treated "what makes an item significant enough to instance-track" as an
open product/design question, not an oversight.

**What real "activate" work would require** (all net-new, not already scaffolded):
1. A real design decision on significance criteria (item rarity tier? named/unique items only?
   quest-critical items?) — the open question `feature_flags.py` itself already flags.
2. Real domain call sites at every acquisition point matching `AcquiredMethod`'s 4 values: a loot-drop
   phase (LOOT), a crafting-output phase (CRAFTED), a trade/gift phase (GIFT), and a
   death/inheritance phase (INHERITED) — each must respect the per-tick single-`ItemInstanceService`-
   instance discipline the class docstring mandates.
3. At least one real consumer — otherwise this repeats the exact "built but not observable" pattern
   this whole epic exists to close, just one step earlier (no producer AND no consumer, vs. this
   epic's other tickets' producer-only gap). Candidates not investigated further here (out of this
   ticket's own scope per its Out-of-Scope): a narrative/flavor-text hook, or a SimQ pillar rule
   (matching M7's own pattern).
4. New corpus-world content plus calibration proof, matching every other ticket in this epic's own
   evidentiary bar.

**Argument for deferring instead:** the mechanism is inert with no downstream value today (no
consumer exists); activating it in isolation (steps 2 above) without a consumer (step 3) would only
convert a "built but dormant" gap into a "built, wired, but still narratively invisible" gap — no net
improvement, and real implementation cost (4 new call sites + a consumer + corpus content) for a P3
idea. This looks structurally different from every other idea closed in this epic, all of which had
a real waiting consumer.

**Decision NOT made here per this fork's directive** — the real activate-vs-defer choice is the
orchestrator's/user's to make, brought to them directly with this evidence.

### Decision, 2026-09-07 (real user decision, via `AskUserQuestion`)
**Deferred.** `ENABLE_ITEM_INSTANCE_HISTORY` stays `OFF`. Rationale (as presented and accepted):
idea 30 is structurally different from every other ticket in this epic — it has neither a
producer nor a consumer wired (idea 56/57 and `SocialBond.role` each had a real, already-shipped
consumer silently starved of a producer; idea 30 has nothing on either end). Activating the flag
in isolation today would only convert a "built but dormant" gap into a "built, wired, but still
narratively invisible" gap, with real new-work cost (a significance-criteria design decision, 4
new domain call sites, at least one real consumer, new corpus content) disproportionate to a P3
idea. Revisit only if/when a real consumer use case is proposed.

## Test Summary
No test-affecting code was written — this ticket resolves to a documented product decision
(defer), not an implementation. No regression risk.

## Files Changed
- `tickets/todos/dormant-mechanism-closure/TCK-20260907-ITEM-INSTANCE-HISTORY-DECISION.md` → moved
  to `tickets/done/`
- `docs/plans/rpg_design_roadmap/rpg_dormant_mechanism_closure_plan.md` (item 4 updated to record
  the ratified deferral decision)

## Completion Summary
Idea 30's `ItemInstanceService` is feature-complete at the primitive level but genuinely inert —
zero producers, zero consumers, unlike every other mechanism this epic closed. Confirmed via
direct grep and code read (not just re-asserting the epic's original scoping claim). Real user
decision, ratified via `AskUserQuestion`: defer, with the evidenced reason recorded here and in
the roadmap plan doc, not silently left open.
