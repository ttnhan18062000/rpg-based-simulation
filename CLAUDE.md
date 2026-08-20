# Project Instructions

## Priority Order

1. Safety and user instruction
2. Repository architecture integrity
3. Traceability and workflow discipline
4. Tests and verification
5. Local convenience

---

## Hard Rules

* Do not act without validating context.
* Do not guess when uncertainty affects behavior or architecture.
* Do not ask questions already answered by repo patterns.
* Do not create hidden or implicit durable behavior.
* Do not mutate durable state outside authoritative flows.
* Do not break determinism.
* Do not expose raw domain models from APIs.
* Do not leave changes untested or untraceable.
* Every implement-ticket workflow run (including hotfix) must record a run entry and at least one event entry to `agent-monitoring/`. Monitoring write failure must never fail the workflow.
* **Do not run grep, find, raw file reads, or spawn Explore agents for investigation before first calling `search_docs` (MCP) and `graphify query` for the topic.** These tools traverse inferred relationships and doc registries that raw grep cannot. Grep and file reads are permitted only as follow-up after the semantic search results are in hand.
* **Never edit an artifact to make an automated gate/check pass instead of fixing the underlying substance.** A gate's blocking result (`NEEDS_CHANGES`, `BLOCKED`, `NEEDS_HUMAN_INPUT`, a failing test, a failing validator, etc.) is correct information to report, not an obstacle to route around — stop and report it truthfully, even if it looks trivially resolvable. This applies at every level of agent delegation, including any sub-agent you spawn to carry out a step.
* **If you are a dispatched sub-agent (not the top-level orchestrator), never end your turn while your own `run_in_background` command is still running.** You are not auto-resumed the way the top-level orchestrator is — an unfinished background command left running when your turn ends stalls the pipeline until it is manually detected and you are re-prompted, wasting a full round-trip. Either run the command in the foreground, or poll for its own completion within the same turn before returning control. (Confirmed as a repeated real failure mode on 2026-08-17/18: 3 independent `general-purpose` sub-agent dispatches spawned their own background tasks, then stopped to "wait for a notification" they had no mechanism to receive, requiring manual `SendMessage` resumption each time. `implementer.md`/`test-scoper.md` already carried this warning for their own roles; this bullet generalizes it to every dispatched agent, since `general-purpose` and most other project agent roles have no equivalent project-level file to carry it.)

---

## Context Scan (Mandatory)

Before any implementation or investigation (ticket creation, scoping, planning), run these tools **in this order**:

1. `mcp__knowledge-search__search_docs` — semantic search over docs, tickets, and investigations. Always call this first.
2. `graphify query "<topic>"` — code structure, relationships, and inferred edges.
3. `python3 tools/knowledge_search.py query "<q>" --top-k 5` — fallback if MCP unavailable.
4. Then check: `tickets/`, `docs/`, `stored_artifacts/`, relevant code and tests.

Raw grep and direct file reads are **follow-up steps only** — they narrow down what the semantic tools already surfaced. Never start with grep.

Detect and stop on duplicate work, conflicting requirements, or architectural mismatch.

---

## Clarification Rule

Ask only if it changes outcomes:

* multiple valid implementations
* unclear acceptance criteria
* conflict with existing system
* missing critical context

Otherwise, follow existing patterns.

---

## Workflow Rule

### Before Work

- Scan tickets, docs, stored artifacts, relevant code, and tests.
- Identify reuse opportunities and conflicts.
- Create `tickets/inprogress/{ticket_id}.md`.
- **Standard/epic only:** Create `staging_artifacts/{ticket_id}/` with `plan.md`, `investigation.md`, `test_plan.md`.
- **Hotfix:** No staging artifacts required — self-evident intent is captured in the ticket itself.

### Required Artifacts (standard/epic only)

At minimum: `plan.md`, `investigation.md`, `test_plan.md`.

Ticket must include: title, summary, scope, out of scope, acceptance criteria, related docs/tickets/artifacts, assumptions/open questions, current status.

### During Work

- Keep ticket and artifacts aligned with actual work.
- Update plan when implementation changes.
- Update investigation when new findings appear.
- Validate continuously against repo patterns and architecture.

### After Work

