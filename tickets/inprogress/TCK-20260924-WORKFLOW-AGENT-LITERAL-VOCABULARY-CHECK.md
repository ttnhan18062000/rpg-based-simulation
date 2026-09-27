---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260924-WORKFLOW-AGENT-LITERAL-VOCABULARY-CHECK
phase: open
date: 2026-09-24
tags: [agent-monitoring, workflows, data-quality]
---

# TCK-20260924-WORKFLOW-AGENT-LITERAL-VOCABULARY-CHECK

## Title
Static check that every agent **and phase** literal in `.claude/workflows/*.js` is registered in
`vocabulary.py`, catching the gap at authoring time instead of after the corpus has already drifted —
and registering the 29 literals that are already unregistered today

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
`tools/agent-monitoring/vocabulary.py` holds two per-workflow allowlists — `WORKFLOW_AGENTS` (agent
literals, consumed by `is_known_agent()`) and `WORKFLOW_PHASES` (phase literals, with **no equivalent
accessor function**, only raw set membership). `tools/gate_checks/monitoring_anomaly_validator.py` uses
the agent side to flag non-canonical agent literals in the corpus, ratcheted against
`AGENT_DRIFT_CEILING = 162`.

That check is **downstream**: an unregistered literal is only noticed once it has been emitted into
`events.jsonl` enough times to push the count over the ceiling — at which point it surfaces as someone
else's CI failure, on someone else's PR, attributed to drift rather than to the workflow edit that
introduced it. This exact sequence already happened: the shadow-reviewer default-on flip
(`TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON`) turned two literals from occasional to
every-ticket volume, pushed the corpus count over the ceiling, and needed a follow-up ticket
(`TCK-20260923-SHADOW-REVIEWER-VOCABULARY-GAP`) to register them after the fact.

The literals are statically present in the source. Checking them there is cheap and catches the gap
before any corpus row exists.

That check is also **agent-only**: nothing anywhere validates phase literals at all.

