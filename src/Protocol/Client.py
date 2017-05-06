#coding=utf-8
import sys
import logging
from twisted.python import log

from .. import Utils
from .. import Config
from .. import StateMachine
from .BaseProtocol import StupBaseProtocol

class StupClientProtocol(StupBaseProtocol):
    state_machine_cls = StateMachine.ClientStateMachine

    def startProtocol(self):
        self.state.send('', syn=1, psh=1)

    def cleanUp(self, msg=""):
        if not self.is_closed:
            self.transport.loseConnection()
            self.is_closed = True
