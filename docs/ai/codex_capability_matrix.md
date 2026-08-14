---
status: active
layer: ai
authority: P1
audience: developer
tags: [ai, workflows, process-improvement]
---

# Codex Capability Matrix — TCK-20260721-CODEX-CAPABILITY-MATRIX

A standalone re-verification of Codex's current capabilities, project trust behavior, lifecycle hooks, role/delegation model, and skills/configuration surfaces, performed independently of — not folded into — `docs/plans/archive/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md:109` (archived — shipped)'s 2026-07-20 hook-list citation. Every entry below carries its own **verification date of 2026-07-21**, sourced fresh at this ticket's execution time, not inherited from the plan doc.

Primary source for every excerpt below: `/tmp/openai-docs-cache/codex-manual.md` (16,525 lines, `mtime` 2026-07-20 16:04), a locally cached copy of the official Codex manual whose sections are individually source-tagged with their `learn.chatgpt.com`/`developers.openai.com` origin URLs. That cache lives outside this repo and outside git, under `/tmp`, and is **not guaranteed to persist** across sessions — so the load-bearing text is excerpted directly into this doc body below, not merely cited by path. Line numbers cited (e.g. "manual line 9163") refer to that cache file's line numbers as of this ticket's execution.

## 1. Lifecycle Hook Events

All ten previously-claimed hook events are individually marked **VERIFIED** against the cached manual's `### Hooks` section (manual lines 9144-9567, source-tagged `Source: [Hooks](https://learn.chatgpt.com/docs/hooks.md)` at line 9146 — the same URL the plan cited on 2026-07-20).

| Event | Status | Scope | Matcher support | Common input fields | Output fields honored | Source |
|---|---|---|---|---|---|---|
| `PreToolUse` | VERIFIED | turn | tool name (`Bash`, `apply_patch`\*, MCP tool names) | `session_id`, `transcript_path`, `cwd`, `hook_event_name`, `model`, `turn_id`, `permission_mode` | `systemMessage` only — `continue`/`stopReason`/`suppressOutput` rejected (hook run marked failed if returned) | manual lines 9163-9166, 9443-9454, 9494-9510, 9517-9549 |
| `PermissionRequest` | VERIFIED | turn | tool name (`Bash`, `apply_patch`\*, MCP tool names) | same 7 fields as above | `systemMessage` only — same rejection rule as `PreToolUse` | manual lines 9163-9166, 9443-9454, 9494-9510, 9517-9549 |
| `PostToolUse` | VERIFIED | turn | tool name | same 7 fields as above | `systemMessage`, `continue: false`, `stopReason` (`suppressOutput` parsed but not implemented) | manual lines 9163-9166, 9443-9454, 9494-9510, 9517-9549 |
| `PreCompact` | VERIFIED | turn | compaction trigger (`manual`\|`auto`) | `session_id`, `transcript_path`, `cwd`, `hook_event_name`, `model`, `turn_id` — **no `permission_mode`** | full shared shape (`continue`/`stopReason`/`systemMessage`/`suppressOutput`) | manual lines 9163-9166, 9443-9454, 9494-9510, 9517-9549 |
| `PostCompact` | VERIFIED | turn | compaction trigger (`manual`\|`auto`) | same as `PreCompact` — **no `permission_mode`** | full shared shape | manual lines 9163-9166, 9443-9454, 9494-9510, 9517-9549 |
| `UserPromptSubmit` | VERIFIED | turn | not supported (matcher ignored) | same 7 fields as `PreToolUse` | full shared shape | manual lines 9163-9166, 9443-9454, 9494-9510, 9517-9549 |
| `SubagentStop` | VERIFIED | turn | subagent type | same 7 fields as `PreToolUse` | full shared shape | manual lines 9163-9166, 9443-9454, 9494-9510, 9517-9549 |
| `Stop` | VERIFIED | turn | not supported (matcher ignored) | same 7 fields as `PreToolUse` | full shared shape | manual lines 9163-9166, 9443-9454, 9494-9510, 9517-9549 |
| `SessionStart` | VERIFIED | thread / subagent-start | start source (`startup`\|`resume`\|`clear`\|`compact`) | same 7 fields as `PreToolUse` | full shared shape | manual lines 9163-9166, 9443-9454, 9494-9510, 9517-9549 |
| `SubagentStart` | VERIFIED | thread / subagent-start | subagent type | same 7 fields as `PreToolUse` | accepts same shape for `systemMessage`/context, but **`continue: false` does not stop the subagent** | manual lines 9163-9166, 9443-9454, 9494-9510, 9517-9549, 9519-9522 |

