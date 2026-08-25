---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260821-DOCS-BUILD-LASTUPDATE-METADATA-OVERHEAD
artifact_type: investigation
tags: [documentation, performance]
---

# Investigation — TCK-20260821-DOCS-BUILD-LASTUPDATE-METADATA-OVERHEAD

## Addendum — Scope Expanded 2026-08-24 (repo-owner decision, post-Investigate)

This investigation was originally scoped narrower (disable `showLastUpdateTime`/
`showLastUpdateAuthor` on 3 of 4 plugins only). After this investigation completed and its findings
(below — see "Risks and Open Questions" #1, and the search-local `docsRouteBasePath` flag) were
reported, the repo owner made two decisions directly informed by those findings:

1. **Drop the `tickets`, `artifacts`, `agent-monitoring` plugin instances entirely**, not just their
   metadata setting — this was previously flagged in "Anti-Drift Hazards" as "adjacent scope creep
   ... should be a new ticket, not folded into this one," but the repo owner explicitly chose to
   fold it into this still-unimplemented ticket rather than spin up a duplicate, since it addresses
   exactly the dominant-cost-driver uncertainty this investigation raised (route generation +
   search-index cost across those routes, not just their `git log` metadata calls).
2. **Trim `docs/`'s own `exclude` list** to additionally drop `archive/**` (448 files), `plans/**`
   (86 files), `audits/**` (29 files) — the content-publishing-policy question this investigation's
   "Anti-Drift Hazards" section explicitly deferred ("the ticket's own Assumptions section
   explicitly flags this as a repo-owner content-publishing decision ... Investigate agrees this is
   correctly out of scope") has now been decided by that repo owner.

The ticket itself (`tickets/inprogress/TCK-20260821-DOCS-BUILD-LASTUPDATE-METADATA-OVERHEAD.md`) has
been updated to reflect this expanded scope — Title, Request Summary, Scope, Out of Scope,
Acceptance Criteria, Related Code Areas, and Assumptions all rewritten. Everything below this
addendum is the original investigation's findings, kept intact for its evidence value (fresh file
counts, the search-local `docsRouteBasePath` observation, the "cannot fabricate a build measurement"
finding, and the two anti-drift notes this addendum explicitly supersedes) — Plan should read both.

## Search-Before-Grep Compliance

Per this project's Hard Rule and Context Scan, `mcp__knowledge-search__search_docs` and
`graphify query` were called first, before any grep or direct file read:

- `mcp__knowledge-search__search_docs(query="docusaurus build memory showLastUpdateTime
  showLastUpdateAuthor OOM")` → `{"error": "index not found", "action": "run make
  knowledge-index"}`.
- `graphify query "docusaurus config showLastUpdateTime"` → `error: graph file not found:
  .../graphify-out/graph.json` (this worktree has no `graphify-out/` at all).
- Fallback step 3, `python3 tools/knowledge_search.py query "..." --top-k 5` → `knowledge index
  not found — run make knowledge-index`.

All three semantic tools are confirmed unavailable in this worktree/environment. This matches
what the dispatching agent flagged up front. Investigation proceeded via the documented fallback:
direct reads of `website/docusaurus.config.js`, the ticket, the related hotfix ticket, and
`docs/parity_ledger/infrastructure.yaml`, plus targeted `grep`/`find` as follow-up only (never as
the first step). One `WebFetch` call was made against Docusaurus's own hosted docs page to avoid
asserting an unverified claim about `showLastUpdateTime`'s documented behavior from training
knowledge alone (see below) — this is a read-only lookup, not a code search, and doesn't
substitute for the search_docs/graphify requirement, which was satisfied first.

## Current Behavior

### `website/docusaurus.config.js` (read in full)

Four `@docusaurus/plugin-content-docs`-family instances exist:

1. **`docs` preset** (lines 61–77, inside the `classic` preset's `docs` block) — `path:
   '../docs'`, `routeBasePath: 'docs'`, `showLastUpdateTime: true`, `showLastUpdateAuthor: true`
   (lines 70–71). **Out of scope for this ticket** — must stay unchanged per the ticket's own
   Scope/Out-of-Scope.
2. **`tickets` plugin instance** (lines 14–25) — `path: '../tickets/done'`, `routeBasePath:
   'tickets'`, `showLastUpdateTime: true`, `showLastUpdateAuthor: true` (lines 22–23).
3. **`artifacts` plugin instance** (lines 26–36) — `path: '../stored_artifacts'`,
   `routeBasePath: 'artifacts'`, `showLastUpdateTime: true`, `showLastUpdateAuthor: true` (lines
   33–34).
4. **`agent-monitoring` plugin instance** (lines 37–47) — `path: '../agent-monitoring/retro'`,
   `routeBasePath: 'agent-monitoring'`, `showLastUpdateTime: true`, `showLastUpdateAuthor: true`
   (lines 44–45).

This exactly matches the ticket's Related Code Areas description (lines ~19–46 for the three
in-scope plugin blocks, ~66–72 for the unchanged `docs` preset block — confirmed against the
actual current line numbers above, which have shifted slightly from the ticket's estimate but the
block identity/order is unchanged).

A fifth content source, `sidebars-archive.js`, exists in `website/` but is not wired into any
plugin/preset in `docusaurus.config.js` — `docs/archive/**` is served through the `docs` preset
itself (it is not in that preset's `exclude` list: `['superpowers/**', 'specs/**',
'parity_ledger/**', 'scenarios/**', 'entity/**']`), so `sidebars-archive.js` currently appears to
be dead config. Not this ticket's concern, but worth flagging as a latent inconsistency for
whoever next touches `docusaurus.config.js`.

Also present: an `@easyops-cn/docusaurus-search-local` theme (lines 50–58) with
`docsRouteBasePath: ['docs', 'tickets', 'artifacts', 'agent-monitoring']` — this full-text search
plugin indexes **all four** route bases, i.e. the same 6,200+-file corpus this ticket is about.
This is a separate, likely larger memory driver than `showLastUpdateTime`/`showLastUpdateAuthor`
(see "Risks and Open Questions" — flagged, not scoped, since Out of Scope explicitly excludes
"further webpack-level tuning" and this search plugin isn't webpack tuning but is still adjacent
scope creep to avoid).

### Fresh file counts (2026-08-24, vs. the ticket's stale 2026-08-21 snapshot)

| Source | Ticket's 2026-08-21 count | Fresh count today | Delta (3 days) |
|---|---|---|---|
| `docs/` (`.md`/`.mdx`) | 899 (ticket text) / 816 (sibling hotfix ticket text — the two source tickets disagree with each other) | 839 | — |
| `tickets/done/` | 1,637 | 1,688 | +51 |
| `stored_artifacts/` | 3,636 | 3,684 | +48 |
| `agent-monitoring/retro/` | 13 | 12 | -1 |
| **Total (all four)** | 6,185 | 6,223 | +38 net |

Disk size: `docs/` 17M, `tickets/done/` 16M, `stored_artifacts/` 38M, `agent-monitoring/retro/`
296K.

Growth-rate evidence (git history, last 30 days, `tickets/done` + `stored_artifacts` combined):
- **2,207 total file touches** (adds + modifies + renames).
- **2,043 of those were new-file adds** (`git log --since="30 days ago" --diff-filter=A
  --name-only`), i.e. ~68 new files/day into exactly the two plugin instances this ticket targets.

This growth rate is the load-bearing fact for the "will this be enough" question below: at ~68
new files/day, any fixed amount of headroom this ticket buys back gets consumed again within days
to a few weeks, not months.

## Docusaurus's `showLastUpdateTime`/`showLastUpdateAuthor` — documented behavior vs. inference

Fetched Docusaurus's own hosted plugin-content-docs API reference
(`https://docusaurus.io/docs/api/plugins/@docusaurus/plugin-content-docs`) rather than relying on
training-data recall alone. The **only** documented caveat found there is:

> "Only for Markdown pages. Whether to display the last date the doc was updated. This requires
> access to git history during the build, so will not work correctly with shallow clones (a
> common default for CI systems). With GitHub `actions/checkout`, use `fetch-depth: 0`."

Two things follow from this, stated with appropriate uncertainty:

1. **Confirmed, not inferred**: the feature requires full git history at build time, which
   `.github/workflows/deploy-docs.yml`'s `Checkout` step already provides (`fetch-depth: 0`, set
   in the earlier hotfix's untouched config). So enabling/disabling this setting does not change
   whether the checkout step needs full history — that stays true regardless, because the `docs`
   preset (out of scope) still needs it.
2. **Not documented, only inferred from known Docusaurus implementation behavior**: Docusaurus's
   `getFileLastUpdate` logic (in `@docusaurus/utils`, consumed by `plugin-content-docs`) resolves
   each file's last-update time/author via a `git log -1 --format=...` subprocess call
   **per file**, when the feature is enabled and no frontmatter override exists to short-circuit
   it. This project's `website/node_modules/` is not installed in this worktree (confirmed: `ls
   website/node_modules` returns 0 entries, and `npm ci` was not run — see "What Could Not Be
   Verified" below), so this could not be confirmed by reading the actual installed source in this
   environment. It should be treated as a plausible, well-known implementation detail, not a
   verified fact for this specific ticket's evidence base.

**Docusaurus's own docs do not state a memory/heap cost for this feature.** The ticket's own
"Assumptions / Open Questions" already flags this precisely: "Assumes Docusaurus's per-file `git
log` cost ... is a measurable contributor to the OOM, based on documented Docusaurus
build-performance behavior at this file count — the Investigate phase should produce real
before/after numbers, not rely on this assumption alone." Investigate could not produce those real
numbers (see next section) — this is reported honestly, not glossed over.

## What Could Not Be Verified (real build measurement)

- `website/node_modules/` does not exist in this worktree (`ls website/node_modules | wc -l` →
  `0`). `npm`/`node` binaries are present and functional
  (`/home/u24desktop/.nvm/versions/node/v24.10.0/bin/{npm,node}`), but no `npm ci` was run.
- Running `npm ci` and a real `npm run build` (docusaurus build) over the actual 6,200+-file
  corpus, twice (before/after this change), to get a real memory/time comparison as the ticket's
  own Scope item 2 and Acceptance Criteria #3 ask for, is a substantial operation (network install
  + a build that took ~16 minutes and multiple GB of heap on the last real CI run before OOM-ing)
  that Investigate should not attempt to fabricate or approximate. This is exactly the situation
  the dispatching agent's brief anticipated and instructed against overclaiming on.
- **This ticket's AC #3 ("A real build comparison ... reports the measured memory/time reduction")
  cannot be satisfied by Investigate.** It must be satisfied either by the Implement/Test phase
  running a real local build (with real time/memory budget allotted for it) or, more reliably,
  by observing the next real push-triggered `Deploy Docs to GitHub Pages` CI run after this
  change merges — the same "confirm via live run" pattern the sibling hotfix ticket itself had to
  fall back on for its own unchecked ACs. **Flagging this now so Plan doesn't silently assume
  Investigate produced numbers it did not produce.**

## Mechanics / Engine Constraints

None. This ticket touches `website/docusaurus.config.js`, a documentation-build tooling config —
it has no interaction with `docs/mechanics/` simulation laws or `docs/engine/` pipeline contracts.
No chapter/contract constrains this change.

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: entry `INFRA-181` (line 1916) has `v2_evidence:
  'website/docusaurus.config.js + website/package.json + Makefile (docs-serve, docs-build
  targets)'` — this ticket directly modifies the exact file cited as that entry's evidence. Per
  the project's Authoritative Mechanics Rule ("If logic changes, update the corresponding doc AND
  the parity ledger entry ... in the same session"), `INFRA-181`'s `v2_evidence` (and optionally
  `text`, which currently already only says "four plugin-content-docs instances ... " without
  mentioning `showLastUpdateTime` specifically, so `text` itself may not strictly need to change)
  should be refreshed to reflect the new `showLastUpdateTime`/`showLastUpdateAuthor` state and a
  current date, so the entry doesn't silently go stale relative to the file it's supposed to be
  evidence for. `INFRA-181` is `priority: P2` (not P0), so a passing `test_path` is not a hard
  gate requirement, but `test_path` is currently `null` — Implement/Test should consider pointing
  it at the new static guard test (see test_plan.md) while touching this entry anyway.

The `docs/README.md` doc (path: `docs/README.md`, under `docs/`) is not required to change for
this ticket: its one Docusaurus mention (line 16: "The project uses a Docusaurus 3 site...") is a
generic, still-accurate description of the site's existence and purpose, and does not reference
`showLastUpdateTime`/`showLastUpdateAuthor` or any option-level build behavior this ticket
changes.

`docs/audits/D18_ci_release_pipeline.md` and `docs/plans/architecture_resilience_remediation_roadmap.md`
(both surfaced by grep for "docusaurus"/"deploy-docs") are not required to change: both describe
`deploy-docs.yml`'s existence and general CI posture (concurrency controls, lack of a doc-path
CI check) at a level this ticket's metadata-flag change doesn't affect — neither references
`showLastUpdateTime`/`showLastUpdateAuthor` or per-plugin memory cost.

## Parity Ledger Overlap

- **`INFRA-181`** (`docs/parity_ledger/infrastructure.yaml`, `infrastructure.yaml` subsystem file)
  — `status: verified`, `priority: P2`. Directly overlaps: its `v2_evidence` names
  `website/docusaurus.config.js`, the exact file this ticket edits. See "Docs Requiring Update"
  above for the specific update needed. **Not P0** — no hard passing-test gate requirement, but
  should still get a `test_path` pointing at the new guard test as good practice while the entry
  is touched.
- No other `infrastructure.yaml` entries (or entries in any other subsystem file) reference
  `docusaurus.config.js`, `showLastUpdateTime`, `showLastUpdateAuthor`, or the `tickets`/
  `artifacts`/`agent-monitoring` plugin instances by name — confirmed via grep across
  `docs/parity_ledger/`.
- No P0 entries are touched by this change.

## Prior Work

- **`TCK-20260821-HOTFIX-GHPAGES-BUILD-OOM`** (done, merged) — the direct predecessor. Raised
  `NODE_OPTIONS: --max-old-space-size=8192` on the `Build` step of
  `.github/workflows/deploy-docs.yml`. Its own ticket text explicitly named this ticket as a
  "complementary structural fix ... not a substitute for it," and flagged in its own Assumptions
  that "if the corpus keeps growing at its current rate this may need revisiting later — not
  necessarily a permanent fix." Per the dispatching agent's brief, that revisiting need has
  already materialized: the very next real push-triggered build still OOM-crashed at V8's own
  logged old-space ceiling of ~8203MB (`NODE_OPTIONS` confirmed applied), aborting near
  `Mark-Compact 7929.5 (8619.6) -> 7576.6 (8281.1) MB` after ~16 minutes, exit 134.
- That hotfix also added `tests/static/test_deploy_docs_heap_limit.py` (3 tests, YAML-parse-based
  static guard over `deploy-docs.yml`'s `Build` step `env` block) — the direct structural
  precedent this ticket's own new test should follow, adapted for a JS config file instead of a
  YAML workflow file (see test_plan.md).
- No other stored artifacts or done tickets specifically address `docusaurus.config.js`'s
  `showLastUpdateTime`/`showLastUpdateAuthor` settings. `INFRA-181` (added at an earlier,
  unspecified ticket) is the only parity-ledger record of the Docusaurus scaffold's existence at
  all.

## Risks and Open Questions

1. **Open, not decided here (per the dispatching agent's brief, item 5)**: Given the observed
   crash point (~8.3–8.6GB old-space, well above the 8192MB flag, meaning the flag itself did
   provide some — just insufficient — headroom over the prior ~4.1GB ceiling), is disabling
   `showLastUpdateTime`/`showLastUpdateAuthor` on 3 of 4 plugin instances (5,384 of 6,223 total
   files: `tickets/done` 1,688 + `stored_artifacts` 3,684 + `agent-monitoring/retro` 12) plausibly
   enough to get under 8192MB, or under whatever ceiling gets set next? **This cannot be answered
   with confidence from static investigation alone**, for two compounding reasons:
   - The actual memory driver behind an ~8.3GB-plus peed is very likely dominated by markdown/MDX
     AST parsing and webpack bundling of 6,223 files into individual routes, plus the
     `@easyops-cn/docusaurus-search-local` theme's full-text index build across all four route
     bases — not by transient per-file `git log` subprocess calls, whose own process memory is
     reclaimed on each subprocess exit and whose retained in-Node footprint is just a timestamp +
     author string per file (kilobytes total across 5,384 files, not gigabytes).
   - Even if this change measurably reduces peak memory by some amount, the ~68-new-file/day
     growth rate (`tickets/done` + `stored_artifacts` alone, last 30 days) means any fixed
     headroom bought back here is a temporary reprieve, not a structural fix, exactly as the
     ticket's own Out-of-Scope section already acknowledges by explicitly declining to scope the
     real structural question (retention/exclusion policy for `tickets/done`/`stored_artifacts`).
   - **Honest assessment for Plan to carry forward**: this fix is worth doing (it is free,
     directionally correct, and removes a genuine per-file git-subprocess cost with no established
     functional dependency elsewhere — see next section), but investigation.md does **not** find
     evidence that it will, on its own, be sufficient to get the next real push-triggered build
     green. Plan should treat "is this enough" as still open pending a real build measurement
     (Implement/Test phase or the next live CI run), not assume yes or no.
2. **Sizing/measurement gap**: this ticket's AC #3 cannot be satisfied without either a real local
   `npm ci && npm run build` (expensive, ~16 min based on the last real CI run, and this
   environment doesn't have `node_modules` installed) or waiting for the next live CI run after
   merge. Flagged for Plan to schedule explicitly rather than skip silently.
3. **Ticket-internal inconsistency, informational only**: the two source tickets disagree on the
   `docs/` file count at the same point in time — this ticket's Request Summary says 899, the
   sibling hotfix ticket's Request Summary says 816 (and its Related Code Areas says "16MB" for
   the same 816-file set). This doesn't affect this ticket's scope (docs/ is unchanged either way)
   but is worth noting since neither historical number matches today's fresh count (839) exactly,
   consistent with docs/ also growing, just far more slowly than tickets/done or stored_artifacts.

## Anti-Drift Hazards

- **Do not touch the `docs` preset's `showLastUpdateTime`/`showLastUpdateAuthor`.** Explicitly
  Out of Scope. It's the smallest of the four instances by file count and has real editorial value
  as live-authored reference material (per the ticket's own rationale) — an easy accidental
  one-line copy-paste mistake to avoid when editing the other three blocks that sit right next to
  it in the same file.
- **Do not attempt to fabricate or approximate a real before/after memory number in place of
  actually running a build.** The ticket's AC #3 asks for a *measured* reduction; a plausible
  estimate written as if it were measured would violate the project's Uncertainty Rule ("vague
  leads stay vague until evidence narrows them") and this ticket's own explicit instruction not to
  overclaim.
- **Do not expand scope into the `@easyops-cn/docusaurus-search-local` theme's
  `docsRouteBasePath`** (flagged above as a plausible larger memory driver) — that's a different
  plugin, a different config surface, and explicitly adjacent scope creep relative to this
  ticket's narrowly-scoped `showLastUpdateTime`/`showLastUpdateAuthor` change. If Plan wants to
  pursue it, it should be a new ticket, not folded into this one.
- **Do not expand scope into deciding retention/exclusion policy for `tickets/done`/
  `stored_artifacts`** — the ticket's own Assumptions section explicitly flags this as a
  repo-owner content-publishing decision, not a build-performance fix, and declines to assume an
  answer. Investigate agrees this is correctly out of scope.
- **`showLastUpdateTime: false` vs. omitting the key entirely** — Docusaurus defaults this option
  to `false` when absent, so either form satisfies the ticket's Acceptance Criteria #1 ("no longer
  set ... or explicitly set them `false`"). Whichever form Plan/Implement chooses, the new static
  guard test (see test_plan.md) should assert on the *effective* value (absent-or-false), not
  assume one specific syntactic form, so a future refactor that flips between the two forms
  doesn't spuriously break the guard.
