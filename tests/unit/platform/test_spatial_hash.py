import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

import unittest
from src.platform.spatial_hash import SpatialHash
from src.core.models import Vector2

class TestSpatialHash(unittest.TestCase):
    def test_insert_query(self):
        sh = SpatialHash(cell_size=10)
        sh.insert(1, Vector2(5, 5))
        sh.insert(2, Vector2(15, 15))
        
        self.assertEqual(sh.query_cell(Vector2(5, 5)), {1})
        self.assertEqual(sh.query_cell(Vector2(15, 15)), {2})

    def test_query_radius(self):
        sh = SpatialHash(cell_size=10)
        sh.insert(1, Vector2(5, 5))
        sh.insert(2, Vector2(15, 15))
        sh.insert(3, Vector2(25, 25))
        
        # Radius 10 covers neighboring cells
        res = sh.query_radius(Vector2(15, 15), 10)
        self.assertIn(1, res)
        self.assertIn(2, res)
        self.assertIn(3, res)

    def test_move(self):
        sh = SpatialHash(cell_size=10)
        sh.insert(1, Vector2(5, 5))
        sh.move(1, Vector2(5, 5), Vector2(15, 15))
        
        self.assertEqual(sh.query_cell(Vector2(5, 5)), set())
        self.assertEqual(sh.query_cell(Vector2(15, 15)), {1})

    def test_remove(self):
        sh = SpatialHash(cell_size=10)
        sh.insert(1, Vector2(5, 5))
        sh.remove(1, Vector2(5, 5))
        self.assertEqual(sh.query_cell(Vector2(5, 5)), set())
