import json

D = "/tmp/claude-1000/-home-u24desktop-Working-rpg-based-simulation/4681963b-938f-48c6-9217-e11f2d9c7a12/scratchpad/"
keys = ["samples", "distinct_combat_projects", "distinct_combat_objective_ids", "projects_ever_terminal",
        "project_ever.COMPLETED", "project_ever.ABANDONED", "target_dead_while_objective_current", "target_out_of_radius_while_objective_current", "dead_holder_samples_excluded",
        "attacks.execute_attack_dispatch", "attacks.resolve_attack_calls", "end_to_close_delay.0-10", "end_to_close_delay.11-20", "end_to_close_delay.21-50", "end_to_close_delay.51+", "end_to_close_delay.max", "ended_never_closed_age.0-10", "ended_never_closed_age.11-20", "ended_never_closed_age.21-50", "ended_never_closed_age.51+", "nav_target_dist_to_live_target.0-1", "nav_target_dist_to_live_target.4+", "state_sha256"]
for world in ("crowded_frontier", "frontier_living_world"):
    c = json.load(open(f"{D}ab_control.{world}.json"))
    f = json.load(open(f"{D}ab_fixed.{world}.json"))
    print(world)
    for k in keys:
        print(f"  {k:42} control={c.get(k, 0)!s:>18} fixed={f.get(k, 0)!s:>18}")
