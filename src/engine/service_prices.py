"""Prices of the town services a subject meets a need with (SURV-06).

A meal at the inn costs gold; a subject that cannot pay has no meal within reach (SURV-06: "a meal where meals are served, for a
price"). `town_resolution` charges it and `EatScorer` offers the inn path only to a subject that can pay it, so the two share
this one value (TCK-20261007-BIOLOGICAL-NEEDS-ESCALATE-ABOVE-ORDINARY-GOALS-BEFORE-THE-CONSEQUENCE-LINE-SURV-07).
"""
EAT_PRICE_GOLD = 5
REST_PRICE_GOLD = 10
INN_MEAL_HUNGER = 40.0  # what a paid inn meal removes from hunger (was the unpaid core EAT's -40 plus the inn's -20)
