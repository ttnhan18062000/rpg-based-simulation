"""Prices of the town services a subject meets a need with (SURV-06).

A meal at the inn costs gold (SURV-06: "a meal where meals are served, for a price"). Free meals stay on today (owner decision 44: the
removal waits for the animals' own ways), so the price is charged only of what the subject holds; the removal branch makes it a gate.
`building_services` charges it and the removal's `EatScorer` gate reads the same value (TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07).
"""
EAT_PRICE_GOLD = 5
REST_PRICE_GOLD = 10
INN_MEAL_HUNGER = 20.0  # what the inn adds to the core EAT's relief of 40 (free meals stay on, owner decision 44)