\*For `apply_patch`, matcher values can also use `Edit` or `Write` (manual line 9456).

### Excerpted source text (manual lines 9144-9567, `### Hooks`)

> Hooks are an extensibility framework for Codex. They allow you to inject your own scripts into the agentic loop... Matching hooks from multiple files all run. Multiple matching command hooks for the same event are launched concurrently, so one hook can't prevent another matching hook from starting. Non-managed command hooks must be reviewed and trusted before they run.
>
> `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `PostCompact`, `UserPromptSubmit`, `SubagentStop`, and `Stop` run at turn scope. `SessionStart` and `SubagentStart` run at thread or subagent-start scope. (manual lines 9163-9166)

Matcher-support table (manual lines 9443-9454, verbatim):

| Event | What `matcher` filters | Notes |
|---|---|---|
| `PermissionRequest` | tool name | Support includes `Bash`, `apply_patch`\*, and MCP tool names |
| `PostToolUse` | tool name | See Tool coverage |
| `PostCompact` | compaction trigger | Values are `manual` or `auto` |
| `PreCompact` | compaction trigger | Values are `manual` or `auto` |
| `PreToolUse` | tool name | See Tool coverage |
| `SessionStart` | start source | Values are `startup`, `resume`, `clear`, and `compact` |
| `SubagentStart` | subagent type | Values depend on the subagent that starts |
| `SubagentStop` | subagent type | Values depend on the subagent that stops |
| `UserPromptSubmit` | not supported | Any configured `matcher` is ignored for this event |
| `Stop` | not supported | Any configured `matcher` is ignored for this event |

Common-input-fields excerpt (manual lines 9490-9510, verbatim):

> Every command hook receives one JSON object on `stdin`. These are the shared fields you will usually use: `session_id` (string, current Codex session id; subagent hooks use the parent session id), `transcript_path` (string|null), `cwd` (string), `hook_event_name` (string), `model` (string, Codex-specific extension). Turn-scoped hooks list `turn_id` as a Codex-specific extension in their event-specific tables. `SessionStart`, `PreToolUse`, `PermissionRequest`, `PostToolUse`, `UserPromptSubmit`, `SubagentStart`, `SubagentStop`, and `Stop` also include `permission_mode`, which describes the current permission mode as `default`, `acceptEdits`, `plan`, `dontAsk`, or `bypassPermissions`.

This is the field-coverage asymmetry: `permission_mode` is listed for 8 of 10 events but **not** `PreCompact`/`PostCompact` — those two are compaction-scoped and don't carry a live permission-mode context at the point they fire.

Common-output-fields excerpt (manual lines 9517-9549, verbatim):

> `SessionStart`, `PreCompact`, `PostCompact`, `UserPromptSubmit`, `SubagentStop`, and `Stop` support these shared JSON fields (`continue`, `stopReason`, `systemMessage`, `suppressOutput`). `SubagentStart` accepts the same shape for `systemMessage` and hook-specific context, but `continue: false` doesn't stop the subagent... `PreToolUse` and `PermissionRequest` support `systemMessage`, but `continue`, `stopReason`, and `suppressOutput` aren't currently supported for those events. If a `PreToolUse` hook returns one of those unsupported fields, Codex marks that hook run as failed, reports the error, and continues the tool call. `PostToolUse` supports `systemMessage`, `continue: false`, and `stopReason`. `suppressOutput` is parsed but not currently supported for that event.

This is the second field-coverage asymmetry: `PreToolUse`/`PermissionRequest` reject `continue`/`stopReason`/`suppressOutput` — sending them causes Codex to mark the hook run failed, distinct from every other event's more permissive output contract.

Project-trust gating for hooks specifically (manual lines 9196-9198, verbatim):

> Project-local hooks load only when the project `.codex/` layer is trusted. In untrusted projects, Codex still loads user and system hooks from their own active config layers.

## 2. Current Codex Capabilities

Verification date: 2026-07-21. Source: manual lines 17-149 (`## Surfaces and experiences` → `### Feature Maturity`, `### Pricing`, `### Quickstart`), source-tagged at line 25 (`Source: [Feature Maturity](https://learn.chatgpt.com/docs/feature-maturity.md)`).

