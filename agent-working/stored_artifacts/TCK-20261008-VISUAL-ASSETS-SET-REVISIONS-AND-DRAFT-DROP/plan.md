---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20261008-VISUAL-ASSETS-SET-REVISIONS-AND-DRAFT-DROP
artifact_type: plan
date: 2026-10-09
tags: [architecture, testing]
---

# Design (for the owner's approval BEFORE code): set-level revisions and draft drop

## Why
Seven revisions cost the owner 14 commands (`review` + `adopt --parent` per slot) because `adopt-set` only creates NEW source assets (`setadoption.py` calls `adoption.new_source_asset`), and `draft keep` refuses an existing source id (`drafts.py`, `source_asset_exists`). Declined drafts also cannot be removed from a set (there is no drop).

## What is read today (facts)
- `adopt-set` (CLI: TTY required via `_require_terminal`, typed id via `_prompt`; no MCP tool, boundary test `GATE_LAYERS`) re-renders every source with the store's own Aseprite, refuses on any mismatch, runs the `adopt` checks (staged bytes, same-bytes-not-adopted, slot free, licence, approver), prints ONE confirmation, then `publish`es all files or none and writes one `SetAdoptionRecord` bound to the exact set bytes.
- Per-slot `adopt --parent` builds the SAME `AdoptionRecord` and `SourceRecord` through `adoption.build_entry_records`, with `revision, parent = _lineage(source, new=False, parent)` (parent must be the latest unrevoked revision).
- `adopt-set` does not need `review`: it makes its own fresh `ReviewRenderCheck`; the human's evidence is `--review-evidence` (stated by them) plus the store's re-render.

