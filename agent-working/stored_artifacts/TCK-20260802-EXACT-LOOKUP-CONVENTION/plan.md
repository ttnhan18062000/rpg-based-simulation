---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260802-EXACT-LOOKUP-CONVENTION
artifact_type: plan
tags: [ai, documentation]
---

# Implementation Plan — TCK-20260802-EXACT-LOOKUP-CONVENTION

## Summary

This ticket appends a single new `## 7. Open Decision 9 Resolution` section to
`docs/engine/contracts/context_packet_contract.md`, updates the epic ticket's OPEN DECISION 9
tracking entry to RESOLVED citing that section, adds one new static-content test file mirroring
the two closed sibling tickets' pattern, and runs the scoped regression pass. The one substantive
open point — whether §7's verdict is "yes, name a general convention now" or "no, stay
parity-specific pending a second real use case" — was a genuine value judgment investigation
explicitly could not resolve from repo evidence alone. During planning, both framings were fully
drafted as a fork so implementation could proceed the moment a human decided; the human reviewer
has since been asked and explicitly chose "no, stay parity-specific for now" (see "Decisions Made
During Human Review" below). Step 2 is therefore now written as a single committed decision: the
pattern's generalizable properties (read-only, deterministic, explicit no-match, no similarity
ranking) are documented as a citable, non-mandatory reference, not declared a mandatory convention,
with an explicit reopening condition. The rejected "yes, adopt now" draft is preserved verbatim in
"Rejected Alternative — Branch A (Not Chosen)" below, in case a future ticket revisits this once a
second kind genuinely needs a gate-safe exact lookup. No code in `tools/parity_index.py`,
`tools/hybrid_retrieval.py`, `tools/context_packet_assembler.py`, or `tools/generate_registry.py`
is touched at any step, and §1-§6 of the contract doc are read-only throughout.

## Steps

### Step 1 — Draft §7 shared scaffolding (verdict-independent)

**Files:** `docs/engine/contracts/context_packet_contract.md`

**Change:** Append a new section after the existing `## 6. Open Decision 8 Resolution` (which
ends the file today), separated by a `---` divider, matching §5/§6's own divider convention.
Write the verdict-independent scaffolding first — this text is identical regardless of which way
Step 2 ultimately resolves:

1. Heading: `## 7. Open Decision 9 Resolution`
2. A verbatim blockquote of Open Decision 9's question text, sourced from
   `docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`
   item 9 (confirmed at lines 351-357 of that file as read during Investigate):
   > `tools/parity_index.py`'s `entry()`/`impact()`/`health()` functions establish a
   > deterministic, exact-structural-lookup query pattern (never similarity-ranked, always
   > gate-safe, explicitly distinct from the fuzzy RRF-fused `search`/`tools/hybrid_retrieval.py`
   > path) for the `parity_ledger_entry` kind specifically. Should this exact-vs-fuzzy
   > retrieval-type split be documented as a general project convention that any future `kind`
   > needing gate-safe lookups should follow, rather than remaining an implicit, parity-specific
   > pattern?
3. A "real precedent" paragraph, present regardless of verdict, that names the actual code on
   both sides of the split by symbol so AC2's "grounded in real precedent" requirement is met
   independent of which branch is chosen:
   - Exact-lookup side: `entry()` (`tools/parity_index.py:485-531`, exact primary-key lookup,
     typed `{"found": False}` no-match shape), `impact()` (`:534-593`, exact path-equality
     lookup, `{"status": "no_filter_provided"}` / `{"status": "no_match"}` distinguished states,
     deterministic `(_PRIORITY_ORDER, _STATUS_SEVERITY, entry_id)` sort — never similarity
     score), `health()` (`:596-643`, exact equality filters, deterministic `ORDER BY`, no
     ranking field at all), all behind `_connect_readonly()`'s `mode=ro` URI connection
     (`:87-92`).
   - Fuzzy side: `reciprocal_rank_fusion()` (`tools/hybrid_retrieval.py:59-77`, literal RRF
     score) and `hybrid_fuse_and_filter()` (`:224-331`, dense+lexical union, fused-score
     ordering).
   - State plainly, as investigation found: the Gate A GO verdict
     (`docs/ai/parity_readpath_gate_a_decision.md`, 66.7% vs. 4.8% recall) is evidence about
     *parity-domain retrieval quality*, not evidence about *pattern generalizability* to a
     different `kind` — these are two different claims and §7 must not conflate them.

