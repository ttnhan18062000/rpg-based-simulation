---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-AI-AGENT-OVERVIEW-DOC
artifact_type: plan
tags: [documentation, ai, workflows]
---

# Plan — TCK-20260705-AI-AGENT-OVERVIEW-DOC

## Summary

Write one new synthesis document, `docs/ai/system_overview.md`, that gives a complete technical
narrative of the AI agent system: the three-layer model (agents/workflows/skills), the full
ticket-lifecycle/implementation pipeline, the two simulation-testing/quality lanes plus the SimQ audit
lane (three lanes total), and observability. The doc narrates and cross-references; it does not
re-render the detailed reference tables that already exist in the six-plus source docs. Two index
updates wire it into the existing doc navigation: `docs/ai/README.md`'s Document Index and
`docs/README.md`'s AI Tooling section. No source document content changes. No new ticket is filed for
the workflows.md/skills.md/README.md staleness found in investigation — it is recorded only as a dated
observation inside the new doc and in this ticket's own Completion Summary.

**File path decision:** `docs/ai/system_overview.md`. Justification: this is meta-documentation about
the agent tooling itself (not a subsystem how-to, which is what `docs/guides/` is for), so it belongs
alongside the five existing `docs/ai/*.md` files it synthesizes. `system_overview.md` names it
distinctly from `README.md` (index/quick-reference) and `ticket-lifecycle.md` (one narrow flow) — this
doc is the broader narrative spanning all of `docs/ai/` plus the two simulation/quality docs outside
that folder.

**"8 workflows" framing decision:** Do not use a specific total workflow count in the new doc's
title, headings, or lead sentences. Where a count is useful for orientation, use the exact phrasing:
"10 documented development and simulation workflows in `docs/ai/workflows.md`, plus `simq-audit` — an
11th workflow file with its own dedicated doc, not yet listed in `workflows.md`'s catalog." Never write
"8 workflows" anywhere in the new doc, including when paraphrasing README.md's index (the new doc's own
Document Index row text is fixed separately — see Step 3).

**Follow-up ticket decision:** Do NOT create a new ticket file. This ticket's Out of Scope explicitly
forbids modifying the 8 source documents' content, and creating a new ticket file is also not part of
this ticket's Scope (it would be new tooling/process work, not documentation synthesis). Record the
staleness finding in exactly two places:
1. One short, dated, clearly-labeled observation paragraph inside the new doc's final section (Step 3,
   Section 7) — framed as "as of 2026-07-05, these do not yet match" not "these were wrong and are now
   fixed."
2. This ticket's own `## Completion Summary` (filled in by Implement/Finalize, not by Plan) noting the
   staleness as a recommended follow-up for a future ticket, per Anti-Drift Hazards' explicit instruction
   not to silently fix it and investigation's Risk #1 recommendation to flag it as a candidate follow-up.

## Steps

### Step 1: Draft sections 1-4 of the new document

**Files:** Create `docs/ai/system_overview.md` (new file, this step writes the top portion only).

**Change:** Write the file's frontmatter plus Sections 1-4. Use this frontmatter (matches every other
`docs/ai/*.md` file's shape per test_plan.md):

```yaml
---
status: active
layer: ai
authority: P1
audience: developer
---
```

**Section 1 — Overview / Purpose** (short, 1-2 paragraphs):
- State the doc's purpose: a single technical narrative tying together the AI agent system, for readers
  who want the full picture without reading 8 separate files first.
- One sentence naming all source docs this synthesizes, each as a link: `docs/ai/README.md`,
  `docs/ai/agents.md`, `docs/ai/workflows.md`, `docs/ai/skills.md`, `docs/ai/ticket-lifecycle.md`,
  `docs/ai/agent_infrastructure_audit.md`, `docs/simulation/lab_contract.md`,
  `docs/simulation_quality/audit_workflow.md`, `docs/agent-monitoring/schema.md`,
  `docs/guides/agent_monitoring.md`.
- Explicitly state up front: "This document narrates; it is not the source of truth for exact schemas,
  field lists, or argument signatures — follow the links for those." (Directly satisfies Anti-Drift
  Hazards' "do not duplicate reference tables" instruction, stated as a doc-level disclaimer so every
  later section can stay narrative without re-litigating it.)

