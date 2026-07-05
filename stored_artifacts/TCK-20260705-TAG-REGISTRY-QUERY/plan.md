---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260705-TAG-REGISTRY-QUERY
artifact_type: plan
tags: [tagging, taxonomy, registry, investigator]
---

# Plan — TCK-20260705-TAG-REGISTRY-QUERY

## Summary
Extract a pure, testable seed-vocabulary tag-matcher + union-filter into `tools/registry_query.py`, import it from create-tickets.js's real (subprocess-executed) Python snippet, and document tags as a second search dimension in investigator.md and ticket_tagging.md.

## Steps

### Step 1: Create `tools/registry_query.py`
- **Files:** `tools/registry_query.py` (new)
- **Change:** Add a small, importable, pure module with no side effects:
  - `SEED_TAGS` — tuple of the 10 Subsystem/Topic words named in `docs/guidelines/tag_taxonomy.md`
    (`combat, economy, cognition, faction, resource, social, content, world, engine, strategy`),
    lowercase, in that order. Comment: extend this list and the taxonomy doc together — one source
    of truth, per investigation Risk 1's rejection of frequency-mining.
  - `candidate_tags_from_text(*texts: str) -> set[str]` — lowercases and concatenates all non-empty
    `texts` with a space, returns `{tag for tag in SEED_TAGS if tag in haystack}`. No NLP, no
    stemming — plain substring test only.
  - `filter_registry(entries, layers=None, candidate_tags=None) -> list[dict]` — union filter:
    an entry matches if `bool(layers) and e.get('layer') in layers`, OR
    `bool(candidate_tags) and set(e.get('tags') or ()) & set(candidate_tags)`. Empty/`None` on one
    side contributes zero matches from that side (does not degrade to "match everything"). Preserves
    input order; no de-duplication needed since a `list` comprehension over `entries` visits each
    entry once and OR-combines the two predicates per entry (not two separate passes concatenated).
  - Module docstring: one paragraph naming this ticket ID and cross-referencing
    `docs/guidelines/tag_taxonomy.md` (Subsystem/Topic category) as the vocabulary's source of truth.
- **Do NOT touch:** `tools/generate_registry.py` (read-only per Related Code Areas) — this module
  only *consumes* the entry-dict shape that `generate_registry.py` already produces
  (`type`, `layer`, `tags`, `path`, `title`, `ticket_id`), it does not import from or modify it.
- **Verify:** `python3 -c "import sys; sys.path.insert(0,'tools'); import registry_query; print(registry_query.SEED_TAGS)"` prints the 10-tuple with no errors.

