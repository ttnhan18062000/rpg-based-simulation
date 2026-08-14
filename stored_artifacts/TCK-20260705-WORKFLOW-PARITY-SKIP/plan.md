---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-WORKFLOW-PARITY-SKIP
artifact_type: plan
tags: [workflows, observability]
---

# Plan — TCK-20260705-WORKFLOW-PARITY-SKIP

## Summary

Add a standalone testable
`tools/parity_ledger_scan.py` P0-safeguard scan, then wrap the existing (byte-unmodified) Parity
`agent(...)` call at `implement-ticket.js:542-567` in an `if/else` keyed on
`implementation.files_changed`/`implementation.behavior_changed`, and update the 3 docs + this file's own
`meta.phases` entry to match the Security-Review sibling's precedent style exactly.

## Steps

### Step 1 — REMOVED per architecture review (do not edit `.claude/skills/implement-ticket/SKILL.md`)

**Architecture-review finding, applied:** the original Step 1 proposed adding a new `orchestratorBash`
row to `SKILL.md`'s translation table — a file that governs how *every* phase of *every* future ticket
gets executed, not just this Parity-phase change. This is out of this ticket's declared Related Code
Areas (`implement-ticket.js`, `docs/parity_ledger/*.yaml` only) and is a bigger precedent than a single
new pseudocode word: it would be the first-ever instance of the orchestrator running Bash directly
outside a spawned `agent(...)` call anywhere in this file.

**Narrower alternative (adopted instead, matches existing precedent):** the sibling
`TCK-20260705-WORKFLOW-SECURITY-GATE` ticket documented its own trigger nuance via a plain JS comment at
the call site (`implement-ticket.js:574-577`), not by expanding the shared execution vocabulary. Step 5
below does the same: an inline comment instructs the orchestrating session to run the Bash command
directly, no new agent, no SKILL.md edit — relying on `.claude/skills/implement-ticket/SKILL.md`'s
existing Action step 1 ("Read `.claude/workflows/implement-ticket.js` in full before doing anything
else"), which already requires the orchestrator to read and interpret every comment in the file,
including this one, without needing a formal table entry.

**Do NOT touch:** `.claude/skills/implement-ticket/SKILL.md` at all, in this ticket.

---

### Step 2 — Create `tools/parity_ledger_scan.py` (P0 safeguard, standalone + testable)

**Files:** `tools/parity_ledger_scan.py` (new)

**Change:** Mirror `tools/registry_query.py`'s style (pure functions, module docstring explaining the
ticket/consumer, no CLI/`argparse`, no `__main__` block — consumed via `python3 -c "..."` exactly like
`registry_query.py` is consumed at `.claude/workflows/create-tickets.js:340-357`).

```python
"""Substring scan of P0 parity-ledger entries' v2_evidence against a changed-files list.

Built for TCK-20260705-WORKFLOW-PARITY-SKIP: the Parity phase in `.claude/workflows/implement-ticket.js`
skips its `parity-updater` agent call when a ticket touches no `src/` file and reports no behavior
change. Before that skip is allowed to fire, `find_p0_intersection` checks that no P0 ledger entry's
`v2_evidence` text already depends on one of the ticket's changed files — protecting a P0 entry from
silently going stale. Scans only the 8 canonical parity-ledger files the Parity phase prompt itself
lists (`implement-ticket.js` Parity agent call); `faction.yaml` is excluded — not one of the 8, and has
0 P0 entries today (see investigation.md's Parity Ledger Overlap table).

This check is empirically inert today (no P0 `v2_evidence` currently cites a non-`src/`/non-`tests/`
path — see investigation.md), but must still be implemented for real: it protects against future ledger
entries that could violate that invariant.

Assumes `files_changed` paths and `v2_evidence` path citations use the same repo-relative,
forward-slashed form (consistent with how `files_changed` is populated everywhere else in
implement-ticket.js today) — a path written with a different form (absolute, backslashed) would not
be matched by this substring check.
"""

import yaml
from pathlib import Path

CANONICAL_LEDGER_FILES = (
    "substrate.yaml",
    "combat_movement.yaml",
    "strategic_cognition.yaml",
    "town_resource.yaml",
    "progression.yaml",
    "social_narrative.yaml",
    "world_dynamics.yaml",
    "infrastructure.yaml",
)


def find_p0_intersection(files_changed, ledger_dir="docs/parity_ledger"):
    """Return (ledger_filename, entry_id, changed_path) triples for every P0 entry whose `v2_evidence`
    text contains one of `files_changed` as a substring. Empty list means no P0 entry depends on any
    changed file — the caller may safely skip the Parity agent call.

    Only scans CANONICAL_LEDGER_FILES — never `faction.yaml` or any other file under `ledger_dir`.
    """
    ledger_path = Path(ledger_dir)
    hits = []
    for filename in CANONICAL_LEDGER_FILES:
        path = ledger_path / filename
        if not path.exists():
            continue
        entries = yaml.safe_load(path.read_text()) or []
        for entry in entries:
            if entry.get("priority") != "P0":
                continue
            evidence = entry.get("v2_evidence") or ""
            if not evidence:
                continue
            for changed_path in files_changed:
                if changed_path and changed_path in evidence:
                    hits.append((filename, entry.get("id"), changed_path))
    return hits
```

