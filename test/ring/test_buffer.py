#coding=utf-8

import unittest

from stup.ring.buffer import RingBuffer
from stup.ring.container.item import ContainerItem

class RingBufferTest(unittest.TestCase):
    def test_basic(self):
        rb1 = RingBuffer(10)
        self.assertEqual(rb1.size(), 0)

        rb1.append(ContainerItem(0, 10000, 'abc'))
        self.assertEqual(rb1.size(), 10000)
        self.assertEqual(
                rb1.append(ContainerItem(0, 10, 'abc')),
                RingBuffer.INVALID)

        rb2 = RingBuffer(10)
        rb2.append(ContainerItem(0, 0, 'foo'))
        self.assertEqual(rb2.size(), 0xFFFFFFFF)

    def test_ring_buffer_append(self):
        rb = RingBuffer(10)
        self.assertEqual(rb.capacity(), 10)
        for i in range(13):
            res = rb.append(ContainerItem(i, i + 1, str(i)))
            if i < 10:
                self.assertEqual(rb.size(), i + 1)
                self.assertEqual(res, RingBuffer.OK)
            else:
                # the capacity is only a soft limitation
                self.assertEqual(rb.size(), i + 1)
                self.assertEqual(res, RingBuffer.FULL)

        self.assertTrue(rb.range_l == 0)
        self.assertTrue(rb.range_r == 13)

    def test_ring_pop_left(self):
        rb = RingBuffer(10)
        self.assertEqual(rb.capacity(), 10)

        self.assertEqual(rb.pop_left(), None)

        rb.append(ContainerItem(0, 6, 'foo'))
        rb.append(ContainerItem(6, 10, 'bar'))

        self.assertEqual(rb.range_l, 0)
        self.assertEqual(rb.range_r, 10)

        self.assertEqual(rb.capacity(), 10)
        self.assertEqual(rb.size(), 10)

        cur = rb.get_left()
        self.assertEqual(cur.payload, 'foo')
        cur.payload = 'baz'
        self.assertEqual(cur.payload, 'baz')

        cur = rb.pop_left()
        self.assertEqual(cur.payload, 'baz')

        self.assertEqual(rb.range_l, 6)
        self.assertEqual(rb.range_r, 10)

        self.assertEqual(rb.capacity(), 10)
        self.assertEqual(rb.size(), 4)


    def test_pop_left_until(self):
        rb = RingBuffer(10)
        self.assertEqual(rb.capacity(), 10)
        self.assertEqual(rb.size(), 0)

        rb.append(ContainerItem(0, 2, 'foo0'))
        rb.append(ContainerItem(2, 4, 'foo1'))

        rb.append(ContainerItem(4, 7, 'bar0'))
        rb.append(ContainerItem(7, 8, 'bar1'))

        self.assertEqual(rb.size(), 8)

        res = rb.pop_left_until(lambda x: x.payload.startswith('bar'))
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0].payload, 'foo0')
        self.assertEqual(res[1].payload, 'foo1')

        self.assertEqual(rb.size(), 4)
        self.assertIsNone(rb.get(0))
        self.assertIsNone(rb.get(2))
        self.assertIsNotNone(rb.get(4))
        self.assertIsNotNone(rb.get(7))

    def test_seq_id_rewind(self):
        rb = RingBuffer(10, 0xFFFFFFFD)
        rb.append(ContainerItem(0xFFFFFFFD, 0x00000001, 'foo'))
        rb.append(ContainerItem(0x00000001, 0x00000003, 'bar'))

        self.assertEqual(rb.range_l, 0xFFFFFFFD)
        self.assertEqual(rb.range_r, 0x00000003)
        self.assertEqual(rb.size(), 6)

        res = rb.pop_left_until(lambda x: x.payload == 'bar')
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0].payload, 'foo')
        self.assertEqual(res[0].size(), 4)

if __name__ == '__main__':
    unittest.main()

