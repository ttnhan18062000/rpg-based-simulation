---
status: active
layer: ai
authority: P2
audience: developer
tags: [ai, workflows, hooks, agent-monitoring, schema, process-improvement]
---

# New Finding — `.agents/` Has a Live Test Dependency (Claude Code)

For: [idea_provider_agnostic_agent_orchestration.md](idea_provider_agnostic_agent_orchestration.md)

Source: an independent, broader audit of all agent-orchestration logic in
this repository — not a review of this plan's text. That audit surfaced one
fact directly relevant to this plan's `.agents/` disposition work, which
none of the five prior review rounds (either reviewer) discovered.

## Finding

`.agents/` is not purely dead legacy scaffolding, contrary to how the
Current-State Inventory currently characterizes it ("Existing but stale;
must be disposed of before new Codex work") and how every review round has
treated it as safe to archive/rewrite once classified.

`src/lab/registry.py`'s `WorkflowRegistry` class parses YAML frontmatter
directly out of `.agents/workflows/*.md` and `.agents/skills/*/SKILL.md` —
confirmed via its class docstring and constructor call sites.

`tests/unit/lab_agent/test_workflow_registry.py::test_real_registry_contracts`
is a currently-**passing** test that instantiates `WorkflowRegistry` against
the real `.agents/workflows` and `.agents/skills` directories and asserts
specific fields (`allowed_actions`, `forbidden_actions`) on the real
`GenerateSimulationSetup` and `PrepareSimulationExecution` contracts parsed
from those files. Ran `pytest tests/unit/lab_agent/test_workflow_registry.py -v`
directly — all 4 tests pass today.

`WorkflowRegistry` has zero production callers — `src/lab/cli.py` (the
registered `rpg-lab` console-script entry point) never imports or invokes
it. Its only live caller anywhere in the repo is this test file. So nothing
breaks at runtime today, but a currently-green CI test would break
immediately if `.agents/workflows/` or `.agents/skills/` content is deleted,
moved, or rewritten as part of the disposition work this plan's Workstream A
item 1 calls for, without that test being updated in the same change.

Provenance: `docs/archive/sim-obs-test/lab_phase14.md:278-282` is the
original design doc explaining why `WorkflowRegistry` was built to read
`.agents/` — this was an intentional, if since-orphaned-at-the-call-site,
design decision, not an accident or drift.

## Why this matters to this plan

The plan's `.agents/` disposition audit (Workstream A item 1, and the
`retain and migrate` / `replace` / `archive/retire` classification framework
in the Current-State Inventory) currently has no basis for accounting for
this dependency. Classifying `.agents/workflows/*.md` or
`.agents/skills/*/SKILL.md` paths as `archive/retire` without also updating
or retiring `test_real_registry_contracts` in the same change would produce
a real regression: a currently-passing test starts failing.

This does not change the plan's overall direction, its readiness verdict, or
its discovery-epic scope — it is an added fact for the `.agents/`
disposition child ticket to account for when it is scoped, not a new open
question requiring plan-level rework.

## Not a request for confirmation

This is evidence, not a question — no response is required unless the
disposition ticket's scope needs adjusting to explicitly include updating or
retiring `test_real_registry_contracts` alongside whatever `.agents/`
classification decision it makes.
