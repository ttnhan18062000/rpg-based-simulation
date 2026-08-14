---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-WORKFLOW-SECURITY-GATE
artifact_type: plan
tags: [tagging, security, workflows]
---

# Plan — TCK-20260705-WORKFLOW-SECURITY-GATE

## Summary

Add a `Security-Review` gate (new `security-reviewer` agent + schema + inert-by-default `if` block) right after Parity's `pushEvent` at `implement-ticket.js:550`, plus an independently-computed `mistag_warning` field on the Scope phase, then document both in the 3 named docs.

## Steps

### Step 1 — Create `.claude/agents/security-reviewer.md`

**Files:** `.claude/agents/security-reviewer.md` (new)

**Change:** Mirror `.claude/agents/architecture-reviewer.md`'s structure exactly (58-line pattern: Registry Lookup → checklist → Output), adapted for security instead of architecture:

- Header: `# Security Reviewer` + one-line role description ("You are a security review subagent for the rpg-based-simulation project. Given implemented code changes, you validate them for security vulnerabilities before Verify.").
- **Registry Lookup** section: same pattern as architecture-reviewer.md lines 5-9 — use `docs/REGISTRY.yaml` filtered by layer to find relevant active docs; fall back to the checklist below if the registry doesn't exist.
- **What to Review** checklist, covering exactly these categories (per investigation Recommendation 1, no more, no less):
  1. Injection (command/SQL/template injection in any new string-building code)
  2. Unsafe deserialization (`pickle`, `yaml.load` without `SafeLoader`, `eval`/`exec` on external input)
  3. Path traversal (unvalidated path joins/user-controlled file paths)
  4. Subprocess/command injection (`subprocess`/`os.system`/shell=True with unsanitized input)
  5. Secrets-in-code (hardcoded credentials, API keys, tokens committed to source)
  6. Raw-domain-model API exposure — **cross-reference** `architecture-reviewer.md`'s existing API-boundary rule by name/link rather than restating it (per investigation: this already overlaps architecture-reviewer's own rule and must not be duplicated).
- **Output** section: verdict enum `APPROVED` / `NEEDS_CHANGES` / `BLOCKED` (same 3-value shape as architecture-reviewer, for consistency — NOT reusing architecture-reviewer's own event/phase name, just the same enum shape), per-violation findings (which category, what the code does, the fix), and a `summary` field (one sentence ≤200 chars, goes into the agent monitoring event record — same convention as every other schema in this file).

**Do NOT touch:** `architecture-reviewer.md` itself (read-only reference) — do not restate its API-boundary rule verbatim, just point to it.

**Verify:** File exists, is well-formed markdown, and its Output verdict enum literally matches the 3 values used in Step 2's `SECURITY_REVIEW_SCHEMA`.

---

### Step 2 — Add `SECURITY_REVIEW_SCHEMA` + gate block + `meta.phases` row to `implement-ticket.js`

**Files:** `.claude/workflows/implement-ticket.js`

**Change (part A — `meta.phases`, lines 4-14):** Insert a new phase row after the `'Parity'` entry (line 11) and before `'Verify'` (line 12):
```js
{ title: 'Parity', detail: 'Update parity ledger entries for behavior changes' },
{ title: 'Security-Review', detail: "Security gate for security-tagged tickets — fires when the ticket's tags include 'security' (ground truth) or suggested_skills includes '/security-review' (skipped otherwise)" },
{ title: 'Verify', detail: 'Run Definition-of-Done checklist' },
```
Also update the top-of-file `description` string (line 3) only if it currently enumerates every phase name — check first; if it's already a short summary (e.g. "scope → investigate → plan → architecture review → implement → test → parity → done-check → finalize"), leave it as-is (out of scope to rewrite the whole description; the `phases` array is the structural source of truth the ticket's Related Docs note flagged as easy to miss, not the prose description).

