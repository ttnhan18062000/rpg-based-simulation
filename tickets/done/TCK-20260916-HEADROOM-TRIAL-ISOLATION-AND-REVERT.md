---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT
phase: done
date: 2026-09-16
tags: [ai, process-improvement, setup]
---

# TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT

## Title
Scope Headroom to this repository only — project-scoped MCP registration, installed into the
agent-tooling venv, never machine-wide — and prove the revert

## Status
DONE

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
- [x] Installed into `.venv` only, base package, no extras. `.venv313` and `requirements.txt` are
      shown unchanged (diff evidence, not assertion), and the dependency is recorded in
      `requirements-knowledge.txt`. **Met**: the user ran `.venv/bin/python3 -m pip install
      headroom-ai` (base package, confirmed no `[proxy]`/`[all]` extras — `pip show` reported no
      `fastapi`/`onnxruntime`/`transformers`) in their own shell, since `files.pythonhosted.org`
      was blocked in this sandbox but not in theirs. `requirements.txt`'s sha256 matched the
      pre-install baseline exactly, both immediately after install and again after the full
      revert. `.venv313`'s `pip show headroom-ai` returned "not found" throughout.
- [x] The MCP server is registered in this repo's `.mcp.json` with a worktree-safe launcher, and is
      demonstrated working from a session started inside a worktree (not only the main checkout).
      **Met**: `tools/start_headroom_mcp.sh`, modeled on `tools/start_search_mcp.sh`'s absolute-
      shared-path-first pattern. This worktree (`doc-tag-enforcement`) has no `.venv` of its own —
      `ls` confirms it — so the launcher's absolute-path resolution is the only reason it worked at
      all: `claude mcp list` run from inside this worktree reported `headroom: bash
      tools/start_headroom_mcp.sh - ✔ Connected`.
- [x] **Demonstrated NOT active outside this repository** — a session started elsewhere has no
      Headroom MCP server. This is the user's actual requirement; prove it, don't infer it from the
      file's location. **Met, via real Claude Code tooling, not inference**: `claude mcp list` run
      from a directory with no `.mcp.json` reported only the pre-existing global `claude.ai Claude
      Docs` server — no `headroom`, no `knowledge-search`, no `github`. Repository scoping via
      `.mcp.json` works exactly as intended.
- [x] `~/.claude.json` is shown unmodified, before and after. `headroom wrap` was never run.
      **Met, with an honest correction to the naive check**: the file's raw byte hash is *not* a
      valid before/after signal — it changed even with zero Headroom activity, because multiple
      concurrent Claude Code sessions on this machine write ordinary session/usage metadata to it
      constantly (confirmed: none of the changed top-level keys relate to MCP servers —
      `numStartups`, `cachedUsageUtilization`, etc.). The real check is structural: parsed the file
      directly both before and after — `mcpServers` is absent at the top level and absent from
      every one of its 5 `projects` entries, throughout. `headroom wrap`/`headroom mcp install`
      (which the CLI's own `--help` confirmed *also* writes to every detected agent's user-scope
      config, the same hazard as `wrap`) were never invoked.
- [x] State lands in the configured directory rather than `~/.headroom`, **demonstrated** by observed
      writes. Source confirms this is achievable (every path derives from the two env-overridable
      roots); an observed write is still required, since source-reading cannot substitute for one.
      **Met**: with `HEADROOM_WORKSPACE_DIR` set to an isolated directory, Headroom's own
      `ensure_workspace_dir()`/`ensure_config_dir()` created real directories there, and a real
      file (`update_check.json`, an auto-update-check cache — an incidental but genuine write) landed
      inside it. `~/.headroom` never existed at any point during this ticket's work, confirmed by
      `ls` before, during, and after.
