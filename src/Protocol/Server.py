#coding=utf-8
import sys
import logging
from twisted.python import log

from .. import Utils
from .. import Config
from .. import StateMachine
from .BaseProtocol import StupBaseProtocol

class StupServerProtocol(StupBaseProtocol):
    state_machine_cls = StateMachine.ServerStateMachine

    def startProtocol(self):
        pass