**Section 2 — The Three-Layer Model** (source: `docs/ai/README.md` L14-30):
- State the three layers verbatim in substance: Agents (`.claude/agents/*.md`, spawned by workflows or
  via `Agent(subagent_type: "name")`), Workflows (`.claude/workflows/*.js`, invoked via
  `Workflow({ name, args })` or `/workflow-name`), Skills (`.claude/skills/*/SKILL.md` + built-in, via
  `/skill-name`).
- State the count facts precisely, sourced as follows (do NOT cite `workflows.md` or README.md for the
  workflow/skill counts — cite the filesystem/investigation facts directly, since those two docs
  undercount):
  - "11 subagents" — cite `docs/ai/agents.md` (matches `.claude/agents/*.md`, confirmed in
    investigation).
  - "11 workflow files in `.claude/workflows/`, 10 of them documented with phase tables in
    `docs/ai/workflows.md`; the 11th, `simq-audit.js`, is covered later in this document (Section 5) and
    in its own doc, `docs/simulation_quality/audit_workflow.md`, but not yet in `workflows.md`'s
    catalog." Do not cite README.md's "All 8 workflows" line here at all — do not repeat it even to
    correct it inline; the correction lives only in Section 7 (see Step 3).
  - "16 skill folders under `.claude/skills/`" — cite investigation's ls count; do not cite
    `skills.md`'s tables for this total since `skills.md`'s own two tables together omit `simq-audit`.
- One short "when to use which" paragraph paraphrasing README.md L26-30 (workflow = multi-phase with
  gates; agent directly = one focused task mid-conversation; skill = single-session pattern, e.g.
  `/graphify`, `/code-review`).
- Link out: "For the full per-agent role/input/output table, see `agents.md`. For full per-workflow
  args/phase/return-value tables, see `workflows.md`. For the complete skill catalog, see `skills.md`."

**Section 3 — Ticket Lifecycle & the Development Pipeline** (sources:
`docs/ai/ticket-lifecycle.md`, `docs/ai/agents.md`, `docs/ai/workflows.md` for the 6 workflows/phases
that match code, CLAUDE.md for tier table cross-check):
- Entry points: `create-tickets` (proposal/backlog → tickets) and direct ticket authoring; both feed
  `implement-ticket` (single ticket) or `implement-epic` (folder/epic of child tickets).
- `create-tickets`: state its **5 real phases** — Comprehend → Investigate → Structure → Write → Link —
  and cite `.claude/workflows/create-tickets.js` directly as the source (its `meta.phases` array and
  `phase(...)` calls), NOT `docs/ai/workflows.md` (which is stale here, documenting only
  Parse→Write→Link). Include one sentence describing what each phase does, using investigation's
  descriptions (Comprehend: read proposal, extract discrete concerns, no codebase investigation yet;
  Investigate: per-concern parallel evidence gathering — `knowledge_search.py`, `graphify query`,
  `REGISTRY.yaml`, working_log grep, code/test reads, tier assessment; Structure: one synthesis agent
  produces ticket fields from investigation evidence only; Write: per-ticket parallel `ticket-scoper`
  runs, produces the `TCK-*.md` file + conditional `SEQUENCE.md`; Link: only if `epic_id` given).
  Cross-reference corroboration: note that `docs/agent-monitoring/schema.md`'s `events.jsonl` phase list
  for `create-tickets` already lists the correct 5 phases — cite `schema.md` as independent confirmation.
- The **9-phase `implement-ticket` pipeline** (standard tier): Scope (`ticket-scoper`) → Investigate
  (`investigator`) → Plan (`planner`) → Review (`architecture-reviewer`, gate: NEEDS_CHANGES/BLOCKED) →
  Implement (`implementer`) → Test (`test-scoper`, gate: TESTS_FAILED) → Parity (`parity-updater`) →
  Verify (`done-checker`, gate: DOD_BLOCKED) → Finalize (inline, no agent). Cite
  `docs/ai/workflows.md`/`docs/ai/ticket-lifecycle.md` directly — investigation confirmed this list
  matches `.claude/workflows/implement-ticket.js` exactly, no staleness here.
