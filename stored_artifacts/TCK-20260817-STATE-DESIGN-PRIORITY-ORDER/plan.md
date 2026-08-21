---
status: historical
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260817-STATE-DESIGN-PRIORITY-ORDER
artifact_type: plan
tags: [documentation, architecture]
---

# Implementation Plan — TCK-20260817-STATE-DESIGN-PRIORITY-ORDER

## Summary

State the reconstructed pillar-precedence order (Determinism → Resource-Safety → Performance →
Auditability) as a terse rule in `docs/engine/project_lawbook_m10.md`, cross-linking
`docs/architecture/kernel_concurrency_design_philosophy.md` Part 1 as the single source of truth
for the full reasoning, exactly as `SEQUENCE.md` (investigation's "Prior Work") already decided.
Fix the one sentence in Part 1 that becomes stale the moment the lawbook states the order as a
rule, and designate Part 1 explicitly as SSOT there too, satisfying AC4's "one designated single
source of truth, the other cross-linking it." Add doc-consistency tests to
`tests/docs/test_doc_integrity.py` matching the 4 tests specified in `test_plan.md`. No code
changes; no other doc is touched.

## Design Decisions

### Decision 1 — File-scope reading of the Out-of-Scope carve-out (investigation Risk #1)

**Question**: The ticket's Out of Scope says "this ticket edits `project_lawbook_m10.md` (or a doc
it links to), not `docs/architecture/`." Does this permit fixing
`kernel_concurrency_design_philosophy.md` Part 1's now-stale "not stated as a rule anywhere"
sentence (verified present verbatim at `docs/architecture/kernel_concurrency_design_philosophy.md:28-29`,
read in full during Plan)?

