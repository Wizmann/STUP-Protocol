#coding=utf-8
'''
State Machine for Client side

    +-------------+
    |             |
    |    CLOSE    |
    |             |
    +------+------+
           |
           |
           |
    +------v------+
    |             |    ERR/TIMEOUT
    |    LISTEN   +-------+
    |             |       |
    +------+------+       |       +-------------+
           |              |       |             |
           |              +------->     RST     |
           |              |       |             |
    +------v------+       |       +-------------+
    |             |       |
    | ESTABLISHED +-------+
    |             |    ERR/TIMEOUT
    +------+------+
           |
           |
           |
    +------v------+
    |             |
    |     FIN     |
    |             |
    +-------------+
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
        logging.debug("[%s:%d] CloseState can not recv pack" % self.protocol.peer_addr)
        return -1

    def send(self, message, **kwargs):
        syn = kwargs.get('syn', 0)
        if not syn:
            logging.debug(
                    "[%s:%d] CloseState can only send syn message" 
                    % self.protocol.peer_addr)
        else:
            self.stupcore.send(message, **kwargs)

class ListenState(BaseState):
    @property
    def state_nr(self):
        return LISTEN
    
    def _recv(self, pack):
        if pack.syn and pack.ack:
            logging.debug("[%s:%d] ListenState get SYN/ACK" % self.protocol.peer_addr)
            self.stupcore.recv(pack)
        else:
            logging.warning(
                "[%s:%d] ListenState invalid input" % self.protocol.peer_addr)
            self.reset()

    def send(self, message, **kwargs):
        logging.debug("[%s:%d] ListenState can not send message" % self.protocol.peer_addr)

class EstablishedState(EstablishedState):
    pass

class RstState(RstState):
    pass

class FinState(FinState):
    pass

class ClientStateMachine(StateMachineBase):
    module = sys.modules[__name__]