- Tier table (hotfix / standard / epic) — reproduce the 3-row table exactly as it appears in CLAUDE.md's
  own "Tier Routing" section (hotfix: Scope→Implement→Test→Parity→Verify→Finalize; standard: full
  9-phase; epic: Scope only, tracks child tickets).
- `implement-epic`: 3 phases — Discover → Implement → Report — cite `docs/ai/workflows.md` directly
  (matches code, no staleness). Args: one of `folder` | `epic_id` | `request`, plus optional
  `tier_override`. Return values include `EPIC_CREATED`, `NOTHING_TO_DO`, `DONE`, or any child gate
  status.
- Gate/return-status vocabulary: name the 7 literal return statuses confirmed in code:
  `CONFLICTS_DETECTED`, `NEEDS_HUMAN_INPUT`, `NEEDS_CHANGES`, `BLOCKED`, `TESTS_FAILED`, `DOD_BLOCKED`,
  `DONE`.
- DoD condition count: state "11 substantive Definition-of-Done conditions, plus a 12th — agent
  monitoring — that is guaranteed by the workflow itself rather than checked by `done-checker`." Match
  CLAUDE.md's own framing exactly (do not describe this as "12 conditions" flatly, and do not repeat
  `ticket-lifecycle.md`'s loosely-worded "11-condition table" heading as if the table only has 11 rows).
- Link out: "For the full worked example (a real ticket walked end to end, plus the manual-execution
  fallback without the workflow), see `ticket-lifecycle.md`."

**Change scope for this step:** create the file with frontmatter + Sections 1-4 only (Section 4 is
"Ticket Lifecycle" above — note the numbering: if Section 3 above is being called "Section 3" in this
plan, keep the implementer's actual document heading numbering consistent with whatever final 7-heading
scheme is used; the plan's internal step/section numbers here are for review tracking, not mandated
document heading numbers).

**Do NOT touch:** any of the 8 source documents; `docs/README.md`; `docs/ai/README.md` (those are Step
3).

**Verify:** Re-read the drafted Sections 1-3 (three-layer model + ticket lifecycle) against
`docs/ai/agents.md`, `docs/ai/workflows.md`, `docs/ai/ticket-lifecycle.md`, and CLAUDE.md's own
"Tier Routing"/"Definition of Done" sections; confirm every phase name, gate name, and return-status
literal matches source exactly. Confirm the `create-tickets` phase list is attributed to
`.claude/workflows/create-tickets.js`, not `workflows.md`.

---

### Step 2: Draft sections 5-7 of the new document

**Files:** `docs/ai/system_overview.md` (append to the file created in Step 1).

**Section 5 — Simulation Testing: the Lab Workflow Chain and the Lab Session Contract**
(sources: `docs/ai/workflows.md` Simulation Workflows section, `docs/simulation/lab_contract.md`):
- Present as **two layers of the same process**, explicitly labeled as such — not as one merged list
  (per Anti-Drift Hazards and investigation Risk #3).
- **Layer A — Claude Code workflow sequence** (7 workflows): `generate-simulation-setup` →
  `prepare-simulation-execution` → [user triggers manually] → `register-simulation-result` →
  `investigate-simulation-result` → `propose-simulation-enhancements` → [human reviews/approves] →
  `update-knowledge-store` → `compact-simulation-result` (cleanup, can run any time on registered runs).
  For phase names, split sourcing exactly as investigation specifies:
  - `generate-simulation-setup`: state phases as **Scan → Draft → Validate**, citing
    `.claude/workflows/generate-simulation-setup.js`'s `meta.phases` directly — NOT `workflows.md` (which
    wrongly says Spec Draft→Validation→Promotion).
  - `investigate-simulation-result`: state phases as **Load → Analyze → Report** (3 phases), citing the
    `.js` file directly — NOT `workflows.md` (which wrongly adds a 4th "Correlate" phase).
  - `compact-simulation-result`: state phases as **Scan → Compact → Archive**, citing the `.js` file
    directly — NOT `workflows.md` (which wrongly says "Inventory" instead of "Scan").
  - `prepare-simulation-execution` (Resolve → Estimate → Generate), `register-simulation-result`
    (Validate → Index → Score), `propose-simulation-enhancements` (Read → Hypothesize → Propose),
    `update-knowledge-store` (Verify → Synthesize → Commit): these 4 match code — cite
    `docs/ai/workflows.md` directly for these.
