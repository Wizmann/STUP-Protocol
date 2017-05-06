#coding=utf-8
import sys

import unittest
import Server as ServerStates
from .. import StupPacket

from Fake_test import *

class FakeServerStupCore(FakeStupCore):
    def send(self, msg, **kwargs):
        super(self.__class__, self).send(msg, **kwargs)

    def recv(self, pack):
        syn = pack.syn
        ack = pack.ack
        if self.state.state_nr == ServerStates.CLOSED and syn:
            self.set_state(ServerStates.LISTEN)
        elif self.state.state_nr == ServerStates.LISTEN and ack:
            self.set_state(ServerStates.ESTABLISHED)
        super(self.__class__, self).recv(pack)

class FakeProtocol(FakeProtocolBase):
    state_machine_cls = ServerStates.ServerStateMachine
    stupcore_cls = FakeServerStupCore

class TestServerStateMachine(unittest.TestCase):
    def test_server_get_syn(self):
        p = FakeProtocol()
        w = p.worker
        c = p.stupcore

        self.assertEqual(p.state.state_nr, ServerStates.CLOSED)
        p.recv(StupPacket.SynPacket())
        self.assertEqual(p.state.state_nr, ServerStates.LISTEN)
        self.assertEqual(c.recv_buffer[0].syn, 1)

    def test_connection_established(self):
        p = FakeProtocol()
        w = p.worker
        c = p.stupcore

        self.assertEqual(p.state.state_nr, ServerStates.CLOSED)
        p.recv(StupPacket.SynPacket())
        self.assertEqual(p.state.state_nr, ServerStates.LISTEN)
        self.assertEqual(c.recv_buffer[0].syn, 1)

        p.recv(StupPacket.AckPacket())
        self.assertEqual(p.state.state_nr, ServerStates.ESTABLISHED)
        self.assertEqual(c.recv_buffer[1].ack, 1)

    def test_syn_then_reset(self):
        p = FakeProtocol()
        w = p.worker
        c = p.stupcore

        self.assertEqual(p.state.state_nr, ServerStates.CLOSED)
        p.recv(StupPacket.SynPacket())
        self.assertEqual(p.state.state_nr, ServerStates.LISTEN)
        self.assertEqual(c.recv_buffer[0].syn, 1)

        p.recv(StupPacket.SynPacket())
        self.assertEqual(p.state.state_nr, ServerStates.LISTEN)
        self.assertEqual(len(c.recv_buffer), 1)

        p.recv(StupPacket.Packet())
        self.assertEqual(p.state.state_nr, ServerStates.LISTEN)
        self.assertEqual(len(c.recv_buffer), 1)

    def test_invalid_syn(self):
        p = FakeProtocol()
        w = p.worker
        c = p.stupcore

        self.assertEqual(p.state.state_nr, ServerStates.CLOSED)
        p.recv(StupPacket.Packet())
        self.assertEqual(p.state.state_nr, ServerStates.RST)

    def test_happy_path(self):
        str_a = "hello world"
        str_b = "are you playing golf, or you're just fucking around"

        p = FakeProtocol()
        w = p.worker
        c = p.stupcore

        self.assertEqual(p.state.state_nr, ServerStates.CLOSED)
        p.recv(StupPacket.SynPacket())
        self.assertEqual(p.state.state_nr, ServerStates.LISTEN)
        self.assertEqual(c.recv_buffer[0].syn, 1)

        p.recv(StupPacket.SynPacket())
        self.assertEqual(p.state.state_nr, ServerStates.LISTEN)
        self.assertEqual(len(c.recv_buffer), 1)

        p.recv(StupPacket.AckPacket())
        self.assertEqual(p.state.state_nr, ServerStates.ESTABLISHED)
        self.assertEqual(len(c.recv_buffer), 2)

        p.recv(StupPacket.Packet(str_a))
        self.assertEqual(p.state.state_nr, ServerStates.ESTABLISHED)
        self.assertEqual(len(c.recv_buffer), 3)

        p.recv(StupPacket.Packet(str_a))
        self.assertEqual(p.state.state_nr, ServerStates.ESTABLISHED)
        self.assertEqual(len(c.recv_buffer), 4)

        p.recv(StupPacket.FinPacket())
        self.assertEqual(p.state.state_nr, ServerStates.ESTABLISHED)
        self.assertEqual(len(c.recv_buffer), 5)

        p.recv(StupPacket.RstPacket())
        self.assertEqual(p.state.state_nr, ServerStates.RST)
        self.assertEqual(len(c.recv_buffer), 5)


