---
status: active
layer: ai
authority: P2
audience: developer
maturity: proposed-bounded-trial
date: 2026-09-16
tags: [ai, workflows, agent-monitoring, process-improvement, optimization]
---

# Plan: Headroom Context-Compression Bounded Trial

> **Maturity: PROPOSED BOUNDED TRIAL.** This authorizes a reversible, opt-in evaluation of a
> third-party compression layer and the measurement needed to judge it. It does **not** authorize
> making compression a default, wrapping any session by default, enabling `headroom learn`, or
> putting compression in the path of gate/CI verification work. Promotion beyond the trial
> requires recorded evidence and the user's explicit approval.

## Problem

Agent token cost is a standing concern for this repo, and the user's own standing preference is
token efficiency over speed (accepting materially slower work for materially fewer tokens). But
this repo currently has **no way to measure token use at all**.

`docs/agent-monitoring/schema.md`'s "What is not recorded" section states it plainly:

> **Token counts** are not recorded. The workflow `agent()` call returns the agent's structured
> output only; API usage metadata (`input_tokens`, `output_tokens`) is consumed internally by the
> Claude Code runtime and is not forwarded to the workflow script. There is no field for it and
> no workaround within the current platform.

`tools/agent-monitoring/retrieval_baseline_metrics.py::build_context_tokens_section()` encodes the
same conclusion as a runtime value, returning `{"status": "unavailable", ...}`. This is why
`cost_proxy_score` exists as a *proxy* at all (`TCK-20260708-AGENT-COST-OBSERVABILITY`, whose
originating plan now sits in `docs/plans/archive/agent_infrastructure/idea_agent_cost_observability.md`).

So the problem is two problems, and the second is the more interesting one:

1. Token spend is high and unoptimized.
2. **Token spend is unmeasurable**, which means any optimization claim — including this one —
   cannot currently be verified from our own data.

## Candidate

[Headroom](https://github.com/headroomlabs-ai/headroom) (Apache-2.0, Python, ~72k stars, actively
maintained as of 2026-09-16) compresses what an agent *reads* — tool outputs, logs, JSON, diffs,
search results — before it reaches the model. Claimed: 20% fewer tokens for coding agents, 60–95%
for JSON.

**The non-obvious benefit.** Headroom sits in the API path as a proxy, so it observes real token
counts. Adopting it — even in a limited mode — would produce the **first real token telemetry this
repo has ever had**, closing a gap our own schema documents as having "no workaround within the
current platform." That capability is arguably worth more than the cost saving, and it is the
reason this trial is worth running even if the savings turn out to be modest.

### Alternate candidate — Caveman (added 2026-09-17)

