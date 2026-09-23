# Implementation Sequence — mechanism-verification

tracking_doc: docs/plans/mechanism_claims_as_tests_initiative.md

Tickets must be implemented in this order. `implement-epic` reads this file to override
alphabetical order. `TCK-20260917-EPIC-MECHANISM-VERIFICATION` is the epic-tier parent and is not
implemented directly — it tracks the five below.

## Order

1. TCK-20260917-MECHANISM-IDENTITY-RULES-AND-CHANGE-TAXONOMY  (no deps in this batch — moved to
   first, 2026-09-17, see below)
2. TCK-20260917-MECHANISM-IMPLEMENTED-BY-COVERAGE-EXTENSION  (depends on: identity rules — see
   below)
3. TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION  (independent of `implemented_by`, but sequenced
   after coverage extension per the epic's own priority order — see below)
4. TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION  (depends on: coverage extension —
   reads `implemented_by` directly, and a 26-of-89-coverage run would measure its false-positive
   rate against the wrong substrate)
5. TCK-20260916-ATLAS-CARD-DESCRIPTION-EFFECT-CAVEAT-AUDIT  (depends on: status-language detection
   landing first — see below)

## Why This Order Matters

**Identity rules first, moved 2026-09-17 (was originally scoped after coverage extension, with the
now-superseded reasoning that it had "no deps in this batch").** That was right when written and
stopped being right once the identity-rules ticket could **split** an existing mechanism into two.
A split has to divide both the `implemented_by` binding and the `verified` verdict between the two
halves — binding 63 entries first and then splitting some of them means redoing that subset's
binding work. `action_pacing_readiness` is the proof this isn't hypothetical: it is already bound
and already verified, and the identity-rules ticket names it as the exact case its own splitting
rule must handle (a working, verified gate and a starved, unverified scaling half sharing one
verdict). At most ~8 entries are realistic split candidates (the seven bundled-name ids named in
that ticket's own Scope §3, plus `action_pacing_readiness`) — modest rework avoided, not a crisis,
but avoidable for the cost of running a cheap, code-free rules ticket first.

**Coverage extension second.** Both detectors (3 and 4) exist to be run against `implemented_by`
data. Status-language detection (3) doesn't read `implemented_by` directly, but the changed-code
drift detector (4) does — running either detector's own false-positive-rate assessment at the
current coverage measures it against the wrong substrate, and the assessment would have to be
redone once coverage grows. Coverage extension now depends only on identity rules (for the reason
above), not on anything else in this batch.

**Status-language detection before the caveat audit.** The status-language detector automates part
of what the caveat audit does by hand — both re-read the atlas/capabilities/wiring-map prose for a
status claim embedded in a description. Doing the audit first means doing that same re-read twice;
building the detector first lets the audit reuse (or at minimum be informed by) whatever the
detector already found mechanically, checking only what a mechanical pass cannot catch.

**Changed-code drift detection after status-language detection** is not a hard dependency between
the two — they read different things (one reads code diffs against `implemented_by`, the other
reads prose) — but both are sequenced after coverage extension for the same reason, and
status-language detection was scoped first in this epic's own priority order.

## Not in this sequence

`TCK-20260917-MECHANISM-THREE-TIER-AXIS-SYSTEM-MECHANISM` is explicitly **not** part of this epic
or this sequence — it is P2, blocked on identity rules landing, and filed at `tickets/todos/` root
per its own author's instruction: a P1 coverage ticket should not wait on a P2 one just because
they touch the same registry.

## Known drift between this epic's own scoping document and its measured findings

Recorded in `TCK-20260917-EPIC-MECHANISM-VERIFICATION`'s own Implementation Notes, not duplicated
here — see that ticket for: (1) `mechanism_claims_as_tests_initiative.md` §4.3's own
forward-looking-only framing of the registration gate, which the completeness pass disproved as
sufficient on its own; (2) claims-as-tests phase 1's own result being measured on a biased sample,
and the orphan-state batch's own targeted-sample result, which must be read together, not
separately.
