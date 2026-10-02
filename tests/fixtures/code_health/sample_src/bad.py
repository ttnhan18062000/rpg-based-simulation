import os


def risky(values, cache={}):
    try:
        total = 0
        for value in values:
            if value > 0:
                for other in values:
                    if other > value:
                        if other % 2 == 0 and value % 3 == 0:
                            total += other
                        elif other % 5 == 0 or value % 7 == 0:
                            total -= other
                        else:
                            while total > 100:
                                total -= 1
                                if total % 2:
                                    break
            elif value < 0:
                for other in values:
                    if other < value:
                        total += 1
        return total
    except:
        return None
