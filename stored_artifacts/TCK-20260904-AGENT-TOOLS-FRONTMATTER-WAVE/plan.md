---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE
artifact_type: plan
tags: [governance, ai, frontmatter]
---

# Implementation Plan — TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE

## Summary

Add an explicit `tools:` allowlist frontmatter line to each of the 11 Wave 1 agent definitions in
`.claude/agents/`, matching the exact per-agent candidate scopes investigation.md already derived
(5 from real usage evidence, 6 policy-derived), leave `concern-investigator.md` byte-identical
(it already has the field and investigation.md found no evidence to change it), add one new
parametrized structural test file that pins every candidate scope and guards against Wave 2/3
scope creep, and update the epic doc's M3 section to record that Step 0 is now empirically
resolved and that this ticket's own closable scope is Wave 1 only. Every edit to an existing
`.claude/agents/*.md` file is **frontmatter-only** — no file's prose body changes as part of this
plan, and `doc-updater.md` in particular gets a frontmatter-only line added on top of the
already-uncommitted prose change from the sibling ticket `TCK-20260904-DOC-COVERAGE-REVERSE-CHECK`,
never a revert of that prose. Wave 2 (`architecture-reviewer`, `security-reviewer`, `planner`) and
Wave 3 (`implementer`, `parity-updater`) are explicitly out of scope for every step below — no step
touches those 5 files, and Step 1's new test file's own anti-drift assertions actively guard
against it.

## Steps

### Step 1 — Create the Wave 1 structural test file
**Files:** `tests/tools/test_wave1_agent_tools_frontmatter.py` (new)
**Change:**
Create a new pytest module, structurally modeled on
`tests/tools/test_concern_investigator_agent_definition.py`'s `_parse_frontmatter` helper (read at
`tests/tools/test_concern_investigator_agent_definition.py:44-47`: strips the file's leading
`---\n`, finds the next `\n---` via `text.index("\n---", 4)`, and `yaml.safe_load`s the slice
between them — reuse this exact parsing approach rather than inventing a new one, since it is
already proven against this repo's actual frontmatter shape).

Module contents:

