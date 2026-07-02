---
status: historical
artifact_type: notice
ticket_id: TCK-20260701-HAZARD-NATIVE-IMMUNITY
date: 2026-07-02
---

# SUPERSEDED — Do Not Use As Plan Of Record

The `investigation.md`, `plan.md`, and `test_plan.md` in this directory document the **first**
implementation pass of `TCK-20260701-HAZARD-NATIVE-IMMUNITY`, which gated the hazard-drain
exemption on `entity.identity.faction == Faction.MONSTER_HORDE and region.kind ==
"WILDERNESS"`. That pass shipped, passed its own review and test suite, and was marked DONE —
it was not a bug or a mistake in execution.

It was **reopened and reverted on 2026-07-02** after further design discussion surfaced a
requirement that mechanism could not satisfy: hazard endurance must be a property a
faction/race declares for itself (e.g. "fiends endure chaos corruption because they're
fiends"), independent of hero-hostility, and a hazard kind nobody is flagged as enduring must
hurt every faction present — including two mutually hostile factions fighting in it together.
The `MONSTER_HORDE`/`WILDERNESS` design could not model either requirement.

The ticket was reopened (`tickets/done/TCK-20260701-HAZARD-NATIVE-IMMUNITY.md`, formerly
`tickets/inprogress/`) and the first pass's working-tree code/doc changes were surgically
reverted. The corrected design (`RegionState.hazard_kind` +
`FactionDefinition.hazard_immunities`, resolved via
`get_faction_id_str`/`FactionSemanticsService`) is now documented in `plan.md`/
`investigation.md`/`test_plan.md` **in this same directory** — those are the current plan of
record for the second (closing) pass.

This directory is kept, not deleted, per the project's traceability rule — it is real, valid
work correctly executed against a design that was later found insufficient.

## Incident note (2026-07-02, Finalize step of the second pass)
The **original** first-pass `investigation.md`, `plan.md`, and `test_plan.md` this notice
describes were accidentally **overwritten** (not merged alongside) when the second pass's
Finalize step moved the corrected-design staging artifacts into this directory — a plain `mv`
was used instead of merging under distinct filenames. Both directories held untracked
(never git-committed) files, so there is no git history to recover the original content from,
and no other on-disk copy was found. This is a genuine, unrecoverable loss of the literal
first-pass planning documents.

What survives as the historical record of the first pass's design and outcome:
- This file's summary above (written before the overwrite, preserved).
- `tickets/done/TCK-20260701-HAZARD-NATIVE-IMMUNITY.md` → Implementation Notes, which retains
  the first pass's exact gating condition
  (`entity.identity.faction == Faction.MONSTER_HORDE and region.kind == "WILDERNESS"`), why it
  shipped, and why it was rejected.
- `tickets/working_log.csv` — the first pass's original DONE entry (timestamp
  `2026-07-02T00:00:00Z`, before the redesign's entry of the same timestamp later in the file)
  describes its scope, test count (56 regression + 5 new), and doc/ledger edits at a summary
  level.

The `plan.md`/`investigation.md`/`test_plan.md` now present in this directory are the
**second pass's** (corrected-design) artifacts, not the original superseded ones.
