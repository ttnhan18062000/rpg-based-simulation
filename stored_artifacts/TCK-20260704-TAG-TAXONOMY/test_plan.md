---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260704-TAG-TAXONOMY
artifact_type: test_plan
tags: [tagging, taxonomy, frontmatter, registry, data-quality]
---

# Test Plan — TCK-20260704-TAG-TAXONOMY

## Regression Surface

**Existing test file**: `tests/tools/test_validate_frontmatter.py` (479 lines) is the sole test
file for `tools/validate_frontmatter.py`. Confirmed by running it in isolation this session:

```
python3 -m pytest tests/tools/test_validate_frontmatter.py -q
# 47 passed in 0.26s
```

It loads the module directly by file path (`importlib.util.spec_from_file_location`, `:35-37`,
since `tools/` is not a package) and is organized into 8 groups: (1) frontmatter detection,
(2) doc content type, (3) ticket content type, (4) artifact content type, (5) archive content
type, (6) directory scan mode, (7) exit-code contract via subprocess, (8) anti-drift enum
assertions (`TestEnumAntiDrift`, `:456-479` — exact-equality checks against every `*_VALUES`
constant, so any new `TAG_VALUES`/canonical-mapping constant this ticket adds must get its own
assertion here too, matching the existing pattern for `STATUS_VALUES`/`LAYER_VALUES`/etc.).

Two existing tests directly touch `tags` and must keep passing without modification (they use
free-form values today — `combat`, `ai` — which should remain valid under any reasonable
`subsystem/topic` taxonomy, but must be re-checked once the taxonomy is defined):
- `TestDocContentType.test_doc_tags_optional_present` (`:233-238`) — `tags: [combat, ai]` on a
  `doc`-type file must still pass.
- `TestDocContentType.test_doc_tags_optional_absent` (`:240-242`) — no `tags` key at all must
  still pass (tags remain optional; nothing in the ticket's AC asks for `tags` to become
  required).

**Related but out-of-scope tools** (confirmed not to require changes): `tools/add_frontmatter_tickets.py`'s
`extract_tags_from_ticket_id()` (`:71-93`, tested in `tests/tools/test_add_frontmatter_tickets.py:100-106`)
auto-derives free-text tags from ticket-ID words (e.g. `docsite`, `fm`, `tickets` from
`TCK-20260606-DOCSITE-FM-TICKETS`) for the one-time historical bulk-tagging migration. This is a
different, already-completed write path from `.claude/agents/ticket-scoper.md`'s live tag
authoring; the ticket's Out of Scope explicitly excludes backfilling history, so this function and
its tests are not touched and their current non-canonical output is expected to remain
unvalidated (it only ran once, historically).

**Confirmed pre-existing, unrelated failures** (full `tests/tools/` run, 253s, 30 failed / 416
passed) in `tests/tools/test_knowledge_search.py` and `tests/tools/test_search_mcp.py` — these
concern the MCP knowledge-search tool, not frontmatter/tags, predate this ticket, and are out of
scope. Do not attempt to fix them as part of this work; do not let a full `tests/tools/` run be
mistaken for a regression this ticket caused.

## New Tests Required (per AC)

All new tests belong in `tests/tools/test_validate_frontmatter.py`, following the existing
`_doc_fm()`/`_ticket_fm()`/`_artifact_fm()` builder-helper pattern (`:61-134`) and per-content-type
class grouping already used for `status`/`layer`/`authority`/`audience`/`phase`/`artifact_type`.

