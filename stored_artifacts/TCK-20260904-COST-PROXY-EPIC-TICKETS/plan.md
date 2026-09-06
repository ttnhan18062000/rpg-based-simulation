---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-COST-PROXY-EPIC-TICKETS
artifact_type: plan
tags: [ai, agent-monitoring]
---

# Implementation Plan — TCK-20260904-COST-PROXY-EPIC-TICKETS

## Summary

Add a `writeSidecar`-equivalent dual-write helper to `implement-epic.js` and `create-tickets.js`,
wire it at every real, top-level-sequential `agent()` call site in each file, and widen
`record_events.py::compute_tool_stats()`'s workflow filter to a membership check covering
`implement-ticket`/`implement-epic`/`create-tickets` (never `simq-audit`). This is a deliberate,
narrower-than-literal-ticket-scope implementation of the four open questions investigation.md
raised: (1) `create-tickets.js`'s `writeMonitoring` call (L131) is excluded, mirroring
`implement-ticket.js`'s own tested precedent; (2) the corrected site list is used (4 sites in
`implement-epic.js`, not 6; 7 locations in `create-tickets.js`, not 3); (3) `implement-epic.js`'s 2
fire-and-forget `bash()`-only early-return paths get no sidecar call at all — they will correctly
compute to `(0, 0.0)` once the filter widens, verified by a new test, not by new code; (4) the two
`create-tickets.js` fan-out sites (`investigate:${concern.id}` at L304, `write:${task.short_scope}`
at L659) are **excluded from sidecar coverage entirely** — confirmed via the `workflow-authoring`
skill's documented `pipeline()` semantics (up to `min(16, CPUs-2)` truly concurrent `agent()` calls,
no barrier between stages) combined with `post_tool_hook.py`'s sidecar design (one mutable
`.claude/current_run.<session_id>` file, shared by every `agent()` call in the same workflow run,
regardless of which pipeline item issued it) that a concurrent `writeSidecar(seq)`-then-`agent()`
pattern at these two sites would let a later fan-out iteration's sidecar write silently overwrite
an earlier iteration's still-in-flight attribution — a structural race, not a rare edge case, that
no per-item `seq` numbering scheme can fix without redesigning the sidecar mechanism itself (out of
scope; noted as a candidate future ticket). Net effect: `implement-epic.js` gets 4 covered sites
(L86, L287, L316, L353); `create-tickets.js` gets 4 covered sites (L156, L439, L796, L818) and 3
explicitly excluded (L131, L304, L659).

**Revision (architecture review, point 5):** `implement-epic.js`'s 4 sites all share one `run_id`
(`batchRunId`) with the pre-existing `batchEvents` array, which already occupies `seq = 1..N`
under that same `run_id` — a fixed positive `seq` (the original `1-4` draft) for the 4 new sites
collides with that range for realistic batch sizes. Step 1 below now uses a disjoint, monotonic
**negative** `seq` range (`-1..-4`, mirroring an existing precedent already documented at
`docs/agent-monitoring/schema.md:339` for a different sidecar-adjacent write path), hoists
`batchRunId`'s computation to before the Discover call (it was previously declared after that
call, out of scope for it), and gives `request`-mode's Discover call a provisional `run_id`
(`EPIC-REQUEST-<ts>`) since the real epic ticket ID does not exist until Discover itself returns.
See Step 1 for the full mechanics and a new Step 5 regression test proving the two `seq` ranges
cannot cross-contaminate.

## Steps

### Step 1 — Add dual-write sidecar helper to `implement-epic.js`, wire its 4 real sites (revised after architecture review — see the defect/fix writeup immediately below)

**Files:** `.claude/workflows/implement-epic.js`

**Confirmed defect in the prior draft of this step (architecture review, point 5):** the prior
draft's fixed `seq` values `1-4` for the 4 top-level sites collide with the pre-existing
`batchEvents` array (`implement-epic.js:277-283`, read in full — `batchEvents = results.map((r,
i) => ({seq: i + 1, phase: 'Implement', agent: 'implement-ticket', ...}))`), which already uses
`seq = 1..N` (one entry per child ticket in the batch) **under the exact same `run_id`**
(`batchRunId`, `implement-epic.js:272-274`: `epicId ? 'EPIC-' + epicId : 'FOLDER-' +
folder.replace(...)`). Since `batchEvents[0].seq` is always `1` for any batch with at least one
ticket, and `batchEvents` is written to `events.jsonl` via `record_events.py --data` inside the
`batch-monitoring-write` agent's own prompt (`implement-epic.js:294-296`), the prior draft's
`seq=1` for Discover would make `compute_tool_stats()`'s `wanted` set (built from `records` in
that exact `record_events.py` invocation, `record_events.py:56-60`, read in full) contain
`(batchRunId, 1)`, and `rows_by_key[(batchRunId, 1)]` would then be populated with **Discover's
own tool-call rows** (tagged via the sidecar before Discover's `agent()` call) — silently
inflating the *first child ticket's* batch-level event's `tool_call_count` with Discover's own
tool usage, not the first child ticket's. Prior draft's `seq=2/3/4` collide identically whenever
`N >= 2/3/4`. This is exactly the `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION` bug class
the exclusions elsewhere in this plan already guard against — the prior draft reintroduced it at
this one spot.

**Fix — disjoint negative `seq` range, mirroring an existing precedent already in this codebase:**
`docs/agent-monitoring/schema.md:339` documents that `implement-ticket.js`'s advisory
context-packet shadow-call site already uses "a monotonic **negative** counter... provably
disjoint from the real per-phase range (`>= 1`)" for exactly this reason (a write path that
bypasses the normal `pushEvent`/`events.length` counter needs a `seq` space that can never
alias onto the real one). Apply the identical pattern here: the 4 top-level sites get fixed
literal `seq` values **`-1, -2, -3, -4`** (in call order), which can never collide with
`batchEvents`' `seq = 1..N` range regardless of batch size, because `i + 1` for `i >= 0` is always
`>= 1` and the 4 new sites are always `<= -1`. **Do not use `seq=0`**: `post_tool_hook.py:124`
(`seq = sidecar.get("seq") or None`) treats `0` as falsy and silently converts it to `None`,
losing attribution entirely — confirmed by reading `post_tool_hook.py:96-131` in full. `-1` through
`-4` are all non-zero/truthy in this check, so this hazard does not apply to them.

