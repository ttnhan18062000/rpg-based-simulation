---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260903-MONITORING-DATA-DOCS-SWEEP
artifact_type: investigation
tags: [agent-monitoring, observability, documentation, claude-md]
---

# Investigation — TCK-20260903-MONITORING-DATA-DOCS-SWEEP

## Current Behavior

All 6 sibling children of `TCK-20260903-MONITORING-UNIFIED-WEEKLY-EPIC` are confirmed landed and
committed on this branch (`git log --oneline`): `WRITE-PATH-UNIFY` (06597f53/d93685ab),
`DATA-MIGRATION` (3f980944), `REFERENTIAL-INTEGRITY` (7a095c0d), `CONSUMERS-GATES-DASHBOARD`
(f0256440), `CONSUMERS-CORE` (76096246), `CODEX-REMIGRATION` (95af999d). The real, landed physical
layout is `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl` — confirmed by reading
`docs/agent-monitoring/schema.md`'s own per-source write-path paragraphs (already correct) and by
`.gitattributes`'s single glob line.

**Full current-state grep** (the exact 3-pattern command the ticket's own Acceptance Criteria
specifies: `agent-monitoring/runs\.jsonl|agent-monitoring/events\.jsonl|agent-monitoring/tools/tools-`)
returned these real hits across `docs/`, `CLAUDE.md`, `.gitattributes`, `.claude/workflows/implement-ticket.js`,
`.claude/skills/` (re-run this session, not trusted from the ticket body):

**Genuinely CURRENT-STATE claims needing a fix** (verified by reading the surrounding paragraph in
each file):

1. `CLAUDE.md:94` — "the monitoring tools auto-update `tools.jsonl` on every run" (bare, but part of
   the same stale claim family; the adjacent sentence doesn't name a path, this one implies a single
   file).
2. `CLAUDE.md:137,140` — "`agent-monitoring/tools.jsonl` is rewritten by a hook..." /
   `git add agent-monitoring/tools.jsonl && git commit ...`. Line numbers **unchanged** from the
   ticket's own citation — no drift occurred since the ticket was scoped.
3. `CLAUDE.md:254` — DoD checklist: "run entry in `agent-monitoring/runs.jsonl`, at least one event
   in `agent-monitoring/events.jsonl`". Line number **unchanged**.
4. `docs/agent-monitoring/schema.md:11` — "Two append-only JSONL files, joined by `run_id`." Wrong on
   two counts: it's 3 sources (runs/events/tools) per week, and `tools` additionally joins on `seq`.
   This line predates even the original tools.jsonl split and was never fixed by any child.
5. `docs/agent-monitoring/schema.md:50,139,368` — section headers `## \`agent-monitoring/runs.jsonl\``,
   `## \`agent-monitoring/events.jsonl\``, `## \`agent-monitoring/tools.jsonl\`` are stale bare-path
   headers, even though the body prose immediately under each (already edited by child 1/2) correctly
   describes the unified `agent-monitoring/data/YYYY-Www/<source>.jsonl` shape. The header and body
   contradict each other today.
6. `docs/agent-monitoring/README.md:19` — "(`tools/tools-YYYY-Www.jsonl`, one shard file per UTC ISO
   week)" — describes the *intermediate* (Sept 2) shard shape, already superseded by Sept 3's
   unification. Confirmed this is genuinely still wrong (not yet touched by any child).
7. `docs/agent-monitoring/README.md:54` — "the same `runs.jsonl`/`events.jsonl`/`tools/tools-YYYY-Www.jsonl`
   sources" (Baseline Metrics Snapshot section) — same intermediate-shape staleness.
8. `docs/guides/agent_monitoring.md:11,24,150` — "raw `runs.jsonl` + `events.jsonl`"; "`agent-monitoring/runs.jsonl`
   whose `start_ts`/`started_at`..."; "`agent-monitoring/runs.jsonl` records for the most recent
   matching timestamp" — all bare/monolithic-path current-state claims, none touched by any prior
   child.
