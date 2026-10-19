# Test plan — TCK-20261016-GRIEF-AS-STATE-GRIEF-TRIGGERS-ARE-DETECTED-AND-CARRIED-IN-AUTHORITATIVE-STATE-D80

- Unit: tests/unit/core/test_grief_triggers.py, tests/unit/kernel/test_grief_trigger_drain.py (restated; watermark idempotency).
- Integration: tests/integration/campaigns/test_mid_episode_grief_trigger.py incl. checkpoint-resume-once and observability OFF == ON.
- Proof (scratch /mnt/data/scratch-lane-c): natural 15-pair projected-digest/death/alive equality; OFF vs ON on 2 seeds; forced ally death on 3 seeds, base vs new, ON and OFF (results in divergence 2.134).
- Known red: tests/regression/test_behavioral_5k.py (red on base too).
