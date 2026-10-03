---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-VALUE-INVESTIGATION
phase: done
date: 2026-09-18
tags: [architecture, documentation, investigation]
---

# TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-VALUE-INVESTIGATION

## Title
Do the broad membership pass as a throwaway exercise and report whether reading a system tells you
anything the per-mechanism view does not — build nothing

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Before building a systems registry and the membership pass 93 mechanisms, find out whether the grouping is worth
maintaining.

**Feasibility is not the question this time.** The previous investigation tested whether *derived*
membership produced recognisable sets — it didn't. Declared-by-intent sets will be sensible by
construction, so asking "do these sets make sense" would be asking whether we can type a list.

**The real question is value against cost:** does reading a system tell you something the
per-mechanism view does not, by enough to justify hand-maintaining membership on 93 mechanisms with no
mechanical backing?

The motivating case, run by hand during scoping, is the benchmark to beat. Entity progression spans
**15 mechanisms**, and grouping them surfaced immediately: 10 of 15 unverified, only 4 bound to code,
**two gated off by default** (`progression_conversion`, `genetics_aptitude`), and the registry's only
`contradicted` verdict in the set (`readiness_speed_scaling`). The core stats chain
`attributes_biology → derived_stats` is entirely unverified.

That was genuinely informative — and it was produced by typing 15 ids into a shell command. The
investigation must establish whether a maintained membership layer beats that, or merely formalises it.

## Scope
**Build nothing.** No registry, no schema field, no validator, no generator. Assign in a throwaway
scratch file or a local script.

### 1. Do the broad pass, large to small
Assign all 93 mechanisms to a small set of broad systems that **cover everything**. Per the user's
direction: coverage before granularity. Starting small-and-precise risks whole areas having no
system; splitting a too-broad system later is safe and loses nothing.

Record the vocabulary you arrive at and how many mechanisms land in each.

### 2. Report the shape honestly
- How many systems did full coverage require?
- **How many mechanisms genuinely belong to more than one?** If almost none do, the many-to-many
  design is unnecessary complexity and child 2 should be simplified.
- How many resist assignment entirely — infrastructure-ish mechanisms with no gameplay system? Those
  become `unassigned`, and the count matters because it sets expectations for the review view.

### 3. The value test — this is the actual deliverable
For **three** systems from your pass, write what the grouped view tells you, then answer:

**Could that have been read off the per-mechanism table without the grouping?**

Progression is the benchmark: it yielded four non-obvious facts (unverified ratio, binding ratio, two
gated-off, one contradicted). Do your three reach that bar? If two of three produce nothing a reader
wouldn't already see, say so.

### 4. Cost estimate
State what maintaining this actually costs: membership on 93 mechanisms now, plus one decision per new
mechanism, plus re-assigning when a mechanism splits (the identity rule produced 4 splits from 9 cases,
so splits are not rare).

## Out of Scope
- **Any schema, field, registry or validator.** Investigation only.
- **Committing the membership** to `registries/mechanisms.yaml`. The pass is an exercise; child 2 does
  the real one.
- **Rollup views.** Child 3, deferred.
- **Deciding the final vocabulary.** Child 2 seeds from your findings, but this is not a binding
  vocabulary decision.

## Acceptance Criteria
1. All 93 mechanisms assigned or explicitly listed as unassignable, with the vocabulary recorded.
2. The three shape questions in §2 answered with counts, not impressions — especially the
   multi-system count, since it decides whether child 2 needs many-to-many at all.
3. Three systems put through the §3 value test, each with an explicit **yes/no** on whether the
   grouping revealed something the per-mechanism table did not.
4. A cost estimate stated, not implied.
5. **A recommendation: proceed, proceed-with-changes, or do not build.** "Do not build" is a real
   outcome and saves children 2 and 3 — the previous investigation's "do not build" saved three
   tickets and a schema, and was the most valuable result of that epic.

## Related Tickets
- `TCK-20260918-EPIC-MECHANISM-SYSTEM-MEMBERSHIP` — parent
- `TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-FOUNDATION` — child 2, seeded by this
- `TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION` — the derived-tier investigation;
  its four failed candidate sets are required reading, since they show what a bad grouping looks like
  and why derivation produced them

## Related Docs
- `docs/plans/mechanism_tier_model_initiative.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-VALUE-INVESTIGATION/` — this
  ticket's own findings