- **Layer B — the Agentic Simulation Lab session contract** (`docs/simulation/lab_contract.md`,
  `src/lab/`): 6 stages — GENERATION → EXECUTION_SUPPORT → REGISTRATION → INVESTIGATION → ENHANCEMENT →
  KNOWLEDGE_UPDATE. Session states: ACTIVE → WAITING_FOR_USER → ... → COMPLETED / FAILED / ARCHIVED.
  Human-gated stages: GENERATION, EXECUTION_SUPPORT, ENHANCEMENT (3 of 6) require explicit
  `approval_status: APPROVED` to advance past WAITING_FOR_USER; REJECTED terminates progression.
  `ScenarioLabOrchestrator` is the central engine (load+validate → isolated run under
  `data/lab_sessions/`, never shares `AuthoritativeState` → single-threaded Kernel ticks → post-run
  analysis). `BudgetGuardrail` is a second, budget-specific gate (OK/WARNING/BLOCKED) layered on top of
  the 3 stage-level approval gates. Mutation pipeline operates on a spec copy, rolls back on failure.
  Metamorphic testing has 3 relation classes (symmetry, monotonicity, equivalence); a failure is
  recorded, not an abort.
- **The relationship statement** (verbatim-spirit from investigation, phrased as inference not fact):
  "The workflow sequence in Layer A drives the lab session state machine in Layer B — for example,
  running `generate-simulation-setup` and `prepare-simulation-execution` corresponds to progressing a lab
  session through its GENERATION and EXECUTION_SUPPORT stages. No source document states an exact 1:1
  mapping between the 7 workflows and the 6 stages, and this document does not assert one; read
  `lab_contract.md` for the authoritative session-state-machine view and `workflows.md` for the
  authoritative per-workflow args/returns."

**Section 6 — Quality Lanes: Test, Lab, and SimQ Audit** (sources: `docs/ai/workflows.md` Test phase,
Section 5 above, `docs/simulation_quality/audit_workflow.md`):
- State explicitly there are **three distinct quality/testing lanes**, not two (correcting the ticket's
  own scope-text framing per investigation's finding — phrase this as this document's own clarification,
  not as "the ticket was wrong"):
  1. **Dev-pipeline Test phase** — `test-scoper` runs scoped pytest inside `implement-ticket`/
     `implement-epic`; gates on `TESTS_FAILED`. Code correctness only.
  2. **Simulation lab workflow chain** (Section 5) — simulation *behavior* discovery, hypothesis
     generation, and knowledge capture; human-gated at 3 stages.
  3. **SimQ audit** (`simq-audit`, this section below) — narrow calibration/anchor-drift maintenance for
     the 10-pillar SimQ grading system specifically.
- SimQ audit's **7 phases**, cite `.claude/workflows/simq-audit.js` (or `audit_workflow.md`, which
  investigation confirms matches code — safe to cite directly): Recalibrate → Classify Drift → Update
  Anchors → Sync Docs → Parity Check → Verify → Report.
  - Recalibrate: runs `make simq-full-audit`/`-full`/`-slow`; the only non-judgment phase.
  - Classify Drift: classifies each item as `EXPECTED_DRIFT` (must cite a specific commit/ticket) /
    `REGRESSION` / `DA_NEEDED` / `NO_ACTION`; rollup verdict `no_regression` / `regression` /
    `needs_da_decision`.
  - Update Anchors: edits `grade_anchors.json` + anchor key lists, `EXPECTED_DRIFT` items only; gate
    `ANCHORS_STILL_FAILING`.
  - Sync Docs, Parity Check, Verify (DoD-style gate, `BLOCKED` on failure), Report (deterministic branch:
    `no_regression` → `DONE_NO_TICKET`; else → spawns one ticket via `ticket-scoper`, returns
    `NEEDS_TICKET`).
  - State the explicit scope boundary verbatim in spirit: "`simq-audit` never changes SimQ scoring
    formulas or pillar logic (`src/simulation_quality/*` is out of scope for it) — it only maintains
    calibration anchors and drift classification."
  - Standalone-invocable: does not require or by default create a ticket; only the regression/DA-needed
    branch spawns one.
