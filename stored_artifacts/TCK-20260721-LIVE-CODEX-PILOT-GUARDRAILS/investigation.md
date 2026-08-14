---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS
artifact_type: investigation
tags: [ai, workflows, hooks, rollback]
---

# Investigation — TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS

## Current Behavior

### The ticket's own scope boundary — confirmed verbatim, not inferred
`tickets/inprogress/TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS.md` Out of Scope (line 40):

> "Does not begin actual live pilot execution until the orchestration-contract-core,
> Claude-conformance-adapter, Codex-guidance-fixture-capture, monitoring-writer-unification, and
> Codex-replay-parity tickets have all landed and passed their own exit criteria, AND the separate
> legacy `.agents/skills/` quarantine gate (owned by the Codex-guidance-fixture-capture ticket) is
> independently satisfied — this ticket's scope is limited to designing and building the
> guardrail/rollback/sign-off mechanisms; live execution itself remains blocked pending those
> preconditions."

AC #7 (the ticket's own meta-acceptance-criterion, line 51) makes this self-referential and
mandatory: *"This ticket's own scope explicitly states that live pilot execution is blocked
pending the prior 5 tickets AND the `.agents/skills` quarantine gate, and that only
guardrail/rollback/sign-off design-and-build work is in scope now."* `tickets/todos/
provider-agnostic-implementation/SEQUENCE.md:34-38` independently corroborates the same reading:
*"LIVE-CODEX-PILOT-GUARDRAILS is deliberately last: its own ticket text is explicit that live
pilot **execution** stays blocked even after this ticket's own guardrail/rollback tooling is
built, pending all 5 prior tickets plus a separate, independently-owned precondition."*

**All 5 hard-predecessor preconditions are confirmed landed** (`tickets/done/` + `stored_artifacts/`
for all 5: ORCHESTRATION-CONTRACT-CORE, CLAUDE-CONFORMANCE-ADAPTER, CODEX-GUIDANCE-FIXTURE-CAPTURE,
MONITORING-WRITER-UNIFICATION, CODEX-REPLAY-PARITY). The `.agents/skills/` quarantine gate is also
confirmed satisfied: `docs/archive/legacy_agents_skills_20260722/` exists (the archived copy), and
the live `.agents/skills/` tree now has exactly 16 contract-generated entries (`ls .agents/skills |
wc -l` → 16), matching `agent-orchestration/skills.yaml`. **This means all of this ticket's own
stated entry gates for beginning guardrail-tooling work are satisfied — but this only unblocks
*building* the guardrails, never live pilot *execution*, per the Out-of-Scope text above.**

### `.codex/config.toml`'s own comment names this exact ticket as owner of eventual hook wiring
`.codex/config.toml` (committed by CODEX-GUIDANCE-FIXTURE-CAPTURE, read in full) — zero `[hooks]`
table, by design — carries this comment: *"A future, separate ticket (live-Codex-pilot-guardrails,
out of this ticket's scope) owns actually wiring a production hook, using the registration syntax
this ticket's Step 11 discovered and recorded in this ticket's Implementation Notes."* The
empirical hook-registration TOML syntax that ticket discovered (recorded in
`stored_artifacts/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE/` Implementation Notes, cross-quoted
by `stored_artifacts/TCK-20260721-CODEX-REPLAY-PARITY/investigation.md:33-40`):
```toml
[[hooks.PostToolUse]]
matcher = "*"

