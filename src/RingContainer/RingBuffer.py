#coding=utf-8

import logging

from .. import Utils
from RingMixin import RingMixin

class RingBuffer(RingMixin, object):
    def __init__(self, size=1, base_idx=0):
        assert isinstance(size, int) and size >= 0

        self._index_valid_check(base_idx)

        self.buf = {}
        self.range_l = self.range_r = base_idx

        self._capacity = size

    def append(self, item):
        if item.range_l != self.range_r:
            logging.error('invalid key: %d [%d, %d]',
                    item.range_l, self.range_l, self.range_r)
            return self.INVALID

        if item.range_l in self.buf:
            logging.error('duplicate key: %d [%d, %d]',
                    item.range_l, self.range_l, self.range_r)
            return self.DUPLICATE

        self.buf[item.range_l] = item
        self.range_r = item.range_r
        if self.size() > self.capacity():
            return self.FULL
        return self.OK

    def full(self):
        return self.size() >= self._capacity

    def pop_left(self):
        if self.size() == 0:
            return None

        logging.debug("pop left [%d, %d]" % (self.range_l, self.range_r))
        assert self.range_l in self.buf

        value = self.buf[self.range_l]
        del self.buf[self.range_l]
        self.range_l = value.range_r
        return value

    def get_left(self):
        if self.size() == 0:
            return None

        logging.debug("get left [%d, %d]" % (self.range_l, self.range_r))
        assert self.range_l in self.buf

        value = self.buf[self.range_l]
        return value

    def get(self, key):
        return self.buf.get(key, None)

    def pop_left_until(self, fun):
        res = []
        logging.debug("ring buf size: %d" % self.size())
        while self.size():
            cur = self.get_left()
            if cur is None:
                break
            if fun(cur):
                break
            res.append(self.pop_left())
        logging.debug("pop left until done: [%d, %d]" % (self.range_l, self.range_r))
        return res