**Measured 2026-09-24 at `cb3a7ccb0`, comment lines excluded. Reproduction: `vocab3.py` (archived
with this ticket's staging artifacts). 29 unregistered literals — 6 agent, 23 phase.**

> **Denominator warning — an earlier pass of this ticket got this wrong and the wrong number nearly
> became an acceptance criterion.** `writeSidecar(seq, phase, agent)` carries **two** literals per
> call: a phase in argument 2 and an agent in argument 3. A scan that reads only one argument position
> silently answers a different question — a naive pass reading the wrong position reported **1**
> finding where the true agent-literal count is **6**. Count the two positions separately, against
> their two separate registries. Do not reintroduce a combined "unique `(workflow, literal)` pair"
> denominator; it conflates the two families.

**The 6 unregistered agent literals** (against `WORKFLOW_AGENTS`):

| workflow | unregistered agent literal |
|---|---|
| `create-tickets` | `comprehend` |
| `implement-epic` | `batch-monitoring-write` |
| `implement-epic` | `discover` |
| `implement-epic` | `epic-close` |
| `implement-epic` | `folder-cleanup` |
| `implement-epic` | `tracking-doc-update` |

**The 23 unregistered phase literals** (against `WORKFLOW_PHASES`), spanning 8 workflows:

| workflow | unregistered phase literals |
|---|---|
| `compact-simulation-result` | `Archive`, `Compact`, `Scan` |
| `generate-simulation-setup` | `Draft`, `Scan`, `Validate` |
| `implement-epic` | `Discover`, `Report` |
| `investigate-simulation-result` | `Analyze`, `Load`, `Report` |
| `prepare-simulation-execution` | `Estimate`, `Generate`, `Resolve` |
| `propose-simulation-enhancements` | `Hypothesize`, `Propose`, `Read` |
| `register-simulation-result` | `Index`, `Score`, `Validate` |
| `update-knowledge-store` | `Commit`, `Synthesize`, `Verify` |

**The structural finding underneath both tables: there are 11 `.claude/workflows/*.js` files, and
`vocabulary.py` keys only 4 of them** (`implement-ticket`, `create-tickets`, `implement-epic`,
`simq-audit`) in either registry. **7 are unkeyed in both.** Those 7 contribute 21 of the 23 phase
literals; only `implement-epic`'s `Discover` and `Report` come from an already-keyed workflow.

Two consequences worth stating plainly:

1. **The 7 unkeyed workflows contain zero agent literals** — they are `phase()`-only, with no
   subagent dispatch and no `writeSidecar` calls. So an agent-literal-only check lost nothing by
   skipping them *today*. The widening to phase literals is what makes them visible at all; it is not
   a bug fix for a check that was mis-measuring.
2. **A check that inherits `infer_workflow`'s "unknown workflow → skip silently" contract would
   silently ignore 7 of 11 workflow files** — precisely the dormant blindness this ticket exists to
   prevent. Hence acceptance criterion 1 below.

So this is not a speculative guard: the gap is live right now across 8 workflows. Note that
`comprehend` is one of the four `writeSidecar` call sites that `docs/agent-monitoring/schema.md`
already documents by name, which makes its absence from the registry a pure bookkeeping gap rather
than a real anomaly.

## Scope
1. **A static check under `tools/gate_checks/`**, alongside the existing 23 scripts and following their
   shared `MARKER:`-prefixed JSON CLI contract.
2. **Two literal families, in `.claude/workflows/*.js` only, each against its own registry:**
   - **Agent literals** → `WORKFLOW_AGENTS`, resolved via `is_known_agent()`:
     - `agent: '<literal>'`
     - `writeSidecar(<seq>, '<phase>', '<agent>')` — the **third** positional argument
   - **Phase literals** → `WORKFLOW_PHASES`, by set membership (no accessor exists; see Implementation
     Notes before adding one):
     - `phase('<literal>')`
     - `pushEvent('<literal>', ...)` — the first positional argument
     - `writeSidecar(<seq>, '<phase>', '<agent>')` — the **second** positional argument
3. **Every workflow file must be keyed.** A `.claude/workflows/*.js` file absent from both registries is
   a **loud failure**, not a silent skip — see acceptance criterion 1. This is the inverse of
   `infer_workflow`'s run_id-keyed contract and must not be implemented by delegating to it.
4. **Per-workflow resolution.** A literal is checked against the set for *its own* workflow, keyed by
   file name (`implement-epic.js` → `implement-epic`, and so on for all 11). A literal registered under
   a different workflow is still a finding.
5. **Honour `WORKFLOW_AGENT_PREFIXES`.** Use `is_known_agent()` rather than testing set membership
   directly, so the `create-tickets` `investigate:` prefix family resolves correctly and the check does
   not reimplement resolution logic that already exists.
6. **Ignore comments.** Measured 2026-09-24 across `.claude/workflows/*.js`: **21 comment-line
   mentions of `writeSidecar` against 22 real `await writeSidecar(` call sites** — very nearly 1:1.
   These files document their own instrumentation heavily, so a check that counts comment text would
   roughly double its findings with false ones. (`agent: '` currently appears on zero comment lines,
   but must be filtered on the same basis rather than relying on that.)
7. **Register all 29 literals in `vocabulary.py`**, additively, so the check reports **zero** findings
   at this ticket's close. This includes **keying the 7 currently-unkeyed workflows** in
   `WORKFLOW_PHASES`. Each addition carries a short comment saying why the literal is real, matching the
   standard every existing entry in that file already meets — `claude` and `orchestrator` are the
   precedent: both were registered after corpus investigation showed a long-running, self-describing
   convention rather than drift, and their inline comments document exactly that reasoning.

## Out of Scope
- **This is not a general dormant-path or unregistered-literal gate.** It checks five specific literal
  call-site shapes in one directory (`.claude/workflows/*.js`) against two registries in one module, and
  nothing else. A broader gate over monitoring data would be disproportionate: agent-monitoring data is
  a side effect of how work happens, not a simulation feature, and strict blocking gates over it are
  explicitly not wanted ([[feedback_agent_tooling_checks_proportionate]]).
- **Other literal families.** Tier literals against `CANONICAL_TIERS`, agent names in
  `.claude/agents/*.md`, and any literal outside `.claude/workflows/*.js` are all out. If any of them
  turns out to have the same gap, that is a separate ticket with its own evidence.
- **Changing `AGENT_DRIFT_CEILING` or touching `monitoring_anomaly_validator.py`.** The downstream
  ratchet stays as it is; this is an independent upstream check. Registering the 6 agent literals must
  **not** be accompanied by a ceiling adjustment — if registering them changes what the validator
  counts, report that as a finding rather than retuning the ratchet to absorb it.
- **Removing or renaming any existing registry entry.** The `vocabulary.py` change is additive only.
- **Blocking a workflow run, a commit, or CI.** Advisory: print findings, exit zero. Wiring it as a
  blocking gate is excluded.
- **Detecting dynamically constructed agent names.** Only string literals are in scope; a name built at
  runtime is out of reach of a static check and must not be guessed at.

## Acceptance Criteria
1. **A workflow file keyed in neither registry is a loud, named failure — never a silent skip.** Asserted
   by a fixture adding an unkeyed `.js` file and confirming the check names it. This is the most
   important criterion: 7 of 11 real workflow files were unkeyed at `cb3a7ccb0`, so a check that
   inherits `infer_workflow`'s "unknown → skip silently" contract would have ignored most of its own
   target population while reporting success. The check must **not** delegate this decision to
   `infer_workflow`.
2. **Before the registry change**, the check reports exactly the 29 literals tabulated in Request
   Summary — 6 agent, 23 phase — when run against `.claude/workflows/*.js`. The two families are
   counted and reported separately, never merged into one combined denominator.
3. **After the registry change**, the check reports **zero** findings, and all 11 workflow files are
   keyed in `WORKFLOW_PHASES`. A test asserts the zero, so any future finding is genuinely new.
4. **A literal appearing only inside a comment produces no finding** — asserted by a fixture containing
   a commented-out `writeSidecar(...)` call, a commented `phase('...')`, and a commented `agent: '...'`.
   This is the check's most likely false-positive source (21 comment mentions against 22 real call
   sites), so it is asserted directly rather than assumed.
