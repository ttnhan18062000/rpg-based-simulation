---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-AI-AGENT-OVERVIEW-DOC
artifact_type: investigation
tags: [documentation, ai, workflows]
---

# Investigation — TCK-20260705-AI-AGENT-OVERVIEW-DOC

## Current Behavior

### (1) Three-layer model — `docs/ai/README.md`

`docs/ai/README.md` defines the model in one table (L14-18): **Agents** (`.claude/agents/*.md`,
spawned by workflows or via `Agent(subagent_type: "name")`), **Workflows** (`.claude/workflows/*.js`,
invoked via `Workflow({ name, args })` or `/workflow-name`), **Skills** (`.claude/skills/*/SKILL.md`
+ built-in, invoked via `/skill-name`). It gives a "when to use which" quick-reference (L24-30),
a Document Index (L34-42) listing 5 docs (agents.md, workflows.md, skills.md, ticket-lifecycle.md,
agent_infrastructure_audit.md — **not** the 3 additional sources this ticket also covers: lab_contract.md,
audit_workflow.md, agent-monitoring/schema.md), a Doc Registry Integration section (`docs/REGISTRY.yaml`,
912 entries, regenerate via `make docs-registry`), and 5 Design Principles (L61-69): separation of
concerns, hard gates, resumability (`ticket_id` skips completed phases), parity discipline (P0 entries
require a passing `test_path`), no silent scope creep (`planner` maps every step to an AC; `done-checker`
verifies scope match).

**Finding:** README.md's Document Index row for workflows.md literally reads "All 8 workflows" (L39).
This is stale — see (2) below; the actual count of documented workflows in workflows.md is 10, and the
actual file count in `.claude/workflows/` is 11 (one, `simq-audit.js`, is undocumented in workflows.md
entirely).

### (2) Ticket-lifecycle / implementation workflow — `docs/ai/agents.md`, `docs/ai/workflows.md`,
`docs/ai/ticket-lifecycle.md`, cross-checked against `.claude/workflows/*.js` and `.claude/agents/*.md`

