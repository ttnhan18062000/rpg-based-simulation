Rework the RPG system with the changes below (applied for all entities),
Think about the core aspects: balance, reality, complexity and deep mechanical, make it a deep RPG simulation. Brainstorming about this deeply, using reference from: games, books, novels, etc.
- add magical damage and related stats (MATK, MDEF, etc)
- adjust the combat formula to account for magical damage
- adjust the attributes to account for magical damage
- add more attributes that affect the non-combat stats, like experience gain, loots, vision, etc
- add secondary stats like: bonus dmg, vulnerability percentage, interaction time, rest time, etc, even stats for "thinking" and "acting"
- adjust the existing actions, interactions, behavior and thinkings for the new system.
- add new actions, interactions, behavior and thinkings for the new system.
- add new items, equipment, consumables, etc for the new system.
- Rework the thinking and behavior of all entities: don't do explicit A -> B -> C, use a way to heuristic, with goals A, entity might choose (randomly based on a formula scaled with stats) different ways to do. Carefully implement this because this is one of the most important parts of the system, make sure we can extend it easily. Make entity "intelligent" and thinking (without actual AI models but with a way to simulate it, like probability), not too perfect but enough to make it feel intelligent.
- Entity now have behaviors and traits, that heavily affect the goal and how they resolve problems, like: aggressive entity, peaceful entity, etc. (based on real world fantasy thinking)
Don't forget to document all the changes, add news if needed not just update the existing ones.