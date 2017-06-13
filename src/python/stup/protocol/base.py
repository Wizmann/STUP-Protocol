#coding=utf-8
from __future__ import absolute_import

import abc
import sys
import logging

import stup

from twisted.python import log
from twisted.internet import defer, protocol, reactor, error
from twisted.internet.defer import DeferredQueue
from twisted.internet.task import deferLater

from stup import utils as Utils
from stup import config as Config
from stup.core.core import StupCore

class StupBaseProtocol(protocol.DatagramProtocol, object):
    __metaclass__ = abc.ABCMeta

    state_machine_cls = None

    def __init__(self, peer_addr):
        self.peer_addr = peer_addr
        self.state_machine = self.state_machine_cls(self)
        self.is_closed = False

        self.stupcore = StupCore(self)

    @property
    def state(self):
        return self.state_machine.state

    def send(self, msg):
        return self.state.send(msg)

    def datagramReceived(self, datagram, addr):
        packet = stup.packet.deserialize(datagram)
        data = self.state.recv(packet)
        if data:
            return self.dataReceived(data)

    def connectionMade(self):
        pass

    @abc.abstractmethod
    def dataReceived(self, msg):
        pass

    @abc.abstractmethod
    def startProtocol(self):
        pass

    def connectionLost(self, reason):
        if self.is_closed:
            return

        if not reason:
            self.stupcore.finalize()
        elif isinstance(reason, str) or isinstance(reason, unicode):
            self.stupcore.reset()
        elif reason.type is error.ConnectionDone:
            self.stupcore.finalize()
        else:
            self.stupcore.reset()

    def cleanUp(self, msg=""):
        pass
