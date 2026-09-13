---
status: active
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE
phase: open
date: 2026-09-13
tags: [registry, process-improvement]
---

# TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE

## Title
Closing a ticket updates only its own file and the working log — nothing checks whether the fix just invalidated another open ticket's stated premise

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Three tickets in one batch (`gameplay-gaps-batch`) had premises that were already stale by the
time they were picked up — not because any of the three was unusually wrong, but because each
was proven wrong only by someone re-verifying its claim against current code before implementing,
which is not a step the ticket lifecycle itself enforces or reminds anyone to take.

**Three instances, same mechanism, same batch:**

1. **`TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING`** (commit `2f72c057f`) — filed
   claiming `GroupRecord` had no reverse reference to its own contract. `GroupRecord.contract_id`
   already existed and was already load-bearing by the time this ticket was picked up. Caught by
   reading the actual code before implementing.
2. **`TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH`** (amended, not yet
   closed, via commit `54f972a26`) — filed claiming `properties["population_id"]` is "never set
   anywhere" in the catalog-native spawn pipeline. `TCK-20260911-REGION-DECLARED-POPULATION-
   SPAWNED-ENTITY-DIVERGENCE` closed *after* this ticket was filed and added exactly that tagging
   to the same two files this ticket cites as never setting it. Caught while cross-referencing an
   unrelated fix's precedent into this ticket, not by anyone specifically auditing it.
3. **`TCK-20260910-HOTFIX-BUILD-INDEX-WARNING-STDOUT-LEAK`** (commit `7af3193d0`) — filed claiming
   3 `print()` calls needed a stdout→stderr fix. By the time it was picked up, 2 of the 3 had
   already been fixed by something else, without that work ever closing or updating this ticket.
   Caught by re-checking the code before implementing, same as case 1.

**In every case, the same underlying mechanism**: a *different* ticket closed, its fix touched
code or made a claim that directly invalidated an *open* ticket's own stated premise, and nothing
in the close-out process looks for that. Closing a ticket updates its own file
(`tickets/done/{id}.md`) and appends one row to `tickets/working_log.csv` — neither step checks
whether any other ticket in `tickets/todos/`/`tickets/inprogress/` cites the same code area or
makes a claim the just-landed change just falsified.

**A related-but-distinct case, not this ticket's own evidence but worth noting for scope
calibration**: `TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED`'s investigation found the
same *decay* shape in a different artifact — a parity ledger entry (`PROG-014`) marked `verified`
that was never actually backed by a test, discovered a third time in one file. That's not the same
mechanism as the three cases above (no other ticket closing invalidated it; it was simply never
true) — already fully covered by `TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP`. Cited
here only to show this arc keeps finding decay in whatever artifact records a claim, not because
this ticket should absorb that one's scope.

## Scope
This ticket is scoped as **the question, not a chosen mechanism** — several real options exist and
none is obviously correct without weighing cost against how often this actually bites:

- **Re-verify at pickup**: before implementing, re-check the ticket's own central factual claims
  against current code — this is what actually caught all three cases above. Cost: manual
  discipline only, no tooling; relies on whoever picks up a ticket actually doing it (which
  happened here, but isn't enforced or reminded), and taxes every pickup regardless of whether
  anything decayed.
- **Back-reference sweep at close time**: when a ticket closes, search open tickets
  (`tickets/todos/`, `tickets/inprogress/`) for shared `Related Code Areas` file paths or keyword
  overlap with the just-closed ticket's own diff, and flag candidates for a human/agent to check.
  Cost: real tooling to build; risk of false positives (shared file ≠ invalidated claim).
- **`related_code_areas` cross-matching against `docs/REGISTRY.yaml`**: since the registry already
  indexes tickets by code area, a query at close time could surface open tickets touching the same
  files without needing new metadata. Cost: depends on how precisely `Related Code Areas` is
  populated today; may need tightening first.
- **A documented convention**: state explicitly in `CLAUDE.md`'s workflow rules that a ticket's own
  central factual claims must be re-verified against current code before implementation begins,
  formalizing what already happened informally in all three cases here.
- **Do nothing further, on the grounds that re-verification is already a real and demonstrated
  practice in this arc**: a legitimate option to weigh, not dismissed — three catches in one batch
  might mean the informal practice already works; more data may be needed before investing in
  tooling.

**No recommendation between the two most concrete options here — both have a real, unresolved
cost/benefit tradeoff, not a clear winner:**

- **Re-verify at pickup** taxes *every* pickup forever, including the majority of tickets where
  nothing has decayed since filing — a fixed cost paid on every single ticket to catch a defect
  that, in this batch, hit 3 of roughly a dozen tickets touched.
- **`related_code_areas` cross-match at close** only fires when something plausibly decayed, at
  essentially zero cost to the common case — but its precision depends entirely on how accurately
  `Related Code Areas` is populated across the existing ticket corpus today, and **nobody has
  measured that**. If the field is sparse or stale itself, this option silently misses exactly the
  cases it exists to catch.

**Measuring how accurate `related_code_areas` actually is across the existing ticket corpus is
probably the real first step** for choosing between these two, and it hasn't been done — this
ticket's own investigation should start there rather than guessing which option is cheaper in
practice.

## Related Shapes (naming only — not this ticket's own scope)
This is one of at least three instances of the same underlying gap, seen from different angles:
**the close/handoff path never checks outward.**

1. **Premise decay** (this ticket) — a ticket closes, its fix invalidates part of an open ticket's
   premise; nothing propagates back to the open ticket.
2. **Unfiled follow-ons** — a ticket closes citing follow-up work that never actually gets filed as
   a real ticket, so the citation points at nothing.
3. **Unpublished handoffs** — an artifact is produced for another track and never made visible
   beyond the session that wrote it, so the handoff reaches one reader and looks complete from both
   ends. Not hypothetical: this very PR's own `rpg_knowledge_investigation_closure_plan.md` cited
   `docs/plans/agent_infrastructure/reachability_verification_findings.md`, a doc written on
   another branch, never pushed, cited across sessions as shared context that nobody but its author
   could actually read. It took both a sender who didn't confirm delivery and a receiver who didn't
   publish — "whose fault" is the wrong question; "neither end has a visibility check" is the right
   one.

A "does this premise still hold" check and a "was this actually published" check are the same
*kind* of mechanism — whoever eventually builds one may be able to build all three cheaply, which
is worth recording even though this ticket's own scope stays the premise-decay question only. The
handoff-visibility mechanism itself belongs to a different track, not here.

## Out of Scope
- Building any of the candidate mechanisms above — this ticket files the problem and investigates
  options; it does not implement a fix.
- Instances 2 and 3 above — named for scope calibration and future cross-reference only, not
  absorbed into this ticket's own investigation.
- `TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP`'s own scope (a different artifact, a
  different decay mechanism — see Request Summary's note above).
- Re-litigating any of the three cases' own already-closed/already-corrected dispositions.

## Acceptance Criteria
- [ ] Real investigation of tooling cost/precision for the back-reference-sweep and registry-
      cross-matching options, not just the re-verification-convention option (which requires no
      tooling and is easy to recommend by default without checking the others).
- [ ] A recommendation among the options in Scope, with rationale, brought to peer/user review
      before any implementation.
- [ ] No implementation without that review.

## Related Tickets
- `TCK-20260913-RECRUITMENT-CONTRACT-GROUP-LINKAGE-MISSING` (done — case 1)
- `TCK-20260911-PENDING-INFORMATION-RESPONSES-CATALOG-ACTOR-ID-MISMATCH` (open — case 2)
- `TCK-20260910-HOTFIX-BUILD-INDEX-WARNING-STDOUT-LEAK` (done — case 3)
- `TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP` (open — related-but-distinct decay
  shape in a different artifact, see Request Summary)

## Related Docs
- `docs/REGISTRY.yaml` (a candidate mechanism's own data source — see Scope)
- `CLAUDE.md` (a candidate mechanism — documenting the convention explicitly)

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `tickets/working_log.csv` (the only durable record a ticket close currently writes to)
- `tools/generate_registry.py` (owns `docs/REGISTRY.yaml`'s generation — relevant if that option is
  chosen)

## Assumptions / Open Questions
- Whether this is worth dedicated tooling at all, versus staying a documented manual convention, is
  the central open question this ticket exists to answer — not pre-judged here.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
