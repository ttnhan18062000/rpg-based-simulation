---
status: active
layer: ai
authority: P1
audience: developer
---

# Skills

Skills are slash commands that trigger focused, session-scoped task patterns. They are defined in `.claude/skills/*/SKILL.md` (project-level) or built into Claude Code (system-level).

**Invocation:** Type `/skill-name` in the prompt. Skills may prompt for additional context before executing.

---

## Skills vs. Workflows — How Invocation Works

**Skills** are the user-facing slash commands. Type `/skill-name args` in the prompt. Claude reads
the skill's `SKILL.md`, which instructs it to read the corresponding `.claude/workflows/*.js` file
directly and translate its phase/agent/bash constructs into tool calls by hand — **there is no
`Workflow` tool in this harness** to invoke instead. Every project workflow-shortcut `SKILL.md`
states this explicitly in its own Action section (e.g. "Do not call the Workflow tool — it is not
available").

**Workflows** (`.claude/workflows/*.js`) are Claude-internal multi-agent scripts. They are **not**
directly slash-commandable on their own — only workflows with a corresponding `.claude/skills/*/
SKILL.md` wrapper (below) are reachable via a slash command at all. `/workflow implement-ticket` is
not a valid command — it will fail with "Unknown command: /workflow". The correct form, for a
workflow that has a skill wrapper, is `/implement-ticket`.

```
You type:                Claude does:
/implement-ticket ...  →  Reads .claude/workflows/implement-ticket.js and manually executes its
                           phases via Agent/Bash/etc. tool calls — no Workflow tool involved.
```

---

## Tag-Based Skill Suggestions

A second, complementary invocation signal exists alongside `CLAUDE.md`'s file-path-based auto-invoke
table (which fires *during* editing): a ticket's `Process/Skill-signal` tags (`api-design`,
`debugging`, `performance`, `security`) now produce a `suggested_skills` note at ticket-scoping time,
*before* implementation work starts — computed by `ticket-scoper` and `create-tickets.js`'s Structure
phase, surfaced via `log(...)` in `implement-ticket.js`'s Scope phase. See
[`docs/guides/ticket_tagging.md`](../guides/ticket_tagging.md) for the full tag→skill mapping and the
related registry-search-filter mechanism — not duplicated here.

---

## Project Skills (Workflow Shortcuts)

These skills trigger the project's multi-agent workflows. **Only 4 of the project's 11
`.claude/workflows/*.js` files currently have a `.claude/skills/*/SKILL.md` wrapper** — a workflow
with no wrapper has no slash command today (confirmed 2026-07-20 orchestration audit; see the row
notes below).

| Skill | Workflow triggered | When to use |
|---|---|---|
| `/create-tickets` | `create-tickets` | Parse a markdown doc into TCK-*.md ticket files |
| `/implement-ticket` | `implement-ticket` | Implement one development task end-to-end |
| `/implement-epic` | `implement-epic` | Implement all tickets in a folder or epic sequentially |
| `/simq-audit` | `simq-audit` | Check SimQ grade/anchor drift after a calibration corpus change; closes cleanly or spawns a follow-up ticket |

The following 7 simulation/lab workflows exist under `.claude/workflows/*.js` but have **no
`SKILL.md` wrapper today** — they are not currently invocable via slash command. Adding wrappers
for them (mirroring the Action-section pattern the 4 skills above already use) is tracked as
future work, not yet scoped:

| Workflow (no skill wrapper) | Intended purpose |
|---|---|
| `generate-simulation-setup` | Create specs for a new simulation experiment |
| `prepare-simulation-execution` | Validate specs and get the run command |
| `investigate-simulation-result` | Deep anomaly investigation after a run |
| `propose-simulation-enhancements` | Hypothesize and propose fixes for anomalies |
| `register-simulation-result` | Register a completed run into the lab index |
| `compact-simulation-result` | Compress old run logs to recover disk space |
| `update-knowledge-store` | Commit approved insights to the knowledge graph |

---

## Built-in Skills

### Code Quality

**`/code-review`** — Review the current diff for correctness bugs and simplification opportunities.
```
/code-review           # medium effort
/code-review high      # broader coverage, may include uncertain findings
/code-review --fix     # apply findings to working tree after review
/code-review --comment # post findings as inline PR comments
```
Use before opening a PR or after a large implementation session.

**`/simplify`** — Review changed code for reuse, simplification, and efficiency, then apply the fixes. Quality only — does not hunt for bugs (`/code-review` for that).

**`/security-review`** — Review for security vulnerabilities across the diff.

**`/verify`** — Run the app and observe behavior to confirm a change works. Use to validate the golden path and edge cases after implementation.

---

### Development Workflow

**`/test-driven-development`** — Use before writing implementation code. Produces failing tests first, then the minimal implementation to pass them.

**`/brainstorming`** — Use before any creative work: new features, new system design, exploring alternatives. Surfaces intent and trade-offs before committing to an approach.

