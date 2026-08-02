---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260802-DOC-UPDATE-DISCIPLINE
artifact_type: plan
tags: [workflows, documentation]
---

# Plan — TCK-20260802-DOC-UPDATE-DISCIPLINE

## Step 1 — `tools/gate_checks/doc_staleness_check.py`: broaden flagged paths, add advisory check

**File:** `tools/gate_checks/doc_staleness_check.py`

- Add `config/` to the flagged-prefix set alongside `src/` and `.claude/workflows/*.js` in
  `check_doc_staleness`'s `flagged_paths` comprehension.
- Add an optional third parameter `docs_to_update: List[str] = None`. When non-empty, compute
  `missing = [d for d in docs_to_update if d not in files_changed]`; if `missing` is non-empty,
  append (not replace) an `{"status": "ADVISORY", "evidence": ...}` entry to the returned list —
  only reached on the non-`FAIL` path, since `FAIL` already returns early.
- Update `__main__`: parse `sys.argv[2:]` for an optional `--docs-to-update` sentinel; everything
  before it is `files_changed`, everything after is `docs_to_update`. Absent sentinel → unchanged
  behavior (`docs_to_update=[]`).
- **Do not touch** the existing `FAIL`/`PASS` early-return logic beyond adding `config/` to the
  prefix list — the advisory branch is strictly additive.

**Do NOT touch:** the module's `MARKER:`-prefixed JSON CLI contract, the docstring's ticket-history
framing (append, don't rewrite).

**Verify:** `tests/tools/test_doc_staleness_check.py`'s 9 existing tests pass unmodified; add new
tests per test_plan.md.

---

## Step 2 — `.claude/workflows/implement-ticket.js`: Investigate phase gets a schema

**File:** `.claude/workflows/implement-ticket.js`, Investigate block (~lines 470-509)

- Add `INVESTIGATION_SCHEMA` (new const, placed right after `phase('Investigate')` and before
  `investigationTs`), requiring `docs_to_update: string[]` and `findings_summary: string`.
- Pass `schema: INVESTIGATION_SCHEMA` to the `investigator` `agent()` call.
- Update the investigation.md sections list in the prompt to insert `Docs Requiring Update` between
  `Mechanics/Engine Constraints` and `Parity Ledger Overlap`.
- Change the prompt's closing `Return:` line from free prose to explicit
  `docs_to_update` / `findings_summary` field descriptions (mirrors the `REVIEW_SCHEMA` prompt
  pattern already used a few blocks below for `architecture-reviewer`).
- Change `investigationText = investigation.toString().trim()` → `investigationText =
  investigation.findings_summary`.
- Change the hotfix-tier default at the top of the function from
  `let investigation = '(hotfix — investigation skipped)'` to
  `let investigation = { docs_to_update: [], findings_summary: '(hotfix — investigation skipped)' }`
  so `investigation.docs_to_update` is always safe to read later regardless of tier, with no
  tier-conditional branch needed at the read site.

**Do NOT touch:** the Plan/Review phase prompts' own reads of `investigationText` (unchanged shape,
still a string).

---

## Step 3 — `.claude/agents/investigator.md`: mirror the schema in the agent's own contract

**File:** `.claude/agents/investigator.md`

- Add a `## Docs Requiring Update` section to the `investigation.md` structure template (between
  `## Mechanics / Engine Constraints` and `## Parity Ledger Overlap`): "Every specific `docs/` path
  this ticket must change if implemented as scoped, with a one-line reason each. Empty/'None' only
  if no doc anywhere needs to change — this is a deliberate judgment, not a lazy default."
- Change the final `## Output` section's return contract from freeform prose to explicit
  `docs_to_update` (array) + a one-sentence findings summary, matching the JS schema exactly.

---

## Step 4 — `.claude/workflows/implement-ticket.js`: broaden `behavior_changed` guidance

**File:** `.claude/workflows/implement-ticket.js`, Implement block (~lines 710-753)

- Add a `description` to `IMPL_SCHEMA.properties.behavior_changed`: "True for ANY new logic, new
  feature, or new setting/config value this ticket introduces — not only modifications to behavior
  that already existed. A brand-new feature has no prior behavior to diverge from, but it still
  counts as `true`."
- Add one clarifying sentence to the Implement prompt itself, immediately before the closing
  `Return:` line, repeating the same guidance in prose (schema `description` fields are not always
  surfaced identically to the agent depending on how the harness renders them — the existing
  pattern in this file duplicates important constraints in both schema description and prompt body,
  e.g. `mistag_warning`).

---

## Step 5 — `.claude/workflows/implement-ticket.js`: wire `docs_to_update` into the post-Implement check

**File:** `.claude/workflows/implement-ticket.js`, post-Implement doc-staleness block (~lines
755-802)

- Before the `docStalenessOutput` bash() call: `const docsToUpdate =
  Array.isArray(investigation.docs_to_update) ? investigation.docs_to_update : []` (defensive —
  `investigation` is always an object per Step 2, but stay defensive in case a future edit changes
  the hotfix default again) and build `docsToUpdateArgs` (empty string when `docsToUpdate.length ===
  0`, else `--docs-to-update ${docsToUpdate.map(d => \`"${d}"\`).join(' ')}`).
