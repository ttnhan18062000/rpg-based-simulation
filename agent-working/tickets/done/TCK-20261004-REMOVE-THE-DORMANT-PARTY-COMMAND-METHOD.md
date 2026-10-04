---
status: historical
layer: systems
authority: P1
audience: agent
ticket_id: TCK-20261004-REMOVE-THE-DORMANT-PARTY-COMMAND-METHOD
phase: done
date: 2026-10-04
tags: [social, documentation, investigation]
---

# TCK-20261004-REMOVE-THE-DORMANT-PARTY-COMMAND-METHOD

## Title

Remove `PartyCoordinationSystem.issue_party_command` — wiring is permanently ruled out, so the only
remaining disposition is removal, and keeping it now hides its own dormancy

## Status

DONE

## Tier

hotfix

## Type

chore

## Priority

P2

## Request Summary

`PartyCoordinationSystem.issue_party_command` (`src/systems/social_systems/party.py`) has **zero callers**
in `src/` or `tests/`. `TCK-20261004-TWO-REAL-UNDEFINED-NAMES-IN-SRC-ONE-LIVE-AND-SILENT` fixed a genuine
undefined name inside it (`StrategicUpdate`, at `src/core/updates.py:515`) and added its first-ever test,
leaving it correct and still uncalled.

**Every input to the disposition question has now been given, and they converge on removal:**

1. **Codebase-health already ruled, and the planner mis-assigned this.**
   `docs/plans/codebase_health/handoffs/handoff_to_rpg.md:117-120` states it directly: *"The ticket
   therefore asks for a decision, not just the one-word import fix: **wire it up or remove it.** Fixing
   the import and leaving an uncalled method preserves the dormancy while deleting the evidence of it."*
   `TCK-20261004-BIBLE-07-DESCRIBES-PARTY-COMMAND-BEHAVIOUR-THAT-NEVER-OCCURS` recorded this as an open
   question owned by codebase-health; that was wrong — codebase-health had already answered and handed
   the decision to the rpg domain. This ticket is the planner making the call it was handed.
2. **Wiring is ruled out permanently, not deferred** — `world-rule-catalog-design`, 2026-10-04. The
   function is not a valid realisation of the party-command concept: it accepts any `EntityState` as
   "leader" with no group parameter, so the command's content alone would confer authority (**AUTH-05**
   forbids this, **INST-02** likewise); its docstring claims "for all members" while it addresses no
   members and returns a single recipient-less `StrategicUpdate`; a `CRITICAL`-priority, salience-1.0
   directive to every member is override-shaped against **ORG-02 / AGENCY-01 / AGENCY-02**; and durable
   meaning sits in strings (`kind` a free `str`, `target` a `str(target_pos)`), breaking the Durable
   State Rule. Party commands are **PERMITTED, not REQUIRED** — `IP-S03` presumes a leader *may* issue a
   valid order; no Rule demands one. **Keeping the function preserves no design value**, and a future
   party-command feature would be designed fresh from `ORG-02`/`AUTH-05`/`INST-02`.
3. **No world-semantics objection to removal** — same ruling.
4. **Nothing is owed elsewhere.** `registries/mechanisms.yaml` has no party-command mechanism (only
   `party_formation` at `:1781`); `docs/parity_ledger/` has zero `issue_party_command`/`party_command`
   matches; `docs/audits/unreachable_code_inventory.csv:381` already lists it unreachable.
5. **The Bible sentence was written to anticipate this.** The corrected text in
   `docs/mechanics/07_social_political_dynamics.md:329` reads *"`issue_party_command()` exists in
   `party.py` but has no caller; no party-command behaviour occurs in the world…"*. The rule owner
   specified that on removal **the sentence simply drops its first clause**.

The argument for acting now rather than leaving it dormant is codebase-health's, and it is the sharpest
point in the chain: the import fix made the method *correct*, which removed the `NameError` that was the
only visible evidence it was never called. A dormant method that no longer carries a latent defect is
strictly harder to find next time.

## Scope

- Remove `PartyCoordinationSystem.issue_party_command` from `src/systems/social_systems/party.py`, and
  the test added for it by `TCK-20261004-TWO-REAL-UNDEFINED-NAMES-IN-SRC-ONE-LIVE-AND-SILENT`.
- Remove any import that existed only for it (the `StrategicUpdate` import added by that ticket, if it
  serves nothing else in the module).
- Edit `docs/mechanics/07_social_political_dynamics.md:329` to drop the first clause, per the rule
  owner's instruction, leaving the sentence about where leadership actually acts.
- Update `docs/audits/unreachable_code_inventory.csv:381` and the matching
  `docs/audits/unreachable_code_inventory.json` entry (`:4535`), or regenerate the inventory if it has a
  generator.

## Out of Scope

- Any other entry in the unreachable-code inventory. One method, named above.
- `TCK-20261004-POSITION-SWAP-CONTRACT-NEVER-CONSTRUCTED` — codebase-health's handoff calls it "the same
  class", and it may well resolve the same way, but it is P2 feature-adjacent work behind roadmap
  decision 7 and is **not** folded in here.
- Designing a party-command feature. Ruled out; a future one starts from the rules, not this code.
- `apply_leadership_influence()` and the rest of `party.py`. Untouched.

## Acceptance Criteria

