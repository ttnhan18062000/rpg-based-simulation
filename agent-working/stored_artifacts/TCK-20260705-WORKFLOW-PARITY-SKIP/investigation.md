---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-WORKFLOW-PARITY-SKIP
artifact_type: investigation
tags: [workflows, observability]
---

# Investigation — TCK-20260705-WORKFLOW-PARITY-SKIP

## Current Behavior

**The ticket's own cited line numbers (~500-535, ~401-404) are stale.** They predate the sibling ticket
`TCK-20260705-WORKFLOW-SECURITY-GATE` (merged, `stored_artifacts/TCK-20260705-WORKFLOW-SECURITY-GATE/`),
which added ~80 lines earlier in the same file: `TICKET_SCHEMA` gained `tags`/`mistag_warning`
(`.claude/workflows/implement-ticket.js:40-45`), both Scope-phase prompt branches gained new instruction
blocks (mis-tag check, steps 3a/3b and 8), and a new Security-Review gate was inserted **after** Parity.
Current (post-security-gate) line numbers, read in full from the live file:

- **IMPL_SCHEMA** (Implement phase, produces the two signals this ticket needs): `implement-ticket.js:432-443`.
  `files_changed: { type: 'array', items: { type: 'string' } }` and `behavior_changed: { type: 'boolean' }`
  are both required fields, already populated by the `implementer` agent before Parity ever runs.
- **Parity phase agent call**: `implement-ticket.js:542-567` (the `agent(...)` invocation itself). The
  prompt's only existing conditional is a ternary at lines 555-563 that **softens wording**, not an actual
  skip: `implementation.behavior_changed ? "Update docs/parity_ledger/... entries..." : "No observable
  behavior change reported. Verify this is accurate..."` — the agent call fires unconditionally either way.
- **Parity's pushEvent**: `implement-ticket.js:569-571` —
  `pushEvent('Parity', 'parity-updater', 'ok', parityText.slice(0, 200), parityTs)`.
- **Hotfix-tier skip precedent** (the pattern this ticket must copy): `implement-ticket.js:421-426`:
  ```js
  } else {
    log('Hotfix tier: skipping Investigate, Plan, and Architecture Review.')
    pushEvent('Investigate', 'investigator', 'skipped', 'Hotfix tier — investigation skipped')
    pushEvent('Plan', 'planner', 'skipped', 'Hotfix tier — plan skipped')
    pushEvent('Review', 'architecture-reviewer', 'skipped', 'Hotfix tier — architecture review skipped')
  }
  ```
  Status value used is the literal string `'skipped'`. Note `ts` is omitted entirely in this precedent —
  `pushEvent`'s signature (`implement-ticket.js:149-159`) defaults `ts` to `null` when omitted, and
  `writeMonitoring`'s Step 3 (`implement-ticket.js:192-195`) back-fills any null/missing `ts` with `END_TS`.
  A new Parity-skip `pushEvent` call should follow this exact shape (no `ts` argument needed, since there
  is no agent invocation to time).
- **Security-Review gate placement, confirmed**: `implement-ticket.js:573-629`, sitting between Parity's
  `pushEvent` (line 571) and `phase('Verify')` (line 633). **Confirmed no interaction with this ticket's
  change**: the gate's trigger (`ticketInfo.tags.includes('security')` /
  `ticketInfo.suggested_skills.includes('/security-review')`, lines 579-580) reads only `ticketInfo`
  (Scope-phase output) and is structurally independent of `implementation.files_changed` /
  `implementation.behavior_changed` / the `parity` variable. The only shared state is that both phases run
  in the same linear sequence — if Parity is skipped, `parity`/`parityText` are never referenced again by
  Security-Review, so no downstream variable is left undefined in a way Security-Review depends on. Safe,
  different code region, no plumbing overlap.

## Mechanics / Engine Constraints

Not directly applicable — this is a workflow-orchestration change (`.claude/workflows/implement-ticket.js`
pseudocode), not simulation logic under `src/`. No `docs/mechanics/` chapter or `docs/engine/` contract
governs workflow phase sequencing; `docs/ai/workflows.md`, `docs/ai/system_overview.md`, and
`docs/ai/ticket-lifecycle.md` are the closest analogue to an authoritative spec for this behavior, and all
three currently describe Parity as unconditional (see Prior Work / doc-drift note below).

