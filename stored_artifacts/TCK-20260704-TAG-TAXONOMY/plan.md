---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260704-TAG-TAXONOMY
artifact_type: plan
tags: [tagging, taxonomy, frontmatter, registry, data-quality]
---

# Implementation Plan — TCK-20260704-TAG-TAXONOMY

## Summary

Add a controlled tag taxonomy: a new `docs/guidelines/tag_taxonomy.md` defining four categories
(subsystem/topic, phase/milestone, process/skill-signal, quality-attribute) plus canonical-form
rules, and extend `tools/validate_frontmatter.py` with a `_check_tags()` function wired into
`_validate_ticket`/`_validate_artifact` (not `_validate_doc`/`_validate_archive`). Enforcement is
**hard-reject** (reuses the existing all-or-nothing `_check_enum` precedent — no new warn-severity
pattern) but is **date-gated**: only tickets/artifacts whose `ticket_id` embeds a date on or after
`2026-07-04` (this ticket's date) are checked, so the ~1001 historical tickets are exempt without
a backfill or an explicit exemption list. Three check types: forbidden `p0`/`p1`/`p2` (any case),
a general format rule (no uppercase, no underscore — auto-derives the hyphenated canonical form),
and a small explicit synonym dict for the handful of confirmed pairs the format rule can't derive
mechanically (`obs`→`observability`, `cog`→`cognition`, `sim`→`simulation`, plus 4 run-together
compound-word pairs). A dedicated `phase(\d+)` regex catches `phaseN` → `phase-N`.

## Design Decisions Made This Session (resolving investigation's open questions)

These are Plan-phase judgment calls, made with supporting evidence gathered below — flagged here
explicitly per this repo's Planning Rule so they can be overridden before implementation if the
rationale doesn't hold up. None are hidden in the steps below; every step references back to one
of these.

**1. Whole-directory invocation mode (investigation's open question #1) — RESOLVED.**
Re-checked this session: no `Makefile` target, `.claude/hooks/`, or `.github/` workflow invokes
`validate_frontmatter.py` at all today (confirmed via grep across all three). However,
`docs/guidelines/frontmatter_schema.md:190` and `docs/README.md:105-106` **explicitly document**
`python3 tools/validate_frontmatter.py tickets/done/` as the recommended example invocation for
checking historical tickets. So enforcement is **not** structurally forward-only by omission — it
is plausible (and documented as correct usage) for someone to run whole-directory mode against
`tickets/done/` at any time. This means a grandfather mechanism genuinely is needed, which resolves
in favor of the date-cutoff design below rather than assuming "no caller exists, so it's naturally
fine."

**2. Reject vs. warn severity (open question #2) — RESOLVED as reject + date cutoff, not a new
warn pattern.** The investigation correctly noted no "warn but pass" path exists anywhere in
`validate_frontmatter.py` today. Rather than inventing one, this plan reuses the existing
hard-reject precedent (matching `layer`/`status`/`authority`/etc.) and instead scopes *when* the
check applies, via a date embedded in `ticket_id` (format `TCK-YYYYMMDD-...`, already a required
field on both tickets and artifacts). This directly matches the AC's own wording — "the new tag
validation only applies going forward" / "does not newly fail... for tickets that predate this
taxonomy" — literally a date-based, not severity-based, distinction. `TAG_TAXONOMY_EFFECTIVE_DATE
= "20260704"`; any `ticket_id` embedding a date `< 20260704`, or no parseable date at all, is
exempt from tag checks (still gets every other existing check).

**3. `sim`/`cog`/`obs` synonym direction (open question #3) — RESOLVED from the ticket's own Scope
text, not re-derived from corpus counts.** The ticket's Scope section already states the mapping
direction as its own example: "`obs` → `observability`, `cog` → `cognition`, `sim` →
`simulation`." This plan adopts that direction as-is. Corroborating evidence: `LAYER_VALUES`
(`tools/validate_frontmatter.py:26-30`) already contains `"simulation"` and `"observability"` as
enum spellings (not `"sim"`/`"obs"`), so using the long form keeps tag spelling consistent with the
adjacent `layer` enum. `cognition` has no `layer` counterpart (`layer` uses `"ai"`), but the long
form is still adopted for consistency with the other two pairs and because it is the standard
technical spelling. The `sim` (33) vs. `simulation` (3) usage skew noted in investigation is real
but does not override the ticket's explicit worked example — noted in the taxonomy doc as a known
inversion of raw usage frequency, not silently smoothed over.

**4. `_validate_doc` scope (open question #4) — RESOLVED: do not extend it.** Ticket Scope
explicitly names only `_validate_ticket` and `_validate_artifact` ("mirrors the existing
`_check_enum(...)` pattern already used for `layer`" — for those two functions specifically).
Extending `_validate_doc` would put `test_doc_tags_optional_present`/`_absent`
(`tests/tools/test_validate_frontmatter.py:233-242`, using `tags: [combat, ai]`) at risk of
breaking for no ticket-scoped reason, exactly the anti-drift hazard the test plan calls out. Left
untouched.

**5. `process/skill-signal` vs. `quality-attribute` overlap (ticket's Scope explicitly flags
`hardening` as appearing in both category descriptions and asks Plan to resolve it) — RESOLVED.**
Disambiguation rule adopted: a tag belongs in **process/skill-signal** only if it names an
*existing or clearly nameable* skill/process gate 1:1 (e.g. `security` → the `security-review`
skill already in this environment's skill catalog). A tag belongs in **quality-attribute** if it
characterizes the *nature* of a change without routing to a specific skill — `hardening` matches
the "Hardened" rationale class already enumerated in `CLAUDE.md`'s Intentional Divergences list
(`Hardened`/`Enforced`/`Unified`/`Stabilized`/`Bounded`/`Bug Fix`/`Intentional Gameplay Change`),
i.e. it describes *how* a change was made, not *what process should run*. So: `hardening` →
quality-attribute; `security` → process/skill-signal (once used). This resolution is recorded in
`tag_taxonomy.md` itself (Step 4), not left implicit.

None of the above are true blockers requiring a main-session decision before coding starts — each
had enough evidence in the ticket/investigation/repo to resolve directly. Flagged here per the
Planning Rule so they're visible, not silently baked in.

## Steps

### Step 1 — Add tag-taxonomy constants and `_check_tags()` to the validator

**Files:** `tools/validate_frontmatter.py`

**Change:** After the existing enum constants block (`:25-34`), add:

```python
# Tag taxonomy — see docs/guidelines/tag_taxonomy.md.
# Enforcement is forward-only: only tickets/artifacts whose ticket_id embeds a date on or
# after this cutoff are checked, per the "no backfill of history" decision (TCK-20260704-TAG-TAXONOMY).
TAG_TAXONOMY_EFFECTIVE_DATE = "20260704"

# Duplicates the dedicated `## Priority` ticket-body field — never valid as a tag, at any date.
FORBIDDEN_PRIORITY_TAGS = {"p0", "p1", "p2"}

# Confirmed synonyms the general format rule (below) cannot derive mechanically, because the
# non-canonical spelling has no separator character to normalize (run-together compounds and
# abbreviations). Keep this small and evidence-based — do not use it to pre-enumerate subsystem
# tags; see docs/guidelines/tag_taxonomy.md's anti-drift note.
TAG_SYNONYM_MAP = {
    "obs": "observability",
    "cog": "cognition",
    "sim": "simulation",
    "worldmodules": "world-modules",
    "selfmodel": "self-model",
    "datamodel": "data-model",
    "worldspec": "world-spec",
}

_PHASE_TAG_PATTERN = re.compile(r"^phase(\d+)$")
_TICKET_ID_DATE_PATTERN = re.compile(r"^TCK-(\d{8})-")
```

Then, near `_check_enum` (`:112-116`), add:

```python
def _ticket_id_effective_date(ticket_id) -> str | None:
    """Extract the YYYYMMDD date embedded in a TCK-YYYYMMDD-... ticket_id, or None if unparseable."""
    if not isinstance(ticket_id, str):
        return None
    m = _TICKET_ID_DATE_PATTERN.match(ticket_id)
    return m.group(1) if m else None


def _check_tags(filepath: str, fm: dict) -> list[str]:
    tags = fm.get("tags")
    if not tags:
        return []

    embedded_date = _ticket_id_effective_date(fm.get("ticket_id"))
    if embedded_date is None or embedded_date < TAG_TAXONOMY_EFFECTIVE_DATE:
        # Predates the taxonomy (or ticket_id unparseable) — exempt, per the explicit
        # no-backfill decision. Every other frontmatter check still applies as normal.
        return []

    errors = []
    for tag in tags:
        lower = tag.lower()
        if lower in FORBIDDEN_PRIORITY_TAGS:
            errors.append(
                f"{filepath}: tags: {tag!r} duplicates the dedicated Priority field — remove it"
            )
            continue
        if tag != lower or "_" in tag:
            errors.append(
                f"{filepath}: tags: {tag!r} is not canonical form "
                f"(use {lower.replace('_', '-')!r})"
            )
            continue
        phase_match = _PHASE_TAG_PATTERN.match(tag)
        if phase_match:
            errors.append(
                f"{filepath}: tags: {tag!r} is not canonical form "
                f"(use {'phase-' + phase_match.group(1)!r})"
            )
            continue
        if tag in TAG_SYNONYM_MAP:
            errors.append(
                f"{filepath}: tags: {tag!r} is a non-canonical synonym "
                f"(use {TAG_SYNONYM_MAP[tag]!r})"
            )
    return errors
```

Wire it into `_validate_ticket` (`:135-145`) and `_validate_artifact` (`:148-158`) by adding
`errors += _check_tags(filepath, fm)` at the end of each function, before `return errors`.

**Do NOT touch:** `_validate_doc`, `_validate_archive`, `_check_enum`, `validate_file`,
`validate_directory`, `main()` — no CLI/exit-code plumbing changes needed since this reuses the
existing hard-reject path (errors just accumulate into the same `all_errors` list `main()` already
prints and exits 1 on).

**Verify:** `python3 -c "import importlib.util; ..."` quick manual check, or just proceed to Step 2
where this is covered by real tests. Do not run pytest yet — Step 1 alone has no test coverage
until Step 2/3 land.

---

### Step 2 — Anti-drift assertions for the new constants

**Files:** `tests/tools/test_validate_frontmatter.py`

**Change:** In `TestEnumAntiDrift` (`:456-479`), add exact-equality assertions mirroring the
existing `STATUS_VALUES`/`LAYER_VALUES`/etc. pattern, for:
- `FORBIDDEN_PRIORITY_TAGS == {"p0", "p1", "p2"}`
- `TAG_SYNONYM_MAP` exact-equality against the 7-entry dict from Step 1
- `TAG_TAXONOMY_EFFECTIVE_DATE == "20260704"`

**Do NOT touch:** the existing 6 enum assertions already in this class.

**Verify:** `python3 -m pytest tests/tools/test_validate_frontmatter.py::TestEnumAntiDrift -v`

---

### Step 3 — New test classes: forbidden tags, canonical/synonym rejection, historical exemption

**Files:** `tests/tools/test_validate_frontmatter.py`

**Change:** Add two new test classes following the existing `_ticket_fm()`/`_artifact_fm()`
builder-helper pattern (`:61-134`). Use ticket_id `TCK-20260704-...` (on/at cutoff, so checks
apply) for all new-behavior tests, and the real historical ticket
`tickets/done/TCK-20260520-SIM-OBS-PHASE5-M24.md` (tags: `[sim, obs, phase5, m24]`, ticket_id date
`20260520` — before the `20260704` cutoff) for the exemption regression test, per the test plan's
"use real corpus data, not synthetic" anti-drift guard.

`TestForbiddenPriorityTags`:
- `test_ticket_forbidden_tag_p0_rejected` / `_p1_rejected` / `_p2_rejected` — `tags: [p0]` /
  `[p1]` / `[p2]` on a `TCK-20260704-...` ticket each rejected.
- `test_ticket_forbidden_tag_uppercase_rejected` — `tags: [P0]`, `[P1]`, `[P2]` also rejected.
- `test_ticket_tag_valid_when_no_priority_tag_present` — `tags: [combat, faction]` (both already
  canonical form) passes cleanly.

`TestTagCanonicalization`:
- `test_ticket_tag_canonical_form_accepted` — `tags: [observability, cognition, simulation]`
  passes.
- `test_ticket_tag_synonym_obs_rejected` — `tags: [obs]` rejected, message names `obs` and suggests
  `observability`.
- `test_ticket_tag_synonym_cog_rejected` — `tags: [cog]` rejected.
- `test_ticket_tag_phase_format_rejected` — `tags: [phase5]` rejected, suggests `phase-5`.
- `test_ticket_tag_underscore_format_rejected` — `tags: [simulation_quality]` rejected, suggests
  `simulation-quality`.
- `test_ticket_tag_uppercase_format_rejected` — `tags: [Combat]` rejected (general format rule,
  not the priority-forbidden path).
- `test_artifact_tag_synonym_rejected` — same `obs`/`cog` check mirrored onto `_artifact_fm()`,
  since Scope explicitly requires `_validate_artifact` coverage too.
- `test_ticket_tag_historical_exemption` — load
  `tickets/done/TCK-20260520-SIM-OBS-PHASE5-M24.md` (real file, `ticket_id` date `20260520`,
  `tags: [sim, obs, phase5, m24]` — three format/synonym violations if checked) through
  `validate_file()` directly and assert **no tag-related errors** appear in the result (other
  fields may or may not already pass independently; only assert on the tag-specific error
  substrings being absent, to avoid coupling this test to unrelated pre-existing frontmatter
  state in that file).
- `test_ticket_tag_no_ticket_id_date_exempt` — a ticket-shaped fixture with a malformed/missing
  `ticket_id` (if constructible without violating the already-required-field check) confirms
  `_check_tags` doesn't crash and treats it as exempt rather than erroring.

**Do NOT touch:** `test_doc_tags_optional_present` (`:233-238`), `test_doc_tags_optional_absent`
(`:240-242`) — must keep passing unmodified, confirming `_validate_doc` was correctly left alone
in Step 1.

**Verify:**
```
python3 -m pytest tests/tools/test_validate_frontmatter.py -v
```
Expect all pre-existing 47 tests plus all new tests green. Do not run the full `tests/tools/`
directory (pre-existing unrelated failures in `test_knowledge_search.py`/`test_search_mcp.py`, per
test_plan.md).

---

### Step 4 — Write `docs/guidelines/tag_taxonomy.md`

**Files:** `docs/guidelines/tag_taxonomy.md` (new)

**Change:** Document, in order:
1. Purpose statement (controlled vocabulary as prerequisite for future routing, not routing
   itself — explicitly note the 5 out-of-scope future scenarios and, per AC, name which category
   each would read from:

   | Scenario | Category it reads |
   |---|---|
   | 1. Tag-driven skill suggestion | Process/Skill-signal |
   | 2. Tag-driven gate routing | Process/Skill-signal |
   | 3. Cross-cutting discovery beyond `layer` | Subsystem/Topic |
   | 4. Retro/analytics grouping | Subsystem/Topic (primary), Process/Skill-signal (skill-specific gate failures) |
   | 5. Automatable skill-catalog health check | Process/Skill-signal |

2. The four categories, each with: definition, canonical-form rule, 3-5 example tags, and its
   relationship to `layer` (for Subsystem/Topic specifically — explicitly state it is a
   deliberately finer-grained, sometimes cross-cutting complement to `layer`'s 19-value enum, not
   a duplicate; cite `faction` spanning `ai`/`systems`/`social` as the worked example from
   investigation):
   - **Subsystem/Topic** — combat, economy, cognition, faction, resource, social, content, world,
     engine, strategy, ...
   - **Phase/Milestone** — canonical format `phase-N`.
   - **Process/Skill-signal** — tags whose canonical spelling matches an existing or clearly
     nameable skill/process gate 1:1 (e.g. `api-design`, `performance`, `debugging`, `security`).
   - **Quality-attribute** — cross-cutting characterizations of a change's nature, not tied to a
     specific skill (e.g. `hardening`, `calibration`, `schema`, `audit`) — explicitly cross-
     reference `CLAUDE.md`'s Intentional Divergences rationale classes (`Hardened`/`Enforced`/
     `Unified`/`Stabilized`/`Bounded`/`Bug Fix`/`Intentional Gameplay Change`) as the model for this
     category, and state the disambiguation rule from this plan's Design Decision #5 verbatim:
     "belongs in Process/Skill-signal only if it names an existing or clearly nameable skill/process
     gate 1:1; otherwise, if it characterizes the nature of a change, it is Quality-attribute."
3. **Forbidden tags**: `p0`/`p1`/`p2` (any case) — duplicates the dedicated `Priority` field.
4. **Canonical-synonym mapping** table — the 7-entry `TAG_SYNONYM_MAP` from Step 1, plus the
   general rules (no uppercase, no underscore, `phase-N` not `phaseN`) stated as rules rather than
   an exhaustive pair list.
5. **Enforcement note**: forward-only from `2026-07-04` (`TAG_TAXONOMY_EFFECTIVE_DATE`); historical
   tickets before this date are intentionally not backfilled or re-validated, matching this
   ticket's explicit Out of Scope.
6. Frontmatter matching every other active `docs/guidelines/*.md` doc exactly (`frontmatter_schema.md`,
   `design_patterns.md`, `intentional_divergences.md` all use the same four-key block, no `tags`
   key at all): `status: active`, `layer: guidelines`, `authority: P1`, `audience: developer`.
   [Corrected during Architecture Review 2026-07-04 — original draft proposed `authority: P2`,
   `audience: agent`, which had no stated rationale for deviating from this repo's established
   guidelines-layer precedent.]

**Do NOT touch:** any other file under `docs/guidelines/`.

**Verify:** `python3 tools/validate_frontmatter.py docs/guidelines/tag_taxonomy.md` passes doc-type
validation (its own frontmatter must be schema-valid).

---

### Step 5 — Update `docs/guidelines/frontmatter_schema.md`'s `tags` field description

**Files:** `docs/guidelines/frontmatter_schema.md`

**Change:** At lines `52`, `84`, `113` (the `doc`, `ticket`, `artifact` rows describing `tags` as
`free-form`), update the `ticket` and `artifact` rows only (leave `doc`'s row as `free-form`,
consistent with Step 1's decision not to extend `_validate_doc`) to reference
`docs/guidelines/tag_taxonomy.md` and note forward-only enforcement from `2026-07-04`.

**Do NOT touch:** the `doc` row (line 52) — `_validate_doc` is intentionally untouched per Design
Decision #4.

**Verify:** manual read-through; no automated test for prose doc content.

---

### Step 6 — Update parity ledger entry `INFRA-180`

**Files:** `docs/parity_ledger/infrastructure.yaml`

**Change:** At the `INFRA-180` entry (`:1846-1861`), update `text` to note that `tags` now has
controlled-vocabulary enforcement (forward-only, forbidden-tag + canonical-synonym rules) on
`ticket`/`artifact` content types, and add `docs/guidelines/tag_taxonomy.md` to `v2_evidence`
alongside the three existing files. Keep `status: verified` (behavior is still internally
consistent and tested) and `priority: P2` unchanged.

**Do NOT touch:** any other parity ledger entry or file — investigation confirmed no other ledger
file references tags/taxonomy/frontmatter.

**Verify:** manual read-through against Step 1/2/3's actual final code, confirming `v2_evidence`
accurately lists every file this ticket touched.

---

### Step 7 — Update `.claude/agents/ticket-scoper.md`

**Files:** `.claude/agents/ticket-scoper.md`

**Change:** At line 28 (`tags: [<scope words from ticket ID, lowercase>]`), add a reference to
`docs/guidelines/tag_taxonomy.md` and instruct the agent to prefer categories/canonical spellings
from that doc over raw scope-word lowercasing, and to never emit `p0`/`p1`/`p2` as a tag.

**Do NOT touch:** any other section of `ticket-scoper.md`.

**Verify:** manual read-through; not pytest-covered (agent prompt, not code) — matches test_plan
item 5.

---

### Step 8 — Run scoped tests, update ticket

**Files:** `tickets/inprogress/TCK-20260704-TAG-TAXONOMY.md`

**Change:** Run:
```
python3 -m pytest tests/tools/test_validate_frontmatter.py -v
python3 -m pytest tests/tools/test_add_frontmatter_tickets.py tests/tools/test_add_frontmatter_live.py tests/tools/test_add_frontmatter_archive.py -q
```
Fill in ticket's Implementation Notes / Test Summary / Files Changed / Completion Summary. Add
`docs/parity_ledger/infrastructure.yaml` and `TCK-20260704-SKILL-TRIGGER-COVERAGE`/
`TCK-20260704-RETRO-LOOP-ENFORCEMENT` cross-references already present in Related Tickets — no
change needed there, already correct.

**Do NOT touch:** full `tests/tools/` suite or full `pytest tests/` — out of scope per test_plan.

**Verify:** all scoped commands green; move ticket to `tickets/done/`; delete source copy from
`tickets/todos/agent-infra-followups/TCK-20260704-TAG-TAXONOMY.md` (leave the folder itself until
all 5 siblings are done, per investigation's Prior Work note).

---

## Scope Guards

- No changes to `_validate_doc` or `_validate_archive`.
- No changes to `LAYER_VALUES` or any other existing enum.
- No backfill/normalization of any of the ~1001 historical ticket files' actual `tags:` values —
  the date-cutoff mechanism achieves forward-only enforcement without touching a single historical
  file.
- No tag-consumption code (skill suggestion, gate routing, REGISTRY.yaml filtering, retro
  grouping) — taxonomy + validator + doc references only.
- `TAG_SYNONYM_MAP` stays at the 7 entries justified by this session's corpus investigation; do not
  expand it to pre-empt hypothetical future tags.

## Dependency Map

1 → 2, 3 (constants must exist before anti-drift/behavior tests reference them)
1 → 4, 5, 6 (doc/ledger updates describe the code Step 1 produces; write after code is final so
  prose matches exactly)
4 → 5 (frontmatter_schema.md's tags row links to tag_taxonomy.md, so the target must exist first)
1, 4 → 7 (ticket-scoper references the taxonomy doc that must already exist)
2, 3, 4, 5, 6, 7 → 8 (final test run + ticket closeout happens last)

## Acceptance Criteria Map

| AC | Step(s) | Notes |
|---|---|---|
| `docs/guidelines/tag_taxonomy.md` exists, defines categories + canonical/synonym mapping | 4 | |
| Validator rejects non-canonical spelling with canonical form defined | 1, 3 | reject, not warn — Design Decision #2 |
| Validator rejects `p0`/`p1`/`p2` (any case) | 1, 3 | `FORBIDDEN_PRIORITY_TAGS`, case-insensitive via `.lower()` |
| `ticket-scoper.md` references taxonomy doc | 7 | |
| New tests cover acceptance/synonym-rejection/forbidden-rejection | 2, 3 | |
| Whole-directory run does not newly fail on historical tickets | 1, 3 | date-cutoff exemption; regression test uses real file `TCK-20260520-SIM-OBS-PHASE5-M24.md` |
| Taxonomy category list checked against all 5 future scenarios | 4 | scenario→category table in Step 4 |

## Anti-Drift Notes

- `TAG_SYNONYM_MAP`, `FORBIDDEN_PRIORITY_TAGS`, and `TAG_TAXONOMY_EFFECTIVE_DATE` must each get an
  exact-equality assertion in `TestEnumAntiDrift` (Step 2) — this is the repo's established guard
  against a validator constant silently drifting from its own test, already applied to every other
  `*_VALUES` constant in this file.
- Do not let the phase-N-format and underscore/uppercase-format checks collapse into a single
  hardcoded pair list — both are implemented as general, parametric rules (regex / character-class
  check) specifically so they cover the full `phase-0` through `phase-6` range and any future
  underscore/uppercase tag without needing a 19-entry lookup table. Only the 7 run-together
  compound/abbreviation cases that have no separator to normalize need an explicit dict entry.
  Preserve this split — collapsing it into "one big synonym dict" would recreate the
  over-enumeration problem the anti-drift hazard warns against.
- Keep the historical-exemption test (`test_ticket_tag_historical_exemption`) pointed at the real
  file `tickets/done/TCK-20260520-SIM-OBS-PHASE5-M24.md` — do not substitute a synthetic fixture;
  the point of this test is proving the actual corpus doesn't newly fail, not a hypothetical one.
- `_validate_doc` and `_validate_archive` must remain untouched through every step — if a later
  session decides doc-type tags should also be validated, that is a new ticket, not silently folded
  into this one (matches Design Decision #4 and the ticket's explicit Scope wording).
- When updating `INFRA-180` (Step 6), do not change its `status` or `priority` — only `text` and
  `v2_evidence`. The behavior remains internally consistent and tested; this is documentation
  catch-up, not a re-certification event.
