---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260924-DELIVERY-PR-RENDERER
date: 2026-09-24
tags: [delivery, ai, documentation]
---

# Investigation — TCK-20260924-DELIVERY-PR-RENDERER

## Confirmed facts
- `tools/delivery/pr_template_spec.json` (from ticket 2) already has the exact section list/order
  and `rendered` flags this ticket must consume, not hardcode.
- `tools/validate_frontmatter.py::extract_frontmatter(text) -> dict|None` parses a ticket's
  frontmatter (gives `layer`) — reused rather than writing a third parser, per Related Code Areas.
- `tools/generate_registry.py::parse_body_section(body, section) -> str` extracts `## <section>`
  text up to the next `## ` heading — reused for `## Title`, `## Tier`, `## Request Summary`,
  `## Test Summary`, `## Completion Summary`.
- `registries/layer_registry.jsonl`: one JSON object per line, `{"layer": ..., "note": ...}` — the
  allowlist `<scope>` must come from.
- **Apparent inconsistency between plan §3.5's abstract template and its own worked examples,
  resolved toward the examples per this ticket's own Implementation Notes instruction to use them
  as fixtures.** The abstract block shows a bare `<scope>: <what landed>` for a single ticket with
  no count suffix, but all three real worked examples (#240, #237, #229) — including the two
  single-ticket ones (#237, #229) — end with `(1 ticket)` / `(N tickets)`. **Decision: always
  include the count suffix**, singular/plural, for every N ≥ 1 — one code path, matches the literal
  historical evidence the ticket told me to fixture against.
- `docs_to_update_coverage` (done-checker precheck) flags any `docs/` path touched but not named in
  a ticket's own `## Files Changed`/`## Related Docs` — confirmed real this session (hit on ticket
  1b's `docs/REGISTRY.yaml` regen). Not directly relevant to this ticket's own scope, but informs
  how `## Verification`'s "Gates" line should be worded (name the condition, not just PASS/FAIL).

## Design decisions
1. **`## Verification` reads each ticket's own recorded `## Test Summary`/`## Completion Summary`
   text, not a live re-run of `done_checker_static.py`.** Assumption 3 leans toward "reading" gate
   results rather than hand-supplying them, but a live re-run reflects *current* working-tree state
   (e.g. `data_runs_clean` scans `data/runs/` as it exists *now*, which drifts constantly in this
   shared worktree — confirmed this session: it FAILed identically-but-for-unrelated-reasons on all
   three of this batch's own closes so far). The ticket's own `## Test Summary`/`## Completion
   Summary` is the historically-accurate record of what actually happened *at that ticket's own
   close*, which is what a PR reviewer actually wants to know. This still satisfies "read them, don't
   hand-supply" — it reads the recorded result rather than re-deriving or re-typing it.
2. **"Known gaps" extraction is a literal scan for the substring `FAIL` inside the two sections
   above**, surfacing the containing line. This matches the convention this very batch already
   established by hand (e.g. "`data_runs_clean` FAIL — ... reported not routed around") — the
   renderer formalizes an existing habit rather than inventing new prose conventions.
3. **Ticket discovery**: primary signal is `TCK-` IDs extracted from `git log <base>..HEAD
   --format=%s` (commit subjects); secondary signal is ticket IDs implied by
   `git diff --name-only <base>..HEAD -- tickets/` (files actually touched). Mismatch between the
   two sets is reported (AC7), but commit-subject IDs remain the set actually rendered — "primary
   signal" per Scope item 2.
4. **File lookup searches every `tickets/` subdirectory** (`tickets/**/<id>.md` via `Path.rglob`),
   so a ticket that moved `inprogress/` → `done/` mid-branch is still found (Assumption 4) —
   verified by fixture, not just by inspection.
5. **`<scope>` tie-break**: most-common `layer` among the discovered tickets; on a tie, report it
   (a warning string, not a raised error) and pick the layer of the first-discovered ticket
   (commit-subject order) as the tiebreak — deterministic and stated, per Assumption 1.
6. **Batch theme**: `--theme` CLI flag as an explicit override (no ticket field exists for "the
   batch's overall theme," and synthesizing one well is a genuinely hand-crafted judgment call in
   the three real worked examples). Without `--theme`, defaults to the first discovered ticket's own
   `## Title` text, truncated to a length budget — an honest, stated default per Assumption 1's
   framing, not a claim of real theme synthesis.
7. **`## Why` concatenates every ticket's Request Summary's first paragraph only** (Assumption 2),
   not the full section — bounds output length for a large batch while still giving the real
   substance (Request Summaries in this repo's tickets consistently front-load the core claim in
   paragraph 1, confirmed by re-reading all six sibling tickets in this very epic).
