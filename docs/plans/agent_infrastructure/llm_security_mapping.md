---
status: active
layer: ai
authority: P2
audience: agent
date: 2026-10-13
tags: [ai, governance, security, mcp]
---

# Agent harness: OWASP LLM Top 10 mapping, threat model and search MCP checklist

Ticket: TCK-20261013-HARNESS-LLM-SECURITY-MAPPING. Docs only; no code was changed and no gap below is fixed here.

## How to read this

- **Present** means the control's code was read and a line or a test shows it works. A line number is from the tree at
  the time of writing (2026-10-13, after #539).
- **Advisory** means the control only warns; the call still runs.
- **Not found** means a search of the named files found nothing. It does not prove the control is absent elsewhere.
- Scope: this repository's harness (hooks, session layer, monitoring, the knowledge-search MCP). Claude Code's own
  sandboxing and model behaviour are out of scope except for what `.claude/settings.json` configures.
- The repository is public. Anything committed (monitoring shards, handover notes, tickets) is public.
- Source of the list: OWASP Top 10 for LLM Applications 2025, https://genai.owasp.org/llm-top-10/ (titles confirmed
  from the page, accessed 2026-10-13).

## 1. OWASP LLM Top 10 (2025) mapping

| ID | Risk | What applies to this harness | Controls present | Controls missing or weak | Evidence |
|---|---|---|---|---|---|
| LLM01 | Prompt Injection | Agents read files, web pages, issue bodies, peer messages and tool output, and act on them with Bash and Edit. | A rule that peer messages and issues never approve anything (documentation, not enforcement). The role guard asks before merge, push to the default branch, remote-branch deletion and worktree/data deletion for every role, so an injected instruction cannot do those silently. | No scan or tagging of untrusted tool output. The allow list is wide (`python3 *`, `curl *`, `rm *`), so an injected command that is not in the ask list runs. The guard is a "guardrail against mistakes, not a sandbox" by its own docstring. | `docs/guides/cross_session_messages.md:80`; `tools/sessions/guard.py` docstring (decision list and "not a sandbox" paragraph), `needs_user` rule at line 14; `tests/tools/test_session_guard.py::test_landing_on_the_default_branch_asks_for_every_role`; `.claude/settings.json` `permissions.allow` |
| LLM02 | Sensitive Information Disclosure | Secrets can appear in commands, tool output, monitoring shards and handover notes, all of which can reach git. | Bash PreToolUse secret scan with ten patterns (AWS key, PEM header, bearer, GitHub, Slack, OpenAI, Anthropic, basic-auth URL, two generic assignments); **advisory**, it never blocks. `.env` and `.envrc` are git-ignored. The handover-transit bundle is documented as never part of a PR. | The scan covers Bash commands only, not Edit/Write contents or tool output. The monitoring hooks store the first 80 characters of a Bash command unscrubbed (see 2.3). The pattern set describes itself as "not a production-complete secret scanner". No secret scanner in CI. | `tools/write_path_guard.py:128` (patterns), `:149` (`scan_for_secrets`); `.claude/settings.json` Bash hook calling `scan_for_secrets` ("Advisory only, not blocked"); `tests/tools/test_bash_secret_scan_hook.py::test_positive_fire_on_synthetic_secret_shaped_command`, `::test_hook_never_emits_permission_decision_or_deny`; `.gitignore:139-140`; `docs/guides/delivery_process.md` step 2a; `tools/agent-monitoring/post_tool_hook.py:58` |
| LLM03 | Supply Chain | Python packages for the knowledge stack, MCP servers launched through Docker and `bash`, Claude Code plugins and skills. | `uv.lock` exists. The knowledge venv's `requirements-knowledge.txt` pins `torch`, `sentence-transformers`, `sqlite-vec`, `rank-bm25`, `graphifyy` and `headroom-ai` exactly. The aseprite MCP is described as hash-pinned Lua in a bwrap sandbox (description in `.mcp.json`; not read further here). | `pyproject.toml` declares `mcp`, `duckdb`, `rank-bm25`, `sqlite-vec` with `>=` bounds only, and `mcp` is not in `requirements-knowledge.txt` at all. The `github` MCP runs `ghcr.io/github/github-mcp-server` with no tag or digest. No dependency audit or dependabot config today (the platform domain plans `dependabot.yml`). | `pyproject.toml:29-46`; `requirements-knowledge.txt:11-29` (6 `==` lines); `.mcp.json` `github` entry; `.github/` has no gitleaks, semgrep, audit or dependabot file |
| LLM04 | Data and Model Poisoning | The search index is built from repo docs, tickets and investigations; a poisoned doc changes what agents retrieve. No model training here. | The index is built from repo files, so changes go through review and PR merge (process, not a technical control). | No provenance or integrity check on the index files; no check that a doc was reviewed before it is indexed. Embedding model is a downloaded third-party model (`sentence-transformers`). | `tests/tools/test_search_shared.py::test_state_dir_key_is_the_resolved_path_not_the_contents` (the server is keyed by path, not by index contents); `requirements-knowledge.txt` |
| LLM05 | Improper Output Handling | Agent output becomes shell commands, file writes, PR bodies and git commits. | The role guard classifies Bash and edit calls and asks or denies for the authority actions; a hook failure on an authority payload exits 2 (fail closed) while other payloads exit 0. PR body lint runs in CI. | Nothing validates generated shell commands beyond the guard's classification. | `tools/sessions/guard.py` docstring "FAIL-CLOSED DISCIPLINE"; `.github/workflows/pr-body-lint.yml`; `tests/tools/test_session_guard.py` |
| LLM06 | Excessive Agency | Agents hold Bash, Write, `gh`, `git push`, `docker`, `curl`. | Role guard: deny a commit/push/open_pr in a worktree whose writer lease belongs to another role; ask for merge, default-branch push, remote-branch delete, worktree/data delete. `gh pr merge` asks and `gh pr merge --admin` is denied in settings. `Workflow` asks. Role boundary check **advisory**: warns once per session on an edit outside the role's grants and never blocks. | The allow list is broad. The guard is a guardrail, not a sandbox, and `boundary.py` never denies. A plain `claude` session without a role is "not role-governed": it asks only when a critical action is present. | `tools/sessions/guard.py` docstring items 2-3 and the unresolved-role paragraph; `tools/sessions/boundary.py:2-7` ("never denied"), `:187` (`_warning`); `.claude/settings.json` `permissions.ask` and `permissions.deny`; `tests/tools/test_session_guard.py::test_designers_and_planners_are_still_denied_by_another_roles_writer_lease`, `::test_non_writer_implementer_is_denied`; `tests/tools/test_session_boundary.py` |
| LLM07 | System Prompt Leakage | Role cards and `CLAUDE.md` are committed to a public repository on purpose. | The cards contain no credentials by design: they are generated from `registries/session_roles.yaml` and the domain/function card sources. | None needed for the prompts themselves: they are public. The risk is a secret pasted into a card or `CLAUDE.md`, which only the advisory Bash scan could catch, and only for Bash. | `tools/sessions/generate_agents.py`; `tests/tools/test_session_cards.py` (budget only); LLM02 row |
| LLM08 | Vector and Embedding Weaknesses | The local search index (SQLite vector table plus BM25) serves every agent session. | The index is local files. The shared search server binds `127.0.0.1`, requires a per-server random token, compares it in constant time, keeps its state in a 0700 directory with a 0600 file and refuses state it does not own. | No per-query access control: any holder of the token reads the whole index. No injection filter on retrieved text. | `tools/search_shared.py:84` (`_owned_and_private`), `:285` (`compare_digest`), `:269` (bind); `tests/tools/test_search_shared.py::test_requests_without_the_token_are_refused`, `::test_client_refuses_a_group_or_other_accessible_state_dir`, `::test_client_refuses_a_state_file_that_is_not_private` |
| LLM09 | Misinformation | Agents report status and "done" claims; a wrong claim reaches a PR or a gate. | Gates that run code rather than trust claims: `done_checker_static.py` (static conditions), the gate ledger records verdicts and outcomes append-only, PR body lint. The CLAUDE.md rule against editing an artifact to pass a gate (documentation). | Nothing independent checks an agent's prose summary. | `tools/gate_checks/done_checker_static.py`; `tools/agent-monitoring/gate_ledger.py:5`; `tests/tools/test_gate_ledger.py::test_outcome_and_adjudication_rows_are_valid_and_append_only`, `::test_later_adjudication_supersedes_and_both_rows_are_kept` |
| LLM10 | Unbounded Consumption | Parallel agents, subagent fan-out, search-model memory, token spend. | The shared search server serialises encode calls behind a lock and exits when idle; `Workflow` (multi-agent fan-out) asks before running; the card budget caps role-card size at 400 tokens. | No spend or call-rate limit at the harness level. No request body size cap on the shared server (see 3). | `tools/search_shared.py:321` (`_idle_watch`); `tests/tools/test_search_shared.py::test_encode_calls_never_overlap_behind_the_model_lock`, `::test_the_server_exits_when_idle_and_removes_its_state`; `.claude/settings.json` `permissions.ask` (`Workflow`); `tests/tools/test_session_cards.py::test_composed_card_is_within_the_token_budget` |