**Do NOT touch:** `## 1` through `## 6` of the same file — no edits, no renumbering, no heading
level changes. Do not add a `---` divider inside §1-§6.

**Verify:** `test_section_7_appears_after_section_6`, `test_section_7_quotes_open_decision_9_verbatim`,
`test_section_7_cites_real_precedent_by_function_name`.

---

### Step 2 — Write the verdict (resolved: stay parity-specific, no general convention yet)

**Files:** `docs/engine/contracts/context_packet_contract.md` (continuing directly after Step 1's
scaffolding, same section, no new heading)

**Change:** Immediately following Step 1's precedent paragraph, add a `**Core resolution.**` line
(matching §3/§5/§6's own convention) stating the verdict in one sentence, then the rationale below
it. This is resolved and final — see "Decisions Made During Human Review" below: the user was
asked to choose between adopting the exact-vs-fuzzy split as a named general convention now, or
staying parity-specific for now, and explicitly chose the latter. Write §7 as a committed decision,
not as a fork between options and not with conditional ("if we pick this branch...") phrasing.

Close the verdict paragraph with a value-judgment framing sentence containing the literal phrases
`human sign-off` and `value judgment` — e.g. "Whether to name a general convention from a single
instance is a genuine value judgment investigation could not resolve from repo evidence alone; the
verdict below reflects explicit human sign-off, not a self-chosen answer presented as objectively
settled." This sentence is required (test 7 is unconditional in `test_plan.md`) because
investigation's own finding — that this decision is a value call, not a technical derivation — is
true independent of which way the verdict ultimately landed.

**§7 resolution text to write:**

- `**Core resolution — no.**` The exact-vs-fuzzy split stays an implicit, parity-specific pattern
  for now; it is not promoted to a named general convention.
- State the rationale explicitly, using language equivalent to "second real use case" / "n=1" /
  rule-of-three reasoning (per test 6): no second `kind` has ever needed a gate-safe exact lookup,
  so any applicability criteria written today could not be tested against a second case and would
  either overfit to `parity_index.py`'s specific choices (SQLite, materialized `entry_health`
  table, fixed `_REF_TABLES`) or be abstracted so far it becomes unfalsifiable.
- State plainly that the Gate A GO verdict's evidence (66.7% vs. 4.8% recall) speaks to
  parity-domain retrieval quality, not to whether an analogous module for a different kind would
  carry the same payoff — so it cannot be used as evidence for generalization. This is the same
  parity-domain-quality-vs-generalizability distinction Step 1's precedent paragraph already
  establishes; §7's resolution text restates it explicitly as the reason the verdict is "no."
- Even though no named convention is adopted, document the pattern's generalizable properties as a
  **citable, non-mandatory reference** (not gated behind an `### Applicability Criteria` heading,
  and not framed as a checklist any future `kind` "should" follow) — read-only access to the
  underlying store, exact equality/primary-key matching only (no similarity ranking, no fuzzy
  scoring field), deterministic sort order via explicit typed keys, an explicit typed no-match
  response, and zero mutation surface. Frame these as "what this pattern looks like, for reference
  if a similar need arises" rather than "criteria a future kind must satisfy."
- State the reopening condition explicitly: if a second real `kind` genuinely needs a gate-safe
  exact lookup, a follow-up ticket should revisit this decision and derive applicability criteria
  from real second-instance evidence, rather than the single-instance criteria that would otherwise
  have to be written speculatively today.

**Do NOT touch:** §1-§6. Do not add a `search` CLI subcommand or any other code-shaped artifact to
`parity_index.py` — this step is prose only. Do not add an `### Applicability Criteria` heading or
otherwise phrase the generalizable-properties list as a mandatory convention — the verdict is "no."

**Verify:** `test_section_7_states_explicit_yes_or_no_verdict`,
`test_section_7_flags_human_sign_off_if_value_judgment`,
`test_section_7_states_parity_specific_rationale_if_no_verdict`.

