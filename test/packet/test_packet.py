#coding=utf-8

import unittest
import random
from stup import packet
from stup.packet.packet import Packet
from stup import crypto

class PacketTest(unittest.TestCase):
    def test_serialize_and_deserialize(self):
        msg = Packet(b'foo')

        self.assertEqual(msg.ver, 0)
        self.assertEqual(msg.nonce, 0)
        self.assertEqual(msg.urg, 0)
        self.assertEqual(msg.liv, 0)
        self.assertEqual(msg.ack, 0)
        self.assertEqual(msg.psh, 0)
        self.assertEqual(msg.rst, 0)
        self.assertEqual(msg.syn, 0)
        self.assertEqual(msg.fin, 0)
        self.assertEqual(msg.seq_number, 0)
        self.assertEqual(msg.ack_number, 0)
        self.assertEqual(msg.data, b'foo')

        buf = Packet.serialize(msg)

        msg1 = Packet.deserialize(buf)
        assert msg.data == msg1.data

    def test_random_serialize_and_deserialize(self):
        for i in range(1111):
            payload = crypto.cipher.nonce(i)
            msg = Packet(payload)

            self.assertEqual(msg.ver, 0)
            self.assertEqual(msg.nonce, 0)
            self.assertEqual(msg.urg, 0)
            self.assertEqual(msg.liv, 0)
            self.assertEqual(msg.ack, 0)
            self.assertEqual(msg.psh, 0)
            self.assertEqual(msg.rst, 0)
            self.assertEqual(msg.syn, 0)
            self.assertEqual(msg.fin, 0)
            self.assertEqual(msg.seq_number, 0)
            self.assertEqual(msg.ack_number, 0)
            self.assertEqual(msg.data, payload)

            buf = Packet.serialize(msg)

            msg1 = Packet.deserialize(buf)
            assert msg.data == msg1.data

    def test_empty_buf(self):
        msg = Packet()
        self.assertEqual(msg.data, b'')

        msg.ver = 0x7
        msg.nonce = 0x3F
        msg.urg = 1
        msg.liv = 1
        msg.ack = 1
        msg.psh = 1
        msg.rst = 1
        msg.syn = 1
        msg.fin = 1
        msg.seq_number = 0xFFFFFFFF
        msg.ack_number = 0xFFFFFFFF

        buf = Packet.serialize(msg)

        buf = Packet.serialize(msg)
        msg1 = Packet.deserialize(buf)

        self.assertEqual(len(msg1.data), 0)

    def test_message_specific(self):
        m1 = packet.ack.AckPacket()
        self.assertEqual(m1.ack, 1)

        m2 = packet.fin.FinPacket()
        self.assertEqual(m2.fin, 1)

        m3 = packet.rst.RstPacket()
        self.assertEqual(m3.rst, 1)

        m4 = packet.synack.SynAckPacket()
        self.assertEqual(m4.syn, 1)
        self.assertEqual(m4.ack, 1)

        m5 = packet.syn.SynPacket()
        self.assertEqual(m5.syn, 1)