[[hooks.PostToolUse.hooks]]
type = "command"
command = "..."
```
**This creates a real tension this ticket's Plan phase must resolve, not assume**: does "own
actually wiring a production hook" mean this ticket writes the `[[hooks.PostToolUse]]` block into
the *committed* `.codex/config.toml` (which would make the adapter live-capable — a step toward,
not identical to, beginning execution), or does it only design/build the *toggle mechanism* while
keeping the committed config hook-free, consistent with the ticket's own Out-of-Scope line? See
Risks and Open Questions #1 — flagged, not decided here.

### No pilot candidate ticket is named anywhere
Checked: this ticket's own `Related Tickets` (8 entries — all are the discovery-epic ADR/matrix/
disposition tickets and this batch's own already-DONE predecessors, none of which is a
standard/hotfix ticket presented as a live-pilot candidate); `Assumptions / Open Questions` (3
bullets, none names a candidate ticket); `implementation_plan.md`'s Phase 5 section (`:234-249`,
read in full — "Select an explicitly designated standard/hotfix ticket..." is phrased as a future
action the pilot workflow performs, not a name); `SEQUENCE.md` (no candidate named). **No concrete,
already-identified real ticket is designated as the pilot candidate anywhere in this repo today.**
This ticket therefore builds generic, ticket-agnostic selection/rejection tooling (the
"ticket-selection step" of AC #1/#2) rather than validating against one hand-picked example ticket
— confirmed, not assumed.

### Ticket format has no "human owner" or "rollback plan" field — a real structural gap
`CLAUDE.md`'s "Ticket Format" section (the authoritative ticket template) lists 17 required body
sections (`## Title` through `## Completion Summary`) — grepped directly against this ticket's own
file: none is named `Owner`, `Human Owner`, or `Rollback Plan`. Searched every ticket in
`tickets/done/` for a `## Owner` or `## Rollback` heading — zero hits. Two tickets
(`TCK-20260424-PH12-M1-READINESS`, `TCK-20260424-PH12-M4-CUTOVER-VALIDATION`) mention "rollback" as
free prose inside `## Scope`/`## Completion Summary`, not as a structured, machine-checkable field.
**AC #1's own wording — "verified against actual ticket/run state (not just doc convention)" —
directly rules out accepting free prose as sufficient evidence.** This means: either (a) the ticket
template needs a new structured field (a `tools/ticket_field_values.py`-style body-field addition,
mirroring how `## Tier`/`## Status`/`## Priority` are already validated), or (b) this ticket defines
a separate, sidecar structured record (e.g. a small YAML/JSON manifest keyed by ticket_id, outside
the ticket file itself) that the selection step reads. Neither is decided by any doc read in this
investigation — see Risks #2.

### `provider`/`execution_id`/`ticket_id` fields exist in the schema but are NOT populated by any
### real call site today — directly undermines the "concurrent claim" check's real-world signal
Confirmed by direct source read, not inference:
- `tools/agent-monitoring/writer.py` is a generic append layer — it never references
  `execution_id`/`provider`/`ticket_id` by name (it writes whatever pre-serialized line string it's
  given).
- `tools/agent-monitoring/record_run.py`/`record_events.py` only validate a fixed `REQUIRED` field
  set (`run_id`, `start_ts`, `workflow`, `tier`, `final_status`, `agent_count` for `record_run.py`)
  — `execution_id`/`provider`/`ticket_id` are accepted **if the caller supplies them** (proven by
  `tests/tools/test_record_run.py::test_execution_identity_fields_pass_through_unchanged` and the
  equivalent `record_events.py` test), but nothing rejects their absence either.
- `grep -rn "execution_id" .claude/workflows/implement-ticket.js` → **zero hits.** The live
  orchestrator that actually invokes `record_run.py --data '...'` for every real ticket run in this
  repo does not construct or pass `execution_id`/`provider`/`ticket_id` today.
- Confirmed against real data: `tail agent-monitoring/runs.jsonl` for the 5 sibling tickets in this
  same batch shows only `run_id`/`start_ts`/`end_ts`/`workflow`/`tier`/`final_status`/`agent_count`/
  `duration_s` — no `provider`, `execution_id`, or top-level `ticket_id` field on any real record.