---

### Step 3 — Update the epic ticket's OPEN DECISION 9 entry

**Files:** `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`

**Change:** Locate the `OPEN DECISION 9` bullet (currently `**UNRESOLVED**`, confirmed at the line
immediately following the OPEN DECISION 8 entry as read during Investigate/Plan). Change
`**UNRESOLVED**` to `**RESOLVED**` and replace the question-only body with a one-paragraph outcome
summary plus a citation to `docs/engine/contracts/context_packet_contract.md` §7, matching exactly
the shape both `TCK-20260802-CONTEXT-KIND-PRIORITY` (Decision 7) and
`TCK-20260802-STORED-ARTIFACT-KIND` (Decision 8) used for their own entries in this same file. The
summary must state the resolved verdict from Step 2 — "no," the exact-vs-fuzzy split stays
parity-specific for now, with the reopening condition noted — and must not hedge between options or
reference the rejected "adopt now" alternative as if it were still live.

**Do NOT touch:** Decisions 1-8's own entries in this file. Only the Decision 9 bullet changes.

**Verify:** `test_epic_ticket_decision_9_marked_resolved`.

**Note on scope (resolves Unresolved Question 3 from investigation):** this file is not a
`docs/` path, but both closed siblings included their own epic-entry update in Files Changed as
an established batch convention (`TCK-20260802-CONTEXT-KIND-PRIORITY`'s Files Changed lists
`tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`; so does
`TCK-20260802-STORED-ARTIFACT-KIND`'s). This ticket's own Files Changed must list it too, for
consistency with precedent — this is a process question with clear precedent, not a value
judgment, so it is decided here rather than flagged.

---

### Step 4 — Add the new static-content test file

**Files:** `tests/tools/test_exact_lookup_convention_decision.py` (new)

**Change:** Following the established pattern from `tests/tools/test_context_kind_priority_decision.py`
and `tests/tools/test_stored_artifact_kind_decision.py` (`Path.read_text()` static assertions, no
importable ranking/lookup logic to exercise), add the 10 tests specified in `test_plan.md`:

1. `test_section_7_appears_after_section_6`
2. `test_section_7_quotes_open_decision_9_verbatim` — use the `_normalize_whitespace()`
   blockquote-safe technique from `TCK-20260802-STORED-ARTIFACT-KIND`'s fix (strip leading `> `
   markers, collapse whitespace) rather than a raw contiguous-substring check, to avoid the same
   markdown line-wrap brittleness that ticket had to fix after the fact.
3. `test_section_7_states_explicit_yes_or_no_verdict`
4. `test_section_7_cites_real_precedent_by_function_name`
5. `test_section_7_applicability_criteria_present_if_yes_verdict` — the resolved verdict is "no"
   (Step 2 documents no `### Applicability Criteria` heading), so this test checks for the
   Branch-A yes-marker, finds it absent, and skips/xfails gracefully per test_plan.md's own
   instruction — it is not expected to exercise its main assertion under this ticket's resolution.
6. `test_section_7_states_parity_specific_rationale_if_no_verdict` — the resolved verdict is "no,"
   so this test exercises its main assertion: it checks for the Branch-B no-marker and the
   parity-specific rationale text and must pass (not skip).
7. `test_section_7_flags_human_sign_off_if_value_judgment` — unconditional; literal `human
   sign-off` and `value judgment` phrases required regardless of branch (see Step 2).
8. `test_sections_1_through_6_untouched_by_section_7_append` — byte-content check for at least one
   load-bearing sentence per section (§3's "must never imply otherwise", §5's "human sign-off
   required", §6's "intentional permanent design" — reuse the exact sentences the two sibling test
   files already assert for their own predecessor-section guards).
9. `test_no_code_changes_to_named_tools_modules` — sha256 hash fixture for
   `tools/parity_index.py`, `tools/hybrid_retrieval.py`, `tools/context_packet_assembler.py`,
   `tools/generate_registry.py`, recorded against their current (pre-ticket) content. Mirrors the
   identical guard in both sibling test files.