**11 subagents confirmed** (`ls .claude/agents/*.md` = 11 files, matches `agents.md`'s claim exactly):
`ticket-scoper`, `investigator`, `planner`, `architecture-reviewer`, `done-checker` (Ticket Lifecycle
group); `implementer`, `test-scoper` (Implementation group); `parity-updater`, `mechanics-auditor`,
`world-debugger` (Quality/Compliance group); `simulation-analyst` (Analysis group). Each has documented
role/inputs/outputs/invoke-when in `agents.md` L28-287, plus an "Agent Summary Table" (L272-287) mapping
agent → lifecycle phase → primary output.

`done-checker`'s **11 Definition-of-Done conditions** are listed in `agents.md` L112-123 (numbered 1-11,
agent-monitoring not among them). `ticket-lifecycle.md`'s own DoD section (L269-289) is headed
"**11-condition table**" but its table actually renders **12 rows** — the 12th is "Agent monitoring
_(pre-marked PASS)_" — and later text in the same file (L346) explicitly calls this "**DoD condition
12**". So `ticket-lifecycle.md` is internally consistent that monitoring is condition 12 (not one of the
11), but its own table heading text ("11-condition table") undercounts the rows it displays by one — a
minor internal labeling inconsistency, not a factual error (agents.md's "11 conditions" is correct; the
12th, monitoring, is explicitly a separate, workflow-guaranteed condition not checked by the agent
itself). Root repo `CLAUDE.md`'s own "Definition of Done" section (unnumbered bullet list) has exactly
this same 11 + 1 shape: 11 substantive bullets, then a 12th ("Agent monitoring records written...
_(guaranteed by workflow — not verified by done-checker)_"). All three sources agree on substance; only
`ticket-lifecycle.md`'s heading text is loosely worded.

**Tier routing** — `ticket-lifecycle.md` L16-27 and `agents.md`/`workflows.md` all agree, and this
matches `CLAUDE.md`'s own "Tier Routing" table verbatim:

| Tier | Phases run | Use when |
|---|---|---|
| `hotfix` | Scope → Implement → Test → Parity → Verify → Finalize | Targeted fix, self-evident intent |
| `standard` | Full 9-phase pipeline (default) | Substantive feature/repair/refactor |
| `epic` | Scope only | Tracks child tickets, no direct implementation |

**9-phase pipeline** (standard tier), confirmed identical in `workflows.md` L78-89, `ticket-lifecycle.md`
L110-306, and the actual `phase(...)` calls in `.claude/workflows/implement-ticket.js` (grepped: Scope,
Investigate, Plan, Review, Implement, Test, Parity, Verify, Finalize — 9 calls, exact match, no
staleness here): Scope (`ticket-scoper`) → Investigate (`investigator`) → Plan (`planner`) → Review
(`architecture-reviewer`, gate: NEEDS_CHANGES/BLOCKED) → Implement (`implementer`) → Test
(`test-scoper`, gate: TESTS_FAILED) → Parity (`parity-updater`) → Verify (`done-checker`, gate:
DOD_BLOCKED) → Finalize (inline, no agent).

**Return statuses** (`workflows.md` L108-116, confirmed against `implement-ticket.js` grep for
`status:`): `CONFLICTS_DETECTED`, `NEEDS_HUMAN_INPUT`, `NEEDS_CHANGES`, `BLOCKED`, `TESTS_FAILED`,
`DOD_BLOCKED`, `DONE` — all 7 literal strings found in the actual `.js` source.

**`implement-epic`** — 3 phases confirmed identical in docs and code: `Discover` → `Implement` →
`Report` (grepped `phase(...)` in `implement-epic.js`: exact match). Args: `folder` | `epic_id` |
`request` (one of three, mutually exclusive per docs) | `tier_override` (optional). Return values include
`EPIC_CREATED`, `NOTHING_TO_DO`, `DONE`, or any child gate status.

**`create-tickets` — CONFIRMED STILL STALE.** `workflows.md` L34-41 documents only 3 phases: `Parse`
→ `Write` → `Link`. The actual `.claude/workflows/create-tickets.js` `meta.phases` array (L4-10) and
the executed `phase(...)` calls in the file body (L39, L204, L446, L672, and L847 conditionally) define
**5 phases**: `Comprehend` (read proposal, extract discrete concerns, no codebase investigation yet) →
`Investigate` (per-concern parallel: `tools/knowledge_search.py`, `graphify query`, `docs/REGISTRY.yaml`
via `registry_query.py`, `working_log.csv` grep, code reads, test lookup, tier assessment — schema
`INVESTIGATION_SCHEMA`) → `Structure` (one synthesis agent produces `TASK_SCHEMA`-shaped ticket fields
from investigation evidence only, handles merge/split/short_scope dedup) → `Write` (per-ticket, parallel,
`ticket-scoper` agentType, produces the actual `TCK-*.md` file + conditionally `SEQUENCE.md` if
intra-batch dependencies are detected) → `Link` (only if `epic_id` given). This is exactly the staleness
this ticket's brief flagged as previously found — **verified it still exists today (2026-07-05)**,
unchanged since it was presumably first noticed. `agent_infrastructure_audit.md` does not call out this
specific staleness (its scope was orchestration-layer scoring, not doc-vs-code line auditing).

**Additional NEW staleness found in `workflows.md` (Simulation Workflows section), not previously
flagged, discovered by diffing every documented phase list against its `.claude/workflows/*.js`
`meta.phases`:**

| Workflow | Docs say (workflows.md) | Code actually has (`meta.phases`) | Verdict |
|---|---|---|---|
| `generate-simulation-setup` | Spec Draft → Validation → Promotion | Scan → Draft → Validate | STALE — wrong names, missing "Scan," invented "Promotion" |
| `investigate-simulation-result` | Load → Analyze → Correlate → Report (4 phases) | Load → Analyze → Report (3 phases) | STALE — "Correlate" does not exist in code |
| `compact-simulation-result` | Inventory → Compact → Archive | Scan → Compact → Archive | STALE — "Inventory" vs. actual "Scan" |
| `prepare-simulation-execution` | Resolve → Estimate → Generate | Resolve → Estimate → Generate | Match |
| `register-simulation-result` | Validate → Index → Score | Validate → Index → Score | Match |
| `propose-simulation-enhancements` | Read → Hypothesize → Propose | Read → Hypothesize → Propose | Match |
| `update-knowledge-store` | Verify → Synthesize → Commit | Verify → Synthesize → Commit | Match |

**`simq-audit.js` is entirely undocumented in `workflows.md`.** It exists as an 11th workflow file
(`.claude/workflows/simq-audit.js`, 7-phase `meta.phases`: Recalibrate → Classify Drift → Update Anchors
→ Sync Docs → Parity Check → Verify → Report) and has its own skill folder
(`.claude/skills/simq-audit/SKILL.md`) and dedicated doc (`docs/simulation_quality/audit_workflow.md`),
but is not listed in `docs/ai/workflows.md`'s workflow catalog at all, and not in `docs/ai/skills.md`'s
"Project Skills (Workflow Shortcuts)" table either (see below). This means the actual count is **11
files in `.claude/workflows/`, 10 documented in `workflows.md`, 1 (`simq-audit`) fully undocumented
there** — so both README.md's "All 8 workflows" (L39) and the ticket's own framing of "the full 8
workflows" undercount by at least 2 relative to what `workflows.md` itself documents (10), and by 3
relative to the actual file count (11). `agent_infrastructure_audit.md` L80 states "Orchestration
workflows | 10 files / 8 documented" as of its 2026-07-03 review date — that count is now itself stale,
since `simq-audit.js` was added afterward (`docs/simulation_quality/audit_workflow.md` states "Last
updated: 2026-07-04", one day after the audit). Net: as of today (2026-07-05) there are 11 workflow
files, 10 are documented in `workflows.md` with phase tables, and `simq-audit` is the 1 fully
undocumented workflow.

**`docs/ai/skills.md` is also missing `simq-audit` entirely** — neither the "Project Skills (Workflow
Shortcuts)" table (L46-58, 10 rows) nor the "Project-Level Skill Files" table (L150-164, 12 rows)
mentions `/simq-audit`, despite `.claude/skills/simq-audit/SKILL.md` existing on disk. `ls
.claude/skills/*/` = 16 folders; `skills.md`'s two tables together account for all 16 *except*
`simq-audit` is missing from both (the 10-row workflow-shortcut table has 4 rows whose skill folder also
exists — create-tickets, implement-ticket, implement-epic, plus the 6 simulation-workflow skills that do
NOT have a dedicated `.claude/skills/` subfolder of their own name checked here — and the 12-row
"Project-Level Skill Files" table lists the other 12 folders). `agent_infrastructure_audit.md` L81 says
"Project skills | 14 | `.claude/skills/*/SKILL.md`" — also stale by 2 (actual is 16 today), consistent
with `simq-audit` (and inferably one other) having been added after that audit's 2026-07-03 date.

**Ticket-lifecycle.md's worked example** (`TCK-20260606-COMBAT-RELATION`, throughout the file) is
consistent with the phase/gate/artifact model described above — no additional staleness found there; it
correctly demonstrates Scope → Investigate → Plan → Review → Implement → Test → Parity → Verify →
Finalize with the "Manual Execution (Without the Workflow)" fallback (L393-424) matching the same 8-agent
sequence (done-checker is agent #8, matching the 9-phase pipeline minus the inline Finalize step).

### (3) Simulation-testing / lab workflow — `docs/simulation/lab_contract.md`, `docs/ai/workflows.md`
(Simulation Workflows + Simulation Workflow Order sections)

Two related but distinct things exist under "simulation testing":

- **The Claude Code simulation *workflows*** (`docs/ai/workflows.md` L178-367): 7 workflows —
  `generate-simulation-setup` → `prepare-simulation-execution` → [user triggers manually] →
  `register-simulation-result` → `investigate-simulation-result` (or lightweight `simulation-analyst`
  agent check) → `propose-simulation-enhancements` → [human reviews/approves] → `update-knowledge-store`
  → `compact-simulation-result` (cleanup, can run any time on registered runs). This sequence is
  explicitly diagrammed in the "Simulation Workflow Order" section (L345-367).
- **The Agentic Simulation Lab contract** (`docs/simulation/lab_contract.md`), a lower-level,
  code-defined session contract (`src/lab/`, 18 files) that the above workflows sit on top of / interact
  with. It defines its own **6 stages** (L62-72, in order): `GENERATION` → `EXECUTION_SUPPORT` →
  `REGISTRATION` → `INVESTIGATION` → `ENHANCEMENT` → `KNOWLEDGE_UPDATE`. Session states (L52-60):
  `ACTIVE` → `WAITING_FOR_USER` → ... → `COMPLETED` / `FAILED` / `ARCHIVED` (at any stage, by user
  action). **Human-gated concretely means:** stages `GENERATION`, `EXECUTION_SUPPORT`, and `ENHANCEMENT`
  (3 of the 6) require an explicit human `approval_status` of `APPROVED` before the session may advance
  past `WAITING_FOR_USER`; a `REJECTED` status terminates progression (L73). `ScenarioLabOrchestrator`
  (SCENARIO-012 through 015, `src/lab/orchestrator.py`) is the central engine: load+validate → instantiate
  isolated run (own namespace under `data/lab_sessions/`, never shares `AuthoritativeState`) → drive
  Kernel ticks (always single-threaded) → post-run analysis (comparison, metamorphic checks, mutation
  analysis).
  Safety guardrail: `BudgetGuardrail` (`src/lab/guardrails.py`) computes a `BudgetEstimation` pre-run
  and returns `OK` / `WARNING` (requires human confirmation, session → `WAITING_FOR_USER`) / `BLOCKED`
  (`BudgetBlockedError`, hard stop, no override path) — this is a second, budget-specific gate layered
  on top of the 3 stage-level approval gates.
  Mutation pipeline (`src/lab/mutation.py`, `mutation_orchestrator.py`): mutations apply to a *copy* of
  the spec, re-validate after each, roll back on failure — original spec is never mutated.
  Metamorphic testing (`src/lab/metamorphic.py`): 3 relation classes (001 symmetry, 002 monotonicity,
  003 equivalence); a metamorphic failure is recorded, not an abort.
  **This document's 6-stage session lifecycle is a distinct concept from workflows.md's 7-workflow
  sequence** — the mapping is roughly: GENERATION≈generate-simulation-setup, EXECUTION_SUPPORT≈
  prepare-simulation-execution, REGISTRATION≈register-simulation-result, INVESTIGATION≈
  investigate-simulation-result, ENHANCEMENT≈propose-simulation-enhancements,
  KNOWLEDGE_UPDATE≈update-knowledge-store — but `lab_contract.md` frames these as `src/lab/`-code-level
  session stages with approval-gate semantics, while `workflows.md` frames them as Claude-Code-agent
  orchestration steps. The new overview doc must be careful to present these as two layers of the same
  process (workflow layer invokes/drives the lab session layer), not conflate them as identical lists —
  neither source doc states the mapping explicitly, so this is an inference for the new doc to state
  carefully, not a verified 1:1 fact.

### (4) SimQ audit workflow — `docs/simulation_quality/audit_workflow.md`

A **separate, third quality lane** from both (2) and (3): a **7-phase** pipeline (defined in
`.claude/workflows/simq-audit.js`, invoked via `/simq-audit`, per `.claude/skills/simq-audit/SKILL.md`):
`Recalibrate` (runs `make simq-full-audit`/`-full`/`-slow`, the only non-judgment phase — diffs
calibration vs. `grade_anchors.json` via `tools/evaluate_simq.py --dry-run`, runs fast-tier grade
regression tests, cross-checks gaps via `tools/simq_audit_gaps.py`) → `Classify Drift` (agent classifies
each REGRESS/uncovered/parity item as `EXPECTED_DRIFT` [must cite a specific commit/ticket — never
"matches a recent pattern"] / `REGRESSION` / `DA_NEEDED` / `NO_ACTION`, computes rollup `verdict`:
`no_regression` / `regression` / `needs_da_decision`) → `Update Anchors` (edits `grade_anchors.json` +
`FAST_ANCHOR_KEYS`/`SLOW_ANCHOR_KEYS` in `tests/simulation_quality/test_grade_regression.py`, for
`EXPECTED_DRIFT` items only; gate: `ANCHORS_STILL_FAILING` if targeted pytest re-run fails) → `Sync Docs`
(updates `eval_matrix_results.md`, `D20_simq_integration.md`, conditionally
`event_type_coverage.md`/`v2_intentional_divergences.md`) → `Parity Check` (updates
`docs/parity_ledger/*.yaml` per `simq_audit_gaps.py` candidates) → `Verify` (DoD-style gate: regression
tests pass + zero uncovered anchor keys + every instructed doc touched or explicitly skipped; `BLOCKED`
on failure) → `Report` (deterministic branch, no agent call: `no_regression` → suggested chore-commit
message, returns `DONE_NO_TICKET`; `regression`/`needs_da_decision` → spawns one ticket via
`ticket-scoper`, returns `NEEDS_TICKET` with a `/implement-ticket ticket_id=...` hand-off). Governance:
`simq-audit` is standalone-invocable, does not require or by default create a ticket; only the
regression/DA-needed branch spawns one. Mechanical-only path exists with no agent session at all:
`make simq-full-audit[-full|-slow]` or `python3 tools/simq_audit_gaps.py` directly (always exits 0 —
informational, not a gate itself; the pytest step inside `make simq-full-audit` is the actual gate).
Explicit "Do not" list (L127-137): never let Update Anchors touch a REGRESSION/DA_NEEDED item's anchor
value; never skip the cause-citation requirement; never assume `data/calibration/` is committed
(untracked, like `data/runs/`).

### (5) Observability / monitoring — `docs/agent-monitoring/schema.md`, `docs/guides/agent_monitoring.md`

**3 append-only JSONL files, joined by `run_id`** (and `run_id`+`seq` for the third):

- **`runs.jsonl`** — one record per workflow invocation. Fields: `run_id` (ticket ID for
  `implement-ticket`; `EPIC-{id}`/`FOLDER-{path}` for `implement-epic`;
  `CREATE-TICKETS-{sanitized-source-path}` for `create-tickets`, confirmed in the actual
  `create-tickets.js` code at L97-98), `start_ts`, `end_ts` (nullable — null if crashed before the end
  write), `workflow`, `tier` (`n/a` for `create-tickets`), `final_status`, `agent_count`, `duration_s`.
  Token counts and per-agent tool-call counts are explicitly **not recorded** (schema.md L45-49) — this
  matches `agent_infrastructure_audit.md`'s flagged gap ("No cost or token telemetry, acknowledged in the
  docs," L53).
- **`events.jsonl`** — one record per agent call, FK `run_id`. Fields: `run_id`, `seq` (1-based,
  monotonic), `ts`, `phase`, `agent`, `summary` (≤200 chars; empty = prompt-quality signal), `status`
  (`ok`/`failed`/`blocked`/`skipped`), `tool_call_count` (nullable, computed by `writeMonitoring` from
  `tools.jsonl`). `phase` values differ per workflow: `implement-ticket` uses `Scope, Investigate, Plan,
  Review, Implement, Test, Parity, Verify, Finalize`; `create-tickets` uses `Comprehend, Investigate,
  Structure, Write, Link` (schema.md L107-113) — this independently corroborates the create-tickets
  staleness found in (2): the monitoring schema doc already reflects the correct 5-phase reality, while
  `workflows.md` still describes the old 3-phase version.
- **`tools.jsonl`** — one record per tool call, written by `PreToolUse`/`PostToolUse` hooks, FK'd to
  events by `run_id`+`seq` (via a `.claude/current_run` sidecar file each agent writes as its first Bash
  step). Fields: `session_id`, `run_id` (nullable — null outside an active workflow run), `seq`
  (nullable), `ts`, `tool`, `input_summary` (≤120 chars), `status` (`ok`/`failed`), `duration_ms`
  (nullable).

**"Known Limitations" section** (schema.md L195-221): (a) at least 5 legacy `runs.jsonl` schema
generations coexist with the current one, handled by `validate.py`'s `LEGACY_COMPLETION_FIELDS` /
`LEGACY_TERMINAL_STATUS_VALUES` allowlists — deliberately not backfilled (append-only precedent); (b)
the recent **`TCK-20260705-MONITORING-RUNID-JOIN`** fix: an exhaustive audit of 126 flagged
incomplete-run/zero-event records found 107/107 residual "Incomplete run (CRASHED?)" warnings were
genuinely completed (98 via direct `tickets/done/` match, 9 via terminal-status fields + independently-
DONE children); exactly 1 permanent, individually-verified exception remains
(`TCK-20260623-TYPE-CHECKER`, a 6th legacy shape, not worth allowlisting for a single record); (c)
manual/ad hoc `run_id` conventions (`run-{code}-{unix_ts}`, `-REDESIGN` suffixes) are confirmed
pre-refactor artifacts, not reproducible by current code — the rule for any future hand-written record is
to reuse the exact ticket ID verbatim, never invent a `run-{code}-{timestamp}` shape.

`docs/guides/agent_monitoring.md` covers the **retro process**: when to run (5+ completed tickets /
weekly / before changing agent prompts or tier rules — enforced-by-nudge via
`tools/agent-monitoring/retro_nudge_hook.py`, a `PostToolUse` hook, advisory-only, fires at most once per
session), `python3 tools/agent-monitoring/generate_retro.py` (current week / `--week` / `--days` /
`--all`), report sections (Run Summary, Gate Failure Breakdown, Tier Distribution — with the EPIC_SCOPED
denominator caveat noted, 44% vs. real 79% — Agent Status Distribution, Summary Quality, Slow Runs),
`validate.py` (checks working_log↔run-record correspondence, every run has ≥1 event, no silently-treated
crashed runs; tolerates both `final_status` and legacy `status`), and the retrospective write-up template
(What failed most / What was slow / What to change / What worked).

## Mechanics / Engine Constraints

N/A — this is a pure documentation-synthesis ticket. No `docs/mechanics/` or `docs/engine/` chapter
governs the AI agent tooling itself (it is meta-tooling about *how work gets done*, not simulation
mechanics); the Mechanics Bible and Engine Contracts are out of scope for this ticket's subject matter.

## Parity Ledger Overlap

N/A — no `docs/parity_ledger/*.yaml` subsystem covers AI tooling/workflow documentation; this ticket
produces no `behavior_changed` simulation logic, so no parity entry applies or needs updating.

## Prior Work

Confirmed no prior consolidated-overview attempt exists: `staging_artifacts/TCK-20260705-AI-AGENT-OVERVIEW-DOC/`
was empty prior to this investigation; `docs/ai/` contains exactly the 6 files this ticket already lists
as sources (README.md, agents.md, workflows.md, skills.md, ticket-lifecycle.md,
agent_infrastructure_audit.md) plus `_category_.json` — no 7th narrative/overview file. No ticket in
`tickets/` other than this one references "AI-AGENT-OVERVIEW" or a "consolidated" AI-tooling doc. The
ticket's own "Related Tickets: None" claim is correct.

## Risks and Open Questions

1. **Doc-vs-code staleness confirmed in `workflows.md`** (see Current Behavior §2-3 for full detail):
   - `create-tickets`: docs say 3 phases (Parse/Write/Link), code has 5 (Comprehend/Investigate/
     Structure/Write/Link) — the pre-flagged staleness, confirmed still present today.
   - `generate-simulation-setup`: docs say Spec Draft→Validation→Promotion, code has
     Scan→Draft→Validate — newly found, not previously flagged.
   - `investigate-simulation-result`: docs list an extra "Correlate" phase (Load→Analyze→Correlate→
     Report) that does not exist in code (actual: Load→Analyze→Report) — newly found.
   - `compact-simulation-result`: docs say Inventory→Compact→Archive, code has Scan→Compact→Archive
     ("Inventory" vs. "Scan") — newly found.
   - `simq-audit.js` (an 11th workflow file, 7-phase, with its own skill folder and dedicated doc) is
     **entirely absent** from `workflows.md`'s catalog and from `skills.md`'s two skill tables.
   - README.md's Document Index literally says "All 8 workflows" — undercounts both the 10 actually
     documented in `workflows.md` and the 11 actual files in `.claude/workflows/`.
   - `agent_infrastructure_audit.md`'s inventory counts ("10 files / 8 documented" workflows, "14"
     project skills) are themselves one day stale relative to `simq-audit.js`'s addition
     (audit dated 2026-07-03; `simq-audit` doc says "Last updated: 2026-07-04").
   These are documentation facts about *other* docs' staleness, not this ticket's own claims — the new
   overview doc must either (a) state the current phase names correctly by citing the actual `.js` files
   directly rather than trusting `workflows.md`'s stale prose for the 4 affected workflows, or (b) state
   the well-known-correct ones (prepare-simulation-execution, register-simulation-result,
   propose-simulation-enhancements, update-knowledge-store, implement-ticket, implement-epic) from
   `workflows.md` directly since those match code, while flagging the 4 stale ones as "see
   `.claude/workflows/<name>.js` for the current phase list" rather than repeating the wrong names.
   Whether Plan/Implement should also *fix* the staleness in `workflows.md`/`skills.md`/README.md itself
   is explicitly **out of scope for this ticket** (ticket's "Out of Scope" section forbids modifying any
   of the 8 source documents) — the new doc can only describe reality accurately and point out (in its
   own text, or not at all) that `workflows.md` is stale for those 4 entries; it cannot silently "correct"
   `workflows.md` in place. This should be flagged to the user/ticket as a candidate **follow-up ticket**
   (fixing `workflows.md`, `skills.md`, and README.md's stale counts) rather than folded into this one.
2. **Internal labeling nit in `ticket-lifecycle.md`**: its DoD section heading says "11-condition table"
   but the table has 12 rows (the 12th, Agent monitoring, is pre-marked PASS and explicitly called
   "condition 12" later in the same file). Not a factual error, just a loosely-worded heading. Low
   priority to even mention in the new doc; if mentioned, phrase as "11 substantive DoD conditions plus a
   12th, workflow-guaranteed monitoring condition," matching CLAUDE.md's own framing exactly.
3. **`lab_contract.md`'s 6-stage session lifecycle vs. `workflows.md`'s 7-workflow simulation sequence**:
   no source document states the explicit 1:1 (or 1:many) mapping between the two lists. The new overview
   doc needs to present them as two conceptual layers (Claude-Code workflow orchestration commanding an
   underlying `src/lab/` session state machine) without asserting an unverified exact correspondence —
   this is the one place in scope where synthesis requires interpretation beyond direct quotation, and it
   should be flagged as such in the new doc's own prose (e.g., "the workflow sequence above interacts
   with the lab session's 6-stage lifecycle described in lab_contract.md — see that document for the
   session-state-machine view of the same process") rather than presented as a verified equivalence.
4. **Open question for Plan**: how much of the "8 workflows" framing to carry into the new doc's title/
   framing given the count is actually 10 documented (11 total, 1 undocumented). Recommend the new doc
   simply says "the development and simulation workflows" without committing to a specific number, or if
   a number is needed, say "10 documented development/simulation workflows (plus `simq-audit`, a distinct
   quality-audit workflow covered separately)" — matching what was actually found, not perpetuating the
   stale "8" figure from README.md/the ticket's own scope text.

## Anti-Drift Hazards

- **Do not duplicate the full agent/workflow reference tables.** `agents.md`'s per-agent role/input/
  output prose and `workflows.md`'s per-workflow args/phase/return-value tables are the source of truth
  for exact schemas — the new doc should synthesize the *narrative* (what the three-layer model is, how
  a ticket flows end to end, how the two testing lanes differ, how observability closes the loop) and
  link out for every field-level detail, not re-render the tables.
  Also see [`docs/guides/ticket_tagging.md`](../../docs/guides/ticket_tagging.md) for the
  `Process/Skill-signal` tag→skill mapping referenced in `skills.md` L30-38 — do not re-derive that
  mapping table in the new doc either; link to it.
- **Do not silently "fix" the 4 stale workflows.md phase lists or the missing simq-audit entries** by
  writing the *correct* phase names into the new doc as if they were quoted from workflows.md — if the
  new doc states phase names for those 4 workflows, it must cite `.claude/workflows/<name>.js` as the
  source (since workflows.md is wrong there), not attribute the correct names to workflows.md.
- **Do not conflate the 3 quality/testing lanes.** There are three genuinely distinct lanes documented
  across the 10 sources: (a) the `implement-ticket`/`implement-epic` dev pipeline's Test phase
  (`test-scoper`, scoped pytest) — code correctness; (b) the simulation-lab workflow chain
  (`generate-simulation-setup` → ... → `update-knowledge-store`, backed by `src/lab/`'s 6-stage
  human-gated session) — simulation *behavior* discovery and knowledge capture; (c) `simq-audit` — a
  narrower, config/anchor-calibration lane for the 10-pillar SimQ grading system specifically, which
  explicitly does NOT touch scoring formulas/pillar logic (`audit_workflow.md` L127-130 "Do not" list).
  The new doc must keep these three distinct, not merge (b) and (c) into one "simulation testing"
  section, since the ticket's own Scope text calls out "(the two distinct testing/quality lanes)" for (b)
  vs (c) but this investigation found they are better framed as three lanes total once (a) is counted.
- **Do not re-score or re-audit the agent infrastructure.** `agent_infrastructure_audit.md`'s 8.0/10
  score and its 7-category breakdown, strengths, risks, and 5 ranked recommendations are a finished,
  dated (2026-07-03) artifact — cite its headline score and 1-2 top risks/strengths for context, do not
  re-derive or re-weight the categories.
- **Do not present `lab_contract.md`'s 6 stages and `workflows.md`'s 7 simulation workflows as the same
  numbered list** — see Risk #3 above. Keep them as two related but separately-sourced views.