**Consequence for this ticket's own AC #1/#2**: "programmatically rejects a candidate that is
concurrently claimed by both providers for the same work" needs a real signal to check — either (a)
a `provider` field on real run records (not populated today, confirmed above), or (b) some other
proxy (e.g. an in-progress marker file, a lock akin to the writer's own lock-file protocol, or
reading `run_id`→ticket-id association plus `final_status`/absence-of-`end_ts` as an "in-progress"
proxy per-workflow, without relying on a `provider` field that doesn't exist in practice yet). This
is a genuine, confirmed gap between what the schema *supports* (via passthrough) and what real
executions actually *write* — flagged for Plan, not silently assumed to already work. See Risks #3.

### Reusable predecessor tooling — direct precedents this ticket should build on
- `tools/agent-monitoring/manifest.py::capture_lines(agent_monitoring_dir) -> dict[str, list[str]]`
  and `assert_prefix_preserved(pre, post)` (read in full, `manifest.py:69-94`) — exactly the
  pre/post baseline-manifest capture-and-diff mechanism this ticket's Scope explicitly says to
  *consume, not rebuild* ("consuming the baseline-monitoring-manifest ticket's tooling"). Raises
  `AssertionError` naming the exact file on any rewrite/reorder/deletion of pre-existing lines;
  new appended lines are tolerated. This is the direct building block for AC #4 ("Pre/post baseline
  manifests are captured and diffed for the pilot; the pilot workflow fails closed if any
  pre-existing line's hash changes" — note: the AC's own wording says "hash changes," but the
  existing tooling's actual mechanism is prefix-line-equality, not a whole-file hash; `build_manifest()`
  in the same module does compute a whole-file SHA-256 per file as a coarser secondary signal — Plan
  should decide whether AC #4's "hash" language maps to `build_manifest`'s hash field, or to
  `assert_prefix_preserved`'s finer-grained check, since they are not the same mechanism).
- `tools/agent_replay_codex/consent_gate.py::require_live_consent()` — the direct precedent for a
  "programmatically-checked" human-consent gate: a strict, non-coercive env-var equality check
  (`env.get(CONSENT_ENV_VAR) != "1"` → raise), checked as the literal first statement before any
  subprocess object exists. `TCK-20260721-CODEX-REPLAY-PARITY`'s own investigation explicitly
  contrasts this against the weaker, honor-based `CODEX-GUIDANCE-FIXTURE-CAPTURE` Step 10 precedent
  and states this ticket's own AC bar is stated even higher still ("distinct from and later than
  ticket designation" — i.e., not just "consent to run the tool at all," but a second, later gate
  specifically "immediately before live pilot execution itself"). Reusing the mechanics (strict env-var
  equality, checked first) is appropriate; the two-gate structure (designation-time gate vs.
  execution-time gate) is new modeling work not present in any predecessor.
- `tools/agent_replay_codex/containment.py::capture_snapshot()`/`assert_no_diff()` — the
  git-porcelain-if-clean/content-hash-if-dirty snapshot technique, watching `tickets/` +
  `agent-monitoring/{runs,events,tools}.jsonl`. Directly reusable as one candidate implementation
  for AC #2's "zero bytes differ across `agent-monitoring/*.jsonl` and the pilot ticket file" test —
  though note this ticket's own AC is scoped tighter (one specific pilot ticket file, not all of
  `tickets/`), so a narrower, single-file variant may be more appropriate than reusing the module
  verbatim.
- `tools/agent_replay_codex/codex_config_guard.py::snapshot_config_bytes()`/
  `assert_config_bytes_unchanged()` — direct precedent for asserting `.codex/config.toml` byte-
  identity across an operation; relevant to whatever config/flag rollback mechanism this ticket
  designs (AC #2).
- No existing feature-flag mechanism is reusable. `src/domains/optimization/feature_flags.py`
  (`FeatureFlagManager`, `OFF/SHADOW/ON/STRICT` modes) is confirmed, by direct read, to be a
  per-tick **simulation-engine** mechanism (`ENABLE_WORLD_CAPABILITY_LAYER`,
  `ENABLE_COMBAT_ENGAGEMENT`, etc.) — structurally unrelated to agent-orchestration/provider
  enablement and not import-compatible with this ticket's concern (confirmed per the ticket's own
  Assumptions line 87). This ticket needs new, purpose-built config/flag tooling, most naturally a
  small addition to (or new sibling of) `tools/agent_orchestration_codex_adapter/`'s existing
  write-guard pattern, not a reuse of `feature_flags.py`.
- `agent-orchestration/rendered/claude-adapter.yaml`/`agent-orchestration/intentional-divergences.md`
  (built by `CLAUDE-CONFORMANCE-ADAPTER`) and `tools/agent_orchestration_claude_adapter/
  divergence_log.py::is_approved()` — the existing human-approved-divergence pattern
  (`Approved-by`/`Approved-date`/`Status: RATIFIED` fields), the closest existing precedent for
  "programmatically-checked human sign-off," although it is scoped to *documentation divergence*
  approval, not *pre-execution* authorization — AC #5's "human sign-off gate... immediately before
  live pilot execution itself" is a different kind of gate (authorization-to-proceed, not
  after-the-fact ratification of an already-observed difference) and needs its own mechanism, not a
  literal reuse of `divergence_log.py`.

