#coding=utf-8

import pytest
import twisted
from twisted.trial import unittest
from twisted.test import proto_helpers
from twisted.internet.defer import inlineCallbacks
from twisted.internet.defer import Deferred
from twisted.python import log

from .. import Utils
from .StupCore import *
from .. import StupPacket
from .. import Config
from .. import StateMachine

class FakeTransport(object):
    def __init__(self, output_buffer):
        self.output_buffer = output_buffer

    def write(self, payload, *args, **kwargs):
        self.output_buffer.append(payload)

class FakeState(object):
    def __init__(self, state_nr):
        self.state_nr = state_nr

class FakeStateMachine(object):
    def __init__(self):
        self.state = FakeState(-1)

    def set_state(self, state_nr):
        self.state = FakeState(state_nr)

class FakeProtocol(object):
    def __init__(self):
        self.output_buffer = []
        self.peer_addr = ('127.0.0.1', 1234)
        self.transport = FakeTransport(self.output_buffer)
        self.state_machine = FakeStateMachine()
        self.is_cleaned_up = 0

    @property
    def state(self):
        return self.state_machine.state

    def last_packet(self):
        payload = self.output_buffer[-1]
        return StupPacket.Packet.deserialize(payload)

    def connectionMade(self):
        pass

    def cleanUp(self):
        self.is_cleaned_up = 1

