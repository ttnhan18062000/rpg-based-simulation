---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE
artifact_type: test_plan
tags: [ai, workflows, process-improvement, hooks, skills]
---

# Test Plan — TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE

## Regression Surface

Existing tests that must keep passing after this ticket's containment action, new generator, and
fixture-capture tooling land.

**Unit / guard tests (agent-orchestration family):**
- `tests/agent_orchestration/test_validator_no_network_calls.py` — must still pass unmodified;
  this ticket does not change `tools/agent_orchestration/{loader,generator,errors}.py`, only reads
  `load_contract()` from a new package.
- `tests/agent_orchestration_claude_adapter/test_generator_containment.py` — must still pass
  unmodified; unrelated to this ticket's new Codex-side generator.
- `tests/agent_orchestration_claude_adapter/test_no_codex_scope_creep.py` —
  `test_no_codex_or_provider_adapter_scope_creep_in_this_tickets_tree` must still pass unmodified
  (this ticket's new files live outside its `_SCANNED_DIRS`/`_SCANNED_FILES`).
  `test_no_dot_codex_directory_exists_in_repo` **will need to change as part of this ticket** — see
  "New Tests Required" below; it is listed here because its *replacement/narrowed* assertion must
  keep passing, not because the current literal assertion survives untouched.
- Any other test under `tests/agent_orchestration_claude_adapter/` — must keep passing; scope
  boundary unaffected by this ticket.

**Unit tests (lab agent / workflow registry, since `.agents/` containment touches this test's
input surface):**
- `tests/unit/lab_agent/test_workflow_registry.py` — confirmed during investigation to already be
  decoupled from live `.agents/workflows/` and `.agents/skills/` (reads
  `tests/unit/lab_agent/fixtures/agents_workflows/*.md` and an empty
  `tests/unit/lab_agent/fixtures/agents_skills/` instead). Must still pass after the live
  `.agents/skills/` tree is quarantined/replaced — this is a direct regression check that the
  containment action doesn't reach a test that looks unrelated but historically depended on the
  live directory.

**Diagnostics / capability tests:**
- `tests/tools/test_codex_capability_diagnostics.py::test_codex_hooks_feature_reported_enabled` —
  must keep passing (skips cleanly if `codex` is not on `PATH`; unaffected by this ticket's own
  `.codex/` config since it only runs `codex features list`, a read-only diagnostic against the
  ambient environment, not this repo's project config).
- `tests/tools/test_post_tool_hook.py` (all four tests) — unrelated subsystem (Claude-side
  `tools/agent-monitoring/post_tool_hook.py`), included here only as a regression guard that this
  ticket's Codex-focused work does not touch shared monitoring-hook code paths.

**Replay-proof family (adjacent fixture convention, must stay isolated from this ticket's new
fixture format):**
- `tests/agent_replay/test_fixture_envelope.py`
- `tests/agent_replay/test_fixture_spec_doc.py`
- `tests/agent_replay/test_no_mutation_snapshot.py`
- `tests/agent_replay/test_runner_no_forbidden_calls.py`
- `tests/agent_replay/test_runner.py`

**Integration / arena-combat:** none applicable — this ticket makes no `src/` simulation change.

## New Tests Required

Per acceptance criteria (`tickets/inprogress/TCK-20260721-CODEX-GUIDANCE-FIXTURE-CAPTURE.md`):

1. **Legacy tree containment — Codex discovery-path absence**
   - Category: architecture guard
   - Verifies: after the containment action, no `SKILL.md` file exists anywhere Codex's
     documented discovery walk (`.agents/skills` from cwd up to repo root, per
     `codex_capability_matrix.md` §5) would find, **and** a byte-identical archived copy of all 18
     original files exists at whatever path Plan specifies (Risk #1 in investigation.md) outside
     that discovery walk.
   - Where: new file, e.g. `tests/agent_orchestration_codex_adapter/test_legacy_skills_containment.py`
     (package name TBD by Plan — mirror `tests/agent_orchestration_claude_adapter/`'s naming
     convention for the sibling generator this ticket builds).

2. **Legacy tree containment — archive byte-identity**
   - Category: unit
   - Verifies: each archived file's content is byte-identical (hash comparison) to a pre-recorded
     snapshot of the original `.agents/skills/<name>/SKILL.md` content (captured once, at
     Implement time, before the containment action runs) — proves the archive is a real
     preservation, not a lossy or partial copy.
   - Where: same file as #1, or a sibling `test_legacy_skills_archive_fidelity.py`.

3. **Generated catalog traces back to contract source fields**
   - Category: unit
   - Verifies: for every entry in the newly generated `.agents/skills/` catalog, its `id`
     matches a `skills.yaml` entry's `id`, and its frontmatter `description` matches that entry's
     `description` verbatim — proving the AC's "generated from the validated contract... not
     independently hand-curated" requirement by tracing content back to source fields, not merely
     asserting a human reviewed it. Mirrors
     `tests/agent_orchestration_claude_adapter/test_generator_containment.py::test_build_claude_adapter_representation_derives_purely_from_load_paths`'s
     technique (assert derived output fields equal specific `load_contract()` bundle fields).
   - Where: `tests/agent_orchestration_codex_adapter/test_generator_traceability.py` (or
     equivalent path chosen by Plan).

4. **Root AGENTS.md is not a copy of the stale draft and states the real pipeline phase count**
   - Category: unit
   - Verifies: (a) new root `AGENTS.md` content does not byte-match or near-duplicate
     `.agents/rules/AGENTS.md`'s content; (b) it does not contain the string `"17-phase"` /
     `"17 phase"`; (c) it does contain `"32"` in the context of the authoritative pipeline (or
     otherwise verifiably reflects `docs/engine/authoritative_pipeline.md`'s 32-phase sequence).
   - Where: `tests/agent_orchestration_codex_adapter/test_agents_md_generation.py`.

5. **Generator write-guard (structural containment)**
   - Category: unit
   - Verifies: the new Codex-adapter generator refuses to write outside its intended targets
     (`.agents/skills/`, root `AGENTS.md`, `.codex/`) without an explicit opt-in flag — mirrors
     `tests/agent_orchestration_claude_adapter/test_generator_containment.py`'s
     `test_render_claude_adapter_refuses_writes_outside_rendered_dir_without_flag` /
     `test_render_claude_adapter_never_targets_dot_claude_directory` pair, adapted to this
     generator's own allowed-target set.
   - Where: same new test package, `test_generator_write_guard.py`.

6. **Fixture-capture experiment produces a committed, schema-conformant fixture record**
   - Category: unit (validates the fixture *file*, does not re-run the live capture)
   - Verifies: whatever fixture format Plan defines for the captured real hook-payload JSON
     (distinct from `replay_fixture_spec.md`'s envelope — see investigation.md Risk/Current
     Behavior #5) parses and validates against its own schema, and the fixture is marked
     explicitly as direct-experiment grade (mirroring `codex_capability_matrix.md` §6's
     documentation-citation vs. direct-experiment distinction) rather than silently presented as
     documentation-derived.
   - Where: `tests/tools/test_codex_hook_payload_fixture.py` (or path Plan specifies) +
     a new committed fixture file under `tests/fixtures/` (exact name/path TBD by Plan).

7. **No production hook enabled — explicit `.codex/` config state check**
   - Category: architecture guard
   - Verifies: after this ticket's work, `.codex/config.toml` (or whatever file(s) Plan's
     fixture-capture experiment determines are needed) contains no hook registration wired to run
     against the live/production repo state — i.e., either no hooks are registered at all, or any
     registered hooks are provably inert (commented out, pointed at a non-existent script, or
     otherwise structurally disabled) — matching this ticket's own AC #6 literally.
   - Where: `tests/agent_orchestration_codex_adapter/test_no_production_hook_enabled.py`.

8. **`.codex/` scope-creep test resolved without leaving a repo-wide regression**
   - Category: architecture guard
   - Verifies: whichever resolution Plan picks for
     `tests/agent_orchestration_claude_adapter/test_no_codex_scope_creep.py::test_no_dot_codex_directory_exists_in_repo`
     (delete / narrow / relocate per investigation.md Risk #3), the **resulting** test suite
     contains an assertion that still meaningfully guards against unscoped Codex-adapter
     scope-creep from ticket 3/7's own delivered tree, and does not simply delete the guard with
     nothing replacing its intent.
   - Where: modification to the existing file (cross-ticket edit, must be called out in
     `plan.md`/`Files Changed` per investigation.md's Anti-Drift Hazards), plus this new assertion
     wherever Plan relocates it.

9. **Append-only diff proof for `agent-monitoring/*.jsonl` around the containment action**
   - Category: architecture guard
   - Verifies: immediately before and immediately after the containment action specifically (not
     the whole ticket's execution), `post_lines[:len(pre_lines)] == pre_lines` holds for each of
     `agent-monitoring/{runs,events,tools}.jsonl` — i.e., zero rewritten/reordered/deleted
     pre-existing lines, appends after that point are allowed. Extend or wrap
     `tools/agent-monitoring/manifest.py`'s per-file line/hash scan (currently whole-file only) with
     a prefix-hash or line-list-prefix check; do not reuse
     `tests/agent_replay/test_no_mutation_snapshot.py`'s whole-file-equality assertion as-is (see
     investigation.md Current Behavior #7 for why that stronger invariant is wrong here).
   - Where: `tests/agent_orchestration_codex_adapter/test_containment_append_only_monitoring.py`
     (or path Plan specifies); may add a small `--prefix-check` mode to `manifest.py` or a
     standalone helper — Plan decides which.

10. **Entry-criterion gate — no generation before `TCK-20260721-ORCHESTRATION-CONTRACT-CORE`**
    - Category: unit / documentation-shaped
    - Verifies: this is largely a process/sequencing AC rather than a runtime-testable one, since
      `TCK-20260721-ORCHESTRATION-CONTRACT-CORE` is already DONE by the time this ticket executes.
      The testable residue is: the new generator's `load_contract()` call must fail loudly
      (`ContractValidationError`) if any of the six `agent-orchestration/` files is missing or
      malformed, rather than silently falling back to hand-curated content — proving the
      generator structurally *cannot* proceed without the contract, not merely that it happened
      not to in this run.
    - Where: `tests/agent_orchestration_codex_adapter/test_requires_valid_contract.py`.

## Scoped Pytest Commands

```
pytest tests/agent_orchestration/ tests/agent_orchestration_claude_adapter/ tests/agent_orchestration_codex_adapter/ -v
pytest tests/agent_replay/ -v
pytest tests/tools/test_codex_capability_diagnostics.py tests/tools/test_post_tool_hook.py -v
pytest tests/unit/lab_agent/test_workflow_registry.py -v
```

(`tests/agent_orchestration_codex_adapter/` is the anticipated new package path per this plan's
"New Tests Required" section — adjust to whatever exact path Plan/Implement actually creates.)

Never: `pytest tests/`.

## Anti-Drift Test Guards

- **A test asserting `skills.yaml`'s 16-entry set is not silently expanded to include the 6
  `retain-and-migrate` legacy-only skill ids** (`clean-code`, `codebase-search`, `code-review`,
  `create-skill`, `receiving-code-review`, `requesting-code-review`) without an explicit,
  separate promotion-review ticket — catches an implementer "helpfully" carrying that unique
  content into the new Codex catalog under the mistaken impression this ticket's scope covers
  their promotion (it explicitly doesn't; see investigation.md's Anti-Drift Hazards).
- **A test asserting the new generator never writes into `docs/ai/agents_dir_disposition.md`** —
  that file is a closed decision record from a different ticket; this ticket executes its
  containment law but must not edit its classification table.
- **A test asserting no production hook wiring appears in `.codex/config.toml`** (item 7 above) —
  the single highest-consequence regression this ticket could introduce if the fixture-capture
  experiment's scratch config accidentally gets promoted into the committed one verbatim.
- **A test asserting `tests/agent_orchestration_claude_adapter/test_no_codex_scope_creep.py::test_no_codex_or_provider_adapter_scope_creep_in_this_tickets_tree`
  still passes unmodified** — catches an implementer accidentally touching ticket 3/7's scanned
  paths (`tools/agent_orchestration_claude_adapter/`, the three named `agent-orchestration/`
  files) while building this ticket's sibling generator.
- **A test asserting the archived legacy-skills copy is never itself placed somewhere Codex's
  `.agents/skills` upward-discovery walk would still find it** — catches a "quarantine" mechanism
  that accidentally archives to a still-discoverable path (e.g. a nested
  `.agents/skills/_archive/` instead of a path fully outside the `.agents/skills` tree), which
  would defeat the entire point of the containment action while appearing to satisfy a naive
  "moved the files" check.
