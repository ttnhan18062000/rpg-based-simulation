---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260709-CONCERN-INVESTIGATOR-AGENT
artifact_type: plan
tags: [ai, investigator, workflows]
---

# Implementation Plan — TCK-20260709-CONCERN-INVESTIGATOR-AGENT

## Summary

Extract create-tickets.js's ~115-line inline Investigate-phase methodology (search_docs → graphify → REGISTRY.yaml → working_log.csv → code read → test discovery → AC-signal derivation → tier assessment) into a new, tool-scoped agent definition, `.claude/agents/concern-investigator.md`, structurally distinct from `investigator` (JSON-returning, concern-scoped, pre-ticket — not file-writing, ticket-ID-scoped). The new agent's frontmatter adds a `tools:` field restricting it to read/search tools (`Read, Grep, Glob, Bash, WebFetch, WebSearch, mcp__knowledge-search__search_docs`) — the first `tools:`-restricted custom agent in this repo, mirroring the built-in `Explore` type's restriction pattern but tuned for a research-only, non-code-search role. `create-tickets.js`'s per-concern `agent()` call is updated to pass `agentType: 'concern-investigator'` and its prompt is shrunk to concern-specific substitutions only (id, title, description, domain_area, type_hint, priority_hint, raw_excerpts, registryLayers), since the durable methodology now lives in the agent file. A new static test file validates both the frontmatter/content shape of the new agent file and the shape of the updated dispatch call — this is the only verification achievable within this session; live tool-enforcement and harness `agentType` resolution require a session restart (per `TCK-20260707-SUBAGENT-FRONTMATTER` precedent) and are explicitly deferred, not silently marked done. `docs/ai/agents.md` gets a new `concern-investigator` subsection under Ticket Lifecycle Agents, distinct from `investigator`'s, including a "When to invoke directly" note since direct/manual invocation is being adopted with no restriction.

Three questions the investigation flagged as open are resolved here, not deferred:
1. **Direct invocation**: adopted, unrestricted — no invocation-context gating is implemented; the tool-scoping itself is what provides safety, gating who calls it adds complexity for no benefit. Documented as directly invokable in Step 4, matching `investigator`/`world-debugger`/`simulation-analyst` precedent.
2. **`.claude/skills/create-tickets/SKILL.md`'s own inline restatement (lines 48-75)**: left untouched — out of this ticket's stated Scope (only names `concern-investigator.md`, `create-tickets.js`, `docs/ai/agents.md`). Named explicitly under Scope Guards and flagged as a candidate follow-up ticket if it drifts.
3. **Tool-scoping verification**: two-part design — (a) a static pytest test parses the new file's frontmatter and asserts `tools:` exists and excludes `Edit`/`Write`/`NotebookEdit` (verifiable now); (b) the ticket's Implementation Notes must state plainly that live runtime enforcement is unverified pending session restart — a known limitation of this run's own verification, not a defect, and not to be glossed as "done."

## Steps

### Step 1 — Create `.claude/agents/concern-investigator.md`
**Files:** `.claude/agents/concern-investigator.md` (new)
**Change:**
- Frontmatter, matching the existing 12-agent 2-field convention plus one new field:
  ```yaml
  ---
  name: concern-investigator
  description: Given a proposal concern (not yet a ticket), investigates the codebase via search_docs → graphify → registry → working_log ordering and returns structured JSON findings for create-tickets.js's Structure phase — read-only, no file writes.
  tools: Read, Grep, Glob, Bash, WebFetch, WebSearch, mcp__knowledge-search__search_docs
  ---
  ```
  The `tools:` list is deliberately Edit/Write/NotebookEdit/Agent/Artifact/ExitPlanMode-free — this phase never mutates repo state. `Bash` stays in-scope because the methodology itself shells out to `python3 tools/knowledge_search.py`, `graphify query`, `python3 -c "...registry_query..."`, and `grep`/`find` — removing `Bash` would break the very steps this agent must perform.
