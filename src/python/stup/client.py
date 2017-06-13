#coding=utf-8
from __future__ import absolute_import

import logging
from twisted.internet import defer, protocol, reactor
from stup import config as Config
from stup.protocol.client import StupClientProtocol

class StupOutgoing(StupClientProtocol):
    def __init__(self, serveraddr, socks5):
        self.socks5 = socks5
        self.socks5.stup = self

        super(StupOutgoing, self).__init__(serveraddr)

    def connectionMade(self):
        self.socks5.defer.callback(None)

    def dataReceived(self, buf):
        self.socks5.transport.write(buf)

    def connectionReset(self):
        logging.warning("connection reset")

    def connectionFinalized(self):
        logging.warning("connection finalized")

    def cleanUp(self, msg=""):
        self.socks5.connectionLost(msg)
        super(StupOutgoing, self).cleanUp()

class Socks5AdapterProtocol(object, protocol.Protocol):
    @defer.inlineCallbacks
    def connectionMade(self):
        serveraddr = (Config.SERVER_ADDR, Config.SERVER_PORT)
        self.defer = defer.Deferred()
        self.transport.stopReading()
        reactor.listenUDP(
                0, StupOutgoing(serveraddr, self))
        yield self.defer
        self.transport.startReading()

    def dataReceived(self, buf):
        self.stup.send(buf)

    def connectionLost(self, reason):
        self.stup.connectionLost(reason)
        self.transport.loseConnection()

    def cleanUp(self):
        pass

factory = protocol.Factory()
factory.protocol = Socks5AdapterProtocol

if __name__ == '__main__':
    reactor.listenTCP(Config.CLIENT_PORT, factory, backlog=1)
    reactor.run()
