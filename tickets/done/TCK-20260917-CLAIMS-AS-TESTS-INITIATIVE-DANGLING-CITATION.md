---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260917-CLAIMS-AS-TESTS-INITIATIVE-DANGLING-CITATION
phase: done
date: 2026-09-17
tags: [architecture, documentation, schema]
---

# TCK-20260917-CLAIMS-AS-TESTS-INITIATIVE-DANGLING-CITATION

## Title
Land `docs/plans/mechanism_claims_as_tests_initiative.md` — cited by two open tickets, existed only
in peer's own uncommitted worktree

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Peer's own review, after the `registries/mechanisms.yaml` relocation: `docs/plans/
mechanism_claims_as_tests_initiative.md` existed only in peer's own uncommitted worktree
(`m2-idea43-temporal-note`), never landed on this branch or `main`. Meanwhile
`TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION` and
`TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION` both cite it by path, and §6 of the
document carries the reasoning for both tickets' own non-goals (the prose-consolidation rejection
and the `CLAUDE.md`-workflow-rule rejection, with `TCK-20260904` as the evidence). If this session
had ended without landing it, both tickets would have pointed at a document that doesn't exist for
anyone but peer — the purest form of the problem this whole arc has been about: an initiative
scoped, tickets filed against it, the initiative itself never landed.

Peer also separately found and removed their own stale duplicate of
`docs/plans/mechanism_registry_initiative.md` (this branch's own, corrected-in-T4 copy is
authoritative; peer's uncommitted copy was stale and has been deleted from peer's own worktree —
no action needed here).

## Scope
1. Copy `docs/plans/mechanism_claims_as_tests_initiative.md` from peer's worktree onto this branch,
   verbatim (peer confirmed it needs no path edits — its only registry reference is a bare
   `mechanisms.yaml`, which survives the relocation).
2. Validate frontmatter, confirm all tags/layer already registered.
3. Regenerate `docs/REGISTRY.yaml` / knowledge index.

## Out of Scope
- Adding the §4.3-vs-completeness-pass contradiction note peer flagged (the registration gate is
  written as forward-looking only; the completeness pass proved that insufficient on its own,
  since the gate alone would have left the 11 mechanisms it found invisible indefinitely) — peer
  explicitly scoped this as "a note for whoever next touches the initiative," not part of this
  ticket's own landing. Recorded here so it isn't lost.
- Any further edits to the initiative document's own content — landed exactly as peer's worktree
  copy read.

## Acceptance Criteria
1. `docs/plans/mechanism_claims_as_tests_initiative.md` exists on this branch, identical to peer's
   worktree copy.
2. Both citing tickets' own `Related Docs` links now resolve to a real file.
3. Frontmatter validates; no new tag/layer registration needed.

## Related Tickets
- `TCK-20260916-MECHANISM-STATUS-LANGUAGE-DETECTION`,
  `TCK-20260916-MECHANISM-CHANGED-CODE-ENTRY-DRIFT-DETECTION` — both cite this document; both had a
  dangling citation until this ticket landed it.
- `TCK-20260917-MECHANISM-REGISTRY-RELOCATION` — the immediately preceding ticket whose own review
  surfaced this gap.

## Related Docs
- `docs/plans/mechanism_claims_as_tests_initiative.md` — landed by this ticket.
- `docs/plans/mechanism_registry_initiative.md` — peer independently confirmed this branch's own
  copy (corrected in T4) is authoritative over their own stale worktree duplicate, which they
  deleted; no action needed on this branch.

## Related Stored Artifacts
None — hotfix tier, self-evident intent (landing an already-written, unchanged document) captured
in this ticket.

## Related Code Areas
- `docs/plans/mechanism_claims_as_tests_initiative.md`

## Assumptions / Open Questions
The §4.3-vs-completeness-pass contradiction peer flagged remains genuinely open in the document
itself (recorded here, not resolved) — whoever next edits the initiative should reconcile "§4.3's
registration gate is forward-looking only" with the completeness pass's own finding that 11
mechanisms would have stayed invisible under a forward-looking-only gate.

## Implementation Notes
Landed via direct file read from peer's own worktree path
(`/home/u24desktop/Working/rpg-based-simulation/.claude/worktrees/m2-idea43-temporal-note/docs/
plans/mechanism_claims_as_tests_initiative.md`, a different local worktree on the same machine) —
copied verbatim, no path edits needed since the document's only registry reference is the bare
string `mechanisms.yaml`, not a full path.

## Test Summary
No code changed; `tools/validate_frontmatter.py` passes on the new file. Not part of the scoped
pytest suite (a docs-only change).

## Files Changed
- `docs/plans/mechanism_claims_as_tests_initiative.md` — new
- `docs/REGISTRY.yaml` — regenerated at Finalize

## Completion Summary
Closed. The document now exists on this branch, identical to peer's own worktree copy, closing the
dangling-citation gap on both open detector tickets. The §4.3/completeness-pass contradiction peer
flagged is recorded as an open item for whoever next touches the initiative, not resolved by this
ticket.