### Related Code Areas — existence check
All 4 files/paths named in this ticket's own `Related Code Areas` were confirmed to exist by direct
read/`ls`: `tools/agent-monitoring/post_tool_hook.py`,
`tests/tools/test_monitoring_writer_lockfile_candidate.py`,
`tests/agent_replay/test_runner_no_forbidden_calls.py`,
`tests/agent_replay/test_no_mutation_snapshot.py`. No gap found here.

### "Enabled hook/writer set" — what Phase 2/Phase 3 evidence this ticket's AC #3 must subset
Per AC #3 ("Only Phase-2/Phase-3-evidenced hook events are registered as enabled for the pilot; a
test enumerates the enabled set as a subset of that evidence"): Phase 2
(`CODEX-GUIDANCE-FIXTURE-CAPTURE`)'s only proven hook event is `PostToolUse` — the one and only
event captured in `tests/fixtures/codex_hook_payloads/post_tool_use_stdin_capture.json` and the one
named in the empirical `[[hooks.PostToolUse]]` TOML syntax above; no other Codex hook event
(`PreToolUse`, `SessionStart`, `Stop`, etc.) has ever been fixture-captured for Codex in this repo.
Phase 3 (`MONITORING-WRITER-UNIFICATION`)'s proven writer is `tools/agent-monitoring/writer.py`'s
`write_line`/`write_lines` pair (both call sites — `post_tool_hook.py`'s single-record path and
`record_run.py`/`record_events.py`'s CLI path — are proven, per that ticket's own regression suite).
So the maximal "evidenced set" this ticket may enable for the pilot is: hook event = `PostToolUse`
only; writer = `write_line`/`write_lines` only. Anything wider (any other hook event, any writer
bypassing `writer.py`) is out of the evidenced set by construction.

## Mechanics / Engine Constraints

Not applicable. This ticket touches only agent-orchestration/guardrail tooling (`tools/`,
`agent-orchestration/`, `.codex/`, tests) — no `src/` simulation code, no `docs/mechanics/` chapter,
no `docs/engine/` contract governs this subsystem, consistent with the identical "not applicable"
finding independently reached by all 5 predecessor tickets in this same batch
(`stored_artifacts/TCK-20260721-{ORCHESTRATION-CONTRACT-CORE,CLAUDE-CONFORMANCE-ADAPTER,
CODEX-GUIDANCE-FIXTURE-CAPTURE,MONITORING-WRITER-UNIFICATION,CODEX-REPLAY-PARITY}/investigation.md`,
each independently checked).

## Parity Ledger Overlap

None requiring an update. Checked all 8 `docs/parity_ledger/*.yaml` files. The one adjacent entry
is **INFRA-275** (`docs/parity_ledger/infrastructure.yaml:4478`, `status: verified`, `priority: P2`)
— it documents `MONITORING-WRITER-UNIFICATION`'s additive dashboard fields
(`provider`/`execution_id`/`ticket_id`/`identity_provenance` on `RunSummary`, plus `get_runs()`
filter kwargs). This ticket does not change that dashboard-ingest behavior and makes no `src/`
change of its own, so INFRA-275 does not need updating — but it is the direct documentary source
confirming those fields are schema-supported-but-not-yet-real-populated (see Current Behavior
above), useful context for whoever picks up Plan. No P0 entry anywhere references this ticket's
subsystem (agent-orchestration/Codex-pilot guardrail tooling is process infrastructure, outside the
parity ledger's simulation-mechanics domain, consistent with all 5 predecessor tickets' own
identical finding).

## Prior Work

All 5 hard predecessors are DONE with stored artifacts, detailed in Current Behavior above:
`TCK-20260721-ORCHESTRATION-CONTRACT-CORE`, `TCK-20260721-CLAUDE-CONFORMANCE-ADAPTER`,
`TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE`, `TCK-20260721-MONITORING-WRITER-UNIFICATION`,
`TCK-20260721-CODEX-REPLAY-PARITY`. Each established the repeated structural convention this ticket
should continue: a new, independent `tools/<name>/` package per ticket (most likely
`tools/agent_codex_pilot_guardrails/` or similarly named — not decided here, a Plan-phase naming
choice), never editing a predecessor's package in place; a local write-guard structurally refusing
writes outside an explicit allowed-target set; an explicit, flagged note whenever a cross-ticket
file edit is genuinely required.