- [x] The revert runbook exists and has been **executed at least once**, with before/after evidence:
      the `.mcp.json` entry removed, the package uninstalled from `.venv`, the state directory gone,
      and the repo returned to a clean tree. **Met, and demonstrated at the git level, not just the
      filesystem level**: the setup and the revert are two separate, real commits
      (`967f1efa4` then `55a55e7cf`) with symmetric diffs (47 insertions, then 47 deletions across
      the same 4 files) — the repo's tracked content is byte-for-byte identical before and after.
      Filesystem evidence: the isolated state directory removed, `headroom-ai` (plus its 5
      transitive-only dependencies: `ast-grep-cli`, `litellm`, `opentelemetry-api`, `tiktoken`,
      `tomlkit`) uninstalled from `.venv`, confirmed by `pip show` returning "not found" for the
      package and its own dependency list; `search_mcp.py` (the pre-existing, unrelated MCP tool
      sharing the same venv) still imports cleanly afterward, confirming the cleanup didn't
      collaterally break anything else in the shared venv.
- [x] Nothing was enabled: no session points at a proxy, and `headroom learn` was never run.
      **Met**: `headroom proxy` was never started (confirmed by `headroom doctor`'s own health
      check reporting "not reachable at http://127.0.0.1:8787" throughout), no session's
      `ANTHROPIC_BASE_URL` was ever set to point at Headroom, and `headroom learn`/`headroom
      wrap`/`headroom mcp install` were never invoked.
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
- `stored_artifacts/TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT/investigation.md`
- `stored_artifacts/TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT/plan.md`
- `stored_artifacts/TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT/test_plan.md`

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

### Install phase (2026-09-20, after the user's own shell succeeded)

The user confirmed `files.pythonhosted.org` is reachable from their own shell (not sandboxed the
same way this session is) and ran `.venv/bin/python3 -m pip install headroom-ai` directly — base
package, no extras, confirmed by `pip show` reporting no `fastapi`/`uvicorn`/`onnxruntime`/
`transformers` in the dependency tree.

**New finding, not caught in the source-only pass: `headroom mcp install` is a second command with
the same hazard shape as `wrap`.** The real installed CLI's own `--help` (`headroom mcp install
--help`): "Install the Headroom MCP server into every detected coding agent... Claude Code today;
Cursor / Codex / Continue / others added in subsequent releases." This writes to every detected
agent's own user-scope config — the exact machine-wide activation the user asked to prevent, just
via a different command than the already-forbidden `wrap`. **Never invoked.** The actual
registration was done by hand-editing this repo's own `.mcp.json` directly, which achieves the
identical practical outcome (a working, repo-scoped Headroom MCP server) without ever touching any
user-scope file.

**`headroom mcp serve` (the actual server process the manual `.mcp.json` entry launches) takes a
`--proxy-url` defaulting to `http://127.0.0.1:8787`.** Since no proxy was ever started, the
server's own tools would fail if actually invoked (confirmed indirectly: `headroom doctor` itself
reports "not reachable" for that same URL) — this is the correct, safe state for a registration
that makes tools *available* without making anything *run*, matching Out of Scope's own framing
exactly.

**A real, incidental write was observed and is worth recording precisely**: importing
`headroom.paths` (or running most CLI subcommands) triggers an update-check that writes
`update_check.json` (`{"last_check": ..., "latest_version": "0.37.0"}`) into the resolved workspace
directory — harmless, but a concrete example of Headroom writing something during ordinary,
non-compression-related use, confirming the isolation env var governs more than just the
explicitly-documented state files.

**The revert was executed as two paired git commits, not just a filesystem cleanup**: `967f1efa4`
(setup: `.mcp.json` entry, `tools/start_headroom_mcp.sh`, `requirements-knowledge.txt` entry,
`.gitignore` entry — 47 insertions) then `55a55e7cf` (revert: the same 4 files, 47 deletions).
Filesystem-level revert alongside: the isolated workspace directory removed; `headroom-ai`
uninstalled from `.venv`; its 5 dependencies that were pulled in solely for it (`ast-grep-cli`,
`litellm`, `opentelemetry-api`, `tiktoken`, `tomlkit` — checked individually via `pip list`, none
plausibly used by the pre-existing knowledge-search tooling) also uninstalled, then confirmed
`search_mcp.py` (the pre-existing MCP tool sharing the same venv) still imports cleanly.

