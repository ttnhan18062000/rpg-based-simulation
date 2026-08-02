# agent-orchestration/

The provider-neutral semantic contract for the `implement-ticket` workflow: phases, per-tier
applicability, roles, skills, monitoring identity fields, and hook-event vocabulary, as the one
authoritative description of "what implement-ticket means" — independent of which provider
(Claude Code, Codex, or a future one) executes it.

This directory implements the design decisions recorded in
`docs/architecture/agent_orchestration_contract.md` (the ADR). It does not amend that document —
read it first for the *why*; this README covers the *what's here* and *how to use it*.

## Layout

| File | Governs |
|---|---|
| `contract.yaml` | Top-level manifest: contract `version`, name, description, pointers to governed sibling files. |
| `workflows/implement-ticket.yaml` | Phase list, per-tier applicability matrix, and the 10-role agent vocabulary for `implement-ticket`. |
| `roles/*.yaml` (10 files) | One file per delegated subagent role that participates in `implement-ticket`. |
| `skills.yaml` | Catalog of reusable skills (`.claude/skills/*/SKILL.md`) and their workflow/role associations. |
| `monitoring-schema.yaml` | Execution-identity field model (`execution_id`/`run_id`/`ticket_id`), consumed verbatim from `docs/ai/monitoring_writer_decision.md`. |
| `hook-events.yaml` | Normalized lifecycle hook-event vocabulary currently wired in `.claude/settings.json`. |
| `hook-surface-policy.yaml` | Per-provider available/normalized/enabled hook-event policy and the Codex activation boundary (available/normalized/enabled distinction, activation candidates, activation prerequisites). |
| `terminal-statuses.yaml` | Normalized terminal outcomes for `implement-ticket`; every value ends the current invocation. |

## Versioning scheme

Each file carries its own independent **integer generation counter** — `version` in
`contract.yaml`, `workflow_version`, `role_version` (per role file), `skills_version`,
`schema_version`, `hook_schema_version`, `hook_surface_policy_version`, `terminal_status_schema_version` — starting at `1`. Not semver: this is a single-repo
internal contract with zero external consumers today (no provider adapter yet reads it), so
semver's major/minor/patch compatibility triad would model guarantees that don't exist yet.

**Bump rule:** increment a file's own counter by exactly 1 on any breaking schema change to that
file (a field rename, a required-field addition, a structural reshape). A non-breaking addition
(a new optional field, a new role/skill entry) does not bump the counter. Each file's counter is
independent — a breaking change to `roles/*.yaml` does not force-bump `hook-events.yaml`.

`workflows/implement-ticket.yaml` may carry an optional validated `continuation_policy`. When
present, it is consumed by the Codex guidance renderer only: it keeps a healthy, already-selected
ticket invocation moving, but every declared terminal outcome ends that invocation. `DONE` and
`EPIC_SCOPED` are completion outcomes; all other terminal outcomes are stop/gate outcomes. It
does not alter the live Claude workflow, select another ticket, or authorize scope changes,
gate bypass, hooks, live/destructive actions, or provider activation. Removing the optional field
and regenerating `AGENTS.md` is the rollback path.

## Bootstrap vocabulary — one-time, not a permanent sync

`workflows/implement-ticket.yaml`'s phase and agent name lists were bootstrap-initialized once
from `tools/agent-monitoring/vocabulary.py`'s `WORKFLOW_PHASES["implement-ticket"]` /
`WORKFLOW_AGENTS["implement-ticket"]` (minus the `implement-ticket-orchestrator` pseudo-agent
label, which is not a delegated role). This is verified by a one-time bootstrap-correctness test,
`tests/agent_orchestration/test_bootstrap_vocabulary_equality.py` — value-equality, not object
identity, and explicitly **not** an ongoing single-source-of-truth guarantee.

**The direction is one-way, and will flip later, not now.** Today, while
`.claude/workflows/implement-ticket.js` remains the live production workflow,
`tools/agent-monitoring/vocabulary.py` stays the legacy, operative source of truth for phase/agent
names — this contract was generated FROM it once. Once provider adapters (Claude conformance,
Codex guidance) exist and actually consume this contract, the relationship is expected to flip:
this contract becomes the upstream semantic authority, and `vocabulary.py` (and any provider
adapter's own vocabulary) becomes generated/validated FROM the contract instead. This ticket
(`TCK-20260721-ORCHESTRATION-CONTRACT-CORE`) does **not** implement that flip — it is explicit
follow-on work for a later ticket once adapters exist. Do not build a two-way sync between
`vocabulary.py` and this contract in the meantime.

## Using the validator

```python
from pathlib import Path
from agent_orchestration.loader import load_contract

bundle = load_contract(Path("/path/to/repo/root"))
```

Raises `agent_orchestration.errors.ContractValidationError` (single flat exception type,
mirroring `tools/agent_replay/fixture_envelope.py`'s `FixtureValidationError`) naming the exact
file and field on any missing required field, malformed value, or non-mapping YAML root.

## Using the generator

```python
from pathlib import Path
from agent_orchestration.generator import generate

# Writes inside agent-orchestration/ — no flag needed.
generate(repo_root, repo_root / "agent-orchestration")

# Writes outside agent-orchestration/ — requires the explicit flag.
generate(repo_root, some_other_dir, allow_outside_contract=True)
```

Without `allow_outside_contract=True`, `generate()` refuses (raises
`agent_orchestration.errors.GeneratorWriteGuardError`) any write whose resolved target path falls
outside `agent-orchestration/` — a structural path-containment check performed before every
write, not a docstring convention.

## Upstream authorities

- `docs/architecture/agent_orchestration_contract.md` — the ADR this directory implements.
- `docs/ai/monitoring_writer_decision.md` — decides the `execution_id`/`run_id`/`ticket_id`
  field model `monitoring-schema.yaml` carries verbatim.

## Out of scope here

This directory and its tooling do not build the Claude conformance/diff tooling or any
`.codex/` provider adapter/hook code — both are owned by separate, already-scoped tickets. See
`tickets/inprogress/TCK-20260721-ORCHESTRATION-CONTRACT-CORE.md`'s Related Tickets section.