Feature-maturity ladder (manual lines 29-34, verbatim):

| Maturity | What it means | Guidance |
|---|---|---|
| Under development | Not ready for use. | Don't use. |
| Experimental | Unstable and OpenAI may remove or change it. | Use at your own risk. |
| Beta | Ready for broad testing; complete in most respects, but some aspects may change based on user feedback. | OK for most evaluation and pilots; expect small changes. |
| Stable | Fully supported, documented, and ready for broad use; behavior and configuration remain consistent over time. | Safe for production use; removals typically go through a deprecation process. |

Hooks are not individually labeled against this ladder in the manual's Hooks section itself, but the fixture-confirmed evidence in §4 below (`codex features list` → `hooks stable true`) places the hooks feature at **Stable** maturity on this installed build.

Surfaces: Codex CLI, IDE extension, ChatGPT desktop app, ChatGPT web (Work mode), and Codex cloud (manual lines 8-16, 61, 8403). This ticket's own environment uses Codex CLI only (`codex-cli 0.144.6`, confirmed via `codex --version` — see §4).

## 3. Project Trust Behavior

Verification date: 2026-07-21. Two source locations, both cited:

Manual line 3170 (`#### Project config files (.codex/config.toml)`), verbatim:

> For security, Codex loads project-scoped config files only when the project is trusted. If the project is untrusted, Codex ignores project `.codex/` layers, including `.codex/config.toml`, project-local hooks, and project-local rules. User and system layers remain separate and still load.

Manual lines 9196-9198 (repeated specifically for hooks within the `### Hooks` section — see §1 above), verbatim:

> Project-local hooks load only when the project `.codex/` layer is trusted. In untrusted projects, Codex still loads user and system hooks from their own active config layers.

Both citations agree: an untrusted project's `.codex/` layer (config, hooks, rules) is ignored wholesale; user- and system-level Codex layers are independent of any given project's trust state and always load. This repo currently has **no** `.codex/` directory (confirmed absent during investigation), so the containment rule this ticket's Scope Guards enforce is currently intact — nothing in this repo can be trusted into running project-local Codex hooks because there is no project-local Codex config to trust in the first place.

## 4. Role/Delegation Model

Verification date: 2026-07-21. Sources:

- Manual line 3219, `#### Agent roles ([agents] in config.toml)`: "For subagent role configuration (`[agents]` in `config.toml`), see [Subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)." — this section is a pointer/stub in the cached manual rather than inline detail; the full subagent-role schema lives at the linked `agent-configuration/subagents` doc, which is outside this cache and was not independently re-fetched (WebFetch is blocked in this sandbox — see §6).
- Manual lines 12976-13007, `### Roles and workspace permissions` (`Source: [Roles and workspace permissions](https://learn.chatgpt.com/docs/enterprise/roles-and-workspace-permissions.md)`): documents six administration control boundaries — ChatGPT workspace, Local clients, Codex cloud, Platform API, Plugins, Connected systems — each independently gating access; "A request must pass every boundary that applies to it." This is workspace/administration-level role control, distinct from the in-session `[agents]` subagent-role config referenced above.

