---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260705-TAG-REGISTRY-QUERY
artifact_type: test_plan
tags: [tagging, taxonomy, registry, investigator]
---

# Test Plan — TCK-20260705-TAG-REGISTRY-QUERY

## Regression Surface

There is **no existing automated test coverage** for either edit surface named in this ticket's
scope:
- `.claude/workflows/create-tickets.js` — a Claude-Code workflow orchestration script (JS,
  interpreted by the internal workflow runtime, not Node/Jest). Confirmed: no `package.json` at repo
  root wires a JS test runner (`jest`/`vitest`/`mocha`) against `.claude/workflows/*.js`, and no
  `*.test.js` files exist under `.claude/`.
- `.claude/agents/investigator.md` — a markdown system-prompt file, not executable code.

The only genuinely regression-testable artifact adjacent to this change is:
- `tests/tools/test_generate_registry.py` — unit tests `collect_docs()` / `collect_tickets()` /
  `sort_entries()` / `generate_registry()`. This ticket's scope explicitly marks
  `tools/generate_registry.py` **read-only**, so these tests are regression surface to keep green,
  not a target for new assertions from this ticket's own scope. (See Anti-Drift Test Guards below
  for why a *separate* ticket, not this one, should add a `test_ticket_entry_has_layer_field` case.)

