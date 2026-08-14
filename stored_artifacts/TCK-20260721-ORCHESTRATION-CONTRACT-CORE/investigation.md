---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-ORCHESTRATION-CONTRACT-CORE
artifact_type: investigation
tags: [ai, workflows, process-improvement]
---

# Investigation — TCK-20260721-ORCHESTRATION-CONTRACT-CORE

## Current Behavior

### `agent-orchestration/` does not exist yet
Confirmed: `ls agent-orchestration/` → no such directory. This ticket creates it from
scratch; there is nothing to migrate or merge, only a layout decision to apply (see
Mechanics/Engine Constraints below for the exact approved layout and one real naming
discrepancy in the source material).

### `tools/agent-monitoring/vocabulary.py` (bootstrap source) — full contents, no drift found
`tools/agent-monitoring/vocabulary.py:1-95` exports:
- `CANONICAL_TIERS = {"hotfix", "standard", "epic", "n/a"}`
- `WORKFLOW_PHASES["implement-ticket"]` (`vocabulary.py:21-24`) = `{Scope, Investigate, Plan,
  Review, Implement, Architecture-Verify, Test, Parity, Security-Review, Verify, Finalize}` — 11
  phases, one flat set (no tier split).
- `WORKFLOW_AGENTS["implement-ticket"]` (`vocabulary.py:40-44`) = `{ticket-scoper, investigator,
  planner, architecture-reviewer, implementer, test-scoper, parity-updater, security-reviewer,
  done-checker, finalizer, implement-ticket-orchestrator}` — 11 agents.
- `is_known_agent()`, `infer_workflow()` — helper functions, not vocabulary data themselves.

**Cross-checked against every real `phase(...)`/`pushEvent(...)` call site in
`.claude/workflows/implement-ticket.js` (1300 lines, read in full) — verdict: exact match, zero
drift**, despite the module's own docstring (`vocabulary.py:9-13`) warning that `schema.md`'s
prose tables were found stale in the past (missing simq-audit's workflow, missing
Architecture-Verify). That staleness applied to `docs/agent-monitoring/schema.md`, not to
`vocabulary.py` itself — `vocabulary.py` is confirmed accurate as of this investigation:

- 11 phases confirmed by call site: `phase('Scope')` (`implement-ticket.js:29`),
  `phase('Investigate')` (424), `phase('Plan')` (465), `phase('Review')` (533), `phase('Implement')`
  (602), `phase('Architecture-Verify')` (702, inside `if (tier !== 'hotfix')`), `phase('Test')`
  (777), `phase('Parity')` (881), `phase('Security-Review')` (1022, inside the security-tag `if`),
  `phase('Verify')` (1072), `phase('Finalize')` (1151).
- 11 agents confirmed by `pushEvent`/`agentType` call site: `ticket-scoper` (357), `investigator`
  (461), `planner` (529), `architecture-reviewer` (581, 591, 759, 769 — used for both Review and
  Architecture-Verify), `implementer` (618 sidecar, 642 `agentType`, 674-675 `pushEvent`),
  `test-scoper` (815, 827), `implement-ticket-orchestrator` (862, the Test-phase cleanup-failure
  pseudo-agent), `parity-updater` (917, 998, 1011), `security-reviewer` (1056, 1066), `done-checker`
  (1134, 1147), `finalizer` (1153, 1233, 1245, 1255, 1284).
- `schema.md`'s `phase` table (`docs/agent-monitoring/schema.md:195-202`) independently lists the
  same 11 phases and explicitly defers to `vocabulary.py` as tie-breaker
  (`schema.md:193`: "if they disagree with `vocabulary.py`, the module wins") — no disagreement
  found.

**Tier structure is NOT captured by `vocabulary.py` at all** — it is a flat set with no
per-phase tier-applicability flag. The real tier distinction lives only in
`implement-ticket.js`'s branch structure:
- Hotfix tier does **not** literally omit Investigate/Plan/Review/Architecture-Verify from
  `events.jsonl` — it emits `status: 'skipped'` events for all four
  (`implement-ticket.js:595-597` for Investigate/Plan/Review, `:772` for Architecture-Verify,
  inside the `else` branch of `if (tier !== 'hotfix')`).
- `Security-Review` is the one phase that is **fully absent** (not even a `skipped` event) for
  tickets whose tags don't include `security` and whose `suggested_skills` doesn't include
  `/security-review` — confirmed by `implement-ticket.js:1020-1068` having no `else` branch that
  pushes a skipped event. This matches `docs/agent-monitoring/schema.md:199-202` exactly.
