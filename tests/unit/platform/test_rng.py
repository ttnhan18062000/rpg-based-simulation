import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import unittest
from src.platform.rng import DeterministicRNG
from src.core.models.enums import Domain

class TestDeterministicRNG(unittest.TestCase):
    def test_reproducibility(self):
        rng1 = DeterministicRNG(42)
        rng2 = DeterministicRNG(42)
        
        for i in range(10):
            self.assertEqual(
                rng1.next_float(Domain.COMBAT, 1, i),
                rng2.next_float(Domain.COMBAT, 1, i)
            )

    def test_domain_separation(self):
        rng = DeterministicRNG(42)
        f1 = rng.next_float(Domain.COMBAT, 1, 100)
        f2 = rng.next_float(Domain.LOOT, 1, 100)
        self.assertNotEqual(f1, f2)

    def test_next_int(self):
        rng = DeterministicRNG(123)
        for _ in range(100):
            val = rng.next_int(Domain.SPAWN, 5, 1, 10, 20)
            self.assertTrue(10 <= val <= 20)
