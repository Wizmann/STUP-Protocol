#coding=utf-8
import os
import sys
import pytest
import logging

from twisted.trial import unittest
from twisted.test import proto_helpers
from twisted.internet import defer
from twisted.python import log

from .. import Config
from .. import StupPacket
from .. import Utils
from .. import StateMachine
from ..RingContainer import RingBuffer
from .Server import StupServerProtocol

log.startLogging(sys.stdout)

class FakeServerProtocol(StupServerProtocol):
    def __init__(self, peer_addr):
        self.output = ''
        super(FakeServerProtocol, self).__init__(peer_addr)

    def dataReceived(self, msg):
        self.output += msg

    def cleanUp(self):
        pass

class TestServerProtocol(unittest.TestCase):
    def setUp(self):
        self.peer_addr = ('127.0.0.1', 12345)
        self.protocol = FakeServerProtocol(self.peer_addr)

        self.protocol.stupcore.get_timeout = lambda x: 0.1
        self.protocol.stupcore.RETRY_THRESHOLD = 3
        self.protocol.stupcore.send_seq_id = 0
        self.protocol.stupcore.output_buffer = RingBuffer(1000, 0)
        self.protocol.stupcore.WAIT_ALL_DONE_TIMEOUT = 0.1

        self.transport = proto_helpers.FakeDatagramTransport()
        self.protocol.makeConnection(self.transport)

    def tearDown(self):
        self.protocol.stupcore.cancel_all_defers()

    def test_happy_path(self):
        sm = StupPacket.SynPacket()
        sm.seq_number = 1
        self.protocol.datagramReceived(StupPacket.serialize(sm), self.peer_addr)
        self.assertEqual(self.protocol.output, '')
        self.assertEqual(self.protocol.state.state_nr, StateMachine.LISTEN)
        seq_id = 0

        pack = StupPacket.deserialize(self.transport.written[0][0])
        self.seq_id = pack.seq_number

        self.assertEqual(pack.syn, 1)
        self.assertEqual(pack.ack, 1)

        am = StupPacket.AckPacket()
        am.seq_number = 1
        am.ack_number = seq_id
        self.protocol.datagramReceived(StupPacket.serialize(am), self.peer_addr)

        self.assertTrue(len(self.transport.written), 1)
        self.assertEqual(self.protocol.state.state_nr, StateMachine.ESTABLISHED)

        msg1 = StupPacket.Packet('de')
        msg1.seq_number = 5
        msg2 = StupPacket.Packet('abc')
        msg2.seq_number = 2

        self.protocol.datagramReceived(StupPacket.serialize(msg1), self.peer_addr)

        self.assertTrue(len(self.transport.written), 1)
        self.assertEqual(self.protocol.output, '')

        self.protocol.datagramReceived(StupPacket.serialize(msg2), self.peer_addr)

        self.assertTrue(len(self.transport.written), 2)
        self.assertEqual(self.protocol.output, 'abcde')

        self.assertEqual(self.protocol.state.state_nr, StateMachine.ESTABLISHED)