Status: **VERIFIED for existence and high-level shape** (the `[agents]` config key and the six-boundary administration model both corroborated directly in the cached manual); **UNVERIFIED for full field-level subagent-role schema**, since that detail lives behind a link this environment could not re-fetch.

## 5. Skills/Configuration Surfaces

Verification date: 2026-07-21. Three sources, all corroborating a consistent model:

- Manual lines 8395-8454, `### Build skills` (`Source: [Build skills](https://learn.chatgpt.com/docs/build-skills.md)`): a skill is a directory with a `SKILL.md` file (`name` + `description` required), read from repository/user/admin/system locations; repositories are scanned via `.agents/skills` from cwd up to the repo root. Codex uses **progressive disclosure**: only name/description/path are loaded upfront (capped at ~2% of context window or 8,000 characters), full `SKILL.md` instructions load only when a skill is selected. Activation is explicit (`/skills`, `$`-mention) or implicit (description-match).
- Manual lines 13051-13098, `### Skill controls` (`Source: [Skill controls](https://learn.chatgpt.com/docs/enterprise/skills.md)`): three distinct distribution/administration paths — ChatGPT workspace Skill, local filesystem skill, and Plugin-packaged skill — each with a separate lifecycle/access-control boundary; moving a skill between these does not transfer ownership or authorization.
- Manual lines 15450-15507, `### Skills & Plugins` (`Source: [Skills & Plugins](https://learn.chatgpt.com/docs/skills-and-plugins.md)`): a skill packages instructions + resources for a repeatable task; a plugin is an installable bundle that can include skills, connectors (MCP-backed), or both. "ChatGPT supports `@` mentions, while Codex supports `$` mentions for skills."

Status: **VERIFIED**. Note this repo's `.agents/skills/` directory (see `docs/ai/agents_dir_disposition.md`) is the concrete in-repo analog of the "repository" skill-discovery location the manual describes at line ~8454 — corroborating, not contradicting, the disposition doc's classification work.

## 6. Payload/Fixture Gaps

Verification date: 2026-07-21. Two explicitly distinguished evidence classes, per AC3:

**Documented in official docs (documentation-citation grade):** the field tables in §1 above (matcher support, common input fields, common output fields) — sourced from a documentation-review pass over the cached manual only. These have not been independently confirmed against a live hook invocation's actual `stdin` payload in this environment.

**Fixture-confirmed by direct experiment (direct-experiment grade):** during investigation, `codex features list` — a read-only CLI diagnostic subcommand — was run against this environment's installed build:

```
$ codex --version
codex-cli 0.144.6
$ codex features list
hooks   stable   true
```

`~/.codex/` exists with `auth.json`, `config.toml`, `sessions/`, `logs_2.sqlite` — a real, authenticated, in-use installation, not a stub. This is genuine direct-experiment evidence, distinct from the documentation citations above: it confirms the hooks **capability** is live, enabled, and reported at `stable` maturity on this specific installed Codex build. It does **not** by itself confirm the exact per-event `stdin` JSON payload shape matches the documented field tables — that would require triggering an actual hook and capturing its real input, which is a materially different (and more invasive) kind of experiment.

This finding is now codified as a re-runnable regression check: `tests/tools/test_codex_capability_diagnostics.py::test_codex_hooks_feature_reported_enabled` re-executes `codex features list` and asserts the `hooks` row reports an enabled/stable state, skipping cleanly in any environment where `codex` is not on `PATH`.

