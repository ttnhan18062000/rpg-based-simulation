---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION
artifact_type: plan
tags: [ai, agent-monitoring, data-quality, documentation]
---

# Implementation Plan — TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION

## Summary

This is a pure-documentation ticket: no `src/` or `tools/` behavior changes, no new registrations.
The plan creates one new committed doc — `docs/guidelines/artifact_retention_classification.md` —
containing an 8-row, 4-column retention-classification table (artifact class / classification from
the 4-way taxonomy / recommended treatment / evidence-reference) that resolves both previously-open
questions (`graphify-out/`, `knowledge-index/`) with the concrete evidence `investigation.md` already
gathered and this plan independently re-verified against the live repo. It adds a matching doc-structure
test file, makes one small precision edit to `docs/guidelines/agent_working_environment.md`'s existing
"Other Local, Gitignored Caches" table (adding the missing `graphify-out/graph.json` row and fixing the
now-inaccurate "one of three" / MCP-only framing), and updates `telemetry_retention_epic.md`'s M2
section to record that this ticket ships it — mirroring the epic doc's existing M1 "superseded" inline
note pattern. Verification is entirely static/doc-structure: registry regeneration, frontmatter/tag/layer
validation, the new pytest file, and a manual re-check of every cited `file:line` against the real repo
at Verify time (not a copy-forward of this plan's own citations).

## Steps

### Step 1 — Create the new retention-classification doc
**Files:** `docs/guidelines/artifact_retention_classification.md` (new file)

**Change:** Create the file with exactly this frontmatter (verified against
`registries/layer_registry.jsonl:10` — `guidelines` is a registered layer — and
`registries/tag_registry.jsonl` — all four tags (`ai`, `agent-monitoring`, `data-quality`,
`documentation`) are registered under category `meta-process`, added 2026-07-06):

```yaml
---
status: active
layer: guidelines
authority: P1
audience: agent
tags: [ai, agent-monitoring, data-quality, documentation]
---
```

Rationale for each field, cited against sibling docs in the same directory (not guessed): `status:
active` and `authority: P1` match the two closest structural precedents in `docs/guidelines/`
(`docs/guidelines/agent_working_environment.md:1-6` and `docs/guidelines/intentional_divergences.md:1-6`,
both `status: active` / `layer: guidelines` / `authority: P1`). `audience: agent` matches
`agent_working_environment.md:5` (the nearer precedent — a doc primarily consulted by agents doing
retention/cleanup work — rather than `intentional_divergences.md`'s `audience: developer`). No `date:`
field: confirmed neither `agent_working_environment.md` nor `intentional_divergences.md` (both `doc`
content-type per `tools/validate_frontmatter.py:120-134`'s `detect_content_type`) carries one; `date` is
only required for `ticket`/`artifact` content types (`tools/validate_frontmatter.py:212` vs. `:229`/`:243`).
No `tags_enforced: true`: confirmed via `tools/validate_frontmatter.py:198-207` (`_check_doc_tags`) that
registry membership is enforced for a `doc` only when `tags_enforced: true` is explicitly set — every
doc in the corpus lacks this field today (per that function's own docstring at line 200-202), and
`agent_working_environment.md:6` itself carries tags (`[setup, tooling, knowledge-search, docker, rag]`)
without the flag. This ticket's chosen tags are already registered regardless, so the flag's absence has
no practical effect here, but do not add `tags_enforced: true` — that would be a scope-creep opt-in this
ticket was not asked to make.

Body content, in this exact order:

```markdown
# Artifact Retention Classification

This doc classifies every repo artifact class that produces durable output outside the
`agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl` weekly shards (already fully classified and
resolved by the shipped `TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC` and
`TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC`). It is the M2 deliverable of
`docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md`, shipped by
`TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION`.

## Taxonomy

Every artifact class below is assigned exactly one of four categories:

- **Ephemeral** — derived/build output that is fully rebuildable from source inputs via a documented
  command; not tied to any single run's lifecycle (persists across many runs until the next rebuild);
  gitignored, never committed.
- **Run-scoped** — exists only for the duration of a single process, tool invocation, or workflow run;
  written fresh per run and never intended to outlive it; gitignored, never committed.
- **Ticket-scoped** — produced by one ticket's own workflow; migrates to a durable location once the
  ticket closes rather than staying attached to the ticket's working files.
- **Long-lived / Institutional** — committed, retained indefinitely as part of the project's durable
  record (audit trail, precedent, cross-referenced by tooling); never pruned by convention.

## Retention Classification Table

| Artifact class | Classification | Recommended Treatment | Evidence / Reference |
|---|---|---|---|
| `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl` | Long-lived / Institutional | Already resolved by the shipped weekly-sharding work; keep committed, no change from this ticket | `tickets/done/agent-monitoring-weekly-sharding/TCK-20260902-MONITORING-WEEKLY-SHARDING-EPIC.md` (Status: DONE), `tickets/done/agent-monitoring-unified-weekly-data/TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC.md` (Status: DONE), `tools/agent-monitoring/verify_referential_integrity.py` |
| `stored_artifacts/{id}/` | Ticket-scoped → Long-lived / Institutional | Keep permanent; never pruned | Referenced by `docs/REGISTRY.yaml` and `tools/registry_query.py`; read by every ticket's Prior Work investigation step |
| `tickets/done/*.md` | Long-lived / Institutional | Keep permanent; never pruned | Same as above — `docs/REGISTRY.yaml` indexes every closed ticket by ID |
| `agent-monitoring/retro/RETRO-*.md` | Long-lived / Institutional | Keep permanent | Generated and committed by `tools/agent-monitoring/generate_retro.py` |
| `tickets/working_log.csv` | Long-lived / Institutional (currently data-quality-broken) | Keep permanent once its parser/format is fixed — see `TCK-20260904-WORKING-LOG-CSV-PARSER` | `tickets/todos/ai-first-hardening-h1-h2-followon/TCK-20260904-WORKING-LOG-CSV-PARSER.md` (not yet implemented) |
| `graphify-out/` | Ephemeral | Keep gitignored; rebuild via `graphify update .` (incremental) or a full `/graphify` rebuild — never commit | See "graphify-out/ resolution" below |
| `knowledge-index/` | Ephemeral | Keep gitignored; rebuild via `make knowledge-index` (full) or `make knowledge-index-update` (incremental) | See "knowledge-index/ resolution" below |
| `.claude/current_run` | Run-scoped | No change needed; already correctly a per-run sidecar | Written per-run by `.claude/workflows/*.js`; never committed |

### `graphify-out/` resolution

This artifact class is confirmed **Ephemeral** build output, with a resolved
recommendation, not a still-pending question:

- `.gitignore:260` — `graphify-out/*` (the active ignore rule).
- `.gitignore:261` — `src/graphify-out/` (a second, path-qualified ignore rule).
- Zero references to `graphify-out` across `.github/workflows/*.yml` (`grep -rn "graphify-out"
  .github/workflows/` returns no matches) — confirms this build output has zero CI dependency.
- Zero git-tracked files under `graphify-out/` (`git ls-files graphify-out/` returns nothing).
- `tests/tools/test_code_health_impact.py:26-40` already documents and enforces this directly: a code
  comment states "graphify-out/ is entirely gitignored (never committed)", and a `_requires_graphify`
  skip marker (`shutil.which("graphify") is not None and (_REPO_ROOT / "graphify-out" /
  "graph.json").exists()`) gates 4 real-path tests so a fresh CI checkout without a prebuilt graph
  skips rather than fails.
- `TCK-20260818-HOTFIX-GRAPHIFY-CLI-TEST-MISSING-INDEX-SKIP` (Status: DONE) landed exactly this
  skip-if-missing pattern as a deliberate, already-shipped fix for this relationship.

**Recommendation:** keep `graphify-out/` gitignored build output as-is. Rebuild via `graphify update .`
(incremental, AST-only, per `CLAUDE.md`'s Graphify Integration section) or a full `/graphify` rebuild.
No further action needed.

### `knowledge-index/` resolution

This artifact class is confirmed **Ephemeral** build output, with a resolved
recommendation, not a still-pending question:

- `.gitignore:264` — `knowledge-index/` (the active ignore rule, immediately preceded by the comment
  "Knowledge search index (local only — rebuild with: make knowledge-index)" at `.gitignore:263`).
- `Makefile:331` — the comment `# developer env only — not CI` immediately precedes the
  `knowledge-index:` target; the target's own `##` help text (`Makefile:334`) repeats "(developer env
  only — not CI)".
- `docs/guidelines/agent_working_environment.md`'s existing "Other Local, Gitignored Caches" table
  already documents two `knowledge-index/` paths (`knowledge.db` at line 278, `retrieval_cache.db` at
  line 280), each citing `.gitignore:264` and a rebuild command.
- `tools/hooks/post-commit-reindex.sh` exists and pairs with `docs/guidelines/agent_working_environment.md:82-87`'s
  description of an installable post-commit hook that runs `make knowledge-index-update` and self-skips
  if `knowledge-index/` does not exist.

**Recommendation:** keep `knowledge-index/` gitignored. Rebuild via `make knowledge-index` (full) or
`make knowledge-index-update` (incremental). No further action needed.

## Related Docs

- `docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md` — this doc is
  the M2 deliverable for that epic.
- `docs/guidelines/agent_working_environment.md` — structural precedent for this doc's table shape, and
  the existing home for `knowledge-index/` and (as of this ticket) `graphify-out/` cache documentation.
```

**Do NOT touch:** `docs/observability/retrieval_retention_redaction_policy.md` (a different, already-
settled question about Knowledge Gateway MCP cache field redaction — cited only as directory-placement
precedent in `investigation.md`, never a doc this ticket edits); `docs/agent-monitoring/schema.md` (fully
covers M1's already-shipped scope, unrelated to M2's 7 remaining artifact classes); the literal two-word
phrase "open question" anywhere in the new doc's `graphify-out/`/`knowledge-index/` content — use
"resolution" / "resolved" / "confirmed" instead, since `test_plan.md`'s new test
(`test_artifact_retention_classification_doc_resolves_both_open_questions`) explicitly guards against
either row reading as still-unresolved.

**Verify:** `test_artifact_retention_classification_doc_exists_and_has_required_sections` and
`test_artifact_retention_classification_doc_resolves_both_open_questions` (both in
`tests/docs/test_artifact_retention_classification_doc.py`, added in Step 2) and
`test_working_log_csv_row_references_parser_ticket_by_id_only` (same file).

---

### Step 2 — Add the doc-structure test file
**Files:** `tests/docs/test_artifact_retention_classification_doc.py` (new file)

**Change:** Follow the exact static-assertion pattern already used by
`tests/docs/test_redaction_retention_policy_doc.py:1-40` (read the doc as text via `Path.read_text()`,
assert required headings/phrases are literal substrings — never import or execute the doc). Write three
test functions, matching `test_plan.md`'s "New Tests Required" section verbatim:

1. `test_artifact_retention_classification_doc_exists_and_has_required_sections` — asserts the file at
   `docs/guidelines/artifact_retention_classification.md` exists, and that each of the 8 artifact-class
   literal strings appears in the text: `agent-monitoring/data/`, `stored_artifacts/`, `tickets/done/`,
   `retro/RETRO-*.md`, `working_log.csv`, `graphify-out/`, `knowledge-index/`, `.claude/current_run`.
   Also assert the four taxonomy category names appear at least once each: `Ephemeral`, `Run-scoped`,
   `Ticket-scoped`, `Long-lived`.
2. `test_artifact_retention_classification_doc_resolves_both_open_questions` — locate the
   `graphify-out/` and `knowledge-index/` sections/rows and assert each contains at least one concrete
   evidence token (e.g. `.gitignore:260`, `.gitignore:264`, `zero`) and does **not** contain the literal
   substring `"open question"` (case-insensitive) anywhere in those sections.
3. `test_working_log_csv_row_references_parser_ticket_by_id_only` — assert the literal string
   `TCK-20260904-WORKING-LOG-CSV-PARSER` appears in the doc, and that neither `"blocked on"` nor
   `"gated on"` (case-insensitive) appears within, say, 200 characters of that ticket ID substring.

**Do NOT touch:** `tests/docs/test_redaction_retention_policy_doc.py` (read-only precedent, must stay
green and unmodified — confirmed unrelated file at
`docs/engine/contracts/knowledge_gateway_mcp/redaction_retention_policy.md`, not this ticket's doc).

**Verify:** `pytest tests/docs/test_artifact_retention_classification_doc.py -v` — all 3 new tests pass.

**Dependency:** requires Step 1's doc content to exist first (tests assert against its literal text).

---

### Step 3 — Add the missing `graphify-out/graph.json` row to `agent_working_environment.md`
**Files:** `docs/guidelines/agent_working_environment.md`

**Change:** This file's existing "Other Local, Gitignored Caches" table
(`docs/guidelines/agent_working_environment.md:267-280`, read and confirmed in this session) has exactly
3 rows today — semantic search index (line 278), parity ledger query index (line 279), Knowledge Gateway
MCP cache (line 280) — under the section header `## Other Local, Gitignored Caches (Knowledge Gateway
MCP)` (line 267) and an intro paragraph (lines 269-274) that says "one of three local, disposable
caches" / "all three are deliberately rebuildable-only". `graphify-out/` is a fourth, structurally
identical local gitignored cache that this table does not yet cover — this was investigation.md's
Risk/Recommendation #4, resolved as "do it now, in this ticket."

Three precise edits, in order:

1. **Header (line 267).** Change:
   ```
   ## Other Local, Gitignored Caches (Knowledge Gateway MCP)
   ```
   to:
   ```
   ## Other Local, Gitignored Caches
   ```
   (Drop the MCP-only parenthetical — `graphify-out/` is not a Knowledge Gateway MCP artifact, so a
   scoped section title would misdescribe the new row.)

2. **Intro paragraph (lines 269-274).** Change:
   ```
   The semantic search index above is one of three local, disposable caches this repository uses. None
   of them are committed — all three are deliberately rebuildable-only, per this repository's own
   principle that "the local database must remain disposable and rebuildable"
   (`docs/plans/knowledge-gateway-mcp-proposal.md` §10, `tmp/mcp-followup-instruction.md` §10). If you
   are setting up a fresh checkout or moving to a new environment, none of these need to be copied —
   rebuild them instead:
   ```
   to:
   ```
   The semantic search index above is one of four local, disposable caches this repository uses. None
   of them are committed — all four are deliberately rebuildable-only. Three of the four (semantic
   search index, parity ledger query index, Knowledge Gateway MCP cache) exist to support the Knowledge
   Gateway MCP and follow its own principle that "the local database must remain disposable and
   rebuildable" (`docs/plans/knowledge-gateway-mcp-proposal.md` §10, `tmp/mcp-followup-instruction.md`
   §10); the fourth (the `graphify` CLI's code-graph index) is unrelated to the Knowledge Gateway MCP but
   shares the same disposable/rebuildable design. If you are setting up a fresh checkout or moving to a
   new environment, none of these need to be copied — rebuild them instead:
   ```
   (This is the explicit resolution to investigation.md's framing concern — broadening the intro
   sentence rather than adding a footnote, since the MCP-vs-non-MCP distinction is one clause, not a
   tangent worth pulling out of the main text.)

3. **New table row.** Insert immediately after the existing `retrieval_cache.db` row (line 280) and
   before the blank line that follows it, in the exact same 5-column format (`Artifact | Real path |
   What it is | Gitignored? | How to rebuild`):
   ```
   | `graphify` code-graph index | `graphify-out/graph.json` (plus other `graphify-out/*` build output) | The `graphify` CLI's persistent knowledge graph — god nodes, community detection, and query/path/explain data described in `graphify-out/GRAPH_REPORT.md` | Yes (`.gitignore:260` `graphify-out/*`, `.gitignore:261` `src/graphify-out/`) | `graphify update .` (incremental, AST-only) or a full `/graphify` rebuild — see `CLAUDE.md`'s Graphify Integration section |
   ```

**Do NOT touch:** the `**One-command bootstrap for a fresh environment:**` subsection (lines 282-286)
or the `retrieval_cache.db` no-rebuild-command explanation (lines 288-294) — `graphify-out/` is not part
of `kgmcp-bootstrap` and has its own rebuild command already given in the new row; do not add it to the
bootstrap script's description. Do not touch any other section of this file (frontmatter, the
Situation/Command table at lines 256-263, or anything above line 267).

**Verify:** manual read-back confirming the row count now matches "four" in the intro text, and
`test_artifact_retention_classification_doc_exists_and_has_required_sections`-style eyeballing is not
required here since no new pytest test targets this file specifically — covered by the existing
`tests/tools/test_validate_frontmatter.py` corpus scan (frontmatter untouched, so it stays green) and a
`git diff` review confirming only the three edits above landed.

---

### Step 4 — Update `telemetry_retention_epic.md`'s M2 section
**Files:** `docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md`

**Other writers to this file (shared-resource check):** This file also contains an M1 section
(`:20-57`, already marked superseded by a prior session, not touched here) and an M3 section (`:87-103`,
"Ownership & lifecycle documentation for new/changed subsystems") which is explicitly a **separate,
not-yet-created ticket's** future scope per this ticket's own Out of Scope and investigation.md's
Anti-Drift Hazards ("Do not conflate M3... with this ticket's M2 scope"). That means a future ticket
will edit this same file's M3 section later — this step's edits must be confined exactly to the M2
heading, the paragraph immediately following it, and the M2 bullet in the "Acceptance signal for this
epic" section, leaving the M1 section, the M3 section, the M3 table, and the "Out of scope" /
"References" sections' non-M2 content byte-for-byte unchanged. No other current writer to this file is
known (it is a planning doc edited manually per-milestone, not machine-generated).

**Change:** Mirror the M1 section's existing "superseded" inline-note structure
(`telemetry_retention_epic.md:20-22`, which opens with a bolded one-line verdict immediately under the
heading) for M2:

1. **Heading (line 68).** Change:
   ```
   ### M2 — Artifact retention classification, repo-wide (gated on nothing)
   ```
   to:
   ```
   ### M2 — Artifact retention classification, repo-wide (gated on nothing) — SHIPPED
   ```

2. **Insert a note paragraph** immediately after that heading and before the existing "Classify every
   artifact class the repo produces..." paragraph (i.e., between the current lines 68 and 70):
   ```
   **M2 is shipped — see `TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION`.** The table below reflects
   this milestone's original planning-time draft; the committed, evidence-verified version — including
   both the `graphify-out/` and `knowledge-index/` questions resolved with concrete citations rather
   than carried forward — now lives at `docs/guidelines/artifact_retention_classification.md`. Treat
   that doc as authoritative; this table is retained here for historical context only.
   ```
   (Leave the existing M2 table, at lines 73-82, untouched — it stays as historical planning context,
   same as how M1's own retracted draft design is described in prose rather than deleted.)

3. **Acceptance-signal bullet (lines 117-119).** Change:
   ```
   - M2: a committed retention-classification table covers every remaining artifact class in the
     table above, with the two open questions either resolved or explicitly assigned a follow-up
     owner.
   ```
   to:
   ```
   - M2: **met** — a committed retention-classification table
     (`docs/guidelines/artifact_retention_classification.md`, shipped by
     `TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION`) covers every remaining artifact class, with both
     `graphify-out/`/`knowledge-index/` questions resolved with concrete evidence citations, not
     deferred.
   ```

4. **References section (lines 123-135).** Add one bullet, after the existing
   `tools/agent-monitoring/verify_referential_integrity.py` bullet and before the
   `docs/agent-monitoring/schema.md` bullet:
   ```
   - `docs/guidelines/artifact_retention_classification.md` — the M2 deliverable (shipped, see
     `TCK-20260904-ARTIFACT-RETENTION-CLASSIFICATION`).
   ```

**Do NOT touch:** the M1 section (lines 20-57), the M3 section and its ownership table (lines 87-103),
the "Out of scope" section (lines 105-112), the M3 bullet in "Acceptance signal for this epic" (line
120-121), or the frontmatter (lines 1-8).

**Verify:** `git diff docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md`
shows only the four edits above; manual read confirming the M1/M3 sections are byte-identical to before.

---

### Step 5 — Static verification pass
**Files:** none changed; read/run-only.

**Change:** Run, in order:

1. `python3 tools/validate_frontmatter.py docs/guidelines/artifact_retention_classification.md` — must
   report zero errors (validates `status`/`layer`/`authority`/`audience` against
   `STATUS_VALUES`/`LAYER_VALUES`/`AUTHORITY_VALUES`/`AUDIENCE_VALUES` per
   `tools/validate_frontmatter.py:44,53-56`; `layer: guidelines` and all four tags are pre-registered per
   Step 1's citations, so this should pass without any registry addition).
2. `pytest tests/docs/ tests/tools/test_validate_frontmatter.py tests/tools/test_tag_registry.py tests/tools/test_layer_registry.py tests/tools/test_generate_registry.py tests/tools/test_registry_query.py tests/tools/test_code_health_impact.py -v`
   (per `test_plan.md`'s Scoped Pytest Commands, plus `test_code_health_impact.py` explicitly included
   as the anti-drift guard that this ticket did not touch the `_requires_graphify` skip logic it merely
   describes). All must pass; `test_code_health_impact.py`'s graphify-dependent tests are expected to
   skip in an environment without a prebuilt `graphify-out/graph.json` — that is correct, pre-existing
   behavior, not a new failure to chase.
3. `make knowledge-index-update` then `make docs-registry` — functional smoke check required by
   CLAUDE.md's After Work step whenever `docs/` changes; confirms `docs/REGISTRY.yaml` regenerates
   cleanly and includes the new doc. Stage the regenerated `docs/REGISTRY.yaml` in the ticket's commit.
4. **Manual citation re-verification (required, not optional):** re-open each of the following and
   confirm the plan's/doc's cited line numbers still match, since the repo continues to change between
   investigation time and Verify time — do not trust this plan's or investigation.md's line numbers as
   permanently correct:
   - `.gitignore` — confirm `graphify-out/*` and `src/graphify-out/` are still at (or near) lines
     260-261, and `knowledge-index/` is still at (or near) line 264.
   - `Makefile` — confirm the `# developer env only — not CI` comment is still immediately above the
     `knowledge-index:` target.
   - `tests/tools/test_code_health_impact.py` — confirm the `_requires_graphify` skip marker and its
     comment are still present and unmodified.
   - `docs/guidelines/agent_working_environment.md` — confirm the new row was inserted in the correct
     table position and the "one of four" text reads correctly with the new row counted.
   - `git ls-files graphify-out/` and `grep -rn "graphify-out" .github/workflows/` — re-run both, confirm
     still zero results.
   - `tickets/todos/ai-first-hardening-h1-h2-followon/TCK-20260904-WORKING-LOG-CSV-PARSER.md` — confirm
     it still exists and is still not in `tickets/done/` (if it has since shipped, update the new doc's
     working_log.csv row's phrasing from "not yet implemented" accordingly — do not leave a stale claim).
5. `git status` — confirm the only new/modified files are: `docs/guidelines/artifact_retention_classification.md`
   (new), `tests/docs/test_artifact_retention_classification_doc.py` (new),
   `docs/guidelines/agent_working_environment.md` (modified), `telemetry_retention_epic.md` (modified),
   the ticket file, staging/stored artifacts, `docs/REGISTRY.yaml`, and `agent-monitoring/`. Anything
   else (especially `tickets/todos/ai-first-hardening-h1-h2-followon/TCK-20260904-WORKING-LOG-CSV-PARSER.md`
   or `working_log.csv` itself) is scope creep — revert it.

**Verify:** all of the above complete cleanly; this step is itself the verification, no further gate.

## Scope Guards

- Do not implement the `working_log.csv` parser/cleanup fix — tracked separately by
  `TCK-20260904-WORKING-LOG-CSV-PARSER`; reference it by ID only in the new doc's table row, never
  duplicate its scope or state this ticket is blocked/gated on it.
- Do not touch `docs/plans/agent_infrastructure/ai_first_hardening_epics/telemetry_retention_epic.md`'s
  M1 section (lines 20-57) or M3 section (lines 87-103, including its ownership table) — M3 is a
  separate milestone with its own future ticket.
- Do not edit `docs/observability/retrieval_retention_redaction_policy.md` — cited only as
  directory-placement precedent in investigation.md, not a doc this ticket updates.
- Do not edit `docs/agent-monitoring/schema.md` — fully covers the already-shipped M1 scope, unrelated
  to this ticket's 7 remaining artifact classes.
- Do not change `tests/tools/test_code_health_impact.py`'s `_requires_graphify` skip logic — only
  describe it; any edit there is a signal of scope creep into M1-adjacent code.
- Do not register any new tag or layer — all four tags (`ai`, `agent-monitoring`, `data-quality`,
  `documentation`) and the `guidelines` layer are already registered; this ticket only reuses them.
- Do not add `tags_enforced: true` to the new doc's frontmatter — out of scope, not requested.
- Do not use the literal phrase "open question" when describing the `graphify-out/`/`knowledge-index/`
  rows in the new doc — both are resolved, and the new test explicitly guards against this phrasing.
- Do not touch `tickets/todos/ai-first-hardening-h1-h2-followon/TCK-20260904-WORKING-LOG-CSV-PARSER.md`
  — reference its ID only.

## Dependency Map

- Step 2 depends on Step 1 (tests assert against Step 1's doc text).
- Step 5 depends on Steps 1-4 (verifies the combined result).
- Steps 1, 3, and 4 are independent of each other and may be done in any order relative to one another,
  but all must land before Step 5.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| New committed doc contains a retention-classification table covering all 8 artifact classes, each with a category from the 4-way taxonomy and a recommended treatment | Step 1 | `test_artifact_retention_classification_doc_exists_and_has_required_sections` |
| `graphify-out/` row cites concrete evidence (gitignore line, zero CI references, zero tracked files) and a resolved recommendation | Step 1 (`graphify-out/ resolution` subsection) | `test_artifact_retention_classification_doc_resolves_both_open_questions` |
| `knowledge-index/` row cites concrete evidence (gitignore line, Makefile comment, existing rebuild automation) and a resolved recommendation | Step 1 (`knowledge-index/ resolution` subsection) | `test_artifact_retention_classification_doc_resolves_both_open_questions` |
| If either question is left unresolved instead of resolved, the doc names a specific follow-up owner/role and trigger | N/A — both questions are resolved per Step 1, not left open; no follow-up-owner text is needed | `test_artifact_retention_classification_doc_resolves_both_open_questions` (asserts absence of "open question" phrasing) |

## Anti-Drift Notes

- The Request Summary and investigation.md's Anti-Drift Hazards both stress: do not let the
  `graphify-out/`/`knowledge-index/` rows silently re-open the questions the epic doc originally left
  pending. Step 1's doc text must read as resolved fact, not as a restated question — this is why
  Step 2's test explicitly checks for absence of "open question" phrasing rather than only checking for
  presence of evidence tokens.
- M3 (ownership/lifecycle documentation) shares a References/Out-of-Scope boundary with this ticket's M2
  scope in the source epic doc, but is a separate milestone with its own future ticket — Step 4 is
  scoped precisely to avoid touching M3's section.
- `docs/observability/retrieval_retention_redaction_policy.md` is a different, already-settled question
  (Knowledge Gateway MCP cache field redaction) — it is cited in investigation.md only as
  directory-placement precedent for why the new doc belongs in `docs/guidelines/`, not
  `docs/observability/`. Nothing in this plan edits that file.
- The `working_log.csv` row must reference `TCK-20260904-WORKING-LOG-CSV-PARSER` by ID only — no
  duplication of its scope, no gating language ("blocked on", "gated on") near the ID.
- Step 3 (the `agent_working_environment.md` edit) was a genuine judgment call in investigation.md,
  resolved as "do now, not defer" — the implementer must not silently skip it and must not leave the
  "one of three" / MCP-only framing inconsistent with the new fourth row if it is done.
- No Mechanics Bible chapter, engine contract, or parity ledger entry is touched — investigation.md
  confirmed zero relevant hits when searching `docs/parity_ledger/*.yaml` for this ticket's topics.