Group-by-domain for the scoped pytest command:
- unit: `tests/tools/test_generate_registry.py` (registry entry shape — must not regress)
- unit: `tests/tools/test_validate_frontmatter.py` (frontmatter tag validation — this ticket must not
  touch `tools/validate_frontmatter.py`, but the taxonomy's forward-only enforcement interacts with
  any new frontmatter this ticket's own artifacts carry, so keep green)
- unit: `tests/tools/test_knowledge_search.py` (confirms `search_docs`/`knowledge_search.py` remains
  untouched — Out of Scope explicitly forbids modifying semantic search)

## New Tests Required

Because the two edit targets are a `.js` prompt-template string and a `.md` agent-instruction file,
neither supports conventional unit tests today. Recommend the following, ordered by how directly they
verify the Acceptance Criteria:

1. **Extract the candidate-tag-derivation logic into a small, importable, pure Python function**
   (recommended new module, e.g. `tools/registry_query.py`, or a new function added to
   `tools/generate_registry.py` if Plan prefers colocating it with the schema it reads — Plan's call,
   not decided here) rather than leaving it only as an inline string inside the `create-tickets.js`
   prompt. This is the single highest-leverage recommendation in this test plan: without it, **none**
   of this ticket's core logic (seed-tag matching, union-with-layer-results) is unit-testable at all,
   and the only verification path is manually re-running the workflow end-to-end.
   - Test name: `test_candidate_tags_from_seed_vocabulary_matches_substring`
   - Category: unit
   - Verifies: given free text containing `"faction"` (case-insensitive, anywhere in
     title+description+domain_area), the seed-vocabulary matcher returns `{"faction"}` (or a superset
     if multiple seed words appear); given text with no seed-word substrings, returns `set()`.
   - Location: `tests/tools/test_registry_query.py` (new file) or
     `tests/tools/test_generate_registry.py` (new test class), matching wherever the extracted
     function lives.

2. **Union-filter correctness** (the core AC1/AC4 behavior):
   - Test name: `test_registry_matches_union_layer_and_tags_not_intersection`
   - Category: unit
   - Verifies: given a fixture registry with (a) one ticket entry matching by `layer` only [not
     applicable today per the Current-Behavior finding that no ticket ever carries a `layer` key —
     so construct this case using a **doc** entry, since only docs currently have `layer`], (b) one
     ticket entry matching by `tags` only, (c) one entry matching neither — the union result includes
     (a) and (b) but not (c), and matching by tags alone (with no layer match) still returns a result
     (this is the specific regression AC1 protects against: "a `tags`-only match should now
     additionally surface").
   - Location: same new/extended test file as #1.

3. **`faction` cross-layer worked example** (AC3's explicit acceptance criterion — "a topic that
   spans multiple `layer` values ... found in one query where it previously required checking
   multiple layers"):
   - Test name: `test_faction_tag_query_surfaces_entries_layer_search_would_miss`
   - Category: unit (using a small fixture registry, not the live 1272-entry one, for determinism)
     — construct ≥2 doc/ticket entries tagged `faction` with **different** `layer` values (e.g. one
     `layer: ai`, one `layer: social`) plus one entry with `layer: ai` but no `faction` tag. Query
     with `layers=['ai']` only (simulating today's pre-fix, single-layer-guess call) and confirm it
     misses the `social`-layer `faction` entry; then query with the tag-augmented function and
     confirm both `faction`-tagged entries surface regardless of `layers` passed.
   - This directly demonstrates the "no NLP layer" claim quantitatively (deterministic fixture, not a
     description) rather than repeating the ticket's own AC3 language as a comment.
   - Location: same file as #1/#2.

4. **Documentation-level check (not pytest, but should be verified manually before closing):**
   confirm `.claude/agents/investigator.md`'s updated "Finding Prior Work" section is internally
   consistent about *which* dimension tags supplement — `related_code_areas` for investigator.md,
   `layer` for create-tickets.js (per the Current Behavior finding these are not the same baseline
   dimension in the two files). A test cannot enforce prose consistency; this is a manual
   read-through gate before Verify phase, called out here so it isn't silently skipped.

## Scoped Pytest Commands

```
pytest tests/tools/test_generate_registry.py tests/tools/test_validate_frontmatter.py tests/tools/test_knowledge_search.py -v
```

If a new `tests/tools/test_registry_query.py` is created per "New Tests Required" above:

```
pytest tests/tools/test_registry_query.py tests/tools/test_generate_registry.py -v
```

Never: `pytest tests/`.

## Anti-Drift Test Guards

- **Do not let this ticket's test suite silently "fix" the missing `layer` key on ticket entries.**
  A naive implementer might notice `test_registry_matches_union_layer_and_tags_not_intersection`
  needs a layer-matching ticket fixture and be tempted to add `layer` to
  `tools/generate_registry.py`'s `collect_tickets()` to make the fixture "realistic." That change is
  explicitly out of this ticket's Related Code Areas (marked read-only) — construct the layer-match
  fixture case using a **doc** entry instead (docs already carry `layer` today), and leave a comment
  in the test explaining why (cross-reference this investigation's Current Behavior section). A
  follow-on ticket, not this one, should add `test_ticket_entry_has_layer_field` to
  `tests/tools/test_generate_registry.py` and fix `collect_tickets()` if that gap is ever closed.
- **Do not add assertions against the live 1272-entry `docs/REGISTRY.yaml`.** All new tests must use
  small, deterministic, hand-built fixture registries (in-memory dicts or `tmp_path`-based, following
  `tests/tools/test_generate_registry.py`'s existing `_make_doc`/`_make_ticket` fixture pattern) — the
  live registry regenerates on every `make docs-registry` run and is not a stable test fixture.
- **Do not test candidate-tag derivation against the full 1367-tag historical corpus.** Test only
  against the small seed vocabulary this ticket's Plan phase adopts (recommended: the 10 words named
  in `docs/guidelines/tag_taxonomy.md`'s Subsystem/Topic section) — asserting behavior against
  today's full historical tag set would make the test brittle to future corpus growth and would
  encode "whatever tags happen to exist today" as spec, which is exactly what
  `docs/guidelines/tag_taxonomy.md` and this ticket's own Out-of-Scope section reject.
- **Do not assert exact match counts against `related_code_areas` for tickets in fixture data.** As
  flagged in the investigation, real `related_code_areas` entries are sometimes non-path tokens
  (e.g. `['tid', 'batchRunId']` in one live entry) — if any new test constructs
  `related_code_areas`-based fixtures, keep them independent of the tag-filter tests (this ticket
  does not change `related_code_areas` matching semantics, only adds a tag dimension alongside it in
  `investigator.md`'s prose).
