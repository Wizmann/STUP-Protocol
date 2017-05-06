#coding=utf-8

import logging
from RingMixin import RingMixin

class RingWindow(RingMixin, object):
    def __init__(self, size=1, base_idx=0):
        assert isinstance(size, int) and size >= 0

        self._index_valid_check(base_idx)

        self.buf = {}
        self.range_l = base_idx
        self.range_r = self._move(base_idx, size)

        logging.debug("init ring window [%d, %d]" 
                % (self.range_l, self.range_r))

        self._capacity = size
        self._size = size

    def get_by_index(self, key):
        return self.buf.get(key, None)

    def pop_left(self):
        if not self.buf:
            return None

        if self.range_l not in self.buf:
            return None

        value = self.buf[self.range_l]
        del self.buf[self.range_l]

        self.range_l = value.range_r
        self.range_r = self._move(self.range_l, self._size)

        return value

    def get_left(self):
        return self.buf.get(self.range_l, None)

    def pop_left_until(self, fun):
        res = []
        while self.buf:
            cur = self.get_left()
            if not cur:
                break
            if fun(cur):
                break
            res.append(self.pop_left())
        return res

    def pop_left_to(self, fun):
        res = []
        while self.buf:
            cur = self.get_left()
            if not cur:
                break
            res.append(self.pop_left())
            if fun(cur):
                break
        return res

    def add(self, item):
        if not self.contains(item.range_l):
            raise self.InvalidOperation(
                    '%x not in range[%x, %x]' 
                    % (item.range_l, self.range_l, self.range_r))
        self.buf[item.range_l] = item

