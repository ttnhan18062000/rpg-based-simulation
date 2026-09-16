---
status: active
layer: ticket
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE
phase: open
date: 2026-09-14
tags: [registry, process-improvement]
---

# Plan — TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE

**This ticket's own Acceptance Criteria require a recommendation brought to peer/user review before
any implementation, and explicitly: "No implementation without that review."** This plan therefore
does not describe code changes — it records the recommendation investigation.md's measurements
support, for that review, and stops there.

## Recommendation (revised after correcting Measurement 2 — see investigation.md)

An earlier pass of this investigation measured `## Related Code Areas` as 53.4% empty on the real
open-ticket corpus and recommended against registry cross-matching on that basis alone. That number
was re-checked and corrected: it measured "visible to the registry's current backtick-only
extractor," not "the field is actually empty." True content population is **96.6%** (56/58 open
tickets have real, accurate Related Code Areas content) — the gap is an extraction regex that
requires backtick-quoting, not an authorship problem. Full detail and the corrected numbers are in
`investigation.md`'s "Correction to Measurement 2" section.

**This changes the recommendation from "eliminate registry cross-matching" to "two live candidates,
bring both to review":**

1. **Fix the extractor + extend the registry's indexing scope.** `generate_registry.py::
   parse_related_code_areas()` would need to also recognize plain `- path` bullets, not only
   backtick-quoted ones (a small, bounded, mechanical regex change), and `generate_registry.py`'s
   ticket-collection walk would need to also index `tickets/todos/`/`tickets/inprogress/`, not only
   `tickets/done/` (Measurement 1's own gap — unaffected by the correction, still real). Together
   these would make registry-visible coverage ~96% instead of the original scoping's assumed-but-
   unmeasured "near-zero cost," and instead of the first-pass-corrected 46.6%. This is now the
   cheaper of the two concrete options, not the more expensive one.
2. **A close-time full-text keyword/path sweep** — search every open ticket's whole body text (not
   a structured field) for mentions of the closing ticket's own git-touched file paths. This is the
   "keyword overlap" half of the ticket's own already-scoped "back-reference sweep" option, not a
   new fourth mechanism. It needs neither the extractor fix nor the indexing extension, at the cost
   of building and maintaining a second scan path outside the registry rather than repairing the
   registry's existing one.

**Do not recommend building anything yet without the peer/user review this ticket's AC requires.**
This plan stops at "here are the two options the corrected data supports, and why neither is
obviously superior now" — actual tooling cost for either (regex correctness on the extractor;
false-positive rate on a full-text keyword sweep; where either should run in the Finalize sequence)
is real design work that has not been scoped here, deliberately, per Out of Scope ("Building any of
the candidate mechanisms above — this ticket files the problem and investigates options; it does
not implement a fix").

## Also worth recording for whoever picks up implementation later (if approved)

- The re-verify-at-pickup option remains viable and already has demonstrated real-world catches (3
  in one batch, per this ticket's own Request Summary) — it costs nothing to keep doing informally
  regardless of what gets built, and a documented-convention bullet in CLAUDE.md (the cheapest of
  the 5 original options) could be adopted independently of, and before, any tooling investment.
- If a full-text sweep is built, it should reuse `_git_touched_paths()`
  (`tools/gate_checks/done_checker_static.py:410`) for "what did this closing ticket's diff actually
  touch," rather than re-deriving that from `Related Code Areas` text — `_git_touched_paths` already
  exists and is git-diff-based, not self-reported-field-based, avoiding exactly the accuracy problem
  Measurement 2/3 surfaced on the *reading* side; the same accuracy concern would apply symmetrically
  to the *closing* ticket's own declared paths if that were used as the query instead of the real
  diff.

## No code changes in this ticket

No files under `src/`, `tools/`, or `tests/` are modified by this ticket. Only:
- `staging_artifacts/TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE/` (this
  investigation/plan/test_plan).
- The ticket file itself (moved to `tickets/inprogress/`, Implementation Notes will record the
  investigation's conclusion once review happens).
