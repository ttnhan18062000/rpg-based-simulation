---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-DOCS-SWEEP
artifact_type: plan
tags: [agent-monitoring, observability, documentation, claude-md]
---

# Implementation Plan — TCK-20260903-MONITORING-DATA-DOCS-SWEEP

## Summary

This is a pure prose/config sweep: correct every doc/skill/workflow-prose location that still
asserts one of the 3 retired `agent-monitoring/*.jsonl` physical shapes (monolithic
`runs.jsonl`/`events.jsonl`/`tools.jsonl`, or the intermediate `tools/tools-YYYY-Www.jsonl` shard)
as *current*, replacing each with the real, landed `agent-monitoring/data/YYYY-Www/{runs,events,
tools}.jsonl` layout — while leaving every dated "how we got here" historical citation untouched.
18 concrete locations across 13 files are in scope, re-verified against the live worktree this
session (all line numbers below were re-grepped just now and are unchanged from investigation.md —
no drift). Two locations investigation.md flagged as candidates are explicitly **not** edited: the
`schema.md` Join Example (already fixed by a just-landed sibling commit) and `.gitattributes`
(already clean). The plan closes with the `INFRA-291` parity-ledger addendum (via the sanctioned
writer only) and the mandatory `make knowledge-index-update` run.

## Steps

