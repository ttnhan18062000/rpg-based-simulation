---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260810-SKILL-USAGE-RETRO-TRACKING
artifact_type: investigation
tags: [skills, agent-monitoring, observability, process-improvement]
---

# Investigation — TCK-20260810-SKILL-USAGE-RETRO-TRACKING

## Current Behavior

**`tools/agent-monitoring/skill_usage_metric.py`** (standalone script, built by
`TCK-20260805-SKILL-USAGE-METRIC`):
- `build_skill_usage_section(tools: list) -> dict` (:28-66) filters `tools.jsonl` rows to
  `tool == "Skill"`, extracts the skill name from `input_summary` via `_SKILL_NAME_RE`
  (`r"'skill':\s*'([^']*)'"`, never `json.loads` — that field is a Python dict-repr string, not
  JSON), and returns `{total_skill_invocations, unparseable, per_skill, per_skill_per_run,
  derivation}`. `per_skill`/`per_skill_per_run` are `defaultdict(int)` cast to plain dict at
  return time; `run_id=None` buckets under the literal string `"unattributed"` (:42, matches
  `generate_retro.py`'s own `build_search_count_section` convention).
- `main()` (:69-86) is the CLI entrypoint: loads `DEFAULT_TOOLS_FILE` via `generate_retro`'s own
  `load_jsonl`, prints JSON, optionally writes to `--output` via `manifest._assert_safe_output_path`.
- **Critically: `skill_usage_metric.py` imports FROM `generate_retro.py`** (:19,
  `from generate_retro import DEFAULT_TOOLS_FILE, load_jsonl`) — a one-directional dependency.
  Confirmed via `graphify query "build_skill_usage_section"`: zero CALLS/inferred edges exist from
  `generate_retro.py` into `skill_usage_metric.py` today — nothing in `generate_retro.py` imports
  or calls `build_skill_usage_section`. This is the current state of the "not wired into the
  recurring retro" gap this ticket exists to close.

**`tools/agent-monitoring/generate_retro.py`** (recurring weekly retro, 1602 lines):
- `generate(runs, events, label, week_str, tickets_root, tools)` (:1027-1511) is the sole Markdown
  renderer. It calls a `compute_*`/`build_*` function per section, then appends `lines.append(...)`
  strings — genuinely thin rendering; every section's actual math lives in a separate pure function
  above `generate()`.
- Two established rendering conventions coexist, both real (not one "the" pattern):
  - **Conditionally rendered** (most sections): omitted entirely — not rendered empty — when the
    period has zero relevant data. E.g. `## Search & Investigation Effort` (:1417
    `if sc["total"] + ric["total"] > 0:`), `## Tool Safety Audit` (:1441
    `if sbg["investigate_pair_count"]:`).
  - **Always rendered** (exactly one section today): `## Parity Index Read-Path Usage` (:1495-1503)
    — "0 today" is itself the reportable finding (a reviewed-GO read path with zero real call
    sites), so it is deliberately never gated.
- `main()` (:1514-1559) loads `all_tools = load_jsonl(DEFAULT_TOOLS_FILE)`, slices per period
  (`--all`/`--days`/`--week`), and calls `generate(runs, events, label, week_str, tools=tools)`.
- `_update_index()` (:1561-1597) renders `agent-monitoring/retro/index.md`'s per-report trend
  table — currently columns Runs/DONE/Gate failures/Search Calls/Read Calls; adding a trended
  Skill-Usage column here (if desired) is this same function.
- **Real circular-import constraint, already hit once in this exact epic**: `generate_retro.py`'s
  own comment on `SEARCH_TOOL_NAMES` (:329-334) documents that `retrieval_baseline_metrics.py`
  imports FROM `generate_retro.py`, so `generate_retro.py` importing a name back FROM
  `retrieval_baseline_metrics.py` would create a two-file import cycle — resolved by *relocating*
  `SEARCH_TOOL_NAMES`/`build_search_count_section`/`build_raw_investigation_count_section` into
  `generate_retro.py` itself (`retrieval_baseline_metrics.py` now re-imports them back, "semantics
  and membership unchanged, only the file of definition moved"). **The identical shape of
  constraint exists here**: `skill_usage_metric.py` imports `DEFAULT_TOOLS_FILE`/`load_jsonl` FROM
  `generate_retro.py` today, so a naive top-level `from skill_usage_metric import
  build_skill_usage_section` added to `generate_retro.py` would recreate the same two-file cycle.
  This is a concrete, evidence-based fact Plan must design around (see Risks/Anti-Drift below), not
  a hypothetical.

**`.claude/skills/*/SKILL.md` catalog** (22 directories under `.claude/skills/`, matching the
ticket's "16+ entries" loosely):
- Only **8 of 22** carry a `date_added` frontmatter field: `api-design-principles`,
  `architecture` (both `date_added: "2026-02-27"`, `source: community` — disclosed origin, per
  `TCK-20260805-COMMUNITY-SKILL-SWAP-DISCLOSED`), and `backend-testing`, `cognition-strategy`,
  `combat-mechanics`, `observability`, `progression-entities`, `simq-dev`, `systems-economy` (all
  `date_added: "2026-08-05"`, `source: project`). The remaining 14 (`agent-monitoring-retro`,
  `brainstorming`, `create-tickets`, `debugging-strategies`, `doc-coauthoring`, `frontend-design`,
  `implement-epic`, `implement-ticket`, `prompt-builder`, `python-performance-optimization`,
  `python-testing-patterns`, `simq-audit`, `test-driven-development`) have **no** `date_added` or
  `source` field at all (directly grepped every `SKILL.md` in this session).
- **`SKILL.md` file mtimes are not a usable signal** — directly checked via `stat -c '%y'` on all
  22 files: every one reports essentially the same timestamp (`2026-08-14 18:23:...`, from the last
  full working-tree write/checkout), regardless of a skill's real authorship date. Using mtime as
  the grace-period clock would make every skill in the catalog read as "just created" forever.
- **No structured `skill_name -> authoring_ticket_id` mapping exists anywhere in the repo.**
  `docs/REGISTRY.yaml` indexes tickets and docs, not `.claude/skills/` files. `docs/ai/skills.md`'s
  "Project-Level Skill Files" table has a human-written `(added TCK-...)` parenthetical for exactly
  4 rows (`observability`, `simq-dev`, `systems-economy`, `combat-mechanics`, `cognition-strategy`,
  `progression-entities` — 6 total, matching the 6 domain skills) — prose, not machine-parseable
  data a script could query.
- **`git log`/`git blame` do not recover real per-skill authorship dates either** — directly tested
  `git log --follow -- .claude/skills/backend-testing/SKILL.md`: 3 commits dated 2026-08-14,
  2026-06-12, 2026-04-09 — none matches its real 2026-08-05 rewrite (confirmed by
  `TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED`'s own `date:` frontmatter and Implementation
  Notes). This repo's current branch has only 5 real commits (`git log` at session start:
  `29d78798`, `6e25d4f2`, `7a41beb5`, `677abbfb`, `ae5a965d`) — history is squashed at a
  multi-ticket-batch grain, not per-ticket, so git timestamps cannot substitute for a real
  per-skill creation date.
- `tools/validate_frontmatter.py::_ticket_id_effective_date(ticket_id)` (already imported by
  `generate_retro.py`) extracts a `YYYYMMDD` date from a `TCK-YYYYMMDD-...` string, but it requires
  *knowing* the authoring ticket_id first — which, per the point above, is not structurally
  available for skills without a `date_added` field.

**Live corpus, checked directly this session** (`python3 tools/agent-monitoring/skill_usage_metric.py`):
`observability=0, simq-dev=0, systems-economy=0, combat-mechanics=0, progression-entities=0,
cognition-strategy=1, backend-testing=0` (15 distinct skills invoked total). This has already
drifted from the ticket's own 2026-08-10 claim of "6 new bespoke domain skills ... show zero
invocations" — `cognition-strategy` now shows 1 real invocation as of this session (2026-08-15).
Expected corpus growth, matching `SKILL-USAGE-METRIC`'s own precedent of numbers drifting between
ticket-authoring and implementation — any new test must not hardcode these figures (see
`test_plan.md`).

## Mechanics / Engine Constraints

None. This is agent-orchestration/monitoring tooling (`layer: ai`), not simulation logic — no
`docs/mechanics/` chapter or `docs/engine/` contract governs `.claude/skills/` catalog behavior or
`agent-monitoring/` reporting. No `src/` file is touched by this ticket's scope.

## Docs Requiring Update

- `docs/agent-monitoring/README.md`: the existing "## Skill Usage Metric" section (:82-91)
  describes `skill_usage_metric.py` as a standalone script; needs a cadence-integration addendum
  once `build_skill_usage_section` is wired into `generate_retro.py`, matching the exact precedent
  already in this file at :61-69 ("2026-08-14 — `search_count`/`raw_investigation_count` now also
  feed the recurring cadence ...").
- `docs/guides/agent_monitoring.md`: the "## Report Sections" table (:55-72) documents every
  section `generate()` renders (e.g. the "Tool Safety Audit" and "Parity Index Read-Path Usage"
  rows added by `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`) — needs a new row for the
  `## Skill Usage` section this ticket adds, including whether it is conditionally- or
  always-rendered and how the zero-invocation flag reads.
- `docs/parity_ledger/infrastructure.yaml`: needs a new `INFRA-*` entry (next available is
  `INFRA-333`, latest existing is `INFRA-332`). See Parity Ledger Overlap below — this is not
  optional despite two prior sibling tickets in this exact area independently concluding "no `src/`
  touched, no entry needed."
- `docs/agent-monitoring/schema.md`: the ticket's AC literally names this file. Investigated its
  actual scope directly: it documents raw `runs.jsonl`/`events.jsonl`/`tools.jsonl` field
  schemas and `generate_retro.py`'s `tool == "Bash"`-subcommand-detection predicates (:406-416,
  e.g. `_is_parity_index_readpath_call`'s path-anchored regex) — it does **not** document retro
  *report section* shapes (that is `docs/guides/agent_manual.md`'s Report Sections table, above).
  Since this ticket's `## Skill Usage` section reuses `tool == "Skill"` filtering (an existing,
  already-schema-relevant `tool` value) and does not add a new `Bash`-subcommand predicate or a new
  raw JSONL field, a schema.md change may be a minimal cross-reference at most, not a new field
  entry — flag this precisely for Plan rather than assume the AC's schema.md mention implies a
  substantive schema-shape change.

If none applied this would read "None." — it does not; five real doc paths are affected as scoped.

## Parity Ledger Overlap

No existing `docs/parity_ledger/*.yaml` entry references `skill_usage_metric.py`,
`build_skill_usage_section`, or a "Skill Usage" retro section — grepped all 5 ledger files.

However, this exact class of change (a new agent-monitoring/tooling report section, zero `src/`
touched) has a strong, repeatedly-*overridden* precedent in `docs/parity_ledger/infrastructure.yaml`:
`INFRA-281` through `INFRA-332` are a continuous run of "agent-tooling-infrastructure" entries
(`INFRA-292` = the original `retrieval_baseline_metrics.py` baseline-snapshot tool this whole family
follows). Two directly relevant, real examples:
- `TCK-20260805-SKILL-USAGE-METRIC` (the ticket that built the function this ticket now wires in)
  concluded in its own Parity section: **"No `src/` files touched ... No parity ledger entry
  needed."** That conclusion was never revisited or overridden by a later ticket.
- `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING`'s own `## Parity Index Read-Path Usage`
  work hit the identical question and *also* initially concluded no entry was needed in its own
  investigation.md — but the ledger's own entry text (infrastructure.yaml :8450-8461) records that
  a parity-ledger entry was **added independently during the Parity phase anyway**, explicitly
  citing the `INFRA-281`–`INFRA-332` precedent as taking priority over that ticket's own
  investigation conclusion.

**Recommendation for Plan/Parity phase**: follow the actually-followed `INFRA-281`–`332`
precedent (add a new `INFRA-333`-range entry, `status: verified`, `priority: P2` matching every
sibling infra entry), not the two-ticket-old "no `src` touched -> no entry" reasoning that has
already been overridden once in this same epic. No `P0` entries are touched by this work.

## Prior Work

- `TCK-20260805-SKILL-USAGE-METRIC` (DONE) — built `build_skill_usage_section`, explicitly chose
  standalone-script over recurring-retro-section, "same reasoning as
  `SECURITY-GATE-FIRING-MONITOR`." This ticket directly reverses that earlier decision (now wiring
  it into the cadence) — that reversal is this ticket's whole premise, already justified in its
  Request Summary; not re-litigated here.
- `TCK-20260810-CONTEXT-TOOLING-EFFECTIVENESS-TRACKING` (sibling, just landed) — the direct,
  freshest precedent for "wire an existing metric into the recurring cadence": established both
  rendering conventions (conditional vs. always-on) used above, the exact circular-import
  resolution pattern (relocate into `generate_retro.py`, re-import back for compatibility), the
  Report Sections table doc-update convention, the README.md cadence-addendum convention, and the
  Parity-phase-overrides-investigation-conclusion precedent for `infrastructure.yaml`. Its test
  suite (`tests/tools/test_generate_retro.py:2056-2133`) is the closest test-pattern precedent:
  synthetic-fixture unit tests + one real-corpus assertion + a "never writes any file" AST-style
  guard + a "derivation key present on every new section" cross-cutting test.
- `TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC` (DONE, parent) — authored the 6 domain skills
  (`date_added: "2026-08-05"`) this ticket's grace-period flag will eventually watch.
- `TCK-20260705-SIX-SKILLS-INVESTIGATION` (DONE) — settled "correctly redundant, not a genuine gap"
  verdicts for 6 *other*, pre-existing zero-invocation skills (`test-driven-development`,
  `python-testing-patterns`, `backend-testing` *as it existed pre-2026-08-05-fix*, `architecture`,
  `brainstorming`, `doc-coauthoring`) via a 27-session-transcript manual audit. Per this ticket's
  own Out of Scope, that verdict is **not reopened** — a future zero-invocation flag firing on any
  of those 6 again (post grace-period) should surface as a signal, not automatically imply the
  prior "correctly redundant" verdict was wrong; a human reviews the flag, per this ticket's Out of
  Scope ("any decision to act on a flagged skill is a separate, later, human-reviewed step").
- `TCK-20260805-COMMUNITY-SKILL-SWAP-UNDISCLOSED` (DONE) — the historical sanity-check case; see
  next section for its concrete reconstruction.

## Risks and Open Questions

**Blocking, must be resolved by Plan with explicit reasoning (not silently defaulted):**

1. **Zero-invocation flagging logic placement** — genuinely open per the ticket's own Assumptions.
   Recommendation with evidence: the cross-reference/grace-period logic is new *skill-domain*
   logic (catalog scan + date comparison), distinct from `build_skill_usage_section`'s existing
   counting logic that Out of Scope forbids modifying — so by the house pattern (`skill_usage_metric.py`
   already frames itself as "how many times was each skill actually invoked," and the flag question
   is a direct extension of that same domain, not a `generate_retro`-owned cross-cutting concern
   like tag-breakdown/outliers/tool-safety are) it fits best as a **new function inside
   `skill_usage_metric.py`**. But the circular-import fact above (skill_usage_metric.py already
   imports FROM generate_retro.py) means `generate_retro.py` cannot do a top-level
   `from skill_usage_metric import <new_function>` without recreating the exact cycle the sibling
   ticket just fixed by *relocating* code. Two real ways around it, both viable, Plan should pick
   with reasoning: (a) mirror the sibling ticket exactly — relocate the new flagging function (and
   only the new one; `build_skill_usage_section` stays put, satisfying Out of Scope's "not
   modified") into `generate_retro.py`, with `skill_usage_metric.py` re-importing it back if CLI
   parity is wanted; (b) keep the new function inside `skill_usage_metric.py` and have
   `generate_retro.py` perform a **local/deferred import inside its own render-time function body**
   (not module-level) — Python permits this without a cycle error since by call time both modules
   are already fully initialized; zero changes to `skill_usage_metric.py`'s top-level import
   structure. Do not let this get decided implicitly by whichever agent writes the code first.

2. **Grace-period creation-date source is the fork that decides whether AC2 is even satisfiable.**
   Only 8/22 skills have a `date_added` field; mtime and git history are both confirmed-unusable
   (see Current Behavior). If the flag design treats "no `date_added`" as **exempt from flagging**
   (fail-closed — "can't prove the grace period elapsed, so don't flag"), then `backend-testing`
   in its real pre-2026-08-05 state (which had **no** `date_added`/`source` field at all — the
   entire point of it being "undisclosed") could **never** have been flagged by that design, and
   AC2's required sanity check ("correctly would have flagged `backend-testing` prior to its fix")
   becomes structurally impossible to satisfy, not just hard to test. If instead missing
   `date_added` is treated as **"creation date unknown, cannot be proven within the grace period,
   therefore eligible to flag if invocation count is zero"** (fail-open on the flagging side),
   `backend-testing`'s pre-fix state becomes correctly flaggable and AC2 is achievable. Plan must
   pick one explicitly, with reasoning tied to this exact tension — it is the single design choice
   this whole ticket's second acceptance criterion hinges on.

3. **Grace-period length (14 days proposed)** — real corroborating evidence for Plan, not a
   decision: the 6 domain skills are 10 days old as of this investigation (`date_added:
   "2026-08-05"`, today 2026-08-15) — still inside a 14-day window, consistent with the ticket's
   requirement that they not yet be flagged. `SIX-SKILLS-INVESTIGATION`'s 6 pre-existing skills
   stayed at zero invocations across a 30+ day observed window and were separately judged
   "correctly redundant" rather than "not enough time yet" — meaning a longer grace period would
   not have changed their outcome; grace-period length mainly protects genuinely-new skills, not a
   cure for structurally-redundant ones. 14 days appears reasonable but is Plan's call.

**Non-blocking:**
- Live-corpus drift is real and ongoing (`cognition-strategy` moved 0→1 between ticket-authoring
  and this investigation) — any new test must independently re-derive expected values, never
  hardcode a frozen snapshot (established convention in every sibling test file read this session).

## Anti-Drift Hazards

- **Do not modify `build_skill_usage_section`'s existing regex, counting logic, or output shape**
  — explicit Out of Scope. A new zero-invocation function must call it, not inline a second
  extraction pass (`skill_usage_metric.py`'s own test suite has an explicit
  `test_reuses_generate_retro_loader_not_a_second_loader`-style AST reuse guard; expect the same
  discipline applied here for reusing `build_skill_usage_section` itself).
- **Do not silently default the missing-`date_added` question to fail-closed** (see Risk 2) — a
  silent default would make AC2 quietly unsatisfiable while looking like an innocuous
  implementation detail. This is the single highest-leverage place scope could drift without
  anyone noticing until Verify/Done-checker finds AC2 unproven.
- **Do not re-litigate `SIX-SKILLS-INVESTIGATION`'s settled verdicts** — explicit Out of Scope. The
  new flag is a forward-looking signal generator only; it must not auto-conclude anything about the
  6 previously-assessed skills, and must not be framed in docs/tests as "proving" those verdicts
  right or wrong.
- **Do not recreate the circular-import bug** the sibling ticket just fixed (Risk 1) — a naive
  top-level `from skill_usage_metric import ...` added to `generate_retro.py` will break module
  import at collection time, likely surfacing as a confusing `ImportError` in an unrelated test
  file rather than an obvious error at the edit site.
- **Do not hardcode the 6 domain skills' current zero/near-zero invocation counts into a test** —
  they are real, live, and already drifting (`cognition-strategy` now 1, not 0). Tests must
  independently re-derive expected values or use synthetic fixtures, matching every sibling test
  file's established convention.
- **Do not conflate "flag exists and is correct" with "flag should trigger action"** — explicit Out
  of Scope: no auto-deprecation, no auto-invocation. The section is visibility only.
