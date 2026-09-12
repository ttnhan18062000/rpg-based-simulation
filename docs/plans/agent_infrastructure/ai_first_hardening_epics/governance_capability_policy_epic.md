---
status: active
layer: ai
authority: P0
audience: agent
date: 2026-09-04
tags: [ai, governance, security, agent-monitoring]
---

# Epic Plan — Governance & Capability Policy

**Tracking ticket**: not yet created (planning stage — detail plan and milestones only, per direct
instruction; no `create-tickets` pass has run against this doc).
**Source**: `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` Rev.3 (READY TO FREEZE, 2026-09-04),
Bucket A / Horizon 0, inventory rows "Per-agent least-privilege tools: frontmatter", "Bash
secret-exposure advisory hook", "Versioned capability-envelope baseline for settings.local.json".
**Roadmap**: `roadmap.md` (this epic runs in parallel with Epic H — Guardrail Enforcement).
**Priority**: P0 — the frozen proposal's own Change Inventory grades this Known Structural Risk
motivation with mostly Level B/C evidence, "Start now" timing, zero unresolved design assumption.

## Problem

Three related governance gaps, all found by direct inspection during the maturity audit and next-
evolution proposal work, none previously flagged by the original 30-pattern review:

1. **Tool permissions are scoped at the session level, not per-agent.** `.claude/settings.json`'s
   `permissions.allow` is one broad wildcard shell allowlist — `Bash(git *)`, `Bash(rm *)`,
   `Bash(docker *)`, `Bash(curl *)`, `Bash(pkill *)`, `Bash(python3 *)`, plus unrestricted
   `Write`/`Edit` — that all 16 agents (`.claude/agents/*.md`) inherit identically regardless of
   role. Only 1 of 16 (`concern-investigator`) declares a scoped `tools:` frontmatter. An
   investigative-only agent (`investigator`, `doc-updater`) has the same `rm */docker */curl *`
   reach as `implementer`.

   **Status update (2026-09-05):** `TCK-20260904-AGENT-TOOLS-FRONTMATTER-WAVE` landed M3's Wave 1 —
   11 of 16 agents (all read-oriented/low-mutation roles, see Wave 1's list below) now declare a
   scoped `tools:` frontmatter, so the `investigator`/`doc-updater` example above no longer holds as
   a current-state fact — both are Wave 1 agents and no longer share `implementer`'s unrestricted
   reach.

   **Status update (2026-09-12):** `TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2` operationally
   defined the "clean observation window" gate (see below) and landed Wave 2 —
   `architecture-reviewer`, `security-reviewer`, `planner` now also declare a scoped `tools:`
   frontmatter, evaluated against the gate at zero failures. 14 of 16 agents now scoped. Only Wave
   3 (`implementer`, `parity-updater` — highest blast radius, done last) still inherits the full,
   unrestricted session-level default described above, gated on Wave 2's own observation window per
   this milestone's own sizing rule below.
2. **No policy layer exists between a model-issued Bash command and host execution**, outside one
   narrow path: `tools/knowledge_gateway_redaction.py::scan_for_secrets()` only guards writes into
   the knowledge-gateway cache. The dominant path — direct Bash tool calls from any of the 16
   agents — has zero secret-exposure detection.
3. **`settings.local.json` (the actual effective permission surface on this machine, ~70 accreted
   entries) is git-ignored** (confirmed via `git check-ignore`) — invisible to PR review,
   unauditable, and can silently diverge machine-to-machine or session-to-session.

## Scope

### M1 — Per-agent tool-usage baseline audit (gated on nothing)

Mine `agent-monitoring/tools.jsonl` for each of the 16 agents' real historical tool-call pattern:
which tools each agent actually invoked, how often, and — where visible from `tool_input` —
against what scope (file paths touched, command classes run). Output: one usage table, one row per
agent, columns at minimum `tool name → call count → representative examples`.

This is pure read/aggregation work against an existing file — no code changes, no risk, and it is
the evidence M3 scopes each agent's `tools:` frontmatter from, rather than guessing.

### M2 — Capability-envelope baseline + auditable diff check (gated on nothing, parallel to M1)

Per the frozen proposal's configuration-precedence invariant:

> Local configuration may specialize machine-specific behavior, but may not silently widen the
> centrally reviewed security envelope. Formally: `effective local capability ⊆ approved
> capability envelope`.

Concretely:
- Commit a version-controlled baseline file describing the *approved* capability envelope,
  separate from the git-ignored `settings.local.json`.
- Write a small auditable comparison script that diffs the live `settings.local.json` against
  that baseline and flags any entry outside it.
- **Explicit limitation, stated rather than assumed away**: this review found no confirmed
  mechanism in the current harness to enforce the `⊆` relationship automatically at runtime. The
  diff script is auditable tooling a human or CI can run — not a proven runtime guarantee that a
  wider local permission can never take effect. Do not present it as more than that.
- What belongs in the version-controlled baseline: the approved envelope itself. What may stay
  machine-local: entries within that envelope. What requires review: any local entry the diff
  flags as outside it.

**Ownership/lifecycle row:** see docs/guidelines/subsystem_ownership_lifecycle.md for this
subsystem's accountable role, update trigger, staleness signal, and removal condition — not
restated here.

### M3 — Per-agent `tools:` frontmatter rollout (gated on M1)

Revised during planning discussion after a proposed runtime "audit mode" turned out to be
unverifiable (Claude Code's own documentation was unreachable from this environment; only
third-party sources describe `tools:`/`disallowedTools:` behavior, and none of this repo's 16
agent files currently declare either field — `concern-investigator` is the sole one with a
`tools:` field today, so it's the only real local precedent). Rather than build new runtime
infrastructure to simulate an audit mode, this milestone gets its safety from process design
instead — offline replay against real history, conservative sizing, staged waves, and observable,
trivially-reversible enforcement:

**Step 0 — Empirical verification (before Wave 1, blocking):** confirm on `concern-investigator`
(the one agent that already has a `tools:` field) whether declaring `tools:` is actually enforced
at the harness level, and whether `disallowedTools` is recognized at all if a denylist approach is
ever needed later. Do not assume either behavior from unverified documentation — observe it.

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

**"Clean observation window", operationally defined (`TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2`,
2026-09-11):** Wave 1's own text used this phrase five times without defining a duration, a "clean"
criterion, or a measurable signal — with `tools.jsonl`'s existing `agent` field unusable as that
signal (it records the pipeline *phase* the orchestrator last announced, not the real tool caller;
see `tools/agent-monitoring/post_tool_hook.py:122-126` and this ticket's investigation.md §2).

- **Signal:** `tools/agent-monitoring/subagent_tool_audit.py --since <wave-landing timestamp on
  main>`, run on the machine where the pipeline runs. It reads Claude Code's own subagent
  transcripts (`~/.claude/projects/<repo-slug>*/<session>/subagents/*.{meta.json,jsonl}`) — the
  real, caller-level record — not `tools.jsonl`.
- **Failure (blocks the next wave):** any post-landing call to a tool outside a scoped agent's
  allowlist, in a session that itself started after landing (enforcement not working — a call from
  a *pre-landing* session that simply hadn't hot-reloaded yet is not a failure, since `.claude/
  agents/` definitions never hot-reload mid-session); any `No such tool available` error for a tool
  not in that agent's allowlist (the agent needed a tool it lacks); or any failed/blocked event
  whose summary attributes the failure to a missing tool.
- **Per-agent label:** `confirmed` (≥ 10 post-landing invocations, zero failures), `under-exercised`
  (1–9), `dormant` (0 post-landing, but used before landing), `never used` (0 both).
- **Rule:** the next wave may proceed when there are zero failures across all of the wave's agents.
  `under-exercised` and `dormant` agents are listed by name in the next wave's own ticket as open
  risk — never silently folded into "clean".
- **Minimum duration:** none beyond what the invocation counts already imply. Calendar days alone
  are a poor proxy for real exercise; the evidence is invocation counts and failure counts, not
  elapsed time.
- **Known limitation, stated plainly:** transcripts are local to the machine the audit runs on and
  can be pruned by Claude Code's own transcript-retention cleanup — a verdict must name its machine
  and date range, and a second environment's activity is invisible to a first environment's audit.
  This makes the signal real but not exhaustive; an honest verdict says so rather than presenting
  absence-of-evidence as evidence-of-absence.

**Wave 1 verdict, caller-level (`subagent_tool_audit.py --since 2026-09-06T04:09:42Z`, run on
`u24desktop`, 2026-09-11/12):** zero failures. `confirmed`: `done-checker`, `investigator`,
`doc-updater`, `test-scoper`. `under-exercised`: `ticket-scoper`, `mechanics-auditor`. `dormant`:
`concern-investigator` (only runs via `create-tickets`, which has not run since landing).
`never used`: `spec-document-reviewer`, `simulation-analyst`, `world-debugger`,
`world-render-reviewer`. One post-landing outside-allowlist signal was investigated rather than
assumed clean: `mechanics-auditor` made 3 `Agent` calls at `2026-09-06T04:13Z`, 4 minutes after
landing. Its own subagent transcript's parent session (`8553c310-aa3d-4e2b-ad90-19452165200a`)
started `2026-08-29T03:44:08Z` — 8 days before landing — confirming (not assuming) this is the
known pre-restart-session case the no-hot-reload constraint describes, not an enforcement gap.
Full evidence: `stored_artifacts/TCK-20260911-AGENT-TOOLS-FRONTMATTER-WAVE-2/`.

**Offline candidate-policy replay (per agent, before that agent's wave enforces anything):** for
every historical tool call the agent made (from M1's usage table), evaluate whether a candidate
scope would have allowed it. Classify every "would deny" result as legitimate-but-rare, obsolete,
inappropriate-legacy, accidental, or unclear/needs-review. Historical usage alone is not
sufficient justification for keeping a capability — a call classified obsolete or
inappropriate-legacy should not automatically earn a place in the candidate scope just because it
happened once.

**Sizing rule**: aim for the smallest scope we're confident won't break legitimate workflows, not
the theoretical minimum — conservative allowlist → observe → tighten later, never aggressive
allowlist → break workflows → widen reactively.

**Wave-based rollout**, each wave gated on the previous wave's observation window clearing with no
unresolved permission regression:

1. **Wave 1 — clearly read-oriented / low-mutation roles**: `doc-updater`, `investigator`,
   `ticket-scoper`, `done-checker`, `mechanics-auditor`, `spec-document-reviewer`,
   `concern-investigator` (re-verify against M1's real data even though it's already scoped),
   `simulation-analyst`, `world-debugger`, `world-render-reviewer`, `test-scoper`.
2. **Wave 2 — review / verification roles**: `architecture-reviewer`, `security-reviewer`,
   `planner`.
3. **Wave 3 — agents with legitimate mutation/execution requirements**: `implementer`,
   `parity-updater` — highest blast radius, done last, with the most compatibility-analysis
   evidence in hand.

**Ownership/lifecycle row:** see docs/guidelines/subsystem_ownership_lifecycle.md for this
subsystem's accountable role, update trigger, staleness signal, and removal condition — not
restated here.

**Observability requirement**: when a wave goes live, a permission-related failure must be
identifiable by agent, tool, and workflow/phase — not a silent or ambiguous failure. Rollback for
any wave is a single-file frontmatter revert, documented as trivial before that wave starts, not
figured out after something breaks.

### M4 — Bash secret-exposure advisory hook (gated on nothing — SHIPPED)

**SHIPPED** by `TCK-20260904-BASH-SECRET-SCAN-HOOK` — a new `PreToolUse[4]` entry in
`.claude/settings.json`'s `hooks` block, matcher `Bash`, reusing `tools/write_path_guard.py::scan_for_secrets()`
unmodified (the cross-epic extraction and the `TCK-20260824-KGMCP-KEEP-OR-DEPRECATE` re-ratification
that had blocked this milestone both resolved by `TCK-20260907-KGMCP-DEPRECATION-EPIC`/
`TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`), and verified by
`tests/tools/test_bash_secret_scan_hook.py` (positive-fire on synthetic secret-shaped commands
across 4 of the 10 patterns, negative-no-fire on ordinary commands, a dedicated
`test_hook_never_emits_permission_decision_or_deny` anti-drift guard, fail-open behavior on
malformed/missing stdin, and a byte-identical-module regression guard) plus
`tests/tools/test_settings_json_hooks_wiring.py` (structural `PreToolUse` array-length assertion).

Reuse `scan_for_secrets(text: str) -> str | None` as-is (it already returns the matching pattern's
key or `None`, and its own docstring already states the caller must reject outright, never
redact-and-store) — but wired as a **new** `PreToolUse` hook matching `Bash`, following the exact
shell-wrapper pattern already used by every other hook in `.claude/settings.json` (parse
`tool_input.command` from stdin JSON via a `python3 -c` one-liner, emit
`hookSpecificOutput.additionalContext` on a match). Scan the outgoing **command string itself**,
not gateway cache writes.

**Explicit scope boundary, carried from the frozen proposal's freeze pass**: this hook detects
secret-shaped values only. It is **not** a dangerous-command policy and **not** command-injection
detection — destructive filesystem/Git commands, Docker host-wide operations, remote script
execution, suspicious piping, privilege escalation, and network exfiltration remain entirely
unaddressed by this epic. That broader policy is out of scope here; it would need its own
evidence-backed proposal.

**Named limitation, checked against the actual patterns (not assumed)**: the 10 patterns in
`_SECRET_SCAN_PATTERNS` are prefix/format-specific (`AKIA...`, `gh[pousr]_...`, `sk-...`,
`-----BEGIN...`, etc.), not generic shape-matchers — reused as-is for Bash commands, they carry
acceptable false-positive risk (verified: a git SHA or a commit message mentioning "secret" does
not trigger any of the 10). The real gap this context introduces is structural, not a coverage
gap: this hook pattern-matches the **command text**, not the command's **effect** — a command like
`cat ~/.aws/credentials` or `export $(cat .env)` contains no secret-shaped literal at all, so it
reads a real secret into the agent's context/output undetected. Only commands that *embed* a
secret literal are visible to this hook; commands that *read* one are not. This is a known,
accepted limitation for M4 as scoped — closing it would mean command-effect analysis, which is the
dangerous-command policy explicitly out of scope above, not a text-scanning improvement.

Ships **advisory-only** (a warning `additionalContext`, never a `deny`) until the blocking-
escalation decision (a separate Bucket-B experiment in the frozen proposal, not part of this
epic) measures a false-positive rate over real operation.

### M5 — Horizon-0 exit signal (observation only, not implementation)

Confirm, after M1–M4 have shipped and run for the stated window, that:
- M3's frontmatter rollout produced zero critical workflow breakage over 2 weeks.
- M4's advisory hook shows an acceptable false-positive rate in normal operation.

This is the epic's contribution to the shared Horizon-0 → Horizon-1 gate defined in `roadmap.md`
— not a separate implementation task.

### Follow-on (Bucket B — not part of this epic's committed scope)

**Bash secret-exposure hook — blocking-escalation decision.** Once M4's advisory hook has run
through M5's exit window, the frozen proposal frames the advisory→blocking question as its own
Bucket-B experiment, not a Bucket-A implementation step: measure the hook's false-positive rate
over several weeks of normal operation before considering a hard block. This decision is owned by
this epic (same hook, same file) but is explicitly *not* one of M1–M5 above — it does not get
ticketed alongside them. Per the freeze verdict's handoff boundary, it becomes an Experiment
Specification (Hypothesis/Baseline/Method/Metrics/Exit/Kill Criteria) only after M5 confirms the
advisory hook is live and stable, tracked as a follow-on to this epic rather than inside it.

## Out of scope

- Any general dangerous-command, command-injection, or network-exfiltration policy (see M4's
  scope boundary above) — explicitly deferred pending its own evidence-backed proposal.
- Escalating the Bash secret-exposure hook from advisory to blocking — that decision is a
  Bucket-B experiment in the frozen proposal (needs a measured false-positive rate first), not
  part of this epic's implementation scope.
- Any change to `settings.json`'s hooks *mechanism* itself — this epic adds one new hook entry
  using the existing pattern, it does not redesign hook infrastructure.
- Removing/archiving `knowledge-gateway` — that is a standalone item in the frozen proposal's
  inventory, tracked separately (only the `scan_for_secrets()` extraction step is a shared
  dependency with this epic's M4 — see `roadmap.md`).

## Acceptance signal for this epic

- M1: a real, committed usage table exists covering all 16 agents, sourced from `tools.jsonl`.
- M2: a versioned capability-envelope baseline file and a working diff script exist; running the
  diff against the current `settings.local.json` produces a real, reviewed report (not a stub).
- M3: Step 0's empirical verification is documented (does `tools:` enforce, does `disallowedTools`
  exist) before any wave starts. A candidate scope and completed historical-compatibility analysis
  exists for every agent, with every "would deny" call classified. No known legitimate capability
  is removed without a documented alternative. All three waves complete with zero unresolved
  permission regression, each wave's rollback having been documented as trivial before that wave
  went live. All 16 `.claude/agents/*.md` files carry explicit `tools:` frontmatter reflecting the
  post-rollout scope. A later tightening pass (post-epic, not part of M3 itself) uses real
  post-rollout evidence, not M1's original data alone.
- M4: confirmed — the Bash secret-exposure hook is registered in `.claude/settings.json`
  (`PreToolUse[4]`), fires correctly against a synthetic command containing a secret-shaped
  literal in a test run, and does not fire on ordinary commands (`tests/tools/test_bash_secret_scan_hook.py`,
  shipped by `TCK-20260904-BASH-SECRET-SCAN-HOOK`).
- M5: the two Horizon-0 exit conditions this epic owns are confirmed true, feeding `roadmap.md`'s
  shared gate.

## References

- `roadmap.md` — shared exit gate and cross-epic dependency with Epic H.
- `AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` (`docs/brainstorm/agent-working-design/ai_first_engineering_next_evolution_proposal.html`) —
  §"Configuration & behavior authority map", §"Automation boundary analysis", Change Inventory rows
  for this epic's three items.
- `.claude/settings.json` — current `permissions.allow` list and hook registration pattern to
  extend.
- `.claude/settings.local.json` — the git-ignored file M2's baseline/diff check targets.
- `tools/write_path_guard.py` — source of `scan_for_secrets()` (line 149) for M4 (relocated from
  `tools/knowledge_gateway_redaction.py` by `TCK-20260907-KGMCP-REDACTION-EXTRACT-ARCHIVE`).
- `agent-monitoring/tools.jsonl` — the real usage data M1 mines.