- Link out: "See `docs/simulation_quality/audit_workflow.md` for the full phase-by-phase mechanics and
  Do-Not list."

**Section 7 — Observability and Where to Go Deeper** (sources: `docs/agent-monitoring/schema.md`,
`docs/guides/agent_monitoring.md`, `docs/ai/agent_infrastructure_audit.md`):
- 3 append-only JSONL files joined by `run_id` (+`seq` for tools.jsonl):
  - `runs.jsonl` — one record per workflow invocation (`run_id`, `start_ts`, `end_ts` nullable,
    `workflow`, `tier`, `final_status`, `agent_count`, `duration_s`); no token/cost telemetry (explicit
    documented gap).
  - `events.jsonl` — one record per agent call, FK `run_id`+`seq` (`phase`, `agent`, `summary` ≤200
    chars, `status`, `tool_call_count`).
  - `tools.jsonl` — one record per tool call, FK `run_id`+`seq` via `.claude/current_run` sidecar
    (`tool`, `input_summary` ≤120 chars, `status`, `duration_ms`).
- The retro process: cadence (5+ completed tickets / weekly / before changing agent prompts or tier
  rules, nudged by a `PostToolUse` hook), `generate_retro.py`, report sections, `validate.py`'s
  correspondence checks.
- The recent `TCK-20260705-MONITORING-RUNID-JOIN` fix: 107/107 flagged incomplete runs confirmed
  genuinely done (98 direct match + 9 terminal-status/child match), 1 permanent documented exception
  (`TCK-20260623-TYPE-CHECKER`).
- One paragraph citing `agent_infrastructure_audit.md`'s headline exactly: **8.0/10**, "Mature, gated,
  not yet deterministic" — with 1-2 top strengths/risks quoted, not re-derived or re-scored.
- **Dated observation on doc staleness** (the one place this ticket records the workflows.md/skills.md/
  README.md gaps — see Plan Summary's "Follow-up ticket decision"): a short, clearly-dated paragraph,
  e.g.: "Note (as of 2026-07-05): `docs/ai/workflows.md` does not yet document `simq-audit` as an 11th
  workflow, and its phase lists for `create-tickets`, `generate-simulation-setup`,
  `investigate-simulation-result`, and `compact-simulation-result` do not match the current
  `.claude/workflows/*.js` phase arrays (this document cites the `.js` files directly for those four).
  `docs/ai/skills.md` similarly does not yet list a `/simq-audit` skill entry. These are candidates for a
  future documentation-maintenance ticket; this document does not modify those files." Do not phrase this
  as "these were fixed" or "this ticket corrected."
- Final "Where to Go Deeper" link list: all 10 source docs, one line each, grouped by topic (Agents/
  Workflows/Skills; Ticket Lifecycle; Simulation Lab; SimQ Audit; Observability).

**Do NOT touch:** any of the 8 source documents.

**Verify:** Re-read drafted Sections 5-7 against `docs/simulation/lab_contract.md`,
`docs/simulation_quality/audit_workflow.md`, `docs/agent-monitoring/schema.md`,
`docs/guides/agent_monitoring.md`, and `docs/ai/agent_infrastructure_audit.md`. Confirm the three-lane
framing is distinct (not 2 lanes). Confirm the lab_contract/workflows relationship is phrased as
inference, not fact. Confirm the staleness paragraph reads as an observation, not a claim of having
fixed anything.

---

### Step 3: Update the two doc indexes

**Files:** `docs/ai/README.md`, `docs/README.md`.

**Change A — `docs/ai/README.md` Document Index table** (currently L36-42): add exactly one new row.
Do not alter any existing row's text (including the stale "All 8 workflows" row for `workflows.md` —
out of scope to fix). Insert as the first row (most relevant entry point) or last row (newest-added) —
use **first row**, since this is the recommended starting point for a reader new to the system:

