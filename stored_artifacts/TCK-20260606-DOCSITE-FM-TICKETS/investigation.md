# Investigation — TCK-20260606-DOCSITE-FM-TICKETS

Ticket: Apply frontmatter to tickets and stored artifacts; update ticket format for new tickets
Date: 2026-06-11

---

## Current Behavior

### tickets/done/ — 656 files, zero frontmatter

All 656 `.md` files in `tickets/done/` lack frontmatter entirely. Spot-checked:
- `METRICS-01.md` — begins with `# Ticket METRICS-01: ...`
- `TCK-20260503-STRATEGIC-PHASE-REALIGNMENT.md` — begins with `# TCK-20260503-...`
- `TCK-20260503-TERRAIN-WEIGHT-AUTHORITY.md` — begins with `# TCK-20260503-...`

All pre-TCK files (METRICS-01, RESTRUCTURE-01, rpg_features.md, techstacks.md, etc.) also lack frontmatter and use non-standard naming — they require special handling (no TCK date prefix to parse).

Naming patterns observed in `tickets/done/`:
- `TCK-YYYYMMDD-SHORT-SCOPE.md` — the vast majority
- `METRICS-01.md`, `RESTRUCTURE-01.md` — legacy format, no date prefix
- `rpg_features.md`, `techstacks.md`, `update_rpg_system.md` — plaintext legacy docs, no TCK format at all

### stored_artifacts/ — 467 directories, ~1240 .md files, zero frontmatter

Sampled artifact files (plan.md, investigation.md, test_plan.md) across multiple ticket folders — none have frontmatter. Example:
- `stored_artifacts/TCK-20260606-DOCSITE-SCHEMA/plan.md` begins `# Plan — TCK-20260606-DOCSITE-SCHEMA`
- `stored_artifacts/TCK-20260424-PH12-M6-EXIT-PACKAGE/plan.md` begins `# Phase 12 Milestone 6 Execution Plan`
- `stored_artifacts/infra_06/guide.md` — non-standard artifact (not plan/investigation/test_plan)

Not all `stored_artifacts/` subdirs are ticket-based (e.g. `9b6a9dff-...`, `infra_06`, `D145C3D0-MILESTONE-*`). The script must handle non-TCK folder names gracefully.

### tools/add_frontmatter_archive.py — pattern reference

Existing script at `tools/add_frontmatter_archive.py` is the proven pattern:
- `has_frontmatter(content)` — checks `content.startswith("---")`
- `infer_layer(filename)` — keyword dict match on lowercased stem
- `extract_date(filename)` — regex on `YYYY-MM-DD` prefix (archive format)
- Idempotent skip on already-frontmattered files
- Reports `modified` / `skipped` / `misc_count`

The new `add_frontmatter_tickets.py` will follow the same structure with ticket-specific logic.

### .claude/agents/ — 11 agents, 3 require updates

Full listing:
```
architecture-reviewer.md
done-checker.md
implementer.md
investigator.md
mechanics-auditor.md
parity-updater.md
planner.md
simulation-analyst.md
test-scoper.md
ticket-scoper.md
world-debugger.md
```

**ticket-scoper.md** — current ticket template section (lines 18–48) does NOT include a frontmatter block. The `## Ticket Format` section shows only the markdown heading and section headers.

**investigator.md** — `Output 1` and `Output 2` templates do not instruct the agent to prepend frontmatter to `investigation.md` or `test_plan.md`. Planner output (`plan.md`) is not covered by investigator — it is produced by `planner.md`.

**done-checker.md** — already has 12 conditions (condition 12 = agent monitoring, pre-marked PASS). The ticket AC says "add frontmatter check as condition 12" — but current condition 12 is agent monitoring. The frontmatter check must become condition 12 and monitoring must shift to condition 13, OR the frontmatter check is appended as a new condition 13. Review: the ticket AC says "condition 12 (new condition added)" — this implies inserting before existing 12, making current 12 become 13.

**investigator.md** produces investigation.md and test_plan.md but NOT plan.md. The planner agent (`planner.md`) produces plan.md. However the ticket scope only mentions updating investigator for artifact frontmatter. The plan.md frontmatter instruction must also go into `planner.md` — this is a gap the ticket scope does not explicitly list but is logically required.

### CLAUDE.md ticket template

The `## Ticket Format` section (lines 103–134) shows the required sections list inside a fenced code block. There is no frontmatter block. The schema (`docs/guidelines/frontmatter_schema.md`) defines the exact required fields for `ticket` type.

---

## Frontmatter Field Inference — tickets/done/

### Ticket frontmatter schema (from frontmatter_schema.md, type: ticket)

Required fields: `status`, `layer`, `authority`, `audience`, `ticket_id`, `phase`, `date`
Optional: `tags`

Field-by-field inference approach for `add_frontmatter_tickets.py`:

| Field | Inference rule |
|---|---|
| `ticket_id` | Filename stem (strip `.md`) — e.g. `TCK-20260606-DOCSITE-FM-TICKETS` |
| `date` | Parse `YYYYMMDD` from ticket ID prefix: `TCK-20260606-...` → `2026-06-06`. Fall back to `unknown` for non-TCK files. |
| `status` | Hardcode `historical` for all `tickets/done/` files (they are closed/archived work) |
| `layer` | Keyword dict on lowercased scope segment(s) of ticket ID. Reuse LAYER_KEYWORDS from archive script, extend with `ticket`-specific terms. |
| `authority` | Hardcode `P1` (tickets are important but not executable law) |
| `audience` | Hardcode `agent` (primary consumers are agents doing prior-work lookup) |
| `phase` | Hardcode `done` (all files under `tickets/done/`) |
| `tags` | Auto-infer from scope words in ticket ID by splitting on `-` and lowercasing; filter out the date segment and known non-semantic tokens (`TCK`, numeric segments) |

