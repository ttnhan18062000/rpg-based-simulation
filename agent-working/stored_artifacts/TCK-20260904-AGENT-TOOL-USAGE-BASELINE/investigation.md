---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260904-AGENT-TOOL-USAGE-BASELINE
artifact_type: investigation
tags: [agent-monitoring, ai, governance]
---

# Investigation — TCK-20260904-AGENT-TOOL-USAGE-BASELINE

## Current Behavior

**No script implementing this ticket's aggregation exists yet.** `tools/agent-monitoring/` has no
file named `agent_tool_usage_baseline.py` or similar — confirmed via direct listing, not
grep-inferred. This is genuinely new tooling, not a modification of existing behavior.

**Real current shard state (live-verified, not trusted from the ticket text):**
`agent-monitoring/data/` has **15** dated week directories (`2026-W23` through `2026-W36`) plus
`unknown-week` — one more dated week (`2026-W36`) than the ticket's own stale "14 shards" claim
implies, since a new ISO week has rolled over since the ticket was scoped. However, only **14** of
those 16 directories actually contain a `tools.jsonl` file — `2026-W23` has only `events.jsonl` and
`runs.jsonl` (no tool-call rows were recorded that week). So a glob of
`agent-monitoring/data/*/tools.jsonl` correctly resolves to 14 shard files, coincidentally matching
the ticket's stated shard *count*, but the stated row count is stale: `wc -l` across all 14
`tools.jsonl` shards on 2026-09-05 totals **191,653** rows (verified: `find agent-monitoring/data
-name tools.jsonl | xargs wc -l`), not the ticket's stated 189,871 — roughly 1,800 more rows have
accumulated since the ticket was scoped (unsurprising, since `2026-W36` — the current week — is
still being actively written to). **The implementation must glob live (`Path("agent-monitoring/
data").glob("*/tools.jsonl")`) and never hardcode a shard count or row-count expectation** — both
of the ticket's own cited numbers were already stale by the time this investigation ran, less than
24 hours after the ticket was written.

