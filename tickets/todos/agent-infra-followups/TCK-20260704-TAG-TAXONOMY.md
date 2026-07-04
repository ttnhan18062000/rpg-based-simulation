---
status: active
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260704-TAG-TAXONOMY
phase: open
date: 2026-07-04
tags: [tagging, taxonomy, frontmatter, registry, data-quality]
---

# TCK-20260704-TAG-TAXONOMY

## Title
Define and enforce a controlled technical-tag taxonomy for tickets

## Status
OPEN

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
- [ ] `docs/guidelines/tag_taxonomy.md` exists, defining tag categories and at least the canonical-vs-synonym mapping for the confirmed duplicate pairs found in this investigation.
- [ ] `tools/validate_frontmatter.py` rejects (or warns — decided during Plan) a ticket/artifact using a non-canonical spelling where a canonical form is defined.
- [ ] `tools/validate_frontmatter.py` rejects a ticket using `p0`/`p1`/`p2` (any case) as a tag, since that duplicates the dedicated `Priority` field.
- [ ] `.claude/agents/ticket-scoper.md` references the taxonomy doc when generating tags for new tickets.
- [ ] New tests cover canonical acceptance, synonym rejection, and forbidden-priority-tag rejection.
- [ ] Running `python3 tools/validate_frontmatter.py` against all 1001 existing tickets does not newly fail on tag grounds for tickets that predate this taxonomy (i.e., the new tag validation only applies going forward, consistent with the historical-data decision) — confirm the validator's scope/invocation pattern (is it run against all files or only new/changed ones?) before deciding whether this needs a grandfather clause or whether it's naturally forward-only because it's only invoked on new ticket creation.
- [ ] The taxonomy doc's category list is checked against all five future scenarios in the Request Summary — each scenario should be able to name which category its routing logic would eventually read, even though none are built here. If a scenario can't point to a category that would serve it, the category design isn't done yet.

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
(not yet implemented — standard tier, requires investigation and plan phases before implementation)

## Test Summary
(not yet implemented)

## Files Changed
(not yet implemented)

## Completion Summary
(not yet implemented)