9. `docs/ai/system_overview.md:229-247` (§6 "Observability and Where to Go Deeper") — describes "two
   single files (`runs.jsonl`, `events.jsonl`) plus a sharded family of tool-call files... (`agent-monitoring/tools/tools-YYYY-Www.jsonl`)".
   This is the most stale doc found: it still describes the **Sept 2 intermediate** shape (2
   monolithic + 1 sharded), not even the pre-epic monolithic-3-file shape this epic started from.
   Needs a full rewrite of the bulleted file-shape description.
10. `docs/ai/ticket-lifecycle.md:578,628,639,640` — "Write agent monitoring records": "`agent-monitoring/runs.jsonl`"
    / "`agent-monitoring/events.jsonl`" named as the literal current write targets in the workflow's
    own step description and the "Artifacts produced" list. **Not in the ticket's own Related Docs
    list — a real gap in the ticket's own pre-investigation.**
11. `docs/ai/workflows.md:140,203,204` — "Artifacts produced: `agent-monitoring/runs.jsonl` + `events.jsonl`"
    (implement-ticket) and the same pair for implement-epic's batch record. **Also missed by the
    ticket's own Related Docs list.**
12. `docs/ai/agents.md:279` — "records any discrepancy in `agent-monitoring/events.jsonl`" (parity-updater
    agent description). **Also missed.**
13. `.claude/skills/implement-ticket/SKILL.md:76` — "Never write to `agent-monitoring/runs.jsonl` or
    `events.jsonl` directly — always go through `record_run.py` / `record_events.py`." **Missed by the
    ticket** (only `agent-monitoring-retro/SKILL.md` was flagged as "not yet checked"; this sibling
    skill file was not named at all).
14. `.claude/skills/simq-audit/SKILL.md:77` — same rule, same stale bare paths. **Missed by the
    ticket.**
15. `.claude/skills/agent-monitoring-retro/SKILL.md:3,8-9` — description frontmatter ("raw
    runs.jsonl/events.jsonl data") and body ("raw `agent-monitoring/runs.jsonl` and
    `agent-monitoring/events.jsonl` records"). This is the file the ticket flagged as "not yet
    checked this session" — confirmed here: it does need updating.
16. `.claude/workflows/implement-ticket.js:385` — prompt template string: "record_events.py now
    computes both deterministically from agent-monitoring/tools.jsonl ground truth at write time".
17. `.claude/workflows/implement-ticket.js:1706` — the `monitoringWarning` fallback message actively
    tells a human to "investigate agent-monitoring/runs.jsonl and events.jsonl manually" — this is a
    user-facing diagnostic message that currently points at nonexistent files. Confirmed (via
    `grep -c "runs.jsonl\|events.jsonl\|tools.jsonl" .claude/workflows/implement-ticket.js` context
    read at lines 44-52, 265-272, 362-388, 560-575, 1700-1708) that **no functional file I/O** exists
    anywhere in this file on these literal paths — every real read/write happens inside the Python
    tools it shells out to (`record_run.py`, `record_events.py`, `seq_offset.py`,
    `emit_retrieval_event()`). This matches the ticket's own claim; only the 2 prose lines above (385,
    1706) plus the comment context at 44-49/265-272/362-370/560-573 (which already reference
    `tools.jsonl` generically/correctly as a concept, not asserting a specific current physical
    layout) need a look. Only 385 and 1706 assert something now factually wrong; the rest are safe as
    generic/conceptual references to "the tools data" and don't need changing.

