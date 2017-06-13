#coding=utf-8

from stup.state import machine as StateMachineBase

class FakeWorker(object):
    def __init__(self, protocol):
        self.send_buffer = []

    def send(self, message, **kwargs):
        self.send_buffer.append( (message, kwargs) )

class FakeStupCore(object):
    def __init__(self, protocol):
        self.protocol = protocol
        self.recv_buffer = []
    
    @property
    def state(self):
        return self.state_machine.state

    @property
    def state_machine(self):
        return self.protocol.state_machine

    @property
    def worker(self):
        return self.protocol.worker

    def set_state(self, state_nr):
        self.state_machine.set_state(state_nr)

    def get_state(self):
        return self.state_machine.state

    def recv(self, pack):
        self.recv_buffer.append(pack)

    def send(self, message, **kwargs):
        self.worker.send(message, **kwargs)

    def finalize(self):
        self.set_state(StateMachineBase.FIN)

    def reset(self):
        self.set_state(StateMachineBase.RST)

    def handle_fin(self):
        self.set_state(StateMachineBase.FIN)

    def handle_rst(self):
        self.set_state(StateMachineBase.RST)

class FakeProtocolBase(object):
    state_machine_cls = None
    stupcore_cls = None
    def __init__(self):
        self.peer_addr = ('127.0.0.1', 12345)
        self.stupcore = self.stupcore_cls(self)
        self.worker = FakeWorker(self)
        self.state_machine = self.state_machine_cls(self)

    @property
    def state(self):
        return self.state_machine.state

    def recv(self, pack):
        self.state.recv(pack)

    def send(self, msg, **kwargs):
        self.state.send(msg, **kwargs)
