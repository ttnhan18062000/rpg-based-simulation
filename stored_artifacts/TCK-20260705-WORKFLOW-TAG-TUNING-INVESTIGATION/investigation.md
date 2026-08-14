---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION
artifact_type: investigation
tags: [investigation, ai, workflows, tagging]
---

# Investigation — TCK-20260705-WORKFLOW-TAG-TUNING-INVESTIGATION

## Current Behavior

### Part 1 — tag → skill → step wiring (exact)

**Mapping table (identical in all 3 places it's defined):**

| Tag | Suggested skill | Defined at |
|---|---|---|
| `api-design` | `/api-design-principles` | `.claude/agents/ticket-scoper.md:86` |
| `debugging` | `/debugging-strategies` (or `Agent(subagent_type: "world-debugger")` if Related Code Areas overlaps `src/worldassembly/`, `src/worldbuilding/`, `src/worldmodules/`, `src/content/`, `src/core/registries.py`) | `.claude/agents/ticket-scoper.md:87` |
| `performance` | `/python-performance-optimization` | `.claude/agents/ticket-scoper.md:88` |
| `security` | `/security-review` | `.claude/agents/ticket-scoper.md:89` |

Same table restated verbatim in `docs/guides/ticket_tagging.md:30-35`, and inlined a third time inside `.claude/workflows/implement-ticket.js:62-67` (the "Load existing ticket" prompt branch). Three copies of one table — a drift risk noted under Anti-Drift Hazards.

**Where `suggested_skills` is computed (3 independent compute sites, one per producer):**

1. `.claude/agents/ticket-scoper.md:75-91` — Output item 5. This is the only place the mapping is defined as agent *instructions* rather than restated for a workflow prompt; single-ticket scoping (`ticket-scoper` invoked directly, or via `implement-ticket`'s "Create new ticket" branch) computes it here.
2. `.claude/workflows/create-tickets.js` — `TASK_SCHEMA` requires `suggested_skills` as a field (line 462-466); the Structure-phase prompt embeds the same 4-row table again at lines 595-604 and instructs the synthesis agent to compute it per batch-created ticket.
3. `.claude/workflows/implement-ticket.js` — `TICKET_SCHEMA` requires `suggested_skills` (line 39); computed in **both** Scope-phase prompt branches: "Load existing ticket" (lines 60-68, reads the ticket's frontmatter `tags` directly) and "Create new ticket" (line 116, delegates to `ticket-scoper`'s own Output contract).

**Where it is surfaced (log-only, confirmed no downstream consumer in either workflow):**

- `create-tickets.js:654-657` — after `droppedScopes` dedup, before the Write phase: `log(\`Suggested skills: ${tasksWithSkills...}\`)`. The `task` object (including `suggested_skills`) IS passed into the Write-phase agent prompt as `JSON.stringify(task, null, 2)` (line 702), but the explicit "Map task data to markdown sections" list at lines 722-737 has no entry for `suggested_skills` — only `tags` is written into ticket frontmatter. `suggested_skills` itself is never persisted to the `.md` file, never read by the Link phase (lines 844-868, which only appends ticket IDs to an epic's Related Tickets). **Confirmed: purely a log line with no downstream consumer anywhere in `create-tickets.js`.**
- `implement-ticket.js:199-201` — `if (ticketInfo.suggested_skills && ticketInfo.suggested_skills.length > 0) { log(...) }`, immediately after the Scope phase's `pushEvent` call. Grep of the entire file for `suggested_skills` (7 hits total) shows every occurrence is either schema declaration, prompt text computing it, or this one log block — **no phase after Scope (Investigate/Plan/Review/Implement/Test/Parity/Verify/Finalize) reads `ticketInfo.suggested_skills`.** Grep for `ticketInfo.tags` returns zero hits — raw `tags` is not even a field on the `TICKET_SCHEMA` returned object (only the derived `suggested_skills` is); `tags` only appears in prompt text describing the ticket frontmatter template (line 103, 60). **Confirmed: purely advisory/logged, identical pattern to `create-tickets.js`.**

`tier`, by contrast, IS read structurally downstream: `const tier = tierOverride || ticketInfo.tier || 'standard'` (line 123) is a plain JS property access on the same schema-typed object `suggested_skills` lives on, then branched on repeatedly (`tier === 'epic'` line 218, `tier !== 'hotfix'` line 242 and re-checked at 432/597/665/667-668). This proves the *mechanism* for tag-driven phase logic is already available — `tags` (or a derived boolean like `hasTag('security')`) would need to be added to `TICKET_SCHEMA`'s `required`/`properties` exactly the way `suggested_skills` was added by `TCK-20260705-TAG-SKILL-SUGGEST`, then read with the same `ticketInfo.<field>` pattern `tier` already uses. No new orchestration primitive is needed — only a schema field addition + a JS conditional, mirroring existing precedent line-for-line.

**Other 3 tag categories — do any drive workflow behavior?**

Per `docs/guidelines/tag_taxonomy.md:31-69` there are 4 categories: Subsystem/Topic, Phase/Milestone, Process/Skill-signal, Quality-attribute.

- **Process/Skill-signal** — the only category with any consumption logic at all, and even that is advisory-only (above).
- **Subsystem/Topic** — has exactly one piece of consumption logic, but it is a *search filter*, not a phase-skip/phase-change: `docs/guides/ticket_tagging.md:40-49` ("Tags as a Registry Search Filter") documents that `tools/registry_query.py`'s `candidate_tags_from_text`/`filter_registry` is used in `create-tickets.js`'s Investigate phase (lines 337-357, unioned with `layer`) and in `investigator.md`'s "Finding Prior Work" step, to narrow which `docs/REGISTRY.yaml` rows get read. It changes *what a phase reads*, never *whether a phase runs*.
- **Phase/Milestone** and **Quality-attribute** — confirmed **zero** consumption logic anywhere in `.claude/workflows/*.js` or `.claude/agents/*.md` (grep + full reads of the 3 files below found no reference). They are pure human-readable/retro-grouping categorization today, exactly as `tag_taxonomy.md`'s own "Purpose" section frames them (a controlled vocabulary "prerequisite for tags becoming an actual routing signal later" — the routing itself is explicitly out of scope of the taxonomy ticket that shipped them).

### Part 2 — exhaustive phase-skip/phase-change enumeration

**`.claude/workflows/implement-ticket.js` — every conditional that changes phase execution:**

1. `tier === 'epic'` (line 218) — short-circuits the entire pipeline after Scope; returns `EPIC_SCOPED` before Investigate ever runs. The **only** tier value with this behavior.
2. `tier !== 'hotfix'` (line 242, closing `else` at 400) — gates whether Investigate/Plan/Review (phases 2-4) execute at all. The `else` branch (400-405) substitutes placeholder values (`investigation`, `plan`, `review` pre-set at lines 229-240) and pushes 3 `'skipped'` events instead of calling any agent.
3. Re-checks of the *same* `tier` value (not new conditionals, but tier-dependent prompt content inside phases that always run): Implement phase reads `plan.md` vs. the ticket directly (line 432); Verify phase's prompt tells `done-checker` to mark Condition 4 as N/A for hotfix (lines 596-598, prompt-level, not JS-level); Finalize branches on `tier !== 'hotfix'` for the working-log `artifacts_path` value (line 665) and whether to move `staging_artifacts/` or delete it if accidentally created (lines 667-668).
4. `planText.toLowerCase().includes('unresolved question')` (line 322) — content-based gate (`NEEDS_HUMAN_INPUT`), not tag/tier-driven.
5. `review.verdict !== 'APPROVED'` (line 383) — gate (`NEEDS_CHANGES`/`BLOCKED`), driven by architecture-reviewer's own judgment, not ticket metadata.
6. `!testResult.passed` (line 497) — gate (`TESTS_FAILED`).
7. `doneCheck.verdict !== 'READY_TO_CLOSE'` (line 611) — gate (`DOD_BLOCKED`).
8. `implementation.behavior_changed` ternary inside the Parity-phase prompt (line 534) — the **closest existing analog** to a "docs-only skip": when false, the prompt tells `parity-updater` to only verify `test_path` references rather than update ledger entries. Critically, **this does not skip the phase** — `parity-updater` is still invoked (line 521's `agent(...)` call always runs), it just receives different instructions. The trigger, `implementation.behavior_changed`, is the **implementer's own post-hoc self-report** (a boolean in `IMPL_SCHEMA`, line 416) — not a ticket tag, not `tier`, and not `Related Code Areas`.

Grep confirms no other JS-level conditional in this file references `tags`, `type`, `priority`, `layer`, or `Related Code Areas` content to change *which* phases run or *whether* an agent is invoked. `priority` and `layer` are never even read as JS variables in this file (only appear inside prompt text templates for ticket frontmatter).

**`.claude/workflows/implement-epic.js` — every conditional:**

This file has **no tier/tag-driven phase-skip logic of its own** — it wholly delegates tier handling to `implement-ticket.js` via `workflow('implement-ticket', ticketArgs)` (line 191), passing through only `tier_override` unmodified (line 187). Its own conditionals are orchestration-level, not phase-skip: `if (result.status !== 'DONE') { ...break }` (line 203, sequential-batch stop-on-failure) and `if (batchStatus === 'DONE' && folder)` (line 258, folder-archival cleanup gate). Confirms: any future tuning built inside `implement-ticket.js` automatically applies to `implement-epic` runs with zero additional plumbing, since every child ticket is dispatched through the same `implement-ticket` workflow.

**Agent files checked for self-contained tag/tier-awareness (all read in full, none found):**

- `.claude/agents/test-scoper.md` — scopes purely from the changed-file list handed to it; no reference to tags, tier, `behavior_changed`, or a "docs-only" concept anywhere in the file. It has no self-narrowing logic — it always attempts a `src/` → `tests/unit/` mapping regardless of ticket type.
- `.claude/agents/parity-updater.md` — the agent's own Output/What-to-Do sections contain no tag/tier read; the only conditional behavior it exhibits comes from the *calling* prompt inside `implement-ticket.js` (item 8 above), not from anything in its own `.md` definition.
- `.claude/agents/architecture-reviewer.md` — no tag/tier awareness; reviews whatever plan it is handed against the fixed architecture-boundary/mechanics/engine/parity checklist unconditionally.

**Empirical confirmation (this session's own recent tickets):** `tickets/done/TCK-20260705-AI-AGENT-OVERVIEW-DOC.md`'s Test Summary shows a full pytest run (`tests/tools/test_validate_frontmatter.py`, 64 passed) was still executed for a documentation-only change — because the changed doc's frontmatter is covered by real test surface (`tests/tools/`). `tickets/done/TCK-20260705-WORKING-LOG-BACKFILL.md` and `tickets/done/TCK-20260705-SIX-SKILLS-INVESTIGATION.md` both show Parity/Test phases concluding trivially ("N/A", "no pytest suite applies") but **still ran the full agent call** to reach that conclusion — matching Part 2 finding #8 exactly (the phase always executes; only its internal conclusion is cheap for docs-only work).

## Mechanics / Engine Constraints

N/A — this is a pure agent-tooling/workflow-orchestration investigation. No simulation mechanics, Mechanics Bible chapter, or Engine Contract governs `.claude/workflows/*.js` or `.claude/agents/*.md` behavior; those docs constrain `src/` simulation logic, not the Claude Code agent harness.

## Parity Ledger Overlap

N/A — the parity ledger (`docs/parity_ledger/`) tracks doc↔code parity for simulation subsystems (combat, economy, cognition, etc.). This investigation touches none of those subsystems; it is scoped entirely to `.claude/` and `docs/ai/`/`docs/guidelines/`/`docs/guides/` tooling docs, which have no parity ledger entries.

## Prior Work

- **`TCK-20260705-TAG-SKILL-SUGGEST`** (done) — shipped the exact mapping table and 3 compute sites this investigation traces (Part 1). Its own **Out of Scope** section already anticipated and explicitly deferred Candidate 1 below: *"Auto-invoking a skill without a suggestion step... Actually triggering a suggested skill remains a decision made by whoever is running the pipeline."* This investigation does not re-litigate that decision — it re-surfaces it for the user with a feasibility/risk assessment now that the mechanism has shipped and been observed in production use.
- **`TCK-20260705-TAG-REGISTRY-QUERY`** (sibling, done) — built the Subsystem/Topic registry-search-filter consumer (`tools/registry_query.py`) referenced in Part 1's "other 3 categories" finding. Not re-derived here, only cross-referenced.
- **`TCK-20260705-AI-AGENT-OVERVIEW-DOC`** — the consolidated `docs/ai/system_overview.md` narrative used to confirm the 9-phase pipeline, tier-routing table, and the `implementation.behavior_changed`-driven Parity-phase ternary; cross-referenced, not duplicated.

## Risks and Open Questions

Four candidate tunings assessed below (the 4 named in ticket Scope), each against: trigger / change / feasibility / risk / recommendation.

---

**Candidate 1 — Auto-invoke suggested skill during Implement (e.g. `performance` tag → actually run `/python-performance-optimization`, not just log it)**

- *Trigger*: `ticketInfo.suggested_skills` non-empty at Scope (already computed, `implement-ticket.js:199`).
- *Change*: Implement-phase prompt (`implement-ticket.js:424-452`) would need to instruct the `implementer` agent to apply the suggested skill's guidance, or the JS orchestrator would need a new invocation step before/around `phase('Implement')` (line 409).
- *Feasibility*: Medium. `suggested_skills` values are heterogeneous — 3 are skill slash-commands (`/api-design-principles`, `/python-performance-optimization`, `/security-review`) and one is an `Agent(subagent_type: "world-debugger")` string (the `debugging` carve-out) — so a generic "invoke `suggested_skills[0]`" JS branch needs a dispatch table distinguishing skill-invocation from agent-invocation. None of the workflow files observed (`create-tickets.js`, `implement-ticket.js`, `implement-epic.js`) call a `Skill`/slash-command primitive from JS today — skills are user-facing, invoked when Claude reads a `SKILL.md` and calls `Workflow` itself (`docs/ai/skills.md:16-26`). The only realistic near-term implementation is prompting the `implementer` agent to itself read and apply the skill's guidance inline — which is delegation, not a true JS-level auto-invoke.
- *Risk*: Moderate-high, and it does bear on "no silent scope creep" (`docs/ai/README.md`'s Design Principles). Tags are LLM-self-assigned at Scope time and never human-verified before Implement runs; auto-expanding Implement's declared behavior (write code per the *already-architecture-reviewed* plan) to silently include a full skill's workflow means the `architecture-reviewer`'s `APPROVED` verdict (Review phase, line 383) was given against a plan that did not describe the auto-invoked step. This is exactly the failure mode the "Hard gates" principle exists to prevent — a step appearing after the gate that the gate never saw.
- *Recommendation*: **Defer.** `TAG-SKILL-SUGGEST`'s own Out of Scope already named this as a future, separate decision. No cost/benefit contrary evidence has accumulated yet (would need retro data showing suggestions are being ignored when they shouldn't be); build only after (a) a JS-callable skill-invocation primitive exists, and (b) retro evidence justifies the token cost.

---

**Candidate 2 — `security`-tagged ticket requires a mandatory `/security-review` gate before Verify**

- *Trigger*: `ticketInfo.suggested_skills.includes('/security-review')` — **already valid JS today**, no new schema field needed (unlike a tuning that reads raw `tags` directly, this one piggybacks on the field `TAG-SKILL-SUGGEST` already added to `TICKET_SCHEMA`).
- *Change*: insert a new gated phase between Test/Parity and Verify — structurally, right before `phase('Verify')` (`implement-ticket.js:554`), following the exact pattern of the existing Review gate (schema with `verdict` enum, `pushEvent`, early-return on fail) at lines 340-399.
- *Feasibility*: **High** — the only candidate of the 4 requiring zero new plumbing (no schema addition, no new orchestration primitive). It's a copy-paste of an existing, proven gate shape.
- *Risk*: Low-moderate, and this one is additive (a new hard gate) rather than a skip — it strengthens rather than weakens the "Hard gates" principle. The residual risk is a false negative: a ticket touching auth/secrets logic that `ticket-scoper` never tagged `security` (tag assignment is best-effort NL matching, not exhaustive) silently never gets the gate — but this is the same pre-existing risk profile every tag-driven mechanism in this system already carries, not a new risk category introduced by this candidate.
- *Recommendation*: **Build now** — of the 4 candidates, the most ready: small, additive, gate-only (never skips anything), directly analogous to a shipped pattern. Should log a visible `WARNING` (not a silent no-op) when Related Code Areas suggests auth/secrets/credential-adjacent paths but no `security` tag was assigned, to surface the mis-tag risk rather than hide it.

---

**Candidate 3 — Skip/narrow Parity for tickets with no `src/` in Related Code Areas**

- *Trigger, evaluated at two different times with very different safety profiles*:
  - **Scope-time** (`Related Code Areas`, human/LLM-authored *before* Investigate/Implement run) — **unsafe**. This is exactly the false-negative scenario the ticket itself warns about: a ticket scoped as "docs only" can still touch `src/` once Implement actually runs (scope drift `architecture-reviewer`/`done-checker` already have to catch elsewhere) — pre-committing to "no Parity" before Implement even executes would silently skip Parity for a ticket that turns out to have real behavior changes.
  - **Implement-time** (`implementation.files_changed`, a `IMPL_SCHEMA`-required field returned by the `implementer` agent, `implement-ticket.js:415`) — **safe and already structured data**. `implementation.files_changed.some(f => f.startsWith('src/'))` is a one-line, authoritative, post-Implement check.
- *Change*: this candidate does not need to invent new logic from scratch — the Parity phase **already** branches on `implementation.behavior_changed` (line 534, Part 2 finding #8), it just never skips the *agent call itself*, only softens the prompt. The tuning is: skip the `agent(...)` invocation at line 521 entirely (replacing it with a synthetic "not applicable" result + a `pushEvent(..., 'skipped', ...)`) when `implementation.files_changed.every(f => !f.startsWith('src/')) && !implementation.behavior_changed` — i.e., require **both** signals to agree, never trust either alone.
- *Feasibility*: High — reuses data already computed and passed by the time Parity phase starts; no new agent, no new schema field on `IMPL_SCHEMA` (it's already there).
- *Risk*: Low, **conditioned on** gating on `implementation.files_changed` (post-Implement, authoritative) and never on Scope-time `Related Code Areas`. The saved cost is modest — one skipped `parity-updater` call for genuinely docs-only tickets — but it is a real, bounded win precisely because the trigger data is authoritative rather than a pre-Implement guess.
- *Recommendation*: **Build now**, narrowly scoped to the post-Implement `files_changed`-based check exactly as described — do not implement any Scope-time variant of this candidate.

---

**Candidate 4 — Skip/narrow Test scope-detection for docs-only tickets, analogous to Candidate 3**

- *Trigger*: same `implementation.files_changed` data, evaluated the same way.
- *Change*: would skip or shortcut `phase('Test')` (`implement-ticket.js:458`) and the `test-scoper` invocation at line 475 when `files_changed` has no `src/` paths.
- *Feasibility*: mechanically identical to Candidate 3 (same data already available).
- *Risk*: **Higher than Candidate 3, and this session's own evidence directly falsifies the "docs-only ⇒ no test surface" premise.** `tickets/done/TCK-20260705-AI-AGENT-OVERVIEW-DOC.md`'s Test Summary shows a real pytest run (`tests/tools/test_validate_frontmatter.py`, 64 passed) was correctly executed for a `docs/`-only change, because frontmatter-validation tooling (`tests/tools/`) covers doc content directly. Parity ledger entries only concern `src/` simulation behavior, so "no `src/` changed" is a sound proxy for "Parity not applicable" (Candidate 3) — but tests exist for non-`src/` tooling too, so "no `src/` changed" is **not** a sound proxy for "no test surface applies" (Candidate 4). A naive port of Candidate 3's rule to Test would have produced a false PASS with zero verification on that exact ticket.
- *Recommendation*: **Reject** the general form. `test-scoper` should keep running unconditionally for any non-empty `files_changed`. The only safe variant — skip when `files_changed.length === 0` exactly — is a near-null-value edge case (Implement almost always changes at least one file) and not the common docs-ticket pattern actually observed, so it is not worth building.

---

**Summary of build recommendations**: Candidate 2 (security gate) and Candidate 3 (Parity skip on authoritative post-Implement data) are both build-now, low-risk, and reuse existing schema/data with no new plumbing. Candidate 1 (auto-invoke) is defer — needs a skill-invocation primitive and retro evidence first. Candidate 4 (Test skip) is reject — directly contradicted by this session's own evidence.

## Anti-Drift Hazards

- **Triple-copy mapping table.** The tag→skill table exists verbatim in 3 places (`ticket-scoper.md:84-89`, `ticket_tagging.md:30-35`, `implement-ticket.js:62-67`). Any future tuning that changes the mapping (e.g. adding a 5th tag, or changing `security`'s target skill) must update all three or the sources will silently diverge — there is no single source of truth today.
- **Tags are unverified LLM output.** Every candidate above that keys off a tag (Candidates 1, 2) inherits the same underlying risk: `ticket-scoper`/`create-tickets.js`'s Structure phase assign tags via best-effort natural-language matching, not exhaustive or human-reviewed classification. Any hard gate or skip built on a tag should assume the tag can be wrong in either direction (false positive costs tokens; false negative silently skips a safeguard) and should log visibly rather than fail silently in the false-negative direction.
- **`implement-epic.js` needs no separate changes.** Because it delegates entirely to `implement-ticket.js` per child ticket (no tier/tag logic of its own — Part 2 finding), any tuning built inside `implement-ticket.js` automatically applies epic-wide with zero additional work. Do not duplicate a tuning into `implement-epic.js`.
- **Doc/code phase-count drift already exists and will worsen if untracked.** `docs/ai/system_overview.md`'s own Section 6 dated note (2026-07-05) already flags that `docs/ai/workflows.md` is stale for 4 of 11 workflows' phase lists. Any tuning that adds/removes a phase in `implement-ticket.js` (e.g. Candidate 2's new gate) must update `docs/ai/workflows.md`, `docs/ai/system_overview.md` (Section 3's phase table), and `docs/ai/ticket-lifecycle.md` in the same session, or this drift grows.
- **Monitoring accounting for skipped phases.** Any phase-skip (Candidates 3/4 if ever built) must still call `pushEvent(..., 'skipped', ...)` — CLAUDE.md's Hard Rule requires at least one event entry per run, and the existing hotfix-tier skip pattern (lines 401-404) already establishes the convention to follow.