**Change (part B — the gate itself, inserted after line 550 `pushEvent('Parity', ...)` and before line 552's blank line / line 554 `phase('Verify')`):**

```js
// ─── Phase 7b: Security-Review (conditional gate) ─────────────────────────────
// Trigger reads ticketInfo.tags (raw, required ground truth) directly rather than relying solely
// on the derived, optional suggested_skills field — per architecture-review finding #6: a gate meant
// to be "mandatory not advisory" must not depend on the same unenforced LLM-derived value that made
// the original signal advisory-only in the first place.

if ((ticketInfo.tags && ticketInfo.tags.includes('security')) ||
    (ticketInfo.suggested_skills && ticketInfo.suggested_skills.includes('/security-review'))) {
  phase('Security-Review')

  const SECURITY_REVIEW_SCHEMA = {
    type: 'object',
    required: ['verdict', 'violations', 'summary'],
    properties: {
      verdict: { type: 'string', enum: ['APPROVED', 'NEEDS_CHANGES', 'BLOCKED'] },
      violations: { type: 'array', items: { type: 'string' } },
      summary: { type: 'string', description: 'One sentence: verdict + key reason (≤200 chars)' },
      ts: { type: 'string', description: 'ISO timestamp from `date -u +%Y-%m-%dT%H:%M:%SZ` at start of this phase' },
    },
  }

  const securityReview = await agent(
    `Security review for ticket ${tid}.

Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\` and include result as the \`ts\` field.

Step 0b: run \`python3 -c "import json; open('.claude/current_run','w').write(json.dumps({'run_id':'${tid}','seq':${events.length + 1}}))" 2>/dev/null || true\` — register this agent call for tool tracking.

Read:
- ${ticketInfo.ticket_path}
- Files changed: ${implementation.files_changed.join(', ')}

This ticket is tagged \`security\` (its frontmatter tags include \`security\`, or suggested_skills includes /security-review). Review the actual diff/changed files for: injection, unsafe deserialization, path traversal, subprocess/command injection, secrets-in-code, raw-domain-model API exposure.

Return: APPROVED / NEEDS_CHANGES (fixable violations) / BLOCKED (fundamental vulnerability),
violations (empty if APPROVED), summary (one sentence: verdict + key reason, ≤200 chars), ts.`,
    { label: 'security-review', schema: SECURITY_REVIEW_SCHEMA, agentType: 'security-reviewer' }
  )

  if (securityReview.verdict !== 'APPROVED') {
    log(`Security review: ${securityReview.verdict}`)
    if (securityReview.violations.length > 0) {
      log(`Violations: ${securityReview.violations.join(' | ')}`)
    }
    pushEvent('Security-Review', 'security-reviewer', 'failed', securityReview.summary || 'Security review: ' + securityReview.verdict, securityReview.ts)
    await writeMonitoring('SECURITY_BLOCKED')
    return {
      status: 'SECURITY_BLOCKED',
      ticket_id: tid,
      violations: securityReview.violations,
      message: 'Fix violations, then re-run with ticket_id="' + tid + '".',
    }
  }

  pushEvent('Security-Review', 'security-reviewer', 'ok', securityReview.summary || 'Security review: APPROVED', securityReview.ts)
  log('Security review: APPROVED')
}
```

**Do NOT touch:** Any code inside the `if (tier !== 'hotfix') { ... } else { ... }` block (lines 242-405) — this new gate is unconditional on tier (fires for hotfix, standard, and epic-child tickets alike), triggered when the ticket's tags include `security` (ground truth) or `suggested_skills` includes `/security-review`, so it must live entirely between Parity's `pushEvent` and `phase('Verify')`, not inside the existing tier-conditional block. Do NOT add an `else` branch to the new `if` — no `pushEvent`, `log`, or agent call outside the trigger condition.

**Verify:** `node -c .claude/workflows/implement-ticket.js` exits 0. Grep confirms the new `if` block's closing brace is the only thing between Parity's `pushEvent('Parity', ...)` and `phase('Verify')`. Grep confirms zero `pushEvent`/`agent(`/`writeMonitoring(` calls exist outside that `if` in the inserted region. Grep confirms the trigger condition reads `ticketInfo.tags` (required, ground-truth) as well as `ticketInfo.suggested_skills` — not `suggested_skills` alone.

---

### Step 3 — Add `tags` (required, ground-truth backstop) and `mistag_warning` fields + compute inline in both Scope branches

**Files:** `.claude/workflows/implement-ticket.js`

**Change (part A0 — architecture-review-required fix, `TICKET_SCHEMA` at lines 29-43): promote raw `tags`
to a required schema field.** Architecture review found that the gate's original trigger
(`ticketInfo.suggested_skills.includes('/security-review')`) depends entirely on an *optional*,
LLM-derived field with no deterministic backstop — if the Scope-phase agent flakily omits or
miscomputes `suggested_skills` for a genuinely `security`-tagged ticket, the mandatory gate silently
never fires, with no error. `tags` (the raw ticket frontmatter list) is not on `TICKET_SCHEMA` at all
today — add it as a **required** property, mirroring `tier`'s existing required-field pattern:
```js
tags: { type: 'array', items: { type: 'string' }, description: 'The ticket frontmatter tags list, read directly — required so the Security-Review gate trigger (Step 2) has a ground-truth fallback independent of the derived suggested_skills field.' },
```
Add `'tags'` to `TICKET_SCHEMA.required` (line 31) alongside the existing 7 fields.

**Change (part A1 — schema, `mistag_warning`):** Add a new optional property (not in `required` — it must not force a schema-shape change that could break existing calls, and it is a warning field, not a hard requirement):
```js
mistag_warning: { type: 'boolean', description: 'True if Related Code Areas suggests auth/secrets/credential paths but no `security` tag was assigned. Computed independently in both Scope-phase branches, alongside the existing suggested_skills tag->skill mapping. NOT mirrored in ticket-scoper.md (Out of Scope for TCK-20260705-WORKFLOW-SECURITY-GATE forbids touching that file).' },
```

**Change (part B — "Load existing ticket" branch, inside the Step 3 instructions at lines 60-68):** After the existing tag→skill mapping table, add:
```
Step 3a — read the ticket's frontmatter `tags` field directly and return it verbatim as `tags` (do not
filter or transform it — this is the ground-truth list the Security-Review gate trigger reads).

Step 3b — check for a security mis-tag: if the ticket's "Related Code Areas" section contains any path or filename matching one of: `credential`, `secret`, `password`, `api_key`, `private_key`, `.env`, `oauth`, `jwt` (case-insensitive substring match; do NOT match `auth`, `cert`, `key`, `token`, or `session` bare — those collide with this codebase's own `AuthoritativeState`/`authoritative_pipeline`/`certification`/`LabSessionStore` vocabulary), AND the ticket's tags do NOT include `security` — set mistag_warning=true. Otherwise mistag_warning=false.
```
Add `tags=(from step 3a, the ticket's actual frontmatter tags list)` and `mistag_warning=(computed per step 3b)` to that branch's `Return:` line.

**Change (part C — "Create new ticket" branch, near line 116):** Add the identical keyword list and logic inline (this branch delegates ticket *creation* to `ticket-scoper`, but per Out of Scope this ticket must NOT touch `ticket-scoper.md` — so `mistag_warning` for this branch must be computed by `implement-ticket.js`'s own prompt text against the just-drafted ticket's Related Code Areas, exactly as `suggested_skills` is independently restated in this same branch today rather than trusted from `ticket-scoper.md`'s output alone). Add to that branch's `Return:` line: `tags=(the tags array written into the new ticket's own frontmatter — the same ground-truth reasoning as the Load-existing branch)` and `mistag_warning=(computed per the same keyword list as the Load-existing branch, [] if none)`.

**Change (part D — surfacing, after line 201's existing `suggested_skills` log block):**
```js
if (ticketInfo.mistag_warning) {
  log('WARNING: Related Code Areas suggests auth/secrets/credential-adjacent paths but no `security` tag was assigned — verify tagging is correct.')
}
```
Use `log(...)` only — never `pushEvent(...)` (critical constraint: this must add zero monitoring events for the non-triggering-tag case, per investigation Risk #3).

**Do NOT touch:** `.claude/agents/ticket-scoper.md`, `.claude/workflows/create-tickets.js` — Out of Scope forbids both.

**Verify:** Grep confirms `mistag_warning` is computed inline in both Scope branches' prompt text (not delegated to `ticket-scoper.md`). Grep confirms the only place `mistag_warning` triggers an action is a `log(...)` call — zero `pushEvent` references to `mistag_warning` anywhere in the file. Manual positive control (`src/api/auth/credentials.py`-style path) and negative controls (`src/engine/authoritative_pipeline.md`, `src/certification/harness.py`) per test_plan.md item 5.

---

### Step 4 — Update the 3 docs + run `make knowledge-index-update`

**Files:** `docs/ai/workflows.md`, `docs/ai/system_overview.md`, `docs/ai/ticket-lifecycle.md`

**Change — `docs/ai/workflows.md`:**
- In the `implement-ticket` **Phases** table (lines 78-88), add a row after `Parity` and before `Verify`:
  `| Security-Review | security-reviewer | Fires when the ticket's tags include `security` (ground truth) or suggested_skills includes /security-review; stops if NEEDS_CHANGES or BLOCKED |`
- In the **Return values** table (lines 108-116), add a row after `DOD_BLOCKED` and before `DONE`:
  `| SECURITY_BLOCKED | Security review rejected the change | Fix violations, re-run with ticket_id |`
  (Placement in the table should reflect actual gate order — Security-Review runs before Verify/DOD_BLOCKED, so consider ordering the row before `DOD_BLOCKED` instead, matching phase order like the Phases table above it. Use phase order, matching the convention the existing table already follows top-to-bottom.)

**Change — `docs/ai/system_overview.md`:**
- Section 3's phase-count prose (line 76-81, "The 9-phase `implement-ticket` pipeline...") — update to describe the gate as conditional, e.g.: "...→ Parity (`parity-updater`) → **Security-Review (`security-reviewer`, conditional: fires when the ticket's `tags` include `security` or `suggested_skills` includes `/security-review`; gate: `SECURITY_BLOCKED`)** → Verify (`done-checker`, gate: `DOD_BLOCKED`) → Finalize..." Do not change the "9-phase" framing to "10-phase" — the gate is conditional/non-standard, not a standing pipeline phase; note this distinction explicitly in prose (e.g. "a 10th, conditional phase").
- Line 96-97's "literal gate/return-status vocabulary" list — add `SECURITY_BLOCKED` to the enumerated list.
- Do NOT touch the Section 6 "Note (as of 2026-07-05)" dated disclosure about unrelated stale docs (`simq-audit`, `create-tickets` phase drift, etc.) — out of scope per investigation Risk #6; this ticket's edits must not expand that note's scope.

**Change — `docs/ai/ticket-lifecycle.md`:**
- **Overview** ASCII diagram (lines 30-81): insert a `[Security-Review]` block between `[Parity]` and `[Verify]`, following the existing block style, e.g.:
  ```
    ▼
  [Parity]         parity-updater    → docs/parity_ledger/*.yaml updated
    │
    ▼  (only if the ticket's tags include `security`, or suggested_skills includes /security-review)
  [Security-Review] security-reviewer → APPROVED / NEEDS_CHANGES / BLOCKED
    │
    ├─ NEEDS_CHANGES / BLOCKED → human fixes code, re-run with ticket_id
    │
    ▼
  [Verify]         done-checker      → DoD check (hotfix: condition 4 N/A)
  ```
- **Step-by-Step Detail** section: add a new `### Security-Review` subsection between `### Parity` (ends ~line 267) and `### Verify` (starts ~line 269), following the same subsection shape as `### Architecture Review` (Agent / What it validates / Gate), noting it only runs when triggered by the ticket's `tags` including `security` (ground truth) or `suggested_skills` including `/security-review`.
- **Failure Recovery Reference** table (lines 382-390): add a row: `| SECURITY_BLOCKED | Security review found a vulnerability | Fix the flagged code | Re-run with ticket_id |`

**Do NOT touch:** Any other section of these 3 files (e.g. Manual Execution section, Simulation Workflows section, Section 4/5 of system_overview.md) — scope is strictly the new gate's documentation, per investigation Risk #6.

**After edits:** Run `make knowledge-index-update` (CLAUDE.md rule — required whenever files under `docs/` are created or modified).

**Verify:** All 3 files still pass `tests/tools/test_validate_frontmatter.py` (frontmatter untouched — only body content edited). Re-read each edited section to confirm no accidental removal of adjacent unrelated content.

---

### Step 5 — Manual verification pass

No new file changes in this step — execute test_plan.md's checks and record results in the ticket's Test Summary:

1. `node -c .claude/workflows/implement-ticket.js` → exit 0.
2. Grep the new gate's `if` block — confirm `agent(...)`, `phase('Security-Review')`, both `pushEvent(...)` calls are the only reachable code inside it, and it sits between line ~550 (Parity's `pushEvent`) and `phase('Verify')`. Confirm the trigger condition checks `ticketInfo.tags.includes('security')` OR `ticketInfo.suggested_skills.includes('/security-review')` — not the derived field alone (architecture-review requirement: `tags` is now `required` on `TICKET_SCHEMA` and must be the primary ground-truth signal, with `suggested_skills` as a secondary/redundant check, not the sole trigger).
3. Grep for any `else` branch on the new `if` calling `pushEvent`/`agent`/monitoring — must find none. Grep for `pushEvent` anywhere referencing `mistag_warning` — must find none.
4. `grep -n "status: '" .claude/workflows/implement-ticket.js` and `grep -n "pushEvent('" .claude/workflows/implement-ticket.js` — confirm `SECURITY_BLOCKED` and `'Security-Review'` do not collide with any pre-existing status/phase string (baseline list in investigation.md's Anti-Drift Hazards: `CONFLICTS_DETECTED`, `EPIC_SCOPED`, `NEEDS_HUMAN_INPUT`, `NEEDS_CHANGES`, `BLOCKED`, `TESTS_FAILED`, `DOD_BLOCKED`, `DONE`).
5. Mis-tag WARNING: positive control (`src/api/auth/credentials.py`-style Related Code Areas entry, no `security` tag) → WARNING fires. Negative controls: `src/engine/authoritative_pipeline.md` and `src/certification/harness.py` → WARNING does NOT fire.
6. Confirm `make knowledge-index-update` was run after Step 4's doc edits.
7. Run regression pytest:
   ```
   python3 -m pytest tests/tools/test_validate_frontmatter.py tests/tools/test_registry_query.py -v
   ```
   Both must pass — `test_registry_query.py` is a negative control confirming `tools/registry_query.py` was not touched.

**Verify:** Record pass/fail for each of the 7 checks above in the ticket's Test Summary section.

## Scope Guards

- Do not touch `.claude/agents/ticket-scoper.md` or `.claude/workflows/create-tickets.js` (Out of Scope).
- Do not touch `.claude/workflows/implement-epic.js` (delegates automatically; zero plumbing needed).
- Do not touch `tools/registry_query.py` or its tests except as a negative-control regression check.
- Do not modify the tag→skill mapping table itself or any of the other 3 mapped tags (`api-design`/`debugging`/`performance`).
- Do not add any code inside the new gate's non-triggering path (no `else` branch pushing events/logs beyond what Step 3 already specifies for `mistag_warning`, which is separate from the gate's trigger `if`).
- Do not widen doc edits beyond documenting this new gate — do not fix pre-existing doc/code drift already disclosed in `system_overview.md` Section 6.
- Do not add enum/allowlist validation to `tools/agent-monitoring/*.py` for the new `final_status`/phase strings — confirmed unnecessary by investigation.
- Do not build the fuller `verified_by`/static-verifier framework from the (unscheduled) idea doc — out of scope.

## Dependency Map

- Step 1 (agent file) must land before Step 2, since Step 2's `agentType: 'security-reviewer'` references it.
- Step 2 (gate) and Step 3 (`mistag_warning`) are independent of each other (different code regions: Step 2 is post-Parity, Step 3 is in Scope phase) — either order is fine, but both must land before Step 5 (verification references both).
- Step 4 (docs) depends on Step 2's final status/phase names (`SECURITY_BLOCKED`, `Security-Review`) being finalized — do docs last, after Steps 1-3 are settled, to avoid documenting names that changed mid-implementation.
- Step 5 (manual verification) depends on Steps 1-4 all being complete.

## Acceptance Criteria Map

| Acceptance Criterion | Step(s) |
|---|---|
| Security-tagged ticket with a real vulnerability → gate fires, distinct failure status, no Verify/Finalize | Step 2 (trigger reads required `tags` ground-truth, not just derived `suggested_skills`), Step 3 |
| Security-tagged ticket, clean code → gate passes, unchanged DONE flow | Step 2 |
| No-`security`-tag ticket → zero added latency/agent calls/events (byte-identical events.jsonl) | Step 2 (no `else` branch), Step 5 check 3 |
| `events.jsonl` gets a distinctly-named phase entry, separable from `Review` | Step 2 (`'Security-Review'` phase label), Step 5 check 4 |
| `Related Code Areas` suggests auth/secrets but no `security` tag → visible WARNING log, not silent | Step 3 |
| `docs/ai/workflows.md`, `system_overview.md`, `ticket-lifecycle.md` updated same session | Step 4 |

## Anti-Drift Notes

- **The gate's trigger must never regress to checking only the derived `suggested_skills` field.**
  Architecture review's core finding: a "mandatory" gate that depends solely on an optional,
  LLM-derived value is not meaningfully different from the advisory mechanism it replaces. `tags` is
  now `required` on `TICKET_SCHEMA` specifically so the gate has a ground-truth fallback; any future
  edit that removes the `ticketInfo.tags.includes('security')` half of the trigger condition
  reintroduces the exact silent-non-fire risk this review round caught and fixed.
- `security-reviewer.md` must cross-reference (not duplicate) `architecture-reviewer.md`'s API-boundary rule for the raw-domain-model-exposure checklist item.
- The new gate is unconditional on tier (fires for hotfix/standard/epic-child alike) — it is gated on the ticket's `tags` including `security` (required, ground truth) or `suggested_skills` including `/security-review` (derived, secondary), not nested inside the `if (tier !== 'hotfix')` block. Implementer must place it structurally outside that block, immediately after Parity's `pushEvent` and before `phase('Verify')`.
- `mistag_warning` is a 4th place in this file independently computing tag-related logic (alongside the existing triple-copy `suggested_skills` mapping). Add a one-line code comment at the `mistag_warning` schema property noting this asymmetry, and note it in the ticket's Implementation Notes so a future reader doesn't assume `ticket-scoper.md` (invoked standalone, outside this workflow) also computes it.
- The mis-tag keyword list (`credential`, `secret`, `password`, `api_key`, `private_key`, `.env`, `oauth`, `jwt`) must never include bare `auth`, `cert`, `key`, `token`, `session` — any future extension to this list must re-run the `grep -rli <term> src/` collision check documented in investigation.md before adding a term.
- `SECURITY_BLOCKED` and `Security-Review` are plain strings with no monitoring-tooling enum protecting them from future reuse-for-a-different-meaning — this is accepted (matches every other status/phase name in this file) but should be spot-checked once after the first real run per test_plan.md's Anti-Drift Test Guards.

## Unresolved Questions

None. Both open items from the ticket's Assumptions/Open Questions section were resolved with evidence in investigation.md (dedicated `security-reviewer.md` agent file — adopted; standalone keyword list inline in `implement-ticket.js`, not `registry_query.py` — adopted) and are treated as decided inputs to this plan, not reopened here.

## Deviations

- Step 3, part C's literal text said to return `mistag_warning=(computed per the same keyword list as
  the Load-existing branch, [] if none)`. Since `mistag_warning` is schema-typed `boolean` (not an
  array), the implementer used `false if none` instead of `[] if none` in the "Create new ticket"
  branch's Return-line prompt text — a wording correction, not a behavior or schema change. All other
  steps were implemented exactly as written.
