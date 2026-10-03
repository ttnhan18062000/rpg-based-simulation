---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260804-AGENT-DEF-GAP-FIXES
artifact_type: plan
tags: [ai, agent-monitoring]
---

# Implementation Plan — TCK-20260804-AGENT-DEF-GAP-FIXES

## Summary

This plan lands three independent, additive prose/regex fixes to close the gaps investigation.md
found via fresh agent-monitoring evidence (15 Review / 25 Verify failures since 2026-07-20): (1)
`.claude/agents/planner.md` gains three concrete, checkable fact-verification sub-instructions
covering the three distinct failure modes the fresh sample actually showed (source-claim/schema
errors, missing concurrent-writer analysis, AC-vs-plan self-contradiction); (2)
`.claude/agents/implementer.md` gains an explicit "before returning" ticket-hygiene checklist
covering Completion Summary, Files Changed, AC-checkbox discipline, and — the new pattern this
session's fresh pull surfaced — `## Status` field currency; (3) the "Docs Requiring Update"
bullet-format trap is fixed at its actual root cause in the parser
(`tools/gate_checks/done_checker_static.py`'s `_parse_docs_to_update`/`check_docs_to_update_coverage`),
not by adding prose guidance to `.claude/agents/investigator.md`.

**Correction from architecture-review (this plan revision):** this step's first draft fixed
`_DOCS_BULLET_RE`'s handling of a `:line` suffix inside the bullet's backticks, on the theory that
a `path:line` bullet-format bug caused the 3 fresh Verify failures this ticket's Scope cites
(`TCK-20260803-DOCS-STRUCTURE-AUDIT`, `TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE`,
`TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION`) — a theory investigation.md itself asserted
("the exact same bug class" as the separately-found `TCK-20260804-EXPANSION-RATE-WIRING` bug).
architecture-review independently checked the real `agent-monitoring/events.jsonl` evidence text
for all 4 cited tickets and found this theory unsupported for the actual 3-ticket pattern; this
revision re-verified that finding directly (not taken on faith — see Decision section below) and
confirms the dominant, currently-recurring cause is a different bug: `_DOCS_NONE_PHRASES`'s
exact-match check (`done_checker_static.py:309`) rejects `"None. <extra rationale sentence>"`
because it is not byte-identical to `"none."`, falls through to the bullet regex (which finds no
bullet in trailing prose), and FAILs. The corrected Step 3 below fixes that exact-match
intolerance and leaves `_DOCS_BULLET_RE` untouched. A fourth step adds regression tests
reproducing the actual observed failure text, and a fifth updates
`docs/ai/agent_definition_gap_audit_2026-08-04.md` with a ticket-specific "how to check if this
worked" pointer, satisfying AC5.

## Decision — Item 3 (Docs Requiring Update bullet-format trap): parser fix, targeting the None-phrase exact-match check, not the bullet regex

**Independent re-verification (this plan revision), not taken on architecture-review's word alone.**
Read `tools/gate_checks/done_checker_static.py:308-368` and `:371-426` directly (current file
state, not investigation.md's paraphrase of it):

- `_DOCS_NONE_PHRASES = {"", "none", "none.", "n/a"}` (line 309) is an **exact-match** set, used
  twice: `_parse_docs_to_update` (line 366, `section_text.strip().lower() in _DOCS_NONE_PHRASES`)
  and duplicated identically in `check_docs_to_update_coverage` (line 409). If an investigator
  writes `"None. <extra rationale sentence>"` instead of exactly `"None."`, both checks are
  `False`. Execution falls through to `_DOCS_BULLET_RE.findall(section_text)` (line 368), which
  finds zero bullets (there is no `- \`docs/...\`` line in trailing prose), so
  `_parse_docs_to_update` returns `[]`. `check_docs_to_update_coverage`'s `if not required_docs:`
  branch (line 408) then re-checks the same exact-match test, which *also* fails, and returns
  `FAIL: "'## Docs Requiring Update' section is non-empty but no docs/ path could be parsed from
  it"` (line 411-416) — this is the exact mechanism, confirmed by reading the code, not inferred.
- Queried `agent-monitoring/events.jsonl` directly (`grep` the ticket ID, parse each row's
  `summary` field as JSON) for the real logged Verify-phase failure text of all 4 cited tickets:
  - `TCK-20260803-DOCS-STRUCTURE-AUDIT` (Verify, `status: failed`): `"BLOCKED - 1 item failing:
    investigation.md's Docs Requiring Update section fails the static none-phrase/bullet parser
    due to trailing rationale prose."` — an exact, unambiguous match to the None-phrase
    exact-match bug, not a `:line`-suffix bug.
  - `TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE`: `"...fails static format parse."` — generic
    wording, does not itself distinguish the two candidate mechanisms.
  - `TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION`: `"...malformed Docs Requiring Update
    section."` — generic, same caveat.
  - `TCK-20260804-EXPANSION-RATE-WIRING` — the 4th ticket, and *not* one of the 3-count pattern
    (investigation.md's own text frames it separately: "independently found and fixed ad hoc
    during this session's own `TCK-20260804-EXPANSION-RATE-WIRING` ticket"): `"BLOCKED -
    docs_to_update_coverage failed on investigation.md bullet format (:line baked inside
    backticks), substance confirmed correct."` — this one genuinely IS the `:line`-suffix bug.
- Cross-checked against the *current* (post-fix) `stored_artifacts/*/investigation.md` "Docs
  Requiring Update" section content for all 4: the 3 pattern tickets now read exactly `"None."`
  with zero bullets — consistent with a fix that trimmed trailing prose down to the bare
  recognized phrase (the None-phrase theory), not one that edited a bullet's `:line` suffix
  (which would still show a bullet). `EXPANSION-RATE-WIRING`'s current section, by contrast,
  retains a real bullet with the line number moved into the prose reason text outside the
  backticks — consistent with its own logged `:line`-suffix description.
- Checked `git log --oneline --all` for each pattern ticket's `investigation.md`: all landed in a
  single squashed commit — the pre-fix failing version was never itself committed, so the
  events.jsonl summary text is the only surviving record and is treated as authoritative (it is
  the done-checker gate's own logged evidence, not a later reconstruction).

**Conclusion — both bugs are real, but only one is in this ticket's evidenced scope.** The
None-phrase exact-match intolerance of trailing prose is the confirmed, dominant cause of the
3-occurrence pattern this ticket's AC4/Scope enumerates (`DOCS-STRUCTURE-AUDIT` confirmed
directly; the other 2 are consistent with, not contradicted by, the same mechanism per the
current-section-content check above). The `:line`-suffix-inside-backticks bug is also real
(confirmed for `EXPANSION-RATE-WIRING`), but that ticket is not one of the 3 counted in this
ticket's Scope, and was already worked around ad hoc (hand-editing that one ticket's
investigation.md, not the parser) — `_DOCS_BULLET_RE`'s greedy capture therefore remains live and
unfixed in the codebase today. Per the planner's scope-discipline rule ("note adjacent problems as
future tickets — do not add them to this plan"), this is flagged in Anti-Drift Notes as a
future-ticket candidate, not folded into Step 3.

**Design choice for the None-phrase fix — Option (b), a targeted prefix-then-remainder check:**

Option (a) (`section_text.strip().lower().startswith(("none", "n/a"))`) is too permissive: it
would treat `"None of the above tickets apply, but docs/foo.md needs updating"` as "no docs to
update" even when a real path follows — a new, opposite-direction false-PASS gap this ticket's
scope (closing a false-FAIL gap) does not license. This is not purely theoretical: investigator
prose commonly opens narrative sentences with "None of the..." framing, so a bare prefix match
would silently swallow a genuine doc-update requirement whenever that phrasing happens to be used.

Chosen: **Option (b)** — a new `_is_none_section(section_text)` helper that (1) keeps the existing
exact-match fast path unchanged, then (2) if the text starts with a `None`/`N/A` prefix
(case-insensitive, optional trailing period), checks whether the *remainder* after that prefix
contains a `- \`docs/...\`` bullet. No bullet in the remainder → treat the whole section as "none"
(closes the real observed gap). A bullet IS found → do not treat as none; normal bullet-parsing
proceeds on the full text (preserves detection of "None of the above, but here's one," closing
option (a)'s risk). See Step 3 for the exact code; verified against 5 hand-run cases (real
observed failure text, prefix-with-real-bullet, the 5 existing exact-phrase variants, existing
non-None unparseable prose, and an existing multi-bullet section) before finalizing this plan.

**Reasoning for the parser fix over the investigator.md-guidance fix** (unaffected by which
parser bug is being fixed, carried forward from the original decision):

1. **Root cause, not symptom.** The bug is a parser condition too narrow for real investigator
   writing patterns, not that agents don't know the "right" format.
2. **Lower drift risk.** This same investigation independently found (investigation.md's "Prior
   Work" section) that prose-guidance fixes to `.claude/skills/*.md`/`.claude/agents/*.md` have a
   documented recurring-drift pattern in this project. A parser fix has no such drift surface.
3. **Scope discipline.** The ticket's Out of Scope section names `investigator.md` as in-scope
   "only if Plan chooses the agent-guidance route" — choosing the parser route keeps
   `investigator.md` untouched.

Per the ticket's out-of-scope constraint, this decision still means
**`.claude/agents/investigator.md` is NOT touched by this plan** — Step 3 below is scoped
entirely to `tools/gate_checks/done_checker_static.py`.

## Steps

### Step 1 — planner.md: add three concrete fact-verification sub-instructions

**Files:** `.claude/agents/planner.md`

**Change:** Insert a new section titled `## Fact-Verification Requirements (Before Writing plan.md)`
immediately after the existing `## Planning Rules` section (i.e., after the line ending "...parity
ledger P0 entries)." and before the `## Output` section). Insert this exact text:

```markdown
## Fact-Verification Requirements (Before Writing plan.md)

Fresh evidence (agent-monitoring, Review-phase failures since 2026-07-20) shows plans failing
review for three distinct, recurring reasons. Before writing `plan.md`, satisfy all three:

1. **Cite source for every behavioral or schema claim.** Before asserting how existing code
   currently behaves, or that a field/attribute/key exists on a schema, dataclass, or payload
   referenced by a proposed change, open and read the actual definition — do not infer it from a
   name, a docstring, or how a similar-looking thing works elsewhere. In the relevant Step's
   **Change** text, cite the `file:line` you read to support the claim. If you cannot find the
   file/field you're about to assert exists, say so as an open question instead of asserting it.
2. **Enumerate every other writer to a shared resource.** If a step touches a file, registry,
   counter, log, or any other resource that other code paths also write to concurrently or at
   different pipeline phases, the step's **Change** text must explicitly list every other writer
   to that resource and state how the proposed change interacts with each one (ordering, races,
   collisions, double-counting) — not just describe the change as if it were the only writer.
3. **Cross-check the ticket's own Acceptance Criteria against this plan's own Steps.** Immediately
   before finishing `plan.md`, re-read every AC in the ticket and confirm each AC's stated field
   names, values, and behavior match what the plan's Steps section actually proposes to build. A
   plan that satisfies an AC by name but contradicts it in a step's implementation detail (e.g. the
   AC references one field name, a step's Change text references a different one) must be
   corrected before the plan is returned, not left for Review to catch.
```

**Do NOT touch:** `## Inputs`, `## What a Good Plan Looks Like`, the `## Output` frontmatter/structure
template, or `## Planning Rules` itself — this is a new, additive section, not a rewrite of
existing sections.

**Verify:** Manual re-read of `planner.md` post-edit (test_plan.md row 1) — confirms the three
sub-instructions are present, concrete (each names a specific artifact to check: source file,
list of writers, AC-vs-Steps cross-check), and map to the three failure modes investigation.md's
"What kind of verification would have caught each sampled Review failure" section identified.

### Step 2 — implementer.md: add a "before returning" ticket-hygiene checklist

**Files:** `.claude/agents/implementer.md`

**Change:** Insert a new section titled `## Before Returning — Ticket Hygiene Checklist`
immediately after the existing `## After Writing Code` section (i.e., after the line "If you
discover a conflict with the plan or an architectural issue mid-implementation, stop and report it
— do not work around it silently.") and before `## Background Commands`. Insert this exact text:

```markdown
## Before Returning — Ticket Hygiene Checklist

Fresh evidence (agent-monitoring, Verify-phase failures since 2026-07-20) shows four specific,
recurring hygiene gaps in `tickets/inprogress/{ticket_id}.md` at the point implementer work ends.
Before ending your turn, confirm all four are true — do not return until each is satisfied:

- [ ] **`## Completion Summary`** no longer reads the placeholder `(filled during Finalize)` — it
  states in 2-4 sentences what was actually implemented, consistent with what you report in
  "Files Changed" below and in your structured output's `implementation_summary`.
- [ ] **`## Files Changed`** lists every file path you created, edited, or deleted for this ticket
  — not only the "primary" file the plan named, and not only files matching the plan's original
  guess if the real diff touched more or fewer files.
- [ ] **Acceptance Criteria checkboxes** — for each `- [ ]` in the ticket's `## Acceptance
  Criteria`, re-read what you actually implemented and check `- [x]` any AC genuinely satisfied.
  Leave a box unchecked if it is genuinely not yet satisfied — never check a box to make the
  ticket look more complete than it is.
- [ ] **`## Status`** — update it to reflect current reality (e.g. away from a stale `OPEN` left
  over from Scope, to whatever value correctly reflects that implementation work has landed). A
  stale `## Status` field is, on its own, a Verify-gate failure independent of the other three
  items above — do not treat it as cosmetic.

If any of the four cannot be completed truthfully (a step was skipped, an AC is not actually
satisfied, a file's status is ambiguous), say so explicitly in your structured report rather than
silently leaving the ticket file inconsistent with reality.
```

**Do NOT touch:** `## Architecture Constraints (Non-Negotiable)`, `## Code Quality Rules`,
`## Source Directory Reference`, or `## Background Commands` — this is a new, additive section
inserted between two existing ones, not a rewrite. Do NOT add `data/runs/` cleanup guidance here —
investigation.md confirmed that cause is stale (`TCK-20260708-DATA-RUNS-CLEANUP-TIMING` already
fixed it 2026-07-08, zero fresh occurrences); re-adding it would contradict the fresh evidence.

**Verify:** Manual re-read of `implementer.md` post-edit (test_plan.md row 2) — confirms the
checklist covers all four items (Completion Summary, Files Changed, AC discipline, Status
currency) matching the fresh-evidence pattern counts (6 AC / 5 Status / 4 Completion-Summary-gap).

### Step 3 — done_checker_static.py: make the None-phrase check tolerant of trailing rationale prose

**Files:** `tools/gate_checks/done_checker_static.py`

**Change:**
1. Immediately after the existing module-level constants at lines 308-309:
   ```python
   _DOCS_BULLET_RE = re.compile(r"^-\s+`(docs/[^`]+)`", re.MULTILINE)
   _DOCS_NONE_PHRASES = {"", "none", "none.", "n/a"}
   ```
   add a new constant and a new helper function (leave both existing lines above completely
   unchanged — this is a pure addition):
   ```python
   _DOCS_NONE_PREFIX_RE = re.compile(r"^(none|n/a)\.?\s*", re.IGNORECASE)


   def _is_none_section(section_text: str) -> bool:
       """True if section_text should be treated as "no docs/ paths flagged."

       Two cases both count:
       1. An exact recognized none-phrase (`_DOCS_NONE_PHRASES`, case-insensitive,
          whitespace-stripped) — the original, still-supported exact form.
       2. A leading "None."/"N/A" prefix (case-insensitive, optional trailing period) followed by
          trailing rationale prose that itself contains no `- \`docs/...\`` bullet line. This
          tolerates the real observed failure mode (TCK-20260804-AGENT-DEF-GAP-FIXES
          investigation, corrected by architecture-review): an investigator writing
          "None. <extra rationale sentence>" instead of exactly "None." — see plan.md's Decision
          section for the confirmed real-ticket evidence (`TCK-20260803-DOCS-STRUCTURE-AUDIT`'s
          own logged Verify-failure text). A "None"-led opening that is in fact followed by a real
          bullet (e.g. "None of the above, but `docs/foo.md` needs updating") still correctly
          requires that path — case 2 only fires when no bullet is found in the remainder.
       """
       stripped = section_text.strip()
       if stripped.lower() in _DOCS_NONE_PHRASES:
           return True
       m = _DOCS_NONE_PREFIX_RE.match(stripped)
       if not m:
           return False
       remainder = stripped[m.end():]
       return _DOCS_BULLET_RE.search(remainder) is None
   ```
2. In `_parse_docs_to_update` (currently lines 358-368), replace the exact-match check:
   ```python
       if section_text.strip().lower() in _DOCS_NONE_PHRASES:
           return []
       return _DOCS_BULLET_RE.findall(section_text)
   ```
   with:
   ```python
       if _is_none_section(section_text):
           return []
       return _DOCS_BULLET_RE.findall(section_text)
   ```
   Also update the docstring's last sentence — replace "Returns `[]` for an empty section or a
   recognized "none applicable" phrase (case-insensitive)." with: "Returns `[]` for an empty
   section, a recognized "none applicable" phrase (case-insensitive, exact match), or a
   "None."/"N/A"-prefixed section whose remaining text contains no docs/ bullet — tolerates
   trailing rationale prose after "None." (see `_is_none_section`, TCK-20260804-AGENT-DEF-GAP-FIXES)."
3. In `check_docs_to_update_coverage` (currently lines 371-426), replace the duplicated exact-match
   re-check at line 409:
   ```python
           if section_text.strip().lower() in _DOCS_NONE_PHRASES:
               return ("PASS", "no docs/ paths flagged as requiring update")
   ```
   with:
   ```python
           if _is_none_section(section_text):
               return ("PASS", "no docs/ paths flagged as requiring update")
   ```
   This is the exact call site that produced the real observed FAIL (`"'## Docs Requiring Update'
   section is non-empty but no docs/ path could be parsed from it"`) for the 3 fresh tickets —
   fixing both this and `_parse_docs_to_update`'s check keeps the module's two None-phrase checks
   from re-diverging (they were already duplicated before this change; `_is_none_section`
   consolidates both call sites onto one shared definition instead of two copies of the same
   exact-match logic).

**Do NOT touch:** `_DOCS_BULLET_RE` itself, `_git_touched_paths`, or `_path_touched` — per the
Decision section above, the real, currently-recurring cause of this ticket's 3-count evidence is
the None-phrase exact-match check, not the bullet regex; the bullet regex's separate,
already-confirmed `:line`-suffix bug (`TCK-20260804-EXPANSION-RATE-WIRING`) is a distinct problem,
out of this ticket's evidenced scope (see Anti-Drift Notes — flagged as a future-ticket candidate,
not fixed here). Do NOT touch `.claude/agents/investigator.md` — per the Decision section, this
ticket's chosen fix is the parser, not agent guidance; touching investigator.md as well would be
undecided scope creep beyond what Plan chose.

**Verify:** New unit tests `test_parse_docs_none_with_trailing_rationale_prose` and
`test_parse_docs_none_prefix_with_later_bullet_still_parses`, plus new integration tests
`test_docs_coverage_none_with_trailing_rationale_passes` and
`test_docs_coverage_none_prefix_but_real_bullet_still_required` (Step 4).

### Step 4 — tests/tools/test_done_checker_static.py: regression tests for the None-phrase fix

**Files:** `tests/tools/test_done_checker_static.py`

**Change:** Add two parse-level tests immediately after `test_parse_docs_ignores_non_bullet_prose`
(currently ending at line 1207, before the `# _git_touched_paths` section comment at line 1210):

```python
def test_parse_docs_none_with_trailing_rationale_prose():
    # Reproduces the real observed failure (TCK-20260803-DOCS-STRUCTURE-AUDIT's own logged
    # Verify-failure text: "fails the static none-phrase/bullet parser due to trailing rationale
    # prose") — "None." plus an extra rationale sentence, not byte-identical to "none.".
    section = "None. This ticket is documentation-prose-only and touches no docs/ files directly."
    assert _parse_docs_to_update(section) == []


def test_parse_docs_none_prefix_with_later_bullet_still_parses():
    # Guards against Option (a)'s false-PASS risk (see plan.md Decision section): a "None"-led
    # opening clause must not swallow a genuine bullet that follows later in the same section.
    section = (
        "None of the initially-considered docs needed changes, but on reflection:\n"
        "- `docs/mechanics/x.md`: reason\n"
    )
    assert _parse_docs_to_update(section) == ["docs/mechanics/x.md"]
```

Add two integration tests immediately after `test_docs_coverage_explicit_none_passes` (currently
ending at line 1313, before `test_docs_coverage_unparseable_non_none_section_fails`), modeled
directly on that existing test's (PASS case) and
`test_docs_coverage_missing_flagged_path_fails`'s (FAIL case) scaffolding:

```python
def test_docs_coverage_none_with_trailing_rationale_passes(tmp_path):
    # End-to-end regression test for the actual observed FAIL, at the exact call site
    # (check_docs_to_update_coverage) that produced it for TCK-20260803-DOCS-STRUCTURE-AUDIT,
    # TCK-20260803-DOC-UPDATER-DASHBOARD-PALETTE, TCK-20260803-DOC-UPDATER-VOCAB-REGISTRATION.
    base = tmp_path / "staging_artifacts"
    _write_investigation(
        base,
        "TCK-FAKE",
        "None. This ticket only touches tooling/test files, no docs/ content changes needed.",
    )
    status, evidence = check_docs_to_update_coverage("TCK-FAKE", "standard", base_dir=base)
    assert status == "PASS"


def test_docs_coverage_none_prefix_but_real_bullet_still_required(tmp_path, monkeypatch):
    # A "None of the..." opening clause followed by a real, untouched bullet must still FAIL —
    # confirms the Option (b) remainder-check keeps working end-to-end, not just at parse level.
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=tmp_path, check=True)

    base = tmp_path / "staging_artifacts"
    _write_investigation(
        base,
        "TCK-FAKE",
        "None of the originally-scoped docs, but on reflection:\n"
        "- `docs/mechanics/x.md`: reason\n",
    )
    monkeypatch.chdir(tmp_path)

    status, evidence = check_docs_to_update_coverage(
        "TCK-FAKE", "standard", base_dir=Path("staging_artifacts")
    )
    assert status == "FAIL"
    assert "docs/mechanics/x.md" in evidence
```

**Do NOT touch:** Any other test in the file — no existing test asserts the old duplicated-inline
exact-match behavior in a way `_is_none_section` changes (confirmed: `test_parse_docs_none_variants`
only exercises the exact-phrase fast path, which is preserved unchanged), so this is a pure
addition with zero risk of breaking an existing assertion. Do NOT add a test for the `:line`-suffix
bullet scenario — that is a real but separate bug, out of this ticket's scope (see plan.md's
Decision section and Anti-Drift Notes); adding a test for an unfixed bug here would be misleading
(a green test suite implying that bug is covered/fixed when it is not).

**Verify:** `pytest tests/tools/test_done_checker_static.py -k "docs" -v` — all `docs`-scoped tests
pass, including the four new ones.

### Step 5 — docs/ai/agent_definition_gap_audit_2026-08-04.md: ticket-specific "how to check" pointer

**Files:** `docs/ai/agent_definition_gap_audit_2026-08-04.md`

**Change:** Append a new section at the end of the file (after the existing "How to tell if these
fixes worked" paragraph, which stays as the general framing) with this exact heading and content:

```markdown
## Update — TCK-20260804-AGENT-DEF-GAP-FIXES landed (2026-08-05)

Landed: `planner.md` fact-verification sub-instructions, `implementer.md` before-returning
checklist, and a root-cause parser fix (`done_checker_static.py`'s new `_is_none_section()` helper
now tolerates trailing rationale prose after "None."/"N/A" — e.g. "None. See note below" — while
still correctly detecting a real `docs/` bullet if one follows, avoiding the false-PASS risk a
looser prefix check alone would carry) — see
`stored_artifacts/TCK-20260804-AGENT-DEF-GAP-FIXES/plan.md` for exact text and reasoning.

**How to check if THIS fix worked**, using the same method as this ticket's own investigation
(`stored_artifacts/TCK-20260804-AGENT-DEF-GAP-FIXES/investigation.md`), not the original audit's
one-time monthly percentages:

1. **Immediate, non-deferred check (parser fix only):** re-run the Verify-failure count for the
   "Docs Requiring Update" none-phrase/trailing-prose failure mode specifically — query
   `agent-monitoring-index/monitoring.db` for `phase='Verify'`, `status='failed'` events since
   2026-08-05 whose evidence text mentions "Docs Requiring Update" or "none-phrase". Expected: 0
   going forward, immediately — this is a deterministic parser fix, not a behavior-change-dependent
   one, so it does not need weeks of accumulation to validate. (A separate, still-open `:line`-
   suffix bullet-format bug was found during this ticket's Plan phase — confirmed real via
   `TCK-20260804-EXPANSION-RATE-WIRING`'s own event log — but is out of this ticket's 3-occurrence-
   evidenced scope; flagged as a future-ticket candidate, not fixed here.)
2. **Deferred check (planner.md / implementer.md fixes — needs real accumulated runs):** re-run
   this investigation's exact query — `events` table, `phase IN ('Review','Verify')`,
   `status='failed'`, grouped by month — after several weeks of real runs post-2026-08-05. Compare
   against the fresh pre-fix baseline this ticket established (not the original audit's monthly
   percentages): 15 Review failures and 25 Verify failures in the 2026-07-20 to 2026-08-05 window.
   A working fix should show:
   - Review failures per equivalent-length window trending below 15, with the specific
     "wrong factual claim about existing code" / "schema-referencing-a-nonexistent-field" /
     "AC-vs-plan self-contradiction" sub-patterns specifically declining (classify manually by
     reading `summary` text, same method investigation.md used — do not swap to a coarser
     "any failure" metric).
   - Verify failures' AC-checkbox-miss (was 6), stale-Status-field (was 5), and
     Completion-Summary-gap (was 4) sub-patterns specifically declining.
   - **Not expected to move** (out of this ticket's scope, do not count as evidence against the
     fix if these don't improve): "Scope item silently not implemented" (1), "Undisclosed scope
     creep" (1), "Real substantive contradiction" (1) — these are different failure classes this
     ticket did not address.
3. **A same-day or single-week re-check is not a valid deferred-check result** for item 2 above —
   report "not enough data yet," not a false negative or false positive.
```

**Do NOT touch:** The existing "Part 1", "Part 2", or "Resulting tickets" sections of this doc, or
its frontmatter — this is a pure append documenting what landed and how to verify it, not a
rewrite of the original audit's findings.

**Verify:** This satisfies AC5 directly — presence of the new section with the two-tier
(immediate/deferred) check is the verification; no automated test exists for doc prose content
(same conclusion investigation.md and test_plan.md reached for the other two agent-file changes).

## Scope Guards

- Do NOT modify `.claude/workflows/implement-ticket.js` (ticket AC6 / Out of Scope).
- Do NOT modify `.claude/agents/investigator.md` — Plan's chosen fix for item 3 is the parser
  (Step 3), not agent guidance; touching investigator.md would exceed what was decided.
- Do NOT build new agent-monitoring instrumentation — existing `agent-monitoring-index/monitoring.db`
  queries are sufficient for both the immediate and deferred checks (ticket Out of Scope).
- Do NOT add `data/runs/`/`reports/release_proof/` cleanup guidance to `implementer.md` — confirmed
  stale by investigation.md (`TCK-20260708-DATA-RUNS-CLEANUP-TIMING` already fixed it, 0 fresh
  occurrences); re-adding would contradict this ticket's own fresh evidence.
- Do NOT fold Docs-Requiring-Update bullet-format guidance into `implementer.md` — investigation.md
  explicitly flags this as an Investigate-phase artifact, wrong agent file, even before Plan's
  parser-vs-guidance decision (which further routes it away from any agent `.md` file).
- Do NOT expand scope to the recurring-SKILL.md-drift-mechanism finding — tracked separately as
  `TCK-20260804-SKILL-DRIFT-DETECTION`, explicitly out of scope here.
- Do NOT touch `docs/parity_ledger/` — investigation.md confirmed no parity ledger overlap for
  agent-instruction prose or tooling-parser changes of this kind.
- Do NOT re-cite the original audit doc's monthly percentages (2.7%/19.5%/22.9% Review,
  0.0%/21.9%/16.3% Verify) as freshly re-verified numbers in any new prose — use this ticket's own
  fresh counts (15 Review / 25 Verify since 2026-07-20) as the baseline going forward, per
  investigation.md's Anti-Drift Hazards.

## Dependency Map

- Steps 1, 2, 3 are mutually independent — each touches a different file and can be implemented
  and verified in any order, or in parallel.
- Step 4 depends on Step 3 (tests exercise `_is_none_section`/the updated `_parse_docs_to_update`
  and `check_docs_to_update_coverage` call sites Step 3 introduces; writing them first would fail
  against the unfixed exact-match check).
- Step 5 should be done last — it documents what Steps 1-4 actually landed (exact section names,
  exact fix mechanism) and would need rewriting if written before the other steps' final form is
  known.
- Recommended order: 1, 2, 3, 4, 5 (matches the plan's step numbering).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Investigate confirms both root causes still active (fresh evidence) | Already satisfied by `investigation.md` — no plan step | N/A (Investigate-phase artifact, pre-dates this plan) |
| `planner.md` gains 2-3 concrete, checkable verification sub-instructions | Step 1 | Manual re-read (test_plan.md row 1) |
| `implementer.md` gains explicit before-returning checklist (Completion Summary, Files Changed, AC discipline, `## Status` currency) | Step 2 | Manual re-read (test_plan.md row 2) |
| Docs-Requiring-Update bullet-format trap fixed, with stated reasoning | Step 3 (fix) + Step 4 (tests) | `pytest tests/tools/test_done_checker_static.py -k "docs" -v` |
| `docs/ai/agent_definition_gap_audit_2026-08-04.md` updated with "how to check if this worked" pointer | Step 5 | Presence of the new section (manual check) |
| No change to `implement-ticket.js` | Scope Guard (no step touches it) | Diff review at Architecture-Verify/Finalize confirms the file is absent from `## Files Changed` |

## Anti-Drift Notes

- The planner.md fix must stay at exactly the three sub-instructions in Step 1 — do not expand to
  a longer checklist; investigation.md's own "Conclusion for Plan" specifically asked for "2-3
  concrete, checkable sub-instructions rather than one vague directive," not an exhaustive list.
- The implementer.md checklist's `## Status` item is new relative to the original audit doc — it
  was found only in this ticket's fresh evidence pull (5 occurrences, comparably frequent to the 6
  AC-checkbox occurrences). Do not treat it as optional or lower-priority than the other three
  items.
- The parser fix (Step 3) is deliberately narrow — a new `_is_none_section` helper plus two
  call-site swaps (replacing the duplicated inline exact-match checks) and two docstring updates.
  `_DOCS_BULLET_RE` itself is explicitly NOT touched — see Decision section for why. Do not use
  this as an opportunity to refactor `_path_touched` or `_git_touched_paths` — neither needs to
  change, and touching them would be unreviewed scope creep against a plan the Review phase will
  check line-by-line.
- **Future-ticket candidate, not fixed here:** `_DOCS_BULLET_RE`'s greedy `[^`]+` capture still
  mis-parses a genuine `` `docs/path.md:42` `` bullet (confirmed real via
  `TCK-20260804-EXPANSION-RATE-WIRING`'s own logged Verify-failure text: "bullet format (:line
  baked inside backticks)") as the literal string `"docs/path.md:42"`, which then never matches a
  bare git-touched path. That ticket's own fix was an ad hoc hand-edit to its own
  `investigation.md` (moving the line number out of the backticks into prose), not a parser fix —
  the underlying bug is still live in `done_checker_static.py` today. Do not fold this into this
  ticket's Step 3; it is a distinct, second bug from the None-phrase issue this ticket's fresh
  3-occurrence evidence actually supports fixing now. Flag as a candidate for a future ticket
  (not scoped, sized, or decided here).
- Both Review-phase mislabeling uncertainty (2 OBSISO event clusters that may be
  Architecture-Verify, not Review) and the exact monthly-percentage figures are explicitly flagged
  by investigation.md as imprecise — Step 5's "how to check" text uses only the ticket's own fresh
  15/25 counts as the going-forward baseline, per that guidance.
- This ticket touches no `src/` or simulation-logic code — `graphify update .` is not required
  after this ticket's changes (only `.claude/agents/*.md`, one tool module under `tools/`, its
  test file, and one `docs/` file are touched; `docs/` changes trigger
  `make knowledge-index-update` per the project's After-Work checklist, not `graphify update`).

## Unresolved Questions

None. The one open question investigation.md flagged for Plan (parser fix vs. investigator.md
guidance for item 3) is resolved above in the Decision section, with corpus evidence gathered
before deciding, per the ticket's explicit instruction not to assume.
