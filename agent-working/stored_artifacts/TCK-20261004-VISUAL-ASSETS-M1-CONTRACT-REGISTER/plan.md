---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261004-VISUAL-ASSETS-M1-CONTRACT-REGISTER
artifact_type: plan
tags: [architecture, documentation]
---

# Plan — TCK-20261004-VISUAL-ASSETS-M1-CONTRACT-REGISTER

1. Split each `AM1-W01`..`W13` "Objective acceptance" cell of the plan package into its clauses (68 rows).
2. For each clause find the as-built evidence first (ADR row, doc heading, code symbol, test), then give a verdict. Where the code and a doc disagree the code wins and the disagreement is listed, not fixed.
3. `W06` and `W11` rows are `GAP` ("written by" the two follow-on tickets); `U-02` is a `MET` row (D10).
4. Generate the page from one table in a scratch script so the summary counts cannot drift from the rows; resolve every evidence entry with a second scratch script.
5. One link from `store_contract.md`; nothing else outside the new page, the ticket and these artifacts changes.
