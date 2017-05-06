#coding=utf-8
import sys
import unittest

import Client as ClientStates
from .. import StupPacket

from Fake_test import *

class FakeClientStupCore(FakeStupCore):
    def send(self, msg, **kwargs):
        syn = kwargs.get('syn', 0)
        if self.state.state_nr == ClientStates.CLOSED and syn:
            self.set_state(ClientStates.LISTEN)
        super(self.__class__, self).send(msg, **kwargs)

    def recv(self, pack):
        syn = pack.syn
        ack = pack.ack
        if self.state.state_nr == ClientStates.LISTEN and syn and ack:
            self.set_state(ClientStates.ESTABLISHED)
        super(self.__class__, self).recv(pack)

class FakeProtocol(FakeProtocolBase):
    state_machine_cls = ClientStates.ClientStateMachine
    stupcore_cls = FakeClientStupCore


class TestClientStateMachine(unittest.TestCase):
    def test_connection_send_syn(self):
        p = FakeProtocol()
        w = p.worker

        self.assertEqual(p.state.state_nr, ClientStates.CLOSED)
        p.send('', syn=1)
        self.assertEqual(p.state.state_nr, ClientStates.LISTEN)
        self.assertEqual(w.send_buffer[0][1]['syn'], 1)

    def test_conection_establish_conn(self):
        p = FakeProtocol()
        w = p.worker

        self.assertEqual(p.state.state_nr, ClientStates.CLOSED)

        p.send('', syn=1)
        self.assertEqual(w.send_buffer[0][1]['syn'], 1)
        self.assertEqual(p.state.state_nr, ClientStates.LISTEN)

        syn_ack_pack = StupPacket.SynAckPacket()
        p.recv(syn_ack_pack)
        self.assertEqual(p.stupcore.recv_buffer[0].syn, 1)
        self.assertEqual(p.stupcore.recv_buffer[0].ack, 1)
        self.assertEqual(p.state.state_nr, ClientStates.ESTABLISHED)

    def test_conection_fin(self):
        p = FakeProtocol()
        w = p.worker

        self.assertEqual(p.state.state_nr, ClientStates.CLOSED)

        p.send('', syn=1)
        self.assertEqual(w.send_buffer[0][1]['syn'], 1)
        self.assertEqual(p.state.state_nr, ClientStates.LISTEN)

        syn_ack_pack = StupPacket.SynAckPacket()
        p.recv(syn_ack_pack)
        self.assertEqual(p.stupcore.recv_buffer[0].syn, 1)
        self.assertEqual(p.stupcore.recv_buffer[0].ack, 1)
        self.assertEqual(p.state.state_nr, ClientStates.ESTABLISHED)

        p.send('foo')
        self.assertEqual(w.send_buffer[1][0], 'foo')
        self.assertTrue(not w.send_buffer[1][1])

        pack = StupPacket.Packet('bar')
        p.recv(pack)
        self.assertEqual(p.stupcore.recv_buffer[1].data, 'bar')
        self.assertEqual(p.state.state_nr, ClientStates.ESTABLISHED)

        fin_pack = StupPacket.FinPacket()
        p.recv(fin_pack)
        self.assertEqual(p.state.state_nr, ClientStates.ESTABLISHED)

        rst_pack = StupPacket.RstPacket()
        p.recv(rst_pack)
        self.assertEqual(p.state.state_nr, ClientStates.RST)
