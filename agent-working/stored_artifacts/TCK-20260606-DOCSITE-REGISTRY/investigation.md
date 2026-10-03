---
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260606-DOCSITE-REGISTRY
artifact_type: investigation
tags: [docsite, registry, frontmatter]
---

# Investigation — TCK-20260606-DOCSITE-REGISTRY

## Current Behavior

### Frontmatter Presence Verification

**Docs (`docs/mechanics/01_entity_anatomy.md`):** Full frontmatter present and valid:
```yaml
status: authoritative
layer: mechanics
authority: P0
audience: developer
last_verified: 2026-06-06
```

**Tickets (`tickets/done/TCK-20260606-DOCSITE-SCHEMA.md`):** Full ticket frontmatter present:
```yaml
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260606-DOCSITE-SCHEMA
phase: done
date: 2026-06-06
tags: [docsite, schema]
```

**Stored artifacts (`stored_artifacts/TCK-20260606-DOCSITE-SCHEMA/investigation.md`):** Full artifact frontmatter present:
```yaml
status: historical
layer: guidelines
authority: P2
audience: agent
ticket_id: TCK-20260606-DOCSITE-SCHEMA
artifact_type: investigation
tags: [docsite, schema]
```

Conclusion: TCK-20260606-DOCSITE-SCHEMA (and its siblings FM-LIVE, FM-TICKETS, FM-ARCHIVE, DOCSITE-SCAFFOLD) have completed the frontmatter tagging work. Frontmatter is present in the sampled docs and done tickets.

---

### Registry Entry Schema

Two entry types, both defined in the ticket spec:

**Doc entry** — sourced from frontmatter of `.md` files under `docs/` (excluding archive subdirs):
```yaml
- type: doc
  path: docs/mechanics/02_combat_laws.md
  title: <from frontmatter `title` or H1 heading>
  status: <fm.status>
  layer: <fm.layer>
  authority: <fm.authority>
  audience: <fm.audience>
  tags: <fm.tags or []>
  last_verified: <fm.last_verified or null>
```

**Ticket entry** — sourced from `tickets/done/*.md` frontmatter + body section parsing:
```yaml
- type: ticket
  path: tickets/done/TCK-YYYYMMDD-SCOPE.md
  ticket_id: <fm.ticket_id or derived from filename>
  title: <parsed from ## Title section in body>
  tier: <parsed from ## Tier section>
  type: <parsed from ## Type section>
  priority: <parsed from ## Priority section>
  date: <fm.date>
  related_code_areas: [<parsed from ## Related Code Areas section>]
  artifact_files: [<files that exist in stored_artifacts/{ticket_id}/>]
  tags: <fm.tags or []>
```

**Key design decisions from ticket spec:**
- `stored_artifacts/` is NOT walked directly — artifact files are joined from the ticket's `ticket_id` at registry generation time.
- `tickets/todos/` and `tickets/inprogress/` are NOT indexed — only `done` tickets.
- Tickets without `## Related Code Areas` emit `related_code_areas: []`.

---

### Script Architecture — `tools/generate_registry.py`

The script reuses `extract_frontmatter` from `tools/validate_frontmatter.py` directly (importable module — no subprocess). The `validate_frontmatter.py` module already has:
- `extract_frontmatter(text: str) -> dict | None` — parses inline-list YAML frontmatter
- `detect_content_type(path: Path) -> str` — infers type from path
- `_FM_PATTERN` — compiled regex for frontmatter extraction

**Walk strategy:**

1. **Doc walk:** `docs/` recursively, skip subdirs `archive/`, `superpowers/`, `specs/`. Each `.md` file must have frontmatter; missing frontmatter → error, exit 1 after full scan.

2. **Ticket walk:** `tickets/done/*.md` (flat glob, not recursive). Frontmatter missing → warning printed to stderr, entry still emitted with defaults. Body sections parsed via regex for `## Title`, `## Tier`, `## Type`, `## Priority`, `## Related Code Areas`.

3. **Artifact join:** For each ticket entry, derive `ticket_id` from `fm.ticket_id` (preferred) or filename stem. Check `stored_artifacts/{ticket_id}/` with `Path.glob("*.md")`. Emit sorted list of relative paths.

**Body section parsing for tickets:**

The ticket body uses `## SectionName\n<content lines until next ##>` format. Related Code Areas lines are markdown list items: `- \`path/to/file.py\` (description)`. Extract the backtick-quoted path from each item. Regex: `` r'`([^`]+)`' `` on each non-empty line in the section.

