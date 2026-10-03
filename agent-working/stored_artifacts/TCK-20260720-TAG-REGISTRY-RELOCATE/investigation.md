---
status: active
layer: ai
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20260720-TAG-REGISTRY-RELOCATE
date: 2026-07-30
tags: [tagging, frontmatter]
---

# Investigation — TCK-20260720-TAG-REGISTRY-RELOCATE

## Current Behavior (file:line refs)

- Three append-only JSONL registries live under `docs/guidelines/`: `tag_registry.jsonl`,
  `layer_registry.jsonl`, `glossary_registry.jsonl`. Each owning module hardcodes its own path:
  `tools/tag_registry.py:116` (`_REGISTRY_REL_PATH = Path("docs/guidelines/tag_registry.jsonl")`),
  `tools/layer_registry.py:60`, `tools/glossary_registry.py:68` — same constant name, same
  relative-path pattern in all three.
- A full-repo grep for the three old path strings across `tools/`, `src/`, `tests/`, `docs/`,
  `.claude/`, `CLAUDE.md` returns 47 matches. 41 are prose/comment/docstring references (no
  behavior change on move); 6 are load-bearing: the 3 `_REGISTRY_REL_PATH` constants above, plus 3
  hardcoded test fixture paths building a `tmp_path`-rooted mirror of the real path structure:
  `tests/tools/test_agent_ops_dashboard_glossary.py:27,32` (`tmp_path/"docs"/"guidelines"/...`) and
  `tests/tools/test_generate_retro.py:168`'s docstring-documented fixture-writer helper.
- `docs/parity_ledger/infrastructure.yaml` has 4 old-path mentions: 2 inside `text:` blocks
  (INFRA-279 line 5018, INFRA-3xx line 5525 — historical narrative describing what was true when
  written, left unchanged per this ticket's AC scope of "v2_evidence entries" only) and 2 inside
  `v2_evidence:` blocks (line 5038, line 5539 — these describe *current* file locations and must
  move).
- `src/api/agent_ops_dashboard/ingest.py:431` and `models.py` were checked directly — no
  `docs/guidelines/*_registry.jsonl` path string appears in either; both consume the registries
  only via the Python modules' own `load_registry()` functions, never a literal path. No change
  needed there (the ticket's own Related Code Areas over-included these defensively; confirmed via
  direct grep, not assumed).
- No `registries/` directory exists at repo root today. The only other use of the word
  `registries` anywhere is the unrelated `src/.../registries.py` Python module (confirmed via `ls`
  and grep — no name collision).
- 6 archived docs under `docs/plans/archive/agent_ops_dashboard/` reference the old paths in
  historical proposal prose. One non-archived doc, `docs/plans/tag_dedup/proposal_tag_corpus_dedup.md`
  (frontmatter `status: active`, `maturity: proposal`), also references the old path once (line 45)
  — this is NOT under `docs/plans/archive/`, so the ticket's "archive is out of scope" framing does
  not automatically cover it. Explicit decision (this investigation): update it, since it is
  `status: active` (not historical) and its own frontmatter marks it as a live, currently-relevant
  proposal doc, unlike the 6 genuinely archived files.

## Mechanics/Engine Constraints

None — this is agent/ticket-tooling infrastructure (`layer: ai`), not simulation engine or
Mechanics Bible territory. No `docs/mechanics/` or `docs/engine/` chapter applies.

## Parity Ledger Overlap (IDs + status)

- `docs/parity_ledger/infrastructure.yaml` INFRA-279 (glossary registry) and one further entry
  near line 5525/5539 (bulk phase-tag glossary seeding) both have `v2_evidence` fields citing the
  old `docs/guidelines/glossary_registry.jsonl` path. Both are `status: verified` already — this
  ticket updates their `v2_evidence` path text only, doesn't change their verified status (the
  underlying behavior isn't changing, only the file's location).
- No P0 entries are affected (checked: `python3 tools/tag_registry.py`/`layer_registry.py`/
  `glossary_registry.py` relocation is not tied to any P0-tagged parity entry per a scan of
  `infrastructure.yaml` for `priority: P0` near either registry's evidence).

## Prior Work

- `TCK-20260706-TAG-REGISTRY-DATA` created `tag_registry.jsonl`, `TCK-20260718-LAYER-REGISTRY-CONVERSION`
  created `layer_registry.jsonl`, `TCK-20260718-GLOSSARY-REGISTRY` created `glossary_registry.jsonl`
  — all three originally placed under `docs/guidelines/` as the established convention at the time.
  This ticket is the first to challenge that placement (docs/ implies documentation, not durable
  git-tracked data; `data/` is already established as ephemeral/wiped-on-cleanup, so neither
  existing convention fits).

## Risks and Open Questions

- **Byte-identical move requirement (AC #1)**: `git mv` preserves content exactly; using `mv` +
  `git add` is equally byte-identical since these are plain-text JSONL files with no OS-level
  transform risk. Either mechanism satisfies the AC; `git mv` is used below to preserve rename
  history for `git blame`/`git log --follow`.
- **`make docs-registry` no-op requirement (AC #7)**: `tools/generate_registry.py`'s walk is
  confirmed (by reading the module) to only match `**/*.md` files under `docs/`. Moving `.jsonl`
  files out of `docs/guidelines/` cannot affect its output — this is verified empirically below in
  Test Summary, not just asserted from reading the code.
- **Archive decision (AC #6)**: resolved above under Current Behavior — `docs/plans/archive/**`
  (6 files) stays untouched as historical archive; `docs/plans/tag_dedup/proposal_tag_corpus_dedup.md`
  (1 file, not archived, `status: active`) is updated alongside the other active docs. This is the
  required explicit, non-silent decision the ticket's AC demands.

## Anti-Drift Hazards

- Do not touch `docs/plans/archive/agent_ops_dashboard/*.md` — these are frozen historical records;
  updating them to a path that didn't exist when they were written would misrepresent history.
- Do not touch `infrastructure.yaml`'s `text:` blocks (only `v2_evidence:`) — `text:` narrates what
  was literally true and implemented at that entry's creation time; the file's later relocation is
  a `v2_evidence` update, not a rewrite of history.
- `tools/tag_registry.py`, `tools/layer_registry.py`, `tools/glossary_registry.py` are otherwise
  identical in shape (`_REGISTRY_REL_PATH` constant, `load_registry()`, `add_*()`) — apply the same
  one-line constant change to all three, do not refactor further (out of scope; this ticket is a
  pure relocation, not a redesign).
