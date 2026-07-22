---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER
artifact_type: investigation
tags: [ai, workflows]
---

# Investigation — TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER

## Current Behavior

### The contract (`agent-orchestration/`, built by TCK-20260721-ORCHESTRATION-CONTRACT-CORE, DONE)
Six files: `contract.yaml`, `workflows/implement-ticket.yaml`, `roles/*.yaml` (10 files), `skills.yaml`,
`monitoring-schema.yaml`, `hook-events.yaml`. `workflows/implement-ticket.yaml` declares 11 phases
(`Scope`...`Finalize`) with a per-phase `tiers: {standard, hotfix}` value from
`{full, skipped_event, conditional}`, plus `agents: [...]` (10 role ids). **It has no
terminal-status field anywhere** — confirmed by `grep -rn "terminal" agent-orchestration/` (zero
hits) and by reading all six files in full. `roles/*.yaml` each carry `role_version`, `role_id`,
`description`, `phases`, `has_agent_file` (`finalizer.yaml` additionally carries
`inline_prompt_exception`, documenting that it has no `.claude/agents/finalizer.md` file — it's an
inline `agent(...)` prompt in `implement-ticket.js` ~1151-1255).

### The validator/generator (`tools/agent_orchestration/`, same predecessor ticket)
- `loader.py::load_contract(root: Path) -> ContractBundle` — reads and validates all six files,
  raises `ContractValidationError` naming the exact file/field on any missing/malformed value.
  Read-only; only `yaml.safe_load` + stdlib.
- `generator.py::generate(repo_root, target_dir, *, allow_outside_contract=False) -> list[Path]` —
  loads the bundle via `load_contract()` and **re-serializes it back out as YAML** under
  `target_dir`. Structural write-guard (`_assert_write_allowed`, generator.py:28-37) refuses any
  write outside `repo_root / "agent-orchestration"` unless `allow_outside_contract=True` is passed
  explicitly — a real `Path.resolve().is_relative_to(...)` check performed before every write, not
  a docstring convention. **This existing generator is a contract-to-contract round-trip
  (self-serialization), not a Claude-shaped rendering** — it writes the same field names/structure
  it read, just re-materialized as fresh YAML files. It is not the "Claude adapter representation"
  this ticket's AC #1 asks for; it is the reusable read path (`load_contract`) this ticket's own
  generator should call, per this ticket's own Related Code Areas note to reuse `loader.py`
  read-only.

### The live pipeline (`.claude/workflows/implement-ticket.js`, 1301 lines, read in full)
- `export const meta = { name, description, phases: [...] }` at lines 1-17. `meta.phases` is an
  array of `{ title, detail }` objects; the 11 `title` values (in order): `Scope`, `Investigate`,
  `Plan`, `Review`, `Implement`, `Architecture-Verify`, `Test`, `Parity`, `Security-Review`,
  `Verify`, `Finalize` — byte-identical, in the same order, to `workflows/implement-ticket.yaml`'s
  11 `phases[].name` entries. **No divergence found in phase order or phase-name set** between the
  contract and the live source as of this investigation.
- Every `phase(...)` call site matches a `meta.phases` title 1:1 (verified by reading the whole
  file: `phase('Scope')` L29, `phase('Investigate')` L424, `phase('Plan')` L465, `phase('Review')`
  L533, `phase('Implement')` L602, `phase('Architecture-Verify')` L702, `phase('Test')` L777,
  `phase('Parity')` L881, `phase('Security-Review')` L1022 (inside the tag/suggested_skills
  conditional), `phase('Verify')` L1072, `phase('Finalize')` L1151).
