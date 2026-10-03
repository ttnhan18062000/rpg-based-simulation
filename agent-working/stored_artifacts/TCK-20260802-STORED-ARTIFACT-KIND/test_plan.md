---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260802-STORED-ARTIFACT-KIND
artifact_type: test_plan
tags: [ai, documentation, registry, frontmatter]
---

# Test Plan — TCK-20260802-STORED-ARTIFACT-KIND

## Regression Surface

This ticket is decision-document-only (no code changes to `tools/generate_registry.py`,
`tools/validate_frontmatter.py`, `tools/context_packet_assembler.py`, or
`tools/hybrid_retrieval.py`). The regression surface is therefore "prove nothing changed" rather
than "prove new logic works":

- Unit:
  - `tests/tools/test_generate_registry.py` — all classes, especially `TestArtifactJoin`
    (lines 190-223: `test_artifact_files_present`, `test_artifact_files_empty_when_no_folder`,
    `test_artifact_files_only_md`, `test_artifact_files_joined_into_ticket_entry`) and
    `TestDocEntryGeneration` (confirms `docs/` walk behavior is untouched).
  - `tests/tools/test_validate_frontmatter.py` (if present) or equivalent frontmatter-schema
    tests covering `ARTIFACT_TYPE_VALUES`, `_validate_artifact`, and `detect_content_type`.
  - `tests/tools/test_context_kind_priority_decision.py` — the sibling ticket's own static
    content-check test file for §5; must remain green and its `_EXPECTED_TOOLS_HASHES` fixture
    values must still match, since this ticket touches none of those four `tools/` files either.
- Integration:
  - `tests/tools/test_context_packet_assembler.py`, `tests/tools/test_hybrid_retrieval.py` —
    confirm the assembler/retrieval modules are untouched (no `kind` vocabulary or ranking logic
    added by this decision-only ticket).
- Architecture guard:
  - `python3 tools/generate_registry.py --check` against the live repo — must still report "in
    sync," confirming this ticket produced zero drift in `docs/REGISTRY.yaml`'s generation
    (expected: no doc/ticket entries change, since only an existing `docs/` file's *content*
    changes, not its frontmatter fields consumed by `collect_docs()`).
  - `python3 tools/validate_frontmatter.py docs/engine/contracts/context_packet_contract.md` —
    must still pass (frontmatter fields `status`/`layer`/`authority`/`audience` at the top of the
    file are unchanged by an append-only body edit).

There is no arena-combat surface — this ticket does not touch `src/` simulation code.

## New Tests Required

Per Acceptance Criteria (`tickets/inprogress/TCK-20260802-STORED-ARTIFACT-KIND.md`):

1. **`test_section_6_heading_exists_after_section_5`**
   - Category: unit (static content check)
   - Verifies: `## 6. Open Decision 8 Resolution` exists in
     `docs/engine/contracts/context_packet_contract.md` and appears after `## 5. Open Decision 7
     Resolution` (index comparison on raw text).
   - Location: `tests/tools/test_stored_artifact_kind_decision.py` (new file)

2. **`test_section_6_quotes_open_decision_8`**
   - Category: unit (static content check)
   - Verifies: §6 contains a verbatim (or clearly attributed) rendering of Open Decision 8's
     question text from the idea doc — the `stored_artifacts/{ticket_id}/*.md` /
     `stored_artifact` kind question and the `staging_artifacts/` exclusion question.
   - Location: `tests/tools/test_stored_artifact_kind_decision.py`

3. **`test_decision_doc_states_yes_or_no_on_new_kind_and_cites_join_artifact_files`**
   - Category: unit (static content check)
   - Verifies: §6 contains an explicit yes/no verdict on whether `stored_artifact` becomes a
     registry-indexed `kind`, and explicitly names `join_artifact_files()` /
     `generate_registry.py` as the status-quo behavior being evaluated (AC1).
   - Location: `tests/tools/test_stored_artifact_kind_decision.py`

