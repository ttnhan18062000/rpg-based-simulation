---
status: active
layer: ai
authority: P1
audience: developer
---

# Subagents

Subagents are focused system-prompt files in `.claude/agents/*.md`. Each agent owns exactly one responsibility in the task pipeline. They are invoked by workflows or directly from the main session.

**Invocation pattern:**
```python
Agent(subagent_type="agent-name", prompt="task description with all needed context")
```

Within a workflow script, the `agentType` option loads the agent's system prompt:
```js
await agent("do X", { agentType: 'agent-name' })
```

---

## Brainstorming Agents

These agents support the `/brainstorming` skill, which runs before a ticket exists — its output
(a design spec at `docs/architecture/YYYY-MM-DD-<topic>-design.md`) feeds `/create-tickets`, which
in turn produces the tickets the agents below act on.

### `spec-document-reviewer`

**Role:** Reviews a written design spec for completeness, internal consistency, clarity, scope
focus, and YAGNI violations before implementation planning begins.

**Scope:** The spec document's own internal quality — not simulation-mechanics parity
(`mechanics-auditor`'s job) or durable-state/API-boundary architecture (`architecture-reviewer`'s
job). Registered `TCK-20260811-BRAINSTORMING-SPEC-REVIEWER-AGENT-MISSING`, replacing an
unregistered generic-agent-plus-inline-prompt template that the `/brainstorming` skill's own
instructions had already drifted to reference as a named subagent type.

**Review dimensions:** Completeness (TODOs/placeholders), Consistency (internal contradictions),
Clarity (ambiguity that could cause the wrong thing to be built), Scope (single-plan focus), YAGNI
(unrequested features).

**Output:** Approved / Issues Found verdict, per-issue findings tied to a spec section, advisory
recommendations (non-blocking).

**When to invoke directly:** `/brainstorming`'s own Spec Review Loop step, immediately after the
design spec is written and committed — never with the invoking session's own conversation history
as context, only the spec file itself.

---

## Ticket Lifecycle Agents

These agents handle the pre-implementation and post-implementation phases of a development ticket.

### `ticket-scoper`

**Role:** Creates a correctly-formatted ticket and scans for conflicts before any work begins.

**What it does:**
- Scans `tickets/inprogress/`, `tickets/done/`, `tickets/backlogs/`, `docs/`, `stored_artifacts/`, and relevant source files for duplicate work, conflicting requirements, or architectural mismatches — a hit in `tickets/backlogs/` means the work was already investigated and deliberately deprioritized, not abandoned
- Produces `tickets/inprogress/TCK-YYYYMMDD-SHORT-SCOPE.md` with all required sections
- Creates `staging_artifacts/{ticket_id}/`
- Picks tags per `docs/guidelines/tag_taxonomy.md`, ideally from what `python3 tools/tag_registry.py list` already shows registered — the orchestrator checks this after the agent returns and gates on it (`TAGS_NOT_REGISTERED`, `TCK-20260706-SCOPE-TAG-REGISTRY-CHECK`), so this agent's own choice doesn't need to enforce it itself

**Inputs:** A request description (free text) or an existing ticket path.