class ClientStupCoreTest(unittest.TestCase):
    def setUp(self):
        self.protocol = FakeProtocol()
        self.stupcore = StupCore(self.protocol)
        self.stupcore.WAIT_ALL_DONE_TIMEOUT = 0.5

    def tearDown(self):
        self.stupcore.cancel_all_defers()

    def test_passively_rst(self):
        self.stupcore.handle_rst()
        self.assertEqual(len(self.protocol.output_buffer), 0)
        self.assertEqual(self.protocol.state.state_nr, StateMachine.RST)

        for d in self.stupcore.get_all_defers():
            d.cancel()

    @pytest.inlineCallbacks
    def test_passively_fin(self):
        self.stupcore.get_timeout = lambda x: 3
        self.stupcore.NAGLE_TIMEOUT = 0.2
        self.stupcore.RETRY_THRESHOLD = 2
        self.stupcore.fin_wait = 0.5
        self.stupcore.send_seq_id = 0
        self.stupcore.output_buffer = RingBuffer(1000, 0)

        syn_ack_pack = StupPacket.SynAckPacket()
        syn_ack_pack.ack_number = 1

        self.stupcore.send('', syn=1)
        self.assertEqual(self.stupcore.output_buffer.size(), 1)

        self.stupcore.recv(syn_ack_pack)
        self.assertEqual(self.stupcore.output_buffer.size(), 0)

        self.assertEqual(self.stupcore.state.state_nr, StateMachine.ESTABLISHED)

        fin_pack = StupPacket.FinPacket()
        fin_pack.seq_number = 1
        self.stupcore.recv(fin_pack)

        self.assertEqual(self.stupcore.state.state_nr, StateMachine.FIN)

        yield TwistedUtils.sleep(0.3)
        print self.protocol.last_packet()

        self.assertEqual(self.protocol.last_packet().fin, 1)
        self.assertEqual(self.protocol.last_packet().ack, 1)

        for d in self.stupcore.get_all_defers():
            d.cancel()

    def test_actively_rst(self):
        self.stupcore.reset()
        self.assertEqual(len(self.protocol.output_buffer), Config.RST_SEND_TIMES)
        for item in self.protocol.output_buffer:
            packet = StupPacket.Packet.deserialize(item)
            self.assertEqual(packet.rst, 1)
        self.assertEqual(self.protocol.is_cleaned_up, 1)

    @pytest.inlineCallbacks
    def test_actively_fin(self):
        self.stupcore.set_state(StateMachine.ESTABLISHED)

        self.stupcore.finalize()

        yield TwistedUtils.Utils.sleep(0.5)
        self.stupcore.cancel_all_defers()

        self.assertTrue(len(self.protocol.output_buffer), 1)
        self.assertTrue(self.protocol.last_packet().fin, 1)
        self.assertEqual(self.protocol.state.state_nr, StateMachine.ESTABLISHED)

    @pytest.inlineCallbacks
    def test_retry_syn(self):
        self.stupcore.get_timeout = lambda x: 0.1
        self.stupcore.RETRY_THRESHOLD = 3
        self.stupcore.send('', syn=1)

        self.assertEqual(
                StupPacket.Packet.deserialize(self.protocol.output_buffer[0]).syn, 1)

        self.assertEqual(len(self.protocol.output_buffer), 1)

        yield TwistedUtils.sleep(0.5)

        for i, item in enumerate(self.protocol.output_buffer):
            packet = StupPacket.Packet.deserialize(item)
            if i < 3:
                self.assertEquals(packet.syn, 1)
                self.assertEquals(packet.ack, 0)
            else:
                self.assertEquals(packet.syn, 0)
                self.assertEquals(packet.rst, 1)
        self.assertEquals(len(self.protocol.output_buffer), 3 + 5)

    def test_build_connection(self):
        SEQ_ID = 0xcafebabe
        self.stupcore.get_timeout = lambda x: 0.2
        self.stupcore.RETRY_THRESHOLD = 3
        self.stupcore.send_seq_id = SEQ_ID
        self.stupcore.output_buffer = RingBuffer(1000, SEQ_ID)

        # send ack
        self.stupcore.send('', syn=1)

        # recv syn_ack
        syn_ack_pack = StupPacket.SynAckPacket()
        syn_ack_pack.ack_number = SEQ_ID + 1
        self.stupcore.recv(syn_ack_pack)

        self.assertNotEqual(self.stupcore.state.state_nr, StateMachine.RST)
        self.assertEqual(self.stupcore.state.state_nr, StateMachine.ESTABLISHED)

        self.assertEqual(len(self.protocol.output_buffer), 2)
        self.assertEqual(len(self.protocol.output_buffer), 2)
        packet1 = StupPacket.deserialize(self.protocol.output_buffer[0])
        packet2 = StupPacket.deserialize(self.protocol.output_buffer[1])

        self.assertEqual(packet1.syn, 1)
        self.assertEqual(packet1.ack, 0)

        self.assertEqual(packet2.syn, 0)
        self.assertEqual(packet2.ack, 1)

        self.assertEqual(self.stupcore.output_buffer.size(), 0)
        self.stupcore.reset()

    @defer.inlineCallbacks
    def test_ping_pong_client(self):
        self.stupcore.get_timeout = lambda x: 0.1
        self.stupcore.NAGLE_TIMEOUT = 0.0
        self.stupcore.RETRY_THRESHOLD = 2
        self.stupcore.send_seq_id = 0
        self.stupcore.output_buffer = RingBuffer(1000, 0)

        syn_ack_pack = StupPacket.SynAckPacket()
        syn_ack_pack.ack_number = 1

        self.stupcore.send('', syn=1)
        self.assertEqual(self.stupcore.output_buffer.size(), 1)

        self.stupcore.recv(syn_ack_pack)
        self.assertEqual(self.stupcore.output_buffer.size(), 0)

        self.assertEqual(self.stupcore.state.state_nr, StateMachine.ESTABLISHED)

        ping_pack = StupPacket.Packet('ping')
        ping_pack.seq_number = 1
        self.stupcore.recv(ping_pack)
        self.assertEqual(self.protocol.last_packet().ack, 1)
        self.assertEqual(self.protocol.last_packet().syn, 0)
        self.assertEqual(self.stupcore.output_buffer.size(), 0)

        self.stupcore.send('pong')
        yield TwistedUtils.sleep(0.5)
        self.assertEqual(self.stupcore.output_buffer.size(), len('pong'))

        self.assertEqual(self.stupcore.state.state_nr, StateMachine.RST)
        self.stupcore.cancel_all_defers()

    @pytest.inlineCallbacks
    def test_nagle(self):
        self.stupcore.get_timeout = lambda x: 0.1
        self.stupcore.NAGLE_TIMEOUT = 0.1
        self.stupcore.RETRY_THRESHOLD = 2
        self.stupcore.send_seq_id = 0
        self.stupcore.SEND_CHUNK_SIZE = 10
        self.stupcore.output_buffer = RingBuffer(1000, 0)

        syn_ack_pack = StupPacket.SynAckPacket()
        syn_ack_pack.ack_number = 1

        self.stupcore.send('', syn=1)
        self.assertEqual(self.stupcore.output_buffer.size(), 1)

        self.stupcore.recv(syn_ack_pack)
        self.assertEqual(self.stupcore.output_buffer.size(), 0)

        self.assertEqual(self.stupcore.state.state_nr, StateMachine.ESTABLISHED)

        self.stupcore.send('a' * 10)
        self.stupcore.send('b' * 10)
        self.stupcore.send('c')

        self.assertEqual(self.stupcore.output_buffer.size(), 20)

        yield TwistedUtils.Utils.sleep(0.5)
        self.stupcore.cancel_all_defers()

        self.assertEqual(self.stupcore.output_buffer.size(), 21)

        rst_count = 0
        for packet in self.protocol.output_buffer:
            rst_count += StupPacket.deserialize(packet).rst

        self.assertTrue(rst_count == Config.RST_SEND_TIMES)

    def test_file_transfer(self):
        self.stupcore.get_timeout = lambda x: 0.2
        self.stupcore.NAGLE_TIMEOUT = 1
        self.stupcore.RETRY_THRESHOLD = 2
        self.stupcore.SEND_CHUNK_SIZE = 10
        self.stupcore.output_buffer = RingBuffer(1000, 990)
        self.stupcore.send_seq_id = 990

        self.stupcore.send('', syn=1)
        self.assertEqual(self.stupcore.output_buffer.size(), 1)

        syn_ack_pack = StupPacket.SynAckPacket()
        syn_ack_pack.ack_number = 991

        self.stupcore.recv(syn_ack_pack)
        self.assertEqual(self.stupcore.output_buffer.size(), 0)

        self.assertEqual(self.stupcore.state.state_nr, StateMachine.ESTABLISHED)

        packet = StupPacket.Packet('a' * 10)
        packet.seq_number = 1

        self.assertEqual(self.stupcore.recv(packet), 'a' * 10)

        packet = StupPacket.Packet('c' * 10)
        packet.seq_number = 21
        self.assertEqual(self.stupcore.recv(packet), '')

        packet = StupPacket.Packet('b' * 10)
        packet.seq_number = 11
        self.assertEqual(self.stupcore.recv(packet), 'b' * 10 + 'c' * 10)

        self.stupcore.reset()

