# SimQ Corpus Tier Expansion — Implementation Sequence

Scoped 2026-07-04 from `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md`
(pre-ticket epic-scoping pass, no code changed) plus three explicit user decisions on AGENCY,
Branch B (self-model), and content-authoring approach (hybrid by tier). Parent epic:
`TCK-20260704-SIMQ-CORPUS-TIERS-EPIC`.

| Order | Ticket | Why this order |
|---|---|---|
| 1 | TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC | Doc-only, defines the Unit/End-to-End/Stress/Regression vocabulary every other ticket in this batch references by name. Must land conceptually first even though nothing downstream has a hard code dependency on it. |
| 2 | TCK-20260704-SIMQ-CORPUS-SCALE-METRIC | Small, independent instrumentation change (adds "distinct populated factions" as a tracked metric). Landing early means tickets 4-8 (which author new worlds at deliberately varied faction density) get the metric for free when they compile, instead of needing a follow-up pass to backfill it. |
3 | TCK-20260704-SIMQ-CORPUS-AGENCY-FLAG-GENERALIZE | Mechanism-only (generalizes `ENABLE_ADVENTURE_ROUTING` activation into the per-world `feature_flags:` profile YAML block already used for `ENABLE_BELIEF_ASSIMILATION`). Ticket 6 (the new AGENCY unit-tier world) depends on this mechanism existing — must land before ticket 6. |
| 4 | TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO | Independent of 2-3; lowest-risk content-only authoring (pure additive `faction_tension_overrides` / `information_source_profiles`, no code risk per investigation.md §3). Establishes the unit-tier authoring pattern the next two unit-tier tickets (5, 6) follow. |
| 5 | TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT | Independent of 3/6 (does not touch AGENCY). Higher-scrutiny than ticket 4 (first live-load evidence for Branch B) — sequenced after 4 establishes the unit-tier world-building pattern, so this ticket's effort is spent on the scrutiny, not re-deriving the authoring mechanics. |
| 6 | TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY | Depends on ticket 3 (needs the generalized `feature_flags:` mechanism to turn `ENABLE_ADVENTURE_ROUTING` on without a new hardcoded harness special-case). Must land after 3. |
| 7 | TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION | Independent of 4-6 (different tier, existing worlds not new ones) but benefits from ticket 1's taxonomy doc existing so "why end-to-end tier gets bespoke content, not templated" has a citable rationale. Larger and riskier than 4-6 (touches 8 existing worlds' calibration anchors) — sequenced after the unit-tier worlds so any interaction lessons from 4-6 (e.g. drift-check discipline) are fresh. |
| 8 | TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS | Independent of all above; benefits from ticket 2's scale metric existing so the new stress-tier worlds can be scale-classified consistently with the rest of the corpus from the moment they're compiled. |
| 9 | TCK-20260704-SIMQ-CORPUS-FACTION-RELATIONSHIPS | Global content (not per-world) — independent of every other ticket in this batch. Sequenced late because it benefits every world simultaneously including the ones ticket 4-8 just added; doing it after they exist means the relationship-density fix is verified against the full expanded corpus, not just the pre-expansion 10 worlds. |
| 10 | TCK-20260704-SIMQ-CORPUS-SCENARIO-FLAG-GUARDRAIL | Must land LAST. It is a guardrail test asserting expected feature-flag state per scenario/world profile — its test matrix needs to cover every world and flag this batch adds (tickets 3-9), so writing it before they exist would under-specify it or require rewriting it repeatedly. |

## Dependency Notes
- Ticket 6 hard-depends on ticket 3 (mechanism must exist before the AGENCY unit-tier world can use it).
- Ticket 10 should be treated as depending on all of 1-9 landing first, even though no other ticket
  hard-depends on it — it is the corpus-wide guardrail, not a component of the corpus itself.
- Tickets 1, 2, 4, 5, 8, 9 have no hard dependencies on each other and could in principle run in
  parallel; the ordering above is a recommended default, not an enforced blocker, except where
  noted (3→6, 1-9→10).
- Per user decision, no ticket in this batch reverses `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` — the
  9 existing non-routing worlds' AGENCY=C grade stays untouched by every ticket in this sequence.


---

## Citation Correction (2026-07-08, TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING)

This doc's citations above to `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md`
and/or its later rename, `staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md`, point
to a pre-ticket epic-scoping investigation that was never migrated to `stored_artifacts/` and is now
unrecoverable: `staging_artifacts/` is gitignored by repo policy, and full git history confirms no commit
ever added a file at either path. This is a citation/traceability gap only -- every specific fact drawn
from that doc has been independently cross-validated against ground truth
(`world.yaml`/`world_compile_report.json`,
`test_corpus_diversity.py::EXPECTED_DISTINCT_POPULATED_FACTIONS`) by
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY` and/or `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`. See
`tickets/done/TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING.md` for the full root-cause writeup.
