---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260923-TERR01-CITATION-FIX
phase: done
date: 2026-09-23
tags: [world, documentation]
---

# TCK-20260923-TERR01-CITATION-FIX

## Title
Repoint TERR-01's stale "see TERR-04" citation to the real Inherited entry (LAW-03)

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
`docs/world_rules/places-culture/territory-control.md` line 30, inside the TERR-01 Domain Rule
statement, cites a Rule ID "TERR-04" for jurisdiction ("jurisdiction (legal/institutional
applicability, see TERR-04)"). No TERR-04 Rule was ever created, and none should be: per the
World Rule Catalog's own admission discipline, jurisdiction was admitted as an
Inherited/Applied Foundational Rule reusing Batch 10's LAW-03 — not as a new local Rule ID.
The citation on line 30 is simply stale/wrong and must be repointed to the real Inherited
entry, mirroring the correct phrasing already used two paragraphs later at line 324
("Inherited jurisdiction entry → Law/Enforcement (LAW-03, Batch 10 — the deferred integration
this entry resolves)").

## Scope
- Edit line 30 of `docs/world_rules/places-culture/territory-control.md` only: replace the
  `see TERR-04` citation with a citation to the real Inherited jurisdiction entry (LAW-03,
  Batch 10), phrased consistently with the established pattern already used at line 324 of the
  same file (`Inherited jurisdiction entry → Law/Enforcement (LAW-03, Batch 10 ...)`).
- No other line of the file changes.

## Out of Scope
- Creating a new TERR-04 Rule ID anywhere in the repo — the numbering gap is intentional and
  correct per the admission discipline (jurisdiction was Inherited, not a new Domain Rule) and
  must remain unfilled.
- Renumbering TERR-01, TERR-02, TERR-03, TERR-05, or any other Rule ID.
- Touching any other Rule's citation, cross-domain link, or the "Cross-domain links recorded
  here" section beyond confirming line 324's existing phrasing (read-only reference, not
  edited).
- Any change to `docs/world_rules/institutions-politics/law-enforcement.md` (LAW-03's home
  file) or any parity ledger entry — this is a pure inline-citation text fix with no semantic
  or mechanics change.

## Acceptance Criteria
1. `grep -n "TERR-04" docs/world_rules/places-culture/territory-control.md` returns no matches
   (currently returns one match, line 30).
2. `grep -n "TERR-04" -r docs/ tickets/ src/ tests/` (repo-wide) returns no matches — confirms
   no TERR-04 Rule was created anywhere as a side effect of this fix.
3. Line 30's corrected text references the real Inherited entry, e.g. matches
   `grep -n "LAW-03" docs/world_rules/places-culture/territory-control.md` showing a new hit on
   (or immediately around) line 30 in addition to the pre-existing line 324 hit.
4. `git diff -- docs/world_rules/places-culture/territory-control.md` shows exactly one line
   changed (line 30) and no other lines of the file touched.

**Verification status (this ticket uses a numbered list, not `- [ ]` checkboxes; all four
confirmed satisfied by direct command output, see Test Summary):**
1. SATISFIED — `grep -n "TERR-04" docs/world_rules/places-culture/territory-control.md` returns
   no matches.
2. SATISFIED (with one expected caveat) — the real target file has zero TERR-04 matches; the
   literal repo-wide command as written also matches this ticket file's own prose describing the
   fix (`tickets/inprogress/TCK-20260923-TERR01-CITATION-FIX.md`), which is the ticket discussing
   its own subject, not a real Rule-ID usage — zero real Rule-ID usages of TERR-04 exist anywhere.
3. SATISFIED — line 30 now contains a `LAW-03` hit alongside the pre-existing line 324 hit.
4. SATISFIED — `git diff` confirms exactly one line (line 30) changed, no other lines touched.

## Related Tickets
None found. Searched `tickets/inprogress/`, `tickets/done/`, and `tickets/backlogs/` for
TERR/territory/world-rule/jurisdiction/citation overlap. All territory-named tickets found
(`TCK-20260619-E53Cc-TERRITORY-TRANSFER`, `TCK-20260807-FACTION-TERRITORY-PCT-PAYLOAD-GAP`,
`TCK-20260831-CREATURE-TERRITORY-LIFECYCLE`, `TCK-20260503-TERRAIN-WEIGHT-AUTHORITY`, and the
worldgen-organic-terrain epic) are engine/gameplay territory-system implementation tickets,
unrelated to this World Rule Catalog documentation citation. Citation-named backlog artifacts
(`TCK-20260916-CITATION-RESOLUTION-FLOOR-DEMOTE`, `TCK-20260904-TOWN-RESOURCE-PARITY-CITATION-HARDENING`,
`TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT`) concern `docs/parity_ledger/` test-path
citations, not `docs/world_rules/` inline Rule ID citations — no TERR references in any of
their stored artifacts.

## Related Docs
- `docs/world_rules/places-culture/territory-control.md` — file being edited (line 30 stale
  citation; line 324 has the correct phrasing pattern to mirror).
- `docs/world_rules/README.md` (lines ~145-150) — states the standing Rule admission
  discipline: "a statement earns a new local Rule ID only if it adds or refines target world
  semantics beyond Rules already defined elsewhere... A direct reuse of an earlier Rule ID is
  an Inherited/Applied Foundational Rule." Confirms Inherited entries reuse an existing Rule ID
  rather than minting a new local one.