10. `test_epic_ticket_decision_9_marked_resolved` — checks the epic ticket's Decision 9 bullet
    reads `**RESOLVED**` with a §7 citation, and that Decisions 1-8's entries are untouched
    (compare against a recorded pre-ticket snapshot or assert absence of any diff-shaped marker
    near those bullets, matching the sibling tests' approach).

**Do NOT touch:** `tests/tools/test_parity_index.py`, `tests/tools/test_hybrid_retrieval.py`,
`tests/tools/test_context_kind_priority_decision.py`,
`tests/tools/test_stored_artifact_kind_decision.py`, `tests/tools/test_gate_a_readpath_review.py`
— all five must stay green and unmodified; this ticket adds one new file only.

**Verify:** `pytest tests/tools/test_exact_lookup_convention_decision.py -v` — all 10 tests pass,
with test 6 (`test_section_7_states_parity_specific_rationale_if_no_verdict`) exercising its main
assertion and test 5 (`test_section_7_applicability_criteria_present_if_yes_verdict`)
skipping/xfailing, consistent with the resolved "no" verdict.

**Dependency:** Requires Step 1, Step 2, and Step 3 to be complete — the tests assert against the
finished doc/ticket content.

---

### Step 5 — Regression pass

**Files:** None changed; verification only.

**Change:** Run the full scoped regression surface from `test_plan.md`:

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
python3 tools/validate_frontmatter.py tickets/inprogress/TCK-20260802-EXACT-LOOKUP-CONVENTION.md
python3 tools/generate_registry.py --check
```

Confirm zero failures and zero unexpected drift. Confirm via `git diff --stat` that only
`docs/engine/contracts/context_packet_contract.md`,
`tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`,
`tests/tools/test_exact_lookup_convention_decision.py`, and this ticket's own paperwork files
appear in the diff — no `tools/` file present.

**Do NOT touch:** Never run `pytest tests/` unscoped for this ticket.

**Dependency:** Requires Steps 1-4 complete.

**Verify:** All commands above exit clean; this step is itself the final acceptance gate for AC5.

## Scope Guards

- No code changes to `tools/parity_index.py`, `tools/hybrid_retrieval.py`,
  `tools/context_packet_assembler.py`, or `tools/generate_registry.py` — zero diffs, enforced by
  Step 4's hash-fixture test.
- No edits to `docs/engine/contracts/context_packet_contract.md` §1-§6 — append-only from `## 6.`
  onward, enforced by Step 4's byte-content guard test.
- No `search` CLI subcommand or any other code-shaped artifact added to `parity_index.py` "to
  prove the pattern," under either verdict branch — `test_parity_index.py`'s
  `TestArchitectureGuards::test_impact_entry_health_still_forbid_search_cli` must stay green
  unmodified.
- No building of a second exact-lookup module for any other `kind` — this ticket is documentation
  only, regardless of which verdict Step 2 lands on.
- No re-litigation of Open Decisions 1-6 (§1-§3), 7 (§5), or 8 (§6).
- No absorption of sibling Decisions 7/8's own content or tracking entries — only the Decision 9
  bullet in the epic ticket changes.
- Never run `pytest tests/` unscoped.

## Dependency Map

- Step 1 (scaffolding) — no dependencies, can start immediately.
- Step 2 (verdict) — depends on Step 1 (continues the same section). The verdict question has been
  resolved by explicit human decision (see "Decisions Made During Human Review" below — stay
  parity-specific, Branch B); Step 2 is unblocked and ready to implement as written.
- Step 3 (epic ticket update) — depends on Step 2 (needs the actual verdict text to summarize and
  cite).
- Step 4 (test file) — depends on Steps 1-3 (asserts against finished doc/ticket content).
- Step 5 (regression pass) — depends on Step 4.

No step can be meaningfully verified out of order; Steps 1-2 must land in the doc before Step 3's
citation is accurate, and Step 4's tests would otherwise assert against incomplete content.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — explicit yes/no verdict on exact-vs-fuzzy convention | Step 2 | `test_section_7_states_explicit_yes_or_no_verdict` |
| AC2 — if yes, new clearly-delimited applicability-criteria section citing real precedent | Not applicable — resolved verdict is "no" (see Decisions Made During Human Review); no `### Applicability Criteria` heading is written. Real-precedent citation is still delivered by Step 1 independent of the verdict. | `test_section_7_cites_real_precedent_by_function_name` (passes); `test_section_7_applicability_criteria_present_if_yes_verdict` (skips/xfails — no Branch-A content exists) |
| AC3 — if no, explicit rationale for staying parity-specific pending a second use case | Step 2 (resolved "no" text) | `test_section_7_states_parity_specific_rationale_if_no_verdict` |
| AC4 — if genuine value judgment, state plainly as needing human sign-off | Step 2 (both branches) | `test_section_7_flags_human_sign_off_if_value_judgment` |
| AC5 — zero diffs to the four named `tools/` modules; doc file(s) only | Steps 1-5 (scope guards throughout) | `test_no_code_changes_to_named_tools_modules`, Step 5's `git diff --stat` check |

## Decisions Made During Human Review

- **Resolution of investigation.md's open value judgment / this plan's former "Unresolved
  Questions" §1 — which verdict does §7 record: "yes, adopt a named general convention now" or
  "no, stay parity-specific pending a second real use case"?** Investigation explicitly found this
  is a genuine value judgment it could not resolve from repo evidence alone: the Gate A GO verdict
  (66.7% vs. 4.8% recall) is evidence about parity-domain retrieval *quality*, not about pattern
  *generalizability* to a different `kind`, and with n=1 (no second `kind` has ever needed a
  gate-safe exact lookup), rule-of-three reasoning applies — any applicability criteria written
  today from a single instance would be either overfit to `parity_index.py`'s specific choices or
  abstracted so far it becomes unfalsifiable. Both the "yes" and "no" framings were fully drafted
  during planning so implementation could proceed immediately once a human decided. **The user was
  asked to choose between adopting the convention now (Branch A) and staying parity-specific for
  now (Branch B), and explicitly chose Branch B — stay parity-specific for now** — while
  documenting the pattern's generalizable properties (read-only, deterministic, explicit no-match,
  no similarity ranking) as a citable, non-mandatory reference, and stating an explicit reopening
  condition: revisit once a second kind genuinely needs a gate-safe exact lookup. This confirms
  Branch B as §7's actual, final resolution. Step 2 above has been rewritten to record only this
  committed decision; the rejected Branch A draft is preserved in full, unadopted, in "Rejected
  Alternative — Branch A (Not Chosen)" below in case a future ticket revisits the question once a
  real second use case exists.