**Do NOT touch:** `tools/registry_query.py` (read-only reference), any file under `docs/parity_ledger/`
(read-only — this module only reads, never writes), `docs/parity_ledger/faction.yaml` /
`docs/parity_ledger/schema.json` (out of the canonical 8, must not be scanned).

**Verify:** `python3 -c "import sys; sys.path.insert(0,'tools'); from parity_ledger_scan import find_p0_intersection, CANONICAL_LEDGER_FILES; print(len(CANONICAL_LEDGER_FILES))"` prints `8`. A real run
`find_p0_intersection(['docs/ai/workflows.md'])` returns `[]` (matches investigation's empirical
invariant).

---

### Step 3 — Add `tests/tools/test_parity_ledger_scan.py`

**Files:** `tests/tools/test_parity_ledger_scan.py` (new)

**Change:** Mirror `tests/tools/test_registry_query.py`'s import-path-shim pattern. Cover exactly the 3
cases test_plan.md requires:

```python
"""Tests for tools/parity_ledger_scan.py."""

import sys
from pathlib import Path

import yaml

_TOOLS_DIR = Path(__file__).parent.parent.parent / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from parity_ledger_scan import find_p0_intersection, CANONICAL_LEDGER_FILES  # noqa: E402


def _write_ledger(tmp_path, filename, entries):
    (tmp_path / filename).write_text(yaml.safe_dump(entries))


def test_detects_p0_intersection_via_synthetic_fixture(tmp_path):
    # Positive control: none of the real ledger's current P0 entries can exercise this branch
    # (investigation.md's empirical finding), so this uses a synthetic fixture.
    _write_ledger(tmp_path, "substrate.yaml", [
        {
            "id": "SUB-001", "text": "x", "status": "verified", "priority": "P0",
            "v2_evidence": "Verified in `src/core/state.py` (IdentityComponent)",
            "test_path": "tests/unit/test_x.py",
        },
    ])
    hits = find_p0_intersection(["src/core/state.py"], ledger_dir=str(tmp_path))
    assert hits == [("substrate.yaml", "SUB-001", "src/core/state.py")]


def test_no_intersection_for_representative_docs_only_change():
    # Negative control against the real 8-file ledger.
    hits = find_p0_intersection(["docs/ai/workflows.md"], ledger_dir="docs/parity_ledger")
    assert hits == []


def test_only_scans_canonical_eight_not_faction(tmp_path):
    _write_ledger(tmp_path, "faction.yaml", [
        {
            "id": "FAC-001", "text": "x", "status": "verified", "priority": "P0",
            "v2_evidence": "src/factions/diplomacy.py",
            "test_path": "tests/unit/test_y.py",
        },
    ])
    hits = find_p0_intersection(["src/factions/diplomacy.py"], ledger_dir=str(tmp_path))
    assert hits == []
    assert "faction.yaml" not in CANONICAL_LEDGER_FILES
```

**Do NOT touch:** `tests/tools/test_registry_query.py` (read-only reference pattern).

**Verify:** `python3 -m pytest tests/tools/test_parity_ledger_scan.py -v` — all 3 tests pass.

---

### Step 4 — Update `meta.phases`'s `'Parity'` entry (in-file consistency with Security-Review precedent)

**Files:** `.claude/workflows/implement-ticket.js` (lines 4-14, the `meta.phases` array)

