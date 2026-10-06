# gate-override-ledger — sequence

Epic: `TCK-20261006-EPIC-GATE-OVERRIDE-LEDGER` (owner chose it on 2026-10-06 as the item after the hand-closure
cost epic).

| # | Ticket | Tier | Depends on | Note |
|---|---|---|---|---|
| 1 | `TCK-20261006-GATE-VERDICT-RECORD-AND-HAND-SITES` (done) | standard | none | record and writer, plus the hand-reachable CLIs; most of the value |
| 2 | `TCK-20261006-GATE-VERDICT-OUTCOME-AND-ADJUDICATION` (done) | standard | 1 | outcomes, adjudication, native-backstop false_pass |
| 3 | `TCK-20261006-GATE-PRECISION-REPORT-AND-RETRO` (done) | standard | 2 | report, retro section, direction doc row |
| 4 | `TCK-20261006-GATE-VERDICT-PIPELINE-SITES` | standard | 1 | formal pipeline only (1 of 37 W41 runs); can run in parallel with 2–3 or land later |

Suggested batch: 1 through 3 together in one PR. Ticket 4 can go in the same PR or the next one.

The epic stays OPEN after the code lands. Its AC2 needs the first full ISO week after the merge.
