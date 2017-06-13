#coding=utf-8
from __future__ import absolute_import

import sys
import logging
from twisted.python import log

from stup import utils as Utils
from stup.state import machine as StateMachine
from .base import StupBaseProtocol

class StupClientProtocol(StupBaseProtocol):
    state_machine_cls = StateMachine.ClientStateMachine

    def startProtocol(self):
        self.state.send('', syn=1, psh=1)

    def cleanUp(self, msg=""):
        if not self.is_closed:
            self.transport.loseConnection()
            self.is_closed = True