5. **Both `writeSidecar` argument positions are read correctly** — argument 2 as a phase, argument 3 as
   an agent — asserted by a fixture whose phase and agent literals are distinguishable, so a check that
   reads the wrong position fails the test rather than silently reporting a plausible wrong number. This
   exact error produced 1 finding instead of 6 during scoping.
6. A literal registered under workflow A but used in workflow B is reported as a finding, for both
   families.
7. A `create-tickets` agent literal matching the `investigate:` prefix family is **not** reported, proven
   by a fixture — agent resolution must go through `is_known_agent()`, not raw set membership.
8. Exit code is zero even with findings. Asserted by a test.
9. `monitoring_anomaly_validator.py` and `AGENT_DRIFT_CEILING` are unmodified. `vocabulary.py` **is**
   modified, additively only: a diff confirms no existing entry was removed or renamed, and every
   addition carries a justifying comment.
10. `pytest tests/tools/` (or the correct scoped directory for `tools/gate_checks/`) passes, with the
    command and result recorded in `## Test Summary`.

## Related Tickets
- `TCK-20260923-SHADOW-REVIEWER-VOCABULARY-GAP` — the after-the-fact registration this check prevents
- `TCK-20260923-SHADOW-REVIEWER-COLLECTION-DEFAULT-ON` — the default-on flip that exposed the gap
- `TCK-20260915-MONITORING-ANOMALY-VALIDATOR` — built the downstream ratchet this complements
- `TCK-20260710-WORKFLOW-META-CONFORMANCE-CHECK` — the closest existing sibling; checks declared
  `meta.phases` against actual run events, a **different** question (run-keyed, needs a real run),
  which is why this check is new rather than an extension
- `TCK-20260924-EPIC-GITHUB-DELIVERY-PROCESS` — scoped in the same review; deliberately unrelated

## Related Docs
- `docs/agent-monitoring/schema.md` — documents the four real `writeSidecar` call sites by name
  (`comprehend`, `structure`, `write-sequence`, `link-epic`), one of which is among the 6 gaps
- `docs/ai/monitoring_writer_decision.md` — the monitoring-write design context

## Related Stored Artifacts
Standard tier — `staging_artifacts/TCK-20260924-WORKFLOW-AGENT-LITERAL-VOCABULARY-CHECK/` with
`plan.md`, `investigation.md` and `test_plan.md`, produced by the pipeline's Investigate/Plan phases and
migrated to `stored_artifacts/` at close.

The scoping-time reconciliation script (`vocab3.py`, which produced the 6 / 23 / 29 figures and the
11-files-4-keyed finding) should be preserved into `investigation.md` — either inlined or committed
alongside it — so the counts in Request Summary are reproducible rather than asserted. It reads both
registries and reports phase and agent literals separately, keyed by workflow.

## Related Code Areas
- `tools/agent-monitoring/vocabulary.py` — 170 lines; `CANONICAL_TIERS` (line 16), `WORKFLOW_PHASES`
  (20), `WORKFLOW_AGENTS` (39), `WORKFLOW_AGENT_PREFIXES` (137), `is_known_agent` (142),
  `infer_workflow` (149). **Modified by this ticket, additively only** — the 29 registrations and the
  7 newly-keyed workflows land here.
- `tools/gate_checks/workflow_meta_conformance.py` — already regex-scans `.claude/workflows/*.js` and
  already imports `infer_workflow`; its scanning approach is the pattern to follow, but note that its
  run-keyed model is exactly what criterion 1 forbids reusing for the keyed-workflow decision
- `tools/gate_checks/monitoring_anomaly_validator.py` — the downstream ratchet. **Read only.**
- `.claude/workflows/` — 11 `.js` files. 4 keyed in `vocabulary.py` at `cb3a7ccb0`
  (`implement-ticket.js`, `implement-epic.js`, `create-tickets.js`, `simq-audit.js`), 7 unkeyed. Only 3
  carry agent literals at all — `simq-audit.js` has neither `writeSidecar` nor `agent:` literals, and
  the 7 unkeyed files are `phase()`-only.

