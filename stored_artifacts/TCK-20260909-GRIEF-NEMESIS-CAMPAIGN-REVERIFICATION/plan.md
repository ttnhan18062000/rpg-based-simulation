# Plan — TCK-20260909-GRIEF-NEMESIS-CAMPAIGN-REVERIFICATION

This ticket is a determination, not an implementation — no production code changes. Plan:

1. Trace both real trigger paths (`grief_urgency_triggered` mid-episode + episode-boundary,
   `nemesis_relation_formed` episode-boundary only) before running anything, per peer review's
   exercisability warning — avoid the same trap as the original `GRIEF-NEMESIS-REACHABILITY`
   ticket (verified synthetically instead of through a real run).
2. Run a real multi-episode campaign to test `nemesis_relation_formed` (structurally requires 2+
   episodes) and grief's episode-boundary path.
3. Run a real single-episode campaign (longer duration) to test grief's mid-episode path
   independently, since it doesn't depend on multi-episode survivor reconstruction.
4. For any leg that can't be exercised, root-cause *why* (not just report "zero") before
   concluding negative vs. inconclusive — distinguish "mechanism broken" from "precondition never
   met" with direct evidence (e.g. checking `trust_history` at the moment of a real death), per
   peer review's explicit standard for this batch.
5. Do NOT hand-construct carry-forwards or shorten scope to route around the
   survivor-position-collision blocker discovered mid-investigation — that would reproduce the
   exact synthetic-verification flaw this ticket exists to correct. File the blocker as its own
   ticket instead.
6. Record real evidence-backed results (confirmed / inconclusive / blocked) in this ticket and in
   `TCK-20260824-GRIEF-NEMESIS-REACHABILITY`'s own addendum, per AC3.

## Scope guards
- No fix attempted for anything found broken or blocked — that's this ticket's own Out of Scope,
  matching the origin ticket's framing ("if the fix isn't trivial, peer-routed decision").
- The survivor-position-collision bug found mid-investigation is filed as its own ticket
  (`TCK-20260911-CAMPAIGN-SURVIVOR-RECONSTRUCTION-POSITION-COLLISION`), not fixed here.