**Outputs:**
- Ticket file at `tickets/inprogress/{ticket_id}.md`
- Staging directory
- Conflict report (if any)
- `suggested_skills` list (skill/agent invocations mapped from the ticket's `Process/Skill-signal` tags — e.g. `debugging` -> `/debugging-strategies` or `world-debugger`; empty if no tag maps)
- `tag_relevance_flags` list (one string per assigned tag whose registered note/category doesn't
  clearly match the ticket's own title/scope/related_code_areas; empty if all tags fit — advisory
  only, never rejects a tag)

**When to invoke directly:** When you want to draft a ticket for human review before running the full `implement-ticket` workflow.

---

### `investigator`

**Role:** Deep-reads the affected codebase and produces the two mandatory pre-plan artifacts.

**What it does:**
- Reads the ticket, all "Related Code Areas" files, relevant `docs/mechanics/` and `docs/engine/` chapters, and `docs/parity_ledger/` for overlapping entries
- Searches `stored_artifacts/` and `tickets/done/` for prior work in the same area (including tag-based matches against `docs/REGISTRY.yaml`, per `docs/guides/ticket_tagging.md`)

**Inputs:** Ticket ID. Reads `tickets/inprogress/{ticket_id}.md`.

**Outputs:**
- `staging_artifacts/{ticket_id}/investigation.md` — current behavior at `file:line`, mechanics constraints, parity ledger overlap, risks, anti-drift hazards
- `staging_artifacts/{ticket_id}/test_plan.md` — regression surface, new tests required per AC, scoped pytest commands

**When to invoke directly:** When an existing ticket needs a fresh investigation before planning (e.g., investigation.md is stale after scope change).

---

### `concern-investigator`

**Role:** Investigates a pre-ticket proposal concern and returns structured JSON findings for `create-tickets.js`'s Structure phase — distinct from `investigator`, which operates on an existing ticket and writes markdown files. Read-only: its `tools:` frontmatter field omits `Edit`, `Write`, and `NotebookEdit`, since this phase never needs to change repo state.

**What it does:**
- Works through the same mandatory context-scan ordering as `investigator`/`CLAUDE.md`'s Context Scan rule: semantic `search_docs` retrieval → graphify query → `docs/REGISTRY.yaml` (layer + tag match) → `tickets/working_log.csv` cross-reference → code file reads → test discovery → AC-signal derivation → tier assessment
- Never writes files to disk — returns JSON only

**Inputs:** A concern object (`id`, `title`, `description`, `domain_area`, `type_hint`, `priority_hint`, `raw_excerpts`) and a derived `registryLayers` list — supplied per-call in the invocation prompt. No ticket file is required or read.

**Outputs:** JSON matching `INVESTIGATION_SCHEMA` (`concern_id`, `files_found`, `constraints`, `existing_tests`, `related_tickets`, `ac_signals`, `risks`, `is_duplicate`, `duplicate_of`, `tier_recommendation`, `summary`) — never writes files to disk.

**When to invoke directly:** Available for ad hoc "investigate this idea before I write a ticket" use, same as `investigator`/`world-debugger`/`simulation-analyst` are documented as directly invokable. No invocation-context restriction — the tool-scoping (not caller identity) is what makes this agent safe to expose broadly.

Use `investigator` when a ticket already exists and you need file-based artifacts; use `concern-investigator` when you have a pre-ticket idea and want structured findings back without writing anything.

---

### `planner`

**Role:** Converts investigation findings into an ordered, implementer-ready plan.

**What it does:**
- Reads the ticket + investigation.md + test_plan.md
- Produces ordered steps, each naming specific files and changes, with scope guards and dependency map
- Maps every step to one or more acceptance criteria
- Flags unresolved questions rather than deciding them unilaterally

**Inputs:** Ticket ID + investigation artifacts already written.

**Outputs:** `staging_artifacts/{ticket_id}/plan.md`

**When to invoke directly:** When the investigation is done but the plan needs revision without re-investigating.

**Critical rule:** If plan.md contains "Unresolved Questions", the `implement-ticket` workflow pauses for human input before proceeding to implementation.

---

### `architecture-reviewer`

**Role:** Validates a plan against architecture rules before any code is written.

**Step 0 — static pre-check (post-Implement only):** The original pre-Implement call (below) has
no code to parse — `plan.md` is prose, not Python source. A **second, post-Implement** call to this
same agent, in the `Architecture-Verify` phase, runs
`tools/gate_checks/architecture_reviewer_static.py::run_architecture_checks(files_changed)` (via
`bash()`, before the agent call) and injects its `condition`/`status`/`evidence` JSON output into
the prompt. Three checks: `check_durable_state_mutation` (AST scan for `object.__setattr__`
bypasses outside a field-name allowlist, nested mutable-container mutation by field-name heuristic,
and direct nested attribute assignment), `check_api_boundary_exposure` (AST scan of `src/api/`
top-level route functions for a raw-domain-model return annotation), and
`check_reason_metadata_smuggling` (regex scan for a delimiter-packed `reason`/`metadata` value later
unpacked via a matching `.split(...)` in the same file — this one has zero confirmed historical
incidents in this repo; disclosed as speculative/rule-derived, not evidence-derived). In this second
call, the agent judges only the flagged item(s) against the real diff — not the whole plan again —
and self-reports provenance in a `verified_by` field.

**What it checks:**
- Durable state rule (no direct mutation, no meaning in `reason`/`metadata` strings)
- API boundary (no raw domain models, shaped read models only)
- Systems/registries (shared behavior through registries, not local hacks)
- Strategy/tactics boundary
- Mechanics Bible compliance (reads relevant `docs/mechanics/` chapters)
- Engine contract compliance (`docs/engine/authoritative_pipeline.md` for pipeline changes)
- Parity ledger impact — flags P0 entries that will be affected

**Inputs:** `staging_artifacts/{ticket_id}/plan.md` + ticket (pre-Implement call); `files_changed` +
static-check JSON (post-Implement `Architecture-Verify` call).

**Outputs:** `APPROVED` / `NEEDS_CHANGES` / `BLOCKED` verdict with violation list and parity entries
affected (pre-Implement call); same vocabulary plus a `verified_by` field (post-Implement
`Architecture-Verify` call).

**Gate behavior:** The `implement-ticket` workflow halts on `NEEDS_CHANGES` or `BLOCKED` from either
call. Pre-Implement: fix the plan, then re-run with `ticket_id`. Post-Implement
(`Architecture-Verify`): fix the flagged code, then re-run with `ticket_id`.

---

### `done-checker`

**Role:** Verifies all 13 Definition-of-Done conditions before a ticket can close.

**Step 0 — static pre-check:** Before judging conditions 3, 4, 7, 10, and 12 by hand, the agent runs
`tools/gate_checks/done_checker_static.py`'s `run_static_precheck(ticket_id, tier, start_ts)` (via
`python3 -c "..."`) and cites its PASS/FAIL/NA + evidence output verbatim for those conditions
instead of re-deriving them by hand. The agent self-reports which conditions came from the script
vs. pure judgment in a `verified_by` field.