- `Parity` similarly emits `skipped` when there is no `src/` change and `behavior_changed` is
  false (`implement-ticket.js:917`) — independent of tier.

This means bootstrapping `workflows/implement-ticket.yaml`'s vocabulary from `vocabulary.py` gives
the phase/agent *names* for free, but the **per-phase tier-applicability model** (which phases run
vs. skip for hotfix) is new modeling work that must be derived from `implement-ticket.js`'s branch
structure directly — `vocabulary.py` has no equivalent data to bootstrap from. This is exactly what
the ticket's own "Assumptions/Open Questions" section already flags: "Terminal statuses currently
live only in implement-ticket.js prose/schema.md with no structured source — roles/*.yaml and
terminal-status structuring is new modeling work with no existing source to lift from" — the same
is true for the phase-tier matrix, not just terminal statuses.

### Terminal-status (`final_status`) inventory — real, exhaustive, grepped
Every `writeMonitoring(...)` call site in `implement-ticket.js`, plus the one path that bypasses
`writeMonitoring` entirely:

| Literal call site | final_status value(s) |
|---|---|
| `:372` | `CONFLICTS_DETECTED` |
| `:384` | `TAGS_NOT_REGISTERED` |
| `:399` | `EPIC_SCOPED` |
| `:182` (bypasses `writeMonitoring`, direct `record_run.py --data` call — see below) | `SCOPE_AGENT_FAILED` |
| `:520` | `NEEDS_HUMAN_INPUT` |
| `:582` (`writeMonitoring(review.verdict)`, verdict enum `['APPROVED','NEEDS_CHANGES','BLOCKED']` at `:539`; only fires when verdict ≠ APPROVED) | `NEEDS_CHANGES` or `BLOCKED` |
| `:684` | `DOC_STALENESS_BLOCKED` |
| `:760` (`writeMonitoring(archVerify.verdict)`, same enum) | `NEEDS_CHANGES` or `BLOCKED` |
| `:817` | `TESTS_FAILED` |
| `:864` | `DATA_RUNS_CLEAN_FAILED` |
| `:999` | `PARITY_INCOMPLETE` |
| `:1057` | `SECURITY_BLOCKED` |
| `:1137` | `DOD_BLOCKED` |
| `:1234`, `:1246` | `FINALIZE_INCOMPLETE` |
| `:1256` | `DONE` |

`SCOPE_AGENT_FAILED` (`implement-ticket.js:164-189`) is structurally special: it fires *before*
`tid`/`events`/`pushEvent`/`writeMonitoring` exist (Scope-phase agent returned null/malformed
output with no `ticket_id`), so it writes a minimal record directly via
`record_events.py --data`/`record_run.py --data` bash calls rather than the normal
`writeMonitoring()` helper. `IN_PROGRESS` and `CRASHED` are not written by
`implement-ticket.js` at all: `IN_PROGRESS` is the run-start sentinel `record_run.py` writes before
any `writeMonitoring` call resolves; `CRASHED` is a synthetic value `validate.py` assigns at
read-time to runs with `start_ts` but no `end_ts` (`docs/agent-monitoring/schema.md:72`) — neither
belongs in a phase→terminal-status contract mapping the same way the 15 explicit values above do.

`docs/agent-monitoring/schema.md`'s `final_status` table (`schema.md:51-72`) lists exactly these
15 implement-ticket-workflow values plus `IN_PROGRESS`, `CRASHED`, and `NOTHING_TO_CREATE`
(the last belongs to `create-tickets`, out of this ticket's scope) — **confirmed accurate, no
drift found** between `schema.md`'s prose table and the real `.js` source for this workflow.

### `roles/*.yaml` — which real roles exist, and which don't have a `.claude/agents/*.md` file
`ls .claude/agents/` → `architecture-reviewer.md`, `concern-investigator.md`, `done-checker.md`,
`implementer.md`, `investigator.md`, `mechanics-auditor.md`, `parity-updater.md`, `planner.md`,
`security-reviewer.md`, `simulation-analyst.md`, `test-scoper.md`, `ticket-scoper.md`,
`world-debugger.md`. Of the 11 `implement-ticket` agent names in `vocabulary.py`:
- 9 have a matching `.claude/agents/{name}.md` subagent file: `ticket-scoper`, `investigator`,
  `planner`, `architecture-reviewer`, `implementer`, `test-scoper`, `parity-updater`,
  `security-reviewer`, `done-checker`.
- `finalizer` has **no** `.claude/agents/finalizer.md` file — confirmed by grep, it is an inline
  `agent(...)` prompt embedded directly in `implement-ticket.js` (around `:1151-1255`), not a
  separate subagent definition.
- `implement-ticket-orchestrator` is not a role at all — it is the orchestrator's own pseudo-agent
  label, used only once, for the Test-phase post-test cleanup failure event (`:862`). It should not
  appear in `roles/*.yaml` as a role entry.

### Skills vocabulary — distinct from roles
`.claude/skills/` (`ls` output) contains 16 skill directories: `agent-monitoring-retro`,
`api-design-principles`, `architecture`, `backend-testing`, `brainstorming`, `create-tickets`,
`debugging-strategies`, `doc-coauthoring`, `frontend-design`, `implement-epic`, `implement-ticket`,
`prompt-builder`, `python-performance-optimization`, `python-testing-patterns`, `simq-audit`,
`test-driven-development`. These are the "reusable skill" semantic concern from the plan's
Provider-Native Delivery table (`implementation_plan.md:126`: `.claude/skills/` ↔ `.agents/skills/`),
distinct from `roles/*.yaml` (ticket-scoper/investigator/planner/etc. subagents). Neither the ADR
nor the implementation plan specifies `skills.yaml`'s exact schema beyond "semantic skill catalog
and provider mappings" (`implementation_plan.md:109`) / "skill-to-workflow/role mappings"
(`idea_provider_agnostic_agent_orchestration.md:170`) — this is genuinely thin and the Plan phase
must decide a minimal shape for the first vertical slice (see Risks below).

`tickets/todos/provider-agnostic-implementation/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE.md`
(the sibling ticket that consumes `skills.yaml`) confirms the intended relationship precisely: its
AC #3 requires the generated Codex `.agents/skills/` catalog to be traceable "back to contract
source fields, not merely asserting human review occurred" — i.e. `skills.yaml` entries need
stable, referenceable identifiers (not free prose) for that later ticket's generator to point at.

### `hook-events.yaml` — normalized lifecycle-event vocabulary
`.claude/settings.json`'s `hooks` key (`:54-` onward) only registers `PreToolUse` and
`PostToolUse` matchers today — these are the two real lifecycle events currently in use. No
`SessionStart`/`Stop`/other hook type is wired. This is the minimal real vocabulary
`hook-events.yaml` has to normalize for the first vertical slice; anything beyond these two would
be speculative.

### `FixtureValidationError` pattern (mirror target for the new validator's error type)
`tools/agent_replay/fixture_envelope.py:22-23`: `class FixtureValidationError(Exception): """Raised
by load_fixture when a required envelope field is missing or null."""` — a single flat exception
class, no subclass hierarchy, raised with an f-string naming the exact file path and the exact
missing field (e.g. `f"{path}: source is missing required field '{key}'"`,
`f"{path}: phases[{idx}] is missing required field '{key}'"`). `load_fixture()`
(`fixture_envelope.py:46-86`) is a single validation entry point returning a frozen dataclass
(`FixtureEnvelope`) on success. This is the exact shape the ticket's AC asks the new
contract validator to mirror ("raises a named, deterministic error type... mirroring the
FixtureValidationError pattern").

### Existing single-source-of-truth test precedent
`tests/tools/test_validate_agent_monitoring.py:188-193`
(`test_canonical_vocabulary_single_sourced`) asserts `record_events.WORKFLOW_PHASES is
validate.WORKFLOW_PHASES` and `record_events.infer_workflow is validate.infer_workflow` — an
object-identity check (both modules import the *same* object from `vocabulary.py`, not two typed-out
copies). This is the structural precedent this ticket's bootstrap-equality test should follow: for a
one-time bootstrap, the check cannot be identity (the contract is YAML-loaded data, not the same
Python object as `vocabulary.py`'s sets) — it must be an explicit **value-equality** assertion
(`set(contract_phases) == vocabulary.WORKFLOW_PHASES["implement-ticket"]`, etc.), run once as a
bootstrap-correctness check, not as an ongoing single-source guarantee the way the existing identity
test is.

### AST-based "no forbidden calls"/write-guard precedent
`tests/agent_replay/test_runner_no_forbidden_calls.py` (full file read) is a real, working
precedent for exactly the kind of static, source-level guarantee this ticket's "zero network
calls" and "writes zero files outside `agent-orchestration/` unless the explicit generation flag is
passed" ACs need: it walks `ast.parse()`'d trees of every `.py` file in a directory, checking for
forbidden `import`/`ImportFrom` names, forbidden dotted-call tails (e.g. `subprocess.run`), and
forbidden string-literal substrings anywhere in the file (not just inside call arguments, to catch
indirect variable-based construction). No existing precedent specifically targets "no network
calls" (no `socket`/`urllib`/`requests`/`http.client` guard exists anywhere in the repo today) —
this is genuinely new, not lifted from an existing test.

## Mechanics / Engine Constraints

Not applicable — this ticket touches only agent-orchestration tooling
(`tools/`, a new `agent-orchestration/` directory, tests), not `src/` simulation code. No
`docs/mechanics/` chapter or `docs/engine/` contract governs YAML contract validators. The
constraints that do bind this ticket come from `docs/architecture/agent_orchestration_contract.md`
(the ADR), read in full:

- **Contract Representation and Format** (`agent_orchestration_contract.md:55-64`, Status: Decided) —
  YAML for human-reviewable definitions, generated Python validation models. Binding: the contract
  files must be plain YAML; validation logic must be Python, generated or derived from the YAML
  (not hand-written Pydantic models maintained independently).
- **Source Ownership** (`:66-78`, Status: Decided) — repo-root `agent-orchestration/` as a source
  specification, not a second implementation, per the proposed layout. **Naming discrepancy found**:
  the ADR's own quoted layout at `:71-74` (paraphrasing the *earlier* source-plan doc,
  `idea_provider_agnostic_agent_orchestration.md:158-178`, verified directly) uses
  `agents/<role>.yaml`, while the *later* `implementation_plan.md`'s "Common Contract and Adapter
  Model" section (`implementation_plan.md:104-113`, verified directly) uses `roles/<role>.yaml`.
  The ticket's own Scope/AC text already resolves this in favor of `roles/*.yaml`
  (`tickets/inprogress/TCK-20260721-ORCHESTRATION-CONTRACT-CORE.md:35,49`), matching the newer
  `implementation_plan.md` naming — not a blocking question, but worth recording since a reader
  cross-referencing the ADR text literally would see `agents/` and could be confused.
- **Versioning** (`:80-90`, Status: Proposed-pending-implementation-evidence) — `contract.yaml`
  must carry a `version` field named consistently with `workflow_version`/`hook_schema_version`.
  Scheme (semver vs. integer generation) explicitly left open — this ticket's Plan phase must
  decide it, per the ticket's own Scope line 36 and Assumptions/Open Questions line 86.
- **Provider-Adapter Boundary** (`:92-103`, Status: Decided) — `.claude/`/`.codex/` adapters may not
  silently redefine phases, terminal statuses, gate policy, or artifact requirements; not directly
  exercised by this ticket (no adapter code here) but constrains how `roles/*.yaml`/
  `workflows/implement-ticket.yaml` must be worded (authoritative semantics, not
  provider-invocation syntax).
- **Conformance Mechanism** (`:105-114`, Status: Proposed-pending-implementation-evidence) — out of
  this ticket's scope per the ticket's own "Out of Scope" (Claude conformance/diff tooling is a
  separate ticket).
- **Execution Identity** (`:116-162`, Status: Consumed-as-input) — `execution_id`, `run_id`,
  `ticket_id` field shapes are already decided by `TCK-20260721-MONITORING-WRITER-DECISION`; the
  contract's `monitoring-schema.yaml` should carry these as already-decided inputs, not re-derive
  them.

Note: the ADR document's own top-level `## Status` field (`agent_orchestration_contract.md:22-23`)
still reads `Proposed` — the *document* has not been flipped to `Accepted`, even though the ticket
that wrote it is in `tickets/done/` and even though each individual Decision subsection carries its
own `Status: Decided`. Per the ADR's own Context section (`:26-32`), this ADR is discovery output
#2 of a 5-output exit gate, and the full discovery epic isn't "complete" until all 5 are reviewed —
the document-level `Proposed` status reflects that outer gate, not doubt about the per-decision
`Status: Decided` lines themselves. Treat the individual `Status: Decided` lines as binding (per
this ticket's own instructions), and the document-level `Proposed` as a discovery-epic bookkeeping
artifact, not a blocker.

## Parity Ledger Overlap

None. Checked all 8 `docs/parity_ledger/*.yaml` files by subsystem name — none cover agent
orchestration, monitoring vocabulary, or workflow tooling; the parity ledger tracks simulation
mechanics (combat, economy, strategic cognition, world dynamics, etc.), not agent-tooling
contracts. No entry ID needs updating for this ticket.

## Prior Work

All five evidence-input tickets this ticket depends on are already in `tickets/done/` with stored
artifacts in `stored_artifacts/`:

- `TCK-20260721-ORCHESTRATION-CONTRACT-ADR` (`stored_artifacts/TCK-20260721-ORCHESTRATION-CONTRACT-ADR/`) —
  produced the ADR this ticket implements. `investigation.md`/`plan.md`/`test_plan.md` all present.
- `TCK-20260721-AGENTS-DIR-DISPOSITION` (`docs/ai/agents_dir_disposition.md`) — classifies
  `.agents/` paths, settles `.claude/` as the one approved active location; directly relevant to
  `roles/*.yaml`'s eventual Claude-adapter mapping.
- `TCK-20260721-CODEX-CAPABILITY-MATRIX` (`docs/ai/codex_capability_matrix.md`) — Codex hook/skill
  surface verification; relevant background for `hook-events.yaml` but not load-bearing for this
  ticket's own deliverables (no Codex adapter code here).
- `TCK-20260721-MONITORING-WRITER-DECISION` (`docs/ai/monitoring_writer_decision.md`) — decides the
  `execution_id`/`run_id`/`ticket_id` field model this ticket's `monitoring-schema.yaml` must carry
  verbatim (already excerpted in the ADR, see Mechanics/Engine Constraints above).
- `TCK-20260721-CODEX-REPLAY-PROOF` (`stored_artifacts/TCK-20260721-CODEX-REPLAY-PROOF/`,
  `tools/agent_replay/`, `tests/agent_replay/`) — the closest prior-art precedent in this repo for
  "deterministic, network-free, containment-guarded tooling around this same workflow's
  vocabulary": `fixture_envelope.py`'s error-type pattern and
  `test_runner_no_forbidden_calls.py`'s AST-scan pattern are both directly reusable templates for
  this ticket's validator and its write-guard/no-network tests.

The one directly downstream sibling ticket, `TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE`
(`tickets/todos/provider-agnostic-implementation/`), is still open and has an explicit hard
predecessor dependency on this ticket landing first (its own Scope: "Entry criterion:
`TCK-20260721-ORCHESTRATION-CONTRACT-CORE` must have landed"). Its AC #3 is the concrete
downstream consumer of `skills.yaml` and constrains this ticket's `skills.yaml` shape (must have
traceable, stable per-skill identifiers).

No prior ticket has created `agent-orchestration/`, a contract validator/generator, or any
`roles/*.yaml`/`skills.yaml`/`monitoring-schema.yaml`/`hook-events.yaml` content — this is
genuinely new modeling work with no existing structured source to lift phase-tier applicability,
role obligations, or skill catalog entries from (matching the ticket's own Assumptions/Open
Questions).

## Risks and Open Questions

1. **Versioning scheme is genuinely undecided** (ADR: Proposed-pending-implementation-evidence;
   ticket's own Assumptions/Open Questions line 86). No source doc recommends semver vs. simple
   integer generation. This must be decided and documented in the Plan phase per AC #8 — flagging
   here per this role's instruction not to assume an answer for the investigator; the Plan phase
   owns the decision.
2. **`skills.yaml`'s exact schema is thin** — neither the ADR nor `implementation_plan.md` specifies
   field names beyond "catalog"/"mappings". The Plan phase needs to define a minimal shape (likely:
   one entry per `.claude/skills/*/SKILL.md` directory, with a stable id, a description, and which
   workflow/role(s) it's associated with) that (a) satisfies this ticket's own AC ("lists the
   semantic skill catalog for the first vertical slice") and (b) gives
   `TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE` traceable fields to generate from, per that
   ticket's AC #3. Not fully specified by any upstream doc — Plan-phase decision required.
3. **`roles/` vs `agents/` naming**: resolved in favor of `roles/*.yaml` by the ticket's own AC text
   (matching `implementation_plan.md`, not the ADR's literal quote of the older source-plan doc) —
   noted above, not blocking, but worth the Plan phase explicitly stating which doc it is following
   so a future reader isn't confused by the ADR's own inconsistent internal quote.
4. **Phase-tier applicability matrix is new modeling work**: `vocabulary.py` has no tier-conditional
   data (flat phase set for both hotfix and standard). `workflows/implement-ticket.yaml` needs a
   per-phase tier-applicability field (e.g. `tiers: [standard]` vs. `tiers: [standard, hotfix]`)
   derived from `implement-ticket.js`'s actual branch structure (documented above under Current
   Behavior), not something the bootstrap-equality test alone can verify — the equality test can
   only check the *phase name set* matches `vocabulary.py`, not the tier-applicability structure
   layered on top (`vocabulary.py` doesn't have that structure to compare against).
5. **"Zero network calls" test has no existing precedent to copy verbatim.** No `socket`/`urllib`/
   `requests` guard test exists anywhere in this repo today (searched). The Plan phase must design
   this test from scratch — likely an AST scan analogous to
   `test_runner_no_forbidden_calls.py` (forbidding `import socket`/`urllib`/`http.client`/
   `requests` and their dotted-call forms), rather than a runtime monkeypatch approach, to stay
   consistent with this ticket's own "deterministic" requirement (a monkeypatch-based test only
   proves no network call happened on the *paths actually exercised* by that one test run, not
   structurally).
6. **`finalizer` has no `.claude/agents/finalizer.md` file** — if `roles/*.yaml` is meant to mirror
   `.claude/agents/*.md` 1:1, `finalizer` needs either a documented exception (inline-prompted role,
   not a separate subagent file) or the Plan phase must decide whether `roles/*.yaml` still gets a
   `finalizer.yaml` entry despite no file to point at. `implement-ticket-orchestrator` should almost
   certainly NOT get a `roles/*.yaml` entry (it's a pseudo-agent label, not a role) — flagging so
   the Plan phase makes this exclusion explicit rather than accidentally including it via a naive
   "one file per WORKFLOW_AGENTS entry" loop.

None of these block starting the Plan phase — they are exactly the kind of decisions the ticket's
own Scope/AC text explicitly defers to Plan ("this ticket's Plan phase must decide", "documented
and tested versioning scheme...before any provider adapter consumes it").

## Anti-Drift Hazards

- **Do not modify `tools/agent-monitoring/vocabulary.py`, `.claude/workflows/implement-ticket.js`,
  or any other live Claude/Codex production file.** This ticket only reads them as bootstrap/
  reference sources (explicit Out of Scope line, explicit CRITICAL CONTAINMENT CONSTRAINT). A
  tempting shortcut — "just add a `from vocabulary import WORKFLOW_PHASES` re-export at the top of
  the new validator" — must not touch `vocabulary.py`'s own file even to add a comment.
- **Do not flip the generation direction.** The ticket explicitly forbids making `vocabulary.py`
  generated-from-`contract.yaml` in this ticket (that's stated as later follow-on work once
  provider adapters exist) — the bootstrap direction is one-time and one-way (`vocabulary.py` →
  `contract.yaml`, verified once, never made a live two-way sync).
- **Do not silently drop the "bootstrap is one-time, not permanent" framing when writing the
  equality test.** The test/docstring must say this is a one-time correctness check while Claude's
  workflow remains live and `vocabulary.py` remains legacy source of truth — not "these two must
  always stay equal forever," which would re-introduce the exact reversed-ownership bug the
  ticket's Codex-review correction #1 fixed.
- **Do not let `roles/*.yaml` silently include `implement-ticket-orchestrator`** as if it were a
  regular subagent role — it's the orchestrator's own pseudo-agent label for one specific event
  (Test-phase cleanup failure), not a delegated role with its own obligations/gates.
- **Do not let the generator's write-guard default to "write anywhere."** AC requires zero writes
  outside `agent-orchestration/` unless an explicit generation flag is passed — the natural
  implementation shortcut (a generic `--output-dir` CLI flag with no default restriction) would
  violate this; the guard needs to be structural (e.g. refuse any output path outside
  `agent-orchestration/` unless the flag is present), not merely documented in a docstring.
- **Do not let `skills.yaml` duplicate role obligations.** Skills (`.claude/skills/*/SKILL.md`,
  e.g. `implement-ticket`, `create-tickets`, `architecture`) are a different vocabulary axis than
  roles (`ticket-scoper`, `investigator`, etc.) — conflating the two into one file/schema would
  make the later Codex `.agents/skills/` generation ticket's traceability requirement (AC #3 of
  `TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE`) ambiguous about which contract file to trace to.
- **Do not scope-creep into building the Claude conformance/diff tooling** or Codex adapter/hook
  work — both are explicitly out of scope, owned by other named tickets.
