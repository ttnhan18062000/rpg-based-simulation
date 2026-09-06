---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE
artifact_type: investigation
tags: [governance, ai, frontmatter]
---

# Investigation — TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE

## Current Behavior

**16 `.claude/agents/*.md` files exist today** (`ls .claude/agents/*.md`, confirmed by direct
listing): `architecture-reviewer`, `concern-investigator`, `doc-updater`, `done-checker`,
`implementer`, `investigator`, `mechanics-auditor`, `parity-updater`, `planner`,
`security-reviewer`, `simulation-analyst`, `spec-document-reviewer`, `test-scoper`,
`ticket-scoper`, `world-debugger`, `world-render-reviewer`. Exactly **one**
(`concern-investigator.md`) declares a `tools:` field today:
```
tools: Read, Grep, Glob, Bash, WebFetch, WebSearch, mcp__knowledge-search__search_docs
```
No file declares `disallowedTools:` anywhere in this repo. All other 15 files' frontmatter is only
`name:`/`description:` — they inherit the full, unscoped session tool surface.

### Step 0 — empirical verification (blocking prerequisite), performed for real this investigation

Two independent, direct-observation methods were used (not assumption, not re-citing the weaker
prior TCK-20260709 smoke test the ticket's own AC explicitly disqualifies):

**Method A — live dispatch against the one real precedent.** A `concern-investigator` subagent was
dispatched with an explicit instruction to attempt calling `Write` and `Edit` (both absent from its
declared `tools:` list) and report the literal, unfiltered result. The agent's actual returned
report states verbatim: *"Write/Edit aren't in my available function schema at all so there was
nothing to literally invoke"* — i.e. the undeclared tools were not offered as callable functions at
all, not merely refused after an attempted call. This is a materially different (and stronger)
signal than the prior TCK-20260709 evidence, which only showed the agent *chose* not to call
Edit/Write — this shows the tool definitions were never exposed to the model's function-calling
surface in the first place. (The agent separately misread the diagnostic framing as illegitimate
and refused to engage further — noted for completeness, but does not undermine the one concrete,
specific technical claim it made about its own available function schema.)

**Method B — direct binary schema extraction**, following the exact precedent the sibling ticket
`TCK-20260904-TEST-SCOPER-HANG-GUARD` used and disclosed as a legitimate substitution when live
network/doc access was blocked (WebFetch to `code.claude.com`/`docs.claude.com` both failed here
too — confirmed via `openssl s_client`, both resolve to a `Fortinet`/`Fortiguard SDNS Blocked Page`
certificate, i.e. this environment's network filter, not a real TLS failure; matches the exact
pattern CLAUDE.md's own CI-Triage section already documents). Reading the installed Claude Code
binary (`/home/u24desktop/.local/share/claude/versions/2.1.261`, an ELF executable bundling the
harness's own minified JS, readable via plain `grep -a`) directly surfaces:

- A literal recognized-frontmatter-key array including, verbatim:
  `"tools","disallowedTools","color","permissionMode","maxTurns","initialPrompt","memory",
  "background","isolation","observer",...` — `tools` and `disallowedTools` sit in the same
  literal key list as unambiguous real agent-definition fields (`color`, `permissionMode`,
  `maxTurns`), not in some unrelated schema. **`disallowedTools` is a real, recognized field name
  in this harness's own code, not a third-party-only concept with zero local grounding.**
- Real, active validation/enforcement code for the `agent()` spawn path: `"agent() opts.
  disallowedTools must be an array of non-empty tool-name strings (e.g. ['Bash', 'Write']); got
  ..."` and `"agent() opts.bashCommandClamp can bind nothing: the spawned agent's resolved tool
  pool has no {tool} (removed by this spawn's disallowedTools, **the agent definition's denies**,
  or absent from the session pool)."` — the phrase "the agent definition's denies" is the harness's
  own internal terminology for exactly what a `.claude/agents/*.md` frontmatter declares, and it is
  read into the same `resolvedTools` computation the spawn-time `disallowedTools` option feeds.
  Minified source: `Smn({allowedToolsCli,disallowedToolsCli,baseToolsCli,...})` → `rm(P)` →
  `toolPermissionContext` — a real function computing an actual permission/tool-availability object
  per spawn, not descriptive text.
- `"workflow agent(): disallowedTools mcp entry '${N}' covers this agent's declared frontmatter MCP
  server '${be.declaredSpelling}'"` — direct confirmation the harness's own error-message code
  refers to "this agent's declared frontmatter" when validating `disallowedTools` against an
  agent's own `.md` file, not only against workflow-script-supplied spawn options.

**Conclusion, evidence-backed, not assumed:** `tools:` **is enforced** at the harness level — a
tool not declared is not exposed to the model at all (Method A), and the harness computes a real
`resolvedTools` set per spawn that is checked and can refuse a spawn outright (Method B).
`disallowedTools:` **is a real, recognized field** in the harness's own schema, used today by the
`agent()` function's spawn-time options and validated with real error-handling — and the harness's
own language ("the agent definition's denies") indicates a `.claude/agents/*.md` frontmatter
`disallowedTools:` field would be read the same way `tools:` already is. This satisfies AC #1
("actual attempt... real harness behavior... directly observed and documented — the prior
TCK-20260709 smoke test does not satisfy this") for both fields, via a genuinely stronger method
than the disqualified prior evidence.

**Residual honesty caveat**: Method B's strings are clearest for the `agent()` function's runtime
spawn-option `disallowedTools` (used by `.claude/workflows/*.js` orchestrator code) and for
`tools:`'s effect on a dispatched subagent's function schema (Method A, direct). The literal
frontmatter-key array (`"tools","disallowedTools",...`) is strong but not 100%-conclusive proof
that `.claude/agents/*.md`'s own YAML parser specifically accepts a top-level `disallowedTools:`
key with identical semantics to `tools:` for every code path — no live test could exercise this
directly, because **agent definitions do not hot-reload mid-session** (already flagged in this
ticket's own Assumptions, and independently re-confirmed by the sibling
`TCK-20260904-TEST-SCOPER-HANG-GUARD`'s Step 1, which hit the same session-restart wall attempting
a different live-registration spike). Given the key literally appears in the harness's own
recognized-agent-field list, the safe, non-overclaiming reading is: **`disallowedTools:` is real
and enforced by the harness's spawn-time logic; whether to prefer it over `tools:` for Wave 1 is
moot, since `tools:` alone is suffient and already has a working precedent** — Wave 1 should use
`tools:` (allowlist), matching `concern-investigator`'s existing, working pattern, not introduce
`disallowedTools:` (denylist) as an unforced, unprecedented-in-`.md`-frontmatter risk.

### Usage-baseline dependency (AC #2)

`TCK-20260904-AGENT-TOOL-USAGE-BASELINE` is finalized: `tools/agent-monitoring/
agent_tool_usage_baseline.py` exists and runs cleanly (re-run live during this investigation,
2026-09-05), `tickets/done/TCK-20260904-AGENT-TOOL-USAGE-BASELINE.md` and
`stored_artifacts/TCK-20260904-AGENT-TOOL-USAGE-BASELINE/` both exist locally. **Not yet
git-committed** in this shared worktree (`git status` shows both as untracked `??` — same
uncommitted state as this ticket's own sibling batch). The dependency is functionally satisfied
(a real, runnable, non-stub usage table exists and was consulted); the outstanding git-commit step
is a repo-hygiene matter for whoever lands this batch, not a blocker to this ticket's own scope.

Live re-run of the script (not trusting the stored investigation.md's numbers, which are already
labeled stale-by-design) confirms the **single most important finding for this ticket**: of the 11
Wave 1 agents, **6 have zero historical tool-call rows anywhere in the corpus**:
`concern-investigator`, `mechanics-auditor`, `simulation-analyst`, `spec-document-reviewer`,
`world-debugger`, `world-render-reviewer`. Only 5 have real usage evidence: `doc-updater`,
`investigator`, `ticket-scoper`, `done-checker`, `test-scoper`.

### Per-agent candidate `tools:` scope (AC #3)

**Agents with real usage evidence** — candidate scope derived from actual historical calls, sized
per the ticket's own rule (smallest scope we're *confident* won't break things, not the theoretical
minimum). For all five, every observed tool's real `input_summary` example was inspected, not just
its count.

| Agent | Real tool-call rows | Candidate `tools:` scope | "Would deny" calls classified |
|---|---:|---|---|
| `doc-updater` | 5,206 | Read, Edit, Write, Bash, Agent, ListAgents, mcp__knowledge-search__search_docs, ToolSearch, TaskUpdate, Artifact, ScheduleWakeup, AskUserQuestion, SendMessage, Skill | **None.** Every one of the 14 distinct tools used has a real, role-consistent example (e.g. `Artifact`/`Skill` calls trace to `docs/brainstorm/*.html` pages, which are legitimately both live docs *and* published Artifacts per this project's own established pattern — not scope creep). Candidate scope = full observed set. |
| `investigator` | 11,799 | Read, Write, Edit, Bash, Agent, mcp__knowledge-search__search_docs, ToolSearch, Skill, Artifact, ListAgents, TaskUpdate, TaskCreate, WebSearch, AskUserQuestion, ScheduleWakeup, Monitor, TaskStop, WebFetch, SendFeedback | **`SendFeedback` (1 call)** — example is a genuine product-bug report ("Model repeats ListAgents-polling anti-pattern..."), a real, sanctioned meta-tool for flagging harness friction, not investigation-domain scope creep. Classified **legitimate-but-rare**; keep in scope. No other "would deny" candidates — all other tools trace to real investigation-pipeline mechanics (dispatch/monitor sub-searches, clarifying questions). |
| `ticket-scoper` | 3,044 | Bash, Read, Edit, Agent, Write, ToolSearch, mcp__knowledge-search__search_docs, ListAgents, AskUserQuestion, TaskCreate, ScheduleWakeup, SendMessage, TaskUpdate, Monitor, TaskStop | **None** excluded — same reasoning as above; `Edit` traces to real ticket-scoper output edits (e.g. `docs/agent-monitoring/README.md`), consistent with its documented role of producing/refining a ticket file plus flagging conflicts. |
| `done-checker` | 17,519 | Bash, Read, Edit, Agent, Write, mcp__knowledge-search__search_docs, TaskUpdate, ToolSearch, ScheduleWakeup, TaskCreate, AskUserQuestion, Artifact, Monitor, ListAgents, WebSearch, TaskOutput, Skill, SendMessage, TaskStop, WebFetch, SendUserFile, ReportFindings, mcp__knowledge-gateway__knowledge_context, mcp__knowledge-gateway__knowledge_status | **`mcp__knowledge-gateway__knowledge_context` / `knowledge_status` (1 call each)** — legitimate-but-rare (a real search-tool variant, not obviously wrong), but flagged **unclear-needs-review**: these are a *different* MCP search surface than the one `done-checker.md`'s own prose ever mentions (only `mcp__knowledge-search__search_docs` is referenced in its role file); 1-call evidence is too thin to confirm this is intended vs. an ad-hoc exploratory call. Recommend keeping in scope for Wave 1 (cost of excluding a legitimately-rare tool outweighs cost of including a harmless read-only MCP query tool) but flag for the post-rollout tightening pass. |
| `test-scoper` | 5,671 | Bash, Read, Agent, ToolSearch, Monitor, Write, SendMessage, ListAgents, mcp__knowledge-search__search_docs, ScheduleWakeup, TaskStop, AskUserQuestion, SendFeedback, TaskUpdate, Artifact, Skill, mcp__knowledge-gateway__knowledge_status, mcp__knowledge-search__search_health, SendUserFile | **`Edit` (147 calls)** — flagged **unclear-needs-review**, not silently included or silently dropped. `test-scoper.md`'s own documented role is "map changed files → tests, build/run the scoped pytest command, report pass/fail" — it never describes editing test files. The real examples (e.g. `tests/tools/test_agent_monitoring_manifest.py`) are consistent with a legitimate adjacent behavior (fixing a stale path/marker discovered while scoping) but are equally consistent with hand-orchestration sessions where "test-scoper" was used as a loose label for broader ad-hoc work rather than the literal narrow subagent role (the usage-baseline ticket's own investigation flags this exact `agent`-field-attribution ambiguity — `tools.jsonl`'s `agent` field does not distinguish a real subagent dispatch from hand-orchestration convention-labeling). **Recommendation, not a silent default: exclude `Edit` from test-scoper's Wave 1 candidate scope.** test-scoper's documented job is report-only; if it discovers something a test needs, the correct pipeline behavior is to report it as a gap for `implementer`/`done-checker` to act on, not self-edit. This keeps blast radius genuinely reduced rather than rubber-stamping the largest anomaly found in the whole dataset. |

**Agents with zero usage evidence** (`concern-investigator`, `mechanics-auditor`,
`simulation-analyst`, `spec-document-reviewer`, `world-debugger`, `world-render-reviewer`) — no
offline replay is possible for these; there is nothing to replay against. Candidate scope below is
derived from a static read of each agent's own `.claude/agents/*.md` prose (methodology,
documented data sources, described inputs/outputs) — explicitly **policy-derived, not
usage-derived**, and flagged as needing the first real observation window before any confidence
claim is made about it:

| Agent | Candidate `tools:` scope (policy-derived) | Basis |
|---|---|---|
| `concern-investigator` | Read, Grep, Glob, Bash, WebFetch, WebSearch, mcp__knowledge-search__search_docs (**unchanged** — already declared) | Zero real usage exists to re-verify against, despite the epic's own M3 language calling for "re-verify against M1's real data" for this agent specifically. Recommend keeping the existing declaration as-is (no evidence to expand or narrow it) rather than inventing a re-verification that has no real data behind it. |
| `mechanics-auditor` | Read, Grep, Glob, Bash, mcp__knowledge-search__search_docs | Its own file: reads Mechanics Bible chapters + source code, runs one static pre-check script via `Bash`, uses `docs/REGISTRY.yaml` lookups. No Write/Edit/Agent described anywhere in its methodology (produces a report only). |
| `spec-document-reviewer` | Read, Grep, Glob, mcp__knowledge-search__search_docs | Reads one spec doc, reviews for internal quality; no Bash/Write/Edit described. |
| `simulation-analyst` | Read, Grep, Glob, Bash | Reads `data/runs/{session_id}/`, `registration/`, `docs/mechanics/`; "lightweight single-pass," report-only. |
| `world-debugger` | Read, Grep, Glob, Bash | Traces the authoritative pipeline via source reads; report-only, no described mutation. |
| `world-render-reviewer` | Read | Narrowest of all 16: reads only a `Tier1Digest` JSON and conditionally one annotated PNG per its own explicit "only call Read... never a substitute" rule; no other tool appears anywhere in its file. |

## Mechanics / Engine Constraints

Not applicable. This is agent-infrastructure/governance tooling (`layer: ai`), not simulation
mechanics — no `docs/mechanics/` chapter or `docs/engine/` contract constrains `.claude/agents/*.md`
frontmatter shape or harness tool-dispatch behavior.

## Docs Requiring Update

- `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md`: Step 0's outcome ("Claude Code's own documentation was unreachable from this environment; only third-party sources describe tools:/disallowedTools: behavior") is now superseded by this ticket's direct binary-schema-extraction evidence — the epic doc's M3 section should be updated to reflect that both fields are now confirmed real and enforced (not merely third-party-documented), and that Wave 1 alone (not all three waves) is this ticket's own closable scope, with Wave 2/Wave 3 tracked as separate follow-on tickets gated on real elapsed observation windows.

The `docs/ai/codex_capability_matrix.md` doc (path: `docs/ai/codex_capability_matrix.md`, under
`docs/`) is not required to change for this ticket: it documents Codex's lifecycle hook events, an
entirely different provider/topic from Claude's per-agent `tools:`/`disallowedTools:` frontmatter
scoping, and this ticket does not modify or extend it.

The `agent-orchestration/hook-events.yaml` and `agent-orchestration/hook-surface-policy.yaml` files
(under the repo root, not `docs/`) are not required to change: they govern hook-event vocabulary
(`PreToolUse`/`PostToolUse`/`SubagentStop`), a different mechanism from per-agent tool-availability
frontmatter, which this ticket's Wave 1 rollout does not touch.

## Parity Ledger Overlap

None. Confirmed by direct grep of all `docs/parity_ledger/*.yaml` for agent-tools/frontmatter/
least-privilege terms — no existing entry tracks per-agent `tools:` frontmatter scoping, and this
is agent-infrastructure tooling outside the Parity Ledger's documented scope (Mechanics-Bible-vs-
code parity for simulation subsystems), matching the same conclusion the sibling
`TCK-20260904-AGENT-TOOL-USAGE-BASELINE` and `TCK-20260904-TEST-SCOPER-HANG-GUARD` investigations
both reached for this same batch of agent-infra tickets. No P0 entry is touched.

## Prior Work

- `stored_artifacts/TCK-20260904-AGENT-TOOL-USAGE-BASELINE/` — this ticket's own required input
  dependency; usage table re-verified live above (6/11 Wave 1 agents have zero rows — the single
  most consequential finding carried forward from that ticket).
- `tickets/done/TCK-20260904-TEST-SCOPER-HANG-GUARD.md` — confirmed via direct `git diff HEAD --
  .claude/agents/` that this sibling ticket touched **zero** `.claude/agents/*.md` files (only
  `test-scoper.md`'s prose section was *considered* and explicitly kept verbatim/untouched, per its
  own Files Changed section, independently corroborated by the live diff rather than trusted from
  its self-report). **No file-overlap risk from this sibling.** It also pioneered the
  binary-schema-extraction method (Step 1 of that ticket) this investigation reused for Step 0.
- `tickets/done/TCK-20260904-DOC-COVERAGE-REVERSE-CHECK.md` — **new coordination point, found by
  this investigation, not previously flagged anywhere**: this sibling ticket (same batch, already
  finalized locally but uncommitted) modified `.claude/agents/doc-updater.md`'s prose body (added a
  numbered self-check step, item 6 under "What to Do"), confirmed live via `git diff HEAD --
  .claude/agents/doc-updater.md`. This is a real, current, uncommitted change to one of this
  ticket's own Wave 1 target files. Whoever implements Wave 1 must add the `tools:` frontmatter
  field on top of that already-landed prose addition, not against a stale/reverted copy, and must
  not re-touch or revert that prose.
- `TCK-20260709-CONCERN-INVESTIGATOR-AGENT` — origin of the repo's sole `tools:` precedent and the
  weaker prior smoke-test evidence this ticket's own AC explicitly says does not satisfy Step 0.
- `tests/tools/test_concern_investigator_agent_definition.py` —
  `test_concern_investigator_agent_file_exists_and_has_frontmatter` is the exact pattern AC #4
  requires parametrizing across every landed Wave 1 agent file (parse frontmatter → assert `tools:`
  present → assert a per-agent disallowed-tools list is absent from the declared set).

## Risks and Open Questions

- **Wave 1 itself is evidence-incomplete by construction**: 6 of its 11 agents have zero historical
  usage to validate a candidate scope against. This is not a defect in this investigation — it is a
  genuine, unavoidable gap (flagged loudly by the usage-baseline ticket's own investigation too).
  The policy-derived candidate scopes above for those 6 agents are a reasonable starting allowlist,
  not a validated one; they are the agents most likely to need the post-rollout tightening pass the
  epic's own acceptance signal already anticipates ("A later tightening pass... uses real
  post-rollout evidence").
- **`test-scoper`'s `Edit` exclusion is a real, consequential judgment call, not a formality.** 147
  historical calls is not a trivial anomaly — excluding it is the single largest behavior change
  Wave 1 proposes. If test-scoper genuinely needs to fix a stale test path/marker as part of its
  normal job (not hand-orchestration drift), excluding `Edit` will surface as a real, visible
  permission-denial during the observation window — which is exactly the kind of signal Wave 1's
  observation window exists to catch, not something to silently avoid by including `Edit`
  preemptively. Recommend Plan phase confirm this exclusion explicitly rather than defaulting either way.
- **Open question requiring an explicit decision, not an assumption (central to this ticket's own
  framing)**: is landing only Wave 1 — with Wave 2 (`architecture-reviewer`, `security-reviewer`,
  `planner`) and Wave 3 (`implementer`, `parity-updater`) explicitly deferred to separate follow-on
  tickets gated on real elapsed observation time — a legitimate, complete closure of this ticket's
  own Acceptance Criteria?

  **Resolved here, with direct evidence, not left open:** **Yes.** Four independent lines of
  evidence converge on this:
  1. This ticket's own `## Acceptance Criteria` section (re-read closely, verbatim) lists exactly
     four checkboxes: Step 0 verification, the usage-baseline dependency, a per-Wave-1-agent
     candidate scope with 5-way taxonomy classification, and "Wave 1... landed... with tests and a
     revert command." **None of the four mentions Wave 2 or Wave 3 landing.**
  2. The epic doc's own M3 section explicitly frames the wave gate as needing **real elapsed
     calendar time**: "each wave gated on the previous wave's observation window clearing with no
     unresolved permission regression." A hand-orchestrated single session cannot manufacture real
     elapsed production usage between Wave 1 landing and Wave 2 starting — attempting Wave 2/3 now
     would either silently skip the gate (defeating the entire point of the wave design, which
     exists specifically to avoid exactly the "aggressive allowlist → break workflows → widen
     reactively" failure mode the epic's own Sizing rule warns against) or fabricate a fake
     observation window, which would be dishonest record-keeping.
  3. This ticket's own `## Assumptions / Open Questions` section already states, as a pre-existing
     assumption (not something this investigation is inventing): "The harness does not hot-reload
     `.claude/agents/` mid-session (requires session restart) — wave observation windows must
     account for this." This is a structural acknowledgment, written into the ticket at scoping
     time, that waves are inherently session-spanning.
  4. The epic doc's own Acceptance signal for M3 ("All three waves complete... each wave's rollback
     having been documented as trivial before that wave went live") describes the **epic
     milestone's** cumulative completion criterion, not a single child ticket's. M1's usage-baseline
     ticket and this ticket are both explicitly scoped as individual installments feeding that
     milestone, not required to single-handedly satisfy it.

  **Concrete recommendation for Plan/Implement**: land Step 0 (documented above), the full
  per-agent candidate-scope table (above), and Wave 1's `tools:` frontmatter rollout (11 files) with
  its tests and a documented revert command, in this ticket. Do **not** attempt Wave 2 or Wave 3 in
  any reduced form. Record the deferral explicitly in this ticket's own Completion Summary,
  including that Wave 2 and Wave 3 require their own future tickets opened only after Wave 1's real
  observation window (spanning genuine elapsed calendar time with live agent-monitoring data) shows
  zero permission regressions — this is itself the ticket's "no material gap left unstated"
  obligation, not an optional footnote.
- **Revert mechanism is genuinely trivial, as the epic requires it to be documented as before each
  wave starts**: each Wave 1 change is a single added `tools:` line in one file's frontmatter block;
  reverting any one agent is `git checkout HEAD -- .claude/agents/<name>.md` (or, pre-commit,
  discarding the single-line frontmatter diff), with zero coupling between the 11 files' individual
  reverts. No shared state, migration, or cross-file dependency to unwind.

## Anti-Drift Hazards

- **Do not silently widen scope into Wave 2/Wave 3 "since we're already in here."** The whole
  design rationale for wave-gating is real elapsed observation time between waves — a single
  session cannot supply that, regardless of how mechanically easy it would be to also touch
  `architecture-reviewer.md`/`planner.md`/`implementer.md`'s frontmatter in the same sitting.
- **Do not narrow `Bash` command-level permissions as part of this ticket.** M3 scopes which
  top-level *tools* an agent's frontmatter grants (`tools:`), not which shell command patterns Bash
  itself may run — that remains `permissions.allow` in `.claude/settings.json`, a separate,
  untouched mechanism. Conflating the two would silently expand this ticket's blast radius beyond
  its own Out-of-Scope line ("Any change to agent files beyond tools:/disallowedTools frontmatter
  scoping").
- **Do not re-touch `doc-updater.md`'s prose body.** `TCK-20260904-DOC-COVERAGE-REVERSE-CHECK`
  already added its self-check step there (uncommitted but finalized); Wave 1's change to this file
  is additive frontmatter only.
- **Do not treat the 6 zero-usage agents' policy-derived candidate scopes as validated.** They carry
  materially weaker confidence than the 5 usage-backed agents and are the most likely candidates for
  the epic's own post-rollout tightening pass — say so explicitly in Plan/Implement, don't present
  them with the same confidence as the usage-derived five.
- **Do not silently include `test-scoper`'s historical `Edit` calls in its Wave 1 scope** just
  because 147 is a large number — a large historical count is not automatic justification (the
  epic's own text: "Historical usage alone is not sufficient justification for keeping a
  capability"). This is the one case in this investigation where the "smallest confident scope"
  rule and "don't flag legitimate-but-rare calls" rule genuinely pull in different directions;
  resolve it explicitly, don't let it default silently either way.