`TCK-20260721-CODEX-REPLAY-PARITY`'s own Anti-Drift Hazards section (its stored investigation.md,
read in full) already anticipates this ticket by name: *"`TCK-20260721-LIVE-CODEX-PILOT-GUARDRAILS`
(next in `SEQUENCE.md`, not yet started) is the only ticket authorized to move toward a live pilot
— this ticket [CODEX-REPLAY-PARITY] must not preempt it."* Confirms this ticket is understood
batch-wide as the eventual (not immediate) live-pilot-authorizing ticket — consistent with the
Out-of-Scope reading above (this ticket builds the authorization *mechanism*, a future one actually
authorizes/executes).

No prior ticket has built any ticket-selection/rejection logic, a Codex-adapter enable/disable
flag, or a pre-live-execution human sign-off gate — this is genuinely new modeling work with no
existing structured source to lift from, beyond the mechanics precedents named above.

## Risks and Open Questions

1. **BLOCKING for Plan — does this ticket write a real `[[hooks.PostToolUse]]` block into the
   committed `.codex/config.toml`, or only build the toggle mechanism while keeping the committed
   config hook-free?** `.codex/config.toml`'s own comment names this ticket as owner of "actually
   wiring a production hook," but the ticket's own Out-of-Scope text forbids beginning live pilot
   execution. Writing a live hook registration into the committed config would make the adapter
   execution-capable — arguably a step toward, not itself, live execution, but a real ambiguity a
   literal reader could resolve either way. Recommend (not decided here, per this role's
   instruction not to assume): Plan should design the "single config/flag flip" as a toggle whose
   *disabled* state is what stays committed at this ticket's close (consistent with every other
   sibling ticket's "config stays hook-free" pattern), with the *enabled* state and its rollback
   drill exercised only against a scratch/test copy of the config — never flipped live in this
   ticket's own Implement phase. This must be an explicit, justified Plan decision, not a silent
   default.

2. **BLOCKING for Plan — where does "recorded human owner" and "rollback plan" structurally live?**
   Confirmed gap: no existing ticket field, no sidecar file convention, no `tools/
   ticket_field_values.py`-style validator for either concept exists today. Two options, both
   requiring new tooling: (a) a new structured ticket body field (parallel to `## Tier`/`##
   Status`), which would need a template change to `CLAUDE.md`'s Ticket Format section plus a new
   validator function; (b) a separate, ticket-id-keyed sidecar manifest (YAML/JSON) the selection
   step reads independently of the ticket file. Neither is implied by any doc read in this
   investigation. Whichever Plan picks, "verified against actual ticket/run state (not just doc
   convention)" (AC #1's own wording) rules out accepting unstructured prose as sufficient.

3. **BLOCKING for Plan — the "concurrent claim by both providers" check has no real signal to
   check against today.** Confirmed: real `agent-monitoring/runs.jsonl` records carry no `provider`
   field for any of the 5 sibling tickets' own runs (`.claude/workflows/implement-ticket.js` never
   constructs one). The schema *supports* the field via passthrough (proven only in isolated unit
   tests), but nothing in this repo's live workflow populates it. Plan must decide: (a) treat
   "provider" absence as implicitly "claude" (the only real writer today) and design the check to
   compare against a proxy for Codex-side claims (e.g., a not-yet-existing in-progress marker this
   ticket itself introduces for a pilot attempt) rather than a real historical `provider` field; or
   (b) explicitly scope a small, additive change so the live orchestrator actually starts
   populating `execution_id`/`provider`/`ticket_id` on real writes — which would arguably be
   `MONITORING-WRITER-UNIFICATION`'s or a new hotfix ticket's territory, not this ticket's, per the
   established one-ticket-one-package convention. Flagging, not assuming — this directly determines
   whether AC #1's second rejection rule is checkable against real data at all.

4. **AC #4's "hash changes" wording doesn't literally match `manifest.py`'s existing mechanism.**
   `assert_prefix_preserved` proves line-prefix-equality (rewrite/reorder/delete detection), not a
   single whole-file hash comparison; `build_manifest()` does compute a whole-file SHA-256 as a
   separate, coarser signal. Plan should state explicitly which of the two (or both) AC #4's "fails
   closed if any pre-existing line's hash changes" maps to, since a naive implementation could
   accidentally use only the coarser whole-file hash (which would fail to localize *which* line
   changed) or only the finer prefix check (which technically isn't a "hash," despite the AC's
   literal wording) without reconciling the vocabulary mismatch.