**Decision**: Yes, in scope. Adopt the investigation's recommended reading: the parenthetical
"(or a doc it links to)" is an explicit carve-out from the blanket "not docs/architecture/"
restriction, not an exception swallowed by it. Once Step 1 makes `project_lawbook_m10.md`
cross-link `kernel_concurrency_design_philosophy.md`, that doc becomes "a doc it links to" and the
carve-out applies. This is also the *only* reading that can satisfy AC4 ("one designated single
source of truth, the other cross-linking it") — AC4 is unsatisfiable if Part 1 is left asserting
that the order "is not stated as a rule anywhere" immediately after the lawbook states it as a
rule, because that leaves neither doc internally consistent about which one is the SSOT. Leaving
the sentence stale would also be a self-inflicted drift introduced by this ticket's own edit,
which contradicts the doc-hygiene intent (`SEQUENCE.md`, C8) this entire ticket batch exists to
serve. Step 2 implements the one-sentence correction.

### Decision 2 — Explicit pillar-to-order-term mapping (investigation Risk #2)

**Question**: Does the lawbook edit need to explicitly map the 4-term order (Determinism,
Resource-Safety, Performance, Auditability) onto the 5 named pillars (Determinism, Authoritative
Apply, Bounded Resources, Hardware-Class Honesty, Observability Separation) — e.g. "Resource-Safety
≈ Authoritative Apply + Bounded Resources + Hardware-Class Honesty"?

**Decision**: No explicit mapping. State the 4-term order as its own addition immediately after
the unchanged 5-item pillar list, without asserting a term-by-term correspondence. Reasoning:

1. **AC2's literal text** only requires the stated order to name "Performance/throughput
   explicitly as a ranked priority, consistent with Determinism -> Resource-Safety -> Performance
   -> Auditability." It does not require reconciling the term count or names against the 5-pillar
   list. Stating the 4-term order satisfies this as written.
2. **Part 1 itself does not state this mapping** (confirmed by reading
   `docs/architecture/kernel_concurrency_design_philosophy.md:18-29` in full during Plan — Part 1
   names the 5 pillars once, in one unordered sentence, then states the 4-term order as a separate
   reconstructed conclusion; it never asserts which pillar(s) correspond to which order term).
   Since Part 1 is the designated SSOT (Decision 1, `SEQUENCE.md`) and it does not state a mapping,
   inventing one in `project_lawbook_m10.md` would mean the lawbook contains derived content
   *absent from its own SSOT* — this is exactly the "independently re-derive or paraphrase"
   anti-drift hazard the investigation flags, just applied to a mapping instead of the order itself.
3. **The mapping is admittedly loose** (investigation: "Resource-Safety plausibly spans 3 of the 5
   pillars... but this mapping has never been stated explicitly anywhere"). Asserting a specific
   pillar-to-term correspondence as authoritative lawbook content would overstate confidence in an
   already-flagged reconstruction (Decision-adjacent Risk #3) beyond what Part 1 itself claims.

Consequence: Step 1's addition states the 4-term order as a standalone precedence statement,
leaves the 5-item pillar list untouched and unmapped, and does not claim any pillar corresponds to
any specific order term.

## Steps

### Step 1 — State the precedence order in project_lawbook_m10.md

**Files:** `docs/engine/project_lawbook_m10.md`

**Change:** Insert new content between line 23 (end of the "Architectural Pillars" numbered list)
and line 24 (`## Table of Contents`) — confirmed by reading the full file during Plan
(`docs/engine/project_lawbook_m10.md:16-24`: pillars 1-5 occupy lines 18-22, line 23 is blank,
line 24 is `## Table of Contents`). Do not add a new `##` heading — insert as a paragraph still
inside the "Architectural Pillars" section, immediately after item 5, so
`test_document_structural_compliance` (which regex-matches `^##\s+...` headers from
`docs/engine/manifest.json:62-64`'s required list `["Purpose", "Architectural Pillars", "Table of
Contents"]`) sees no new/renamed/removed headers.

Insert this paragraph (verbatim order terms and verbatim order-sentence copied from
`docs/architecture/kernel_concurrency_design_philosophy.md:27-29`, confirmed by reading that file
in full during Plan):

```
**Precedence**: The pillars above are not equally weighted. Under trade-off, the order is:
Determinism, then Resource-Safety, then Performance (only within what the first two allow), then
Auditability (proving the first three held). This order is reconstructed from observed kernel
mechanisms, not confirmed maintainer intent. See
`docs/architecture/kernel_concurrency_design_philosophy.md` Part 1 for the full reasoning — that
section is the single source of truth for this ordering; this is a terse restatement of its
conclusion, not an independent derivation.
```

Cross-link style matches the doc's own existing pattern at
`docs/engine/project_lawbook_m10.md:13` ("See `project_lawbook.md` for the full law text and
parity proofs.") — plain backtick-path prose inside a "See `path`..." sentence, not
`[label](path)` markdown-link syntax. This matters because `test_link_integrity`
(`tests/docs/test_doc_integrity.py:121-156`) only parses `\[.*?\]\((.*?)\)` markdown-link syntax;
plain backtick-path prose is invisible to it, so no link-resolution risk either way, but matching
the existing convention keeps the doc internally consistent (per test_plan.md's explicit
recommendation).

Per Decision 2, do NOT add any sentence mapping individual order terms to individual pillar names.
Per AC3/Decision-1-adjacent Risk #3, the phrase "reconstructed from observed kernel mechanisms,
not confirmed maintainer intent" must be preserved — do not state the order as settled/confirmed
fact.

**Do NOT touch:** The 5-item numbered pillar list itself (lines 18-22) — do not renumber, rename,
reorder, or annotate individual pillars. Do NOT touch `## Table of Contents` (line 24+) or
`## Release-Readiness` (line 33+).

**Verify:** `test_lawbook_states_pillar_precedence_order` and
`test_lawbook_cross_links_design_philosophy_doc` (Step 3, new tests).

### Step 2 — Fix the stale "not stated as a rule anywhere" sentence in Part 1

**Files:** `docs/architecture/kernel_concurrency_design_philosophy.md`

**Change:** Replace the sentence at `docs/architecture/kernel_concurrency_design_philosophy.md:28-29`
— confirmed verbatim by reading the file in full during Plan: "This ordering is implicit,
reconstructed from three documents plus code — it is not stated as a rule anywhere." — with:

```
This ordering is reconstructed from three documents plus code. It is now stated as a terse rule
in `docs/engine/project_lawbook_m10.md`'s Architectural Pillars section, which cross-links here;
this Part remains the single source of truth for the full reasoning behind that rule.
```

This is the one-sentence correction the investigation identifies as necessary once Step 1 lands
(investigation "Docs Requiring Update"), and it satisfies AC4's "one designated single source of
truth, the other cross-linking it" by stating the SSOT designation explicitly in both directions:
Step 1's addition says Part 1 is the SSOT; this sentence confirms the lawbook holds the terse rule
and cross-links here.

**Do NOT touch:** The mermaid `flowchart LR` block (`docs/architecture/kernel_concurrency_design_philosophy.md:31-36`),
the rest of Part 1's prose (lines 20-27, 38-40), `## Part 2` (line 42+) or any other section of
this file. Do not re-open any of C2/C3/C4/C6/C7/C8's already-closed drift items while in this file
— only the single sentence at lines 28-29 is in scope (investigation Anti-Drift Hazards).

**Verify:** `test_design_philosophy_part1_not_stale_after_lawbook_states_order` (Step 3, new test).

### Step 3 — Add doc-consistency tests

**Files:** `tests/docs/test_doc_integrity.py`

**Change:** Add 4 new test functions, following the existing file's established pattern (plain
`open()`/`.read()` on doc paths, no fixtures — confirmed by reading
`tests/docs/test_doc_integrity.py:105-119`'s `test_release_target_binding`, the closest existing
analogue: it already reads `docs/engine/project_lawbook_m10.md` as plain text and asserts substring
presence). This file is the only writer of test content to `docs/engine/project_lawbook_m10.md`'s
and `docs/architecture/kernel_concurrency_design_philosophy.md`'s doc-consistency test coverage —
no other test file currently asserts on either doc's prose content (confirmed: `test_plan.md`'s
Regression Surface lists only `tests/docs/*` and `tests/tools/test_validate_frontmatter.py` as
existing coverage of these two files, and neither of those asserts on pillar/precedence prose), so
there is no other writer to reconcile with for these specific assertions.

```python
def test_lawbook_states_pillar_precedence_order():
    """
    TCK-20260817-STATE-DESIGN-PRIORITY-ORDER: project_lawbook_m10.md must state an explicit
    precedence order among the Architectural Pillars, not just an enumerated list.
    """
    lawbook_path = "docs/engine/project_lawbook_m10.md"
    with open(lawbook_path, "r") as f:
        content = f.read()

    order_terms = ["Determinism", "Resource-Safety", "Performance", "Auditability"]
    positions = []
    search_from = 0
    for term in order_terms:
        idx = content.index(term, search_from)
        positions.append(idx)
        search_from = idx + len(term)
    assert positions == sorted(positions), "Pillar precedence order terms are not in stated order"

def test_lawbook_precedence_matches_design_philosophy_verbatim():
    """
    Anti-drift guard: the 4 order terms in project_lawbook_m10.md must be character-identical
    to the terms used in kernel_concurrency_design_philosophy.md Part 1.
    """
    lawbook_path = "docs/engine/project_lawbook_m10.md"
    design_doc_path = "docs/architecture/kernel_concurrency_design_philosophy.md"
    with open(lawbook_path, "r") as f:
        lawbook_content = f.read()
    with open(design_doc_path, "r") as f:
        design_content = f.read()

    order_terms = ["Determinism", "Resource-Safety", "Performance", "Auditability"]
    for term in order_terms:
        assert term in lawbook_content, f"{term} missing from lawbook"
        assert term in design_content, f"{term} missing from design philosophy doc"

def test_lawbook_cross_links_design_philosophy_doc():
    """
    project_lawbook_m10.md must cross-link kernel_concurrency_design_philosophy.md as the single
    source of truth for the precedence reasoning, rather than restating it independently.
    """
    lawbook_path = "docs/engine/project_lawbook_m10.md"
    with open(lawbook_path, "r") as f:
        content = f.read()
    assert "docs/architecture/kernel_concurrency_design_philosophy.md" in content

def test_design_philosophy_part1_not_stale_after_lawbook_states_order():
    """
    Regression guard: Part 1's "not stated as a rule anywhere" claim must not reappear now that
    project_lawbook_m10.md states the order as a rule.
    """
    design_doc_path = "docs/architecture/kernel_concurrency_design_philosophy.md"
    with open(design_doc_path, "r") as f:
        content = f.read()
    assert "not stated as a rule anywhere" not in content
    assert "docs/engine/project_lawbook_m10.md" in content
```

Add these functions at the end of `tests/docs/test_doc_integrity.py` (after
`test_link_integrity`, currently the file's last function, ending at line 156). Do not modify any
existing function in this file.

**Do NOT touch:** `tests/docs/test_kernel_phase_names_consistent.py`,
`tests/docs/test_contributor_guardrails.py`, `tests/tools/test_validate_frontmatter.py` — run
these as regression checks (Step 4) but do not edit them.

**Verify:** `pytest tests/docs/test_doc_integrity.py -v` — all 4 new tests plus all existing tests
in the file pass.

### Step 4 — Run full doc-integrity regression suite

**Files:** none (verification only)

**Change:** Run the scoped pytest commands from `test_plan.md`:

```
pytest tests/docs/ -v
pytest tests/tools/test_validate_frontmatter.py -v
```

Confirms Step 1/2's edits did not break `test_manifest_file_existence`,
`test_document_structural_compliance`, `test_release_target_binding`, `test_link_integrity`,
`test_terminology_alignment` (all in `test_doc_integrity.py`), `test_kernel_phase_names_consistent.py`,
`test_contributor_guardrails.py`, and `test_validate_frontmatter.py` — none of which this ticket's
steps intentionally modify, but all of which read files this ticket edits.

**Do NOT touch:** Any test file's assertions in order to make this pass — if a pre-existing test
fails because of Step 1/2's edits, that is a signal the edit violated a structural constraint
(e.g. accidentally altered a required header or a `class_b` mention), not something to route
around by editing the test (per CLAUDE.md Gate Integrity rule).

**Verify:** All commands above exit 0.

## Scope Guards

- Do NOT touch `docs/engine/project_lawbook.md`. Its differently-shaped, differently-named,
  differently-counted (4 vs. 5) pillar list is real, pre-existing, already-found-and-explicitly-
  left-unfixed drift (`TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT`, closed). This ticket's edit to
  `project_lawbook_m10.md`'s 5-pillar list does not reconcile it with `project_lawbook.md`'s
  4-item list — do not "helpfully" fix this while editing the adjacent section.
- Do NOT touch `docs/engine/contracts/harness_architecture.md`. Its 3-step order (Absolute
  Determinism → Resource Boundaries → Auditability, confirmed verbatim at
  `docs/engine/contracts/harness_architecture.md:15-17`) is a consistent subsequence of the 4-step
  engine order with "Performance" omitted — correct as-is for its scope (verification, not runtime
  trade-offs), not a gap to fill. Do not add a "Performance" step there.
- Do NOT independently re-derive, paraphrase, or reword the order. Any occurrence of the 4 order
  terms in `project_lawbook_m10.md` must be character-identical to
  `kernel_concurrency_design_philosophy.md` Part 1's terms ("Determinism", "Resource-Safety",
  "Performance", "Auditability") — verified by Step 3's
  `test_lawbook_precedence_matches_design_philosophy_verbatim`.
- Do NOT state a pillar-to-order-term mapping (Decision 2) — neither doc states one; inventing one
  here would be new derived content outside the designated SSOT.
- Do NOT re-open any of C2/C3/C4/C6/C7/C8's already-closed drift items while editing
  `kernel_concurrency_design_philosophy.md` — only the single sentence at lines 28-29 (Step 2) is
  in scope.
- Do NOT touch `docs/engine/architecture.md` or `docs/engine/contracts/certification_contract.md`
  — investigation confirms neither conflicts with nor needs updating for this ticket's scope.
- No `src/` or other code changes — this ticket is documentation-only.
- No `docs/parity_ledger/*` entry changes — investigation confirms no existing entry covers
  document-precedence-ordering and this ticket introduces no code behavior change.

## Dependency Map

- Step 1 and Step 2 are logically sequenced (Step 2's correction only becomes true once Step 1
  lands) but touch different files and can be implemented in either file-edit order within the
  same commit — however, Step 1 must be reasoned about first since Step 2's wording ("now stated
  as a terse rule in `project_lawbook_m10.md`'s Architectural Pillars section") describes Step 1's
  output.
- Step 3 depends on Steps 1 and 2 being complete (tests assert on both edited docs' final content).
- Step 4 depends on Step 3 (runs the new tests plus the full regression suite).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1: lawbook (or linked doc) states explicit precedence order, not just enumerated list | Step 1 | `test_lawbook_states_pillar_precedence_order` |
| AC2: order names Performance explicitly as ranked priority, consistent with Determinism→Resource-Safety→Performance→Auditability | Step 1 | `test_lawbook_states_pillar_precedence_order` |
| AC3: written precedence is the reconstructed order (with reconstruction caveat) or a stated deviation+rationale | Step 1 (states "reconstructed... not confirmed maintainer intent") | Manual verification checklist (Step 5 below); no automated test asserts prose nuance beyond term presence/order |
| AC4: if kernel concurrency design doc lands, both docs' orders match verbatim with one designated SSOT and the other cross-linking it | Step 1 (lawbook cross-links + defers to Part 1 as SSOT) + Step 2 (Part 1 confirms SSOT status, cross-references lawbook) | `test_lawbook_precedence_matches_design_philosophy_verbatim`, `test_lawbook_cross_links_design_philosophy_doc`, `test_design_philosophy_part1_not_stale_after_lawbook_states_order` |

## Verification (Manual Checklist)

No automated test can fully cover prose-precedence-ordering *content* (only term-presence and
term-order, per Step 3's tests). Before closing this ticket, manually confirm:

- [ ] Both `docs/engine/project_lawbook_m10.md` and `docs/architecture/kernel_concurrency_design_philosophy.md`
  state the identical 4 verbatim order terms in the identical relative order.
- [ ] `project_lawbook_m10.md`'s new cross-link (`docs/architecture/kernel_concurrency_design_philosophy.md`)
  resolves to a real, existing file.
- [ ] `kernel_concurrency_design_philosophy.md`'s corrected sentence (Step 2) reads accurately —
  it no longer claims the order is unstated as a rule, and correctly attributes the terse rule to
  `project_lawbook_m10.md` while retaining Part 1's own status as the fuller narrative/SSOT.
- [ ] `project_lawbook_m10.md`'s new paragraph does not state a pillar-to-order-term mapping
  (Decision 2).
- [ ] `project_lawbook_m10.md`'s new paragraph explicitly labels the order as reconstructed, not
  confirmed maintainer intent (AC3 / Risk #3).
- [ ] `tests/docs/test_doc_integrity.py` and `tests/docs/test_doc_path_existence.py` still pass —
  no dead citations introduced by the new cross-link.

## Anti-Drift Notes

- The investigation confirms `docs/engine/project_lawbook.md`'s pillar list is a real,
  pre-existing, already-closed-as-out-of-scope drift item (`TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT`).
  This plan does not touch it. If a future ticket reconciles it, that ticket owns its own tests —
  do not add a test here asserting `project_lawbook.md` matches `project_lawbook_m10.md`.
- `harness_architecture.md`'s 3-step order omitting "Performance" is confirmed order-consistent
  (a strict subsequence) with the 4-step order, not a contradiction — implementer must not "fix"
  it by adding a Performance step; doing so would be scope creep the test_plan explicitly flags as
  something a reviewer should catch, not something to preempt.
- The reconstructed order is not maintainer-confirmed. Both Step 1's and the existing Part 1 text
  already carry this caveat — do not strengthen either doc's language to assert the order as
  settled fact during implementation; preserve the "reconstructed... not confirmed maintainer
  intent" framing verbatim in intent even if exact wording is adjusted for flow.
- `docs/engine/manifest.json`'s `forbidden_terms` list (`docs/engine/manifest.json:78-87`) includes
  phrases like "guaranteed performance" and "maximum speed" — confirmed the Step 1 addition's
  wording ("use available headroom, never borrow from 1 or 2" is Part 1's phrasing, not lawbook's;
  lawbook's own added text contains none of the forbidden phrases) does not trigger any forbidden
  term. Implementer should re-check this if wording is adjusted during implementation.
- `kernel_concurrency_design_philosophy.md` is not in `docs/engine/manifest.json`'s
  `mandatory_documents` list (confirmed by reading the manifest in full during Plan) — so
  `test_manifest_file_existence`, `test_document_structural_compliance`, and `test_link_integrity`
  do not apply to it; only the 4 new tests in Step 3 cover its content directly.