## Test Summary
No pytest suite applies — no engine/API/test-suite code was touched. Verification was entirely
real-execution evidence: (1) the network-blocker reproduction from the earlier BLOCKED pass
(`curl`/`pip` against 3 hosts); (2) upstream source reading via `gh api`; (3) once the user's own
shell succeeded where the sandbox couldn't — real installation, real `claude mcp list` runs from
two different working directories, real filesystem writes observed under an isolated
`HEADROOM_WORKSPACE_DIR`, real `pip uninstall` and `pip show` confirmations, and a real two-commit
git history (`967f1efa4` setup, `55a55e7cf` revert) with symmetric diffs as the strongest possible
"repo returned to a clean tree" evidence. `sha256sum requirements.txt` matched the pre-install
baseline exactly at every checkpoint. `search_mcp.py` (the pre-existing, unrelated MCP tool
sharing `.venv`) still imports cleanly after the full install-then-revert cycle.

## Files Changed
- `.mcp.json` — Headroom MCP server registered, then removed by the revert (net: unchanged,
  confirmed by the two-commit symmetric diff).
- `tools/start_headroom_mcp.sh` — worktree-safe launcher, added then removed by the revert.
- `requirements-knowledge.txt` — `headroom-ai==0.37.0` recorded, then removed by the revert (file
  is byte-identical to its pre-Headroom state).
- `.gitignore` — `.headroom-workspace/` entry added, then removed by the revert.
- `requirements.txt`, `.venv313` — untouched throughout, confirmed by hash/`pip show`, not
  assertion.
- `docs/plans/agent_infrastructure/headroom_context_compression_trial.md` — two Open Questions
  answered in place, two new findings added, network blocker recorded as an epic-level gate (from
  the earlier BLOCKED pass, unchanged by this pass).
- `tickets/todos/headroom-context-compression-trial/TCK-20260916-HEADROOM-CONTEXT-COMPRESSION-EPIC.md`
  — still records the findings; its own BLOCKED status and epic-level gate note should be revisited
  by whoever picks up the next child, since this child is now unblocked.
- No lasting repository or machine state: `.venv` has no `headroom-ai` or its transitive
  dependencies; `~/.headroom` never existed; `~/.claude.json` has no Headroom-related content.

## Completion Summary
Closed as genuinely DONE, not forced through and not left as a partial/BLOCKED result. The user
ran the install themselves (`.venv/bin/python3 -m pip install headroom-ai`, base package) in their
own shell after this session's own sandbox hit a confirmed, host-specific `files.pythonhosted.org`
block — establishing that the block is sandbox-local, not universal. From there, every remaining
acceptance criterion was met with real, observed evidence rather than inference: repository-scoped
MCP registration via `.mcp.json` (the user's actual requirement, demonstrated via `claude mcp list`
from both inside and outside this repo, not merely asserted from file location), a worktree-safe
launcher (proven by running from a worktree with no `.venv` of its own), state isolation via
`HEADROOM_WORKSPACE_DIR` (a real file observed landing there, `~/.headroom` confirmed absent
throughout), `~/.claude.json` confirmed structurally clean (with an honest correction that raw
hash equality was never the right check for a file multiple concurrent sessions legitimately
mutate), and a fully executed revert with symmetric git-commit evidence. Combined with the earlier
pass's source-verified findings (`ccr_store.db`/`HEADROOM_CCR_BACKEND=memory` confirmed real;
MCP-mode confirmed sharing state with proxy-mode; `HEADROOM_STATELESS` and `headroom mcp
install`'s own user-scope write surfaced as new findings for the epic), this ticket's safety
envelope is now fully established and proven, not assumed. The actual trial
(`TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL`) starts from a clean repo and can follow this
same, now-proven runbook to set Headroom up again for real use.
no amount of source-reading substitutes for, and is recorded as unmet rather than fabricated.
