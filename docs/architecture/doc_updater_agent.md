---
status: active
layer: architecture
authority: P1
audience: developer
---

# Document-Update Agent and Phase

## Status
Accepted — implemented across TCK-20260803-DOC-UPDATER-CORE-WIRING, -VOCAB-REGISTRATION, and
-DASHBOARD-PALETTE (all DONE). `.claude/agents/doc-updater.md` and the Document-Update phase are
live in `.claude/workflows/implement-ticket.js` for every tier including hotfix.

## Context

`implement-ticket.js` already enforces documentation staleness through three layers:

1. **Investigate** (standard/epic tier) produces a mandatory `## Docs Requiring Update`
   section in `investigation.md`, in a strict machine-parseable bullet format
   (`tools/gate_checks/done_checker_static.py::_parse_docs_to_update`).
2. **Implement** (orchestrator-run, immediately after the agent returns) runs
   `tools/gate_checks/doc_staleness_check.py`: a hard block (`DOC_STALENESS_BLOCKED`) if a
   behavior-changing `src/`/`config/`/`.claude/workflows/*.js` diff has zero `docs/` path in
   `files_changed`, plus a non-blocking `ADVISORY` if a specifically-flagged doc wasn't touched.
3. **Verify** independently re-derives ground truth via
   `check_docs_to_update_coverage` — reads `investigation.md`'s flagged list and real `git
   status`, ignoring the Implement agent's self-reported `files_changed`/`behavior_changed`
   entirely. This is the actual backstop: it caught two real gate failures in the session that
   motivated this design (an unchecked-but-satisfied Acceptance Criteria list, and an
   unparseable `## Docs Requiring Update` section with trailing prose). Later extended by
   `TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED` (after this design shipped,
   independent of it) to recognize a third bullet case: a Format 1 bullet whose requirement
   depended on an implementation-time choice, then genuinely resolved as not-applicable and
   marked with a recognized phrase in its own body ("Resolved during implementation, condition
   not met") — such a bullet PASSes without its doc being touched, while sibling unconditional
   bullets in the same section still hard-fail if untouched. See `docs/ai/ticket-lifecycle.md`'s
   "Two distinct formats" subsection for the full contract.

What's missing is not enforcement — it's *execution quality*. Doc edits are currently made by
the generalist `implementer` agent (`.claude/agents/implementer.md`), which has zero doc-specific
rules of its own; the "what" flows indirectly through `investigation.md` → `plan.md`'s ordered
steps → whatever the same agent that's also writing code does with it. There is no agent that
specializes in *how* to write a Mechanics Bible update versus a `docs/guides/` table row versus a
`docs/guidelines/intentional_divergences.md` entry, the way `parity-updater`
(`.claude/agents/parity-updater.md`) specializes in `docs/parity_ledger/*.yaml` specifically.

A companion investigation (`TCK-20260803-DOCS-STRUCTURE-AUDIT`, done) was run as a prerequisite
to verify the real, current structure of `docs/` before writing per-family rules — confirming all
26 top-level subfolders are real and populated, `_SKIP_DOC_SUBDIRS` is accurate, and surfacing
`docs/audits/` as a load-bearing 20-dimension audit programme (D01-D20; `audit_dimensions.md`'s
own index text still says "18," last updated before D19/D20 were added — itself an instance of
the exact staleness this document warns about) whose findings are dated snapshots,
not always-current truth (at least one finding — `authoritative_pipeline.md`'s stale phase-count
claim — has already been fixed by unrelated work since it was recorded).

## Decision

Add a new subagent, `.claude/agents/doc-updater.md`, and a new pipeline phase,
**Document-Update**, inserted between Implement's `agent()` call and the existing
`doc_staleness_check.py` bash() call (`implement-ticket.js` lines 773-835) — not after that
gate, which is where "between Implement and Architecture-Verify" would otherwise default to:

```
Implement (agent call, code only)
  → Document-Update (new phase: doc-updater agent call)
  → doc_staleness_check.py (existing gate, UNCHANGED logic, now evaluates
     implementation.files_changed + docUpdate.files_changed combined)
  → Architecture-Verify → Test → Parity → Security-Review → Verify → Finalize
```

This ordering is load-bearing, not cosmetic: `doc_staleness_check.py` already runs at this exact
seam today, immediately after Implement returns, and hard-blocks the workflow
(`DOC_STALENESS_BLOCKED`) using `implementation.files_changed` if a behavior-changing diff has no
`docs/` path in it. If Document-Update ran *after* that check instead, every ticket whose only
`docs/` change comes from doc-updater (not from Implement's own diff) would be
`DOC_STALENESS_BLOCKED` before doc-updater ever got a chance to run — a regression versus today's
world, where the doc edit is inline in Implement's own diff and the existing check already sees
it. The fix is structural, not a new check: the orchestrator merges doc-updater's own
`files_changed` into the list `doc_staleness_check.py` evaluates, before that call runs. The
check's own internal logic (`check_doc_staleness()` in `tools/gate_checks/doc_staleness_check.py`)
does not change at all.

Runs for every tier, including hotfix.

### Scope boundary

Five rows, not a simple two-way or three-way split — doc-updater does not overlap any of the
other four, and three subfolders are out-of-scope-for-everyone by design (not "owned," just
excluded — matching `tools/generate_registry.py`'s own `_SKIP_DOC_SUBDIRS` set):

| Owner / status | Scope |
|---|---|
| **doc-updater** (new) | `docs/` minus the four rows below |
| **parity-updater** (existing, unchanged) | `docs/parity_ledger/*.yaml` — still runs in its own Parity phase after Test |
| **finalizer** (existing, unchanged) | The ticket file, `tickets/working_log.csv`, `docs/REGISTRY.yaml` regeneration, `make knowledge-index-update` — still in Finalize |
| **Out of scope for everyone** | `docs/archive/`, `docs/scenarios/`, `docs/entity/` — not live prose (matches `_SKIP_DOC_SUBDIRS`), no agent in this pipeline edits them |
| **Cite-only, never edited** | `docs/audits/` — see How table below; distinct from the four rows above because it *is* live prose, just not one this pipeline mutates |

`planner`/`plan.md` are unchanged — `plan.md` stays one ordered step list. doc-updater works
from `investigation.md`'s flagged list and the real code diff, not a re-labeled plan.md.

### Data flow — what, how, why

**What** — computed by the orchestrator before spawning doc-updater (mirrors
`parity-updater`'s existing `expected_subsystems_for_files()` precedent), never by the agent
itself:

- **Standard/epic tier**: parse `investigation.md`'s `## Docs Requiring Update` bullets — already
  machine-parseable via the same format `check_docs_to_update_coverage` enforces. Each bullet is
  a `(path, reason)` pair; the reason text is the "why."
- **Hotfix tier**: no `investigation.md` exists. The orchestrator instead passes the ticket's own
  `## Scope` text plus `implementation.files_changed` (the real diff). doc-updater's job then
  includes a lighter-weight judgment: does this diff plausibly need a `docs/` update, and if so
  where — mirroring how hotfix already substitutes "read the ticket directly" elsewhere in the
  pipeline.

**How** — static per-family rules baked into `.claude/agents/doc-updater.md`, in the same table
shape `parity-updater.md`'s "Parity Ledger Files" section already uses (`File | Subsystem`) —
not its "Entry Schema" section, which is a YAML field-shape block, not a table:

| Family | Rule |
|---|---|
| `docs/mechanics/` | Bit-identical parity with source, Certified Level 1 — cite chapter + section. |
| `docs/engine/` | Cite the specific contract ID (`docs/engine/project_lawbook_m10.md` is the index). |
| `docs/guides/*.md` | Match the file's existing terse per-row table convention exactly. |
| `docs/guidelines/intentional_divergences.md` | Rationale class + description + `Verification:` test path, all three required. |
| `docs/plans/` | Update in place if the plan is still live; never move to `docs/plans/archive/` — that is a separate, whole-epic human decision, not a per-ticket action. |
| `docs/audits/` | Never edited as part of a ticket's own doc-update work — these are dated point-in-time survey snapshots (20 dimensions, each independently `state`/`impact`/`interest`-scored), not living reference docs. May be *cited* as context, but any staleness claim from an audit finding must be independently re-verified before being trusted (confirmed stale-itself in this design's own review — see Context). Updating `docs/audits/` content is the audit programme's own separate re-run process. |
| Everything else (the 17 general folders confirmed real by the structure audit — `agent-monitoring`, `ai`, `architecture`, `cognition`, `combat`, `compliance`, `content`, `core`, `guidelines`, `observability`, `performance`, `simulation`, `simulation_quality`, `strategy`, `systems`, `testing`, `world`) | Read the target doc's own frontmatter plus 2-3 sibling docs before editing; match existing structure rather than inventing one. Any doc with `status: authoritative` gets full Mechanics-Bible-level rigor regardless of folder. |

**Why** always travels with the what — the reason text from Investigate's bullet (standard/epic)
or doc-updater's own stated judgment against ticket Scope (hotfix). The agent's output echoes
this back per doc touched, so `agent-monitoring/data/YYYY-Www/events.jsonl`'s summary is self-explanatory
without re-reading `investigation.md`.

**Output contract** (mirrors `parity-updater.md`'s Output section): one-sentence summary
(≤200 chars) for the monitoring event; `docs_updated` (list of `{path, reason, what_changed}`);
`docs_skipped` (any flagged path the agent judged didn't actually need touching, with
justification — allowed and expected, not a failure); `verified_by`.

### Error handling

The Verify-time gate (`check_docs_to_update_coverage`) stays **fully decoupled** from
doc-updater's own output — it continues re-deriving ground truth from `investigation.md`/the
ticket's own `## Files Changed`/`## Related Docs` body-section text plus real `git status` only,
never from doc-updater's own `docs_updated` self-report. This preserves the "never trust the
self-report" principle that caught two real gate failures in the session motivating this design.
As of TCK-20260904-DOC-COVERAGE-REVERSE-CHECK, the same function additionally checks the reverse
direction (a `docs/` path git shows touched that never made it into the ticket's own Files
Changed/Related Docs text) — a coupling between the ticket's own body text and real `git status`
now exists that did not before, though it still excludes doc-updater's self-report specifically,
exactly as the forward direction always has.

Two phase-local cases, **standard/epic tier**:

1. **doc-updater judges a flagged doc doesn't actually need touching** — goes in `docs_skipped`
   with justification, phase reports `ok`. If the judgment is wrong, Verify's existing
   independent gate catches it exactly as it does today; the ticket blocks at `DOD_BLOCKED`, same
   recovery path as any other Verify failure.
2. **doc-updater fails outright** (can't resolve how to update a flagged doc, or hits genuine
   ambiguity) — reports the blocker in its structured output, mirroring `parity-updater`'s
   pattern. No new blocking gate status is introduced for this phase; the pipeline continues to
   Architecture-Verify/Test, and Verify's existing gate is what actually stops the ticket if a
   doc genuinely never got updated.

**Hotfix tier's backstop is now split, not fully absent.** `check_docs_to_update_coverage`'s
*forward* half still returns no usable signal for hotfix tier (no `investigation.md` exists to
check against — genuinely unchanged by TCK-20260904-DOC-COVERAGE-REVERSE-CHECK). It means case 1
above still has no safety net on hotfix tickets for the omission class: if doc-updater misjudges
that a hotfix's docs don't need updating at all, and so never touches them, git then shows nothing
touched — nothing in the pipeline catches that. This slice of the gap is accepted and pre-existing
(the same gap exists today for the generalist implementer's own hotfix-tier doc edits), not made
worse by adding doc-updater. However, the function's *reverse* half now runs unconditionally,
hotfix included: if doc-updater (or the generalist implementer) does touch a `docs/` file during a
hotfix ticket but that touch never lands in the ticket's own Files Changed/Related Docs text, the
reverse check catches that specific failure mode tier-agnostically. The narrower
touched-but-undeclared case is closed on hotfix tier; the broader never-touched-at-all omission
case remains an open, accepted gap. Any future ticket that wants a hotfix-tier backstop for the
omission case is a separately-scoped decision, not implied here.

## Rationale

- **Specialization over generalism**: `parity-updater` already proves narrow, single-purpose
  post-Implement agents with static rules + orchestrator-injected dynamic context work well in
  this pipeline. doc-updater is the same pattern applied to the one doc family that currently has
  no specialist.
- **No new blocking logic, only a corrected input**: the existing three-layer enforcement
  (Investigate's mandatory section, Implement-time `doc_staleness_check.py`, Verify's independent
  re-derivation) already works — confirmed twice in the session motivating this design.
  doc-updater improves who executes the work the gates already require. The one wiring change
  (merging doc-updater's `files_changed` into what `doc_staleness_check.py` evaluates) keeps that
  gate's own pass/fail logic byte-for-byte unchanged — it only fixes what input reaches it, since
  the input's shape changes once doc edits move to a separate agent call.
- **Audit-content caution earned, not assumed**: `docs/audits/` was nearly treated as a normal
  editable doc family before its own D17 finding was checked against current code and found
  already-fixed. Encoding "audits are dated snapshots, verify before trusting" as an explicit
  rule prevents a future doc-updater run from citing stale audit findings as current fact.

## Trade-offs

- **One more phase, one more agent call per ticket** (every tier, including hotfix) — added
  latency and token cost on every run, in exchange for consistent doc-family-specific execution
  quality. Accepted: doc-editing work already happens today inside Implement; this moves it to a
  dedicated call rather than adding new work.
- **`docs/audits/` exclusion means doc-updater cannot self-heal a stale audit finding it notices**
  — a ticket that happens to fix something D17 flagged does not also get to update D17's own
  entry. Accepted: that is the audit programme's own re-run responsibility, and conflating the
  two would let ticket-scoped doc-updater calls silently drift the audit's dated-snapshot
  semantics into "always current," reintroducing the exact trap this design avoided.

## Consequences

- `.claude/agents/doc-updater.md` (new file) and one new phase block in
  `.claude/workflows/implement-ticket.js`, following the existing `parity-updater`
  call-site/event-push/monitoring pattern.
- `investigation.md`'s `## Docs Requiring Update` format and `check_docs_to_update_coverage` are
  unchanged **by this design** — doc-updater is a new consumer of an existing contract, not a new
  producer. (The contract itself was later extended, independent of this ADR, by
  `TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED` to recognize a resolved-
  conditional bullet marker — see Context above. That extension does not change doc-updater's
  consumer-only relationship to the contract.)
- No change to `parity-updater`, `finalizer`, `planner`, or `plan.md`'s shape.
- **Monitoring/retro/dashboard registration — five concrete, hand-maintained touch points, none
  automatic.** Confirmed by reading the actual registration mechanisms, not assumed:
  1. `tools/agent-monitoring/vocabulary.py`'s `WORKFLOW_PHASES["implement-ticket"]` gains
     `"Document-Update"`; `WORKFLOW_AGENTS["implement-ticket"]` gains `"doc-updater"`. This is the
     single source of truth `record_events.py`'s write-time warn-only check,
     `generate_retro.py`'s phase/agent normalization, and `validate.py`'s drift report all import
     from — skipping this step means every real Document-Update event gets flagged as vocabulary
     drift in the retro report and dashboard drift view, even though the phase is legitimate.
  2. `registries/glossary_registry.jsonl` gains one new `category: "phase"` entry for
     `"Document-Update"` (one line, matching the existing 11 `implement-ticket` phase entries'
     shape) — this is what the dashboard's tooltip glossary reads for phase descriptions.
     `doc-updater`'s own agent-role tooltip needs **no separate registration**: the dashboard's
     `_load_agent_role_descriptions()` (`src/api/agent_ops_dashboard/ingest.py:422`) reads every
     `.claude/agents/*.md` file's own `description:` frontmatter directly at request time, so
     `doc-updater.md`'s frontmatter is the only place that description needs to be written.
  3. `dashboard-frontend/src/lib/phasePalette.ts` gains `'Document-Update'` to the `WorkflowPhase`
     union, a `PHASE_FAMILY` entry (the `'build'` family, alongside `Implement`/`'Sync Docs'`, is
     the natural fit — same pipeline stage), and a `PHASE_PALETTE` hex value stepped within that
     family's existing OKLCH-lightness band, re-validated via the dataviz skill's
     `validate_palette.js` the same three ways this file's own header comment documents. This file
     has **no automated cross-language sync guard** with `vocabulary.py` — it must be hand-updated
     in the same PR, and its own completeness test (`dashboard-frontend/src/test/phasePalette.test.ts`'s "exports a
     key set exactly equal to the 21 distinct WORKFLOW_PHASES strings" assertion) must be updated
     from 21 to 22 or it fails immediately, by design, as the sync-drift alarm.
  4. `tests/tools/test_validate_agent_monitoring.py::test_canonical_vocabulary_single_sourced`
     (and any sibling test asserting a fixed phase/agent count against `vocabulary.py`) must be
     re-run and, if count-based, updated — confirms the new phase/agent didn't silently duplicate
     or diverge from an existing entry.
  5. No change needed to `docs/agent-monitoring/schema.md`'s prose tables — `vocabulary.py`'s own
     module docstring already documents that those tables were found stale once before and are
     not treated as a source of truth by any tooling; this design does not reverse that.
  
  All five are explicit implementation-plan steps for whoever builds this, not optional polish —
  omitting any one of them means Document-Update runs and writes real events, but those events
  render as unrecognized/drift in the retro report, the dashboard's Gantt/timeline view, and the
  drift-detection view, rather than as a normal, understood phase.
- Follow-up (not part of this design): `.claude/agents/implementer.md`'s Source Directory
  Reference table still lists `src/data/`, which no longer exists on disk. Noted during the
  prerequisite structure audit, not in scope here. (A companion claim raised during the same
  audit — that `src/logging/` has no `docs/` coverage — did not survive spec review: it has real
  production callers, `docs/observability/loki_label_policy.md:35` already cites
  `JsonFormatter` directly, and there is no actual gap. Fully retracted, not a follow-up
  candidate.)

## Revisit Trigger

If a future ticket wants to promote doc-updater's `docs_skipped` judgments into a second
Verify-time cross-reference (rejected in this design to keep the gate simple and independent),
or if `docs/audits/` gains its own re-run automation that could safely feed doc-updater instead
of being excluded, revisit this document's Scope boundary and Error handling sections.