As of `TCK-20260718-TIER-PRIORITY-CANONICAL-ENUM`, the static pre-check aggregates **6** checks,
not 5: `staging_artifacts_complete` (4), `data_runs_clean` (10), `ticket_location` (3),
`working_log_no_row_yet` (7), `frontmatter_valid` (12), and a 6th, `ticket_field_values_valid`
(canonical `## Tier`/`## Priority` body-field values), which does not yet have a dedicated
numbered DoD condition of its own — deliberately left undecided by that ticket's own Implementation
Notes ("left for a future ticket if a dedicated DoD-list entry for this check is ever wanted").

**The 13 conditions:**
1. Implementation matches accepted scope
2. Architecture constraints respected
3. Ticket has required metadata, in `tickets/inprogress/` — script-checked
4. Staging artifacts complete (`plan.md`, `investigation.md`, `test_plan.md`) — script-checked
5. Tests run and updated
6. Docs updated if behavior changed
7. `tickets/working_log.csv` entry not yet present (pre-Finalize) — script-checked
8. No undocumented decisions
9. Repo state consistent
10. `data/runs/` and `reports/release_proof/` cleaned — script-checked
11. No material gaps unstated
12. Frontmatter valid in ticket and staging artifacts — script-checked
13. Agent monitoring records (pre-marked PASS — written by workflow after READY_TO_CLOSE)

**Inputs:** Ticket ID. Reads the ticket, staging artifacts, test results, and parity ledger.

**Outputs:** `READY_TO_CLOSE` or `BLOCKED` with a per-condition table showing evidence, plus a
`verified_by` field listing which conditions came from the static script vs. pure judgment.

**When to invoke directly:** Before manually closing a ticket that was implemented outside the workflow.

---

## Implementation Agents

### `implementer`

**Role:** Writes the code changes described in `plan.md`.