**Change:** The sibling `TCK-20260705-WORKFLOW-SECURITY-GATE` ticket updated this same array's own new
`'Security-Review'` row to describe its conditional trigger inline (current line 12). Match that
precedent for `'Parity'` (currently line 11):

Before:
```js
    { title: 'Parity', detail: 'Update parity ledger entries for behavior changes' },
```
After:
```js
    { title: 'Parity', detail: 'Update parity ledger entries for behavior changes — skips the parity-updater agent call when files_changed has no src/ path and behavior_changed is false (a P0 ledger safeguard can force it to run anyway)' },
```

**Do NOT touch:** Any other row in `meta.phases` (Scope through Finalize), `meta.name`, `meta.description`.

**Verify:** `grep -n "'Parity'" .claude/workflows/implement-ticket.js` shows the updated detail string;
`node -c .claude/workflows/implement-ticket.js` still exits 0.

---

### Step 5 — Wrap the Parity `agent(...)` call in the skip condition + lazy P0 safeguard

**Files:** `.claude/workflows/implement-ticket.js` (lines 540-571, the entire Parity phase body)

**Change:** Replace lines 540-571 with the block below. The existing `agent(...)` call (prompt text and
options) is copied **byte-for-byte unmodified** into the `else` branch — do not reword, do not touch the
ternary at lines 555-563, do not change the schema/label/agentType.

```js
phase('Parity')

// Skip-eligible only when BOTH post-Implement signals agree: no src/ file touched AND no reported
// behavior change. Reads implementation.* (post-Implement, authoritative) — never ticketInfo/Scope-time
// fields, so mid-run scope drift (a ticket that turns out to touch src/ once Implement runs) always
// forces the full call, never the skip.
const parityNoSrcChange = implementation.files_changed.every(f => !f.startsWith('src/'))
const paritySkipEligible = parityNoSrcChange && !implementation.behavior_changed

let parityForceFullRun = false
if (paritySkipEligible) {
  // Lazy P0 safeguard — only runs in this rare skip-eligible branch, zero cost on the common
  // (non-skip) path. The orchestrating session runs this Bash command directly itself — do NOT
  // spawn a new agent() for it (a sub-agent call here would defeat the point of the optimization).
  // Each changed path is passed as its own shell argument (never embedded as a JSON blob inside the
  // quoted -c script) — embedding `${JSON.stringify(implementation.files_changed)}` directly inside
  // the double-quoted `python3 -c "..."` string causes the shell to strip the JSON array's own
  // double quotes (since they're unescaped and nested inside the same quote style), corrupting the
  // script into a Python NameError and causing this check to silently fail open. Passing paths as
  // trailing argv elements (each independently shell-quoted) avoids that collision entirely.
  const filesChangedArgs = implementation.files_changed.map(f => `"${f}"`).join(' ')
  const p0ScanOutput = await bash(
    `python3 -c "
import sys
sys.path.insert(0, 'tools')
from parity_ledger_scan import find_p0_intersection
hits = find_p0_intersection(sys.argv[1:])
print('P0_INTERSECTION_FOUND' if hits else 'P0_NO_INTERSECTION')
if hits: print(hits)
" ${filesChangedArgs}`
  )
  parityForceFullRun = p0ScanOutput.includes('P0_INTERSECTION_FOUND')
}