[Caveman](https://github.com/juliusbrussee/caveman) (Go, ~106k stars, created 2026-04-04) overlaps
Headroom almost exactly on the input side — proxy, MCP server (`caveman_compress` /
`caveman_retrieve` / `caveman_stats`), lossy structural compression of logs/JSON/diffs, originals
recoverable from local SQLite. It is **not** adopted here, but it is recorded as the named alternate
so a Headroom-negative result does not read as a verdict on compression generally.

Where it is genuinely better:

- **It compresses output.** Headroom only touches what the agent *reads*. Output tokens bill at a
  premium, so an 8–10% output cut can be worth more than a 30% input cut. Headroom has no answer to
  this at any price, because it is not in that path.
- **External validation.** A JetBrains lab study over 86 real tasks (8.5% fewer output tokens, ~10%
  cost, no detectable quality change) and an Adobe Research paper, versus Headroom's self-reported
  benchmarks.
- **It publishes its own negative results**, including a benchmark case that came out **+9.9% worse**
  and an explicit "skip it if your workload is pure code generation."

Where Headroom stays better, and why it is the one being trialled first:

- **Code handling.** Headroom treats code as passthrough by design (*"Compressing function bodies
  would remove exactly what they need"*). Caveman's structural compression *"keeps signatures,
  removes bodies"* — the opposite choice, on the content type most dangerous to lose in a 150k-line
  code repo.
- **Licensing.** Apache-2.0 throughout, versus dual MIT + BSL-1.1 with `engine/`, `proxy/`, `mcp/`,
  `rewriter/` under BSL. Our use is permitted — the Additional Use Grant covers *"self-hosted use for
  your own first-party traffic, including production"*, and the restriction targets only third-party
  hosted services — but it is a weaker position until BSL converts to Apache-2.0 in June 2030.

**Caveman's output-side skill is out of scope regardless of any trial result.** It rewrites what the
agent *says*, stripping articles, hedging, and prose. That would degrade exactly the reporting
precision this repo's agent work depends on — distinguishing "verified" from "unconfirmed", quoting
an exit code rather than saying "looks fine". The proxy is separable from the skill; only the proxy
is of interest. Its claimed savings also span 8.5%–75% depending on who measured, which is precisely
why any evaluation must use paired measurement rather than a published figure.

## Why this is not a duplicate of context-efficient retrieval

`context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`
(maturity: proposed-future-epic) addresses a different layer and is **not** superseded by this:

| | That plan | This trial |
|---|---|---|
| Mechanism | Builds a bounded, cited `ContextPacket` — decides *what to retrieve* | Compresses payloads already being read — shrinks *what was retrieved* |
| Ownership | Ours, built in-repo | Third-party dependency |
| Status | Sequenced after provider-agnostic orchestration | Independently runnable now |

They are complementary. That plan explicitly withholds authorization for "a new mandatory workflow
gate, a production monitoring writer change, or a new external retrieval service" — this trial
respects the same boundary and adds none of those.

**Its governing principle is adopted here verbatim**, because it is exactly right for this work:

> The dashboard must not reward smaller packets by themselves. A context-budget reduction is
> successful only when correctness signals hold or improve.

## The integration constraint that shapes everything

Claude Code can only set `ANTHROPIC_BASE_URL`. It cannot pass request headers or per-request
parameters. Therefore:

- `headroom_mode="audit"` and per-tool `skip_compression` profiles are **SDK-only** and
  unreachable from Claude Code.
- `headroom proxy --mode` accepts only `cache` and `token` — **there is no proxy-level audit or
  observe-only mode**.
- `x-headroom-bypass` applies only to the `/v1/compress` endpoint, not `/v1/messages`.

So proxy mode is **all-or-nothing per session**, fixed at proxy startup. An "observe first, commit
later" rollout is therefore *not available* via the proxy path — which is what makes MCP mode the
correct first step rather than merely the cautious one.

## Approach: MCP-triggered first, proxy-per-session-class only on evidence

**Phase 1 — explicit trigger (MCP).** Headroom exposes `headroom_compress`, `headroom_retrieve`,
and `headroom_stats` as MCP tools. Nothing is intercepted; compression happens only when
deliberately invoked on a chosen payload. This gives a real measured number with zero exposure for
work where lossy compression is dangerous.

Target payloads — the JSON/log-shaped content where 60–95% actually applies:

- `agent-monitoring/data/**/*.jsonl` shards during retro and corpus analysis
- `graphify-out/graph.json` (~50MB, local-only)
- `docs/REGISTRY.yaml`, junit XML under `reports/junit/`

**Phase 2 — proxy for one session class,** only if Phase 1's numbers justify it: its own port, its
own `HEADROOM_WORKSPACE_DIR`/`HEADROOM_CONFIG_DIR`, restricted to data-heavy sessions, and
**`--mode cache` rather than `--mode token`** — see the cache-stability constraint below.

## Where compression must not go

The lossy compressors keep anomalies and drop normality: `LogCompressor` "keeps failures, errors,
warnings. Drops passing noise"; `DiffCompressor` drops unchanged context; `SearchCompressor`
rank-filters to top matches; `SmartCrusher` drops non-anomalous JSON rows.

That is precisely inverted for verification work, where the evidence **is** the absence of anomaly:
`273 passed, 0 failed`; a `uniq -d` returning empty; a `diff` reporting identical; an empty
protected-ratchet diff. Gate, CI, and review sessions must stay out of the compression path for the
duration of this trial. This is a scope boundary, not a preference.

`headroom learn` stays **off**: it auto-writes to `CLAUDE.md`, which requires the user's direct
authorization per repeated precedent in this repo.

## Isolation and reversibility

Headroom state is **per-user and machine-wide**, not per-session or per-worktree:

| State | Location | Scope |
|---|---|---|
| Workspace / read-write state | `~/.headroom` (`HEADROOM_WORKSPACE_DIR`) | Per-user, machine-wide |
| Config | `~/.headroom/config` (`HEADROOM_CONFIG_DIR`) | Per-user, machine-wide |
| Savings ledger | `HEADROOM_SAVINGS_PATH` | Per-user |
| Learned TOIN patterns | `HEADROOM_TOIN_PATH` | Per-user |

Config "applies globally to the proxy instance or SDK client — not per-user, per-project, or
per-directory." With several concurrent sessions across worktrees, one shared store and one shared
learned-pattern set is structurally the same hazard as the confirmed `.claude/current_run` sidecar
contamination, which misattributed monitoring data for two days. Isolation must therefore be
explicit, not assumed.

Revert is clean and total: stop pointing at the proxy / remove the MCP server, then
`rm -rf ~/.headroom/`. Nothing is written into the repository.

## Measurement

Two instruments, deliberately measuring different things.

**Savings — Headroom's own ledger / `headroom_stats`.** This is the only real token source
available (see Problem). It is a *paired* measurement: the same payload, compressed versus not, so
differences in ticket scale cancel by construction. This matters because **cross-ticket cost
comparison is invalid** — a hotfix and a 95-file epic differ by orders of magnitude, and that
variance dwarfs a 20% effect.

### Cache stability is a constraint, not a side effect (added 2026-09-17)

An external review of this account's usage measured roughly **48.8B cache-read against 815.6M
cache-write — about 60:1 reuse**. Prefix caching is already working extremely well, and that changes
what "saving tokens" means here.

`headroom proxy --mode token` explicitly *"maximizes visible per-request compression **at the cost
of cache stability**"*; `--mode cache` freezes prior turns to preserve it. Because cache reads bill
at a fraction of fresh input, **trading cached tokens for compressed-but-uncached ones can cost more
than it saves** — a compression win measured per-request can still be a net loss overall.

Two consequences, both binding on this trial:

1. **`--mode cache` is the default.** `--mode token` requires positive evidence before use, not
   merely a better per-request compression number.
2. **Cache-hit degradation is a harm signal in its own right**, tracked alongside
   `tool_call_count`-per-phase inflation. A fall in cache reuse counts against the trial even if
   per-request sizes improve.

This is the one recommendation from that review adopted directly into the design rather than merely
noted. Its other headline metrics — uncached input, cache-read, cache-write, output and tool-result
token counts — are **not executable here**, since `docs/agent-monitoring/schema.md` records no token
counts and states there is "no workaround within the current platform". That gap is itself part of
this trial's rationale.

**Harm — agent-monitoring, as a tripwire, not a cost metric.** `cost_proxy_score` is computed from
tool-call shape, not tokens, so it would stay flat regardless of savings; using it to measure
savings would measure the wrong thing entirely. Its real value is detecting degradation, via
scale-invariant rates:

| Signal | Source | Why |
|---|---|---|
| `final_status` DONE-rate; per-event `failed`/`blocked` rate | `runs.jsonl`, `events.jsonl` | Direct quality regression |
| `reason_code` frequency | `events.jsonl` | Shifts in *why* things fail |
| **`tool_call_count` per phase** | `events.jsonl` + `tools.jsonl` | **Over-compression detector**: if compression drops something needed, the agent calls `headroom_retrieve` to recover it, inflating tool calls per phase |
| `session_id` filtering | `tools.jsonl` | Isolates trial-session rows from concurrent sessions |

**Honest limit:** at roughly 16–70 runs/week this is a coarse tripwire, not a statistical result.
It will catch "noticeably worse." It will not resolve a subtle few-percent quality regression, and
no promotion decision should claim otherwise.

## Decision criteria

Promote to Phase 2 only if all hold:

1. Measured savings on real payloads are material (target: ≥30% on JSON/JSONL; the 20% coding-agent
   figure is *not* expected here, since code is passthrough by design).
2. No degradation in DONE-rate, failure rate, or `reason_code` mix over the trial window.
3. No unexplained `tool_call_count`-per-phase inflation.
4. The isolation and revert runbook has been executed successfully at least once.

Abandon — and revert — if savings are immaterial, any correctness signal degrades, or isolation
proves unreliable across concurrent sessions.

## Epic-level gate: package installation — resolved, with two caveats (2026-09-20)

`TCK-20260916-HEADROOM-TRIAL-ISOLATION-AND-REVERT` found that `files.pythonhosted.org` (the
package-download CDN, not the `pypi.org` index — that resolves fine) is unreachable from this
account's **Claude Code sandbox specifically**: every install attempt from an agent session
(`pip install`, `pip install --cert <system CA bundle>`, raw `curl --cacert` against the exact
wheel URL) fails with `SSL: CERTIFICATE_VERIFY_FAILED`, confirmed general (not Headroom-specific)
via an unrelated trivial package. This is the same host-specific-filter shape as CLAUDE.md's
documented `*.blob.core.windows.net` block, just a different host. A `git+https://github.com/...`
install would not route around it either, since Headroom's own dependencies resolve through the
same blocked host. This history is kept, not deleted — it's why that ticket closed proving the
safety envelope from source and a hermetic clean-clone repro rather than by installing anything in
this sandbox.

**Resolved by asking the user to run the install in their own shell, not by working around the
block.** The user's shell is not behind the same block and installed `headroom-ai` into `.venv`
twice — once during that ticket's own work (later uninstalled again as part of proving the
revert), and again afterward, which is the install still present today (confirmed importable,
runnable, and functionally exercised via a real MCP client smoke test).

**Two honest caveats, not "simply fixed":**

1. **The second install resolved entirely from pip's local cache** (`Using cached` on every
   wheel) — it did **not** re-prove network access to the blocked host. If that cache is ever
   cleared, the same block would need working around again via the user's own shell, not assumed
   already solved.
