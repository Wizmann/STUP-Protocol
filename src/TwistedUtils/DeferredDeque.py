#coding=utf-8

from twisted.internet import defer, protocol, reactor
from collections import deque

class DeferredDeque(object):
    def __init__(self):
        self.waiting = deque()
        self.pending = deque()

    def get_left(self):
        return self.pending[0] if self.pending else None

    def get_right(self):
        return self.pending[-1] if self.pending else None

    def append_left(self, obj):
        if self.waiting:
            self.waiting.popleft().callback(obj)
            return
        self.pending.appendleft(obj)

    def append_right(self, obj):
        if self.waiting:
            self.waiting.popleft().callback(obj)
            return
        self.pending.append(obj)

    def pop_left(self):
        if self.pending:
            return defer.succeed(self.pending.popleft())
        d = defer.Deferred(canceller=self._cancelGet)
        self.waiting.append(d)
        return d

    def pop_right(self):
        if self.pending:
            return defer.succeed(self.pending.pop())
        d = defer.Deferred(canceller=self._cancelGet)
        self.waiting.append(d)
        return d

    def _cancelGet(self, d):
        self.waiting.remove(d)