**A gap in the ticket's own Acceptance-Criteria grep pattern, found this session:** the AC's 3-pattern
grep (`agent-monitoring/runs\.jsonl|agent-monitoring/events\.jsonl|agent-monitoring/tools/tools-`)
does not cover bare `agent-monitoring/tools\.jsonl` (no `/tools/tools-` in it) — the *original*
monolithic tools file, retired all the way back on 2026-09-02 by `TCK-20260902-MONITORING-SHARD-MIGRATION`,
one epic before this one. Several of the hits above (`CLAUDE.md:94/137/140`, both `SKILL.md` files,
`docs/testing/regression_policy.md:68`, `implement-ticket.js:385`) use exactly this bare form, and
would **not** be caught by the literal AC grep command as written, even though they are real,
current-state, stale claims squarely within this ticket's stated scope ("replacing every remaining
reference to any of the 3 retired shapes (monolithic `runs.jsonl`/`events.jsonl`, or the prior
epic's `tools/tools-YYYY-Www.jsonl`)" — the ticket's own prose scope already implicitly covers the
monolithic-tools.jsonl case as one of the "3 retired shapes," the AC command just under-specifies
it). Flagged in the Test Plan's verification commands so Verify doesn't rubber-stamp on an
incomplete grep.

18. `docs/testing/regression_policy.md:68` — "real `agent-monitoring/tools.jsonl` invocation history"
    (Zero-invocation skill-staleness assertions row). Current-state claim, not caught by the AC's
    literal grep, found via the broader bare-pattern sweep. **Missed by the ticket.**

**Already fixed — contradicts the ticket's own pre-investigation claim (re-verify, don't trust
citations):** the ticket's Request Summary states the Join Example in `docs/agent-monitoring/schema.md`
"confirmed this session to literally do `Path('agent-monitoring/runs.jsonl')`-style single-file
reads." This is **no longer true.** `git log -p --follow -- docs/agent-monitoring/schema.md` shows
commit `76096246` (`TCK-20260903-MONITORING-DATA-CONSUMERS-CORE`, landed *after* this ticket was
scoped) already rewrote the Join Example (lines 470-502 today) to
`Path('agent-monitoring/data').glob('*/runs.jsonl')`-style unified globbing. **No action needed on
the Join Example** — this is the one place where the ticket's own text is now stale about what's
stale.

**Already clean, confirmed:**

- `.gitattributes` — full file read. Exactly one unified glob line
  (`agent-monitoring/data/*/*.jsonl merge=union`), a comment explaining why, plus
  `tickets/working_log.csv merge=union` and a `docs/REGISTRY.yaml` exclusion note. Zero legacy lines
  (no `agent-monitoring/runs.jsonl merge=union` / `events.jsonl merge=union` / `tools.jsonl merge=union`
  remain). Matches the ticket's claim and the target AC exactly — no edit needed, only confirmation.
- `docs/agent-monitoring/README.md`'s Navigation table (line 148) — already says "Full field
  reference for the `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl` per-week layout."
  Already fixed.
- `docs/observability/agent_ops_dashboard_contract.md` — confirmed clean per the ticket's own
  expectation (child 4, `CONSUMERS-GATES-DASHBOARD`, already updated it). The remaining bare
  `runs.jsonl`/`events.jsonl`/`tools.jsonl` mentions found in the broader sweep (lines 85, 179, 214,
  397) are either (a) logical-shorthand references to the dataset concept (e.g. "`self._runs_all`...
  the raw, ungrouped `runs.jsonl`/`events.jsonl`/`tools.jsonl` lists" — describing what the in-memory
  attribute holds conceptually, same accepted convention as `docs/agent-monitoring/README.md`'s "What
  It Captures" bullets), or (b) dated historical citations (line 397: "`TCK-20260719-LIVE-PHASE-AGENT-LABEL`
  added nullable `phase`/`agent` fields to the raw `agent-monitoring/tools.jsonl` records themselves
  (populated for workflow runs after 2026-07-19)" — a July-dated fact about the file as it existed
  then). Neither needs a change.

## Mechanics / Engine Constraints

