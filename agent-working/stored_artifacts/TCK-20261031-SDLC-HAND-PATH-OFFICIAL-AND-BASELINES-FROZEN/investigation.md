---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261031-SDLC-HAND-PATH-OFFICIAL-AND-BASELINES-FROZEN
artifact_type: investigation
tags: [ai, governance, delivery]
---

# Investigation

- `record_run.py:65` and the closure CLI (`record_hand_orchestrated_closure.py`, the `--path-reason other` check) were the only two places that enforced a note, and only for `other`.
- Stored rows are never re-validated for a note: `record_run.validate_record` is called only on new writes (record_run main, the closure tool, the Codex pilot simulation). `validate.py::check_path_record` checks only that `path_reason` is a known value. `path_note` is read by no other tool.
- The decided set comes from #715 comments 6529263880 (2026-10-31) and 6529808776 (2026-10-30). Where plan section 6 words OD-2, OD-10 and OD-14 more widely than the comments, the comments win.
- Baselines: plan section 46 at `1ccaba303` names no measurement SHA; rows are frozen as written with that ref. Host ubuntu timings before 2026-10-30 are not a baseline (#715 6527003378).
- CLAUDE.md example of `--path-reason` shows alternatives without `--path-note`; left to the owner.
