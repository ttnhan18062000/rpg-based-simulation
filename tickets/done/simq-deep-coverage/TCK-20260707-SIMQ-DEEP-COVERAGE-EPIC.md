---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC
phase: done
date: 2026-07-07T16:31:09Z
tags: [simulation-quality, corpus, calibration, world]
---

# TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC

## Title
SimQ Deep Coverage: long-run drift detection and pillar-completeness verification

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
Follow-up epic to the just-completed `TCK-20260704-SIMQ-CORPUS-TIERS-EPIC` (10 tickets, corpus grew
10→17 worlds, tiered Unit/End-to-End/Stress/Regression). That epic's orchestrator gave an honest
assessment of remaining weaknesses — long-run under-coverage and piling-up meta-hygiene debt — and
the user asked for a new epic covering: (1) long-run coverage capped at ~2000 ticks (explicitly NOT
5000+), (2) coverage gaps, (3) full pillar coverage verification, (4) consideration of new pillars if
warranted, (5) organized in a folder for the next epic.

Pre-ticket scoping investigation (`staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md`)
found the epic's core justification: only 3 of 17 worlds have ANY anchor >=1000 ticks
(`dungeon_crawl`, `sandbox_world`, `urban_political`), and across all 11 existing long-run anchors,
AGENCY/COMBAT/PROGRESSION/WORLD grades are **literally invariant** (never vary) — while the
short-run corpus shows those same pillars reaching A/S grades in *other*, specialized worlds
(`unit_selfmodel_pilot`, `unit_faction_tension`, `hero_guild_routing`, `simq_routing_test`) that have
never been run past 500t. This is exactly the drift-blind-spot this epic exists to close
(investigation.md §1.3-1.4).

Pillar-completeness research (investigation.md §2) concluded **no new top-level pillar is
justified** — the four candidate dimensions (determinism, performance, checkpoint integrity, catalog
health) are each already owned by dedicated systems outside SimQ. One genuine, narrow gap was found:
`building_sabotage` (pipeline phase 15, `src/engine/sabotage.py`) is live, exercised by real content
(`urban_political`), but emits no observability event and is invisible to all 10 pillars —
recommended as a new scoring rule under the existing WORLD pillar, not an 11th pillar, blocked on an
event-emission prerequisite.

## Scope
This epic tracks 10 child tickets across two threads and does not implement anything directly (per
CLAUDE.md's epic tier: scope-only, tracks children).

**Thread 1 — Long-run coverage (capped at ≤2000t, per explicit user cap):**
Add 1000t anchors for the specialized worlds already known to drive AGENCY, COGNITION, FACTION, and
NARRATIVE into their peak grades at short run (`unit_selfmodel_pilot`, `unit_faction_tension`,
`hero_guild_routing`, `simq_routing_test`); extend `unit_faction_tension` and `urban_political` to
2000t; establish `generated_frontier_3_42`'s first-ever anchors (it currently has zero, at any tick
count). Four pre-existing resource/coverage-gap tickets, relocated into this epic's folder, must land
first since they touch worlds the long-run anchors will be measured against — anchoring long-run
grades against known-broken content would produce misleading "regressions."

**Thread 2 — Pillar completeness:**
Document the pillar-completeness research conclusion (no new top-level pillar; 4 candidate dimensions
each already owned elsewhere). Close the one genuine gap found (`building_sabotage`) as a small,
low-priority WORLD-pillar scoring rule addition, explicitly not a new pillar.

**Child tickets (10 total), in `tickets/todos/simq-deep-coverage/` (see that folder's
`SEQUENCE.md` for full ordering rationale):**
1. `TCK-20260707-HERO-GUILD-ROUTING-RESOURCE-TAG-GAP` — fix `hero_guild_routing` resource-tag gap
   before it is anchored at long run
2. `TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP` — resolve `urban_political`'s dormant
   hometown resource gap before its 2000t extension
3. `TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT` — corpus-wide resource/region coverage
   audit, same subsystem as long-run anchoring
4. `TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP` — extend population-stability test
   coverage to the worlds this epic anchors at long run
5. `TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER` — independent doc-hygiene chore, runs in parallel
6. `TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING` — independent doc-traceability chore, runs in
   parallel
7. `TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS` — new: add the 1000t/2000t hot-pillar anchors
   (depends on 1-4)
