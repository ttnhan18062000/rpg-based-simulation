---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260907-FILTERED-REPLAY-EVAL-PILOT
artifact_type: investigation
tags: [ai, agent-monitoring, testing]
---

# Investigation — TCK-20260907-FILTERED-REPLAY-EVAL-PILOT

## Current Behavior

### 1. The frozen experiment spec (`docs/plans/agent_infrastructure/ai_first_hardening_epics/agent_evaluation_foundation_experiment.md`)

Read in full. Exact content by section:

**Hypothesis** (lines 34-40): "A small, stratified sample of historical closed tickets, replayed
through `implement-ticket.js`'s investigation/plan/implement phases in isolation, can be scored
against known recurring defect classes with **repeatable** results (the same configuration scores
the same way across 2 independent runs) — even though it cannot yet be scored for **absolute
accuracy** against every possible defect type, because no adjudicated ground-truth labels exist for
that broader claim."

**Baseline** (lines 42-55, Level A data): corpus size "1,752 top-level ticket files (1,331
standard-tier, 292 hotfix-tier, 45 epic-tier)"; artifact coverage "1,099 of the 1,331 standard-tier
tickets (82.6%)"; failure-rate baseline "`agent-monitoring/runs.jsonl` (1,388 total records) shows
a 6.3% baseline gate-failure rate (DOD_BLOCKED, NEEDS_HUMAN_INPUT, NEEDS_CHANGES,
CONFLICTS_DETECTED, TESTS_FAILED, and related terminal statuses combined)"; and "two known,
independently-confirmed recurring defect classes" — doc-update self-report gap and test-scoper
background-hang pattern.

**Method** (lines 57-77), 5 numbered steps: (1) sample 20-40 tickets, stratified by tier/layer/
success-failure; (2) dataset hygiene — dev/validation/holdout split, ~60/20/20; (3) "Replay in
strict isolation: an isolated worktree, using `implement-ticket.js`'s session-scoped sidecar
exclusively — never the shared unscoped `.claude/current_run` path... do not run this experiment
before that milestone lands, or schedule the replay to strictly avoid overlapping live sessions in
the meantime"; (4) score for repeatability first — run twice, compare; (5) periodically refresh the
eligible pool.

**Metrics — three tiers** (lines 79-94): Primary = "does the replay correctly flag the 2 known
recurring defect classes, consistently, across 2 independent runs?"; Safety = "does the pilot's own
execution avoid contaminating any concurrent live session's sidecar state"; Efficiency = "wall-clock
time and tool-call volume for the replay itself — informative for scaling decisions later, not a
pass/fail bar." Terminology discipline: "only claim what's directly observed... or repeatable... Do
not claim a 'false-pass' or 'false-block' rate for anything beyond the 2 known classes."

**Exit criteria** (lines 96-105), verbatim, 3 items:
1. "Repeatable scoring established — the same configuration scores the same on 2 independent runs."
2. "Sample quality accepted for the 2 target defect classes specifically (not claimed for defect
   classes beyond those two)."
