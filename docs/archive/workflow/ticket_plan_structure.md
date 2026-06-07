# General implementation plan format for AI agents

Use this structure:

```text
Implementation Plan
→ Phase
   → Tasks
      → Technical details
      → Tests
      → Acceptance checklist
      → Anti-drift notes
```

The key goal is: **AI agent should know exactly what to change, what not to change, how to test, and how to prove completion.**

---

# 1. Top-level document structure

```markdown
# Implementation Plan: <Feature / Migration / Refactor Name>

## 1. Goal

## 2. Scope

## 3. Non-goals

## 4. Source of truth

## 5. Current state summary

## 6. Target architecture / target behavior

## 7. Implementation phases

## 8. Global test strategy

## 9. Anti-drift contract

## 10. Final definition of done
```

---

# 2. Top-level sections

## 1. Goal

Describe the real purpose, not just the code change.

Example:

```text
Move world module authoring from manually injected test data to real catalog-backed executable content.
```

Bad:

```text
Update module code.
```

---

## 2. Scope

Say exactly what this plan covers.

Example:

```text
This plan covers:
- module loading
- module normalization
- module reference validation
- module assembly
- tests using real YAML files
```

---

## 3. Non-goals

This is very important for AI agents.

Example:

```text
This plan does not cover:
- rewriting combat logic
- changing EntityState structure
- deleting legacy fallback
- adding new gameplay content
- changing observability/reporting
```

This prevents the agent from “helpfully” doing too much.

---

## 4. Source of truth

State which files/folders are authoritative.

Example:

```text
Source of truth:
- data/content/world_modules
- data/content/world_compositions
- src/worldbuilding/*
- tests/unit/worldassembly/*
```

Also state what is **not** source truth:

```text
Not source of truth:
- manually injected test modules
- old data/world_modules path except legacy tests
- YAML comments such as # STATE: ...
```

---

## 5. Current state summary

Short description of what exists now.

Example:

```text
Current implementation has WorldModuleRepository and WorldModuleAuthoringNormalizer.
However, v2 fields are partially normalized and dict counts can be lost.
Tests still rely on manually injected modules, so real YAML executable path is not proven.
```

---

## 6. Target behavior

Describe what should be true after the work.

Example:

```text
After this implementation, real YAML files under data/content/world_modules must load, validate, normalize, preserve counts, resolve references, and assemble into WorldSpec / CompileContext.
```

---

# 3. Phase structure

Each phase should use this format:

```markdown
# Phase <number> — <phase name>

## Phase goal

## Why this phase exists

## Dependencies

## Tasks

## Phase-level acceptance checklist

## Phase-level anti-drift notes
```

Example:

```markdown
# Phase 22 — Module normalization correction

## Phase goal

Fix v2 module normalization so real authoring data is preserved.

## Why this phase exists

The current normalizer loses counts when dict fields are converted with list(...).

## Dependencies

- ContentFamilySpec exists
- WorldModuleSpec exists
- Current worldassembly tests pass

## Tasks

- Task 22.1 — Fix resource/building/service normalization
- Task 22.2 — Add typed NormalizedWorldModule
- Task 22.3 — Add real module normalization tests

## Phase-level acceptance checklist

- [ ] Real module files normalize without count loss.
- [ ] Existing v1 tests still pass.
- [ ] Unknown v2 fields fail clearly.

## Phase-level anti-drift notes

- Do not rewrite world compiler.
- Do not add new gameplay content.
- Do not rely on manual injection as proof.
```

---

# 4. Task structure

Each task should be ticket-ready.

Use this exact structure:

```markdown
## Task <phase.task> — <task name>

### Objective

### Problem / current behavior

### Expected behavior

### Technical direction

### Affected components

### Test plan

### Acceptance checklist

### Anti-drift notes

### Output evidence
```

---

# 5. Task template

```markdown
## Task 22.1 — Preserve v2 module contribution counts

### Objective

Fix module normalization so dict-based contribution fields preserve counts.

### Problem / current behavior

The normalizer converts dict fields using list(...), so this:

resources:
wood_node: 2

can become:

["wood_node"]

This loses authoring meaning.

### Expected behavior

The same input must normalize to:

resource_refs:
wood_node: 2

List shorthand should normalize to count 1.

### Technical direction

- Replace list-based v2 normalized fields with dict[str, int].
- Add helper normalize_count_map(value).
- Support both list and dict authoring forms.
- Reject negative counts.
- Reject zero counts unless explicitly allowed.

### Affected components

- WorldModuleAuthoringNormalizer
- NormalizedWorldModule
- WorldAssemblyResolver
- ContentReferenceGraph
- tests/unit/worldmodules/\*
- tests/integration/worldassembly/\*

### Test plan

Add or update:

- test_list_resources_normalize_to_count_one
- test_dict_resources_preserve_counts
- test_dict_buildings_preserve_counts
- test_dict_services_preserve_counts
- test_negative_count_fails
- test_real_world_module_preserves_counts

### Acceptance checklist

- [ ] Dict resource counts are preserved.
- [ ] Dict building counts are preserved.
- [ ] Dict service counts are preserved.
- [ ] List shorthand becomes count 1.
- [ ] Invalid counts fail clearly.
- [ ] Existing v1 module tests still pass.
- [ ] Real module YAML test passes.

### Anti-drift notes

- Do not solve by changing YAML only.
- Do not manually inject module objects as the only proof.
- Do not make WorldCompiler parse raw YAML.
- Do not add behavior scripts to modules.

### Output evidence

- Passing unit tests
- Passing real YAML integration test
- Short note showing before/after normalized output
```