```python
from pathlib import Path
import pytest
import yaml

_ROOT = Path(__file__).parent.parent.parent
_AGENTS_DIR = _ROOT / ".claude" / "agents"

# Candidate tools: scope per Wave 1 agent, copied verbatim from investigation.md's
# per-agent candidate-scope table (usage-backed table + policy-derived table).
_WAVE1_CANDIDATE_TOOLS = {
    "concern-investigator": ["Read", "Grep", "Glob", "Bash", "WebFetch", "WebSearch",
                              "mcp__knowledge-search__search_docs"],  # unchanged, existing precedent
    "doc-updater": ["Read", "Edit", "Write", "Bash", "Agent", "ListAgents",
                    "mcp__knowledge-search__search_docs", "ToolSearch", "TaskUpdate",
                    "Artifact", "ScheduleWakeup", "AskUserQuestion", "SendMessage", "Skill"],
    "investigator": ["Read", "Write", "Edit", "Bash", "Agent",
                      "mcp__knowledge-search__search_docs", "ToolSearch", "Skill", "Artifact",
                      "ListAgents", "TaskUpdate", "TaskCreate", "WebSearch", "AskUserQuestion",
                      "ScheduleWakeup", "Monitor", "TaskStop", "WebFetch", "SendFeedback"],
    "ticket-scoper": ["Bash", "Read", "Edit", "Agent", "Write", "ToolSearch",
                       "mcp__knowledge-search__search_docs", "ListAgents", "AskUserQuestion",
                       "TaskCreate", "ScheduleWakeup", "SendMessage", "TaskUpdate", "Monitor",
                       "TaskStop"],
    "done-checker": ["Bash", "Read", "Edit", "Agent", "Write",
                       "mcp__knowledge-search__search_docs", "TaskUpdate", "ToolSearch",
                       "ScheduleWakeup", "TaskCreate", "AskUserQuestion", "Artifact", "Monitor",
                       "ListAgents", "WebSearch", "TaskOutput", "Skill", "SendMessage", "TaskStop",
                       "WebFetch", "SendUserFile", "ReportFindings",
                       "mcp__knowledge-gateway__knowledge_context",
                       "mcp__knowledge-gateway__knowledge_status"],
    "test-scoper": ["Bash", "Read", "Agent", "ToolSearch", "Monitor", "Write", "SendMessage",
                     "ListAgents", "mcp__knowledge-search__search_docs", "ScheduleWakeup",
                     "TaskStop", "AskUserQuestion", "SendFeedback", "TaskUpdate", "Artifact",
                     "Skill", "mcp__knowledge-gateway__knowledge_status",
                     "mcp__knowledge-search__search_health", "SendUserFile"],  # Edit deliberately excluded
    "mechanics-auditor": ["Read", "Grep", "Glob", "Bash", "mcp__knowledge-search__search_docs"],
    "spec-document-reviewer": ["Read", "Grep", "Glob", "mcp__knowledge-search__search_docs"],
    "simulation-analyst": ["Read", "Grep", "Glob", "Bash"],
    "world-debugger": ["Read", "Grep", "Glob", "Bash"],
    "world-render-reviewer": ["Read"],
}

# Tools this investigation explicitly classified as excluded per agent — the anti-drift pin
# for the single most consequential judgment call in this ticket (test-scoper's Edit exclusion)
# plus the four policy-derived report-only agents and world-render-reviewer's narrow scope.
_WAVE1_FORBIDDEN_PAIRS = [
    ("test-scoper", "Edit"),
    ("mechanics-auditor", "Write"), ("mechanics-auditor", "Edit"), ("mechanics-auditor", "Agent"),
    ("spec-document-reviewer", "Write"), ("spec-document-reviewer", "Edit"),
    ("spec-document-reviewer", "Agent"),
    ("simulation-analyst", "Write"), ("simulation-analyst", "Edit"), ("simulation-analyst", "Agent"),
    ("world-debugger", "Write"), ("world-debugger", "Edit"), ("world-debugger", "Agent"),
    ("world-render-reviewer", "Write"), ("world-render-reviewer", "Edit"),
    ("world-render-reviewer", "Bash"), ("world-render-reviewer", "Agent"),
    ("world-render-reviewer", "Grep"), ("world-render-reviewer", "Glob"),
]

_WAVE2_WAVE3_AGENTS = ["architecture-reviewer", "security-reviewer", "planner",
                        "implementer", "parity-updater"]

_CONCERN_INVESTIGATOR_EXPECTED_TOOLS_LINE = (
    "Read, Grep, Glob, Bash, WebFetch, WebSearch, mcp__knowledge-search__search_docs"
)


def _parse_frontmatter(agent_name: str) -> dict:
    text = (_AGENTS_DIR / f"{agent_name}.md").read_text(encoding="utf-8")
    assert text.startswith("---\n")
    end = text.index("\n---", 4)
    return yaml.safe_load(text[4:end])


@pytest.mark.parametrize("agent_name", sorted(_WAVE1_CANDIDATE_TOOLS))
def test_wave1_agent_files_declare_tools_field(agent_name):
    fm = _parse_frontmatter(agent_name)
    assert "tools" in fm, f"{agent_name}.md must declare a tools: field"
    declared = [t.strip() for t in fm["tools"].split(",")]
    assert declared, f"{agent_name}.md tools: field must not be empty"
    expected = _WAVE1_CANDIDATE_TOOLS[agent_name]
    assert declared == expected, (
        f"{agent_name}.md tools: field {declared} does not match the candidate scope "
        f"pinned from investigation.md: {expected}"
    )


@pytest.mark.parametrize("agent_name,forbidden_tool", _WAVE1_FORBIDDEN_PAIRS)
def test_wave1_candidate_scope_excludes_known_denied_tools(agent_name, forbidden_tool):
    fm = _parse_frontmatter(agent_name)
    declared = [t.strip() for t in fm["tools"].split(",")]
    assert forbidden_tool not in declared, (
        f"{agent_name}.md must not grant {forbidden_tool} per investigation.md's classification"
    )


@pytest.mark.parametrize("agent_name", sorted(_WAVE1_CANDIDATE_TOOLS))
def test_wave1_agents_do_not_declare_disallowed_tools_field(agent_name):
    fm = _parse_frontmatter(agent_name)
    assert "disallowedTools" not in fm, (
        f"{agent_name}.md must use the tools: allowlist pattern only for Wave 1, "
        "not the unprecedented disallowedTools: denylist (investigation.md Step 0 conclusion)"
    )


@pytest.mark.parametrize("agent_name", _WAVE2_WAVE3_AGENTS)
def test_wave2_wave3_agents_do_not_gain_tools_field(agent_name):
    fm = _parse_frontmatter(agent_name)
    assert "tools" not in fm, (
        f"{agent_name}.md is Wave 2/3 scope, explicitly deferred by this ticket — "
        "it must not gain a tools: field as a side effect of Wave 1"
    )


def test_concern_investigator_tools_field_unchanged_byte_identical():
    fm = _parse_frontmatter("concern-investigator")
    assert fm["tools"] == _CONCERN_INVESTIGATOR_EXPECTED_TOOLS_LINE, (
        "concern-investigator.md's tools: value must stay byte-identical — "
        "investigation.md found zero usage evidence to justify changing it"
    )
```