**Critical execution-model finding, confirmed via `.claude/skills/implement-ticket/SKILL.md`:**
`.claude/workflows/implement-ticket.js` is not executed by a real JS/Node runtime. It is pseudocode that the
orchestrating Claude agent reads and manually translates into tool calls, phase by phase (see SKILL.md's
translation table, e.g. `phase('Name')` → "announce to user", `await agent(...)` → `Agent(...)` tool call).
There is no `fs`, `require`, or file-I/O primitive available inside this pseudocode — confirmed by a
repo-wide grep for `readFileSync`/`require(`/`fs.`/`yaml.load` across `.claude/workflows/*.js`, zero hits.
This matters directly for the Assumptions/Open Questions section below: the new P0-safeguard check cannot
be "free" inline JS logic with file access — any file read (including the P0 ledger scan) must either be
done via a shell command run directly by the orchestrating agent (cheap, no sub-agent dispatch) or
delegated to a full `agent(...)` call (expensive, defeats the purpose of the optimization).

## Parity Ledger Overlap

Read all 9 files under `docs/parity_ledger/` (`combat_movement.yaml`, `faction.yaml`, `infrastructure.yaml`,
`progression.yaml`, `social_narrative.yaml`, `strategic_cognition.yaml`, `substrate.yaml`,
`town_resource.yaml`, `world_dynamics.yaml`) plus `schema.json`.

**Important scoping correction**: the Parity phase's own prompt (`implement-ticket.js:556`) only ever
writes to **8** files — `substrate.yaml, combat_movement.yaml, strategic_cognition.yaml, town_resource.yaml,
progression.yaml, social_narrative.yaml, world_dynamics.yaml, infrastructure.yaml` — matching the 8
`parity_subsystems` enum values in `IMPL_SCHEMA` (`implement-ticket.js:438`). **`faction.yaml` is not one of
the 8** and is never touched by the Parity phase at all (also has 0 P0 entries, see below, so it is a
non-issue either way, but the new safeguard should scan the same 8 canonical files Parity itself uses, not
"all of `docs/parity_ledger/*.yaml`" literally — that literal reading would include an irrelevant 9th file
and, if a `schema.json` glob match were naive, a non-YAML-entry-list file).

