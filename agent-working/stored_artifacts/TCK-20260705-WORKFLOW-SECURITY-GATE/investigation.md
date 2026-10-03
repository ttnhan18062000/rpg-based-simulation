---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-WORKFLOW-SECURITY-GATE
artifact_type: investigation
tags: [tagging, security, workflows]
---

# Investigation — TCK-20260705-WORKFLOW-SECURITY-GATE

## Current Behavior

### File structure and exact insertion point (resolved, not ambiguous)

`.claude/workflows/implement-ticket.js` (691 lines) runs 9 phases in strict sequence:
Scope (27) → [Investigate (245) → Plan (288) → Review (338)] (skipped for hotfix) → Implement (409) →
Test (458) → Parity (519) → Verify (554) → Finalize (629).

Test phase spans 458–515 (`test-scoper` agent, `TESTS_FAILED` early-return at 497–508, `pushEvent('Test', ...)`
at 510). Parity phase spans 517–550 (`parity-updater` agent, no gate/early-return, `pushEvent('Parity', ...)`
at 550). Verify begins at `phase('Verify')` (554). Because Test always executes before Parity, "inserted
between Test/Parity and Verify" (ticket Scope) and "right before `phase('Verify')`" are the same, single,
unambiguous point: **after line 550 (Parity's `pushEvent`), before line 552/554**. The sibling investigation
(`stored_artifacts/TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION/investigation.md:109`) already named this
exact line number when it recommended this candidate — confirmed correct on this re-read.

### The gate pattern to mirror (Review phase, lines 336–399)

1. `REVIEW_SCHEMA` (340–351): `type: object`, `required` array, `verdict` as a `string` `enum`, plus
   `violations`/other arrays and a `summary` field (description: "one sentence ... ≤200 chars ... goes into
   the agent monitoring event record" — every schema in this file carries that same `summary` convention,
   per `TCK-20260607-MON-AGENTS`).
2. `agent(promptText, { label, schema, agentType })` (353–381) — the `agentType` here is `'architecture-reviewer'`,
   which maps 1:1 to `.claude/agents/architecture-reviewer.md`.
3. `if (review.verdict !== 'APPROVED') { pushEvent(..., 'failed', ...); await writeMonitoring(review.verdict);
   return { status: review.verdict, ... } }` (383–396) — the early-return `status` **is** the verdict value
   itself, i.e. a gate failure's returned `status` is exactly one of the schema's own enum values
   (`NEEDS_CHANGES`/`BLOCKED`), not a separately-invented string.
4. On success: `pushEvent('Review', 'architecture-reviewer', 'ok', review.summary, review.ts)` (398).

Every phase in this file follows step 0/0b boilerplate inside its prompt: `date -u ...` for `ts`, and a
`.claude/current_run` sidecar write for tool-call-count tracking (`seq: ${events.length + 1}`) — the new
gate's prompt must include both, exactly like Review's (356–358).

### `suggested_skills` — confirmed still purely advisory today

`TICKET_SCHEMA` (29–43) declares `suggested_skills` (added by `TCK-20260705-TAG-SKILL-SUGGEST`, not new
here). It is computed in *both* Scope-phase prompt branches — "Load existing ticket" (60–68, reads ticket
frontmatter `tags` directly and restates the tag→skill table inline) and "Create new ticket" (116, delegates
to `ticket-scoper`'s own Output contract item 5, `.claude/agents/ticket-scoper.md:79-91`). The only consumer
today is `log(...)` at 199–201 — confirmed by re-reading the whole file: no phase after Scope references
`ticketInfo.suggested_skills`. This ticket's trigger condition (`ticketInfo.suggested_skills.includes('/security-review')`)
is therefore valid JS today with zero schema changes needed for the trigger itself, exactly as the ticket
states.

### `architecture-reviewer.md` as the template for a possible `security-reviewer.md`

`.claude/agents/architecture-reviewer.md` is 58 lines: a Registry Lookup step, a "What to Review" checklist
(6 architecture-boundary bullets + Mechanics Bible chapter table + Engine Contract table + Parity Ledger
check), and an Output section (verdict enum, per-violation findings, parity IDs, chapters to read, `summary`
field). It is not a one-line stub — it is a substantial, repo-specific checklist that gives the LLM a
concrete rubric instead of "use your judgment."

`docs/ai/skills.md:76` is the **entire** published description of the built-in `/security-review` skill:
*"Review for security vulnerabilities across the diff."* There is no `.claude/skills/security-review/`
directory (confirmed absent — `find .claude/skills -iname "*security*"` returns nothing) and no further
guidance text anywhere in the repo to "reference inline" — the skill is an opaque, system-level built-in.
An inline prompt referencing it would have nothing concrete to reference beyond that one sentence.

**Every `agentType:` value actually used in `implement-ticket.js` maps 1:1 to an existing `.claude/agents/*.md`
file** — `ticket-scoper`, `investigator`, `planner`, `architecture-reviewer`, `implementer`, `test-scoper`,
`parity-updater`, `done-checker` — all 8 present, no exceptions, no bare/file-less `agentType`. (`mechanics-auditor.md`,
`simulation-analyst.md`, `world-debugger.md` exist too but are invoked from other workflows/ad hoc `Agent()`
calls, not from this file.)

### Monitoring: no enum/allowlist gates phase names or final_status anywhere

Read `tools/agent-monitoring/record_run.py` (only checks 5 required *keys* are present, no value
validation), `record_events.py`, `query.py`, `generate_retro.py` (all treat `final_status` as a free string),
and `validate.py` (its `LEGACY_TERMINAL_STATUS_VALUES` set — `DONE`, `EPIC_SCOPED`, `DOD_BLOCKED`,
`NEEDS_HUMAN_INPUT`, `GATE_FAIL`, `STOPPED_BY_USER`, etc. — is explicitly a **legacy backward-compat**
allowlist for *old* records lacking `end_ts`, used only as a fallback inside `_record_is_complete()`; since
`writeMonitoring` always populates `end_ts` via `record_run.py`'s Step 4, any new `final_status` value like
`SECURITY_BLOCKED` satisfies completeness via the `end_ts` check regardless, without needing to be added to
that set). **Confirmed: introducing a new `final_status` string and a new phase-name string requires zero
changes anywhere in `tools/agent-monitoring/`.**

### No automated test harness exists for `.claude/workflows/*.js`

Repo-wide search (`tests/`, `tools/`) for references to `implement-ticket` / `workflows/*.js` returns zero
hits. `node -c .claude/workflows/implement-ticket.js` exits 0 today (valid syntax) but Node does not
*execute* this file the way the Claude Code harness does — `agent()`, `phase()`, `log()`, `workflow()` are
harness-injected primitives, not real Node globals. `tickets/done/TCK-20260607-MON-CAPTURE.md`'s own Test
Summary states the established precedent explicitly: *"Manual verification: implement-ticket.js reviewed
for all 8 exit paths ... No automated tests added (workflow script testing is manual)."* This ticket should
follow the same precedent.

### Mis-tag `WARNING` heuristic — collision risk confirmed empirically, and a schema/scope tension found

`tools/registry_query.py`'s `SEED_TAGS` = `(combat, economy, cognition, faction, resource, social, content,
world, engine, strategy)` — a **Subsystem/Topic** vocabulary for filtering `docs/REGISTRY.yaml` search
results by prose substring match. It has zero overlap with auth/secrets/credential concepts and its two
functions (`candidate_tags_from_text`, `filter_registry`) are purpose-built for registry search, not a
safety heuristic over `Related Code Areas` paths — reusing it would be a category-purpose mismatch, not a
maintenance win.

Spot-checked candidate keywords against the actual codebase to catch false-positive collisions before Plan
picks a list:
- `auth` as a bare substring: **catastrophic false-positive risk**. `AuthoritativeState`,
  `authoritative_pipeline.md`, `authoritative_mutation_pipeline_contract.md`, and the word "authoritative"
  generally are used pervasively — the term is this codebase's core state-mutation vocabulary (`grep -rli
  authoritative src/` matches broadly across `src/core/`, `src/engine/`). A ticket touching almost any engine
  or state-mutation code would false-positive-WARN. `authoring` (`docs/guides/content_authoring.md`) is a
  second, independent collision on the same substring.
- `cert`/`certif` as a substring: collides with `src/certification/*` (the SimQ/perf certification harness —
  `CertificationHarness`, `certification_reporter.py`), unrelated to security certificates.
- `key`, `token`, `session`: all heavily overloaded — `grep` for `\btoken\b|\bsession\b|\blogin\b|\bkey\b`
  in `src/` matches 150 files, dominated by `src/lab/session.py` (`LabSessionStore`), generic dict/DB "key"
  usage, and `context.py`'s "token-efficient" (LLM token, unrelated to auth tokens).
- `secret`/`credential`: narrow and low-collision — only 3 files repo-wide (`src/core/self_model.py`,
  `src/certification_reporter.py`, `src/api/server.py`). Manually confirmed the one near-hit
  (`src/api/server.py:76`, `allow_credentials=True`) is ordinary FastAPI CORS config, not a real secrets file.

**Conclusion: the ticket's own hint to use "a small standalone keyword list" rather than `SEED_TAGS` is
correct, and the list must deliberately exclude bare `auth`, `cert`, `key`, `token`, `session` — safer
candidates are `credential`, `secret`, `password`, `api_key`, `private_key`, `.env`, `oauth`, `jwt`.**

**Schema/scope tension (not previously surfaced by the sibling investigation):** the WARNING needs both
`Related Code Areas` content and whether `security` was suggested — but `TICKET_SCHEMA` has no
`related_code_areas` field today, and ticket Out of Scope explicitly forbids touching
`create-tickets.js`'s Structure phase or `ticket-scoper.md`'s Output contract. Resolution precedented by
this same file's own history: the sibling investigation already documented that `suggested_skills` is
computed independently in **three** places (not read from one shared source) — the "Load existing ticket"
branch (60–68) restates the mapping inline rather than delegating to `ticket-scoper.md`. The same technique
applies here: add a new field (e.g. `mistag_warning: boolean`) to `TICKET_SCHEMA` and compute it inline
within **both** Scope-phase prompt branches in `implement-ticket.js` itself (never touching
`ticket-scoper.md` or `create-tickets.js`), fully honoring Out of Scope.

## Mechanics / Engine Constraints

N/A — pure agent-tooling/workflow-orchestration change to `.claude/workflows/implement-ticket.js`,
`docs/ai/*.md`, and possibly a new `.claude/agents/security-reviewer.md`. No `docs/mechanics/` chapter or
`docs/engine/` contract governs the Claude Code agent harness; identical conclusion to the sibling
investigation's own "Mechanics / Engine Constraints" section.

## Parity Ledger Overlap

N/A — confirmed by grepping all 8 `docs/parity_ledger/*.yaml` files for `security|vulnerab|secret|credential|auth`
(case-insensitive): every hit is the unrelated term "authoritative" (state-mutation terminology). Zero
genuine security/vulnerability/credential entries exist in the parity ledger. No entry needs a status
update from this ticket.

## Prior Work

- **`TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION`** (done) — the source investigation. Candidate 2
  (`stored_artifacts/.../investigation.md:106-112`) already fully assessed trigger/change/feasibility/risk
  and recommended "Build now" — this ticket implements that recommendation; not re-derived, only
  re-verified line-by-line above.
- **`TCK-20260705-TAG-SKILL-SUGGEST`** (done) — shipped `suggested_skills` on `TICKET_SCHEMA` and the 3-copy
  tag→skill mapping table this ticket's trigger reuses without modification.
- **`TCK-20260705-TAG-REGISTRY-QUERY`** (done) — built `tools/registry_query.py`'s `SEED_TAGS`/
  `candidate_tags_from_text`; evaluated above and rejected as a reuse candidate for the mis-tag heuristic
  (wrong taxonomy category, wrong purpose, and empirically collision-prone for this codebase's vocabulary).
- **`TCK-20260607-MON-CAPTURE`** (done) — established the `events[]`/`pushEvent`/`writeMonitoring` pattern
  this ticket's new gate must extend, and its own Test Summary is the direct precedent for "manual
  verification, no automated tests" on this file.
- **`TCK-20260607-MON-AGENTS`** (done) — established the `summary` field convention on every agent schema;
  the new gate's schema must include it.
- **`TCK-20260705-WORKFLOW-PARITY-SKIP`** (sibling, named in Related Tickets) — not yet started (no file
  under `tickets/inprogress/` or `tickets/done/`). Confirmed independent: it would touch the Parity phase's
  own agent-invocation-skip logic at line 521 (Candidate 3 in the sibling investigation), while this ticket
  only inserts a new phase *after* Parity's existing `pushEvent` at line 550 — no shared line ranges, no
  ordering dependency either direction.

## Risks and Open Questions

1. **Decision — dedicated agent file vs. inline prompt (ticket Assumption 1).** Recommend a dedicated
   `.claude/agents/security-reviewer.md`, mirroring `architecture-reviewer.md`'s structure (Registry Lookup →
   checklist → Output with verdict/violations/summary). Reasoning: (a) the 1:1 `agentType`↔role-file pattern
   is unbroken across all 8 existing uses in this file — an inline-only approach would be the first
   exception; (b) the built-in `/security-review` skill's published guidance is one sentence with nothing
   further to "reference" — a real, repo-specific checklist (injection, unsafe deserialization, path
   traversal, subprocess/command injection, secrets-in-code, raw-domain-model API exposure — this last one
   already overlaps `architecture-reviewer`'s own API-boundary rule and should be cross-referenced, not
   duplicated) needs the same order of structure `architecture-reviewer.md` has, not less.
2. **Decision — mis-tag WARNING heuristic (ticket Assumption 2).** Recommend a small standalone keyword list
   defined in `implement-ticket.js` itself (not `tools/registry_query.py`, not a new shared module) —
   `credential`, `secret`, `password`, `api_key`, `private_key`, `.env`, `oauth`, `jwt` — explicitly excluding
   `auth`, `cert`, `key`, `token`, `session` as bare substrings for the collision reasons documented above.
   Plan should decide whether this list lives as a JS array constant or as instructions inside the
   Scope-phase prompt (the latter is consistent with how `suggested_skills` itself is computed — see
   schema/scope tension above).
3. **Zero-added-cost AC (ticket Scope, 4th bullet) requires the mis-tag check to ride on data the Scope-phase
   agent call already produces** — it must not add a second agent call. The recommended `mistag_warning`
   field, computed by the *same* `ticket-scoper`-typed Scope call and surfaced via `log(...)` (never
   `pushEvent(...)`), satisfies this: no new event, no new agent invocation, for every ticket regardless of
   tag.
4. **The hotfix-tier "skip" convention must NOT be copied for the non-triggering case.** Lines 401–404 push
   `pushEvent(..., 'skipped', ...)` for Investigate/Plan/Review when `tier === 'hotfix'`. The new gate's
   ticket-level AC #3 explicitly requires **zero new phase events** for a non-security ticket — a `'skipped'`
   pushEvent would violate that AC even though it wouldn't violate CLAUDE.md's own "at least one event per
   run" Hard Rule (already satisfied by Scope/Implement/etc.). Plan/Implement must wrap the entire
   `phase()+agent()+pushEvent()` sequence in the trigger `if`, with **no** `else` branch that pushes anything.
5. **`meta.phases` array (lines 4–14) is easy to miss.** It's not named in the ticket's Related Docs (which
   lists 3 external `docs/ai/*.md` files) but is the first thing a reader of `implement-ticket.js` itself
   sees, and every existing phase has a `{ title, detail }` row there — Plan should add one for the new gate
   in the same edit, for internal consistency, even though it's not an external doc.
6. **Doc drift is already acknowledged and must not worsen.** The sibling investigation's Anti-Drift Hazards
   section already notes `docs/ai/system_overview.md`'s own dated note flags `docs/ai/workflows.md` stale for
   4/11 workflows. This ticket's required updates (`workflows.md`, `system_overview.md` §3, `ticket-lifecycle.md`)
   should be scoped strictly to documenting the new gate, not incidentally "fixing" unrelated stale content —
   that would blur this ticket's diff and its own Files Changed section.
7. **Idea doc `idea_agent_gate_determinism.md` (unscheduled) is relevant context, not a requirement.** It
   argues every LLM-judged gate should get a deterministic pre-check backstop. The mis-tag `WARNING` this
   ticket adds *is* exactly that kind of small deterministic pre-check (a keyword match, not an LLM
   judgment) ahead of/alongside the new LLM-judged Security-Review gate — worth noting as directionally
   aligned, but the ticket's own scope does not require building the fuller `verified_by`/static-verifier
   framework described in that doc, and Plan should not expand scope toward it.

## Anti-Drift Hazards

- **Status/phase-name uniqueness must be verified by grep, not assumed.** Before implementation, grep the
  whole file for the chosen failure status string (e.g. `SECURITY_BLOCKED`) and phase label (e.g.
  `'Security-Review'`) to confirm neither collides with any of the file's existing 7 distinct return
  `status` values (`CONFLICTS_DETECTED`, `EPIC_SCOPED`, `NEEDS_HUMAN_INPUT`, `NEEDS_CHANGES`, `BLOCKED`,
  `TESTS_FAILED`, `DOD_BLOCKED`, `DONE`) or 9 existing phase labels.
- **No monitoring-tooling code changes are needed** for the new `final_status`/phase name — confirmed no
  enum/allowlist exists in `record_run.py`/`record_events.py`/`validate.py`/`query.py`/`generate_retro.py`.
  Do not add one speculatively; that would be scope creep beyond this ticket.
- **The 1:1 `agentType` ↔ `.claude/agents/*.md` convention is a real, unbroken architectural pattern in this
  file** — if Plan chooses the inline-prompt route instead of a dedicated `security-reviewer.md`, that
  should be recorded as a deliberate, justified deviation (e.g. in Implementation Notes), not a silent
  first exception.
- **`mistag_warning` (or equivalent) becomes a 4th place carrying tag-related computation inside
  `implement-ticket.js`, alongside the existing triple-copy tag→skill mapping table already flagged as a
  drift risk by the sibling investigation.** It is *not* mirrored in `ticket-scoper.md` (Out of Scope
  forbids that) — record this asymmetry explicitly (e.g., a one-line comment in the JS, and a note in
  Implementation Notes) so a future reader doesn't assume `ticket-scoper.md` invoked standalone (outside
  this workflow) also computes it.
- **Keyword-list collision risk is specific to this codebase's vocabulary, not a generic security-keyword
  concern.** Do not reuse the list without the collision spot-checks documented above; if the list is later
  extended, re-run the same `grep -rli <term> src/` collision check before adding any new term.