None. This ticket touches only agent-orchestration/dev-tooling documentation (`docs/agent-monitoring/`,
`docs/ai/`, `docs/guides/agent_monitoring.md`, `CLAUDE.md`, `.gitattributes`,
`.claude/workflows/implement-ticket.js` prose, `.claude/skills/`) — none of it is governed by the
Mechanics Bible (`docs/mechanics/`) or Engine Contracts (`docs/engine/`); the same "Agent-orchestration/
monitoring-pipeline tooling only" support boundary the existing `docs/parity_ledger/infrastructure.yaml`
INFRA-28x/29x entries already state applies here too.

## Docs Requiring Update

- `CLAUDE.md`: lines 94, 137, 140, 254 still assert `agent-monitoring/tools.jsonl`/`runs.jsonl`/`events.jsonl` as current single-file targets; correct to the `agent-monitoring/data/YYYY-Www/{runs,events,tools}.jsonl` layout.
- `docs/agent-monitoring/schema.md`: line 11's "Two append-only JSONL files" is wrong (now 3, one join key each); lines 50/139/368's section headers still name bare monolithic paths despite already-correct body prose.
- `docs/agent-monitoring/README.md`: line 19 and line 54 still describe the retired intermediate `tools/tools-YYYY-Www.jsonl` shard shape instead of the unified `data/YYYY-Www/tools.jsonl` shape.
- `docs/guides/agent_monitoring.md`: lines 11, 24, 150 assert bare/monolithic current-write-path claims.
- `docs/ai/system_overview.md`: §6 (lines 229-247) describes the Sept-2 intermediate shape (2 monolithic files + 1 sharded family), the most stale doc found in this sweep.
- `docs/ai/ticket-lifecycle.md`: lines 578, 628, 639, 640 name bare `agent-monitoring/runs.jsonl`/`events.jsonl` as current write targets in the Finalize step description and Artifacts-produced lists — missed by the ticket's own Related Docs list.
- `docs/ai/workflows.md`: lines 140, 203, 204, same current-write-path claims in Artifacts-produced lists for both `implement-ticket` and `implement-epic` — missed by the ticket's own Related Docs list.
- `docs/ai/agents.md`: line 279 names `agent-monitoring/events.jsonl` as the current write target for parity-updater's discrepancy record — missed by the ticket's own Related Docs list.
- `.claude/skills/implement-ticket/SKILL.md`: line 76's "Never write to `agent-monitoring/runs.jsonl` or `events.jsonl` directly" rule names retired bare paths — missed by the ticket (only `agent-monitoring-retro/SKILL.md` was named as unchecked).
- `.claude/skills/simq-audit/SKILL.md`: line 77, identical rule, identical staleness — missed by the ticket.
- `.claude/skills/agent-monitoring-retro/SKILL.md`: frontmatter `description` and body lines 8-9 assert "raw `agent-monitoring/runs.jsonl` and `agent-monitoring/events.jsonl` records" — this is the file the ticket flagged as not-yet-checked; confirmed it needs the update.
- `.claude/workflows/implement-ticket.js`: line 385 (prose comment inside a prompt template string) and line 1706 (the `monitoringWarning` fallback message shown to a human) both assert the bare, retired `agent-monitoring/tools.jsonl`/`runs.jsonl`/`events.jsonl` paths — prose-only fix, no functional-logic change, per the ticket's own Out-of-Scope note.
- `docs/testing/regression_policy.md`: line 68's Zero-invocation skill-staleness row asserts "real `agent-monitoring/tools.jsonl` invocation history" as the current source — found via the broader bare-pattern sweep, not caught by the ticket's own named AC grep pattern; missed by the ticket.
- `docs/parity_ledger/infrastructure.yaml`: `INFRA-291`'s `divergence_note` field needs a 4th, date-stamped `**Addendum (TCK-20260903-MONITORING-DATA-DOCS-SWEEP, 2026-09-04):**` paragraph appended (via `tools/parity_ledger_writer.py::write_entry()`, never a raw YAML edit) documenting that this ticket's changes are prose/doc-only — no further `generate_retro.py` source-resolution-layer change beyond what CONSUMERS-CORE (the entry's 3rd addendum) already landed.

Doc paths considered and explicitly excluded (Format 2, historical framing preserved as-is):

`docs/REGISTRY.yaml` (path: `docs/REGISTRY.yaml`) is not touched: it is a `make docs-registry`-generated
flat index of ticket metadata, regenerated wholesale on every Finalize per CLAUDE.md's own "After
Work" rule — its `agent-monitoring/runs.jsonl`/`events.jsonl` hits are historical `related_code_areas`
values frozen at the time each cited ticket (e.g. `TCK-20260713-MONITORING-SQLITE-INDEX`) was closed,
correctly describing what was true then, not something this ticket should hand-edit.

`docs/audits/D23_architecture_resilience.md` and `docs/audits/D24_codebase_health_observatory.md`
(paths: `docs/audits/D23_architecture_resilience.md`, `docs/audits/D24_codebase_health_observatory.md`)
are not touched: both are dated, numbered point-in-time audit reports (`status: active` refers to the
audit's own tracking lifecycle, not a claim that every fact in it self-updates) whose `agent-monitoring/runs.jsonl`/`events.jsonl`/`tools.jsonl`
mentions are evidence quotes describing the corpus as it existed on the audit's own date — the same
"how we got here" carve-out this ticket's own Scope section explicitly protects.

`docs/plans/architecture_resilience_remediation_roadmap.md` (path:
`docs/plans/architecture_resilience_remediation_roadmap.md`, line 347) and
`docs/plans/knowledge-gateway-mcp-proposal.md` (path: `docs/plans/knowledge-gateway-mcp-proposal.md`,
line 1486) are not touched: both hits are dated changelog/evidence entries ("(2026-08-23) Resolved
via...", "`TCK-20260816-KGMCP-P5-REPEATED-DEMAND-MEASUREMENT` performed the first real measurement...
Primary source (`agent-monitoring/events.jsonl` Investigate-phase summaries, 521 distinct tickets)")
describing what was true and what file was queried at that dated point in the past, not a present-tense
claim about today's physical layout.

`docs/parity_ledger/infrastructure.yaml`'s other entries (INFRA-283, INFRA-284, INFRA-289, INFRA-290,
INFRA-292, and every entry outside INFRA-291's own `divergence_note` addendum chain) are not touched:
every `agent-monitoring/*.jsonl` mention inside an entry's `text`/`v2_evidence`/`divergence_note` is a
frozen, dated evidence citation of source-code line numbers and file paths *as they existed when that
entry's own ticket landed* — rewriting them to the current layout would falsify the historical record
these fields exist to preserve (the ledger's own established addendum convention, seen 3 times already
on INFRA-291 itself, is to *append* a new dated paragraph documenting the next change, never to edit
the original text describing a past state).

Every `docs/archive/`, `docs/plans/archive/`, and `docs/engine/contracts/knowledge_gateway_mcp/*_decision.md`/`*_measurement.md`
hit found in the broader (non-AC-pattern) sweep is, by the same reasoning and by directory-name
convention (`archive/`) or file-naming convention (`_decision.md`, a decision record fixed at its
decision date), a dated historical record and out of scope for a "current state" rewrite.

## Parity Ledger Overlap

`INFRA-291` (`docs/parity_ledger/infrastructure.yaml`) — status `verified`, priority `P2`. Tracks
`generate_retro.py`'s data-loading layer, already carrying 3 addenda (`TCK-20260811-AGENT-MONITORING-INDEX-SILENT-STALENESS`,
`TCK-20260902-MONITORING-SHARD-CONSUMERS`, `TCK-20260903-MONITORING-DATA-CONSUMERS-CORE`), the last of
which is the entry's current state — it already fully describes the unified `agent-monitoring/data/<week>/{runs,events,tools}.jsonl`
layout `generate_retro.py` reads today. This ticket's own change is docs/config prose only, so its
addendum should be a short one stating that the physical-layout description this entry already tracks
is now also reflected consistently across the surrounding docs suite (`CLAUDE.md`, `docs/agent-monitoring/`,
`docs/ai/`, `.claude/skills/`) rather than describing any further code change. Priority is `P2`, not
`P0` — no `test_path` regression requirement beyond confirming the addendum itself validates against
`tools/parity_ledger_writer.py::validate_entry()`.

No other `docs/parity_ledger/*.yaml` entry needs a new entry or addendum for this ticket — confirmed:
this ticket makes no `src/`/`tools/` behavior change, only doc/prose/`.gitattributes` edits (already
clean) and the one `INFRA-291` addendum required by the ticket's own Scope.

## Prior Work

- `stored_artifacts/TCK-20260903-MONITORING-DATA-MIGRATION/` — the child-2 migration that produced the
  real, landed `agent-monitoring/data/YYYY-Www/` layout this ticket documents. Its own investigation.md
  is the authoritative description of the final physical shape.
- `stored_artifacts/TCK-20260903-MONITORING-DATA-CONSUMERS-CORE/` — landed after this ticket was
  scoped; already fixed `docs/agent-monitoring/schema.md`'s Join Example (see "Already fixed" above).
  Any implementer picking this ticket up should re-diff `schema.md` against `HEAD` before editing to
  avoid re-touching already-correct prose.
- `stored_artifacts/TCK-20260902-MONITORING-SHARD-CONSUMERS/` (prior, tools-only epic) — established
  the "logical shorthand kept" precedent this investigation reuses to decide `docs/agent-monitoring/README.md`
  lines 17-18/20-21 and `docs/observability/agent_ops_dashboard_contract.md`'s conceptual `runs.jsonl`/`tools.jsonl`
  mentions don't need literal-path correction.
- `docs/parity_ledger/infrastructure.yaml`'s `INFRA-291` addendum chain — the established pattern (read
  full entry → append a new `**Addendum (TCK-..., date):**` paragraph to `divergence_note` → call
  `tools/parity_ledger_writer.py::write_entry("infrastructure.yaml", full_entry_dict)`, which upserts
  by `id` and rebuilds the derived SQLite index in-process) is the exact mechanism to reuse for this
  ticket's 4th addendum. `write_entry()` requires the **complete** entry dict (it replaces the whole
  entry, keyed by `id`) — the implementer must read the current full YAML entry first, not construct a
  partial diff.

