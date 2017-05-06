#coding=utf-8

import unittest
import random
from .StupPacket import Packet
from .. import Crypto

class PacketTest(unittest.TestCase):
    def test_serialize_and_deserialize(self):
        msg = Packet('foo')

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
        self.assertEqual(msg.data, 'foo')

        buf = Packet.serialize(msg)

        msg1 = Packet.deserialize(buf)
        assert msg.data == msg1.data

    def test_random_serialize_and_deserialize(self):
        for i in xrange(1111):
            payload = Crypto.Cipher.nonce(i)
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
        self.assertEqual(msg.data, '')

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
        from .AckPacket import *
        m1 = AckPacket()
        self.assertEqual(m1.ack, 1)

        from .FinPacket import *
        m2 = FinPacket()
        self.assertEqual(m2.fin, 1)

        from .RstPacket import *
        m3 = RstPacket()
        self.assertEqual(m3.rst, 1)

        from .SynAckPacket import *
        m4 = SynAckPacket()
        self.assertEqual(m4.syn, 1)
        self.assertEqual(m4.ack, 1)

        from .SynPacket import *
        m5 = SynPacket()
        self.assertEqual(m5.syn, 1)

if __name__ == '__main__':
    unittest.main()

