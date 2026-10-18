# Investigation — TCK-20261016-GRIEF-AS-STATE-GRIEF-TRIGGERS-ARE-DETECTED-AND-CARRIED-IN-AUTHORITATIVE-STATE-D80

Defect: grief triggers were detected in `Kernel._phase_observability` and held in a kernel list outside the world, so observability OFF dropped them and changed the authoritative outcome (owner decision 80 (ii)).
Finding: the only production writer of `active=False` is the lifecycle resolver, which writes `death_record` in the same update, so `death_record.tick == tick-1` is a complete detector.
Finding (proof): in 15 natural runs (3 worlds x seeds 42-46 x 5000t) no grief trigger is ever detected and no entity holds a trust_history entry, so natural runs prove inertness only; the trigger path is proven by the forced ally-death scenario and the unit/integration tests.
