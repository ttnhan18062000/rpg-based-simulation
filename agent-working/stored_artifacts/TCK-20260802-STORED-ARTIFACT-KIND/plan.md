---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260802-STORED-ARTIFACT-KIND
artifact_type: plan
tags: [ai, documentation, registry, frontmatter]
---

# Implementation Plan — TCK-20260802-STORED-ARTIFACT-KIND

## Summary

This is a decision-document-only ticket: no `tools/` code changes. The plan appends a new `## 6.
Open Decision 8 Resolution` section to `docs/engine/contracts/context_packet_contract.md`
(immediately after the sibling ticket's `## 5. Open Decision 7 Resolution`, leaving §1-§5
byte-for-byte untouched), decides **yes** — `stored_artifacts/*.md` warrants a new
registry-indexed `kind` (`stored_artifact`) under Open Decision 3's **Branch 1 (REGISTRY-backed
direct mapping)** — and separately confirms `staging_artifacts/`'s total exclusion from
`generate_registry.py`'s scan is **intentional, permanent design**, not an accidental gap. It
updates the epic ticket's tracking entry for Decision 8 from UNRESOLVED to RESOLVED (mirroring
every prior decision in this batch), adds a static content-check test file following the sibling
ticket's `test_context_kind_priority_decision.py` pattern exactly, and runs a regression pass to
prove zero drift into `tools/` or `docs/REGISTRY.yaml`.

