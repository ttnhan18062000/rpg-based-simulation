---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-CODEX-CAPABILITY-MATRIX
artifact_type: investigation
tags: [ai, workflows, process-improvement]
---

# Investigation — TCK-20260721-CODEX-CAPABILITY-MATRIX

## Current Behavior

### Where the "10 claimed hooks" citation originates

`docs/plans/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md:108` is the sole origin of the claim:

> "Codex supports ten documented lifecycle hooks through trusted project `.codex/` configuration: `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `PostCompact`, `UserPromptSubmit`, `SubagentStop`, `Stop`, `SessionStart`, and `SubagentStart`. This was verified against the current [Codex Hooks documentation](https://learn.chatgpt.com/docs/hooks.md) on 2026-07-20."

No other doc in the repo independently re-derives this list; the handoff doc (`idea_provider_agnostic_agent_orchestration_ticket_handoff_codex.md:77-80`) and the epic ticket both simply repeat "the plan lists all ten documented events; the capability ticket must re-verify them at execution time" without adding new evidence. This confirms the ticket's own framing: the list is currently a single, single-day-old, unverified-at-execution-time citation, not something independently corroborated in-repo before this investigation.

### What this investigation found when re-verifying against documentation

This machine has a locally cached copy of the official Codex manual at `/tmp/openai-docs-cache/codex-manual.md` (799,577 bytes, 16,525 lines; `mtime` 2026-07-20 16:04, one day before this investigation ran). Every section is explicitly source-tagged, e.g. line 9146: `Source: [Hooks](https://learn.chatgpt.com/docs/hooks.md)` — the **exact same URL** cited in the plan doc. This is not a repo artifact (it lives outside git, under `/tmp`), so it is environment-local, not durable, and was not created by this ticket.

The manual's `### Hooks` section (lines 9144-9567) documents **all ten** claimed events, corroborating the plan's citation rather than contradicting it:

- Line 9163-9166: "`PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `PostCompact`, `UserPromptSubmit`, `SubagentStop`, and `Stop` run at turn scope. `SessionStart` and `SubagentStart` run at thread or subagent-start scope." — all 10 names appear, matching the plan's list exactly, including capitalization.
- Config-shape example (lines 9227-9302) shows working `hooks.json` entries for `SessionStart`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `UserPromptSubmit`, and `Stop`.
- A matcher-support table (lines 9443-9454) enumerates matcher semantics per event (tool name for `PreToolUse`/`PostToolUse`/`PermissionRequest`; compaction trigger `manual|auto` for `PreCompact`/`PostCompact`; start-source `startup|resume|clear|compact` for `SessionStart`; subagent type for `SubagentStart`/`SubagentStop`; **no matcher support** for `UserPromptSubmit` and `Stop`).
- A common-input-fields table (lines 9494-9510) documents `session_id`, `transcript_path`, `cwd`, `hook_event_name`, `model`, `turn_id` (turn-scoped only), and `permission_mode` (listed for `SessionStart`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `UserPromptSubmit`, `SubagentStart`, `SubagentStop`, `Stop` — 8 of 10; notably *not* listed for `PreCompact`/`PostCompact`).
- A common-output-fields table (lines 9517-9549) documents which of `continue`/`stopReason`/`systemMessage`/`suppressOutput` each event actually honors, and explicitly flags exceptions (`PreToolUse`/`PermissionRequest` reject `continue`/`stopReason`/`suppressOutput`; sending them makes Codex mark the hook run failed).
- Project-trust behavior is documented separately at line 3170: "If the project is untrusted, Codex ignores project `.codex/` layers, including `.codex/config.toml`, project-local hooks, and project-local rules. User and system layers remain separate and still load," and repeated at line 9196-9198 specifically for hooks.
- Role/delegation ("Agent roles (`[agents]` in `config.toml`)" heading, line 3219) and skills/config surfaces ("Build skills" line 8395, "Roles and workspace permissions" line 12976, "Skill controls" line 13051, "Skills & Plugins" line 15450) are also covered in the same cached manual, giving the Plan/Implement phase a grounded source for the matrix's other required rows (capabilities, trust, roles, skills) beyond the ten hooks that were this investigation's specific focus.