- Finish ticket, move to `tickets/done/`.
- If the ticket originated in a `tickets/todos/{folder}/` subfolder:
  - Delete the source file from the subfolder (`rm tickets/todos/{folder}/{ticket_id}.md`).
  - When **all** tickets in the folder are done, move the **entire folder** to `tickets/done/{folder}/` — this preserves `SEQUENCE.md` and any folder-level metadata (`mv tickets/todos/{folder}/ tickets/done/{folder}/`). Never leave a completed folder's skeleton in `tickets/todos/`.
- Append to the **bottom** of `tickets/working_log.csv` (never insert after the header).
- **Standard/epic only:** Move staging artifacts to `stored_artifacts/`.
- Update related docs.
- Clean up: `rm -rf data/runs/* reports/release_proof/*`.
- Verify no leftover staging/temp files remain.
- If any files under `docs/` were created or modified: run `make knowledge-index-update` to keep the agent context search index current.
- `docs/REGISTRY.yaml` is regenerated unconditionally as part of Finalize's post-migration self-check (all tiers, including hotfix) — no manual `make docs-registry` step is needed. Always stage the regenerated file (`git add docs/REGISTRY.yaml`) as part of ticket close, alongside `agent-monitoring/`.
- **Always stage `agent-monitoring/` (including `tools.jsonl`) in every commit** — the monitoring tools auto-update `tools.jsonl` on every run; never leave it as an unstaged modification.

### Commit Convention

Reference the ticket ID in every commit for this ticket's work:

```
TCK-YYYYMMDD-SHORT-SCOPE: Brief description of change
```

### Tier Routing

| Tier | Pipeline | Use when |
|---|---|---|
| `hotfix` | Scope → Implement → Test → Parity → Verify → Finalize | Bug fix or minimal targeted change with self-evident intent |
| `standard` | Full 10-phase pipeline (+1 conditional: Security-Review) | Any new feature, refactor, or substantive repair |
| `epic` | Scope only — tracks child tickets | Large multi-ticket initiative; no direct implementation |

---

## Ticket Format

**File name:** `TCK-YYYYMMDD-SHORT-SCOPE.md` (uppercase, hyphen-separated)

**Location:** `tickets/inprogress/{ticket_id}.md` → `tickets/done/{ticket_id}.md`

**Required sections (in order):**

```
---
status: active
layer: <engine|combat|economy|strategy|world|core|observability|performance|testing|simulation|guidelines|ai|architecture|misc>
authority: P1
audience: agent
ticket_id: TCK-YYYYMMDD-SHORT-SCOPE
phase: open
date: YYYY-MM-DD
tags: []
---

# TCK-YYYYMMDD-SHORT-SCOPE

## Title
## Status         (OPEN | INPROGRESS | BLOCKED | DONE)
## Tier           (hotfix | standard | epic)
## Type           (bug | feature | refactor | chore | repair)
## Priority       (P0 | P1 | P2 | P3)
## Request Summary
## Scope
## Out of Scope
## Acceptance Criteria
## Related Tickets
## Related Docs
## Related Stored Artifacts
## Related Code Areas
## Assumptions / Open Questions
## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
```

Frontmatter block is required as the first element. Fill `layer` and `tags` based on scope; leave `tags: []` if uncertain.

**`layer` is a hard allowlist**, not free text, and stays single-valued (never a list): every ticket/doc's `layer:` must already be registered in `registries/layer_registry.jsonl`, or `validate_frontmatter.py` rejects it. Before assigning `layer`, check `python3 tools/layer_registry.py list` — use an existing entry if it genuinely fits the ticket's subsystem; register a new one only if it doesn't, with `python3 tools/layer_registry.py add <layer> --note "why this layer exists"` (append-only: it cannot be renamed or removed once added). Use `misc` only if no real layer fits — never force-fit into `misc` when a genuine category is just missing from the registry; register the real one instead.

**Tags are a hard allowlist**, not free text: every tag on a ticket/artifact created on or after 2026-07-04 must already be registered in `registries/tag_registry.jsonl`, or `validate_frontmatter.py` rejects it. Before using a genuinely new tag, check `python3 tools/tag_registry.py list` — if it isn't there, register it first with `python3 tools/tag_registry.py add <tag> --category <subsystem-topic|process-skill-signal|quality-attribute|meta-process> --note "why"` (append-only: it cannot be renamed or removed once added). See `docs/guidelines/tag_taxonomy.md` for the category definitions and `docs/guides/ticket_tagging.md` for a practical walkthrough.