## Risks and Open Questions

- **Non-blocking, real functional-code finding, explicitly out of scope for this ticket:**
  `tests/agent_replay/test_no_mutation_snapshot.py:34` defines
  `_WATCHED_GIT_PATHSPECS = ["tickets/", "agent-monitoring/runs.jsonl", "agent-monitoring/events.jsonl", "agent-monitoring/tools.jsonl"]`
  — 3 of these 4 pathspecs no longer exist in the working tree. If this list feeds a `git status
  --porcelain -- <pathspecs>`-style check, watching a nonexistent path silently returns empty rather
  than erroring, meaning the no-mutation guard may not actually be watching anything for these 3
  entries today. This is `tests/` code (functional), not docs — out of scope per this ticket's own
  "Out of Scope: Any functional code change" line. **Recommend filing a small follow-up hotfix ticket**
  to repoint this list at `agent-monitoring/data/` (or a glob) rather than silently leaving a
  no-mutation guard partially blind. Flagging here per this repo's "file tickets for workflow gaps"
  convention rather than fixing it inline.
- The AC's own 3-pattern grep command under-specifies "retired shape" coverage (see "A gap in the
  ticket's own Acceptance-Criteria grep pattern" above) — bare `agent-monitoring/tools\.jsonl` (no
  `/tools/tools-`) is a real 4th pattern that should be checked too, or several genuinely-stale hits
  (`CLAUDE.md:94/137/140`, both `SKILL.md` rule lines, `regression_policy.md:68`, `implement-ticket.js:385`)
  will not register on a literal re-run of the AC's own command. Test Plan below adds this as an
  explicit additional verification command.
