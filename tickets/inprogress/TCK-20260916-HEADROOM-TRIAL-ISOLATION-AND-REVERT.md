---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT
phase: open
date: 2026-09-16
tags: [ai, process-improvement, setup]
---

# TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT

## Title
Scope Headroom to this repository only — project-scoped MCP registration, installed into the
agent-tooling venv, never machine-wide — and prove the revert

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
First child of `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC`, and it **blocks every other child**.

Headroom's state is per-user and machine-wide, not per-session or per-worktree: `~/.headroom`
(`HEADROOM_WORKSPACE_DIR`), `~/.headroom/config` (`HEADROOM_CONFIG_DIR`), plus the savings-ledger
(`HEADROOM_SAVINGS_PATH`) and learned-pattern (`HEADROOM_TOIN_PATH`) locations. Upstream
configuration docs state config "applies globally to the proxy instance or SDK client — not
per-user, per-project, or per-directory."

This machine routinely runs several concurrent Claude sessions across worktrees. One shared store,
one shared config, and one shared learned-pattern set across all of them is **structurally the same
hazard as the confirmed `.claude/current_run` sidecar contamination**, which misattributed
monitoring data to an already-closed ticket for two days
(`project_sidecar_cross_session_contamination`). That precedent is why isolation is a prerequisite
rather than a later refinement.

The user's explicit requirement (2026-09-16): *"make sure we can revert the change if observe the
result is not good enough."* A revert path that has been written but never executed is not evidence
that it works — this repo has catalogued 13+ mechanisms that exist, have tests, and do not do what
they claim.

### Why it is blocked (2026-09-20)

**A host-specific network filter, not a general PyPI outage.** `pypi.org/simple/` returns `200` —
the package index resolves fine — but `files.pythonhosted.org` (the actual package-download CDN)
returns `000`/`SSL: CERTIFICATE_VERIFY_FAILED` on every attempt: plain `pip install headroom-ai`
(base package, no extras, into a fresh isolated venv outside the repo — never touched
`.venv313`), `pip install --cert <system CA bundle>`, and a raw `curl --cacert <system CA bundle>`
against the exact wheel-metadata URL all failed identically. Confirmed this is not
Headroom-specific by installing a trivial, unrelated package (`six`) in the same venv — same
failure. This is the same shape as CLAUDE.md's CI Triage section's documented host-specific TLS
block on GitHub's blob-storage hosts (`*.blob.core.windows.net`), just against a different host
(`files.pythonhosted.org`) — package *metadata* resolves, package *bytes* do not. A
`git+https://github.com/...` install would not route around this either, since `headroom-ai`'s own
dependencies (`litellm`, `tiktoken`, `ast-grep-cli`, ...) still resolve through the same blocked
host. `registry.npmjs.org` returns `200` — reachable — which is relevant only if the epic considers
switching candidates to Caveman (`@caveman-ai/cli`, npm); that is a candidate-substitution decision
for the user, not something this ticket acts on.