```
| [system_overview.md](system_overview.md) | Consolidated technical narrative — three-layer model, ticket lifecycle, simulation lab, SimQ audit, observability, with links to every detail doc |
| [agents.md](agents.md) | All 11 subagents — role, inputs, outputs, when to invoke |
| [workflows.md](workflows.md) | All 8 workflows — phases, args, return values, when to use |
| [skills.md](skills.md) | Project skills and built-in Claude Code skills |
| [ticket-lifecycle.md](ticket-lifecycle.md) | Complete development flow from request to closed ticket |
| [agent_infrastructure_audit.md](agent_infrastructure_audit.md) | Scored technical audit of the agent orchestration layer (2026-07-03) |
```

(Only the first row is new; the other five rows are reproduced here unchanged to show placement —
implementer must not edit their text.)

**Change B — `docs/README.md` AI Tooling section** (currently L185-194): add exactly one new bullet as
the first bullet in the list (same rationale — recommended starting point):

```
- [System Overview](ai/system_overview.md) — consolidated technical narrative of the full agent system
- [AI README](ai/README.md) — overview
- [Agents](ai/agents.md) — all subagents: roles, inputs, outputs
- [Workflows](ai/workflows.md) — multi-agent orchestration phases and return values
- [Skills](ai/skills.md) — slash commands for focused task patterns
- [Ticket Lifecycle](ai/ticket-lifecycle.md) — complete flow from request to closed ticket
```

(Only the first bullet is new; the rest are reproduced unchanged to show placement.)

**Do NOT touch:** either file's frontmatter (both already have valid frontmatter — `status: active`,
`layer: ai`/`guidelines`, `authority: P1`, `audience: developer` — untouched); any other section of
either file; any of the 8 source documents' own content.