### Candidate controls the ticket named, and what was found

| Candidate | Finding |
|---|---|
| `tools/agent-monitoring/pre_tool_hook.py` | **Not a security control.** It only records the session id and a start timestamp (18 lines). |
| `tools/agent-monitoring/post_tool_hook.py` | Records a summary of each tool call. Not a control; it truncates, it does not scrub (`:58`, `:56`, `:60`, `:64`). |
| `tools/agent-monitoring/gate_ledger.py` | Present as an audit trail. Rows are appended, never rewritten; later rows supersede earlier ones. Nothing signs or hash-chains them (see 2.4). |
| `tools/write_path_guard.py` | Present: `scan_for_secrets` (used by the Bash hook, advisory) and `redact_content` (strips home paths). Its own docstring says the pattern set is a starting point, not production-complete. |
| Redaction in `tools/retrieval_cache.py` | **Not found.** The module only calls `write_path_guard.open_connection_with_limits()` (`:794`, `:874`). Its other "redaction" hits are column names for a policy version. It does not call `scan_for_secrets`, `redact_content` or `evaluate_write_candidate`. |
| Redaction in `tools/agent_codex_posttool_adapter/` | **Truncation, not redaction.** `redaction.py` truncates inputs to 80-120 characters and never stores `tool_response` text, only an ok/failed flag. It does not remove secrets from the truncated command. |
| `tools/sessions/boundary.py` | Present and **advisory** (module docstring: "warned about and logged, never denied"). |
| The search MCP token in `tools/search_shared.py` | Present; see the checklist in section 3. |