**Canonical loader to reuse, not reimplement:** `tools/agent-monitoring/validate.py:238`,
`load_data_glob(data_dir: Path, source: str) -> list`, already implements exactly this glob +
concatenate + sort-by-week-folder-name pattern (`data_dir.glob(f"*/{source}.jsonl")`), documented as
matching `record_events.py`'s own write-side glob shape. `tools/agent-monitoring/
retrieval_baseline_metrics.py` (a directly analogous prior one-off read-only baseline script) reuses
this same function rather than reimplementing a loader, and its own test suite
(`tests/tools/test_retrieval_baseline_metrics.py::test_baseline_report_reuses_load_data_pattern_not_a_fourth_loader`)
asserts this reuse explicitly. This ticket's script should do the same — a 4th independent
glob-and-parse implementation of the same shard layout would be exactly the kind of drift this
project's `load_data_glob` precedent exists to prevent.

**16 currently-registered agents** (`ls .claude/agents/*.md`, confirmed by direct listing, 2026-09-05):
`architecture-reviewer`, `concern-investigator`, `doc-updater`, `done-checker`, `implementer`,
`investigator`, `mechanics-auditor`, `parity-updater`, `planner`, `security-reviewer`,
`simulation-analyst`, `spec-document-reviewer`, `test-scoper`, `ticket-scoper`, `world-debugger`,
`world-render-reviewer`. The script must enumerate this list live (globbing `.claude/agents/*.md`
and stripping `.md`), never hardcode it — per the ticket's own AC1 wording ("not hardcoded or stale
against the current agent roster").

**Live distribution of the `agent` field across all 191,653 rows** (computed directly against the
real corpus, not sampled):

| `agent` value | rows | Registered agent? |
|---|---:|---|
| `null` | 85,554 | No — outside an active workflow run, or predates `TCK-20260719-LIVE-PHASE-AGENT-LABEL` |
| `implementer` | 23,563 | Yes |
| `done-checker` | 17,344 | Yes |
| `investigator` | 11,646 | Yes |
| `architecture-reviewer` | 10,454 | Yes |
| `planner` | 8,499 | Yes |
| `finalizer` | 7,790 | No — legitimate orchestrator pseudo-agent, not a `.claude/agents/*.md` file (see `vocabulary.py`) |
| `test-scoper` | 5,586 | Yes |
| `doc-updater` | 5,115 | Yes |
| `parity-updater` | 4,771 | Yes |
| `claude` | 4,704 | No — documented hand-orchestration literal (`TCK-20260808-AGENT-MONITORING-CLAUDE-VOCAB-REGISTRATION`) |
| `orchestrator` | 3,068 | No — see Risks below, this one is *not* accounted for in `vocabulary.py` |
| `ticket-scoper` | 3,033 | Yes |
| `create-tickets` | 241 | No — documented pseudo-agent for the `create-tickets` workflow |
| `security-reviewer` | 213 | Yes |
| `finalizer-resume` | 48 | No |
| `implement-ticket-orchestrator` | 21 | No — documented pseudo-agent |
| `test-scoper-resume` | 1 | No |
| `parity-updater-resume` | 1 | No |
| `done-checker-resume` | 1 | No |

**10 of 16** registered agents have real tool-call rows. **6 of 16 have zero rows anywhere in the
corpus**: `concern-investigator`, `mechanics-auditor`, `simulation-analyst`, `spec-document-reviewer`,
`world-debugger`, `world-render-reviewer`. Per AC1 these must still appear as explicit zero-count
rows in the output table (never silently omitted) — this is itself the single most important
finding for the downstream M3 scoping ticket: **6 of 16 agents currently have zero empirical
tool-usage evidence to scope a `tools:` frontmatter from.**

None of the 10 non-matching literal values above (`null`, `finalizer`, `claude`, `orchestrator`,
`create-tickets`, the four `-resume` suffixed values, `implement-ticket-orchestrator`) is a
`.claude/agents/*.md` filename, so per the ticket's own scope wording ("null/non-matching agent
values") all of them bucket into the single `unattributed` row, regardless of whether they are
documented legitimate pseudo-agents (`finalizer`, `claude`, `create-tickets`,
`implement-ticket-orchestrator` — all named in `tools/agent-monitoring/vocabulary.py`'s
`WORKFLOW_AGENTS`) or undocumented/anomalous values (`orchestrator`, the `-resume` suffixed
values — see Risks below). This is a deliberate simplification the ticket's own scope already
accepts: distinguishing "legitimate pseudo-agent" from "genuine drift" within the unattributed
bucket is explicitly Out of Scope (frontmatter scoping is a separate, dependent ticket).

**`input_summary` field** (`docs/agent-monitoring/schema.md` lines 403-417): confirmed real field
name, max 120 chars, per-tool shape (file path for Read/Edit/Write/MultiEdit; first 80 chars of
command for Bash — note: 80, not 120, for the Bash sub-case specifically; description/prompt for
Agent; a Python dict-repr string, not JSON, for Skill). `tool_input` (the field name the epic doc
assumes) does not exist anywhere in the schema — confirmed by direct schema read, not grep.

**No existing script aggregates tool calls by agent.** `tools/agent-monitoring/query.py` (165
lines) queries the SQLite index's `events`/`runs` tables only — it has no `tools` table query path
and cannot answer "how many Bash calls did `investigator` make." `tools/agent-monitoring/
generate_retro.py` computes `tool_call_count` per-event (not per-agent-aggregate) and has
`build_skill_usage_section`/`build_search_count_section` for narrower tool-name-specific questions,
neither of which is a general per-agent-per-tool usage table. This ticket's deliverable is
genuinely new functionality, not a duplicate of existing capability.

## Mechanics / Engine Constraints

Not applicable — this is pure agent-monitoring tooling work (`layer: ai`), not simulation
mechanics. No `docs/mechanics/` chapter or `docs/engine/` contract constrains this ticket; no
Mechanics Bible law governs the shape of a JSONL aggregation script.

## Docs Requiring Update

- `docs/agent-monitoring/README.md`: add a new section documenting the new per-agent tool-usage
  baseline audit script, matching the established convention every other one-off audit-style script
  in this same file already follows (see "Skill Usage Metric", "Done-Ticket Monitoring Coverage
  Audit", and "Security Gate Firing Check" sections — each a short paragraph naming the script,
  what it reports, and the ticket that built it). `TCK-20260805-SKILL-USAGE-METRIC` and
  `TCK-20260805-DONE-TICKET-MONITORING-COVERAGE-AUDIT` — the two closest sibling precedents, both
  new one-off `tools/agent-monitoring/*.py` audit scripts producing a report over the same JSONL
  corpus — both listed exactly this file in their own `Files Changed` section ("added '<Section
  Name>' section"). This ticket's script is the same shape of deliverable and should follow the
  same convention.

The epic plan doc `docs/plans/agent_infrastructure/ai_first_hardening_epics/
governance_capability_policy_epic.md` (path, under `docs/`) is **not** required to change as part of
this ticket, even though it is confirmed to contain the two stale assumptions the ticket's own Scope
section already flags (`## Scope` line 45: "Mine `agent-monitoring/tools.jsonl`" — the single
retired monolithic file, not the real `agent-monitoring/data/YYYY-Www/tools.jsonl` per-week shards;
and line 46: "where visible from `tool_input`" — a field that does not exist in the real schema,
which uses `input_summary` instead). The ticket's own Assumptions section frames this as something
"corrected in this ticket's own documentation before implementation" — satisfied by this
investigation.md making the real schema/glob explicit for whoever scopes M3 next — not as an
instruction to edit the epic's own planning prose. Neither sibling precedent ticket
(`TCK-20260805-SKILL-USAGE-METRIC`, `TCK-20260805-DONE-TICKET-MONITORING-COVERAGE-AUDIT`) edited its
own parent epic/idea doc as part of building its audit tool, and this ticket's own Scope/Out-of-Scope
sections list no such edit. Recommended as a follow-up for whoever next touches that epic doc (e.g.
at M3 scoping time), not mandated here.

The `docs/agent-monitoring/schema.md` doc (path: `docs/agent-monitoring/schema.md`, under `docs/`)
is not required to change for this ticket: it already correctly documents the real shard glob
pattern, the `input_summary` field (including its 120-char cap), and the `agent` field's
nullability rules — this ticket's script reads against that existing, accurate schema and does not
modify it, add a field, or change a write path.

## Parity Ledger Overlap

None. This ticket touches no `src/` files (pure `tools/`-directory read-only script over existing
`agent-monitoring/data/` JSONL). Both directly analogous sibling tickets
(`TCK-20260805-SKILL-USAGE-METRIC`, `TCK-20260805-DONE-TICKET-MONITORING-COVERAGE-AUDIT`) recorded
"No `src/` files touched... no parity ledger entry needed" for the same reason. No
`docs/parity_ledger/*.yaml` entry currently tracks agent-monitoring tool-usage aggregation (the
`infrastructure.yaml` entries mentioning `tools.jsonl` — e.g. those touching `INFRA-289`
through `INFRA-291`'s neighborhood — all concern the *write path*/schema shape of `tools.jsonl`
itself, not a read-only consumer script; none needs updating by this ticket).