**Verify:** `git diff docs/ai/README.md docs/README.md` shows exactly one added table row and exactly
one added bullet line respectively, with zero other line changes (confirms no accidental frontmatter or
adjacent-content mutation, per test_plan.md's Regression Surface note).

---

### Step 4: Run frontmatter validation and the regression pytest command

**Files:** none changed — verification only.

**Do:**
```
python3 tools/validate_frontmatter.py docs/ai/system_overview.md
python3 tools/validate_frontmatter.py staging_artifacts/TCK-20260705-AI-AGENT-OVERVIEW-DOC/investigation.md
python3 tools/validate_frontmatter.py staging_artifacts/TCK-20260705-AI-AGENT-OVERVIEW-DOC/plan.md
python3 tools/validate_frontmatter.py staging_artifacts/TCK-20260705-AI-AGENT-OVERVIEW-DOC/test_plan.md
python3 -m pytest tests/tools/test_validate_frontmatter.py -q
```

**Verify:** All five commands exit 0. If `validate_frontmatter.py` rejects `docs/ai/system_overview.md`,
fix the frontmatter block only (do not touch body content to work around a frontmatter failure).

---

## Scope Guards

- No edits to any of the 8 source documents' body content: `agents.md`, `workflows.md`, `skills.md`,
  `ticket-lifecycle.md`, `agent_infrastructure_audit.md`, `lab_contract.md`, `audit_workflow.md`, and
  (per test_plan.md's frontmatter-schema reference) `schema.md` under `docs/agent-monitoring/`. These are
  read-only inputs.
- No re-scoring or re-weighting of `agent_infrastructure_audit.md`'s 8.0/10 or its category breakdown —
  cite the headline and 1-2 points verbatim only.
- No assertion that `lab_contract.md`'s 6 stages and `workflows.md`'s 7 simulation workflows are an
  exact 1:1 correspondence — present as two related layers, phrase the mapping as illustrative/inferred.
- No new ticket file created for the workflows.md/skills.md/README.md staleness — record only as (a) one
  dated paragraph inside the new doc's final section, and (b) this ticket's own Completion Summary.
- No code, test, or `src/` changes — this ticket has zero regression surface beyond frontmatter
  validation.
- No new number is invented for "total workflows" beyond what investigation verified (11 files, 10
  documented in workflows.md, 1 — `simq-audit` — undocumented there). Never write "8 workflows" as a
  factual total anywhere in the new doc.
- Do not touch `docs/ai/README.md`'s or `docs/README.md`'s frontmatter blocks, or any line in those files
  outside the one new row / one new bullet specified in Step 3.

## Dependency Map

- Step 1 and Step 2 both write to the same new file (`docs/ai/system_overview.md`) — Step 2 must run
  after Step 1 completes (appends to the file Step 1 creates). Sequential, not parallel.
- Step 3 (index updates) is independent of Step 1/2's content but should run after Step 2 so the
  Document Index row's description text (if it mentions section coverage) reflects the finished doc.
  Sequential after Step 2.
- Step 4 (validation) depends on Steps 1-3 all being complete — must run last.
- No dependency on any other in-flight ticket. No code dependency at all.

## Acceptance Criteria Map

| Acceptance Criterion (from ticket) | Step(s) that satisfy it |
|---|---|
| New document exists, covering: three-layer model, full ticket-lifecycle/implementation workflow, simulation-testing/lab workflow, SimQ audit workflow, observability/monitoring, with accurate cross-references to all source docs | Step 1 (Sections 1-4), Step 2 (Sections 5-7) |
| Every specific claim (phase names, file paths, tier rules, gate names) is verified against the actual current source docs/code, not paraphrased from memory | Step 1 Verify, Step 2 Verify (re-check against primary sources, especially the 4 stale-in-workflows.md workflows sourced from `.js` files directly) |
| `docs/ai/README.md`'s Document Index has a new row for this document | Step 3 Change A |
| `docs/README.md`'s AI Tooling section references it | Step 3 Change B |
| Frontmatter passes `tools/validate_frontmatter.py` | Step 4 |

## Anti-Drift Notes

- The new document is a narrative synthesis with links out — it must not become a second copy of
  `agents.md`'s per-agent table or `workflows.md`'s per-workflow args/phase/return-value tables. If a
  reviewer finds the new doc reproducing a full table rather than summarizing + linking, that is a scope
  violation of this plan's Step 1/2 instructions, not an acceptable "thoroughness" addition.
- The 4 phase-list corrections (`create-tickets`, `generate-simulation-setup`,
  `investigate-simulation-result`, `compact-simulation-result`) must be attributed in the new doc's own
  prose to the `.claude/workflows/<name>.js` file, not to `workflows.md` — this is a hard citation
  requirement, not a style preference, per test_plan.md's Anti-Drift Test Guards (a reviewer should reject
  "workflows.md says X" as sourcing for these four).
- The three quality lanes (Test phase / simulation lab / SimQ audit) must remain three distinct
  subsections in Section 6, never merged into "two testing lanes" (the ticket's own Scope text uses "two
  distinct testing/quality lanes" language for the lab-vs-SimQ split, but investigation found a third,
  pre-existing lane — the dev-pipeline Test phase — that must also be named to keep the picture complete
  and non-misleading).
- The lab_contract.md/workflows.md relationship paragraph in Section 5 must use hedged language ("drives",
  "corresponds to", "no source states an exact mapping") — an implementer rewriting this into an
  unhedged 1:1 list (e.g., a table pairing all 6 stages to all 7 workflows as if verified) is a drift
  violation.
- The Section 7 staleness paragraph must read as a dated observation for future work, never as "fixed by
  this ticket" — Verify/done-checker should reject any wording implying `workflows.md`/`skills.md`/
  README.md were corrected.
- Step 3's two index edits are the ONLY permitted edits to `docs/ai/README.md` and `docs/README.md` —
  no incidental fixes to those files' other stale content (e.g., do not also fix README.md's "All 8
  workflows" line while in the file for the index edit; that line is explicitly out of scope).

## Unresolved Questions

None. Investigation's four flagged open questions (file path, "8 workflows" framing, follow-up-ticket
handling, lab_contract/workflows relationship framing) are all resolved by this plan (see Summary and
Section 5/7 guidance above) rather than deferred, since none of them require architecture-level judgment
beyond documentation-synthesis conventions already established by this repo's own doc patterns.