class ServerStupCoreTest(unittest.TestCase):
    def setUp(self):
        self.protocol = FakeProtocol()
        self.stupcore = StupCore(self.protocol)
        self.stupcore.WAIT_ALL_DONE_TIMEOUT = 0.1

    def tearDown(self):
        self.stupcore.cancel_all_defers()

    @pytest.inlineCallbacks
    def test_retry_syn_ack(self):
        self.stupcore.get_timeout = lambda x: 0.1
        self.stupcore.RETRY_THRESHOLD = 3

        syn_pack = StupPacket.SynPacket()
        self.stupcore.recv(syn_pack)

        self.assertEqual(self.protocol.last_packet().syn, 1)
        self.assertEqual(self.protocol.last_packet().ack, 1)
        self.assertEqual(self.stupcore.state.state_nr, StateMachine.LISTEN)

        # retry & rst
        yield TwistedUtils.sleep(0.5)
        self.assertEqual(self.stupcore.state.state_nr, StateMachine.RST)

        for i, item in enumerate(self.protocol.output_buffer):
            packet = StupPacket.Packet.deserialize(item)
            print packet
            if i < 3:
                self.assertEquals(packet.syn, 1)
                self.assertEquals(packet.ack, 1)
            else:
                self.assertEquals(packet.ack, 0)
                self.assertEquals(packet.syn, 0)
                self.assertEquals(packet.rst, 1)
        self.assertEquals(len(self.protocol.output_buffer), 3 + 5)

    def test_build_connection(self):
        self.stupcore.send_seq_id = 0
        self.stupcore.output_buffer = RingBuffer(1000, 0)
        self.stupcore.get_timeout = lambda x: 0.1
        self.stupcore.NAGLE_TIMEOUT = 0.2
        self.stupcore.RETRY_THRESHOLD = 3

        syn_pack = StupPacket.SynPacket()
        self.stupcore.recv(syn_pack)

        self.assertEqual(self.stupcore.state.state_nr, StateMachine.LISTEN)
        self.assertEqual(self.protocol.last_packet().syn, 1)
        self.assertEqual(self.protocol.last_packet().ack, 1)

        ack_pack = StupPacket.AckPacket()
        ack_pack.ack_number = 1
        self.stupcore.recv(ack_pack)

        self.assertEqual(self.stupcore.state.state_nr, StateMachine.ESTABLISHED)
        self.stupcore.reset()

    @defer.inlineCallbacks
    def test_ping_pong_server(self):
        self.stupcore.get_timeout = lambda x: 0.1
        self.stupcore.NAGLE_TIMEOUT = 0.0
        self.stupcore.RETRY_THRESHOLD = 2
        self.stupcore.send_seq_id = 0
        self.stupcore.output_buffer = RingBuffer(1000, 0)

        syn_pack = StupPacket.SynPacket()
        self.stupcore.recv(syn_pack)

        self.assertEqual(self.stupcore.state.state_nr, StateMachine.LISTEN)
        self.assertEqual(self.protocol.last_packet().syn, 1)
        self.assertEqual(self.protocol.last_packet().ack, 1)

        ack_pack = StupPacket.AckPacket()
        ack_pack.ack_number = 1
        ack_pack.psh = 1
        self.stupcore.recv(ack_pack)
        self.assertEqual(self.stupcore.state.state_nr, StateMachine.ESTABLISHED)

        ping_pack = StupPacket.Packet('ping')
        ping_pack.seq_number = 1
        self.stupcore.recv(ping_pack)
        yield TwistedUtils.sleep(0.2)
        self.assertEqual(self.protocol.last_packet().ack, 1)
        self.assertEqual(self.protocol.last_packet().syn, 0)
        self.stupcore.send('pong')

        yield TwistedUtils.sleep(0.5)

        self.assertEqual(self.stupcore.state.state_nr, StateMachine.RST)

    @defer.inlineCallbacks
    def test_fast_resend(self):
        self.stupcore.get_timeout = lambda x: 0.5
        self.stupcore.NAGLE_TIMEOUT = 0.0
        self.stupcore.RETRY_THRESHOLD = 2
        self.stupcore.FAST_RESEND_THRESHOLD = 5
        self.stupcore.send_seq_id = 0
        self.stupcore.output_buffer = RingBuffer(1000, 0)

        syn_pack = StupPacket.SynPacket()
        self.stupcore.recv(syn_pack)

        self.assertEqual(self.stupcore.state.state_nr, StateMachine.LISTEN)
        self.assertEqual(self.protocol.last_packet().syn, 1)
        self.assertEqual(self.protocol.last_packet().ack, 1)

        ack_pack = StupPacket.AckPacket()
        ack_pack.ack_number = 1
        ack_pack.psh = 1
        self.stupcore.recv(ack_pack)
        self.assertEqual(self.stupcore.state.state_nr, StateMachine.ESTABLISHED)

        ping_pack = StupPacket.Packet('ping')
        ping_pack.seq_number = 1
        self.stupcore.recv(ping_pack)
        yield TwistedUtils.sleep(0.3)
        self.assertEqual(self.protocol.last_packet().ack, 1)
        self.assertEqual(self.protocol.last_packet().syn, 0)
        self.stupcore.send('pong1')
        yield TwistedUtils.sleep(0.1)
        self.stupcore.send('pong2')
        yield TwistedUtils.sleep(0.1)
        self.stupcore.send('pong3')

        yield TwistedUtils.sleep(0.1)

        for i in xrange(20):
            ack_pack = StupPacket.AckPacket()
            ack_pack.ack_number = 6
            self.stupcore.recv(ack_pack)

        yield TwistedUtils.sleep(0.5)

        self.assertEqual(
                sum(map(lambda bin_: StupPacket.deserialize(bin_).urg, self.protocol.output_buffer)), 4)

        self.assertEqual(self.stupcore.state.state_nr, StateMachine.RST)