### Step 1 — Fix `CLAUDE.md`'s 4 stale monitoring-write claims
**Files:** `CLAUDE.md`
**Change:** Re-verified this session, unchanged from investigation.md:
- Line 94: `- **Always stage \`agent-monitoring/\` (including \`tools.jsonl\`) in every commit** — the monitoring tools auto-update \`tools.jsonl\` on every run; never leave it as an unstaged modification.` — reword to describe staging `agent-monitoring/` broadly (the per-week `data/YYYY-Www/{runs,events,tools}.jsonl` shards), not a bare `tools.jsonl` file.
- Line 137: `` `agent-monitoring/tools.jsonl` is rewritten by a hook on nearly every tool call `` — reword to name the current per-week `data/YYYY-Www/tools.jsonl` shard path (the hook still rewrites *a* file on nearly every tool call, just not that literal path today).
- Line 140: `` (`git add agent-monitoring/tools.jsonl && git commit -m "..." && git checkout -b <branch>` `` — update the example command to `git add agent-monitoring/data/` (directory-level stage, since the exact current week's shard filename is a moving target and the existing convention elsewhere in this repo's docs — see README.md's Navigation table, already fixed — stages/describes at the `data/` root, not a single shard file).
- Line 254 (Definition of Done checklist): `` run entry in `agent-monitoring/runs.jsonl`, at least one event in `agent-monitoring/events.jsonl` `` — reword to `agent-monitoring/data/YYYY-Www/runs.jsonl` and `.../events.jsonl` (per-week shard), keeping the parenthetical "(guaranteed by workflow — not verified by done-checker)" unchanged.
**Do NOT touch:** Any other line in `CLAUDE.md` outside these 4 (e.g. the Worktree & Branch Isolation section's own separate `agent-monitoring/tools.jsonl` race-condition note further down — re-check at implementation time whether that note also needs the same word-for-word fix; if found, treat as a 5th sub-edit of this same step, not a scope expansion, since it's the same file and same underlying fact).
**Verify:** Test plan command 3 (`grep -n "tools\.jsonl\|runs\.jsonl\|events\.jsonl" CLAUDE.md`) — every surviving line must describe the `data/YYYY-Www/` layout, not a bare single-file path.

### Step 2 — Fix `docs/agent-monitoring/schema.md`'s intro line and 3 section headers (NOT the Join Example)
**Files:** `docs/agent-monitoring/schema.md`
**Change:** Re-verified this session:
- Line 11: `Two append-only JSONL files, joined by \`run_id\`.` — factually wrong on 2 counts (confirmed by reading the file's own per-source sections immediately below, already correctly describing 3 sources): it's 3 sources (runs/events/tools) per week, not 2, and `tools` additionally joins on `seq` (not `run_id` alone). Reword to state 3 append-only JSONL sources per ISO week, joined by `run_id` (and `tools` additionally by `seq`).
- Line 50: `## \`agent-monitoring/runs.jsonl\`` — reword header to name the logical source (e.g. `## \`runs\` (agent-monitoring/data/YYYY-Www/runs.jsonl)`), matching the body prose immediately below (already correct per child 1/2's edits) rather than asserting a bare monolithic path.
- Line 139: `## \`agent-monitoring/events.jsonl\`` — same header-style fix for the `events` source.
- Line 368: `## \`agent-monitoring/tools.jsonl\`` — same header-style fix for the `tools` source.
**Do NOT touch:** The Join Example block at lines 470-502 (confirmed this session via `grep -n "glob(" docs/agent-monitoring/schema.md` → lines 478/482/489 already do `Path('agent-monitoring/data').glob('*/runs.jsonl')`-style unified globbing — this was fixed by commit `76096246`, `TCK-20260903-MONITORING-DATA-CONSUMERS-CORE`, landed after this ticket was scoped. Re-editing it is scope creep / risk of regression, not a required fix. Confirm with `git diff docs/agent-monitoring/schema.md | grep -A3 -B3 "Join Example\|glob('\*/"` showing **no changes** to that hunk.
**Verify:** Test plan command 1 and 2 (grep sweeps) — no current-state hits remain in this file; manual read confirms the 3 headers now match their body prose's already-correct per-week description.

### Step 3 — Fix `docs/agent-monitoring/README.md`'s 2 intermediate-shard-shape lines
**Files:** `docs/agent-monitoring/README.md`
**Change:** Re-verified this session:
- Line 19: `` - Every individual tool call during a session: tool name, input summary, status, duration (`tools/tools-YYYY-Www.jsonl`, one shard file per UTC ISO week) `` — this describes the *intermediate* (2026-09-02) flat-shard shape, already superseded by the 2026-09-03 unification. Reword to `agent-monitoring/data/YYYY-Www/tools.jsonl` (per-week, alongside `runs`/`events` in the same week folder).
- Line 54: `` JSON report over the same `runs.jsonl`/`events.jsonl`/`tools/tools-YYYY-Www.jsonl` sources. `` — same intermediate-shape staleness; reword to the unified 3-source-per-week description.
**Do NOT touch:** Line 17-18's bare `runs.jsonl` mention (logical shorthand, same accepted convention as the "What It Captures" bullets — this is the established precedent from the prior tools-only epic, per investigation.md's "Already clean, confirmed" section) or line 148's Navigation table entry (already fixed — re-confirmed this session, reads "Full field reference for the `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl` per-week layout"). Do not touch lines 128-129/138's "Deliberately reads `runs.jsonl` directly rather than through `generate_retro`'s SQLite-index path" passage — this describes a script's read-strategy choice using the accepted logical-shorthand convention, not a current-physical-layout claim; not in investigation.md's confirmed-stale list.
**Verify:** Test plan command 1/2 grep sweeps return zero current-state hits on lines 19/54 post-edit.

### Step 4 — Fix `docs/guides/agent_monitoring.md`'s 3 bare/monolithic current-write-path claims
**Files:** `docs/guides/agent_monitoring.md`
**Change:** Re-verified this session:
- Line 11: `` The retro process transforms raw `runs.jsonl` + `events.jsonl` into a structured improvement cycle. `` — reword to name the per-week `data/YYYY-Www/{runs,events}.jsonl` sources.
- Line 24: `` `agent-monitoring/runs.jsonl` whose `start_ts`/`started_at` is later than the `` — reword to the per-week path.
- Line 150: `` `tickets/working_log.csv` rows and `agent-monitoring/runs.jsonl` records for `` — reword to the per-week path.
**Do NOT touch:** Line 165's `` `runs.jsonl` record, for any child, at any time) is **never** flagged stale, `` — this is conceptual/contextual prose about *a* runs record generically, not investigation.md's confirmed-stale list (only 11/24/150 were confirmed); leave as-is unless a closer read at implementation time finds it genuinely asserts the retired bare path as a current physical location, in which case treat it as a 4th sub-edit of this same step (same file, same fact), not scope creep.
**Verify:** Test plan command 1/2 grep sweeps.

### Step 5 — Rewrite `docs/ai/system_overview.md` §6's file-shape description (most stale doc)
**Files:** `docs/ai/system_overview.md`
**Change:** Re-verified this session (lines unchanged from investigation.md). The block at lines 229-247 currently reads (confirmed via `grep -n "runs.jsonl\|events.jsonl\|tools.jsonl\|tools/tools-" docs/ai/system_overview.md`):
- Lines 232-234: "two single files (`runs.jsonl`, `events.jsonl`) plus a sharded family of tool-call files, one per UTC ISO week (`agent-monitoring/tools/tools-YYYY-Www.jsonl`):" — this describes the **Sept-2 intermediate** shape (2 monolithic + 1 sharded), not even the pre-epic monolithic-3-file shape this epic started from. This is the single most stale claim found in the whole sweep.
- Line 236: `- **\`runs.jsonl\`** — one record per workflow invocation...`
- Lines 238-240: `` not recorded — a documented gap — but `events.jsonl`'s `cost_proxy_score` (below) `` and `- **\`events.jsonl\`** — one record per agent call...`
- Line 244: `` - **\`tools/tools-YYYY-Www.jsonl\`** — one record per tool call, keyed to events via `run_id`+`seq` ``
Rewrite this whole bulleted block (lines ~229-247) to describe the unified layout: 3 append-only JSONL sources (`runs`, `events`, `tools`) all under `agent-monitoring/data/YYYY-Www/`, one week-folder per UTC ISO week, joined by `run_id` (and `tools` additionally by `seq`) — mirror the corrected `schema.md` intro line from Step 2 for consistency of phrasing across docs, but keep this section's own surrounding context (§6 "Observability and Where to Go Deeper") and any other prose in that section not about physical file shape unchanged.
**Do NOT touch:** Any other section of `system_overview.md` outside §6's file-shape bullets — this ticket does not do a general accuracy pass on the whole document.
**Verify:** Test plan command 1/2 grep sweeps return zero hits in this file; manual read confirms the block now matches the real 3-source-per-week layout, not the Sept-2 intermediate shape.

### Step 6 — Fix `docs/ai/ticket-lifecycle.md`'s 4 current-write-target claims (file missed by the ticket's own Related Docs list)
**Files:** `docs/ai/ticket-lifecycle.md`
**Change:** Re-verified this session, unchanged from investigation.md:
- Line 578: `` 7. **Write agent monitoring records** (`writeMonitoring`): appends one run entry to `agent-monitoring/runs.jsonl` and one event per phase to `agent-monitoring/events.jsonl` — status is `DONE`... `` — reword the two bare paths to the per-week `data/YYYY-Www/{runs,events}.jsonl` form.
- Line 628: `` **Batch monitoring:** A single batch run record (prefixed `EPIC-` or `FOLDER-`) is written to `agent-monitoring/runs.jsonl` in addition to the per-ticket run records. `` — same fix.
- Line 639: `` - `agent-monitoring/runs.jsonl` — one run record: `run_id`, timestamps, tier, `final_status`, phase event count `` — same fix.
- Line 640: `` - `agent-monitoring/events.jsonl` — one event per phase: phase name, agent name, status, summary `` — same fix.
**Do NOT touch:** Line 632's "Epic staleness check" paragraph, which also contains a bare `agent-monitoring/runs.jsonl` mention inside a longer sentence about `epic_staleness_check.py` — re-check at implementation time whether this specific bare mention needs the same fix (it reads as a current-state claim, same family as 578/628/639/640, just not separately itemized by investigation.md); if so, treat as part of this same step, not a new one.
**Verify:** Test plan command 1/2 grep sweeps.

### Step 7 — Fix `docs/ai/workflows.md`'s 3 current-write-path claims (file missed by the ticket's own Related Docs list)
**Files:** `docs/ai/workflows.md`
**Change:** Re-verified this session, unchanged from investigation.md:
- Line 140: `` - `agent-monitoring/runs.jsonl` + `events.jsonl` (one run record + per-phase events) `` — reword to per-week form.
- Line 203: `` - `agent-monitoring/runs.jsonl` — one batch run record (`EPIC-{id}` or `FOLDER-{path}`) `` — reword to per-week form.
- Line 204: `` - `agent-monitoring/events.jsonl` — one event per child ticket `` — reword to per-week form.
**Do NOT touch:** Line 94's "check_monitoring_write_recorded (confirms the agent-monitoring write, `runs.jsonl`/`events.jsonl`, for this run landed)" — re-verified this session: this is a bare, unprefixed mention (no literal `agent-monitoring/` immediately before `runs.jsonl`) describing what the advisory check looks for conceptually, matching the accepted "logical shorthand" convention `docs/agent-monitoring/README.md` already establishes (per investigation.md's "Already clean, confirmed" precedent) — not itemized in investigation.md's confirmed-stale list, and it does not match either of the test plan's 2 grep patterns (it lacks the `agent-monitoring/` prefix directly before `runs.jsonl`). Leave unchanged.
**Verify:** Test plan command 1/2 grep sweeps.

### Step 8 — Fix `docs/ai/agents.md`'s 1 current-write-target claim (file missed by the ticket's own Related Docs list)
**Files:** `docs/ai/agents.md`
**Change:** Re-verified this session, unchanged from investigation.md. Line 279: `` `docs/parity_ledger/` and records any discrepancy in `agent-monitoring/events.jsonl` — visibility `` (parity-updater agent description) — reword to the per-week `data/YYYY-Www/events.jsonl` form.
**Do NOT touch:** Nothing else in this file was flagged; do not do a broader accuracy pass.
**Verify:** Test plan command 1/2 grep sweeps.

### Step 9 — Fix `.claude/skills/implement-ticket/SKILL.md`'s write-discipline rule (file missed by the ticket's own scoping)
**Files:** `.claude/skills/implement-ticket/SKILL.md`
**Change:** Re-verified this session, unchanged from investigation.md. Line 76: `` - Never write to `agent-monitoring/runs.jsonl` or `events.jsonl` directly — always go through `record_run.py` / `record_events.py` `` — the *rule itself* (never write directly, always go through the recorder scripts) stays completely correct and must not be softened; only the bare path names need updating to the per-week `data/YYYY-Www/{runs,events}.jsonl` form.
**Do NOT touch:** The rule's substance (the "always go through record_run.py/record_events.py" discipline) — only the path names change.
**Verify:** Test plan command 1/2 grep sweeps.

### Step 10 — Fix `.claude/skills/simq-audit/SKILL.md`'s identical write-discipline rule
**Files:** `.claude/skills/simq-audit/SKILL.md`
**Change:** Re-verified this session, unchanged from investigation.md. Line 77: same rule text as Step 9 (`` Never write to `agent-monitoring/runs.jsonl` or `events.jsonl` ``) — identical fix, identical do-NOT-touch note (rule substance unchanged, only path names).
**Do NOT touch:** Same as Step 9.
**Verify:** Test plan command 1/2 grep sweeps.

### Step 11 — Fix `.claude/skills/agent-monitoring-retro/SKILL.md`'s frontmatter description and body (file the ticket itself flagged as "not yet checked")
**Files:** `.claude/skills/agent-monitoring-retro/SKILL.md`
**Change:** Re-verified this session, unchanged from investigation.md:
- Line 3 (frontmatter `description:`): `` Generate the agent monitoring retro report from accumulated runs.jsonl/events.jsonl data. `` — reword to reference the per-week `data/YYYY-Www/{runs,events}.jsonl` sources (keep the rest of the description — cadence trigger conditions — unchanged).
- Lines 8-9 (body): `` Runs `make agent-monitoring-retro` to turn raw `agent-monitoring/runs.jsonl` and `agent-monitoring/events.jsonl` records into a structured retro report, then `` — same path fix.
**Do NOT touch:** Anything else in this skill file outside the frontmatter `description` and these 2 body lines.
**Verify:** Test plan command 1/2 grep sweeps.

### Step 12 — Fix `.claude/workflows/implement-ticket.js`'s 2 prose-only stale lines (NO functional JS change)
**Files:** `.claude/workflows/implement-ticket.js`
**Change:** Re-verified this session via `sed -n '380,390p'` and `sed -n '1700,1710p'`, unchanged from investigation.md:
- Line 385 (inside a prompt template string, itself inside a comment-like instructional block): `` Do NOT compute or set "tool_call_count"/"cost_proxy_score" yourself — record_events.py now computes both deterministically from agent-monitoring/tools.jsonl ground truth at write time `` — reword the bare `agent-monitoring/tools.jsonl` reference to the per-week `data/YYYY-Www/tools.jsonl` form. This is prose inside a template string passed to an agent, not executable logic.
- Line 1706 (the `monitoringWarning` fallback message, user-facing diagnostic text): `` : \`WARNING: agent-monitoring write for this run could not be verified (${monitoringWarning}). Ticket is otherwise complete — investigate agent-monitoring/runs.jsonl and events.jsonl manually.\` `` — reword the bare paths to the per-week form so a human following this diagnostic message looks in the right place.
**Do NOT touch:** Any other line in this file, including the comment blocks at lines 44-49, 265-272, 362-370, 560-573 — confirmed this session (and by investigation.md) these already read as generic/conceptual references to "the tools data" and do not assert a specific current physical layout; editing them would be unnecessary scope creep. Do not change any executable JS statement, control flow, or function signature anywhere in this file — confirmed (investigation.md, re-confirmed this session by reading the two target contexts) that all real file I/O on these paths happens inside the Python tools this file shells out to (`record_run.py`, `record_events.py`, `seq_offset.py`), never inline in this JS file itself.
**Verify:** Test-plan's dedicated guard command: `git diff .claude/workflows/implement-ticket.js` — manually confirm every changed line is inside a string literal / prompt text, never a bare executable statement. Also test plan command 1/2 grep sweeps.

### Step 13 — Fix `docs/testing/regression_policy.md`'s bare `tools.jsonl` current-state claim (found only by the broader bare-pattern sweep, missed by the ticket's own AC grep)
**Files:** `docs/testing/regression_policy.md`
**Change:** Re-verified this session, unchanged from investigation.md. Line 68 (Zero-invocation skill-staleness assertions row): `` these 2 tests cross-reference the real `.claude/skills/*/SKILL.md` catalog against real `agent-monitoring/tools.jsonl` invocation history via `compute_zero_invocation_skill_flags()` `` — reword the bare `agent-monitoring/tools.jsonl` reference to the per-week `data/YYYY-Www/tools.jsonl` (or "per-week `tools.jsonl` shards," matching this table row's own narrative style) form.
**Do NOT touch:** The rest of this row's or table's content (the soft-warning mechanism description, test IDs, grace-period rationale) — only the stale path reference.
**Verify:** Test plan command 2 (the bare-`tools.jsonl` gap-pattern grep) specifically catches this one — confirm it returns zero hits in this file post-edit.

### Step 14 — Confirm `.gitattributes` needs no edit (verification-only step, no file change)
**Files:** `.gitattributes` (read-only confirmation)
**Change:** Re-verified this session via `cat .gitattributes`: exactly one unified glob line (`agent-monitoring/data/*/*.jsonl merge=union`), the explanatory comment, `tickets/working_log.csv merge=union`, and the `docs/REGISTRY.yaml` exclusion note. Zero legacy `merge=union` lines for `agent-monitoring/runs.jsonl`, `events.jsonl`, or `tools.jsonl` remain. **No edit is made in this step** — it exists in the plan only to record that the AC's `.gitattributes` requirement is satisfied by the current state, and to head off an implementer "confirming by touching it" (explicit anti-drift hazard from investigation.md).
**Do NOT touch:** `.gitattributes` — any diff to this file in the final changeset is a plan violation (investigation.md: "a no-op diff there would be scope creep").
**Verify:** Test plan command 4 (`cat .gitattributes`) plus `git diff --stat .gitattributes` showing no changes.

### Step 15 — Append the `INFRA-291` addendum via `tools/parity_ledger_writer.py::write_entry()` (sanctioned writer only)
**Files:** `docs/parity_ledger/infrastructure.yaml` (written only through `tools/parity_ledger_writer.py`, never via raw `Edit`/`Write`)
**Change:** `INFRA-291`'s full current entry was read this session (`docs/parity_ledger/infrastructure.yaml:6391-6562`) and already carries 3 addenda in its `divergence_note` field, each following the identical pattern:
```
**Addendum (TCK-<id>, <date>):** <prose>
```
appended as a new paragraph (blank line, then the bolded addendum header, then prose, then a trailing blank line) to the *end* of the existing `divergence_note` string, with every other field (`id`, `text`, `status: verified`, `priority: P2`, `legacy_evidence: null`, `v2_evidence`, `test_path`, `support_boundary`) carried forward byte-identical from the current entry.

Implementation procedure (matches the 3 prior addenda's own established mechanism, per investigation.md "Prior Work"):
1. Read the full current `INFRA-291` entry from `docs/parity_ledger/infrastructure.yaml:6391-6562` (or its current line range at implementation time — re-locate by `id: INFRA-291`, not by these line numbers, since a prior addendum shifts everything below it) into a Python dict — via `yaml.safe_load()` on the shard file, then select the entry whose `id == "INFRA-291"`.
2. Append a 4th paragraph to that entry's `divergence_note` field, following the exact 3-prior-addenda format:
   ```
   **Addendum (TCK-20260903-MONITORING-DATA-DOCS-SWEEP, 2026-09-04):** this entry's own physical-layout
   description (fully reflected by the 2026-09-03 CONSUMERS-CORE addendum immediately above) is now also
   consistently reflected across the surrounding docs suite (CLAUDE.md, docs/agent-monitoring/, docs/ai/,
   .claude/skills/, docs/testing/regression_policy.md) — a docs/prose-only sweep correcting every remaining
   reference to a retired physical shape (bare runs.jsonl/events.jsonl/tools.jsonl, or the intermediate
   tools/tools-YYYY-Www.jsonl shard) to the unified agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl
   layout this entry already documents at the code level. No further generate_retro.py source-resolution
   change beyond what the CONSUMERS-CORE addendum already landed.
   ```
   (Match the surrounding whitespace/quoting conventions the 3 prior addenda already use — a trailing blank
   line, no manual YAML quoting since `write_entry()`'s `yaml.safe_dump()` handles escaping.)
3. Call `tools/parity_ledger_writer.py::write_entry("infrastructure.yaml", full_entry_dict)` with the complete, updated entry dict (per `write_entry()`'s own docstring at `tools/parity_ledger_writer.py:90-93`: "upsert it (by `id`)" — it replaces the whole entry keyed by `id`, so a partial diff is not sufficient; the implementer must pass every field, not just `divergence_note`). `write_entry()` internally calls `validate_entry()` first (raises `EntryValidationError` on the 2 rules that apply here: non-empty `id` and, since `status == "verified"`, non-empty `v2_evidence` + `test_path` — both already present and unchanged) and, on success, rebuilds `tools/parity_index.py`'s derived SQLite index in-process via `build()`.
4. Per `tools/parity_ledger_writer.py`'s own module docstring, separately issue a second, visible `python3 tools/parity_index.py build` Bash call after the writer call — the in-process rebuild inside `write_entry()` does not itself move the `parity_write_safety` retro metric, since `generate_retro.py`'s `_is_parity_index_build_call` only matches a literal Bash call containing `"parity_index.py"` and `"build"`.

**Other writers to this same resource (docs/parity_ledger/infrastructure.yaml), enumerated:** `tools/parity_ledger_writer.py::write_entry()` is the *only* code path that writes to this file (confirmed by this module's own docstring: `tools/parity_index.py` "never writes into docs/parity_ledger/ and implements no mutation CLI," and a static architecture-guard test — `tests/tools/test_parity_index.py::TestArchitectureGuards::test_no_mutation_cli_or_write_path_to_docs_parity_ledger` — asserts no write call in `parity_index.py`'s source targets this directory). No other agent/ticket/tool in this repo writes to `infrastructure.yaml` directly; the `.claude/agents/parity-updater.md` agent role is the only other caller of `write_entry()`, and it runs sequentially (never concurrently with this ticket's own Implement phase) as part of the standard pipeline's Parity phase for a *different* ticket. There is no concurrent-write race for this step: `write_entry()`'s read-modify-write (read full shard → mutate in memory → `yaml.safe_dump()` the whole shard back) is not safe against two simultaneous callers on the same shard file, but this repo's pipeline serializes Parity-phase writes per ticket by construction (one ticket's Implement→Parity sequence at a time on a given worktree/branch) — no other ticket's Parity phase runs against `infrastructure.yaml` in the same window as this one.
**Do NOT touch:** Any other entry in `infrastructure.yaml` (`INFRA-283`, `INFRA-284`, `INFRA-289`, `INFRA-290`, `INFRA-292`, or any entry outside `INFRA-291`) — every `agent-monitoring/*.jsonl` mention inside another entry's `text`/`v2_evidence`/`divergence_note` is a frozen, dated evidence citation and must not be rewritten (investigation.md Anti-Drift Hazards). Do NOT edit any of `INFRA-291`'s own 3 existing addendum paragraphs — only append a 4th, never alter the first 3. Do NOT hand-edit the YAML file with `Edit`/`Write` under any circumstance (CLAUDE.md hard rule).
**Verify:** Test plan command 5 (`git diff --stat docs/parity_ledger/infrastructure.yaml` + `grep -c "Addendum (TCK-20260903-MONITORING-DATA-DOCS-SWEEP" docs/parity_ledger/infrastructure.yaml` must return `1`) plus the Anti-Drift Test Guard (`git diff docs/parity_ledger/infrastructure.yaml | grep "^-" | grep -v "^--- "` must return zero removed lines — a pure-addition diff).

### Step 16 — Run `make knowledge-index-update`
**Files:** None (build/index step only)
**Change:** Run `make knowledge-index-update` per CLAUDE.md's "After Work" rule, since `docs/` files were modified in Steps 1-13 (and 5).
**Do NOT touch:** Nothing — this is a command run, not a file edit; do not hand-edit any generated index file it produces.
**Verify:** Test plan command 6 — command must complete successfully (exit 0).

### Step 17 — Final verification sweep
**Files:** None (verification only)
**Change:** Run, in order: test plan command 1 (AC's own 3-pattern grep), command 2 (the bare-`tools.jsonl` gap-pattern grep this investigation found), command 3 (`CLAUDE.md`-specific content re-check), command 4 (`.gitattributes` cat), command 7 (confirm no `src/`/`tools/` files in the diff), and the 3 Anti-Drift Test Guards (Join Example non-touch, parity-ledger pure-addition diff, archived/dated-doc non-touch, `implement-ticket.js` prose-only diff).
**Do NOT touch:** Nothing — pure verification.
**Verify:** All commands above return the expected zero-hit / pure-addition / no-file-list results documented in test_plan.md's "Scoped Verification Commands" and "Anti-Drift Test Guards" sections.

## Scope Guards

- **No functional code change anywhere** — every edit in this plan is to a `.md`/`CLAUDE.md`/`SKILL.md` file's prose, or to `infrastructure.yaml`'s `divergence_note` field via the sanctioned writer. No `src/` file is touched. No `.claude/workflows/implement-ticket.js` executable statement is touched (Step 12 is prose-only).
- **`tests/agent_replay/test_no_mutation_snapshot.py` and `tests/agent_replay/test_fixture_envelope.py` are explicitly out of scope** — both are confirmed real, functional-code staleness (the former's `_WATCHED_GIT_PATHSPECS` still names 3 retired paths at line 34) but are `tests/` code, not docs, and are excluded by this ticket's own Out-of-Scope line ("Any functional code change"). This gap has already been filed as `TCK-20260904-HOTFIX-AGENT-REPLAY-MONITORING-PATH-STALENESS` (a combined follow-up also covering the previously-known `test_fixture_envelope.py` gap). **Do not touch either file in this ticket's implementation.**
- **`docs/agent-monitoring/schema.md`'s Join Example (lines 470-502) is not touched** — already fixed by commit `76096246` (`TCK-20260903-MONITORING-DATA-CONSUMERS-CORE`), confirmed this session still glob-based.
- **`.gitattributes` is not touched** — already clean, confirmed this session; Step 14 is verification-only.
- **`docs/REGISTRY.yaml`, `docs/audits/D23_architecture_resilience.md`, `docs/audits/D24_codebase_health_observatory.md`, `docs/plans/architecture_resilience_remediation_roadmap.md`, `docs/plans/knowledge-gateway-mcp-proposal.md`, and every `docs/archive/`/`docs/plans/archive/`/`*_decision.md`/`*_measurement.md` file are not touched** — all are dated historical/evidence records explicitly protected by this ticket's own Out-of-Scope section ("Rewriting any doc's historical/'how we got here' framing... into something that never happened").
- **No entry in `docs/parity_ledger/infrastructure.yaml` other than `INFRA-291` is touched**, and within `INFRA-291`, only a 4th addendum paragraph is appended — the 3 existing addenda and every other field are carried forward unchanged.
- **No new parity ledger entry is created** — investigation.md confirmed no other `docs/parity_ledger/*.yaml` shard needs a new entry or addendum; this ticket's change is docs/config prose only.
- **`docs/observability/agent_ops_dashboard_contract.md` is not touched** — already confirmed clean by child 4 (`CONSUMERS-GATES-DASHBOARD`); its remaining bare `runs.jsonl`/`tools.jsonl` mentions are conceptual/dated per investigation.md, not current-state claims.

## Dependency Map

All 17 steps are file-independent of each other except as noted below — most can be done in any
order, but the plan lists them in the order that groups related risk together (`CLAUDE.md` and
`system_overview.md` first/mid since they carry the most substantive edits and the most anti-drift
risk; verification-only steps last).

- Step 17 (final verification sweep) depends on all of Steps 1-16 being complete — it is the
  integration check, not an independent edit.
- Step 16 (`make knowledge-index-update`) should run after all doc edits (Steps 1-13) are made, since
  it indexes `docs/` content — running it mid-sweep would just mean re-running it again at the end
  anyway, so sequencing it last avoids a wasted extra run.
- Step 15 (`INFRA-291` addendum) is independent of every doc-edit step (different file, different
  write mechanism) and could run at any point, but is sequenced after the doc edits so its addendum
  text can honestly state the docs-suite sync is complete.
- Steps 1-14 have no dependencies on each other — each touches a distinct file (except Steps 9/10,
  which touch 2 different files with the same rule text, independently editable in either order).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Grep for `agent-monitoring/runs.jsonl`, `agent-monitoring/events.jsonl`, and `agent-monitoring/tools/tools-` across `docs/`, `CLAUDE.md`, `.gitattributes`, `.claude/workflows/implement-ticket.js`, and `.claude/skills/` returns zero current-state hits | Steps 1-13 | Test plan command 1 (`grep -rn "agent-monitoring/runs\.jsonl\|agent-monitoring/events\.jsonl\|agent-monitoring/tools/tools-" ...`) |
| (Investigation-identified gap in the AC's own pattern) bare `agent-monitoring/tools.jsonl` also returns zero current-state hits | Steps 1, 9, 10, 11, 12, 13 | Test plan command 2 (`grep -rn "agent-monitoring/tools\.jsonl" ...`) |
| `CLAUDE.md` lines 94, 137, 140, 254 (or post-edit equivalents) no longer make the confirmed-stale claims | Step 1 | Test plan command 3 (`grep -n "tools\.jsonl\|runs\.jsonl\|events\.jsonl" CLAUDE.md`, manual content check) |
| `.gitattributes` contains exactly the unified `data/*/*.jsonl`-style glob and no legacy lines | Step 14 (verification-only, no edit) | Test plan command 4 (`cat .gitattributes`) |
| `docs/parity_ledger/infrastructure.yaml`'s `INFRA-291` entry has a new, date-stamped addendum added via `tools/parity_ledger_writer.py` | Step 15 | Test plan command 5 (`git diff --stat` + `grep -c "Addendum (TCK-20260903-MONITORING-DATA-DOCS-SWEEP"` == 1) plus the pure-addition diff guard |
| `make knowledge-index-update` completes successfully | Step 16 | Test plan command 6 |

## Anti-Drift Notes

- **Historical framing must be preserved, only current-state claims corrected** — this is the single
  most important discipline in this ticket, matching the precedent every prior sibling child
  established for the same distinction (e.g. child 1/2's own migration-history sentences describing
  "what was true before" stay as written). Every step above names precisely which lines are
  current-state claims (edit) vs. dated/historical citations (leave alone). When in doubt at
  implementation time about a line not explicitly named in this plan, default to leaving it — do not
  proactively "fix" a line this plan doesn't cite; if it's genuinely stale, note it and treat it as
  part of the nearest matching step (as several steps above explicitly allow for), not as an
  unscoped new edit.
- **Do not re-touch the `schema.md` Join Example** — it is already correct (fixed by a sibling
  commit that landed after this ticket was scoped). This is the one place where the ticket's own
  original text is now stale about what's stale; trust this plan's Step 2 note and investigation.md
  over the ticket body's original claim.
- **Do not touch `.gitattributes`** — confirmed clean; a no-op diff there is scope creep against the
  AC, which only requires confirmation, not modification.
- **`docs/parity_ledger/infrastructure.yaml` may only be written through
  `tools/parity_ledger_writer.py::write_entry()`** — never a raw `Edit`/`Write` to the YAML file. This
  is both a CLAUDE.md hard rule and the file's own established addendum convention (3 prior addenda,
  same mechanism). `write_entry()` requires the complete entry dict — read the full current entry
  first, then pass it back with only `divergence_note` appended to, never write a partial diff.
- **`.claude/workflows/implement-ticket.js` gets prose-only edits** — confirmed twice (investigation
  session and this planning session) that no functional file I/O on these paths exists in this file;
  all real reads/writes happen in the Python tools it shells out to. If an implementer's edit to
  lines 385/1706 accidentally touches a bare executable statement (not inside a string literal), that
  is a plan violation — re-check before committing.
- **The 2 files tracked in the new follow-up hotfix ticket
  (`tests/agent_replay/test_no_mutation_snapshot.py`, `tests/agent_replay/test_fixture_envelope.py`)
  must not appear in this ticket's diff at all** — even a well-intentioned "just fix it while I'm
  here" edit would violate this ticket's own Out-of-Scope line and duplicate/conflict with the
  already-filed follow-up.
- **No unresolved open questions block this plan** — investigation.md's remaining "Risks and Open
  Questions" items (the 8 `_decision.md`/`_audit.md` files not individually read, and the
  `implement-ticket.js` comment-block staleness at lines 632/context) are noted as implementer
  spot-check opportunities within their respective steps above, not blockers; none of them changes
  this plan's approach if the spot-check finds nothing further, and each is scoped as an optional
  sub-edit of an existing step (never a new step) if it does.

## Deviations

- **Step 15 — wrong field name.** This plan instructed appending the 4th `INFRA-291` addendum to
  the `divergence_note` field, describing that as "the identical pattern" the 3 prior addenda used.
  This was wrong: on reading the live entry at implementation time, `divergence_note` holds a
  distinct, unrelated paragraph (the malformed-JSONL-line edge case documented in this entry's
  `text`/`v2_evidence`), and all 3 prior addenda
  (`TCK-20260811-AGENT-MONITORING-INDEX-SILENT-STALENESS`, `TCK-20260902-MONITORING-SHARD-CONSUMERS`,
  `TCK-20260903-MONITORING-DATA-CONSUMERS-CORE`) are actually chained onto the `support_boundary`
  field. investigation.md's "Prior Work" section made the same misidentification, so this was not
  caught during planning. The implementer's first pass appended to `divergence_note` exactly as
  instructed, then a post-write verification read of the raw file (checking the addendum count
  landed where expected) surfaced the mismatch. That write was reverted with `git checkout --`
  before it left the working tree in a bad state, and re-run correctly against `support_boundary`.
  A field-by-field Python comparison against `git show HEAD:docs/parity_ledger/infrastructure.yaml`
  confirmed every other field, including `divergence_note` itself, is byte-identical before/after,
  and `support_boundary` is a pure textual superset (original text + the new addendum paragraph).
  No other step's instructions needed correction.
