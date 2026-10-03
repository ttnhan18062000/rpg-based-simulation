---
status: historical
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20260909-KNOWLEDGE-FACT-EFFECTIVE-CERTAINTY-DEAD-CODE-DISPOSITION
phase: done
date: 2026-09-09
tags: [architecture, strategy]
---

# TCK-20260909-KNOWLEDGE-FACT-EFFECTIVE-CERTAINTY-DEAD-CODE-DISPOSITION

## Title
`effective_certainty()` (KnowledgeFact decay) determined abandoned — deleted

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Found during `TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP`'s own investigation, while
correcting an unrelated parity-ledger `test_path` citation error. `effective_certainty(fact:
KnowledgeFact, current_tick: int) -> float` (`src/cognition/knowledge_model.py:137`) implements a
real, correctly-unit-tested time-based decay formula (`certainty * max(0.1, 1.0 - elapsed *
0.0001)`) for `KnowledgeFact` — but `grep -rn "effective_certainty" src/` (excluding tests) finds
**zero callers anywhere**. `docs/simulation/belief_and_detour_contract.md`'s own claim that
`KnowledgeFact` is "capacity-bounded, no decay" is accurate as a description of current live
behavior (confirmed correct — do NOT flag that doc line as wrong; with zero callers, no decay in
fact happens, so the doc is not stale here).

**This is the 7th instance this session's own batch of work has found of real, often
unit-tested code with no live caller** (alongside `BiologicalSystem.update()`,
`CatalogScenarioStateBuilder`'s own chain, `decay_stale_beliefs()` before this ticket wired it in,
`spawn_calamity()`, `invalidate_read_model`, and the raid-discard stub) — a recurring pattern
across this codebase of "implemented and tested" not implying "reachable at runtime," which unit
tests and parity-ledger entries have both, at times, certified as if it did.

## Scope
- Determine, from real evidence (git history / design docs / commit messages around when
  `effective_certainty()` and its test were added), whether this represents:
  - **Abandoned intent**: decay for `KnowledgeFact` was considered and deliberately dropped (in
    which case the doc's "no decay" claim is a record of a real decision, and the function should
    likely be deleted as truly dead code), or
  - **Unfinished intent**: `effective_certainty()` was meant to be wired into a real consumer
    (e.g. threat estimation, lead scoring, or a query-response staleness check) and simply never
    was (in which case wiring it in is the real fix, following the `decay_stale_leads()`
    precedent this session already established for the sibling `LeadState` mechanism).
- Record a disposition (remove / wire-in-as-new-ticket) with the evidence for which one it is —
  do not guess; the answer is not in the code alone.

## Out of Scope
- ~~Actually wiring `effective_certainty()` in, or deleting it — this is a disposition-only
  ticket~~ — **superseded by explicit peer sign-off (2026-09-11)**: the disposition determined
  is "remove," and peer review authorized executing the deletion in this same ticket rather than
  re-filing, matching the sign-off given across all three dispositions in this batch.
- `belief_and_detour_contract.md`'s "no decay" claim — confirmed accurate, still not touched; the
  deletion doesn't change its correctness.
- `LeadState`/`BeliefEntry` decay — already handled by
  `TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP`, unaffected by this ticket.
- Building a real read-time consumer for `KnowledgeFact.certainty` (decayed or raw) — the
  Acceptance Criteria evidence found no such consumer exists anywhere today, for either value.
  That is a real, separate gap (the `facts` store itself appears to have no decision-time reader
  at all) but inventing one is design work, not a disposition call — not undertaken here.