### Artifact frontmatter schema (type: artifact)

Required fields: `status`, `layer`, `authority`, `audience`, `ticket_id`, `artifact_type`
Optional: `tags`

| Field | Inference rule |
|---|---|
| `ticket_id` | Parent directory name (the folder under `stored_artifacts/`) |
| `artifact_type` | Filename stem: `plan` → `plan`, `investigation` → `investigation`, `test_plan` → `test_plan`. Only these three names are processed; other `.md` files are skipped. |
| `status` | Hardcode `historical` |
| `layer` | Infer from parent folder name (ticket_id) using same keyword dict |
| `authority` | Hardcode `P2` (supporting artifacts, not authoritative) |
| `audience` | Hardcode `agent` |
| `tags` | Same auto-infer from folder name scope words |

### Layer inference — key mappings needed

The existing archive `LAYER_KEYWORDS` dict covers: `combat`, `movement`, `economy`, `strategy`, `world`, `core`, `observability`, `performance`, `testing`, `engine`, `simulation`.

Additional mappings needed for ticket scope tokens:
- `DOCSITE`, `DOC`, `DOCS` → `guidelines`
- `SCHEMA`, `FM`, `FRONTMATTER`, `REGISTRY` → `guidelines`
- `PHASE\d+` (e.g. PHASE22, PHASE28) → `engine`
- `CONTENT` → `engine` (content pipeline is engine-layer)
- `SOCIAL`, `NARRATIVE`, `REPUTATION` → `ai`
- `CALAMIT`, `ECOLOGY` → `world`
- `INFRA`, `KERNEL`, `WORKER`, `THREAD` → `engine`

Unresolvable cases (no keyword match) → fall back to `misc`. Script reports count of `misc` cases for manual review.

---

## Agent Update Scope

### ticket-scoper.md
- Add frontmatter block as the FIRST output in the ticket template section, before `# TCK-YYYYMMDD-SHORT-SCOPE`
- Frontmatter block uses ticket schema fields with sensible defaults for a new open ticket:
  - `status: active`, `layer: <inferred>`, `authority: P1`, `audience: agent`, `ticket_id: <id>`, `phase: open`, `date: <today>`

### investigator.md
- Add instruction to Output 1 (`investigation.md`) and Output 2 (`test_plan.md`) to prepend artifact frontmatter block:
  - `status: historical`, `layer: <inferred from ticket>`, `authority: P2`, `audience: agent`, `ticket_id: <id>`, `artifact_type: investigation|test_plan`

### planner.md (gap — not in ticket scope but logically required)
- Planner produces `plan.md`. It also needs an artifact frontmatter block instruction.
- Decision: flag as a gap in investigation. The ticket scope only lists `investigator` — implementer should add planner update or create a follow-up ticket. Do not silently skip plan.md frontmatter.

### done-checker.md
- Current condition 12 = agent monitoring (pre-marked PASS).
- AC says "add frontmatter check as condition 12 (new condition added)" — this requires renumbering: insert frontmatter check as new condition 12, shift monitoring to condition 13.
- New condition 12 text: "**Frontmatter present and valid in ticket and artifacts** — run `tools/validate_frontmatter.py` against the ticket file and all `stored_artifacts/{ticket_id}/*.md` files. All must pass."

### CLAUDE.md
- In `## Ticket Format` section, add a frontmatter YAML block as the first element inside the fenced code block (before `# TCK-YYYYMMDD-SHORT-SCOPE`).

---

## tickets/backlogs/ — Out of Scope Confirmed

`tickets/backlogs/` contains epic planning docs (`epic-01-dungeon-system.md`, etc.) and one `ticket_metadata.md`. These are planning/backlog documents, not closed tickets. Confirmed out of scope — consistent with ticket's out-of-scope clause.

---

## Risks and Open Questions

1. **Non-TCK filenames in tickets/done/** (METRICS-01.md, rpg_features.md, etc.): date cannot be parsed from prefix. Script should emit `date: unknown` and flag for manual review. `ticket_id` will be set to filename stem.
2. **Non-standard stored_artifacts/ subdirs** (9b6a9dff-..., infra_06, D145C3D0-MILESTONE-*): ticket_id inference will produce non-TCK IDs. Script should warn but not fail.
3. **planner.md not in ticket scope**: `plan.md` frontmatter will be produced by `investigator` agent update per the ticket, but the actual `planner.md` agent also produces `plan.md`. This is a logical gap — recommend updating `planner.md` in the same pass and noting it in the ticket.
4. **done-checker.md condition renumbering**: currently 12 conditions; adding frontmatter as #12 pushes monitoring to #13. The tier-aware text references "11 DoD conditions" in the header — this will need updating to 12/13.
5. **validate_frontmatter.py**: The AC references running this tool to verify. It must exist and be functional before this ticket's AC can be satisfied. It is listed as a dependency (TCK-20260606-DOCSITE-SCHEMA). Verify it exists and handles the `--content-type` override flag.

---

## Anti-Drift Hazards

- Do not touch `tickets/inprogress/` files — explicitly out of scope.
- Do not touch `tickets/todos/` or `tickets/backlogs/` files.
- Do not touch `staging_artifacts/` — temporary, not indexed.
- Layer keyword dict must stay in sync with `LAYER_VALUES` in `tools/validate_frontmatter.py` — only valid enum values are allowed.
- Idempotency is critical: re-running the script on already-frontmattered files must be a no-op (check `content.startswith("---")`).