2. **The install is machine-level state, not a repository artifact.** It is not checked into git
   and not reproduced by cloning this repo elsewhere. Any child ticket that needs Headroom
   actually present in `.venv` (rather than just its `.mcp.json` registration, which an agent
   session can re-apply on its own directly) depends on that machine-level install still being
   there — on a different machine, or after this venv is rebuilt, it is not a one-time unblock.

`registry.npmjs.org` **is** reachable from the sandbox, which is relevant only to a possible
Caveman (`@caveman-ai/cli`) candidate-substitution, a decision for the user.

## Open questions

- ~~Whether `ccr_store.db` / `HEADROOM_CCR_BACKEND=memory` exist as documented~~ — **resolved
  2026-09-20, from source, not third-party summaries**: both are real.
  `headroom/cache/backends/__init__.py`'s own docstring: `get_compression_store()` (the proxy
  path) defaults to SQLite at `workspace_dir()/ccr_store.db`; `HEADROOM_CCR_BACKEND=memory` forces
  in-memory instead. `CompressionStore()` constructed directly defaults to in-memory unless a
  backend is passed explicitly.
- ~~Whether MCP mode shares `~/.headroom` state with proxy mode, or is independently isolatable~~
  — **resolved 2026-09-20, from source**: shared, not independent. `headroom/ccr/mcp_server.py`
  calls the identical `get_compression_store()` the proxy path uses, and sets its own
  `SHARED_STATS_DIR` directly to `paths.workspace_dir()`. The two canonical env vars
  (`HEADROOM_WORKSPACE_DIR`/`HEADROOM_CONFIG_DIR`) isolate a trial's MCP+proxy activity *together*
  from other concurrent sessions on the same machine, but do not isolate MCP-mode state from
  proxy-mode state within one trial — relevant to Phase 1→Phase 2 sequencing, since they'll share
  CCR/stats state unless a fresh workspace root is deliberately rotated between phases.