### Step 2: Add `tests/tools/test_registry_query.py`
- **Files:** `tests/tools/test_registry_query.py` (new)
- **Change:** Follow `tests/tools/test_generate_registry.py`'s import pattern exactly (insert
  `tools/` onto `sys.path`, flat `from registry_query import ...` — the repo has no
  `tools/__init__.py`, so this is the only import style that works and matches existing convention).
  Build fixture entries as **plain in-memory dicts** (per test_plan's explicitly-allowed "in-memory
  dicts" option) — do not round-trip through `generate_registry.py`'s file-parsing path, since
  `filter_registry` operates on already-loaded entry dicts, not markdown files. Add exactly the 3
  tests test_plan.md specifies, using its exact names:
  1. `test_candidate_tags_from_seed_vocabulary_matches_substring` — text containing `"faction"`
     (case-insensitive, anywhere across simulated title+description+domain_area args) returns a set
     containing `"faction"`; text with no seed-word substrings returns `set()`.
  2. `test_registry_matches_union_layer_and_tags_not_intersection` — 3-entry fixture: (a) one **doc**
     entry (`type: "doc"`) matching by `layer` only (per investigation's finding that no ticket entry
     ever carries `layer` — use a doc entry for this side, with a code comment citing
     investigation.md's Current Behavior section for why), (b) one entry matching by `tags` only
     (no layer match), (c) one entry matching neither. Assert union result contains (a) and (b), not
     (c); assert a tags-only call (empty/mismatched `layers`) still returns (b).
  3. `test_faction_tag_query_surfaces_entries_layer_search_would_miss` — fixture with ≥2 entries
     tagged `faction` at different `layer` values (e.g. `ai` and `social`) plus one `layer: ai` entry
     with no `faction` tag. Query with `layers=['ai']` and `candidate_tags=None` (simulating
     today's pre-fix single-layer guess) — assert the `social`-layer `faction` entry is absent.
     Then query with `candidate_tags={'faction'}` added — assert both `faction` entries are present
     regardless of the `layers` value passed.
- **Do NOT touch:** `tests/tools/test_generate_registry.py`, `tests/tools/test_validate_frontmatter.py`,
  `tests/tools/test_knowledge_search.py` — regression surface only, not edit targets. Do not add a
  `layer` field to any ticket-shaped fixture and do not add `test_ticket_entry_has_layer_field` here
  (explicitly deferred to a future ticket per test_plan's Anti-Drift Test Guards).
- **Verify:** `pytest tests/tools/test_registry_query.py -v` — all 3 tests pass.

### Step 3: Wire `create-tickets.js`'s Investigate-phase query to `tools/registry_query.py`
- **Files:** `.claude/workflows/create-tickets.js` (lines ~335-353 only)
- **Wiring mechanism (resolved during planning, not left open):** the embedded `python3 -c "..."`
  block inside the `agent(...)` prompt template is not LLM-interpreted pseudocode — it is a literal
  shell command that the Investigate-phase subagent executes via its Bash tool from the repo root
  (confirmed by Step 0's sibling `python3 tools/knowledge_search.py ...` line, which is a real,
  currently-working script invocation in the same prompt). Because it runs as a real subprocess with
  cwd = repo root, it can `sys.path.insert(0, 'tools')` and `from registry_query import
  candidate_tags_from_text, filter_registry` exactly like `tests/tools/test_generate_registry.py`
  does — no JS-to-Python bridging is needed, and no inlining of the matcher logic as a duplicate
  string is required.
- **Change:**
  1. In the prose line just above the snippet ("Query REGISTRY.yaml for entries in the relevant
     layers (...)"), add one clause noting the query now also unions in entries whose `tags` match
     candidate Subsystem/Topic tags derived from the concern's own text.
  2. Replace the embedded snippet with:
     ```python
     import sys, yaml
     sys.path.insert(0, 'tools')
     from registry_query import candidate_tags_from_text, filter_registry

     with open('docs/REGISTRY.yaml') as f:
         entries = yaml.safe_load(f)
     layers = ${JSON.stringify(registryLayers)}
     candidate_tags = candidate_tags_from_text(${JSON.stringify(concern.title)}, ${JSON.stringify(concern.description)}, ${JSON.stringify(concern.domain_area)})
     matches = filter_registry(entries, layers=layers, candidate_tags=candidate_tags)
     docs    = [e for e in matches if e.get('type') == 'doc']
     tickets = [e for e in matches if e.get('type') == 'ticket']
     print('candidate tags:', sorted(candidate_tags))
     print('=== DOCS ===')
     for e in docs[:20]:   print(e['path'], '-', e['title'])
     print('=== TICKETS ===')
     for e in tickets[:30]: print(e.get('ticket_id', e['path']), '-', e['title'])
     ```
     (`${JSON.stringify(...)}` matches the existing pattern already used for `registryLayers` two
     lines above — safe against embedded quotes/backticks in `concern.title`/`description`.)
- **Do NOT touch:** `DOMAIN_TO_LAYERS` (lines 262-284) or its lookup logic at lines 286-290 — the
  `layers` variable it produces is passed through unchanged, only consumed differently downstream.
  Do NOT touch the Structure phase (`TASK_SCHEMA`, ~441-460/583-597/712) — that is
  TCK-20260705-TAG-SKILL-SUGGEST's already-merged surface (git commit `16dd0241`), confirmed
  disjoint by investigation.md's `git show` check.
- **Verify:** No automated test exists for this file (confirmed in test_plan.md — no JS test runner
  wired to `.claude/`). Manual verify: run the Step 1 smoke-import command from a shell with
  `docs/REGISTRY.yaml` present, substituting a real `layers` list and sample title/description
  strings for the template placeholders, confirming the snippet runs without a Python exception and
  prints a `candidate tags:` line.

### Step 4: Update `.claude/agents/investigator.md`'s "Finding Prior Work" section
- **Files:** `.claude/agents/investigator.md` (lines 13-25 only)
- **Change:** Per the ticket's corrected Assumptions/Open Questions #2 (investigator.md has no
  existing `layer` dimension — only `related_code_areas`), add tags as a second dimension alongside
  `related_code_areas`, in both listed paths:
  1. **REGISTRY.yaml-preferred path** (item 1, line 18): reword to filter `type: ticket` entries
     where `related_code_areas` overlaps with the current ticket's Related Code Areas **OR** `tags`
     intersects candidate Subsystem/Topic tags derived from the current ticket's own title/summary
     (via the same seed-vocabulary substring match as `tools/registry_query.py` — reference the
     module by path so the two consumers stay conceptually in sync, even though this file is prose,
     not code that imports it).
  2. **Fallback path** (no `docs/REGISTRY.yaml`, lines 22-25): add one sentence noting that for
     promising name-matched candidates, also check whether the candidate ticket's own frontmatter
     `tags` overlap with candidate Subsystem/Topic tags for the current ticket — a lightweight
     supplementary check, not a new file-scan mechanism (this path has no registry to query, so it
     cannot replicate the exact `filter_registry` call — keep the wording as "also consider," not
     "query").
- **Do NOT touch:** the `## Output 1` / `## Output 2` structure sections, or anything below line 25 —
  edit surface is the "Finding Prior Work" subsection only.
- **Verify:** Manual read-through only (per test_plan item 4 — prose consistency cannot be pytest-
  enforced). Confirm the updated section is internally consistent that `investigator.md` supplements
  `related_code_areas`, while `create-tickets.js` supplements `layer` — do not let the two files'
  wording drift into implying the same baseline dimension.

### Step 5: Add a short note to `docs/guides/ticket_tagging.md`
- **Files:** `docs/guides/ticket_tagging.md`
- **Change:** Append a new short section (after "Skill Suggestions From Tags", before the closing
  cross-reference line) titled `## Tags as a Registry Search Filter`, 2-4 sentences: Subsystem/Topic
  tags are now also used as a second, cheap filter dimension when searching
  `docs/REGISTRY.yaml` for prior work — alongside `layer` in `create-tickets.js`'s Investigate phase
  and alongside `related_code_areas` in `investigator.md`'s "Finding Prior Work" step. Link to
  `tools/registry_query.py` (the seed-vocabulary matcher) and note the vocabulary is the same 10
  Subsystem/Topic words this guide's sibling doc (`docs/guidelines/tag_taxonomy.md`) names as
  examples — not a separate list.
- **Do NOT touch:** the existing "The 4 Categories" table or "Skill Suggestions From Tags" section —
  those are TCK-20260704-TAG-TAXONOMY's / TCK-20260705-TAG-SKILL-SUGGEST's delivered content.
- **Verify:** Manual read-through; confirm frontmatter (`tags: [tagging, taxonomy, skills]`) does not
  need a new tag for this addition (it already covers "tagging" and "taxonomy").

### Step 6: `docs/ai/agents.md` and `docs/ai/workflows.md` — materiality check
- **Files:** `docs/ai/agents.md` (investigator section, line ~55), `docs/ai/workflows.md`
  (create-tickets section, lines ~30-40) — conditionally.
- **Decision (made here, not left open):**
  - `docs/ai/agents.md`'s investigator bullet ("Searches `stored_artifacts/` and `tickets/done/` for
    prior work in the same area") is already coarse and doesn't name `related_code_areas` filtering
    explicitly today. Add one short clause: "...(including tag-based matches against
    `docs/REGISTRY.yaml`, per `docs/guides/ticket_tagging.md`)." One-line change, low risk.
  - `docs/ai/workflows.md`'s create-tickets phase table (Parse/Write/Link — note: this table doesn't
    even list "Investigate" as a phase name, and doesn't mention `layer` filtering at all today) is
    at a coarser level of abstraction than filter mechanics. Adding tag-filtering detail here would
    be disproportionate to the doc's existing granularity — **no edit** to this file under this
    ticket. (The Parse/Write/Link vs. actual Comprehend/Investigate/Structure/Write/Link phase-name
    mismatch predates this ticket and is not in scope to fix here.)
- **Do NOT touch:** anything else in either file.
- **Verify:** Manual read-through of the one-clause `agents.md` addition for accuracy.

### Step 7: Regression test run
- **Command 1 (required regression surface, per test_plan.md):**
  `pytest tests/tools/test_generate_registry.py tests/tools/test_validate_frontmatter.py tests/tools/test_knowledge_search.py -v`
- **Command 2 (new tests):**
  `pytest tests/tools/test_registry_query.py tests/tools/test_generate_registry.py -v`
- **Do NOT run:** `pytest tests/` (explicitly forbidden by test_plan.md).
- **Verify:** All tests pass. Record the exact commands and pass/fail counts in the ticket's Test
  Summary section.

## Scope Guards
- No edits to `tools/generate_registry.py` (read-only) under any step, including tempting
  "just add `layer` to `collect_tickets()`" fixes surfaced by Step 2's fixture design — that gap is
  explicitly deferred to a future ticket (see investigation.md Risk 2).
- No edits to `create-tickets.js`'s Structure phase (`TASK_SCHEMA`, ~441-460/583-597/712) —
  TCK-20260705-TAG-SKILL-SUGGEST's surface.
- No new frequency-mined tag vocabulary, no semantic/embedding matching anywhere in this ticket's
  code — `SEED_TAGS` is fixed to the 10 taxonomy-doc-named words only.
- No assertions against the live 1272-entry `docs/REGISTRY.yaml` in tests — fixtures only.
- No retroactive re-tagging of historical tickets/docs.
- No change to `mcp__knowledge-search__search_docs` or `tools/knowledge_search.py` (Step 0 of the
  Investigate prompt is untouched — this ticket only edits Step 2).

## Dependency Map
- Step 2 depends on Step 1 (imports the module it creates).
- Step 3 depends on Step 1 (imports `tools/registry_query` at runtime) but not on Step 2.
- Step 4 and Step 5 are independent of Steps 1-3 (prose-only) but should land in the same commit
  since they describe the same feature.
- Step 6 is independent, lowest priority, can be done last.
- Step 7 depends on Steps 1-2 (new test file must exist and pass) and should be run after all code
  changes (Steps 1-3) are complete.

## Acceptance Criteria Map

| Acceptance Criterion | Step(s) |
|---|---|
| AC1: `create-tickets.js`'s REGISTRY.yaml query filters by `tags` in addition to `layer`, unioning both | Step 1 (filter_registry), Step 3 (wiring) |
| AC2: `investigator.md` documents tag-based filtering as part of "Finding Prior Work" | Step 4 |
| AC3: Worked example (`faction` cross-layer) demonstrated | Step 2 (`test_faction_tag_query_surfaces_entries_layer_search_would_miss`) |
| AC4: No existing `layer`-only query behavior regresses | Step 2 (`test_registry_matches_union_layer_and_tags_not_intersection`, doc-entry layer-match case), Step 7 (full regression run incl. `test_generate_registry.py`) |

## Anti-Drift Notes
- The pre-existing `layer`-missing-on-tickets bug (investigation.md Current Behavior) is stated
  plainly here, not re-litigated: this ticket's tag filter is the *only* mechanism that will ever
  surface tickets through `create-tickets.js`'s REGISTRY.yaml query until a separate future ticket
  fixes `collect_tickets()`. Implementation Notes in the ticket should restate this so it isn't
  rediscovered as a surprise during Test or Review.
- `investigator.md` and `create-tickets.js` supplement *different* existing dimensions
  (`related_code_areas` vs. `layer` respectively) — keep that distinction explicit in both edits so
  reviewers don't flag it as an inconsistency.
- `docs/ai/workflows.md` is deliberately left unedited (Step 6) — this is a proportionality judgment
  made during planning, not an oversight; if Review disagrees, it's a one-line addition to reconsider,
  not a sign Step 6 was skipped.
- Two seed-vocabulary lists now conceptually exist (`docs/guidelines/tag_taxonomy.md`'s prose list
  and `tools/registry_query.py`'s `SEED_TAGS` tuple) — they must be kept in sync by hand since the
  module intentionally does not parse the doc at runtime (that would be over-engineering for a
  10-word list). Any future addition to one must be mirrored in the other; call this out in
  `registry_query.py`'s docstring (already planned in Step 1) so it's discoverable at the point of
  future edits.

## Unresolved Questions
None. The one open question flagged for Plan in investigation.md (candidate-tag derivation approach)
was resolved by adopting the investigation's own recommendation (seed vocabulary, substring match,
no frequency-mining). The wiring-mechanism question raised in this ticket's brief was resolved above
in Step 3 by direct inspection of `create-tickets.js`: the embedded snippet is a real subprocess
Python invocation, not LLM-interpreted prompt text, so a plain `import` is correct and sufficient.