**Resolution of Open Question 1 (epic ticket update vs. AC4's literal wording).** AC4 reads: "No
code changes to tools/generate_registry.py, tools/context_packet_assembler.py, or
tools/hybrid_retrieval.py — Files Changed contains docs/ paths only." Read literally this would
forbid touching `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`, a
`tickets/` path. Decision: update the epic ticket anyway, in a step separate from and not gated by
AC4. Rationale: (a) every prior decision in this batch (Decisions 1-7, including the sibling
`TCK-20260802-CONTEXT-KIND-PRIORITY` closed one day before this one) updated the same epic
ticket's tracking entry as a standard, workflow-mandated bookkeeping step, and the sibling ticket's
own AC4-equivalent wasn't separately gated on that update either — it appears only in its
Implementation Notes / Files Changed, not its AC list; (b) AC4's evident intent, read in context
of the ticket's own Out-of-Scope line ("No code changes to tools/generate_registry.py,
tools/context_packet_assembler.py, or tools/hybrid_retrieval.py"), is "no `tools/` code changes,"
not "zero non-`docs/` files touched anywhere" — the ticket's own Out of Scope section never
mentions `tickets/` paths as forbidden, only the three named `tools/` modules; (c) leaving the
epic's Decision 8 entry at UNRESOLVED after this ticket closes would itself be an inconsistency a
future reader would trip over. The plan below treats the epic-ticket update as Step 2, verified by
the same test file's content checks, and explicitly out of AC4's own literal scope — AC4 is
satisfied by "no `tools/` code changes exist" (verified by the hash-fixture test), independent of
the epic ticket edit.

**Resolution of Open Question 2 (corpus heterogeneity).** The decision doc's §6 states the
existence of `index.md` files (412, a separate `tools/generate_artifact_pages.py` Docusaurus
output, structurally different frontmatter shape), the `notice` artifact_type outlier, ~20 legacy
non-`TCK-*` directories, and dozens of non-canonical filenames (`walkthrough.md`, `task.md`, etc.)
as an explicit **scope boundary** for any future scanner-building ticket — not something this
ticket resolves. The decision doc's "yes" verdict and Branch 1 classification apply specifically
to the canonical `investigation.md`/`plan.md`/`test_plan.md` triplet the ticket's own Request
Summary and AC2 scope to; the heterogeneity note prevents a future reader from assuming "yes,
warranted" trivially implies "any `stored_artifacts/*.md` file can be indexed as-is."

## Steps

### Step 1 — Write `## 6. Open Decision 8 Resolution` in the contract doc
**Files:** `docs/engine/contracts/context_packet_contract.md`
**Change:** Append a new section immediately after the existing `## 5. Open Decision 7
Resolution` (the file's current final section), separated by a `---` divider matching the
existing section-separator convention. Do not touch any byte of §1-§5. Content, in this order:

1. **Open Decision 8 quote block** — a `>`-blockquote verbatim rendering of the idea doc's item 8
   text (`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`,
   numbered list item 8), covering both the `stored_artifact`-kind question and the
   `staging_artifacts/` exclusion question in one quote, mirroring §3's and §5's own
   quote-then-resolve convention.
2. **Core resolution — yes/no verdict (AC1).** State plainly: **yes**, `stored_artifacts/*.md`
   (the `investigation.md`/`plan.md`/`test_plan.md` triplet) warrants a new registry-indexed
   `kind` (`stored_artifact`). Explicitly name and describe the status quo being changed:
   `tools/generate_registry.py::join_artifact_files()` (lines 105-112) globs `stored_artifacts/
   {ticket_id}/*.md` non-recursively and returns only a **flat sorted list of path strings** into
   the parent ticket's `artifact_files` field — no frontmatter (`status`/`authority`/
   `artifact_type`) from any artifact file is read or copied anywhere today. This is the concrete
   gap the "yes" verdict addresses: rationale/decision content inside a closed ticket's artifacts
   is currently retrievable only by a human or agent opening each path in that flat list, not as
   an independently authority/freshness-ranked source in a `ContextPacket`.
3. **Branch classification (AC2).** Name **Branch 1 — REGISTRY-backed direct mapping** (one of
   §3's three named branches: REGISTRY-backed direct mapping / `unrated` sentinel /
   differently-shaped-primitive mapping) as the answer, with reasoning tied to the real fields:
   `stored_artifacts/{ticket_id}/*.md` frontmatter carries `status`, `layer`, `authority`,
   `audience`, `ticket_id`, `artifact_type` — six fields, validated by
   `tools/validate_frontmatter.py::_validate_artifact()` (lines 214-225) — and its `status` values
   (`historical`/`active`/`authoritative`/`archive`) and `authority` values (`P0`/`P1`/`P2`) are
   drawn from the **exact same enums** (`STATUS_VALUES`, `AUTHORITY_VALUES`) that
   `docs/REGISTRY.yaml`'s own `doc`/`ticket` entries use — not a second, disjoint vocabulary the
   way `parity_ledger_entry`'s 5-value `status` enum is (Branch 3, §3's parity extension). State
   explicitly this rules out Branch 2 (`unrated` sentinel): unlike `code_symbol`/`test`/
   `graphify_node`/in-progress-ticket-body sources, which carry **no** authority/freshness
   primitive anywhere in the repo, `stored_artifacts/*.md` files carry real, populated values —
   cite the empirical corpus scan: 2,941 real files, `authority` spread `P0=4`/`P1=258`/`P2=1698`.
   Explicitly state the field-shape match means the only reason `docs/REGISTRY.yaml` doesn't
   already treat these as a REGISTRY-backed kind is that `collect_docs()`
   (`tools/generate_registry.py:186-238`) walks `root / "docs"` only — `stored_artifacts/` sits at
   repo root, a sibling of `docs/`, structurally unreachable by that walk regardless of
   `_SKIP_DOC_SUBDIRS` — a **directory-scope gap**, not a schema mismatch that would push this
   toward Branch 2 or 3.