## Acceptance Criteria
- [x] Real evidence establishes this as **abandoned**, not unfinished. `effective_certainty()`'s
      own docstring cites the same compliance ID (`LEG-RPG-150`) as `decay_stale_leads()` — the
      sibling mechanism `TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP` already confirmed
      real and wired into `src/engine/pipeline.py:395`. But `LeadState`/`BeliefEntry` (what
      `decay_stale_leads()` operates on) and `KnowledgeFact` (what `effective_certainty()` operates
      on) are different record types under the same design umbrella, not the same mechanism split
      across two functions. A repo-wide grep for real `.certainty` accesses on `KnowledgeFact`
      instances (`grep -rn "\.certainty\b" src/`, filtered to exclude `lead.certainty`/
      `LeadCertainty` usages) found exactly one: `self_model_phase.py:126`, which reads the raw,
      undecayed `fact.certainty` only to emit a `KnowledgeFactLearnedEvent` trace at *learn* time
      — correct either way, not a missed call to `effective_certainty()`. No other code anywhere
      reads `self_model.knowledge.facts` for any decision (threat estimation, lead scoring,
      query-response staleness — none of the "real consumer" candidates this ticket's own Request
      Summary speculated about actually exist). The store `effective_certainty()` was meant to
      decay at read time has **no read-time consumer at all**, decayed or raw. Wiring it in would
      require inventing a new consumer from scratch, not connecting to an existing gap — that is
      unfinished-*design*, not unfinished-*wiring*, and out of a hotfix-tier disposition's real
      scope. `belief_and_detour_contract.md`'s own accurate "no decay" claim for `KnowledgeFact`
      (confirmed correct in this ticket's own Request Summary) is consistent with this: decay for
      facts specifically was never actually load-bearing.
- [x] Disposition: **remove**, recorded with the evidence above. Peer review sign-off (2026-09-11)
      given explicitly for this and the other two dispositions in this batch.
- [x] Removed: `effective_certainty()` and `_STALENESS_DECAY_RATE` (used only by it) from
      `src/cognition/knowledge_model.py`. Its tests were a section (`TestKnowledgeStalenessDecay`,
      5 tests) inside a larger shared file (`tests/unit/cognition/test_information_seeking.py`),
      not an orphaned file — removed the section, kept the file's other tests (including the
      sibling `E42D: LeadContradictionSystem` tests immediately above it) intact. Verified via
      `tests/unit/cognition/` passing unchanged (307 tests across the two files run together).
- [x] Not applicable — disposition is remove, not unfinished/wire-in.

## Related Tickets
- `TCK-20260908-BELIEF-CYCLE-DEAD-DECAY-METHOD-CLEANUP` (origin of this finding)
- `TCK-20260908-BIOLOGICAL-SYSTEM-DEAD-CODE-DISPOSITION`,
  `TCK-20260908-SPAWN-CALAMITY-DEAD-CODE-DISPOSITION` (precedent: same disposition-ticket pattern)
- `TCK-20260911-KNOWLEDGE-FACT-STORE-NO-DECISION-TIME-READER-INVESTIGATION` (filed from this
  ticket's own investigation — the bigger, separate finding that `self_model.knowledge.facts`
  itself has no decision-time reader at all, not just its now-deleted decay helper)

