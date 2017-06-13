#coding=utf-8
from __future__ import absolute_import

import pytest
import twisted
from twisted.trial import unittest
from twisted.internet.defer import Deferred
from twisted.python import log

from stup.twistedutils.deferred_deque import *

class DeferredDequeueTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.buffer = []

        super(DeferredDequeueTest, self).__init__(*args, **kwargs)

    def test_all(self):
        dd = DeferredDeque()
        dd.append_left('a')
        dd.append_right('b')

        self.assertEqual(list(dd.pending), ['a', 'b'])
        dd.pop_right().addCallback(lambda x: self.buffer.append(x))
        self.assertEqual(self.buffer, ['b'])

        dd.pop_left().addCallback(lambda x: self.buffer.append(x))
        self.assertEqual(self.buffer, ['b', 'a'])

        dd.pop_right().addCallback(lambda x: self.buffer.append(x))
        self.assertEqual(self.buffer, ['b', 'a'])

        dd.append_left('c')
        self.assertEqual(self.buffer, ['b', 'a', 'c'])