- Body: a `# Concern Investigator` heading, then an `## Inputs` section stating the agent receives a **concern** (not a ticket_id) with fields `id`, `title`, `description`, `domain_area`, `type_hint`, `priority_hint`, `raw_excerpts`, and a derived `registryLayers` list — supplied per-call by the caller's prompt, not read from a ticket file.
- Then a `## Methodology` section that is a **direct extraction** of `create-tickets.js:312-406`'s Step 0–7 ordering (semantic retrieval → graphify → REGISTRY.yaml query via `candidate_tags_from_text`/`filter_registry` → `working_log.csv` grep + `stored_artifacts/` cross-reference → code file reads → test discovery → AC-signal derivation with the same Bad/Good examples → tier assessment with the same hotfix/standard split criteria) — reworded from the JS template-literal form (which interpolates `${concern.title}` etc.) into generic prose that refers to "the concern" and "its `registryLayers`", preserving every step's actual mechanics (same scripts, same fallback behavior, same ordering discipline) so this is a move, not a rewrite. Do not drop the "Do NOT invent file paths — report only what the tools actually return" instruction (`create-tickets.js:310`).
- Then an `## Output` section stating the exact JSON contract, copied field-for-field from `INVESTIGATION_SCHEMA` (`create-tickets.js:210-263`): `concern_id, files_found, constraints, existing_tests, related_tickets, ac_signals, risks, is_duplicate, duplicate_of, tier_recommendation, summary` — with the same per-field descriptions (e.g. `constraints` format `"docs/mechanics/03_economic_laws.md: <rule summary>"`, `summary` ≤200 chars). State explicitly: "Return JSON matching this schema. Do not write files to disk." — this is the structural distinction from `investigator` (Scope item 3 of the ticket).
- State the ≤200-char one-sentence-summary convention explicitly per the `TCK-20260607-MON-AGENTS` precedent (investigation.md Prior Work).
**Do NOT touch:** `.claude/agents/investigator.md`, any of the other 11 `.claude/agents/*.md` files, `INVESTIGATION_SCHEMA`'s definition in `create-tickets.js` (read it, copy it verbatim into the new file — do not edit the schema itself).
**Verify:** `test_concern_investigator_agent_file_exists_and_has_frontmatter`, `test_concern_investigator_encodes_context_scan_ordering` (Step 3).

### Step 2 — Update `create-tickets.js`'s Investigate-phase dispatch
**Files:** `.claude/workflows/create-tickets.js` (lines ~296-412 only)
**Change:**
- In the `agent(...)` call inside `pipeline(comprehension.concerns, (concern) => { ... })`, add `agentType: 'concern-investigator'` to the options object alongside the existing `label` and `schema`:
  ```js
  { agentType: 'concern-investigator', label: `investigate:${concern.id}`, schema: INVESTIGATION_SCHEMA }
  ```
- Shrink the prompt string (currently lines 297-410) to **only** the concern-specific substitutions the agent needs per-call — no methodology restatement:
  ```
  Investigate concern "${concern.id}: ${concern.title}".

  Concern (from proposal):
    Title: ${concern.title}
    Description: ${concern.description}
    Domain area: ${concern.domain_area}
    Type hint: ${concern.type_hint}
    Priority hint: ${concern.priority_hint}

  Raw excerpts from proposal:
  ${concern.raw_excerpts.map(e => `  - ${e}`).join('\n')}

  Registry layers to search: ${registryLayers.join(', ')}

  Return: concern_id="${concern.id}", plus all other INVESTIGATION_SCHEMA fields per your system prompt's methodology.
  ```
