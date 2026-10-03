---
status: active
layer: testing
authority: P2
audience: agent
tags: [testing]
---

# Mutation baseline method

How a mutation baseline in `tests/mutation/baselines/` is produced. The method was kept only inside the
baseline records and the batch reports, and was re-derived once for the social baseline. This page writes it
down once. It is a method, not a policy: it adds no tool, no gate and no threshold.

A baseline is an **observation of what a named test selection catches on a named target at a named SHA**. It
is not a score to defend. Survivors are findings, never requests to change a test, and some survivors may be
equivalent mutants (the records say `equivalent: not-classified`).

Worked examples, referenced and not copied:

- `tests/mutation/baselines/src_core_conservation_v3.json` (supersedes v2, which superseded v1).
- `tests/mutation/baselines/src_systems_social_appraisal_v1.json` (the fullest record: it carries the G3,
  positive-control, `stale_after` and catalog-CONFLICTING fields below).
- `docs/testing/social_test_report_2026-10-03.md` §4 (the social run's summary).

## 1. Procedure

1. **Pin the SHA.** Name one full 40-character `origin/main` SHA for the whole run. Every figure in the record
   names it.
2. **Scratch copy.** Make the copy with `git archive` of that commit into a directory **outside the repo**,
   with a cleared `.mutmut-cache`. Mutation edits files in place, so it never runs in the working tree.
3. **Install mutmut with `pip --target`** into a private scratch directory (the social record: mutmut 2.5.1,
   `python -m pip install --target <scratch>/mutmut_pkg mutmut==2.5.1`). It is an optional dev tool, not a
   project dependency, and the shared venv is untouched. No configuration file is added to the repo: every
   option is on the command line, and the record's `tool.reproduction_command` carries it.
4. **Selection.** Resolve the test files with `tools/test_architecture/mutation_selection.py`, rule
   `import-based-one-hop`: a `tests/**/test_*.py` (excluding `tests/mutation/`) is selected when it imports the
   target module, or imports a `src/` module that itself imports the target directly. Record the rule, the
   resolved file list, the one-hop `src/` modules and the sha256 of the resolved list
   (`selection.resolved_files_sha256`; the social record also folds it into a `selection_identity`). Curated
   additions are appended by hand and recorded in their own list (`curated_additions`), never merged into the
   rule's list. The rule is a starting point: dynamic imports, fixtures and paths of two or more hops are not
   found, and the record's `not_proof` field says so. A file the plan expected but the rule did not select
   (for example `tests/unit/social/test_multi_hero.py`) is named in `known_exclusions`, not silently added.
5. **Green before mutation.** Run the selection unmutated and confirm it passes; record the count and time
   (social: 313 passed in about 5 s). A selection that is not green gives meaningless kills.
6. **G3, the determinism check.** Detect whether the selection runs the kernel at all (a read-only pytest
   plugin kept outside the repo can count `Kernel.tick_once` calls per file). If it does, the kernel drops a
   tick's results when `audit_mode` is false and the tick exceeds `max_tick_budget_ms` (reference:
   `docs/engine/deterministic_execution.md`, extension rule 5), so a slow mutated run could change results
   for a reason that is not the mutant. Force `audit_mode=True` and a relaxed budget through the **out-of-repo
   plugin only** (`PYTHONPATH` and `-p <plugin>` on the runner), confirm the selection is still green under the
   forcing, and record **both the as-found and the forced values** in `determinism_g3`. The social record:
   kernel ran in 3 selected files (5 calls), as found `audit_mode False` and `max_tick_budget_ms 100`, forced
   `audit_mode=True` and `max_tick_budget_ms=10000000`. No test or source file in the repo is changed. If the
   kernel does not run in the selection, say so (`kernel_ran_in_selection: false`) and skip the forcing.
