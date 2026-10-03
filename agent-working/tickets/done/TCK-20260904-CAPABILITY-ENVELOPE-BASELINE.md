---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260904-CAPABILITY-ENVELOPE-BASELINE
phase: done
date: 2026-09-04
tags: [governance, ai, security]
---

# TCK-20260904-CAPABILITY-ENVELOPE-BASELINE

## Title
Capability-envelope baseline file and auditable diff check

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P0

## Request Summary
Per the frozen proposal's configuration-precedence invariant ("effective local capability ⊆ approved capability envelope"), commit a version-controlled baseline file describing the approved capability envelope, kept separate from the git-ignored settings.local.json. Write a small auditable comparison script that diffs the live settings.local.json against that baseline and flags any entry outside it. This is explicitly auditable tooling only — there is no confirmed runtime-enforcement mechanism today, so the ticket must not claim to provide a proven runtime guarantee. Gated on nothing, runs in parallel with the tool-usage baseline audit ticket.

## Scope
- New version-controlled baseline file describing the approved capability envelope, following the tag_registry.py/layer_registry.py registry convention (documented lifecycle, stable location, script-enforced)
- Baseline covers all of settings.local.json's schema fields: permissions.allow plus the enableAllProjectMcpServers/enabledMcpjsonServers/disabledMcpjsonServers fields — not just permissions.allow
- New diff script comparing the live .claude/settings.local.json against the committed baseline and flagging any out-of-envelope entry
- Script/report output explicitly states its audit-only, no-runtime-enforcement nature in its own docstring or printed output

## Out of Scope
- Any change to settings.json's hooks mechanism
- Fixing settings.local.json's git-ignore coverage gap (only the user's personal global gitignore covers it today, not the repo's own tracked .gitignore) — flagged as a related risk, not fixed here
- Building or claiming any actual runtime-enforcement mechanism

## Acceptance Criteria
- [x] Baseline file covers all settings.local.json schema fields observed in the live file (permissions.allow plus the 3 MCP server fields), not just permissions.allow
- [x] Diff script run against the real settings.local.json (114 permissions.allow entries as of investigation) produces a real, non-stub report
- [x] Diff script/report explicitly states audit-only / no-runtime-enforcement in its own output or docstring
- [x] Positive and negative control cases both verified: a clean-baseline input produces an empty/clean result, and an out-of-envelope entry produces a flagged result

## Related Tickets
- No duplicate or overlapping ticket found

## Related Docs
- docs/plans/agent_infrastructure/ai_first_hardening_epics/governance_capability_policy_epic.md
- docs/ai/codex_posttool_adapter_exact_config_diff_for_review.md

## Related Stored Artifacts
None.

## Related Code Areas
- .claude/settings.local.json
- .claude/settings.json
- .gitignore
- docs/ai/codex_posttool_adapter_exact_config_diff_for_review.md
- tools/tag_registry.py
- tools/layer_registry.py
- .claude/agents/concern-investigator.md
- tests/tools/test_tag_registry.py
- tests/tools/test_layer_registry.py