**This materially changes the risk read stated in the ticket's own Assumptions.** The initial hypothesis worth flagging going in was that the "10 hooks" list might be a citation error — Claude Code's own hook taxonomy (confirmed live in this repo's `.claude/settings.json:54-119`, which wires exactly `PreToolUse` and `PostToolUse`) uses several of the same event names (`PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`, `PreCompact`, `UserPromptSubmit`, `SessionStart` are also real Claude Code hook events), which could indicate the plan conflated the two providers' taxonomies. The cached official manual resolves this: Codex's hook framework genuinely uses this near-identical naming by design, and the plan's citation is corroborated, not contradicted, by the best available grounding source in this environment.

### Live-environment fixture-experiment feasibility (resolves an open Assumption)

The ticket's own Assumptions/Open Questions section states Codex fixture experiments "may need Codex CLI/API access not yet confirmed present in this environment." This is now resolved: Codex CLI **is** installed and authenticated on this machine.

- `which codex` → `/home/u24desktop/.local/bin/codex`
- `codex --version` → `codex-cli 0.144.6`
- `~/.codex/` exists with `auth.json`, `config.toml`, `sessions/`, `logs_2.sqlite`, etc. — a real, live-used installation, not a stub.
- `codex features list` (read-only diagnostic subcommand) reports: `hooks   stable   true` — i.e. the installed CLI build reports the hooks feature as stable and enabled. This is genuine **direct-experiment evidence** (not documentation citation) that hooks are a live, enabled capability of this specific installed Codex build — exactly the kind of evidence AC3 asks the matrix to distinguish from "documented in official docs."
- No project-local `.codex/` directory exists in this repo (`ls .codex` → not found), confirming the containment rule is currently intact — nothing in this repo has enabled trusted project-local Codex hooks.

What this investigation did **not** do, and left open for Plan/Implement: actually trigger a hook (e.g. write an isolated `hooks.json` outside this repo, run `codex exec` against a throwaway fixture project, and capture the real `stdin` JSON payload for one event). That is implementation/fixture-construction work, not fact-finding, it would consume real API usage under the user's authenticated Codex account, and the ticket's own framing asks this be flagged as a Plan-phase decision rather than performed here. `codex features list` and `codex --version`/`codex doctor` are read-only informational subcommands and do not have this cost; they were run as they are squarely within "read-only/fact-gathering."

### WebFetch/WebSearch feasibility from this environment

- **WebSearch is feasible.** A query for "Codex CLI lifecycle hooks documentation" returned indexed results whose titles/snippets corroborate the manual: `developers.openai.com/codex/hooks`, `learn.chatgpt.com/docs/hooks`, `deepwiki.com/openai/codex/3.11-hooks-system`, and third-party write-ups, with a snippet independently naming `SessionStart, PreToolUse, PermissionRequest, PostToolUse, UserPromptSubmit, SubagentStart, SubagentStop, Stop` as "key lifecycle events."
- **WebFetch is NOT feasible from this sandbox.** Three attempts (`https://learn.chatgpt.com/docs/hooks.md`, `https://developers.openai.com/codex/hooks`, and an unrelated third-party URL as a control) all failed identically with `self signed certificate` — this is a sandbox-wide TLS-interception failure, not a URL-specific issue. Live re-fetch of the primary source to confirm it hasn't changed since the plan's 2026-07-20 citation or since this cache's 2026-07-20 16:04 snapshot is not currently possible from inside this environment.

## Mechanics / Engine Constraints

Not applicable. This ticket concerns third-party AI-provider (Codex) capability verification for the repo's own dev-tooling/agent-orchestration system, not simulation mechanics. No chapter of `docs/mechanics/` or contract in `docs/engine/` constrains this work.

## Parity Ledger Overlap

None. Searched all files under `docs/parity_ledger/*.yaml` for `codex`, `lifecycle hook`, `PreToolUse`, and `PermissionRequest` — no matches. This confirms the ticket's own "likely None" expectation. No `docs/parity_ledger/` entry needs updating as a result of this investigation.

**Note on the ticket's own "Related Code Areas":** `src/engine/capability.py`, `tests/unit/engine/test_capability_registry.py`, and `tests/architecture/test_capability_references.py` were read in full. They implement and test `docs/engine/capability_registry.yaml` — the **simulation engine's own** OFFICIAL/SUPPORTED/EXPERIMENTAL/UNSUPPORTED capability matrix (combat resolution, world generation, crafting, etc. — see `stored_artifacts/TCK-20260619-E-CAP-REGISTRY/investigation.md`). This is a different "capability matrix" than the one this ticket is about (Codex's agent-provider capabilities). The name collision is coincidental — likely the term "capability matrix" pattern-matched during epic/child-ticket generation. No code, test, or doc under this area was written to or needs modification by this ticket; flagging so Plan/Implement does not mistake `src/engine/capability.py` as an integration point.

## Prior Work

- **`TCK-20260721-AGENTS-DIR-DISPOSITION`** (done, sibling child of the same parent epic, `tickets/done/TCK-20260721-AGENTS-DIR-DISPOSITION.md` + `stored_artifacts/TCK-20260721-AGENTS-DIR-DISPOSITION/`) — the only completed precedent for this containment pattern. Its deliverable was a single new decision-record doc (`docs/ai/agents_dir_disposition.md`) plus two isolated test fixtures, with zero production file changes. Its investigation.md demonstrates the expected evidence density (exact file:line citations, explicit "ran the test, N passed" verification, named prior tickets as evidence for "abandoned not merely deferred" claims). This ticket's own investigation and eventual matrix should match that evidence bar.
- **`TCK-20260619-E-CAP-REGISTRY`** (done) — built the *simulation engine's* capability registry pattern (YAML + thin Python reader + architecture-guard uniqueness test). Structurally the closest in-repo precedent for "a machine-readable OFFICIAL/SUPPORTED/EXPERIMENTAL/UNSUPPORTED matrix with a reader," but for a different domain (engine features, not a third-party AI provider). Worth considering as a *format* precedent for the Plan phase (e.g. whether the Codex matrix should also get a thin YAML+reader shape), while being careful not to conflate the two domains (see note above).
- **`idea_provider_agnostic_agent_orchestration_finding_01_claude.md`** (2026-07-20) — established the evidentiary bar for this discovery batch: cite exact file:line, name the specific currently-passing test, and state explicitly that a claim is "not a request for confirmation... evidence." This ticket's own citation work followed the same discipline.
- **`tickets/todos/provider-agnostic-discovery/SEQUENCE.md`** — confirms this ticket (#3 in sequence) has no dependency on sibling children #2 (`AGENTS-DIR-DISPOSITION`, done) or #4 (`MONITORING-WRITER-DECISION`), and is itself a dependency of #5 (`ORCHESTRATION-CONTRACT-ADR`) and #6 (`CODEX-REPLAY-PROOF`) — nothing in those siblings' work changes this ticket's scope.
- No prior ticket in this repo has verified a third-party AI provider's capabilities against live external docs (confirmed via `mcp__knowledge-search__search_docs` and `graphify query`, both of which surfaced only the unrelated `src/engine/capability.py` domain) — citation/evidence conventions for this exact kind of external-product verification are being established fresh by this ticket, as the ticket itself anticipated.

## Risks and Open Questions

- **Cache durability (open, blocks nothing but should inform Plan):** `/tmp/openai-docs-cache/codex-manual.md` is the strongest available grounding source, but it lives outside the repo and outside `/tmp`'s guaranteed lifetime — it could be absent in a future session (container restart, cache eviction). If the matrix artifact cites it as "official documentation, verified <date>," the Plan/Implement phase should either (a) quote/excerpt the load-bearing passages directly into the durable matrix doc (so the citation survives even if the cache disappears), or (b) treat the cache as corroborating-only and cite the live URL as the primary source, accepting that this environment currently cannot re-fetch it directly (WebFetch is blocked; see below).
- **WebFetch is blocked in this sandbox** (self-signed certificate error on every URL tried, including a control URL unrelated to Codex) — the Plan phase should not assume direct live re-verification of `https://learn.chatgpt.com/docs/hooks.md` is possible without a different tool path (e.g., an MCP fetch tool, a different agent/environment, or accepting the cache + WebSearch as sufficient grounding). WebSearch does work and returned corroborating third-party summaries.
- **AC3's "fixture-confirmed by direct experiment" is only partially satisfied by this investigation.** `codex features list` is real, direct, live evidence that this installed build has hooks enabled — but it is a feature-flag check, not a payload/matcher/timing fixture experiment (i.e., it does not itself prove the exact JSON shape delivered to a hook script matches the documented tables). A true fixture experiment — write an isolated `hooks.json` outside this repo, run `codex exec` with a trivial prompt, capture the real `stdin` payload for at least one event (e.g. `PreToolUse`) — remains undone and is recommended as explicit Plan-phase scope, consistent with the ticket's own framing that Investigate should not perform it.
- **Matrix scope is broader than the 10 hooks this investigation focused on.** The ticket's Scope/AC1 also requires rows for "current Codex capabilities, project trust behavior... role/delegation model, skills/configuration surfaces." The cached manual has sections for all of these (see Current Behavior above), but this investigation did not deep-read them line-by-line the way it did for Hooks — Plan/Implement will need a further, more focused read of those sections before the matrix doc can be considered complete against AC1's full enumeration, not just the hooks AC (AC2).
- **No decision yet on where the matrix artifact should live.** The sibling `AGENTS-DIR-DISPOSITION` ticket created `docs/ai/agents_dir_disposition.md`. This ticket's AC explicitly requires "a standalone Codex capability-matrix artifact, not folded into the existing dated (2026-07-20) plan citation" — a natural, consistent location would be `docs/ai/codex_capability_matrix.md`, but naming/placement is a Plan-phase decision, not resolved here.

## Anti-Drift Hazards

- Do not modify `src/engine/capability.py`, `docs/engine/capability_registry.yaml`, or their tests as part of this ticket — they belong to the simulation engine's own, unrelated capability-matrix system (see Parity Ledger Overlap note above). The "Related Code Areas" name collision is coincidental.
- Do not create, modify, or trust any `.codex/` directory inside this repository — the containment rule (`SEQUENCE.md`, this ticket's own Scope) forbids production Codex wiring; confirmed no such directory currently exists here. Any fixture experiment for AC3 must run in an isolated location outside this repo's trust boundary (e.g. a throwaway `/tmp` project), never by adding `.codex/hooks.json` here.
- Do not touch `.claude/settings.json`, any `.claude/workflows/*.js`, or `tools/agent-monitoring/*` — those are the "production Claude workflows/hooks/monitoring writers" the containment rule protects, and are also in-flight/owned by sibling ticket `TCK-20260721-MONITORING-WRITER-DECISION`.
- Do not let the matrix conflate "documented in official docs" with "fixture-confirmed by direct experiment" — AC3 requires the matrix to distinguish these explicitly per entry; `codex features list`'s hooks=true finding is direct-experiment-grade for capability-presence but not for per-event payload/matcher/timing correctness.
- Do not assume the `/tmp/openai-docs-cache/` file will still exist in a later session — cite specific excerpted content in the durable matrix doc rather than only a path reference to a non-repo temp file.
- Do not open or scope a provider-runtime implementation ticket from this work — blocked until all five discovery outputs across the epic are complete and approved (per parent epic `TCK-20260721-PROVIDER-AGNOSTIC-EPIC` and `SEQUENCE.md`).