if (paritySkipEligible && !parityForceFullRun) {
  log('Parity: no src/ changes and no reported behavior change — skipping parity-updater agent call.')
  pushEvent('Parity', 'parity-updater', 'skipped', 'No src/ changes and behavior_changed=false — parity ledger unaffected')
} else {
  const parity = await agent(
    `Update parity ledger for ticket ${tid}.

Step 0: run \`date -u +%Y-%m-%dT%H:%M:%SZ\`. Your response MUST begin with this exact line (nothing before it):
PHASE_TS: <result>

Step 0b: run \`python3 -c "import json; open('.claude/current_run','w').write(json.dumps({'run_id':'${tid}','seq':${events.length + 1}}))" 2>/dev/null || true\` — register this agent call for tool tracking.

Behavior changed: ${implementation.behavior_changed}
Parity subsystems affected: ${(implementation.parity_subsystems || []).join(', ') || 'check implementation summary'}
Parity entries from architecture review: ${review.parity_entries_affected.join(', ') || 'none pre-identified'}
Implementation: ${implementation.implementation_summary}

${implementation.behavior_changed
  ? `Update docs/parity_ledger/ entries (files: substrate.yaml, combat_movement.yaml, strategic_cognition.yaml, town_resource.yaml, progression.yaml, social_narrative.yaml, world_dynamics.yaml, infrastructure.yaml).

Rules:
- behavior matches Mechanics Bible → status=verified, update v2_evidence (file:line), set test_path
- intentional divergence → status=divergent, update divergence_note, add to docs/guidelines/v2_intentional_divergences.md
- new behavior with no entry → add entry with next available ID for the prefix
- P0 entries MUST have a non-null test_path pointing to a now-passing test`
  : `No observable behavior change reported. Verify this is accurate by checking whether any referenced parity entries need test_path updates (e.g., tests were renamed or moved). Report what you checked.`}

Then report: entries updated (by ID and what changed), any P0 entries missing a test_path.`,
    { label: 'parity-update', agentType: 'parity-updater' }
  )

  const parityTs = parity.toString().match(/^PHASE_TS: (\S+)/m)?.[1] || null
  const parityText = parity.toString().replace(/^PHASE_TS: \S+\n?/, '').trim()
  pushEvent('Parity', 'parity-updater', 'ok', parityText.slice(0, 200), parityTs)
}
```

Critical correctness note for the implementer: use the two distinct, non-overlapping tokens
`P0_INTERSECTION_FOUND` / `P0_NO_INTERSECTION` exactly as written above. Do **not** use bare
`'INTERSECTION'` / `'NO_INTERSECTION'` as the pair — `"NO_INTERSECTION".includes("INTERSECTION")` is
`true` in JS, which would make `parityForceFullRun` true on every skip-eligible ticket (silently
defeating the entire optimization). This is a real, non-hypothetical bug trap — verify the exact strings
before considering this step done.

**Do NOT touch:** The Security-Review block (lines 573-629, immediately following), `IMPL_SCHEMA` (432-443),
the Test phase (479-536), `implement-epic.js`, any `docs/parity_ledger/*.yaml` content, the ternary at
lines 555-563 (softening wording — keep exactly as-is), the agent prompt text/schema/label/agentType for
the Parity `agent(...)` call.

**Verify:**
1. `node -c .claude/workflows/implement-ticket.js` exits 0.
2. `git diff .claude/workflows/implement-ticket.js` shows the `else` branch's `agent(...)` call body is
   character-identical to the pre-change lines 542-567 (only indentation from the new wrapping block
   changes, no prompt text/schema/option changes).
3. Hand-trace the 3 synthetic cases from test_plan.md items 3/4/5 against the new condition:
   - `files_changed: ['docs/foo.md', 'src/core/state.py']`, `behavior_changed: false` →
     `parityNoSrcChange` is `false` → `paritySkipEligible` is `false` → full agent call fires. (AC 2)
   - `files_changed: ['config/simulation_quality/profiles/foo.yaml']`, `behavior_changed: true` →
     `parityNoSrcChange` is `true` but `!implementation.behavior_changed` is `false` →
     `paritySkipEligible` is `false` → full agent call fires. (AC 3)
   - `files_changed: ['docs/ai/workflows.md']`, `behavior_changed: false` → `paritySkipEligible` is
     `true`; P0 scan (Step 2's `find_p0_intersection`) returns `[]` today → `parityForceFullRun` stays
     `false` → skip branch fires, `pushEvent('Parity', 'parity-updater', 'skipped', ...)` recorded. (AC 1)
4. **Shell-quoting fix, verify directly** (architecture-review finding): construct the actual Bash
   command with a realistic `files_changed` array (e.g. `['docs/ai/workflows.md', 'tickets/done/TCK-...']`)
   and run it for real — confirm it prints `P0_NO_INTERSECTION` (not a Python traceback). Do NOT accept
   an implementation that embeds `JSON.stringify(implementation.files_changed)` directly inside the
   double-quoted `python3 -c "..."` string — that form is confirmed broken (shell strips the embedded
   JSON's own double quotes, causing a `NameError` and making the safeguard silently fail open). Confirm
   the actual code uses `sys.argv[1:]` with each path passed as its own trailing, independently-quoted
   shell argument.

---

### Step 6 — Update `docs/ai/workflows.md` (Parity row)

**Files:** `docs/ai/workflows.md` (line 86)

**Change:**

Before:
```
| Parity | `parity-updater` | — |
```
After:
```
| Parity | `parity-updater` | Skipped when `files_changed` has no `src/` path and `behavior_changed` is false; a P0 ledger safeguard forces the full run instead if any P0 entry's `v2_evidence` would go stale |
```

**Do NOT touch:** Any other row in this table, the `**Args:**`/`**Usage:**` sections below it.

**Verify:** `grep -n "Skipped when" docs/ai/workflows.md` shows the new cell text.

---

### Step 7 — Update `docs/ai/system_overview.md` (phase-chain description)

**Files:** `docs/ai/system_overview.md` (line 78, the one-line phase-chain sentence)

**Change:** Match the existing bolded-parenthetical style already used for Security-Review in the same
sentence (lines 78-81).

Before:
```
→ Implement (`implementer`) → Test (`test-scoper`, gate: `TESTS_FAILED`) → Parity (`parity-updater`) →
**Security-Review (`security-reviewer`, conditional: fires when the ticket's `tags` include `security`
```
After:
```
→ Implement (`implementer`) → Test (`test-scoper`, gate: `TESTS_FAILED`) →
**Parity (`parity-updater`, conditional agent call: skipped when `files_changed` has no `src/` path and
`behavior_changed` is false, unless a P0 ledger safeguard forces it to run)** →
**Security-Review (`security-reviewer`, conditional: fires when the ticket's `tags` include `security`
```

Note: Parity remains a standing (always-announced) phase — only its `agent(...)` call is conditional, not
the phase itself (unlike Security-Review, which is a fully conditional 10th phase). Word the surrounding
prose so it does not imply the phase count changed from "9 standing phases plus one conditional gate" —
only add a clause distinguishing "the agent call is conditional" from "the phase is conditional" if the
existing paragraph's phase-count claim (lines 82-84) would otherwise read as contradicted.

**Do NOT touch:** The tier-routing table (line 90), the `create-tickets` 5-phase description above it, the
`Sync Docs → Parity Check → Verify → Report` line (169) — that is a different pipeline
(`investigate-simulation-result` or similar), not `implement-ticket`'s Parity phase.

**Verify:** `grep -n "conditional agent call" docs/ai/system_overview.md` shows the new clause; re-read
lines 76-85 as a whole to confirm the phase-count sentence still reads correctly.

---

### Step 8 — Update `docs/ai/ticket-lifecycle.md` (ASCII diagram + Parity prose section)

**Files:** `docs/ai/ticket-lifecycle.md` (diagram ~line 66, prose section ~lines 261-271)

**Change A — diagram**, matching the existing conditional-annotation style used immediately below for
Security-Review (lines 67-68):

Before:
```
[Parity]         parity-updater    → docs/parity_ledger/*.yaml updated
  │
  ▼
```
After:
```
  ▼  (agent call skipped if files_changed has no src/ path and behavior_changed is false — a P0 ledger
      safeguard forces the full run instead if any P0 entry's v2_evidence would go stale)
[Parity]         parity-updater    → docs/parity_ledger/*.yaml updated
  │
  ▼
```

**Change B — prose section** (lines 261-271), add one paragraph after the existing bullet list, mirroring
the explanatory paragraph already used for Security-Review (line 278):

```
**Skipped when:** `files_changed` has no `src/` path and `behavior_changed` is false — the
`parity-updater` agent call is replaced with a `skipped` event. A P0 ledger safeguard checks first that
no P0 entry's `v2_evidence` depends on a changed file; if it does, the full agent call runs anyway.
```

**Do NOT touch:** The worked example at lines 425-438 (`# 7. Parity` — `behavior_changed: true` case,
still accurate as the non-skip path), the tier-routing table (line 22), any other numbered/lettered
section.

**Verify:** `grep -n "Skipped when" docs/ai/ticket-lifecycle.md` shows the new prose line; the diagram
still renders as plain-text-aligned (no column misalignment from the added annotation line).

---

### Step 9 — Run `make knowledge-index-update`

**Files:** None directly (regenerates the knowledge-search index).

**Change:** Run `make knowledge-index-update` after Steps 6-8 land, per CLAUDE.md's "If any files under
`docs/` were created or modified" rule.

**Do NOT touch:** Do not hand-edit any generated index file.

**Verify:** Command exits 0.

---

### Step 10 — Manual verification pass (test_plan.md items 1-9)

**Files:** None (verification only).

**Do:**
1. `node -c .claude/workflows/implement-ticket.js` — exit 0.
2. Re-confirm the skip condition text is exactly `implementation.files_changed.every(f =>
   !f.startsWith('src/')) && !implementation.behavior_changed` in spirit (as the two-variable
   `parityNoSrcChange && !implementation.behavior_changed` form) and reads only `implementation.*`.
3. Re-run the 3 hand-traced synthetic cases from Step 5's Verify block.
4. Confirm P0 safeguard runs only inside `if (paritySkipEligible)` — never unconditionally.
5. Confirm `parityForceFullRun` can actually route into the full `agent(...)` call (not just log) —
   trace the `if (paritySkipEligible && !parityForceFullRun) { skip } else { full call }` branch by hand
   for `parityForceFullRun = true`.
5b. **Actually execute the P0-safeguard Bash command** (not just read it) with a realistic non-empty
    `files_changed` list — confirm it prints `P0_NO_INTERSECTION` cleanly, with no Python traceback.
    This is the single most important check in this step: the original draft of this command silently
    crashed on every real invocation (confirmed by architecture review) because it embedded a raw JSON
    array inside a double-quoted shell string; a hand-trace alone would not have caught this, only
    actually running the command does.
6. Diff the `pushEvent('Parity', 'parity-updater', 'skipped', ...)` call shape against
   `pushEvent('Investigate', 'investigator', 'skipped', 'Hotfix tier — investigation skipped')` — same
   4-arg shape, no `ts` argument.
7. `git diff` on `implement-ticket.js` — confirm the `else` branch's agent call body is unchanged from
   the pre-change file.
8. Confirm `make knowledge-index-update` was run after doc edits.
9. Confirm `agent-monitoring/events.jsonl`/`tools.jsonl` handling is untouched (no code changes to
   `tools/agent-monitoring/*.py`).
10. `python3 -m pytest tests/tools/test_parity_ledger_scan.py tests/tools/test_validate_frontmatter.py -v`
    — all pass.

**Verify:** All items above pass; no `src/` files touched anywhere in this ticket's diff (this ticket's
own `files_changed` should end up being `.claude/`, `tools/`, `tests/tools/`, `docs/ai/` paths only —
ironically itself a "no-`src/`" change, but note `implementation.behavior_changed` for the workflow's own
future self-application should be reported `true`, since this changes the Parity phase's actual runtime
behavior — do not let this ticket's own Implement-phase report `behavior_changed: false` just because it
touches no `src/` file; workflow-orchestration behavior change still counts as a behavior change for this
ticket's own honesty, even though `docs/parity_ledger/*.yaml` has no entry for workflow-orchestration
logic itself).

## Scope Guards

- Do not touch `implement-epic.js` — it delegates entirely to `implement-ticket.js`; the skip applies
  epic-wide automatically.
- Do not touch the Test phase (`implement-ticket.js:479-536`) or build any "skip Test for docs-only
  tickets" logic — explicitly out of scope (falsified by `TCK-20260705-AI-AGENT-OVERVIEW-DOC`).
- Do not touch how `implementation.behavior_changed` is computed/reported by the `implementer` agent —
  this ticket only adds a new consumer of the existing field.
- Do not touch the Security-Review gate (`implement-ticket.js:573-629`) — confirmed structurally
  independent, no shared state with this change.
- Do not implement a Scope-time (pre-Implement) variant of this skip — explicitly rejected as unsafe.
- Do not build the P0 safeguard as a full-scan-every-run or a pre-built/cached index — must be lazy
  (skip-eligible-branch-only) per investigation's explicit recommendation.
- Do not let the P0 safeguard degrade to a warning/log-only check — it must be able to force the full
  agent call.
- Do not scan `docs/parity_ledger/faction.yaml` or `docs/parity_ledger/schema.json` in the P0 safeguard —
  only the 8 canonical files.
- Do not modify any `docs/parity_ledger/*.yaml` content — read-only for this ticket.

## Dependency Map

- Step 1 is a no-op (removed per architecture review — no SKILL.md edit in this ticket).
- Step 2 (`tools/parity_ledger_scan.py`) must land before Step 3 (tests import it) and before Step 5 (the
  JS `python3 -c` snippet imports it).
- Step 3 (tests) depends on Step 2 only.
- Step 4 (`meta.phases` edit) and Step 5 (Parity body edit) are both in `implement-ticket.js` — do them in
  the same pass to avoid two separate diffs to the same file; Step 4 has no code dependency on Step 5.
- Steps 6, 7, 8 (docs) depend on Step 5 being finalized (so the described condition text matches the
  actual code) but are independent of each other and of Steps 1-4.
- Step 9 (`make knowledge-index-update`) depends on Steps 6-8 completing.
- Step 10 (manual verification) depends on all prior steps.

## Acceptance Criteria Map

| Ticket Acceptance Criterion | Step(s) |
|---|---|
| Docs-only ticket → Parity agent call skipped, `events.jsonl` shows `skipped` | Step 5, Step 10 (#3, #6) |
| Scope-drift ticket (Implement touches `src/`) → Parity still runs full | Step 5, Step 10 (#3) |
| `behavior_changed: true` but no `src/` path → Parity still runs full | Step 5, Step 10 (#3) |
| No P0 `v2_evidence` path ever touched by a skipped ticket (explicit check) | Step 2, Step 3, Step 5, Step 10 (#4, #5) |
| Ticket that DOES need Parity sees zero change from today's flow | Step 5 (byte-identical `else` branch), Step 10 (#7) |

## Anti-Drift Notes

- The `P0_INTERSECTION_FOUND` / `P0_NO_INTERSECTION` token pair in Step 5 is deliberately
  non-overlapping — do not "simplify" it back to `'INTERSECTION'`/`'NO_INTERSECTION'`, which silently
  breaks the check (see Step 5's Critical correctness note).
- The P0 safeguard (Step 2) is expected to always return `[]` against the real ledger today — this is a
  known, documented, *inert-but-required* invariant (investigation.md's Parity Ledger Overlap section),
  not a sign the check is unnecessary or can be stubbed out.
- **No `SKILL.md` edit in this ticket** (architecture-review finding, applied) — the P0 safeguard's
  direct-Bash-no-agent instruction lives as an inline JS comment at the call site (Step 5), mirroring
  the Security-Review sibling ticket's own precedent for documenting a call-site nuance without
  expanding the shared execution-contract file. Do not resurrect the `orchestratorBash`
  SKILL.md-table-row idea as part of this ticket.
- **Shell-quoting fix (architecture-review finding, applied):** the P0 safeguard's changed-file list
  must be passed as individually-quoted trailing shell arguments (`sys.argv[1:]` in the Python script),
  never embedded as a raw `JSON.stringify(...)` blob inside the double-quoted `python3 -c "..."` string
  — the latter causes the shell to strip the JSON array's own embedded double quotes, corrupting the
  script and making the safeguard silently fail open (confirmed by direct reproduction). Do not revert
  to the JSON-embedding form.
- Step 4's `meta.phases` edit is not separately called out in the ticket's own Scope/Acceptance Criteria,
  but directly mirrors the sibling Security-Review ticket's own Step 2 ("part A — meta.phases") in the
  same file — include it for consistency, not as scope creep.
- Step 7's doc wording must preserve the existing "9 standing phases plus one conditional gate
  (Security-Review)" framing — do not let the new Parity clause imply a phase-count change; only the
  agent call within the Parity phase is conditional, the phase itself still always runs (and is still
  announced/logged) for every ticket.
- Do not update `docs/agent-monitoring/schema.md`'s `'skipped'` status example list (line 105) — it is
  already generic ("e.g. Investigate/Plan/Review for hotfix tier") and not one of the ticket's named 3
  docs; extending it is out of scope.

## Unresolved Questions

None. All open items from investigation.md's Risks and Open Questions section (P0-safeguard mechanism:
lazy orchestrator-run scan, not full-scan-every-run or pre-built index) are resolved with a concrete
implementation above. If a future reviewer disagrees with making the P0 scan a standalone
`tools/parity_ledger_scan.py` module (vs. an ad-hoc inline Bash one-liner, which test_plan.md offered as
an alternative), that is a style preference, not an open architectural question — the standalone-module
route was chosen because it is independently unit-testable (satisfying CLAUDE.md's Testing Rule for a
safeguard that must demonstrably be able to block, not just warn), matching `tools/registry_query.py`'s
established precedent in this same codebase.