- `docs/observability/decision_trace_contract.md`, `docs/ai/replay_fixture_spec.md`,
  `docs/ai/default_packet_scenarios_decision.md`, `docs/ai/shadow_promotion_gate_thresholds_decision.md`,
  `docs/ai/monitoring_writer_decision.md`, `docs/ai/codex_posttool_adapter_real_command_proposal.md`,
  `docs/ai/agent_definition_gap_audit_2026-08-04.md`, `docs/ai/agent_infrastructure_audit.md` all
  appeared in the broader (non-AC-pattern) sweep with bare `runs.jsonl`/`events.jsonl`/`tools.jsonl`
  mentions but were **not individually read line-by-line** this session (effort-bounded — none matched
  the AC's own 3 literal patterns, meaning none currently assert the specific retired
  `agent-monitoring/<file>.jsonl` or `agent-monitoring/tools/tools-` forms; by naming convention
  (`_decision.md`, `_audit.md`, dated) they read as dated decision/audit records like the ones
  confirmed historical above). Flagged so the implementer can spot-check rather than assume.
- Priority `P1` on this ticket vs. `P2` on the `INFRA-291` parity entry it touches — not a conflict;
  the ticket's own priority governs pipeline urgency, the ledger entry's priority governs whether a
  `test_path` is mandatory (P0 only). No open question, just noting for the Parity phase.