**Do NOT touch:** `tests/tools/test_concern_investigator_agent_definition.py` (stays as-is per its
own scope — its `_DISALLOWED_TOOLS`/`_EXPECTED_SCHEMA_REQUIRED_FIELDS` constants are specific to
that one agent's `create-tickets.js` dispatch contract, not a place to fold Wave 1's broader
concerns into).
**Verify:** immediately after creating this file, run
`pytest tests/tools/test_wave1_agent_tools_frontmatter.py -v`. At this point in the sequence
(before Steps 2-11 land), expect: the `test_wave2_wave3_agents_do_not_gain_tools_field` and
`test_concern_investigator_tools_field_unchanged_byte_identical` cases PASS immediately (nothing to
change yet), and every `test_wave1_agent_files_declare_tools_field`/
`test_wave1_candidate_scope_excludes_known_denied_tools`/
`test_wave1_agents_do_not_declare_disallowed_tools_field` case for the other 10 agents FAILS with
`assert "tools" in fm` — this is the expected RED state proving the test actually exercises the
files, not a false-pass. Each subsequent step turns exactly one agent's parametrized cases GREEN.

### Step 2 — doc-updater.md: add `tools:` frontmatter line on top of the existing uncommitted prose change
**Files:** `.claude/agents/doc-updater.md`
**Change:** This file is a **confirmed concurrent-writer situation** — `git diff HEAD --
.claude/agents/doc-updater.md` (re-run during planning) shows an existing **uncommitted** working-tree
modification: `TCK-20260904-DOC-COVERAGE-REVERSE-CHECK` already added item 6 under "## What to Do"
(the file's current lines 68-73, beginning `6. Before returning, cross-reference every...`), on top
of the last-committed version at `6dcc5dc9`. **No other writer touches this file concurrently** —
`tickets/done/TCK-20260904-TEST-SCOPER-HANG-GUARD.md`'s own investigation confirmed via `git diff
HEAD -- .claude/agents/` that it touched zero `.claude/agents/*.md` files (only considered
`test-scoper.md`'s prose and explicitly left it untouched), so there is no third writer to
reconcile against for this file.

Current frontmatter (as it exists in the working tree right now, confirmed by direct read):
```
---
name: doc-updater
description: After a behavior change is implemented, updates the relevant docs/ files (outside parity_ledger/, audits/, archive/, scenarios/, entity/) to reflect the new state.
---
```
Insert a new `tools:` line between the `description:` line and the closing `---`, in the exact
comma-separated single-line style `concern-investigator.md:4` already uses (`tools: Read, Grep,
Glob, Bash, WebFetch, WebSearch, mcp__knowledge-search__search_docs`), so the result is:
```
---
name: doc-updater
description: After a behavior change is implemented, updates the relevant docs/ files (outside parity_ledger/, audits/, archive/, scenarios/, entity/) to reflect the new state.
tools: Read, Edit, Write, Bash, Agent, ListAgents, mcp__knowledge-search__search_docs, ToolSearch, TaskUpdate, Artifact, ScheduleWakeup, AskUserQuestion, SendMessage, Skill
---
```
Use the `Edit` tool with `old_string` scoped to exactly these 4 lines (description line + both
`---` delimiters) so the diff is a pure single-line addition, leaving lines 68-73 (item 6's prose)
untouched. Per investigation.md's candidate-scope table, **no tool is excluded here** — all 14
observed tools have a role-consistent example (5,206 real historical rows), so the candidate scope
is the full observed set with no 5-way-taxonomy exclusion needed.
**Do NOT touch:** the "## What to Do" section's item 6 (lines 68-73) — that is
`TCK-20260904-DOC-COVERAGE-REVERSE-CHECK`'s own uncommitted work, not this ticket's. Do not
re-order, reformat, or re-word any existing prose in this file; the only diff this step produces is
the one added `tools:` line.
**Verify:** `pytest tests/tools/test_wave1_agent_tools_frontmatter.py -k doc-updater -v` and
`pytest tests/tools/test_doc_updater_agent_file.py -v` (must still pass unmodified — confirms the
frontmatter addition didn't disturb whatever structural/prose assertions that pre-existing test
makes).

### Step 3 — investigator.md
**Files:** `.claude/agents/investigator.md`
**Change:** Same insertion pattern as Step 2 (new `tools:` line between `description:` and the
closing `---`, no other file in this batch is a concurrent writer to `investigator.md` — confirmed,
investigation.md's Prior Work section names only `doc-updater.md` as having a live concurrent-edit
consideration). Current frontmatter (confirmed by direct read, lines 1-4):
```
---
name: investigator
description: Given a ticket, digs into the affected codebase and produces the two mandatory pre-implementation artifacts, investigation.md and test_plan.md.
---
```
New line to insert:
```
tools: Read, Write, Edit, Bash, Agent, mcp__knowledge-search__search_docs, ToolSearch, Skill, Artifact, ListAgents, TaskUpdate, TaskCreate, WebSearch, AskUserQuestion, ScheduleWakeup, Monitor, TaskStop, WebFetch, SendFeedback
```
Per investigation.md: the one "would deny" candidate (`SendFeedback`, 1 call) is classified
**legitimate-but-rare** and kept in scope (a genuine harness-friction bug report, not domain scope
creep) — so nothing is excluded from the full observed set.
**Do NOT touch:** any prose in this file (its `## Inputs`/methodology sections are untouched).
**Verify:** `pytest tests/tools/test_wave1_agent_tools_frontmatter.py -k investigator -v`.

### Step 4 — ticket-scoper.md
**Files:** `.claude/agents/ticket-scoper.md`
**Change:** Same pattern. Current frontmatter (confirmed, lines 1-4):
```
---
name: ticket-scoper
description: Given a request description, produces a complete correctly-formatted ticket and flags any conflicts (duplicate work, mechanics constraints, parity overlap) before implementation begins.
---
```
New line:
```
tools: Bash, Read, Edit, Agent, Write, ToolSearch, mcp__knowledge-search__search_docs, ListAgents, AskUserQuestion, TaskCreate, ScheduleWakeup, SendMessage, TaskUpdate, Monitor, TaskStop
```
Per investigation.md: no exclusions — `Edit` traces to real output edits (e.g.
`docs/agent-monitoring/README.md`), consistent with its documented ticket-producing role.
**Do NOT touch:** any other line in this file.
**Verify:** `pytest tests/tools/test_wave1_agent_tools_frontmatter.py -k ticket-scoper -v`.

### Step 5 — done-checker.md
**Files:** `.claude/agents/done-checker.md`
**Change:** Same pattern. Current frontmatter (confirmed, lines 1-4):
```
---
name: done-checker
description: Verifies all 13 Definition-of-Done conditions for a ticket before it can move to tickets/done/, citing the static pre-check script for the five script-checkable conditions.
---
```
New line:
```
tools: Bash, Read, Edit, Agent, Write, mcp__knowledge-search__search_docs, TaskUpdate, ToolSearch, ScheduleWakeup, TaskCreate, AskUserQuestion, Artifact, Monitor, ListAgents, WebSearch, TaskOutput, Skill, SendMessage, TaskStop, WebFetch, SendUserFile, ReportFindings, mcp__knowledge-gateway__knowledge_context, mcp__knowledge-gateway__knowledge_status
```
Per investigation.md: the two `mcp__knowledge-gateway__*` calls (1 each) are flagged
**unclear-needs-review** (a different MCP search surface than `done-checker.md`'s own prose ever
names) but are kept in scope for Wave 1 per the investigation's explicit recommendation — cost of
excluding a legitimately-rare read-only tool outweighs the cost of including it; flagged for the
post-rollout tightening pass, not resolved here.
**Do NOT touch:** any other line in this file.
**Verify:** `pytest tests/tools/test_wave1_agent_tools_frontmatter.py -k done-checker -v`.

### Step 6 — test-scoper.md (Edit deliberately excluded)
**Files:** `.claude/agents/test-scoper.md`
**Change:** Same pattern. Current frontmatter (confirmed, lines 1-4):
```
---
name: test-scoper
description: Given a set of changed files, maps them to relevant existing tests, builds and runs the correct scoped pytest command, and reports pass/fail counts and coverage gaps.
---
```
New line:
```
tools: Bash, Read, Agent, ToolSearch, Monitor, Write, SendMessage, ListAgents, mcp__knowledge-search__search_docs, ScheduleWakeup, TaskStop, AskUserQuestion, SendFeedback, TaskUpdate, Artifact, Skill, mcp__knowledge-gateway__knowledge_status, mcp__knowledge-search__search_health, SendUserFile
```
**This is the single most consequential judgment call in the whole ticket** (investigation.md's own
Risks section language): `Edit` had **147 historical calls** — not a trivial anomaly — but is
**deliberately excluded** per investigation.md's explicit recommendation, because `test-scoper.md`'s
own documented role ("map changed files → tests, build/run the scoped pytest command, report
pass/fail") never describes editing test files, and the usage-baseline ticket's own investigation
flags that `tools.jsonl`'s `agent` field cannot distinguish a real subagent dispatch from
hand-orchestration convention-labeling — so the 147 calls are judged more likely to be
hand-orchestration mislabeling than a genuine required capability. If this exclusion is wrong,
Wave 1's observation window will surface it as a real, visible permission-denial — that is the
intended signal, not a bug to route around.
**Do NOT touch:** any other line in this file. Do not add `Edit` "just in case" — that would
silently reverse the one explicit judgment call this investigation made.
**Verify:** `pytest tests/tools/test_wave1_agent_tools_frontmatter.py -k test-scoper -v` (must
confirm both that `tools:` is declared AND that `Edit` is absent — the
`test_wave1_candidate_scope_excludes_known_denied_tools[test-scoper-Edit]` case is the specific
regression guard for this step).

### Step 7 — mechanics-auditor.md
**Files:** `.claude/agents/mechanics-auditor.md`
**Change:** Same pattern. Current frontmatter (confirmed, lines 1-4):
```
---
name: mechanics-auditor
description: Compares a Mechanics Bible chapter to the actual source implementation and reports PARITY/DIVERGENT/MISSING/UNDOCUMENTED findings.
---
```
New line:
```
tools: Read, Grep, Glob, Bash, mcp__knowledge-search__search_docs
```
**Policy-derived, zero usage evidence** (this agent has zero historical tool-call rows in the
corpus per the live re-run of `tools/agent-monitoring/agent_tool_usage_baseline.py`) — scope is
derived from a static read of the agent's own file: it reads Mechanics Bible chapters + source
code, runs one static pre-check script via `Bash`, uses `docs/REGISTRY.yaml` lookups; no
Write/Edit/Agent described anywhere in its methodology (report-only). This is a materially weaker
confidence claim than the usage-backed agents in Steps 2-6 — flag it as such, do not present it
with equal confidence.
**Do NOT touch:** any other line in this file.
**Verify:** `pytest tests/tools/test_wave1_agent_tools_frontmatter.py -k mechanics-auditor -v`.

### Step 8 — spec-document-reviewer.md
**Files:** `.claude/agents/spec-document-reviewer.md`
**Change:** Same pattern. Current frontmatter (confirmed, lines 1-4):
```
---
name: spec-document-reviewer
description: Reviews a written design spec for completeness, internal consistency, clarity, scope focus, and YAGNI violations before implementation planning begins.
---
```
New line:
```
tools: Read, Grep, Glob, mcp__knowledge-search__search_docs
```
Policy-derived, zero usage evidence, same caveat as Step 7 — reads one spec doc, reviews for
internal quality; no Bash/Write/Edit described in its own methodology.
**Do NOT touch:** any other line in this file.
**Verify:** `pytest tests/tools/test_wave1_agent_tools_frontmatter.py -k spec-document-reviewer -v`.

### Step 9 — simulation-analyst.md
**Files:** `.claude/agents/simulation-analyst.md`
**Change:** Same pattern. Current frontmatter (confirmed, lines 1-4):
```
---
name: simulation-analyst
description: Lightweight single-pass analysis of a completed simulation run against Mechanics Bible ranges — spots anomalies and classifies severity; escalate CRITICAL findings to the investigate-simulation-result workflow.
---
```
New line:
```
tools: Read, Grep, Glob, Bash
```
Policy-derived, zero usage evidence, same caveat as Step 7 — reads `data/runs/{session_id}/`,
`registration/`, `docs/mechanics/`; "lightweight single-pass," report-only per its own file.
**Do NOT touch:** any other line in this file.
**Verify:** `pytest tests/tools/test_wave1_agent_tools_frontmatter.py -k simulation-analyst -v`.

### Step 10 — world-debugger.md
**Files:** `.claude/agents/world-debugger.md`
**Change:** Same pattern. Current frontmatter (confirmed, lines 1-4):
```
---
name: world-debugger
description: Given a failure symptom in world assembly, worldbuilding, worldmodules, worldgeneration, content resolution, or the core registries, traces the authoritative pipeline to find the root cause.
---
```
New line:
```
tools: Read, Grep, Glob, Bash
```
Policy-derived, zero usage evidence, same caveat as Step 7 — traces the authoritative pipeline via
source reads; report-only, no described mutation in its own file.
**Do NOT touch:** any other line in this file.
**Verify:** `pytest tests/tools/test_wave1_agent_tools_frontmatter.py -k world-debugger -v`.

### Step 11 — world-render-reviewer.md (narrowest of all 16)
**Files:** `.claude/agents/world-render-reviewer.md`
**Change:** Same pattern. Current frontmatter (confirmed, lines 1-4):
```
---
name: world-render-reviewer
description: Tiered visual/geometric quality review of a rendered world state — Tier 0 pure-data scoring by default, escalating to the annotated/gridlined render only when Tier 0/1 flags an anomaly. Cites tile coordinates from the annotated image, never the plain render.
---
```
New line:
```
tools: Read
```
Policy-derived, zero usage evidence — this agent's own file states an explicit "only call Read...
never a substitute" rule and no other tool appears anywhere in it; it reads only a `Tier1Digest`
JSON and conditionally one annotated PNG. Narrowest scope of all 16 agents in the repo.
**Do NOT touch:** any other line in this file.
**Verify:** `pytest tests/tools/test_wave1_agent_tools_frontmatter.py -k world-render-reviewer -v`.

### Step 12 — concern-investigator.md: verification only, no edit
**Files:** none edited.
**Change:** No file change. `concern-investigator.md:4` already declares
`tools: Read, Grep, Glob, Bash, WebFetch, WebSearch, mcp__knowledge-search__search_docs` and
investigation.md found zero usage evidence (this agent has zero historical tool-call rows) to
justify expanding or narrowing it — despite the epic doc's M3 language calling for "re-verify
against M1's real data," the correct action per investigation.md's own recommendation is to keep
the existing declaration as-is rather than invent a re-verification with no real data behind it.
**Do NOT touch:** `.claude/agents/concern-investigator.md` — any diff to this file during Wave 1 is
itself a regression signal, not an improvement (per test_plan.md's own anti-drift framing).
**Verify:** `pytest tests/tools/test_wave1_agent_tools_frontmatter.py::test_concern_investigator_tools_field_unchanged_byte_identical -v` (already passing since Step 1; re-run here as the closing
confirmation for this agent specifically).

### Step 13 — Full scoped regression pass
**Files:** none (verification only).
**Change:** Run, in order:
1. `pytest tests/tools/test_wave1_agent_tools_frontmatter.py tests/tools/test_concern_investigator_agent_definition.py tests/tools/test_doc_updater_agent_file.py -v` — all Wave 1 parametrized cases plus both pre-existing structural tests must now pass.
2. `PYTHONPATH=tools:. pytest tests/agent_orchestration/ -q` — pure regression check (this ticket touches no `agent-orchestration/*.yaml`); must still pass unmodified. Use `PYTHONPATH=tools:.` per the sibling `TCK-20260904-TEST-SCOPER-HANG-GUARD`'s documented environment note — this test file only imports successfully with that PYTHONPATH, not the bare `pythonpath=["."]` pytest config.
3. `pytest tests/tools/ -q` — the bare directory, not cherry-picked files, per test-scoper's own documented scoping rule (cherry-picking individual files within an otherwise-correctly-identified directory is the project's most common `test_scope_coverage_static` failure mode).
4. **`tools/validate_frontmatter.py` is confirmed N/A for this change, not assumed so**: direct read of `tools/validate_frontmatter.py:1-36` shows it "Supports four content types: doc, ticket, artifact, archive" (docstring, lines 6-7) and a `grep -n "agents\|\.claude" tools/validate_frontmatter.py` returns zero matches — this script never scans `.claude/agents/*.md`, so no separate validation run against it is needed or possible for this step's files. Do not run it against the agent files and do not treat its absence of coverage as a gap to fix in this ticket (out of scope — it would be a change to the validator's content-type scope, not a frontmatter-wave rollout).
**Do NOT touch:** no file changes in this step.
**Verify:** all four commands above exit 0 / all tests pass.

### Step 14 — Update the epic doc's M3 section
**Files:** `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md`
**Change:** Confirmed sole writer to this doc for this ticket batch: `git log` shows its last
commit is `220618bd` (the epic's own creation commit) and `git status --porcelain` on the file is
clean (no other concurrent uncommitted change); the sibling
`TCK-20260904-AGENT-TOOL-USAGE-BASELINE` explicitly ruled this file out of its own scope
(`stored_artifacts/TCK-20260904-AGENT-TOOL-USAGE-BASELINE/investigation.md:132` and
`plan.md:196,214` both state it is "not required to change" / "explicitly out of scope"). No
concurrent-writer reconciliation is needed for this step.

Insert a new paragraph immediately after the existing Step 0 bullet (the file's current lines
85-88, ending "...Do not assume either behavior from unverified documentation — observe it.") and
before the "**Offline candidate-policy replay**" paragraph (current line 90), reading:

```
**Step 0 outcome, confirmed (2026-09-05):** `TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE`'s
investigation empirically confirmed both fields via direct binary-schema extraction from the
installed harness and a live subagent dispatch — `tools:` is enforced (an undeclared tool is not
exposed to the model's function-calling surface at all) and `disallowedTools` is a real, recognized
frontmatter/spawn-option key in the harness's own schema. This supersedes the earlier framing above
that "Claude Code's own documentation was unreachable... only third-party sources describe"
this behavior — it is now confirmed directly, not merely third-party-documented. That same ticket
landed Wave 1 (11 read-oriented agents) only; Wave 2 (`architecture-reviewer`, `security-reviewer`,
`planner`) and Wave 3 (`implementer`, `parity-updater`) remain unimplemented, gated on Wave 1's real
elapsed observation window (a single session cannot manufacture that time) and tracked as separate
future tickets, not sub-steps of the ticket that landed Wave 1.
```

This is an additive insertion only — per `doc-updater.md`'s own per-family rule for
`docs/plans/`, "update in place if the plan is still live," never rewriting the surrounding
prose or moving the doc to `docs/plans/archive/`.
**Do NOT touch:** the M3 milestone's Wave 1/2/3 role lists (current lines 105-113), the Sizing rule
paragraph, the Observability requirement paragraph, or the epic's Acceptance signal section (lines
191-198) — none of those describe outcomes this ticket changes; they already correctly describe the
target end-state across all three waves, which this ticket does not complete.
**Verify:** manual read-back confirming the inserted paragraph is the only diff to this file
(`git diff -- docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md` shows exactly one added paragraph, zero deletions, zero reflow of surrounding lines).

## Scope Guards

- Do not create, edit, or add `tools:`/`disallowedTools:` frontmatter to `architecture-reviewer.md`,
  `security-reviewer.md`, `planner.md`, `implementer.md`, or `parity-updater.md` — Wave 2/3, out of
  scope for this ticket regardless of how mechanically easy it would be to also touch them in the
  same sitting. `test_wave2_wave3_agents_do_not_gain_tools_field` (Step 1) enforces this.
- Do not introduce `disallowedTools:` anywhere in `.claude/agents/*.md` — Wave 1 uses the `tools:`
  allowlist pattern exclusively, matching the one working local precedent
  (`concern-investigator.md`), per investigation.md's Step 0 conclusion.
  `test_wave1_agents_do_not_declare_disallowed_tools_field` (Step 1) enforces this.
- Do not narrow `Bash` command-level permissions (`.claude/settings.json`'s `permissions.allow`) as
  part of this ticket — that is a separate, untouched mechanism from which top-level *tools* an
  agent's frontmatter grants. Out of this ticket's own Out-of-Scope line.
- Do not re-touch or revert `doc-updater.md`'s existing uncommitted prose (item 6 under "## What to
  Do", lines 68-73) — Step 2's edit is frontmatter-only.
- Do not modify any of the other 10 files' body/prose content — every step 2-11 edit is a single
  added `tools:` frontmatter line, nothing else.
- Do not change `concern-investigator.md` at all (Step 12).
- Do not attempt Wave 2 or Wave 3 in any reduced/partial form, and do not fabricate an observation
  window for them.
- Do not edit `tools/validate_frontmatter.py` to add `.claude/agents/` coverage — confirmed out of
  scope for this ticket (Step 13.4); that would be a change to the validator's scope, not a
  frontmatter-wave rollout.

## Dependency Map

Steps 2-11 (the 11 per-file frontmatter edits) are mutually independent — each touches exactly one
file and can be done/reviewed/reverted in any order. Step 1 (test file creation) should land first
so each subsequent step has an immediate, narrow verification target (`-k <agent-name>`), but the
test file's assertions do not require any particular file-edit ordering among Steps 2-11. Step 12
has no file dependency (verification only). Step 13 depends on Steps 1-12 all being complete (it is
the full regression pass). Step 14 (doc update) is independent of Steps 1-13 and could be done at
any point, but is sequenced last here since it documents the batch's completed outcome.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Step 0 empirical verification performed before Wave 1, real harness behavior directly observed and documented (not the disqualified TCK-20260709 evidence); disallowedTools checked the same way | Already satisfied by investigation.md (Method A live dispatch + Method B binary-schema extraction) — no plan step redoes this; Step 14 records the outcome in the epic doc | N/A (evidence-based, not test-based) — cited in investigation.md's Step 0 section |
| Rollout does not begin until TCK-20260904-AGENT-TOOL-USAGE-BASELINE's usage table exists and is linked as this ticket's input dependency | Already satisfied — investigation.md confirms the usage-baseline ticket is finalized and its usage table was live re-run and consulted for every usage-backed agent's candidate scope (Steps 2-6) | N/A (dependency-check, not test-based) |
| For every Wave 1 agent, a candidate tools: scope is proposed with every historical "would deny" call classified per the 5-way taxonomy — no capability silently dropped without that classification | Steps 2-11 (each step's Change text states the taxonomy classification for every excluded/included edge case: doc-updater none excluded, investigator SendFeedback legitimate-but-rare, ticket-scoper none excluded, done-checker knowledge-gateway calls unclear-needs-review-but-kept, test-scoper Edit excluded, 6 policy-derived agents flagged as zero-usage/weaker-confidence) | `test_wave1_candidate_scope_excludes_known_denied_tools` (Step 1) pins every excluded tool per agent |
| After a wave lands, each of that wave's agent files carries an explicit tools: field verified by a parametrized extension of test_concern_investigator_agent_definition.py's pattern, plus a documented single-file revert command written before the change lands | Steps 2-12 (frontmatter lands); Step 1 (parametrized test); revert commands documented below in Anti-Drift Notes | `test_wave1_agent_files_declare_tools_field` (Step 1), full pass confirmed in Step 13 |

## Anti-Drift Notes

- **Documented per-file revert commands (written before any wave starts, per the epic's own
  requirement)**:
  - For 10 of the 11 files (`investigator`, `ticket-scoper`, `done-checker`, `test-scoper`,
    `mechanics-auditor`, `spec-document-reviewer`, `simulation-analyst`, `world-debugger`,
    `world-render-reviewer`, and — trivially, since it is never edited — `concern-investigator`),
    the revert is the simple, trivial single-file checkout the epic requires:
    `git checkout HEAD -- .claude/agents/<name>.md`. Each of these files has no other uncommitted
    change layered on it, confirmed by `git status --porcelain -- .claude/agents/` at planning
    time, so `HEAD` is a safe, clean revert baseline for all 10.
  - **`doc-updater.md` is the one exception, and using `git checkout HEAD --
    .claude/agents/doc-updater.md` would be WRONG for it** — that command would revert not only
    Step 2's added `tools:` line but also the sibling `TCK-20260904-DOC-COVERAGE-REVERSE-CHECK`'s
    already-uncommitted item-6 prose addition (lines 68-73), which this ticket must not touch or
    lose. The correct, documented revert for this one file is a **surgical single-line removal**:
    delete only the `tools: Read, Edit, Write, Bash, Agent, ListAgents,
    mcp__knowledge-search__search_docs, ToolSearch, TaskUpdate, Artifact, ScheduleWakeup,
    AskUserQuestion, SendMessage, Skill` line via `Edit` (exact `old_string`/`new_string` matching
    Step 2's insertion, reversed), leaving every other line — including item 6 — exactly as it was
    before this ticket's edit. Do not default to `git checkout HEAD --` for this file.
- **The 6 zero-usage-evidence agents' scopes are policy-derived, not validated** — flag this
  explicitly in the ticket's own Completion Summary, not just here: `concern-investigator`,
  `mechanics-auditor`, `simulation-analyst`, `spec-document-reviewer`, `world-debugger`,
  `world-render-reviewer` carry materially weaker confidence than the 5 usage-backed agents and are
  the most likely candidates for the epic's own post-rollout tightening pass.
- **`test-scoper`'s `Edit` exclusion (Step 6) is the single largest, most consequential judgment
  call in this ticket** — 147 historical calls excluded on the reasoning that `test-scoper.md`'s
  documented role is report-only and the calls are more likely hand-orchestration mislabeling than
  a genuine capability need. This is stated explicitly, not defaulted silently either way; if wrong,
  Wave 1's observation window will surface it as a real permission-denial, which is the intended
  signal.
- **Completion Summary must state the Wave-1-only closure explicitly, not leave it implied**: this
  ticket closes Step 0 + usage-baseline dependency check + per-agent candidate-scope/taxonomy
  proposal + Wave 1's 11-agent rollout with tests and per-file revert commands. Wave 2
  (`architecture-reviewer`, `security-reviewer`, `planner`) and Wave 3 (`implementer`,
  `parity-updater`) are explicitly NOT part of this ticket's completion and require their own future
  tickets, opened only after Wave 1's real observation window (genuine elapsed calendar time with
  live agent-monitoring data) shows zero permission regressions — per investigation.md's Risks
  section, this is itself part of the ticket's "no material gap left unstated" obligation, not an
  optional footnote.
- **Do not conflate this ticket's `tools:` scoping with `.claude/settings.json`'s
  `permissions.allow` Bash command-level allowlist** — separate, untouched mechanism (see Scope
  Guards).