**Real progress was still made from source, without installing anything** (`gh api` reaches
GitHub's own API, unaffected by the `files.pythonhosted.org` block) — see Implementation Notes for
the full detail. This resolved 2 of 3 named unknowns and surfaced 2 new findings, which is why this
ticket is `BLOCKED` rather than simply reverted-to-`OPEN`-with-nothing-learned. What remains
genuinely blocked needs live execution (installing and running the actual CLI), which no amount of
source-reading substitutes for — Acceptance Criteria 2 and 3 are marked accordingly below, not
fudged.

### Rescoped 2026-09-20 (user decision) — repository-scoping replaces bespoke state isolation

The user approved installing Headroom normally, with one requirement in their own words: *"we still
need configure it to be used in this repository, so that other repositories that not yet config will
not automatically triggered"*, and then asked the sharper question: *"our project use local venv or
venv313 under this repository?"* Both change this ticket's approach, and for the better — the repo
already has an established pattern for exactly this, which the original scope did not use.

**Activation is scoped by `.mcp.json`, which is per-repository and committed.** This repo's own
`.mcp.json` already registers `knowledge-search` and `github` this way, so only sessions started in
this repo get them. Registering Headroom's MCP server there gives repository scoping directly, and
makes the activation switch a **version-controlled file change** — reviewable in a PR and revertible
with git, which is strictly better than the bespoke env-var state isolation this ticket originally
proposed.

**Installation goes into the agent-tooling venv, not the project's dependency set.**
`requirements.txt` is core app plus tests and is what CI installs; its own header states that the
local agent knowledge-search tooling "lives in `requirements-knowledge.txt` instead — those packages
are not needed by the engine, API, or test suite." Headroom is agent tooling by that same test, so it
belongs in `requirements-knowledge.txt` and in `.venv` (3.12.3, the venv that actually holds the
agent tooling — `tools/start_search_mcp.sh` resolves to it by absolute path). `.venv313` (3.13.14)
mirrors CI's interpreter and is used for CI-matching test runs, so it stays clean.

**The launcher must be worktree-safe.** `tools/start_search_mcp.sh` documents the trap in its own
comments: the shared venv lives at the main checkout root, but every worktree has its own copy of the
script, so `$REPO_ROOT/.venv` does not exist in a worktree and a naive launcher silently falls through
to bare `python3`. Model Headroom's launcher on that script — absolute shared path first, then
fallbacks.

**`headroom wrap claude` is now explicitly forbidden**, not merely out of scope. It writes to
`~/.claude.json` — confirmed present on this machine, 78KB, containing its own `mcpServers` section —
which is *user* scope, machine-wide, and would trigger Headroom in every repository. That is precisely
what the user asked to prevent. It also installs a third dependency (Serena) at user scope.

**On the network blocker:** the `files.pythonhosted.org` block applies to the agent sandbox. Whether
the user's own shell is subject to the same filter is **unknown and must be established first** — the
user can run the install themselves (`! pip install headroom-ai` into `.venv`, no extras). If their
shell hits the same block, return this ticket to `BLOCKED` with that recorded; do not hunt for
workarounds around a network filter.

## Scope
- Determine and record where Headroom actually stores state, **verified from source or `--help`**,
  not from documentation. (Done from source — see Acceptance Criteria.)
- **Install into `.venv` only** (the agent-tooling venv at the main checkout root), base package, no
  extras. Record the dependency in `requirements-knowledge.txt`, never `requirements.txt`.
- **Register the MCP server in this repo's `.mcp.json`**, via a launcher modeled on
  `tools/start_search_mcp.sh` so it resolves the shared venv from any worktree.
- **Demonstrate the repository scoping**: it works in a session started in this repo, and is absent
  from a session started outside it. This is the user's actual requirement and the primary
  acceptance bar.
- Set `HEADROOM_WORKSPACE_DIR`/`HEADROOM_CONFIG_DIR` in the launcher's own env so state does not land
  in `~/.headroom`, and verify by observed writes. Secondary to the scoping above, not the main
  mechanism.
- Write a revert runbook and **execute it at least once**, recording the result.
- Confirm whether MCP mode shares state with proxy mode, or is independently isolatable. (Done from
  source — shared.)

## Out of Scope
- Installing Headroom into any default or shared configuration, or pointing any existing session at
  it. This ticket establishes the safety envelope; the trial itself is
  `TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL`.
- `headroom learn` — off for the entire epic (auto-writes to `CLAUDE.md`).
- Proxy mode configuration. Phase 2, and separately BLOCKED.
- Any change to `.claude/settings.json` permissions or `CLAUDE.md`.
- **`headroom wrap claude` — forbidden, not merely deferred.** It writes user-scope
  `~/.claude.json`, which would activate Headroom in every repository on this machine, and installs
  Serena alongside. This is the exact outcome the user asked to prevent.
- **`requirements.txt` and `.venv313` — do not touch either.** CI installs `requirements.txt` on
  every job and has no use for a compression tool; `.venv313` mirrors CI's interpreter and is used
  for CI-matching test runs.
- Enabling compression, or pointing any session's `ANTHROPIC_BASE_URL` at a proxy. Registration
  makes the tools *available*; nothing in this ticket makes them *run*.

## Acceptance Criteria
- [x] Headroom's real state locations are recorded, each with the source that confirmed it (source
      file, `--help` output, or observed filesystem behaviour) — never a doc page alone. **Met from
      source**, not `--help` (installation itself is what's blocked) — see Implementation Notes for
      the full `paths.py` contract, spot-checked (2 of ~26 files referencing `.headroom`) rather
      than exhaustively audited, stated as such.
- [ ] Installed into `.venv` only, base package, no extras. `.venv313` and `requirements.txt` are
      shown unchanged (diff evidence, not assertion), and the dependency is recorded in
      `requirements-knowledge.txt`.
- [ ] The MCP server is registered in this repo's `.mcp.json` with a worktree-safe launcher, and is
      demonstrated working from a session started inside a worktree (not only the main checkout).
- [ ] **Demonstrated NOT active outside this repository** — a session started elsewhere has no
      Headroom MCP server. This is the user's actual requirement; prove it, don't infer it from the
      file's location.
- [ ] `~/.claude.json` is shown unmodified, before and after. `headroom wrap` was never run.
- [ ] State lands in the configured directory rather than `~/.headroom`, **demonstrated** by observed
      writes. Source confirms this is achievable (every path derives from the two env-overridable
      roots); an observed write is still required, since source-reading cannot substitute for one.
- [ ] The revert runbook exists and has been **executed at least once**, with before/after evidence:
      the `.mcp.json` entry removed, the package uninstalled from `.venv`, the state directory gone,
      and the repo returned to a clean tree.
- [ ] Nothing was enabled: no session points at a proxy, and `headroom learn` was never run.
- [x] The `ccr_store.db` / `HEADROOM_CCR_BACKEND=memory` question is resolved either way and the
      finding recorded — currently unconfirmed, appearing only in third-party summaries. **Resolved:
      both are real**, confirmed directly from `headroom/cache/backends/__init__.py`'s own
      docstring — `get_compression_store()` (the proxy path) defaults to SQLite at
      `workspace_dir()/ccr_store.db`; `HEADROOM_CCR_BACKEND=memory` forces in-memory instead.
- [x] Confirmed whether MCP-mode state is shared with, or independent of, proxy-mode state.
      **Resolved: shared, not independent.** `headroom/ccr/mcp_server.py` calls the identical
      `get_compression_store()` the proxy path uses, and sets its own `SHARED_STATS_DIR` directly to
      `paths.workspace_dir()`. Both env-overridable roots isolate MCP+proxy together from other
      concurrent sessions, but do not isolate MCP-mode state from proxy-mode state within one trial.

## Related Tickets
- `TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC` — parent
- `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` — the prior confirmed instance of shared-state
  contamination across concurrent sessions; the reason this ticket exists first

## Related Docs
- `docs/plans/agent_infrastructure/headroom_context_compression_trial.md` — Isolation and
  reversibility section

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `.mcp.json` — where the project-scoped MCP registration lands (this is now a real repo change,
  and is what makes the activation revertible with git)
- `requirements-knowledge.txt` — where the dependency is recorded, never `requirements.txt`
- `tools/start_search_mcp.sh` — the launcher pattern to copy, including its worktree/shared-venv
  resolution and the comment explaining why a naive `$REPO_ROOT/.venv` lookup fails
- Superseded note: this ticket previously stated that no repository source is modified and all state
  is external (`~/.headroom` or an
  isolated equivalent)

## Assumptions / Open Questions
- Assumed that `HEADROOM_WORKSPACE_DIR` and `HEADROOM_CONFIG_DIR` fully redirect state. If some
  component ignores them and writes to `~/.headroom` regardless, isolation is not achievable as
  designed — **report that rather than working around it**, since it would change the epic's
  viability, not just this ticket's approach.
- Whether an isolated trial is achievable at all while other sessions run concurrently is the real
  question this ticket answers. A negative answer is a valid, useful outcome.

## Implementation Notes
Prefer observing actual filesystem behaviour over trusting either the upstream docs or this ticket.
Several upstream details are absent from authoritative pages or differ between them.

Do not enable anything beyond what is needed to observe where state lands.

**Findings from real upstream source (`gh api repos/headroomlabs-ai/headroom/contents/...`,
unaffected by the `files.pythonhosted.org` block since it's GitHub's own API), 2026-09-20:**

- **`headroom/paths.py` is the single canonical filesystem-contract module.** Every state
  file/dir — `proxy_savings.json`, `savings_events.jsonl`, `toin.json`, `subscription_state.json`,
  `memory.db`, `memories/`, `license_cache.json`, `session_stats.jsonl`, `sync_state.json`,
  `bridge_state.json`, `logs/` (`proxy.log`, `proxy-stdio.log`, `debug_400/`, `codex_wire/`),
  `bin/` (vendored binaries), `clients/`, `deploy/`, `plugins/`, `ccr_store.db`, and per-port lock
  files — derives from exactly two roots: `workspace_dir()` (`$HEADROOM_WORKSPACE_DIR` >
  `~/.headroom`) and `config_dir()` (`$HEADROOM_CONFIG_DIR` > `$HEADROOM_WORKSPACE_DIR/config` >
  `~/.headroom/config`). Precedence for every per-resource helper is explicit argument > per-
  resource env var > derived from canonical root > default, and the module's own docstring states
  the canonical-root env vars were added "strictly additive" over the older per-resource overrides.
  **Isolation via these two env vars is achievable in principle, source-verified** — the open
  question this ticket's own Assumptions section raised ("if some component ignores them... report
  that rather than working around it") did not turn up a code-level bypass in the files checked,
  but this was a **2-of-~26 spot check** (`settings_store.py`, `telemetry/toin.py` — both import
  `headroom.paths` rather than hardcoding `~/.headroom`), not an exhaustive audit of every file a
  `search/code` query for `.headroom` returned. `wrap`/`proxy`/provider-specific files (VSCode,
  Codex, OMP) were not checked, since neither is in this trial's Phase 1 scope.
- **`ccr_store.db` / `HEADROOM_CCR_BACKEND=memory` — confirmed real, resolving AC4.**
  `headroom/cache/backends/__init__.py`'s own module docstring: `get_compression_store()` (the
  proxy code path) "defaults to SQLite (restart-safe, shared across workers)" at
  `workspace_dir()/ccr_store.db`; `HEADROOM_CCR_BACKEND=memory` forces in-memory instead.
  `CompressionStore()` constructed directly (bypassing `get_compression_store()`) defaults to
  in-memory unless a backend is passed explicitly.
