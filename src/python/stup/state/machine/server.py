#coding=utf-8

'''
State Machine of Server side

    +-----------+
    |           |
    |   CLOSE   |
    |           |
    +-----+-----+
          |
     SYN  |
          |
    +-----v-----+
    |           |       ERROR/TIMEOUT
    |   LISTEN  +-----------+
    |           |           |
    +-----+-----+           |    +-----------+
          |                 |    |           |
     ACK  |                 +---->    RST    |
          |                 |    |           |
    +-----v-----+           |    +-----------+
    |           |           |
    |ESTABLISHED+-----------+
    |           |        ERROR/TIMEOUT
    +-----+-----+
          |
     FIN  |
          |
    +-----v-----+
    |           |
    |    FIN    |
    |           |
    +-----------+
'''

import sys
import abc
import logging

from .base import *

class ClosedState(BaseState):
    @property
    def state_nr(self):
        return CLOSED

    def _recv(self, pack):
        if pack.syn:
            logging.debug("[%s:%d] CloseState get SYN" % self.protocol.peer_addr)
            return self.stupcore.recv(pack)
        else:
            logging.warning("[%s:%d] CloseState invalid input" % self.protocol.peer_addr)
            self.reset()
            return ''

    def send(self, message, **kwargs):
        syn = kwargs.get('syn', 0)
        ack = kwargs.get('ack', 0)
        if syn and ack:
            self.stupworker.send(message, **kwargs)
        else:
            logging.debug(
                    "[%s:%d] CloseState can only send synack message" 
                    % self.protocol.peer_addr)

class ListenState(BaseState):
    @property
    def state_nr(self):
        return LISTEN
    
    def _recv(self, pack):
        if pack.ack:
            logging.debug("[%s:%d] ListenState get ACK for SYN/ACK" % self.protocol.peer_addr)
            return self.stupcore.recv(pack)
        else:
            logging.warning("[%s:%d] ListenState invalid input" % self.protocol.peer_addr)
            return ''

    def send(self, message, **kwargs):
        ack = kwargs.get('ack', 0)
        if ack:
            self.stupworker.send(message, **kwargs)
        else:
            logging.debug(
                    "[%s:%d] ListenState can only send ack message" 
                    % self.protocol.peer_addr)

class EstablishedState(EstablishedState):
    pass

class RstState(RstState):
    pass

class FinState(FinState):
    pass

class ServerStateMachine(StateMachineBase):
    module = sys.modules[__name__]
