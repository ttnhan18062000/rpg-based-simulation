# Frozen open-ticket corpus snapshot

`tests/tools/test_open_ticket_overlap_real_corpus.py`'s job is to prove
`tools/open_ticket_overlap.py`'s scoring is genuinely usable against a real, messy corpus — not a
synthetic one. But the *live* `tickets/todos/`/`tickets/inprogress/` tree changes on every merge:
the target ticket this test's rank/margin assertions depend on
(`TCK-20260920-PERCEPTION-UPDATE-PHASE-NEVER-INSTANTIATED`) will eventually close and leave the
open corpus, and any new open ticket touching the same code areas could become a close runner-up
and collapse the measured margin — both would fail an unrelated PR for a reason that has nothing
to do with `open_ticket_overlap.py` itself. Same defect class as
`TCK-20260929-RUN-DEDUP-BASELINE-PINS-GROWING-CORPUS` (an exact assertion over a corpus that keeps
changing), found by peer review round 4 on `TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER`.

This directory (`todos/` + `inprogress/`) is a frozen copy of the real
`tickets/todos/`+`tickets/inprogress/` trees as they stood at commit
**`25be81b396e9b7fbe6c43df5d559831dc7381684`** on branch `working-log-consolidation-cross-checkout-fix`
(82 real open tickets, full directory structure including `tickets/todos/<folder>/` subfolders
preserved). The real-corpus test passes this directory as `todos_root`/`inprogress_root` instead
of the live tree — still a real, messy, non-synthetic corpus (nothing here was written or trimmed
for the test), just a stable one that won't drift out from under an unrelated future PR.

**Deliberately not a skip-if-absent/skip-if-target-missing guard** — that would silently turn the
only real-quality proof this tool has into a no-op the moment the frozen target ticket's shape
stopped matching reality, which is worse than a loud, obviously-wrong failure. If this corpus ever
needs updating (e.g. a real scoring change genuinely requires re-measuring against fresher data),
re-snapshot deliberately and update this README's SHA — never quietly.