- Keep `INVESTIGATION_SCHEMA` (lines 210-263) and `DOMAIN_TO_LAYERS` (lines 266-288) exactly as-is — both are still needed (`schema` option, `registryLayers` derivation) and are explicitly out of scope to change (ticket AC #3).
- Keep the `domainKey`/`registryLayers` derivation logic (lines 293-294) unchanged; it now only needs to compute the value to interpolate into the shrunk prompt, not to build multi-step instructions around it.
**Do NOT touch:** the Structure phase's `suggested_skills` tag→skill table (lines ~599-608, the thing `test_tag_skill_mapping_check.py` parses), the Write phase's `agentType: 'ticket-scoper'` call (line ~785), the Comprehend/Link-epic/monitoring-write call sites (lines 139, 184, 622, 908), `INVESTIGATION_SCHEMA`'s field list itself, `DOMAIN_TO_LAYERS`.
**Verify:** `test_investigate_phase_uses_concern_investigator_agent_type` (Step 3); existing `tests/tools/test_tag_skill_mapping_check.py` must stay green (regression guard — proves the edit didn't bleed into the adjacent Structure-phase table).

### Step 3 — Add static tests
**Files:** `tests/tools/test_concern_investigator_agent_definition.py` (new)
**Change:** Add:
- `test_concern_investigator_agent_file_exists_and_has_frontmatter` — asserts `.claude/agents/concern-investigator.md` exists; parses its frontmatter block as YAML; asserts `name == 'concern-investigator'`, `description` is non-empty, and a `tools` field exists whose value (parse as comma-separated list) does **not** contain `Edit`, `Write`, or `NotebookEdit`.
- `test_concern_investigator_encodes_context_scan_ordering` — reads the file body as text; asserts that string-index positions of `search_docs` (or `mcp__knowledge-search__search_docs`), `graphify query`, `docs/REGISTRY.yaml`, and `tickets/working_log.csv` occur in that relative order (mirrors the `extract_pairs_*`-style text-as-data parsing already used by `test_tag_skill_mapping_check.py`).
- `test_investigate_phase_uses_concern_investigator_agent_type` — reads `.claude/workflows/create-tickets.js` as text; asserts the Investigate-phase `agent(...)` call (locate via the `investigate:${concern.id}` label string) contains `agentType: 'concern-investigator'`; asserts the methodology step headers (`"Step 0: Semantic prior-work retrieval"`, `"Step 1: Knowledge graph"`, `"Step 2: Docs and prior tickets"`, etc.) are **absent** post-change — a positive signal the extraction happened rather than merely being duplicated.
- `test_investigation_schema_definition_unchanged` (recommended per test_plan.md) — regex/string-containment check that `INVESTIGATION_SCHEMA`'s `required` array in `create-tickets.js` still lists all 10 original field names.
- `test_agents_doc_has_concern_investigator_heading` (optional, include if low-cost) — asserts `docs/ai/agents.md` contains a `### \`concern-investigator\`` heading distinct from (not nested under) `### \`investigator\``.
**Do NOT touch:** `tests/tools/test_tag_skill_mapping_check.py` itself (run it, don't edit it), any `tests/unit/`, `tests/integration/`, or `tests/simulation_quality/` path — no `src/` files are touched by this ticket.
**Verify:** Run `.venv/bin/python3 -m pytest tests/tools/test_tag_skill_mapping_check.py tests/tools/test_concern_investigator_agent_definition.py -v` — all pass.

### Step 4 — Document in `docs/ai/agents.md`
**Files:** `docs/ai/agents.md`
**Change:**
- Add a new `### \`concern-investigator\`` subsection immediately after the existing `### \`investigator\`` subsection (before `### \`planner\``), following the established per-agent structure (Role / What it does / Inputs / Outputs / When to invoke directly):
  - **Role:** Investigates a pre-ticket proposal concern and returns structured JSON findings for `create-tickets.js`'s Structure phase — distinct from `investigator`, which operates on an existing ticket and writes markdown files.
  - **What it does:** search_docs → graphify → REGISTRY.yaml → working_log.csv → code read → test discovery → AC-signal derivation → tier assessment, read-only (no `Edit`/`Write`/`NotebookEdit` tool access).
  - **Inputs:** A concern object (`id`, `title`, `description`, `domain_area`, `type_hint`, `priority_hint`, `raw_excerpts`) and derived `registryLayers` — no ticket file required or read.
  - **Outputs:** JSON matching `INVESTIGATION_SCHEMA` (`files_found`, `constraints`, `existing_tests`, `related_tickets`, `ac_signals`, `risks`, `is_duplicate`, `duplicate_of`, `tier_recommendation`, `summary`) — never writes files to disk.
  - **When to invoke directly:** Adopted per this ticket's resolution of the direct-invocation question — available for ad hoc "investigate this idea before I write a ticket" use, same as `investigator`/`world-debugger`/`simulation-analyst` are documented as directly invokable. No invocation-context restriction; the tool-scoping (not caller identity) is what makes this agent safe to expose broadly.
  - A one-line explicit contrast: "Use `investigator` when a ticket already exists and you need file-based artifacts; use `concern-investigator` when you have a pre-ticket idea and want structured findings back without writing anything."
- Add a `concern-investigator` row to the **Agent Summary Table** at the bottom (after the `investigator` row): `| \`concern-investigator\` | Pre-work (pre-ticket) | Structured JSON (files_found, ac_signals, ...) |`.
**Do NOT touch:** any other agent's existing subsection or table row; `.claude/skills/create-tickets/SKILL.md` (explicitly out of scope per resolution #2 above — do not edit it in this step even though its Pipeline section describes the same phase).
**Verify:** `test_agents_doc_has_concern_investigator_heading` if added in Step 3; otherwise manual read-through confirming the heading is distinct from `investigator`'s.

## Scope Guards

- Do not edit `.claude/agents/investigator.md` or any of the other 11 existing `.claude/agents/*.md` files — no frontmatter, no body content, no tool restriction added to any of them. This ticket adds exactly one new file.
- Do not widen `investigator`'s contract to support a second (JSON-returning) output mode. `investigator` keeps writing `investigation.md`/`test_plan.md` for an existing `ticket_id`, unchanged.
- Do not touch `implement-ticket.js` or `implement-epic.js` — both use `agentType: 'investigator'` for the standard-tier pipeline; `concern-investigator` must never be substituted there.
- Do not edit `.claude/skills/create-tickets/SKILL.md` (its lines 48-75 inline methodology restatement is a known, disclosed third copy per investigation.md Risk #3 — explicitly left out of this ticket's Scope, not silently ignored; flag as a candidate follow-up ticket if it visibly drifts from the new agent's actual behavior).
- Do not change `INVESTIGATION_SCHEMA`'s field list, types, or `required` array in `create-tickets.js` — AC #3 requires this schema stay byte-identical. Copy it into the new agent file verbatim; never edit the source definition.
- Do not touch `DOMAIN_TO_LAYERS` (`create-tickets.js:266-288`) or the Structure/Write/Link-epic phases of `create-tickets.js` (out of scope per ticket).
- Do not touch `tests/tools/test_tag_skill_mapping_check.py` — it is a regression guard to keep passing, not a file to modify.
- Do not attempt a live `Agent(subagent_type: "concern-investigator", ...)` smoke-test call within this same implementation session — per `TCK-20260707-SUBAGENT-FRONTMATTER` precedent, `.claude/agents/` is not hot-reloaded mid-session; a first-attempt "type not found" or unrestricted-tools result is expected and is not a defect to fix now. Document this explicitly in the ticket's Implementation Notes rather than attempting a workaround.
- Do not add any new parity ledger entries — investigation confirmed no `docs/parity_ledger/*.yaml` entry governs `.claude/agents/` or `create-tickets.js` (grepped all 8 files).

## Dependency Map

- Step 1 (new agent file) and Step 2 (create-tickets.js dispatch update) are content-independent — Step 2's `agentType: 'concern-investigator'` string reference does not require Step 1's file to exist for the *text edit* to be made, but Step 1 should land first so the reference is meaningful and Step 4's documentation accurately describes a file that exists. Recommended order: 1 → 2 → 3 → 4.
- Step 3's tests depend on both Step 1 (parses the new agent file) and Step 2 (parses the updated dispatch call) having landed — run Step 3 last among the code-touching steps.
- Step 4 (docs) depends on Step 1's finalized contract description (Inputs/Outputs field names) to avoid documenting something that doesn't match the actual file — do after Step 1, can be done in parallel with Step 2/3 in principle, but sequencing after Step 1 is simplest.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC #1 — `concern-investigator.md` exists, encodes mandatory context-scan ordering, does not grant Edit/Write/NotebookEdit | Step 1 | `test_concern_investigator_agent_file_exists_and_has_frontmatter`, `test_concern_investigator_encodes_context_scan_ordering` — **structurally satisfied and statically verified this session; live runtime tool-enforcement (does the harness actually refuse an Edit call from this agent type) is unverified pending a required session restart — see Anti-Drift Notes. Do not report as "fully verified end-to-end."** |
| AC #2 — Investigate phase invokes `agentType: 'concern-investigator'`, prompt reduced to concern-specific substitutions | Step 2 | `test_investigate_phase_uses_concern_investigator_agent_type`; regression guard `test_tag_skill_mapping_check.py` |
| AC #3 — end-to-end run still produces `INVESTIGATION_SCHEMA`-conformant JSON, schema unchanged | Step 1 (schema copied verbatim, not edited), Step 2 (schema definition untouched) | `test_investigation_schema_definition_unchanged` (static field-list check); the actual end-to-end run is a **manual verification step outside pytest**, and — like the live tool-enforcement check — cannot be executed until a new agent type is resolvable, i.e. after a session restart. Static verification (schema untouched, dispatch correctly wired) is what this session can confirm. |
| AC #4 — `docs/ai/agents.md` documents `concern-investigator` under a distinct heading, states when to use each | Step 4 | `test_agents_doc_has_concern_investigator_heading` (if added) or manual read-through |

## Anti-Drift Notes

- **Schema drift**: `INVESTIGATION_SCHEMA` must stay byte-identical (AC #3). The new agent's `## Output` section must describe this exact same JSON contract, field names and descriptions verbatim — not a paraphrase, not an "improved" version. Any mismatch will silently corrupt the Structure phase's `investigationBundle` consumer.
- **Frontmatter minimalism precedent**: `TCK-20260707-SUBAGENT-FRONTMATTER` established that `.claude/agents/*.md` frontmatter changes must be additive and must not touch the other 11 files. This ticket's `tools:` field is a genuine first — the first custom agent in this repo to declare one — so there is no in-repo precedent proving the harness enforces it. Treat the addition as "structurally correct, functionally unverified" until a session restart permits a live smoke test (mirrors `TCK-20260707`'s own registration-verification gap).
- **Session-restart requirement**: do not attempt to invoke `Agent(subagent_type: "concern-investigator", ...)` within this same implementation session and interpret a failure or an unrestricted-tools result as a bug — the harness does not hot-reload `.claude/agents/` mid-session (confirmed precedent). Record this explicitly in the ticket's Implementation Notes as a stated limitation, not a silently-passed check.
- **Prompt-shrink must not drop substitutions**: Step 2's shrunk prompt must still interpolate `concern.id`, `concern.title`, `concern.description`, `concern.domain_area`, `concern.type_hint`, `concern.priority_hint`, `concern.raw_excerpts`, and `registryLayers` — losing any of these silently degrades the new agent's per-call context even though the methodology itself is intact in the system prompt.
- **"investigator" naming collision risk**: `concern-investigator` and `investigator` share a name stem and a conceptual neighborhood. It is easy to accidentally "clean up" by pointing `implement-ticket.js`/`implement-epic.js`'s existing `agentType: 'investigator'` calls at the new type, or by copy-editing `investigator.md` itself while working on the new file open in an adjacent tab. Neither must happen — confirm `git diff --stat` at the end of implementation shows only `concern-investigator.md` added and `create-tickets.js` / `docs/ai/agents.md` / the new test file modified.
- **SKILL.md is a known, disclosed gap, not an oversight**: `.claude/skills/create-tickets/SKILL.md:48-75` will now describe the Investigate-phase methodology in a way that has drifted one step further from the actual implementation (now living in `concern-investigator.md`, not `create-tickets.js`). This is intentional per resolution #2 — do not "fix" it as a drive-by change.

## Deviations

- **Step 1 Inputs wording**: the plan's Step 1 description of the `registryLayers` input field did not specify exact wording. During implementation, the Inputs section's bullet was worded as "REGISTRY.yaml layers" (no `docs/` prefix) rather than "`docs/REGISTRY.yaml` layers", so that the literal string `docs/REGISTRY.yaml` first appears in the Methodology's Step 2 section rather than earlier in Inputs — this keeps `test_concern_investigator_encodes_context_scan_ordering` (Step 3's ordering test) meaningful, since it asserts `search_docs` -> `graphify query` -> `docs/REGISTRY.yaml` -> `tickets/working_log.csv` occur in that relative order across the file. No content or meaning was lost; purely a phrasing choice, discovered while writing the test in the same implementation pass.
- No other deviations. All four steps landed as specified: `concern-investigator.md` created with the `tools:` field and extracted methodology; `create-tickets.js`'s Investigate-phase dispatch updated with `agentType: 'concern-investigator'` and a shrunk prompt, `INVESTIGATION_SCHEMA`/`DOMAIN_TO_LAYERS` byte-identical; static tests added and passing; `docs/ai/agents.md` documented with a distinct heading and summary-table row. The session-restart-required limitation on live runtime verification (tool-enforcement, agentType resolution) was anticipated by the plan and is disclosed as unverified in the ticket's Implementation Notes, not silently marked done.