## Prior Work

- `stored_artifacts/TCK-20260721-BASELINE-MONITORING-MANIFEST/` — prior read-only manifest/baseline
  work over agent-monitoring data; confirms the "genuinely new tooling, no prior script exists"
  pattern this investigation also found for this ticket.
- `stored_artifacts/TCK-20260804-RETRIEVAL-RAW-INVESTIGATION-METRIC/` — another prior read-only
  metric built the same way (derive from existing JSONL, disclose every proxy/derivation inline,
  prove zero mutation with a real-corpus test).
- `tools/agent-monitoring/retrieval_baseline_metrics.py` + `tests/tools/
  test_retrieval_baseline_metrics.py` (`TCK-20260728-RETRIEVAL-BASELINE-METRICS`) — the closest
  direct precedent for this ticket's shape of deliverable: a one-off, read-only JSON-report script
  over `agent-monitoring/data/*/{runs,events,tools}.jsonl`, reusing `load_data_glob` from
  `validate.py`, with a real-corpus zero-mutation test using `git status --porcelain --
  agent-monitoring/` before/after (`_porcelain_snapshot()`, `tests/tools/
  test_retrieval_baseline_metrics.py:374-395`). This is the exact mechanism to reuse for this
  ticket's AC4 (read-only guard).
- `tools/agent-monitoring/skill_usage_metric.py` (`TCK-20260805-SKILL-USAGE-METRIC`) — precedent for
  extracting a name from `input_summary`'s dict-repr-string shape via regex (relevant if any
  `Skill`-tool rows need surfacing as a representative example for an agent that uses `Skill`).