**Deferred (not performed in this ticket):** an isolated stdin-payload-capture fixture experiment — writing a throwaway `hooks.json` outside this repo's trust boundary and running `codex exec` against a scratch fixture to capture one event's real JSON payload — was considered and explicitly **not** performed. `codex features list` already satisfies AC3's literal requirement (at least one entry distinguishing fixture-confirmed from documentation-cited evidence). Payload-capture would consume real API usage under the user's authenticated account and is recorded here as future scope for a dedicated ticket (e.g. a `CODEX-REPLAY-PROOF` child per `tickets/todos/provider-agnostic-discovery/SEQUENCE.md`), not a gap silently filled by this one.

## 7. Divergences / Silences vs. the Plan's Existing Claims

- **No divergence found.** All ten hook names, their turn-vs-thread/subagent-start scope split, and their existence are corroborated exactly as `docs/plans/archive/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md:109` (archived — shipped) claimed on 2026-07-20 — including capitalization. This matrix's independent re-verification one day later, against the same cited source URL, found no drift.
- **Silences the plan left, this matrix fills.** The plan's 2026-07-20 citation covered only the ten hook *names*. It said nothing about: current Codex capabilities/feature-maturity ladder (§2), project trust behavior (§3), the role/delegation model (§4), skills/configuration surfaces (§5), or the per-event field-level matcher/input/output tables (§1's detailed columns). This matrix is the first artifact in this repo to cover those, sourced fresh from the manual rather than assumed.
- **Residual limitation — WebFetch is blocked in this sandbox.** Three attempts (the primary hooks URL, a secondary Codex docs URL, and an unrelated third-party control URL) all failed identically with a self-signed-certificate error — a sandbox-wide TLS-interception issue, not a URL-specific one. Live re-fetch of `https://learn.chatgpt.com/docs/hooks.md` to confirm it has not changed since the plan's 2026-07-20 citation, or since this cache's 2026-07-20 16:04 snapshot, is not currently possible from inside this environment. `WebSearch` does work and returned corroborating third-party summaries (`developers.openai.com/codex/hooks`, `deepwiki.com/openai/codex/3.11-hooks-system`) naming the same ten events. This is recorded as a residual limitation, not a blocker: the cache excerpt (§1) plus the live CLI fixture (§6) together are sufficient for VERIFIED status on all ten hooks.
- **The `[agents]` subagent-role schema (§4) is only partially verified** — the cached manual's own "Agent roles" section is a pointer to an external doc this environment could not re-fetch, so role/delegation is marked VERIFIED for existence and high-level shape only, not for full field-level schema. This is a genuine gap, not a silently-assumed fact.

## What this doc does not do

- It does not implement, wire, or trust any `.codex/` directory inside this repo.
- It does not perform the stdin-payload-capture fixture experiment described in §6 — recorded as deferred future scope.
- It does not open or scope a Codex provider-runtime implementation ticket — blocked until all five discovery outputs across `TCK-20260721-PROVIDER-AGNOSTIC-EPIC` are complete and approved.
- It does not modify `src/engine/capability.py` or its tests — that is an unrelated, coincidentally-named simulation-engine capability registry.

## Related

- `docs/plans/archive/agent_infrastructure/idea_provider_agnostic_agent_orchestration.md:109` (archived — shipped) — the original 2026-07-20 ten-hook citation this matrix independently re-verifies, without merging into it.
- `docs/ai/agents_dir_disposition.md` — sibling decision-record artifact from the same discovery batch; structural precedent for this doc's format.
- `stored_artifacts/TCK-20260619-E-CAP-REGISTRY/investigation.md` — closest in-repo precedent for a machine-readable capability matrix, for a different domain (simulation engine features, not a third-party AI provider).
- `tests/tools/test_codex_capability_diagnostics.py` — the re-runnable diagnostic test codifying §6's fixture-confirmed evidence.
- `tickets/todos/provider-agnostic-discovery/SEQUENCE.md` — sequencing context; this ticket is a dependency of `TCK-20260721-ORCHESTRATION-CONTRACT-ADR` and `TCK-20260721-CODEX-REPLAY-PROOF`.
