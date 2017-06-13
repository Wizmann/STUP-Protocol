#coding=utf-8
import sys
import abc
import logging
from twisted.internet import defer

from stup import config as Config

STATES = [
    'CLOSED',
    'LISTEN',
    'ESTABLISHED',
    'FIN',
    'RST',
]

for (i, state) in enumerate(STATES):
    setattr(sys.modules[__name__], state, i)

class BaseState(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, protocol):
        self.protocol = protocol

    @property
    def stupcore(self):
        return self.protocol.stupcore

    @abc.abstractproperty
    def state_nr(self):
        return -1

    @abc.abstractmethod
    def send(self, message, **kwargs):
        pass

    def recv(self, pack):
        if pack.rst and self.state_nr not in [RST, FIN]:
            logging.warning("got rst pack from %s:%d" % self.protocol.peer_addr)
            self.handle_reset()
            return ''
        return self._recv(pack)
    
    @abc.abstractmethod
    def _recv(self, pack):
        pass

    def handle_reset(self):
        self.stupcore.handle_rst()

    def reset(self):
        self.stupcore.reset()

    def handle_finalize(self):
        self.stupcore.handle_fin()

    def finalize(self):
        self.stupcore.finalize()

class EstablishedState(BaseState):
    @property
    def state_nr(self):
        return ESTABLISHED
        
    def _recv(self, pack):
        return self.stupcore.recv(pack)

    def send(self, message, **kwargs):
        return self.stupcore.send(message, **kwargs)

class RstState(BaseState):
    @property
    def state_nr(self):
        return RST
    
    def _recv(self, pack):
        logging.debug(
                "[%s:%d] RstState should not read any pack"
                % self.protocol.peer_addr)

    def send(self, message, **kwargs):
        rst = kwargs.get('rst', 0)
        if not rst:
            logging.debug(
                    "[%s:%d] RstState should not send any message"
                    % self.protocol.peer_addr)
        else:
            self.stupcore.send(message, **kwargs)

class FinState(BaseState):
    @property
    def state_nr(self):
        return FIN
    
    def _recv(self, pack):
        self.stupcore.send('', ack=1, psh=1)
        return ''

    def send(self, message, **kwargs):
        pass

class StateMachineBase(object):
    module = None
    def __init__(self, protocol):
        self.protocol = protocol

        self.state_dict = {}
        for state_name in STATES:
            cls_name = state_name.capitalize() + 'State'
            var_name = state_name.lower() + '_state'
            setattr(self, var_name, getattr(self.module, cls_name)(self.protocol))

            new_state = getattr(self, var_name)
            self.state_dict[new_state.state_nr] = new_state

        self.state = self.closed_state

    def set_state(self, state_nr):
        self.state = self.state_dict[state_nr]

    def get_state(self, state_nr):
        return self.state_dict[state_nr]
