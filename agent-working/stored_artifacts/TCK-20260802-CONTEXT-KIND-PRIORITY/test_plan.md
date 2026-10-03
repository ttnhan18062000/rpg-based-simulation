---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260802-CONTEXT-KIND-PRIORITY
artifact_type: test_plan
tags: [ai, documentation]
---

# Test Plan — TCK-20260802-CONTEXT-KIND-PRIORITY

This ticket's deliverable is a decision document (a new section/addendum to
`docs/engine/contracts/context_packet_contract.md`, plus an epic-ticket tracking update). No
`tools/context_packet_assembler.py`, `tools/hybrid_retrieval.py`, `tools/parity_index.py`, or
`tools/generate_registry.py` code changes are in scope (explicit Out of Scope). Accordingly this
plan has two parts: (1) the regression surface that must stay green because it is adjacent code
this ticket must not touch, and (2) new tests that verify the decision doc itself, plus the
frontmatter/format gates every doc change already goes through.

**Important finding (see investigation.md "Risks and Open Questions"):** there is no existing
precedent in this repo for a test file that asserts a `docs/ai/*_decision.md` (or a contract
addendum)'s required content. Decisions 1, 2, 5, and 6 — the four prior sibling decision tickets
in this same epic — all shipped without such a test. Grepping `tests/` for `_decision.md` /
`decision.md` finds only unrelated simulation-domain "decision service" tests (adventure/faction/
cooperation/progression phases), a naming coincidence, not the pattern this ticket's briefing
speculated might exist. This plan therefore proposes a **new** lightweight content-assertion test
as an optional strengthening, but does not treat it as required-by-precedent, since the precedent
does not exist. The Plan phase should make an explicit call on whether to add it.

## Regression Surface

