# Monitoring Follow-ups — Implementation Sequence

Three tickets filed 2026-07-05 from findings explicitly disclosed-but-unactioned in the just-completed
`retro-findings` epic (`tickets/done/retro-findings/`). None share a hard code dependency with each
other, but one has a real cross-folder sequencing consideration.

| Order | Ticket | Why this order |
|---|---|---|
| 1 | TCK-20260705-RETRO-INDEX-ALL-ROW | Smallest, most mechanical fix (hotfix tier), reuses an already-built helper (`_resolve_status`) — do first as a quick win |
| 2 | TCK-20260705-WORKING-LOG-BACKFILL | Standard tier, larger volume (62 tickets to individually verify) but no design uncertainty — independent of the other two |
| 3 | TCK-20260705-SIX-SKILLS-INVESTIGATION | Standard tier; the *investigation* itself has no dependency, but per explicit user decision, any confirmed-gap **wiring** this investigation surfaces should wait for `tickets/todos/tag-taxonomy-followups/TCK-20260705-TAG-SKILL-SUGGEST.md` to land first — see that ticket's own Out of Scope |

## Dependency Notes

- Tickets 1 and 2 are fully independent of ticket 3 and of each other — any order works.
- Ticket 3 is an **investigation-only** ticket in this folder; it does not implement any skill wiring
  itself. If it confirms one or more of the 6 skills as genuine gaps, the actual wiring work is
  explicitly deferred to after `TCK-20260705-TAG-SKILL-SUGGEST` (in the separate
  `tickets/todos/tag-taxonomy-followups/` folder) lands — so a confirmed gap gets wired through the
  more general tag-based mechanism that ticket builds, rather than a third, redundant one-off
  `CLAUDE.md` table addition duplicating what `TAG-SKILL-SUGGEST` will already do. This is a
  cross-folder sequencing note, not a blocking dependency for running this ticket's own
  investigation — the investigation itself can proceed at any time.
