#coding=utf-8
from __future__ import absolute_import

import time
import logging
from twisted.internet import protocol, reactor, defer
from stup import config as Config
from stup.protocol.server import StupServerProtocol
from stup.third.party.socks5 import SOCKSv5

class StupTransportAdapter(object):
    def __init__(self, stup):
        self.stup = stup

    def write(self, buf):
        logging.debug("StupTransportAdapter send %d bytes" % len(buf))
        self._write(buf, 0.5)

    def _write(self, buf, sleep_time):
        ret = self.stup.send(buf)
        if ret == -1:
            sleep_time = min(10, sleep_time * 2)
            logging.debug("output buffer is full, arrange next send in %ds", sleep_time)
            self.stup.socks5.peersock.transport.pauseProducing()
            reactor.callLater(sleep_time, self._write, buf, sleep_time)
        elif self.stup.socks5.peersock:
            self.stup.socks5.peersock.transport.resumeProducing()

    def loseConnection(self, reason):
        logging.debug("StupTransportAdapter lose connection")
        self.stup.connectionLost(reason)

    def startReading(self):
        self.stup.transport.startReading()

    def stopReading(self):
        self.stup.transport.stopReading()

class StupProtocol(StupServerProtocol):
    def __init__(self, factory, addr):
        self.socks5 = SOCKSv5()
        self.socks5.transport = StupTransportAdapter(self)
        self.factory = factory
        self.addr = addr

        super(StupProtocol, self).__init__(addr)

    def dataReceived(self, buf):
        self.socks5.dataReceived(buf)

    def cleanUp(self):
        if self.addr in self.factory.connections:
            del self.factory.connections[self.addr]
        super(StupProtocol, self).cleanUp()

class StupServerFactoryProtocol(protocol.DatagramProtocol):
    def __init__(self, *args, **kwargs):
        self.connections = {}
    
    def datagramReceived(self, msg, addr):
        if addr not in self.connections:
            protocol = StupProtocol(self, addr)
            protocol.makeConnection(self.transport)
            self.connections[addr] = protocol

        self.connections[addr].datagramReceived(msg, addr)

if __name__ == '__main__':
    reactor.listenUDP(Config.SERVER_PORT, StupServerFactoryProtocol())
    reactor.run()
