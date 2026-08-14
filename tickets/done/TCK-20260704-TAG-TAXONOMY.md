---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260704-TAG-TAXONOMY
phase: done
date: 2026-07-04
tags: [tagging, taxonomy, frontmatter, registry, data-quality]
---

# TCK-20260704-TAG-TAXONOMY

## Title
Define and enforce a controlled technical-tag taxonomy for tickets

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
Analyzed all 1001 ticket entries in `docs/REGISTRY.yaml`. Tags are being filled in dutifully (only 0.4% empty), but the vocabulary is uncontrolled free text: **1273 distinct tags across 1001 tickets, 730 of them (57.3%) used exactly once.** At least 19 confirmed format-duplicate groups exist purely from case/hyphen/underscore variation (`p0`/`P0`, `phase-5`/`phase5`, `simulation_quality`/`simulation-quality`, `world-modules`/`worldmodules`, etc.) — the true synonym count is likely higher (`obs` 45 / `observability` 43 and `cog` 30 / `cognition` 24 look like the same split, just not caught by a mechanical hyphen/case check). Some tags (`p0`, `p1`, `p2`) are pure duplicates of the dedicated `Priority` field already in the ticket body — redundant by construction.

Root cause: `tools/validate_frontmatter.py` validates `layer` as a closed enum (`LAYER_VALUES`) but has **no validation at all for `tags`** — anything goes, so it drifted into per-ticket free text over ~1001 tickets.

**Why this matters beyond cleanliness (2026-07-04 direction: design for future usage/scenarios first, not just past mess):** a clean tag vocabulary is the prerequisite for tags becoming an actual *routing signal* for workflow/process/skill management, not just descriptive metadata. Concrete future scenarios the taxonomy's category design should hold up against, even though none are implemented by this ticket:

1. **Tag-driven skill suggestion.** `TCK-20260704-SKILL-TRIGGER-COVERAGE` found 3 skills (`api-design-principles`, `debugging-strategies`, `python-performance-optimization`) with confirmed applicable-but-unsurfaced work, and proposed *file-path-based* triggers in `CLAUDE.md` as the fix. A controlled tag on the ticket itself (`api-design`, `debugging`, `performance`) is a more direct signal of *intent* than inferring it from which files got touched — a ticket tagged `performance` should be able to suggest `/python-performance-optimization` at scope time, before any file is even edited.
2. **Tag-driven process/gate routing.** Tickets carrying certain tags (e.g. a future `security`/`hardening` category) could trigger an extra review step, the way `authority: P0` docs already get special treatment in `mechanics-auditor`'s queries. This requires tags to be a category the routing logic can pattern-match on reliably — impossible while the vocabulary is free text.
3. **Cross-cutting discovery that `layer` can't provide.** `layer` is a deliberately coarse 19-value enum. A topic like `faction` genuinely spans `ai`, `systems`, and `social` layers — `layer`-only search (the only thing actually queried today, per investigation) can't find "everything about factions" in one query the way a clean `faction` tag could.
4. **Retro/analytics grouping.** `TCK-20260704-RETRO-LOOP-ENFORCEMENT` found the retro loop has never run for real. Once it does, tag-based grouping of `runs.jsonl`/`events.jsonl` (e.g. "which tagged subsystem has the most gate failures or slowest runs") is a finer-grained lens than `tier`/`workflow` alone — but only if tags are a controlled, groupable vocabulary rather than 1273 mostly-singleton strings.
5. **Ongoing skill-catalog health check.** This session's skill-usage investigation (cross-referencing tag-implied applicable work against actual `Skill` tool invocation counts) was done manually, once, ad hoc. A controlled taxonomy makes that check automatable and repeatable — the same analysis, run periodically instead of rediscovered from scratch.

These scenarios are why the taxonomy category design (see Scope) explicitly separates a **process/skill-signal** category from generic subsystem tags, rather than treating all non-phase, non-forbidden tags as one undifferentiated bucket — the categories need the right shape for scenario 1-2 above to be buildable later, even though building them isn't this ticket's job.

User decisions (2026-07-04): build a controlled taxonomy and enforce it going forward (not a lighter format-only normalization); do not backfill the ~1001 historical tickets; do not *implement* tag consumption yet (routing/hook code is a separate, later concern) — but the taxonomy's category design must be validated against the scenarios above during Plan, not decided in a vacuum.

