# Tag Taxonomy Follow-ups — Implementation Sequence

Two tickets filed 2026-07-05, both consuming categories from the tag taxonomy shipped in
`TCK-20260704-TAG-TAXONOMY` (`docs/guidelines/tag_taxonomy.md`) per its own explicitly-deferred
future-usage scenarios. Neither depends on the other — they touch different code paths
(`ticket-scoper`/`create-tickets.js` Structure phase vs. `create-tickets.js` Investigate phase /
`investigator.md`) and consume different taxonomy categories (Process/Skill-signal vs.
Subsystem/Topic).

| Order | Ticket | Why this order |
|---|---|---|
| 1 | TCK-20260705-TAG-SKILL-SUGGEST | No preference either way — listed first only because it was the user's first-stated priority when both were selected for ticketing |
| 2 | TCK-20260705-TAG-REGISTRY-QUERY | Independent of ticket 1; can be done first, last, or in parallel |

## Dependency Notes

- No hard dependency between these two tickets — pick whichever order suits available time/interest.
- Both tickets require a new or updated developer-facing doc (`docs/guides/ticket_tagging.md` for
  ticket 1; a possible small addition to an existing guide for ticket 2, per that ticket's own
  Related Docs note) — this is a shared expectation across both, not a technical dependency.
