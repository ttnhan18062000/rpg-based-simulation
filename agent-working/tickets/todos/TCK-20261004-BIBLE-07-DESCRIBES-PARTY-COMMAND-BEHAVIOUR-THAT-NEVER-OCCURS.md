---
status: active
layer: mechanics
authority: P1
audience: agent
ticket_id: TCK-20261004-BIBLE-07-DESCRIBES-PARTY-COMMAND-BEHAVIOUR-THAT-NEVER-OCCURS
phase: open
date: 2026-10-04
tags: [social, documentation, investigation]
---

# TCK-20261004-BIBLE-07-DESCRIBES-PARTY-COMMAND-BEHAVIOUR-THAT-NEVER-OCCURS

## Title

Correct Bible 07's `issue_party_command()` sentence in place — the function has no caller, so no
party-command behaviour occurs in the world (rule owner's ruling, verbatim replacement text below)

## Status

OPEN

## Tier

hotfix

## Type

bug

## Priority

P2

## Request Summary

`docs/mechanics/07_social_political_dynamics.md` describes `issue_party_command()` as world behaviour.
The function has **zero callers** — nothing in the simulation ever issues a party command — so the Bible
describes a mechanic that does not occur. Found while closing
`TCK-20261004-TWO-REAL-UNDEFINED-NAMES-IN-SRC-ONE-LIVE-AND-SILENT`, which fixed a genuine undefined name
in the same function (`StrategicUpdate`, at `src/core/updates.py:515`, omitted from the function-local
import).

Escalated to the rule owner (`world-rule-catalog-design`) rather than decided by the planner, because
"should the mechanic exist" is a world-semantics question. **The owner ruled: the doc is wrong; correct
it in place.** Their reasoning, recorded because it closes off the other option permanently:

- **Party commands are PERMITTED, not REQUIRED.** `IP-S03` presumes "a leader issues a valid order"; no
  Rule demands one. So nothing in the catalog is unsatisfied by the behaviour's absence.
- **This function would not be a valid realisation anyway**, read at `origin/main` `party.py:123-145`:
  - **AUTH-05 / INST-02** — it takes any `EntityState` as "leader" and has no group parameter, so it
    never checks that the caller leads anything. The content of the command alone would confer
    authority, which `AUTH-05` forbids.
  - Its docstring says "for all members", but it addresses no members: it returns a single
    `StrategicUpdate` with no recipient. Bible 07's "creates a directive for all members" is false of
    the code as written.
  - **ORG-02 / AGENCY-01 / AGENCY-02** — membership is never a universal override of a member's own
    decision, and a `CRITICAL`-priority, salience-1.0 directive pushed to every member is
    override-shaped. The conformant shape already exists and runs: `apply_leadership_influence()`
    injects the leader's objective as a *candidate* that survival needs can outscore.
  - **Durable State Rule** — durable meaning sits in strings: `kind` is a free `str` and `target` is
    `str(target_pos)`.
- A future party-command feature would therefore be designed fresh from `ORG-02`/`AUTH-05`/`INST-02`,
  **not** by wiring this function. Keeping it preserves no design value.
- Independently, wiring would be new feature work, which the memo's row 7 freezes.

**Deliberately not an `intentional_divergences.md` entry.** That file records code that intentionally
departs from the Bible; here the code never ran the behaviour, so nothing in the world diverges, and none
of its rationale classes fits. Filing it there would misfile it. Verified by the planner: this ticket's
author found **zero** `issue_party_command`/`party_command` matches anywhere in `docs/parity_ledger/`, so
no ledger entry needs marking `missing`/`unsupported` either, and the owner does not want one added for a
doc correction. `registries/mechanisms.yaml` has no party-command mechanism (only `party_formation` at
`:1781`), so the registry already agrees and nothing is owed there.

## Scope

A single in-place sentence correction in `docs/mechanics/07_social_political_dynamics.md`, following that
section's own existing precedent for corrections ("Corrected — there is no `PartyRecord` type…").

**Anchor, verified unique** — one occurrence of `issue_party_command` in all of `docs/mechanics/`, at
`07_social_political_dynamics.md:328`, in the `### Leadership Influence (party.py)` section. The sentence
wraps across lines 328–329; match both lines.

**Replace this text exactly:**

```
`issue_party_command()`
creates a `CRITICAL`-priority `DirectiveState` (REGROUP/RETREAT/ATTACK) for all members.
```

**With this text exactly (the rule owner's wording, not to be paraphrased):**

```
`issue_party_command()` exists in `party.py` but has no caller; no party-command behaviour occurs in
the world. Leadership acts only through `apply_leadership_influence()`'s goal injection above.
```

Re-wrap to the file's prevailing line width if needed; do not reword.

## Out of Scope

- **Wiring `issue_party_command()`.** Ruled out on the catalog, permanently — see Request Summary.
- **Removing the function.** The rule owner states there is no world-semantics objection to removal, and
  `docs/audits/unreachable_code_inventory.csv:381` already lists it as unreachable
  (`PartyCoordinationSystem.issue_party_command`, `src/systems/social_systems/party.py:123`). But
  keep-vs-remove is a **codebase-health** disposition call, not a mechanics one, and it touches Lane A's
  `party.py`. If it is later removed, the corrected sentence simply drops its first clause. See
  Assumptions.
- Any `intentional_divergences.md` or `docs/parity_ledger/` change — both ruled out above.
- Any code change. The undefined-name fix already landed in
  `TCK-20261004-TWO-REAL-UNDEFINED-NAMES-IN-SRC-ONE-LIVE-AND-SILENT`.

## Acceptance Criteria

1. `docs/mechanics/07_social_political_dynamics.md:328-329` carries the replacement text verbatim; the
   old claim that a directive is created "for all members" is gone.
2. No `intentional_divergences.md` entry is added, and no `docs/parity_ledger/` entry is created or
   modified by this ticket.
3. `grep -rn "issue_party_command" docs/` shows the function described only as caller-less.
4. The rule owner's rationale is traceable from the doc change — this ticket ID appears in the commit
   subject.

## Related Tickets

- `TCK-20261004-TWO-REAL-UNDEFINED-NAMES-IN-SRC-ONE-LIVE-AND-SILENT` — fixed the undefined name in this
  same function and escalated the disposition question; its record reads "kept, dormant, escalated to the
  rule owner via the planner"
- `TCK-20260908-RAID-SIZE-FORMULA-DOC-CODE-MISMATCH` — open; the same doc-describes-absent-behaviour shape
  in a different chapter

## Related Docs

- `docs/mechanics/07_social_political_dynamics.md` — `### Leadership Influence (party.py)`
- `docs/world_rules/` — `IP-S03`, `AUTH-05`, `INST-02`, `ORG-02`, `AGENCY-01`, `AGENCY-02`; accepted Rule
  IDs outrank the Bible
- `docs/audits/unreachable_code_inventory.csv:381`
- `docs/plans/rpg_design_roadmap/rpg_implementer_lane_split.md` §3 — `docs/mechanics/**` is contested
  surface, so this ticket carries an explicit planner-granted hold

## Related Stored Artifacts

None.

## Related Code Areas

- `src/systems/social_systems/party.py:123-145` — read only; no change in this ticket
- `src/core/updates.py:515` — `StrategicUpdate`, for reference

## Assumptions / Open Questions

- **UQ-1 (open, owner named):** keep the dormant function or remove it? Codebase-health's call, with no
  world-semantics objection to removal. Not blocking this doc correction either way.
- **UQ-2:** the rule owner read the function at `origin/main` `party.py:123-145`. Lane B has since fixed
  the import on its branch, so line numbers may shift. Re-locate by symbol, not by line.
- Assumption: the `IP-S03`/`AUTH-05`/`INST-02`/`ORG-02`/`AGENCY-01`/`AGENCY-02` readings are the rule
  owner's own, relayed verbatim and **not independently re-derived by this ticket's author**. They are
  the owner's to own; do not re-litigate them here, but cite the owner rather than this ticket if they
  are quoted elsewhere.

## Implementation Notes

**Contested-surface hold:** `docs/mechanics/**` belongs to neither implementer lane. The planner grants
an exclusive hold on `docs/mechanics/07_social_political_dynamics.md` for the life of this ticket only.

## Test Summary

_(to be filled during implementation)_

## Files Changed

_(to be filled during implementation)_

## Completion Summary

_(to be filled during implementation)_
