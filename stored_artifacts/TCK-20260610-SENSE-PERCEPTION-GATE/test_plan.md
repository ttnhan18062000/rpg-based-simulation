# Test Plan — TCK-20260610-SENSE-PERCEPTION-GATE

## Coverage

| Test | Scenario |
|------|----------|
| wolf detects scent | predator_smell_senses very_high smell → medium scent signal perceived |
| wolf > human scent confidence | wolf confidence ≥ human confidence same signal |
| spider vibration | spider_vibration_senses very_high vibration → low vibration signal perceived |
| arcane detects magic | arcane_senses high magic_sense → high magic_signal perceived |
| human no magic | normal_humanoid_senses magic_sense=none → magic_signal not in signals_used |
| no profile → baseline | entity without sense_profile_id uses baseline_humanoid |
| unknown profile → baseline | unrecognised profile_id falls back to baseline_humanoid |
| determinism | same inputs → identical PerceptionResult |
| catalog immutability | catalog.sense_profiles unchanged after can_perceive |
| distance reduces confidence | near > far confidence same signal |
| no signal no perception | scent=none → scent not in signals_used |

All 11 pass.
