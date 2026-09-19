---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-VALUE-INVESTIGATION
artifact_type: plan
tags: [architecture, documentation, investigation]
---

# Plan — TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-VALUE-INVESTIGATION

Investigation only, per this ticket's own explicit scope. No schema, field, registry, or
generator built — a throwaway Python script against `registries/mechanisms.yaml`, discarded
after use except for its output captured in `investigation.md`.

## Steps

1. Read `TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION`'s four failed derived
   candidate sets first (required reading per this ticket's own Related Tickets) to see what a
   bad grouping looks like before doing a declared one: `combat` (partial fit, missing
   `tactical_decision`), `progression` (mostly `combat`'s own set plus `xp_leveling`), `economy`
   (n=2, missing most of the real domain), `social` (two roots giving 4 vs. 17 members with
   almost no overlap).
2. Dump all 93 mechanisms with `layer`/`state`/`verified.verdict` from the registry for reference.
3. Do the broad, coverage-first membership pass by hand: assign every mechanism to one or more of
   a small system vocabulary, judgment calls noted inline in the assignment script itself. Check
   the assignment against the ticket's own worked example (progression = 15 mechanisms) as a
   sanity check that this session's judgment matches the ticket author's.
4. Compute the shape numbers required by Scope §2: system count, multi-membership count,
   unassigned count.
5. Run the value test (Scope §3) on three systems **other than** progression (already given as
   the benchmark) — chose `combat`, `faction`, `economy` for domain diversity (entity-layer
   real-time, faction-layer politics, world-layer production).
6. For each of the three, compute per-system diagnostics (state/verdict breakdown, gated/orphan/
   gap counts, internal `depends_on` edges, `implemented_by` binding rate) and **compare each rate
   against the whole-registry baseline**, not just report it in isolation — an isolated "77%
   unverified" sounds informative until you learn the whole registry is 74% unverified anyway.
   This comparison step is not in the ticket's literal Scope text but is the only way to honestly
   answer "could this have been read off the per-mechanism table without the grouping" — a raw
   percentage is exactly the kind of thing that table already shows per-row; only a rate compared
   against a baseline is a synthesis the table doesn't hand you for free.
7. State the cost estimate and a real recommendation, not softened regardless of which way the
   evidence points.