- **MCP mode shares state with proxy mode — resolving AC5, and the less convenient answer.**
  `headroom/ccr/mcp_server.py` line 401 calls the identical `get_compression_store()` the proxy
  uses; line 203 sets `SHARED_STATS_DIR = paths.workspace_dir()` directly. Both mechanisms funnel
  through the same SQLite-backed CCR store and the same stats directory by default. The two
  canonical env vars isolate a trial's MCP+proxy activity *together* from other concurrent Claude
  Code sessions on the same machine — they do **not** isolate MCP-mode state from proxy-mode state
  *within* one trial. Relevant for Phase 2 sequencing: Phase 1 (MCP) and a later Phase 2 (proxy)
  will share the same CCR/stats state unless a fresh `HEADROOM_WORKSPACE_DIR` is deliberately
  rotated between them.
- **New finding, not in the ticket or the plan doc: `HEADROOM_STATELESS`.** `paths.py` has a
  process-wide `set_process_stateless()` / `process_is_stateless()` flag (also settable via the
  `HEADROOM_STATELESS` env var) that "forbids writes to the workspace" entirely once set. This is
  **not** the same thing as an observe-only *compression* mode — the plan doc's "there is no
  proxy-level audit or observe-only mode" claim was specifically about `headroom_mode="audit"`
  being SDK-only/unreachable via `ANTHROPIC_BASE_URL`, and that claim still stands — but this is a
  separate, real mechanism neither this ticket nor the plan doc knew about, worth the epic's Phase
  2 planning knowing about.