- Append `${docsToUpdateArgs}` to the existing single-line bash template string — keep
  `implementation.behavior_changed` and `docStalenessFilesArgs` substrings present and on the same
  line (required by `test_doc_staleness_check_passes_behavior_changed_and_files_changed`).
- After parsing `docStalenessResults`, add `const docStalenessAdvisory = docStalenessResults &&
  docStalenessResults.find(r => r.status === 'ADVISORY')`.
- Precompute the event summary in a `const` (mirrors the `parityEvidence` pattern in the Parity
  phase) rather than inlining a nested ternary directly into the `pushEvent(...)` call — this is
  required to keep `test_doc_staleness_blocked_status_has_no_reason_code`'s naive
  `)\n`-substring-based call-boundary detection working (a multi-line nested-paren ternary inlined
  directly risks a premature match). Keep exactly one `pushEvent(...)` call in this block —
  `test_doc_staleness_failure_folds_into_the_single_implement_event_not_a_second_one` asserts this.
- When `docStalenessAdvisory` is present, add one `log(...)` warning line — never change `status`,
  never add a second `pushEvent`.

---

## Step 6 — `.claude/workflows/implement-ticket.js`: Finalize runs `make knowledge-index-update`

**File:** `.claude/workflows/implement-ticket.js`, Finalize block (~lines 1259-1421)

- After the `finalizeFailures.length > 0` early-return check (Finalize's own migration self-check
  must have already passed) and before the `pushEvent('Finalize', 'finalizer', 'ok', ...)` line, add
  an orchestrator-run (not agent-prompt) block:
  1. `const docsChangedOutput = await bash(\`git status --porcelain -- docs/ 2>/dev/null\`)`
  2. If non-empty, run `make knowledge-index-update 2>&1 || echo "REINDEX_FAILED"` via `bash()`.
  3. On `REINDEX_FAILED`, `log('WARNING: ...')` — **never** change `finalizeResults`/`status`, never
     return early. Matches the fail-open convention already used for the monitoring-write
     self-check and tag-drift check immediately below in the same phase.
- Do **not** add this as a step inside the Finalize agent's own prompt text — `docs/ai/
  ticket-lifecycle.md`'s existing Reliability caveat for the post-Test cleanup checkpoint documents
  that a bare, non-`phase()`-anchored bash instruction inside agent prose has been observed to
  silently not execute. This step must be orchestrator-run to be reliable.

---

## Step 7 — `docs/ai/ticket-lifecycle.md`: keep doc/code in parity

**File:** `docs/ai/ticket-lifecycle.md`

- Investigate section: mention the `docs_to_update` field / "Docs Requiring Update" artifact
  section.
- Implement section: mention the broadened `behavior_changed` definition (new logic/feature/setting,
  not just modified existing behavior) and the advisory doc-relevance check.
- "Gate (doc staleness)" paragraph: mention `config/` is now a flagged prefix alongside `src/` and
  `.claude/workflows/*.js`, and that a separate, non-blocking `ADVISORY` signal now exists for
  specific-doc mismatches.
- Finalize section: add a numbered step for the `make knowledge-index-update` refresh, fail-open,
  after the existing self-verification/monitoring-write steps.

---

## Acceptance Criteria Map

| AC | Step(s) |
|---|---|
| `## Docs Requiring Update` section + `docs_to_update` field | 2, 3 |
| Investigate schema requires `docs_to_update` | 2 |
| `behavior_changed` guidance broadened | 4 |
| `config/` flagged like `src/`/workflows | 1 |
| `docs_to_update` optional param + `ADVISORY` result | 1, 5 |
| Finalize runs `make knowledge-index-update` | 6 |
| `docs/ai/ticket-lifecycle.md` parity | 7 |
| Tests for new behavior | (test_plan.md) |

## Dependency Map

Step 1 (Python) is independent and should land first — Step 5 (JS) depends on its new
`--docs-to-update` CLI contract. Steps 2/3/4 (JS Investigate schema + agent doc + behavior_changed
guidance) are independent of Step 1 and can land in any order relative to it. Step 5 depends on
Steps 1 and 2 (needs both the new CLI param and `investigation.docs_to_update` to exist). Step 6 is
fully independent. Step 7 (docs) should land last, once the actual code shape is final, to avoid
describing behavior that then changes.

## Open-Question Status

No unresolved questions remain — the one open design decision (advisory vs. blocking) was resolved
with the user before this plan was written (see ticket's Request Summary and investigation.md's
Risks section). Deliberately not using a literal `## Unresolved Questions` heading here: the
Plan-phase gate (`tools/gate_checks/plan_gate_static.py::plan_has_unresolved_questions_heading`)
triggers on heading *presence* alone, not body content — an empty/"None" body under that exact
heading would still pause the workflow for human review.
