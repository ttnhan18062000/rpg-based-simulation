---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260920-SWEEP-TICKET-BRANCH-RECONCILIATION
phase: done
date: 2026-09-20
tags: [architecture, documentation]
---

# TCK-20260920-SWEEP-TICKET-BRANCH-RECONCILIATION

## Title
Reconcile two leftover parallel branches that independently edited
`TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP` after this session's own PR #219–#224
sequence merged everything else

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Peer review, after PR #224 merged: reconciliation of this session's own leftover parallel branches
was unblocked. Checked all of this session's own branches (the disclosed set from earlier in the
session: `combat-hostility-source-divergence-unification` → merged as #222,
`agent-monitoring-manifest-ci-failure` → handed to `agent-working-design`, not touched,
`combat-engage-scorer-hostility-investigation`, and `mechanism-system-membership-foundation` →
merged as #224). Found real, unmerged content on two of them: `combat-engage-scorer-hostility-
investigation` and `combat-hostility-source-divergence-unification` both independently created and
then separately edited `tickets/todos/TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP.md`
(the sweep ticket was filed *after* the two branches had already diverged from a common ancestor
where the file didn't exist yet, so this is a genuine independent-creation-then-divergent-edit
situation, not a simple sequential edit history).

## Scope
Union the evidence both branches recorded; do not reconcile conclusions unless they are genuinely
contradictory (per peer's own explicit rule for this reconciliation). Checked directly, not
assumed: the two branches' edits are **not contradictory** — `combat-hostility-source-divergence-
unification`'s own commits (`f9f960483`, `9426e199f`) are strictly the *earlier* draft of the
sweep ticket (files an open question about `CombatEngageScorer`'s own error direction);
`combat-engage-scorer-hostility-investigation`'s own commits (`32366800c`, `e2b2f6201`) are the
*later* draft that actually performed that investigation and answered the open question,
superseding the earlier draft's content wholesale (confirmed by diffing both branches' full file
content against their shared merge-base — the later branch's every section is either identical to
or a strict elaboration of the earlier one, never a different claim about the same fact). Main's
own current copy (brought in by PR #222) was the *earlier*, less-complete draft — this ticket
replaces it with the later, complete one.

1. Replace `tickets/todos/TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP.md` with
   `combat-engage-scorer-hostility-investigation`'s own final version (the strict superset).
2. Complete the one deferred item that version itself flagged as blocked: a cross-reference to
   `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN`, deferred because that epic's file sat in
   PR #222's still-open branch at the time — #222 has since merged, so this is now addable for
   real. Added to both the sweep ticket's own Related Tickets and the epic's own Related Tickets
   (mirroring the existing pattern already used for the sibling
   `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` cross-reference).
3. Apply `combat-engage-scorer-hostility-investigation`'s own real, previously-unmerged addendum to
   the already-closed `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION.md` (22 lines,
   cross-referencing the scorer's own dispatch-discard finding as a deeper cause for that
   investigation's own candidate 4).

## Out of Scope
- Restarting, re-verifying, or re-scoping `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP`
  itself — it stays paused, per explicit instruction. This ticket reconciles the *record* of what
  was already learned; it does not resume the sweep.
- Any code change — this is a documentation/ticket-content reconciliation only.
- `agent-monitoring-manifest-ci-failure` — that branch is `agent-working-design`'s own domain, not
  touched here.
- Deleting the two source branches — reconciliation lands first; deletion is a separate, later
  step per peer's own explicit sequencing.

## Acceptance Criteria
1. The sweep ticket's own content on `main` reflects the later, more complete draft, not the
   earlier one PR #222 happened to bring in.
2. No contradictory claim from either branch was silently adjudicated — checked directly (see
   Implementation Notes) and confirmed none exists; if one had, this ticket would stop and flag it
   per peer's own explicit instruction rather than resolve it here.
3. The one genuinely deferred item (the epic cross-reference) is completed now that its own
   precondition (PR #222 merged) is satisfied.
4. `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP`'s own `## Status`/pause framing is
   unchanged — this ticket does not alter what work remains open on it.

## Related Tickets
- `TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP` — the ticket being reconciled; stays
  paused, untouched in scope.
- `TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` — receives the previously-unmerged
  addendum.
- `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` — receives the now-unblocked cross-reference.

## Related Docs
None.

## Related Stored Artifacts
None — hotfix tier, self-evident intent captured in the ticket itself per this repo's own
hotfix-tier convention (no staging artifacts required).

## Related Code Areas
- `tickets/todos/TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP.md`
- `tickets/done/TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION.md`
- `tickets/todos/progression-starvation-chain/TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN.md`

## Assumptions / Open Questions
None open — the one question this ticket needed to answer (are the two branches' claims
compatible or contradictory) was checked directly and resolved: compatible, one supersedes the
other cleanly.

## Implementation Notes
**The no-contradiction check, performed directly, not assumed.** Found the merge-base of the two
branches (`ff00d95c4`) and confirmed the sweep ticket file did not exist there — both branches
created it independently after diverging. Extracted the full file content from both branch tips
(`git show <branch>:<path>`) and diffed them directly: exactly two differing sections (the
`scorers.py:108` investigation entry, and the Priority-order/Related-Tickets/Implementation-Notes/
Completion-Summary sections) — every other section (Related Docs, Related Stored Artifacts,
Related Code Areas, Assumptions/Open Questions, sites 2-8's own descriptions) is byte-identical
between the two. In every differing section, `combat-engage-scorer-hostility-investigation`'s own
version either restates `combat-hostility-source-divergence-unification`'s own claim verbatim or
directly answers a question that version posed as open (e.g. the "counterintuitive error
direction" question is explicitly resolved, not contradicted, by the later investigation's own
"this resolves the counterintuitive-direction tension... not by picking a side" language) — never
a different factual claim about the same code. Confirmed against `main`'s own current copy too:
byte-identical to `combat-hostility-source-divergence-unification`'s own (earlier) version,
confirming PR #222 brought in the less-complete draft.

**The completed cross-reference is new content, not merely copied** — written fresh in this ticket
since neither source branch could write it (the epic ticket sat unmerged in #222 until after both
branches' own last real commits).

## Test Summary
`tests/docs`, `tests/integrity`, `tests/static` (156 passed, 2 skipped, 1 deselected, 2 xfailed,
all pre-existing) — no regression from ticket-content-only changes. Frontmatter validated on all
3 touched files.

## Files Changed
- `tickets/todos/TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP.md` — replaced with the
  later, complete draft; completed the one deferred cross-reference.
- `tickets/done/TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION.md` — applied the
  previously-unmerged addendum.
- `tickets/todos/progression-starvation-chain/TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN.md` —
  added the new cross-reference.

## Completion Summary
**Done.** No contradiction found between the two branches — union was straightforward because one
branch's own content was a strict, later superset of the other's, not two independent parallel
observations needing careful merging. The one real judgment call (confirming no contradiction
existed rather than assuming it) was performed directly via full-file diffing against the
branches' own shared merge-base, not inferred from commit messages alone. The sweep ticket's own
paused status and remaining scope are unchanged, per this ticket's own explicit scope guard.