- **New finding, real risk, out of this ticket's own scope but belongs in the epic's risk list:**
  the README confirms `headroom wrap claude` "starts a local proxy, installs Serena for semantic
  code navigation, and launches the agent configured to route through Headroom. Serena is
  registered at user scope (for Claude Code, in `~/.claude.json`), so it stays available in your
  other projects until you run `headroom unwrap`." `~/.claude.json` is machine-wide, shared by
  every concurrent Claude Code session — the same hazard shape as the confirmed sidecar
  contamination this ticket already cites. Never invoked `wrap` (out of scope for Phase 1's
  explicit-trigger MCP mode), so this is a documented risk for whoever scopes the trial itself, not
  something this ticket needed to isolate against.

**The blocker itself, precisely characterized (verified, not assumed):** `pypi.org/simple/` →
`200` (index resolves); `files.pythonhosted.org` → `000`/`SSL: CERTIFICATE_VERIFY_FAILED` on every
attempt (`pip install`, `pip install --cert <system CA bundle>`, raw `curl --cacert <system CA
bundle>` against the exact wheel-metadata URL). Confirmed general (not Headroom-specific) by
installing an unrelated trivial package (`six`) in the same fresh venv — identical failure. This
is a host-specific filter on the package-download CDN, the same shape as CLAUDE.md's documented
`*.blob.core.windows.net` block, just a different host. `registry.npmjs.org` → `200` (reachable) —
noted only because it bears on a possible candidate-substitution decision (Caveman, npm-installable
where Headroom is not), which is the user's call, not something acted on here.