## Anti-Drift Hazards

- **Do not touch `docs/agent-monitoring/schema.md`'s Join Example** (lines ~470-502) — it is already
  correct (fixed by `CONSUMERS-CORE`, landed after this ticket was scoped). Editing it again risks
  introducing a regression or an unnecessary diff.
- **Do not rewrite any dated evidence/citation text** inside `docs/parity_ledger/infrastructure.yaml`'s
  existing entries, `docs/audits/D23`/`D24`, or any `docs/plans/archive/`/`_decision.md` file — these
  are explicitly protected "how we got here" history per this ticket's own Out-of-Scope section. The
  only sanctioned edit to `infrastructure.yaml` is *appending* a new addendum paragraph to `INFRA-291`'s
  `divergence_note`, via `tools/parity_ledger_writer.py::write_entry()` — never a raw `Edit`/`Write` to
  the YAML file directly (CLAUDE.md hard rule, and this file's own module docstring: "nothing enforces
  the two representations stay in sync automatically" is about `schema.json`, but the write-safety
  rationale is the same).
- **Do not touch `.claude/workflows/implement-ticket.js`'s functional logic** — confirmed again this
  session that all real reads/writes on these paths happen inside the Python tools it shells out to.
  Only the 2 prose lines (385, 1706) need editing; every other `.jsonl`-mentioning line in that file
  (the comment blocks at 44-49, 265-272, 362-370, 560-573) already reads as generic/conceptual
  references to "the tools data," not a specific current-physical-layout assertion, and should be left
  alone unless a closer read at implementation time finds otherwise.
- **`.gitattributes` needs no edit** — resist the urge to "confirm by touching it"; a no-op diff there
  would be scope creep against the ticket's own Acceptance Criteria, which only requires confirming its
  current state, not modifying it.
- Keep the `INFRA-291` addendum scoped to what actually changed (docs prose sync, no code) — do not
  inflate it into a restatement of the whole epic; the 3 existing addenda already cover every real
  code-level physical-layout change.
- When editing `docs/agent-monitoring/schema.md`'s 3 stale section headers (lines 50, 139, 368), keep
  each header naming its *logical* source name (e.g. `runs`, `events`, `tools`) rather than a literal
  single-file path, consistent with how the body prose immediately below each header already refers to
  the per-week glob — do not invent a 4th header style inconsistent with the rest of the doc.
