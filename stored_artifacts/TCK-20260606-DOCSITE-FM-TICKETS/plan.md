# Plan — TCK-20260606-DOCSITE-FM-TICKETS

Ticket: Apply frontmatter to tickets and stored artifacts; update ticket format for new tickets
Date: 2026-06-11

---

## Overview

This ticket has two distinct work streams:

1. **Backfill**: Apply YAML frontmatter to all existing `tickets/done/` and `stored_artifacts/` markdown files via a new idempotent script.
2. **Forward-looking**: Update the ticket format template (CLAUDE.md) and three agent files so all future tickets and artifacts are born with frontmatter.

Dependencies satisfied: `tools/validate_frontmatter.py` exists (from TCK-20260606-DOCSITE-SCHEMA).

---

## Implementation Steps

### Step 1 — Write `tools/add_frontmatter_tickets.py`

Model on `tools/add_frontmatter_archive.py`. Key differences:

**Layer keyword dict** — reuse and extend `LAYER_KEYWORDS`:
```python
LAYER_KEYWORDS = {
    "combat": ["combat", "battle", "fight", "weapon", "durability", "damage"],
    "movement": ["movement", "pathfind", "navigation", "motion", "travel"],
    "economy": ["resource", "economy", "economic", "crafting", "harvest", "trade", "market", "item", "gold", "cost"],
    "strategy": ["strategy", "strat", "cognition", "cognitive", "goal", "planning", "decision", "intel", "attention"],
    "world": ["world", "region", "ecology", "ecosystem", "biome", "terrain", "zone", "map", "topology", "climate", "calamit"],
    "core": ["entity", "aspect", "attribute", "stat", "health", "class", "character"],
    "observability": ["observ", "monitor", "metric", "log", "telemetry", "trace", "debug", "profil"],
    "performance": ["performance", "perf", "optimiz", "latency", "throughput", "benchmark", "speed"],
    "testing": ["test", "coverage", "fixture", "mock", "assert"],
    "engine": ["engine", "kernel", "pipeline", "phase", "tick", "loop", "dispatch", "scheduler", "governance", "phase2", "phase3", "infra", "worker", "thread", "content"],
    "simulation": ["simulation", "sim", "run", "replay", "determinism"],
    "guidelines": ["docsite", "doc", "schema", "frontmatter", "registry", "fm"],
    "ai": ["social", "narrative", "reputation", "faction", "npc", "ai"],
    "combat": ["combat", "battle", "fight", "weapon", "durability", "damage"],
}
```

**`extract_date_from_ticket_id(stem)`** — parse `TCK-YYYYMMDD-*` pattern:
```python
def extract_date_from_ticket_id(stem: str) -> str:
    m = re.match(r"TCK-(\d{4})(\d{2})(\d{2})-", stem)
    return f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else "unknown"
```

**`extract_ticket_id(stem)`** — return stem as-is (filename without `.md`).

**Ticket frontmatter builder** (`build_ticket_frontmatter(stem)`):
```yaml
---
status: historical
layer: <inferred>
authority: P1
audience: agent
ticket_id: <stem>
phase: done
date: <parsed or unknown>
tags: [<auto-inferred scope words>]
---
```

**Tag inference** — split ticket ID on `-`, drop `TCK`, drop the 8-digit date segment, lowercase remaining tokens, filter tokens shorter than 3 chars. Example: `TCK-20260606-DOCSITE-FM-TICKETS` → `["docsite", "fm", "tickets"]`.

**Artifact frontmatter builder** (`build_artifact_frontmatter(ticket_id, artifact_type, stem)`):
```yaml
---
status: historical
layer: <inferred from ticket_id>
authority: P2
audience: agent
ticket_id: <ticket_id>
artifact_type: <investigation|plan|test_plan>
tags: [<inferred from ticket_id>]
---
```

**Target directories and logic**:
```
TICKET_DIR = Path("tickets/done")
ARTIFACT_DIR = Path("stored_artifacts")
ARTIFACT_NAMES = {"investigation", "plan", "test_plan"}
```

Walk `TICKET_DIR` — all `.md` files → apply ticket frontmatter.
Walk `ARTIFACT_DIR` subdirs — only files whose stem is in `ARTIFACT_NAMES` → apply artifact frontmatter.
All other `.md` files in `stored_artifacts/` (e.g. `guide.md`, `implementation_plan.md`) → skip.

**Idempotency**: skip any file where `content.startswith("---")`.

**Output summary**:
```
Done: {n} tickets modified, {n} tickets skipped
Done: {n} artifacts modified, {n} artifacts skipped
Tickets with layer=misc: {n}
Artifacts with layer=misc: {n}
```

**Script must be run from repo root** (uses relative paths, consistent with `add_frontmatter_archive.py` pattern).

---

### Step 2 — Update `CLAUDE.md` Ticket Format section

In the `## Ticket Format` section, update the fenced code block to prepend a frontmatter block before the `# TCK-YYYYMMDD-SHORT-SCOPE` heading:

```
# TCK-YYYYMMDD-SHORT-SCOPE     ← becomes the second element

New first element:
---
status: active
layer: <engine|mechanics|...>
authority: P1
audience: agent
ticket_id: TCK-YYYYMMDD-SHORT-SCOPE
phase: open
date: YYYY-MM-DD
tags: []
---
```

Add a note under the code block: "Frontmatter block is required as the first element. Fill `layer` and `tags` based on scope; leave `tags: []` if uncertain."

---

### Step 3 — Update `.claude/agents/ticket-scoper.md`

In the `## Ticket Format` section, prepend the frontmatter block to the template before `# TCK-YYYYMMDD-SHORT-SCOPE`:

