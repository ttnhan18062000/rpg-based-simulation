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

## Recommendation

**Do not build "registry cross-matching" as originally scoped.** Measurement 1 (investigation.md)
found `docs/REGISTRY.yaml` does not index open tickets at all today, and Measurement 2 found that
even if it did, the `## Related Code Areas` field it would key off is empty on 53.4% of open
tickets — a majority miss, not a marginal one. The option as described in this ticket's own Scope
is not "near-zero cost, unmeasured precision"; it is real-cost-to-build with measured-low precision.

**Recommend prototyping a close-time full-text keyword/path sweep instead** — search every open
ticket's whole body text (not a structured field) for mentions of the closing ticket's own git-
touched file paths, and flag candidates for human/agent review. This is the "keyword overlap" half
of the ticket's own already-scoped "back-reference sweep" option, not a new fourth mechanism. It
sidesteps the sparsity problem entirely (it doesn't depend on any ticket having filled in `Related
Code Areas`), and Measurement 3 shows that where citations DO exist they are accurate, so a hybrid
that checks both the structured field (when present) and a full-text fallback would not be strictly
worse than either alone.

**Do not recommend building anything yet without the peer/user review this ticket's AC requires.**
This plan stops at "here is the option this data supports" — actual tooling cost (false-positive
rate on a full-text keyword sweep, whether to gate it as blocking or advisory-only, where it should
run in the Finalize sequence) is real design work that has not been scoped here, deliberately, per
Out of Scope ("Building any of the candidate mechanisms above — this ticket files the problem and
investigates options; it does not implement a fix").

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
