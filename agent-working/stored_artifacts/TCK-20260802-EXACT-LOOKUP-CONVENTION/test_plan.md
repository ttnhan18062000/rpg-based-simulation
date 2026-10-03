---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260802-EXACT-LOOKUP-CONVENTION
artifact_type: test_plan
tags: [ai, documentation]
---

# Test Plan — TCK-20260802-EXACT-LOOKUP-CONVENTION

## Regression Surface

This is a documentation-only ticket (no code changes to `tools/parity_index.py`,
`tools/hybrid_retrieval.py`, `tools/context_packet_assembler.py`, or
`tools/generate_registry.py` are permitted). The regression surface exists to *prove* that
constraint held, and that the two sibling additive sections (§5, §6) are unaffected by this
ticket's own §7 append.

**Unit / static-content (existing, must stay green, unmodified):**
- `tests/tools/test_parity_index.py` — full file, all 13 test groups, especially
  `TestArchitectureGuards` (`:513-546`, forbids `search` subcommand / any mutation path into
  `docs/parity_ledger`) and `TestImpactQuery::test_impact_never_claims_symbol_level_match`
  (`:697-724`, the explicit-warning-not-silent-overclaim behavior this ticket's investigation
  cites as evidence).
- `tests/tools/test_hybrid_retrieval.py` — full file (the fuzzy-path counterpart; must remain
  unmodified and green, confirming this ticket touched no fusion logic).
- `tests/tools/test_context_kind_priority_decision.py` — sibling Decision 7 test file; its own
  §1-§5 byte-identity/hash-fixture assertions must still pass after this ticket appends §7,
  proving §5 itself was untouched.
- `tests/tools/test_stored_artifact_kind_decision.py` — sibling Decision 8 test file; same
  byte-identity requirement for §6.
- `tests/tools/test_gate_a_readpath_review.py` — reproduces the Gate A GO-verdict numbers this
  investigation cites as evidence; asserts `tools/parity_index.py` byte-identity throughout its
  own run. Must stay green to confirm the cited evidence is still reproducible and the module
  is still untouched.

**Frontmatter / registry validation:**
- `python3 tools/validate_frontmatter.py docs/engine/contracts/context_packet_contract.md`
- `python3 tools/validate_frontmatter.py tickets/inprogress/TCK-20260802-EXACT-LOOKUP-CONVENTION.md`
  (and again on the ticket once moved to `tickets/done/`)
- `python3 tools/generate_registry.py --check` (confirm registry stays in sync after the doc
  edit; no drift expected since only a new section is appended, not a new file).

## New Tests Required

Per Acceptance Criteria, add one new test file,
`tests/tools/test_exact_lookup_convention_decision.py`, following the established static
content-check pattern (`Path.read_text()` assertions, no importable ranking/lookup logic
exists to exercise — mirrors `tests/tools/test_context_kind_priority_decision.py` and
`tests/tools/test_stored_artifact_kind_decision.py`).

1. **`test_section_7_appears_after_section_6`**
   - Category: unit (static content)
   - Verifies: `## 7. Open Decision 9 Resolution` appears in
     `docs/engine/contracts/context_packet_contract.md` after `## 6. Open Decision 8
     Resolution`'s content, i.e. correct append position and heading level.
   - Lives in: `tests/tools/test_exact_lookup_convention_decision.py`

2. **`test_section_7_quotes_open_decision_9_verbatim`**
   - Category: unit (static content)
   - Verifies: the new §7 quotes (verbatim or via the established normalized-whitespace
     blockquote-safe comparison technique from `TCK-20260802-STORED-ARTIFACT-KIND`'s
     `_normalize_whitespace()` fix) Open Decision 9's question text from
     `idea_context_efficient_agent_retrieval_observability.md` item 9 (lines 351-357) —
     confirms the resolution answers the actual question asked, not a paraphrase drift.
   - Lives in: `tests/tools/test_exact_lookup_convention_decision.py`

3. **`test_section_7_states_explicit_yes_or_no_verdict`** (AC1)
   - Category: unit (static content)
   - Verifies: §7 contains an unambiguous verdict marker (e.g. a literal "**Core
     resolution.**" line, matching §3/§5/§6's own convention, immediately followed by a
     yes/no-shaped sentence) — not a hedge-only paragraph with no stated conclusion.
   - Lives in: `tests/tools/test_exact_lookup_convention_decision.py`

4. **`test_section_7_cites_real_precedent_by_function_name`** (AC2, both yes/no branches)
   - Category: unit (static content)
   - Verifies: §7's text references the real precedent by name — `entry(`, `impact(`,
     `health(` (or their qualified forms) from `tools/parity_index.py`, and
     `reciprocal_rank_fusion`/`hybrid_fuse_and_filter` from `tools/hybrid_retrieval.py` —
     regardless of which verdict was reached, so the decision is grounded in the actual code,
     not an abstract restatement of the ticket prompt.
   - Lives in: `tests/tools/test_exact_lookup_convention_decision.py`

