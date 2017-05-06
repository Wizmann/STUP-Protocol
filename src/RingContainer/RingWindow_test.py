#coding=utf-8

import unittest
from .RingWindow import RingWindow
from .ContainerItem import ContainerItem


class RingWindowTest(unittest.TestCase):
    def test_random_get_and_set(self):
        rw = RingWindow(10)
        
        self.assertEqual(rw.get_by_index(5), None)

        rw.add(ContainerItem(3, 5, 'foo'))
        a = rw.get_by_index(3)
        self.assertEqual(a.payload, 'foo')
        self.assertEqual(rw.size(), 10)

    def test_window_movement_1(self):
        rw = RingWindow(5)

        rw.add(ContainerItem(0, 3, 'foo'))
        rw.add(ContainerItem(3, 4, 'bar'))

        a = rw.pop_left()
        self.assertEqual(a.payload, 'foo')

        self.assertEqual(rw.size(), 5)
        self.assertEqual(rw.range_l, 3)
        self.assertEqual(rw.range_r, 8)

        b = rw.get_by_index(3)
        self.assertEqual(b.payload, 'bar')
        b.payload = 'baz'
        self.assertEqual(b.payload, 'baz')

    def test_window_movement_2(self):
        rw = RingWindow(5)
        self.assertEqual(rw.range_l, 0)
        self.assertEqual(rw.range_r, 5)

        for i in xrange(100):
            rw.add(ContainerItem(i, i + 1, 'foo'))

            a = rw.pop_left()
            self.assertEqual(a.payload, 'foo')

            self.assertEqual(rw.range_l, i + 1)
            self.assertEqual(rw.range_r, i + 6)

    def test_pop_left_until(self):
        rw = RingWindow(10)
        for i in xrange(10):
            rw.add(ContainerItem(i, i + 1, i))

        res = rw.pop_left_until(lambda x: x.payload == 5)
        print map(lambda x: x.payload, res)
        self.assertEqual(len(res), 5)
        self.assertEqual(
                map(lambda x: x.payload, res), 
                [0, 1, 2, 3, 4])

    def test_pop_left_to(self):
        rw = RingWindow(10)
        for i in xrange(10):
            rw.add(ContainerItem(i, i + 1, i))

        res = rw.pop_left_to(lambda x: x.payload == 5)
        print map(lambda x: x.payload, res)
        self.assertEqual(len(res), 6)
        self.assertEqual(
                map(lambda x: x.payload, res), 
                [0, 1, 2, 3, 4, 5])

    def test_pop_left_until(self):
        rw = RingWindow(10)
        rw.add(ContainerItem(1, 2, 'foo'))
        res = rw.pop_left_until(lambda x: False)
        print res
        self.assertEqual(res, [])

        rw.add(ContainerItem(0, 1, 'bar'))
        res = rw.pop_left_until(lambda x: False)
        self.assertEqual(len(res), 2)
        self.assertEqual( (res[0].range_l, res[0].range_r), (0, 1) )
        self.assertEqual(res[0].payload, 'bar')
        self.assertEqual( (res[1].range_l, res[1].range_r), (1, 2) )
        self.assertEqual(res[1].payload, 'foo')

    def test_out_of_bound(self):
        rw = RingWindow(10, 1000)

        self.assertEqual(rw.get_by_index(999), None)
        self.assertEqual(rw.get_by_index(1999), None)
        self.assertEqual(rw.get_by_index(1999999999), None)

    def test_seq_id_rewind(self):
        rw = RingWindow(10, 0xFFFFFFFD)
        self.assertEqual(rw.range_l, 0xFFFFFFFD)
        self.assertEqual(rw.range_r, 0x00000007)

        rw.add(ContainerItem(0x00000001, 0x00000004, 'foo'))

        self.assertEqual(rw.get_left(), None)

        rw.add(ContainerItem(0xFFFFFFFD, 0x00000001, 'bar'))
        self.assertEqual(rw.get_left().payload, 'bar')

        rw.add(ContainerItem(0x00000004, 0x00000006, 'baz0'))
        rw.add(ContainerItem(0x00000006, 0x00000010, 'baz1'))

        with self.assertRaises(RingWindow.InvalidOperation):
            rw.add(ContainerItem(0x00000011, 0x0000ABCD, 'baz2'))

        res = rw.pop_left_until(lambda x: x.payload.startswith('baz'))

        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].payload, 'bar')
        self.assertEqual(res[1].payload, 'foo')

if __name__ == '__main__':
    unittest.main()

