---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-GATE-DET-DONE-CHECKER
artifact_type: investigation
tags: [ai, workflows, determinism]
---

# Investigation — TCK-20260705-GATE-DET-DONE-CHECKER

## Current Behavior

### `.claude/agents/done-checker.md` (read in full)

13 numbered DoD conditions (not 11 — the idea doc's own count is stale; `docs/ai/system_overview.md:106`
also still says "12 substantive... conditions", a second stale count worth fixing in the doc-update AC).
Tier-aware: hotfix marks condition 4 (staging artifacts) and condition 12 (frontmatter-in-artifacts) N/A.
Condition 13 (agent monitoring) is pre-marked PASS unconditionally — "will be written by workflow
writeMonitoring after READY_TO_CLOSE." Machine-checkable subset, by condition number:

| # | Condition | Machine-checkable pre-Finalize? |
|---|---|---|
| 3 | Ticket has required metadata, in `tickets/inprogress/` | Yes — file existence + frontmatter fields |
| 4 | Staging artifacts complete (N/A hotfix) | Yes — 3 files exist & non-empty |
| 7 | `working_log.csv` entry added | Yes, but **inverted**: pre-Finalize the correct assertion is "row does NOT yet exist" (Finalize adds it) |
| 10 | `data/runs/`, `reports/release_proof/` clean | Partially — needs a definition of "this ticket's" artifacts (see below) |
| 12 | Frontmatter valid (ticket + artifacts) | Yes — `validate_frontmatter.py` exit code |
| 1, 2, 5, 6, 8, 9, 11 | Scope match, architecture, tests, docs, undocumented decisions, repo consistency, material gaps | No — irreducibly LLM judgment, correctly out of scope per the ticket |
| 13 | Agent monitoring | N/A pre-Finalize by design — pre-marked PASS |

### `.claude/workflows/implement-ticket.js` — current line numbers (verified 2026-07-05, file is 806 lines; do not trust any prior ticket's citations, they have shifted)

- **Phase 8: Verify** — `phase('Verify')` at line 670. `DONE_SCHEMA` at lines 672–693: required
  `['verdict', 'failing_items', 'checklist', 'summary']`. **No `verified_by` field exists today.**
  `checklist[].status` enum is `['PASS', 'FAIL', 'NA']`. The `agent(...)` call (695–725) passes
  `Tier: ${tier}` directly into the prompt (line 703) — this is how tier is threaded into done-checker's
  N/A rules today; a static pre-check module needs the same `tier` value passed as a plain argument.
  Lines 716–720 tell done-checker to mark conditions 7 (working_log), 3-equivalent (ticket in done/), and
  12-numbered-in-comment-but-actually-13 (agent monitoring) as PASS with "will be completed by workflow" —
  this is the one place the orchestrator already tells the LLM gate "don't bother checking this, it hasn't
  happened yet," which is exactly the seam Part A's static pre-check should formalize.
  Verdict check at line 727: `if (doneCheck.verdict !== 'READY_TO_CLOSE')` → returns `DOD_BLOCKED`.
  **This is the existing failure vocabulary Part A's static check must reuse — no new status string.**

- **Phase 9: Finalize** — `phase('Finalize')` at line 745. The `agent(...)` call (747–792) has **no
  `schema` key** in its options object (`{ label: 'finalize' }` only, line 791) **and its return value is
  never assigned to a variable** — `await agent(...)` at line 747 is a bare statement, not
  `const finalizeResult = await agent(...)`. Confirmed by reading the literal code: nothing between line
  747 and line 794 reads any property off the Finalize agent's response.
  Line 794 (`pushEvent('Finalize', 'finalizer', 'ok', ...)`) and the final `return { status: 'DONE', ... }`
  (line 797) execute **unconditionally** — regardless of what the Finalize agent actually reported for its
  own step 7 self-check ("Verify: (a) no leftover files... (b) stored_artifacts/ exists..."). The prompt
  asks the agent to "Report each step: DONE / SKIPPED (reason)" (line 790) but that report is pure prose
  text the orchestrator discards. **This confirms the ticket's premise exactly**: there is no
  orchestrator-level (JS) verification of the Finalize agent's own migration work today.