5. **Enabled-hook-event/writer-subset test needs a concrete "evidence" data source to enumerate
   against.** AC #3 requires "a test enumerates the enabled set as a subset of that evidence" —
   Current Behavior above identifies the maximal evidenced set (`PostToolUse` hook event;
   `write_line`/`write_lines` writer functions) by tracing through Phase 2/3's own artifacts, but no
   existing file declares this set in one machine-readable place. Plan must decide whether this
   ticket's own tooling is the first to formally enumerate it (e.g. a small constant/frozenset in
   the new package) or whether it should be sourced from an existing contract file
   (`agent-orchestration/hook-events.yaml`, confirmed to exist from `ORCHESTRATION-CONTRACT-CORE`
   but not yet read in this investigation for its exact schema — Plan should read it before
   deciding).

6. **Whether this ticket names or reserves a specific future pilot-candidate ticket is genuinely
   undecided by any source doc.** Confirmed (Current Behavior above) that no candidate is named
   anywhere. This investigation recommends the tooling stay ticket-agnostic (built to evaluate
   *any* candidate against the rejection rules) rather than hard-coding a specific ticket ID, since
   no doc identifies one and the ticket's own Scope describes a "step" (a reusable check), not a
   one-time selection event — but this is a reasonable inference, not a documented decision, and
   Plan should state it explicitly rather than silently assume it.

None of these block starting the Plan phase — they are exactly the kind of decisions this ticket's
own Scope/AC text implicitly defers to Plan, following the same pattern every predecessor
investigation in this batch used for its own open questions.

## Anti-Drift Hazards

- **Do not let this ticket begin live pilot execution in any form** — no real ticket gets actually
  worked by Codex under this ticket's own Implement phase; no real production hook fires against a
  real ticket; nothing this ticket builds may be exercised against a real, currently-open
  standard/hotfix ticket as a live trial run. This is the ticket's own explicit, doubly-stated
  boundary (Out of Scope + AC #7) and the single most safety-critical constraint in this entire
  7-ticket batch.
- **Do not silently flip `.codex/config.toml` to a hook-enabled state and leave it committed.**
  Per Risk #1, if Plan's design needs to exercise an "enabled" state for testing, that must happen
  against a scratch/tmp copy or be reverted before the ticket closes — mirroring every sibling
  ticket's own "config stays hook-free at close" invariant, verified today by
  `tests/agent_orchestration_claude_adapter/test_no_codex_scope_creep.py::
  test_no_production_hook_registered_in_codex_config` and
  `tests/agent_orchestration_codex_adapter/test_no_production_hook_enabled.py`, both of which this
  ticket's own tests must not regress.
- **Rollback logic must never delete output or modify historic JSONL records** — the ticket's own
  Out-of-Scope line is explicit ("only additive quarantine or reader-side exclusion; no
  data-repair-via-deletion mechanism"). A tempting shortcut for the "zero bytes differ" rollback
  test — e.g. truncating/rewriting a file to force equality — would violate this directly.
- **Do not re-implement `manifest.py`'s baseline-manifest tooling.** The ticket's own Out-of-Scope
  line says so explicitly; Current Behavior above confirms `capture_lines`/`assert_prefix_preserved`
  are already exactly fit-for-purpose and must be consumed, not forked.
- **Do not accept unstructured prose as "recorded human owner"/"rollback plan" evidence** — per
  Risk #2, AC #1's own wording explicitly rules this out; any implementation that merely
  greps ticket prose for the word "rollback" would fail to satisfy "verified against actual
  ticket/run state (not just doc convention)."
- **Do not claim the "concurrent claim by both providers" check works against real historical data
  without flagging the gap found in Risk #3.** A silently-passing test that only ever exercises
  synthetic/mocked `provider` values (because no real record has one) could look green while
  proving nothing about real pilot safety — Test Plan must include an explicit note about this
  limitation, not just a happy-path synthetic test.
- **Do not scope-creep into wiring `execution_id`/`provider`/`ticket_id` population into
  `.claude/workflows/implement-ticket.js`** — that would be a live-workflow behavior change well
  outside this ticket's own "guardrail/rollback/sign-off design-and-build" scope and belongs, if
  ever done, to a separately-scoped ticket (per the established one-ticket-one-concern convention
  this whole batch follows).
