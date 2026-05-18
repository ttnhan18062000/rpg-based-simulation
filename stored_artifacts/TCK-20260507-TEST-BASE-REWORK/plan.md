# Plan: Test Base Rework

## Strategy
Fix legacy V2EntityBuilder API calls domain by domain. Each domain: investigate → fix local helpers → verify tests pass → move to next.

## Legacy → V2 Mapping
- `.position(x, y)` → `.location(x, y)`
- `.hp(hp, max_hp)` → `.combat(hp=hp, max_hp=max_hp)`
- `.gold(amount)` → `.inventory(gold=amount)`
- `.with_base_stats(atk=, def_stat=, range=)` → `.combat(atk=, def_stat=, attack_range=)`
- `.active(bool)` → `.lifecycle(active=bool)`
- `.combat(range=N)` → `.combat(attack_range=N)`
- `.action_style(n)` → `.combat(action_style=n)`
- `.with_interaction(...)` → `.interaction(...)`
- `.at(x, y)` → `.location(x, y)`
- `.max_slots(n)` → `.inventory(max_slots=n)`
- `.with_class(id)` → `.identity(class_id=id)`
- `.with_personality(...)` → `.identity(personality=...)`
- `.stamina(current, max)` → `.stamina(current=current, max_stamina=max)`
- `.cognition(breadth=)` → `.cognition(detour_breadth=)`
- `.cognition(resistance=)` → `.cognition(interruption_resistance=)`
- `.navigation(mode=)` → `.navigation(movement_mode=)`
- `.monster()` → `.kind("monster").identity(role=MONSTER, faction=MONSTER_HORDE)`
- `.current_project(id)` → `.strategic(current_project_id=id)`
- `.source_trust(...)` → `.strategic(source_trust=...)`
- `.betrayal_count(n)` → `.social(betrayal_count=n)`
- `.movement_mode(m)` → `.navigation(movement_mode=m)`
- `.strategic_project(...)` → `.strategic(projects=...)`
- `.strategic_contract(...)` → `.strategic(contracts=...)`
- `.with_property(k, v)` → `.properties({k: v})`
- `.with_properties(d)` → `.properties(d)`
- `.group_id(n)` → `.identity(group_id=n)`
- `.target(x, y)` → `.navigation(target=(x, y))`
- `.home_pos(x, y)` → `.navigation(home_position=(x, y))`
- `.sleep_debt(v)` → `.biological(sleep_debt=v)`
- `.hunger(v)` → `.biological(hunger=v)`
- `.evolution(lvl)` → `.identity(evolution_level=lvl)`
- `.trust(...)` → `.social(trust_history=...)`
- `.items(...)` → `.inventory(items=[...])`
- `.item(item)` → `.inventory(items=[item])`
- `.skills(s)` → `.identity(learned_skills=s)`
- `.trait(t)` → `.identity(traits={t})`
- `.life_stage(ls)` → `.identity(life_stage=ls)`
- `.personality(p)` → `.identity(personality=p)`
- `.with_contract(c)` → `.strategic(contracts=...)`
- `.social_bond(...)` → `.social(bonds=...)`
- `.social_rejection(...)` → `.social(rejection_count=...)`
- `.with_navigation_v2(...)` → `.navigation(...)`
