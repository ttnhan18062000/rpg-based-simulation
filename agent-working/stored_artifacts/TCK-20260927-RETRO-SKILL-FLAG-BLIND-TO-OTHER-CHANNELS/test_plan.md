---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260927-RETRO-SKILL-FLAG-BLIND-TO-OTHER-CHANNELS
artifact_type: test_plan
tags: [agent-monitoring, retro, data-quality]
---

# Test Plan: TCK-20260927-RETRO-SKILL-FLAG-BLIND-TO-OTHER-CHANNELS

Extends `tests/tools/test_generate_retro.py` (same file — this ticket modifies that module's
existing function, not a separate concern).

## Normal flow
- AC1: fixture skill "security-review" (past grace period, would be stale otherwise) with a
  covering tag mapping -> not flagged, `covered_by_other_channel` names the channel.
- AC6 (covered case): same as AC1.

## Edge cases
- AC2: fixture skill with no tag mapping, past grace period -> still flagged (signal not
  silenced).
- AC6 (uncovered case): same as AC2.
- A covered skill with NO `date_added` (the `flagged_unknown_age` shape) is also correctly
  diverted to `covered_by_other_channel`, not just the `flagged_stale` shape — checked so the
  "before either flag branch" ordering claim in the docstring is actually exercised for both
  branches, not just one.
- AC6 (nonzero-invocation case, pre-existing guarantee unaffected): a skill with a real Skill-tool
  invocation is never flagged regardless of channel coverage.

## Failure modes / regression-prone paths
- AC3: derivation string names `covered_by_other_channel` and states what a zero does/does not
  imply.
- AC4: source is `get_skill_mapping()`, never a hardcoded skill-name list — asserted via
  `inspect.getsource()` grep, mirroring `test_flagged_skills_list_never_auto_triggers_downstream_
  action`'s existing precedent for the same style of guard in this file.
- AC5: not modified by this ticket; existing `test_write_report_preserving_notes_*` tests re-run
  unmodified as a regression guard.
- Real-corpus check: `api-design-principles` and `python-performance-optimization` (2 of the 3
  currently-zero-invocation tag-mapped skills) must appear in `covered_by_other_channel` today,
  confirming the fix actually changes real-corpus output, not just fixture behavior.

## Existing tests checked for overlap
- `test_zero_invocation_flag_current_domain_skills_all_excluded_on_real_corpus`,
  `test_backend_testing_post_fix_state_not_currently_flagged` — re-run unmodified; both still pass
  (their assertions target specific domain-skill absence, unaffected by the new bucket).
- `test_flagged_skills_list_never_auto_triggers_downstream_action`,
  `test_six_domain_skills_verdict_not_reopened` — re-run unmodified; confirm the new code doesn't
  reintroduce a forbidden downstream-action pattern or re-litigate the settled verdict.