## The design
### 1. A draft declares a revision
`DraftEntry` gains an optional `parent_revision` (e.g. `r0001`). Absent = a new source asset (today's meaning; existing sets stay byte-identical, so their recorded hashes do not move). Present = "this draft is the NEXT revision of the existing source asset `source_asset_id`, whose latest unrevoked revision was `parent_revision` when the draft was kept".
`draft keep ... --revises rNNNN` sets it. With the flag keep REQUIRES the source asset to exist and `rNNNN` to be its latest unrevoked revision; without the flag the existing `source_asset_exists` refusal stays, so nothing becomes a revision silently. Keeping records no approval (as today), so an agent may run it.

### 2. `adopt-set` adopts new and revision entries in one decision
Per entry, at adoption time (nothing trusted from keep time):
- new: unchanged.
- revision: `parent_revision` must equal the source's latest unrevoked revision NOW (`parent_not_latest_unrevoked` = a stale draft, refused before anything is written); the entry's `visual_key` and `detail` must equal the slot the parent revision was adopted for (`revision_changes_slot` otherwise; see security note 3); the slot may be held by the entry's own source; records are built by the SAME `build_entry_records` with the revision number and parent that `adopt --parent` would use, so the lineage is identical.
Everything else is unchanged: store re-render match, same-bytes checks, licence CLEARED and evidence from the human, approver, `--review-evidence`.

### 3. What the owner sees before typing the id
For every slot, in set order, one line: `NEW source asset <id> r0001 for <slot>` or `REVISION of <id>: r0001 -> r0002 for <slot> (parent r0001 is the latest unrevoked)`, followed by the existing per-slot render-match line; plus a summary line `N new, M revisions, ALL or NONE`, the draft set hash and the owner's own evidence lines, exactly as today. The typed confirmation is the set id, as today.

### 4. Atomicity and records
All files of all entries and the `SetAdoptionRecord` go through one `publish`; any refusal happens before it, so nothing is written (tested with a refusal injected at the last entry). `SetAdoptedEntry` gains the same optional `parent_revision`, so the set record alone says which slots were revisions (absent for new entries: records of new-only sets are byte-identical to today's).

### 5. `draft drop <set> --slot KEY[:DETAIL] --reason TEXT`
Removes one draft from a set. Recorded in the set file: `DraftSet` gains an optional `dropped` list (visual key, detail, the dropped draft id, the reason, sorted; absent when empty, so existing sets do not change). The entry's folder is removed; the set's hash changes by design, so any earlier review of the old hash is void and `adopt-set` prints the new one. Refused: unknown slot; a set that has a `SetAdoptionRecord` ("an adopted set can never be altered": `set_adopted`); an entry whose own draft was adopted (`entry_adopted`, e.g. adopted per slot). Like `keep` it records no approval and has no MCP tool; it can only REDUCE what a human is later asked to adopt, and the removal stays visible in the set file and in git.

### 6. Unchanged human-gate properties
TTY required; typed confirmation; no agent/MCP path (boundary tests unchanged: `setadoption` and `adoption` stay gate layers the drawing server cannot import); licence and approver from the human's own arguments; the store's own render of each source must equal the draft's preview or the whole set is refused.

## Security review (to be run after code, findings recorded; planned scope)
1. An agent can keep a draft with `--revises` for an adopted source: it is only a draft; a human must adopt, and the confirmation names it REVISION.
2. Stale parent (another adoption or a revocation between keep and adopt) is refused at adoption time.
3. Re-targeting: `adopt --parent` today does not require the new revision to keep the parent's visual key and detail (`check_slot` only excludes the source's own holder). The set path will require equality (`revision_changes_slot`); I will report the per-slot gap as a finding and NOT change `adopt` here (out of scope).
4. `drop` cannot touch an adopted set or an adopted entry; it cannot add anything.
5. Mixed sets cannot adopt one slot twice (DraftSet already requires one entry per slot and unique source ids).
6. No new import path: the boundary test is extended with the new functions' modules unchanged.

## Not decided here / question for the owner
- Whether to apply `draft drop` to `icons-owner-fixes-v1` (the declined ruins and enemy-camp drafts): it would change that set's recorded hash, which the adoption guards (`ICON_FIX_DRAFT_SET_HASH`) and the review doc pin. Proposal: NOT now; the drop command lands, the existing set is left as the history of what the owner adopted slot by slot.

## ADR row D22 (proposed text)
| D22 | Set-level revisions and draft drop (`TCK-20261008-VISUAL-ASSETS-SET-REVISIONS-AND-DRAFT-DROP`): a draft entry may declare `parent_revision` (set with `draft keep --revises`), meaning the next revision of an existing source asset; `adopt-set` then adopts new and revision entries in ONE reviewed decision, all or nothing, with the lineage records identical to per-slot `adopt --parent` (parent must be the latest unrevoked revision at adoption time, the slot must not change); the confirmation lists every slot as NEW or REVISION with its parent. `draft drop <set> --slot K --reason R` removes a draft and records it in the set (`dropped`); an adopted set, or an entry already adopted, can never be altered. The human-only gate is unchanged: TTY, typed confirmation, the store's own re-render of every source, no MCP or agent path. |

## Tests planned
mixed new + revision set; stale parent refused with nothing written; revision changing slot refused; revision of a revoked-out source refused; atomic: a failure injected at the last entry leaves the catalog byte-identical; lineage identical to per-slot `adopt --parent` (same catalog state, same timestamps: equal `AdoptionRecord`/`SourceRecord` bytes); records of a new-only set byte-identical to today's; `draft keep --revises` accepted only for an existing latest unrevoked parent; drop: refused on an adopted set and on an adopted entry, recorded, hash changes, no stray files; gate tests: no TTY refused, wrong typed id refused, boundary test (drawing server cannot import); mutants for each refusal; then the security review.

## Planner review and owner answers (2026-10-09), verbatim
Planner approved the design; added: state the hash-voiding effect plainly in the ADR (done in D22 and in `store_contract.md`), and tighten per-slot `adopt --parent` (revision_changes_slot) with a test, a mutant and a D22 note. Owner, by blocking question:
1. Design with ADR D22: "Approve the design".
2. Tightening per-slot `adopt --parent`: "Approve the tightening".
3. Declined drafts in `icons-owner-fixes-v1`: "Leave them as history" (no drop applied; its hash and records stay).

## Deviations while building (disclosed)
- `DraftSet.dropped` is capped (`MAX_DROPPED_DRAFTS = 8`, reason at most 80 characters) so the widest legal set stays under `MAX_RECORD_BYTES` (127211 B, 97.1 %); a new `budgets.md` row records it.
- `adoption.revision_of` and `records.revision_slot` were added so the set path, `adopt` and `draft keep` share one lineage and one slot rule.
- `draft keep` also checks the slot and the parent at keep time (early failure); `adopt-set` and `adopt` re-check at adoption time (nothing is trusted from keep time).
- The review-sheet generator's owner commands still print per-slot commands for revisions; teaching it to print one `adopt-set` for sets with revision drafts is a follow-up (not in this ticket).

