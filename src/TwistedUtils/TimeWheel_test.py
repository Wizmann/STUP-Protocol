#coding=utf-8

import pytest
import unittest
from TimeWheel import *

class TimeWheelTest(unittest.TestCase):
    def test_run(self):
        tw = TimeWheel(size=100, granularity=0.1)
        self.assertEqual(len(tw.wheel), 101)

        self.is_called = False

        def cb():
            self.is_called = True

        tw.addCallLater(10, cb)

        self.assertEqual(len(tw.wheel[100]), 1)
        for i in xrange(101):
            tw.moveNext()

        self.assertTrue(self.is_called)

        #test ptr rewind
        self.is_called = False

        tw.addCallLater(10, cb)

        self.assertEqual(len(tw.wheel[100]), 1)
        for i in xrange(101):
            tw.moveNext()

        self.assertTrue(self.is_called)

    def test_kwargs(self):
        tw = TimeWheel(size=100, granularity=1)

        self.is_called = False
        def cb(arg1, **kwargs):
            self.is_called = True
            print kwargs
            assert arg1 == ''
            arg2 = kwargs.get('arg2', 0)
            assert arg2 == 1

        tw.addCallLater(1, cb, '', **{'arg2': 1})

        tw.moveNext()
        tw.moveNext()

        self.assertTrue(self.is_called)