- **Resolution of investigation.md's Question 2** (moot under the Branch B verdict, but recorded
  for the historical record): had the answer instead been "yes," Step 2's Branch A draft would have
  written applicability criteria at the abstraction level of five generalizable properties
  (read-only access, exact equality matching, deterministic sort, explicit typed no-match response,
  zero mutation surface), explicitly excluding `parity_index.py`'s specific implementation choices
  (SQLite, the materialized `entry_health` table, the fixed `_REF_TABLES` list) from the criteria,
  with an explicit "untested against a second case" caveat in the doc text itself. This did not end
  up governing the shipped resolution, since Branch B was chosen instead.

- **Resolution of investigation.md's Question 3**: resolved — yes, the epic ticket's Decision 9
  entry update belongs in this ticket's Files Changed, matching the established convention both
  closed siblings (`TCK-20260802-CONTEXT-KIND-PRIORITY`, `TCK-20260802-STORED-ARTIFACT-KIND`)
  already set. See Step 3's note. This was decided as a process question with clear precedent, not
  a value judgment requiring human sign-off.

## Rejected Alternative — Branch A (Not Chosen)

During planning, the following "yes, adopt a named general convention now" text was fully drafted
as the alternative to Branch B, in case the human reviewer chose it. It was **not** chosen — see
"Decisions Made During Human Review" above — and is preserved here, unadopted, only so a future
ticket that revisits this decision (once a second kind genuinely needs a gate-safe exact lookup)
does not have to re-derive it from scratch:

