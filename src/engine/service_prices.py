"""Prices of the town services a subject meets a need with (SURV-06).

A meal at the inn costs gold (SURV-06: "a meal where meals are served, for a price"). Nothing is free (owner decisions 44 and 73): a service is
served only to a subject holding the full price, and the price is taken atomically with the meal (no clamp to what the subject holds).
`building_services` charges it (a bed is refused at service time, not by a scorer: `SleepScorer` still targets the inn) and `EatScorer` reads the same price (TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1).
"""
EAT_PRICE_GOLD = 5
REST_PRICE_GOLD = 10
INN_MEAL_HUNGER = 60.0  # the relief of one paid inn meal: today's total of the core 40 plus the inn's 20 (owner decision 73, memo row 73)