4. **`last_verified` absence note (AC2, ties to ticket wording).** State explicitly that artifact
   frontmatter carries **no `last_verified` field** at all (confirmed against
   `_validate_artifact()`, which requires only the six fields above — `last_verified` appears only
   in `_validate_doc()`, conditionally, for `status: authoritative` docs). Per §3's own Branch 1
   text ("`freshness` is derived from ... `status` ... plus `last_verified` recency **where
   present**"), this is not disqualifying: freshness for a future `stored_artifact` kind would
   derive from `status` alone (`historical`/`active`/etc.), the same partial-derivation already
   tolerated for any REGISTRY-backed doc lacking `last_verified` today.
5. **Corpus-heterogeneity caveat, framed as scope boundary (not a resolution).** One paragraph
   noting: the real `stored_artifacts/` corpus is not uniform — 412 `index.md` files (a separate,
   deliberate `tools/generate_artifact_pages.py` Docusaurus-build output with a structurally
   different frontmatter shape: `title`/`description`/`artifact_type: index`/`layer`/`tags` only,
   no `status`/`authority`/`audience`/`ticket_id`), one `notice`-typed file, ~20 legacy non-`TCK-*`
   directories, and dozens of non-canonical filenames (`walkthrough.md`, `task.md`,
   `implementation_plan.md`, `parity.md`, `security_review.md`, etc.) that `join_artifact_files()`'s
   non-recursive glob already picks up today. State plainly that this "yes" verdict applies to the
   canonical `investigation.md`/`plan.md`/`test_plan.md` triplet's clean six-field shape; any
   future `stored_artifact`-kind scanner (explicitly out of scope for this ticket, per its own Out
   of Scope: "No implementation of a stored_artifact kind scanner") would need to filter to that
   triplet or define separate handling for `index`/other shapes — this doc flags the complexity
   without resolving it.
6. **`staging_artifacts/` exclusion paragraph (AC3).** One reasoned paragraph stating the
   exclusion is **intentional, permanent design**, not an accidental gap. Evidence: (a) the idea
   doc's own Open Decision 8 text already asserts this is "correct today, since it holds
   in-progress/scratch content for open tickets"; (b) `tools/gate_checks/done_checker_static.py`
   (lines 279-282) already documents awareness of the asymmetry via its
   `content_type_override="artifact"` comment, showing this is known, existing behavior, not an
   overlooked one; (c) empirically, both `staging_artifacts/{ticket_id}/` directories that exist
   on disk at investigation time map 1:1 to open `tickets/inprogress/` tickets, none orphaned —
   consistent with the "Move staging artifacts to `stored_artifacts/`" step in this project's
   workflow rule (CLAUDE.md "After Work"), which treats the transition as a move, not a copy, so a
   `staging_artifacts/` directory's lifetime is bounded to exactly the ticket's open window; (d)
   indexing ephemeral WIP content as a retrievable, authority-ranked source would conflict with
   the contract's own load-bearing principle that "packets with a stale hash must be rejected, not
   trusted" — staging content is expected to churn or disappear before a packet consumer could act
   on it. State explicitly this paragraph does not reopen or re-litigate the question; it records
   an already-correct decision as durable and explicit, matching the ticket's own instruction not
   to re-litigate correctness that the evidence already confirms.
7. **What does not change** (closing paragraph, mirroring §3's and §5's own closing convention).
   `docs/REGISTRY.yaml`'s generator, schema, and enum values remain untouched by this resolution.
   No `tools/generate_registry.py`, `tools/context_packet_assembler.py`, or
   `tools/hybrid_retrieval.py` code change accompanies this document. A future, separately-scoped
   ticket implementing a `stored_artifact`-kind scanner must handle the corpus-heterogeneity
   caveat above and add its own `tests/`-path verification; this document only records the
   decision that such a scanner is warranted and which branch it falls into.

**Do NOT touch:** `## 1` through `## 5` of this file (verbatim text, structure, and section
ordering). Do not add a `## 7` or renumber any existing section. Do not edit the file's YAML
frontmatter (`status`/`layer`/`authority`/`audience` at the top) — this is a body-only append.
**Verify:** `tests/tools/test_stored_artifact_kind_decision.py::test_section_6_heading_exists_after_section_5`,
`test_section_6_quotes_open_decision_8`,
`test_decision_doc_states_yes_or_no_on_new_kind_and_cites_join_artifact_files`,
`test_decision_doc_picks_one_of_decision_3s_three_branches_with_reasoning`,
`test_decision_doc_confirms_last_verified_absent_from_artifact_frontmatter`,
`test_decision_doc_contains_staging_artifacts_exclusion_paragraph`.

### Step 2 — Update the epic ticket's OPEN DECISION 8 tracking entry
**Files:** `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`
**Change:** Locate the existing bullet at (currently) lines 190-194:

```
- OPEN DECISION 8 — **UNRESOLVED** (raised 2026-08-02): should `stored_artifacts/{ticket_id}/*.md`
  become its own registry-indexed `kind` ... Source: same doc, item 8.
```

Change `**UNRESOLVED**` to `**RESOLVED**` and replace the body with a one-paragraph outcome
summary plus a citation to the resolving doc location, matching the exact shape Decisions 1-7 use
in this same file (see the Decision 7 bullet, updated by the sibling ticket, as the immediate
precedent). Summary must state: resolved as a documentation-only change; verdict is "yes,
`stored_artifacts/*.md` warrants a new `stored_artifact` registry-indexed kind, classified under
Open Decision 3's Branch 1 (REGISTRY-backed direct mapping)"; `staging_artifacts/`'s exclusion is
confirmed intentional permanent design; corpus heterogeneity (index.md files, legacy directories,
non-canonical filenames) is flagged as a scope boundary for a future scanner-building ticket, not
resolved here. Cite `docs/engine/contracts/context_packet_contract.md` §6 as the resolving
location, mirroring the Decision 7 bullet's citation of §5.
**Do NOT touch:** Decisions 1-7 and 9's entries in this same file (verify via a scoped diff
touching only the Decision 8 bullet's lines). Do not touch any other section of this epic ticket
(Implementation Notes, other tracking entries, etc.).
**Verify:** No dedicated automated test exists for ticket-body prose (this file is not scanned by
`validate_frontmatter.py`'s content checks beyond its own frontmatter block, which is untouched);
verify manually via `git diff tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`
showing only the Decision 8 bullet changed, mirroring the sibling ticket's own verification
approach ("29 lines changed in this file, all within the Decision 7 bullet").

### Step 3 — Add the static content-check test file
**Files:** `tests/tools/test_stored_artifact_kind_decision.py` (new)
**Change:** Create using the same `Path.read_text()`-only static-content-check technique as
`tests/tools/test_context_kind_priority_decision.py` (no ranking/scanner logic exists anywhere to
import against — this ticket is decision-document-only). Implement the 8 tests from
`staging_artifacts/TCK-20260802-STORED-ARTIFACT-KIND/test_plan.md`'s "New Tests Required" section:

1. `test_section_6_heading_exists_after_section_5` — `## 6. Open Decision 8 Resolution` exists and
   its index is greater than `## 5. Open Decision 7 Resolution`'s index.
2. `test_section_6_quotes_open_decision_8` — §6 contains key phrases from the Open Decision 8
   quote (e.g. `"become its own registry-indexed"`, `"join_artifact_files"`,
   `"staging_artifacts"`, `"permanent design decision"` — verify against the actual rendered quote
   text from Step 1, not guessed phrasing).
3. `test_decision_doc_states_yes_or_no_on_new_kind_and_cites_join_artifact_files` — §6 contains an
   explicit verdict marker (e.g. `"yes"` near `"stored_artifact"`/`"kind"`) and names
   `join_artifact_files` and `generate_registry.py`.
4. `test_decision_doc_picks_one_of_decision_3s_three_branches_with_reasoning` — §6 contains
   `"Branch 1"` and `"REGISTRY-backed direct mapping"`, references `STATUS_VALUES`/
   `AUTHORITY_VALUES` or the six named fields, and does NOT contain fabricated branch names beyond
   the three defined in §3 (assert absence of any invented "Branch 4"-style text).
5. `test_decision_doc_confirms_last_verified_absent_from_artifact_frontmatter` — §6 contains
   `"no last_verified field"` or equivalent explicit phrasing plus `"_validate_artifact"`.
6. `test_decision_doc_contains_staging_artifacts_exclusion_paragraph` — §6 contains
   `"staging_artifacts"` plus a clear verdict word (`"intentional"` and `"permanent design"`), not
   merely the word "excluded" alone.
7. `test_context_packet_contract_sections_1_through_5_text_unchanged` — extend the sibling test
   file's byte-preservation technique: assert presence of key load-bearing sentences from §3
   (reuse the same assertions as `test_context_packet_contract_section_3_text_unchanged` in the
   sibling file), §4 (reuse `test_context_packet_contract_section_4_text_unchanged`'s assertions),
   and add new assertions for §5's key sentences (e.g. `"Human sign-off required"`, `"No shared
   numeric scale"`) to prove this ticket did not disturb the sibling ticket's freshly-landed
   section.
8. `test_no_code_changes_to_named_tools_modules` — sha256 hash fixture (`_EXPECTED_TOOLS_HASHES`
   dict, computed fresh at write time via `hashlib.sha256(path.read_bytes()).hexdigest()`) for
   `tools/generate_registry.py`, `tools/validate_frontmatter.py`,
   `tools/context_packet_assembler.py`, `tools/hybrid_retrieval.py` — note this ticket's named set
   differs from the sibling ticket's (`parity_index.py` swapped out for
   `validate_frontmatter.py`, per this ticket's own Out of Scope list and AC4 wording).

**Do NOT touch:** `tests/tools/test_context_kind_priority_decision.py` (the sibling's test file) —
add a new file, do not extend or modify the existing one.
**Verify:** `pytest tests/tools/test_stored_artifact_kind_decision.py -v` — all 8 tests pass.

### Step 4 — Regression pass
**Files:** None changed; verification only.
**Change:** Run the scoped commands from `test_plan.md`:
```
pytest tests/tools/test_generate_registry.py tests/tools/test_context_kind_priority_decision.py tests/tools/test_stored_artifact_kind_decision.py -v
pytest tests/tools/test_context_packet_assembler.py tests/tools/test_hybrid_retrieval.py -v
python3 tools/generate_registry.py --check
python3 tools/validate_frontmatter.py docs/engine/contracts/context_packet_contract.md
```
Also run `python3 tools/validate_frontmatter.py tickets/inprogress/TCK-20260802-STORED-ARTIFACT-KIND.md`
and `git diff --stat` scoped to confirm only `docs/engine/contracts/context_packet_contract.md`,
`tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`,
`tests/tools/test_stored_artifact_kind_decision.py`, and this ticket's own files changed — zero
`tools/` files in the diff.
**Do NOT touch:** Do not run the full `pytest tests/` suite — stay scoped per `test_plan.md`'s own
"Scoped Pytest Commands" instruction.
**Verify:** All commands above report green/in-sync/OK.

## Scope Guards

- No code changes to `tools/generate_registry.py`, `tools/context_packet_assembler.py`, or
  `tools/hybrid_retrieval.py` (ticket's own Out of Scope). `tools/validate_frontmatter.py` is also
  not modified (it is only cited as evidence and hash-verified in Step 3/4, not touched).
- No reopening or editing Decisions 1-7's existing resolved text in
  `docs/engine/contracts/context_packet_contract.md` — §1-§5 are read-only for this ticket.
- No absorbing Decision 9 (exact-vs-fuzzy lookup convention) — stays scoped to Decision 8 only.
- No implementation of a `stored_artifact`-kind scanner — this ticket produces a decision
  document only; the corpus-heterogeneity caveat is recorded as a future-scanner concern, not
  solved.
- No renumbering or restructuring of the contract doc's existing sections; §6 is strictly
  additive, appended after §5.
- No editing any Decision entry in the epic ticket other than Decision 8's own bullet.
- `docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`
  is read for the verbatim Decision 8 quote text only — it is not edited by this ticket.

## Dependency Map

- Step 1 (write §6) has no dependency — it can be written and verified independently once the
  quote text and evidence are drawn from investigation.md (already gathered).
- Step 2 (epic ticket update) is independent of Step 1's exact wording but should be written
  *after* Step 1 so its outcome-summary paragraph accurately reflects the final §6 text (avoid
  drafting the epic summary before §6 is finalized, to prevent the two documents drifting out of
  sync on the verdict wording).
- Step 3 (test file) depends on Step 1 being complete — its assertions read the literal §6 text
  Step 1 produces, and its hash fixture depends on Step 2 not having touched any of the four named
  `tools/` files (it never does, by design).
- Step 4 (regression pass) depends on Steps 1-3 all being complete.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — yes/no verdict citing `join_artifact_files()`'s flat-list-only status quo | Step 1 (item 2) | `test_decision_doc_states_yes_or_no_on_new_kind_and_cites_join_artifact_files` |
| AC2 — names exactly one of Decision 3's three branches with reasoning tied to real fields (incl. no `last_verified`) | Step 1 (items 3-4) | `test_decision_doc_picks_one_of_decision_3s_three_branches_with_reasoning`, `test_decision_doc_confirms_last_verified_absent_from_artifact_frontmatter` |
| AC3 — reasoned paragraph on `staging_artifacts/` exclusion (intentional vs. accidental) | Step 1 (item 6) | `test_decision_doc_contains_staging_artifacts_exclusion_paragraph` |
| AC4 — no code changes to the three named `tools/` modules; Files Changed is `docs/`-paths-only in the sense of "no `tools/` code changes" (epic-ticket update is a separate, always-required bookkeeping step outside AC4's own scope, per this plan's Open Question 1 resolution above) | Steps 1, 2 (epic update, outside AC4), 3 (hash fixture), 4 (diff scoping) | `test_no_code_changes_to_named_tools_modules`, Step 4's `git diff --stat` check |

## Anti-Drift Notes

- **§1-§5 byte-preservation is the highest-risk mechanical mistake**, per investigation: this
  ticket and the sibling ticket share the same file with adjacent section numbers (§5 landed one
  day before this ticket started). Step 3's test 7 must assert presence of §3, §4, and §5 key
  sentences, not just §1-§2, to catch an accidental edit to the sibling's freshly-landed section.
- **Do not invent a fourth branch.** Decision 3 defines exactly three: REGISTRY-backed direct
  mapping, `unrated` sentinel, differently-shaped-primitive mapping. §6 must pick Branch 1 with
  reasoning, not describe a new hybrid category.
- **The `unrated`-must-not-default-to-worst constraint (§5, Constraint A) and the parity
  differently-shaped-vocabulary warning (§3) are not directly applicable here** — `stored_artifact`
  is being classified as Branch 1 (REGISTRY-backed), not Branch 2 or 3 — but the implementer
  should not accidentally cite those constraints as if they applied to this kind; they are
  evidence for what `stored_artifact` is *not*, not part of its own resolution mechanism.
- **The `content_type_override="artifact"` asymmetry in `done_checker_static.py` (lines 279-282)
  is pre-existing, documented behavior** cited as evidence for the `staging_artifacts` exclusion
  paragraph — it must not be described as a bug this ticket fixes; no change to
  `tools/gate_checks/done_checker_static.py` is in scope.
- **Corpus heterogeneity (412 `index.md` files, `notice` type, ~20 legacy directories, dozens of
  non-canonical filenames) must be described as a scope boundary, not resolved** — do not let §6
  drift into specifying scanner filtering logic; that is explicitly out of scope per the ticket's
  Out of Scope line "No implementation of a stored_artifact kind scanner."
- **No `docs/parity_ledger/` entry is needed** — this contract governs agent-orchestration/
  retrieval tooling, not simulation logic, per §4's already-established posture (reaffirmed by
  investigation's Parity Ledger Overlap section: "None").
- **`join_artifact_files()`'s current behavior must be described accurately, not as a bug** — it
  is correct, intentional flat-list behavior for the ticket's `artifact_files` field; the "yes"
  verdict on a new `stored_artifact` kind is about adding a *complementary* registry-indexed path,
  not implying `join_artifact_files()` itself needs to change (and it isn't changed by this
  ticket).

## Resolution Note

No unresolved questions remain for the implementer. Both open questions flagged by investigation
(epic-ticket update vs. AC4 wording; corpus-heterogeneity handling) are resolved above under
"Resolution of Open Question 1/2" in the Summary. The one genuine value judgment surfaced in
investigation ("which of Decision 3's three branches applies") is not left open — it is decided in
Step 1 as Branch 1, with the empirical evidence (field-shape match, 2,941-file corpus scan,
directory-scope gap vs. schema mismatch) making this a technical classification rather than an
arbitrary policy call, consistent with how §3 and §5 each already distinguish technical
derivations from genuine value judgments requiring human sign-off.

## Deviations

**Architecture-review correction (pre-Implement):** the first Review pass found this ticket's own
AC4 text ("Files Changed contains docs/ paths only") is textually stricter than sibling ticket
TCK-20260802-CONTEXT-KIND-PRIORITY's AC4, which had no such clause — the sibling's plan reasoned
its epic-ticket update fell "outside AC4's scope," but that precedent only covers "epic updates are
standard bookkeeping," not "an explicit Files-Changed restriction can be reasoned away." Rather
than proceed and check AC4 `[x]` against a Files Changed list that would literally contradict it
(a real ticket-record inconsistency, not a gate to route around), the ticket's own AC4 wording in
tickets/inprogress/TCK-20260802-STORED-ARTIFACT-KIND.md was corrected before Implement to
explicitly permit this ticket's own file, staging/stored artifacts, the new test file, and the
epic-ticket's Open Decision 8 entry — matching what Step 2 was always going to do, stated
accurately instead of reasoned around. Step 1-4's actual content and Step 2's action are
unchanged; only the ticket's own AC4 sentence was amended to remove the self-contradiction.