Existing tests that must keep passing (all adjacent to but untouched by this ticket's scope —
run to confirm no accidental drift, since the decision doc will directly quote/cite these
modules' current line numbers and behavior):

**Unit — context packet / retrieval tooling:**
- `tests/tools/test_context_packet_assembler.py` — especially `TestConflictResolution` (same-
  `subject_key` authority-then-recency tie-break) and `TestParityLedgerEntryAdapter`
  (`parity_ledger_entry` kind's own `priority`/`status` passthrough) — these are the exact
  functions the decision doc cites as same-kind precedent; if their behavior has drifted since
  this investigation read them, the decision doc's citations would be stale on arrival.
- `tests/tools/test_hybrid_retrieval.py` — `reciprocal_rank_fusion()`/`filter_candidates()`
  single-corpus behavior, cited in the decision doc as confirmed non-cross-kind.
- `tests/tools/test_parity_ledger_scan.py` — parity/doc-path intersection helper, adjacent to
  `parity_index.py`.

**Integration / architecture guard — frontmatter and registry:**
- `tests/tools/test_add_frontmatter_live.py` (or whatever suite exercises
  `tools/validate_frontmatter.py` directly) — the new decision-doc section's frontmatter (if a
  new file is added) or the existing `context_packet_contract.md` frontmatter (if only a new
  section is appended in place) must still pass `validate_frontmatter.py`'s enum checks
  (`STATUS_VALUES`, `AUTHORITY_VALUES`, `ARTIFACT_TYPE_VALUES` — confirmed at
  `tools/validate_frontmatter.py:44,54,57`).
- `tests/tools/test_doc_staleness_check.py` / `tests/tools/test_parity_ledger_scan.py` — both
  already parametrize on `docs/ai/*.md` paths as generic fixtures; confirm neither breaks if a
  new `docs/ai/*_decision.md` file is added (only relevant if the Plan phase chooses that layout
  over a contract-only addendum).

**No arena-combat / simulation-domain regression surface applies** — this ticket touches no
`src/` code and no Mechanics Bible chapter.

## New Tests Required

Per Acceptance Criteria (`tickets/inprogress/TCK-20260802-CONTEXT-KIND-PRIORITY.md`):

1. **AC1 — cites `_resolve_subject_conflicts()` and explains generalization.**
   - Test name: `test_decision_doc_cites_resolve_subject_conflicts_precedent`
   - Category: architecture guard (static content check, following
     `tests/tools/test_shadow_packet_call_site.py`'s Path.read_text()-only technique, per
     `docs/plans/.../idea_...md`'s established convention for doc-content assertions)
   - What it verifies: the decision doc's text contains the literal string
     `_resolve_subject_conflicts` and, near it, prose addressing why it does/does not generalize
     cross-kind (e.g. assert the doc's raw text also contains a marker phrase like
     `subject_key` and `freshness` together with either `structurally` or `does not generalize`
     or `same-kind` — a soft content-presence check, not an NLP judgment).
   - Where it lives: `tests/tools/test_context_kind_priority_decision.py` (new file, if the Plan
     phase decides to add doc-content tests at all — see note above).

2. **AC2 — explicit position on both concrete examples.**
   - Test name: `test_decision_doc_addresses_unrated_code_symbol_vs_p1_doc_example`
   - Category: architecture guard (static content check)
   - What it verifies: the doc's text contains both `code_symbol` and `P1` in reasonable
     proximity to an explicit stance (assert absence of a hedge-only non-answer by checking a
     stance keyword is present, e.g. `outrank`, `never`, `always`, or `case-by-case` — whichever
     the resolution actually lands on).
   - Where it lives: same new file as above.
   - Test name: `test_decision_doc_addresses_p0_parity_entry_inclusion_floor`
   - Category: architecture guard (static content check)
   - What it verifies: the doc's text contains `parity_ledger_entry`, `P0`, and `inclusion` (or
     `floor`) together, and takes an explicit yes/no/deferred stance rather than only restating
     the question.
   - Where it lives: same new file as above.

3. **AC3 — plain human-sign-off statement if genuinely a value judgment.**
   - Test name: `test_decision_doc_states_human_signoff_needed_if_value_judgment` (conditional —
     only meaningful if the Plan/Implement phase actually lands on a "needs sign-off" outcome for
     part or all of the ordering; if the doc resolves everything as a technical derivation, this
     test should instead assert the *absence* of an unresolved value-judgment claim, to prevent
     future silent softening of a decision back into a punt without updating the test).
   - Category: architecture guard (static content check)
   - What it verifies: presence (or confirmed absence, per whichever the doc actually claims) of
     an explicit phrase such as `needs explicit human sign-off` / `human sign-off required`.
   - Where it lives: same new file as above.

4. **AC4 — no code changes; §3 not edited in place.**
   - Test name: `test_no_code_changes_to_named_tools_modules`
   - Category: architecture guard (git-diff-shaped check, following the pattern of
     `tests/tools/test_shadow_packet_call_site.py`'s `TestWorkflowIsolationGuards` static-source
     scanning, adapted to check file modification rather than import graphs)
   - What it verifies: `tools/context_packet_assembler.py`, `tools/hybrid_retrieval.py`,
     `tools/parity_index.py`, `tools/generate_registry.py` are byte-identical to their
     pre-ticket state (e.g. via `git diff --stat` against the base commit, or a stored hash
     fixture) — a CI-time check, but worth stating explicitly as a done-checker-adjacent guard
     even if implemented as a one-off verification rather than a permanent pytest test, since
     this constraint is scoped to this one ticket, not a durable invariant.
   - Test name: `test_context_packet_contract_section_3_text_unchanged`
   - Category: architecture guard (static content check)
   - What it verifies: the exact text of `context_packet_contract.md` §3 (line range ~102-179 as
     read during investigation) is unchanged — e.g. hash the section's text between the `## 3.`
     and `## 4.` headings and compare against a recorded pre-ticket hash, or simpler: assert the
     specific known sentences from §3 (e.g. "must never imply otherwise by, for example,
     defaulting to P2/historical") are still present verbatim, proving no in-place edit occurred.
   - Where it lives: same new file as above, or inline as a quick diff-based assertion run once
     during Verify rather than a permanent pytest addition — Plan phase should decide which.

**If the Plan phase decides against adding a new test file** (defensible, since no precedent
requires it — see note above), the equivalent verification should still happen manually during
Verify: read the produced decision doc against each Acceptance Criterion bullet, and run
`git diff --stat` to confirm only doc files changed.

## Scoped Pytest Commands

```
pytest tests/tools/test_context_packet_assembler.py tests/tools/test_hybrid_retrieval.py tests/tools/test_parity_ledger_scan.py -v
```

If a new `tests/tools/test_context_kind_priority_decision.py` is added:

```
pytest tests/tools/test_context_kind_priority_decision.py -v
```

Frontmatter/registry validation (only if a new `docs/ai/*.md` file is added, or if
`context_packet_contract.md`'s frontmatter is touched at all):

```
python3 tools/validate_frontmatter.py docs/engine/contracts/context_packet_contract.md
```

(Do not run `pytest tests/` — scope stays confined to the tools/context-packet domain and the
frontmatter validator, per project testing rule.)

## Anti-Drift Test Guards

- The `test_context_packet_contract_section_3_text_unchanged`-style check above is itself the
  primary anti-drift guard for this ticket: it directly encodes the Out-of-Scope line "§3's
  resolved text is not edited in place" as a check that can catch an accidental edit even if the
  diff is reviewed casually.
- `test_no_code_changes_to_named_tools_modules` (or the manual `git diff --stat` equivalent)
  guards against the exact temptation flagged in investigation.md's Anti-Drift Hazards: the
  absence of any existing selection/ranking code in `context_packet_assembler.py` might tempt an
  implementer to add "just a small ranking helper" to make the decision doc feel more concrete —
  this guard makes that drift immediately visible.
- Re-running `tests/tools/test_context_packet_assembler.py::TestConflictResolution` and
  `TestParityLedgerEntryAdapter` after the doc lands (even though no code changed) confirms the
  decision doc's citations of these tests' exact behavior have not silently gone stale between
  investigation and doc-writing — a docs-only ticket can still drift if the underlying code was
  touched by an unrelated concurrent change.
- If the decision doc asserts "`_resolve_subject_conflicts()` cannot structurally fire cross-kind
  because freshness vocabularies never intersect," a guard test could assert this fact directly
  against the live enums (`_CONFLICT_ELIGIBLE_FRESHNESS` from `context_packet_assembler.py` vs.
  the parity ledger's `status` values from `docs/parity_ledger/schema.json`) rather than only
  against static doc text — this would catch the day someone widens
  `_CONFLICT_ELIGIBLE_FRESHNESS` or the parity schema's `status` enum and silently invalidates the
  decision doc's stated technical basis. Recommended as a stronger, code-grounded version of test
  #1 above if the Plan phase wants extra durability; not required for AC coverage.
