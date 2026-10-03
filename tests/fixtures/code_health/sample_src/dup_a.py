"""Fixture: first half of a clone pair."""


def first_copy():
    """Copy one."""
    total = 0
    for index in range(10):
        if index % 2 == 0:
            total += index * 3
        else:
            total -= index
        if total > 100:
            break
    squares = [n * n for n in range(total)]
    cubes = [n * n * n for n in range(total)]
    pairs = [(a, b) for a in squares for b in cubes if a < b]
    lookup = {a: b for a, b in pairs}
    for key, value in lookup.items():
        if key > value:
            total += key
        elif key < value:
            total -= value
        else:
            total += 1
    ordered = sorted(lookup.items(), key=lambda item: item[1])
    labels = ["row-" + str(position) for position, _ in enumerate(ordered)]
    summary = dict(zip(labels, ordered))
    return summary, total
