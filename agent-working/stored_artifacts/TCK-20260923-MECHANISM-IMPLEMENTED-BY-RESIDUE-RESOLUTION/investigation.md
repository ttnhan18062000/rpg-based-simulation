---
status: historical
layer: architecture
authority: P2
audience: agent
ticket_id: TCK-20260923-MECHANISM-IMPLEMENTED-BY-RESIDUE-RESOLUTION
artifact_type: investigation
tags: [architecture]
---

# Investigation

- Numbers re-verified: 77 of 93 bound at start (ticket said 76); 11 `gap` (ticket said 12); real residue 5, unchanged.
- rpg-feature-planning signed off on the merge and the state direction, and required a runtime instrument for absence claims (the repo's own `TCK-20260930-MECHANISM-ABSENCE-VERDICTS-NEED-RUNTIME-EVIDENCE` rule). Done: 0 calls for `CalamityService.apply_calamity_consequences`, `SocialMemoryService.tick_place_attachment`/`check_nemesis_promotion` and `SourceTrustUpdateService.update` over 5 worlds x 2000 ticks, with `InformationBeliefPhase.apply` (2000/world) and `RelationshipService.process_update` as live contrast.
- The static traces and the runtime probe agreed on every absence claim. The probe is what makes the correction to the 2026-09-23 addendum defensible: that addendum said `place_attachment` "accumulates for real", a runtime-sounding claim made without a runtime instrument, and the probe shows its only producer is never called. That is a process finding for agent-working-design.
- `xp_leveling`: independent corroboration of "one undivided implementation" from the progression epic (which already treats `evolution.py` and `leveling.py` as one chain). Merged state: `evolution` becomes `partial` (keeps xp_leveling's corpus-volume caveat).
- `cross_episode_social_consequences.depends_on: [social_memory]` looks semantically wrong (that mechanism uses the campaigns module) and was left unchanged pending a decision.