- **Established `bash(...)` pattern to mirror (Part B)**: `TCK-20260705-WORKFLOW-PARITY-SKIP`'s Parity
  phase (lines 549–572) already does exactly this shape — the orchestrating session runs a `bash(...)`
  call directly (not a new `agent()` sub-call) to invoke a pure Python function
  (`tools/parity_ledger_scan.py::find_p0_intersection`) via `python3 -c "..."`, passing changed-file paths
  as individually-quoted argv elements (explicit comment at lines 554–559 explains why: embedding a JSON
  array inside a double-quoted `-c` string corrupts on unescaped nested quotes). Part B's Finalize
  self-check should use this same `bash(...)`-after-`agent(...)` shape: call `bash(...)` immediately after
  the (still-unassigned-today) Finalize `agent(...)` call returns, running a new pure function in
  `tools/gate_checks/done_checker_static.py` (or a Finalize-specific sibling) that checks the 5 migration
  conditions listed in the ticket's Part B scope directly against the filesystem/CSV.

### `tools/validate_frontmatter.py` — CLI contract (confirmed by reading `main()`, lines 301–341)

`python3 tools/validate_frontmatter.py <path>` accepts **both** a single file and a directory:
`target.is_dir()` (line 322) routes to `validate_directory()` (recursive `.rglob("*.md")`, line 291);
otherwise `validate_file()` on the single path. Exit 0 on zero errors, exit 1 if `all_errors` is non-empty
(lines 332–339). `--content-type` override exists but is not required — content type is auto-detected from
path (`detect_content_type`, lines 116–130: `tickets` in parts → `ticket`, `stored_artifacts` in parts →
`artifact`). **Caveat for a static pre-check**: `staging_artifacts/{ticket_id}/` files will NOT
auto-detect as `artifact` type (only `stored_artifacts` triggers that branch) — they'll fall through to
`doc` detection, which requires a different required-field set (`status/layer/authority/audience`, no
`ticket_id`/`artifact_type`). A static pre-check calling this script against `staging_artifacts/{id}/`
must pass `--content-type artifact` explicitly, or the check will validate against the wrong schema.
This is a real, previously-undocumented gap done-checker's own condition 12 wording (`.claude/agents/done-checker.md:66`,
"Run `python3 tools/validate_frontmatter.py staging_artifacts/{ticket_id}/`") does not call out — it
currently relies on the artifact files' own `content_type` frontmatter field never being set (falling
through to path detection) coincidentally landing on `doc`'s validator, which happens to accept these
files today only because their frontmatter also satisfies `doc`'s required fields
(`status/layer/authority/audience` — all artifact frontmatter blocks already include these). Confirmed
empirically: `python3 tools/validate_frontmatter.py stored_artifacts/TCK-20260705-WORKFLOW-PARITY-SKIP/`
exits 0 without `--content-type` today (path contains `stored_artifacts` → correctly detected as
`artifact`), but the parallel `staging_artifacts/` path does not get this treatment. Part A's implementation
should pass `--content-type artifact` explicitly when validating `staging_artifacts/{id}/`.

### `data/runs/` / `reports/release_proof/` distinguishing mechanism (ticket's Assumption/Open Question — resolved)