## 2. Threat model: an agent with tool access

### 2.1 Prompt injection through tool output
- **Entry points:** web pages fetched by tools, repo files and docs the agent reads, GitHub issue and PR bodies, peer
  messages from other sessions, search results from the local index.
- **Impact:** the agent runs commands or edits files on an attacker's instruction, within what the allow list and the
  guard permit.
- **Current mitigation:** the documented rule that peer messages and issues are data and never approve anything
  (`docs/guides/cross_session_messages.md:80`); the ask/deny rules for merge, default-branch push, remote deletion and
  worktree/data deletion (`tools/sessions/guard.py`); `Workflow` asks.
- **Gap:** nothing technical marks tool output as untrusted. The allow list covers `python3 *`, `curl *`, `rm *`,
  `docker *` and `pip *`, so most harmful actions outside the ask list run without a prompt.

### 2.2 Excess permissions
- **Entry points:** every session starts from the same `.claude/settings.json` allow list; a role grant is `may_write` plus `owns`.
- **Impact:** a confused or injected agent edits files outside its domain or runs broad commands.
- **Current mitigation:** the writer lease (deny on another role's worktree), the ask list, and the advisory
  `role_boundary` warning once per session (`tools/sessions/boundary.py`).
- **Gap:** the boundary check never blocks. Any session without a resolved role is "not role-governed" and is asked
  only about critical actions. No per-tool allow list per role.

### 2.3 Secret leakage
- **Entry points:** secrets typed or generated in Bash commands; secrets in tool output; secrets in Edit/Write
  content; the monitoring hooks' stored command prefix; handover notes, drafts and memory files.
- **Impact:** the repository is public, so a committed monitoring shard or note publishes the secret permanently.
- **Current mitigation:** the advisory Bash secret scan (`tools/write_path_guard.py:149`, ten patterns); `.env` is
  git-ignored; the handover-transit bundle is kept out of ticket PRs (`docs/guides/delivery_process.md` step 2a).
- **Gap:** the scan warns only, and only for Bash commands. `post_tool_hook.py:58` and the Codex adapter store the
  first 80 characters of a Bash command without scrubbing, and shards are committed. No secret scanner runs in CI.
  A secret in the first 80 characters of a command that the scan did not match is committed as written.

### 2.4 Log tampering
- **Entry points:** the monitoring JSONL shards and the gate ledger are plain files in git, writable by any session
  with Write access to `agent-working/agent-monitoring/**`.
- **Impact:** a session or a person can edit or delete rows after the fact, so the record of what ran or what a gate
  said can be altered.
- **Current mitigation:** the rows are append-only by convention and by tool design (`gate_ledger.py:5`, tested by
  `test_outcome_and_adjudication_rows_are_valid_and_append_only`); git history shows later changes; `rm` of
  `agent-working/agent-monitoring/*` asks (`.claude/settings.json` `permissions.ask`).
- **Gap:** no signature, no hash chain, and no check that an existing line was not changed. Edit/Write to a shard is
  allowed. History in git is the only evidence, and a branch rebase or force-push can drop it.

## 3. Hardening checklist: the search MCP server

Files: `tools/search_mcp.py` (stdio MCP front end), `tools/search_server.py`, `tools/search_shared.py` (per-user shared
HTTP server), `tools/start_search_mcp.sh` (launcher).

| Item | Status | Evidence |
|---|---|---|
| Pinned dependency versions | **Partial.** `requirements-knowledge.txt` pins `torch`, `sentence-transformers`, `sqlite-vec` and `rank-bm25` exactly. `mcp` is only `>=1.0.0` in `pyproject.toml` and absent from that file, and the launcher requires it to be importable, so its version is whatever is installed. | `requirements-knowledge.txt:11-14`; `pyproject.toml:29-46`; `tools/start_search_mcp.sh` probe loop |
| Scoped tokens, socket and file permissions | **Done** for the shared server: loopback only, 32-byte random token (`secrets.token_hex(32)`), constant-time compare, 0700 directories, 0600 state, log and lock files, state refused unless owned by this uid and not group/other accessible. **Open:** no token scope (one token covers `/health` and `/search`); `/health` answers the code version and database path to any token holder. | `tools/search_shared.py:84-123`, `:164`, `:189`, `:269`, `:285`, `:336`; tests `test_requests_without_the_token_are_refused`, `test_client_refuses_a_group_or_other_accessible_state_dir`, `test_client_refuses_a_state_file_that_is_not_private`, `test_state_file_is_written_atomically_with_mode_0600` |
| Tool allow-list | **Done by construction:** the MCP server registers exactly two tools, `search_docs` and `search_health`. The HTTP server answers only `GET /health` and `POST /search`. **Partial:** `top_k` is passed through as given; request bodies are read to the length the client sends, with no cap (`search_shared.py` `do_POST`). | `tools/search_mcp.py:311`, `:333`; `tools/search_shared.py` `do_GET`, `do_POST` (`:304`) |
| Append-only query log | **Open.** No query is logged. The server's `log_message` is silenced and only stdout/stderr go to a 0600 `server.log`. | `tools/search_shared.py:280` (silenced `log_message`), `:189` (`server.log`) |
| Idle exit | **Done.** The shared server exits after an idle period and removes its state. | `tools/search_shared.py:321` (`_idle_watch`); `test_the_server_exits_when_idle_and_removes_its_state` |

## 4. Proposed follow-ups (not filed; the planner decides)

1. Scrub or hash secret-shaped text before the monitoring hooks and the Codex adapter store a command prefix; add a
   test that a synthetic token in the first 80 characters never reaches a shard. (LLM02, 2.3)
2. Run a secret scanner in CI (gitleaks or equivalent) on every PR. Platform domain. (LLM02, 2.3)
3. Extend the secret scan to Edit/Write content, or decide in writing that it stays Bash-only. (LLM02)
4. Make the Bash secret scan blocking for high-confidence patterns, or record the decision to keep it advisory. (LLM02)
5. Pin `mcp` and the other knowledge-stack dependencies exactly; pin the `github` MCP image by digest; add dependency
   auditing. (LLM03)
6. Cap the request body size and `top_k` on the shared search server. (LLM10, section 3)
7. Add an append-only search query log (hashes or truncated text), if a record of what agents searched is wanted.
   (section 3)
8. Add a cheap integrity check for monitoring and gate-ledger shards, such as a hash chain or a CI check that existing
   lines did not change between `main` and the PR. (2.4)
9. Decide whether any boundary rule should block instead of warn, per role. (LLM06, 2.2)
10. Narrow the allow list (for example `curl *`, `rm *`) or document why each entry is needed. (LLM01, LLM06)
11. Decide a provenance rule for what enters the search index. (LLM04)