- **Terminal-status (`writeMonitoring(...)`) call sites — exhaustive, re-verified against the
  predecessor ticket's own grepped inventory** (`stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/investigation.md:78-113`,
  confirmed by independently re-reading the live file line-by-line in this investigation):

  | Call site | Literal / derived value(s) |
  |---|---|
  | `:372` | `CONFLICTS_DETECTED` |
  | `:384` | `TAGS_NOT_REGISTERED` |
  | `:399` | `EPIC_SCOPED` |
  | `:182` (bypasses `writeMonitoring` entirely — direct `record_run.py --data`/`record_events.py --data` bash calls, since `tid`/`events`/`pushEvent`/`writeMonitoring` don't exist yet at this point) | `SCOPE_AGENT_FAILED` |
  | `:520` | `NEEDS_HUMAN_INPUT` |
  | `:582` (`writeMonitoring(review.verdict)`; verdict enum at `:539` is `['APPROVED','NEEDS_CHANGES','BLOCKED']`; only fires when verdict ≠ `APPROVED`) | `NEEDS_CHANGES` or `BLOCKED` |
  | `:684` | `DOC_STALENESS_BLOCKED` |
  | `:760` (`writeMonitoring(archVerify.verdict)`, same enum shape as Review) | `NEEDS_CHANGES` or `BLOCKED` |
  | `:817` | `TESTS_FAILED` |
  | `:864` | `DATA_RUNS_CLEAN_FAILED` |
  | `:999` | `PARITY_INCOMPLETE` |
  | `:1057` | `SECURITY_BLOCKED` |
  | `:1137` | `DOD_BLOCKED` |
  | `:1234`, `:1246` | `FINALIZE_INCOMPLETE` (same literal, two call sites: unparseable self-check output vs. a real failing condition) |
  | `:1256` | `DONE` |

  13 literal `writeMonitoring('STRING')` call sites + 2 call sites whose argument is a verdict
  variable (`NEEDS_CHANGES`/`BLOCKED`, shared value space across Review and Architecture-Verify) —
  matches this ticket's own scope text ("~13 literal + 2 verdict-derived") exactly. **15 distinct
  terminal-status values total** reachable through `writeMonitoring()`, plus one
  (`SCOPE_AGENT_FAILED`) that bypasses it structurally.
- `docs/agent-monitoring/schema.md`'s `final_status` table (read in full, lines 51-72) lists these
  same 15 `implement-ticket` values plus `IN_PROGRESS` (run-start sentinel, never written by
  `implement-ticket.js` itself — written by `record_run.py` before any `writeMonitoring` call
  resolves) and `CRASHED` (synthetic, assigned at read-time by `validate.py` for runs with
  `start_ts` but no `end_ts`), plus `NOTHING_TO_CREATE` (belongs to `create-tickets`, not this
  workflow). This doc was independently re-checked against the live source in this investigation
  and found accurate — no drift.

### Phase-order extraction precedent (`tools/gate_checks/workflow_meta_conformance.py`, read in full)
`extract_meta_phases(workflow_js_path)` (lines 51-79): locates the `phases: [` block via
`_PHASES_BLOCK_START_RE = re.compile(r"phases:\s*\[")`, then does a manual bracket-depth scan
(`depth` counter over `[`/`]` characters) to find the matching close bracket — explicitly not a
general JS parser, justified by the docstring as safe because "the block never nests further in
any of the three in-scope workflow files." Within that block, `_TITLE_RE =
re.compile(r"title:\s*'([^']+)'")` extracts every `title` value. Returns `[]` (never raises) if no
`phases: [` block is found. `tests/tools/test_workflow_meta_conformance.py::test_parses_meta_phases_from_implement_ticket_js`
asserts the exact 11-title list against the real live file — this is the existing regression proof
this ticket's own phase-order conformance test should build on (reuse the function directly, don't
reimplement).

**No equivalent extractor exists for terminal statuses.** `workflow_meta_conformance.py` only
extracts `meta.phases` titles; nothing in this repo today parses `writeMonitoring('...')` call
sites out of a workflow `.js` file. This part of AC #3 is genuinely new tooling, not a reuse of an
existing extractor — confirmed by grepping `tools/gate_checks/` and `tools/agent-monitoring/` for
`writeMonitoring` (zero hits outside `implement-ticket.js`/`implement-epic.js` themselves).

## Mechanics / Engine Constraints
Not applicable. This ticket touches only agent-orchestration tooling (`tools/`,
`agent-orchestration/`, tests) — no `src/` simulation code, no `docs/mechanics/` chapter, no
`docs/engine/` contract governs Claude-conformance tooling.

## Parity Ledger Overlap
None found. `docs/parity_ledger/infrastructure.yaml` (grepped for `orchestrat|conformance|claude.*adapter|implement-ticket`)
has entries referencing `implement-ticket.js` gate-check wiring (e.g. `run_finalize_selfcheck`,
`resolveScopeTicketLocation`) but none for the `agent-orchestration/` contract or Claude-conformance
tooling — expected, since the predecessor ticket (`TCK-20260721-ORCHESTRATION-CONTRACT-CORE`)
reported `behavior_changed: false` and made no `src/` change. This ticket is likewise scoped to be
read-only against `implement-ticket.js` and produce no simulation-behavior change, so no parity
ledger entry should be required — confirmed no P0 entry anywhere references this subsystem.

## Prior Work
- **`TCK-20260721-ORCHESTRATION-CONTRACT-CORE`** (DONE, `stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-CORE/`):
  built the contract this ticket diffs against. Its own investigation.md
  (`investigation.md:73-108`) already did the exhaustive terminal-status grep this investigation
  re-verified, under its own "Assumptions / Open Questions": *"Terminal statuses currently live
  only in implement-ticket.js prose/schema.md with no structured source — roles/*.yaml and
  terminal-status structuring is new modeling work with no existing source to lift from."*
  **Its plan.md never mentions "terminal" once** (grepped, zero hits) — the investigation-phase
  observation was never carried into that ticket's scope or implementation. `workflow_version: 1`
  ships with zero terminal-status representation. This is a real, unresolved gap this ticket
  inherits, not a misreading of the contract.
- **`TCK-20260721-CODEX-REPLAY-PROOF`** (DONE): built `tools/agent_replay/runner.py` +
  `fixture_envelope.py` + the two AST/snapshot test precedents this ticket should mirror for its
  own AC #1 (zero-diff) and AC #6 (AST no-write-mode/subprocess) requirements —
  `tests/agent_replay/test_no_mutation_snapshot.py`'s porcelain-then-content-hash-fallback pattern
  for proving zero mutation of a real (not tmp-copied) directory tree, and
  `tests/agent_replay/test_runner_no_forbidden_calls.py`'s AST `_dotted_call_name`/
  `_string_constants_in` scan pattern for proving a module never imports/calls/references forbidden
  targets — both directly reusable techniques, only the forbidden-target sets and watched paths
  need to change (watched path becomes `.claude/` instead of `tickets/`+`agent-monitoring/`;
  forbidden calls become write-mode `open()`/`subprocess.*` against `implement-ticket.js` instead of
  the four monitoring scripts).
- **`tests/agent_orchestration/test_validator_no_network_calls.py`** (from
  `TCK-20260721-ORCHESTRATION-CONTRACT-CORE`) is the closest existing precedent for an AST
  write/network-call guard scoped to a specific tool package (`tools/agent_orchestration/`), plus a
  `_SCOPE_CREEP_MARKERS` string-substring scan (`.codex/`, `conformance_diff`, `claude_conformance`,
  `.claude/conformance`) proving that ticket's own tree never started the out-of-scope
  Claude-conformance work — i.e. the predecessor ticket already anticipated and fenced off this
  ticket's exact scope, from the other side.
- **`docs/architecture/agent_orchestration_contract.md`** (the ADR): "Conformance Mechanism"
  section explicitly names all 4 axes conformance tests must check: "phases, terminal statuses,
  gate policy, and artifact requirements" (Status: Proposed-pending-implementation-evidence) — this
  ticket is the first one to actually build that mechanism, so its test shape is not itself
  pre-constrained by any earlier implementation.
- **`docs/ai/replay_fixture_spec.md`**: explicitly disclaims itself as *not* the same artifact as
  the ADR's future `agent-orchestration/contract.yaml`-adjacent representation work — confirms this
  ticket's deliverable is a distinct concern from the replay-fixture format, not overlapping scope.

## Risks and Open Questions

1. **BLOCKING — the contract has no terminal-status representation to diff against.** AC #1 asks
   for a generator that "renders a Claude adapter representation from the contract"; AC #3 asks for
   a conformance test that "asserts full match to the contract's status representation." No such
   representation exists in any of the six `agent-orchestration/` files today (verified: zero hits
   for "terminal" anywhere under `agent-orchestration/`). The predecessor ticket explicitly deferred
   this as unaddressed, non-scope work. **This ticket's Plan phase must decide, not assume:**
   (a) whether this ticket adds a terminal-status field/file to the existing contract (extending
   `workflows/implement-ticket.yaml` or a new sibling file under `agent-orchestration/`, even though
   `agent-orchestration/` is not listed in this ticket's own "Related Code Areas"), or (b) whether
   this ticket defines the terminal-status vocabulary as its own authoritative reference data
   (e.g. hardcoded/sourced from the now-reconfirmed-accurate `docs/agent-monitoring/schema.md`
   table) external to the six contract files, treating it as this ticket's own "Claude adapter
   representation" input rather than something read out of `load_contract()`. Per the README's
   versioning note, adding a new optional field to an existing file would not require a
   `workflow_version` bump; adding a new file would not need any bump at all — so the versioning
   mechanics do not block either option, but the *ownership* boundary (this ticket doesn't list
   `agent-orchestration/` as a Related Code Area) does need a decision.
2. **What "rendered Claude adapter representation" concretely means is genuinely underspecified.**
   The existing `generate()` function in `tools/agent_orchestration/generator.py` is a
   contract-to-contract round-trip (same field names, same YAML shape, just re-serialized) — not
   Claude-shaped in any sense (it doesn't reference `.claude/workflows/*.js`'s `title`/`detail`
   shape, `writeMonitoring` literals, or anything provider-specific). The ADR's Conformance
   Mechanism section states only the *principle* ("verifying each adapter's translated
   configuration does not diverge...") with "no further detail on test shape, location, or
   invocation" (ADR: "this ADR does not invent one beyond the stated principle"). This ticket's
   own AC text ("running it produces zero git diff under .claude/ before/after") clarifies that the
   representation must NOT be written into `.claude/` — it is a read-only projection generated
   elsewhere (most likely under `agent-orchestration/` itself, consistent with `generate()`'s
   existing write-guard default, or a location under this ticket's own `tools/` package) that
   *mirrors the shape* `.claude/workflows/implement-ticket.js`'s `meta.phases` array uses (`title`,
   `detail`-equivalent), so the conformance test can diff it 1:1 against the live extraction. This
   still leaves the exact target directory/filename undecided — a Plan-phase decision, not
   something the investigation should assume.
3. **"Human-approved divergence" has no existing convention anywhere in this repo to reuse.**
   Neither `docs/guidelines/intentional_divergences.md` (the mechanics-bible log — reviewer/date
   fields not used there either; its records carry `Rationale Class`/`Status` (RATIFIED/DEFERRED),
   no named-human-approval field) nor any `tools/` module defines a "reviewer + date" parsed/
   enforced field format. This is genuinely new modeling work the Plan phase must specify precisely
   (exact heading/field names, exact parse regex or YAML-key contract) — not something this
   investigation can infer from a precedent, per the ticket's own Assumptions/Open Questions.
4. **Zero-diff-under-`.claude/` proof needs a real containment test**, mirroring
   `test_no_mutation_snapshot.py`'s porcelain-or-content-hash-fallback pattern (this repo's tree is
   routinely dirty during active development, so a naive "must start clean" gate would false-skip on
   nearly every real run here) — but scoped to `.claude/` specifically rather than `tickets/`+
   `agent-monitoring/`.
5. **`FINALIZE_INCOMPLETE` appears at two distinct call sites (`:1234`, `:1246`) with the same
   literal value** — an extractor built with a naive "assert exactly one call site per status
   string" invariant would false-fail on this one legitimate duplicate. The extractor and any
   conformance assertion must tolerate (or explicitly dedupe) this.
6. **`SCOPE_AGENT_FAILED` structurally bypasses `writeMonitoring()`** — a regex/AST extractor that
   only looks for `writeMonitoring(...)` call arguments will miss it entirely, since it's written via
   a raw `bash()`-embedded `record_run.py --data '{...,"final_status":"SCOPE_AGENT_FAILED",...}'`
   Python one-liner (lines 178-183), not a JS string literal passed to a named helper function. The
   extraction technique's design must explicitly decide whether to also capture this value (e.g. by
   also scanning for `"final_status":"..."` JSON-key patterns inside `bash()` template strings) or
   explicitly document it as an intentionally out-of-scope edge case with a stated reason — silently
   omitting it without a decision would under-report the true vocabulary.
7. **`docs/guidelines/intentional_divergences.md` is layer `guidelines`, audience `developer`, and
   is a subsystem-behavior (Mechanics Bible) divergence log** — its own frontmatter and content
   (RPG-CORE, World Assembly, Engine/Cognition entries) confirm it is a different subsystem/format
   entirely from what this ticket needs. No structural or content conflict with creating
   `agent-orchestration/intentional-divergences.md` as a wholly separate file — the ADR's own
   "Source Ownership" section (`docs/architecture/agent_orchestration_contract.md:73`) already names
   `intentional-divergences.md` as part of `agent-orchestration/`'s originally proposed layout, so
   this ticket's plan to create it there is consistent with, not a deviation from, the ADR.

## Anti-Drift Hazards
- **Never open, write, or subprocess-touch `.claude/workflows/implement-ticket.js`** from any tool
  built in this ticket. All extraction must be read-only (`Path.read_text()` only), mirroring
  `extract_meta_phases`'s existing pattern exactly. AC #6's AST guard must scan this ticket's own
  new `.py` files (whichever package it lands in) the same way
  `tests/agent_replay/test_runner_no_forbidden_calls.py` scans `tools/agent_replay/` — including the
  whole-file string-constant scan (not just call-argument-scoped nodes), per that precedent's own
  documented rationale for the wider scan (`test_no_forbidden_filename_substring_in_any_string_constant_in_the_file`).
- **Do not write into `docs/guidelines/intentional_divergences.md`** (Out of Scope, explicit). The
  new `agent-orchestration/intentional-divergences.md` is a distinct file with a distinct purpose —
  keep any generator/test code from accidentally resolving a path into the wrong file (e.g. a
  copy-pasted path constant).
- **Do not implement the Codex-side adapter** — no `.codex/` files, no `conformance_diff`/
  `claude_conformance` module names (per the existing `_SCOPE_CREEP_MARKERS` precedent in
  `test_validator_no_network_calls.py`, which already scans for exactly this leakage from the
  contract-core side; this ticket's own tests should apply the analogous guard against the Codex
  side to keep the boundary honest in both directions, if that's judged in-scope by Plan).
- **Do not conflate "skipped_event" (an explicit `skipped`-status event still written) with
  "conditional_absent" (zero events at all)** — `workflows/implement-ticket.yaml`'s own header
  comment (lines 8-14) already documents this distinction precisely; a Claude adapter
  representation that collapses the two would silently misrepresent Security-Review's real
  behavior (fully absent, not skipped) vs. Investigate/Plan/Review/Architecture-Verify's real
  hotfix-tier behavier (explicitly skipped-status event written).
- **Do not treat `NEEDS_CHANGES`/`BLOCKED` as belonging to a single call site** — they are shared
  values reachable from two distinct phases (Review, Architecture-Verify) via two distinct verdict
  variables with the same enum shape. A conformance mapping that assumes a 1:1 phase→status
  relationship will misrepresent this.
- **Do not silently invent an operational meaning for "human-approved"** without flagging it as a
  net-new decision requiring explicit Plan-phase sign-off — there is no existing convention to
  quietly reuse.
