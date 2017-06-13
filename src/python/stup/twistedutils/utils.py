#coding=utf-8

from twisted.internet import defer, protocol, reactor

@defer.inlineCallbacks
def sleep(timeout, reactor_=reactor):
    d = defer.Deferred()
    reactor_.callLater(timeout, d.callback, None)
    yield d