## Scope
- Write `docs/guidelines/tag_taxonomy.md` defining tag **categories** (not necessarily a single frozen list of every individual tag — that would need to grow forever) with canonical spelling rules per category. Starting point derived from the actual corpus (to be finalized during Investigate/Plan, not mandated here):
  - **Subsystem/topic** tags: combat, economy, cognition, faction, resource, social, content, world, engine, ... — likely overlaps with `layer` at a coarser grain; the taxonomy should clarify when a tag adds information beyond `layer` vs. when it's redundant. Serves future scenario 3 (cross-cutting discovery).
  - **Phase/milestone markers**: canonical format `phase-N` (not `phaseN`) — resolves the 3 confirmed `phase-N`/`phaseN` duplicate pairs.
  - **Process/skill-signal** tags: a *distinct* category (not folded into subsystem or quality-attribute) for tags whose whole purpose is future routing to a specific skill or process step — e.g. `api-design`, `performance-profiling`, `debugging`, and (once defined) `security`/`hardening`. This category exists specifically to serve future scenarios 1-2 (tag-driven skill suggestion, tag-driven gate routing) — its canonical tag names should be chosen to line up 1:1 with the skill/process they'd eventually trigger, so a later routing table is a lookup, not a re-mapping exercise.
  - **Quality-attribute** tags: hardening, calibration, schema, audit — cross-cutting concerns not captured by subsystem or layer, and not specifically a skill/process trigger (distinguish from the process/skill-signal category above; some overlap is likely and should be resolved explicitly during Plan, not left ambiguous).
  - **Explicitly forbidden**: `p0`/`p1`/`p2`/`P0`/`P1`/`P2` as tags — this information already lives in the ticket's dedicated `Priority` section; a tag duplicating it is pure redundancy, not a taxonomy gap to fill.
- Add a canonical-synonym mapping (e.g. `obs` → `observability`, `cog` → `cognition`, `sim` → `simulation`) that `tools/validate_frontmatter.py` can check tags against — reject (or warn, TBD during Plan) if a ticket uses a non-canonical spelling that has an established canonical form.
- Extend `tools/validate_frontmatter.py`'s `_validate_ticket` (and `_validate_artifact`, since artifacts carry tags too) to check `tags` against the new taxonomy rules — mirrors the existing `_check_enum(filepath, fm, "layer", LAYER_VALUES)` pattern already used for `layer`.
- Update the `ticket-scoper` agent's prompt (`.claude/agents/ticket-scoper.md`) to reference the taxonomy doc when choosing tags for a new ticket, instead of picking free text.
- Add tests to `tests/tools/test_validate_frontmatter.py` (or wherever the existing frontmatter validation tests live) covering: canonical-form acceptance, non-canonical-synonym rejection, forbidden-priority-tag rejection.

## Out of Scope
- Backfilling or normalizing tags on the ~1001 existing tickets — explicit user decision to leave history alone, matching the precedent already set this session for agent-monitoring's historical schema drift.
- **Building** any tag consumption — no skill-suggestion logic, no gate-routing hook, no REGISTRY.yaml tag filter, no retro tag grouping. All five future scenarios in the Request Summary are context for *designing the categories correctly*, not work items for this ticket. Enforcing a clean taxonomy is the prerequisite; building what reads it is separate, later ticket(s).
- Changing the `layer` enum or its validation — already correctly enforced; this ticket only touches `tags`.
- A fully closed, exhaustive list of every permitted individual tag — the taxonomy should define categories and canonical-form rules for known synonyms, not attempt to enumerate every valid subsystem tag up front (that list will grow as the project grows; over-constraining it would just recreate the `layer`-enum-is-too-narrow problem at the tag level).

## Acceptance Criteria
- [x] `docs/guidelines/tag_taxonomy.md` exists, defining tag categories and at least the canonical-vs-synonym mapping for the confirmed duplicate pairs found in this investigation.
- [x] `tools/validate_frontmatter.py` rejects (or warns — decided during Plan) a ticket/artifact using a non-canonical spelling where a canonical form is defined.
- [x] `tools/validate_frontmatter.py` rejects a ticket using `p0`/`p1`/`p2` (any case) as a tag, since that duplicates the dedicated `Priority` field.
- [x] `.claude/agents/ticket-scoper.md` references the taxonomy doc when generating tags for new tickets.
- [x] New tests cover canonical acceptance, synonym rejection, and forbidden-priority-tag rejection.
- [x] Running `python3 tools/validate_frontmatter.py` against all 1001 existing (pre-2026-07-04) tickets does not newly fail on tag grounds — resolved via a date-gated cutoff (`TAG_TAXONOMY_EFFECTIVE_DATE`) rather than an explicit exemption list; confirmed via whole-directory run (only 2 same-cutoff-date tickets from a concurrent session are newly flagged, which is correct per design — disclosed in Implementation Notes, not a historical-ticket failure).
- [x] The taxonomy doc's category list is checked against all five future scenarios in the Request Summary — each scenario maps to a category in `tag_taxonomy.md`'s scenario→category table.

