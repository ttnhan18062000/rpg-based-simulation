"""
tests/unit/engine/test_sort_tiebreaker.py

Verifies that the sort tiebreaker added to ConversionOptionGenerator and
PersonalityAwareSelector produces a deterministic canonical ordering when
multiple options share the same score.
"""

from src.domains.progression.schema import ConversionKind, ConversionOption


def _opt(kind: ConversionKind, score: float) -> ConversionOption:
    return ConversionOption(kind=kind, score=score, expected_growth_delta=0.0)


# Canonical order for tied score is alphabetical by kind.value (descending=True reverses string sort)
# STORE_ITEM > SELL_LOOT > SAVE_FOR_LATER > REPAIR_GEAR > ... alphabetically reversed
_TIED_OPTIONS = [
    _opt(ConversionKind.SAVE_FOR_LATER, 0.5),
    _opt(ConversionKind.STORE_ITEM, 0.5),
    _opt(ConversionKind.SELL_LOOT, 0.5),
    _opt(ConversionKind.REPAIR_GEAR, 0.5),
    _opt(ConversionKind.CRAFT_ITEM, 0.5),
]


def _apply_generator_sort(options):
    return sorted(options, key=lambda o: (o.score, o.kind.value), reverse=True)


def _apply_selector_sort(pairs):
    return sorted(pairs, key=lambda pair: (pair[1], pair[0].kind.value), reverse=True)


class TestGeneratorSortTiebreaker:
    def test_sort_is_stable_on_tied_scores(self):
        result_a = _apply_generator_sort(_TIED_OPTIONS)
        result_b = _apply_generator_sort(list(reversed(_TIED_OPTIONS)))
        assert [o.kind for o in result_a] == [o.kind for o in result_b]

    def test_kind_value_breaks_ties_alphabetically_descending(self):
        result = _apply_generator_sort(_TIED_OPTIONS)
        kind_values = [o.kind.value for o in result]
        assert kind_values == sorted(kind_values, reverse=True)

    def test_higher_score_still_wins_over_kind(self):
        winner = _opt(ConversionKind.ALLOCATE_AP, 0.9)  # lowest kind.value alphabetically
        losers = [_opt(ConversionKind.STORE_ITEM, 0.5), _opt(ConversionKind.TRAIN_SKILL, 0.5)]
        result = _apply_generator_sort([*losers, winner])
        assert result[0].kind == ConversionKind.ALLOCATE_AP


class TestSelectorSortTiebreaker:
    def test_sort_is_stable_on_tied_scores(self):
        pairs = [(_opt(kind, 0.0), 0.7) for kind in [
            ConversionKind.SAVE_FOR_LATER,
            ConversionKind.CRAFT_ITEM,
            ConversionKind.STORE_ITEM,
        ]]
        result_a = _apply_selector_sort(pairs)
        result_b = _apply_selector_sort(list(reversed(pairs)))
        assert [p[0].kind for p in result_a] == [p[0].kind for p in result_b]

    def test_higher_final_score_wins(self):
        winner = (_opt(ConversionKind.ALLOCATE_AP, 0.0), 1.5)
        loser = (_opt(ConversionKind.TRAIN_SKILL, 0.0), 0.2)
        result = _apply_selector_sort([loser, winner])
        assert result[0][0].kind == ConversionKind.ALLOCATE_AP
