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
Establish per-session isolation and a *proven* revert path for Headroom before anything is enabled —
its state is machine-wide, so an unisolated trial affects every concurrent session at once

## Status
BLOCKED

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

## Scope
- Determine and record where Headroom actually stores state, **verified from source or `--help`**,
  not from documentation. The CCR page documents behaviour but no paths, TTL, or purge command.
- Establish explicit isolation for any trial session: dedicated `HEADROOM_WORKSPACE_DIR` and
  `HEADROOM_CONFIG_DIR` outside the default `~/.headroom`, so a trial cannot read or write state
  shared with concurrent non-trial sessions.
- Write a revert runbook: exact commands to fully disable Headroom and purge its state.
- **Execute the revert runbook at least once** and record the result. This is the acceptance bar.
- Confirm whether MCP mode shares state with proxy mode, or is independently isolatable.

## Out of Scope
- Installing Headroom into any default or shared configuration, or pointing any existing session at
  it. This ticket establishes the safety envelope; the trial itself is
  `TCK-20260916-HEADROOM-MCP-EXPLICIT-TRIGGER-TRIAL`.
- `headroom learn` — off for the entire epic (auto-writes to `CLAUDE.md`).
- Proxy mode configuration. Phase 2, and separately BLOCKED.
- Any change to `.claude/settings.json` permissions or `CLAUDE.md`.

## Acceptance Criteria
- [x] Headroom's real state locations are recorded, each with the source that confirmed it (source
      file, `--help` output, or observed filesystem behaviour) — never a doc page alone. **Met from
      source**, not `--help` (installation itself is what's blocked) — see Implementation Notes for
      the full `paths.py` contract, spot-checked (2 of ~26 files referencing `.headroom`) rather
      than exhaustively audited, stated as such.
- [ ] A trial session can run with state confined to a dedicated directory, **demonstrated** by
      showing writes landing there and `~/.headroom` remaining untouched. **Not met — genuinely
      blocked, not worked around.** Source confirms isolation is achievable in principle (every
      state path derives from the two env-overridable roots), but "demonstrated by showing writes
      landing there" requires actually running the installed CLI, which the `files.pythonhosted.org`
      network block prevents. Source-reading cannot substitute for an observed write.
- [ ] The revert runbook exists and has been executed at least once, with before/after evidence that
      state is gone and no repository file was modified. **Not met, same reason as above** — nothing
      was ever installed, so there is nothing to revert; the "revert" of this attempt is simply that
      the isolated venv was `rm -rf`'d with no trace left anywhere in the repo or `~/.headroom`.
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
- `.mcp.json` — where an MCP-mode registration would land
- No repository source is modified by this ticket; all state is external (`~/.headroom` or an
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