1. **AC: `docs/guidelines/tag_taxonomy.md` exists** — no unit test possible for doc existence
   alone; covered structurally by a `Path(...).exists()` smoke assertion if desired, but the real
   verification is the taxonomy doc itself being present and referenced by the validator (test #2
   below) and by `ticket-scoper.md` (test #5, a doc-content assertion, not a pytest test).

2. **AC: validator rejects/warns on non-canonical spelling when a canonical form exists** —
   new test class `TestTagCanonicalization` (or extend `TestTicketContentType` /
   `TestArtifactContentType` depending on how canonicalization is scoped):
   - `test_ticket_tag_canonical_form_accepted` — a ticket with `tags: [observability]` (or
     whatever the taxonomy names as canonical) passes with `validate_file(f) == []`.
   - `test_ticket_tag_noncanonical_synonym_rejected` — a ticket with `tags: [obs]` (a confirmed
     synonym from this investigation's corpus data) is rejected (or produces a warning, per
     whatever severity Plan decides) with an error message identifying the offending tag and, if
     the design supports it, suggesting the canonical replacement.
   - Repeat for at least one more confirmed pair from the corpus data (e.g. `cog` → `cognition`,
     or a `phase-N` vs `phaseN` pair) so the test isn't tied to a single hardcoded synonym.
   - Mirror onto `_validate_artifact` too, since artifacts carry `tags` and the ticket's Scope
     explicitly says `_validate_artifact` must also be extended.

3. **AC: validator rejects `p0`/`p1`/`p2` (any case) as a tag** — new test class
   `TestForbiddenPriorityTags`:
   - `test_ticket_forbidden_tag_p0_rejected`, `_p1_rejected`, `_p2_rejected` — tickets with
     `tags: [p0]`, `[p1]`, `[p2]` each rejected.
   - `test_ticket_forbidden_tag_uppercase_rejected` — `tags: [P0]`, `[P1]`, `[P2]` (uppercase
     variants) also rejected — case-insensitivity is essential here since the corpus data shows
     both cases in active use (`P0`: 2, `P1`: 7, `P2`: 4).
   - `test_ticket_tag_valid_when_no_priority_tag_present` — a ticket with a normal canonical tag
     list and no `p0`/`p1`/`p2` passes cleanly (negative control, avoid false-positive rejection).

4. **AC: new tests cover canonical acceptance, synonym rejection, forbidden-tag rejection** —
   satisfied jointly by tests #2 and #3 above; no additional dedicated test needed beyond ensuring
   all three categories (acceptance / synonym rejection / forbidden-tag rejection) have at least
   one passing test each, per the ticket's explicit wording.

5. **AC: `.claude/agents/ticket-scoper.md` references the taxonomy doc** — not a pytest-testable
   claim (it's an agent prompt file, not code). Verify by direct read/grep during implementation
   review: confirm `.claude/agents/ticket-scoper.md:28` (currently `tags: [<scope words from
   ticket ID, lowercase>]`, no taxonomy reference) is updated to point at
   `docs/guidelines/tag_taxonomy.md`. Record this verification step in the ticket's
   Implementation Notes / Test Summary rather than as a `pytest` assertion.

6. **AC: whole-directory invocation does not newly fail on tag grounds for historical tickets**
   — depends on resolving the open question in `investigation.md` (is `validate_frontmatter.py`
   ever invoked in `validate_directory()` mode against `tickets/`, and by what caller). Once
   resolved during Plan/Implementation, add either:
   - a regression test asserting `validate_directory(Path("tickets"))` (or a fixture subset of
     real historical ticket files with known non-canonical tags) produces **zero new tag-related
     errors**, if a grandfather/exemption mechanism is built; or
   - explicit documentation (no test needed) if the conclusion is that no code path invokes
     directory-mode validation against historical tickets in practice, making the guarantee
     structurally true rather than something to test.
   This AC cannot be finalized into a concrete test until that Plan-phase decision is made — flag
   as a placeholder in Implementation Notes if left unresolved when coding begins.

7. **AC: taxonomy category list checked against all five future scenarios** — not a pytest test;
   a Plan-phase documentation review checklist item (each of the 5 scenarios in
   `investigation.md`'s "Design Constraints from Future Usage Scenarios" section must name a
   taxonomy category). Record as a checklist in `docs/guidelines/tag_taxonomy.md` itself or in the
   ticket's Implementation Notes, not as automated test coverage.

## Scoped Pytest Commands

```
# Primary regression + new-test surface for this ticket
python3 -m pytest tests/tools/test_validate_frontmatter.py -v

# Confirm the unrelated bulk-tagging tool's tests are untouched (should remain green, unchanged)
python3 -m pytest tests/tools/test_add_frontmatter_tickets.py tests/tools/test_add_frontmatter_live.py tests/tools/test_add_frontmatter_archive.py -q

# Do NOT run the full tests/tools/ directory as a pass/fail gate for this ticket —
# tests/tools/test_knowledge_search.py and tests/tools/test_search_mcp.py have 30 pre-existing,
# unrelated failures (confirmed this session) that this ticket must not be blocked on or blamed for.
```

Do not run the full repository suite (`pytest tests/`) — out of scope per `CLAUDE.md`'s Testing
Rule; this change touches only `tools/validate_frontmatter.py`, `docs/guidelines/`,
`.claude/agents/ticket-scoper.md`, and their direct tests.

## Anti-Drift Test Guards

- **Mirror the `TestEnumAntiDrift` pattern** (`test_validate_frontmatter.py:456-479`): any new
  `TAG_VALUES`-equivalent constant or canonical-synonym mapping dict added to
  `validate_frontmatter.py` must get its own exact-equality assertion test in that class, the same
  way `STATUS_VALUES`/`LAYER_VALUES`/`AUTHORITY_VALUES`/`AUDIENCE_VALUES`/`ARTIFACT_TYPE_VALUES`/
  `PHASE_VALUES` already do — this is the repo's established guard against a constant silently
  drifting out of sync with its own test.
- **Do not let synonym-rejection tests hardcode only the ticket's example pairs** (`obs`/
  `observability`, `cog`/`cognition`) without also covering at least one `phase-N`/`phaseN` pair —
  the investigation found these are the highest-volume duplicate groups (`phase-5`/`phase5`:
  32/7; also confirmed non-singleton for `phase-1` through `phase-4`), so a taxonomy fix that only
  handles the `obs`/`cog` abbreviation case while leaving `phase-N` format inconsistency unfixed
  would technically satisfy a narrow reading of the AC while missing the majority of the actual
  corpus problem.
- **Do not assert exact error message text** in synonym/forbidden-tag rejection tests beyond
  checking the offending tag name and category appear in the message (matching the existing loose
  `"invalid value" in e` / `"missing" in e` substring-check convention already used throughout this
  test file, e.g. `:187`, `:207`) — tying tests to exact wording would make them brittle to
  message-copy iteration during implementation.
- **Do not silently change the two existing `tags`-touching tests'** (`test_doc_tags_optional_present`,
  `test_doc_tags_optional_absent`) **expected outcome from pass to fail** as a side effect of
  adding tag validation to `_validate_doc` — the ticket's Scope only calls out extending
  `_validate_ticket` and `_validate_artifact` explicitly; if `_validate_doc` also gains tag
  validation, `combat`/`ai` must already be canonical-taxonomy-valid subsystem tags, or these two
  pre-existing tests will need a deliberate, documented update (not an accidental break) — a
  break here means either the test needs updating in the same commit, or the taxonomy's
  `subsystem/topic` category is missing an entry that clearly should be in it.
- **Grandfather-clause test (if built) must use real corpus data, not a synthetic example** — if
  Plan decides a grandfather/exemption mechanism is needed for the historical-tickets AC, the
  regression test should exercise at least one real non-canonical tag pattern confirmed in this
  investigation (e.g. a ticket using `phase5` or `p2`), not an invented placeholder tag, so the
  test actually proves the historical corpus doesn't newly fail.