> `**Core resolution — yes.**` The exact-vs-fuzzy split becomes a named, documented general
> convention: any future `kind` needing a gate-safe (never similarity-ranked, always deterministic)
> lookup should follow the same shape `parity_index.py` established.
>
> Add a `### Applicability Criteria` subsection (a `###`-level heading, clearly delimited from the
> verdict paragraph — not folded unlabeled into prose). List the criteria at the abstraction level
> of five generalizable properties, separable from `parity_index.py`'s specific implementation
> choices:
> 1. Read-only connection to the underlying store (not merely "no write call site," but a
>    connection-string- or transaction-level read-only guarantee, mirroring `_connect_readonly()`'s
>    `mode=ro` URI).
> 2. Exact equality/primary-key matching only — no similarity ranking, no fuzzy scoring field.
> 3. Deterministic sort order defined by explicit typed keys, never a relevance score.
> 4. Explicit, typed no-match response distinguishing "no filter provided" from "filter provided,
>    zero hits" — never a bare exception or a silently empty collection.
> 5. Zero mutation surface — no write path back into the source of truth, enforced at the
>    architecture-guard test level (citing `TestArchitectureGuards` in
>    `tests/tools/test_parity_index.py` as the existing enforcement pattern to replicate for a
>    future kind's own test file).
>
> Add an explicit caution paragraph: this criteria list does not mandate `parity_index.py`'s
> specific storage technology (SQLite), its materialized `entry_health` table, or its fixed
> `_REF_TABLES` — those are implementation choices for this one instance, not part of the
> convention. Add an explicit untested-against-a-second-case caveat: no second `kind` has ever
> needed a gate-safe exact lookup, so these criteria are necessarily n=1-derived and may need
> revision once a real second use case tests them, and this caveat must appear in the doc itself,
> not only in this plan.

## Deviations

- **Step 4 test file — 14 tests instead of the 10 named in `test_plan.md`, and test 8 split by
  section.** `test_plan.md`'s test 8 (`test_sections_1_through_6_untouched_by_section_7_append`)
  was implemented as three separately named tests
  (`test_context_packet_contract_section_3_text_unchanged`,
  `test_context_packet_contract_section_5_text_unchanged`,
  `test_context_packet_contract_section_6_text_unchanged`) — one per section, matching the actual
  naming convention both sibling test files (`test_context_kind_priority_decision.py`,
  `test_stored_artifact_kind_decision.py`) already use for their own predecessor-section guards,
  rather than test_plan.md's single combined-name suggestion. Coverage is identical (still exactly
  the §3/§5/§6 load-bearing sentences test_plan.md named — §1/§2/§4 were never in scope for this
  guard, matching the two sibling files' own scope). Two additional tests were added beyond
  test_plan.md's list —
  `test_section_7_documents_generalizable_properties_as_non_mandatory_reference` (directly verifies
  Step 2's "citable, non-mandatory reference, not a checklist" instruction, including the absence
  of an `### Applicability Criteria` heading) and `test_section_7_states_reopening_condition`
  (directly verifies Step 2's explicit reopening-condition requirement) — both cover explicit
  Step 2 content requirements that test_plan.md's 10-item list did not enumerate as their own
  named tests. Net: 13 passing + 1 skipped (the conditional yes-verdict test, correctly inert under
  the resolved "no" verdict) = 14 total, a superset of test_plan.md's required coverage, not a
  reduction.
- **`tests/tools/test_gate_a_readpath_review.py` fails independent of this ticket's changes.**
  Confirmed via `git stash` (re-running the file against the pre-ticket working tree reproduces
  the identical 3 failed / 7 errored results) that this file's fixture
  (`staging_artifacts/TCK-20260731-PARITY-READPATH-GATE/gate_a_corpus.json`) no longer exists — it
  was moved to `stored_artifacts/TCK-20260731-PARITY-READPATH-GATE/gate_a_corpus.json` when that
  ticket closed, and the test file itself was never updated to read the new location. This is a
  pre-existing environmental defect unrelated to and not caused by this ticket; fixing it is out
  of this ticket's scope (it is not one of the four named `tools/` files and not
  `context_packet_contract.md`), so it was left untouched and reported here rather than silently
  worked around.