8. `TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS` — new: establish `generated_frontier_3_42`'s
   first-ever anchors including a long-run tier (independent of 1-4)
9. `TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC` — new: document the pillar-completeness conclusion
   (independent)
10. `TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL` — new: building_sabotage event emission + WORLD-pillar
    scoring rule (depends on 9 for citation; lowest priority, lands last)

## Out of Scope
- Extending any long-run anchor past 2000 ticks — explicitly capped per user direction; a 5000t+
  tier is a distinct, future, separately-scoped decision, not part of this epic.
- Adding an 11th top-level pillar — investigation.md §2.7 concludes this is not justified; any child
  ticket proposing one is out of scope for this epic.
- Re-litigating any of investigation.md §5's 5 open questions — all were decided by the orchestrator
  before this epic was scoped (anchor matrix worlds/tiers, sequencing order, `building_sabotage`
  inclusion, `generated_frontier_3_42` treatment, missing calibration profiles are a non-blocking
  in-ticket assumption). See investigation.md §5 for the full list; do not re-open these.
- Re-fixing anything already closed by `TCK-20260704-SIMQ-CORPUS-TIERS-EPIC`'s 10 completed child
  tickets.

## Acceptance Criteria
- [x] All 10 child tickets listed above exist, are correctly formatted, and pass
      `python3 tools/validate_frontmatter.py <file> --content-type ticket`
- [x] The 4 relocated resource/coverage-gap tickets land (move to `tickets/done/`) before
      `TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS` touches `hero_guild_routing` or
      `urban_political`
- [x] No new long-run anchor exceeds 2000 ticks
- [x] No 11th top-level pillar is added
- [x] This epic ticket is moved to `tickets/done/` only once all 10 child tickets are done (or
      explicitly descoped with rationale recorded here)

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TIERS-EPIC — predecessor epic this one follows up on
- TCK-20260707-HERO-GUILD-ROUTING-RESOURCE-TAG-GAP (child)
- TCK-20260706-SIMQ-URBAN-POLITICAL-HOMETOWN-RESOURCE-GAP (child)
- TCK-20260706-SIMQ-CORPUS-RESOURCE-REGION-COVERAGE-AUDIT (child)
- TCK-20260707-CORPUS-POPULATION-STABILITY-COVERAGE-GAP (child)
- TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER (child)
- TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING (child)
- TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS (child, new)
- TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS (child, new)
- TCK-20260707-SIMQ-PILLAR-COMPLETENESS-DOC (child, new)
- TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL (child, new)

## Related Docs
- `staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` — full pre-ticket
  scoping investigation: long-run coverage audit (§1), pillar-completeness research (§2),
  existing-ticket triage (§3), long-run test infrastructure mechanism (§4), and the 5 open
  questions the orchestrator decided (§5). Every child ticket in this epic must cite this file
  directly rather than re-deriving its evidence.
- `docs/simulation_quality/quality_scoring_contract.md` — §7 Extensibility Protocol (governs both
  the pillar-completeness conclusion and the `building_sabotage` WORLD-pillar rule addition)
- `docs/simulation_quality/eval_matrix_results.md` — corpus-wide grade history, cited throughout
  investigation.md
- `tickets/done/simq-corpus-tiers/SEQUENCE.md` — predecessor epic's sequencing document, format
  reference for this epic's own `tickets/todos/simq-deep-coverage/SEQUENCE.md`

## Related Stored Artifacts
- `staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/` — **could not be preserved at epic
  close: the file no longer exists.** See Citation Note below.

## Related Code Areas
- `tests/simulation_quality/fixtures/grade_anchors.json` — anchor data
- `tests/simulation_quality/test_grade_regression.py` — `SLOW_ANCHOR_KEYS`
- `src/simulation_quality/scorers/` — all 10 pillar scorers
- `src/engine/sabotage.py` — `BuildingSabotageSystem.resolve()` (child ticket 10 only)

## Assumptions / Open Questions
- Exact seed count per world/tier (1 vs 2 vs 3) is intentionally left to
  `TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS`'s own Plan phase to decide with cost/coverage
  reasoning — this epic sets only the floor (at least 1 seed per world/tier) and the ≤2000t cap.
- Missing calibration profiles for `unit_faction_tension`/`crowded_frontier`/`resource_dense_basin`/
  `wilderness_survival` (investigation.md §4 point 4) are a non-blocking assumption for the relevant
  child ticket to confirm live, not a blocking epic-level decision.