**Constraints pre-loaded:**
- Decision logic reads state only — never mutates durable state directly
- All durable changes through typed records and the authoritative application path
- No raw domain models from APIs
- No unnecessary abstractions, no half-finished implementations
- No comments unless WHY is non-obvious

**Inputs:** Approved `staging_artifacts/{ticket_id}/plan.md` + investigation.md.

**Outputs:**
- Code changes in `src/`
- Implementation Notes written back to the ticket's `Implementation Notes` section
- Deviations from the plan written to `staging_artifacts/{ticket_id}/plan.md`
- Structured report: files changed, `behavior_changed` boolean, parity subsystems affected, implementation summary

**When to invoke directly:** When re-running a single implementation step after a plan correction (use the workflow's resume feature instead where possible).

---

### `test-scoper`

**Role:** Maps changed files to relevant tests, builds a scoped `pytest` command, executes it, and reports results.

**What it does:**
1. Maps each changed `src/X/` file to `tests/unit/X/`
2. Expands to transitive test dependents for changes in `src/core/`, `src/systems/`, `src/engine/`
3. Checks `test_plan.md` for new tests that should have been added
4. Builds and executes the scoped `pytest` command via Bash
5. Reports pass count, fail count, failing test names, and coverage gaps

**Inputs:** List of changed source files. Reads `staging_artifacts/{ticket_id}/test_plan.md`.

**Outputs:** Pytest command used, pass/fail counts, failing test names, coverage gaps.

**Rule:** Never outputs `pytest tests/` — always scopes to specific paths.

---

## Quality and Compliance Agents

### `parity-updater`

**Role:** Keeps `docs/parity_ledger/` accurate after a behavior change.

**Step 0 — static pre-check:** The orchestrator runs
`tools/gate_checks/parity_updater_static.py::expected_subsystems_for_files` (via `bash()`) *before*
this agent is invoked, injecting the resulting `src/` file → expected ledger file(s) todo-list into
the prompt's preamble (`NA` = no existing `v2_evidence` citation found). The same `bash()` step also
runs `::next_available_id` for every shard `expected_subsystems_for_files` named as a candidate,
injecting a `Next available ID per candidate shard` hint line (`max-numeric-suffix + 1`, never
`entry-count + 1` — shards have gaps). After this agent's turn ends, the orchestrator runs
`::cross_reference_touched` (via `bash()`) against the actual `git status` diff of
`docs/parity_ledger/` and records any discrepancy in `agent-monitoring/events.jsonl` — visibility
only, not a blocking gate. The agent self-reports which of its findings were informed by the
injected context vs. independent judgment in a `verified_by` field.

The agent can also call `::search_existing_entries` itself via Bash — a case-insensitive substring
search (not fuzzy/semantic) across every entry's `text`/`v2_evidence` fields, scoped to one shard or
all of them — to check whether an entry already exists for the concern at hand before constructing a
new one. Unlike the two functions above, this is not auto-injected (there is no automatic query
string to feed it); it's a tool the agent invokes on demand.

**Ledger files it manages:**

| File | Subsystem |
|---|---|
| `substrate.yaml` | World generation, determinism |
| `combat_movement.yaml` | Combat, movement |
| `strategic_cognition.yaml` | AI goal hierarchy |
| `town_resource.yaml` | Resources, harvesting, crafting |
| `progression.yaml` | XP, rewards, skills |
| `social_narrative.yaml` | Reputation, relationships |
| `world_dynamics.yaml` | Ecology, calamities |
| `infrastructure.yaml` | Replay, telemetry, observability |

**Entry update rules:**
- Behavior matches Mechanics Bible → `status: verified`, update `v2_evidence` and `test_path`
- Intentional divergence → `status: divergent`, set `divergence_note`, add to `docs/guidelines/intentional_divergences.md`
- New behavior with no entry → add with next available ID
- P0 entries must have a non-null `test_path` pointing to a passing test

**When to invoke directly:** After any manual code change that affects simulation behavior.

---

### `doc-updater`

**Role:** Applies `docs/` updates for a behavior change, outside `parity_ledger/`, `audits/`,
`archive/`, `scenarios/`, `entity/`.

**Step 0 — orchestrator-injected context:** Standard/epic tier: the orchestrator injects
`investigation.md`'s `## Docs Requiring Update` bullets (flagged paths) into the prompt preamble,
and the agent reads `investigation.md` itself for the full reason text alongside each. Hotfix tier:
no `investigation.md` exists, so the agent reads `${ticketInfo.ticket_path}`'s own `## Scope`
section directly, plus the real `files_changed` diff, and uses its own judgment for whether a
`docs/` update is warranted.

**Per-family rules it applies:**
- `docs/mechanics/` — bit-identical parity with source, cite chapter + section
- `docs/engine/` — cite the specific contract ID (`project_lawbook_m10.md` is the index)
- `docs/guides/*.md` — match the file's existing terse per-row table convention
- `docs/guidelines/intentional_divergences.md` — rationale class + description + `Verification:` test path, all three required
- `docs/plans/` — update in place if still live, never move to `docs/plans/archive/`
- `docs/audits/` — never edited; cite-only, dated point-in-time snapshots
- Everything else (17 general folders) — read the target doc's frontmatter plus 2-3 sibling docs first, match existing structure; `status: authoritative` docs get full Mechanics-Bible-level rigor regardless of folder

**When to invoke directly:** After any manual doc-relevant change — mirrors `parity-updater`'s own guidance.

---

### `mechanics-auditor`

**Role:** Compares a Mechanics Bible chapter to the source implementation and reports divergences.

**Mechanics Bible chapters:**

| Ch | File | Covers |
|---|---|---|
| 01 | `01_entity_anatomy.md` | Attributes, derived stats, XP |
| 02 | `02_combat_laws.md` | Damage formula, modifiers, durability |
| 03 | `03_economic_laws.md` | Conservation, harvesting, trade, crafting |
| 04 | `04_strategic_cognition.md` | Goals, interruption, perception |
| 05 | `05_world_evolution.md` | Tick/time, trauma, ecology |
| 06 | `06_worldbuilding_foundation.md` | Topology, sovereignty, distribution |

**Output classification:**
- `PARITY` — implementation matches documented formula
- `DIVERGENT` — implementation differs (describes what's different)
- `MISSING` — law is documented but has no implementation
- `UNDOCUMENTED` — implementation exists but has no corresponding law

**Step 0 — static pre-check:** Before finalizing a `Status`/`Finding` for any entry, the agent runs
`tools/gate_checks/mechanics_auditor_static.py`'s `verify_entry_test_path(entry_id)` (via
`python3 -c "..."`) and cites its PASS/FAIL + evidence verbatim. This check only confirms whether the
entry's cited `test_path` exists and passes — it never overrides the agent's own bit-identical
code-vs-formula comparison. A static `FAIL` (commonly: no `test_path` at all — 82% of `verified`
entries have none) does not downgrade a `PARITY` row to `DIVERGENT`/`MISSING`; it is appended as a
caveat in `Finding` instead, since a missing test citation is a verification gap, not evidence of code
divergence. Unlike `done-checker`/`parity-updater`'s Step 0 (orchestrator-run and independently
verified), this Step 0 has no orchestrator-side enforcement — `mechanics-auditor` has no pipeline call
site — so compliance depends entirely on the agent actually running the script and citing it honestly.
The agent self-reports in `verified_by` whether each row's `Status` was corroborated by the static check
or came from independent judgment alone.

