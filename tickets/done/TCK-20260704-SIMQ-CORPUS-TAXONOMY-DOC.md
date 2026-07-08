---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC
phase: done
date: 2026-07-04T12:17:33Z
tags: [simulation-quality, world, corpus, documentation, taxonomy]
---

# TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC

## Title
Document the Unit/End-to-End/Stress/Regression SimQ corpus tier taxonomy

## Status
DONE

## Tier
hotfix

## Type
documentation

## Priority
P1

## Request Summary
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` and the parent epic
(`TCK-20260704-SIMQ-CORPUS-TIERS-EPIC`) introduce a test-pyramid-style tier vocabulary for the SimQ
world corpus (Unit / End-to-End / Stress / Regression) that does not exist anywhere in the docs
today. Every other child ticket in this batch (`TCK-20260704-SIMQ-CORPUS-*`) references this
taxonomy by name — new worlds are described as "unit-tier" or "stress-tier" without a canonical
definition of what that means, which worlds belong to which tier today, or how a future world
addition should be classified. This ticket creates that canonical reference.

**Tier justification (hotfix, not standard):** this is a single new doc with no code changes, no
schema changes, and no calibration re-run required — it only classifies and describes worlds/
mechanics that already exist per the investigation's own tables. It mirrors the doc-only hotfix
precedent set by `TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA` (same shape: document an already-decided
architectural stance, no staging artifacts required). Self-evident intent: transcribe the tier
definitions and the investigation's existing world-inventory table into a durable, discoverable
doc location.

## Scope
1. Create a new doc — `docs/simulation_quality/corpus_tier_taxonomy.md` — defining:
   - **Unit tier**: new, small, synthetic-content-OK worlds, each isolating exactly ONE gated
     mechanic with everything else at baseline. Template/synthetic content acceptable; narrative
     coherence is not a goal.
   - **End-to-end tier**: existing archetype worlds get richer, bespoke, archetype-matched content
     (not templated).
   - **Stress tier**: new worlds specifically filling identified scale-diversity gaps.
   - **Regression/baseline tier**: already-calibration-anchored worlds, left alone as a stable
     control group — explicitly a "do not touch" policy, not an oversight.
2. Map every world currently under `data/worlds/` to its tier as of 2026-07-04 (all 10 are
   Regression/baseline today, since none of the new unit/stress worlds exist yet — state this
   explicitly so the doc doesn't read as if tiers are already populated).
3. Define criteria for classifying a future world addition into one of the four tiers (e.g.
   "isolates exactly one Pattern-6 field with everything else at baseline" → unit tier; "fills a
   named scale-diversity gap from an investigation" → stress tier; "extends an existing archetype
   world's content richness" → end-to-end tier).
4. Cross-reference `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` as
   the evidentiary source for the current per-world content/scale tables (§1, §2), rather than
   duplicating the full tables verbatim.
5. Add an entry to `docs/REGISTRY.yaml` if a REGISTRY entry pattern applies to
   `docs/simulation_quality/` docs (check existing entries for `eval_matrix_results.md` /
   `event_type_coverage.md` for the pattern to follow).
6. Run `make knowledge-index-update` (required — this ticket creates a new file under `docs/`).

## Out of Scope
- Authoring any actual unit/stress-tier world content (that is tickets 4-6, 8 in this batch)
- Changing any existing world's tier classification behavior (this ticket only documents; it does
  not gate or enforce tier membership in code)
- Re-running `make evaluate` calibration (no world content or code changes in this ticket)

## Acceptance Criteria
- [ ] `docs/simulation_quality/corpus_tier_taxonomy.md` exists with all four tier definitions
- [ ] All 10 current worlds under `data/worlds/` are explicitly mapped to Regression/baseline tier
      in the new doc, with a note that no unit/end-to-end-richened/stress worlds exist yet as of
      this ticket's authoring date
- [ ] Future-classification criteria section exists and is concrete enough that a later ticket could
      cite it (not vague)
- [ ] New doc cites `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md`
      directly rather than re-deriving its tables
- [ ] `docs/REGISTRY.yaml` updated if applicable (per existing `docs/simulation_quality/*` entries)
- [ ] `make knowledge-index-update` run successfully after the doc is added
- [ ] `python3 tools/validate_frontmatter.py docs/simulation_quality/corpus_tier_taxonomy.md
      --content-type doc` passes

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TIERS-EPIC (parent epic)
- TCK-20260704-SIMQ-CORPUS-SCALE-METRIC — references this taxonomy for scale-axis criteria
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLDS-FACTION-INFO — first unit-tier worlds; must conform to this
  doc's unit-tier definition
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-SELFMODEL-PILOT — unit-tier world; must conform
- TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY — unit-tier world; must conform
- TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION — end-to-end tier; must conform
- TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS — stress tier; must conform
- TCK-20260702-SIMQ-UPLIFT2-AGENCY-DA — doc-only hotfix precedent this ticket's tier choice mirrors

## Related Docs
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` — full per-world
  content/scale evidence (§1 mechanic inventory table, §2 scale diversity table and gap analysis)
- `docs/simulation_quality/eval_matrix_results.md` — existing calibration grade tables
- `docs/simulation_quality/quality_scoring_contract.md` — SimQ pillar contract
- `docs/plans/audit_fix_plan.md`

## Related Stored Artifacts
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/` — this ticket's evidentiary source

## Related Code Areas
- `data/worlds/` — the 10 worlds being tier-mapped (no code changes, reference only)
- `docs/REGISTRY.yaml`

## Assumptions / Open Questions
- UQ-1: Should the taxonomy doc live under `docs/simulation_quality/` (SimQ-specific) or
  `docs/guidelines/` (general authoring guidance)? Scoped to `docs/simulation_quality/` since the
  tiering is specifically about SimQ calibration corpus organization, not general world-authoring
  guidance (that's `docs/guides/content_authoring.md`) — confirm this placement is correct during
  implementation, and relocate if investigation reveals a stronger existing convention.

## Implementation Notes
Created `docs/simulation_quality/corpus_tier_taxonomy.md` with all four tier definitions (Unit,
End-to-end, Stress, Regression/baseline), each with an explicit classification criterion. Mapped
all 10 current `data/worlds/` entries to Regression/baseline tier (none of the new unit/stress
worlds exist yet, and no world has been promoted into deliberate end-to-end content expansion, as
of this ticket's authoring date) — cited `staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/
investigation.md` §2 as the evidentiary source for per-world counts rather than duplicating the
table verbatim (per Scope item 4). Also transcribed the investigation's 5 named scale-diversity
gaps as concrete stress-tier candidates, and added a decision-order section for classifying future
world additions.

Note: the ticket's own citation to `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/
investigation.md` is a stale path — that folder was renamed to `staging_artifacts/
TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/` earlier this session once the epic ticket ID existed. The new
doc cites the correct, current path.

Ran `make docs-registry` to index the new doc — it exited non-zero, but the registry write itself
succeeded (`docs/REGISTRY.yaml` correctly indexes the new doc; confirmed via direct grep). The
non-zero exit is caused by 12 pre-existing, unrelated docs across `docs/engine/`, `docs/mechanics/`,
`docs/simulation/`, `docs/simulation_quality/`, `docs/systems/`, and `docs/world/` that have no YAML
frontmatter at all — a repo-wide gap that predates and is unrelated to this ticket. Filed
`TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER` to track it rather than silently ignoring the
non-zero exit code or expanding this hotfix ticket's scope to fix 12 unrelated files.

## Citation Correction (2026-07-08, TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING)

This ticket's citations above to `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md`
(later renamed to `staging_artifacts/TCK-20260704-SIMQ-CORPUS-TIERS-EPIC/investigation.md`) point to a
pre-ticket epic-scoping investigation that was never migrated to `stored_artifacts/` and is now
unrecoverable: `staging_artifacts/` is gitignored by repo policy, and full git history confirms no commit
ever added a file at either path. This is a citation/traceability gap only -- every specific fact this
ticket drew from that doc has been independently cross-validated against ground truth
(`world.yaml`/`world_compile_report.json`,
`test_corpus_diversity.py::EXPECTED_DISTINCT_POPULATED_FACTIONS`) by this ticket and/or
`TCK-20260704-SIMQ-CORPUS-UNIT-WORLD-AGENCY` / `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`. See
`tickets/done/TCK-20260707-EPIC-SCOPE-INVESTIGATION-DOC-MISSING.md` for the full root-cause writeup.

## Test Summary
- `python3 tools/validate_frontmatter.py docs/simulation_quality/corpus_tier_taxonomy.md
  --content-type doc` → OK, no violations.
- `make docs-registry` → registry write succeeded (new doc indexed, confirmed via grep); non-zero
  exit code attributed entirely to the 12 pre-existing files tracked in the new follow-up ticket,
  not to this ticket's own doc.
- `make knowledge-index-update` → 1 file re-embedded successfully.
- No code changes in this ticket; no calibration re-run required (per Out of Scope).

## Files Changed
- `docs/simulation_quality/corpus_tier_taxonomy.md` — new file
- `docs/REGISTRY.yaml` — regenerated (includes the new doc)
- `tickets/todos/TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER.md` — new follow-up ticket

## Completion Summary
Created the canonical SimQ corpus tier taxonomy doc, giving every other ticket in this batch
(2-10) a durable, citable definition for the Unit/End-to-end/Stress/Regression vocabulary they
each reference by name. All 10 current worlds mapped explicitly to Regression/baseline tier, with
concrete classification criteria for future world additions and the investigation's 5 named
scale-diversity gaps transcribed as stress-tier candidates. While regenerating the docs registry to
index the new file, found and filed a follow-up ticket for a pre-existing, unrelated repo-wide gap
(12 docs missing frontmatter entirely, causing `make docs-registry` to always exit non-zero) rather
than letting it pass silently or expanding this hotfix ticket's scope to fix it directly.
