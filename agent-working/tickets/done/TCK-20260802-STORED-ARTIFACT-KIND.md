---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260802-STORED-ARTIFACT-KIND
phase: done
date: 2026-08-02
tags: [ai, documentation, registry, frontmatter]
---

# TCK-20260802-STORED-ARTIFACT-KIND

## Title
Decide whether stored_artifacts/ becomes a registry-indexed retrieval kind, and confirm staging_artifacts/'s exclusion is intentional (Open Decision 8)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
We want to know whether stored_artifacts/{ticket_id}/*.md (investigation.md/plan.md/test_plan.md, real frontmatter — artifact_type, status, authority) is sufficient to justify a new registry-indexed kind (e.g. stored_artifact), so decision/rationale content buried in a closed ticket's artifacts is retrievable on its own terms instead of only via the parent ticket's flat artifact_files path list (generate_registry.py::join_artifact_files()). If warranted, this should document the authority/freshness rule following Decision 3's pattern, not invent new vocabulary. Relatedly, we need a reasoned confirmation of whether staging_artifacts/'s total exclusion from generate_registry.py's scan is a correct permanent design decision or an accidental gap.

## Scope
- Produce a decision document evaluating whether stored_artifacts/{ticket_id}/*.md warrants a new registry-indexed kind (stored_artifact), following Open Decision 3's authority/freshness population pattern.
- Include a reasoned paragraph confirming whether staging_artifacts/'s total exclusion from generate_registry.py's scan is intentional permanent design or an accidental gap.
- Extend docs/engine/contracts/context_packet_contract.md (or add a named sibling doc) with the new decision, without altering existing resolved text.

## Out of Scope
- No code changes to tools/generate_registry.py, tools/context_packet_assembler.py, or tools/hybrid_retrieval.py.
- No reopening or amending Open Decisions 1-6 or context_packet_contract.md's already-resolved §3 text.
- No implementation of a stored_artifact kind scanner — decision-document only.
- Do not absorb Decision 7's cross-kind ranking question; stay scoped to Decision 8 only.

## Acceptance Criteria
- [x] Decision doc states yes/no on whether stored_artifacts/*.md warrants a new registry-indexed kind, explicitly citing generate_registry.py::join_artifact_files()'s current flat-list-only behavior as the status quo being evaluated.
- [x] If warranted, the doc specifies exactly which of Open Decision 3's three authority/freshness population branches (REGISTRY-backed direct mapping / unrated sentinel / differently-shaped-primitive mapping) stored_artifact frontmatter falls into, with explicit reasoning tied to its real fields (status, layer, authority, audience, ticket_id, artifact_type — no last_verified).
- [x] Doc contains an explicit reasoned paragraph confirming whether staging_artifacts/'s total exclusion from generate_registry.py's scan is intentional permanent design or an accidental gap.
- [x] No code changes to tools/generate_registry.py, tools/context_packet_assembler.py, or tools/hybrid_retrieval.py — Files Changed contains only docs/ paths, this ticket's own file, staging/stored artifacts, a new test file, and (per this batch's established Related-Tickets/epic-tracking convention, as TCK-20260802-CONTEXT-KIND-PRIORITY already did for Decision 7) the epic ticket's own Open Decision 8 entry — no other ticket, config, or workflow file.

## Related Tickets
- TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC
- TCK-20260728-CONTEXT-PACKET-SCHEMA
- TCK-20260728-DEFAULT-PACKET-CRITERIA
- TCK-20260728-CODE-TEST-INDEX-BOUNDARIES
- TCK-20260731-PARITY-INDEX-BASELINE
- TCK-20260731-PARITY-INDEX-IMPORTER
- TCK-20260731-PARITY-READPATH-GATE

## Related Docs
- docs/engine/contracts/context_packet_contract.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_opendecisions_7_9.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/generate_registry.py
- tools/validate_frontmatter.py
- tests/tools/test_generate_registry.py
- stored_artifacts/TCK-20260728-CONTEXT-PACKET-SCHEMA/investigation.md
- tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md

## Assumptions / Open Questions
- Whether stored_artifacts frontmatter (status/authority, no last_verified, not top-level-scanned) qualifies as "REGISTRY-backed" under Decision 3's own definition is a genuine judgment call requiring explicit argument in the doc — not to be silently pre-resolved in this ticket's scope/AC.
- Risk of mis-tiering as an implementation ticket rather than a documentation-only decision ticket; scope stays decision-doc-only.
- Keep scoped to Decision 8 only; do not absorb Decision 7's cross-kind ranking question.

## Implementation Notes

This ticket's Implement phase was interrupted mid-task by an API spend limit in a prior session.
That session completed Step 1 (contract doc §6) and Step 2 (epic ticket Decision 8 tracking entry)
correctly, and wrote most of Step 3 (the test file) — but left one test assertion broken and never
ran Step 4 (regression pass) or filled in this ticket's own paperwork. This session resumed from
that interrupted state: it independently re-verified Steps 1-2 were genuinely correct (read the
actual §6 text and the epic ticket's Decision 8 bullet directly, rather than trusting the resuming
prompt's claim), fixed the one failing test, ran the full regression pass, and completed this
paperwork.

- **Step 1 (contract doc §6)** — verified correct as written by the prior session.
  `docs/engine/contracts/context_packet_contract.md` §6 ("Open Decision 8 Resolution") is appended
  cleanly after §5 with a `---` divider, quotes Open Decision 8 verbatim as a blockquote, states the
  "yes" verdict citing `join_artifact_files()`'s current flat-list-only behavior, classifies
  `stored_artifact` under Open Decision 3's Branch 1 (REGISTRY-backed direct mapping) with reasoning
  tied to the real six-field frontmatter shape and the shared `STATUS_VALUES`/`AUTHORITY_VALUES`
  enums, notes the absence of `last_verified` from artifact frontmatter, flags corpus heterogeneity
  (412 `index.md` files, legacy directories, non-canonical filenames) as an unresolved scope
  boundary for a future scanner ticket, and confirms `staging_artifacts/`'s total exclusion is
  intentional permanent design with four supporting points of evidence. §1-§5 are untouched (`git
  diff` on the file shows 196 insertions, 0 deletions — a pure append).
- **Step 2 (epic ticket Decision 8 entry)** — verified correct. The OPEN DECISION 8 bullet in
  `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md` reads **RESOLVED**, citing
  `TCK-20260802-STORED-ARTIFACT-KIND` and `docs/engine/contracts/context_packet_contract.md` §6, and
  summarizes the same verdict as §6. `git diff` on the epic ticket shows only Decision 8's own
  bullet (plus the pre-existing Related Tickets list addition) changed — no edits to Decisions 1-7
  or 9.
- **Step 3 (test file) — fixed the one failing test.**
  `tests/tools/test_stored_artifact_kind_decision.py::test_section_6_quotes_open_decision_8` was
  asserting the literal contiguous substring `"become its own registry-indexed"` against the raw
  file text, but the actual §6 blockquote wraps that phrase across a markdown line break with a
  `"> "` continuation prefix in the middle (`"...become its own\n> registry-indexed..."`), so the
  substring never appears contiguously in the raw text. This was a test brittleness bug, not a
  content bug — the underlying §6 content correctly quotes Decision 8's substance. Fixed by adding a
  `_normalize_whitespace()` helper that strips leading `"> "` blockquote markers per line (via
  `re.sub(r"(?m)^>\s?", "", text)`) and then collapses all whitespace runs to single spaces (`re.sub(r"\s+", " ", ...)`)
  before the substring check, so the assertion is robust to blockquote line-wrapping without
  weakening what it verifies. The other three assertions in that same test (`join_artifact_files`,
  `staging_artifacts`, `permanent design decision`) were already passing against the raw text and
  were left unchanged.
- **Step 4 (regression pass) — run for the first time this session, all green.**
  `pytest tests/tools/test_generate_registry.py tests/tools/test_context_kind_priority_decision.py
  tests/tools/test_stored_artifact_kind_decision.py -v` → 70 passed.
  `pytest tests/tools/test_context_packet_assembler.py tests/tools/test_hybrid_retrieval.py -v` → 32
  passed. `python3 tools/generate_registry.py --check` → in sync (1577 entries). `python3
  tools/validate_frontmatter.py docs/engine/contracts/context_packet_contract.md` → OK, no
  violations. `python3 tools/validate_frontmatter.py
  tickets/inprogress/TCK-20260802-STORED-ARTIFACT-KIND.md` → OK, no violations. `git diff --stat`
  scoped to this ticket's two touched pre-existing files confirms a clean, purely-additive diff (235
  insertions, 0 deletions across `docs/engine/contracts/context_packet_contract.md` and
  `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md`); none of the four named
  `tools/` modules (`generate_registry.py`, `context_packet_assembler.py`, `hybrid_retrieval.py`,
  `validate_frontmatter.py`) appear in the diff, confirmed both by `git status`/`git diff --stat`
  and by the test file's own sha256 hash-fixture guard (`test_no_code_changes_to_named_tools_modules`).
  Note: the working tree at investigation time also carried a large amount of unrelated,
  already-uncommitted work from other tickets in this same batch (e.g.
  `TCK-20260802-CONTEXT-KIND-PRIORITY`, `TCK-20260802-DOC-COVERAGE-CHECK`, changes to
  `tools/gate_checks/done_checker_static.py`, `docs/REGISTRY.yaml`, `agent-monitoring/`, etc.) — none
  of that is this ticket's own work; this ticket's own diff is scoped to exactly the two
  pre-existing files plus the new test file and this ticket file itself, as confirmed above.
- No deviations beyond the known test bug fix were found; nothing was added to
  `staging_artifacts/TCK-20260802-STORED-ARTIFACT-KIND/plan.md`'s Deviations section this session.

## Test Summary
- `pytest tests/tools/test_stored_artifact_kind_decision.py -v` — 11/11 passed (was 10/11 before this
  session's fix).
- `pytest tests/tools/test_generate_registry.py tests/tools/test_context_kind_priority_decision.py
  tests/tools/test_stored_artifact_kind_decision.py -v` — 70/70 passed.
- `pytest tests/tools/test_context_packet_assembler.py tests/tools/test_hybrid_retrieval.py -v` —
  32/32 passed.
- `python3 tools/generate_registry.py --check` — in sync, 1577 entries, no drift.
- `python3 tools/validate_frontmatter.py docs/engine/contracts/context_packet_contract.md` — OK, no
  violations.
- `python3 tools/validate_frontmatter.py tickets/inprogress/TCK-20260802-STORED-ARTIFACT-KIND.md` —
  OK, no violations.
- No pre-existing test was modified other than the one assertion fix described above; the full
  `pytest tests/` suite was intentionally not run, per this ticket's own `test_plan.md` scoped-command
  instruction.

## Files Changed
- `docs/engine/contracts/context_packet_contract.md` — added `## 6. Open Decision 8 Resolution`
  after §5 (prior session; verified correct this session, not re-edited).
- `tickets/inprogress/TCK-20260728-CONTEXT-EFFICIENT-RETRIEVAL-EPIC.md` — OPEN DECISION 8 bullet
  changed from UNRESOLVED to RESOLVED (prior session; verified correct this session, not re-edited).
- `tests/tools/test_stored_artifact_kind_decision.py` (new) — 11 static content-check tests against
  the contract doc's §6, plus a sha256 hash-fixture guard on the four named `tools/` modules; one
  test assertion (`test_section_6_quotes_open_decision_8`) fixed this session for blockquote
  line-wrap robustness.
- `tickets/inprogress/TCK-20260802-STORED-ARTIFACT-KIND.md` (this file) — paperwork completed this
  session: all 4 Acceptance Criteria checked, Status set to DONE, Implementation Notes / Test
  Summary / Files Changed / Completion Summary filled in.

## Completion Summary
Open Decision 8 is resolved: `stored_artifacts/{ticket_id}/*.md`'s canonical
`investigation.md`/`plan.md`/`test_plan.md` triplet warrants a new registry-indexed `stored_artifact`
kind under Open Decision 3's Branch 1 (REGISTRY-backed direct mapping), and `staging_artifacts/`'s
total exclusion from `generate_registry.py`'s scan is confirmed intentional, permanent design. The
resolution is recorded in `docs/engine/contracts/context_packet_contract.md` §6 and mirrored in the
epic ticket's Decision 8 tracking entry, both landed correctly by the prior (spend-limit-interrupted)
session. This session verified that work, fixed one brittle test assertion in the new static
content-check test file (a markdown-blockquote line-wrap issue, not a content defect), ran the full
scoped regression pass with all commands green, and completed this ticket's paperwork. No code
changes were made to `tools/generate_registry.py`, `tools/context_packet_assembler.py`,
`tools/hybrid_retrieval.py`, or `tools/validate_frontmatter.py` — verified by hash fixture and diff
inspection. All 4 Acceptance Criteria are satisfied.