A separate, on-demand post-hoc audit closes part of this gap after the fact:
`tools/gate_checks/mechanics_auditor_static.py`'s `audit_verified_by_claims(rows, ...)` takes a
`mechanics-auditor` session's own output rows and independently recomputes each `verified`-status
row's Step 0 result, flagging a row whose `verified_by` omits the static-check tag entirely ("Step 0
skipped") or whose claim contradicts a fresh recompute without a disclosed caveat ("falsely cited").
It returns `honesty_status: "PASS"|"FAIL"` per row — a field distinct from, and never overriding,
the agent's own `PARITY`/`DIVERGENT`/`MISSING`/`UNDOCUMENTED` classification. **Disclosed
limitation:** nothing currently calls this function automatically — it requires a human reviewer or
a future ticket to supply a session's output rows explicitly. Closing that invocation gap would
require a durable-capture mechanism for ad hoc agent output that does not exist yet (see
`TCK-20260710-MECHANICS-AUDITOR-ENFORCEMENT`'s plan.md, Decision 2).

A convenience wrapper, `candidate_ledger_files_for_module`, reuses `parity-updater`'s
`expected_subsystems_for_files` to locate candidate ledger files when auditing a whole chapter/module
rather than a single named entry.

**When to invoke directly:** Before modifying a simulation subsystem, or after a `parity-updater` run to verify the ledger is consistent with the actual implementation.

---

### `security-reviewer`

**Role:** Reviews implemented code changes for security vulnerabilities before Verify.

**Trigger:** Conditional — the `implement-ticket` workflow's Security-Review phase fires only when the
ticket's `tags` include `security` (ground truth), or its derived `suggested_skills` include
`/security-review` (secondary). For a ticket matching neither, this phase does not run — zero added
latency, agent calls, or events.

**Registry lookup:** Before reviewing, reads `docs/REGISTRY.yaml` to find active docs matching the
ticket's layer (`type: doc`, `status: active`/`authoritative`, `layer: <ticket_layer>`) rather than
scanning `docs/` by listing. Falls back to the checklist below directly if the registry doesn't exist.

**What it checks:**
1. Injection — command/SQL/template injection in new string-building code
2. Unsafe deserialization — `pickle`, `yaml.load` without `SafeLoader`, `eval`/`exec` on external input
3. Path traversal — unvalidated path joins or user-controlled file paths
4. Subprocess/command injection — `subprocess`/`os.system`/`shell=True` with unsanitized input
5. Secrets-in-code — hardcoded credentials, API keys, tokens committed to source
6. Raw-domain-model API exposure — overlaps `architecture-reviewer`'s API-boundary rule (no raw domain
   models exposed from APIs, shaped read models only); cross-references that rule by name rather than
   restating it

