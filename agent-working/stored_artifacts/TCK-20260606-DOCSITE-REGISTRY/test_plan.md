---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260606-DOCSITE-REGISTRY
artifact_type: test_plan
tags: [docsite, registry, frontmatter]
---

# Test Plan — TCK-20260606-DOCSITE-REGISTRY

## Test File

`tests/tools/test_generate_registry.py`

All tests use `tmp_path` fixtures with synthetic file trees — no real `docs/` or `tickets/done/` reads.

---

## Test Groups

### Group 1 — Doc entry generation

**1.1 Basic doc entry**
- Input: single `docs/mechanics/02_combat_laws.md` with valid frontmatter + H1 heading `# Combat Laws`
- Assert: entry has `type: doc`, `path: docs/mechanics/02_combat_laws.md`, `title: Combat Laws`, all frontmatter fields mapped

**1.2 Doc with no title heading**
- Input: frontmatter present, no H1 in body
- Assert: `title` is `""` or `None` (no crash)

**1.3 Doc missing frontmatter — CI gate**
- Input: `docs/somemod/file.md` with no frontmatter block
- Assert: `generate_registry()` exits non-zero (raises SystemExit(1) or returns error list)

**1.4 Archive subdirs skipped**
- Input: `docs/archive/old.md`, `docs/superpowers/spec.md`, `docs/specs/x.md` — all with valid frontmatter
- Assert: zero doc entries emitted for these paths

**1.5 All doc frontmatter fields mapped**
- Input: doc with `status`, `layer`, `authority`, `audience`, `tags: [a, b]`, `last_verified: 2026-01-01`
- Assert: entry fields match exactly; `tags` is a Python list `["a", "b"]`

---

### Group 2 — Ticket entry generation

**2.1 Basic ticket entry with full frontmatter**
- Input: `tickets/done/TCK-20260101-FOO-BAR.md` with full frontmatter + `## Title\nMy Title\n` + `## Tier\nstandard\n` + `## Type\nchore\n` + `## Priority\nP1\n` + `## Related Code Areas\n- \`src/foo.py\` (new)\n`
- Assert: `type: ticket`, `ticket_id: TCK-20260101-FOO-BAR`, `title: My Title`, `tier: standard`, `type_field: chore`, `priority: P1`, `related_code_areas: ["src/foo.py"]`

**2.2 Ticket with no Related Code Areas section**
- Input: ticket body with no `## Related Code Areas` heading
- Assert: `related_code_areas: []`

**2.3 Ticket missing frontmatter — warning, not failure**
- Input: ticket file with no frontmatter
- Assert: entry still emitted with `ticket_id` from filename stem, `date: ""`, warning printed to stderr; exit code remains 0

**2.4 `ticket_id` fallback from filename**
- Input: ticket with no `ticket_id` in frontmatter
- Assert: `ticket_id` equals `Path.stem` of the file

**2.5 Multiple Related Code Areas lines**
- Input: 3 backtick-quoted paths in Related Code Areas section
- Assert: `related_code_areas` list has 3 items in order

**2.6 Related Code Areas line with no backticks**
- Input: one line `- plain text no backtick`, one line `- \`good/path.py\``
- Assert: only `good/path.py` extracted; no crash on plain-text line

---

### Group 3 — Artifact join

**3.1 Artifact files joined from stored_artifacts**
- Input: ticket `TCK-20260101-FOO-BAR`, `stored_artifacts/TCK-20260101-FOO-BAR/` contains `plan.md`, `investigation.md`, `test_plan.md`
- Assert: `artifact_files` contains all three relative paths, sorted

**3.2 No artifact folder — empty list**
- Input: ticket with no corresponding folder under `stored_artifacts/`
- Assert: `artifact_files: []`

**3.3 Partial artifact folder**
- Input: `stored_artifacts/TCK-X/plan.md` only (no investigation.md)
- Assert: `artifact_files: ["stored_artifacts/TCK-X/plan.md"]`

**3.4 Non-md files in artifact folder ignored**
- Input: `stored_artifacts/TCK-X/plan.md`, `stored_artifacts/TCK-X/notes.txt`
- Assert: only `plan.md` in `artifact_files`

---

### Group 4 — Sort order

**4.1 Docs before tickets**
- Input: mix of doc and ticket entries
- Assert: all `type: doc` entries precede all `type: ticket` entries

**4.2 Docs sorted by authority then path**
- Input: P2 doc at `docs/a.md`, P0 doc at `docs/b.md`, P1 doc at `docs/c.md`
- Assert: order is `docs/b.md` (P0) → `docs/c.md` (P1) → `docs/a.md` (P2)

**4.3 Tickets sorted by date descending**
- Input: tickets with dates `2026-01-01`, `2026-06-06`, `2025-12-01`
- Assert: order is `2026-06-06` → `2026-01-01` → `2025-12-01`

**4.4 Tickets with no date sort last**
- Input: ticket with `date: ""` and ticket with `date: 2026-01-01`
- Assert: dated ticket first, undated ticket last

---

### Group 5 — Summary output

**5.1 Count by type**
- Input: 3 docs, 2 tickets
- Assert: stdout/return contains count summary: `docs: 3`, `tickets: 2`

**5.2 Count by status and layer (docs)**
- Input: 2 `status: authoritative` docs in `layer: mechanics`, 1 `status: active` doc in `layer: engine`
- Assert: summary shows breakdown

---

### Group 6 — YAML output format

**6.1 Output is valid YAML**
- Run `generate_registry()` on a synthetic tree
- Assert: `yaml.safe_load()` of the output produces a list with no exceptions

**6.2 Relative paths (not absolute)**
- Assert: all `path` and `artifact_files` values are relative (no leading `/`)

**6.3 Empty tags field**
- Input: doc frontmatter with no `tags` field
- Assert: emitted entry has `tags: []`

---

### Group 7 — Regression / edge cases

**7.1 Docs subdir without archive markers processed correctly**
- Input: `docs/engine/kernel.md` with valid frontmatter
- Assert: emitted as `type: doc` (not skipped, not misclassified as archive)

**7.2 Multiple tickets with same date sorted by path**
- Input: two tickets with same `date: 2026-06-06` at different paths
- Assert: sorted by path ascending as tiebreaker

**7.3 Large Related Code Areas section (10 items)**
- Input: 10 backtick-quoted paths
- Assert: all 10 present, no truncation

---

## Integration Smoke Test

After `tools/generate_registry.py` is written, run:
```bash
python3 tools/generate_registry.py --root .
```
Assert:
- Exit code 0 (assuming all doc frontmatter is valid after FM-LIVE/FM-TICKETS/FM-ARCHIVE complete)
- `docs/REGISTRY.yaml` created with at least 1 `type: doc` and 1 `type: ticket` entry
- File is valid YAML (`python3 -c "import yaml; yaml.safe_load(open('docs/REGISTRY.yaml'))"`)

---

## Not Tested Here

- Docusaurus consumption of `docs/REGISTRY.yaml` (Ticket 7 scope)
- Agent behavior changes from updated agent files (behavioral, tested in agent integration tests)
- `make docs-registry` Makefile target (smoke-tested manually during implementation)
