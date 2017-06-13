#coding=utf-8

import logging
import six

from stup import utils as Utils

class RingMixin(object):
    OK = 0
    FULL = -1
    EMPTY = -2
    INVALID = -3
    DUPLICATE = -4

    class InvalidOperation(Exception): pass

    def _index_valid_check(self, key):
        if six.PY2:
            if not (type(key) in [int, long] and Utils.is_u32(key)):
                raise self.InvalidOperation('key{0} out of range'.format(key))
        else:
            if not (type(key) in [int] and Utils.is_u32(key)):
                raise self.InvalidOperation('key{0} out of range'.format(key))

    def _move(self, key, offset):
        return Utils.seq_add(key, offset)

    def capacity(self):
        return self._capacity

    def size(self):
        res = Utils.seq_sub(self.range_r, self.range_l)
        if res != 0:
            return res
        elif self.buf:
            return 0xFFFFFFFF
        else:
            return 0

    def contains(self, key):
        self._index_valid_check(key)
        l, r = self.range_l, self.range_r

        if l == r:
            return False

        if r < l:
            '''
            seq id rewind

                   R                  L
                   v                  v
            ----------------------------------->
               ^                           ^
              key0                       key1
            '''
            return l <= key or key < r
        else:
            '''
                   L                  R
                   v                  v
            ----------------------------------->
                          ^
                         key
            '''
            return l <= key < r

    def __str__(self):
        return '\n'.join(map(str, self.__iter__()))

    def __iter__(self):
        items = sorted(self.buf.items(),
                cmp=lambda x, y: cmp(x.range_l, y.range_l))
        for item in items:
            yield item
