---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-CAPABILITY-ENVELOPE-BASELINE
artifact_type: investigation
tags: [governance, ai, security]
---

# Investigation — TCK-20260904-CAPABILITY-ENVELOPE-BASELINE

## Current Behavior

**Semantic prior-work search (Step 0c) returned nothing directly on-topic.** `mcp__knowledge-search__search_docs`
for "Capability-envelope baseline file and auditable diff script" returned only loosely-related
hits (balance-envelope config, memray budget, KGMCP query router) — none about `settings.local.json`
or a capability-envelope baseline. `graphify query "Capability-envelope baseline diff script"`
returned only unrelated `package.json` script-block nodes (`frontend/`, `dashboard-frontend/`,
`website/`) — graphify's indexed graph has no coverage of `.claude/` config files. Both tools were
called first, per the hard rule, before any grep/file read; both came back empty of anything
relevant, which is itself a finding — this genuinely is new tooling with no existing script or doc
to build on, not a case of prior-work reuse being available.

**`.claude/settings.local.json` does NOT exist in this worktree**, confirmed live: `ls
.claude/settings.local.json` → `No such file or directory` in
`.claude/worktrees/doc-tag-enforcement`. It **does** exist in the main checkout
(`/home/u24desktop/Working/rpg-based-simulation/.claude/settings.local.json`, 10,713 bytes, last
modified Jul 17). This confirms the prior investigation's finding still holds and is a real,
current condition — not stale.

**Live schema and counts in the main-checkout file** (parsed directly, not estimated):
```
permissions.allow: 114 entries        (matches the ticket's own cited "114" exactly — NOT stale)
permissions.deny / permissions.ask: absent (permissions dict has only "allow")
enableAllProjectMcpServers: true
enabledMcpjsonServers: ["knowledge-search", "graphify"]
disabledMcpjsonServers: ["github"]
```
Confirms the ticket's Scope line 34 framing is accurate: the file's real top-level schema is exactly
4 fields (`permissions.allow` plus the 3 MCP fields), and a baseline that covers only
`permissions.allow` would miss 3 of the 4 fields entirely.

**`.gitignore` (repo-tracked) has no entry for `.claude/settings.local.json` anywhere** — confirmed
by full read of `.gitignore` (284 lines) and a targeted grep for `settings.local`, both empty. `git
check-ignore -v .claude/settings.local.json` resolves the ignore to
`/home/u24desktop/.config/git/ignore:1:**/.claude/settings.local.json` — the user's personal global
gitignore, not this repo's own. This confirms the ticket's flagged risk (Assumptions line 72) is
real, current, and unrelated to whether this ticket is implemented — it is correctly marked Out of
Scope to fix, not to ignore as a risk.

**`.claude/settings.json` (tracked, shared, NOT git-ignored) has its own, much smaller
`permissions.allow` list: 48 entries** (`python3 -c "...json.load..."` count). This is a materially
different number from the 114 in `settings.local.json` and is itself a candidate "already-reviewed,
already-committed" seed set for the approved envelope — see Risks below; the ticket does not say
whether the baseline should start from this file's 48 entries, from a manual curation of the live
114, or from something else entirely.

**Registry convention this ticket's Scope section names as the template** —
`tools/tag_registry.py` and `tools/layer_registry.py` (both read in full):
- `tools/tag_registry.py:151-153` `registry_path()` — stable location under `registries/`.
- `tools/tag_registry.py:156-179` `load_registry()` — parses one JSON object per line, raises
  `ValueError` on a duplicate key (append-only-uniqueness invariant enforced at read time, not just
  write time).
- `tools/tag_registry.py:187-196` `check_tags_registered()` — batch-check helper returning only the
  unregistered subset, used by the Scope phase for early failure.
- `tools/tag_registry.py:199-245` `add_tag()` — the sole writer; refuses to re-add an existing key;
  appends a `{tag, category, added_date, note}` object.
