---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260802-CONTEXT-KIND-PRIORITY
artifact_type: plan
tags: [ai, documentation]
---

# Implementation Plan — TCK-20260802-CONTEXT-KIND-PRIORITY

## Summary

This ticket resolves Open Decision 7 (cross-kind candidate ranking/selection for the context
packet's bounded `token_budget`) with a documentation-only change: a new §5 section appended to
`docs/engine/contracts/context_packet_contract.md` (contract-only — no separate `docs/ai/*.md`
file, following Decision 3's own precedent for this exact contract), an update to the epic
ticket's OPEN DECISION 7 tracking entry, and a new lightweight architecture-guard test file
asserting the decision doc's required content. The new §5 definitively resolves three
code-grounded technical constraints the investigation surfaced (the `unrated`-must-not-default-
to-worst rule already in §3, the score non-comparability gap, and `_resolve_subject_conflicts()`'s
structural inapplicability cross-kind) and takes an explicit position on both concrete competing-
kind examples the ticket names — but that position is itself "this remaining ordering question is
a genuine value judgment with zero repo precedent for the underlying mechanism, and is deferred
pending explicit human sign-off," not a self-invented ordering. No code is touched anywhere in
this plan.

## Decided Open Questions (this ticket's own process authority)

1. **Doc location: contract-only, no standalone `docs/ai/*_decision.md` file.** Decision 3 is the
   directly analogous precedent — it also extends `context_packet_contract.md` itself for a
   `context_packet_contract.md`-shaped question — and it did not spawn a separate `docs/ai/` file.
   The ticket's own Scope text ("Extend `docs/engine/contracts/context_packet_contract.md` with a
   new section/addendum") also reads as sufficient on its own. Decisions 1/2/5/6 got standalone
   `docs/ai/` files because they were not extensions of this specific contract. Decided: contract-
   only.
2. **Add a new test file.** No repo precedent requires this (Decisions 1/2/5/6 shipped without
   one), but the test_plan.md for this ticket already specifies concrete, low-cost, static
   content-check tests mapped 1:1 to this ticket's four ACs, and they directly guard against the
   two things this ticket is most likely to silently drift on later (an edit creeping into §3, or
   a future code change invalidating the doc's cited technical facts without anyone noticing).
   Decided: add `tests/tools/test_context_kind_priority_decision.py` per test_plan.md's Step 2/3/4
   test names, as a strengthening beyond precedent, not because precedent requires it.

## Steps

### Step 1 — Add new §5 "Open Decision 7 Resolution" section to the contract

**Files:** `docs/engine/contracts/context_packet_contract.md`

**Change:** Append a new `## 5. Open Decision 7 Resolution` section after the existing `## 4.
Verification Path` section (do not renumber or touch §4). Follow the skeleton confirmed in
Decisions 1/2 (open with a verbatim quote of the Open Decision being resolved) and the "Extension
—" heading convention already used in §3, cross-referencing §3 rather than duplicating it. The
section must contain, in this order:

1. **Verbatim quote** of Open Decision 7 as stated in the epic ticket
   (`tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`, OPEN DECISION 7 entry,
   currently lines 174-179) — read that exact text before writing this section; do not paraphrase
   the quote itself.
2. **Three technical constraints, resolved definitively, each with a direct code citation:**
   - *Constraint A — `unrated` must not default to worst.* Cite §3's own existing text
     ("must never imply otherwise by, for example, defaulting to P2/historical as if that were a
     real registry read") as an already-resolved textual constraint that any cross-kind ordering
     must also respect — this is not new, just newly load-bearing for Decision 7.
   - *Constraint B — score is not cross-kind-comparable today.* Cite
     `candidate_from_hybrid_result()` setting `score = result.rrf_score` (a real RRF float) versus
     `unrated_candidate()` / `candidate_from_code_index_record()` defaulting `score = 0.0` versus
     `candidate_from_parity_ledger_fixture()` hardcoding `score = 0.0` at line 220 — state plainly
     that "sort by score" is technically broken today independent of any policy choice, so no
     resolution in this section may rely on `.score` as a cross-kind ranking signal without also
     naming this as a separate, out-of-scope normalization prerequisite.
   - *Constraint C — `_resolve_subject_conflicts()` cannot structurally fire cross-kind.* Cite the
     freshness-eligibility gate (`_CONFLICT_ELIGIBLE_FRESHNESS = {"active","authoritative"}`)
     against the fact that `code_symbol`/`test`/`graphify_node`/in-progress-ticket freshness is
     always `"unrated"` and `parity_ledger_entry` freshness is a disjoint 5-value status enum —
     state this as a structural fact about the current code, not a policy stance, and therefore
     explain why "just reuse `_resolve_subject_conflicts()`" is not an available option for cross-
     kind pairs today.
3. **Explicit position on both named concrete examples**, framed honestly as a deferral-with-
   reasoning (not a hedge, not an invented ordering):
   - *Unrated `code_symbol` vs. P1 doc:* state that Constraint A forbids ranking `unrated` below
     P1 by silent default, and Constraint B forbids using `.score` to break the tie instead — so
     no defensible ordering between these two can be derived from existing code or contract text
     today; this specific pair is deferred pending human sign-off on what `unrated`'s relative
     position should be once "don't default to worst" is honored.
   - *P0 `parity_ledger_entry` inclusion-floor guarantee:* state that no inclusion-floor or
     budget-trimming mechanism exists anywhere in the repo today (confirmed by investigation — no
     precedent found), so whether a P0 parity entry should bypass ordinary ranking and always be
     included is a genuine, undecided policy choice, not a technical derivation from `impact()`'s
     existing same-kind severity sort (`_PRIORITY_ORDER`/`_STATUS_SEVERITY`) — that sort ranks
     parity entries against each other only, and does not establish a cross-kind floor rule.
4. **Explicit human-sign-off statement.** State in plain language (using a literal phrase such as
   "needs explicit human sign-off") that the residual ordering/floor policy — where exactly
   `unrated` sits relative to `P1`/`P2` once Constraint A is honored, and whether `P0`
   `parity_ledger_entry` sources get a hard inclusion floor — is a genuine value judgment with zero
   existing repo precedent for the underlying mechanism (an inclusion-floor/budget-trimming
   concept does not exist anywhere in this codebase today), and is therefore left open pending
   human decision rather than resolved by this document. This must not be presented as a
   self-chosen ordering dressed up as settled.
5. Do not introduce any shared numeric scale that silently merges parity `priority` and REGISTRY
   `authority` — if the section discusses both in the same sentence, say explicitly that they are
   lexically identical (`P0`-`P2`) but semantically distinct, per §3's own existing warning against
   silent coercion.

**Do NOT touch:** `## 3. Open Decision 3 Resolution`'s existing text (including its two
"Extension —" subsections and "What does not change" subsection) — read-only precedent to cite,
never edit. Do not touch `## 4. Verification Path`. Do not touch the document's frontmatter beyond
what is already valid (no field changes needed). Do not create a `docs/ai/*_decision.md` file (see
Decided Open Question 1 above).

**Verify:** `test_context_packet_contract_section_3_text_unchanged` (Step 3, below) plus manual
review of the new §5 text against AC1, AC2, and AC3 line-by-line.

---

### Step 2 — Update the epic ticket's OPEN DECISION 7 entry to resolved

**Files:** `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`

**Change:** Locate the OPEN DECISION 7 entry (currently marked `**UNRESOLVED**`, lines ~174-179).
Replace the unresolved marker and body with the same shape every prior sibling entry (OPEN
DECISION 1/2/3/4/5/6) uses: a `**RESOLVED**` marker, a one-paragraph summary of the outcome, and a
citation to the new decision location. Because the actual outcome is "three technical constraints
resolved, residual ordering question deferred pending human sign-off," the summary paragraph must
say exactly that — do not write a bare `**RESOLVED**` that overstates the outcome as a complete
ordering policy. Cite `docs/engine/contracts/context_packet_contract.md` §5 (the exact section
heading added in Step 1) as the resolution location, matching how prior entries cite their own
resolving doc.

**Do NOT touch:** OPEN DECISION 1, 2, 3, 4, 5, or 6 entries in this same epic ticket — read-only
formatting precedent only. Do NOT touch OPEN DECISION 8 or 9 entries (sibling decisions from the
same batch, explicitly out of scope for this ticket). Do not touch any other section of the epic
ticket (its own Status/Tier/Scope/etc. fields).

**Verify:** Manual review — confirm the OPEN DECISION 7 entry now reads RESOLVED with a summary
matching the actual §5 content, and a diff of the epic ticket touches only the OPEN DECISION 7
block.

---

### Step 3 — Add architecture-guard test file for the decision doc's content

**Files:** `tests/tools/test_context_kind_priority_decision.py` (new file)

**Change:** Add a new pytest module using the static `Path.read_text()` content-check technique
established by `tests/tools/test_shadow_packet_call_site.py` (no imports of `tools/` selection
logic — none exists to import). Read `docs/engine/contracts/context_packet_contract.md` once per
test (or once at module scope) and assert on its raw text. Implement the tests named in
test_plan.md, scoped to this ticket's four ACs:

- `test_decision_doc_cites_resolve_subject_conflicts_precedent` (AC1) — asserts the literal string
  `_resolve_subject_conflicts` appears in the doc, and that `subject_key` and `freshness` also
  appear near it alongside a generalization-verdict marker phrase (e.g. `structurally` or `does
  not generalize` or `same-kind`).
- `test_decision_doc_addresses_unrated_code_symbol_vs_p1_doc_example` (AC2) — asserts `code_symbol`
  and `P1` appear together with an explicit-position marker (given Step 1's actual resolution,
  this will be a deferral marker such as `human sign-off` or `deferred`, not `outrank`/`always` —
  write the assertion to match whatever Step 1 actually produced, not a guessed keyword).
- `test_decision_doc_addresses_p0_parity_entry_inclusion_floor` (AC2) — asserts
  `parity_ledger_entry`, `P0`, and `inclusion` (or `floor`) appear together with an explicit
  yes/no/deferred stance marker.
- `test_decision_doc_states_human_signoff_needed_if_value_judgment` (AC3) — asserts the literal
  phrase `human sign-off` (or the exact phrasing Step 1 used) is present, since Step 1's resolution
  lands on "needs sign-off," not a fully technical derivation.
- `test_context_packet_contract_section_3_text_unchanged` (AC4) — asserts specific known §3
  sentences (e.g. the exact phrase "must never imply otherwise by, for example, defaulting to
  P2/historical") are still present verbatim, proving no in-place edit occurred to §3.
- `test_no_code_changes_to_named_tools_modules` (AC4) — a `git diff --stat` (or equivalent
  subprocess check against the ticket's base commit) confirming `tools/context_packet_assembler.py`,
  `tools/hybrid_retrieval.py`, `tools/parity_index.py`, and `tools/generate_registry.py` are
  byte-identical to their pre-ticket state. If a stable base-commit reference is impractical inside
  a pytest test, implement this as a content-hash-vs-recorded-fixture check instead (record each
  file's current hash as a literal constant in the test, matching this ticket's one-off scope, not
  a durable invariant).

Write these as straightforward `assert "..." in text` checks — no NLP, no fuzzy matching, matching
the existing `test_shadow_packet_call_site.py` style precedent.

**Do NOT touch:** `tests/tools/test_context_packet_assembler.py`,
`tests/tools/test_hybrid_retrieval.py`, `tests/tools/test_parity_ledger_scan.py`,
`tests/tools/test_shadow_packet_call_site.py` — these are read-only regression precedent and
technique references, not edit targets.

**Verify:** `pytest tests/tools/test_context_kind_priority_decision.py -v` — all new tests pass
against the Step 1 doc content.

---

### Step 4 — Regression pass and frontmatter validation

**Files:** none changed — verification only.

**Change:** Run the existing regression suite named in test_plan.md to confirm nothing this ticket
touched (in practice, nothing — this is doc + new-test-file only) broke adjacent behavior, and that
the doc citations in the new §5 (line numbers, function names) still match live code before this
ticket closes:

```
pytest tests/tools/test_context_packet_assembler.py tests/tools/test_hybrid_retrieval.py tests/tools/test_parity_ledger_scan.py -v
pytest tests/tools/test_context_kind_priority_decision.py -v
python3 tools/validate_frontmatter.py docs/engine/contracts/context_packet_contract.md
```

Also run `git diff --stat` against the ticket's base commit and confirm the changed-file set is
exactly: `docs/engine/contracts/context_packet_contract.md`,
`tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`,
`tests/tools/test_context_kind_priority_decision.py`, plus this ticket's own
ticket/staging-artifact files. No `tools/` or `src/` file may appear in that diff.

**Do NOT touch:** Nothing new — this step is read-only verification.

**Verify:** All commands above exit zero; `git diff --stat` file list matches exactly the expected
set.

## Scope Guards

- No code changes to `tools/context_packet_assembler.py`, `tools/hybrid_retrieval.py`,
  `tools/parity_index.py`, or `tools/generate_registry.py` — confirmed by investigation that none
  of them implement any selection/ranking-against-budget logic today, so there is no small
  "obvious" fix to sneak in. Do not add a minimal ranking helper "to make the doc feel concrete."
- Do not edit `context_packet_contract.md` §3's existing resolved text (its core resolution or
  either "Extension —" subsection or "What does not change" subsection) — cite it, never modify it.
- Do not create a standalone `docs/ai/*_decision.md` file (Decided Open Question 1).
- Do not reopen or amend Open Decisions 1-6 anywhere they are recorded (their own `docs/ai/*.md`
  files, or their entries in the epic ticket).
- Do not touch OPEN DECISION 8 or 9 entries in the epic ticket, and do not discuss the
  `stored_artifact` kind (Decision 8) or the exact-vs-fuzzy lookup convention (Decision 9) in the
  new §5 section, even in passing, while writing about `kind` vocabulary generally.
- Do not introduce a shared numeric scale that silently coerces `unrated` / parity `priority` /
  REGISTRY `authority` onto one number line without saying explicitly that it is doing so — this is
  the same silent-coercion trap §3 already warns against.
- Do not invent a concrete P0-floor / unrated-position answer to close out AC2/AC3 more tidily than
  the evidence supports — the deferral-with-reasoning framing in Step 1 item 3-4 is the required
  output, not a placeholder to later replace with a guessed number.

## Dependency Map

- Step 1 has no dependencies — it is the sole content-producing step.
- Step 2 depends on Step 1 (cites the exact §5 heading and summarizes its actual resolution — must
  be written after Step 1's text is final).
- Step 3 depends on Step 1 (its assertions target Step 1's actual wording, not a guessed keyword
  set) but is independent of Step 2.
- Step 4 depends on Steps 1, 2, and 3 all being complete — it is the final regression/diff check.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — cites `_resolve_subject_conflicts()` same-kind precedent and explains generalization | Step 1 (item 2, Constraint C) | `test_decision_doc_cites_resolve_subject_conflicts_precedent` (Step 3) |
| AC2 — explicit position on both concrete examples (unrated code_symbol vs. P1 doc; P0 parity floor) | Step 1 (item 3) | `test_decision_doc_addresses_unrated_code_symbol_vs_p1_doc_example`, `test_decision_doc_addresses_p0_parity_entry_inclusion_floor` (Step 3) |
| AC3 — plain human-sign-off statement if genuine value judgment | Step 1 (item 4) | `test_decision_doc_states_human_signoff_needed_if_value_judgment` (Step 3) |
| AC4 — no code changes; §3 not edited in place | Step 1 (Do NOT touch), Scope Guards; verified in Step 4 | `test_context_packet_contract_section_3_text_unchanged`, `test_no_code_changes_to_named_tools_modules` (Step 3); `git diff --stat` check (Step 4) |

## Anti-Drift Notes

- The absence of any selection/ranking code anywhere in `tools/context_packet_assembler.py` is not
  license to add a minimal implementation "just to be concrete" — investigation explicitly flagged
  this temptation; Step 1 produces documentation only.
- §3's "Extension —" subsections use the same heading convention the new §5 will reuse — be careful
  when appending not to accidentally nest the new content under `## 3.` instead of creating a new
  `## 5.` heading at the same outline level as `## 4.`.
- Constraint B (score non-comparability) means Step 1 must not lean on "well just sort by score" as
  a partial answer anywhere in the deferred-example reasoning — `.score` is currently 0.0 for two
  of the three kinds in question, so it cannot break any tie today.
- The epic ticket update (Step 2) is easy to skip because "Related Tickets" reads as read-only
  context — it is a required update target, confirmed by the fact every one of the six prior
  sibling decisions updated their own OPEN DECISION entry.
- Step 3's tests must be written against Step 1's actual final wording, not against the illustrative
  keyword guesses in test_plan.md (e.g. `outrank`/`always`/`case-by-case`) — since Step 1's actual
  resolution is a deferral, the AC2 tests should key on deferral language (`human sign-off`,
  `deferred`), and the test_plan.md's own note anticipates this mismatch is possible and tells the
  implementer to match whichever the doc actually lands on.

## Decisions Made During Human Review

- **Residual ordering/floor policy (where `unrated` sits relative to `P1`/`P2` once "don't default
  to worst" is honored, and whether a P0 `parity_ledger_entry` gets a hard inclusion floor): the
  planner flagged this as an open question with two options — (a) document the deferral with
  reasoning, or (b) have a human supply a concrete ordering/floor policy now. The user was asked to
  choose between these two options and explicitly chose (a): document the deferral, don't invent a
  policy.** This is exactly the approach the plan's Step 1 already specified (a documented,
  reasoned deferral stating the three technical constraints — A/B/C — as resolved, and the exact
  ordering/floor policy as an open value judgment with no derivable answer from existing code or
  precedent, deferred to a future ticket once a human supplies a concrete policy). Because the
  chosen option matches Step 1's original text exactly, **no content change was made to Step 1** —
  this decision confirms and ratifies Step 1 as originally drafted rather than revising it. If a
  human reviewer later supplies a concrete ordering/floor policy, a follow-up ticket should extend
  §5 with it; this ticket's own scope ends at stating the deferral honestly.

## Deviations

None. All 4 steps were implemented exactly as specified. One minor implementation choice, within
the plan's own stated flexibility: Step 3's `test_no_code_changes_to_named_tools_modules` uses a
recorded-sha256-hash-fixture check rather than a `git diff --stat`-against-base-commit check — the
plan's own Step 3 text explicitly names this as an acceptable alternative ("If a stable base-commit
reference is impractical inside a pytest test, implement this as a content-hash-vs-recorded-fixture
check instead"), and it was impractical here because the working tree already carried several
unrelated concurrent modifications from other in-flight tickets at implementation time, with no
single clean base commit to diff against. Two additional tests beyond test_plan.md's named set were
added (`test_section_5_heading_exists_after_section_4`, `test_section_5_quotes_open_decision_7`,
`test_context_packet_contract_section_4_text_unchanged`) as straightforward strengthenings of the
same static-content-check technique — not required by the plan, but directly supporting AC4's "§4
also untouched" guarantee and the "new section actually exists at the right outline level" guard
called out in the plan's own Anti-Drift Notes.
