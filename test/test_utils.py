#coding=utf-8
import sys
import unittest

from stup import utils as Utils

class TestUtils(unittest.TestCase):
    def test_seq_add(self):
        self.assertEqual(Utils.seq_add(0xFFFFFFFF, 1), 0x0)
        self.assertEqual(Utils.seq_add(0xFFFFFFFF, 2), 0x1)

        self.assertEqual(Utils.seq_add(0xFFFFFFFE, 1), 0xFFFFFFFF)
        self.assertEqual(Utils.seq_add(0xFFFFFFFE, 2), 0x0)

    def test_seq_sub(self):
        self.assertEqual(Utils.seq_sub(0xFFFFFFFF, 1), 0xFFFFFFFE)
        self.assertEqual(Utils.seq_sub(0x00000000, 1), 0xFFFFFFFF)
        self.assertEqual(Utils.seq_sub(0x00000000, 2), 0xFFFFFFFE)
        for i in range(1000):
            a, b = Utils.rand_u32(), Utils.rand_u32()
            x = Utils.seq_add(a, b)
            y = Utils.seq_sub(x, a)
            z = Utils.seq_sub(x, b)
            self.assertEqual(b, y)
            self.assertEqual(a, z)
