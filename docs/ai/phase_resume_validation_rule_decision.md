---
status: active
layer: ai
authority: P1
audience: agent
tags: [ai, workflows, agent-monitoring]
---

# Phase-Level Workflow-Resume Validation Rule Decision — TCK-20260907-PHASE-RESUME-VALIDATION-RULE-DESIGN

Resolves **M3** of
`docs/plans/agent_infrastructure/ai_first_hardening_epics/workflow_reliability_epic.md`
(roadmap item 15, Bucket B, Horizon 1), which itself operationalizes §76 of the frozen
`AI_FIRST_ENGINEERING_NEXT_EVOLUTION_PROPOSAL` Rev.3 ("Resume semantics, not just resume
mechanics"):

> A checkpoint is reusable only if `workflow_version` matches, the input the phase consumed is
> unchanged (`input_hash`), and every artifact the phase produced still exists on disk. All three
> must hold, or the workflow restarts from the earliest invalidated phase — never a blind
> "checkpoint exists, so skip."

This document **decides and evidences**. It implements nothing — no phase-level checkpoint
mechanism, no skip-if-done logic, and no new `agent-monitoring/` field is added or written as part
of landing it. Every claim below is either (a) a direct reading of the real, current source of
`.claude/workflows/implement-ticket.js`, `.claude/skills/implement-ticket/SKILL.md`,
`agent-orchestration/workflows/implement-ticket.yaml`, `tools/agent_codex_runtime_shadow/matrix.py`,
or `docs/agent-monitoring/schema.md`, re-checked on 2026-09-07 for this document, or (b) an explicit,
labeled policy choice made in the deliberate absence of an existing mechanism — never an
unattributed assumption about what "probably" already exists.

**This document is exclusively about resuming a stalled/crashed `implement-ticket.js`
ticket-workflow pipeline run** (Scope → Investigate → Plan → Review → Implement → ... → Finalize).
See §2 for the explicit distinction from the simulation engine's own unrelated checkpointing
subsystem, which this document does not model or touch.

---

## 1. Today's baseline: what "resume" actually does (greenfield — no phase-level checkpoint exists)

Direct investigation of `.claude/workflows/implement-ticket.js` confirms exactly one resume
mechanism exists today, and it operates only at the Scope phase:

```js
// Args: { ticket_id?, request?, tier? }
// Pass ticket_id to resume from an existing ticket (skips ticket creation).
```

`.claude/skills/implement-ticket/SKILL.md` documents the same behavior in one line: "Pass
`ticket_id` to resume from an existing in-progress ticket (Scope phase re-loads it and skips
creation)."

Concretely, passing `ticket_id`:

- Makes the Scope phase look the ticket up in `tickets/inprogress/`, `tickets/done/`, or
  `tickets/todos/**/` instead of dispatching `ticket-scoper` to create a new one.
- Computes a monitoring-attribution `seqOffset` (via `tools/agent-monitoring/seq_offset.py`, added
  by `TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION`) so a resumed session's own `events` array
  — which restarts at 0 in the new session — does not collide with the pre-pause session's
  `(run_id, seq)` buckets already written to `tools.jsonl`/`events.jsonl`.

Neither of these is a phase-level checkpoint. A direct grep of `implement-ticket.js` for
`existsSync`, "already exists", or any skip-if-already-done conditional turns up **zero** matches
tied to phase execution (the one `skip` hit in the file, line 1840, concerns the tier-conditional
`Architecture-Verify`/`Security-Review` phases emitting no event at all for hotfix tier or
non-security tickets — an unrelated, tier-driven branch, not a resume/checkpoint mechanism). The
file's phase sequence (`meta.phases`, twelve entries, Scope through Finalize) is unconditionally
linear: every phase after Scope runs its full `agent()` call and gate logic every single time the
workflow is invoked, resumed or not, regardless of whether `investigation.md`, `plan.md`, a prior
`Implement` diff, or any other phase artifact already exists on disk from an earlier, interrupted
invocation of the same `ticket_id`.

**Stated plainly, as the greenfield baseline this design starts from:** today, "resume" means
*ticket-ID re-invocation from Scope*, not phase-level checkpoint restoration. There is no
phase-level checkpoint, no skip-if-already-done logic, and no validation of prior-phase output
validity anywhere in the pipeline today. Any phase-level resume mechanism is new work, not an
extension of an existing partial one.

**Prior art in the same problem space, not the same mechanism.**
`TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION` (done) fixed a `seq`-numbering collision when a
ticket's monitoring run is paused mid-pipeline and resumed later under the same `run_id` — it makes
resumed *monitoring attribution* correct (tool calls get attributed to the right `(run_id, seq)`
bucket instead of colliding with the pre-pause session's rows). It says nothing about whether any
given *phase* should be re-run or skipped; it exists entirely to keep `tools.jsonl`/`events.jsonl`
bookkeeping correct regardless of how many times a ticket is resumed. This document's validation
rule is a different, currently-nonexistent layer sitting logically *above* that mechanism: it would
decide whether to skip a phase at all, before that phase's own (already-solved) seq-attribution
problem is even reached.

---

## 2. Explicit distinction from `src/engine/checkpoint.py`

`graphify query "workflow resume checkpoint validation"` was run directly for this document (BFS
depth=2 from `checkpoint.py`, `CheckpointRequest`, and the checkpoint-file JSON header) and returned
111 nodes, all rooted in `src/engine/checkpoint.py` (`CanonicalStateHasher`, `CanonicalHashScheduler`,
`BudgetedCanonicalHasher`, `HashMode`, `HashScheduleViolation`), `src/engine/scenario_checkpoint.py`
(`ScenarioCheckpointer`), and `src/engine/scenario_runtime.py` (`ScenarioRuntimeService`,
`ScenarioObjectiveState`) — plus their certification harness and API-route consumers
(`src/api/routes/scenarios.py::restore_checkpoint()`).

This is a **completely separate subsystem** from the one this document designs for:
`src/engine/checkpoint.py` checkpoints **simulation-tick state** — a serialized `AuthoritativeState`
snapshot plus RNG state, hashed deterministically (`CanonicalStateHasher`) on a scheduled cadence
(`CanonicalHashScheduler`) so a scenario run can pause/restore across process restarts
(`ScenarioCheckpointer.restore()`), verified bit-identical for certification (`CertificationHarness`).
It has no relationship — architectural, code-level, or conceptual — to resuming a crashed
`implement-ticket.js` **agent-orchestration** pipeline run. The graph traversal confirms zero edges
connecting the two: no node under `src/engine/` or `src/certification/` references
`.claude/workflows/implement-ticket.js`, `agent-monitoring/`, or any ticket-workflow phase name, and
no node discovered in §1's investigation references `src/engine/checkpoint.py` or any of its
classes. This document does not touch, reference as a design template, or conflate with
`src/engine/checkpoint.py`, `CanonicalStateHasher`, `CanonicalHashScheduler`, `BudgetedCanonicalHasher`,
or `ScenarioCheckpointer`.

---

## 3. Evaluating the proposed minimum sufficient validation-field set

The epic's proposed minimum set is: **`workflow_version` matches** + **`input_hash` unchanged** +
**every artifact the phase produced still exists on disk** — with `source_revision`/`phase_version`
added only if this design work finds them materially necessary.

### 3.1 `workflow_version`: real precedent exists, and it can be reused as-is

`agent-orchestration/workflows/implement-ticket.yaml` already carries a top-level
`workflow_version: 2` field. It is not hypothetical or newly proposed — it has exactly one real
consumer today, `tools/agent_codex_runtime_shadow/matrix.py`:

```python
_VERIFIED_AGAINST_WORKFLOW_VERSION = 2
...
def validate_contract_version(matrix: SupportedMatrix) -> None:
    if matrix.workflow_version != _VERIFIED_AGAINST_WORKFLOW_VERSION:
        raise ContractVersionMismatchError(...)
```

`matrix.py`'s own docstring states the semantics precisely: `workflow_version` is deliberately
*decoupled* from any individual fixture/artifact version (`TCK-20260817-STANDARD-CODEX-SHADOW-
CONTRACT-VERSION-FIXTURE-CONFLATION` fixed exactly the bug of conflating the two). It answers "is
THIS PACKAGE's own hardcoded phase/gate contract still what the live orchestrator expects" — i.e.
it is a coarse, whole-workflow-level version number, bumped manually whenever
`implement-ticket.yaml`'s phase list, tier behavior, or gate structure changes in a way that matters
to a downstream consumer of that contract. `docs/architecture/agent_orchestration_contract.md`'s
Versioning decision independently confirms this is the intended shape: `workflow_version` (and its
sibling `hook_schema_version`) is named as the established field-naming convention for "does the
live contract still match what I was built against," not a per-artifact or per-phase-content hash.

**Finding: yes, reuse `workflow_version` as-is — do not fork a distinct field.** The resume
validation rule's `workflow_version` check needs exactly the same semantics `matrix.py` already
uses it for: "was the workflow contract that produced this checkpoint the same contract version
running now." Both are whole-workflow-level staleness checks against the same single source of
truth (`agent-orchestration/workflows/implement-ticket.yaml`'s `workflow_version` field), read the
same way (`yaml.safe_load` + top-level int field), and both are deliberately coarse rather than
per-phase — forking a second field with identical semantics would create two numbers a maintainer
must remember to bump in lockstep for the same underlying event (a phase/gate/tier structural
change to the workflow), which is exactly the kind of duplicated-source-of-truth problem
`matrix.py`'s own contract-version-vs-fixture-version bug (§ above) already demonstrated in this
same file family. A future phase-resume implementation should read `implement-ticket.yaml`'s
`workflow_version` the same way `matrix.py::load_supported_matrix()` does, and compare it against
the value recorded at the time the checkpoint's phase artifacts were produced.

One caveat carried forward, not resolved here: `workflow_version` is coarse by design — it is
bumped only when a maintainer judges the phase/gate/tier *structure* to have materially changed, not
on every edit to `implement-ticket.js`'s prompt text or an individual phase's internal logic. This
means a resume validation rule relying on `workflow_version` alone will not catch every possible
"the phase's own logic quietly changed since the checkpoint was written" case — only the subset a
maintainer already judged worth a version bump. §3.3 addresses whether this gap is closed by
`source_revision`/`phase_version` instead, or is an accepted limitation.

### 3.2 `input_hash`: no existing implementation, but the concept is well-grounded

No tool in this repository computes a phase's "input hash" today — this is confirmed absent, not
merely unexplored: neither `implement-ticket.js`, `record_events.py`, nor any `tools/agent-monitoring/`
script hashes a phase's consumed input (the ticket file content, the prior phase's artifact content,
or the diff a phase reads). This is new work a future implementation ticket would build, not a gap
in existing tooling this document overlooked. It is, however, a well-grounded concept: this repo
already computes content hashes elsewhere for materially the same purpose (staleness detection) —
`tools/retrieval_cache.py`'s cache-key/`source_hash` mechanism (cited in
`docs/ai/shadow_promotion_gate_thresholds_decision.md` §2 criterion 4, "cache correctness: stale
packets are rejected and source-hash checks pass") is the closest existing precedent for "hash an
input, compare it later, treat a mismatch as invalidating a cached artifact." A future
implementation should model `input_hash`'s computation on that precedent (a deterministic hash over
the exact file(s)/content a phase actually reads) rather than inventing a new hashing convention.

### 3.3 Is `source_revision`/`phase_version` materially necessary? Concrete conclusion: no, not as separate fields

Evaluated against real evidence, not assumed either way in advance:

- **`source_revision`** (a git commit/revision the checkpoint was produced against) would answer
  "has the repository's own code changed since this phase ran" — a legitimate concern in general,
  but one this repo's actual invocation model does not need a dedicated field for. `implement-ticket.js`
  runs are single-ticket, single-branch-or-worktree invocations (per CLAUDE.md's Worktree & Branch
  Isolation section); a resumed run of the same `ticket_id` in the same worktree is, by this repo's
  own working convention, expected to run against the same or a fast-forwarded state of the same
  branch, not an unrelated revision. The one case `source_revision` would genuinely catch — a
  long-paused ticket resumed after unrelated commits landed on the same branch, invalidating a
  phase's stale factual assumptions about the codebase — is exactly the case `input_hash` (§3.2)
  already covers for any phase that reads specific files: if a phase's `input_hash` is computed over
  the actual content it consumed (ticket file, prior artifact, relevant source paths), an unrelated
  intervening commit that changed those same paths already invalidates the hash. A `source_revision`
  field would only add value for content a phase *implicitly* depends on without ever reading it
  directly (e.g. "did anything in `src/` change at all," a much coarser signal already available for
  free via `git rev-parse HEAD` without a new typed field). **Conclusion: not materially necessary as
  a distinct validation field** — its one genuine use case is already subsumed by a correctly-scoped
  `input_hash`, and its coarser fallback use case doesn't need a durable field at all, just an
  ad hoc `git` read if a future implementation wants the extra signal.
- **`phase_version`** (a version number for an individual phase's own logic, finer-grained than
  whole-workflow `workflow_version`) would close exactly the gap §3.1's caveat named: a phase's
  internal logic changing without a `workflow_version` bump. Real evidence against inventing this as
  a new field today: no phase in `implement-ticket.js` or `implement-ticket.yaml` carries any
  per-phase version marker today, `docs/architecture/agent_orchestration_contract.md`'s Versioning
  decision explicitly scoped `version`-family fields at the whole-contract level (`contract.yaml`'s
  own `version`, paired with `workflow_version`/`hook_schema_version` — no per-phase variant is
  named anywhere in that decision or its source plan), and `matrix.py`'s own comment explains
  *why* per-artifact/per-fixture versioning was deliberately kept separate from the coarse
  contract-level number (the exact conflation bug `TCK-20260817-STANDARD-CODEX-SHADOW-CONTRACT-
  VERSION-FIXTURE-CONFLATION` fixed). Introducing `phase_version` now, with zero real evidence of a
  phase-logic change slipping past a `workflow_version` bump in practice, would be inventing
  precision this repo's actual versioning conventions do not currently need — the same anti-pattern
  `docs/ai/shadow_promotion_gate_thresholds_decision.md` explicitly avoided (its §6 defers rather
  than invents a proxy where the underlying signal genuinely doesn't exist yet). **Conclusion: not
  materially necessary today.** If a future implementation ticket finds real evidence of
  `workflow_version` failing to catch a phase-logic regression in practice, that evidence — not this
  document's advance speculation — should be what justifies adding `phase_version` then.

**Overall conclusion on the field set: the epic's proposed minimum set is sufficient.**
`workflow_version` (reused as-is from `implement-ticket.yaml`) + `input_hash` (new, modeled on
`retrieval_cache.py`'s existing hash-staleness precedent) + per-phase-artifact-existence (a direct
filesystem check against the artifact paths each phase is already documented to produce — `investigation.md`,
`test_plan.md`, `plan.md`, the `Implement` diff's `files_changed`, etc.) together cover every real
invalidation scenario this investigation surfaced. Neither `source_revision` nor `phase_version`
earns a place in the minimum set; both are either subsumed by a correctly-scoped `input_hash` or
lack any real evidence of a gap `workflow_version` leaves open today.

---

## 4. Grounding in `docs/agent-monitoring/schema.md`'s actually-recorded fields

Per-validation-field assessment of whether the needed data already has a home in the recorded
`runs`/`events`/`tools` JSONL shapes, or would require a new field:

| Validation-rule need | Existing home in `schema.md`? | Finding |
|---|---|---|
| Which phase a prior (possibly crashed) run reached | Yes — `events.jsonl`'s `phase` field, one record per agent call, `status` ∈ `ok`\|`failed`\|`blocked`\|`skipped`. A crashed run is detectable today via `runs.jsonl`'s own `CRASHED` synthetic status (`start_ts` present, no `end_ts`, per `validate.py`), combined with the highest-`seq` `events.jsonl` row for that `run_id` to identify the last phase that actually completed. | Already has a home — no new field needed to determine "how far did the last attempt get." |
| `workflow_version` at the time a phase's artifact was produced | **No.** Neither `runs.jsonl` nor `events.jsonl` records `workflow_version` (or any `implement-ticket.yaml`-derived field) per run or per event today — schema.md's full field tables for both files (reproduced above in this document's investigation) contain no such column. | **Needs a new field.** A future implementation would need to add `workflow_version` (read from `implement-ticket.yaml` at run start, per §3.1) to either the `runs.jsonl` record (one value per whole run) or each phase's `events.jsonl` record (if a long-paused run could span a `workflow_version` bump mid-run, which is possible in principle for a very long pause). |
| `input_hash` per phase | **No.** No hash-of-consumed-input field exists on any `events.jsonl` record. The closest existing precedent, `cited_source_hashes` (an array of source-content hashes), belongs to the wholly separate, additive **retrieval-event field family** (`RETRIEVAL_EVENT_FIELDS`, gated behind `SHADOW_CONTEXT_PACKET_ENABLED`) — it hashes retrieved *context-packet* sources for a shadow-logging purpose, not a phase's actual consumed input for resume-validity purposes, and is emitted only for the advisory shadow-packet call site, not for every real phase. | **Needs a new field**, and it needs to be its own field on the real per-phase `events.jsonl` record (not a reuse of `cited_source_hashes`, whose schema and gating are purpose-built for a different, opt-in advisory mechanism). |
| Per-phase-artifact-existence | **No.** `events.jsonl` records that a phase ran and its outcome `status`, but never enumerates the artifact path(s) it produced (`investigation.md`, `plan.md`, etc.) as a structured field — those paths are implicit, derivable only from the tier-and-phase pairing documented in `SKILL.md`, not recorded per-run. | **Needs no new *recorded* field** — this check does not need a durable record at all; it is a direct filesystem existence check (`staging_artifacts/{ticket_id}/investigation.md` etc.) performed live at resume time against the well-known, tier-determined artifact-path convention already documented in `SKILL.md`. The one thing that *would* benefit from a recorded field is which artifact paths a given phase actually wrote this run (in case a future phase's artifact-producing behavior itself changes) — deferred to the audit-trail requirement in §6, not required for the validation check itself. |

**Summary:** of the three validation-rule inputs, one (`workflow_version`) already exists as a
field, but not yet *recorded per run/event* — that plumbing gap is real and would need a new
`runs.jsonl`/`events.jsonl` field. `input_hash` needs an entirely new field. Per-phase-artifact-
existence needs no new field at all, since it is answerable by a live filesystem check against an
already-documented path convention, not something that needs to be durably recorded to be checked.

---

## 5. The invariant and the fallback behavior

Stated verbatim, per §76 of the frozen proposal, and held as the binding rule for any future
implementation:

> **`checkpoint exists + checkpoint still valid = safe to reuse` — never `checkpoint exists = skip
> phase`.**

**Fallback on validation failure: restart from the earliest invalidated phase**, determined given
the pipeline's real, linear phase ordering (`meta.phases`, §1) as follows: walk the ordered phase
list from Scope forward; for each phase that produced a durable artifact in a prior attempt, apply
the three-part validation rule (§3) to that phase's own checkpoint. The **first** phase (in pipeline
order) whose checkpoint fails validation — `workflow_version` mismatch, `input_hash` mismatch, or a
missing expected artifact — is the earliest invalidated phase; the workflow restarts execution from
that phase, re-running it and every phase after it in the normal linear sequence, exactly as if no
checkpoint existed for any of them. A later phase's checkpoint is never trusted once an earlier
phase's checkpoint has been invalidated, even if the later phase's own three-part check would pass
in isolation — because a later phase's artifact was produced *using* the earlier phase's (now
invalid) output as input, so its own apparent validity cannot be trusted independent of its
upstream dependency. This is a direct consequence of the pipeline's real structure (§1): each phase
after Scope consumes the prior phases' artifacts (Plan consumes Investigate's `investigation.md`;
Implement consumes Plan's `plan.md`; etc.), so invalidating phase *N* transitively invalidates every
downstream phase *N+1, N+2, ...* regardless of their own individual checkpoint state.

---

## 6. Audit-trail requirement for the future implementation ticket

Per §76's own governance-table framing ("Auto-with-audit, gated by the validation rule"), a resume
decision must leave enough behind in `agent-monitoring/` to be inspected after the fact — this
section states that requirement; it does not build it.

A future implementation ticket must ensure that whenever a resumed run makes a checkpoint-reuse
decision (whether it reuses a checkpoint, or invalidates one and restarts from an earlier phase),
that decision is recorded as an inspectable `agent-monitoring/events.jsonl` record, following this
repo's own established convention for collapsed-cause statuses (§ schema.md's `reason_code` design,
`docs/agent-monitoring/schema.md`): a new, closed-vocabulary `reason_code` value (or an equivalent
new field, if `reason_code`'s existing `Scope`/`Verify`-only scope turns out not to fit) —
e.g. distinguishing `checkpoint_reused` from `checkpoint_invalidated_workflow_version` /
`checkpoint_invalidated_input_hash` / `checkpoint_invalidated_missing_artifact` — so a retro reader
can answer "how often did resume actually skip work, and why did it invalidate when it didn't."
This mirrors the same principle `docs/agent-monitoring/schema.md`'s `reason_code` section already
states: "populated wherever a gate status collapses more than one distinct cause into a single
value" — a bare `resumed: true/false` boolean would collapse exactly the three distinct invalidation
causes above into one undifferentiated bucket, repeating the same collapsed-cause problem
`reason_code` was introduced to solve for `Scope`/`Verify`. This repo's Durable State Rule
(CLAUDE.md) applies directly here too: the resume decision and its cause must live in a typed,
closed-vocabulary field with a stable schema location — never only in a free-text `summary` string
or an ad hoc log line, which would recreate the exact never-do-this pattern this repo's Durable
State Rule already prohibits for any other durable meaning.

This requirement is stated here as a design constraint the future implementation ticket must
satisfy — building the actual field, its JSONL schema entry, and its `schema.md` documentation is
explicitly out of scope for this document (see Out of Scope in the owning ticket).

---

## 7. Resolution

**The resume-semantics validation rule required before any phase-level resume logic can be written
for `.claude/workflows/implement-ticket.js` is resolved as follows:**

1. **Minimum sufficient validation-field set confirmed, no field-set redesign needed:**
   `workflow_version` + `input_hash` + per-phase-artifact-existence, exactly as the epic proposed.
   `source_revision` and `phase_version` are **not** materially necessary (§3.3) — both are either
   subsumed by a correctly-scoped `input_hash` or lack real evidence of a gap `workflow_version`
   leaves open today.
2. **`workflow_version` reuse confirmed:** `agent-orchestration/workflows/implement-ticket.yaml`'s
   existing top-level `workflow_version` field (currently `2`) can and should be reused as-is for
   the resume validation rule — same source of truth, same coarse whole-workflow semantics
   `tools/agent_codex_runtime_shadow/matrix.py` already relies on for an analogous staleness check.
   No distinct field should be forked (§3.1).
3. **`input_hash` is new work**, with `tools/retrieval_cache.py`'s existing source-hash/staleness
   mechanism as the design precedent to model it on (§3.2) — not built by this document.
4. **Schema gap identified:** `workflow_version` and `input_hash` both need new fields added to
   `runs.jsonl`/`events.jsonl` (§4) — neither is recorded per-run/per-event today. Per-phase-
   artifact-existence needs no new recorded field; it is a live filesystem check.
5. **Invariant and fallback stated and binding** (§5): `checkpoint exists + checkpoint still valid =
   safe to reuse` — never `checkpoint exists = skip phase`; on any validation failure, restart from
   the earliest invalidated phase and every phase after it, since downstream phases transitively
   depend on upstream artifacts.
6. **Audit-trail requirement stated** (§6) for the future implementation ticket: checkpoint-reuse
   and checkpoint-invalidation decisions must be recorded as a typed, closed-vocabulary field in
   `agent-monitoring/events.jsonl` (a new `reason_code`-family value or equivalent), never only in
   free text.

`docs/plans/agent_infrastructure/ai_first_hardening_epics/workflow_reliability_epic.md`'s M3 section
is updated to reflect this resolution, pointing to this document, and stating M3 is now eligible to
move from Bucket B to a future Bucket-A ticket — not yet that ticket itself.

Any future ticket that builds the actual phase-level resume implementation should: (a) add the
`workflow_version`/`input_hash` fields identified in §4 to `runs.jsonl`/`events.jsonl` and document
them in `docs/agent-monitoring/schema.md`; (b) build `input_hash` computation modeled on
`retrieval_cache.py`'s existing precedent (§3.2); (c) implement the earliest-invalidated-phase
restart logic exactly as stated in §5; and (d) add the audit-trail field from §6 before, or as part
of, the same change — never ship resume-skip logic without its own inspectable audit trail landing
in the same ticket.