**Inputs:** Ticket + its changed files/diff.

**Outputs:** `APPROVED` / `NEEDS_CHANGES` / `BLOCKED` verdict, per-violation findings (which of the six
categories, what the code does, the fix), and a `summary` field (one sentence ≤200 chars) for the agent
monitoring event record.

**Gate behavior:** The `implement-ticket` workflow halts with `SECURITY_BLOCKED` on `NEEDS_CHANGES` or
`BLOCKED` and does not proceed to Verify/Finalize. Fix the flagged code, then re-run with `ticket_id`.

**When to invoke directly:** After any manual change touching auth, secrets, subprocess calls,
deserialization, or file-path handling, even outside the automated workflow.

---

### `world-debugger`

**Role:** Traces world assembly and content resolution failures through the authoritative pipeline.

**Scope:** Failures in `src/worldassembly/`, `src/worldbuilding/`, `src/worldmodules/`, `src/worldgeneration/`, `src/content/`, `src/core/registries.py`.

**Common failure patterns it diagnoses:**
- Missing content reference (entity references unregistered content)
- Schema validation failure (input doesn't match pipeline stage schema)
- Resolver conflict (multiple content items compete for same slot)
- Registry inconsistency (entity state diverges from authoritative state)
- Normalization failure (`src/worldmodules/normalizer.py`)
- Path resolution failure (`src/content/paths.py`)

**Output:** Root cause at `file:line`, upstream state, pipeline stage that failed, fix recommendation, regression risk.

**When to invoke directly:** Any time world assembly, content loading, or resolver fails with an unclear error.

---

## Analysis Agents

### `simulation-analyst`

**Role:** Lightweight single-pass analysis of a completed simulation run against Mechanics Bible ranges.

**Scope:** This is the fast check — anomaly spotting, severity classification, law reference. For deep multi-agent investigation with hypothesis generation and enhancement proposals, use the `investigate-simulation-result` workflow.

**Analysis dimensions:**
- Entity population arc (population crash/explosion detection)
- Combat formula spot-checks against Ch02
- Economic conservation check against Ch03
- Goal distribution and interruption patterns against Ch04
- Tick-to-day and regional trauma against Ch05

**Anomaly severity:** `CRITICAL` (law violated) / `HIGH` (severe imbalance) / `MEDIUM` (trending unstable) / `LOW` (minor deviation).

**Escalation rule:** If CRITICAL anomalies are found, recommend running the `investigate-simulation-result` workflow for full diagnosis.

---

### `world-render-reviewer`

**Role:** Tiered visual/geometric quality review of a rendered world state — Tier 0 pure-data
scoring by default, escalating to the annotated/gridlined render only when Tier 0/1 flags an
anomaly. Cites tile coordinates from the annotated image, never the plain render.

**Scope:** A pure geometry/statistics review — connectivity, terrain shape, entity density, and
the composite grade produced by `src/rendering/review_pipeline.py::run_tier0_tier1_pipeline`. No
relationship to the Mechanics Bible (`docs/mechanics/`); none of its findings cite a Mechanics
Bible chapter, because none apply to this domain. For gameplay-balance or mechanics-law review of
a completed simulation run, use `simulation-analyst` instead — a different job over different
data.

**What it does:**
- Always reads the `Tier1Digest` JSON first (`review_pipeline.py::digest_to_json`) — connectivity
  (`connectivity_component_count`/`connectivity_percent_reachable`), terrain shape
  (`flagged_shape_components`), entity density (`entity_count`), and the composite `grade`/
  `combined_score`
- Reads the annotated/gridlined render at `Tier1Digest.annotated_render_path` only when the
  digest's `escalate` field is `True` (set by `should_escalate`: any failed hard rule, or
  `grade` in `D`/`F`) — `plain_render_path` exists for unrelated human-requested general health
  checks only and is never substituted as an escalation image