**`run_id` scoping fix — hoist `batchRunId`'s computation before the Discover call, and give
`request` mode a provisional value:** `batchRunId` is declared at `implement-epic.js:272-274`,
*after* the Discover `agent()` call at line 86 — confirmed by direct read of the file: at line 86
neither `batchRunId` nor `discovery` (whose `.epic_ticket_path` request-mode needs) exists yet, so
no correct run_id was in scope for a sidecar write immediately before Discover fires. Two of
`batchRunId`'s three inputs (`folder`, `epicId`) are however already in scope from argument parsing
(`implement-epic.js:25-26`, before Discover ever runs) — only the third case (`request` mode, where
neither `folder` nor `epicId` is set) has no natural identifier before Discover returns, because
`request` mode's real identifier (`createdEpicId`, hence `epicCreatedRunId =
'EPIC-' + createdEpicId`, `implement-epic.js:186-187`) is derived from `discovery.epic_ticket_path`
— an epic ticket that Discover's own `agent()` call is what *creates* in this mode
(`implement-epic.js:148-164`'s prompt), so it cannot exist before that same call returns.

  Fix: hoist the `batchRunId` computation to immediately after `discoverTs` is captured
  (`implement-epic.js:85`, `const discoverTs = await captureTs()`) and before the Discover
  `agent()` call, extending its ternary to cover all 3 modes:
  ```js
  const batchRunId = folder
    ? 'FOLDER-' + folder.replace(/[^a-zA-Z0-9]/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '')
    : epicId
    ? 'EPIC-' + epicId
    : 'EPIC-REQUEST-' + (discoverTs || '').replace(/[^0-9]/g, '')
  ```
  The `folder`/`epic_id` branches are copied verbatim from the existing `implement-epic.js:272-274`
  formula (same sanitization), so both modes' 4 sidecar writes use the exact same value the file
  already treats as this batch's canonical identifier — no new run_id scheme is introduced for
  them, only an earlier computation of the same one. The `request`-mode branch mints a **provisional**
  identifier from the already-captured `discoverTs`, following the same `EPIC-<slug>-<ts-digits>`
  convention this file already uses for its `EPIC-INVALID-ARGS-<ts>` no-op path
  (`implement-epic.js:36`) — accepted as the same low-probability, pre-existing collision-risk class
  (two `request`-mode invocations starting in the same UTC second), not a new risk this step
  introduces.

  Then **delete** the now-duplicate `const batchRunId = ...` declaration at
  `implement-epic.js:272-274` (its old, later position) — the single hoisted declaration is the only
  definition, referenced unchanged by every existing later use (`batchEvents`, the
  `batch-monitoring-write`/`folder-cleanup`/`tracking-doc-update` prompts, and the `batch_run_id:
  batchRunId` field in the final `return` at `implement-epic.js:392`). This removes a
  formula-duplication risk (two independently-maintained copies of the same sanitization regex that
  must always agree) rather than introducing one.

  **Request-mode residual limitation (sub-issue #2), documented not silently accepted:** because
  `request` mode's sidecar write necessarily uses the provisional `EPIC-REQUEST-<ts>` value (the
  real `epicCreatedRunId` is unknowable before Discover returns), and the existing, **unchanged**
  `record_events.py`/`record_run.py` calls at `implement-epic.js:188-192` still key their one
  `events.jsonl` row to `epicCreatedRunId` (a *different* string from the provisional value) at
  `seq=1`, Discover's own real tool-call rows (tagged `(EPIC-REQUEST-<ts>, -1)` by the sidecar) will
  **not** retroactively join that row once the real epic ID becomes known — `compute_tool_stats()`
  will legitimately compute `(0, 0.0)` for `(epicCreatedRunId, 1)`, exactly like Step 2's already-
  accepted zero-tool-call precedent, not a new bug. This plan deliberately does **not** change
  `implement-epic.js:184-193` to reconcile the two run_ids (e.g. by making the final record use the
  provisional id instead) — doing so would sacrifice the real epic ticket ID's traceability in
  `events.jsonl` for a one-off, low-volume bootstrap path (creating a brand-new epic), which is a
  worse trade than accepting a `(0, 0.0)` result for this one path. This is a known, permanent,
  documented limitation of writing a sidecar before an identity is known — not something a future
  change should try to "fix" by touching Step 2's already-approved, untouched lines 184-227.

Add a `writeSidecar(seq, phase, agentName)` helper mirroring `implement-ticket.js`'s current
helper at `implement-ticket.js:274-285` (read and confirmed verbatim during investigation —
dual-write shape: unscoped `.claude/current_run` AND session-scoped
`.claude/current_run.<CLAUDE_CODE_SESSION_ID>`, argv-quoted (not JSON-embedded), fail-open with
`2>/dev/null || true`), with one structural difference from that file's version: like
`implement-ticket.js`'s helper closes over its file-scoped `tid` constant rather than taking
`run_id` as a parameter (confirmed by reading `implement-ticket.js:274-285` — `sys.argv[1]` is
bound to `"${tid}"`, not a parameter), this file's helper closes over the hoisted `batchRunId`
constant instead of taking `run_id` as a parameter — safe here specifically because, unlike a
per-child value, `batchRunId` is a single, unchanging value for the entire script execution (all 4
real sites read it after the same one assignment; `request` mode only ever reaches the first site
before returning, so the closure is never read stale). **Scope narrowing on the helper's shape**:
omit the `execution_id`/`provider` fields present in `implement-ticket.js`'s current 6-arg helper
(added later by `TCK-20260730-CLAUDE-EXECUTION-IDENTITY`, a separate, unrelated feature this
ticket does not extend to these 2 workflows) — pass only `run_id` (closed-over `batchRunId`),
`seq`, `phase`, `agent` to the `python3 -c` argv. This is safe: `post_tool_hook.py:127-128` reads
`execution_id`/`provider` via `sidecar.get("execution_id") or None` / `sidecar.get("provider") or
None`, which tolerates the keys being absent entirely (verified by reading
`post_tool_hook.py:96-131`).

Place `batchRunId`'s hoisted declaration, then the `writeSidecar` helper, immediately after
`discoverTs` is captured (`implement-epic.js:85`) and before the Discover `agent()` call. Then
insert one `await writeSidecar(seq, phase, agentLabel)` call immediately before each of the file's
4 real `agent()` call sites (line numbers as currently confirmed by direct `grep -n "agent("` read
of the file, not the ticket's own wrong 6/796/818 citations):
- `implement-epic.js:86` — `discovery = await agent(...)`, label `'discover'`, phase `'Discover'`.
  `seq=-1`. Fires in all 3 modes (`folder`/`epic_id`/`request`) since this is the one shared call
  site.
- `implement-epic.js:287` — `batch-monitoring-write`, phase `'Implement'` (the last `phase(...)`
  marker called before this point is `phase('Implement')` at `implement-epic.js:233`; `Report`
  isn't declared until line 339, after this site). `seq=-2`. Only reached in `folder`/`epic_id`
  modes (`request` mode returns at `implement-epic.js:194-199`, before this code is reached, so
  `batchRunId` is guaranteed non-provisional here).
- `implement-epic.js:316` — `folder-cleanup`, phase `'Implement'` (same reasoning — still before
  `phase('Report')`), conditional on `batchStatus === 'DONE' && folder`. `seq=-3`. `folder`-mode
  only (guarded by `&& folder`).
- `implement-epic.js:353` — `tracking-doc-update`, phase `'Report'` (`phase('Report')` was called
  at line 339, before this site), conditional on `discovery.mode === 'folder' &&
  discovery.tracking_doc`. `seq=-4`. `folder`-mode only.

Use fixed literal `seq` values (`-1` to `-4`), not `events.length + 1`, because — unlike
`implement-ticket.js` — `implement-epic.js` has no `events`/`pushEvent` array of its own; its
`batchEvents` array (built at `implement-epic.js:277-283`) is a separate, per-child-ticket list
written directly via the `batch-monitoring-write` `agent()` prompt, not via a local `pushEvent`
counter. Confirmed by reading the full file: no `pushEvent`/`events.push` pattern exists in
`implement-epic.js` today; only `batchEvents`.

**Expectation to set explicitly (so Verify does not mistake this for a gap):** none of these 4
sites' own tool-call rows (tagged `(batchRunId, -1..-4)`) currently have a matching `events.jsonl`
record to join to, because this plan does not add a `pushEvent`-equivalent write for Discover/
batch-monitoring-write/folder-cleanup/tracking-doc-update themselves (only `batchEvents`,
`epicCreatedRunId`'s one record, and `nothingRunId`'s one record are ever written to `events.jsonl`
for this workflow, and none of those changes in this plan). These 4 sites' negative-seq
`tools.jsonl` rows are therefore expected to remain permanently unjoined/orphaned — harmless, and
not a regression, since `compute_tool_stats()` only ever computes stats for `(run_id, seq)` pairs
that actually appear in the `records` passed to a given `record_events.py --data` invocation
(`record_events.py:56-60`, read in full). **The real, load-bearing purpose of these 4 writes is
not to make Discover's own count visible — it is to stop these 4 bookkeeping `agent()` calls from
inheriting and polluting whatever `(run_id, seq)` the sidecar was last set to** (in `folder`/
`epic_id` mode, that is very often the *last child ticket's own* `(tid, seq)` from the nested
`workflow('implement-ticket', ...)` loop at `implement-epic.js:239-268`, which just finished
immediately before `batch-monitoring-write` fires at line 287) — exactly the
`TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION` bug class, now prevented by redirecting the
sidecar to `batchRunId` before each of these 4 calls, adding a new test (Step 5) that proves this
redirection actually happens.

**Other writers to `.claude/current_run`/`.claude/current_run.<session>`, and to the
`(batchRunId, seq)` key-space specifically, this step interacts with** (enumerated per
fact-verification requirement #2):
- `implement-ticket.js`'s `writeSidecar()` (11 call sites, `implement-ticket.js:274-285` + its call
  sites) and its Scope-phase resume branch (`implement-ticket.js` lines around `170-183`, inlined
  bash) write the same file convention, keyed to the *child ticket's own* `tid`, never to
  `batchRunId` — no key-space overlap, but **temporal** overlap matters: as noted above, the
  sidecar is still holding the last-run child ticket's `(tid, seq)` at the moment
  `batch-monitoring-write` (`implement-epic.js:287`) fires, which is precisely the misattribution
  this step's `writeSidecar(-2, ...)` call prevents by overwriting it first.
- The pre-existing `batchEvents` array (`implement-epic.js:277-283`, this same file) writes `N`
  records with `seq = 1..N` under this identical `batchRunId` — the disjoint negative range chosen
  above (`-1..-4`) is specifically sized to never collide with this regardless of `N`; verified by a
  dedicated regression test (Step 5).
- The `nothingRunId` (`implement-epic.js:211-227`, Step 2, untouched) and `invalidRunId`
  (`implement-epic.js:36-39`, untouched, out of this ticket's scope entirely) direct-`bash()` paths
  independently recompute the identical `EPIC-`/`FOLDER-` formula for a `run_id` that happens to
  equal `batchRunId`'s value in `folder`/`epic_id` mode — but both are mutually exclusive at
  runtime with the code this step touches (they each `return` before reaching the Discover-onward
  code path this step modifies further, for `nothingRunId`) or fire on a fully separate early-exit
  branch (`invalidRunId`, before Discover ever runs) — no runtime concurrency or seq-range overlap
  with this step's 4 sites.
- `tools/retrieval_cache.py::read_current_run_sidecar()` only reads the sidecar (not a writer) — it
  will now see real `implement-epic` attribution during these runs instead of a stale foreign
  session's data or the ADHOC-NULL sentinel; benign side effect, not a regression.
- `.claude/settings.json`'s inline PreToolUse "sidecar-check" hook (settings.json:88) only reads the
  **unscoped** file's `run_id` to nudge about hand-orchestrated `implement-ticket.js` runs — writing
  a real `implement-epic` run_id there during an epic run does not break that hook (it only warns
  when `run_id` is empty), and this pre-existing unscoped-file cross-session-sharing caveat is
  already documented and accepted (`TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`'s own "kept for ...
  deferred rather than migrated" note) — not something this ticket needs to fix.

**Do NOT touch:** `implement-epic.js:184-193` and `implement-epic.js:209-219` (the 2
fire-and-forget `bash()`-only early-return paths, and their `seq=1` literals — see Step 2 and the
request-mode residual-limitation note above). Do not add a `pushEvent`/`events` array to this
file — out of scope; `batchEvents` stays exactly as-is, including its own `seq = 1..N` numbering.
Do not touch the nested `workflow('implement-ticket', ...)` loop (`implement-epic.js:239-268`). Do
not change `batchEvents`' own `seq` numbering to try to "make room" for the new sites — the fix is
the new sites moving to negative `seq`, not renumbering the pre-existing positive range.

**Verify:** New architecture-guard test (Step 5) asserting `writeSidecar(...)` immediately
precedes each of the 4 `agent(` calls; a second test asserting the helper's body performs the
dual-write (mirrors `test_write_sidecar_also_writes_session_scoped_copy`'s exact assertion shape
from `tests/tools/test_current_run_sidecar_orchestrator.py:465-478`, applied to the new helper);
and the new full-batch collision-regression test described in Step 5's updated list below.

---

### Step 2 — Confirm implement-epic.js's 2 fire-and-forget sites need no code change

**Files:** none (test-only; see Step 5)

**Change:** No production code change. `implement-epic.js:184-193` (`request` mode, "Discover ran
and created a real ticket") and `implement-epic.js:209-219` (`ticketIds.length === 0`, "Discover
found no tickets to implement") both write a single hardcoded `seq:1` event via direct `bash()`
(never `agent()`) and then `return` — confirmed by direct read of the file: no `agent()` call
follows either `bash()` write on either path, so there is no `(run_id, seq)` tool-call group to
attribute in the first place. Once Step 4's filter widens, `compute_tool_stats()`'s existing
unconditional-entry-per-wanted-key behavior (`record_events.py:74`:
`{key: (len(rows_by_key[key]), ...) for key in wanted}`) will legitimately return `(0, 0.0)` for
these two `EPIC-`/`FOLDER-` `run_id`, `seq=1` records — correct because they genuinely made zero
tracked tool calls, not an artifact of a missing sidecar write.

**Do NOT touch:** Do not wrap `implement-epic.js:184-193`/`209-219` in an `agent()` call just to
give them sidecar coverage — this would be an unscoped behavior change to code paths that
currently work correctly and terminate the workflow immediately (explicit Anti-Drift Test Guard
from test_plan.md).

**Verify:** New test `test_zero_tool_call_no_sidecar_paths_compute_zero_not_null` (Step 5) —
an `EPIC-...`/`FOLDER-...` record at `seq=1` with no matching `tools.jsonl` rows computes to
`(0, 0.0)`, not an omitted key.

---

### Step 3 — Add dual-write sidecar helper to `create-tickets.js`, wire its 4 coverable sites; explicitly exclude 3

**Files:** `.claude/workflows/create-tickets.js`

**Change:** Add the same 4-arg `writeSidecar(seq, phase, agentName)` helper (same dual-write
shape as Step 1, adapted to this file's own `pushEvent`-based `seq` numbering — `events.length + 1`
mirrors `implement-ticket.js`'s own convention, since `create-tickets.js` already maintains an
`events` array via `pushEvent` at `create-tickets.js:104-114`). Place it immediately after
`pushEvent`'s definition (`create-tickets.js:104-114`) and before `writeMonitoring`'s definition
(`create-tickets.js:127-153`), matching `test_writeSidecar_defined_once_after_pushEvent_before_classifyChecklistFailure`'s
ordering convention from the `implement-ticket.js` precedent (`test_current_run_sidecar_orchestrator.py:239-245`).

Wire `await writeSidecar(events.length + 1, phase, agentLabel)` immediately before each of these 4
call sites (confirmed real, top-level-sequential — never inside `pipeline()`/`parallel()`):
- `create-tickets.js:156` — `comprehension = await agent(...)`, label `'comprehend'`.
- `create-tickets.js:439` — `structured = await agent(...)`, label `'structure'`.
- `create-tickets.js:796` — write-sequence `await agent(...)`, label `'write-sequence'`,
  conditional on `hasIntraDeps`.
- `create-tickets.js:818` — `linkResult = await agent(...)`, label `'link-epic'`, conditional on
  `epicId && ticketIds.length > 0`.

**Explicitly excluded — do NOT add `writeSidecar()` at these 3 locations, and add a code comment
at each documenting why:**
- **`create-tickets.js:131`** (`writeMonitoring`'s own `agent()` call, label `'monitoring-write'`).
  Directly parallels `implement-ticket.js`'s own `writeMonitoring` call, which is deliberately,
  permanently excluded and test-enforced
  (`tests/tools/test_current_run_sidecar_orchestrator.py::test_writeMonitoring_call_has_no_preceding_sidecar_write`,
  read in full — asserts `"writeSidecar(" not in monitoring_write_region`, and the module
  docstring at `test_current_run_sidecar_orchestrator.py:24-28` states this is permanent by
  design). Adding coverage here would reintroduce the exact attribution-inflation pattern
  `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION` fixed (a bookkeeping call's own tool calls
  silently attributed to whatever sidecar state was last set by the phase immediately preceding
  it). **Resolution of Open Question #1: excluded**, mirroring the `implement-ticket.js` precedent
  exactly — this is a deliberate scope narrowing from the ticket's literal Scope bullet, which
  listed line 131 as one of the "9 call sites" without noticing this architectural conflict.
- **`create-tickets.js:304`** (`investigate:${concern.id}` inside `pipeline(comprehension.concerns,
  (concern) => agent(...))`) and **`create-tickets.js:659`** (`write:${task.short_scope}` inside
  `pipeline(tasksReadyToWrite, (task) => agent(...))`). **Resolution of Open Question #4,
  concretely evidenced, not hand-waved:** the `workflow-authoring` skill's own documentation of
  `pipeline()`'s semantics states it runs items through stages "independently, NO barrier between
  stages" and that "Concurrent agent() calls are capped at min(16, available CPUs - 2) per
  workflow — excess calls queue and run as slots free up" — i.e. up to 16 of these two sites'
  `agent()` calls can be genuinely in flight at once for any batch with 2+ concerns/tickets (the
  common case, not an edge case). Cross-referenced against `post_tool_hook.py:96-131` (read in
  full): the sidecar is a **single mutable file per `session_id`**
  (`.claude/current_run.<session_id>`), shared by every `agent()` call made within the *same*
  workflow-script session — not scoped per individual `agent()` invocation or subagent. A naive
  `writeSidecar(seq)`-then-`agent()` pattern at a fan-out site would let iteration B's
  `writeSidecar()` call overwrite the shared sidecar file while iteration A's subagent is still
  mid-flight making its own tool calls, silently misattributing A's remaining tool calls to B's
  `seq` — this is a structural race in the existing single-writer sidecar design, not fixable by
  choosing distinct per-item `seq` values (the collision is on the shared file's "currently active"
  pointer, not on `seq` uniqueness). No safe design exists within the current sidecar mechanism for
  concurrent fan-out; a real fix would require redesigning `post_tool_hook.py`'s attribution key
  (e.g. per-invocation-scoped files keyed by something other than `session_id`) — an architectural
  change to the shared tool-call-attribution mechanism itself, well beyond "wire two more
  workflows into the existing mechanism," and explicitly deferred as a candidate future ticket, not
  implemented here (per CLAUDE.md: adjacent problems become future tickets, not scope creep on this
  one). **These two sites get zero code change in this ticket.**

**Other writers to `.claude/current_run`/`.claude/current_run.<session>` this step interacts with**
(same enumeration as Step 1): `implement-ticket.js`'s 11 `writeSidecar()` sites and Scope-resume
branch are unaffected (`create-tickets.js` never invokes `implement-ticket.js` or shares a run).
`tools/retrieval_cache.py`'s reader benefits the same way as Step 1. The unscoped-file
cross-session-sharing caveat is unchanged/pre-existing.

**Do NOT touch:** `create-tickets.js:131`, `:304`, `:659` (excluded above — no `writeSidecar()`
call, no restructuring of `pipeline(...)` itself, no change to `pushEvent` call sites at
`create-tickets.js:329`/`:544`/`:613`/`:718`/`:722`/`:835`). Do not change the `pipeline(...)`
concurrency cap or add a `phase: 'Investigate'`/`phase: 'Write'` option to these `agent()` calls
beyond what already exists.

**Verify:** New architecture-guard tests (Step 5): adjacency assertion for the 4 covered sites;
absence assertion (with a documenting comment) for the 3 excluded sites; dual-write assertion for
the new helper.

---

### Step 4 — Widen `record_events.py::compute_tool_stats()`'s workflow filter

**Files:** `tools/agent-monitoring/record_events.py`

**Change:** At `record_events.py:59`, replace:
```python
if infer_workflow(r.get("run_id", "")) == "implement-ticket" and r.get("seq") is not None
```
with a membership check:
```python
if infer_workflow(r.get("run_id", "")) in {"implement-ticket", "implement-epic", "create-tickets"} and r.get("seq") is not None
```
`infer_workflow()` (`tools/agent-monitoring/vocabulary.py:80-101`, read in full) already
recognizes `'EPIC-'`/`'FOLDER-'` → `'implement-epic'` and `'CREATE-TICKETS-'` → `'create-tickets'`,
disjoint from `'SIMQ-AUDIT-'` → `'simq-audit'` — no change needed to `vocabulary.py` itself (ticket
Out-of-Scope respects this; `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` stay untouched). Also update the
function's docstring (`record_events.py:34-55`, read in full) to drop the now-false claim "that's
the only workflow whose Scope-through-Finalize call sites write a live .claude/current_run
sidecar" and "implement-epic/create-tickets never register a sidecar per agent call, so their
tool_call_count/cost_proxy_score stay absent, as documented" — replace with a description of the
new partial-coverage state (which sites are covered vs. excluded in each of the 3 files, citing
this plan's Step 1/3 site lists) and the explicit exclusion of `simq-audit`.

**Other writers to this shared function/resource** (enumerated per fact-verification requirement
#2): `compute_tool_stats()` has exactly one call site, inside this same file's `main()`
(`record_events.py:142`) — no other module calls it. The function reads
`agent-monitoring/data/*/tools.jsonl` (`record_events.py:65`), whose only writer is
`post_tool_hook.py` (a global PostToolUse hook firing for every tool call across every session and
workflow, including `simq-audit`'s — unaffected by this filter widening, since `simq-audit`
records are still excluded from `wanted` and therefore never looked up). `main()`'s
caller-override behavior at `record_events.py:142-147` (`if key in tool_stats: ... overrides
records[i]`) is unchanged — it will now also fire for `implement-epic`/`create-tickets` records
whose `(run_id, seq)` matches something in the newly-widened `wanted` set, exactly mirroring the
existing `implement-ticket` override behavior (satisfies the ticket's Out-of-Scope: "must extend
that rule identically to the two newly-covered workflows, not change it").

**Do NOT touch:** `tools/agent-monitoring/cost_proxy.py`'s formula/weights (explicit ticket
Out-of-Scope — `tests/tools/test_cost_proxy.py` must stay 100% unmodified and passing).
`vocabulary.py`'s `WORKFLOW_PHASES`/`WORKFLOW_AGENTS`. `record_run.py`'s `compute_duration_s`
(unrelated, cited only as a design precedent). Do not change the multi-week-glob logic
(`record_events.py:65`, `TCK-20260903-MONITORING-DATA-WRITE-PATH-UNIFY`, unrelated to this ticket).

**Verify:** `test_compute_tool_stats_targets_implement_ticket_implement_epic_and_create_tickets`
and `test_implement_epic_and_create_tickets_records_now_computed_from_real_tools_jsonl` (Step 5).

---

### Step 5 — Update/rename existing tests; add new tests

**Files:** `tests/tools/test_record_events.py`, new file
`tests/tools/test_epic_create_tickets_sidecar_orchestrator.py`

**Change:**

1. **Rename and rewrite** `test_implement_epic_and_create_tickets_records_unaffected_no_sidecar`
   (currently `test_record_events.py:249-261`, read in full — currently asserts `stats == {}`)
   → **`test_implement_epic_and_create_tickets_records_now_computed_from_real_tools_jsonl`**. New
   body: use `_write_tools_jsonl` (helper at `test_record_events.py:188-193`) to seed real
   `tools.jsonl` rows for an `EPIC-...`, a `FOLDER-...`, and a `CREATE-TICKETS-...` `run_id` each at
   a distinct `(run_id, seq)`, then assert `compute_tool_stats()` returns the correct non-null
   `(tool_call_count, cost_proxy_score)` tuple for each — mirroring
   `test_cost_proxy_score_and_tool_call_count_computed_from_real_tools_jsonl_not_passthrough`'s
   existing fixture pattern (`test_record_events.py:196-` ff.) applied to the 3 newly-included
   run_id prefixes. Docstring must state explicitly this reverses
   `TCK-20260719-COST-PROXY-WRITE-PATH`'s prior exclusion, and why (a scope-discipline decision for
   a narrowly-framed bug-fix ticket, not a technical constraint — investigation.md's Prior Work
   section, confirmed by reading `TCK-20260719-COST-PROXY-WRITE-PATH` in full).

2. **Rename and rewrite** `test_compute_tool_stats_only_targets_implement_ticket_workflow`
   (currently `test_record_events.py:264-276`, read in full) →
   **`test_compute_tool_stats_targets_implement_ticket_implement_epic_and_create_tickets`**. New
   body: a 4-way batch — one `TCK-...`, one `EPIC-...`, one `CREATE-TICKETS-...` record each with a
   matching `tools.jsonl` fixture row at a distinct `(run_id, seq)` (proving no cross-bucket
   leakage — satisfies the Acceptance Criteria's mixed-batch independence requirement in the same
   test, per test_plan.md item 6, rather than as a separate test), plus one `SIMQ-AUDIT-...` record
   with its own `tools.jsonl` fixture row. Assert the first 3 compute correct non-null tuples and
   the `SIMQ-AUDIT-...` key is **absent from the result dict entirely** (not `None`, not `(0,
   0.0)`) — proves the filter is a membership check against exactly `{implement-ticket,
   implement-epic, create-tickets}`, not "any known workflow."

3. **New test** `test_zero_tool_call_no_sidecar_paths_compute_zero_not_null` (per Step 2): an
   `EPIC-...`/`FOLDER-...` record at `seq: 1` with **no** matching `tools.jsonl` rows computes to
   `(0, 0.0)`.

3b. **New test** `test_batch_top_level_negative_seq_and_child_ticket_positive_seq_do_not_cross_contaminate`
   (in `test_record_events.py`, alongside `test_compute_tool_stats_only_targets_...` above — added
   specifically to reproduce and pin the Step 1 collision fix; per fact-verification requirement
   #3, this is the concrete AC-facing proof that "a mixed-batch test confirms
   implement-ticket/implement-epic/create-tickets buckets compute independently without
   cross-contamination" extends to intra-`implement-epic` contamination too, not just
   cross-workflow). Full-batch reproduction, using `_write_tools_jsonl` (test_record_events.py:
   188-193) and `compute_tool_stats()` directly (no JS execution needed — this is a Python-level
   proof of the key-space property the JS change relies on):
   - Pick one `run_id`, e.g. `"EPIC-TCK-BATCH-COLLISION-TEST"`.
   - Seed `tools.jsonl` rows: 2 rows at `seq=-1` (simulating Discover's own tool calls), 1 row at
     `seq=-2` (simulating batch-monitoring-write's own tool calls), 1 row at `seq=1` (simulating a
     row that would exist at the first child ticket's `batchEvents` slot — included specifically so
     the test proves independence in both directions, not just "negative seq is untouched"), and
     **no** row at `seq=2` (a second child ticket slot with genuinely zero tool calls).
   - Build `records` = `[{...VALID_EVENT, run_id, seq: 1}, {...VALID_EVENT, run_id, seq: 2},
     {...VALID_EVENT, run_id, seq: -1}, {...VALID_EVENT, run_id, seq: -2}]` (the first two shaped
     like `batchEvents` entries; the last two shaped like a hypothetical future events.jsonl
     record for the top-level phase sites — included to exercise `compute_tool_stats()`'s
     per-key exactness generically, even though Step 1 does not currently make `implement-epic.js`
     write events.jsonl records for the negative-seq sites themselves, per Step 1's "Expectation to
     set explicitly" note).
   - Call `compute_tool_stats(records)` and assert all four keys are present and exact:
     `(run_id, 1)` has `tool_call_count == 1` (only its own row, not seq=-1's 2 rows or seq=-2's 1
     row); `(run_id, 2)` == `(0, 0.0)` (genuinely zero, not leaking seq=-2's row); `(run_id, -1)`
     has `tool_call_count == 2` (only its own rows); `(run_id, -2)` has `tool_call_count == 1`
     (only its own row). `cost_proxy_score` values asserted against the real
     `compute_cost_proxy_score()` formula for each bucket's exact row set (same hand-computation
     approach as `test_cost_proxy_score_and_tool_call_count_computed_from_real_tools_jsonl_not_passthrough`,
     `test_record_events.py:196-227`), not hardcoded/guessed numbers.

4. **New file** `tests/tools/test_epic_create_tickets_sidecar_orchestrator.py` (mirrors
   `test_current_run_sidecar_orchestrator.py`'s established static-source-text-parsing pattern,
   applied to the 2 newly-touched `.js` files instead of scattering these assertions into
   unrelated files):
   - Architecture guard: `create-tickets.js`'s `writeMonitoring` region (same slicing technique as
     `test_writeMonitoring_call_has_no_preceding_sidecar_write`,
     `test_current_run_sidecar_orchestrator.py:145-151`) contains no `writeSidecar(`.
   - Architecture guard: each of `implement-epic.js`'s 4 covered sites (L86, L287, L316, L353) and
     `create-tickets.js`'s 4 covered sites (L156, L439, L796, L818) has its
     `writeSidecar(...)` call immediately preceding the paired `agent(` call — same adjacency-string
     technique as `test_sidecar_bash_write_precedes_each_covered_agent_call`.
   - Architecture guard, specific to Step 1's collision fix: each of `implement-epic.js`'s 4
     `writeSidecar(...)` calls uses one of the literal `seq` values `-1`, `-2`, `-3`, `-4` (in that
     order, one per site) — asserted by parsing the exact call text at each site, not just checking
     adjacency — so a future edit cannot silently revert to a positive/colliding value without this
     test failing. A companion assertion confirms `implement-epic.js` has exactly one
     `const batchRunId = ` declaration (not two), positioned before the Discover `agent(` call and
     after `discoverTs`'s assignment — guards against the deleted-duplicate-declaration step (Step
     1) silently regressing back to two independently-maintained copies of the same formula.
   - Architecture guard, with an explicit assertion + comment documenting the concurrency
     rationale (not silent): `create-tickets.js`'s `investigate:${concern.id}` and
     `write:${task.short_scope}` `agent()` call regions inside their respective `pipeline(...)`
     callbacks contain no `writeSidecar(`.
   - Architecture guard: `implement-epic.js:184-193`/`:209-219` regions still use direct `bash()`
     only — no `agent(` call introduced on either path.
   - Dual-write guard (both new helpers): each writes both `open('.claude/current_run', 'w')`
     and `open('.claude/current_run.' + sid, 'w')`, mirroring
     `test_write_sidecar_also_writes_session_scoped_copy` exactly.

**Do NOT touch:** `tests/tools/test_cost_proxy.py` (formula tests, out of scope).
`tests/tools/test_current_run_sidecar_orchestrator.py` (targets `implement-ticket.js` only — stays
green, untouched). `tests/tools/test_validate_agent_monitoring.py` (vocabulary single-source-of-truth
guard — unaffected, since `vocabulary.py` itself is untouched).

**Verify:** `.venv/bin/python3 -m pytest tests/tools/test_record_events.py
tests/tools/test_cost_proxy.py tests/tools/test_current_run_sidecar_orchestrator.py
tests/tools/test_validate_agent_monitoring.py
tests/tools/test_epic_create_tickets_sidecar_orchestrator.py -q` (per test_plan.md's Scoped Pytest
Commands — never the full `pytest tests/`).

---

### Step 6 — Update `docs/agent-monitoring/schema.md`

**Files:** `docs/agent-monitoring/schema.md`

**Change:** Correct the 4 locations investigation.md identified as now actively misdescribing
behavior (not merely stale):
- **L180** (`tool_call_count` field description): remove "and for workflows that never register a
  `.claude/current_run` sidecar (`create-tickets`, `implement-epic`)" — replace with a description
  of the new partial-coverage state: computed for `implement-ticket` (all real sites),
  `implement-epic` (all 4 real sites), and `create-tickets` (4 of 7 real sites — `comprehend`,
  `structure`, `write-sequence`, `link-epic`; `monitoring-write`, and the 2 `pipeline()`-fan-out
  sites `investigate`/`write` per-item, are excluded and stay null/absent), still `null` for runs
  before this field existed.
- **L182** (`cost_proxy_score` field description): same correction — "for `implement-ticket`
  workflow records only" → "for `implement-ticket`, `implement-epic`, and `create-tickets`
  workflow records (see the `tool_call_count` row above for `create-tickets`'/`implement-epic`'s
  own partial-coverage caveat)."
- **L289** (`### phase values (create-tickets workflow)`): the sentence "Neither `create-tickets`
  nor `implement-epic` registers a `.claude/current_run` sidecar per agent call (neither ever
  has)..." is now false. Replace with: which of the 5 `create-tickets` phases get real
  `tool_call_count` coverage (`Comprehend`, `Structure`, and — when they fire —
  `write-sequence`/`Link`) and which don't (`Investigate` and `Write`, both `pipeline()` fan-outs,
  excluded for the concurrency reason in Step 3), citing this ticket.
- **~L424 area** (`### How tool calls are attributed to agent events`): add a paragraph describing
  the new `implement-epic.js`/`create-tickets.js` `writeSidecar` helpers, their dual-write shape,
  and the 3 explicit `create-tickets.js` exclusions (`monitoring-write`, `investigate:`, `write:`)
  with the concurrency rationale, mirroring how this section already documents
  `implement-ticket.js`'s own `writeMonitoring` exclusion (`schema.md:444`).

Also verify (no change expected, confirmed by reading the file) that `docs/agent-monitoring/schema.md:291-294`
(`### phase values (implement-epic workflow)`) needs **no** change — it describes `events.jsonl`
phase-tagged records (all still `phase: 'Implement'`, one per child ticket, via
`batch-monitoring-write`'s own prompt-constructed events), which this ticket does not alter.

**Do NOT touch:** `docs/parity_ledger/infrastructure.yaml`'s `INFRA-282` entry — investigation.md
flags this as a likely target for the **Parity phase** (`parity-updater`), not for this plan;
implementing it here would preempt that phase's own review of the ticket's final shipped diff.

**Verify:** No automated test currently pins these doc line numbers besides
`test_schema_doc_no_longer_describes_agent_self_report_mechanism` (already-passing, targets
different text, in `test_current_run_sidecar_orchestrator.py`) — manual review during Verify phase
that the corrected prose matches the shipped code exactly (per CLAUDE.md's Parity rule: docs and
code must remain in semantic parity).

---

### Step 7 — Real-run acceptance verification (not a pytest)

**Files:** none (operational verification)

**Change:** Per the ticket's Acceptance Criteria (which are explicitly framed as "a real ... run",
not a unit test), after Steps 1-6 land: trigger one real `implement-epic` run and one real
`create-tickets` run (or confirm via the next natural such runs during this ticket's own closure,
since this ticket itself will be closed via `implement-ticket.js`, not `implement-epic`/
`create-tickets` — a genuinely separate real run of each of those two workflows is needed
elsewhere, e.g. the next batch ticket implementation or ticket-creation task) and inspect the
resulting `agent-monitoring/data/<week>/events.jsonl` rows for the covered phases
(`discover`/`batch-monitoring-write`/etc. for implement-epic; `comprehend`/`structure`/etc. for
create-tickets) to confirm non-null `tool_call_count`/`cost_proxy_score` matching the real
`(run_id, seq)`-grouped `tools.jsonl` rows for those same phases.

**Do NOT touch:** Do not write a backfill script for historical rows (explicit Out of Scope) —
only forward runs after this ships are expected to show non-null values.

**Verify:** Direct inspection of `events.jsonl`/`tools.jsonl` rows from the real run(s), per AC1/AC2.

## Scope Guards

- Do not add `writeSidecar()` coverage to `create-tickets.js:131` (`writeMonitoring`) — mirrors the
  `implement-ticket.js` precedent exactly (Step 3).
- Do not add `writeSidecar()` coverage to `create-tickets.js:304`/`:659` (the 2 `pipeline()`
  fan-out sites) — concurrency-unsafe with the existing sidecar mechanism, confirmed via
  `workflow-authoring` skill + `post_tool_hook.py` reading (Step 3).
- Do not wrap `implement-epic.js:184-193`/`:209-219` in an `agent()` call — they stay pure `bash()`
  early returns (Step 2).
- Do not touch `tools/agent-monitoring/cost_proxy.py`'s formula or weights.
- Do not touch `tools/agent-monitoring/vocabulary.py`'s `WORKFLOW_PHASES`/`WORKFLOW_AGENTS`.
- Do not change `record_events.py`'s "always overrides caller-supplied value" rule — only extend
  which `run_id` prefixes it applies to.
- Do not write a historical backfill script for already-written null `implement-epic`/
  `create-tickets` event rows.
- Do not implement `docs/parity_ledger/infrastructure.yaml`'s `INFRA-282` update in this plan —
  flagged for the Parity phase.
- Do not add `execution_id`/`provider` identity tracking to `implement-epic.js`/`create-tickets.js`
  — out of scope (`TCK-20260730-CLAUDE-EXECUTION-IDENTITY` territory, a separate feature).
- Do not modify `implement-ticket.js` itself — this ticket only adds analogous machinery to the
  other 2 workflow files and widens `record_events.py`'s filter.

## Dependency Map

- Steps 1, 2, 3 are independent of each other (different files/regions) and can be implemented in
  any order, but all three must land before Step 4 is meaningfully testable (Step 4's widened
  filter has no visible effect without Steps 1/3's sidecar coverage, per investigation.md's
  Assumptions: "shipping either alone produces no visible effect").
- Step 4 depends on Steps 1 and 3 being complete (needs real sidecar-covered sites to compute
  non-null values against).
- Step 5's tests depend on Steps 1, 3, and 4 all being implemented (tests assert the shipped
  behavior of all three).
- Step 6 (docs) depends on Steps 1-4 being finalized (describes the actual shipped site list).
- Step 7 depends on all prior steps and must happen after code lands.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| A real `implement-epic` run's `events.jsonl` rows have non-null `tool_call_count`/`cost_proxy_score` matching real `(run_id,seq)`-grouped `tools.jsonl` rows | Steps 1, 4 | `test_compute_tool_stats_targets_implement_ticket_implement_epic_and_create_tickets`, `test_implement_epic_and_create_tickets_records_now_computed_from_real_tools_jsonl` (Step 5); real-run check (Step 7). **Caveat, not a gap**: the `events.jsonl` rows that satisfy this AC for `implement-epic` are `batchEvents`' pre-existing per-child-ticket rows (`seq=1..N`) computing to real or `(0, 0.0)` values once Step 4's filter widens — "non-null" is satisfied literally (`0`/`0.0` are non-null), not by the 4 new negative-`seq` sites gaining their own `events.jsonl` rows (they deliberately do not, per Step 1's "Expectation to set explicitly" note) |
| A real `create-tickets` run likewise produces non-null values | Steps 3, 4 | Same 2 tests (Step 5); real-run check (Step 7) |
| `test_implement_epic_and_create_tickets_records_unaffected_no_sidecar` is updated (not left contradicting) to assert non-null values with a corrected docstring | Step 5 (rename #1) | The renamed test itself, `test_implement_epic_and_create_tickets_records_now_computed_from_real_tools_jsonl` |
| A mixed-batch test confirms implement-ticket/implement-epic/create-tickets buckets compute independently without cross-contamination | Step 5 (rename #2, and new test 3b) | `test_compute_tool_stats_targets_implement_ticket_implement_epic_and_create_tickets` (cross-workflow independence); `test_batch_top_level_negative_seq_and_child_ticket_positive_seq_do_not_cross_contaminate` (intra-`implement-epic` independence between the 4 new negative-`seq` sites and `batchEvents`' positive-`seq` range under the same `run_id` — the specific collision this plan's Step 1 revision fixes) |

## Anti-Drift Notes

- **`implement-epic.js`'s 4 top-level sidecar `seq` values must stay negative (`-1..-4`), never
  renumbered into the positive range.** They share `batchRunId` with the pre-existing `batchEvents`
  array (`implement-epic.js:277-283`), whose `seq = 1..N` grows with batch size and is otherwise
  unbounded — any positive value chosen for the 4 new sites collides for some batch size N, exactly
  reproducing the `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION` bug class (a prior draft of
  this plan made exactly this mistake with `seq=1..4`; architecture review caught it). The negative
  range is provably disjoint regardless of `N`; do not "reclaim" it or renumber `batchEvents` to
  make room instead — the fix is the new sites staying out of the positive range, not the reverse.
  Also never use `seq=0` for these sites (`post_tool_hook.py:124`'s `sidecar.get("seq") or None`
  silently drops it to `None`). The Step 5 architecture-guard test module pins the exact literal
  values (`-1`,`-2`,`-3`,`-4`) at each site, not just their adjacency to the paired `agent(` call.
- **`batchRunId` must be declared exactly once, hoisted before the Discover `agent()` call** — not
  twice (once early for the sidecar, once again at its old `implement-epic.js:272-274` position).
  Two independently-maintained copies of the same `EPIC-`/`FOLDER-` sanitization formula are a
  standing risk of silent drift between them; the hoisted single declaration is a correctness
  requirement, not a style preference — resurrecting the second copy could make the Discover-phase
  sidecar's `run_id` diverge from the one `batchEvents`/`batch-monitoring-write`/etc. use.
- **`request`-mode's Discover sidecar write necessarily uses a provisional `EPIC-REQUEST-<ts>`
  run_id, never the real `epicCreatedRunId`.** This is a permanent, accepted limitation (the real
  epic ticket ID does not exist until Discover's own `agent()` call returns), not something to
  "fix" by changing `implement-epic.js:184-193`'s existing, Step-2-owned `record_events.py`/
  `record_run.py` calls to use the provisional value instead — that would trade away the real epic
  ticket ID's traceability in `events.jsonl` for a rarely-hit bootstrap path. A future change adding
  real reconciliation between the two identifiers is a legitimate candidate future ticket, not
  something this plan's Step 1 attempts.
- **L131/L304/L659 exclusions are permanent architectural decisions, not TODOs.** A future change
  that silently adds `writeSidecar()` at any of these 3 sites without re-litigating the precedent
  (L131) or the concurrency race (L304/L659) would reintroduce
  `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION`-class bugs. The new architecture-guard test
  module (Step 5, item 4) exists specifically to catch this.
- **`compute_tool_stats()`'s filter must stay a membership check against exactly 3 literals**, never
  simplified to "not None" — `simq-audit` (`SIMQ-AUDIT-` prefix) is a real, distinct workflow with
  its own separate, still-unfixed inline `TOOL_STATS`-compute anti-pattern
  (`TCK-20260719-COST-PROXY-WRITE-PATH`'s "Found but explicitly out of scope" note); accidentally
  including it would silently overwrite whatever `simq-audit.js` computes itself.
- **The 2 fire-and-forget `implement-epic.js` sites legitimately compute `(0, 0.0)`, not an error
  state** — this is `compute_tool_stats()`'s existing, unmodified
  unconditional-entry-per-wanted-key behavior (`record_events.py:74`), not new logic added by this
  ticket. Do not "fix" this into an omitted key — that would be a real, unrequested behavior
  change to `compute_tool_stats()`'s existing contract.
- **No historical backfill** — a test asserting forward-only behavior is correct; a test or script
  implying retroactive population of pre-cutover null rows is scope creep.
- **`docs/parity_ledger/infrastructure.yaml`'s `INFRA-282`** likely needs an update once the
  filter's final shipped shape is known — this is explicitly a Parity-phase concern
  (`parity-updater`), not something to implement inside this plan.

## Deviations (recorded during Implement)

- **Step 6's Verify note was factually wrong about test overlap; resolved without touching the
  protected test file.** Step 6's Verify note claimed
  `test_schema_doc_no_longer_describes_agent_self_report_mechanism`
  (`tests/tools/test_current_run_sidecar_orchestrator.py`, explicitly listed elsewhere in this plan
  as a file that "stays green, untouched") "targets different text" than what Step 6's L289
  correction touches. This was incorrect: that test asserts the literal substring `"neither ever
  has"` is present in `docs/agent-monitoring/schema.md` — a substring that lived inside the exact
  L289 sentence ("Neither `create-tickets` nor `implement-epic` registers a `.claude/current_run`
  sidecar per agent call (neither ever has)...") Step 6 instructs replacing, since that sentence's
  overall claim is now false (both workflows have partial coverage after this ticket). A first pass
  at Step 6 removed the substring outright and broke this test — running the plan's own scoped
  Step 5 Verify command surfaced it immediately.
  Fix: rather than touching the protected test file (forbidden by this plan's own Step 5 "Do NOT
  touch" list) or restoring the false claim just to keep a string match green, the L289 paragraph
  was reworded to open with an explicitly-scoped **historical** sentence — "Prior to
  `TCK-20260904-COST-PROXY-EPIC-TICKETS`, neither `create-tickets` nor `implement-epic` registered
  a `.claude/current_run` sidecar per agent call — **neither ever has** until that ticket landed."
  — which is fully truthful (it was true before this ticket) and preserves the pinned substring for
  a legitimate reason (documenting the exact baseline this ticket changed), immediately followed by
  the accurate current-state description the rest of Step 6 specifies. This is a genuine plan defect
  found during implementation (an unverified cross-reference, not an architecture-review miss on
  substance), not a workaround of the test's actual intent — the test's own purpose (documenting
  that both workflows' historical sidecar gap was disclosed) remains satisfied, and the doc's
  substantive claim about current behavior is now accurate, not gamed. No other step's Verify
  commands or file-touch lists were affected.

- **Step 1's and Step 3's `writeSidecar` insertions break an older, pinned test's literal adjacency
  strings for BOTH `implement-epic.js` and `create-tickets.js` — not implement-epic.js alone as
  initially suspected; the invariants structurally cannot both hold for either file; resolved by
  narrowing the older test for both files' Discover/Comprehend sites, not by reordering code.**

  The broader `tests/tools/` sweep run during Test phase failed
  `tests/tools/test_step0_ts_orchestrator.py::test_ts_capture_bash_precedes_each_covered_agent_call`,
  built by the earlier, unrelated `TCK-20260710-STEP0-TS-ORCHESTRATOR-BASH`. This test asserts two
  constants verbatim (module-level, `test_step0_ts_orchestrator.py:46,48`):
  - `_IMPLEMENT_EPIC_ADJACENCY = "const discoverTs = await captureTs()\nconst discovery = await agent("`
  - `_CREATE_TICKETS_ADJACENCY = "const comprehendTs = await captureTs()\nconst comprehension = await agent("`

  **Both are now false**, confirmed by direct string search against the shipped files (not just the
  `implement-epic.js` one the investigation request initially flagged):
  ```
  >>> "const discoverTs = await captureTs()\nconst discovery = await agent(" in open(".claude/workflows/implement-epic.js").read()
  False
  >>> "const comprehendTs = await captureTs()\nconst comprehension = await agent(" in open(".claude/workflows/create-tickets.js").read()
  False
  ```
  `implement-epic.js` (confirmed by direct read, `.claude/workflows/implement-epic.js:85-132`):
  `discoverTs = await captureTs()` (line 85), then the hoisted `batchRunId` computation (lines
  87-103 — whose `request`-mode branch is `'EPIC-REQUEST-' + (discoverTs || '').replace(...)`, i.e.
  it genuinely requires `discoverTs`'s value and therefore cannot execute before it), then the
  `writeSidecar` helper's definition (lines 105-129), then `await writeSidecar(-1, 'Discover',
  'discover')` (line 131), then `const discovery = await agent(` (line 132) — 46 lines now sit
  between `discoverTs`'s capture and the `agent()` call.

  `create-tickets.js` (confirmed by direct read, `.claude/workflows/create-tickets.js:191-193`):
  `const comprehendTs = await captureTs()` (line 191), then `await writeSidecar(events.length + 1,
  'Comprehend', 'comprehend')` (line 192), then `const comprehension = await agent(` (line 193) —
  Step 3's one new `writeSidecar()` line now sits directly between `comprehendTs`'s capture and the
  `agent()` call, breaking the same literal 2-line adjacency the same way, just with only 1
  intervening line instead of 46.

  This ticket's own new test file independently pins a **different**, now-satisfied adjacency for
  both same sites (`tests/tools/test_epic_create_tickets_sidecar_orchestrator.py:62,69`):
  - `"await writeSidecar(-1, 'Discover', 'discover')\nconst discovery = await agent("` — satisfied,
    `implement-epic.js:131-132` contiguous.
  - `"await writeSidecar(events.length + 1, 'Comprehend', 'comprehend')\nconst comprehension = await agent("`
    — satisfied, `create-tickets.js:192-193` contiguous.

  **Confirmed no reordering makes both literally true, for either file.** For `implement-epic.js`:
  `batchRunId`'s `request`-mode formula depends on `discoverTs`'s already-captured value, so some
  synchronous code computing `batchRunId` (and, given the plan's closure-based `writeSidecar`
  design — Step 1, "closes over the hoisted `batchRunId` constant instead of taking `run_id` as a
  parameter" — the `writeSidecar` definition itself, which must exist before it is called and after
  `batchRunId` is at least declared) must sit between `discoverTs`'s capture and the first
  `writeSidecar()` call. For `create-tickets.js`: Step 3's `writeSidecar(events.length + 1,
  'Comprehend', 'comprehend')` call is itself the thing that must fire immediately before
  `agent()` (per this ticket's own new test's adjacency requirement) — there is no way to also keep
  `captureTs()` immediately before `agent()` without either calling `writeSidecar()` *before*
  `captureTs()` (backwards — `writeSidecar`'s own architecture-approved design fires immediately
  before the `agent()` call it labels, not before the phase's ts capture) or duplicating the
  ts-capture bash call. The only alternatives that would preserve literal 2-line adjacency for the
  *older* test in either file are: (a) restructuring `writeSidecar`'s call sites to inline extra
  state instead of relying on a single hoisted/closed-over value (duplicating logic across call
  sites — a correctness regression, exactly the drift risk Step 1's hoisting was written to
  eliminate), or (b) dropping `request` mode's `discoverTs`-derived provisional identifier (a real
  behavior change to an already-implemented, architecture-approved ticket, not something to alter
  post hoc to satisfy an unrelated older test). Neither is an acceptable fix; for both files, the
  two literal adjacency strings are mutually exclusive given the correct, already-shipped code
  shape.

  **Resolution: narrow `test_step0_ts_orchestrator.py`'s scope for these two specific sites
  (`implement-epic.js`'s Discover site and `create-tickets.js`'s Comprehend site) only; do not touch
  `_IMPLEMENT_TICKET_ADJACENCY` or anything else in this file.** The older test's own module
  docstring (`test_step0_ts_orchestrator.py:104-108`) frames the property it protects as two things:
  (1) `captureTs()` precedes the corresponding `agent()` call (or its paired `writeSidecar()` call,
  where one exists), and (2) the captured value is wired downstream, not discarded. Property (2) for
  both files is asserted by **separate** lines in the same test function, unaffected by this change:
  `assert "const batchStartTs = discoverTs || null" in ie_source` (`discoverTs` is read at
  `implement-epic.js:215` and does flow downstream) and `assert "startTs = comprehendTs || null" in
  ct_source` (`comprehendTs` is read at `create-tickets.js:232` and does flow downstream) — both
  assertions stay exactly as-is. Only the literal-adjacency portion of property (1) is now
  over-specified for these two sites: both were written when their respective files had no
  `writeSidecar` call at all (hence the direct `captureTs()`→`agent()` form), and this ticket's
  `writeSidecar` additions supersede them with a newer, more load-bearing ordering invariant —
  attribution correctness for tool-call cost tracking (the exact
  `TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION` bug class Steps 1/3 were written to
  prevent) — which is already test-enforced by this ticket's own
  `test_epic_create_tickets_sidecar_orchestrator.py` for both sites (`_EPIC_COVERED_ADJACENCY[0]`
  and `_CREATE_TICKETS_COVERED_ADJACENCY[0]`). Dropping the literal-adjacency-only assertion for
  these two sites loses no real coverage: the freshness property the original ticket cared about
  (ts reflects a moment close to just-before-the-agent-call, not stale from an earlier phase) still
  holds in substance for both — the code between `discoverTs`/`comprehendTs`'s capture and the
  `agent()` call is synchronous, non-blocking string/closure setup plus (now) one `bash()`-backed
  `writeSidecar()` call that itself runs immediately before `agent()` fires, not a delay — it is
  only the literal-string-adjacency *test technique* that no longer fits either site, not the
  invariant it was a stand-in for. Note `_CREATE_TICKETS_ADJACENCY` is a single string (unlike
  `_IMPLEMENT_TICKET_ADJACENCY`'s list of 10) — this fix retires exactly that one constant plus its
  sibling `_IMPLEMENT_EPIC_ADJACENCY`, nothing else.

  **Exact edit to apply to `tests/tools/test_step0_ts_orchestrator.py`** (implementer: apply
  verbatim; do not touch `_IMPLEMENT_TICKET_ADJACENCY` or any other test function in this file):

  1. Replace the two module-level constants at lines 46 and 48:
     ```python
     _IMPLEMENT_EPIC_ADJACENCY = "const discoverTs = await captureTs()\nconst discovery = await agent("

     _CREATE_TICKETS_ADJACENCY = "const comprehendTs = await captureTs()\nconst comprehension = await agent("
     ```
     with a single retirement comment (no live constants — unused ones only invite drift):
     ```python
     # _IMPLEMENT_EPIC_ADJACENCY (literal "const discoverTs = await captureTs()\nconst discovery =
     # await agent(") and _CREATE_TICKETS_ADJACENCY (literal "const comprehendTs = await
     # captureTs()\nconst comprehension = await agent(") were retired by
     # TCK-20260904-COST-PROXY-EPIC-TICKETS: that ticket's Step 1 inserted a hoisted `batchRunId`
     # computation + implement-epic.js's first `writeSidecar()` call between `discoverTs`'s capture
     # and the Discover `agent()` call (batchRunId's request-mode branch genuinely depends on
     # discoverTs's value, so nothing can execute between them for free); Step 3 inserted
     # create-tickets.js's first `writeSidecar()` call directly between `comprehendTs`'s capture and
     # the Comprehend `agent()` call. The superseding invariant for both sites —
     # `writeSidecar()` immediately precedes `agent()` — is asserted instead by
     # tests/tools/test_epic_create_tickets_sidecar_orchestrator.py
     # (`_EPIC_COVERED_ADJACENCY[0]` / `_CREATE_TICKETS_COVERED_ADJACENCY[0]`). The "captured value
     # actually reaches downstream code" property this file still protects for both files is
     # unchanged — see the `batchStartTs = discoverTs || null` / `startTs = comprehendTs || null`
     # assertions below.
     ```
  2. In `test_ts_capture_bash_precedes_each_covered_agent_call`
     (`test_step0_ts_orchestrator.py:111-126`), delete these two lines (one per file):
     ```python
     assert _IMPLEMENT_EPIC_ADJACENCY in ie_source
     ```
     and
     ```python
     assert _CREATE_TICKETS_ADJACENCY in ct_source
     ```
     Keep `ie_source = _read_implement_epic()` and `ct_source = _read_create_tickets()` (both still
     needed by the downstream-wiring assertions later in the same function) and every other line in
     the function unchanged. The function's shape after this edit:
     ```python
     def test_ts_capture_bash_precedes_each_covered_agent_call():
         it_source = _read_implement_ticket()
         for adjacency in _IMPLEMENT_TICKET_ADJACENCY:
             assert adjacency in it_source, f"expected adjacency not found: {adjacency!r}"

         ie_source = _read_implement_epic()
         # implement-epic.js's Discover-site captureTs()->agent() adjacency is no longer checked
         # here — see the retirement comment above _IMPLEMENT_EPIC_ADJACENCY's old location.

         ct_source = _read_create_tickets()
         # create-tickets.js's Comprehend-site captureTs()->agent() adjacency is no longer checked
         # here — see the same retirement comment (covers both constants).

         # Captured values are wired downstream, not discarded.
         assert "const startTs = scopeTs || null" in it_source
         assert "const batchStartTs = discoverTs || null" in ie_source
         assert "startTs = comprehendTs || null" in ct_source
     ```
  3. Optional but recommended for doc accuracy: append one sentence to the module docstring's
     item-2 paragraph (`test_step0_ts_orchestrator.py:104-108`) noting that `implement-epic.js`'s
     Discover site and `create-tickets.js`'s Comprehend site are the two documented exceptions,
     cross-referencing `test_epic_create_tickets_sidecar_orchestrator.py`. Not required for the test
     itself to pass; do this only if the implementer has budget left after the required edits above.

  **Do NOT touch:** `_IMPLEMENT_TICKET_ADJACENCY` and its assertions (implement-ticket.js's 10
  captureTs→writeSidecar→agent chains are unaffected by this ticket — Steps 1/3 never touch
  implement-ticket.js). Every other test function in `test_step0_ts_orchestrator.py`
  (`test_step_0_ts_capture_lines_gone_from_all_covered_sites`,
  `test_phase_ts_prefix_convention_removed_from_investigate_and_plan`,
  `test_ts_schema_required_field_dropped_at_scope_and_discover`,
  `test_end_ts_and_batch_end_ts_captures_untouched`,
  `test_captureTs_helper_defined_once_after_writeSidecar`) — none reference either retired constant
  and none are affected by Step 1/3's changes.

  **Verify:** `.venv/bin/python3 -m pytest tests/tools/test_step0_ts_orchestrator.py
  tests/tools/test_epic_create_tickets_sidecar_orchestrator.py -q` — both files must pass together
  (the older file no longer asserts either retired invariant; the new file asserts the superseding
  one for both sites).