- `tools/layer_registry.py` mirrors this exactly, minus the `category` dimension (single-value
  `layer:` field, no further taxonomy split — see that module's own docstring, lines 12-20).
- Both live under `registries/*.jsonl` (`ls registries/`: `glossary_registry.jsonl`,
  `layer_registry.jsonl`, `tag_category_registry.jsonl`, `tag_registry.jsonl` — no
  `capability_envelope`-named file exists yet).
- `tests/tools/test_tag_registry.py` and `tests/tools/test_layer_registry.py` (both read in full)
  cover: canonical-form validation, duplicate-detection on load, append-only `add_*()` behavior,
  and the batch `check_*_registered()` helper — the direct template for this ticket's own new tests.

**A second, structurally different in-repo precedent also exists**: `tools/agent-monitoring/manifest.py`
(`capture_lines`/`assert_prefix_preserved`) plus `tools/agent_codex_pilot_guardrails/
baseline_manifest_gate.py`, which wraps it for a different ticket
(`TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS`). This pattern captures a **snapshot** of pre-existing
state and asserts nothing pre-existing was rewritten/reordered/deleted (only new appended lines are
tolerated) — a fundamentally different shape from tag/layer's "one independently-added unique key at
a time" model. The capability envelope this ticket needs is conceptually closer to a reviewed
*snapshot* of approved permission entries than to a growing list of independently-registered unique
tags — see Risks below, this is an open design question for the planner, not resolved by this
investigation.

**`.claude/agents/concern-investigator.md`** (read in full): the sole one of the repo's 16 agents
that currently declares a `tools:` frontmatter field (line 4: `tools: Read, Grep, Glob, Bash,
WebFetch, WebSearch, mcp__knowledge-search__search_docs`). This file is listed in the ticket's
Related Code Areas, but its content is about per-agent tool scoping (the *separate*, M3-gated
milestone in the parent epic), not about `settings.local.json`'s capability envelope at all — its
relevance to *this* ticket (M2) is only as supporting epic context (evidence that the M3 rollout
this ticket is NOT part of hasn't started), not a file this ticket reads for its own logic or
modifies.

**`docs/ai/codex_posttool_adapter_exact_config_diff_for_review.md`** (read in full): entirely about
a different feature — a Codex `PostToolUse` hook config diff, unrelated to capability envelopes or
`settings.local.json`. Its only relevance to this ticket is stylistic: it is the repo's existing
precedent for "compute and show the *exact* diff for human review; explicitly state what is and
isn't decided by the document; never silently apply it" — the same audit-only, no-enforcement
framing this ticket's own Scope explicitly requires. It contains zero content this ticket's
implementation would read or need to change.

**No script or committed baseline for a capability envelope exists anywhere** in either this
worktree or the main checkout — confirmed via `find -iname "*capability_envelope*"` returning
nothing repo-wide. This is genuinely new tooling, matching the ticket's own framing.

## Mechanics / Engine Constraints

Not applicable. This is pure agent-infrastructure governance tooling (`layer: ai`), touching no
`src/` simulation code. No `docs/mechanics/` chapter or `docs/engine/` contract constrains the shape
of a config-diff script; no Mechanics Bible law governs `.claude/settings.local.json`.

## Docs Requiring Update

- `docs/ai/capability_envelope_baseline.md`: new doc required — this is a brand-new feature (a
  version-controlled baseline file + diff script), and per this project's Authoritative Mechanics
  Rule / Definition of Done ("a brand-new feature still needs a doc describing it"), no existing
  doc anywhere currently describes this convention. Should document: the baseline file's schema/
  location/lifecycle, how to run the diff script, and its explicit audit-only/no-runtime-enforcement
  limitation (mirrored from the epic's own M2 acceptance signal).
- `docs/ai/README.md`: the Document Index table lists every doc under `docs/ai/` (see current rows
  for `system_overview.md`, `agents.md`, `workflows.md`, `skills.md`, `ticket-lifecycle.md`,
  `agent_infrastructure_audit.md`) — a new doc added under this directory needs a corresponding row
  added here, matching the file's own stated convention.
- `docs/parity_ledger/infrastructure.yaml`: a new entry is needed, per the established, same-day,
  same-epic precedent set by `TCK-20260904-AGENT-TOOL-USAGE-BASELINE` (parity ledger entry
  `INFRA-402`, added in that ticket's Parity phase). That sibling ticket's own investigation.md
  concluded "no parity entry needed" (reasoning "touches no `src/` files"), and the Parity phase
  independently reversed that conclusion, citing prior entries `INFRA-275`/`282`/`291`/`315` as
  establishing that `infrastructure.yaml` already tracks agent-infrastructure meta-tooling additions
  under the "Replay, telemetry, observability, workers" subsystem regardless of `src/` involvement.
  This investigation applies that lesson upfront: this ticket's new `tools/`-directory script and
  `registries/`-directory baseline file are the same shape of deliverable. Flagged here as Format-1
  required specifically to avoid repeating the same miss — final subsystem fit (governance/security
  config auditing vs. "telemetry/observability") should still be confirmed at the Parity phase, since
  it is a real judgment call, not a certainty (see Risks below).

The parent epic doc `docs/plans/agent_infrastructure/ai_first_hardening_epics/
governance_capability_policy_epic.md` (path, under `docs/`) is not required to change for this
ticket: this ticket's own Scope/Out-of-Scope sections list no edit to it, and the directly analogous
sibling M1 ticket in the same epic (`TCK-20260904-AGENT-TOOL-USAGE-BASELINE`) established the same
reasoning for the same epic doc and did not edit it either — a future scoping pass (e.g. at M3) is
the natural place to revise the epic doc's own prose.

`docs/ai/codex_posttool_adapter_exact_config_diff_for_review.md` (path, under `docs/`) is not
required to change: as detailed in Current Behavior above, it documents an entirely separate,
already-closed feature with zero content overlap with capability-envelope baselines; its presence in
this ticket's Related Docs/Code Areas is a stylistic precedent reference only.

`docs/ai/skills.md` (path, under `docs/`) is not required to change: it already documents
`/update-config` (line 170) as the generic tool for modifying `settings.json`/`settings.local.json`
directly; this ticket adds a separate, narrower auditable baseline+diff tool alongside that existing
config-editing skill — it does not change what `/update-config` itself does or documents.

## Parity Ledger Overlap

No existing `docs/parity_ledger/*.yaml` entry currently covers capability-envelope or
`settings.local.json` auditing (confirmed via targeted grep of `infrastructure.yaml` for
`capability_envelope` — no hits). The closest precedent entries are `INFRA-275`, `INFRA-282`,
`INFRA-291`, `INFRA-315`, `INFRA-400`, `INFRA-402` — all `status: verified`, `priority: P2`, under
the "Replay, telemetry, observability, workers" subsystem — for prior agent-infrastructure
meta-tooling additions under `tools/`. None is `P0`, so no pre-existing `test_path` is required to
keep passing as a gate for this ticket. A new entry (likely `verified`/`P2`, following the same
pattern) should be added once this ticket's script exists, citing the new script path(s) as
`v2_evidence` — see Docs Requiring Update above for the caveat that final subsystem fit should be
confirmed, not assumed, at the Parity phase.

## Prior Work

- `stored_artifacts/TCK-20260904-AGENT-TOOL-USAGE-BASELINE/{investigation.md,plan.md,test_plan.md}`
  — same epic (`governance_capability_policy_epic.md`), same day, the M1 sibling milestone
  ("gated on nothing, runs in parallel with" this M2 ticket per this ticket's own Request Summary).
  Direct structural precedent for: read-only audit-tool shape, a real-corpus zero-mutation test
  (`git status --porcelain` before/after), a `docs/agent-monitoring/README.md`-style doc-update
  pattern, and — critically — the exact parity-ledger-entry correction this investigation applies
  upfront (see above).
- `tools/tag_registry.py` + `tests/tools/test_tag_registry.py`, `tools/layer_registry.py` +
  `tests/tools/test_layer_registry.py` — the explicit registry convention this ticket's own Scope
  section names as the template to follow (documented lifecycle, stable `registries/` location,
  script-enforced canonical form and append-only-uniqueness).
- `tools/agent-monitoring/manifest.py` (`capture_lines`/`assert_prefix_preserved`) +
  `tools/agent_codex_pilot_guardrails/baseline_manifest_gate.py` — a second, structurally different
  in-repo precedent for "capture a baseline and fail on drift of anything pre-existing" (snapshot +
  prefix-preservation, not append-only unique-key registration). Worth the planner's explicit
  consideration since the capability envelope is conceptually closer to a reviewed snapshot than to
  an accreted list of independently-registered tags.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md`
  (§M2) — the parent epic milestone this ticket implements; already states the explicit
  "no confirmed runtime-enforcement mechanism" limitation and the acceptance signal this ticket must
  satisfy ("a versioned capability-envelope baseline file and a working diff script exist; running
  the diff against the current `settings.local.json` produces a real, reviewed report").

## Risks and Open Questions

- **Baseline file shape is genuinely undecided.** Tag/layer registries model an append-only list of
  independently-added unique string keys (one `add` CLI call at a time). The capability envelope is
  conceptually a reviewed snapshot of an approved state (a set of `permissions.allow` patterns plus 3
  MCP fields), closer to `manifest.py`'s capture/compare shape. This materially changes both the
  baseline file's own schema and the diff script's comparison logic. Flagged for the planner to
  decide explicitly in `plan.md`, not assumed here.
- **What seeds the initial baseline is unresolved and consequential.** `.claude/settings.json`
  (tracked, committed, already centrally reviewed) has 48 `permissions.allow` entries; the live
  `settings.local.json` has 114. If the baseline starts from the smaller 48-entry set, a first real
  diff run will immediately flag roughly 66+ existing entries as "outside the envelope" — a large,
  possibly-unwanted initial signal. If it instead starts from a manual review/grandfather of the
  current 114, that review work itself isn't scoped by this ticket's AC. This is a real product
  decision the ticket text does not resolve — do not assume either answer.
- **Exact-string vs. normalized comparison** (carried forward from the ticket's own Assumptions):
  the live file has near-duplicate command variants and very broad entries (e.g. `Read(//tmp/**)`,
  `Bash(find / -maxdepth 8 ...)`, `Bash(gh api *)`, `Bash(ps *)`). An exact-string diff and a
  normalized/pattern-aware diff will produce materially different false-positive/negative rates.
  Must be an explicit, documented design decision in `plan.md`, not an implicit default.
- **Diff-script target-file resolution is untested by this investigation's own environment.** This
  worktree has no `settings.local.json` at all — a real, live instance of the "file doesn't exist
  here" case the ticket's own Assumptions flag (per-machine/per-worktree divergence). The diff
  script must define unambiguously which path it targets (explicit `--path` argument recommended)
  and must handle a missing target file as a clean, reported condition, not an unhandled exception —
  this is directly testable using this very worktree as a real negative-path fixture.
- **`docs/parity_ledger/infrastructure.yaml` entry's subsystem fit is a judgment call**, not a
  certainty — flagged as Format-1-required above specifically because the immediately-preceding
  sibling ticket in this same epic got this wrong at investigation time and had to be corrected at
  Parity; but this ticket's actual subject (settings/permission-envelope auditing) is a less
  obvious fit for "Replay, telemetry, observability, workers" than M1's agent-monitoring
  tools.jsonl aggregator was. Confirm at Parity phase rather than treating this investigation's
  recommendation as settled.

## Anti-Drift Hazards

- **Do not build any actual runtime-enforcement mechanism.** Explicitly Out of Scope per both the
  ticket and the epic doc's own M2 scope text ("this review found no confirmed mechanism in the
  current harness to enforce the ⊆ relationship automatically at runtime"). The script is auditable
  tooling only — every AC and the epic's own M2 acceptance signal require this to be stated in the
  script's own docstring/output, not just in this investigation.
- **Do not fix the `settings.local.json` git-ignore gap** (adding it to the repo's tracked
  `.gitignore`) — confirmed real and current (see Current Behavior), but explicitly listed Out of
  Scope; flag it, do not resolve it.
- **Do not touch `.claude/settings.json`'s hooks mechanism** — explicitly Out of Scope.
- **Do not scope-creep into M3 (per-agent `tools:` frontmatter rollout) or M4 (Bash secret-exposure
  hook)** — both are separate, gated milestones in the same epic; `concern-investigator.md`'s
  `tools:` field is relevant only as epic context, not something this ticket modifies or depends on.
- **Do not hardcode the 114-entry or 48-entry counts anywhere in the implementation.** Both numbers
  are already live-verified-accurate as of this investigation but will drift — mirrors the sibling
  M1 ticket's own explicit finding that its cited corpus numbers were already stale one day later.
  The script must compute both counts live.
- **Do not assume `settings.local.json` always exists.** This worktree is direct, current proof that
  it does not always exist — the diff script's handling of that case is a real behavior to test, not
  a hypothetical edge case.