```markdown
Produce a file with this exact structure (frontmatter first, then markdown body):

```yaml
---
status: active
layer: <infer from scope — see LAYER_VALUES in tools/validate_frontmatter.py>
authority: P1
audience: agent
ticket_id: TCK-YYYYMMDD-SHORT-SCOPE
phase: open
date: YYYY-MM-DD    ← today's date
tags: [<scope words from ticket ID, lowercase>]
---
```

Then the markdown body:
```
# TCK-YYYYMMDD-SHORT-SCOPE
...
```
```

Instruct the agent: "If layer cannot be confidently inferred, use `misc` and note it in Assumptions / Open Questions."

---

### Step 4 — Update `.claude/agents/investigator.md`

In `## Output 1` and `## Output 2` sections, add a frontmatter preamble instruction:

> "Each output file must begin with a YAML frontmatter block before the `# Investigation —` or `# Test Plan —` heading:
>
> ```yaml
> ---
> status: historical
> layer: <same layer as the ticket>
> authority: P2
> audience: agent
> ticket_id: <ticket_id>
> artifact_type: investigation   # or test_plan
> tags: [<from ticket ID scope words>]
> ---
> ```"

**Gap note**: `plan.md` is produced by the planner agent (`planner.md`), not investigator. The same frontmatter block instruction (with `artifact_type: plan`) must also be added to `.claude/agents/planner.md`. This is not listed in the ticket scope but is logically required for completeness. Add the update to `planner.md` and document it under Implementation Notes in the ticket. If blocked, create a follow-up ticket.

---

### Step 5 — Update `.claude/agents/done-checker.md`

The current 12 conditions end with condition 12 = agent monitoring (pre-marked PASS). Insert a new condition 12 for frontmatter, and renumber the agent monitoring condition to 13.

**New condition 12**:
```
12. **Frontmatter present and valid in ticket and artifacts**
    - Run `python3 tools/validate_frontmatter.py tickets/inprogress/{ticket_id}.md` — must exit 0.
    - Run `python3 tools/validate_frontmatter.py stored_artifacts/{ticket_id}/` — must exit 0.
    - N/A for hotfix if no staging artifacts exist.
```

**Updated condition 13** (was 12):
```
13. **Agent monitoring records** _(pre-marked PASS — written by workflow after READY_TO_CLOSE)_
    - Mark PASS with note "will be written by workflow writeMonitoring after READY_TO_CLOSE".
    - Do not try to verify it exists yet.
```

**Update header tier-aware text**: change "all 11 conditions" to "all 13 conditions" and update standard tier to reference 13. Update "11 DoD conditions" → "13 DoD conditions" in the preamble. Verify the `## Tier-Aware Checking` section accurately reflects the new numbering.

---

### Step 6 — Write tests in `tests/tools/test_add_frontmatter_tickets.py`

Implement all 10 unit/integration tests listed in `test_plan.md`. Use `tmp_path` pytest fixture to create isolated file trees — do not touch real `tickets/done/` or `stored_artifacts/` in tests.

---

### Step 7 — Run the backfill script

```bash
python3 tools/add_frontmatter_tickets.py
```

Review output, especially `misc` counts. Manually review a sample of `layer=misc` files and correct if obvious layer is apparent (can be done inline or deferred to a follow-up).

---

### Step 8 — Validate

```bash
python3 tools/validate_frontmatter.py tickets/done/
python3 tools/validate_frontmatter.py stored_artifacts/
```

Both must exit 0. Fix any validation failures before closing.

---

### Step 9 — Run tests

```bash
pytest tests/tools/test_add_frontmatter_tickets.py -v
pytest tests/tools/ -v
```

All must pass.

---

## File Change Summary

| File | Action |
|---|---|
| `tools/add_frontmatter_tickets.py` | NEW |
| `tests/tools/test_add_frontmatter_tickets.py` | NEW |
| `CLAUDE.md` | UPDATE — add frontmatter block to ticket template |
| `.claude/agents/ticket-scoper.md` | UPDATE — add frontmatter block to ticket output template |
| `.claude/agents/investigator.md` | UPDATE — add frontmatter instruction to Output 1 and Output 2 |
| `.claude/agents/planner.md` | UPDATE — add frontmatter instruction to plan.md output (gap from scope, include in same pass) |
| `.claude/agents/done-checker.md` | UPDATE — insert condition 12 (frontmatter), renumber monitoring to 13 |

---

## Execution Order

1. Write `tools/add_frontmatter_tickets.py` (Step 1)
2. Write `tests/tools/test_add_frontmatter_tickets.py` (Step 6) — run before backfill to validate logic
3. Update CLAUDE.md (Step 2)
4. Update ticket-scoper.md (Step 3)
5. Update investigator.md + planner.md (Step 4)
6. Update done-checker.md (Step 5)
7. Run backfill script (Step 7)
8. Validate (Step 8)
9. Run full test suite (Step 9)

---

## Risks and Mitigations

| Risk | Mitigation |
|---|---|
| 656 tickets × backfill = many file writes | Script is idempotent; dry-run option can be added (`--dry-run` flag) |
| Non-TCK filenames produce `date: unknown` | Script warns, does not fail; flag count reported for manual review |
| layer=misc hits may be significant | Script reports count; acceptable to leave misc for backfill; validator still passes |
| done-checker renumbering breaks any existing scripted references to condition numbers | Condition numbers are prose labels, not machine IDs — safe to renumber |
| planner.md not in stated scope | Including in same pass is lower-risk than leaving plan.md without frontmatter; documented in ticket |