---

### Related Code Areas Extraction

From observed done tickets, the `## Related Code Areas` section uses this format:
```
## Related Code Areas
- `tools/add_frontmatter_live.py` (new)
- `docs/**/*.md` (modified, not code changes)
- `.claude/agents/ticket-scoper.md` (update)
```

Each line is a markdown list item. The backtick-quoted token is the canonical code path. The parenthetical annotation is metadata and should be discarded. Lines that are blank or have no backtick-quoted token are skipped.

The parser should: split body on `## Related Code Areas`, take the text until the next `## ` heading, then extract all backtick-quoted tokens from that block.

---

### Sort Order

From ticket spec:
- Primary: `type` — `doc` before `ticket`
- Secondary within `doc`: `authority` ascending (`P0` → `P1` → `P2`)
- Tertiary within `doc`: `path` ascending
- Secondary within `ticket`: `date` descending (newest first)
- Tertiary within `ticket`: `path` ascending

Authority sort key: `{"P0": 0, "P1": 1, "P2": 2}`.

---

### Agent Update Scope

**`investigator.md`:** Already updated (confirmed by reading `.claude/agents/investigator.md`). It has full registry-first workflow: reads `docs/REGISTRY.yaml`, filters `type: ticket` by `related_code_areas` overlap, reads `artifact_files` directly — no `stored_artifacts/` scan. Fallback to directory scan when registry absent. **No changes needed.**

**`mechanics-auditor.md`:** Currently has no registry reference. Needs one instruction added: before auditing a layer, use the registry to identify all `type: doc` entries with matching `layer` and `authority: P0` — these are the canonical law sources to audit against. Registry lookup replaces a manual scan of `docs/mechanics/`.

**`architecture-reviewer.md`:** Currently has no registry reference. Needs one instruction added: when validating a plan, use the registry to find `type: doc` entries with `status: active` or `status: authoritative` in the relevant `layer` — these are the active architecture docs to check compliance against.

---

### CLAUDE.md Changes Needed

The Graphify Integration section (line 315) currently has 4 bullets. A 5th bullet needs to be added:

```
- If `docs/REGISTRY.yaml` exists and the question involves prior work or related docs,
  query the registry by `related_code_areas` or `layer` — do not scan raw directories.
```

This already appears as a table row in the "Always auto-invoke" proactive tools table (line 302). The Graphify Integration section should also mention it so agents reading that section have the reference inline.

---

### Scale Assessment

- `tickets/done/` has **657 files** (counted) — this is the dominant cost of registry generation.
- `stored_artifacts/` has **468 directories** — joined by ticket_id, not walked directly.
- `docs/` has many subdirectories; the script must correctly skip `archive/`, `superpowers/`, `specs/`.
- The frontmatter parser in `validate_frontmatter.py` handles inline lists `[a, b, c]` but NOT multi-line YAML lists. The `tags` field in all observed frontmatter uses inline list format — this is consistent with what the parser supports.

---

## Gaps and Open Questions

1. **Title extraction for docs:** The frontmatter schema does not include a `title` field for docs. The registry entry schema in the ticket shows `title: Combat Laws` — this must be extracted from the H1 heading in the doc body (first `# ` line after the frontmatter block). The parser should strip the leading `# `.

2. **Ticket `title` extraction:** Parsed from `## Title` section in the body. The DOCSITE-SCHEMA ticket body has `## Title\nDefine frontmatter schema...` on the next line. This pattern is consistent across observed tickets.

3. **`ticket_id` fallback:** If `fm.ticket_id` is absent (pre-schema tickets), derive from `Path.stem` (filename without `.md`). This handles backward compatibility.

4. **`date` fallback:** If `fm.date` is absent, use `""` (empty string) — sorts last under descending date order, which is correct for old tickets.

5. **Archive subdirs for docs:** The `detect_content_type` function in `validate_frontmatter.py` already identifies `docs/archive/`, `docs/superpowers/`, `docs/specs/` as `archive` type. The registry script should skip these entirely (they are not indexed).

6. **Registry commit policy:** Confirmed by ticket — `docs/REGISTRY.yaml` should be committed to git, not gitignored.

7. **`make docs-registry` placement:** Insert under the `# ── Documentation Site ───` section in Makefile, after the existing `docs-build` target (line ~140).