## Assumptions / Open Questions
1. **Whether regex parsing is sufficient, or a JS parser is warranted.** The existing
   `workflow_meta_conformance.py` uses regex against these same files successfully, so regex is the
   precedent. Multi-line `writeSidecar(...)` calls are the real risk here, and more so now that two
   argument positions must be read from the same call — a single-line regex that silently misses a
   wrapped call produces exactly the undercount criterion 5 exists to catch. Confirm whether any
   multi-line calls exist and state the coverage achieved rather than assuming it is total.
2. **Whether all 29 literals are genuinely intentional.** The 6 agent literals are `implement-epic.js`
   orchestrator-side labels plus `create-tickets`'s `comprehend`, closely resembling the
   already-registered orchestrator pseudo-agent family (`orchestrator`, `claude`, `implement-ticket`);
   `comprehend` is additionally documented by name in `schema.md`. The 23 phase literals read as
   ordinary phase names for the simulation-lab workflows. **Registering them is now in scope, so each
   one needs its justifying comment written, not assumed** — if any single literal turns out not to be
   defensible, report it as a finding rather than registering it to reach the zero in criterion 3.
3. Whether the check should be wired into a pipeline phase or stay pytest-only. `workflow_meta_conformance.py`
   does both (advisory in Finalize, plus a pytest-only sibling check). Pytest-only is the smaller,
   more proportionate default; wiring can follow if it proves useful.
4. Whether `simq-audit.js`'s agents (`workflow`, `drift-classifier`, `anchor-updater`, `doc-syncer`) are
   emitted some other way, since that file has neither literal shape. Not this ticket's problem, but
   worth a line in the module docstring so a future reader does not read its absence as a bug.
5. **Whether to add an `is_known_phase()` accessor** mirroring `is_known_agent()`. There is no phase
   accessor today, so the check would otherwise reach into `WORKFLOW_PHASES` directly. Adding one is a
   small, symmetrical improvement, but it is an API addition to a module this ticket is otherwise only
   appending data to — decide explicitly in `plan.md` rather than drifting into it.
6. **The ticket ID says `AGENT-LITERAL` but the scope now covers phase literals too.** The ID is left
   unchanged deliberately: it is referenced from `TCK-20260924-EPIC-GITHUB-DELIVERY-PROCESS` and the
   working log, and renaming it would break those references for a cosmetic gain. The `## Title` carries
   the accurate scope.

## Implementation Notes
**Standard tier.** This was scoped as `hotfix` while it was a report-only check over one literal family.
Widening it to two families plus a 29-entry registry expansion across 8 workflows makes it "a new
feature" under CLAUDE.md's Tier Routing, not "a minimal targeted change with self-evident intent".
Staging artifacts (`plan.md`, `investigation.md`, `test_plan.md`) are therefore required and will be
produced by the pipeline's own Investigate/Plan phases — **do not hand-write them ahead of that.**

The framing that matters is **upstream vs downstream**. `monitoring_anomaly_validator.py` asks "has the
corpus drifted?" and can only answer once drift has accumulated past a ceiling. This check asks "does the
source name a literal the registry does not know?" and can answer the moment the line is written. They
are complements, not duplicates — and the ticket should not be talked into being a replacement for either.

Resist scope creep toward a general literal-registry gate. The value still comes from being narrow enough
to be obviously correct: five call-site shapes, one directory, two registries in one module, advisory
output. The widening to phase literals was taken on evidence (23 live findings, 7 blind workflows), not
on symmetry — and that is the only basis on which it should widen again.

**On registering the 29 — note the tension with Gate Integrity and why this is the allowed side of it.**
The rule is never to edit an artifact to make a check pass instead of fixing the substance. Registering a
literal the workflow genuinely emits *is* the substance: the registry is a record of real vocabulary, and
an unregistered-but-real literal is a registry gap. What would violate the rule is registering a literal
that is *not* defensible in order to reach criterion 3's zero, or moving `AGENT_DRIFT_CEILING` to absorb a
count change. Both are explicitly out of scope. The distinction to hold: justify each literal, then
register it — never register it to clear the report.

The precedent is already in the file. `claude` (45 of ~91 non-standard agent values) and `orchestrator`
(401 occurrences spanning 2026-06 to 2026-09) were both registered after investigation showed a
long-running, self-describing convention rather than drift, each with an inline comment recording that
reasoning. Match that standard, one comment per addition.

## Test Summary
To be completed during implementation.

## Files Changed
To be completed during implementation.

## Completion Summary
Open.
