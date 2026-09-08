# Implementation Sequence — dormant-mechanism-closure

No child ticket in this batch has a hard cross-ticket dependency on another, **except**
`TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING`, which hard-depends on
`TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE` landing first. Order below is by priority (recency
of the blocked idea + breadth of impact once fixed), not a hard build-order constraint otherwise.
`implement-epic` reads this file to override alphabetical order; re-run after any gate failure —
already-done tickets are skipped automatically.

**2026-09-07 update:** `TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE` landed with idea 56 as its
real, complete scope (DONE, `tickets/done/`) — idea 57 turned out to need reviving 2 entirely dead
subsystems, a materially larger scope than "bridge one signal," so it was split out into
`TCK-20260907-PERCEPTION-MOTIVATION-PIPELINE-REVIVAL`. That investigation ticket then found the real
gap is even bigger — a 4-component dead chain plus a missing `AdventureRouteOption.tags` data model
— and was itself closed DONE (its own deliverable being the investigation) with a further split into
`TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE` (the real shared prerequisite) and
`TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING` (idea 57's own narrow piece, depends on the
infrastructure ticket). `TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH` also landed DONE the same day
(appended onto PR #143, since it directly extended docs authored there).

**2026-09-07 update 2:** `TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE` and
`TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING` both landed DONE. While implementing ticket 6
(`ROUTE-NEW-QUERY-CORPUS-SCENARIO`), found a real, unrelated regression affecting both of the
above: their own bridge fields (`region_culture_states`/`entity_legend_facts`) silently reset to
empty after tick 1 of any real campaign episode (`ApplyPath.apply_generation()` never carried
them forward) — fixed as its own hotfix, `TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-
CARRYFORWARD` (DONE, also fixed idea 56's `region_loyalty_pressure` sibling field). Ticket 6 itself
then found its own real blocker is structural (two independently-correct design decisions that
never overlap for the same tick), not a missing-corpus-content gap as originally scoped — closed
DONE as an investigation (+ a real, ready-to-use new corpus world), split into
`TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION`.

**2026-09-07 update 3:** `TCK-20260907-ITEM-INSTANCE-HISTORY-DECISION` (idea 30) landed DONE —
real user decision: defer, leave `ENABLE_ITEM_INSTANCE_HISTORY` OFF (confirmed zero producer AND
zero consumer, unlike every other ticket here). `TCK-20260907-DORMANT-IDEA-DISPOSITION-DECISIONS`
also landed DONE, but found the epic's own scoping premise for idea 62 was stale — idea 62
(Chronicle Fidelity Drift) and idea 63 (Belief Institution) had already shipped 2026-09-05, not
blocked as originally claimed. Real remaining gap ("no live consumer," same shape as tickets 4-5's
own idea 56/57 gap) split into a new ticket, `TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING` — not
in the original 6-ticket plan, grows this batch to 10 real tickets total.

## Order

1. ~~TCK-20260907-DORMANT-SIGNAL-CAMPAIGN-BRIDGE~~ — **DONE, 2026-09-07** (idea 56 only; idea 57 split
   out below)
2. ~~TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH~~ — **DONE, 2026-09-07**
3. ~~TCK-20260907-PERCEPTION-MOTIVATION-PIPELINE-REVIVAL~~ — **DONE, 2026-09-07, as an investigation**
   (found the real 4-component gap; split further into tickets 4-5 below)
4. ~~TCK-20260907-ROUTE-BIAS-SCORING-INFRASTRUCTURE~~ — **DONE, 2026-09-07**
5. ~~TCK-20260907-LEGEND-FACT-ROUTE-BIAS-WIRING~~ — **DONE, 2026-09-07**
6. ~~TCK-20260907-ROUTE-NEW-QUERY-CORPUS-SCENARIO~~ — **DONE, 2026-09-07, as an investigation** (real
   blocker is structural, not a content gap; split into ticket 6b below)
6b. ~~TCK-20260907-INFORMATION-SOURCE-PROFILES-PERSISTENCE-DECISION~~ — **DONE, 2026-09-07** (Option
    1 implemented; surfaced a second, separate real bug fixed as ticket 6d below;
    `route_new_query` now genuinely fires end-to-end)
6c. ~~TCK-20260907-APPLY-GENERATION-EPISODE-BRIDGE-CARRYFORWARD~~ — **DONE, 2026-09-07** (hotfix found
    while implementing ticket 6, fixes a real regression in tickets 4-5's own bridge fields)
6d. ~~TCK-20260907-INFORMATION-INTENT-EXECUTION-RESULT-TYPE-MISMATCH~~ — **DONE, 2026-09-07** (hotfix,
    NEW, not in the original plan — fixes the second bug ticket 6b surfaced)
7. ~~TCK-20260907-ITEM-INSTANCE-HISTORY-DECISION~~ — **DONE, 2026-09-07** (real decision: defer idea
   30, `ENABLE_ITEM_INSTANCE_HISTORY` stays OFF — confirmed zero producer AND zero consumer)
8. ~~TCK-20260907-DORMANT-IDEA-DISPOSITION-DECISIONS~~ — **DONE, 2026-09-07** (ideas 50/64 scheduled
   for a future milestone, not retired; found the epic's own idea-62 premise was stale — both 62/63
   already shipped — split real remaining gap into ticket 8b below)
8b. ~~TCK-20260907-CHRONICLE-BELIEF-CONSUMER-WIRING~~ — **DONE, 2026-09-07** (NEW, not in the
    original 6-ticket plan: wired idea 62/63's `FidelityState`/`BeliefInstitution` into a live
    `personality_bias` consumer via `QUEST_OPPORTUNITY`, matching tickets 4-5's own pattern)
9. ~~TCK-20260907-CHURCH-CONTENT-AUTHORING~~ — **DONE, 2026-09-07** (original "pure content" premise
   was wrong — services are inert data labels; first placed with inertness disclosed, **reverted to
   deferred after independent review** — matches ticket 7's own idea-30 treatment)
9b. ~~TCK-20260907-DORMANT-CLOSURE-CI-REGRESSION-FIXUP~~ — **DONE, 2026-09-07** (hotfix, NEW: fixes
    3 real CI clusters an independent review of this PR found in tickets 6b/8b's own changes)
9c. TCK-20260907-CAMPAIGN-BRIDGE-FIELDS-STATE-HASH-COVERAGE (P2 — NEW, filed but deliberately left
    OPEN, not implemented: a real determinism-coverage question raised by the same review, spanning
    all 6 `CampaignState`-bridge fields this batch added)

**All 14 tickets in this batch (grown from an original scope of 6) are now DONE**, except
`TCK-20260907-SOCIALBOND-ROLE-WRITE-PATH`, whose code lives on the separate, still-unmerged PR #143
branch (`social-mechanics-bible-chapter`) rather than this one — see the epic ticket's own
`## Implementation Notes` decision #7 for the full cross-reference.

## Why This Order Matters

Ticket 1 was the highest-leverage fix — one architectural bridge unlocked idea 56 immediately.
Idea 57 needed two rounds of proper re-scoping (tickets 3, then 4-5) once its own real scope became
clear at each level — a materially larger, multi-subsystem infrastructure gap, not a small wiring
fix. Tickets 4-5 have a real, hard dependency (5 cannot start meaningfully until 4's own data
model/scoring-formula change exists). Ticket 6 similarly needed re-scoping once its real blocker
turned out to be structural (ticket 6b) rather than content-authoring, and directly surfaced an
unrelated regression in tickets 4-5's own shipped work (ticket 6c, already fixed). Ticket 7 is a
real, bounded fix with no shared blocker. Tickets 8-9 are lower priority: 8 produces decisions
rather than code, and 9 is isolated, low-risk content work that can land whenever convenient.

**2026-09-07 update 4 (post-review):** An independent review of PR #144 (requested specifically to
scrutinize decisions 3, 6(i), 9(ii), and 10 above) found 3 real CI regression clusters — fixed as
`TCK-20260907-DORMANT-CLOSURE-CI-REGRESSION-FIXUP` (hotfix, DONE) — plus a real determinism-
coverage question spanning all 6 `CampaignState`-bridge fields this batch added, filed as
`TCK-20260907-CAMPAIGN-BRIDGE-FIELDS-STATE-HASH-COVERAGE` (not implemented, needs its own
investigation). Ticket 9 (CHURCH) was reversed: after review, `CHURCH` is now deferred (not
placed), matching ticket 7's own idea-30 treatment for the same "no producer, no consumer" shape.
See the epic ticket's own `## Implementation Notes` decision #11 for the full record.

**2026-09-07 update 5 (closure):** PR #143 merged (`1500384f`) — ticket 2's
(`SOCIALBOND-ROLE-WRITE-PATH`) code is now genuinely on `main`. All 14 tickets in this batch are
DONE. Epic ticket `TCK-20260907-EPIC-RPG-DORMANT-MECHANISM-CLOSURE` closed and moved to
`tickets/done/`; this folder moved alongside it, per the standard folder-close convention.