Per-file entry/priority counts (P0 = highest bar, requires non-null `test_path` when `status` is
`verified`/`divergent` per `schema.json`'s conditional `required`):

| File | Total entries | P0 entries |
|---|---|---|
| `combat_movement.yaml` | 293 | 289 |
| `faction.yaml` | 13 | 0 |
| `infrastructure.yaml` | 266 | 178 |
| `progression.yaml` | 116 | 107 |
| `social_narrative.yaml` | 260 | 225 |
| `strategic_cognition.yaml` | 245 | 225 |
| `substrate.yaml` | 386 | 369 |
| `town_resource.yaml` | 187 | 169 |
| `world_dynamics.yaml` | 118 | 97 |
| **Total (8 canonical files)** | **1,871** | **1,659** |

Total on-disk size of the 9 files: ~800KB, ~21,700 lines combined (`wc -l`/`du -sh` run directly).

**`v2_evidence` field shape** (the field the new safeguard must check `files_changed` against) — sampled
across all P0 entries in all 9 files: it is a free-form prose string, **sometimes** containing one or more
backtick-quoted path-like tokens (e.g. `` `src/engine/legality.py` (`get_manhattan_dist`) ``,
`` `src/core/state.py` (`IdentityComponent` level, ...) ``), and **frequently** containing no path at all —
a large fraction (all of `substrate.yaml`'s and `world_dynamics.yaml`'s sampled P0 entries, and many in
`infrastructure.yaml`/`progression.yaml`/`town_resource.yaml`) simply read
`"Implementation proven via exhaustive checklist audit Phase 1-11"` with `test_path: null`. This is a
**mixed-format free-text field, not a structured path list** — matching by substring/regex extraction of
backtick-quoted tokens is the only generic approach; there is no clean structured field to key off.

**Empirically verified invariant (as of this investigation, not a durable guarantee)**: a script scan of
every P0 entry's `v2_evidence` across all 9 files found **zero** backtick-quoted path-like tokens (tokens
containing `/`) that do not start with `src/`, `tests/`, or `tests_v2/`. In other words, no P0 entry's
`v2_evidence` currently cites a `docs/`, `tickets/`, `staging_artifacts/`, or other non-code path. Combined
with the skip trigger's own precondition (`files_changed.every(f => !f.startsWith('src/'))` — i.e. the skip
is only even considered when **zero** changed files are under `src/`), this means: **given the ledger's
current contents, the "does `files_changed` intersect a P0 entry's `v2_evidence` path" check can never
actually fire true today.** It is a structurally-inert safeguard right now — but it is still required as
written, because it protects against (a) future ledger entries that might cite a non-`src/` path (e.g. a
config file or generated data file with `test_path` still pointing at it), and (b) the case where
`v2_evidence` cites a `tests/`/`tests_v2/` path that a docs-only ticket's `files_changed` could plausibly
touch (e.g. a ticket that only edits a test fixture or a test docstring under `tests/` — that is a `src/`-free
change today per the trigger's own precondition, so this is exactly the scenario the safeguard exists for).

Status distribution across all 9 files (informational, not required by scope): `verified` 1644,
`legacy_verified` 232, `missing` 4, `unsupported` 2, `divergent` 2.

## Prior Work

- **`stored_artifacts/TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION/investigation.md`** (lines 116-124,
  "Candidate 3") is the direct origin of this ticket's scope. It already establishes: the Scope-time vs.
  Implement-time trigger safety distinction, the exact trigger expression
  (`implementation.files_changed.every(f => !f.startsWith('src/')) && !implementation.behavior_changed`),
  and the "skip the `agent(...)` call, replace with synthetic result + `pushEvent(..., 'skipped', ...)`"
  mechanism. **This ticket adds one thing Candidate 3 did not originally specify**: the P0 `v2_evidence`
  intersection safeguard — that is new scope introduced directly in this ticket's own Scope section, not
  carried over from Candidate 3.
- **`stored_artifacts/TCK-20260705-WORKFLOW-SECURITY-GATE/`** (sibling ticket, same parent investigation,
  merged) — independent code region (confirmed above), but its `test_plan.md` establishes the exact testing
  precedent this ticket should follow (see Test Plan doc): **no automated pytest exists for
  `.claude/workflows/*.js` semantics** (confirmed again in this investigation — zero hits searching
  `tests/`/`tools/` for `implement-ticket`/`workflows/*.js` beyond unrelated `lab_agent` workflow tests, which
  cover a different, actually-Python-executed workflow system under `src/`). Verification for this ticket
  must be structural/manual (`node -c` syntax check, grep-verified branch placement, byte-level
  `events.jsonl` diff), matching `TCK-20260607-MON-CAPTURE`'s established precedent
  ("workflow script testing is manual").
- **`docs/REGISTRY.yaml`** queried for tickets whose `related_code_areas` overlap
  `implement-ticket.js`/`parity_ledger`: 18 matches, all either (a) unrelated `src/` feature tickets that
  merely updated a specific parity-ledger *entry* as part of normal Parity-phase work (e.g.
  `TCK-20260702-SIMQ-EVAL-HARNESS`, `TCK-20260702-SIMQ-UPLIFT2-FACTION`), or (b) prior workflow-infrastructure
  tickets (`TCK-20260612-LOCAL-CTX-MCP`, `TCK-20260607-MON-AGENTS`, `TCK-20260607-MON-CAPTURE`) that touched
  `implement-ticket.js` for monitoring/context-search plumbing, not Parity-phase logic. No duplicate or
  conflicting prior attempt at this specific skip exists.
- `implement-epic.js:191` confirmed: `result = await workflow('implement-ticket', ticketArgs)` — it has no
  phase logic of its own, delegates entirely per child ticket. The sibling ticket's finding holds
  unchanged; this skip applies epic-wide with zero additional plumbing, and `implement-epic.js` must not be
  touched.

## Risks and Open Questions

- **Mechanism for the P0 safeguard (the ticket's own stated open question) — recommend resolving as
  follows**, based on evidence gathered here:
  - A **full YAML parse of all 8 canonical parity ledger files on every Parity phase invocation** is
    wasteful: most tickets (the common case) touch `src/` and never reach the skip-eligible branch at all,
    so paying an ~800KB/9-file parse cost unconditionally is pure waste for the majority of runs.
  - The check should be **lazy — invoked only after both existing signals (`files_changed` has no `src/`
    path AND `behavior_changed` is false) already indicate the skip is about to fire.** At that point, and
    only then, run the P0 intersection check.
  - Given the execution-model finding above (pseudocode with no JS file-I/O primitive), the cheapest correct
    implementation is **a single shell command the orchestrating agent runs directly** (not a new
    `agent(...)` dispatch) — e.g. a `grep`/small Python one-liner across the 8 canonical files' P0 entries'
    `v2_evidence` fields, checking whether any `files_changed` path string appears as a substring. This adds
    one Bash tool call only in the rare skip-eligible case, with zero added cost to the common (non-skip)
    path, and zero new agent/token spend either way.
  - A pre-built index (e.g. a cached JSON mapping path → entry ID) is not justified: the check only ever
    runs in the already-rare skip-eligible branch, and the raw scan is a few hundred milliseconds of local
    grep — building and maintaining a cache would be premature engineering for a check that, per the
    empirical finding above, currently always resolves to "no intersection" anyway.
  - **This is the one item explicitly left open by the ticket's Assumptions section; Plan should adopt the
    lazy-grep-by-orchestrator approach above rather than a full-scan-every-run or pre-built-index approach.**
- **The safeguard is currently inert but must not be treated as optional.** Because it can never fire true
  today (see Parity Ledger Overlap), there is a temptation to treat it as dead code / skip implementing it
  rigorously. It must still be implemented for real, because the invariant it depends on (no P0
  `v2_evidence` cites a non-`src/` path) is a fact about the ledger's *current* contents, not an enforced
  constraint — a future Parity-phase run could add an entry that violates it.
- **`docs/ai/workflows.md`, `docs/ai/system_overview.md`, `docs/ai/ticket-lifecycle.md` all need updating**
  (see Anti-Drift Hazards) — none currently mention any skip condition for Parity; all three describe it as
  running unconditionally with the `parity-updater` agent. This is the same "phase-count/behavior drift"
  hazard the tag-tuning investigation already flagged as an existing, worsening problem in
  `docs/ai/system_overview.md`.
- **No open question requiring a human decision remains** beyond the mechanism choice above, which this
  investigation resolves with evidence (lazy orchestrator-run shell scan, not a full-scan-every-run or
  pre-built index).

## Anti-Drift Hazards

- **Doc drift (3 files).** `docs/ai/workflows.md:86` (Parity row in the phase table),
  `docs/ai/system_overview.md:78` (the one-line phase-chain description), and
  `docs/ai/ticket-lifecycle.md:66` (the ASCII pipeline diagram's `[Parity]` node) all currently show Parity
  as unconditional. Each needs a short annotation analogous to how Security-Review's conditional trigger is
  already documented in all three (e.g. `docs/ai/ticket-lifecycle.md:68`'s
  "only if the ticket's tags include `security`..." comment line, and
  `docs/ai/workflows.md:87`'s inline gate-condition cell). Do not skip any of the three — the security-gate
  ticket updated all three together and that is the correct precedent to match.
- **Monitoring event-count drift.** The skip path must still call `pushEvent(..., 'skipped', ...)` exactly
  once — CLAUDE.md's Hard Rule requires at least one event entry per phase-equivalent step, and skipping
  the `pushEvent` call entirely (not just the `agent()` call) would silently violate that rule for every
  docs-only ticket going forward.
- **Scope-drift regression is the single most safety-critical behavior to verify.** A ticket that starts
  looking docs-only in `Related Code Areas` but whose `implementation.files_changed` (post-Implement)
  includes even one `src/` path must never skip — this is explicitly called out as the "single most
  important regression test" in the ticket's own Acceptance Criteria, and this investigation found nothing
  in the current code that would already prevent a naive implementation from accidentally reading
  `ticketInfo`/Scope-time data instead of `implementation.files_changed`/`implementation.behavior_changed`
  (both are in scope/available at the Parity call site already, so the risk is purely "did the implementer
  wire the check to the right variable," not a data-availability problem).
- **`faction.yaml` exclusion.** Any implementation that naively globs `docs/parity_ledger/*.yaml` for the
  P0 safeguard (rather than the 8 canonical files the Parity phase prompt itself lists) will also scan
  `faction.yaml` and `schema.json`-adjacent files unnecessarily. Harmless today (`faction.yaml` has 0 P0
  entries, and `schema.json` is not a `.yaml` glob match), but worth being precise about in the
  implementation to avoid silent scope creep of "which files count as the parity ledger."
