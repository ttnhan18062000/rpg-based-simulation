---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261006-CAMPAIGN-EPISODE-COMBAT-TEST-RED-BECAUSE-NO-DELIBERATE-ATTACK-ONLY-OPPORTUNITY-ATTACKS
artifact_type: investigation
tags: [engine, combat]
---

# Investigation: why the campaign combat test is red on main

Findings and numbers are in the ticket. This file records how they were obtained.

- `probes/first_bad_search.py <good> <bad>`: exports each candidate with `git archive` and runs the test from the export's own root (content seeds from the cwd-relative `data/content`); `probes/bisect.log` is its output (190 commits, first bad `bc00caa1a`, last good `24920f912`). Two classifier flaws were found and handled: pytest prints the whole test source on any failure, so "combat_initiated appears" is not evidence of the combat assertion failing; the boundary commits were therefore re-run and their actual assertion read (`assert 1 >= 3` at `bc00caa1a`). The script is named so it cannot shadow Python's `bisect` module.
- `probes/groups.py`: restores one file group of `bc00caa1a` to its parent's version and reruns. `candidate_selector`, contracts and campaigns: still 1. The governor, worker manager and kernel group: passes (the full group with `pipeline.py` fails to import because it is coupled to the new `ContractService`).
- `probes/campaign_actions.py <root>`: the test's own manifest, seed 42, 70 ticks; counts `ActionRouter` dispatches and combat entry points. Last good: 0 dispatches, 15 opportunity-attack resolutions; #366 head: 0 dispatches, 1.
- Positive control for the action counter: the same wrapper counted `ATTACK` 31 and `INTERACT` 431 on `crowded_frontier` in the action-handler ticket's probe, so a zero here is a measured zero, though through `ScenarioRuntimeService` rather than the standard worlds.
- Limit: the scripts hard-code this worktree's paths and scratchpad; they are a record, not a tool.