7. **Fresh positive control, per new target.** Before trusting a run, make one hand mutant of the target that a
   selected test must catch (social: `appraisal.py` line 67, `public_trust * 0.7` to `* 0.6`), apply it in the
   scratch copy, and require that the same runner and environment **fail** on it and **pass** on the
   original; then restore the target and check its sha256 equals the recorded one. A control may be reused
   only for a rerun of **the same target and the same selection**; a new target or a changed selection needs a
   fresh one. The control shows the runner, environment and forcing can kill a mutant of this target; it does
   not validate the selection (the record's `positive_control.scope` says so).
8. **Detached run.** Launch the run with `setsid` so it survives the session ending: a plain background run was
   killed when a session closed in an earlier baseline
   (`agent-working/stored_artifacts/TCK-20260930-CORE-RPG-TEST-BASELINE-POST-REPAIR/investigation.md`,
   relaunched fully detached).
9. **Run and collect.** `mutmut run --paths-to-mutate <target>` with a runner of
   `python -m pytest -x -q -p no:cacheprovider` plus the selected files (and the plugin if G3 forced). Collect
   total, killed, survived, timeout and suspicious counts and the survivor diffs.

## 2. The record

Each baseline JSON carries, at least the fields below. **Provenance** (which SHA, which tool, who chose the
target) is carried by `run`, `tool` and `target_selection` together, and `stale_after` says when it stops
being trusted; there is no single `provenance` key.

| Field | What it holds |
|---|---|
| `run` | start and finish, runtime, `source_sha` (full), how the copy was made, the target's last-changed commit |
| `tool` | name, version, install and reproduction commands |
| `selection`, `tests` | rule, resolved list, its sha256, green-before-mutation line, known exclusions, `not_proof` |
| `determinism_g3` | kernel detection, as-found values, forced values, reference |
| `positive_control` | fresh or `reused_from`, the mutant, expected and observed, scope |
| `counts`, `survivors` | the totals and the survivor list |
| `target_selection` | who confirmed the target and when, why it was chosen, and what was excluded and why |
| `stale_after` | `target_sha256_changes`, `selection_changed`, `days` (30 in both examples), and any named event |
| `expectation_note` | the statement that no survivor-count threshold applies |

`stale_after` is how a baseline stops being trusted: the target file's sha256 changing, the re-resolved
selection differing, 30 days passing, or a named landing. The social record names
`TCK-20260822-RELATIONSHIP-VECTOR-ADDITIVE-FIELD`, because it touches relationship precedence and `appraisal.py`
measurements go stale when it lands. A newer record names the one it replaces in `supersedes`, and a changed
selection is a **new comparison population, not a re-measurement**: the v1 and v2 conservation scores must not
be read as a score change (see the pilot's v2 update).

### Catalog-CONFLICTING lines

Where a read in the target is marked CONFLICTING by the world-rules catalog (the social example: the
`public_reputation` read on line 46 and the `clan_reputation` read on line 64 of `appraisal.py`, PERC-01 /
KNOW-01), keep the mutants on those lines in **separate, labelled lists**
(`catalog_conflicting_survivor_ids`, `catalog_conflicting_mutants_on_those_lines`,
`catalog_conflicting_note`). Any survivor among them carries the label "current behaviour,
catalog-CONFLICTING". The label comes from the catalog owner's answer and is not re-derived here; the list is
an observation, not a recommendation either way. At the social run's SHA there was no such survivor: all 7
mutants on those two lines were killed, so the selected tests pin that current behaviour.

## 3. Reach check before reporting a zero (rule added 2026-10-03)

**Before reporting 0% coverage or 0 kills for a file or a function, run a reach check with the repository's
other tests that touch it** (search the importers of its callers, not only of the target), and report the
number together with its **selection scope**. A zero measured under one selection is a statement about that
selection, not about the code. The check runs in scratch, changes no test, and its result is not a defect
finding.

Two cases from the social batch, both read from the batch report and its records:

- **`guilds.py`, a false zero for live code.** Under every social selection `guilds.py` reads 0% (39
  statements). It is imported by `src/systems/guild_system.py`, so it is live code in the social directory
  owned by another domain, and `tests/unit/world/test_guild_intel.py` (2 tests, both passed; it calls
  `GuildIntelSystem.update`) covers it at **92%** (3 statements missed), with the same coverage command.
  Measured at branch head `f13baaf24578eb4529948f4e7e045c8468ca6886` (`origin/main`
  `9640ff942877cc7264e83309f35d19022a4a3fe6` plus the C1 routing case). Source: report §2.2.
- **`_appraise_position_swap`, a zero that survives the reach check.** 0 of 38 mutants were killed under the
  one-hop selection, which only names `POSITION_SWAP` in a gate-dispatch dict. A reach check on three other
  files that exercise it (`tests/unit/movement/test_position_swap.py`,
  `tests/integration/pipeline/test_movement_micro_arena_position_swap.py`,
  `tests/unit/ai/goals/test_social_contract_goal_scorer.py`; 24 tests passed) executed **1 of the 28
  statements** (lines 234 to 298), so the zero was not an artefact of the selection, though only those three
  files were checked. Measured at `origin/main` `9640ff942877cc7264e83309f35d19022a4a3fe6`. Source: report §4.

The first case changed the answer; the second confirmed it. Each result states its scope, and neither is a
claim about the rest of the repository.

## 4. What a baseline is not

- Not proof that every relevant test is selected (`not_proof`), and not a score to raise.
- Not an equivalent-mutant classification.
- Not a defect list: a survivor is an observation about that selection at that SHA.
- Not a basis to edit, move, mark or strengthen a test; any such work is a separate, owned ticket.