## Implementation Notes
Per this epic's own Tier Routing (scope-only, no direct implementation), all work happened in the
10 child tickets, each following its own tier-appropriate pipeline independently. This epic
ticket's role was tracking and sequencing only. The child tickets landed across 2026-07-07 through
2026-07-08 (see `working_log.csv` for the full timeline); all 10 are confirmed `DONE` and the
child-tracking folder was moved to `tickets/done/simq-deep-coverage/` per the standard
folder-completion rule, but this epic ticket itself was left behind in `tickets/todos/` after the
last child (`TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL`) closed. Closed out here as a follow-up
housekeeping pass (2026-07-09), discovered while auditing `tickets/todos/` for simulation-quality
work.

## Citation Note (2026-07-09)
`staging_artifacts/TCK-20260707-SIMQ-DEEP-COVERAGE-EPIC/investigation.md` no longer exists — not in
the working tree, and (per `git log --all --diff-filter=A`) never committed, since
`staging_artifacts/` is gitignored by repo policy. This is the exact citation-rot pattern
`TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING` fixed for the predecessor epic, recurring here
despite this epic's own Related Stored Artifacts section explicitly calling out the intent to avoid
it. Impact is limited: every specific finding this epic's Request Summary cites (the 3-of-17-worlds
long-run coverage gap, the AGENCY/COMBAT/PROGRESSION/WORLD invariance finding, the
`building_sabotage` gap) is preserved directly in this ticket's own Request Summary text above, and
every child ticket's own investigation/implementation independently re-verified its slice against
live data rather than trusting the epic doc blindly (e.g. `TCK-20260707-SIMQ-LONGRUN-HOTPILLAR-ANCHORS`
and `TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS` both re-ran calibration live). No child
ticket's acceptance criteria depended on re-reading the missing file. Flagged here rather than
silently closing, per this ticket's own "no known material gap left unstated" obligation; a future
ticket may want to harden `staging_artifacts/` migration enforcement so this stops recurring, but
that is not scoped here.

## Test Summary
Each child ticket ran and independently verified its own test suite at closure; no epic-level test
run beyond the children's own (see individual child tickets' Test Summary sections). Most recent
corpus-wide confirmation across the epic's full output was `TCK-20260707-SIMQ-BUILDING-SABOTAGE-SIGNAL`'s
close.

## Files Changed
See each child ticket's own Files Changed section. At a corpus level: 6 new long-run calibration
anchors (1000t/2000t, capped per this epic's explicit ≤2000t rule), `generated_frontier_3_42`'s
first-ever grade anchors (200t + 1000t), 5 tag-gap resource/region catalog fixes, a new
`building_sabotaged` WORLD-pillar observability signal, and `quality_scoring_contract.md` §7.5
documenting the pillar-completeness conclusion (no 11th pillar justified). One genuine new defect
was discovered as a byproduct and correctly spun out rather than fixed in-epic:
`TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE` (found during the
`generated_frontier_3_42` 1000t anchor run).

## Completion Summary
All 10 child tickets landed in `tickets/done/`; the child-tracking folder moved to
`tickets/done/simq-deep-coverage/` per the standard folder-completion rule. This epic delivered its
two threads as scoped: (1) long-run coverage — new 1000t/2000t anchors for the worlds already known
to drive AGENCY/COGNITION/FACTION/NARRATIVE to peak grades at short run, plus `generated_frontier_3_42`'s
first-ever anchors at any tick count, all within the explicit ≤2000t cap; (2) pillar completeness —
documented conclusion that no 11th top-level pillar is justified, and closed the one genuine gap
found (`building_sabotage`) as a WORLD-pillar scoring-rule addition rather than a new pillar. Two
genuine population-collapse defects were surfaced as a byproduct of the long-run anchoring work
(not epic-in-scope to fix) and correctly spun into their own standalone tickets rather than papered
over: `TCK-20260708-DUNGEON-URBAN-POPULATION-COLLAPSE` and
`TCK-20260708-GENERATED-FRONTIER-LATE-TICK-POPULATION-COLLAPSE`. This epic ticket itself was left
open in `tickets/todos/` after its last child closed; closed out here as housekeeping (see
Implementation Notes and Citation Note above for the two process gaps found during closure).
