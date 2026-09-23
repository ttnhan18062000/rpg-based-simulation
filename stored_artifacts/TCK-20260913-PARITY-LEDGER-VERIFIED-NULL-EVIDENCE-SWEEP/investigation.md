---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP
artifact_type: investigation
---

# Investigation — TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP

## Scope guard

Per the ticket's own scope split with `TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS`: this
investigation covers `status: verified` entries whose named class/function/module is confirmed
**absent from src/ entirely** (a dangling citation, PROG-014's own shape), not the 1307-entry
bare-missing-`test_path` corpus that sibling ticket owns. Scope was further narrowed live during
the batch by `rpg-feature-planning` (binding, per `docs/plans/mechanism_claims_as_tests_initiative.md`
§3.1's seven search-failure shapes) and `agent-working-design`'s own relayed conditions:
attach exact search commands/scope to every "absent" claim; three outcomes (RE-POINT / DOWNGRADE /
LEAVE), prefer downgrade when unsure; write only through `tools/parity_ledger_writer.py`.

## Method

1. **Candidate extraction.** For every `status: verified` entry across all 9
   `docs/parity_ledger/*.yaml` shards (1888 entries), extracted candidate symbol/path strings from
   `text` + `v2_evidence`: CamelCase classes, `snake_case()` calls, backtick-quoted identifiers,
   PascalCase compounds, and `src|tests|tools|frontend|dashboard-frontend|.claude`-prefixed file
   paths ending in a real source extension.
2. **src/-only pass.** `grep -rl -F <candidate> src/` for every candidate. Sanity-checked against
   the ticket's own motivating case: `grep -rl -F StatsProxy src/` returns 0 matches, confirming
   the method catches the PROG-014 shape (StatsProxy was corrected out of the `verified` set by
   `TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED` before this sweep ran — see Findings).
3. **Full-repo escalation.** Any candidate absent from src/ alone was re-checked against the whole
   repo (excluding `docs/parity_ledger/`, `tickets/`, `stored_artifacts/`, `data/`,
   `agent-monitoring/data/`, `.venv*`, `node_modules`, `.git`) — this repo's infrastructure/tooling
   entries legitimately cite `dashboard-frontend/`, `tools/`, `tests/`, `.claude/`, not backend
   `src/`, and an src/-only scope for those entries would itself be shape 6 (scope-too-narrow).
4. **Git-history classification.** For anything still absent repo-wide: `git log --diff-filter=D
   --follow -- <path>` to find the deleting commit, then read the commit message / PR title for
   intent (deliberate retirement vs. accidental loss vs. rename), and cross-referenced the full
   entry `text`/`v2_evidence` for self-documented relocation notes.
5. **Test-path spot-check.** Not run systematically across all 1888 entries (see Limitations
   below) — only checked for entries already flagged suspect by steps 2-4. Confirmed absent test
   functions for `INFRA-228` this way (incidental find, not planned coverage).

## Findings

### PROG-014 accounted for (the ticket's own motivating example)

`PROG-014` (`docs/parity_ledger/progression.yaml`) is **not** `status: verified` — it is already
`status: missing`, corrected by `TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED` (commit
`71767d9bd`, 2026-09-13), *before this sweep's investigation began*. Step 1's `if e.get('status')
!= 'verified': continue` filter therefore excludes it at the very first step — the correct
behavior, not a hole in the pipeline. Confirmed directly against `origin/main` by
`agent-working-design` during the gate review. See the entry's own `support_boundary` for the
correction record.

### 1888 `status: verified` entries swept — 2 confirmed corrections

**Strong-candidate (PascalCase, class-like) layer:** 120 hits absent from `src/` alone. **All 120
resolved** once escalated to full-repo scope — real code/config in `dashboard-frontend/`, `tools/`,
`tests/`, `.claude/`, `docs/`. My own initial `src/`-only scoping for these was itself an instance
of §3.1 shape 6 (scope too narrow), caught and corrected in-session before any candidate was
reported as a finding.

**Module/file-path citation layer:** 36 paths absent on disk. 34 resolved as false positives:
- `SOC-001/002/003/004/006/008`, `SOC-051`, `STRAT-006/007/008/009`: the ledger already
  self-documents the relocation inline — e.g. `SOC-001`'s `v2_evidence` reads "...relocated from
  the now-deleted `src/systems/social.py` during the social-systems package split, function renamed
  from `evaluate_recruitment_offer`" and cites the real current path
  (`src/systems/social_systems/appraisal.py`), confirmed to exist.
- `STRAT-225/236/243/246/252`, `INFRA-211`: same pattern for the
  `TCK-20260811-DELETE-ADVENTURE-DECISION-PHASE` migration (`AdventureDecisionPhase` →
  `AdventureGoalScorer`) — each entry's `v2_evidence` carries an explicit "Addendum" or "relocated
  from" note naming the deleting ticket and the real successor, confirmed to exist.
- `SUBSTRATE-NEW-003`: self-correcting entry — its own `v2_evidence` narrates a *prior* wrong
  citation (`src/worldmodules/resolver.py` / `WorldModuleAssemblyResolver`) and its own fix
  (`src/worldassembly/resolver.py`); my path regex matched the historical mention inside the
  narrative, not a live citation.
- `INFRA-275/277/303` (GanttBar/RecentActivityGantt), `INFRA-225` (`src/lab/workflows.py`),
  `INFRA-323` (`biological.py`), `SUB-376` (`src/actions/attributes.py`): the missing path is
  mentioned as historical backstory or a negative-comparison point in the evidence prose, not as
  the load-bearing evidence for the entry's own claim — the actual cited proof for each entry's law
  is separate, current, real code.
- 12 infrastructure.yaml entries touching the retired Knowledge Gateway MCP subsystem
  (`INFRA-295/296/297/340/341/342/345/346/353/382/410/414`): already fully handled by
  `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY`'s own closure, which updated the 21 affected
  entries via `tools/parity_ledger_writer.py` as part of that ticket's own Step 8. No new action.

**Confirmed genuine (2 of 1888):**

1. **`INFRA-228`** (infrastructure.yaml, P1). `GracefulDegradationManager.resolve_content_source()`
   cited in `v2_evidence`; `src/domains/optimization/degradation.py` confirmed deleted (`find
   src/domains/optimization -type f` shows only `feature_flags.py` + pycache; git confirms via PR
   #176 "Batch: gate inert API subsystems, delete the remaining src/domains/optimization/
   package"). Cited `test_path`
   (`tests/unit/core/test_degraded_fallback.py::test_resolve_content_source_degraded_uses_catalog`)
   does not exist in that file — `grep -n "^def test_"` lists 4 different tests, none matching.
   Same bare-missing-citation shape as `PROG-001`. A sibling investigation
   (`tickets/done/TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION.md`) found
   a structural-match successor for the *general* degradation mechanism
   (`src/engine/governor.py::ResourceGovernor`) but explicitly leaves this specific behavior
   (cheapest-first catalog selection in degraded mode) unconfirmed. `agent-working-design`
   independently confirmed one sub-claim survives: the module-level `runtime_content_source`
   default change is still tested by
   `tests/unit/core/test_degraded_fallback.py::test_runtime_content_source_module_default_is_not_legacy_hardcoded`
   (line 30) — that test covers only the sub-claim, not the headline behavior.

2. **`WORLD-CULT-002`** (world_dynamics.yaml, P1). Core claim and its `test_path`
   (`tests/unit/domains/culture/test_culture_applicator.py::test_zero_culture_produces_zero_delta`)
   are solid and unaffected — `CulturalBiasApplicator.compute_culture_delta()` is real, unchanged,
   independently tested. Only the *consumption-site* citation
   (`src/domains/motivation/service.py`'s `culture_values` param) was stale — that file is
   confirmed deleted (commit `fc1abd089`, "delete dead Doctrine/Values chain"). Read the two real
   current consumers directly: `src/domains/adventure/scoring.py:294` (local `personality_bias`
   float accumulator, folded into a new route-option via `dataclasses.replace()`, never written
   back onto `entity`) and `src/domains/culture/settlement_personality.py:97`
   (`SettlementPersonalityService.describe()`, module docstring explicitly states "Pure and
   stateless... WORLD-CULT-002/003 stay untouched", builds an immutable frozen-dataclass
   descriptor). Both confirmed CERTAIN to satisfy the law's one required property (never mutates
   entity durable state) by direct code read, not inference.

## Method limitation (stated per gate requirement)

This sweep checks that **named symbols exist** (and, incidentally for the 2 flagged entries, that
cited `test_path` functions exist in their files). It does **not** check that an existing symbol
implements the behavior its entry's `text` claims. A `status: verified` entry that names a real
class for behavior that class does not actually have would pass this sweep untouched — that is the
§3.2 misattribution shape (confident false positive, not confident absence), and a symbol-existence
sweep cannot detect it. **The other 1886 entries passed "every cited symbol resolves to real code,"
not "the entry is correct."** This is a solid, real result for what it checked, not a corpus-wide
correctness certification.

Test-path-function existence was **not** checked systematically across all 1888 entries — only for
the 2 entries already flagged suspect by the symbol/path-existence layers above (`INFRA-228`
incidentally, `WORLD-CULT-002` as a deliberate cross-check once flagged). The closest prior
systematic coverage of this specific shape (a cited `test_path` function that does not exist in its
named file) is `TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT`, which found `PROG-001` this
way; this ticket does not claim to extend that coverage to the remaining corpus.

## Related

- `TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT` — `PROG-001`, the bare-missing-citation
  method this ticket reused for `INFRA-228`'s test_path check.
- `TCK-20260912-VETERANCY-STAT-MULTIPLIER-NEVER-APPLIED` — corrected `PROG-014` before this sweep
  ran; the ticket's own motivating example.
- `TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS` — owns the corpus-wide bare-missing-`test_path`
  policy question (1307 entries); explicitly out of this ticket's scope.
- `TCK-20260911-OPTIMIZATION-PACKAGE-SUPERSEDED-OR-MISSING-DETERMINATION` — the open question
  `INFRA-228`'s `divergence_note` now points at.
- `TCK-20260908-KGMCP-DELETE-ARCHIVED-GATEWAY` — already handled the 12 KGMCP-touching entries.