5. **`test_section_7_applicability_criteria_present_if_yes_verdict`** (AC2, conditional)
   - Category: unit (static content)
   - Verifies: *if* the verdict is "yes," §7 contains a clearly-delimited
     applicability-criteria subsection (e.g. a `###`-level heading) distinct from the verdict
     statement itself — not folded unlabeled into prose. This test should be written to only
     assert this when the yes-branch marker from test 3 is present (skip/xfail gracefully
     otherwise), since the ticket's own AC is conditional on which verdict is chosen.
   - Lives in: `tests/tools/test_exact_lookup_convention_decision.py`

6. **`test_section_7_states_parity_specific_rationale_if_no_verdict`** (AC3, conditional)
   - Category: unit (static content)
   - Verifies: *if* the verdict is "no," §7 explicitly states the rationale for staying
     parity-specific pending a second real use case (e.g. contains language equivalent to
     "second real use case" / "n=1" / "rule of three" reasoning) — not just a bare "no" with no
     justification.
   - Lives in: `tests/tools/test_exact_lookup_convention_decision.py`

7. **`test_section_7_flags_human_sign_off_if_value_judgment`** (AC4)
   - Category: unit (static content)
   - Verifies: §7 contains the literal phrases `human sign-off` and `value judgment` (matching
     the exact phrasing convention `test_context_kind_priority_decision.py` already checks for
     §5's own deferred residual question) — confirms the doc does not present a self-chosen
     answer as objectively settled if the underlying investigation determined it is a genuine
     value call.
   - Lives in: `tests/tools/test_exact_lookup_convention_decision.py`

8. **`test_sections_1_through_6_untouched_by_section_7_append`** (AC5, part 1)
   - Category: architecture guard (byte-content / anti-drift)
   - Verifies: key load-bearing sentences from §1-§6 (e.g. §3's "must never imply otherwise,"
     §5's "human sign-off required," §6's "intentional permanent design") are still present
     verbatim in the file, proving the append did not silently mutate existing sections.
   - Lives in: `tests/tools/test_exact_lookup_convention_decision.py`

9. **`test_no_code_changes_to_named_tools_modules`** (AC5, part 2)
   - Category: architecture guard (anti-drift, hash fixture)
   - Verifies: sha256 hashes of `tools/parity_index.py`, `tools/hybrid_retrieval.py`,
     `tools/context_packet_assembler.py`, and `tools/generate_registry.py` match pre-ticket
     recorded fixture values — mirrors the identical guard already present in both sibling
     test files for their own four-module list.
   - Lives in: `tests/tools/test_exact_lookup_convention_decision.py`

10. **`test_epic_ticket_decision_9_marked_resolved`**
    - Category: unit (static content)
    - Verifies: `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`'s `OPEN
      DECISION 9` bullet (currently `**UNRESOLVED**` at line 205) is updated to `**RESOLVED**`
      with a citation to the new §7, and that Decisions 1-8's own entries are untouched —
      mirrors the epic-ticket-update guard pattern from the two prior sibling tickets.
    - Lives in: `tests/tools/test_exact_lookup_convention_decision.py`

## Scoped Pytest Commands

```
pytest tests/tools/test_parity_index.py tests/tools/test_hybrid_retrieval.py \
       tests/tools/test_context_kind_priority_decision.py \
       tests/tools/test_stored_artifact_kind_decision.py \
       tests/tools/test_exact_lookup_convention_decision.py -v
```

```
pytest tests/tools/test_gate_a_readpath_review.py -v
```

```
python3 tools/validate_frontmatter.py docs/engine/contracts/context_packet_contract.md
python3 tools/generate_registry.py --check
```

Never `pytest tests/` — scope stays within `tests/tools/` for this documentation-only,
`tools/`-adjacent ticket.

## Anti-Drift Test Guards

- **Search-subcommand guard** (`test_parity_index.py::TestArchitectureGuards::
  test_impact_entry_health_still_forbid_search_cli`) — catches any attempt, in this ticket or
  a future one citing it, to "prove" the exact-lookup convention by actually building a second
  lookup surface inside `parity_index.py` itself. Must stay green untouched.
- **Mutation-path guard** (`test_parity_index.py::TestArchitectureGuards::
  test_no_mutation_cli_or_write_path_to_docs_parity_ledger`) — same anti-scope-creep purpose,
  applied to the write side.
- **Byte-identity guards on the four named `tools/` modules** (new test 9 above, plus the
  identical pre-existing guards in the two sibling decision test files) — the single strongest
  anti-drift signal for a ticket whose entire Out-of-Scope is "no code changes." Any diff to
  `parity_index.py`, `hybrid_retrieval.py`, `context_packet_assembler.py`, or
  `generate_registry.py` fails immediately and unambiguously, independent of what the doc text
  says.
- **§1-§6 preservation guard** (new test 8 above) — catches accidental renumbering, heading-level
  drift, or in-place editing of the already-resolved sections, the same class of regression the
  two sibling tickets each guarded against for their own predecessor sections.
- **Epic-ticket scope guard** (new test 10 above) — confirms only the Decision 9 bullet in the
  epic ticket changes, not Decisions 1-8's entries, matching the sibling tickets' own verified
  `git diff` scope (e.g. `TCK-20260802-CONTEXT-KIND-PRIORITY`'s Implementation Notes: "Only this
  one entry was touched; entries 1-6, 8, and 9 are untouched").