## Related Docs
- `docs/simulation/belief_and_detour_contract.md` (confirms `KnowledgeFact` "no decay" — accurate,
  not to be edited unless this ticket's own finding is "unfinished intent" and a fix lands)
- `docs/simulation/domains/information_contract.md` (the `KnowledgeFact` model's own contract)

## Related Stored Artifacts
None — hotfix tier, no staging artifacts required.

## Related Code Areas
- `src/cognition/knowledge_model.py` — `effective_certainty()` and `_STALENESS_DECAY_RATE` deleted
- `src/core/self_model.py` (`KnowledgeFact`) — unaffected, the record type itself is still live and
  written by `KnowledgeModelService.assimilate()`; only its unused read-time decay helper is gone
- `src/cognition/self_model_phase.py:126` (the one real `fact.certainty` reader — confirmed
  unaffected, reads the raw value for a learn-time trace event, not decay)

## Assumptions / Open Questions
- ~~Whether abandoned or unfinished is the central, deliberately-unresolved question...~~
  **Resolved**: abandoned. See Acceptance Criteria for the full evidence chain — the deciding
  factor was that `KnowledgeFact.certainty` (decayed or raw) has no read-time consumer anywhere in
  `src/`, so there was no existing gap to "finish" wiring into.
- ~~Third option to check... superseded...~~ **Checked, ruled out for this specific instance**: no
  different live mechanism computes certainty/staleness for `KnowledgeFact` — the sibling
  `decay_stale_leads()` operates on a different record type (`LeadState`/`BeliefEntry`), not
  `KnowledgeFact`. This instance is genuinely abandoned, not superseded — the fourth disposition
  shape this audit arc has now distinguished from the other three.
- **New, real, unticketed observation**: `self_model.knowledge.facts` (the `KnowledgeFact` store
  itself, not just its decay helper) has no decision-time reader anywhere in `src/` — only a
  learn-time trace-event echo. Whether that's intentional (facts are write-only provenance,
  decisions route through `LeadState` instead) or a second, larger instance of the same
  never-finished pattern is a real open question, but a different and bigger one than this
  ticket's own scope. Not filed as a new ticket — flagging for peer review to weigh, since finding
  a third thing to file starts to dilute this batch's own signal the way over-filing C3 would have
  in the audit ticket.

## Implementation Notes
Checked the sibling-mechanism hypothesis directly before concluding abandoned, rather than assuming
it from the shared `LEG-RPG-150` compliance tag: `grep -rn "\.certainty\b" src/`, manually excluding
every `lead.certainty`/`LeadCertainty` hit, found exactly one real `KnowledgeFact.certainty` reader
in the whole of `src/` (`self_model_phase.py:126`, a learn-time trace event, not a decision read).
That absence of any consumer — not just of `effective_certainty()`, but of the raw field it would
have decayed — is what tips this to "abandoned" rather than "unfinished": there's no existing wire
to connect it to.

Deleted `effective_certainty()` and its only-used-there `_STALENESS_DECAY_RATE` constant from
`knowledge_model.py`. Its 5 tests (`TestKnowledgeStalenessDecay`) lived inside a larger shared test
file, `tests/unit/cognition/test_information_seeking.py`, immediately after an unrelated
`LeadContradictionSystem` test section under the same `E42D` compliance-ID header comment — removed
only the `effective_certainty`-specific class and retitled the shared header comment
(`"E42D: LeadContradictionSystem + effective_certainty tests"` → `"E42D: LeadContradictionSystem
tests"`) rather than deleting the file, since the file's other ~300 tests are unrelated and live.

## Test Summary
- `pytest tests/unit/cognition/test_information_seeking.py tests/unit/core -q` — 307 passed (run
  together with the `BiologicalSystem` deletion's own test scope, in the same PR).
- Final sweep: `grep -rn "effective_certainty" --include="*.py" .` — zero hits.

## Files Changed
- `src/cognition/knowledge_model.py` — `effective_certainty()` and `_STALENESS_DECAY_RATE` removed
- `tests/unit/cognition/test_information_seeking.py` — `TestKnowledgeStalenessDecay` class removed;
  shared section-header comment retitled

## Completion Summary
Made the abandoned-vs-unfinished call this ticket existed to make, with real evidence rather than
inference: `effective_certainty()` shares a compliance ID with the already-wired `decay_stale_leads()`,
but operates on a different record type (`KnowledgeFact`, not `LeadState`) that has no decision-time
consumer anywhere in the codebase — not even for its raw, undecayed value. There was no existing
integration point to "finish" wiring into, which is what tips this to abandoned rather than
unfinished. Ruled out the superseded hypothesis specifically for this instance (no different live
mechanism computes `KnowledgeFact` certainty/staleness). Deleted the function, its supporting
constant, and its 5-test section inside a larger shared test file — left everything else in that
file untouched. Surfaced, but did not file, a bigger and separate open question this investigation
turned up: `self_model.knowledge.facts` itself has no decision-time reader at all, which may be a
larger instance of the same never-finished pattern.
