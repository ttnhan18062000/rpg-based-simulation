# ticket-path-record — sequence

Epic: `TCK-20261006-EPIC-TICKET-PATH-RECORD` (the owner chose it on 2026-10-06 as the item after the gate override
ledger).

| # | Ticket | Tier | Depends on | Note |
|---|---|---|---|---|
| 1 | `TCK-20261006-PATH-REASON-AND-PHASE-COVERAGE-RECORD` | standard | none | `path_reason`, `phases_omitted` and `skip_reason`; CLAUDE.md closure example |
| 2 | `TCK-20261006-PATH-AND-PHASE-REPORT-AND-RETRO` | standard | 1 | reading, Paths retro section, direction doc rows |

Riding in the same PR, already filed in todos:
- `TCK-20261006-GATE-VERDICT-PIPELINE-SITES` (P3). It touches the same `implement-ticket.js` run and skip sites as
  #1; do them together.
- `TCK-20261006-KNOWLEDGE-INDEX-STALE-WARNING` (hotfix, P3).

The epic stays OPEN after the code lands. Its AC2 needs the first full ISO week after the merge.
