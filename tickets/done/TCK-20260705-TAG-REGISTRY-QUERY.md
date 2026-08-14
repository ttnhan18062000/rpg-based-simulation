---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260705-TAG-REGISTRY-QUERY
phase: done
date: 2026-07-05
tags: [tagging, taxonomy, registry, investigator]
---

# TCK-20260705-TAG-REGISTRY-QUERY

## Title
Extend REGISTRY.yaml prior-work search to filter by tags, not just layer

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
`docs/guidelines/tag_taxonomy.md`'s `Subsystem/Topic` category was designed specifically to serve "Scenario 3: cross-cutting discovery beyond `layer`" — `layer` is a deliberately coarse 19-value enum, and a topic like `faction` genuinely spans the `ai`, `systems`, and `social` layers at once. Confirmed directly in code: `.claude/workflows/create-tickets.js`'s Investigate phase (`Step 2: Docs and prior tickets via REGISTRY.yaml`, around line 343: `matches = [e for e in entries if e.get('layer') in layers]`) and `.claude/agents/investigator.md`'s "Finding Prior Work" step both filter `docs/REGISTRY.yaml` by `layer` only — `tags` is never read as a filter anywhere in agent-facing code. This means a query for "everything about factions" today requires knowing which layers to search rather than being answerable in one pass. This ticket wires the now-controlled tag vocabulary into that search.

## Scope
- Extend `create-tickets.js`'s Investigate-phase REGISTRY.yaml query (the Python one-liner around line 340-343) to also accept a set of candidate `Subsystem/Topic` tags derived from the concern's `domain_area`/title/description, and match entries where `tags` intersects with those candidates, in addition to the existing `layer` filter — union the two result sets rather than requiring both to match (a `layer`-only match today should still surface; a `tags`-only match should now additionally surface).
- Update `.claude/agents/investigator.md`'s "Finding Prior Work" section (both the REGISTRY.yaml-preferred path and the fallback path) to describe tag-based filtering as a supplementary search dimension alongside `related_code_areas`/`layer`.
- Decide, during Investigate, how to derive "candidate tags" from free-text ticket/concern descriptions without inventing a new NLP layer — the likely approach is a simple keyword match against the canonical `Subsystem/Topic` tag vocabulary already observable in the corpus (e.g. via `docs/REGISTRY.yaml` itself, or a small curated list), not a fuzzy/semantic match (that's what `mcp__knowledge-search__search_docs` is already for — this ticket should not duplicate that tool's job, only add a second, cheap, exact-tag-match lens).

## Out of Scope
- Any change to how `mcp__knowledge-search__search_docs`'s semantic search works — that tool already does fuzzy, cross-cutting discovery; this ticket adds a cheap, exact, tag-based filter as a second, complementary lens for the structured `REGISTRY.yaml` lookup specifically, not a replacement for semantic search.
- Building a full tag-based faceted search UI or CLI tool — this ticket only wires tag filtering into the two existing agent-facing consumers (`create-tickets.js`, `investigator.md`).
- Retroactively re-tagging any of the ~1001 historical tickets to make them more discoverable by this new filter — historical tags are whatever they are (many pre-taxonomy, uncontrolled); this ticket makes tag search *possible* going forward, it does not clean up what's searchable today.

## Acceptance Criteria
- [ ] `create-tickets.js`'s REGISTRY.yaml query in the Investigate phase filters by `tags` (candidate `Subsystem/Topic` tags derived from the concern) in addition to `layer`, unioning both result sets.
- [ ] `.claude/agents/investigator.md` documents tag-based filtering as part of its "Finding Prior Work" step.
- [ ] A worked example (in the ticket's Implementation Notes or a small test/demo) shows a topic that spans multiple `layer` values (e.g. `faction`, per the taxonomy doc's own worked example) being found in one query where it previously required checking multiple layers.
- [ ] No existing `layer`-only query behavior regresses — a query that previously matched by `layer` alone must still match.

## Related Tickets
- TCK-20260704-TAG-TAXONOMY (defined the Subsystem/Topic category and confirmed "tags never queried" as the baseline gap this ticket closes)
- TCK-20260705-TAG-SKILL-SUGGEST (sibling follow-up ticket consuming the Process/Skill-signal category instead — independent of this ticket, no shared code path)

## Related Docs
- docs/guidelines/tag_taxonomy.md (Subsystem/Topic category definition, Scenario 3, the `faction` worked example)
- docs/ai/agents.md (`investigator` section — update to describe tag-based prior-work search)
- docs/ai/workflows.md (`create-tickets` section — update if the Investigate phase description changes materially)
- Consider whether `docs/guides/` needs an update: if a developer-facing guide ever documents "how ticket investigation finds prior work," this ticket's tag-filtering addition belongs there too — no existing guide currently describes this internal agent behavior in detail, so check during Investigate whether this is worth a small addition to an existing guide (e.g. `docs/guides/README.md`'s general framing) rather than a new file, since this change is more of an internal agent-tooling improvement than a subsystem developers directly interact with.

