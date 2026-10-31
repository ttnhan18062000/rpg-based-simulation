---
content_type: doc
status: historical
layer: ai
authority: P2
audience: agent
tags: [ai, governance, delivery]
---

# Research stage R0: inventory record

Result record for `TCK-20261031-SDLC-R0-INVENTORY-AND-BASELINE-TAGS` (plan section 70). R0 is read-only apart from the tags (created by the owner). Plan read as on main at `1ccaba303`; repository state read at `origin/main` `6fdfdf555`, 2026-10-31. Nothing here is a decision: OD-16 to OD-21 stay undecided and no budget is named.

## 1. Candidate tasks (plan section 66)

Method: the 80 first-parent merges since 2026-10-10 were filtered to those that change both code and tests (about 40). Ten merged PRs (eleven tickets) with a narrow, single-purpose change were read against the admission test; two of them (#789, #779) only for a shorter check. **Every verdict is "static reading; controls not run, needed before R1"**: ticket text, test file names and test imports were read. The positive control (the grader passes on the true solution) and negative control (it fails on the base commit) were **not run**; that needs a lead slot and is outstanding. "Provisional" means admissible on the static reading and subject to those controls. By the owner's narrowing of R0 (#715 6540856174) the controls are **not** run in R0.

Base is the merge's first parent; solution is the merge commit.

| # | Source close (PR, tickets) | Base → solution | Grader | Verdict |
|---|---|---|---|---|
| 1 | #733 `TCK-20261024-PERF-TOOLS-HELP-FLAG-NEVER-STARTS-A-RUN` | `ab184acfc` → `2b8b1d989` | new `tests/unit/perf/test_tools_help_never_runs.py`; it forbids child processes, so running it on the base cannot start a benchmark | **Provisional.** The symptom (`--help` starts a run) can be stated without the cause. The ticket text names the cause (hand-read `sys.argv`), so the spec must be rewritten from the symptom. |
| 2 | #762 `TCK-20261027-CRAFT-UNKNOWN-RECIPE-RAISES-KEYERROR` | `13c1b1307` → `792a6b439` | added case in `tests/integration/economy/test_crafting_live_path.py` | **Provisional.** Behavioural ("an unknown or missing recipe is refused, not raised"). The ticket quotes the line and the old behaviour; the spec must drop the fix direction. |
| 3 | #762 `TCK-20261027-HISTORY-SNAPSHOT-STRIP-MISSES-NESTED-GRAPH` | `13c1b1307` → `792a6b439` | edit to `tests/unit/observability/cognition/test_cognition_query_service.py` (uses `build_snapshot_record`, which exists on the base) | **Provisional.** Same note on the ticket naming file and line. |
| 4 | #752 `TCK-20261026-PAIRED-COMPARES-COLLECTED-OFF-HOST-RESULTS` | `35e80fb56` → `1f749c1aa` | new `tests/unit/tools/test_rpg_measure_collected.py` | **Provisional.** The ticket carries an agreed CLI contract, so the spec is the contract, not the solution. Larger than the others; may sit near the frontier. |
| 5 | #727 `TCK-20261022-RPG-GATE-KNOWN-ENTRY-CAN-NAME-A-WORLD-AND-SEED` | `6c1373951` → `0a3df6159` | new cases in `test_known_reds.py`, `test_rpg_gate_candidate.py`, `test_rpg_gate_report.py` | **Provisional.** Whether the new tests call API names the ticket does not specify was not checked. |
| 6 | #789 `TCK-20261029-A-BROKE-HUNGRY-SUBJECT-NEVER-EARNS-SO-THE-FREE-MEAL-CANNOT-GO` | `ba7aa11bd` → `3b16d1cab` | new `tests/integration/scenarios/test_a_broke_hungry_worker_earns_and_then_eats.py` and `tests/unit/engine/test_earn_shift.py` | **Provisional, shallow.** Only the ticket header and test file names were read. `test_earn_shift.py` probably names the solution's API; the scenario test is the likelier grader. |
| 7 | #779 `TCK-20261028-EVENT-RECORDER-NEVER-GIVEN-THE-RUN-ID-SO-EVENTS-SAY-UNKNOWN-RUN` | `f102085e0` → `1d8eef91f` | new `tests/unit/observability/test_event_recorder_run_id.py` | **Provisional, shallow.** As row 6. |
| – | #765 `TCK-20261023-SALTED-HASH-IN-HASHED-STATE-FACTION-SQUAD-GROUP-ID` | `957caf8f6` → `f34d8254d` | `tests/unit/domains/faction/test_squad_group_id_hashseed.py` | **Quarantined:** the grader imports `src.core.stable_hash`, a module the solution adds, so a solver must guess its name. Could return with a rewritten grader. |
| – | #720 `TCK-20261022-NO-MEAT-DECAYED-RECORD-FOR-A-CARCASS-RE-ADDED-ON-ITS-DECAY-TICK` | `81b387aa8` → `e8df8b96d` | `tests/unit/engine/test_no_meat_decay_record_for_a_readded_carcass.py` | **Quarantined:** the spec rests on a CI run and a trace file outside the repository, and on an owner decision about splitting the work. Not solvable from the frozen state. |
| – | #785 `TCK-20261027-CAPACITY-GATE-FIRST-RECORD-OF-KIND-IS-DEAD-SO-LIVE-SIBLING-NEVER-RESUMED` | `abcf14869` → `fe604fff2` | `tests/unit/strategic/test_project_lookup_live_record_first.py` | **Quarantined:** the evidence cited lives in scratch files outside the repository. |
| – | #769 `TCK-20261020-HUNGER-AND-RETREAT-ON-ONE-ESCALATION-SCALE` | `a25619971` → `d914bace7` | `tests/unit/ai/test_retreat_escalates_on_the_need_scale.py` and an edit to a mechanic scenario | **Quarantined:** the behaviour is the outcome of owner decisions and measured runs, so "fair acceptance" cannot be shown from the ticket. |

**Count:** 7 provisional tasks (the plan expects 6-8; that expectation is confirmed only after the controls), 4 quarantined with reasons, from 11 tickets (10 PRs) read. The rejection rate (4 of 11) is a tracked metric, not a failure (section 66). Where a ticket text names the cause, the task spec has to be rewritten without it before use: that is R1 work, not done here.

Not done, by choice, and needed before R1: the positive and negative control for each provisional task, and the section 66 check that the environment rebuilds. Nothing is built toward the pilot.

## 2. Disposition review (plan section 32a)

Every row has a disposition. The disposition is the plan's recommendation carried here with what R0 checked; **it is not an owner decision**, and the gates (OD-5, OD-6, R2) are undecided. "Checked" lists what was measured on `6fdfdf555`; "not checked" says so.

| Component (32a row) | Plan recommendation | R0 disposition | Checked |
|---|---|---|---|
| `implement-ticket.js`, `implement-epic.js` | Freeze as experimental baseline | **Freeze** (tag, below); gate OD-5 | Pipeline-marked runs in the shards since 2026-10-04: the last DONE is 2026-10-04T05:14; five later starts ended `WORKFLOW_ERROR`, `NATIVE_GATE_SITES_UNPORTED` or `TAGS_NOT_REGISTERED`. That agrees with "0 completions since 10-04". `implement-ticket.js` is 2,379 lines (last change 2026-10-09), `implement-epic.js` 670 (2026-10-03). 61 test files under `tests/` name one of the two files (the plan says about 57): 50 in `tests/tools`. |
| Skill imitation | Retire | **Retire**, gate OD-5 | The `implement-ticket` and `implement-epic` skills exist under `.claude/skills/`. "Not reproducible" was not checked. |
| Provider-neutral contract + YAML | Freeze | **Freeze** (tag, below); gate R2 | `tools/agent_orchestration` is 630 lines; `agent-working/agent-orchestration/` holds the YAML. Its tests share one CI lane with the Codex tests (see the Codex row). |
| Codex track | Freeze, not maintain | **Freeze** (tag, below); gate R2 | Non-test Python lines by `git ls-files` glob (`*.py` only): `tools/agent_codex*` 2,768; `tools/agent_orchestration_codex_adapter` 101; `tools/agent_replay_codex` 586; total **3,455**. Plan 32a says about 5.0k for the track alone; sections 32 and the retirement table say 5.0k for "Codex track + replay". About 5.1k is reached only by adding `tools/agent_replay` (1,659). So the plan's sections disagree with each other, and 32a's figure does not match the track alone. One CI lane, "Agent orchestration / codex / replay" in `.github/workflows/test.yml`, runs the Codex tests together with `tests/agent_orchestration`, so leaving CI needs the lane split first. |
| `tools/agent_replay`: sampler, exclusion logging, metrics | Extract for research | **Extract** at R1, gate R0 | `sampler.py`, `metrics.py` and the fixture modules exist; last change 2026-10-04. Reuse cost not measured. |
| `tools/agent_replay`: `runner.py`, detectors | Freeze with the pipeline | **Freeze** (tag, below) | `runner.py`, `defect_detectors.py` exist. Coupling to pipeline gate branches was not checked. |
| `model_routing_mechanical_agents_experiment.md` | Rewrite for the hand path at R2 | **Rewrite at R2** | Not checked. |
| `paired-arms.yml`, `rpg_measure/paired.py` | Preserve; do not couple | **Preserve** | Both exist; `paired.py` gained a load-only comparison mode in #752. |
| Context packet assembler | Archive | **Archive** at the gate | `tools/context_packet_assembler.py` last changed 2026-10-04. Importers: `retrieval_events.py` and four tests. Not wired into any hook. |
| Headroom MCP | Retire now | **Retire** ("now" is the plan's disposition) | **Not yet done:** the `headroom` server is still in `.mcp.json` and `tools/start_headroom_mcp.sh` exists. Nothing was changed here. |
| `retrieval_cache.py` | Investigate, then archive | **Investigate** at Phase 5 | No module imports it; `write_path_guard.py`, `context_packet_assembler.py`, `retrieval_events.py` and `post_tool_hook.py` mention it in comments or wrap its check functions by name. Supports "not wired"; the runtime trace (whether anything calls it) was **not done**. |
| Shadow reviewer path | Extract reviewer prompt and contract | **Extract** at R2 | `tools/agent-monitoring/shadow_reviewer_events.py` exists. Not examined further. |
| `create-tickets.js` | Preserve | **Preserve** | 1,066 lines; last change 2026-10-06. |
| Hand path + recorder | Harden | **Harden** | The recorder now requires a `path_note` for `owner_directed` and `other` (`TCK-20261031-SDLC-HAND-PATH-OFFICIAL-AND-BASELINES-FROZEN`). |

## 3. Billing and subscription limits

**Outstanding by the owner's choice** (#715 comment 6540856174: billing is "not now" and the research is deferred). No account details are recorded and no further question is asked. R1 and later stages do not start until the owner says otherwise; OD-16 stays open. Everything else in R0 stands without it.

## 4. Baseline tags (OD-15, decided: freeze baselines as tags)

The owner created and pushed the four annotated tags on 2026-10-31 (#715 comment 6541773425). All four are on `origin`, annotated, at `6fdfdf5556548105e28ab370832f36bc96241561`. R0 created no tag and moved none. Each tag message holds only a name and a measured result; **the test command is in this record, not in the tag**.

| Tag | What it freezes | Result in the tag message | Test command (lives here) |
|---|---|---|---|
| `baseline/sdlc-pipeline-workflows-20261031` | `.claude/workflows/implement-ticket.js`, `implement-epic.js`, the two skills, their source-pinned tests | 342 passed, 3 skipped, 1 xfailed | `pytest tests/agent_orchestration tests/agent_orchestration_claude_adapter tests/tools -k "implement_ticket or implement_epic or workflow or sidecar or step0"` |
| `baseline/sdlc-provider-neutral-contract-20261031` | `tools/agent_orchestration`, `agent-working/agent-orchestration` YAML and adapters | 139 passed | `pytest tests/agent_orchestration tests/agent_orchestration_claude_adapter tests/agent_orchestration_codex_adapter` |
| `baseline/sdlc-codex-track-20261031` | `tools/agent_codex*`, `agent_replay_codex`, `agent_orchestration_codex_adapter` | 299 passed, 5 skipped | `pytest` over `tests/agent_codex_live_transport`, `agent_codex_pilot_executor`, `agent_codex_pilot_guardrails`, `agent_codex_pilot_orchestration`, `agent_codex_posttool_adapter`, `agent_codex_realrepo_pilot_harness`, `agent_codex_runtime_shadow`, `agent_replay_codex`, `agent_orchestration_codex_adapter` |
| `baseline/sdlc-agent-replay-20261031` | `tools/agent_replay` (sampler, runner, detectors) | 45 passed | `pytest tests/agent_replay` |

**How the results were measured:** 2026-10-31, CPUs 4-5, `-n 2`, in a detached git checkout of `6fdfdf555`. A first attempt in a tree made with `git archive` (no `.git`) failed, because some tests run `git status`; it was discarded and the numbers above come from the re-run in a real checkout.

Tags are **not protected** until the ruleset ticket (`TCK-20261031-SDLC-RULESET-M1-AND-TAG-PROTECTION`) lands; until then anyone with push access can move or delete one.

## 5. Still needed before R1

Nothing in this list is started; R1 and later stages wait for the owner (#715 6540856174).

- The owner's decisions on OD-16 (evaluation investment and execution), OD-17 (framework), OD-18 (scope of comparisons) and OD-21 (threshold and budget per stage). None is decided and this record names no budget.
- The positive and negative control for each of the 7 provisional tasks, the section 66 environment-rebuild check, and rewritten task specs that no longer name the cause.