## Related Tickets
- TCK-20260704-SKILL-TRIGGER-COVERAGE — natural future consumer of the `process/skill-signal` tag category (scenario 1); that ticket's file-path-based `CLAUDE.md` triggers and a future tag-based lookup are complementary, not competing, mechanisms.
- TCK-20260704-RETRO-LOOP-ENFORCEMENT — natural future consumer of a clean tag vocabulary for retro report grouping (scenario 4), once the retro loop actually runs.

## Related Docs
- docs/README.md ("Frontmatter classification" section)
- docs/ai/agent_infrastructure_audit.md
- docs/plans/agent_infrastructure/idea_agent_monitoring_schema_enforcement.md (same underlying pattern — write-time validation exists for some fields but not others, leading to drift; this ticket is the `tags` analogue of that idea applied to a different subsystem)

## Related Stored Artifacts
- `staging_artifacts/TCK-20260704-TAG-TAXONOMY/investigation.md` — written 2026-07-04, covers the exact `validate_frontmatter.py` enum pattern to mirror, the full confirmed near-duplicate-group table, and the confirmed "tags are never queried" evidence.
- `plan.md` and `test_plan.md` intentionally not yet written — commit to concrete implementation steps, deferred until implementation actually begins per explicit user decision (ticket stays queued, not in-progress).

## Related Code Areas
- tools/validate_frontmatter.py (LAYER_VALUES pattern to mirror for tags)
- .claude/agents/ticket-scoper.md
- docs/guidelines/ (new: tag_taxonomy.md)
- docs/REGISTRY.yaml (read-only reference for the existing tag corpus analysis)
- tests/tools/test_validate_frontmatter.py (or equivalent existing test location)