- `tools/agent-monitoring/done_ticket_monitoring_coverage.py` (`TCK-20260805-DONE-TICKET-MONITORING-COVERAGE-AUDIT`)
  — precedent for a read-only audit tool that reports `covered`/`missing` style buckets (structurally
  analogous to this ticket's "16 agents + unattributed" bucket design), and for adding a
  `docs/agent-monitoring/README.md` section documenting a new one-off script.
- `tools/agent-monitoring/vocabulary.py` — single source of truth for which non-`.claude/agents/`
  literal values (`finalizer`, `claude`, `create-tickets`, `implement-ticket-orchestrator`, etc.) are
  documented, legitimate orchestrator pseudo-agents rather than drift. Useful context for the
  `unattributed` bucket's composition, though this ticket's scope does not require distinguishing
  documented-legitimate from undocumented-anomalous within that bucket.

## Risks and Open Questions

- **6 of 16 registered agents have zero real historical tool-call rows** (`concern-investigator`,
  `mechanics-auditor`, `simulation-analyst`, `spec-document-reviewer`, `world-debugger`,
  `world-render-reviewer`). This is not a bug in this ticket's script — it is a genuine gap in the
  evidence M3 will need. Flag loudly in the output table (explicit zero-count row per AC1); do not
  let the downstream M3 ticket discover this gap by surprise. Whether M3 falls back to a different
  evidence source (e.g. static read of each agent's own `.claude/agents/*.md` prompt) for these 6 is
  a decision for that ticket, not this one — flagged, not resolved here.
- **The bare literal `orchestrator` (3,068 rows, `agent-monitoring/data/2026-W33/tools.jsonl`) has no
  current code path producing it.** Direct grep of every `.claude/workflows/*.js` file's
  `writeSidecar(...)` call sites (`implement-ticket.js`) finds only `'investigator'`, `'planner'`,
  `'architecture-reviewer'`, `'implementer'`, `'doc-updater'`, `'test-scoper'`, `'parity-updater'`,
  `'security-reviewer'`, `'done-checker'`, `'finalizer'` as literal agent arguments — never
  `'orchestrator'`. It is also absent from `vocabulary.py`'s `WORKFLOW_AGENTS`/
  `WORKFLOW_AGENT_PREFIXES` (unlike `finalizer`, `claude`, `create-tickets`,
  `implement-ticket-orchestrator`, all of which are explicitly documented there as legitimate). This
  ticket's scope correctly buckets it into `unattributed` regardless of root cause, so it does not
  block this ticket — but since `2026-W33` is a recent week (not ancient legacy data), this may be a
  genuine, currently-live vocabulary-drift source that `vocabulary.py`'s drift-report doesn't
  currently catch (that module only warns on `phase`/`agent` values recorded in `events.jsonl`
  through `record_events.py`'s own warn-only check — it does not currently validate `tools.jsonl`'s
  `agent` field the same way). Flagged as a possible follow-up for whoever owns `vocabulary.py`, not
  resolved here.
- **Ambiguity in AC3's granularity**: "Every tool-name entry in the output table includes at least
  one real representative example" could mean (a) one example per (agent, tool-name) pair with a
  nonzero count, or (b) one example per distinct tool name globally, regardless of which agent(s)
  used it. The ticket text does not disambiguate. Recommend the planner resolve this explicitly in
  `plan.md` before implementation — (a) is the stricter, more useful reading (it directly serves
  M3's "which tools does *this* agent actually use, with what real inputs" question) and is the
  reading this investigation assumes going forward, but it is a real open question, not an assumed
  answer.
- **`unknown-week` fallback shard**: contains exactly 1 `tools.jsonl` row (per
  `docs/agent-monitoring/schema.md`'s Known Limitations section, this is the single confirmed
  pre-migration row with no parseable `ts` field). The glob `agent-monitoring/data/*/tools.jsonl`
  naturally includes this shard — confirmed correct behavior, not an edge case to special-case out,
  since the ticket's own sanity-check AC (wc -l across all matched shards) should include it too.

## Anti-Drift Hazards

- **Do not hardcode the 16-agent list, the 14-shard count, or the 191,653-row total anywhere in
  the script.** All three must be derived live at run time (glob `.claude/agents/*.md`; glob
  `agent-monitoring/data/*/tools.jsonl`; sum row counts) — this investigation's own numbers will
  already be stale by the time this ticket is implemented, exactly as the ticket's own numbers were
  stale by the time this investigation ran less than a day later.
- **Do not reimplement the multi-week shard glob.** Reuse `tools/agent-monitoring/validate.py`'s
  `load_data_glob(data_dir, source)` — a 4th independent parser of the same shard layout is exactly
  the kind of drift `retrieval_baseline_metrics.py`'s own test suite was built to catch
  (`test_baseline_report_reuses_load_data_pattern_not_a_fourth_loader`).
- **Do not silently drop or merge the 6 zero-count agents into the unattributed bucket** — they are
  registered agents with zero rows, not non-matching values; AC1 requires them as explicit
  zero-count rows among the 16, structurally distinct from `unattributed`.
- **Do not attempt to derive a finer-grained "Bash command class" than `input_summary`'s 120-char
  (or 80-char, for the Bash sub-case) truncation actually supports** — this is explicitly Out of
  Scope; representative examples must be labeled as truncated/summarized, never presented as a full
  reconstruction of the original command.
- **Do not touch `.claude/agents/*.md` `tools:` frontmatter, agent-monitoring write paths, schema, or
  shard migration tooling** — all explicitly Out of Scope; this ticket is read-only aggregation
  only, gating a separate future ticket.
- **Do not let the read-only guarantee (AC4) become a token check that only inspects the target
  file's own mtime or size** — reuse the `git status --porcelain -- agent-monitoring/` +
  pre/post-diff pattern from `test_retrieval_baseline_metrics.py`, which actually detects byte-level
  content changes via git's own tracked-file diffing, not a weaker proxy.