## Test Summary
No tests apply — no repository code was changed. Verification was: (1) `curl`/`pip` reproduction
of the network blocker against 3 different hosts (`pypi.org`, `files.pythonhosted.org`,
`registry.npmjs.org`) and 2 different tools; (2) direct reading of real upstream source
(`headroom/paths.py`, `headroom/cache/backends/__init__.py`, `headroom/ccr/mcp_server.py`,
`README.md`, `pyproject.toml`) via `gh api`, cross-checked against the ticket's own flagged
unknowns.

## Files Changed
- `tickets/todos/headroom-context-compression-trial/TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT.md`
  — this ticket, marked `BLOCKED` with findings recorded; stays in `tickets/todos/`, not moved to
  `tickets/done/` (the safety-envelope gate this ticket exists to establish is not cleared).
- `docs/plans/agent_infrastructure/headroom_context_compression_trial.md` — two Open Questions
  answered in place, two new findings added, network blocker recorded as an epic-level gate.
- `tickets/todos/headroom-context-compression-trial/TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC.md`
  — noted as environment-blocked at the epic level (children 3-5 all need a working install, not
  just this child).
- No repository source code changed. No package was ever successfully installed; the empty scratch
  venv used for the failed attempt was deleted (`rm -rf`), leaving no trace in the repo or
  `~/.headroom`.

## Completion Summary
Blocked, not abandoned or forced through. The installation step itself is prevented by a
host-specific network filter on `files.pythonhosted.org` (index host `pypi.org` resolves fine;
confirmed general via an unrelated trivial package, not Headroom-specific) — genuinely outside
this ticket's ability to route around, and not attempted to be routed around (no `git+https`
workaround, since Headroom's own dependencies resolve through the same blocked host anyway).
Real progress was still made without installing anything: reading Headroom's actual upstream
source resolved 2 of the ticket's 3 named open questions with direct evidence (`ccr_store.db`'s
real default path and `HEADROOM_CCR_BACKEND=memory`'s reality; MCP-mode's real sharing of proxy-
mode's CCR/stats state) and surfaced 2 findings neither this ticket nor the plan doc knew about
(`HEADROOM_STATELESS`; `headroom wrap`'s `~/.claude.json`/Serena side effect). What remains
genuinely unmet — a demonstrated isolated write and an executed revert — needs live execution that
no amount of source-reading substitutes for, and is recorded as unmet rather than fabricated.