4. **`test_decision_doc_picks_one_of_decision_3s_three_branches_with_reasoning`**
   - Category: unit (static content check)
   - Verifies: §6 names exactly one of Decision 3's three branch labels (e.g.
     "REGISTRY-backed direct mapping", "`unrated` sentinel", "differently-shaped-primitive
     mapping") as its answer, ties the reasoning to the real fields (`status`, `layer`,
     `authority`, `audience`, `ticket_id`, `artifact_type`), and does not introduce a fourth
     unnamed branch (AC2). Assert presence of the chosen branch's key phrase and absence of
     any invented alternative-branch language.
   - Location: `tests/tools/test_stored_artifact_kind_decision.py`

5. **`test_decision_doc_confirms_last_verified_absent_from_artifact_frontmatter`**
   - Category: unit (static content check)
   - Verifies: §6 explicitly states artifact frontmatter carries no `last_verified` field,
     consistent with the ticket's own Acceptance Criteria wording (AC2).
   - Location: `tests/tools/test_stored_artifact_kind_decision.py`

6. **`test_decision_doc_contains_staging_artifacts_exclusion_paragraph`**
   - Category: unit (static content check)
   - Verifies: §6 contains an explicit reasoned paragraph (not a bare assertion) addressing
     whether `staging_artifacts/`'s total exclusion from `generate_registry.py`'s scan is
     intentional permanent design or an accidental gap, and states a clear verdict word
     (e.g. "intentional"/"permanent design", not merely "excluded") (AC3).
   - Location: `tests/tools/test_stored_artifact_kind_decision.py`

7. **`test_context_packet_contract_sections_1_through_5_text_unchanged`**
   - Category: unit (static content check / architecture guard)
   - Verifies: byte-level presence of key load-bearing sentences from §1-§5 (mirroring
     `test_context_kind_priority_decision.py`'s own `test_context_packet_contract_section_3_text_unchanged`
     / `_section_4_text_unchanged` pattern), proving no in-place edit occurred to already-resolved
     text, extended to also cover §5 (the sibling ticket's own new section) since this ticket sits
     immediately after it.
   - Location: `tests/tools/test_stored_artifact_kind_decision.py`

8. **`test_no_code_changes_to_named_tools_modules`**
   - Category: architecture guard (content-hash fixture, same technique as the sibling ticket's
     `_EXPECTED_TOOLS_HASHES`)
   - Verifies: `tools/generate_registry.py`, `tools/validate_frontmatter.py`,
     `tools/context_packet_assembler.py`, `tools/hybrid_retrieval.py` are byte-identical to their
     pre-ticket content (sha256 fixture), proving AC4 ("No code changes ... Files Changed
     contains docs/ paths only").
   - Location: `tests/tools/test_stored_artifact_kind_decision.py`

## Scoped Pytest Commands

```
pytest tests/tools/test_generate_registry.py tests/tools/test_context_kind_priority_decision.py tests/tools/test_stored_artifact_kind_decision.py -v
pytest tests/tools/test_context_packet_assembler.py tests/tools/test_hybrid_retrieval.py -v
python3 tools/generate_registry.py --check
python3 tools/validate_frontmatter.py docs/engine/contracts/context_packet_contract.md
```

Never `pytest tests/` — scoped to `tests/tools/` (registry/frontmatter/context-packet domain)
plus the two direct tool invocations above for drift/frontmatter verification.

## Anti-Drift Test Guards

- The `_EXPECTED_TOOLS_HASHES`-style fixture (test 8 above) is the primary guard against silent
  scope creep into any of the four named `tools/` modules — a failure here means the ticket
  drifted from "decision-document-only" into an implementation change, which must be reported,
  not routed around.
- Test 7 (byte-preservation of §1-§5) guards against accidentally editing the sibling ticket's
  freshly-landed §5 text while inserting §6 immediately after it — the highest-risk mechanical
  mistake given the two tickets share the same file and adjacent section numbers.
- `python3 tools/generate_registry.py --check` guards against this ticket accidentally causing
  `docs/REGISTRY.yaml` drift — since this ticket only edits an existing `docs/` file's body
  (not its frontmatter `status`/`layer`/`authority`/`audience`), the check should report "in
  sync"; a drift result would indicate an unintended frontmatter change and must be investigated,
  not suppressed.
- `TestArtifactJoin` in `tests/tools/test_generate_registry.py` staying green guards against any
  accidental narrowing/widening of `join_artifact_files()`'s current flat-list-only behavior —
  this ticket's decision doc describes that behavior but the code implementing it must remain
  byte-identical (covered by test 8 above too).