---

# 6. Acceptance checklist style

Acceptance criteria should be checklist-based and testable.

Good:

```text
- [ ] Real data/content/world_modules/frontier_village_core.yaml loads successfully.
- [ ] Normalizer preserves resources.wood_node = 2.
- [ ] Unknown module field fails with clear error.
- [ ] Existing v1 module test still passes.
```

Bad:

```text
- [ ] Module system is improved.
- [ ] Code is cleaner.
- [ ] Data is better.
```

---

# 7. Anti-drift notes

Every task should include anti-drift notes.

Typical rules:

```text
- Do not rewrite unrelated systems.
- Do not change public behavior unless this task says so.
- Do not delete legacy fallback unless this phase explicitly allows it.
- Do not bypass repository/resolver layers.
- Do not add new active data without consumer path.
- Do not make tests pass by weakening validation.
- Do not manually inject objects as the only proof.
- Do not silently fallback to old paths.
```

This is one of the most important sections for AI agents.

---

# 8. Test plan format

Each task should say which tests to:

```text
add
update
preserve unchanged
not duplicate
```

Example:

```markdown
### Test plan

Add:

- tests/unit/worldmodules/test_normalizer.py::test_dict_resources_preserve_counts

Update:

- tests/unit/worldassembly/test_assembly.py to use data/content path

Preserve:

- existing v1 module tests
- existing provenance determinism tests

Do not duplicate:

- basic catalog loading tests
- basic world assembly smoke tests
```

---

# 9. Phase-level table

At the top of the implementation plan, include a summary table.

| Phase | Goal                        | Main output                   | Main tests                     | Risk     |
| ----- | --------------------------- | ----------------------------- | ------------------------------ | -------- |
| 21    | Unify content paths         | Canonical content path config | content path tests             | High     |
| 22    | Fix module normalization    | Typed normalized module       | normalizer + real module tests | Critical |
| 23    | Strengthen graph validation | Typed reference graph edges   | graph tests                    | High     |
| 24    | Resolver proof              | Resolver output tests         | resolver tests                 | Medium   |

This helps the AI agent know priority and dependencies.

---

# 10. Global anti-drift contract

Put this near the top of the plan.

```markdown
# Global anti-drift contract

The implementer must preserve:

- Existing regression tests unless the task explicitly says to update them.
- Legacy compatibility paths unless the phase explicitly retires them.
- EntityState structure unless the phase explicitly changes it.
- YAML comments as human planning notes only.

The implementer must not:

- Parse YAML comments for engine behavior.
- Treat manually injected test objects as executable source proof.
- Make WorldCompiler load catalog files directly.
- Put provenance into EntityState.
- Add new active content without consumer path.
- Replace a failing strict validation with silent fallback.
- Add broad rewrites outside the task scope.
```

---

# 11. Definition of done

Use this for the whole plan:

```text
A phase is done only when:
- target code is implemented
- related tests are added/updated
- existing relevant tests still pass
- no unrelated system was changed
- acceptance checklist is fully satisfied
- output evidence is attached or described
```

For data/runtime work:

```text
A content pipeline task is done only when real content flows through:

file
→ canonical repository path
→ schema
→ validator
→ normalizer/resolver
→ assembly/registry/runtime consumer
→ test evidence
```

---

# 12. Best compact format

For future implementation plans, I recommend this structure:

```markdown
# Implementation Plan: <name>

## Goal

## Scope

## Non-goals

## Source of truth

## Global anti-drift contract

## Phase summary table

# Phase 1 — <name>

## Phase goal

## Dependencies

## Tasks

### Task 1.1 — <name>

#### Objective

#### Problem / current behavior

#### Expected behavior

#### Technical direction

#### Affected components

#### Test plan

#### Acceptance checklist

#### Anti-drift notes

#### Output evidence

### Task 1.2 — <name>

...

## Phase-level acceptance checklist

# Phase 2 — <name>

...

## Final definition of done
```

---

# 13. My strongest recommendation

For AI-agent implementation, every task must answer these 5 questions:

```text
1. What exactly is wrong or missing?
2. What exact behavior should exist after the task?
3. Which files/components are allowed to change?
4. Which tests prove the task is complete?
5. What must the agent not change?
```

That keeps the agent from drifting or implementing a “similar but wrong” solution.