Both directories are **currently empty** (confirmed via `ls`, 2026-07-05). The open question — "is there a
timestamp-based way to tell this ticket's run data from a concurrent session's, or is the convention simply
confirm-empty" — has a **concrete existing answer already written into this same file**:
`implement-ticket.js` Finalize step 6 (line 786): `"Clean data/runs/* and reports/release_proof/* only if
they contain artifacts from this work session (check modification times before deleting)."` This is the
established precedent — **mtime-based, not session-ID-based** (no session/run UUID is embedded in
`data/runs/` paths generically; `.claude/agents/simulation-analyst.md:9` and the simulation-lab workflow
files address a different, unrelated `data/runs/{session_id}/` convention used for *simulation* runs, not
agent-workflow runs — do not conflate the two). Part A's static pre-check should mirror step 6's own
logic: compare each file/dir's mtime under `data/runs/` and `reports/release_proof/` against the run's own
`start_ts` (already available in JS scope as `startTs`/`ticketInfo.ts` and could be passed into the Python
check as an argument) — anything modified before `start_ts` is presumptively a concurrent/pre-existing
session's artifact and should not fail the check; anything at/after `start_ts` is this ticket's own and
should have been cleaned by Finalize (not yet run) or flagged if found already at Verify time (this ticket's
own work leaking data before Finalize's cleanup step, which is itself worth a FAIL/warning).

### `tools/registry_query.py` / `tools/parity_ledger_scan.py` style (confirmed — module docstring, pure functions, no CLI/argparse)

Both modules: (1) open with a module-level docstring naming the ticket that built them and why: (2) expose
only plain functions taking simple args (lists/dicts/Paths) and returning plain Python values (sets, lists
of tuples) — zero `argparse`, zero `if __name__ == "__main__":`, consumed exclusively via
`python3 -c "..."` from the JS workflow file. `tools/gate_checks/done_checker_static.py` should follow this
exact shape: one function per condition (e.g. `check_staging_artifacts_complete(ticket_id, tier)`,
`check_ticket_in_inprogress(ticket_id)`, `check_working_log_no_row_yet(ticket_id)`,
`check_data_runs_clean(start_ts)`, `check_frontmatter_valid(ticket_id, tier)`), each returning something
like a `(status: "PASS"|"FAIL", evidence: str)` tuple or small dataclass, plus one aggregate function the
`done-checker` agent prompt is told to call and cite verbatim.

### `tools/agent-monitoring/validate.py` — retrospective-audit precedent (confirmed)

Read in full: module docstring states its purpose plainly, uses `MONITORING_START` date-gating
("Only validate working_log entries on or after this date... Historical tickets... are skipped
silently"), is non-blocking for warnings (only hard `errors` — runs with zero events — cause `sys.exit(1)`;
everything else prints `WARNING:` and exits 0), disclose-don't-fix (never mutates `working_log.csv` or
`runs.jsonl`/`events.jsonl` itself). This is the exact shape Part C's audit tool (if built) should copy:
read-only, warn-only, forward-gated by a start date if the historical count is large (which it is — see
below).

## Mechanics / Engine Constraints

Not applicable. This ticket touches only `.claude/agents/`, `.claude/workflows/implement-ticket.js`, and a
new `tools/gate_checks/` subpackage — agent-workflow-hygiene tooling, not simulation mechanics. No
`docs/mechanics/` chapter or `docs/engine/` contract governs gate-agent determinism.

## Parity Ledger Overlap

None. Grepped all 8 canonical `docs/parity_ledger/*.yaml` files for `done-checker|finaliz|workflow|gate`
hits — every match is either a *simulation-domain* gate (`src/lab/workflows.py`'s `Workflow.run()` typing,
`.github/workflows/test.yml` CI gates, `src/engine/kernel.py`'s tick_hash gate, resource-budget pressure
gates, mypy gate) or unrelated prose ("Monitoring checks fail loudly..." describing in-simulation telemetry,
not agent-monitoring). None reference `.claude/workflows/implement-ticket.js`, `.claude/agents/`, or
`tools/gate_checks/`. This matches the established precedent from both sibling agent-infra tickets this
session (`TCK-20260705-WORKFLOW-SECURITY-GATE`, `TCK-20260705-WORKFLOW-PARITY-SKIP`) and
`TCK-20260705-WORKING-LOG-BACKFILL`, none of which touched the parity ledger — confirmed by reading their
own stored `investigation.md` files, each stating "None... not simulation subsystems tracked by the parity
ledger."

## Prior Work

`docs/REGISTRY.yaml` queried for `type: ticket` entries whose `related_code_areas` overlaps
`done-checker.md` / `implement-ticket.js` / `validate_frontmatter.py` / `gate_checks`:

- `TCK-20260606-DOCSITE-FM-TICKETS` (done) — applied frontmatter to tickets/stored artifacts and
  introduced `tools/add_frontmatter_tickets.py`; touched `done-checker.md` to add condition 12
  (frontmatter validation) originally. No conflict — this ticket's Part A makes that existing manual
  step scriptable, doesn't change its substance.
- `TCK-20260607-MON-AGENTS`, `TCK-20260607-MON-CAPTURE` (done) — introduced the `agent-monitoring`
  hooks/writeMonitoring plumbing this ticket's condition 13 depends on. No conflict.
- `TCK-20260612-LOCAL-CTX-MCP` (done) — added the `search_docs`/`knowledge_search.py` context-scan
  requirement to `implement-ticket.js`'s Scope phase. Unrelated to Verify/Finalize.