**`/debugging-strategies`** — Systematic debugging with profiling and root cause analysis. Use when investigating bugs or unexpected behavior. Complements `world-debugger` (agent) for world assembly failures.

---

### Testing

**`/python-testing-patterns`** — Comprehensive pytest patterns: fixtures, mocking, parametrize, test-driven development for Python. Use when setting up new test modules or improving test structure.

**`/backend-testing`** — Backend test strategy covering unit, integration, and API tests. Use for testing repository layers, data pipelines, or service boundaries.

---

### Architecture and Design

**`/architecture`** — ADR (Architecture Decision Record) workflow. Use when making a significant architectural decision that should be recorded in `docs/architecture/`.

**`/api-design-principles`** — REST and API design review. Use when designing new API endpoints or reviewing schema shape.

**`/doc-coauthoring`** — Structured workflow for writing documentation (proposals, specs, decision docs). Use when creating new `docs/` content.

---

### Performance

**`/python-performance-optimization`** — Profile and optimize Python code using cProfile and memory profilers. Use when investigating slow simulation ticks or high-memory world assembly.

---

### Knowledge Graph

**`/graphify`** — Build or rebuild the project knowledge graph at `graphify-out/`. Parses AST, extracts symbols, relationships, and community structure. Read `graphify-out/GRAPH_REPORT.md` for god nodes and architecture overview.

```
/graphify              # full rebuild
graphify update .      # incremental update after src/ changes (run in shell)
```

The `graphify-out/wiki/index.md` provides a navigable wiki built from the graph. Use it instead of reading raw source files for architecture questions.

---

### Observability

**`/agent-monitoring-retro`** — Generate the weekly agent monitoring retro report (`make agent-monitoring-retro`) and walk through the retrospective process (run summary, gate failures, tier distribution, summary quality, slow runs). Use weekly, after 5+ completed tickets, or before changing any agent prompt/phase/tier rule. A `PostToolUse` hook (`tools/agent-monitoring/retro_nudge_hook.py`) nudges via `additionalContext` once 5+ `implement-ticket` runs have completed DONE since the last dated `RETRO-<week>.md` report.

---

### Configuration

**`/update-config`** — Modify `settings.json` or `settings.local.json`. Use for:
- Adding tool permissions (`allow X commands`)
- Configuring hooks (`when Claude stops, show X`)
- Setting environment variables

**`/fewer-permission-prompts`** — Scans transcripts for common read-only Bash and MCP calls, then adds an allowlist to `settings.json` to reduce future prompts.

---

## Project-Level Skill Files

These skills are Python and engineering patterns adapted for this project and stored in `.claude/skills/`:

| Skill | File | Purpose |
|---|---|---|
| `/python-testing-patterns` | `python-testing-patterns/SKILL.md` | Project-specific pytest patterns |
| `/debugging-strategies` | `debugging-strategies/SKILL.md` | Systematic debugging adapted to this stack |
| `/backend-testing` | `backend-testing/SKILL.md` | Backend test patterns |
| `/test-driven-development` | `test-driven-development/SKILL.md` | TDD workflow |
| `/python-performance-optimization` | `python-performance-optimization/SKILL.md` | Performance profiling |
| `/brainstorming` | `brainstorming/SKILL.md` | Feature exploration |
| `/api-design-principles` | `api-design-principles/SKILL.md` | API design review |
| `/architecture` | `architecture/SKILL.md` | ADR documentation |
| `/doc-coauthoring` | `doc-coauthoring/SKILL.md` | Documentation co-authoring |
| `/prompt-builder` | `prompt-builder/SKILL.md` | Prompt construction guidance |
| `/frontend-design` | `frontend-design/SKILL.md` | Frontend component design |
| `/agent-monitoring-retro` | `agent-monitoring-retro/SKILL.md` | Agent monitoring retro report generation |

---

## Choosing the Right Tool

| Situation | Tool |
|---|---|
| Parse a plan doc into ticket files | `/create-tickets` |
| Implement a single task or resume a ticket | `/implement-ticket` |
| Implement all tickets in a folder or epic | `/implement-epic` |
| Quick code review before PR | `/code-review` |
| Understand codebase architecture | `/graphify` → read `graphify-out/wiki/index.md` |
| Debug a world assembly failure | `Agent(subagent_type: "world-debugger")` |
| Check mechanics parity after a change | `Agent(subagent_type: "mechanics-auditor")` |
| Profile slow simulation tick | `/python-performance-optimization` |
| Design a new subsystem | `/architecture` then `/brainstorming` |
| Run a simulation experiment | `/generate-simulation-setup` → `/prepare-simulation-execution` → `/register-simulation-result` |
| Analyze run anomalies | `Agent(subagent_type: "simulation-analyst")` for quick check; `/investigate-simulation-result` for deep diagnosis |