## Related Stored Artifacts
None yet.

## Related Code Areas
- .claude/workflows/create-tickets.js (Investigate phase, ~line 335-345)
- .claude/agents/investigator.md ("Finding Prior Work" section)
- docs/REGISTRY.yaml (read-only — the data source being queried)
- tools/generate_registry.py (read-only reference — confirms what fields are actually present on each entry)

## Assumptions / Open Questions
- Whether "candidate tags" should be derived from the ticket/concern's own free text via simple keyword matching against known canonical tags, or whether a more structured input (e.g. requiring the concern to already declare a tentative tag) is cleaner — left for Plan to decide with evidence, not assumed here.
- Whether this same tag-filtering logic should also be exposed via `tools/knowledge_search.py`'s keyword-search mode (the "Tier 3" fallback mentioned in `create-tickets.js`) — likely a nice-to-have, not required by this ticket's Acceptance Criteria; flag as a possible smaller follow-on rather than expanding this ticket's scope.
- **Pre-existing bug discovered during investigation (2026-07-05), not this ticket's to fix:** `tools/generate_registry.py`'s `collect_tickets()` never emits a `layer` key on ticket entries at all (confirmed: 0 of 1019 live ticket entries in `docs/REGISTRY.yaml` carry `layer`, even though every ticket's own frontmatter has one). This means `create-tickets.js`'s existing `layer`-only query has *never* matched a single ticket, regardless of domain — it is silently dead code for tickets today (it does work for docs). Consequence: this ticket's tag-based union filter is not "a second lens alongside an already-working layer lens" for tickets — it will be the *first and only* mechanism that has ever surfaced tickets through this code path. `tools/generate_registry.py` remains read-only per this ticket's Related Code Areas; fixing `collect_tickets()` to also emit `layer` is explicitly deferred to a separate future ticket, not built here. AC4 ("no existing layer-only query behavior regresses") is trivially satisfied for tickets (there is no existing ticket-matching behavior to preserve) but must still hold for docs, where layer filtering does work today.
- **Correction to this ticket's own Request Summary wording:** `.claude/agents/investigator.md`'s "Finding Prior Work" step does not currently filter by `layer` at all — it filters by `related_code_areas` overlap only. So tags become a second dimension alongside `related_code_areas` there, not alongside `layer` as the Scope section's phrasing implies. Only `create-tickets.js` has an existing `layer` dimension.

## Implementation Notes
Implemented per the approved plan's 7 steps:

1. **`tools/registry_query.py`** (new): `SEED_TAGS` (the 10 taxonomy-doc-named Subsystem/Topic
   words, lowercase), `candidate_tags_from_text(*texts)` (substring match, no NLP), and
   `filter_registry(entries, layers=None, candidate_tags=None)` (union filter — an entry matches on
   `layer` OR `tags` overlap; empty/`None` on one side contributes zero matches from that side).
   Pure, side-effect-free, does not import `tools/generate_registry.py` (left read-only).
2. **`tests/tools/test_registry_query.py`** (new): exactly the 3 tests named in test_plan.md. All
   pass (`pytest tests/tools/test_registry_query.py -v` → 3 passed).
3. **`.claude/workflows/create-tickets.js`** (Investigate phase, ~lines 335-353): the embedded
   `python3 -c "..."` snippet now imports `candidate_tags_from_text`/`filter_registry` from
   `tools/registry_query.py` and unions the tag-match result with the existing layer-match result.
   Manually verified against the live `docs/REGISTRY.yaml` (1272 entries): a sample concern
   containing "faction"/"cognition" text correctly surfaced ticket entries via the tag path that the
   pre-existing `layer`-only query has never been able to surface (see point below).
4. **`.claude/agents/investigator.md`** ("Finding Prior Work", lines 13-25): both the
   REGISTRY.yaml-preferred path and the fallback path now describe tag-based filtering as a second
   dimension alongside `related_code_areas` (not alongside `layer` — `investigator.md` never had a
   `layer` dimension to begin with, confirmed in investigation.md).
5. **`docs/guides/ticket_tagging.md`**: added a "Tags as a Registry Search Filter" section
   describing the new filter dimension in both consumers and linking to `tools/registry_query.py`.
6. **`docs/ai/agents.md`**: added one clause to the `investigator` bullet noting tag-based matches
   against `docs/REGISTRY.yaml`. `docs/ai/workflows.md` was deliberately **not** touched — a
   proportionality judgment made in the plan (that doc's create-tickets phase table is coarser than
   filter mechanics and doesn't even name `layer` filtering today), not an oversight.
7. Regression pytest run — see Test Summary.

**Disclosed, not fixed (deferred to a future ticket):** `tools/generate_registry.py`'s
`collect_tickets()` never emits a `layer` key on ticket entries (0 of 1019 live ticket entries carry
`layer`, confirmed both in investigation.md and by the manual verification run in point 3 above,
where the `layers=['ai','strategy']` filter alone would have returned 0 tickets — the tag path is
what actually surfaced results). This means the pre-existing `layer`-only ticket search in
`create-tickets.js` has been dead code since the registry was introduced, and this ticket's
tag-based union filter is the *first and only* mechanism that has ever surfaced tickets through that
code path — not "a second lens alongside an already-working one." `tools/generate_registry.py`
remains untouched per this ticket's Related Code Areas (explicitly read-only); fixing
`collect_tickets()` to also emit `layer` is out of scope here.

**Manual sync note:** two seed-vocabulary lists now exist by design —
`docs/guidelines/tag_taxonomy.md`'s prose list of Subsystem/Topic example words, and
`tools/registry_query.py`'s `SEED_TAGS` tuple. They are intentionally not derived from one another
at runtime (parsing the doc for a 10-word list would be over-engineering) and must be kept in sync
by hand; `registry_query.py`'s module docstring calls this out for discoverability.

## Test Summary
Both regression pytest commands from plan Step 7 were run:

1. `pytest tests/tools/test_generate_registry.py tests/tools/test_validate_frontmatter.py tests/tools/test_knowledge_search.py -v`
   → 178 passed, 28 failed. All 28 failures are in `tests/tools/test_knowledge_search.py` and are
   **pre-existing, environmental** (not caused by this ticket): the underlying `knowledge_search.py
   build` subprocess fails with `RuntimeError: unable to mmap ... Cannot allocate memory` while
   loading the `sentence-transformers/all-MiniLM-L6-v2` model — reproduced identically on a clean
   `git stash` of this ticket's changes (i.e. the failure exists on the unmodified tree too). This
   ticket does not touch `tools/knowledge_search.py` or its tests (explicitly out of scope per
   Scope Guards). `test_generate_registry.py` (42/42) and `test_validate_frontmatter.py` both fully
   passed.
2. `pytest tests/tools/test_registry_query.py tests/tools/test_generate_registry.py -v`
   → 42 passed, 0 failed (3 new + 39 existing).

## Files Changed
- `tools/registry_query.py` (new)
- `tests/tools/test_registry_query.py` (new)
- `.claude/workflows/create-tickets.js` (Investigate phase snippet only, ~lines 335-353)
- `.claude/agents/investigator.md` ("Finding Prior Work" section only, lines 13-25)
- `docs/guides/ticket_tagging.md` (new section added)
- `docs/ai/agents.md` (one clause added to investigator bullet)
- `tickets/todos/tag-taxonomy-followups/TCK-20260705-TAG-REGISTRY-QUERY.md` — deleted (routine Scope-phase move: content copied forward to `tickets/inprogress/TCK-20260705-TAG-REGISTRY-QUERY.md` at the start of this pipeline run, nothing lost).
- No diff to `tools/generate_registry.py`, `create-tickets.js`'s Structure phase, `docs/ai/workflows.md`, or `tickets/working_log.csv` (all explicitly out of scope, confirmed empty).

## Completion Summary
Extended `docs/REGISTRY.yaml`'s prior-work search with a second, cheap filter dimension over `tags`
(Subsystem/Topic category): a new pure module `tools/registry_query.py` (`SEED_TAGS`,
`candidate_tags_from_text()`, `filter_registry()`) is imported by `create-tickets.js`'s Investigate-phase
subprocess snippet and described in `investigator.md`'s "Finding Prior Work" step, unioned with each
consumer's existing dimension (`layer` for create-tickets.js, `related_code_areas` for investigator.md).
Investigation surfaced a real, disclosed-not-fixed pre-existing bug: `tools/generate_registry.py` never
emits a `layer` key on ticket entries (0/1019 confirmed), so this ticket's tag filter is the first and
only mechanism that has ever surfaced tickets through `create-tickets.js`'s registry query — not a
second lens alongside an already-working one. 3 new unit tests added (all passing) plus a full
regression run (42/42 on the directly-relevant suites; the unrelated `test_knowledge_search.py`
suite's 28 failures are pre-existing/environmental, reproduced identically on the unmodified tree via
`git stash`, and this ticket never touches that file). No `docs/parity_ledger/` entry affected (the one
keyword hit, INFRA-180, covers `validate_frontmatter.py`'s taxonomy enforcement, untouched here; this
is agent-orchestration tooling, not a tracked simulation/infrastructure behavior). The two
seed-vocabulary copies (`tag_taxonomy.md` prose, `registry_query.py`'s `SEED_TAGS`) must be kept in
sync by hand — disclosed in the module's own docstring.
