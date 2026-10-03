"""Seeded test-order shuffle for the Epic A criterion 3 random-order check
(TCK-20261003-EPIC-A-LEAK-REVERIFY-AND-PILOT-CI-RUN-CROSS-CHECK).

A private, self-contained pytest plugin, not a project tool: it uses its own `random.Random(seed)` instance,
never the global `random` state or any simulation RNG, so it does not touch the repo's RNG contract. No
third-party random-order plugin is installed in the project venv.

Usage (the seed comes from the environment so each run is reproducible):

    SEEDED_SHUFFLE_SEED=3 PYTHONPATH=<this directory> python -m pytest -p seeded_shuffle_plugin -q \
        -p no:cacheprovider <affected test files>

The plugin shuffles the collected items once, after collection, and prints the seed in the header.
"""
import os
import random


def pytest_report_header(config):
    return "seeded_shuffle_plugin: seed=%s" % os.environ.get("SEEDED_SHUFFLE_SEED", "unset")


def pytest_collection_modifyitems(session, config, items):
    seed = int(os.environ["SEEDED_SHUFFLE_SEED"])
    random.Random(seed).shuffle(items)
