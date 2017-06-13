#coding=utf-8

from __future__ import absolute_import
import logging
import six

from stup.utils import nop

class TimeWheel(object):
    def __init__(self, size=100, granularity=0.05):
        assert granularity >= 0.01

        self.size = size + 1
        self.granularity = granularity
        self.wheel = [[] for i in range(self.size)]
        self.ptr = 0
        self.pending = 0

    def addCallLater(self, time, cb, *args, **kwargs):
        offset = int(time / self.granularity - 1e-5) + 1

        offset = max(1, offset)
        offset = min(offset, self.size - 1)

        logging.debug("add calllater[%d][%d]: %s %s %s" % (self.ptr, offset, cb, args, kwargs))

        self.pending += 1
        cur = (self.ptr + offset) % self.size
        self.wheel[cur].append((cb, args, kwargs))

    def moveNext(self):
        for (cb, args, kwargs) in self.wheel[self.ptr]:
            logging.debug("time wheel call: %s %s %s", cb, args, kwargs)
            try:
                cb(*args, **kwargs)
            except Exception as e:
                logging.warning("function[%s] throws an exception: %s" , cb, e)
            self.pending -= 1
        self.wheel[self.ptr] = []
        self.ptr = (self.ptr + 1) % self.size

    def isEmpty(self):
        return self.pending == 0

    def maxTimeout(self):
        return (self.size - 1) * self.granularity

    def clear(self):
        self.pending = 0
        self.moveNext = nop
        self.addCallLater = nop