1. `grep -rn "issue_party_command" src/ tests/` returns nothing.
2. `docs/mechanics/07_social_political_dynamics.md` describes leadership as acting only through
   `apply_leadership_influence()`'s goal injection, with no claim that `issue_party_command` exists.
3. `docs/audits/unreachable_code_inventory.{csv,json}` no longer list the method (or are regenerated).
4. No `src/api/`, `frontend/` or scenario/content reference to the method exists — verified by grep
   across the whole repo, not just `src/` and `tests/`, and the search is stated in the Test Summary.
5. Scoped tests pass: `tests/unit/systems/` (or the directory holding the party tests) plus
   `tests/unit/engine/`, since the removed import touches module-level state.
6. No `intentional_divergences.md` entry and no `docs/parity_ledger/` change — neither is warranted; see
   Request Summary §4.

## Related Tickets

- `TCK-20261004-BIBLE-07-DESCRIBES-PARTY-COMMAND-BEHAVIOUR-THAT-NEVER-OCCURS` — corrected the Bible
  sentence; this ticket drops its first clause. **Close that one first or in the same pass.**
- `TCK-20261004-TWO-REAL-UNDEFINED-NAMES-IN-SRC-ONE-LIVE-AND-SILENT` — fixed the import and added the
  test that this ticket removes; its record reads "kept, dormant, escalated to the rule owner via the
  planner", which this ticket resolves
- `TCK-20261004-POSITION-SWAP-CONTRACT-NEVER-CONSTRUCTED` — same class per codebase-health; deliberately
  not folded in

## Related Docs

- `docs/plans/codebase_health/handoffs/handoff_to_rpg.md:105-124` — the handoff that already made this
  call, and the "three instances of an artifact nothing validated" pattern it draws
- `docs/mechanics/07_social_political_dynamics.md` — `### Leadership Influence (party.py)`
- `docs/world_rules/` — `IP-S03`, `AUTH-05`, `INST-02`, `ORG-02`, `AGENCY-01`, `AGENCY-02`
- `docs/audits/unreachable_code_inventory.csv` / `.json`
- `docs/plans/rpg_design_roadmap/rpg_implementer_lane_split.md` — `party.py` is **Lane A** territory and
  `docs/mechanics/**` is contested; this ticket needs a planner-granted hold on both

## Related Stored Artifacts

None.

## Related Code Areas

- `src/systems/social_systems/party.py` — the method, its local imports, and the module's import block
- `src/core/updates.py:515` — `StrategicUpdate`, the only consumer of which here is the removed method
- the party test module touched by `TCK-20261004-TWO-REAL-UNDEFINED-NAMES-IN-SRC-ONE-LIVE-AND-SILENT`

## Assumptions / Open Questions

- **UQ-1:** does `StrategicUpdate` serve anything else in `party.py` after the removal? If it does, keep
  the import. Check, do not assume.
- **UQ-2:** does `docs/audits/unreachable_code_inventory.{csv,json}` have a generator? If so regenerate
  rather than hand-editing two files out of sync.
- The rule-catalog readings in Request Summary §2 are `world-rule-catalog-design`'s own, relayed
  verbatim and **not re-derived by this ticket's author**. Cite the owner, not this ticket, if quoted
  elsewhere.
- Line numbers in codebase-health's handoff and the rule owner's reading were taken at `origin/main`
  before the import fix landed. **Re-locate by symbol, not by line.**

## Implementation Notes

**Holds required, both planner-granted for the life of this ticket only:**
`src/systems/social_systems/party.py` (Lane A territory, extending the cross-lane exception already
recorded for this file) and `docs/mechanics/07_social_political_dynamics.md` (contested surface).

## Test Summary

- `tests/unit/social tests/unit/engine tests/refactor` (`-m "not slow"`): 539 passed, 0 failed, after the removal.
- AC-4 search, stated: `grep -rIn issue_party_command .` over the whole repo, excluding `.git`, `.venv`, `node_modules`, `graphify-out` and the `agent-working/` and `docs/plans/` history, returns nothing. That covers `src/` (including `src/api/`), `frontend/`, `tests/`, `data/`, `config/`, `tools/` and `docs/`. Historical mentions remain only in closed/in-flight ticket records, staging artifacts and the codebase-health handoff, which describe the past and were deliberately not rewritten.
- UQ-1 answered: `StrategicUpdate` (and `DirectiveState`/`DirectivePriority`) were imported only function-locally inside the method, so no module-level import remained to drop; `Optional` and the other module imports are still used elsewhere.
- UQ-2 answered: no generator for the inventory exists in the repo (searched `.py`, Makefile, shell and workflow files), so both files were edited by hand, byte-preservingly (the CSV's line endings were kept; the JSON round-trips identically before and after), one entry each.

## Files Changed

`src/systems/social_systems/party.py` (method removed); `tests/unit/social/test_party_issue_command.py` (deleted); `docs/mechanics/07_social_political_dynamics.md` (first clause dropped, leaving the sentence about where leadership acts); `docs/audits/unreachable_code_inventory.csv` and `.json` (one entry each). No `intentional_divergences.md` or `docs/parity_ledger/` change.

## Completion Summary

Removed the caller-less PartyCoordinationSystem.issue_party_command, its test, and its two inventory entries; dropped the Bible clause. Whole-repo grep shows no remaining reference outside historical records; tests/unit/social, engine and refactor pass.