3. "Replay contamination risk is understood and demonstrably controlled in the pilot's own execution
   (Method step 3's isolation actually held, not just planned)."

**Kill criteria** (lines 107-117), verbatim, 2 items:
- "Scores are noisy/non-repeatable even on this clean, filtered, small sample — the signal isn't
  real at this scale, and scaling up first (a larger benchmark) would only compound an unproven
  method, per §69's own warning against exactly that trap."
- "Worktree isolation cannot fully eliminate the shared-sidecar contamination risk in practice — if
  `workflow_reliability_epic.md`'s M1 fix doesn't hold up under real replay conditions, this
  experiment should pause rather than proceed on a known-contaminated state path."
"If either kill criterion fires, the result is reported as a negative finding — not silently
abandoned, and not quietly rescoped into a smaller claim without saying so."

**Out of scope** (lines 119-127): widening sample/building a general eval platform before exit
criteria are met; deriving a task-success-rate metric for the retro loop; any change to
`implement-ticket.js`'s production behavior.

### 2. Existing replay infrastructure (`tools/agent_replay/`)

`tools/agent_replay/fixture_envelope.py` (86 lines, full read): `load_fixture()` is the single
validation entry point. `FixtureEnvelope` = `{version: int, source: dict, phases: list[PhaseEntry]}`.
`_REQUIRED_SOURCE_KEYS = ("ticket_id", "ticket_path", "events_run_id")`. `_REQUIRED_PHASE_KEYS =
("phase", "agent", "input", "output", "transition")`. Fail-closed: any missing/null required field
raises `FixtureValidationError` naming the exact field and phase index (lines 8-11, 46-86) — no
default substitution, no log-and-continue.

`tools/agent_replay/runner.py` (103 lines, full read): `replay_slice(fixture)` iterates
`fixture.phases` and hand-mirrors 4 deterministic branch points from `implement-ticket.js`, calling
the SAME real imported functions (`tag_registry.check_tags_registered`,
`gate_checks.plan_gate_static.plan_has_unresolved_questions_heading`):
- `Scope`: `entry.input["conflicts"]` non-empty → `CONFLICTS_DETECTED`; else
  `check_tags_registered(entry.input["tags"])` non-empty → `TAGS_NOT_REGISTERED`.
- `Investigate`: no deterministic gate exists — `pass`.
- `Plan`: `plan_has_unresolved_questions_heading(entry.input["plan_path"])` → `NEEDS_HUMAN_INPUT`.
- `Review`: `entry.output.get("verdict") != "APPROVED"` → that verdict string.
- Otherwise falls through to `final_status="ok"`.

`_fake_write_monitoring`/`_fake_hook_boundary` (lines 50-59) are pure in-memory no-ops — the module
docstring (lines 19-26) states an "Unconditional containment law": this file must never subprocess
or import any of the four `tools/agent-monitoring/{pre_tool_hook,post_tool_hook,record_run,
record_events}.py` scripts, enforced by `tests/agent_replay/test_runner_no_forbidden_calls.py`'s
whole-file string-constant scan (not just call-argument-scoped).

**Critically**: `replay_slice()` today has exactly 4 branch points and none of them are the 2 target
defect classes. There is no hook into it for a 5th/6th check — extending it means adding new branch
logic (or a wrapping scorer) that runs alongside/after these 4, not modifying them.

Existing tests (`tests/agent_replay/`, 5 files): `test_fixture_envelope.py`,
`test_fixture_spec_doc.py`, `test_runner.py`, `test_runner_no_forbidden_calls.py`, and
`test_no_mutation_snapshot.py` (see Isolation Mechanism below — this is the load-bearing precedent
for Method step 3/5's "capture evidence" requirement).

### 3. The one existing fixture (`tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml`)

Full read, 70 lines. `version: 1`, `source: {ticket_id, ticket_path, stored_artifacts_dir,
events_run_id, events_seq_range, final_status, tier}`, then 4 `phases` entries (Scope/Investigate/
Plan/Review), each with `phase`/`agent`/`input`/`output`/`transition`. Its header comment discloses
that Review phase `output.verdict`/`.violations` are *reconstructed* from `events.jsonl`'s
truncated `summary` text, not literally persisted anywhere as full JSON — a real limitation any bulk
converter inherits: `events.jsonl`'s `summary` field is capped at 200 chars
(`docs/agent-monitoring/schema.md` line ~445-462), so a bulk-converted fixture's `Review.output`
will frequently be a best-effort reconstruction, not a verbatim record, for tickets whose real
verdict/violations text exceeded that cap.

### 4. `docs/ai/replay_fixture_spec.md` — full read

Envelope shape spec matches `fixture_envelope.py` exactly (5 required phase keys, 3 required source
keys). Key constraints for new tooling:
- **"Why telemetry alone is insufficient"** (lines 46-56): a fixture cannot be built from
  `events.jsonl`/`tools.jsonl` rows alone — those only carry a truncated summary, not the full
  `agent()` JSON return or which branch was taken. A bulk converter must therefore read the real
  `stored_artifacts/{id}/{investigation,plan}.md` files (paths only, not embedded copies — "the
  runner reads the real permanent files at replay time, not a copy embedded here", per the existing
  fixture's own header) plus reconstruct `Review.output` from `events.jsonl`'s summary text where a
  full verdict record doesn't exist.
- **"Phase-slice scope statement"** (lines 58-65): this fixture format covers ONLY Scope→
  Investigate→Plan→Review. Implement/Architecture-Verify/Test/Parity/Security-Review/Verify/
  Finalize are explicitly out of scope for this format (would need a `files_changed`/diff payload
  not defined here). This bounds what the pilot's replay can score: it cannot replay or detect
  anything that only manifests in Implement-phase file diffs — directly relevant to the M2 defect
  class (see below), which is fundamentally an Implement/Document-Update/Verify-phase phenomenon.
- **"Unconditional containment law"** (lines 89-96, verbatim): "The replay runner must never
  subprocess or import `tools/agent-monitoring/pre_tool_hook.py`, `post_tool_hook.py`,
  `record_run.py`, or `record_events.py`, under any condition — including from an isolated or
  sandboxed working directory. This holds with zero exceptions; there is no conditional or 'safe
  mode' form of this rule." Any new fixture-conversion/defect-detection code this ticket adds under
  `tools/agent_replay/` inherits this law unconditionally — it must not import or subprocess those 4
  scripts even to *read* historical monitoring data (read access to `agent-monitoring/data/*/
  {runs,events,tools}.jsonl` must go through plain file I/O, e.g. the pattern
  `tools/agent_replay_codex/monitoring_shards.py` already uses, never through the forbidden
  scripts).
- **Fail-closed law** (lines 98-106): explicit, deliberate inversion of CLAUDE.md's fail-open
  monitoring-write convention — fixture validation must fail loudly, never silently substitute a
  default.

### 5. `guardrail_enforcement_epic.md` M2/M3 — full read; both already SHIPPED

**M2 — doc-update self-report gap** (lines 87-103, 168-179): **satisfied by
`TCK-20260904-DOC-COVERAGE-REVERSE-CHECK`** (done). Read `tools/gate_checks/done_checker_static.py`'s
`check_docs_to_update_coverage` (lines 529-610+) directly. It runs two independent directions:
- *Forward* (pre-existing): parses `investigation.md`'s "Docs Requiring Update" section for Format-1
  bullets, then checks `git status` shows each flagged path touched.
- *Reverse* (the M2 fix, lines 553-570 docstring): "does real `git status` show a `docs/` path
  touched during the ticket's diff that never made it into the ticket's own resolved `## Files
  Changed` or `## Related Docs` body-section text?" Tier-agnostic (no hotfix skip, unlike forward).
  Scoped to `docs/` paths only — explicitly cannot catch a non-`docs/` gap (disclosed limitation).

**Concrete detectable signal for M2** (real, retro-verified instances, `RETRO-2026-W36.md` line 343):
"the recurring 'Document-Update writes a real doc, but the writing agent's own self-report to the
ticket never mentions it' pattern (3 occurrences: ITEM-INSTANCE-HISTORY's `to_readonly()` fix,
RACE-RELATIONS-MATRIX's `02_combat_laws.md`, READINESS-SPEED-FORMULA's `corpus_tier_taxonomy.md`)".
The signal is fully reconstructable for a *historical* ticket without any live git working-tree
state: `git log --name-only` (or `git show --name-only`) for the ticket's own closing commit(s)
restricted to `docs/` paths, diffed against the closed ticket's own final `## Files Changed`/
`## Related Docs` body-section text. This is the same forward/reverse comparison
`check_docs_to_update_coverage` already does against *live* `git status`, just against a *historical*
commit's diff instead — the comparison logic is directly reusable, only the diff source changes.
Known-positive fixtures: `TCK-20260831-ITEM-INSTANCE-HISTORY`, `TCK-20260831-RACE-RELATIONS-MATRIX`,
`TCK-20260831-READINESS-SPEED-FORMULA` (all `tickets/done/`, all confirmed real instances where the
gap fired and was caught at Verify before shipping).

**M3 — test-scoper background-hang pattern** (lines 105-129, 180-188): **SHIPPED by
`TCK-20260904-TEST-SCOPER-HANG-GUARD`** — a real `SubagentStop` hook
(`tools/agent-monitoring/subagent_stop_background_guard.py`, full read, 76 lines). Reads
`payload["background_tasks"]` (a harness-populated array, "In-flight background work... registered
in this session") directly off the live `SubagentStop` hook payload; blocks (`sys.exit(2)` +
`{"decision": "block", ...}`) when non-empty and `stop_hook_active` is false; fails open on any
malformed input.

**Concrete detectable signal for M3 — real gap found**: `background_tasks` is a **live runtime-only
signal** sourced from "a live per-session task registry" (module docstring) — it is never persisted
to any ticket-level artifact, `events.jsonl`, or `tools.jsonl` row. `docs/agent-monitoring/schema.md`
was grepped in full for "background": the only hit (line 266) is prose about spend-proxy cost
invisibility, not a schema field. `tools.jsonl`'s `input_summary` field (schema lines 445-462)
records only "first 80 chars of command for Bash" — the `run_in_background` boolean parameter is a
separate tool-call argument not guaranteed to appear in that truncated text, and there is no
dedicated boolean/flag field recording whether a given Bash call was backgrounded. This means: unlike
M2, **there is no reliable structural signal in any stored historical artifact (ticket body,
`stored_artifacts/`, `events.jsonl`, `tools.jsonl`) that would let a bulk fixture-conversion of a
past closed ticket determine whether that ticket's `test-scoper` subagent ended its turn on a live
background task.** `RETRO-2026-W36.md`'s Notes section (line 343) reports the pattern "recurred 3
times this batch" in aggregate prose, without naming the 3 specific ticket IDs (unlike M2's named
3). A targeted search of `tickets/working_log.csv` for "background"/"hang"/"still running" found
only meta-tickets about the *fix itself* (`TCK-20260712-WORKFLOW-FRICTION-FIXES`,
`TCK-20260902-AGENT-BACKGROUND-TASK-TURN-END-DEFENSE-IN-DEPTH`,
`TCK-20260904-TEST-SCOPER-HANG-GUARD`), not per-incident tickets. **This is a real, load-bearing gap
for this pilot's own Method step 4 (AC #3: "detects... the test-scoper background-hang pattern on at
least one known-positive fixture") — flagged under Risks and Open Questions below.**

### 6. Re-verified baseline numbers (fresh as of this investigation, 2026-09-07, later same day than
the ticket's own scoping pass — corpus grew further within this session)

| Metric | Spec doc (frozen, stale) | Ticket's own scoping (a few hours earlier) | This investigation (now) |
|---|---|---|---|
| `tickets/done/` top-level `.md` count | 1,752 | 1,849 | 1,852 (1,815 are `TCK-*.md`; 37 are legacy pre-ticket-ID files, e.g. `RESTRUCTURE-01.md`, `enhance_frontend.md`) |
| `tickets/done/` incl. 79 tracking subfolders | (not stated) | (not stated) | 1,955 `.md` files total recursively (103 additional files live under subfolders like `tickets/done/m1-quick-wins/`) |
| Tier breakdown (body `## Tier`, top-level `TCK-*.md` only) | 1,331 standard / 292 hotfix / 45 epic | 1,401 standard / 312 hotfix / 52 epic / 3 unlabeled | **1,398 standard / 313 hotfix / 52 epic / 3 unlabeled** (1,766 typed total) |
| Standard-tier with matching `stored_artifacts/{id}/` | 1,099/1,331 (82.6%) | 1,169/1,401 (83.4%) | **1,171/1,398 (83.76%)** |
| `stored_artifacts/` directory count (all, not just standard-tier) | (not stated) | (not stated) | 1,288 |
| `runs.jsonl` records (now sharded, not one file) | 1,388 (single file — path doesn't exist) | 1,476+ | **1,479** across `agent-monitoring/data/{2026-W23...2026-W37,unknown-week}/runs.jsonl` (15 weekly shards + 1 fallback bucket) |
| `events.jsonl` records | (not stated) | (not stated) | 9,735 across shards |
| `tools.jsonl` records | (not stated) | (not stated) | 203,752 across shards |

Confirms the ticket's own finding: numbers keep moving (a handful more tickets closed between the
ticket's scoping pass and this investigation, same session) — the sampler and results report must
compute these live at run time, never hardcode any of the 3 columns above.

### 7. Isolation mechanism — real prior art found, not build-from-scratch

`tools/agent_replay/`'s own `replay_slice()` is **already proven zero-write** by
`tests/agent_replay/test_no_mutation_snapshot.py` (full read, 132 lines) — this directly satisfies
half of Exit Criterion 3 already, for the *existing* Scope→Review replay path. Its technique: capture
a `git status --porcelain` snapshot of `tickets/` and `agent-monitoring/data/` before running
`replay_slice()`; if clean before, assert clean after; if dirty before (the common real case, since
this repo is routinely dirty with concurrent sibling-ticket work), fall back to a sha256 content-hash
of every watched file taken immediately before/after and assert identity. A dedicated regression test
(`test_watch_set_actually_detects_a_deliberate_mutation_under_agent_monitoring_data`) proves the
watch set actually fires on a real mutation, guarding against the exact vacuous-pass failure mode a
naive "assert no diff" implementation could silently have.

`tools/agent_replay_codex/containment.py` (full read, 106 lines) **generalizes this exact same
technique into a reusable, parameterized module** — `capture_snapshot(repo_root)` /
`assert_no_diff(pre, post)`, watching `tickets/`, `agent-monitoring/runs.jsonl`,
`agent-monitoring/events.jsonl`, `agent-monitoring/tools.jsonl` pathspecs (note: these 3 literal
paths are the *retired* pre-sharding convention — see Anti-Drift Hazards, this module has the same
staleness risk `test_no_mutation_snapshot.py`'s regression test was built to catch and fix). It also
wraps `tools/agent-monitoring/manifest.py`'s `capture_lines`/`assert_prefix_preserved` for an
append-only-specific check (`snapshot_monitoring_lines`/`assert_monitoring_prefix_preserved`) —
verifying a JSONL file only ever gained lines at its end, never had existing lines mutated, which is
a strictly stronger guarantee than pure content-hash-equality for the "zero contamination" claim
Exit Criterion 3 actually wants (a real live session doing legitimate concurrent work WILL make
`agent-monitoring/*.jsonl` grow during the pilot's run window — the pilot needs to distinguish "grew
because another concurrent session wrote its own attributed lines" from "grew because the pilot's own
`replay_slice()` execution wrote something," which pure content-hash equality cannot do but
prefix-preservation can, combined with attribution-scoping the new lines' `run_id`s away from the
pilot's own).

`tools/agent_codex_realrepo_pilot_harness/preflight.py` (full read) is a **structurally adjacent but
functionally different** pattern: "no-write, fail-closed admission for an injected scratch
repository." It captures a baseline tree hash (`capture_policy_baseline`/`tree_digest`) of a
caller-supplied scratch root before any operation, and validates a signed `ExpectedWritePolicy`
against that baseline — this is a *pre-admission gate for a Codex-runtime-activation pilot's own
write budget*, not a git-worktree-creation mechanism. **Grepped the entire
`tools/agent_codex_realrepo_pilot_harness/` and `tools/agent_replay_codex/` trees for the literal
string "worktree" — zero matches.** Neither module creates or manages a `git worktree`; "scratch
root"/"injected root" in this subsystem means an arbitrary directory path the caller supplies
(commonly a `tmp_path` in tests), not necessarily a real git worktree.

### 8. `tools/agent_replay_codex/` relevance — confirmed genuinely relevant prior art, not an
unrelated Codex-specific subsystem

Read `monitoring_shards.py` (74 lines) and `containment.py` (106 lines) in full. `monitoring_shards.py`
docstring states explicitly: "The codex-runtime-activation containment/rollback/provenance guardrails
in this subsystem... treat each of the 3 sources as one logical monitoring stream, both against the
real repo (sharded per week) and against synthetic scratch trees." Its `source_paths()`/
`read_source_bytes()`/`hash_source()` functions are the **already-correct, already-tested way to read
across `agent-monitoring/data/<week>/<source>.jsonl` shards** (matching the current real layout, sorted,
including the `unknown-week` fallback bucket) — this is genuinely reusable for (a) building the
sampler's success/failure stratum from `runs.jsonl` across all shards, and (b) the pilot's own
no-contamination-evidence snapshot needing to hash/diff the *sharded* `agent-monitoring/data/`
layout, not the retired 3-file layout `containment.py`'s own `_WATCHED_GIT_PATHSPECS` still
hardcodes (see Anti-Drift Hazards). It is not Codex-CLI-specific in the way its package name
suggests — it is a general "read every monitoring shard, compare a repo tree before/after" utility
that happens to live under a Codex-labeled package because that's the ticket that built it
(`TCK-20260721-CODEX-REPLAY-PARITY`, `TCK-20260903-MONITORING-DATA-CODEX-REMIGRATION`), not because
its logic is Codex-provider-specific.

## Mechanics / Engine Constraints

None apply directly — this is agent-infrastructure tooling work (`layer: ai`), not a change to
simulation mechanics or gameplay behavior. No `docs/mechanics/` chapter or `docs/engine/` contract
governs this ticket's scope. Confirmed via the ticket's own Related Docs list (none cite a Mechanics
Bible chapter or engine contract) and via this investigation's own reads above (all `docs/ai/`,
`docs/plans/agent_infrastructure/`, and `tools/agent_replay*` — none touch `src/` simulation code).

## Docs Requiring Update

- `docs/plans/agent_infrastructure/ai_first_hardening_epics/agent_evaluation_foundation_experiment.md`:
  the frozen spec's own stated lifecycle is "Frozen Architecture Proposal → Experiment Specification
  → Hypothesis/Baseline/Method/Metrics/Exit Criteria/Kill Criteria → Run Experiment → Decision" — this
  ticket is the "Run Experiment → Decision" step, so the results (per-Exit-Criterion met/not-met with
  evidence, whether either Kill Criterion fired, the 3-tier metric numbers) must be recorded back into
  this doc (e.g. an appended `## Results` / `## Decision` section) or this frozen spec permanently
  reads as still-unexecuted to any future reader, contradicting the ticket's own AC #5/#6. This does
  NOT mean rewriting the Hypothesis/Method/Metrics/Exit/Kill Criteria text itself (explicitly out of
  scope) — only appending the outcome.
- `docs/plans/agent_infrastructure/ai_first_hardening_epics/roadmap.md`: item 13's Horizon-1 status
  and the "downstream Bucket-C dependency notes (items 18-20)" this ticket's own Related Docs cites
  must reflect whether this pilot's Exit Criteria were met (unblocking those items) or a Kill
  Criterion fired (keeping them blocked) — the roadmap is the doc other tickets read to know whether
  items 18-20 are actionable yet, so leaving it stating the old "gated, pending pilot" language after
  this pilot concludes would misinform every future reader of that doc.
- `docs/ai/replay_fixture_spec.md`: **conditional** — only if the fixture-conversion tooling this
  ticket builds needs to extend the envelope shape itself (a new `version: 2`, new required phase
  keys for defect-class-detection input, or a documented divergence for how `Review.output` gets
  reconstructed at bulk-conversion scale vs. the single hand-built example's disclosed
  reconstruction). If the implementer's chosen design instead layers defect-class detection as a
  separate post-`replay_slice()` scoring pass that consumes the *existing* unmodified envelope shape
  (reading `fixture.source`/`fixture.phases` as already defined, e.g. deriving M2's signal from a
  separately-loaded git-diff artifact rather than a new envelope field), this doc does not need to
  change. Leave this bullet in Format 1 per the resolved-conditional-bullet convention
  (`TCK-20260829-DOC-COVERAGE-CONDITIONAL-BULLET-BLIND-DOD-BLOCKED`) — whoever resolves it should add
  "Resolved during implementation, condition not met" if the envelope shape ends up unchanged.
  **Resolved during implementation, condition not met**: `tools/agent_replay/defect_detectors.py`
  layers M2/M3 as separate detector functions consuming their own inputs (a git-diff docs-path list
  plus ticket body-section text for M2; a `SubagentStop`-shaped payload dict for M3) — neither
  `fixture_envelope.py`'s required-key set nor `docs/ai/replay_fixture_spec.md`'s envelope shape
  changed.

The `docs/parity_ledger/*.yaml` files (any subsystem) are not required to change for this ticket: the
ticket's own Out of Scope section states this explicitly ("this ticket builds pilot/analysis tooling
and produces an evidence report; it does not change any authoritative simulation/gameplay behavior,
so no parity ledger entry applies"), and this investigation's own reads confirm no simulation/gameplay
code path is touched — restated here in Format 2 so `check_docs_to_update_coverage`'s regex never
mistakes it for a required bullet.

The `docs/plans/agent_infrastructure/ai_first_hardening_epics/bucket_c_future_options.md` doc (items
18-20, the downstream work gated on this pilot) is not required to change for this ticket: the
ticket's own Out of Scope section frames those items as "separate, larger Bucket-C item[s]... not a
byproduct this ticket produces automatically" — this ticket's job is to produce the gating evidence
(via the results appended to `agent_evaluation_foundation_experiment.md` and `roadmap.md` above), not
to itself unblock or re-scope items 18-20's own doc.

## Parity Ledger Overlap

None. This ticket does not modify any `src/` simulation/gameplay code path — it builds read-only
sampling/fixture-conversion/detection tooling under `tools/agent_replay/` and produces an evidence
report. No `docs/parity_ledger/*.yaml` entry's `text` overlaps with this scope (checked: none of the
8 subsystem files reference replay tooling, agent evaluation, or defect-class detection — this is
agent-infrastructure meta-work, categorically outside all 8 subsystems' scope:
`substrate.yaml`/`combat_movement.yaml`/`strategic_cognition.yaml`/`town_resource.yaml`/
`progression.yaml`/`social_narrative.yaml`/`world_dynamics.yaml`/`infrastructure.yaml`).

## Prior Work

- `stored_artifacts/TCK-20260721-CODEX-REPLAY-PROOF` — built `tools/agent_replay/` (runner +
  fixture_envelope) from scratch; this pilot extends it, matching the ticket's own framing.
- `TCK-20260904-DOC-COVERAGE-REVERSE-CHECK` (done) — shipped M2's structural fix; the reverse-check
  logic in `check_docs_to_update_coverage` is the reusable comparison pattern for the M2 fixture
  detector.
- `TCK-20260904-TEST-SCOPER-HANG-GUARD` (done) — shipped M3's structural fix; its own investigation/
  plan (in `stored_artifacts/TCK-20260904-TEST-SCOPER-HANG-GUARD/`, not re-read in full here — the
  live hook code was read directly instead, since that's what a fixture-based detector would need to
  emulate) is the canonical source for `background_tasks`' real schema shape.
- `TCK-20260904-SIDECAR-SETTINGS-HOOK-MIGRATE` (done, 2026-09-04) — the M1 sidecar fix Method step 3
  depends on; confirmed shipped and live in `.claude/workflows/implement-ticket.js` (both
  `.claude/current_run` unscoped and `.claude/current_run.<SESSION_ID>` scoped paths are written side
  by side by the live orchestrator's `writeSidecar()` — the pilot's replay execution itself must not
  invoke that function at all, matching the containment law already enforced for
  `replay_slice()`).
- `TCK-20260721-CODEX-REPLAY-PARITY` — built `tools/agent_replay_codex/containment.py`'s
  `capture_snapshot`/`assert_no_diff`, the most directly reusable prior art for this ticket's own
  Method step 5 no-contamination evidence requirement.
- No prior stored artifact investigates this exact pilot scope (confirmed by the ticket's own Related
  Stored Artifacts section and independently by this investigation's searches above) — this is
  genuinely new-build work, not a duplicate.

## Risks and Open Questions

1. **M3's known-positive fixture requirement (AC #3) has no reliable historical signal — this could
   block that specific AC as scoped.** As detailed in Current Behavior §5, `background_tasks` is a
   live-session-only runtime signal never persisted to any stored artifact for a *past* ticket. Three
   options exist, and the choice materially affects what "known-positive fixture" means for M3:
   (a) construct a *synthetic* fixture (a hand-built minimal envelope simulating a `SubagentStop`
   payload with a non-empty `background_tasks`, exercising the guard's own detection logic directly,
   not derived from any real historical ticket) — this satisfies AC #3's literal text ("at least one
   known-positive fixture") without claiming it represents a real past ticket; (b) treat
   `TCK-20260904-TEST-SCOPER-HANG-GUARD`'s own regression test fixture
   (`tests/fixtures/claude_hook_payloads/subagent_stop_schema_capture.json`) as the known-positive
   source, if its shape is adaptable; (c) flag M3 detection as validated only against synthetic/guard-
   level fixtures, not against a genuine historical `tickets/done/` sample member, and disclose this
   explicitly in the results report rather than silently treating a synthetic fixture as equivalent to
   a real M2-style historical instance. **This is a real open question for the planner to resolve
   explicitly, not an assumption to make silently** — the spec's own "Terminology discipline" clause
   (only claim what's directly observed) argues for option (c)'s honesty over silently blurring
   synthetic and real-historical fixture provenance.
2. **The Kill Criterion for isolation ("Worktree isolation cannot fully eliminate the shared-sidecar
   contamination risk in practice") is written assuming literal git-worktree isolation, but no
   existing tooling in this repo actually creates one for this purpose** (§7/§8 above — zero
   "worktree" hits in the two most relevant existing packages). The planner must decide whether "an
   isolated worktree" (Method step 3's literal words) means (a) a real `git worktree add` per this
   project's own "Worktree & Branch Isolation" CLAUDE.md convention, run for the duration of the pilot,
   or (b) reuses the existing `replay_slice()`/`containment.py` snapshot-and-assert pattern without a
   literal separate worktree, on the reasoning that `replay_slice()` itself never writes anything
   regardless of which directory it runs from (already proven). Recommendation (not a decision, per
   Gate Integrity): (b) is lower-risk and directly reuses tested code, but if pursued, the results
   report must be explicit that "isolated worktree" was satisfied via a proven zero-write execution
   path plus a snapshot-diff check, not via literal worktree creation — otherwise a future reader
   could reasonably conclude Method step 3 wasn't actually followed as written.
3. **`containment.py`'s `_WATCHED_GIT_PATHSPECS` still hardcodes the 3 retired monolithic
   `agent-monitoring/{runs,events,tools}.jsonl` paths** (§7 above) — reusing it unmodified for this
   pilot's own no-contamination evidence would silently watch nothing under the real
   `agent-monitoring/data/<week>/` shard layout (the exact vacuous-pass bug
   `test_no_mutation_snapshot.py`'s own regression test was built to catch, in the *other* module).
   Any reuse of `containment.py` for this ticket must either widen its pathspecs the same way
   `test_no_mutation_snapshot.py` already did, or route through `agent_replay_codex/
   monitoring_shards.py`'s `source_paths()` instead of `containment.py`'s own hardcoded list.
4. **The results-report doc location is genuinely ambiguous** — see Docs Requiring Update above;
   flagged there as a recommendation (append to the frozen spec doc + roadmap.md), not asserted as the
   only valid answer. The planner should confirm this placement rather than default silently to
   `stored_artifacts/{ticket_id}/results.md` only (which would satisfy AC #5/#6 literally but leave
   the frozen spec doc itself stranded as "not yet run" for any reader who doesn't know to look in
   `stored_artifacts/`).
5. **Bulk-converted fixtures will have lower-fidelity `Review.output` than the one hand-built example**
   (§3 above, the 200-char `events.jsonl` summary cap) — for the 20-40 sampled tickets, some fraction
   will have Review verdicts/violations that cannot be faithfully reconstructed from truncated
   telemetry. This is not a blocker (the existing fixture already discloses and accepts this
   limitation) but should be surfaced per-fixture in the manifest/conversion-exclusion log, not
   silently smoothed over.

## Anti-Drift Hazards

- **Do not modify `replay_slice()`'s 4 existing branch points** (Scope conflicts/tags,
  Plan unresolved-questions, Review verdict) while adding defect-class detection — the ticket's Related
  Code Areas says "extend," and the existing 5-file test suite (`tests/agent_replay/`) asserts exact
  behavior for those 4 branches; a change there is scope creep into `TCK-20260721-CODEX-REPLAY-PROOF`'s
  already-closed, already-tested surface.
- **Never let the new fixture-conversion/defect-detection code import or subprocess any of the 4
  forbidden `tools/agent-monitoring/` scripts**, even for read-only historical data access — use plain
  file I/O or `agent_replay_codex/monitoring_shards.py`'s helpers instead. This is an unconditional law
  per `docs/ai/replay_fixture_spec.md`, and `test_runner_no_forbidden_calls.py`'s whole-file string
  scan will likely need a sibling test covering any new module this ticket adds under
  `tools/agent_replay/`.
- **Do not let "run the sample through the replay pipeline twice" become a live re-execution of real
  agents against real tickets** — Out of Scope explicitly states "Any change to `implement-ticket.js`'s
  production behavior — the replay calls the same real, already-tested functions read-only/imported,
  in isolation; it never modifies the orchestrator." The 2 runs are 2 replay-layer executions against
  the same static fixtures, not 2 fresh live ticket implementations.
- **Do not widen the sample beyond 20-40 or build general eval-platform scaffolding** — explicitly Out
  of Scope both in this ticket and in the frozen spec's own Out-of-scope section, twice-stated for a
  reason (the frozen proposal's §69 warning against scaling an unproven method).
- **Do not let the "repeatable refresh procedure" (Scope item 8) turn into actually re-running a
  refreshed pilot** — the ticket explicitly separates "documenting the procedure is in scope; actually
  re-running the refreshed pilot is not."
- **Do not silently claim a "false-pass"/"false-block" rate for anything beyond the 2 known defect
  classes** — the spec's own Terminology discipline clause forbids this explicitly; the results report
  must stay within what the 2-run repeatability comparison and the 2 named classes actually support.
