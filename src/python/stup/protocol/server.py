#coding=utf-8
from __future__ import absolute_import

import sys
import logging
from twisted.python import log

from stup.state.machine import ServerStateMachine
from .base import StupBaseProtocol

class StupServerProtocol(StupBaseProtocol):
    state_machine_cls = ServerStateMachine

    def startProtocol(self):
        pass