- No prior `TCK-*GATE-DET*` ticket exists in the registry — this is genuinely the first of the 4 sibling
  gate-determinism tickets to be investigated (matches `SEQUENCE.md`'s stated order: done-checker first).
- Sibling design doc: `tickets/todos/gate-determinism-followups/SEQUENCE.md` (read in full) — the 5 shared
  decisions (module location `tools/gate_checks/`, shared failure vocabulary, `verified_by` provenance
  field, coverage-honesty tests, token/cost telemetry out of scope) all apply as given; no evidence found
  to contradict any of them.

## Risks and Open Questions

1. **`validate_frontmatter.py` content-type gap (new finding, not in the ticket's own Assumptions)**: as
   detailed above, `staging_artifacts/` paths don't auto-detect as `artifact` content type the way
   `stored_artifacts/` paths do. Part A's implementation must pass `--content-type artifact` explicitly (or
   equivalently call `validate_file`/`validate_directory` with `content_type_override="artifact"` directly
   as a Python import rather than shelling out) — otherwise the pre-check silently validates against the
   wrong schema and could false-pass or false-fail.
2. **Part C's git-history ambiguity**: `implement-ticket.js` never runs `git add`/`git commit` itself
   (grepped — zero hits); committing is a separate, human/manual step per this repo's own CLAUDE.md Bash
   rules. This means `git log` cannot reliably distinguish "staging_artifacts/{id}/ never existed" from
   "staging_artifacts/{id}/ existed uncommitted and was deleted by a Finalize `rm -rf`/move step before ever
   being committed" for the 237 fully-missing cases found below. Recommend Part C's own writeup (if built)
   state this ambiguity explicitly rather than asserting either failure mode with confidence.
3. **Doc drift already present, unrelated to this ticket but touched by its own AC**: `docs/ai/system_overview.md:106`
   says done-checker checks "12 substantive Definition-of-Done conditions" — the live `done-checker.md` has
   13 numbered conditions today. This ticket's own doc-update AC (updating `system_overview.md`) should fix
   this count while it's in there, or explicitly flag it as a pre-existing drift being fixed opportunistically.
4. **Should `verified_by` be populated by the static script itself or by the LLM agent citing it?** The
   sibling design (SEQUENCE.md decision 3) says `verified_by: ["static:...", "llm"]` — Plan phase must
   decide whether `DONE_SCHEMA`'s new `verified_by` field is populated by parsing the static script's own
   PASS/FAIL list programmatically in JS (deterministic) or is left to the `done-checker` agent to
   self-report after running the script (matches how every other schema field in this file is populated
   today — always agent-self-reported, never JS-parsed from tool output). Recommend the latter for
   consistency with the rest of `DONE_SCHEMA` (verdict, failing_items, checklist are all agent-authored),
   but flag this as a genuine Plan-phase decision, not pre-decided by this investigation.

## Anti-Drift Hazards

- **Do not let Part A's static pre-check replace done-checker's judgment-based conditions** (1, 2, 5, 6, 8,
  9, 11) — those remain irreducibly LLM-judged per the ticket's own Out of Scope line and the idea doc's own
  table. The static script's job is to run first and let the agent *cite* its output for the
  machine-checkable subset only.
- **Do not add a second failure vocabulary.** A static-check `FAIL` must downgrade to the existing
  `DOD_BLOCKED` status (Verify) — never introduce a new status string, per `SEQUENCE.md` decision 2 and the
  idea doc's own Open Questions.
- **Do not have Part B's Finalize self-check silently swallow a discrepancy.** Per the ticket's own Scope
  line, a failed self-check must "report the discrepancy explicitly rather than silently returning DONE."
  Concrete recommendation (Plan phase should confirm): change the final `return` at line 797 to a
  conditional — if the new post-Finalize `bash(...)` check finds any of the 5 conditions false, return a
  **new, distinct status** (e.g. `FINALIZE_INCOMPLETE`) rather than `DONE`, carrying the specific failed
  condition(s) in the response, so a caller (human or `implement-epic.js`'s batch loop) can see the run did
  NOT actually complete cleanly — do not silently return `DONE` while logging a warning nobody reads.
  `implement-epic.js`'s batch loop (lines 203–209) already treats any `result.status !== 'DONE'` as a batch
  stop — a new distinct status here would automatically halt a batch epic run at the first
  incompletely-finalized ticket, which is exactly the desired failure mode (visible, not silent).
- **Part C build-or-skip decision — GO, with high confidence, not a coin flip.** See measured counts below:
  this is not a negligible historical curiosity to skip.

## Part C — Measured Historical-Orphan Counts (actual scan, not estimated)

Script run against the live repo, 2026-07-05 (see method: walked `tickets/done/*.md` **and**
`tickets/done/{folder}/*.md`, extracted each ticket's `## Tier` field, checked `stored_artifacts/{id}/`
existence/completeness for every `standard`/`epic` ticket, and checked the inverse — any
`staging_artifacts/{id}/` still present for an already-done ticket):

- **Total `.md` files under `tickets/done/` (incl. subfolders): 1038** (1026 direct + 12 in 11 subfolders,
  minus `README.md` and 11 `SEQUENCE.md` files excluded as non-tickets = 1026 actual tickets scanned).
- **Tier distribution**: `standard` 828, `hotfix` 73, `epic` 34, `UNKNOWN` (no parseable `## Tier` field —
  pre-frontmatter-era legacy tickets like `METRICS-01.md`, `RESTRUCTURE-01.md`) 91.
- **Standard/epic tickets checked (stored_artifacts applies): 862.**
- **stored_artifacts/{id}/ missing entirely: 237 / 862 (27.5%).**
- **stored_artifacts/{id}/ present but missing ≥1 of the 3 required files: 101 / 862 (11.7%).**
- **Total gap: 338 / 862 (39.2%)** of all standard/epic done tickets have an incomplete or absent
  stored_artifacts migration today.
- **Inverse check — stale staging_artifacts/{id}/ left behind for an already-done ticket: 0 / 862.** Every
  Finalize run that reached the "move" step appears to have actually removed the source
  `staging_artifacts/` directory (no leftover source dirs found) — the failure mode is not "moved partially
  and left debris," it's "the destination ended up incomplete/absent while the source was still cleared."
- **By month** (using each ticket's embedded `TCK-YYYYMMDD-` date prefix as a proxy for when it was
  finalized): the gap rate is declining but **not resolved**, and is still materially present in the most
  recent data:

  | Month | Total std/epic | Missing dir | Incomplete dir | OK | Gap rate |
  |---|---|---|---|---|---|
  | 2026-04 | 207 | 98 | 54 | 55 | 73.4% |
  | 2026-05 | 244 | 56 | 30 | 158 | 35.2% |
  | 2026-06 | 363 | 68 | 15 | 280 | 22.9% |
  | 2026-07 (partial, through 07-05) | 43 | 8 | 3 | 32 | 25.6% |

- **Concrete recent examples (2026-07, i.e. days/hours before this investigation, not ancient legacy debt)**:
  `TCK-20260703-SIMQ-UPLIFT3-DUAL-GATE-AUDIT` is missing both `plan.md` and `test_plan.md` in its
  `stored_artifacts/`; `TCK-20260703-SIMQ-UPLIFT3-GOAL-TRACE` is missing `plan.md`;
  `TCK-20260701-SIMQ-EMIT-CAMP`, `-CONTRACT-MILESTONE`, `-PROGRESSION`, `-SOCIAL-MEM`, `-SOCIAL2`, `-WORLD2`,
  and `TCK-20260701-SIMQ-KERNEL-WIRE` (7 tickets, same day, same `SIMQ-EMIT` epic family) have **no**
  `stored_artifacts/` directory at all. These 7 were run via `implement-epic.js` — confirmed by reading that
  file in full that it delegates each child ticket to `workflow('implement-ticket', ...)` (line 191), i.e.
  each child goes through the *exact same* per-ticket Finalize phase as a standalone run; there is no
  separate, buggier epic-level migration path. This means these 7 failures are exactly the class of bug
  Part B's Finalize self-check is designed to catch in real time — strong direct evidence this ticket's Part
  B is worth building, not just Part C's retrospective audit.

**Go/no-go recommendation: GO — build Part C's audit tool.** A 39.2% overall historical gap, with a
still-nontrivial ~23–26% gap rate in the two most recent complete/partial months, is not "confirmed not to
exist at scale" — it is a real, ongoing, non-negligible gap. Recommend the audit tool mirror
`tools/agent-monitoring/validate.py`'s shape exactly: read-only, `WARNING`-only (never blocks anything),
disclose-don't-fix, and — given the volume — should probably support a `MONITORING_START`-style date
threshold too (or simply report all 338 with counts, since unlike `validate.py`'s CSV-parsing false-positive
problem, these are confirmed-real gaps, not parsing artifacts).