## Assumptions / Open Questions
- The frozen proposal's "~70 permissions" figure is stale — the real live count is 114 entries; baseline scoping must be derived from current live data, not the proposal's stale figure
- settings.local.json's git-ignore status is only enforced by the user's personal global ~/.config/git/ignore, not this repo's own tracked .gitignore — a real gap worth flagging even though fixing it is explicitly out of scope
- settings.local.json differs per machine/worktree (this worktree currently has none) — the diff script must define unambiguously which file/path it targets
- The live file has near-duplicate command variants and some very broad entries (e.g. Read(//tmp/**), Bash(find / -maxdepth 8 ...), Bash(gh api *), Bash(ps *)) — exact-string vs. normalized comparison design materially affects false-positive/negative rate and must be an explicit design decision

## Implementation Notes

Implemented `staging_artifacts/TCK-20260904-CAPABILITY-ENVELOPE-BASELINE/plan.md`'s 8 steps in
order, following `tools/tag_registry.py`/`tools/layer_registry.py`'s registry convention exactly:

- **Step 1/2 (registry core + typed `reviewed` field)**: `tools/capability_envelope_baseline.py`
  defines `FIELDS` (the 4 real `settings.local.json` top-level fields), `load_registry()` keyed on
  `(field, value)` tuples (raises `ValueError` on a duplicate key found on disk), and `add_entry()`
  which raises on an unknown field or an already-registered `(field, value)` pair. `add_entry`
  defaults `reviewed=True` (a direct CLI `add` is a deliberate, individually-reviewed governance
  addition); `seed_registry` calls `add_entry(..., reviewed=False, ...)` for every flattened entry
  and swallows the `ValueError` for already-registered pairs (idempotent bulk bootstrap, a
  deliberately different contract from `add_entry`'s raise-on-duplicate). This is the exact fix the
  architecture review's NEEDS_CHANGES finding required: the reviewed/unreviewed fact is a typed
  `bool` field on disk, never recovered by parsing `note`'s prose.
- **Step 2 (parsing)**: `load_settings_local()` returns `None` for a missing file instead of
  raising; `extract_entries()` flattens all 4 schema fields (`permissions.allow` list,
  `enableAllProjectMcpServers` scalar, `enabledMcpjsonServers`/`disabledMcpjsonServers` lists) into
  `(field, value)` tuples.
- **Step 3 (diff/report)**: `compute_diff()` treats all 4 fields uniformly (including the scalar
  `enableAllProjectMcpServers` as a one-element set, no special-cased boolean branch), returning
  `in_envelope`/`out_of_envelope` per field; `{"status": "no_local_file", "fields": {}}` when the
  live file is absent. `build_report()` adds a top-level `audit_only_disclaimer` string to every
  report.
- **Step 4 (CLI)**: `argparse` subcommands `add`/`seed`/`list`/`diff`, mirroring
  `tag_registry.py`'s CLI shape. `--settings-path` defaults to
  `REPO_ROOT / ".claude" / "settings.local.json"`, always overridable. No subcommand ever writes to
  any `settings*.json` file — the only file this module writes is
  `registries/capability_envelope_registry.jsonl`.
- **Step 5 (seed the real baseline)**: ran
  `python3 tools/capability_envelope_baseline.py seed --settings-path
  /home/u24desktop/Working/rpg-based-simulation/.claude/settings.local.json --note "..."` once
  against the real main-checkout file (this worktree has none). Appended 118 entries: 114
  `permissions.allow` + 1 `enableAllProjectMcpServers` + 2 `enabledMcpjsonServers` + 1
  `disabledMcpjsonServers`, every one `reviewed: false`, every `note` disclosing the grandfathered/
  unreviewed provenance. Committed `registries/capability_envelope_registry.jsonl`.
- **Step 6 (tests)**: `tests/tools/test_capability_envelope_baseline.py`, all 9 tests from
  `test_plan.md` plus the architecture-review's added `reviewed`-field test. Synthetic tests use
  `tmp_path` root overrides; the real-corpus and read-only-guard tests run against the real main-
  checkout `settings.local.json` and the committed registry.
- **Step 7 (regression sweep)**: all 4 scoped pytest commands run via
  `.venv/bin/python3 -m pytest` (bare `python3` lacks `pydantic`, needed by `tests/conftest.py`) —
  9/9, 50/50 (tag+layer), 10/10 (sibling M1), 72/72 (combined `-k` sweep). All green.
- **Step 8 (docs)**: new `docs/ai/capability_envelope_baseline.md` (schema, lifecycle, both
  Resolved Design Questions in plain terms, CLI reference, disclosed known limitations); one new row
  added to `docs/ai/README.md`'s Document Index. `docs/parity_ledger/infrastructure.yaml` was
  explicitly deferred to the later Parity phase per direct instruction — not touched by this
  implementer run (see `plan.md`'s new Deviations section). Ran `make knowledge-index-update` and
  `graphify update .` since `docs/`/`tools/`/`tests/` files changed.

## Test Summary

`pytest tests/tools/test_capability_envelope_baseline.py -v` — 9/9 passed (all tests from
`test_plan.md` plus the architecture-review's `reviewed`-field test:
`test_seeded_entries_marked_unreviewed_and_manual_adds_marked_reviewed`).

Regression sweep (all via `.venv/bin/python3 -m pytest`, since bare `python3` lacks `pydantic`):
- `tests/tools/test_tag_registry.py tests/tools/test_layer_registry.py -v` — 50/50 passed.
- `tests/tools/test_agent_tool_usage_baseline.py -v` (same-day sibling M1 ticket) — 10/10 passed.
- `tests/tools/ -k "capability_envelope or tag_registry or layer_registry or agent_tool_usage" -v`
  — 72/72 passed.

No existing test was modified.

## Files Changed

- `tools/capability_envelope_baseline.py` (new) — registry core, live-file parsing, diff/report
  logic, CLI.
- `tests/tools/test_capability_envelope_baseline.py` (new) — 9 tests.
- `registries/capability_envelope_registry.jsonl` (new, committed data file) — 118 seeded entries.
- `docs/ai/capability_envelope_baseline.md` (new).
- `docs/ai/README.md` (modified) — one new Document Index row.
- `staging_artifacts/TCK-20260904-CAPABILITY-ENVELOPE-BASELINE/plan.md` (modified) — Revision
  History section (typed `reviewed` field added per architecture-review NEEDS_CHANGES fix) and
  Deviations section (parity-ledger-entry deferral, later resolved — see below).
- `tickets/inprogress/TCK-20260904-CAPABILITY-ENVELOPE-BASELINE.md` (this file, modified) —
  Status, Acceptance Criteria checkboxes, Implementation Notes, Test Summary, Files Changed,
  Completion Summary.
- `docs/parity_ledger/infrastructure.yaml` (modified, by this ticket's own Parity phase, after
  Implement) — new `INFRA-403` entry (verified, P2), citing `tools/capability_envelope_baseline.py`
  and `docs/ai/capability_envelope_baseline.md` as `v2_evidence`. This was **not** yet touched at
  Implement time (deferred per plan.md's Deviations section), which is why an earlier draft of this
  section listed it as untouched — corrected here now that Parity has actually run.
- `docs/REGISTRY.yaml` (modified, by this ticket's own Verify phase) — regenerated via `make
  docs-registry` after the Test phase's regression sweep surfaced a temporary registry-drift test
  failure (the registry hadn't yet been regenerated to reflect the new `docs/ai/
  capability_envelope_baseline.md` doc). Regeneration is a sanctioned mid-session action per
  CLAUDE.md; re-running the specific failing test afterward confirmed it now passes.

Not touched by this run (pre-existing, unrelated changes from a concurrent session's same-day
sibling ticket TCK-20260904-AGENT-TOOL-USAGE-BASELINE already present in this shared worktree):
`docs/agent-monitoring/README.md`, `tickets/done/TCK-20260904-AGENT-TOOL-USAGE-BASELINE.md`,
`tools/agent-monitoring/agent_tool_usage_baseline.py`,
`tests/tools/test_agent_tool_usage_baseline.py`,
`stored_artifacts/TCK-20260904-AGENT-TOOL-USAGE-BASELINE/`.

## Completion Summary

Built `tools/capability_envelope_baseline.py`, a new append-only registry-and-diff tool
(`registries/capability_envelope_registry.jsonl`) that records the approved capability envelope for
all 4 of `.claude/settings.local.json`'s schema fields (`permissions.allow` plus the 3 MCP fields),
following the `tag_registry.py`/`layer_registry.py` convention exactly, including a typed
`reviewed: bool` field (added by an architecture-review revision) that durably distinguishes
individually-reviewed `add`-CLI entries from bulk-seeded, unreviewed entries. Seeded the baseline
once from the real main-checkout `settings.local.json` (118 entries, all `reviewed: false`,
disclosed as a grandfathered snapshot). The `diff` CLI subcommand produces a real, non-stub,
audit-only report (every report carries an explicit `audit_only_disclaimer`) comparing a live
settings file against the registry, uniformly across all 4 fields. All 9 new tests pass, plus the
full `tests/tools/` regression sweep (2711 passed; the only non-pre-existing failure, a
`docs/REGISTRY.yaml` drift check, was root-caused to the registry not yet reflecting the new doc
and resolved by regenerating it via `make docs-registry`, confirmed by re-running that test). New
doc `docs/ai/capability_envelope_baseline.md` plus a `docs/ai/README.md` index row were added. The
parity-ledger entry, initially deferred to the Parity phase per explicit instruction, was
subsequently added there as `INFRA-403` (verified, P2) once that phase ran. Went through one
architecture-review revision cycle (initial NEEDS_CHANGES on the `reviewed` field's typing →
fixed → re-reviewed APPROVED) and one Security-Review pass (APPROVED, one informational
non-blocking note on a path fragment in seeded data, already disclosed as part of the
grandfathered-seed design) — both documented in plan.md's Revision History.