- `stored_artifacts/TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION/` — required
  reading, the four failed derived candidate sets

## Related Code Areas
- `registries/mechanisms.yaml` — read-only for this ticket

## Assumptions / Open Questions
1. **A "do not build" here means something different from last time.** Then, the design was broken.
   Here it would mean the grouping is real but not worth its maintenance cost — in which case the
   fallback is the ad-hoc query that produced the progression example, accepted openly as
   unreproducible rather than pretended away.
2. Whether a mechanism can be judged as belonging to a system without reading its code is unknown.
   If assignment requires opening the implementation each time, the cost estimate in §4 rises sharply
   and that changes the recommendation.
3. The 93 count is current as of 2026-09-18 and grew from 89 via the identity-rule splits. Expect it
   to keep moving.

## Implementation Notes
The pattern this follows has now paid off twice — measure the cheapest discriminating thing before
committing to a design. The difference is what is being measured: last time feasibility, this time
value against cost.

**Full findings in `stored_artifacts/TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-VALUE-INVESTIGATION/investigation.md`.**
Summary:
- All 93 mechanisms assigned to 7 broad systems (`combat`, `progression`, `cognition`, `social`,
  `faction`, `economy`, `world`), zero unassigned. The independently-derived `progression`
  assignment matched the ticket's own worked-example count (15) exactly, a real cross-check that
  this session's judgment tracked the ticket author's.
- **8 of 93 (8.6%) are genuinely multi-system** — real, not padding (`movement`, `personality`,
  `adventure_routing`, `entity_trade`, `guilds`, `regional_sovereignty`, `fame`,
  `quest_generation_sourcing`). Low enough that a single-valued field with a short documented
  exception list is a real alternative to full many-to-many — not decided here, flagged for
  child 2.
- **Value test, 2 of 3 systems cleared the bar** (`combat`, `economy`) once checked against the
  whole-registry baseline (74% unverified, 30% `implemented_by` overall) rather than reported in
  isolation. `faction`'s own raw numbers (77% unverified, 23% bound) looked informative until
  checked against baseline and found statistically indistinguishable from the corpus average —
  exactly the "two of three" honesty check this ticket's own Scope anticipated, and evidence the
  design needs a baseline-comparison step to be reliably informative, not evidence it's unsound.
- `economy` reached the same caliber of finding as the ticket's own `progression` benchmark
  (100% unverified — 26 points above baseline — with a real, coherent 4-edge internal
  `depends_on` structure, unlike the prior derived-economy candidate's n=2 failure).
- Cost: real and recurring, not one-time — the identity-rules ticket's own ~44% split rate (4 of
  9 cases) means membership needs periodic re-review, not just initial assignment.

## Test Summary
Not applicable in the usual sense — investigation only, no code/schema/field/generator built.
Internal-consistency checks on the throwaway assignment script: all 93 real registry ids
assigned (verified via direct set-difference, `missing` = empty), no typo'd/extra ids, baseline
rates computed the same way as per-system rates before comparing. See `test_plan.md`.

## Files Changed
- `stored_artifacts/TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-VALUE-INVESTIGATION/{plan,investigation,test_plan}.md` — new.
- No `src/`, `registries/`, or schema files touched — investigation only, per this ticket's own
  explicit scope (`registries/mechanisms.yaml` was read-only).

## Completion Summary
**Recommendation: proceed, with one required change to the foundation's own design (not "do not
build," and not an unconditional "proceed" either).** The value test passed 2 of 3 test systems
(`combat`, `economy`), including one (`economy`) that matches the caliber of the ticket's own
progression benchmark — real signal, distinct from the prior derived-membership investigation
where every candidate failed for a structural design reason. The one failure here (`faction`)
failed for a measurement reason (a raw percentage that looks informative until compared against
the whole-registry baseline), which is fixable in how the foundation presents membership: any
rollup/review view must report per-system rates against baseline, not in isolation, or it will
mislead readers the way `faction`'s own raw 77% would have. Multi-membership is real but small
(8.6%) — a genuine simplification candidate (single-valued field + short exception list) for
child 2 to weigh against full many-to-many, not settled here. Cost is real and recurring given
the identity-rules ticket's own ~44% mechanism-split rate, not a one-time setup cost.