- Cites tile-coordinate evidence only from the annotated image when one was read, never invented
  from the digest alone

**Inputs:** A `Tier1Digest` produced by `run_tier0_tier1_pipeline`.

**Outputs:** One-line summary, digest summary (grade/combined score/escalate flag), findings
table (dimension | severity | description | evidence | related digest field), a
Tier-0-verifiable-vs-annotated-image-required breakdown, and recommended next steps. Severity:
`CRITICAL`/`HIGH`/`MEDIUM`/`LOW`.

**When to invoke directly:** After `run_tier0_tier1_pipeline` produces a `Tier1Digest` for a
rendered world state that needs a spatial/geometric quality read. Report-only — never a blocking
gate, matching this ticket's own Out of Scope.

---

## Agent Summary Table

| Agent | Phase in lifecycle | Primary output |
|---|---|---|
| `spec-document-reviewer` | Brainstorming (pre-ticket) | Approved / Issues Found verdict |
| `ticket-scoper` | Pre-work | `tickets/inprogress/{id}.md` |
| `investigator` | Pre-work | `investigation.md`, `test_plan.md` |
| `concern-investigator` | Pre-work (pre-ticket) | Structured JSON (files_found, ac_signals, ...) |
| `planner` | Pre-work | `plan.md` |
| `architecture-reviewer` | Gate before implementation | APPROVED / NEEDS_CHANGES verdict |
| `implementer` | Implementation | Code changes + implementation notes |
| `test-scoper` | Post-implementation | Test results (pass/fail) |
| `parity-updater` | Post-implementation | Updated `docs/parity_ledger/*.yaml` |
| `doc-updater` | Post-implementation | Updated `docs/` files (`docs_updated`/`docs_skipped`) |
| `done-checker` | Closure gate | READY_TO_CLOSE / BLOCKED verdict |
| `mechanics-auditor` | Quality / compliance | PARITY/DIVERGENT/MISSING table |
| `security-reviewer` | Conditional gate (security-tagged tickets only) | APPROVED/NEEDS_CHANGES/BLOCKED verdict |
| `world-debugger` | Debugging | Root cause + fix recommendation |
| `simulation-analyst` | Analysis | Anomaly table + severity |
| `world-render-reviewer` | Analysis | Findings table + grade/escalate summary |