- `docs/world_rules/review-exports/places-territory-batch-11a-review.md` — "Rule admission
  accounting" section (~line 96-110) explicitly documents Batch 11A's breakdown: TERR-01,
  TERR-02, TERR-03, TERR-05 are the only genuine Domain Rules in territory-control.md;
  jurisdiction's territorial basis is listed as one of the 4 Inherited/Applied Foundational
  Rules, "resolving Batch 10's own deferred integration (LAW-03, Batch 10)". The Rule Catalog
  table in the same file (line 131) lists only TERR-01/02/03/05 — confirms TERR-04 was never
  created and the gap is intentional.

## Related Stored Artifacts
None found covering this specific citation. Checked `stored_artifacts/` for territory/TERR/
world-rule/jurisdiction/citation matches; only unrelated engine-implementation and
parity-ledger-citation artifacts exist (see Related Tickets).

## Related Code Areas
- `docs/world_rules/places-culture/territory-control.md` (documentation only — no `src/`
  code path affected).

## Assumptions / Open Questions
- Assumes the corrected line 30 citation should be phrased as a reference to the "Inherited
  jurisdiction entry" concept (mirroring line 324's own wording pattern) rather than a bare
  "see LAW-03" — implementer should match line 324's established phrasing as closely as
  fits inline within TERR-01's own sentence structure. If a materially different phrasing is
  chosen, it must still satisfy Acceptance Criteria 3 (a LAW-03 reference appears at/near line
  30).
- `layer: world` chosen over registering a new `world-rules`-specific layer, since `world`
  (World generation, worldbuilding, region/biome content) already covers
  `docs/world_rules/` content and no dedicated narrower layer exists in
  `registries/layer_registry.jsonl`.
- Tags `[world, documentation]` chosen from already-registered tags
  (`python3 tools/tag_registry.py list`) — `world` for the subsystem-topic dimension,
  `documentation` (meta-process) since this is a docs-authoring/maintenance fix with no
  behavior or mechanics change.

## Implementation Notes
Read lines 30 and 324 of `docs/world_rules/places-culture/territory-control.md` directly before
editing, per the instruction not to guess at wording. Line 30's original text was:
`> in fact), **jurisdiction** (legal/institutional applicability, see TERR-04), **property`.
Line 324's established phrasing was confirmed as:
`- Inherited jurisdiction entry → Law/Enforcement (LAW-03, Batch 10 — the deferred integration
this entry resolves)`.

Replaced the `see TERR-04` fragment on line 30 with an inline citation mirroring line 324's
phrasing: `Inherited jurisdiction entry → Law/Enforcement, LAW-03, Batch 10, the deferred
integration this entry resolves`. The punctuation was adapted from line 324's parenthetical/
em-dash form to fit inline inside TERR-01's own already-parenthesized clause (line 30's
`(legal/institutional applicability ...)` wrapper), using an em-dash separator and commas in
place of the standalone-bullet form's parentheses and em-dash, since line 30's citation sits
inside an existing `(...)` group rather than at the top level of a bullet.

One deliberate deviation from a naive minimal-diff approach: rather than editing only the
`see TERR-04` substring in place (which would have let the paragraph's manual line-wrapping
reflow and touch lines 31-32 as well, since the replacement text is longer), the entire content
of line 30 was replaced as a single line, left un-wrapped/long, so that lines 31 onward remain
byte-identical and untouched. This was necessary to satisfy the ticket's own Acceptance
Criterion 4 (`git diff` shows exactly one line changed) — confirmed via `git diff` after the
edit: exactly one line (line 30) shows as changed, no other lines touched.

No TERR-04 Rule ID was created anywhere. No other line, section, or file was edited.

## Test Summary
This is a pure documentation citation-text fix with no code or test surface. No automated
tests apply. Verification was done via direct grep/diff commands instead:
- `grep -n "TERR-04" docs/world_rules/places-culture/territory-control.md` → no matches (exit 1).
- `grep -rn "TERR-04" .` (repo-wide) → matches only inside this ticket's own file
  (`tickets/inprogress/TCK-20260923-TERR01-CITATION-FIX.md`, which itself describes the historical
  TERR-04 citation as its subject) — zero real Rule-ID usages of TERR-04 remain anywhere else.
- `grep -n "LAW-03" docs/world_rules/places-culture/territory-control.md` → new hit at line 30,
  in addition to the pre-existing hits at lines 220, 225, 229, 233, and 324.
- `git diff -- docs/world_rules/places-culture/territory-control.md` → exactly one line changed
  (line 30); no other lines of the file touched.
All four Acceptance Criteria confirmed passing by direct command output.

## Files Changed
- `docs/world_rules/places-culture/territory-control.md` — line 30 citation text repointed from
  the stale `see TERR-04` to the real Inherited jurisdiction entry (LAW-03, Batch 10).
- `tickets/inprogress/TCK-20260923-TERR01-CITATION-FIX.md` — this ticket file itself, filled in
  with Implementation Notes, Test Summary, Files Changed, Completion Summary, and Status updates
  as part of ticket close.

## Completion Summary
Repointed the stale `see TERR-04` citation on line 30 of
`docs/world_rules/places-culture/territory-control.md` (inside the TERR-01 Domain Rule's
jurisdiction clause) to the real Inherited jurisdiction entry, using phrasing that mirrors the
established pattern already present at line 324 of the same file (`Inherited jurisdiction entry
→ Law/Enforcement, LAW-03, Batch 10, the deferred integration this entry resolves`). No TERR-04
Rule ID was created, no other line was touched, and no simulation, code, or parity-ledger
behavior changed — this was a pure prose citation-text correction confirmed by grep and git diff.