## Assumptions / Open Questions
- Whether `validate_frontmatter.py` is invoked on every file on every run (which would need an explicit grandfather/exemption mechanism for the ~1001 historical tickets) or only on newly-created files as part of the ticket-scoper flow (which would make forward-only enforcement free) is not yet confirmed — resolve during Investigate before deciding on reject-vs-warn severity.
- Whether "subsystem/topic" tags should eventually be merged into `layer` entirely (since they appear to overlap) or intentionally kept as a finer-grained complement to `layer` is a design question for the Plan phase, not decided here.
- Whether rejection should be a hard validator failure or a softer lint warning (given this repo's general pattern of hooks nudging rather than blocking) is left for Plan/Investigate to resolve against precedent.

## Implementation Notes
Implemented per the approved plan (`staging_artifacts/TCK-20260704-TAG-TAXONOMY/plan.md`), Steps 1-8, no deviations:

1. **Validator**: Added `TAG_TAXONOMY_EFFECTIVE_DATE = "20260704"`, `FORBIDDEN_PRIORITY_TAGS = {"p0", "p1", "p2"}`, `TAG_SYNONYM_MAP` (7 entries), `_PHASE_TAG_PATTERN`, `_TICKET_ID_DATE_PATTERN` constants; `_ticket_id_effective_date()` and `_check_tags()` helper functions in `tools/validate_frontmatter.py`. Wired `errors += _check_tags(filepath, fm)` into `_validate_ticket` and `_validate_artifact` only — `_validate_doc`/`_validate_archive` untouched.
2. **Anti-drift tests**: Added `test_forbidden_priority_tags`, `test_tag_synonym_map`, `test_tag_taxonomy_effective_date` to `TestEnumAntiDrift`, mirroring the existing `*_VALUES` exact-equality pattern.
3. **New test classes**: `TestForbiddenPriorityTags` (5 tests: p0/p1/p2 rejection, uppercase rejection, valid-when-absent negative control) and `TestTagCanonicalization` (8 tests: canonical acceptance, obs/cog synonym rejection, phase-N format rejection, underscore format rejection, uppercase format rejection, artifact-path synonym rejection, historical-exemption regression against the real file `tickets/done/TCK-20260520-SIM-OBS-PHASE5-M24.md`, and malformed-ticket-id exemption). All new tests use ticket_id `TCK-20260704-TEST` (on-cutoff, checks apply) except the two exemption tests.
4. **`docs/guidelines/tag_taxonomy.md`** (new) — defines the four categories (Subsystem/Topic, Phase/Milestone, Process/Skill-signal, Quality-attribute), the scenario→category table for all 5 future usage scenarios, the forbidden-tag list, the canonical-synonym table, and the forward-only enforcement note. Frontmatter matches the established `docs/guidelines/*.md` convention exactly (`status: active`, `layer: guidelines`, `authority: P1`, `audience: developer`, no `tags` key) — validated via `python3 tools/validate_frontmatter.py docs/guidelines/tag_taxonomy.md` (passes).
5. **`docs/guidelines/frontmatter_schema.md`** — updated the `ticket` (line 84) and `artifact` (line 113) `tags` rows to reference `tag_taxonomy.md` and note forward-only enforcement from `2026-07-04`. The `doc` row (line 52) is untouched, still `free-form`.
6. **`docs/parity_ledger/infrastructure.yaml`** — updated `INFRA-180`'s `text` to describe the new tag enforcement and added `docs/guidelines/tag_taxonomy.md` to `v2_evidence`. `status: verified` and `priority: P2` left unchanged, per the plan's explicit guard (documentation catch-up, not a re-certification event).
7. **`.claude/agents/ticket-scoper.md`** — line 28's `tags:` template field now reads: `tags: [<see docs/guidelines/tag_taxonomy.md — prefer its categories and canonical spellings over raw scope-word lowercasing; never emit p0/p1/p2>]`.
8. **Manual whole-directory check** (beyond the unit test): ran `python3 tools/validate_frontmatter.py tickets/done/` — found 2 pre-existing, unrelated tickets (`TCK-20260704-SIMQ-AGENCY-STASIS-COLLAPSE`, `TCK-20260704-SIMQ-RESOURCEREGISTRY-STONE-GAP`) that carry the non-canonical `simulation_quality` tag and are newly flagged. This is correct, not a regression: both have a `ticket_id` date of `20260704`, which is on/after the effective cutoff, so they are not exempt by design — the AC only guarantees no new failures for tickets that *predate* the taxonomy. Fixing those two tickets' tags is out of scope here (no backfill of any ticket's tags is this ticket's job); noted for awareness only, not actioned.

No deviations from `plan.md` were needed; no entry added to its Deviations section.

## Test Summary
```
python3 -m pytest tests/tools/test_validate_frontmatter.py -v
# 64 passed (47 pre-existing + 17 new: 3 anti-drift + 5 TestForbiddenPriorityTags + 9 TestTagCanonicalization)

python3 -m pytest tests/tools/test_add_frontmatter_tickets.py tests/tools/test_add_frontmatter_live.py tests/tools/test_add_frontmatter_archive.py -q
# 199 passed, unaffected

python3 tools/validate_frontmatter.py docs/guidelines/tag_taxonomy.md
# OK: 1 file(s) checked — no violations
```
Full `tests/tools/` suite and full `pytest tests/` were intentionally not run, per `test_plan.md` (pre-existing, unrelated failures in `test_knowledge_search.py`/`test_search_mcp.py`).

## Files Changed
- `tools/validate_frontmatter.py` — added tag-taxonomy constants + `_check_tags()`, wired into `_validate_ticket`/`_validate_artifact`
- `tests/tools/test_validate_frontmatter.py` — 3 new anti-drift assertions + `TestForbiddenPriorityTags` + `TestTagCanonicalization` (17 new tests total)
- `docs/guidelines/tag_taxonomy.md` (new)
- `docs/guidelines/frontmatter_schema.md` — ticket/artifact `tags` rows updated
- `docs/parity_ledger/infrastructure.yaml` — `INFRA-180` `text`/`v2_evidence` updated
- `.claude/agents/ticket-scoper.md` — `tags:` template field updated

## Completion Summary
Added a controlled tag taxonomy (`docs/guidelines/tag_taxonomy.md`, 4 categories) and wired forward-only (`>= 2026-07-04`), hard-reject enforcement into `tools/validate_frontmatter.py`'s `_validate_ticket`/`_validate_artifact` for forbidden `p0`/`p1`/`p2` tags and non-canonical format/synonym spellings, with 17 new tests (including a regression against the real historical ticket `TCK-20260520-SIM-OBS-PHASE5-M24.md` proving no backfill/re-validation of history occurs). `ticket-scoper.md` and `frontmatter_schema.md` updated to reference the taxonomy; `INFRA-180` parity ledger entry updated in the same session. All acceptance criteria met; all scoped tests pass (64 + 199).