- Whether Claude *subscription* auth works through the proxy — an open, actively-discussed upstream
  integration question, and a hard blocker for Phase 2 if unresolved.
- **New (2026-09-20): `HEADROOM_STATELESS`.** `headroom/paths.py` has a process-wide
  `process_is_stateless()` flag (also settable via the `HEADROOM_STATELESS` env var) that forbids
  all writes to the workspace once set. This is a real, separate mechanism from the "no proxy-level
  audit/observe-only *compression* mode" limitation described above (that limitation is specifically
  about `headroom_mode="audit"` being SDK-only/unreachable via `ANTHROPIC_BASE_URL`, and still
  holds) — worth Phase 2 planning knowing about as a genuine no-workspace-writes safety valve.
- **New (2026-09-20): `headroom wrap claude` installs a third dependency at user scope.** Per the
  README: it "installs Serena for semantic code navigation... registered at user scope (for Claude
  Code, in `~/.claude.json`), so it stays available in your other projects until you run `headroom
  unwrap`." `~/.claude.json` is machine-wide, shared by every concurrent Claude Code session — the
  same hazard shape as the confirmed sidecar contamination this plan already cites. Not relevant to
  Phase 1 (MCP, no `wrap`), but belongs in this epic's risk list before any `wrap`-based phase.
- **New (2026-09-20, from the real installed CLI's own `--help`, not just the README):
  `headroom mcp install` has the identical hazard shape as `wrap`.** "Install the Headroom MCP
  server into every detected coding agent... Claude Code today; Cursor / Codex / Continue / others
  added in subsequent releases" — a second, separate command that writes to every detected agent's
  user-scope config, not just `wrap`. Both are now confirmed forbidden for this repo's own use;
  the repo-scoped `.mcp.json` entry is hand-edited directly instead, achieving the same practical
  outcome without touching any user-scope file.

## Related

- `docs/agent-monitoring/schema.md` — "What is not recorded"; the token-unavailability authority
- `tools/agent-monitoring/retrieval_baseline_metrics.py` — existing baseline harness;
  `build_context_tokens_section()` is the natural place for real token data to land
- `docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md`
- `docs/plans/archive/agent_infrastructure/idea_agent_cost_observability.md` (archived) and
  `TCK-20260708-AGENT-COST-OBSERVABILITY`