`layer` and `tags` are both registry-backed and append-only, but differ in shape: `layer` is single-value and uncategorized (it *is* the subsystem-topic dimension itself), `tags` is multi-value and split into 4 taxonomy categories (Subsystem/Topic, Process/Skill-signal, Phase/Milestone, Quality-attribute — see `docs/guidelines/tag_taxonomy.md`). `## Tier` (`hotfix | standard | epic`) and `## Status` (`OPEN | INPROGRESS | BLOCKED | DONE`, plus `EPIC_SCOPED` for epic-tier tickets) are ticket-*body* fields, not frontmatter — validated by a separate mechanism, `tools/ticket_field_values.py`, since body sections are parsed differently from frontmatter (see that module's docstring). `## Priority` is body-field too, values `P0 | P1 | P2 | P3`.

---

## Testing Rule

- Run relevant existing tests before claiming completion. Do not run the entire suite (`pytest tests/`) — scope to the domain under modification or use `pytest -m "not slow"`.
- Add or update tests whenever behavior changes.
- Prefer deterministic, isolated, readable tests.
- Test meaningful behavior, not superficial coverage.

**Required coverage:** normal flow, edge cases, failure modes, regression-prone paths.

**Architecture tests:** verify read-only logic did not mutate live state, authoritative application path was used, typed records serialize/deserialize correctly.

---

## Architecture Rule

### Core Boundaries

- Decision logic reads state. It does not authoritatively mutate durable state.
- Durable changes must be represented through typed records/updates.
- Authoritative application is the only place durable state should be committed.
- Shared world behavior should go through systems/registries, not scattered local hacks.
- API/routes present shaped read models through presenters/schemas, not raw domain objects.

### Durable State Rule

If something survives beyond the current tick or current function call, it must have a typed model, a stable location in entity/world/registry state, a defined lifecycle, inspection/debug visibility, and tests.

Do not store durable meaning in `reason` strings, free-form `metadata`, comments, or temporary local variables.

### Strategic/Tactical Rule

- Strategy owns enduring direction. Tactics own immediate execution.
- Do not solve strategic problems by stacking more tactical goal scoring.

### Uncertainty Rule

- Vague leads stay vague until evidence narrows them.
- Do not collapse investigation into exact coordinates too early.

---

## Definition of Done

A task is not done unless all are true:

- Implementation matches accepted scope
- Architecture constraints were respected
- Ticket is updated and moved to `tickets/done/`
- Staging artifacts are complete and migrated to `stored_artifacts/`
- Tests were run and updated
- Docs were updated if behavior changed
- Working log entry was added (`tickets/working_log.csv`)
- No important decision is undocumented
- Repo state is consistent
- Temporary run data cleaned: `data/runs/`, `reports/release_proof/`
- No known material gap is left unstated
- Agent monitoring records written: run entry in `agent-monitoring/runs.jsonl`, at least one event in `agent-monitoring/events.jsonl` _(guaranteed by workflow — not verified by done-checker)_
- Frontmatter valid in the ticket and its staging artifacts (script-checked by `done-checker`'s `frontmatter_valid` condition)

---

## Authoritative Mechanics Rule

The **Mechanics Bible** (`docs/mechanics/`) and the **Engine Contracts** (`docs/engine/`) are the definitive sources for simulation laws, formulas, and pipeline behavior.

- **Consistency**: All logic changes MUST be consistent with the laws defined in the Mechanics Bible.
- **Parity**: Documentation and source code must remain in 100% semantic parity. If logic changes, update the corresponding doc AND the parity ledger entry (`docs/parity_ledger/`) in the same session.
- **Reference**: When explaining or implementing mechanics, cite the specific chapter in `docs/mechanics/` or the contract ID in `docs/engine/`.
- **Divergence**: Any intentional behavior change that differs from the Mechanics Bible MUST be recorded in `docs/guidelines/intentional_divergences.md` with a rationale class and verification path.
- **Precedence**: In case of ambiguity between legacy behavior and the V2 Mechanics Bible, the Mechanics Bible takes precedence.

### Mechanics Bible — `docs/mechanics/`

All chapters are Certified Level 1 (Authoritative). Every formula is verified for bit-identical parity with source code.

| Chapter | File | Covers |
|---|---|---|
| 01 | `01_entity_anatomy.md` | Core attributes, derived stats, biological pressures, XP scaling |
| 02 | `02_combat_laws.md` | Damage formula, tactical modifiers, durability decay, victory outcomes |
| 03 | `03_economic_laws.md` | Atomic conservation, harvesting, trade, crafting |
| 04 | `04_strategic_cognition.md` | Goal hierarchy, interruption resistance, knowledge management, perception |
| 05 | `05_world_evolution.md` | Tick-to-day time, regional trauma, ecology, calamities |
| 06 | `06_worldbuilding_foundation.md` | Declarative topology, sovereignty, distribution, integrity validation |

Also: `content_usage_matrix.md` (content resolution rules), `regional_sovereignty.md` (region boundaries).

### Engine Contracts — `docs/engine/`

The master index is `project_lawbook_m10.md`. Key contracts:

| File | Covers |
|---|---|
| `kernel.md` | 7-phase deterministic loop (Init → Scheduling → Collection → Resolution → Cleanup → Advancement → Persistence) |
| `authoritative_pipeline.md` | 37-phase refinement sequence for world mutation |
| `authoritative_mutation_pipeline_contract.md` | Mutation rules and apply-path law |
| `governance_logic.md` | Governance and eligibility rules |
| `performance_contract.md` | Hardware classes (A/B/C) and scaling limits |
| `known_limitations.md` | Current scope boundaries |

### Core State — `docs/core/`

| File | Covers |
|---|---|
| `state.md` | Immutability law, authoritative vs non-authoritative state partitioning |
| `entities.md` | Entity lifecycle and identity |
| `attributes_and_classes.md` | Attribute definitions and class rules |

### Parity Ledger — `docs/parity_ledger/`

Machine-readable parity tracking. One YAML file per subsystem, schema in `schema.json`.

Each entry has: `id`, `text`, `status` (`verified` / `divergent` / `missing` / `unsupported` / `legacy_verified`), `priority` (`P0`/`P1`/`P2`), `v2_evidence`, `test_path`, `divergence_note`.

**When a behavior changes:** find the relevant parity ledger entry and update `status` and `v2_evidence`. If no entry exists, add one. `P0` entries require a passing `test_path`.

| File | Subsystem |
|---|---|
| `substrate.yaml` | World generation, authoritative objects, determinism |
| `combat_movement.yaml` | Combat resolution, movement, legality |
| `strategic_cognition.yaml` | AI goal hierarchy, leads, attention bounds |
| `town_resource.yaml` | Resource nodes, harvesting, crafting, economy |
| `progression.yaml` | XP, rewards, skill advancement |
| `social_narrative.yaml` | Reputation, relationships, social events |
| `world_dynamics.yaml` | World evolution, ecology, calamities |
| `infrastructure.yaml` | Replay, telemetry, observability, workers |

### Intentional Divergences — `docs/guidelines/intentional_divergences.md`

The canonical record of V2 behavior shifts from legacy. Any new divergence must be added here with a rationale class (`Hardened` / `Enforced` / `Unified` / `Stabilized` / `Bounded` / `Bug Fix` / `Intentional Gameplay Change`) and a `Verification` test path.

### Other Active Doc Areas

- `docs/architecture/` — ADR-shaped design docs (`simulation_watchdog.md`, `performance_optimization.md`, world assembly, world repository layout)
- `docs/combat/` — Combat rulebooks (`combat_movement_overhaul_spec.md`, `observability_rulebook.md`, `rollout_hardening_rulebook.md`)
- `docs/strategy/` — Bounded cognition contracts and test matrices
- `docs/guidelines/design_patterns.md` — Coding and design conventions
- `docs/compliance/checklist.md` + `gap_analysis.md` — Compliance tracking
- `docs/testing/test_taxonomy.md` — Test classification rules

---

## Proactive Tool Use

Some tools should be invoked automatically based on the task — the user does not need to mention them.

### Always auto-invoke (no user prompt required)

| Trigger | Action |
|---|---|
| "how does X work?" or explaining an unfamiliar module | Read `graphify-out/GRAPH_REPORT.md`, then `graphify explain "<X>"` |
| "how does X relate to Y?" or cross-module question | `graphify path "<X>" "<Y>"` |
| "where is X defined/used?" | `graphify query "<X>"` |
| Searching across more than 3 files | Spawn `Explore` agent instead of sequential Bash greps |
| Starting implementation on an unfamiliar module | Read `GRAPH_REPORT.md` for community structure before touching code |
| `docs/REGISTRY.yaml` exists + user asks about prior work or related docs | Query registry by `related_code_areas` or `layer` — do not scan raw directories |
| **Any investigation** (ticket creation, scoping, implementation planning, answering "how does X work") | **Step 1 (required)**: `mcp__knowledge-search__search_docs` with `query` = the topic. **Step 2 (required)**: `graphify query "<topic>"`. **Step 3 (fallback only)**: `python3 tools/knowledge_search.py query "<q>" --top-k 5`. Only after these: use grep/read/Explore to verify specific file paths. |
| User asks project-specific mechanics, architecture, or history question | Same as "Any investigation" row above. `search_docs` is always available inside Claude Code sessions registered with `.mcp.json` — never skip it. |
| Editing or investigating `src/api/` | `/api-design-principles` — review shape/boundaries before or after the change |
| Investigating a traceback, test failure, or unexpected runtime error | `/debugging-strategies`; if the failure is specifically in world assembly/content resolution (`src/worldassembly/`, `src/worldbuilding/`, `src/worldmodules/`, `src/content/`, `src/core/registries.py`) use `Agent(subagent_type: "world-debugger")` instead — narrower and more specific for that case |
| Profiling or investigating a slow simulation tick / high-memory world assembly | `/python-performance-optimization` |
| A `git push` the user already authorized triggers CI on an open PR | Poll `gh pr checks <PR#>` to completion; on any failure, pull real logs before concluding root cause — see "CI Failure Triage" below |

### Require explicit user opt-in (never auto-invoke)

| Tool | Why |
|---|---|
| `Workflow` (`implement-ticket`, `investigate-simulation-result`, etc.) | Spawns many agents, costs real tokens — user must request the scale |
| `git push`, PR creation, `git checkout`/merge to land a batch | Irreversible or visible to others — the user drives when a batch is ready to push, PR'd, or merged; do not decide this yourself |

The boundary is: **single read/query tools are free to invoke proactively; multi-agent orchestration and anything that changes shared/remote state requires the user to ask**.

### CI Failure Triage (read-only follow-up to an already-authorized push — no separate opt-in needed to check)

Checking CI status and diagnosing a failure is read-only — do it proactively once a push the user already authorized triggers a run, without asking again just to look. What the check finds determines the next step, which is bounded by the table above (a fix still needs its own ticket/pipeline run; pushing that fix rides on the same standing push authorization already granted for the batch, not a fresh ask each time).

1. **Never conclude root cause from the job name or a guess.** Pull real logs (`gh api repos/{owner}/{repo}/actions/jobs/{id}/logs`) for every failing job. Do not assume it's a known local-sandbox quirk (e.g. bare `python3` lacking `pydantic`) without checking the actual CI log first — CI runs in a clean `actions/setup-python` + `pip install -r requirements.txt` environment and does not share the sandbox's gaps.
   - **If log fetching itself fails with a TLS/cert error** (`gh run view --log`, `gh api .../logs`, or a raw `curl` to the redirect target all fail the same way): check `echo | openssl s_client -connect <host>:443 | openssl x509 -noout -subject -issuer`. If the cert's subject/issuer reads as a network filter block page (e.g. `O = Fortinet, CN = Fortiguard SDNS Blocked Page`) rather than the real host, raw log fetching is blocked at the sandbox's network layer for that host (`results-receiver.actions.githubusercontent.com`, `*.blob.core.windows.net`) — not an SSL misconfiguration you can fix. Do not keep retrying variations of the same fetch. Instead: (a) try `gh api repos/{owner}/{repo}/check-runs/{job_id}/annotations` first — sometimes enough on its own; (b) reproduce the failing job locally by running the exact same command from the relevant `.github/workflows/*.yml` job block (e.g. `pytest tests/api tests/cli tests/tools ... -m "not slow and not extra_slow"`) — this is usually more actionable than the raw log anyway. A local repro will include environment-only noise (e.g. live-server tests failing for lack of a running server) that the real CI runner doesn't hit — cross-check any suspicious failure by fetching the job list (`gh run list --workflow=test.yml --json databaseId,conclusion`) for the last known-green run on the base branch and confirming that job passed there, before treating a locally-reproduced failure as real.
2. **Classify each failure before acting:**
   - **A real regression caused by this session's own changes** → file a `hotfix`-tier ticket and run it through the full pipeline (Scope → Implement → Test → Parity → Verify → Finalize), same as any other hotfix.
   - **Matches a category `docs/testing/regression_policy.md` already documents as environment-dependent/flaky** (e.g. live-server subprocess tests) → do not code-fix it; report it as environment noise, let it re-run, and don't touch the test.
   - **A hardcoded test baseline that this session's own legitimate change caused to drift** (matching an existing documented drift pattern, e.g. `tests/tools/test_parity_index_baseline.py`'s `missing_test_path_count`) → same as the first case: a small hotfix ticket updating the baseline with fresh evidence, never a silent edit outside a ticket.
3. **Never edit a test's assertion or a gate's logic just to make CI pass without one of the paths above** — this is the same Gate Integrity rule (`.claude/skills/implement-ticket/SKILL.md`) applied to CI as the outermost gate, not just the local pipeline's own gates.
4. Report the real CI status and the triage conclusion. Don't report a fix as done until CI is confirmed green (or explicitly still-pending, reported as such) — a local test pass is not the same claim as a green CI run.

### PR Lifecycle (once the user has authorized landing a batch)

The steps above cover diagnosing a failure; this covers the surrounding push→PR→merge→sync cadence itself, since it isn't a `Workflow` and has no other home.

1. **Before staging/committing**: always run `git status`/`git log` first — this repo's working directory can be shared by more than one concurrent session (see Hard Rules), so check for in-flight files that belong to another ticket before touching them.
2. **Commit** per ticket, referencing its ID (see Commit Convention). Stage `agent-monitoring/` in every commit, including any small trailing update the monitoring tools auto-write after the main commit — commit that separately rather than leaving it unstaged.
3. **Push** the branch, then **create the PR** (`gh pr create`). PR body: no `Co-Authored-By`/session-link trailer (commit message trailers still keep it) — this was an explicit user preference, opposite of the commit-message convention above.
4. **Monitor CI** per the Triage steps above until every check is green or a failure is triaged and fixed.
5. Report the PR link and CI status back to the user — landing the PR (merge) is their call, not something to do automatically once CI is green.
6. **After the user reports a merge**: `git checkout main && git pull` to sync. If local `main` is already ahead of `origin/main` by a commit you didn't make, that's another concurrent session's unpushed local work — leave it alone, don't push it for them and don't rebase/reset over it.

---

## Graphify Integration

This project has a graphify knowledge graph at `graphify-out/`.

- Before answering architecture or codebase questions, read `graphify-out/GRAPH_REPORT.md` for god nodes and community structure.
- For cross-module questions ("how does X relate to Y"), prefer `graphify query "<question>"`, `graphify path "<A>" "<B>"`, or `graphify explain "<concept>"` over grep — these traverse extracted and inferred edges instead of scanning files.
- After modifying files under `src/` or `tests/`, run `graphify update .` to keep the graph current (AST-only, no API cost). Do not run if changes are only to docs, configurations, or non-code files.
- Use `/graphify` to build or rebuild the full graph.
- `docs/REGISTRY.yaml` is the authoritative flat index of all tagged docs and closed tickets. Query it with `grep` or `python3 -c 'import yaml; ...'` before scanning raw directories. Regeneration on ticket close is automatic (see "After Work" above); run `make docs-registry` manually only to preview an up-to-date registry mid-session, e.g. after adding new docs before any ticket has closed.
